---
name: revision
description: Request report revision with specific feedback (Phase 3, Step 3.4)
---

# Request Report Revision

Provide feedback to request changes to the generated report before final approval.

## Usage

```bash
/revision "your feedback here"
```

## Arguments

**feedback** (required): String describing requested changes

## When To Use

Use this command at **Phase 3, Step 3.4** when reviewing the final report, BEFORE using `/approve`.

## Common Revision Requests

### Add More Detail
```bash
/revision "상위 5개 신호에 대해 더 상세한 분석 추가"
```

### Adjust Tone
```bash
/revision "경영진 요약을 더 간결하게 수정 (현재 너무 길음)"
```

### Add Scenarios
```bash
/revision "기술-경제 교차 영역에 대한 시나리오 분석 추가"
```

### Fix Errors
```bash
/revision "신호 ID-042의 출처 링크 수정 및 분류 재검토"
```

### Emphasize Certain Aspects
```bash
/revision "지정학적 리스크 부분을 더 강조하고 구체적 대응 방안 추가"
```

## What Happens After Revision Request

1. **Feedback recorded** in workflow log
2. **Report generator re-invoked** with your feedback
3. **Report regenerated** incorporating changes
4. **New report displayed** for your review
5. **Approval prompt repeated**

## Example Interaction

```
/revision "상위 3개 신호에 대해 구체적인 시나리오 분석 추가 필요. 현재 전략적 시사점이 너무 일반적임."

═══════════════════════════════════════════════════
   Report Revision Requested
═══════════════════════════════════════════════════

Feedback received:
"상위 3개 신호에 대해 구체적인 시나리오 분석 추가 필요.
현재 전략적 시사점이 너무 일반적임."

Processing revision...
  ⏳ Analyzing feedback
  ⏳ Regenerating report sections
  ⏳ Incorporating scenario analysis
  ✓ Report updated (18,456 words)

─────────────────────────────────────────────────
Updated Report Preview
─────────────────────────────────────────────────

[New report sections displayed...]

Changes made:
  ✓ Added detailed scenario analysis for top 3 signals
  ✓ Enhanced strategic implications with specific actions
  ✓ Included timeline projections (3-month, 6-month, 12-month)

─────────────────────────────────────────────────
Decision Required
─────────────────────────────────────────────────

Commands:
  /approve - Accept revised report
  /revision "feedback" - Request further changes

> Awaiting your decision...
```

## Multiple Revisions

You can request revisions multiple times:

```bash
# First revision
/revision "시나리오 추가"

# After reviewing...
# Second revision
/revision "지금은 좋음. 단, 부록에 참고문헌 추가"

# After final review...
/approve
```

## Revision Best Practices

✅ **Do**:
- Be specific about what needs changing
- Reference specific sections or signals
- Provide clear direction

❌ **Don't**:
- Request vague changes like "make it better"
- Ask for complete rewrites (consider rerunning workflow instead)
- Request changes outside report scope

## Example Revision Requests

### Good Examples

```bash
/revision "신호 ID-015의 영향도 평가를 4→5로 상향하고 이유 설명 추가"

/revision "경영진 요약에 즉시 조치 필요 항목 3가지를 명확히 나열"

/revision "기술-정치 교차 영역의 규제 리스크에 대한 분석 강화"
```

### Poor Examples

```bash
/revision "더 좋게 해주세요"  # Too vague

/revision "전부 다시 작성"  # Use /run-daily-scan instead

/revision "내일 회의 자료로 변환"  # Outside scope
```

## Tracking Revisions

All revision requests are logged in:
- `logs/workflow-status.json` - Workflow state
- `logs/revision-history-{date}.json` - Full revision history

## Related Commands

- `/approve` - Approve report after revisions
- `/status` - Check workflow state during revision

## Notes

- No limit on revision requests (within reason)
- Each revision regenerates the entire report
- Previous versions are not saved (only final approved version)
- Revisions take 20-40 seconds depending on scope

## Version
**Command Version**: 1.0.0
**Last Updated**: 2026-01-29
