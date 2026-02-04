# Patent Agent

## Role
**Specialized Agent** for scanning patent databases (Google Patents). Part of Agent Swarm parallelization of multi-source scanning.

## Agent Type
**Worker Agent** - Phase 1, Step 2b (Parallel Execution)

## Objective
Independently scan patent sources for emerging technological innovations and intellectual property signals, focusing on Technological domain (T).

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: true
  independent_context: true  # 200K token dedicated context
  model: "haiku"  # Simple patent data collection - lightweight model sufficient
  max_tokens: 6000

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
    - name: "Google Patents"
      type: "patent"
      api_endpoint: "https://patents.google.com/api"
      # Note: Google Patents does not have a free public API
      # Alternative: Scraping or USPTO API

  scan_parameters:
    days_back: 30  # Patents: monthly scan (slower publication cycle)
    max_results: 30
```

---

## Current Implementation Status

⚠️ **Note**: Google Patents scanner not yet implemented.

**Reason**: Google Patents does not provide a free public API. Alternatives:
1. **USPTO API**: Free, official US patent data
2. **Web scraping**: Google Patents search results (rate-limited)
3. **EPO OPS API**: European patents (requires registration)

**Recommendation**: Implement USPTO API scanner for US patents as primary source.

For now, this agent returns empty results with a placeholder message.

---

## Output

### Primary Output (Placeholder)
```yaml
output:
  file: "env-scanning/raw/patent-scan-{date}.json"
  format: "JSON"
  schema:
    agent_metadata:
      agent_name: "patent-agent"
      model_used: "haiku"
      execution_time: Float
      patents_collected: Integer
      sources_scanned: Integer
      status: "not_implemented" | "success"
    items: Array<StandardSignal>
```

### Output Structure (When Implemented)
```json
{
  "agent_metadata": {
    "agent_name": "patent-agent",
    "model_used": "haiku",
    "execution_time": 8.1,
    "patents_collected": 15,
    "sources_scanned": 1,
    "scan_date": "2026-01-30",
    "status": "success"
  },
  "items": [
    {
      "id": "patent-us-20260012345",
      "title": "Method and System for Quantum Error Correction",
      "source": {
        "name": "Google Patents",
        "type": "patent",
        "url": "https://patents.google.com/patent/US20260012345",
        "published_date": "2026-01-15"
      },
      "content": {
        "abstract": "A novel quantum error correction method using...",
        "keywords": ["quantum computing", "error correction", "qubits"],
        "language": "en"
      },
      "preliminary_category": "T",
      "collected_at": "2026-01-30T06:15:32Z",
      "metadata": {
        "patent_number": "US20260012345",
        "inventors": ["Smith, John", "Doe, Jane"],
        "assignee": "Quantum Tech Corp",
        "filing_date": "2025-07-15"
      }
    }
  ]
}
```

---

## Execution Logic (Placeholder)

### Current Implementation (Returns Empty)
```python
import json
from datetime import datetime
import time

def run_patent_agent():
    """
    Placeholder implementation
    Returns empty results until patent scanner is implemented
    """
    start_time = time.time()

    output = {
        "agent_metadata": {
            "agent_name": "patent-agent",
            "model_used": "haiku",
            "execution_time": round(time.time() - start_time, 2),
            "patents_collected": 0,
            "sources_scanned": 0,
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "not_implemented",
            "message": "Patent scanner not yet implemented. Use USPTO API or alternative."
        },
        "items": []
    }

    output_path = f"env-scanning/raw/patent-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("⚠ Patent agent: Scanner not implemented, returning empty results")
    return output
```

### Future Implementation (With USPTO API)
```python
from scanners.uspto_scanner import USPTOScanner  # To be implemented
import yaml

# Load configuration
with open("env-scanning/config/sources.yaml") as f:
    config = yaml.safe_load(f)
    patent_sources = [
        s for s in config['sources']
        if s['type'] == 'patent' and s.get('enabled', True)
    ]

# Load STEEPs domains
with open("env-scanning/config/domains.yaml") as f:
    domains = yaml.safe_load(f)
    steeps_domains = domains['STEEPs']

# Scan patents
all_patents = []

for source in patent_sources:
    try:
        scanner = USPTOScanner(source)
        patents = scanner.scan(
            steeps_domains=steeps_domains,
            days_back=30  # Patents: monthly scan
        )
        all_patents.extend(patents)
        print(f"✓ {source['name']}: {len(patents)} patents")
    except Exception as e:
        print(f"⚠ {source['name']} failed: {e}")
        continue

# Write output
output = {
    "agent_metadata": {
        "agent_name": "patent-agent",
        "model_used": "haiku",
        "execution_time": round(time.time() - start_time, 2),
        "patents_collected": len(all_patents),
        "sources_scanned": len(patent_sources),
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "success"
    },
    "items": all_patents
}

output_path = f"env-scanning/raw/patent-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✓ Patent scan complete: {len(all_patents)} patents saved")
```

---

## Agent Swarm Integration

### Parallel Execution Slot
```
Orchestrator
  ├─ @arxiv-agent (12s) ─────┐
  ├─ @patent-agent (8s) ─────┤  ← This agent (when implemented)
  ├─ @policy-agent (5s) ─────┼─→ Result Merger
  └─ @blog-agent (4s) ────────┘
