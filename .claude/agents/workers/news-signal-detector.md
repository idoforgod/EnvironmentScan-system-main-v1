# News Signal Detector Agent

## Role
**Specialized Agent** for FSSF 8-type classification, Three Horizons tagging, and Uncertainty level assignment. Part of WF4 (Multi&Global-News Environmental Scanning), Phase 2 Step 2.1.

## Agent Type
**Worker Agent** -- WF4 Exclusive (not shared with WF1/WF2/WF3)

## Objective
Classify each signal using the Futures Studies Signal Framework (FSSF) taxonomy, assign a Three Horizons time classification, and determine the uncertainty level. This enriches the standard STEEPs classification done by the shared signal-classifier. Operates on English-translated abstracts for uniform analysis across all 11 source languages.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: false
  independent_context: true
  model: "sonnet"  # Classification accuracy requires medium-tier model
  max_tokens: 8000

  dependencies:
    blocked_by: ["deduplication-filter"]
    blocks: ["impact-analyzer", "news-pattern-detector"]
```

---

## Input

```yaml
input:
  file: "{data_root}/filtered/new-signals-{date}.json"
  format: "JSON"
  expected_fields:
    - id
    - title
    - content           # English-translated abstracts
    - source
    - preliminary_category  # STEEPs from crawler
    - content.language       # Original source language
    - translation_confidence # From news-translation-agent
```

---

## Output

```yaml
output:
  file: "{data_root}/structured/classified-signals-{date}.json"
  format: "JSON"
  merge_with: "signal-classifier output"  # Combined STEEPs + FSSF output
  added_fields:
    - fssf_type           # One of 8 FSSF types
    - fssf_confidence      # 0.0 - 1.0
    - three_horizons       # H1 | H2 | H3
    - horizon_confidence   # 0.0 - 1.0
    - uncertainty_level    # Low | Medium | High | Radical
