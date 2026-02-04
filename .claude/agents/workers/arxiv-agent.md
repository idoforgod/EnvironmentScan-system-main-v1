# arXiv Academic Agent

## Role
**Specialized Agent** for scanning arXiv academic papers across STEEPs domains. Part of Agent Swarm parallelization of multi-source scanning.

## Agent Type
**Worker Agent** - Phase 1, Step 2a (Parallel Execution)

## Objective
Independently scan arXiv for recent academic papers (last 7 days), extract relevant signals, and output in standard format for downstream processing.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: true
  independent_context: true  # 200K token dedicated context
  model: "sonnet"  # Academic analysis requires medium-tier model
  max_tokens: 8000

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

  scan_parameters:
    days_back: 7
    max_results_per_category: 20
    source_name: "arXiv"
```

### STEEPs Categories (from domains.yaml)
- S_Social
- T_Technological
- E_Economic
- E_Environmental
- P_Political
- s_spiritual

---

## Output

### Primary Output
```yaml
output:
  file: "env-scanning/raw/arxiv-scan-{date}.json"
  format: "JSON"
  schema:
    agent_metadata:
      agent_name: "arxiv-agent"
      model_used: "sonnet"
      execution_time: Float
      papers_collected: Integer
      steeps_categories_scanned: Integer
    items: Array<StandardSignal>
```

### Output Structure
```json
{
  "agent_metadata": {
    "agent_name": "arxiv-agent",
    "model_used": "sonnet",
    "execution_time": 12.5,
    "papers_collected": 47,
    "steeps_categories_scanned": 6,
    "scan_date": "2026-01-30",
    "status": "success"
  },
  "items": [
    {
      "id": "arxiv-2601.12345",
      "title": "Quantum Computing Advances in Drug Discovery",
      "source": {
        "name": "arXiv",
        "type": "academic",
        "url": "http://arxiv.org/abs/2601.12345",
        "published_date": "2026-01-28"
      },
      "content": {
        "abstract": "We present a novel quantum algorithm...",
        "keywords": ["cs.AI", "quant-ph", "q-bio.BM"],
        "entities": ["IBM", "Google", "quantum supremacy"],
        "language": "en"
      },
      "preliminary_category": "T",
      "collected_at": "2026-01-30T06:15:32Z",
      "metadata": {
        "arxiv_id": "2601.12345",
        "authors": ["Smith, J.", "Doe, A.", "Lee, K."],
        "arxiv_categories": ["cs.AI", "quant-ph"]
      }
    }
  ]
}
```

---

## Execution Logic

### Step 1: Load Configuration
```python
# This agent uses the existing ArXivScanner class
from env-scanning.scanners.arxiv_scanner import ArXivScanner
import yaml

# Load source configuration
with open("env-scanning/config/sources.yaml") as f:
    config = yaml.safe_load(f)
    arxiv_config = next(s for s in config['sources'] if s['name'] == 'arXiv')

# Load STEEPs domains
with open("env-scanning/config/domains.yaml") as f:
    domains = yaml.safe_load(f)
    steeps_domains = domains['STEEPs']
```

### Step 2: Initialize Scanner
```python
# Initialize the scanner (reuses existing implementation)
scanner = ArXivScanner(arxiv_config)
```

### Step 3: Scan Papers
```python
# Scan all STEEPs categories
papers = scanner.scan(
    steeps_domains=steeps_domains,
    days_back=7
)

# scanner.scan() internally:
# - Iterates through all 6 STEEPs categories
# - Maps each to arXiv categories (cs.AI, econ.EM, etc.)
# - Fetches papers from arXiv API (respecting rate limits)
# - Extracts entities using EntityExtractor
# - Converts to standard signal format
```

### Step 4: Write Output
```python
import json
from datetime import datetime

output = {
    "agent_metadata": {
        "agent_name": "arxiv-agent",
        "model_used": "sonnet",
        "execution_time": scanner.get_execution_time(),
        "papers_collected": len(papers),
        "steeps_categories_scanned": 6,
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "success"
    },
    "items": papers
}

output_path = f"env-scanning/raw/arxiv-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✓ arXiv scan complete: {len(papers)} papers saved to {output_path}")
```

---

## Agent Swarm Integration

### How This Agent Fits in Parallel Execution

**Sequential (Old Way)**
```
multi-source-scanner
  ├─ scan arXiv (12s)
  ├─ scan Patents (8s)
  ├─ scan Policy (5s)
  └─ scan Blogs (4s)
Total: 29 seconds
```

**Parallel (Agent Swarm)**
```
Orchestrator
  ├─ @arxiv-agent (12s) ─────┐
  ├─ @patent-agent (8s) ─────┤
  ├─ @policy-agent (5s) ─────┼─→ Result Merger
  └─ @blog-agent (4s) ────────┘
