"""
PSSTCalculator - predicted Signal Scanning Trust score calculator.

Inspired by AlphaFold's pLDDT (predicted Local Distance Difference Test),
pSST provides a per-signal confidence score (0-100) across 6 dimensions:

    SR (Source Reliability)       - How trustworthy is the source?
    ES (Evidence Strength)        - How strong is the supporting evidence?
    CC (Classification Confidence)- How confident is the STEEPs classification?
    TC (Temporal Confidence)      - How fresh and temporally relevant?
    DC (Distinctiveness Confidence)- How unique is this signal?
    IC (Impact Confidence)        - How confident are the impact predictions?

The final pSST score is a weighted composite of these dimensions,
accumulated across 5 pipeline stages.

This module is a PURE COMPUTATION module (no side effects, no I/O).
All data loading/saving is handled by the calling agents.

Usage:
    from core.psst_calculator import PSSTCalculator

    calc = PSSTCalculator(config)   # Pass psst config from thresholds.yaml
    sr = calc.calculate_sr(source_type='academic', peer_reviewed=True)
    psst = calc.calculate_psst(dimensions={'SR': sr, 'TC': tc, ...})
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class PSSTCalculator:
    """
    Calculate pSST (predicted Signal Scanning Trust) scores.

    Layer 1: Individual dimension scores (0-100 each)
    Layer 2: Stage-wise cumulative confidence
    Layer 3: Final composite pSST score + grade
    """

    # Default configuration (overridden by thresholds.yaml values)
    DEFAULT_DIMENSION_WEIGHTS = {
        'SR': 0.20, 'ES': 0.20, 'CC': 0.15,
        'TC': 0.15, 'DC': 0.15, 'IC': 0.15
    }

    DEFAULT_STAGE_ALPHAS = {
        'stage_1_collection': 0.15,
        'stage_2_filtering': 0.15,
        'stage_3_classification': 0.25,
        'stage_4_impact': 0.20,
        'stage_5_ranking': 0.25
    }

    DEFAULT_GRADE_THRESHOLDS = {
        'very_high': 90,
        'confident': 70,
        'low': 50,
        'very_low': 0
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PSSTCalculator with configuration from thresholds.yaml.

        Args:
            config: Dictionary containing psst_scoring and dimension_params
                    from thresholds.yaml. If None, uses defaults.
        """
        config = config or {}

        scoring = config.get('psst_scoring', {})
        self.dimension_weights = scoring.get(
            'dimension_weights', self.DEFAULT_DIMENSION_WEIGHTS
        )
        self.stage_alphas = scoring.get(
            'stage_alphas', self.DEFAULT_STAGE_ALPHAS
        )
        self.grade_thresholds = scoring.get(
            'grade_thresholds', self.DEFAULT_GRADE_THRESHOLDS
        )

        self.coverage_exponent = scoring.get('coverage_exponent', 0.5)

        level2 = scoring.get('level2_config', {})
        self.level2_enabled = level2.get('enabled', True)
        self.level2_base_weight = level2.get('base_weight', 0.85)
        self.level2_advanced_weight = level2.get('advanced_weight', 0.15)
        self.level2_grade_a_threshold = level2.get('grade_a_threshold', None)

        self.dimension_params = config.get('dimension_params', {})
        self.reporting = config.get('psst_reporting', {})

    # ── Layer 1: Individual Dimension Calculators ──────────────────────

    def calculate_sr(
        self,
        source_type: str,
        peer_reviewed: bool = False,
        citation_count: int = 0,
        corroboration_count: int = 1,
        source_quality: str = 'high',
        level2_data: Optional[Dict] = None
    ) -> int:
        """
        Calculate Source Reliability (SR) dimension.

        Args:
            source_type: Type of source (academic, patent, blog, etc.)
            peer_reviewed: Whether the source is peer-reviewed
            citation_count: Number of citations
            corroboration_count: Number of independent corroborating sources
            source_quality: Quality tier within source type.
                'high' = top-tier (e.g., Nature, Science) — default, backward compatible
                'medium' = mid-tier (e.g., regional journals, established outlets)
                'low' = low-tier (e.g., predatory journals, minor outlets)
            level2_data: Optional Level 2 criteria dict with keys:
                has_methodology (bool), has_replication (bool), data_transparency (bool)

        Returns:
            SR score (0-100). Capped at 85 without level2_data.
        """
        params = self.dimension_params.get('SR', {})
        base_scores = params.get('base_scores', {
            'academic': 85, 'patent': 80, 'government': 80,
            'policy': 75, 'news_major': 65, 'news_minor': 50,
            'blog': 45, 'social_media': 30
        })
        bonuses = params.get('bonuses', {
            'peer_reviewed': 10, 'citation_count_high': 5,
            'multiple_corroboration': 5
        })
        quality_offsets = params.get('quality_offsets', {
            'high': 0, 'medium': -15, 'low': -30
        })
        max_score = params.get('max_score', 100)

        score = base_scores.get(source_type, 40)
        score += quality_offsets.get(source_quality, 0)

        if peer_reviewed:
            score += bonuses.get('peer_reviewed', 10)
        if citation_count > 50:
            score += bonuses.get('citation_count_high', 5)
        if corroboration_count >= 2:
            score += bonuses.get('multiple_corroboration', 5)

        level1 = max(0, min(score, max_score))

        level2_raw = 0
        if level2_data:
            level2_raw = self.calculate_sr_level2(
                has_methodology=level2_data.get('has_methodology', False),
                has_replication=level2_data.get('has_replication', False),
                data_transparency=level2_data.get('data_transparency', False)
            )

        return self._apply_level2(level1, level2_raw)

    def calculate_es(
        self,
        has_quantitative_data: bool = False,
        source_count: int = 1,
        verification_status: str = 'unverified'
    ) -> int:
        """
        Calculate Evidence Strength (ES) dimension.

        Args:
            has_quantitative_data: Whether signal includes numeric metrics
            source_count: Number of independent sources
            verification_status: One of 'verified', 'partially_verified', 'unverified'

        Returns:
            ES score (0-100)
        """
        params = self.dimension_params.get('ES', {})
        scoring = params.get('scoring', {})

        # Quantitative component
        if has_quantitative_data:
            quant_score = scoring.get('quantitative_present', 40)
        else:
            quant_score = scoring.get('quantitative_absent', 10)

        # Source count component
        if source_count >= 3:
            source_score = scoring.get('sources_3_plus', 30)
        elif source_count == 2:
            source_score = scoring.get('sources_2', 20)
        else:
            source_score = scoring.get('sources_1', 10)

        # Verification component
        verification_scores = {
            'verified': scoring.get('verified', 30),
            'partially_verified': scoring.get('partially_verified', 15),
            'unverified': scoring.get('unverified', 5)
        }
        verif_score = verification_scores.get(verification_status, 5)

        return min(quant_score + source_score + verif_score, 100)

    def calculate_cc(
        self,
        top_category_score: float = 0.0,
        second_category_score: float = 0.0,
        keyword_match_ratio: float = 0.0,
        expert_validated: bool = False
    ) -> int:
        """
        Calculate Classification Confidence (CC) dimension.

        Args:
            top_category_score: Score of the highest-ranked category (0-1)
            second_category_score: Score of the second-ranked category (0-1)
            keyword_match_ratio: Ratio of keywords matching the category (0-1)
            expert_validated: Whether an expert confirmed the classification

        Returns:
            CC score (0-100). Returns 0 if signal is unclassified (both scores zero).
        """
        # Unclassified guard: both scores zero means no classification was attempted
        if top_category_score == 0.0 and second_category_score == 0.0:
            return 0

        params = self.dimension_params.get('CC', {})
        components = params.get('components', {
            'category_margin': 60, 'keyword_match': 25, 'expert_validation': 15
        })
        margin_scoring = params.get('margin_scoring', {
            'clear_margin': 60, 'moderate_margin': 40, 'narrow_margin': 20
        })

        # Category margin component
        margin = top_category_score - second_category_score
        if margin >= 0.20:
            margin_score = margin_scoring.get('clear_margin', 60)
        elif margin >= 0.10:
            margin_score = margin_scoring.get('moderate_margin', 40)
        else:
            margin_score = margin_scoring.get('narrow_margin', 20)

        # Keyword match component (scale to weight)
        max_kw = components.get('keyword_match', 25)
        keyword_score = int(keyword_match_ratio * max_kw)

        # Expert validation component
        max_exp = components.get('expert_validation', 15)
        expert_score = max_exp if expert_validated else 0

        return min(margin_score + keyword_score + expert_score, 100)

    def calculate_tc(
        self,
        published_date: Optional[str] = None,
        signal_status: str = 'developing',
        reference_date: Optional[str] = None,
        level2_data: Optional[Dict] = None
    ) -> int:
        """
        Calculate Temporal Confidence (TC) dimension.

        Args:
            published_date: Publication date (YYYY-MM-DD format)
            signal_status: One of 'emerging', 'developing', 'mature'
            reference_date: Reference date for freshness (defaults to today)
            level2_data: Optional Level 2 criteria dict with keys:
                momentum (str), has_update (bool), time_sensitivity (bool)

        Returns:
            TC score (0-100). Capped at 85 without level2_data.
        """
        params = self.dimension_params.get('TC', {})
        decay = params.get('freshness_decay', {
            'days_0_7': 100, 'days_8_14': 85, 'days_15_30': 70,
            'days_31_90': 50, 'days_91_plus': 30
        })

        # Parse dates
        if reference_date:
            ref = datetime.strptime(reference_date, '%Y-%m-%d')
        else:
            ref = datetime.now()

        if published_date:
            pub = datetime.strptime(published_date, '%Y-%m-%d')
            days_old = (ref - pub).days
        else:
            days_old = 999  # Unknown date → assume old

        # Future date guard: published_date after reference_date is a data error
        if days_old < 0:
            return 0

        # Freshness score
        if days_old <= 7:
            freshness = decay.get('days_0_7', 100)
        elif days_old <= 14:
            freshness = decay.get('days_8_14', 85)
        elif days_old <= 30:
            freshness = decay.get('days_15_30', 70)
        elif days_old <= 90:
            freshness = decay.get('days_31_90', 50)
        else:
            freshness = decay.get('days_91_plus', 30)

        # Status bonus
        status_bonus = {
            'emerging': params.get('emerging_bonus', 10),
            'developing': params.get('developing_bonus', 5),
            'mature': 0
        }
        bonus = status_bonus.get(signal_status, 0)

        level1 = min(freshness + bonus, 100)

        level2_raw = 0
        if level2_data:
            level2_raw = self.calculate_tc_level2(
                momentum=level2_data.get('momentum', 'stable'),
                has_update=level2_data.get('has_update', False),
                time_sensitivity=level2_data.get('time_sensitivity', False)
            )

        return self._apply_level2(level1, level2_raw)

    def calculate_dc(
        self,
        dedup_stage_passed: str = 'passed_all_4',
        level2_data: Optional[Dict] = None
    ) -> int:
        """
        Calculate Distinctiveness Confidence (DC) dimension.

        Args:
            dedup_stage_passed: How far the signal passed in dedup cascade.
                One of: 'passed_all_4', 'passed_3', 'passed_2', 'passed_1', 'duplicate'
            level2_data: Optional Level 2 criteria dict with keys:
                semantic_distance (float), information_gain (float),
                cross_category_novelty (bool)

        Returns:
            DC score (0-100). Capped at 85 without level2_data.
        """
        params = self.dimension_params.get('DC', {})
        stage_scores = params.get('cascade_stage_scores', {
            'passed_all_4': 100, 'passed_3': 85,
            'passed_2': 70, 'passed_1': 60, 'duplicate': 0
        })

        level1 = stage_scores.get(dedup_stage_passed, 0)

        level2_raw = 0
        if level2_data:
            level2_raw = self.calculate_dc_level2(
                semantic_distance=level2_data.get('semantic_distance', 0.0),
                information_gain=level2_data.get('information_gain', 0.0),
                cross_category_novelty=level2_data.get('cross_category_novelty', False)
            )

        return self._apply_level2(level1, level2_raw)

    def calculate_ic(
        self,
        cluster_stability: float = 0.5,
        cross_impact_consensus: float = 0.5,
        score_consistency: float = 0.5
    ) -> int:
        """
        Calculate Impact Confidence (IC) dimension.

        Args:
            cluster_stability: How stable the impact cluster assignment is (0-1)
            cross_impact_consensus: Agreement level in cross-impact scores (0-1)
            score_consistency: Impact score consistency across methods (0-1)

        Returns:
            IC score (0-100)
        """
        # Clamp inputs to valid range
        cluster_stability = max(0.0, min(1.0, cluster_stability))
        cross_impact_consensus = max(0.0, min(1.0, cross_impact_consensus))
        score_consistency = max(0.0, min(1.0, score_consistency))

        params = self.dimension_params.get('IC', {})
        components = params.get('components', {
            'cluster_stability': 50, 'cross_impact_consensus': 30,
            'score_consistency': 20
        })

        stability_score = int(cluster_stability * components.get('cluster_stability', 50))
        consensus_score = int(cross_impact_consensus * components.get('cross_impact_consensus', 30))
        consistency_score = int(score_consistency * components.get('score_consistency', 20))

        return min(stability_score + consensus_score + consistency_score, 100)

    # ── Level 2 Advanced Scoring (Difficulty Evolution) ─────────────────

    def _apply_level2(self, level1_score: int, level2_raw: int, max_level2: int = 15) -> int:
        """
        Blend Level 1 and Level 2 scores using configured weights.

        Without Level 2 data (level2_raw=0), the score is capped at
        level1 * base_weight (default 85% of level1).

        Args:
            level1_score: The base dimension score (0-100)
            level2_raw: Raw Level 2 points earned (0 to max_level2)
            max_level2: Maximum possible Level 2 points (default 15)

        Returns:
            Blended score (0-100)
        """
        if not self.level2_enabled:
            return level1_score
        if level2_raw == 0:
            return int(round(level1_score * self.level2_base_weight))
        level2_scaled = (level2_raw / max_level2) * 100
        final = level1_score * self.level2_base_weight + level2_scaled * self.level2_advanced_weight
        return int(round(max(0, min(100, final))))

    def calculate_sr_level2(
        self,
        has_methodology: bool = False,
        has_replication: bool = False,
        data_transparency: bool = False
    ) -> int:
        """
        Calculate SR Level 2 raw points (0-15).

        Args:
            has_methodology: Source describes research methodology
            has_replication: Results have been replicated
            data_transparency: Raw data or code is publicly available

        Returns:
            Raw Level 2 points (0-15)
        """
        params = self.dimension_params.get('SR', {})
        criteria = params.get('level2_criteria', {
            'has_methodology': {'points': 5},
            'has_replication': {'points': 5},
            'data_transparency': {'points': 5}
        })

        score = 0
        if has_methodology:
            score += criteria.get('has_methodology', {}).get('points', 5)
        if has_replication:
            score += criteria.get('has_replication', {}).get('points', 5)
        if data_transparency:
            score += criteria.get('data_transparency', {}).get('points', 5)

        return min(score, 15)

    def calculate_tc_level2(
        self,
        momentum: str = 'stable',
        has_update: bool = False,
        time_sensitivity: bool = False
    ) -> int:
        """
        Calculate TC Level 2 raw points (0-15).

        Args:
            momentum: Signal momentum ('accelerating', 'stable', 'decelerating')
            has_update: Signal has recent updates or follow-up coverage
            time_sensitivity: Signal has a time-bound decision window

        Returns:
            Raw Level 2 points (0-15)
        """
        params = self.dimension_params.get('TC', {})
        criteria = params.get('level2_criteria', {
            'momentum': {'accelerating': 6, 'stable': 3, 'decelerating': 0},
            'has_update': {'points': 5},
            'time_sensitivity': {'points': 4}
        })

        momentum_scores = criteria.get('momentum', {})
        score = momentum_scores.get(momentum, 0)

        if has_update:
            score += criteria.get('has_update', {}).get('points', 5)
        if time_sensitivity:
            score += criteria.get('time_sensitivity', {}).get('points', 4)

        return min(score, 15)

    def calculate_dc_level2(
        self,
        semantic_distance: float = 0.0,
        information_gain: float = 0.0,
        cross_category_novelty: bool = False
    ) -> int:
        """
        Calculate DC Level 2 raw points (0-15).

        Args:
            semantic_distance: Cosine distance from nearest cluster centroid (0-1)
            information_gain: Ratio of new keywords vs existing DB (0-1)
            cross_category_novelty: Signal introduces novel concepts to its category

        Returns:
            Raw Level 2 points (0-15)
        """
        params = self.dimension_params.get('DC', {})
        criteria = params.get('level2_criteria', {
            'semantic_distance': {'very_novel': 7, 'moderately_novel': 4, 'slightly_novel': 1},
            'information_gain': {'high': 5, 'medium': 3, 'low': 1},
            'cross_category_novelty': {'points': 3}
        })

        score = 0

        # Semantic distance scoring
        sd_scores = criteria.get('semantic_distance', {})
        if semantic_distance >= 0.7:
            score += sd_scores.get('very_novel', 7)
        elif semantic_distance >= 0.5:
            score += sd_scores.get('moderately_novel', 4)
        elif semantic_distance >= 0.3:
            score += sd_scores.get('slightly_novel', 1)

        # Information gain scoring
        ig_scores = criteria.get('information_gain', {})
        if information_gain >= 0.5:
            score += ig_scores.get('high', 5)
        elif information_gain >= 0.3:
            score += ig_scores.get('medium', 3)
        elif information_gain >= 0.1:
            score += ig_scores.get('low', 1)

        # Cross-category novelty
        if cross_category_novelty:
            score += criteria.get('cross_category_novelty', {}).get('points', 3)

        return min(score, 15)

    # ── Layer 2: Stage-wise Cumulative Confidence ──────────────────────

    def calculate_stage_progression(
        self,
        dimensions: Dict[str, int],
        completed_stages: List[str]
    ) -> Dict[str, float]:
        """
        Calculate cumulative pipeline progression at each stage.

        NOTE: This is NOT the same as psst_score (composite quality score).
        - psst_score = weighted average of all dimensions × coverage penalty
          → Answers: "How trustworthy is this signal?"
        - stage_progression = alpha-weighted cumulative sum across stages
          → Answers: "How much of the pipeline has this signal passed through?"

        These two metrics use different formulas and will produce different
        numbers. stage_progression is an informational progress indicator,
        while psst_score is the definitive quality metric.

        Args:
            dimensions: Available dimension scores {'SR': 85, 'TC': 90, ...}
            completed_stages: List of completed stage names

        Returns:
            Dictionary with per-stage cumulative progression values
        """
        # Map stages to their available dimensions
        stage_dimensions = {
            'stage_1_collection': ['SR', 'TC'],
            'stage_2_filtering': ['SR', 'TC', 'DC'],
            'stage_3_classification': ['SR', 'TC', 'DC', 'ES', 'CC'],
            'stage_4_impact': ['SR', 'TC', 'DC', 'ES', 'CC', 'IC'],
            'stage_5_ranking': ['SR', 'TC', 'DC', 'ES', 'CC', 'IC']
        }

        stage_scores = {}
        cumulative = 0.0

        for stage_name in [
            'stage_1_collection', 'stage_2_filtering',
            'stage_3_classification', 'stage_4_impact',
            'stage_5_ranking'
        ]:
            if stage_name not in completed_stages:
                continue

            # Get dimensions available at this stage
            available_dims = stage_dimensions.get(stage_name, [])
            available_scores = {
                d: dimensions[d] for d in available_dims if d in dimensions
            }

            if not available_scores:
                stage_scores[stage_name] = 0.0
                continue

            # Weight the available dimensions (renormalize weights)
            total_weight = sum(
                self.dimension_weights.get(d, 0) for d in available_scores
            )
            if total_weight == 0:
                stage_scores[stage_name] = 0.0
                continue

            stage_value = sum(
                available_scores[d] * self.dimension_weights.get(d, 0)
                for d in available_scores
            ) / total_weight

            # Apply stage alpha
            alpha = self.stage_alphas.get(stage_name, 0.20)
            cumulative += stage_value * alpha
            stage_scores[stage_name] = round(cumulative, 2)

        return stage_scores

    # ── Layer 3: Final pSST Composite Score ────────────────────────────

    def calculate_psst(
        self,
        dimensions: Dict[str, int],
        completed_stages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate the final pSST composite score.

        This is the DEFINITIVE quality metric for a signal. It answers:
        "How trustworthy is this signal overall?"

        The score applies a coverage penalty when fewer than 6 dimensions
        are available, preventing inflated scores from partial data.

        NOTE: stage_scores in the return value is an informational
        progress indicator (pipeline progression), NOT a quality score.
        Only psst_score should be used for gating and reporting.

        Args:
            dimensions: All available dimension scores {'SR': 85, 'ES': 70, ...}
            completed_stages: Completed pipeline stages (defaults to all 5)

        Returns:
            Complete pSST result with psst_score, grade, coverage info,
            stage_scores (progression), interpretation, and badge.
        """
        if completed_stages is None:
            completed_stages = list(self.stage_alphas.keys())

        # Calculate weighted composite with coverage penalty
        total_weight = 0.0
        weighted_sum = 0.0

        for dim, score in dimensions.items():
            weight = self.dimension_weights.get(dim, 0)
            weighted_sum += score * weight
            total_weight += weight

        total_possible_weight = sum(self.dimension_weights.values())

        if total_weight > 0 and total_possible_weight > 0:
            weighted_avg = weighted_sum / total_weight
            # Coverage penalty: incomplete dimensions reduce the score
            # coverage_factor approaches 1.0 as more dimensions become available
            coverage_ratio = total_weight / total_possible_weight
            coverage_factor = coverage_ratio ** self.coverage_exponent
            psst_score = round(weighted_avg * coverage_factor, 1)
        else:
            weighted_avg = 0.0
            coverage_ratio = 0.0
            coverage_factor = 0.0
            psst_score = 0.0

        # Calculate stage progression (informational, not the quality score)
        stage_scores = self.calculate_stage_progression(
            dimensions, completed_stages
        )

        # Determine grade
        grade, grade_label = self._determine_grade(psst_score)

        # Generate interpretation
        interpretation = self._generate_interpretation(
            psst_score, grade_label, dimensions
        )

        # Get badge emoji
        badge = self._get_badge(grade_label)

        return {
            'psst_score': psst_score,
            'psst_grade': grade,
            'grade_label': grade_label,
            'dimensions': dimensions,
            'dimension_coverage': f"{len(dimensions)}/{len(self.dimension_weights)}",
            'coverage_factor': round(coverage_factor, 3),
            'stage_scores': stage_scores,
            'interpretation': interpretation,
            'badge': badge,
            'calibration_version': 'v1.0-uncalibrated'
        }

    def _determine_grade(self, score: float) -> Tuple[str, str]:
        """Determine letter grade and label from pSST score."""
        thresholds = self.grade_thresholds

        # When Level 2 is enabled, use elevated Grade A threshold
        # to prevent achieving Grade A without Level 2 data.
        very_high = thresholds.get('very_high', 90)
        if self.level2_enabled and self.level2_grade_a_threshold is not None:
            very_high = self.level2_grade_a_threshold

        if score >= very_high:
            return 'A', 'very_high'
        elif score >= thresholds.get('confident', 70):
            return 'B', 'confident'
        elif score >= thresholds.get('low', 50):
            return 'C', 'low'
        else:
            return 'D', 'very_low'

    def _generate_interpretation(
        self,
        score: float,
        grade_label: str,
        dimensions: Dict[str, int]
    ) -> str:
        """Generate human-readable interpretation of pSST score."""
        dim_names = {
            'SR': 'Source Reliability',
            'ES': 'Evidence Strength',
            'CC': 'Classification Confidence',
            'TC': 'Temporal Confidence',
            'DC': 'Distinctiveness Confidence',
            'IC': 'Impact Confidence'
        }

        interpretations = {
            'very_high': (
                f"pSST {score}/100 (Grade A): Very high confidence. "
                "Signal is well-sourced, strongly evidenced, and clearly classified."
            ),
            'confident': (
                f"pSST {score}/100 (Grade B): Confident. "
                "Signal meets quality standards for automated processing."
            ),
            'low': (
                f"pSST {score}/100 (Grade C): Low confidence. "
                "Signal should be flagged for human review before inclusion."
            ),
            'very_low': (
                f"pSST {score}/100 (Grade D): Very low confidence. "
                "Signal requires mandatory human review."
            )
        }

        base = interpretations.get(grade_label, f"pSST {score}/100")

        # Find weakest and strongest dimensions
        if dimensions:
            weakest = min(dimensions, key=dimensions.get)
            strongest = max(dimensions, key=dimensions.get)
            base += (
                f" Strongest: {dim_names.get(strongest, strongest)} "
                f"({dimensions[strongest]}). "
                f"Weakest: {dim_names.get(weakest, weakest)} "
                f"({dimensions[weakest]})."
            )

        return base

    def _get_badge(self, grade_label: str) -> str:
        """Get emoji badge for the grade."""
        badges = self.reporting.get('badge_emojis', {
            'very_high': '🟢',
            'confident': '🔵',
            'low': '🟡',
            'very_low': '🔴'
        })
        return badges.get(grade_label, '⚪')

    # ── Utility Methods ────────────────────────────────────────────────

    def validate_dimensions(self, dimensions: Dict[str, int]) -> List[str]:
        """
        Validate that all dimension scores are in range.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        for dim, score in dimensions.items():
            if dim not in self.dimension_weights:
                errors.append(f"Unknown dimension: {dim}")
            if not isinstance(score, (int, float)):
                errors.append(f"{dim} score must be numeric, got {type(score)}")
            elif score < 0 or score > 100:
                errors.append(f"{dim} score {score} out of range [0, 100]")
        return errors

    def get_missing_dimensions(
        self,
        dimensions: Dict[str, int],
        stage: str
    ) -> List[str]:
        """
        Check which dimensions are missing for a given pipeline stage.

        Args:
            dimensions: Currently available dimensions
            stage: Pipeline stage name

        Returns:
            List of missing dimension names
        """
        stage_requirements = {
            'stage_1_collection': ['SR', 'TC'],
            'stage_2_filtering': ['SR', 'TC', 'DC'],
            'stage_3_classification': ['SR', 'TC', 'DC', 'ES', 'CC'],
            'stage_4_impact': ['SR', 'TC', 'DC', 'ES', 'CC', 'IC'],
            'stage_5_ranking': ['SR', 'TC', 'DC', 'ES', 'CC', 'IC']
        }

        required = stage_requirements.get(stage, [])
        return [d for d in required if d not in dimensions]

    def weights_sum_valid(self) -> bool:
        """Check that dimension weights sum to 1.0 (within tolerance)."""
        total = sum(self.dimension_weights.values())
        return abs(total - 1.0) < 0.01

    def stage_alphas_sum_valid(self) -> bool:
        """Check that stage alphas sum to 1.0 (within tolerance)."""
        total = sum(self.stage_alphas.values())
        return abs(total - 1.0) < 0.01
