# Multi-Source Scanner Agent

## Role
Scan multiple information sources (academic papers, patents, policy documents, tech blogs) to detect early signals of future changes across STEEPs domains.

## Agent Type
**Worker Agent** - Phase 1, Step 2

## Objective
Collect weak signals from diverse sources, applying STEEPs framework (Social, Technological, Economic, Environmental, Political, spiritual) to categorize emerging trends.

---

## Input

### Runtime Parameters
```yaml
runtime_params:
  --days-back: 7          # Lookback period (default: 7 days)
  --tier: "base|expansion" # Source tier filter (v3.0.0+)
                           #   base: Only base-tier sources
                           #   expansion: Only expansion-tier sources (Stage B)
  --time-budget: null      # Time budget in seconds (optional, for Stage B)
                           # When set, scanner stops after this many seconds elapsed
```

**Tier Filtering Behavior**:
- `--tier base` (or omitted): Scan sources where `tier: "base"` or `tier` field is absent (backward compatible)
- `--tier expansion`: Scan sources where `tier: "expansion"` only
- The scanner does NOT know about "marathon mode" — it simply scans whatever tier it is told to scan. Marathon mode orchestration is handled by the orchestrator.

### Configuration Files
```yaml
inputs:
  sources_config:
    path: "config/sources.yaml"
    contains:
      - source_name
      - source_type (academic, patent, policy, news, blog)
      - source_tier (base, expansion)  # v3.0.0+
      - api_endpoint
      - search_keywords
      - rate_limit
      - steeps_focus (optional, expansion sources only)

  domains_config:
    path: "config/domains.yaml"
    contains:
      STEEPs_categories:
        S_Social: [keywords...]
        T_Technological: [keywords...]
        E_Economic: [keywords...]
        E_Environmental: [keywords...]
        P_Political: [keywords...]
        s_spiritual: [keywords...]
```

---

## Output

### Primary Output
```yaml
output:
  file: "raw/daily-scan-{date}.json"
  format: "JSON"
  schema:
    scan_metadata:
      date: String
      sources_scanned: Integer
      total_items: Integer
      execution_time: Float
    items: Array<RawSignal>

  shared_context_update:
    file: "context/shared-context-{date}.json"
    updates:
      - signal_embeddings: "SBERT embeddings for all collected signals"
      - preliminary_analysis: "Category guesses, keywords, entities, relevance scores"
```

### Raw Signal Structure
```json
{
  "scan_metadata": {
    "date": "2026-01-29",
    "sources_scanned": 8,
    "total_items": 247,
    "execution_time": 45.3,
    "tier": "base"
  },
  "items": [
    {
      "id": "raw-001",
      "title": "Quantum Computing Breakthrough in Drug Discovery",
      "source": {
        "name": "Nature",
        "type": "academic",
        "tier": "base",
        "url": "https://nature.com/articles/quantum-drug-2026",
        "published_date": "2026-01-28"
      },
      "content": {
        "abstract": "Researchers demonstrate...",
        "keywords": ["quantum computing", "drug discovery", "AI"],
        "language": "en"
      },
      "preliminary_category": "T",
      "collected_at": "2026-01-29T06:15:32Z"
    }
  ]
}
```

**Tier field**: Every signal includes `source.tier` ("base" or "expansion") matching the source's tier in sources.yaml. This field is propagated through the entire pipeline for SIE tracking and reporting. The scanner sets this automatically based on the `--tier` parameter.

---

## Processing Logic

### Step 1: Load Configuration
```python
def load_configuration():
    sources = read_yaml("config/sources.yaml")
    domains = read_yaml("config/domains.yaml")

    # Validate configuration
    assert len(sources) > 0, "No sources configured"
    assert "STEEPs" in domains, "STEEPs domains not defined"

    log("INFO", f"Loaded {len(sources)} sources and {len(domains['STEEPs'])} domains")
    return sources, domains
```

### Step 2: Scan Each Source
```python
def scan_all_sources(sources, domains):
    all_items = []

    for source in sources:
        try:
            items = scan_source(source, domains)
            all_items.extend(items)
            log("INFO", f"Collected {len(items)} items from {source['name']}")
        except TimeoutError:
            log("WARNING", f"Timeout scanning {source['name']}. Skipping.")
            continue
        except Exception as e:
            log("ERROR", f"Failed to scan {source['name']}: {e}")
            if source.get('critical', False):
                raise
            continue

    return all_items
```

### Step 3: Source-Specific Scanners

