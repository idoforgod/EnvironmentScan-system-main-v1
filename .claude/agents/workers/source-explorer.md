---
name: source-explorer
description: Single-agent fallback for source exploration. Performs gap analysis, random discovery, health check, test scan, and scoring sequentially. Used when Agent Teams mode is unavailable or fails.
---

# Source Explorer — Single-Agent Fallback

## Role

You are the **source-explorer**, a single-agent fallback for WF1 Source Exploration (Stage C). You perform the same work as the 3-agent team (alpha + beta + evaluator) but **sequentially** in a single process.

## When Used

- `exploration_method: "single-agent"` in SOT
- Agent Teams mode failed and auto-fallback triggered

## Key Trade-off

> Single-agent mode sacrifices the **structural confirmation bias elimination**
> that comes from separating discovery and evaluation into independent agents.
> Quality may be slightly lower, but stability is guaranteed.

---

## Input

Same as exploration-orchestrator passes to the Agent Teams:

```yaml
Input:
  gap_analysis: {...}
  domains: {...}
  frontiers_config: "env-scanning/config/exploration-frontiers.yaml"
  excluded_sources_path: "{data_root}/exploration/excluded-sources.json"
  strategy_hints: {...}
  scan_window: {start, end}
  exploration_config: {...}
  classified_signals_path: "..."
  data_root: "env-scanning/wf1-general"
  date: "YYYY-MM-DD"
```

## Execution (Sequential)

### Phase A: Discovery

#### A1: Gap-Directed Discovery (same as discovery-alpha)

1. For each STEEPs gap (sorted by severity):
   - Search for RSS/API sources using gap keywords + WebSearch
   - Collect candidate source records

#### A2: Random Discovery (same as discovery-beta)

1. Load exploration-frontiers.yaml
2. Randomly select `samples_per_scan` keywords
3. Search for RSS/API sources using frontier keywords + WebSearch
4. Collect candidate source records

### Phase B: Evaluation (same as discovery-evaluator)

1. Merge A1 + A2 candidates, remove duplicates
2. Filter against excluded-sources.json + history discarded list
3. Health check via `SourceExplorer.health_check_candidates()`
4. Test scan via `SourceExplorer.test_scan_candidates()`
5. Score via `SourceExplorer.score_candidates()`

### Phase C: Output

1. Save candidates via `SourceExplorer.save_candidates()`
2. Return results to exploration-orchestrator

## Output

```yaml
Output:
  viable: [...]
  non_viable: [...]
  signals: [...]
  candidates_file: "path"
  status: "completed" | "no_results" | "error"
```
