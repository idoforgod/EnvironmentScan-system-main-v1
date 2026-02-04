# Priority Ranker Agent

## Role
Rank signals by priority using weighted multi-criteria scoring.

## Agent Type
**Worker Agent** - Phase 2, Step 3

## Objective
Calculate priority scores and rank signals for strategic decision-making.

## Constraints

- **Score range**: All `priority_score` values MUST be in range [1, 5]. Any score outside this range is a computation error.
- **Component score range**: Each component score (impact, probability, urgency, novelty) MUST be in range [1, 5].
- **Weight invariant**: Weights MUST sum to 1.0 (Impact 0.40 + Probability 0.30 + Urgency 0.20 + Novelty 0.10). Individual weight values are tunable by SIE within `core-invariants.yaml` bounds (±0.05 per cycle), but sum constraint is absolute.
- **Completeness**: Every signal in the input file MUST appear in the output. Dropping signals during ranking is forbidden.
- **Determinism**: Given identical input, ranking output MUST be identical. No randomization in scoring.
- **No manual override**: Priority scores are computed algorithmically only. Manual score injection is not permitted at this step (human adjustments occur at Step 2.5 checkpoint).
- **pSST range**: All `psst_score` values MUST be in range [0, 100]. Grade assignment MUST follow `thresholds.yaml` `grade_thresholds` (default: A≥95 when Level 2 enabled, B≥70, C≥50, D<50). Always read live config — do not hardcode.

---

## Input
- `analysis/impact-assessment-{date}.json` (from @impact-analyzer)

## Output
- `analysis/priority-ranked-{date}.json`

---

## Priority Scoring Formula

```python
def calculate_priority_score(signal, impact_data):
    """
    Priority = Impact(40%) + Probability(30%) + Urgency(20%) + Novelty(10%)
    """
    scores = {
        "impact": calculate_impact_score(signal, impact_data),
        "probability": calculate_probability_score(signal),
        "urgency": calculate_urgency_score(signal),
        "novelty": calculate_novelty_score(signal)
    }

    weights = {
        "impact": 0.40,
        "probability": 0.30,
        "urgency": 0.20,
        "novelty": 0.10
    }

    priority_score = sum(scores[k] * weights[k] for k in scores.keys())

    return {
        "signal_id": signal['id'],
        "priority_score": priority_score,
        "component_scores": scores,
        "rank": None  # Assigned after sorting
    }


def calculate_impact_score(signal, impact_data):
    """
    Based on:
    - Number of affected domains
    - 1st and 2nd order impact severity
    - Cross-impact influence (from matrix)
    """
    impact_assessment = find_impact(signal['id'], impact_data)

    domain_diversity = len(impact_assessment['affected_domains']) / 6  # Max 6 STEEPs
    impact_count = len(impact_assessment['first_order']) + len(impact_assessment['second_order'])
    influence_score = sum(abs(i['influence_score']) for i in impact_assessment['cross_impacts']) / 10

    return (domain_diversity + impact_count/10 + influence_score) / 3 * 5  # Normalize to 1-5


def calculate_probability_score(signal):
    """
    Based on:
    - Source reliability
    - Evidence strength
    - Expert validation (if available)
    """
    source_score = signal['accuracy']  # 1-5
    confidence = signal['confidence']  # 1-5

    return (source_score + confidence) / 2


def calculate_urgency_score(signal):
    """
    Based on:
    - Time horizon (how soon will this matter?)
    - Rate of change (how fast is this evolving?)
    """
    status_urgency = {
        "emerging": 3,
        "developing": 4,
        "mature": 2
    }

    return status_urgency.get(signal['status'], 3)


def calculate_novelty_score(signal):
    """
    Based on:
    - Innovative capacity rating
    - How different from existing signals
    """
    return signal['innovative_capacity']  # Already 1-5
```

---

## pSST Final Aggregation (Stage 5)

The priority ranker is the final pipeline stage where all 6 pSST dimensions are collected and the composite score is calculated. It gathers dimensions from all upstream agents.