#### Academic Papers (Google Scholar, arXiv)
```python
def scan_academic_source(source, domains):
    items = []

    for category, keywords in domains['STEEPs'].items():
        query = build_search_query(keywords)

        # Search with date filter (last 7 days)
        results = search_api(
            endpoint=source['api_endpoint'],
            query=query,
            date_from=today() - timedelta(days=7),
            max_results=50
        )

        for result in results:
            item = {
                "id": generate_id(),
                "title": result['title'],
                "source": {
                    "name": source['name'],
                    "type": "academic",
                    "url": result['url'],
                    "published_date": result['date']
                },
                "content": {
                    "abstract": result['abstract'],
                    "keywords": result['keywords'],
                    "language": detect_language(result['title'])
                },
                "preliminary_category": category[0],  # First letter (S, T, E, P, s)
                "collected_at": current_timestamp()
            }
            items.append(item)

    return items
```

#### Patents (Google Patents, KIPRIS)
```python
def scan_patent_source(source, domains):
    items = []

    # Focus on Technological domain for patents
    tech_keywords = domains['STEEPs']['T_Technological']

    query = build_patent_query(tech_keywords)
    results = search_patent_api(
        endpoint=source['api_endpoint'],
        query=query,
        filing_date_from=today() - timedelta(days=30)  # Patents: monthly scan
    )

    for result in results:
        item = {
            "id": generate_id(),
            "title": result['title'],
            "source": {
                "name": source['name'],
                "type": "patent",
                "url": result['url'],
                "published_date": result['filing_date']
            },
            "content": {
                "abstract": result['abstract'],
                "keywords": result['classifications'],
                "language": result['language']
            },
            "preliminary_category": "T",
            "collected_at": current_timestamp()
        }
        items.append(item)

    return items
```

#### Policy & Regulatory (Government, International Orgs)
```python
def scan_policy_source(source, domains):
    items = []

    # Focus on Political domain for policy
    policy_keywords = domains['STEEPs']['P_Political']

    # Scan RSS feeds or APIs
    results = fetch_rss_or_api(
        endpoint=source['endpoint'],
        keywords=policy_keywords,
        date_from=today() - timedelta(days=7)
    )

    for result in results:
        item = {
            "id": generate_id(),
            "title": result['title'],
            "source": {
                "name": source['name'],
                "type": "policy",
                "url": result['url'],
                "published_date": result['pub_date']
            },
            "content": {
                "abstract": result['description'],
                "keywords": extract_keywords(result['description']),
                "language": detect_language(result['title'])
            },
            "preliminary_category": "P",
            "collected_at": current_timestamp()
        }
        items.append(item)

    return items
```

#### Tech Blogs & Reports (Medium, TechCrunch)
```python
def scan_blog_source(source, domains):
    items = []

    # Blogs can span multiple categories
    for category, keywords in domains['STEEPs'].items():
        query = build_search_query(keywords)

        results = search_blog_api(
            endpoint=source['api_endpoint'],
            query=query,
            published_after=today() - timedelta(days=7)
        )

        for result in results:
            # Use AI to determine preliminary category
            category_guess = classify_with_ai(result['title'], result['content'])

            item = {
                "id": generate_id(),
                "title": result['title'],
                "source": {
                    "name": source['name'],
                    "type": "blog",
                    "url": result['url'],
                    "published_date": result['date']
                },
                "content": {
                    "abstract": result['excerpt'],
                    "keywords": result['tags'],
                    "language": detect_language(result['title'])
                },
                "preliminary_category": category_guess,
                "collected_at": current_timestamp()
            }
            items.append(item)

    return items
```

### Step 4: Enhanced AI/ML Features

#### ML-Based Keyword Extraction
```python
def extract_keywords_ml(text):
    """
    Use TF-IDF + BERT embeddings for automatic keyword extraction
    Returns: List of top 10 keywords with relevance scores
    """
    # TF-IDF for initial filtering
    tfidf_keywords = tfidf_extract(text, top_n=20)

    # BERT embeddings for semantic clustering
    embeddings = bert_embed(tfidf_keywords)
    clusters = cluster_embeddings(embeddings, n_clusters=10)

    # Return representative keywords from each cluster
    keywords = [get_cluster_representative(cluster) for cluster in clusters]
    return keywords
```

