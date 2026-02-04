# Policy Agent

## Role
**Specialized Agent** for scanning government policy and regulatory documents. Part of Agent Swarm parallelization of multi-source scanning.

## Agent Type
**Worker Agent** - Phase 1, Step 2c (Parallel Execution)

## Objective
Independently scan policy sources (US Federal Register, WHO Press Releases) for regulatory changes, policy shifts, and international health/safety signals.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: true
  independent_context: true  # 200K token dedicated context
  model: "haiku"  # Policy document collection - lightweight model sufficient
  max_tokens: 5000

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
    - name: "US Federal Register"
      type: "policy"
      api_endpoint: "https://www.federalregister.gov/api/v1/documents"
      scanner: "FederalRegisterScanner"

    - name: "WHO Press Releases"
      type: "policy"
      rss_feed: "https://www.who.int/rss-feeds/news-english.xml"
      scanner: "RSSScanner"

  scan_parameters:
    days_back: 7
    max_results_per_source: 50
```

---

## Output

### Primary Output
```yaml
output:
  file: "env-scanning/raw/policy-scan-{date}.json"
  format: "JSON"
  schema:
    agent_metadata:
      agent_name: "policy-agent"
      model_used: "haiku"
      execution_time: Float
      documents_collected: Integer
      sources_scanned: Integer
    items: Array<StandardSignal>
```

### Output Structure
```json
{
  "agent_metadata": {
    "agent_name": "policy-agent",
    "model_used": "haiku",
    "execution_time": 5.3,
    "documents_collected": 18,
    "sources_scanned": 2,
    "scan_date": "2026-01-30",
    "status": "success"
  },
  "items": [
    {
      "id": "policy-federal-register-2026-01234",
      "title": "Proposed Rule on AI Risk Management Framework",
      "source": {
        "name": "US Federal Register",
        "type": "policy",
        "url": "https://www.federalregister.gov/documents/2026/01/28/2026-01234",
        "published_date": "2026-01-28"
      },
      "content": {
        "abstract": "The National Institute of Standards and Technology proposes...",
        "keywords": ["AI regulation", "risk management", "NIST"],
        "language": "en"
      },
      "preliminary_category": "P",
      "collected_at": "2026-01-30T06:15:32Z",
      "metadata": {
        "document_type": "Proposed Rule",
        "agencies": ["National Institute of Standards and Technology"],
        "topics": ["Science and Technology", "Government Regulation"]
      }
    }
  ]
}
```

---

## Execution Logic

### Step 1: Load Configuration
```python
from scanners.federal_register_scanner import FederalRegisterScanner
from scanners.rss_scanner import RSSScanner
import yaml

# Load source configuration
with open("env-scanning/config/sources.yaml") as f:
    config = yaml.safe_load(f)

    # Get policy sources
    policy_sources = [
        s for s in config['sources']
        if s['type'] == 'policy' and s.get('enabled', True)
    ]

# Load STEEPs domains
with open("env-scanning/config/domains.yaml") as f:
    domains = yaml.safe_load(f)
    steeps_domains = domains['STEEPs']
```

### Step 2: Scan Each Policy Source
```python
all_documents = []

for source in policy_sources:
    try:
        # Select appropriate scanner
        if 'api_endpoint' in source and 'federal' in source['name'].lower():
            scanner = FederalRegisterScanner(source)
        elif 'rss_feed' in source:
            scanner = RSSScanner(source)
        else:
            print(f"⚠ Unknown scanner type for {source['name']}, skipping")
            continue

        # Scan source
        documents = scanner.scan(
            steeps_domains=steeps_domains,
            days_back=7
        )

        all_documents.extend(documents)

        print(f"✓ {source['name']}: {len(documents)} documents")

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
        "agent_name": "policy-agent",
        "model_used": "haiku",
        "execution_time": round(time.time() - start_time, 2),
        "documents_collected": len(all_documents),
        "sources_scanned": len(policy_sources),
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "success"
    },
    "items": all_documents
}

output_path = f"env-scanning/raw/policy-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✓ Policy scan complete: {len(all_documents)} documents saved")
```

---

## Agent Swarm Integration

### Parallel Execution Slot
```
Orchestrator
  ├─ @arxiv-agent (12s) ─────┐
  ├─ @patent-agent (8s) ─────┤
  ├─ @policy-agent (5s) ─────┼─→ Result Merger  ← This agent
  └─ @blog-agent (4s) ────────┘
