# Deduplication Filter Agent

## Role
Filter out duplicate signals using multi-stage cascade approach, ensuring only genuinely new signals proceed to analysis phase.

## Agent Type
**Worker Agent** - Phase 1, Step 3

## Objective
Apply 4-stage cascade filtering to remove duplicates with >95% accuracy while maintaining 30% processing time reduction compared to baseline.

---

## Input

### Required Files
```yaml
inputs:
  raw_scan:
    path: "raw/daily-scan-{date}.json"
    from: "@multi-source-scanner"

  previous_signals:
    path: "context/previous-signals.json"
    from: "@archive-loader"

  thresholds_config:
    path: "config/thresholds.yaml"
    contains:
      stage_1_url_exact: 1.0
      stage_2_string_similarity: 0.9
      stage_3_semantic_similarity: 0.8
      stage_4_entity_matching: 0.85
```

---

## Output

### Primary Output
```yaml
output:
  file: "filtered/new-signals-{date}.json"
  format: "JSON"
  schema:
    filter_metadata:
      total_raw: Integer
      total_duplicates: Integer
      total_new: Integer
      filter_rate: Float
      stage_breakdown: Object
    new_signals: Array<Signal>
```

### Log Output
```yaml
log_file: "logs/duplicates-removed-{date}.log"
content:
  - List of removed duplicates with reasons
  - Confidence scores for each decision
  - Explainability notes for human review
```

### Example Output
```json
{
  "filter_metadata": {
    "total_raw": 247,
    "total_duplicates": 168,
    "total_new": 79,
    "filter_rate": 0.68,
    "stage_breakdown": {
      "stage_1_url": 85,
      "stage_2_string": 42,
      "stage_3_semantic": 31,
      "stage_4_entity": 10
    },
    "execution_time": 12.4,
    "confidence_distribution": {
      "high": 145,
      "medium": 18,
      "low": 5
    }
  },
  "new_signals": [...]
}
```

---

## Processing Logic: 4-Stage Cascade Filtering

### Stage 1: URL Exact Matching
**Threshold**: 100% (1.0)
**Method**: URL normalization + exact matching
**Action**: Exact URL match → immediate duplicate verdict

```python
def stage_1_url_exact_match(item, previous_signals_index):
    """
    Fastest filter: Check if URL already exists in database
    Expected: 35-40% of duplicates caught here
    """
    normalized_url = normalize_url(item['source']['url'])

    if normalized_url in previous_signals_index['by_url']:
        existing_id = previous_signals_index['by_url'][normalized_url]
        return {
            "is_duplicate": True,
            "stage": 1,
            "reason": "Exact URL match",
            "matched_signal": existing_id,
            "confidence": 1.0
        }

    return {"is_duplicate": False}
```

**Expected Performance**:
- Catches: 35-40% of duplicates
- Execution time: < 0.001s per item

---

### Stage 2: String Similarity
**Threshold**: 90% (0.9)
**Method**: Jaro-Winkler algorithm
**Action**: Similarity > 0.9 → mark as duplicate

```python
def stage_2_string_similarity(item, previous_signals):
    """
    Title/content string matching using Jaro-Winkler
    Expected: Additional 15-20% of duplicates caught
    """
    from jellyfish import jaro_winkler_similarity

    item_title = normalize_text(item['title'])

    for prev_signal in previous_signals:
        prev_title = normalize_text(prev_signal['title'])

        similarity = jaro_winkler_similarity(item_title, prev_title)

        if similarity > 0.9:
            return {
                "is_duplicate": True,
                "stage": 2,
                "reason": "High string similarity",
                "matched_signal": prev_signal['id'],
                "confidence": similarity,
                "details": {
                    "algorithm": "Jaro-Winkler",
                    "score": similarity
                }
            }

    return {"is_duplicate": False}
```

**Expected Performance**:
- Catches: Additional 15-20% of duplicates
- Execution time: < 0.01s per item

---

### Stage 3: Semantic Similarity
**Threshold**: 80% (0.8)
**Method**: TF-IDF or SBERT (Sentence-BERT)
**Action**: Similarity > 0.8 → mark as near-duplicate

**OPTIMIZED**: Uses pre-computed embeddings from shared-context (Phase 4 optimization)

