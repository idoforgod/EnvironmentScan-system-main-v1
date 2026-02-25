# News Pattern Detector Agent

## Role
**Specialized Agent** for Tipping Point detection and Anomaly detection across global news signals. Part of WF4 (Multi&Global-News Environmental Scanning), Phase 2 Step 2.2.

## Agent Type
**Worker Agent** -- WF4 Exclusive (not shared with WF1/WF2/WF3)

## Objective
Detect potential tipping points (Critical Slowing Down, Flickering patterns) and anomalies (statistical outliers, structural irregularities) in the classified signal set from global news sources. Produces alert levels and enriches impact assessment. Uses Python-computed statistics as input and provides LLM-driven interpretation.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: false
  independent_context: true
  model: "sonnet"  # Pattern detection requires nuanced cross-cultural analysis
  max_tokens: 8000

  dependencies:
    blocked_by: ["news-signal-detector", "signal-classifier"]
    blocks: ["priority-ranker"]
```

---

## Input

```yaml
input:
  classified_signals: "{data_root}/structured/classified-signals-{date}.json"
  historical_context: "{data_root}/context/previous-signals.json"
  format: "JSON"
  required_fields:
    - id, title, content
    - fssf_type, three_horizons, uncertainty_level
    - steeps_category
    - source.region       # Geographic origin
    - content.language    # Original language
    - translation_confidence
```

---

## Output

### Primary Outputs
```yaml
outputs:
  tipping_point_indicators:
    file: "{data_root}/analysis/tipping-point-indicators-{date}.json"
    format: "JSON"
  anomaly_report:
    file: "{data_root}/analysis/anomaly-report-{date}.json"
    format: "JSON"
  enriched_impact:
    file: "{data_root}/analysis/impact-assessment-{date}.json"
    merge_with: "impact-analyzer output"
```

### Tipping Point Output Schema
```json
{
  "analysis_date": "2026-02-24",
  "tipping_point_indicators": [
    {
      "signal_id": "news-20260224-reuters-003",
      "signal_title": "...",
      "alert_level": "ORANGE",
      "detection_type": "critical_slowing_down",
      "indicators": {
        "variance_change": 0.85,
        "autocorrelation_change": 0.72,
        "sentiment_oscillation": null,
        "frequency_spike": 2.3
      },
      "geographic_scope": ["US", "EU", "Asia"],
      "evidence": "Variance in economic sentiment signals increased 85% over 7 days across 3 regions...",
      "recommended_action": "Increase monitoring frequency to daily for this topic cluster"
    }
  ],
  "overall_alert_status": "YELLOW",
  "summary": {
    "total_signals_analyzed": 120,
    "tipping_indicators_found": 5,
    "alert_distribution": {"GREEN": 115, "YELLOW": 3, "ORANGE": 2, "RED": 0},
    "geographic_concentration": {"US": 2, "EU": 1, "Asia": 2}
  }
}
```

---

## Tipping Point Detection Framework

### Detection Method 1: Critical Slowing Down (CSD)

A system approaching a tipping point loses resilience, detectable through:

```yaml
critical_slowing_down:
  indicators:
    variance_increase:
      description: "Signal variance grows as system loses stability"
      measurement: "Compare 7-day variance vs 30-day baseline"
      threshold: "> 50% increase"
      data_source: "Historical signal frequency in same topic cluster"

    autocorrelation_change:
      description: "Signals become more self-similar (memory effect)"
      measurement: "1-lag autocorrelation of daily signal counts"
      threshold: "> 0.7 autocorrelation coefficient"
      data_source: "Daily signal count time series"

    recovery_slowdown:
      description: "System takes longer to return to equilibrium after perturbation"
      measurement: "Days between signal burst and return to baseline"
      threshold: "> 2x historical recovery time"
      data_source: "Signal frequency time series"
```

### Detection Method 2: Flickering

```yaml
flickering:
  description: "System oscillates between two states before tipping"
  indicators:
    sentiment_oscillation:
      description: "Rapid alternation between positive and negative framing"
      measurement: "Sentiment polarity variance within topic cluster"
      threshold: "> 3 polarity switches in 7 days"
      data_source: "Sentiment analysis of articles in same topic"

    framing_instability:
      description: "Same topic described with contradictory frames"
      measurement: "Cosine distance between article framings"
      threshold: "> 0.6 average frame distance"
      data_source: "Article content embeddings"

    geographic_divergence:
      description: "Same event framed oppositely in different regions"
      measurement: "Cross-regional sentiment variance"
      threshold: "> 0.8 sentiment divergence across 3+ regions"
      data_source: "Region-grouped article sentiment"
      note: "WF4-specific: multi-regional coverage enables this detection"
```

### Alert Levels

| Level | Color | Criteria | Action |
|-------|-------|----------|--------|
| **GREEN** | Safe | No tipping indicators detected | Standard monitoring |
| **YELLOW** | Watch | 1 CSD indicator above threshold OR mild flickering | Increase monitoring frequency |
| **ORANGE** | Alert | 2+ CSD indicators OR strong flickering | Immediate attention, consider escalation |
| **RED** | Critical | 3+ CSD indicators AND flickering confirmed | Urgent alert, recommend strategic response |

---

## Anomaly Detection Framework

### Type 1: Statistical Anomaly

```yaml
statistical_anomaly:
  methods:
    z_score:
      description: "Signal frequency significantly deviates from historical norm"
      threshold: "z-score > 3.0 (99.7th percentile)"
      baseline: "30-day rolling average of signal counts per topic"

    new_keyword_cluster:
      description: "Entirely new keyword combination not seen in last 30 days"
      threshold: "Cluster of 3+ related signals with no historical precedent"

    volume_spike:
      description: "Sudden increase in article count for a topic"
      threshold: "> 200% of 7-day average"