Total: 12 seconds (longest agent)
```

### Task Graph Entry
```json
{
  "id": "patent-scan",
  "agent": "@patent-agent",
  "status": "not_implemented",
  "blockedBy": [],
  "blocks": ["merge-results"],
  "output": "raw/patent-scan-2026-01-30.json"
}
```

---

## Error Handling

### Current Behavior
```python
# Returns empty results, does not block workflow
# Result merger will simply skip empty patent data
```

### Future Behavior (When Implemented)
```yaml
retry_policy:
  max_attempts: 2
  backoff: exponential  # 2s, 4s

  errors:
    TimeoutError:
      action: "Retry with increased timeout"

    RateLimitError:
      action: "Wait and retry"

    APIError:
      action: "Log and skip"
```

---

## Performance Expectations (When Implemented)

```yaml
performance:
  execution_time: "7-10 seconds"
  patents_per_scan: "10-30 patents"
  sources_covered: "1 patent database"

  optimizations:
    - "Lightweight Haiku model"
    - "Focus on Technological domain (T)"
    - "Monthly scan cycle (patents are slower to publish)"

  cost_per_run:
    - "Haiku: ~$0.001 per run"
```

---

## Implementation Roadmap

### Phase 1: USPTO API Scanner (Recommended)
```yaml
priority: high
effort: 2-4 hours
benefits:
  - Free, official US patent data
  - No authentication required for basic search
  - Reliable API with good documentation

implementation:
  - Create uspto_scanner.py
  - Use USPTO PatFT/AppFT search APIs
  - Focus on recent applications (last 30 days)
  - Extract: title, abstract, inventors, filing date
```

### Phase 2: EPO OPS API (Optional)
```yaml
priority: medium
effort: 3-5 hours
benefits:
  - European patent coverage
  - Free tier available
  - Complements US patents

implementation:
  - Register for EPO OPS access
  - Create epo_scanner.py
  - Integrate with existing workflow
```

---

## TDD Verification (Future)

### Unit Test (When Implemented)
```python
def test_patent_agent_output():
    """Verify patent agent produces valid output"""
    from datetime import datetime
    import json

    output_path = f"env-scanning/raw/patent-scan-{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(output_path) as f:
        data = json.load(f)

    # Test 1: Required metadata
    assert "agent_metadata" in data
    assert data["agent_metadata"]["agent_name"] == "patent-agent"

    # Test 2: If implemented, check items
    if data["agent_metadata"]["status"] == "success":
        for item in data["items"]:
            assert "id" in item
            assert item["id"].startswith("patent-")
            assert item["source"]["type"] == "patent"
            assert item["preliminary_category"] == "T"  # Technological

    print(f"✓ Patent agent test passed")
```

---

## Logging

```python
log_examples = {
    "START": "Patent agent started (placeholder mode)",
    "WARNING": "Patent scanner not implemented, returning empty results",
    "INFO": "Future implementation: USPTO API scanner",
    "END": "Patent agent finished in 0.1s → raw/patent-scan-2026-01-30.json (empty)"
}
```

---

## Integration with Result Merger

```python
# Result Merger handles empty patent data gracefully
def merge_parallel_results():
    arxiv_data = load_json("raw/arxiv-scan-2026-01-30.json")
    patent_data = load_json("raw/patent-scan-2026-01-30.json")  # ← May be empty
    policy_data = load_json("raw/policy-scan-2026-01-30.json")
    blog_data = load_json("raw/blog-scan-2026-01-30.json")

    # Skip empty patent data if not implemented
    all_items = []
    for data in [arxiv_data, patent_data, policy_data, blog_data]:
        if data["agent_metadata"].get("status") == "success":
            all_items.extend(data["items"])
        elif data["agent_metadata"].get("status") == "not_implemented":
            print(f"⚠ {data['agent_metadata']['agent_name']}: Not implemented, skipping")

    merged = {
        "scan_metadata": {
            "date": "2026-01-30",
            "parallelization": "agent_swarm",
            "agents_used": ["arxiv", "policy", "blog"],  # Patent excluded for now
            "total_items": len(all_items)
        },
        "items": all_items
    }

    write_json("raw/daily-scan-2026-01-30.json", merged)
```

---

## Dependencies

### Code Dependencies (Future)
- `env-scanning/scanners/uspto_scanner.py` (to be implemented)
- `env-scanning/scanners/base_scanner.py`

### Configuration Files
- `env-scanning/config/sources.yaml` (Google Patents / USPTO entry)
- `env-scanning/config/domains.yaml` (STEEPs definitions, focus on T_Technological)

### External Dependencies (Future)
- `requests` library (API requests)
- USPTO API access (free, no key required)

---

## Version
- **Agent Version**: 1.0.0 (Placeholder - Not Implemented)
- **Compatible with**: Environmental Scanning Workflow v1.0
- **Model**: Haiku
- **Context**: Independent 200K tokens
- **Status**: ⚠️ **Placeholder** - USPTO scanner implementation needed
- **Last Updated**: 2026-01-30