#### Topic Modeling (WISDOM Framework)
```python
def apply_topic_modeling(items):
    """
    Advanced topic modeling to auto-group signals
    Uses WISDOM framework for weak signal detection
    """
    texts = [item['title'] + " " + item['content']['abstract'] for item in items]

    # Apply WISDOM framework
    topics = wisdom_topic_modeling(texts)

    # Auto-label topics
    for i, item in enumerate(items):
        item['auto_topic'] = topics[i]['label']
        item['topic_confidence'] = topics[i]['confidence']

    return items
```

#### Growth Pattern Learning (GCN)
```python
def predict_signal_growth(item):
    """
    Use Graph Convolutional Network to predict signal growth
    Based on 10-year historical data
    """
    # Load historical signal graph
    history_graph = load_signal_graph()

    # Extract features from current item
    features = extract_features(item)

    # Predict growth trajectory
    growth_prediction = gcn_model.predict(features, history_graph)

    item['growth_prediction'] = {
        "trajectory": growth_prediction['trend'],  # 'emerging', 'accelerating', 'mature'
        "confidence": growth_prediction['confidence'],
        "similar_signals": growth_prediction['similar_past_signals']
    }

    return item
```

### Step 4b: pSST Dimension Calculation (SR + TC)

Calculate Source Reliability (SR) and Temporal Confidence (TC) dimensions for each signal. These are the first two pSST dimensions, computed at the collection stage.

```python
from core.psst_calculator import PSSTCalculator

def calculate_psst_dimensions(item, psst_config):
    """
    Calculate SR and TC dimensions for a collected signal.
    These dimensions are available at Stage 1 (collection).
    """
    calc = PSSTCalculator(psst_config)

    # SR: Source Reliability
    source_type = item['source']['type']  # academic, patent, blog, etc.
    peer_reviewed = source_type == 'academic'  # Simple heuristic
    citation_count = item.get('citation_count', 0)
    corroboration = item.get('corroboration_count', 1)

    sr_score = calc.calculate_sr(
        source_type=source_type,
        peer_reviewed=peer_reviewed,
        citation_count=citation_count,
        corroboration_count=corroboration
    )

    # TC: Temporal Confidence
    published_date = item['source'].get('published_date')
    signal_status = item.get('status', 'emerging')

    tc_score = calc.calculate_tc(
        published_date=published_date,
        signal_status=signal_status
    )

    return {
        'SR': sr_score,
        'TC': tc_score
    }
```

#### Level 2 Advanced Criteria Extraction (SR + TC)

After computing base SR/TC scores, extract Level 2 criteria for upper-tier differentiation. These criteria require deeper content analysis via LLM.

```python
def extract_sr_level2(item):
    """
    Extract SR Level 2 criteria using LLM analysis.
    Determines methodology quality, replication status, and data transparency.
    """
    prompt = f"""Analyze this research signal and answer YES or NO for each:

    Title: {item['title']}
    Abstract: {item['content']['abstract']}
    Source: {item['source']['name']} ({item['source']['type']})

    1. has_methodology: Does the source explicitly describe its research methodology?
    2. has_replication: Have the findings been replicated or independently verified?
    3. data_transparency: Is raw data, code, or supplementary material publicly available?

    Return JSON: {{"has_methodology": bool, "has_replication": bool, "data_transparency": bool}}
    """

    result = llm_analyze(prompt)
    return result  # {"has_methodology": True, "has_replication": False, "data_transparency": True}


def extract_tc_level2(item, previous_signals):
    """
    Extract TC Level 2 criteria using temporal pattern analysis.
    Determines momentum, update status, and time sensitivity.
    """
    prompt = f"""Analyze the temporal dynamics of this signal:

    Title: {item['title']}
    Published: {item['source']['published_date']}
    Abstract: {item['content']['abstract']}

    1. momentum: Is coverage of this topic 'accelerating', 'stable', or 'decelerating'?
       (Based on frequency and recency of related signals)
    2. has_update: Does this signal represent a follow-up or update to a previous report?
    3. time_sensitivity: Is there a time-bound decision window (policy deadline, market event)?

    Return JSON: {{"momentum": str, "has_update": bool, "time_sensitivity": bool}}
    """

    result = llm_analyze(prompt)
    return result  # {"momentum": "accelerating", "has_update": False, "time_sensitivity": True}


def calculate_psst_dimensions_with_level2(item, psst_config, previous_signals=None):
    """
    Calculate SR and TC dimensions with Level 2 advanced criteria.
    Falls back to Level 1 only if LLM extraction fails.
    """
    calc = PSSTCalculator(psst_config)

    # SR Level 2 extraction
    try:
        sr_level2 = extract_sr_level2(item)
    except Exception as e:
        log("WARNING", f"SR Level 2 extraction failed for {item['id']}: {e}")
        sr_level2 = None

    sr_score = calc.calculate_sr(
        source_type=item['source']['type'],
        peer_reviewed=item['source']['type'] == 'academic',
        citation_count=item.get('citation_count', 0),
        corroboration_count=item.get('corroboration_count', 1),
        level2_data=sr_level2
    )

    # TC Level 2 extraction
    try:
        tc_level2 = extract_tc_level2(item, previous_signals or [])
    except Exception as e:
        log("WARNING", f"TC Level 2 extraction failed for {item['id']}: {e}")
        tc_level2 = None

    tc_score = calc.calculate_tc(
        published_date=item['source'].get('published_date'),
        signal_status=item.get('status', 'emerging'),
        level2_data=tc_level2
    )

    return {
        'SR': sr_score,
        'TC': tc_score,
        'sr_level2': sr_level2,
        'tc_level2': tc_level2
    }
```