```python
from core.psst_calculator import PSSTCalculator
from core.context_manager import SharedContextManager

def aggregate_psst_scores(signals, shared_context_path, psst_config):
    """
    Collect all 6 pSST dimensions from upstream agents and calculate
    the final composite pSST score for each signal.

    Dimension sources:
    - SR, TC → @multi-source-scanner (preliminary_analysis.psst_dimensions)
    - DC     → @deduplication-filter (deduplication_analysis.psst_dimensions)
    - ES, CC → @signal-classifier (final_classification.psst_dimensions)
    - IC     → @impact-analyzer (impact_analysis.psst_dimensions)
    """
    ctx = SharedContextManager(shared_context_path)
    calc = PSSTCalculator(psst_config)

    psst_results = {}

    for signal in signals:
        signal_id = signal['id']
        dimensions = {}

        # Collect SR, TC from scanner
        prelim = ctx.get_preliminary_analysis([signal_id])
        if signal_id in prelim:
            scanner_dims = prelim[signal_id].get('psst_dimensions', {})
            dimensions.update(scanner_dims)

        # Collect DC from dedup filter
        dedup = ctx.get_deduplication_analysis([signal_id])
        if signal_id in dedup:
            dedup_dims = dedup[signal_id].get('psst_dimensions', {})
            dimensions.update(dedup_dims)

        # Collect ES, CC from classifier
        classif = ctx.get_final_classification([signal_id])
        if signal_id in classif:
            class_dims = classif[signal_id].get('psst_dimensions', {})
            dimensions.update(class_dims)

        # Collect IC from impact analyzer
        impact = ctx.get_impact_analysis([signal_id])
        if signal_id in impact:
            impact_dims = impact[signal_id].get('psst_dimensions', {})
            dimensions.update(impact_dims)

        # Calculate final pSST score (all 5 stages completed)
        psst_result = calc.calculate_psst(
            dimensions=dimensions,
            completed_stages=[
                'stage_1_collection',
                'stage_2_filtering',
                'stage_3_classification',
                'stage_4_impact',
                'stage_5_ranking'
            ]
        )

        # Store in shared context
        ctx.update_psst_scores(signal_id, {
            'psst_score': psst_result['psst_score'],
            'psst_grade': psst_result['psst_grade'],
            'grade_label': psst_result['grade_label'],
            'dimensions': psst_result['dimensions'],
            'stage_scores': psst_result['stage_scores'],
            'calibration_version': psst_result['calibration_version'],
            'computed_at': 'step_2.3'
        })

        psst_results[signal_id] = psst_result

    ctx.save()
    return psst_results
```

**Integration with priority output**: Add pSST to each ranked signal:
```json
{
    "rank": 1,
    "signal_id": "signal-042",
    "title": "...",
    "category": "T",
    "priority_score": 4.72,
    "psst_score": 87.3,
    "psst_grade": "B",
    "component_scores": {...}
}
```

---

## Ranking

```python
def rank_signals(scored_signals):
    """
    Sort by priority score (descending)
    Assign ranks
    """
    sorted_signals = sorted(scored_signals, key=lambda x: x['priority_score'], reverse=True)

    for rank, signal in enumerate(sorted_signals, start=1):
        signal['rank'] = rank

    return sorted_signals
```

---

## Output Format

```json
{
  "ranking_metadata": {
    "total_signals": 79,
    "ranking_date": "2026-01-29",
    "criteria_weights": {
      "impact": 0.4,
      "probability": 0.3,
      "urgency": 0.2,
      "novelty": 0.1
    }
  },
  "ranked_signals": [
    {
      "rank": 1,
      "signal_id": "signal-042",
      "title": "...",
      "category": "T",
      "priority_score": 4.72,
      "component_scores": {
        "impact": 4.8,
        "probability": 4.5,
        "urgency": 5.0,
        "novelty": 4.2
      }
    },
    // ... more signals in descending order
  ]
}
```

---

## TDD Verification

```python
def test_priority_ranking():
    output = load_json(f"analysis/priority-ranked-{today()}.json")

    # Test 1: All signals ranked
    assert len(output['ranked_signals']) == total_signal_count

    # Test 2: Ranks are sequential (1, 2, 3, ...)
    ranks = [s['rank'] for s in output['ranked_signals']]
    assert ranks == list(range(1, len(ranks) + 1))

    # Test 3: Descending order by priority score
    scores = [s['priority_score'] for s in output['ranked_signals']]
    assert scores == sorted(scores, reverse=True)

    # Test 4: Scores in valid range (1-5)
    for signal in output['ranked_signals']:
        assert 1 <= signal['priority_score'] <= 5

    log("PASS", "Priority ranking validation passed")
```

---

## Error Handling

```yaml
Errors:
  missing_impact_data:
    condition: "Signal exists in input but has no corresponding impact assessment"
    action: "Assign default component scores (impact=2.5, probability=2.5, urgency=3, novelty=2.5), log WARNING"
    log: "WARN: Signal {signal_id} missing impact data, using defaults"

  score_out_of_range:
    condition: "Calculated priority_score < 1 or > 5"
    action: "Clamp to [1, 5], log WARNING with original value"
    log: "WARN: Signal {signal_id} score {original} clamped to {clamped}"

  empty_input:
    condition: "Input file contains 0 signals"
    action: "Write empty ranked output with metadata, log WARNING"
    output: '{"ranking_metadata": {...}, "ranked_signals": []}'

  psst_dimension_missing:
    condition: "One or more pSST dimensions unavailable from upstream"
    action: "Calculate pSST with available dimensions only, set missing to 0, log WARNING"
    log: "WARN: Signal {signal_id} missing pSST dimensions: {missing_list}"

  input_file_corrupt:
    condition: "Input JSON is invalid or schema mismatch"
    action: "Return error to orchestrator for VEV retry"
```

---

## Performance Targets
- Execution time: < 5 seconds
- Ranking accuracy: > 85% agreement with expert rankings (if available)

## Version
**Agent Version**: 1.1.0
**pSST Role**: Final aggregation of all 6 dimensions + composite score calculation
**Last Updated**: 2026-01-30
