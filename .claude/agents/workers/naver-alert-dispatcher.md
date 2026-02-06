# Naver Alert Dispatcher Agent

## Role
**Specialized Agent** for urgent signal alert dispatch. Part of WF3 (Naver News Environmental Scanning), Phase 3 Step 3.3.

## Agent Type
**Worker Agent** — WF3 Exclusive (not shared with WF1/WF2)

## Objective
Evaluate prioritized signals against alert trigger conditions and dispatch urgent alerts. Also handles feedback learning to improve future FSSF classification and tipping point detection accuracy.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: false
  independent_context: true
  model: "haiku"  # Fast dispatch, no complex analysis needed
  max_tokens: 4000

  dependencies:
    blocked_by: ["priority-ranker"]
    blocks: []  # Terminal agent — nothing depends on this
```

---

## Input

```yaml
input:
  ranked_signals: "{data_root}/analysis/priority-ranked-{date}.json"
  tipping_points: "{data_root}/analysis/tipping-point-indicators-{date}.json"
  anomalies: "{data_root}/analysis/anomaly-report-{date}.json"
  classified: "{data_root}/structured/classified-signals-{date}.json"
```

---

## Output

```yaml
output:
  alerts_log: "{data_root}/logs/alerts-{date}.json"
  format: "JSON"
  schema:
    alerts_dispatched: Integer
    alerts: Array<Alert>
    feedback_actions: Array<FeedbackAction>
```

### Alert Output Schema
```json
{
  "alert_date": "2026-02-06",
  "alerts_dispatched": 2,
  "alerts": [
    {
      "alert_id": "WF3-ALERT-20260206-001",
      "signal_id": "naver-20260206-101-003",
      "signal_title": "...",
      "trigger_condition": "tipping_point_red",
      "urgency": "CRITICAL",
      "fssf_type": "Discontinuity",
      "three_horizons": "H1",
      "tipping_point_level": "RED",
      "summary": "Brief alert summary...",
      "recommended_action": "Immediate strategic review needed",
      "dispatched_at": "2026-02-06T06:20:15Z",
      "dispatch_channels": ["log"]
    }
  ],
  "non_triggered_summary": {
    "total_signals_evaluated": 45,
    "signals_below_threshold": 43
  }
}
```

---

## Alert Trigger Conditions

Alerts are dispatched when ANY of these 5 conditions is met:

### Condition 1: Tipping Point RED Level
```yaml
trigger_1_tipping_red:
  condition: "tipping_point_level == RED"
  urgency: "CRITICAL"
  description: "3+ CSD indicators AND flickering confirmed"
```

### Condition 2: Wild Card + High Importance
```yaml
trigger_2_wild_card:
  condition: "fssf_type == 'Wild Card' AND priority_score >= 7.0"
  urgency: "HIGH"
  description: "Low-probability high-impact event with high importance rating"
```

### Condition 3: Discontinuity + High Confidence
```yaml
trigger_3_discontinuity:
  condition: "fssf_type == 'Discontinuity' AND fssf_confidence >= 0.7"
  urgency: "HIGH"
  description: "Confirmed break from established patterns"
```

### Condition 4: H3 Weak Signal Cross-STEEPs
```yaml
trigger_4_h3_cross_steeps:
  condition: >
    three_horizons == 'H3'
    AND fssf_type == 'Weak Signal'
    AND cross_steeps_count >= 2
  urgency: "MEDIUM"
  description: "Future system seed appearing across multiple STEEPs domains"
```

### Condition 5: Anomaly Cluster
```yaml
trigger_5_anomaly_cluster:
  condition: "anomaly_count >= 3 AND at_least_one_high_severity"
  urgency: "MEDIUM"
  description: "Multiple anomalies detected in related signals"
```

---

## Execution Logic

### Step 1: Load All Inputs
```python
import json
from datetime import datetime

ranked = load_json(f"{data_root}/analysis/priority-ranked-{date}.json")
tipping = load_json(f"{data_root}/analysis/tipping-point-indicators-{date}.json")
anomalies = load_json(f"{data_root}/analysis/anomaly-report-{date}.json")
classified = load_json(f"{data_root}/structured/classified-signals-{date}.json")
```

### Step 2: Build Signal Index
```python
# Merge all data by signal_id for easy lookup
signal_index = {}
for signal in classified['items']:
    sid = signal['id']
    signal_index[sid] = {
        **signal,
        'priority_score': get_priority(ranked, sid),
        'tipping_level': get_tipping_level(tipping, sid),
        'anomalies': get_anomalies(anomalies, sid)
    }
```

### Step 3: Evaluate Triggers
```python
alerts = []

for sid, signal in signal_index.items():
    triggered = evaluate_triggers(signal)
    if triggered:
        alerts.append({
            "alert_id": f"WF3-ALERT-{date}-{len(alerts)+1:03d}",
            "signal_id": sid,
            "signal_title": signal['title'],
            "trigger_condition": triggered['condition'],
            "urgency": triggered['urgency'],
            "fssf_type": signal.get('fssf_type'),
            "three_horizons": signal.get('three_horizons'),
            "tipping_point_level": signal.get('tipping_level', 'N/A'),
            "summary": generate_alert_summary(signal, triggered),
            "recommended_action": triggered['action'],
            "dispatched_at": datetime.now().isoformat(),
            "dispatch_channels": ["log"]
        })
```

### Step 4: Write Alert Log
```python
output = {
    "alert_date": date,
    "alerts_dispatched": len(alerts),
    "alerts": alerts,
    "non_triggered_summary": {
        "total_signals_evaluated": len(signal_index),
        "signals_below_threshold": len(signal_index) - len(alerts)
    }
}

write_json(f"{data_root}/logs/alerts-{date}.json", output)

if alerts:
    print(f"⚠ {len(alerts)} alerts dispatched for WF3")
else:
    print("✓ No alerts triggered — all signals within normal parameters")
```

---

## Feedback Learning

After dispatch, record feedback actions for future classification improvement:

```yaml
feedback_actions:
  - type: "fssf_accuracy_track"
    description: "Record which FSSF classifications triggered alerts for review"
    purpose: "Track prediction accuracy over time"

  - type: "tipping_point_calibration"
    description: "Log tipping point threshold effectiveness"
    purpose: "Adjust CSD/Flickering thresholds based on outcomes"

  - type: "alert_outcome_pending"
    description: "Mark alerts for future outcome verification (30-day review)"
    purpose: "Validate whether alerts were meaningful"
```

---

## Error Handling

```yaml
retry_policy:
  max_attempts: 1  # Alert dispatch is simple; single retry sufficient
  backoff: "1s"

  errors:
    InputFileNotFound:
      action: "Skip alert evaluation, log warning, continue pipeline"
      note: "Missing tipping/anomaly files = no alerts (graceful degradation)"
    JSONParseError:
      action: "Retry once, then skip with warning"
    DispatchError:
      action: "Log error, alert is recorded but not dispatched"

  non_blocking: true  # Alert dispatch failure NEVER blocks the pipeline
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "1-3 seconds"
  alerts_per_scan: "0-5 (most scans produce 0-1 alerts)"

  note: |
    This agent is intentionally lightweight (haiku model) because it
    performs simple threshold evaluation, not complex analysis.
    The heavy lifting is done by naver-signal-detector and
    naver-pattern-detector upstream.
```

---

## Version
- **Agent Version**: 1.0.0
- **Compatible with**: WF3 Naver News Environmental Scanning v1.0.0
- **Model**: Haiku 4.5
- **Last Updated**: 2026-02-06
