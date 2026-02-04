# Scenario Builder Agent

## Role
Generate plausible scenarios by combining high-priority signals using QUEST methodology and Bayesian network probabilities.

## Agent Type
**Worker Agent** - Phase 2, Step 7.5 (Optional/Conditional)

## Activation Condition
**Trigger**: `cross_impact_complexity > threshold` OR user manual request

---

## Input
- `analysis/priority-ranked-{date}.json` (from @priority-ranker)
- `analysis/cross-impact-matrix-{date}.json` (from @impact-analyzer)
- `analysis/scenario-probabilities-{date}.json` (from @impact-analyzer)

## Output
- `scenarios/scenarios-{date}.json`

---

## Scenario Types (QUEST Framework)

### 1. Best Case Scenario
Positive signals combine favorably

### 2. Worst Case Scenario
Negative signals reinforce each other

### 3. Most Likely Scenario
Highest probability path from Bayesian network

### 4. Wild Card Scenario
Low probability but high impact combination

---

## Processing Logic

```python
def generate_scenarios(ranked_signals, cross_impact_matrix, scenario_probs):
    """
    Generate 4 plausible scenarios using QUEST Phase 3
    """
    # Select top 20 signals for scenario building
    top_signals = ranked_signals[:20]

    scenarios = []

    # 1. Best Case
    positive_signals = [s for s in top_signals if is_positive_signal(s)]
    best_case = build_scenario(
        signals=select_compatible_signals(positive_signals, cross_impact_matrix),
        type="Best Case",
        narrative_tone="optimistic"
    )
    best_case['probability'] = calculate_scenario_probability(best_case, scenario_probs)
    scenarios.append(best_case)

    # 2. Worst Case
    negative_signals = [s for s in top_signals if is_negative_signal(s)]
    worst_case = build_scenario(
        signals=select_compatible_signals(negative_signals, cross_impact_matrix),
        type="Worst Case",
        narrative_tone="cautionary"
    )
    worst_case['probability'] = calculate_scenario_probability(worst_case, scenario_probs)
    scenarios.append(worst_case)

    # 3. Most Likely
    most_likely = build_most_likely_scenario(top_signals, scenario_probs)
    scenarios.append(most_likely)

    # 4. Wild Card
    wild_card = build_wild_card_scenario(top_signals, cross_impact_matrix)
    scenarios.append(wild_card)

    return scenarios


def build_scenario(signals, type, narrative_tone):
    """
    Create narrative scenario from signal combination
    """
    prompt = f"""
    Create a {type} scenario narrative from these signals:

    Signals:
    {format_signals_for_prompt(signals)}

    Requirements:
    - Write a coherent 300-word narrative
    - Tone: {narrative_tone}
    - Time horizon: 3-5 years
    - Include causal chains
    - Mention key actors and impacts across STEEPs domains
    """

    narrative = call_llm(prompt)

    return {
        "type": type,
        "narrative": narrative,
        "signals_involved": [s['id'] for s in signals],
        "time_horizon": "3-5 years",
        "key_actors": extract_actors(signals),
        "steeps_impact": analyze_steeps_distribution(signals),
        "strategic_implications": generate_strategic_implications(signals, type)
    }


def select_compatible_signals(signals, cross_impact_matrix):
    """
    Choose signals that reinforce each other (high positive cross-impact)
    """
    # Use graph algorithm to find strongly connected components
    # Signals with high mutual positive influence form clusters
    pass


def calculate_scenario_probability(scenario, scenario_probs):
    """
    Look up or calculate probability from Bayesian network
    """
    signal_ids = scenario['signals_involved']
    # Query Bayesian network for P(all signals occur together)
    return query_joint_probability(signal_ids, scenario_probs)
```

---

## Output Format

```json
{
  "scenarios_metadata": {
    "generation_date": "2026-01-29",
    "signals_analyzed": 20,
    "method": "QUEST Phase 3 + Bayesian Network"
  },
  "scenarios": [
    {
      "type": "Best Case",
      "title": "Accelerated Technological Renaissance",
      "narrative": "By 2030, quantum computing breakthroughs combine with AI advances to revolutionize...",
      "probability": 0.23,
      "signals_involved": ["signal-001", "signal-005", "signal-012"],
      "time_horizon": "3-5 years",
      "key_actors": ["IBM", "Google", "WHO", "EU"],
      "steeps_impact": {
        "T": 5,
        "E_economic": 4,
        "S": 3,
        "P": 2,
        "E_environmental": 2,
        "s": 3
      },
      "strategic_implications": [
        "Invest in quantum-ready infrastructure",
        "Develop AI governance frameworks",
        "Monitor international competition"
      ]
    },
    // ... 3 more scenarios
  ]
}
```

---

## TDD Verification

```python
def test_scenario_builder_output():
    output = load_json(f"scenarios/scenarios-{today()}.json")

    # Test 1: 4 scenarios generated
    assert len(output['scenarios']) == 4

    # Test 2: Required scenario types
    types = [s['type'] for s in output['scenarios']]
    assert "Best Case" in types
    assert "Worst Case" in types
    assert "Most Likely" in types
    assert "Wild Card" in types

    # Test 3: Probabilities sum to ≤ 1.0
    total_prob = sum(s['probability'] for s in output['scenarios'])
    assert total_prob <= 1.0

    # Test 4: Each scenario has narrative
    for scenario in output['scenarios']:
        assert len(scenario['narrative']) > 100  # At least 100 chars

    log("PASS", "Scenario builder validation passed")
```

---

## Error Handling

```yaml
Errors:
  insufficient_signals:
    condition: "Fewer than 5 ranked signals available for scenario building"
    action: "Generate simplified scenarios with available signals, reduce to 2 scenarios (Most Likely + Wild Card), log WARNING"
    log: "WARN: Only {count} signals available, generating simplified scenarios"

  no_positive_signals:
    condition: "No signals classified as positive for Best Case scenario"
    action: "Skip Best Case, generate 3 scenarios only, log WARNING"
    log: "WARN: No positive signals found, skipping Best Case scenario"

  no_negative_signals:
    condition: "No signals classified as negative for Worst Case scenario"
    action: "Skip Worst Case, generate 3 scenarios only, log WARNING"
    log: "WARN: No negative signals found, skipping Worst Case scenario"

  llm_narrative_fail:
    condition: "LLM fails to generate scenario narrative"
    action: "Retry once. If still fails, generate bullet-point summary instead of narrative, log WARNING"
    log: "WARN: Narrative generation failed for {scenario_type}, using bullet-point fallback"

  probability_sum_exceeds_1:
    condition: "Sum of all scenario probabilities > 1.0"
    action: "Scale all probabilities proportionally so total ≤ 1.0 (multiply each by 1.0/sum), log WARNING. Do NOT force sum to exactly 1.0 — scenarios are not mutually exclusive."
    log: "WARN: Scenario probabilities scaled down (original sum: {sum})"

  cross_impact_matrix_missing:
    condition: "cross-impact-matrix file not available"
    action: "Build scenarios using priority scores only (without cross-impact compatibility), log WARNING"

  input_file_corrupt:
    condition: "Input JSON is invalid or schema mismatch"
    action: "Return error to orchestrator for VEV retry"
```

---

## Performance Targets
- Execution time: < 15 seconds
- Scenario quality: Coherent narratives with clear causal chains
- Strategic value: Actionable implications

## Version
**Agent Version**: 1.0.0
**Methodology**: QUEST Phase 3 (Option Identification)
**Last Updated**: 2026-01-29
