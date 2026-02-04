# Realtime Delphi Facilitator Agent

## Role
Facilitate expert panel validation using Real-Time AI Delphi (RT-AID) methodology when large signal volume requires collective intelligence verification.

## Agent Type
**Worker Agent** - Phase 1.5 (Optional/Conditional)

## Activation Condition
**Trigger**: `len(filtered/new-signals-{date}.json) > 50`

When more than 50 new signals detected, this agent activates to accelerate expert consensus gathering from months to days (2-3 days target).

---

## Input

### Required Files
```yaml
inputs:
  filtered_signals:
    path: "filtered/new-signals-{date}.json"
    from: "@deduplication-filter"
    trigger_threshold: 50

  expert_panel_config:
    path: "config/expert-panel.yaml"
    contains:
      - expert_profiles
      - expertise_domains (STEEPs)
      - contact_methods
      - response_window (default: 48 hours)
```

---

## Output

### Primary Output
```yaml
output:
  file: "validated/expert-validated-signals-{date}.json"
  format: "JSON"
  schema:
    validation_metadata:
      total_signals: Integer
      experts_participated: Integer
      consensus_reached: Integer
      response_rate: Float
      rounds_completed: Integer
    validated_signals: Array<ValidatedSignal>
```

### Validated Signal Structure
```json
{
  "validation_metadata": {
    "total_signals": 73,
    "experts_participated": 12,
    "consensus_reached": 68,
    "response_rate": 0.75,
    "rounds_completed": 2,
    "execution_time_hours": 52.3
  },
  "validated_signals": [
    {
      "signal_id": "signal-001",
      "original_data": {...},
      "expert_validation": {
        "importance_score": 4.2,
        "urgency_score": 3.8,
        "impact_score": 4.5,
        "confidence": 0.87,
        "consensus_level": "high",
        "expert_comments": [
          "Significant technological breakthrough",
          "Monitor regulatory response closely"
        ],
        "modified_category": "T",  # If experts suggest recategorization
        "priority_adjustment": "+2"  # Adjust priority up/down
      },
      "ai_initial_assessment": {
        "importance": 3.5,
        "urgency": 3.0,
        "impact": 4.0
      },
      "human_ai_agreement": 0.85
    }
  ]
}
```

---

## Real-Time AI Delphi (RT-AID) Methodology

### Modified Delphi Process

#### Round 1: Initial Assessment
```python
def delphi_round_1(signals, expert_panel):
    """
    AI generates initial assessment for each signal
    Experts provide independent ratings (no AI bias)
    """
    assessments = []

    for signal in signals:
        # AI generates initial analysis
        ai_assessment = generate_ai_assessment(signal)

        # Send to experts WITHOUT showing AI assessment (blind review)
        expert_requests = []
        for expert in select_experts_by_domain(signal['category'], expert_panel):
            request = {
                "expert_id": expert['id'],
                "signal": signal,
                "questions": [
                    "Rate importance (1-5)",
                    "Rate urgency (1-5)",
                    "Rate impact (1-5)",
                    "Suggest category (STEEPs)",
                    "Comments/concerns"
                ],
                "deadline": now() + timedelta(hours=48)
            }
            expert_requests.append(send_expert_request(request))

        assessments.append({
            "signal": signal,
            "ai_assessment": ai_assessment,
            "expert_requests": expert_requests
        })

    return assessments


def generate_ai_assessment(signal):
    """
    AI analyzes signal and provides initial scores
    Uses Claude or similar LLM
    """
    prompt = f"""
    Analyze this signal for environmental scanning:

    Title: {signal['title']}
    Category: {signal['preliminary_category']}
    Source: {signal['source']['name']}
    Content: {signal['content']['abstract']}

    Rate on scale 1-5:
    - Importance: How significant is this signal?
    - Urgency: How quickly should we act?
    - Impact: What is the potential impact scope?

    Provide brief justification for each rating.
    """

    response = call_llm(prompt)
    return parse_ai_ratings(response)
```

#### Round 2: Consensus Building
```python
def delphi_round_2(round_1_results):
    """
    Show aggregated expert opinions and AI assessment
    AI facilitates convergence by highlighting disagreements
    Experts revise their ratings with full context
    """
    for assessment in round_1_results:
        # Collect Round 1 responses
        expert_responses = collect_responses(assessment['expert_requests'])

        # Calculate statistics
        stats = calculate_statistics(expert_responses)

        # AI identifies areas of disagreement
        disagreements = identify_disagreements(
            expert_responses,
            assessment['ai_assessment'],
            threshold=0.3
        )

        # Generate consensus facilitation prompt
        if len(disagreements) > 0:
            facilitation = generate_facilitation_prompt(disagreements)

            # Send Round 2 requests with full context
            for expert in expert_responses.keys():
                round_2_request = {
                    "expert_id": expert,
                    "signal": assessment['signal'],
                    "round_1_your_ratings": expert_responses[expert],
                    "round_1_group_stats": stats,
                    "ai_assessment": assessment['ai_assessment'],
                    "disagreement_areas": disagreements,
                    "facilitation_prompt": facilitation,
                    "question": "Revise your ratings if needed, or explain reasoning",
                    "deadline": now() + timedelta(hours=24)
                }
                send_expert_request(round_2_request)
```