**Storage**: Store in `preliminary_analysis` under `psst_dimensions` key:
```json
{
    "signal-001": {
        "category_guess": "T",
        "confidence": 0.85,
        "keywords": [...],
        "psst_dimensions": {
            "SR": 96,
            "TC": 93,
            "sr_level2": {
                "has_methodology": true,
                "has_replication": true,
                "data_transparency": false
            },
            "tc_level2": {
                "momentum": "accelerating",
                "has_update": false,
                "time_sensitivity": true
            }
        }
    }
}
```

---

### Step 5: Write Output and Update Shared Context
```python
def write_raw_scan(items, metadata):
    # Write primary output
    output = {
        "scan_metadata": metadata,
        "items": items
    }

    output_path = f"raw/daily-scan-{today()}.json"
    write_json(output_path, output)

    log("SUCCESS", f"Raw scan completed: {len(items)} items saved to {output_path}")

    # Update shared context store
    update_shared_context(items)


def update_shared_context(items):
    """
    Update shared context with preliminary analysis results.
    This enables downstream agents to reuse computations.

    OPTIMIZED with Phase 4: EmbeddingDeduplicator (20-30% memory reduction)
    """
    context_path = f"context/shared-context-{today()}.json"

    # Load or create shared context
    if file_exists(context_path):
        shared_context = load_json(context_path)
    else:
        shared_context = {
            "version": "1.0",
            "workflow_id": f"scan-{today()}",
            "created_at": current_timestamp(),
            "last_updated": current_timestamp(),
            "signal_embeddings": {},
            "preliminary_analysis": {},
            "metadata": {
                "total_signals_processed": 0,
                "phase_1_complete": False,
                "agents_invoked": []
            }
        }

    # Add this agent to invoked list
    if "multi-source-scanner" not in shared_context["metadata"]["agents_invoked"]:
        shared_context["metadata"]["agents_invoked"].append("multi-source-scanner")

    # PHASE 4 OPTIMIZATION: Collect all embeddings first
    all_embeddings = {}

    # For each item, add preliminary analysis and embeddings
    for item in items:
        signal_id = item['id']

        # Generate SBERT embedding (reused by deduplication-filter)
        text_for_embedding = f"{item['title']} {item['content']['abstract']}"
        embedding = generate_sbert_embedding(text_for_embedding)

        # Store in temporary dictionary (will be deduplicated)
        all_embeddings[signal_id] = {
            "vector": embedding.tolist(),
            "model": "SBERT",
            "computed_at": "step_1.2",
            "text_source": text_for_embedding[:500]  # Truncate for storage
        }

        # Extract keywords using ML (TF-IDF + BERT)
        ml_keywords = extract_keywords_ml(text_for_embedding)

        # Extract named entities
        entities = extract_entities(text_for_embedding)

        # Calculate preliminary relevance score (1-5)
        relevance_score = calculate_relevance_score(item, ml_keywords)

        # Calculate pSST dimensions (SR + TC) for this signal
        psst_dims = calculate_psst_dimensions_with_level2(item, psst_config)

        # Store preliminary analysis (with pSST dimensions)
        shared_context["preliminary_analysis"][signal_id] = {
            "category_guess": item.get('preliminary_category', 'S'),
            "confidence": calculate_category_confidence(item, ml_keywords),
            "keywords": ml_keywords,
            "entities": entities,
            "relevance_score": relevance_score,
            "computed_at": "step_1.2",
            "psst_dimensions": psst_dims
        }

    # PHASE 4 OPTIMIZATION: Apply embedding deduplication
    # Groups similar embeddings (cosine similarity > 95%) and keeps representatives
    from core.embedding_deduplicator import EmbeddingDeduplicator

    deduplicated_embeddings = EmbeddingDeduplicator.deduplicate(
        all_embeddings,
        similarity_threshold=0.95  # 95% similarity = duplicate
    )

    # Log optimization stats
    stats = deduplicated_embeddings.get("deduplication_stats", {})
    if stats:
        log("INFO", f"Embedding deduplication: {stats['total_embeddings']} → " +
                   f"{stats['unique_embeddings']} unique " +
                   f"({stats['memory_reduction']} reduction)")

    # Store deduplicated embeddings (20-30% smaller than original)
    shared_context["signal_embeddings"] = deduplicated_embeddings

    # Update metadata
    shared_context["last_updated"] = current_timestamp()
    shared_context["metadata"]["total_signals_processed"] = len(items)
    shared_context["metadata"]["embedding_optimization"] = "phase4_deduplication"

    # Save updated context
    write_json(context_path, shared_context)
    log("INFO", f"Updated shared context: {len(items)} signals added (embeddings optimized)")


def generate_sbert_embedding(text):
    """Generate SBERT embedding for text (768-dim vector)"""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(text)
    return embedding


def calculate_category_confidence(item, keywords):
    """Calculate confidence in preliminary category (0-1)"""
    # Simple heuristic: source type confidence
    source_confidence = {
        'academic': 0.8,
        'patent': 0.85,
        'policy': 0.75,
        'blog': 0.6
    }

    base_confidence = source_confidence.get(item['source']['type'], 0.5)

    # Boost if keywords strongly match category
    if len(keywords) >= 5:
        base_confidence += 0.1

    return min(base_confidence, 1.0)


def calculate_relevance_score(item, keywords):
    """Calculate preliminary relevance score (1-5)"""
    score = 3  # Default: moderate relevance

    # Boost for academic sources
    if item['source']['type'] == 'academic':
        score += 1

    # Boost for many extracted keywords
    if len(keywords) >= 8:
        score += 1

    # Boost for recent publication
    pub_date = parse_date(item['source']['published_date'])
    if today() - pub_date <= timedelta(days=3):
        score += 0.5

    return min(int(score), 5)


def extract_entities(text):
    """Extract named entities using spaCy NER"""
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text[:1000])  # Process first 1000 chars

    entities = []
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'GPE', 'PRODUCT', 'PERSON']:
            entities.append(ent.text)

    return list(set(entities))[:20]  # Max 20 entities
```