```python
def stage_3_semantic_similarity(item, previous_signals, shared_context, use_sbert=True):
    """
    Semantic meaning comparison beyond literal text matching
    Captures nuanced similarities (e.g., different wording, same concept)
    Expected: Additional 10-15% of duplicates caught

    PHASE 4 OPTIMIZATION: Uses pre-computed embeddings from @multi-source-scanner
    instead of re-encoding with SBERT model (10x faster)
    """
    if use_sbert:
        # SBERT for better semantic understanding (OPTIMIZED)
        return stage_3_sbert_optimized(item, previous_signals, shared_context)
    else:
        # Fallback to TF-IDF
        return stage_3_tfidf(item, previous_signals)


def stage_3_sbert_optimized(item, previous_signals, shared_context):
    """
    OPTIMIZED: Use pre-computed SBERT embeddings from shared-context
    Avoids re-encoding each signal with SBERT model (10x faster)

    Handles Phase 4 deduplicated embeddings automatically
    (EmbeddingDeduplicator.get_embedding resolves references)
    """
    import numpy as np
    from core.embedding_deduplicator import EmbeddingDeduplicator

    # Get current item's embedding from shared-context
    signal_embeddings = shared_context.get("signal_embeddings", {})

    # Handle both deduplicated and regular embedding formats
    if "version" in signal_embeddings and signal_embeddings.get("version") == "1.0":
        # Phase 4 deduplicated format - use resolver
        item_embedding = EmbeddingDeduplicator.get_embedding(signal_embeddings, item['id'])
    else:
        # Legacy format - direct access
        item_emb_data = signal_embeddings.get(item['id'])
        item_embedding = np.array(item_emb_data["vector"]) if item_emb_data else None

    if item_embedding is None:
        # Fallback: compute embedding on-the-fly
        log("WARNING", f"No pre-computed embedding for {item['id']}, computing on-the-fly")
        return stage_3_sbert_legacy(item, previous_signals)

    # Normalize item embedding
    item_embedding = item_embedding / (np.linalg.norm(item_embedding) + 1e-8)

    # Compare with previous signals
    for prev_signal in previous_signals:
        prev_id = prev_signal['id']

        # Get previous signal's embedding (with Phase 4 deduplication support)
        if "version" in signal_embeddings and signal_embeddings.get("version") == "1.0":
            prev_embedding = EmbeddingDeduplicator.get_embedding(signal_embeddings, prev_id)
        else:
            prev_emb_data = signal_embeddings.get(prev_id)
            prev_embedding = np.array(prev_emb_data["vector"]) if prev_emb_data else None

        if prev_embedding is None:
            continue  # Skip if no embedding available

        # Normalize previous embedding
        prev_embedding = prev_embedding / (np.linalg.norm(prev_embedding) + 1e-8)

        # Cosine similarity (dot product of normalized vectors)
        similarity = np.dot(item_embedding, prev_embedding)

        if similarity > 0.8:
            return {
                "is_duplicate": True,
                "stage": 3,
                "reason": "Semantic similarity (SBERT - pre-computed)",
                "matched_signal": prev_signal['id'],
                "confidence": float(similarity),
                "details": {
                    "algorithm": "SBERT",
                    "model": "all-MiniLM-L6-v2",
                    "cosine_similarity": float(similarity),
                    "optimization": "phase4_precomputed"
                }
            }

    return {"is_duplicate": False}


def stage_3_sbert_legacy(item, previous_signals):
    """
    FALLBACK: Original SBERT method (compute embeddings on-the-fly)
    Used when pre-computed embeddings are not available
    """
    from sentence_transformers import SentenceTransformer, util

    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Combine title + abstract for better context
    item_text = f"{item['title']} {item['content']['abstract']}"
    item_embedding = model.encode(item_text, convert_to_tensor=True)

    for prev_signal in previous_signals:
        prev_text = f"{prev_signal['title']} {prev_signal.get('description', '')}"
        prev_embedding = model.encode(prev_text, convert_to_tensor=True)

        # Cosine similarity
        similarity = util.cos_sim(item_embedding, prev_embedding).item()

        if similarity > 0.8:
            return {
                "is_duplicate": True,
                "stage": 3,
                "reason": "Semantic similarity (SBERT - legacy)",
                "matched_signal": prev_signal['id'],
                "confidence": similarity,
                "details": {
                    "algorithm": "SBERT",
                    "model": "all-MiniLM-L6-v2",
                    "cosine_similarity": similarity,
                    "optimization": "none_legacy_mode"
                }
            }

    return {"is_duplicate": False}


def stage_3_tfidf(item, previous_signals):
    """
    Fallback: TF-IDF based similarity (faster but less accurate)
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer()

    item_text = f"{item['title']} {item['content']['abstract']}"
    corpus = [item_text] + [
        f"{s['title']} {s.get('description', '')}" for s in previous_signals
    ]

    tfidf_matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    max_similarity = max(similarities)
    if max_similarity > 0.8:
        matched_idx = similarities.argmax()
        return {
            "is_duplicate": True,
            "stage": 3,
            "reason": "Semantic similarity (TF-IDF)",
            "matched_signal": previous_signals[matched_idx]['id'],
            "confidence": max_similarity,
            "details": {
                "algorithm": "TF-IDF",
                "cosine_similarity": max_similarity
            }
        }

    return {"is_duplicate": False}
```