#### Convergence Detection
```python
def check_convergence(round_1, round_2):
    """
    Measure if expert opinions have converged
    Stop if consensus reached, otherwise proceed to Round 3
    """
    convergence_metrics = {
        "importance": calculate_std_dev([r['importance'] for r in round_2]),
        "urgency": calculate_std_dev([r['urgency'] for r in round_2]),
        "impact": calculate_std_dev([r['impact'] for r in round_2])
    }

    # Convergence threshold: Std dev < 0.5 for all metrics
    is_converged = all(std < 0.5 for std in convergence_metrics.values())

    if is_converged:
        log("INFO", "Consensus reached after Round 2")
        return True
    else:
        log("INFO", f"Convergence not reached. Std devs: {convergence_metrics}")
        return False
```

---

## Expert Panel Management

### Expert Selection
```python
def select_experts_by_domain(category, expert_panel):
    """
    Match signal category to expert domains
    Aim for 3-5 experts per signal
    """
    category_map = {
        "S": ["sociology", "demographics", "urban_planning"],
        "T": ["technology", "AI", "engineering", "innovation"],
        "E": ["economics", "finance", "business"],
        "E": ["environment", "climate", "sustainability"],  # Environmental
        "P": ["political_science", "policy", "law", "geopolitics"],
        "s": ["ethics", "philosophy", "psychology", "religion"]
    }

    relevant_domains = category_map.get(category, [])

    selected_experts = [
        expert for expert in expert_panel
        if any(domain in expert['expertise'] for domain in relevant_domains)
    ]

    # Limit to 5 experts to keep manageable
    return selected_experts[:5]
```

### Response Tracking
```python
def track_responses(expert_requests, response_window_hours=48):
    """
    Monitor expert responses in real-time
    Send reminders if no response after 24 hours
    """
    pending = expert_requests.copy()
    responses = []

    deadline = now() + timedelta(hours=response_window_hours)
    reminder_sent = set()

    while now() < deadline and len(pending) > 0:
        # Check for new responses
        for request in pending:
            if has_response(request):
                responses.append(get_response(request))
                pending.remove(request)

        # Send reminders after 24 hours
        if (deadline - now()).total_seconds() < (response_window_hours - 24) * 3600:
            for request in pending:
                if request['expert_id'] not in reminder_sent:
                    send_reminder(request)
                    reminder_sent.add(request['expert_id'])

        time.sleep(3600)  # Check every hour

    # Calculate response rate
    response_rate = len(responses) / len(expert_requests)
    log("INFO", f"Response rate: {response_rate:.1%} ({len(responses)}/{len(expert_requests)})")

    return responses, response_rate
```

---

## AI Facilitation Strategies

### Disagreement Resolution
```python
def generate_facilitation_prompt(disagreements):
    """
    AI generates targeted prompts to facilitate consensus
    """
    prompt_templates = {
        "importance_disagreement": """
        Experts disagree on importance (range: {min}-{max}).
        High scorers noted: {high_reasons}
        Low scorers noted: {low_reasons}
        Consider: What criteria matter most for "importance"?
        """,

        "category_disagreement": """
        Signal categorization split between {categories}.
        This suggests cross-domain nature.
        Consider: Is this a hybrid signal? What's the primary domain?
        """
    }

    facilitations = []
    for disagree in disagreements:
        template = prompt_templates.get(disagree['type'])
        facilitation = template.format(**disagree['details'])
        facilitations.append(facilitation)

    return facilitations
```

### AI-Expert Agreement Tracking
```python
def calculate_human_ai_agreement(expert_responses, ai_assessment):
    """
    Measure agreement between AI and expert consensus
    Used for continuous AI model improvement
    """
    expert_avg = {
        "importance": mean([r['importance'] for r in expert_responses]),
        "urgency": mean([r['urgency'] for r in expert_responses]),
        "impact": mean([r['impact'] for r in expert_responses])
    }

    # Calculate mean absolute error
    mae = mean([
        abs(expert_avg['importance'] - ai_assessment['importance']),
        abs(expert_avg['urgency'] - ai_assessment['urgency']),
        abs(expert_avg['impact'] - ai_assessment['impact'])
    ])

    # Convert to agreement score (0-1, where 1 = perfect agreement)
    agreement = 1 - (mae / 5.0)

    return agreement
```

---

## TDD Verification