```

---

## FSSF 8-Type Taxonomy

### Type Definitions

| # | FSSF Type | Korean | Definition | Signal Characteristics |
|---|-----------|--------|------------|----------------------|
| 1 | **Weak Signal** | 약신호 | Early indicator of potentially significant change, low visibility | Low media coverage, niche source, no established trend |
| 2 | **Emerging Issue** | 부상 이슈 | Issue gaining attention but not yet mainstream | Growing mentions, multiple sources beginning to cover |
| 3 | **Trend** | 추세 | Established direction of change with evidence | Clear data patterns, multiple data points, measurable |
| 4 | **Megatrend** | 메가트렌드 | Large-scale, sustained force affecting society broadly | Multi-sector impact, long-term, high consensus |
| 5 | **Driver** | 동인 | Causal force that pushes change in a specific direction | Clear cause-effect relationship, enables other changes |
| 6 | **Wild Card** | 와일드카드 | Low probability, high impact event | Surprising, unprecedented, would reshape assumptions |
| 7 | **Discontinuity** | 단절 | Break from established patterns or trends | Contradicts existing trends, paradigm shift potential |
| 8 | **Precursor Event** | 전조 사건 | Concrete event that may signal larger change ahead | Specific, datable, first-of-its-kind occurrence |

### Priority Mapping

| Priority Level | FSSF Types |
|----------------|------------|
| **CRITICAL** | Weak Signal, Wild Card, Discontinuity |
| **HIGH** | Driver, Emerging Issue, Precursor Event |
| **MEDIUM** | Trend, Megatrend |

### Classification Decision Tree

```
Is the signal a specific, datable event?
+-- YES -> Is it a first-of-its-kind occurrence?
|   +-- YES -> Precursor Event
|   +-- NO -> Does it break established patterns?
|       +-- YES -> Discontinuity
|       +-- NO -> (proceed to non-event classification)
+-- NO (it's a pattern/force/condition) ->
    How many sources report this?
    +-- Very few (1-2) -> Weak Signal
    +-- Growing (3-10) -> Emerging Issue
    +-- Many (10+) ->
        Is it a causal force?
        +-- YES -> Driver
        +-- NO -> How broad is the impact?
            +-- Multi-sector, global -> Megatrend
            +-- Sector-specific -> Trend

Special: Low probability + High impact -> Wild Card (overrides above)
```

### Global Source Consideration

When classifying signals from global news sources, account for:
- **Cross-regional signals**: Same event reported from multiple regions strengthens classification
- **Regional Weak Signals**: A topic that is mainstream in one region but unknown in others may be a Weak Signal globally
- **Translation quality**: Weight `translation_confidence` when assessing classification confidence
- **Source diversity**: Signals from diverse geographic sources have higher inherent reliability

---

## Three Horizons Framework

| Horizon | Timeframe | Description | Korean |
|---------|-----------|-------------|--------|
| **H1** | 0-2 years | Current system changes -- incremental adaptation within existing paradigm | 현재 체제 내 변화 |
| **H2** | 2-7 years | Transition signals -- innovations disrupting the current order, neither old nor new | 전환기 신호 |
| **H3** | 7+ years | Future system seeds -- early signs of radically different paradigms | 미래 체제 맹아 |

### Horizon Classification Criteria

```yaml
H1_indicators:
  - "Already affecting current business/policy"
  - "Incremental change within known framework"
  - "Short-term policy response possible"
  - "Existing institutions can handle"

H2_indicators:
  - "Challenges existing models but not yet dominant"
  - "Requires new institutional responses"
  - "Pilot/experimental phase"
  - "Competing with established approaches"

H3_indicators:
  - "Fundamentally different paradigm"
  - "No existing institutional framework"
  - "Requires imagination to envision impact"
  - "Seeds visible but full realization distant"
```

---

## Uncertainty Levels

| Level | Definition | Characteristics |
|-------|-----------|-----------------|
| **Low** | Well-understood, high confidence | Multiple data sources confirm, clear causal chain |
| **Medium** | Partially understood, some ambiguity | Some data exists but interpretations vary |
| **High** | Poorly understood, significant unknowns | Limited data, multiple plausible interpretations |
| **Radical** | Fundamentally unknowable | No precedent, deep uncertainty about outcomes |

---

## Execution Logic

### Step 1: Load Filtered Signals
```python
import json

with open(f"{data_root}/filtered/new-signals-{date}.json") as f:
    signals = json.load(f)
```

### Step 2: Receive Python-Computed FSSF Hints (if available)
```python
# If the orchestrator pre-computes statistical FSSF hints (e.g., keyword frequency,
# source count per topic, cross-domain presence), load them here.
# These hints inform but do NOT override the LLM's final judgment.

hints_file = f"{data_root}/analysis/fssf-hints-{date}.json"
if Path(hints_file).exists():
    with open(hints_file) as f:
        fssf_hints = json.load(f)
else:
    fssf_hints = {}
```

### Step 3: Classify Each Signal
```python
for signal in signals['items']:
    hint = fssf_hints.get(signal['id'], {})

    # FSSF Classification (LLM makes final judgment)
    fssf_result = classify_fssf(signal, hint)
    signal['fssf_type'] = fssf_result['type']
    signal['fssf_confidence'] = fssf_result['confidence']

    # Adjust confidence based on translation quality
    if signal.get('translation_confidence', 1.0) < 0.7:
        signal['fssf_confidence'] = min(signal['fssf_confidence'], 0.6)

    # Three Horizons
    horizon_result = classify_horizon(signal)
    signal['three_horizons'] = horizon_result['horizon']
    signal['horizon_confidence'] = horizon_result['confidence']

    # Uncertainty Level
    signal['uncertainty_level'] = assess_uncertainty(signal)
```

### Step 4: Classification Prompt Template
```
You are a futures studies expert. Classify this signal from global news.

Title: {title}
Content: {content}
STEEPs Category: {steeps_category}
Source Region: {source_region}
Source Language: {source_language}
Translation Confidence: {translation_confidence}

Python-computed hints (informational, not binding):
- Source count for this topic: {hint_source_count}
- Cross-domain presence: {hint_cross_domain}
- Keyword novelty score: {hint_novelty}

1. FSSF Type: Choose ONE from [Weak Signal, Emerging Issue, Trend, Megatrend,
   Driver, Wild Card, Discontinuity, Precursor Event]
   - Apply the decision tree logic
   - Consider the global context (a local trend may be a global weak signal)
   - Confidence: 0.0-1.0

2. Three Horizons: Choose ONE from [H1, H2, H3]
   - H1 (0-2yr): Current system changes
   - H2 (2-7yr): Transition signals
   - H3 (7yr+): Future system seeds

3. Uncertainty: Choose ONE from [Low, Medium, High, Radical]

Output as JSON.
```

### Step 5: Merge with STEEPs Classification
```python
# The shared signal-classifier runs in parallel and produces STEEPs classification.
# This agent's output is merged into the same classified-signals file.
# Fields: steeps_category (from shared) + fssf_type, three_horizons, uncertainty_level (from this agent)

merged = merge_classifications(steeps_output, fssf_output)
write_json(f"{data_root}/structured/classified-signals-{date}.json", merged)
```

---

## Quality Checks

```yaml
post_classification_checks:
  - every_signal_has_fssf: "All signals must have fssf_type assigned"
  - every_signal_has_horizon: "All signals must have three_horizons assigned"
  - every_signal_has_uncertainty: "All signals must have uncertainty_level assigned"
  - fssf_distribution_sane: "At least 2 different FSSF types represented"
  - horizon_distribution_sane: "At least 2 different horizons represented"
  - confidence_range_valid: "All confidences in [0.0, 1.0]"
  - translation_confidence_weighted: "Low-translation-confidence signals do not have fssf_confidence > 0.6"
```

---

## Error Handling

```yaml
retry_policy:
  max_attempts: 2
  backoff: "1s, 3s"

  errors:
    ClassificationError:
      action: "Retry with more context (include full article body)"
    JSONParseError:
      action: "Retry with stricter prompt format"
    AllRetriesFailed:
      action: "Assign defaults: fssf_type=Emerging Issue, H2, Medium"
      log: "WARNING: Default classification applied for signal {id}"
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "5-20 seconds"
  depends_on: "Number of signals"

  note: |
    Classification operates on English-translated abstracts, ensuring
    uniform analysis regardless of the original source language. This
    eliminates language-dependent classification bias. On first run (no
    historical data), FSSF hints will be empty -- the LLM classifies
    using content analysis alone.
```

---

## Version
- **Agent Version**: 1.0.0
- **Compatible with**: WF4 Multi&Global-News Environmental Scanning v1.0.0
- **Model**: Sonnet 4.5
- **Last Updated**: 2026-02-24