**Expected Performance**:
- Catches: Additional 10-15% of duplicates
- Execution time: < 0.1s per item (SBERT), < 0.05s (TF-IDF)

---

### Stage 4: Entity Matching
**Threshold**: 85% (0.85)
**Method**: Named Entity Recognition (NER)
**Criteria**: Same actor + same technology + same policy
**Action**: Entity overlap > 0.85 → mark as contextual duplicate

```python
def stage_4_entity_matching(item, previous_signals):
    """
    Deep contextual analysis using Named Entity Recognition
    Identifies same story even if wording is completely different
    Expected: Final 5-10% of duplicates caught
    """
    # Extract entities from current item
    item_entities = extract_entities(item)

    for prev_signal in previous_signals:
        prev_entities = extract_entities(prev_signal)

        # Calculate entity overlap
        overlap_score = calculate_entity_overlap(item_entities, prev_entities)

        if overlap_score > 0.85:
            return {
                "is_duplicate": True,
                "stage": 4,
                "reason": "Entity matching (contextual duplicate)",
                "matched_signal": prev_signal['id'],
                "confidence": overlap_score,
                "details": {
                    "item_entities": item_entities,
                    "matched_entities": prev_entities,
                    "overlap_score": overlap_score
                }
            }

    return {"is_duplicate": False}


def extract_entities(signal):
    """
    Extract named entities: Organizations, Technologies, Policies, Locations
    """
    text = f"{signal['title']} {signal.get('content', {}).get('abstract', '')}"

    # Use spaCy or similar NER tool
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)

    entities = {
        "organizations": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
        "technologies": extract_tech_keywords(text),  # Custom tech dictionary
        "policies": extract_policy_names(text),  # Custom policy patterns
        "locations": [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    }

    return entities


def calculate_entity_overlap(entities1, entities2):
    """
    Calculate Jaccard similarity across all entity types
    """
    def jaccard(set1, set2):
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0

    # Weighted average of overlaps
    weights = {"organizations": 0.4, "technologies": 0.3, "policies": 0.2, "locations": 0.1}

    overlap_scores = []
    for entity_type in weights.keys():
        set1 = set(entities1.get(entity_type, []))
        set2 = set(entities2.get(entity_type, []))
        overlap = jaccard(set1, set2)
        overlap_scores.append(overlap * weights[entity_type])

    return sum(overlap_scores)
```

**Expected Performance**:
- Catches: Final 5-10% of duplicates
- Execution time: < 0.2s per item

---

## Main Filter Pipeline

```python
def filter_pipeline(raw_items, previous_signals_index, previous_signals_list, shared_context=None):
    """
    Apply 4-stage cascade filtering
    Early exit optimization: If duplicate found in stage N, skip stages N+1 to 4

    PHASE 4 OPTIMIZATION: Accepts shared_context to use pre-computed embeddings
    """
    new_signals = []
    duplicates = []
    stage_counts = {"stage_1": 0, "stage_2": 0, "stage_3": 0, "stage_4": 0}

    # Load shared context if not provided (for backward compatibility)
    if shared_context is None:
        context_path = f"context/shared-context-{today()}.json"
        if file_exists(context_path):
            shared_context = load_json(context_path)
            log("INFO", "Loaded shared context for embedding optimization")
        else:
            shared_context = {}
            log("WARNING", "No shared context found - falling back to legacy SBERT")

    for item in raw_items:
        # Stage 1: URL Exact Match (fastest)
        result = stage_1_url_exact_match(item, previous_signals_index)
        if result["is_duplicate"]:
            duplicates.append({"item": item, "reason": result})
            stage_counts["stage_1"] += 1
            continue  # Early exit

        # Stage 2: String Similarity
        result = stage_2_string_similarity(item, previous_signals_list)
        if result["is_duplicate"]:
            duplicates.append({"item": item, "reason": result})
            stage_counts["stage_2"] += 1
            continue  # Early exit

        # Stage 3: Semantic Similarity (OPTIMIZED with pre-computed embeddings)
        result = stage_3_semantic_similarity(item, previous_signals_list, shared_context)
        if result["is_duplicate"]:
            duplicates.append({"item": item, "reason": result})
            stage_counts["stage_3"] += 1
            continue  # Early exit

        # Stage 4: Entity Matching
        result = stage_4_entity_matching(item, previous_signals_list)
        if result["is_duplicate"]:
            duplicates.append({"item": item, "reason": result})
            stage_counts["stage_4"] += 1
            continue  # Early exit

        # Not duplicate - add to new signals
        new_signals.append(item)

    return new_signals, duplicates, stage_counts
```