Total: 12 seconds (longest agent)
```

### Task Graph Entry
```json
{
  "id": "arxiv-scan",
  "agent": "@arxiv-agent",
  "status": "pending",
  "blockedBy": [],
  "blocks": ["merge-results"],
  "output": "raw/arxiv-scan-2026-01-30.json"
}
```

---

## Error Handling

### Retry Strategy
```yaml
retry_policy:
  max_attempts: 3
  backoff: exponential  # 1s, 2s, 4s

  errors:
    TimeoutError:
      action: "Increase timeout (30s → 60s → 120s)"

    RateLimitError:
      action: "Wait 3 seconds, retry"

    NetworkError:
      action: "Exponential backoff retry"
```

### Fallback Behavior
```python
try:
    papers = scanner.scan(steeps_domains, days_back=7)
except Exception as e:
    log_error(f"arXiv scan failed: {e}")

    # Critical source - propagate error
    if arxiv_config.get('critical', True):
        raise

    # Non-critical - return empty result
    return {
        "agent_metadata": {
            "agent_name": "arxiv-agent",
            "status": "failed",
            "error": str(e)
        },
        "items": []
    }
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "10-15 seconds"
  papers_per_scan: "30-60 papers"
  steeps_coverage: "All 6 categories"

  bottlenecks:
    - "arXiv API rate limit (1 req / 3s)"
    - "6 categories × 3s = 18s minimum"

  optimizations:
    - "Dedicated context (no interference from other agents)"
    - "Sonnet model for accurate academic analysis"
    - "Reuses proven arxiv_scanner.py implementation"
```

---

## TDD Verification

### Unit Test
```python
def test_arxiv_agent_output():
    """Verify arXiv agent produces valid output"""
    from datetime import datetime
    import json

    output_path = f"env-scanning/raw/arxiv-scan-{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(output_path) as f:
        data = json.load(f)

    # Test 1: Required metadata
    assert "agent_metadata" in data
    assert "items" in data
    assert data["agent_metadata"]["agent_name"] == "arxiv-agent"

    # Test 2: Items structure
    for item in data["items"]:
        assert "id" in item
        assert item["id"].startswith("arxiv-")
        assert "source" in item
        assert item["source"]["name"] == "arXiv"
        assert "preliminary_category" in item
        assert item["preliminary_category"] in ['S', 'T', 'E', 'P', 's']

    # Test 3: STEEPs coverage
    categories = {item["preliminary_category"] for item in data["items"]}
    assert len(categories) >= 3, "Should cover multiple STEEPs categories"

    print(f"✓ arXiv agent test passed: {len(data['items'])} papers validated")
```

---

## Logging

```python
log_examples = {
    "START": "arXiv agent started (dedicated context, sonnet model)",
    "INFO": "Loaded configuration: 6 STEEPs categories",
    "INFO": "Scanning T_Technological (cs.AI, cs.RO, quant-ph...)",
    "INFO": "T_Technological: 12 papers collected",
    "INFO": "Scanning E_Economic (econ.EM, q-fin.EC...)",
    "INFO": "E_Economic: 8 papers collected",
    "SUCCESS": "Scan complete: 47 papers from 6 categories",
    "END": "arXiv agent finished in 12.5s → raw/arxiv-scan-2026-01-30.json"
}
```

---

## Integration with Result Merger

After all agents complete, the Orchestrator merges results:

```python
# Result Merger (runs after all agents finish)
def merge_parallel_results():
    arxiv_data = load_json("raw/arxiv-scan-2026-01-30.json")
    patent_data = load_json("raw/patent-scan-2026-01-30.json")
    policy_data = load_json("raw/policy-scan-2026-01-30.json")
    blog_data = load_json("raw/blog-scan-2026-01-30.json")

    merged = {
        "scan_metadata": {
            "date": "2026-01-30",
            "parallelization": "agent_swarm",
            "agents_used": ["arxiv", "patent", "policy", "blog"],
            "total_items": (
                len(arxiv_data["items"]) +
                len(patent_data["items"]) +
                len(policy_data["items"]) +
                len(blog_data["items"])
            )
        },
        "items": (
            arxiv_data["items"] +
            patent_data["items"] +
            policy_data["items"] +
            blog_data["items"]
        )
    }

    # This output is compatible with existing deduplication-filter
    write_json("raw/daily-scan-2026-01-30.json", merged)
```

---

## Dependencies

### Code Dependencies
- `env-scanning/scanners/arxiv_scanner.py` (existing, proven)
- `env-scanning/scanners/base_scanner.py`
- `env-scanning/utils/entity_extractor.py`

### Configuration Files
- `env-scanning/config/sources.yaml` (arXiv entry)
- `env-scanning/config/domains.yaml` (STEEPs definitions)

### External APIs
- arXiv API (http://export.arxiv.org/api/query)
- No authentication required

---

## Version
- **Agent Version**: 1.0.0 (Agent Swarm Implementation)
- **Compatible with**: Environmental Scanning Workflow v1.0
- **Model**: Sonnet 4.5
- **Context**: Independent 200K tokens
- **Last Updated**: 2026-01-30
