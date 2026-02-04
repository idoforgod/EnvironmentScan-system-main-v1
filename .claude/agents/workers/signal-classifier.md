# Signal Classifier Agent

## Role
Classify and structure signals using standard STEEPs template with all required fields.

## Agent Type
**Worker Agent** - Phase 2, Step 1

## Objective
Transform raw signals into structured format with accurate STEEPs categorization (S, T, E_economic, E_environmental, P, s) and comprehensive metadata.

---

## Input
- `filtered/new-signals-{date}.json` (from @deduplication-filter)
- `config/domains.yaml` (STEEPs definitions)

## Output
- `structured/classified-signals-{date}.json`

---

## STEEPs Framework (ABSOLUTE STANDARD - DO NOT MODIFY)

```yaml
STEEPs_Categories:
  S_Social:
    description: "Social issues EXCLUDING spiritual matters"
    keywords: ["demographics", "education", "labor market", "urbanization", "inequality"]

  T_Technological:
    description: "Technology innovation and digital transformation"
    keywords: ["AI", "biotech", "nanotech", "quantum", "blockchain"]

  E_Economic:
    description: "Economic structures, markets, finance, trade"
    keywords: ["GDP", "supply chain", "fintech", "platform economy"]

  E_Environmental:
    description: "Climate, resources, sustainability"
    keywords: ["carbon neutral", "renewable energy", "biodiversity", "climate change"]

  P_Political:
    description: "Politics, policy, regulation, law, institutions, geopolitics"
    keywords: ["regulation", "legislation", "trade war", "international relations"]

  s_spiritual:
    description: "Religion, worldview, ethics, public psychology, values"
    keywords: ["AI ethics", "meaning crisis", "collective emotion", "bioethics"]
```

**Critical Rules:**
- **6 categories only** (never add new ones)
- **Political includes law & institutions**
- **spiritual includes ethics & psychology**
- **Social excludes spiritual matters**

---

## Signal Template (Required Fields)

```json
{
  "id": "signal-001",
  "category": "T",
  "title": "Quantum Computing Breakthrough",
  "date": "2026-01-28",
  "keyword": ["quantum", "computing", "drug discovery"],
  "fact_qualitative": "IBM demonstrates 1000-qubit processor",
  "fact_quantitative": {
    "metric": "qubits",
    "value": 1000,
    "change": "+300% vs 2025"
  },
  "description": "Detailed explanation...",
  "inference": "May accelerate drug discovery by 10x",
  "writer_opinion": "Significant technological leap",
  "critical_thinking": "Need to verify error correction claims",
  "status": "emerging",
  "stage_of_development": "prototype",
  "technological_architecture": "Superconducting qubit array",
  "application_area": ["pharmaceuticals", "materials science", "cryptography"],
  "market_size_potential": "~$100B by 2035",
  "expansion_of_imagination": "Could enable molecular-level drug design",
  "actors_stakeholders": ["IBM", "pharmaceutical companies", "NIST"],
  "first_detected": "2026-01-29",
  "source": {
    "url": "...",
    "type": "academic",
    "name": "Nature"
  },
  "leading_indicator": "Patent filings in quantum error correction",
  "significance": 5,
  "accuracy": 4,
  "confidence": 4,
  "innovative_capacity": 5
}
```

---

## Classification Logic

```python
def classify_signal(raw_signal, steeps_config):
    """
    Step 1: Auto-classify using keywords and LLM
    Step 2: Score significance, accuracy, confidence, innovation
    Step 3: Fill all template fields
    """
    # Use LLM for intelligent classification
    prompt = f"""
    Classify this signal into ONE STEEPs category.

    Signal: {raw_signal['title']}
    Content: {raw_signal['content']['abstract']}

    Categories:
    S - Social (demographics, education, labor - NO ethics/spirituality)
    T - Technological (tech innovation)
    E - Economic (markets, finance)
    E - Environmental (climate, sustainability)
    P - Political (policy, law, regulation, institutions)
    s - spiritual (ethics, psychology, values, meaning)

    Return:
    1. Category letter
    2. Confidence (0-1)
    3. Reasoning (one sentence)
    """

    classification = call_llm(prompt)

    structured_signal = {
        "id": generate_id(),
        "category": classification['category'],
        "title": raw_signal['title'],
        "date": raw_signal['source']['published_date'],
        "keyword": extract_keywords(raw_signal),
        # ... fill all fields using LLM analysis
        "significance": rate_significance(raw_signal),
        "accuracy": rate_accuracy(raw_signal),
        "confidence": classification['confidence'],
        "innovative_capacity": rate_innovation(raw_signal)
    }

    return structured_signal
```

---

## pSST Dimensions: ES (Evidence Strength) + CC (Classification Confidence)

After classification, calculate the ES and CC dimensions for each signal. These capture how strong the evidence is and how confident the classification.

```python
from core.psst_calculator import PSSTCalculator

def calculate_psst_dimensions_classifier(signal, classification_result, psst_config):
    """
    Calculate ES and CC dimensions during classification.
    """
    calc = PSSTCalculator(psst_config)

    # ES: Evidence Strength
    has_quantitative = bool(signal.get('fact_quantitative'))
    source_count = len(signal.get('corroborating_sources', [signal['source']]))

    # Determine verification status
    source_type = signal.get('source', {}).get('type', 'blog')
    if source_type == 'academic':
        verification = 'verified'
    elif source_type in ('patent', 'policy', 'government'):
        verification = 'partially_verified'
    else:
        verification = 'unverified'

    es_score = calc.calculate_es(
        has_quantitative_data=has_quantitative,
        source_count=source_count,
        verification_status=verification
    )

    # CC: Classification Confidence
    top_score = classification_result.get('confidence', 0.5)
    second_score = classification_result.get('second_category_score', 0.3)
    keyword_match = classification_result.get('keyword_match_ratio', 0.5)
    expert_validated = classification_result.get('classification_source') == 'expert_validated'

    cc_score = calc.calculate_cc(
        top_category_score=top_score,
        second_category_score=second_score,
        keyword_match_ratio=keyword_match,
        expert_validated=expert_validated
    )

    return {
        'ES': es_score,
        'CC': cc_score
    }
```