```

### Type 2: Structural Anomaly

```yaml
structural_anomaly:
  methods:
    cross_domain:
      description: "Signal appears in unexpected STEEPs domain"
      example: "Technology regulation signal appearing primarily in social section"
      threshold: "> 60% of articles in non-primary domain"

    single_source_dominance:
      description: "One news outlet or region dominates coverage (potential bias)"
      threshold: "> 70% of articles from single source or single region"

    temporal_clustering:
      description: "Signals cluster in unusually short time window"
      threshold: "> 5 related signals within 2 hours"

    geographic_isolation:
      description: "Signal reported in only one region despite global relevance"
      threshold: "Only 1 region reporting, topic has global keyword markers"
      note: "WF4-specific: multi-regional coverage enables this detection"

    cross_regional_convergence:
      description: "Unrelated regions simultaneously reporting on new topic"
      threshold: "> 3 regions, no prior coverage, within 24 hours"
      note: "WF4-specific: indicates potential paradigm-level shift"
```

### Anomaly Severity

| Severity | Criteria | Action |
|----------|----------|--------|
| **Low** | Single statistical anomaly | Log and note in report |
| **Medium** | Multiple statistical OR single structural | Highlight in report |
| **High** | Structural + statistical combined | Alert flag in report, notify |

---

## Execution Logic

### Step 1: Load Data
```python
import json

with open(f"{data_root}/structured/classified-signals-{date}.json") as f:
    signals = json.load(f)

with open(f"{data_root}/context/previous-signals.json") as f:
    historical = json.load(f)
```

### Step 2: Compute Tipping Point Indicators
```python
tipping_results = []

# Group signals by topic cluster
clusters = group_by_topic(signals['items'])

for cluster_id, cluster_signals in clusters.items():
    # Get historical data for this cluster
    hist = get_historical_cluster(historical, cluster_id)

    # CSD Detection (Python-computed statistics)
    csd = detect_critical_slowing_down(cluster_signals, hist)

    # Flickering Detection (Python-computed statistics)
    flicker = detect_flickering(cluster_signals, hist)

    # Geographic divergence (WF4-specific)
    geo_div = detect_geographic_divergence(cluster_signals)

    # Determine alert level (LLM interprets combined statistics)
    alert = compute_alert_level(csd, flicker, geo_div)

    if alert != "GREEN":
        tipping_results.append({
            "signal_id": cluster_signals[0]['id'],
            "signal_title": cluster_signals[0]['title'],
            "alert_level": alert,
            "detection_type": determine_primary_type(csd, flicker, geo_div),
            "indicators": {**csd['indicators'], **flicker['indicators']},
            "geographic_scope": list(set(s['source']['region'] for s in cluster_signals)),
            "evidence": generate_evidence_summary(csd, flicker, geo_div),
            "recommended_action": recommend_action(alert)
        })
```

### Step 3: Detect Anomalies
```python
anomalies = []

for signal in signals['items']:
    # Statistical anomalies
    stat = detect_statistical_anomaly(signal, historical)
    if stat['detected']:
        anomalies.append({
            "signal_id": signal['id'],
            "type": "statistical",
            "subtype": stat['method'],
            "severity": stat['severity'],
            "detail": stat['detail']
        })

    # Structural anomalies
    struct = detect_structural_anomaly(signal, signals['items'])
    if struct['detected']:
        anomalies.append({
            "signal_id": signal['id'],
            "type": "structural",
            "subtype": struct['method'],
            "severity": struct['severity'],
            "detail": struct['detail']
        })

    # Geographic anomalies (WF4-specific)
    geo = detect_geographic_anomaly(signal, signals['items'])
    if geo['detected']:
        anomalies.append({
            "signal_id": signal['id'],
            "type": "geographic",
            "subtype": geo['method'],
            "severity": geo['severity'],
            "detail": geo['detail']
        })
```

### Step 4: Write Outputs
```python
# Tipping Point report
write_json(f"{data_root}/analysis/tipping-point-indicators-{date}.json", {
    "analysis_date": date,
    "tipping_point_indicators": tipping_results,
    "overall_alert_status": max_alert(tipping_results),
    "summary": compute_summary(tipping_results, len(signals['items']))
})

# Anomaly report
write_json(f"{data_root}/analysis/anomaly-report-{date}.json", {
    "analysis_date": date,
    "anomalies": anomalies,
    "summary": {
        "total_anomalies": len(anomalies),
        "by_type": count_by_type(anomalies),
        "by_severity": count_by_severity(anomalies)
    }
})
```

---

## Error Handling

```yaml
retry_policy:
  max_attempts: 2
  backoff: "2s, 5s"

  errors:
    InsufficientHistoricalData:
      action: "Skip CSD/Flickering (need >= 7 days history), log warning"
      fallback: "All signals default to GREEN alert"
    AnalysisError:
      action: "Retry with simplified analysis"
    AllRetriesFailed:
      action: "Output empty tipping/anomaly reports, log error, continue pipeline"
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "5-20 seconds"
  depends_on: "Number of signals and historical data depth"

  note: |
    On first run (no historical data), tipping point detection will
    return all GREEN. This is expected -- CSD and Flickering require
    temporal data to detect patterns. After 7+ days of data, detection
    becomes meaningful. Geographic divergence detection (WF4-specific)
    can operate on single-day data if multiple regions are represented.
```

---

## Version
- **Agent Version**: 1.0.0
- **Compatible with**: WF4 Multi&Global-News Environmental Scanning v1.0.0
- **Model**: Sonnet 4.5
- **Last Updated**: 2026-02-24