### Unit Tests (< 5 seconds)
```python
def test_delphi_output():
    output = load_json(f"validated/expert-validated-signals-{today()}.json")

    # Test 1: File exists
    assert output is not None, "Validated file not created"

    # Test 2: Metadata present
    assert "validation_metadata" in output
    assert "validated_signals" in output

    # Test 3: Response rate threshold
    response_rate = output['validation_metadata']['response_rate']
    assert response_rate > 0.5, f"Low response rate: {response_rate}"

    # Test 4: Consensus reached for most signals
    consensus_rate = output['validation_metadata']['consensus_reached'] / output['validation_metadata']['total_signals']
    assert consensus_rate > 0.7, "Low consensus rate"

    # Test 5: Score ranges (1-5)
    for signal in output['validated_signals']:
        validation = signal['expert_validation']
        assert 1 <= validation['importance_score'] <= 5
        assert 1 <= validation['urgency_score'] <= 5
        assert 1 <= validation['impact_score'] <= 5

    # Test 6: Execution time within target (< 3 days = 72 hours)
    exec_time = output['validation_metadata']['execution_time_hours']
    assert exec_time < 72, f"Exceeded target: {exec_time} hours"

    log("PASS", "Realtime Delphi output validation passed")
```

---

## Performance Targets

```yaml
performance_targets:
  response_window: "48 hours per round"
  total_time: "< 72 hours (3 days)"
  response_rate: "> 70%"
  consensus_rate: "> 80%"
  human_ai_agreement: "> 0.8"

  vs_traditional_delphi:
    speedup: "10-15x faster (months → days)"
    quality: "comparable or better"
```

---

## Error Handling

### Error Codes
- `E1501`: Expert panel configuration missing
- `E1502`: Low response rate (< 50%)
- `E1503`: Consensus not reached after 3 rounds
- `E1504`: Expert communication failure

### Fallback Strategy
```python
def handle_low_response_rate(response_rate):
    if response_rate < 0.5:
        log("WARNING", f"Low response rate: {response_rate:.1%}")

        # Option 1: Extend deadline by 24 hours
        extend_deadline(24)

        # Option 2: Proceed with available responses
        # Use AI to weight responses based on expert reliability scores

        # Option 3: Skip Phase 1.5 and continue with AI-only assessment
        log("INFO", "Proceeding without expert validation (Phase 1.5 skipped)")
        return None
```

---

## Logging

```python
log_examples = {
    "START": "Realtime Delphi facilitator activated. 73 signals require validation.",
    "INFO": "Selected 12 experts across STEEPs domains",
    "INFO": "Round 1 requests sent. Deadline: 2026-01-30T18:00:00Z",
    "INFO": "Round 1 responses: 9/12 (75% response rate)",
    "INFO": "Identified 15 disagreement areas. Preparing Round 2...",
    "INFO": "Round 2 requests sent with facilitation prompts",
    "INFO": "Round 2 responses: 10/12 (83% response rate)",
    "INFO": "Consensus reached for 68/73 signals (93%)",
    "INFO": "Human-AI agreement: 0.87 (high)",
    "SUCCESS": "Validation complete: validated/expert-validated-signals-2026-01-29.json",
    "END": "Realtime Delphi completed in 52.3 hours"
}
```

---

## Configuration Example

### expert-panel.yaml
```yaml
expert_panel:
  - id: "expert-001"
    name: "Dr. Jane Smith"
    expertise: ["AI", "technology", "ethics"]
    steeps_domains: ["T", "s"]
    email: "jane.smith@university.edu"
    reliability_score: 0.92

  - id: "expert-002"
    name: "Prof. John Doe"
    expertise: ["climate", "sustainability", "policy"]
    steeps_domains: ["E", "P"]  # Environmental, Political
    email: "john.doe@institute.org"
    reliability_score: 0.88

  # ... more experts

response_settings:
  default_window_hours: 48
  reminder_after_hours: 24
  max_rounds: 3
  consensus_threshold: 0.5  # Std dev threshold
```

---

## Dependencies

### Required Tools
- Email/messaging service (for expert communication)
- LLM API (Claude, GPT) for AI assessment and facilitation
- Statistical analysis tools (numpy, scipy)

### Required Files
- `config/expert-panel.yaml`
- `filtered/new-signals-{date}.json`

---

## Integration Points

### Called By
- Orchestrator Agent (Phase 1.5, conditional)

### Inputs From
- `@deduplication-filter` (filtered signals)

### Outputs Used By
- `@signal-classifier` (Step 2.1, uses validated signals if available)

---

## Version
- **Agent Version**: 1.0.0
- **Compatible with**: Enhanced Environmental Scanning Workflow v1.0
- **Methodology**: Real-Time AI Delphi (RT-AID)
- **Last Updated**: 2026-01-29