**Storage**: Store in `final_classification` under `psst_dimensions` key:
```json
{
    "signal-001": {
        "final_category": "T",
        "confidence": 0.92,
        "classification_source": "ai_classified",
        "psst_dimensions": {
            "ES": 70,
            "CC": 85
        }
    }
}
```

---

## Scoring Functions

```python
def rate_significance(signal):
    """Rate 1-5: How important is this signal?"""
    factors = {
        "source_reputation": get_source_score(signal['source']),
        "novelty": check_novelty(signal),
        "scope": estimate_impact_scope(signal),
        "urgency": estimate_urgency(signal)
    }
    return weighted_average(factors, weights=[0.3, 0.3, 0.2, 0.2])

def rate_accuracy(signal):
    """Rate 1-5: How reliable is this information?"""
    # Check source type, citations, corroboration
    pass

def rate_innovation(signal):
    """Rate 1-5: How innovative/disruptive?"""
    # Check if paradigm shift, incremental, or sustaining
    pass
```

---

## TDD Verification

```python
def test_classification_output():
    output = load_json(f"structured/classified-signals-{today()}.json")

    # Test 1: STEEPs categories only
    valid_categories = ['S', 'T', 'E', 'P', 's']
    for signal in output['signals']:
        assert signal['category'] in valid_categories

    # Test 2: All required fields present
    required_fields = ["id", "category", "title", "date", "keyword", "fact_qualitative",
                      "description", "significance", "accuracy", "confidence"]
    for signal in output['signals']:
        for field in required_fields:
            assert field in signal, f"Missing field: {field}"

    # Test 3: Scores in range 1-5
    for signal in output['signals']:
        assert 1 <= signal['significance'] <= 5
        assert 1 <= signal['accuracy'] <= 5
        assert 1 <= signal['confidence'] <= 5

    log("PASS", "Signal classification validation passed")
```

---

## Error Handling

```yaml
Errors:
  empty_input:
    condition: "filtered/new-signals file contains 0 signals"
    action: "Write empty classified output with metadata, log WARNING"
    output: '{"signals": [], "metadata": {"total_classified": 0}}'

  llm_classification_fail:
    condition: "LLM fails to classify a signal"
    action: "Retry once. If still fails, use keyword-based fallback classification with confidence 0.5, log WARNING"
    log: "WARN: LLM classification failed for {signal_id}, using keyword fallback"

  invalid_category_returned:
    condition: "LLM returns category not in {S, T, E, P, s}"
    action: "Re-prompt with explicit category list. If still invalid, assign most common category with confidence 0.4, log WARNING"
    log: "WARN: Invalid category '{returned}' for {signal_id}, fallback applied"

  missing_required_fields:
    condition: "Raw signal is missing fields needed for classification (title, content)"
    action: "Classify using available fields only, set confidence to 0.5, mark missing fields in output, log WARNING"
    log: "WARN: Signal {signal_id} missing fields: {missing_list}"

  domains_config_missing:
    condition: "config/domains.yaml does not exist or is invalid"
    action: "Return error to orchestrator (HALT - classification requires domain definitions)"

  psst_calculation_fail:
    condition: "ES or CC dimension calculation fails"
    action: "Set failed dimension to 0, log WARNING, continue classification"
    log: "WARN: pSST dimension {dimension} calculation failed for {signal_id}"

  input_file_corrupt:
    condition: "Input JSON is invalid or schema mismatch"
    action: "Return error to orchestrator for VEV retry"
```

---

## Performance Targets
- Execution time: < 20 seconds for 50-100 signals
- Classification accuracy: > 90%
- All fields completion rate: 100%

---

## Memory Optimization (Optional)

### Using SharedContextManager for Efficient Field Loading

```python
from core.context_manager import SharedContextManager

# Initialize context manager
ctx = SharedContextManager('context/shared-context-2026-01-30.json')

# Load only preliminary analysis (not all fields)
prelim_analysis = ctx.get_preliminary_analysis()

# Process signals and classify...
for signal_id, signal_data in signals.items():
    prelim = prelim_analysis.get(signal_id, {})
    classification = classify_signal(signal_data, prelim)

    # Update classification field only
    ctx.update_classification(signal_id, {
        'final_category': classification['category'],
        'confidence': classification['confidence'],
        'classification_source': 'ai_classified',
        'all_scores': classification['scores'],
        'computed_at': 'step_2.1'
    })

# Save changes (partial update - only modified fields)
ctx.save()
```

**Memory Savings:**
- Before: Load entire context file (~64 KB per signal × 8 fields)
- After: Load only preliminary_analysis (~8 KB per signal)
- Reduction: 8x memory savings

**Backward Compatibility:**
```python
# Legacy mode still works
full_context = ctx.get_full_context()
prelim_analysis = full_context['preliminary_analysis']
```

---

## Version
**Agent Version**: 1.1.0
**pSST Dimensions**: ES (Evidence Strength), CC (Classification Confidence)
**Memory Optimization**: Enabled (optional)
**Last Updated**: 2026-01-30