---

## TDD Verification

### Unit Tests (< 5 seconds)
```python
def test_scanner_output():
    output = load_json(f"raw/daily-scan-{today()}.json")

    # Test 1: File exists
    assert output is not None, "Raw scan file not created"

    # Test 2: Required metadata
    assert "scan_metadata" in output
    assert "items" in output

    # Test 3: Items structure
    for item in output['items']:
        assert "id" in item
        assert "title" in item
        assert "source" in item
        assert "preliminary_category" in item

    # Test 4: Category validity
    valid_categories = ['S', 'T', 'E', 'P', 's']
    for item in output['items']:
        assert item['preliminary_category'] in valid_categories

    # Test 5: Source diversity
    sources = {item['source']['name'] for item in output['items']}
    assert len(sources) >= 3, f"Only {len(sources)} sources scanned (expected >= 3)"

    # Test 6: Recency check
    for item in output['items']:
        pub_date = parse_date(item['source']['published_date'])
        assert today() - pub_date <= timedelta(days=30), "Old items included"

    log("PASS", "Multi-source scanner output validation passed")
```

---

## Error Handling

### Error Codes
- `E2001`: Source API timeout
- `E2002`: Rate limit exceeded
- `E2003`: Invalid API credentials
- `E2004`: Network connection failure
- `E2005`: Empty search results (WARNING, not error)

### Retry Strategy
```yaml
retry_policy:
  max_attempts: 3
  backoff: exponential  # 1s, 2s, 4s

  per_error_strategy:
    TimeoutError:
      action: "Increase timeout on retry (30s → 60s → 120s)"

    RateLimitError:
      action: "Wait for rate limit reset, then retry"
      wait_time: "dynamic (from API response header)"

    NetworkError:
      action: "Retry with exponential backoff"

    EmptyResultsWarning:
      action: "Log and continue (not an error)"
```

