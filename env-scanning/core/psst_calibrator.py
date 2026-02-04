"""
PSSTCalibrator - Calibration module for pSST scores using Platt Scaling.

Tracks human review outcomes and adjusts pSST scoring weights so that
predicted confidence matches observed reliability. For example, signals
scored at pSST=80 should be judged reliable ~80% of the time by human
reviewers.

Key concepts:
    - ECE (Expected Calibration Error): Measures gap between predicted
      confidence and actual accuracy across binned intervals.
    - Platt Scaling: Fits logistic parameters (A, B) so that
      calibrated_score = 1 / (1 + exp(A * raw_score + B))
    - Review History: Stores (signal_id, psst_score, human_judgment)
      tuples for calibration training data.

Usage:
    from core.psst_calibrator import PSSTCalibrator

    calibrator = PSSTCalibrator(config, calibration_dir)
    calibrator.record_human_review('signal-001', 78.5, True)

    if calibrator.should_calibrate():
        result = calibrator.calibrate_weights()
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class PSSTCalibrator:
    """
    Calibrate pSST scores using human feedback and Platt Scaling.

    Stores review history and periodically recalibrates weights
    to minimize Expected Calibration Error (ECE).
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        calibration_dir: Optional[Path] = None
    ):
        """
        Initialize PSSTCalibrator.

        Args:
            config: psst_calibration section from thresholds.yaml
            calibration_dir: Directory for storing calibration data
                            (defaults to env-scanning/calibration/)
        """
        config = config or {}

        self.min_samples = config.get('min_samples', 20)
        self.trigger_interval = config.get('trigger_interval', 10)
        self.ece_target = config.get('ece_target', 0.05)
        self.num_bins = config.get('bins', 10)
        self.enabled = config.get('enabled', True)

        # Set up calibration directory
        if calibration_dir:
            self.calibration_dir = Path(calibration_dir)
        else:
            self.calibration_dir = Path('env-scanning/calibration')

        self.history_file = self.calibration_dir / 'psst-review-history.json'
        self.weights_file = self.calibration_dir / 'psst-calibrated-weights.json'

        # In-memory cache
        self._history: Optional[List[Dict]] = None
        self._weights: Optional[Dict] = None

    # ── Review History Management ──────────────────────────────────────

    def record_human_review(
        self,
        signal_id: str,
        psst_score: float,
        human_judgment: bool,
        dimensions: Optional[Dict[str, int]] = None,
        reviewer_notes: str = ''
    ) -> Dict[str, Any]:
        """
        Record a human review outcome for calibration.

        If a previous review exists for the same signal_id, the old review
        is marked as superseded and only the latest review is used for
        calibration. Contradictory judgments are flagged.

        Args:
            signal_id: The signal that was reviewed
            psst_score: The pSST score at time of review
            human_judgment: True if human confirmed signal as reliable/valid
            dimensions: Optional dimension scores at time of review
            reviewer_notes: Optional notes from reviewer

        Returns:
            {'status': 'recorded'} or {'status': 'superseded', 'conflict': True/False}
        """
        history = self._load_history()

        record = {
            'signal_id': signal_id,
            'psst_score': psst_score,
            'human_judgment': human_judgment,
            'dimensions': dimensions or {},
            'reviewer_notes': reviewer_notes,
            'recorded_at': datetime.now().isoformat(),
            'superseded': False
        }

        # Check for existing reviews of the same signal
        conflict = False
        for existing in history:
            if existing.get('signal_id') == signal_id and not existing.get('superseded'):
                existing['superseded'] = True
                if existing.get('human_judgment') != human_judgment:
                    conflict = True

        history.append(record)
        self._save_history(history)
        self._history = history

        if conflict:
            return {'status': 'superseded', 'conflict': True}
        elif any(r.get('signal_id') == signal_id and r.get('superseded') for r in history):
            return {'status': 'superseded', 'conflict': False}
        return {'status': 'recorded'}

    def get_review_count(self) -> int:
        """Get total number of active (non-superseded) human reviews."""
        return len(self._get_active_reviews())

    def _get_active_reviews(self) -> List[Dict]:
        """Get only non-superseded reviews for calibration."""
        history = self._load_history()
        return [r for r in history if not r.get('superseded', False)]

    def get_review_history(self) -> List[Dict]:
        """Get full review history."""
        return self._load_history()

    # ── Calibration Trigger ────────────────────────────────────────────

    def should_calibrate(self, scan_count: Optional[int] = None) -> bool:
        """
        Check if calibration should be triggered.

        Conditions:
        1. Calibration is enabled
        2. Minimum sample size reached (default: 20 reviews)
        3. Trigger interval reached (default: every 10 scans)

        Args:
            scan_count: Current scan number (if None, checks sample size only)

        Returns:
            True if calibration should run
        """
        if not self.enabled:
            return False

        review_count = self.get_review_count()
        if review_count < self.min_samples:
            return False

        if scan_count is not None:
            return scan_count % self.trigger_interval == 0

        return True

    # ── ECE Calculation ────────────────────────────────────────────────

    def calculate_ece(
        self,
        scores: Optional[List[float]] = None,
        outcomes: Optional[List[bool]] = None
    ) -> Dict[str, Any]:
        """
        Calculate Expected Calibration Error.

        ECE = sum(|accuracy_b - confidence_b| * n_b / N)

        Where b iterates over bins, accuracy_b is the fraction of
        correct predictions in bin b, confidence_b is the average
        predicted confidence in bin b.

        Args:
            scores: List of predicted scores (0-100). If None, uses history.
            outcomes: List of actual outcomes (True/False). If None, uses history.

        Returns:
            {
                'ece': 0.045,
                'bins': [...],
                'total_samples': 50,
                'meets_target': True
            }
        """
        if scores is None or outcomes is None:
            history = self._get_active_reviews()
            scores = [r['psst_score'] for r in history]
            outcomes = [r['human_judgment'] for r in history]

        if len(scores) == 0:
            return {
                'ece': 0.0,
                'bins': [],
                'total_samples': 0,
                'meets_target': True
            }

        n = len(scores)
        bin_width = 100.0 / self.num_bins

        bins = []
        ece = 0.0

        for i in range(self.num_bins):
            bin_lower = i * bin_width
            bin_upper = (i + 1) * bin_width

            # Find samples in this bin
            bin_indices = [
                j for j in range(n)
                if bin_lower <= scores[j] < bin_upper
            ]

            if not bin_indices:
                bins.append({
                    'range': [bin_lower, bin_upper],
                    'count': 0,
                    'avg_confidence': 0,
                    'accuracy': 0,
                    'gap': 0
                })
                continue

            bin_count = len(bin_indices)
            avg_confidence = sum(scores[j] for j in bin_indices) / bin_count / 100.0
            accuracy = sum(1 for j in bin_indices if outcomes[j]) / bin_count
            gap = abs(accuracy - avg_confidence)

            ece += gap * (bin_count / n)

            bins.append({
                'range': [bin_lower, bin_upper],
                'count': bin_count,
                'avg_confidence': round(avg_confidence, 4),
                'accuracy': round(accuracy, 4),
                'gap': round(gap, 4)
            })

        return {
            'ece': round(ece, 4),
            'bins': bins,
            'total_samples': n,
            'meets_target': ece <= self.ece_target
        }

    # ── Platt Scaling Calibration ──────────────────────────────────────

    def calibrate_weights(self) -> Dict[str, Any]:
        """
        Run Platt Scaling calibration on collected review data.

        Fits logistic parameters A, B such that:
            P(reliable | score) = 1 / (1 + exp(A * score + B))

        Uses gradient descent to minimize log-loss.

        Returns:
            {
                'status': 'success',
                'platt_A': -0.05,
                'platt_B': 3.5,
                'pre_ece': 0.08,
                'post_ece': 0.03,
                'samples_used': 50,
                'calibrated_at': '2026-01-30T...'
            }
        """
        history = self._get_active_reviews()

        if len(history) < self.min_samples:
            return {
                'status': 'insufficient_data',
                'samples_available': len(history),
                'samples_required': self.min_samples
            }

        scores = [r['psst_score'] / 100.0 for r in history]  # Normalize to 0-1
        outcomes = [1.0 if r['human_judgment'] else 0.0 for r in history]

        # ── Degeneracy checks ──────────────────────────────────────
        # Platt Scaling requires both positive and negative examples
        # and sufficient score variance to fit a meaningful sigmoid.
        positive_count = sum(1 for o in outcomes if o > 0.5)
        negative_count = len(outcomes) - positive_count

        if positive_count == 0 or negative_count == 0:
            return {
                'status': 'skipped_no_label_variance',
                'reason': (
                    'All reviews have identical judgment '
                    f'(positive={positive_count}, negative={negative_count}). '
                    'Platt Scaling requires both classes.'
                ),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'recommendation': 'Collect reviews with both positive and negative judgments'
            }

        # Check score variance (on 0-1 scale)
        mean_score = sum(scores) / len(scores)
        score_variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        min_variance = 0.01  # Minimum variance threshold

        if score_variance < min_variance:
            return {
                'status': 'skipped_low_score_variance',
                'reason': (
                    f'Score variance ({score_variance:.4f}) is below minimum ({min_variance}). '
                    'Calibration would collapse discrimination between scores.'
                ),
                'score_variance': round(score_variance, 6),
                'min_variance': min_variance,
                'recommendation': 'Collect reviews across a wider range of pSST scores'
            }

        # Calculate pre-calibration ECE
        pre_ece_result = self.calculate_ece(
            [r['psst_score'] for r in history],
            [r['human_judgment'] for r in history]
        )

        # Fit Platt Scaling via gradient descent
        A, B = self._fit_platt_scaling(scores, outcomes)

        # Apply calibration and calculate post-ECE
        calibrated_scores = [
            self._platt_transform(s, A, B) * 100 for s in scores
        ]
        post_ece_result = self.calculate_ece(
            calibrated_scores,
            [r['human_judgment'] for r in history]
        )

        # Save calibration weights
        calibration_result = {
            'platt_A': round(A, 6),
            'platt_B': round(B, 6),
            'pre_ece': pre_ece_result['ece'],
            'post_ece': post_ece_result['ece'],
            'samples_used': len(history),
            'calibrated_at': datetime.now().isoformat(),
            'version': self._next_version()
        }

        self._save_weights(calibration_result)

        return {
            'status': 'success',
            **calibration_result
        }

    def apply_calibration(self, raw_score: float) -> float:
        """
        Apply Platt Scaling calibration to a raw pSST score.

        Args:
            raw_score: Raw pSST score (0-100)

        Returns:
            Calibrated score (0-100)
        """
        weights = self._load_weights()

        if not weights or 'platt_A' not in weights:
            return raw_score  # No calibration available

        A = weights['platt_A']
        B = weights['platt_B']

        calibrated = self._platt_transform(raw_score / 100.0, A, B) * 100.0
        return round(max(0, min(100, calibrated)), 1)

    def get_calibration_version(self) -> str:
        """Get current calibration version string."""
        weights = self._load_weights()
        if not weights:
            return 'v1.0-uncalibrated'
        return weights.get('version', 'v1.0-calibrated')

    # ── Internal Methods ───────────────────────────────────────────────

    def _fit_platt_scaling(
        self,
        scores: List[float],
        outcomes: List[float],
        learning_rate: float = 0.01,
        max_iterations: int = 1000,
        tolerance: float = 1e-7
    ) -> Tuple[float, float]:
        """
        Fit Platt Scaling parameters using gradient descent.

        Minimizes negative log-likelihood:
            L = -sum(y * log(p) + (1-y) * log(1-p))

        where p = sigma(A * s + B) and sigma is the sigmoid function.
        """
        A = 0.0
        B = 0.0
        n = len(scores)

        for _ in range(max_iterations):
            grad_A = 0.0
            grad_B = 0.0

            for i in range(n):
                p = self._platt_transform(scores[i], A, B)
                p = max(1e-15, min(1 - 1e-15, p))  # Clamp for numerical stability
                error = p - outcomes[i]
                grad_A += error * scores[i]
                grad_B += error

            grad_A /= n
            grad_B /= n

            A -= learning_rate * grad_A
            B -= learning_rate * grad_B

            # Check convergence
            if abs(grad_A) < tolerance and abs(grad_B) < tolerance:
                break

        return A, B

    @staticmethod
    def _platt_transform(score: float, A: float, B: float) -> float:
        """Apply sigmoid transformation: 1 / (1 + exp(A*s + B))"""
        x = A * score + B
        # Clamp to avoid overflow
        x = max(-500, min(500, x))
        return 1.0 / (1.0 + math.exp(-x))

    def _next_version(self) -> str:
        """Generate next calibration version string."""
        weights = self._load_weights()
        if not weights or 'version' not in weights:
            return 'v1.1-calibrated'

        current = weights['version']
        try:
            version_num = current.split('v')[1].split('-')[0]
            major, minor = version_num.split('.')
            return f'v{major}.{int(minor) + 1}-calibrated'
        except (IndexError, ValueError):
            return 'v1.1-calibrated'

    # ── File I/O ───────────────────────────────────────────────────────

    def _load_history(self) -> List[Dict]:
        """Load review history from disk."""
        if self._history is not None:
            return self._history

        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self._history = json.load(f)
        else:
            self._history = []

        return self._history

    def _save_history(self, history: List[Dict]):
        """Save review history to disk."""
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def _load_weights(self) -> Optional[Dict]:
        """Load calibration weights from disk."""
        if self._weights is not None:
            return self._weights

        if self.weights_file.exists():
            with open(self.weights_file, 'r', encoding='utf-8') as f:
                self._weights = json.load(f)
        else:
            self._weights = None

        return self._weights

    def _save_weights(self, weights: Dict):
        """Save calibration weights to disk."""
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        with open(self.weights_file, 'w', encoding='utf-8') as f:
            json.dump(weights, f, indent=2, ensure_ascii=False)
        self._weights = weights