---

## pSST Dimension: DC (Distinctiveness Confidence)

After the cascade filter, calculate the DC dimension based on how far the signal passed through the deduplication stages. Signals that pass all 4 stages are considered truly unique.

```python
from core.psst_calculator import PSSTCalculator

def calculate_dc_dimension(item, filter_result, psst_config):
    """
    Calculate Distinctiveness Confidence (DC) for a signal
    based on its deduplication cascade result.
    """
    calc = PSSTCalculator(psst_config)

    # Determine cascade passage level
    if filter_result.get('is_duplicate', False):
        stage_passed = 'duplicate'
    else:
        # Signal passed all stages → truly unique
        stage_passed = 'passed_all_4'

    dc_score = calc.calculate_dc(dedup_stage_passed=stage_passed)

    return {'DC': dc_score}


def calculate_dc_for_near_duplicates(item, filter_result, psst_config):
    """
    For signals that were NOT removed but were close to duplicate
    thresholds, assign intermediate DC scores.
    """
    calc = PSSTCalculator(psst_config)

    # Check highest stage that came close to matching
    max_stage_reached = filter_result.get('max_stage_reached', 0)

    stage_mapping = {
        0: 'passed_all_4',  # Never matched anything
        1: 'passed_all_4',  # Stage 1 didn't match
        2: 'passed_3',      # Stage 2 had close match but below threshold
        3: 'passed_2',      # Stage 3 had close semantic match
        4: 'passed_1'       # Stage 4 had close entity match
    }

    stage_passed = stage_mapping.get(max_stage_reached, 'passed_all_4')
    dc_score = calc.calculate_dc(dedup_stage_passed=stage_passed)

    return {'DC': dc_score}
```

#### DC Level 2: True Novelty Assessment

After the cascade filter determines basic distinctiveness, apply Level 2 criteria to measure **true novelty** — how genuinely new information this signal contributes beyond surface-level uniqueness.