Total: 12 seconds (longest agent)
```

### Task Graph Entry
```json
{
  "id": "policy-scan",
  "agent": "@policy-agent",
  "status": "pending",
  "blockedBy": [],
  "blocks": ["merge-results"],
  "output": "raw/policy-scan-2026-01-30.json"
}
```

---

## Error Handling

### Retry Strategy
```yaml
retry_policy:
  max_attempts: 2
  backoff: linear  # 1s, 2s

  errors:
    TimeoutError:
      action: "Skip source and continue"

    APIError:
      action: "Retry once, then skip"

    NetworkError:
      action: "Retry once, then skip"
```

### Fallback Behavior
```python
# Policy sources are important but not critical
# If all sources fail, return empty result with warning
try:
    documents = scanner.scan(steeps_domains, days_back=7)
except Exception as e:
    log_warning(f"Policy source {source['name']} failed: {e}")
    continue  # Move to next source

# If no documents collected from any source
if len(all_documents) == 0:
    log_warning("No policy documents collected from any source")
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "4-6 seconds"
  documents_per_scan: "10-25 documents"
  sources_covered: "2 policy sources"

  optimizations:
    - "Lightweight Haiku model (fast + cheap)"
    - "API calls are straightforward (no complex analysis)"
    - "Parallel to other agents (zero additional wait time)"

  cost_per_run:
    - "Haiku: ~$0.001 per run"
    - "80% cheaper than using Sonnet"
```

---

## TDD Verification

### Unit Test
```python
def test_policy_agent_output():
    """Verify policy agent produces valid output"""
    from datetime import datetime
    import json

    output_path = f"env-scanning/raw/policy-scan-{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(output_path) as f:
        data = json.load(f)

    # Test 1: Required metadata
    assert "agent_metadata" in data
    assert data["agent_metadata"]["agent_name"] == "policy-agent"
    assert data["agent_metadata"]["model_used"] == "haiku"

    # Test 2: Items structure
    for item in data["items"]:
        assert "id" in item
        assert item["id"].startswith("policy-")
        assert item["source"]["type"] == "policy"

    # Test 3: Preliminary category (should be mostly 'P' for Political)
    categories = [item["preliminary_category"] for item in data["items"]]
    assert 'P' in categories, "Expected at least some Political category items"

    print(f"✓ Policy agent test passed: {len(data['items'])} documents validated")
```

---

## Logging

```python
log_examples = {
    "START": "Policy agent started (haiku model, 2 sources)",
    "INFO": "Loaded configuration: Federal Register, WHO",
    "INFO": "Scanning US Federal Register API...",
    "INFO": "US Federal Register: 12 documents collected",
    "INFO": "Scanning WHO Press Releases RSS...",
    "INFO": "WHO Press Releases: 6 documents collected",
    "SUCCESS": "Scan complete: 18 documents from 2 sources",
    "END": "Policy agent finished in 5.3s → raw/policy-scan-2026-01-30.json"
}
```

---

## Integration with Result Merger

```python
# Result Merger aggregates all agent outputs
def merge_parallel_results():
    arxiv_data = load_json("raw/arxiv-scan-2026-01-30.json")
    patent_data = load_json("raw/patent-scan-2026-01-30.json")
    policy_data = load_json("raw/policy-scan-2026-01-30.json")  # ← This agent
    blog_data = load_json("raw/blog-scan-2026-01-30.json")

    merged = {
        "scan_metadata": {
            "date": "2026-01-30",
            "parallelization": "agent_swarm",
            "agents_used": ["arxiv", "patent", "policy", "blog"],
            "total_items": sum([
                len(arxiv_data["items"]),
                len(patent_data["items"]),
                len(policy_data["items"]),
                len(blog_data["items"])
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
- `env-scanning/scanners/federal_register_scanner.py` (existing)
- `env-scanning/scanners/rss_scanner.py` (existing)
- `env-scanning/scanners/base_scanner.py`

### Configuration Files
- `env-scanning/config/sources.yaml` (Federal Register, WHO entries)
- `env-scanning/config/domains.yaml` (STEEPs definitions)

### External Dependencies
- `requests` library (HTTP/API requests)
- `feedparser` library (RSS parsing for WHO)

---

## Version
- **Agent Version**: 1.0.0 (Agent Swarm Implementation)
- **Compatible with**: Environmental Scanning Workflow v1.0
- **Model**: Haiku
- **Context**: Independent 200K tokens
- **Last Updated**: 2026-01-30
