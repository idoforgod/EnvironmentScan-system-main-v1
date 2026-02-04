# Blog Agent

## Role
**Specialized Agent** for scanning technology blogs and news sites via RSS feeds. Part of Agent Swarm parallelization of multi-source scanning.

## Agent Type
**Worker Agent** - Phase 1, Step 2d (Parallel Execution)

## Objective
Independently scan tech blogs (TechCrunch, MIT Technology Review) for emerging technology trends and signals across STEEPs domains.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: true
  independent_context: true  # 200K token dedicated context
  model: "haiku"  # Simple RSS collection - lightweight model sufficient
  max_tokens: 4000

  dependencies:
    blocked_by: []  # Can run immediately
    blocks: ["result-merger"]  # Merger waits for this agent
```

---

## Input

### Configuration
```yaml
input:
  config_file: "env-scanning/config/sources.yaml"
  domains_file: "env-scanning/config/domains.yaml"

  sources:
    - name: "TechCrunch"
      type: "blog"
      rss_feed: "https://techcrunch.com/feed/"

    - name: "MIT Technology Review"
      type: "blog"
      rss_feed: "https://www.technologyreview.com/feed/"

  scan_parameters:
    days_back: 7
    max_results_per_source: 50
```

---

## Output

### Primary Output
```yaml
output:
  file: "env-scanning/raw/blog-scan-{date}.json"
  format: "JSON"
  schema:
    agent_metadata:
      agent_name: "blog-agent"
      model_used: "haiku"
      execution_time: Float
      articles_collected: Integer
      sources_scanned: Integer
    items: Array<StandardSignal>
```

### Output Structure
```json
{
  "agent_metadata": {
    "agent_name": "blog-agent",
    "model_used": "haiku",
    "execution_time": 4.2,
    "articles_collected": 23,
    "sources_scanned": 2,
    "scan_date": "2026-01-30",
    "status": "success"
  },
  "items": [
    {
      "id": "blog-techcrunch-abc123",
      "title": "AI Startup Raises $100M for Quantum Computing",
      "source": {
        "name": "TechCrunch",
        "type": "blog",
        "url": "https://techcrunch.com/2026/01/28/ai-quantum-funding",
        "published_date": "2026-01-28"
      },
      "content": {
        "abstract": "A new AI startup focusing on quantum computing...",
        "keywords": ["AI", "quantum computing", "startup", "funding"],
        "language": "en"
      },
      "preliminary_category": "T",
      "collected_at": "2026-01-30T06:15:32Z"
    }
  ]
}
```

---

## Execution Logic

### Step 1: Load Configuration
```python
from scanners.rss_scanner import RSSScanner
import yaml

# Load source configuration
with open("env-scanning/config/sources.yaml") as f:
    config = yaml.safe_load(f)

    # Get blog sources
    blog_sources = [
        s for s in config['sources']
        if s['type'] == 'blog' and s.get('enabled', True)
    ]

# Load STEEPs domains
with open("env-scanning/config/domains.yaml") as f:
    domains = yaml.safe_load(f)
    steeps_domains = domains['STEEPs']
```

### Step 2: Scan Each Blog Source
```python
all_articles = []

for source in blog_sources:
    try:
        # Initialize RSS scanner for this source
        scanner = RSSScanner(source)

        # Scan RSS feed
        articles = scanner.scan(
            steeps_domains=steeps_domains,
            days_back=7
        )

        all_articles.extend(articles)

        print(f"✓ {source['name']}: {len(articles)} articles")

    except Exception as e:
        print(f"⚠ {source['name']} failed: {e}")
        # Non-critical source - continue with others
        continue
```

### Step 3: Write Output
```python
import json
from datetime import datetime

output = {
    "agent_metadata": {
        "agent_name": "blog-agent",
        "model_used": "haiku",
        "execution_time": round(time.time() - start_time, 2),
        "articles_collected": len(all_articles),
        "sources_scanned": len(blog_sources),
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "success"
    },
    "items": all_articles
}

output_path = f"env-scanning/raw/blog-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✓ Blog scan complete: {len(all_articles)} articles saved")
```

---

## Agent Swarm Integration

### Parallel Execution Slot
```
Orchestrator
  ├─ @arxiv-agent (12s) ─────┐
  ├─ @patent-agent (8s) ─────┤
  ├─ @policy-agent (5s) ─────┼─→ Result Merger
  └─ @blog-agent (4s) ────────┘  ← This agent