```python
import numpy as np

def calculate_dc_level2(item, previous_signals, shared_context, category_keyword_index):
    """
    Calculate DC Level 2 criteria for true novelty assessment.

    Returns dict with:
        semantic_distance: float (0-1) — cosine distance from nearest cluster centroid
        information_gain: float (0-1) — ratio of new keywords vs existing DB
        cross_category_novelty: bool — signal introduces concepts rare in its category
    """
    signal_embeddings = shared_context.get("signal_embeddings", {})

    # 1. Semantic Distance: SBERT embedding distance from nearest cluster centroid
    item_embedding = get_embedding(signal_embeddings, item['id'])
    if item_embedding is not None:
        # Compute centroid of existing signals in same category
        category = item.get('preliminary_category', 'T')
        cluster_embeddings = [
            get_embedding(signal_embeddings, s['id'])
            for s in previous_signals
            if s.get('preliminary_category') == category
        ]
        cluster_embeddings = [e for e in cluster_embeddings if e is not None]

        if cluster_embeddings:
            centroid = np.mean(cluster_embeddings, axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
            item_norm = item_embedding / (np.linalg.norm(item_embedding) + 1e-8)
            # Distance = 1 - cosine_similarity
            semantic_distance = 1.0 - float(np.dot(item_norm, centroid))
        else:
            semantic_distance = 1.0  # No prior signals in category → fully novel
    else:
        semantic_distance = 0.0  # Cannot assess without embedding

    # 2. Information Gain: ratio of new keywords not in existing DB
    item_keywords = set(item.get('content', {}).get('keywords', []))
    existing_keywords = set()
    for s in previous_signals:
        existing_keywords.update(s.get('content', {}).get('keywords', []))

    if item_keywords:
        new_keywords = item_keywords - existing_keywords
        information_gain = len(new_keywords) / len(item_keywords)
    else:
        information_gain = 0.0

    # 3. Cross-Category Novelty: keyword appears in < 5% of category signals
    category = item.get('preliminary_category', 'T')
    category_freq = category_keyword_index.get(category, {})
    total_in_category = max(sum(category_freq.values()), 1)

    novel_keywords = [
        kw for kw in item_keywords
        if category_freq.get(kw, 0) / total_in_category < 0.05
    ]
    cross_category_novelty = len(novel_keywords) >= 2  # At least 2 rare keywords

    return {
        'semantic_distance': round(semantic_distance, 4),
        'information_gain': round(information_gain, 4),
        'cross_category_novelty': cross_category_novelty
    }


def calculate_dc_with_level2(item, filter_result, psst_config,
                              previous_signals, shared_context, category_keyword_index):
    """
    Calculate DC dimension with Level 2 true novelty assessment.
    Falls back to Level 1 only if Level 2 computation fails.
    """
    calc = PSSTCalculator(psst_config)

    # Determine cascade passage level (Level 1)
    if filter_result.get('is_duplicate', False):
        stage_passed = 'duplicate'
    else:
        stage_passed = 'passed_all_4'

    # Level 2 assessment
    try:
        dc_level2 = calculate_dc_level2(
            item, previous_signals, shared_context, category_keyword_index
        )
    except Exception as e:
        log("WARNING", f"DC Level 2 failed for {item['id']}: {e}")
        dc_level2 = None

    dc_score = calc.calculate_dc(
        dedup_stage_passed=stage_passed,
        level2_data=dc_level2
    )

    return {
        'DC': dc_score,
        'dc_level2': dc_level2
    }
```

**Storage**: Store in `deduplication_analysis` under `psst_dimensions` key:
```json
{
    "signal-001": {
        "is_duplicate": false,
        "stage_matched": "none",
        "match_confidence": 0.0,
        "psst_dimensions": {
            "DC": 98,
            "dc_level2": {
                "semantic_distance": 0.72,
                "information_gain": 0.55,
                "cross_category_novelty": true
            }
        }
    }
}
```

---

## AI Confidence-Based Review Protocol

```python
def generate_review_recommendations(duplicates):
    """
    Categorize duplicates by confidence for human review
    """
    high_confidence = [d for d in duplicates if d['reason']['confidence'] > 0.9]
    medium_confidence = [d for d in duplicates if 0.7 <= d['reason']['confidence'] <= 0.9]
    low_confidence = [d for d in duplicates if d['reason']['confidence'] < 0.7]

    review_protocol = {
        "auto_approve": high_confidence,  # >0.9: Auto-approve removal
        "sample_review": medium_confidence[:int(len(medium_confidence) * 0.1)],  # 0.7-0.9: Sample 10%
        "full_review": low_confidence  # <0.7: Full human review required
    }

    return review_protocol
```

---

## TDD Verification

### Unit Tests (< 5 seconds)
```python
def test_deduplication_output():
    output = load_json(f"filtered/new-signals-{today()}.json")

    # Test 1: File exists
    assert output is not None, "Filtered file not created"

    # Test 2: Required fields
    assert "filter_metadata" in output
    assert "new_signals" in output

    # Test 3: Filter rate range
    filter_rate = output['filter_metadata']['filter_rate']
    assert 0.3 <= filter_rate <= 0.9, f"Filter rate {filter_rate} out of expected range"

    # Test 4: No duplicate URLs in output
    urls = [s['source']['url'] for s in output['new_signals']]
    assert len(urls) == len(set(urls)), "Duplicate URLs found in filtered output"

    # Test 5: Stage breakdown adds up
    stage_sum = sum(output['filter_metadata']['stage_breakdown'].values())
    assert stage_sum == output['filter_metadata']['total_duplicates']

    # Test 6: Log file created
    assert file_exists(f"logs/duplicates-removed-{today()}.log")

    # Test 7: Quality metrics (Precision target)
    # This requires ground truth, typically validated in integration test

    log("PASS", "Deduplication filter output validation passed")
```

---

## Error Handling

### Error Codes
- `E3001`: Previous signals index not loaded
- `E3002`: SBERT model loading failure
- `E3003`: NER model loading failure
- `E3004`: Invalid threshold configuration