### Fallback Behavior
```python
def handle_source_failure(source, error):
    if source.get('critical', False):
        log("CRITICAL", f"Critical source {source['name']} failed: {error}")
        raise error
    else:
        log("WARNING", f"Skipping {source['name']}: {error}")
        # Continue with other sources
        return []
```

---

## Performance Considerations

### Rate Limiting
```python
rate_limiter = {
    "google_scholar": RateLimiter(max_calls=100, period=3600),  # 100/hour
    "arxiv": RateLimiter(max_calls=300, period=60),  # 300/minute
    "patents": RateLimiter(max_calls=50, period=60)  # 50/minute
}
```

### Parallelization
```python
def scan_sources_parallel(sources, domains):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(scan_source, source, domains)
            for source in sources
        ]

        results = [future.result() for future in futures]

    return flatten(results)
```

### Expected Performance
```yaml
performance_targets:
  execution_time: "30-60 seconds"
  items_collected: "100-500 items per scan"
  sources_scanned: "5-10 sources"
  success_rate: "> 80% (critical sources must succeed)"
```

---

## Logging

```python
log_examples = {
    "START": "Multi-source scanner started. Scanning 8 sources...",
    "INFO": "Loaded configuration: 8 sources, 6 STEEPs domains",
    "INFO": "Scanning Google Scholar (academic)...",
    "INFO": "Collected 47 items from Google Scholar",
    "WARNING": "Timeout scanning TechCrunch API. Retrying...",
    "INFO": "Retry successful: 23 items from TechCrunch",
    "INFO": "Applied ML keyword extraction to 247 items",
    "INFO": "Applied WISDOM topic modeling: 12 topics identified",
    "SUCCESS": "Scan completed: 247 items from 8 sources",
    "END": "Multi-source scanner completed in 45.3 seconds"
}
```

---

## Configuration Examples

### sources.yaml
```yaml
sources:
  - name: "Google Scholar"
    type: "academic"
    api_endpoint: "https://serpapi.com/search"
    api_key: "${SERPAPI_KEY}"
    rate_limit: 100  # per hour
    critical: true

  - name: "arXiv"
    type: "academic"
    api_endpoint: "http://export.arxiv.org/api/query"
    rate_limit: 300  # per minute
    critical: false

  - name: "Google Patents"
    type: "patent"
    api_endpoint: "https://patents.google.com/api"
    rate_limit: 50  # per minute
    critical: false

  - name: "TechCrunch"
    type: "blog"
    rss_feed: "https://techcrunch.com/feed/"
    critical: false
```

### domains.yaml
```yaml
STEEPs:
  S_Social:
    - "demographic shift"
    - "generational gap"
    - "urbanization trend"
    - "social movement"

  T_Technological:
    - "AI breakthrough"
    - "quantum computing"
    - "biotech innovation"
    - "nanotechnology"

  E_Economic:
    - "market disruption"
    - "platform economy"
    - "supply chain"
    - "fintech"

  E_Environmental:
    - "climate change"
    - "carbon neutral"
    - "renewable energy"
    - "biodiversity"

  P_Political:
    - "policy change"
    - "regulation"
    - "geopolitical risk"
    - "trade war"

  s_spiritual:
    - "AI ethics"
    - "meaning crisis"
    - "collective emotion"
    - "value shift"
```

---

## Dependencies

### Required Tools
- Web search/fetch capabilities
- JSON/YAML parser
- HTTP client with rate limiting
- Natural language processing (keyword extraction, language detection)

### Optional AI/ML Models
- BERT for embeddings
- SBERT for semantic similarity
- WISDOM framework for topic modeling
- GCN for growth prediction

### API Keys Required
- Google Scholar API (SerpAPI)
- Other source APIs as configured

---

## Integration Points

### Called By
- Orchestrator Agent (Phase 1, Step 2)

### Calls To
- External APIs (Google Scholar, arXiv, Patents, etc.)
- Optional: ML model services (BERT, GCN)

### Outputs Used By
- `@deduplication-filter` (Step 1.3)

---

## Version
- **Agent Version**: 1.3.1 (2-Tier Source Architecture — Marathon Default)
- **Compatible with**: Enhanced Environmental Scanning Workflow v1.0
- **Tier Support**: Supports `--tier` and `--time-budget` parameters (v3.0.0+)
- **pSST Dimensions**: SR (Source Reliability), TC (Temporal Confidence)
- **pSST Level 2**: SR Level 2 (methodology, replication, transparency), TC Level 2 (momentum, update, time sensitivity)
- **Last Updated**: 2026-01-31