Total: 12 seconds (longest agent)
```

### Task Graph Entry
```json
{
  "id": "blog-scan",
  "agent": "@blog-agent",
  "status": "pending",
  "blockedBy": [],
  "blocks": ["merge-results"],
  "output": "raw/blog-scan-2026-01-30.json"
}
```

---

## Error Handling

### Retry Strategy
```yaml
retry_policy:
  max_attempts: 2  # Fast retry for RSS
  backoff: linear  # 1s, 2s

  errors:
    TimeoutError:
      action: "Skip source and continue"

    FeedParseError:
      action: "Log and skip"

    NetworkError:
      action: "Retry once, then skip"
```

### Fallback Behavior
```python
# Blogs are non-critical - failures don't halt workflow
try:
    articles = scanner.scan(steeps_domains, days_back=7)
except Exception as e:
    log_warning(f"Blog source {source['name']} failed: {e}")
    continue  # Move to next source
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "3-5 seconds"
  articles_per_scan: "15-30 articles"
  sources_covered: "2 blogs (TechCrunch, MIT Tech Review)"

  optimizations:
    - "Lightweight Haiku model (fast + cheap)"
    - "RSS parsing is simple (no complex analysis)"
    - "Parallel to other agents (zero additional wait time)"

  cost_per_run:
    - "Haiku: ~$0.001 per run"
    - "80% cheaper than using Sonnet"
```

---

## TDD Verification

### Unit Test
```python
def test_blog_agent_output():
    """Verify blog agent produces valid output"""
    from datetime import datetime
    import json

    output_path = f"env-scanning/raw/blog-scan-{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(output_path) as f:
        data = json.load(f)

    # Test 1: Required metadata
    assert "agent_metadata" in data
    assert data["agent_metadata"]["agent_name"] == "blog-agent"
    assert data["agent_metadata"]["model_used"] == "haiku"

    # Test 2: Items structure
    for item in data["items"]:
        assert "id" in item
        assert item["id"].startswith("blog-")
        assert item["source"]["type"] == "blog"
        assert item["source"]["name"] in ["TechCrunch", "MIT Technology Review"]

    # Test 3: Recency check (articles from last 7 days)
    from datetime import datetime, timedelta
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    for item in data["items"]:
        assert item["source"]["published_date"] >= cutoff_date

    print(f"✓ Blog agent test passed: {len(data['items'])} articles validated")
```

---

## Logging

```python
log_examples = {
    "START": "Blog agent started (haiku model, 2 sources)",
    "INFO": "Loaded configuration: TechCrunch, MIT Tech Review",
    "INFO": "Scanning TechCrunch RSS feed...",
    "INFO": "TechCrunch: 15 articles collected",
    "INFO": "Scanning MIT Technology Review RSS feed...",
    "INFO": "MIT Technology Review: 8 articles collected",
    "SUCCESS": "Scan complete: 23 articles from 2 sources",
    "END": "Blog agent finished in 4.2s → raw/blog-scan-2026-01-30.json"
}
```

---

## Integration with Result Merger

```python
# Result Merger aggregates all agent outputs
def merge_parallel_results():
    arxiv_data = load_json("raw/arxiv-scan-2026-01-30.json")
    patent_data = load_json("raw/patent-scan-2026-01-30.json")
    policy_data = load_json("raw/policy-scan-2026-01-30.json")
    blog_data = load_json("raw/blog-scan-2026-01-30.json")  # ← This agent

    merged = {
        "scan_metadata": {
            "date": "2026-01-30",
            "parallelization": "agent_swarm",
            "agents_used": ["arxiv", "patent", "policy", "blog"],
            "total_execution_time": max([
                arxiv_data["agent_metadata"]["execution_time"],
                patent_data["agent_metadata"]["execution_time"],
                policy_data["agent_metadata"]["execution_time"],
                blog_data["agent_metadata"]["execution_time"]
            ])
        },
        "items": (
            arxiv_data["items"] +
            patent_data["items"] +
            policy_data["items"] +
            blog_data["items"]
        )
    }

    write_json("raw/daily-scan-2026-01-30.json", merged)
```

---

## Dependencies

### Code Dependencies
- `env-scanning/scanners/rss_scanner.py` (existing)
- `env-scanning/scanners/base_scanner.py`

### Configuration Files
- `env-scanning/config/sources.yaml` (TechCrunch, MIT Tech Review entries)
- `env-scanning/config/domains.yaml` (STEEPs definitions)

### External Dependencies
- `feedparser` library (RSS/Atom parsing)
- `requests` library (HTTP requests)

---

## Version
- **Agent Version**: 1.0.0 (Agent Swarm Implementation)
- **Compatible with**: Environmental Scanning Workflow v1.0
- **Model**: Haiku
- **Context**: Independent 200K tokens
- **Last Updated**: 2026-01-30