### Retry Strategy
```yaml
retry_policy:
  max_attempts: 2
  backoff: linear  # 2s, 4s

  fallback_strategy:
    SBERT_failure:
      action: "Fall back to TF-IDF"
      log: "SBERT model unavailable, using TF-IDF"

    NER_failure:
      action: "Skip Stage 4"
      log: "NER unavailable, skipping entity matching"
```

---

## Performance Optimization

### Early Exit Strategy
- Stage 1 catches 35-40% → saves 3 stages for 40% of items
- Stage 2 catches additional 15-20% → saves 2 stages for 20% of items
- Total time saving: ~30% compared to running all 4 stages on all items

### Caching
```python
# Cache embeddings for previous signals (avoid recomputing)
embedding_cache = {}

def get_or_compute_embedding(text):
    if text in embedding_cache:
        return embedding_cache[text]
    else:
        embedding = model.encode(text)
        embedding_cache[text] = embedding
        return embedding
```

### Expected Performance
```yaml
performance_targets:
  execution_time: "10-15 seconds for 200-300 items"
  accuracy: "> 95% (Precision and Recall)"
  processing_speedup: "30% faster than single-stage approach"
```

---

## Quality Metrics

### Feedback Loop
```python
def collect_human_feedback(duplicates, human_decisions):
    """
    Collect human corrections for model retraining
    """
    corrections = []

    for dup in duplicates:
        if dup['item']['id'] in human_decisions:
            decision = human_decisions[dup['item']['id']]

            if decision == "not_duplicate":
                # Human overrode AI - collect as training data
                corrections.append({
                    "item": dup['item'],
                    "ai_decision": "duplicate",
                    "human_decision": "not_duplicate",
                    "stage": dup['reason']['stage'],
                    "confidence": dup['reason']['confidence']
                })

    # Save for weekly model retraining
    append_to_json("logs/quality-metrics/human-corrections.json", corrections)
```

### Weekly Calibration
```python
def weekly_threshold_calibration():
    """
    Adjust thresholds based on past week's performance
    """
    corrections = load_json("logs/quality-metrics/human-corrections.json")

    # Analyze correction patterns
    stage_3_false_positives = [c for c in corrections if c['stage'] == 3]

    if len(stage_3_false_positives) > 10:
        # Too many false positives in Stage 3 - increase threshold
        new_threshold = 0.85  # Up from 0.8
        log("INFO", f"Adjusting Stage 3 threshold to {new_threshold}")
        update_config("config/thresholds.yaml", "stage_3_semantic_similarity", new_threshold)
```

---

## Logging

```python
log_examples = {
    "START": "Deduplication filter started. Processing 247 raw items...",
    "INFO": "Loaded previous signals: 935 items with indexes",
    "INFO": "Stage 1 (URL): Removed 85 duplicates in 0.2s",
    "INFO": "Stage 2 (String): Removed 42 duplicates in 1.1s",
    "INFO": "Stage 3 (Semantic): Removed 31 duplicates in 8.7s",
    "INFO": "Stage 4 (Entity): Removed 10 duplicates in 2.4s",
    "INFO": "Total duplicates: 168 (68.0% filter rate)",
    "INFO": "New signals: 79 items",
    "INFO": "Confidence distribution: 145 high, 18 medium, 5 low",
    "WARNING": "5 low-confidence removals require human review",
    "SUCCESS": "Filtered output saved: filtered/new-signals-2026-01-29.json",
    "END": "Deduplication filter completed in 12.4 seconds"
}
```

---

## Dependencies

### Required Tools
- JSON parser
- String similarity library (jellyfish, python-Levenshtein)
- NLP libraries (spaCy, NLTK)

### Optional AI/ML Models
- Sentence-BERT (sentence-transformers)
- scikit-learn (TF-IDF)
- spaCy (NER)

### Configuration
- `config/thresholds.yaml` - Stage thresholds

---

## Integration Points

### Called By
- Orchestrator Agent (Phase 1, Step 3)

### Inputs From
- `@multi-source-scanner` (raw scan)
- `@archive-loader` (previous signals)

### Outputs Used By
- `@signal-classifier` (Step 2.1)
- Human review (Step 1.4, optional)

---

## Version
- **Agent Version**: 1.2.0
- **Compatible with**: Enhanced Environmental Scanning Workflow v1.0
- **pSST Dimensions**: DC (Distinctiveness Confidence)
- **pSST Level 2**: DC Level 2 (semantic distance, information gain, cross-category novelty)
- **Last Updated**: 2026-01-30
