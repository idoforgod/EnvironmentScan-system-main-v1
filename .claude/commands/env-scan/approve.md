---
name: approve
description: Approve final environmental scanning report and complete workflow (Phase 3, Step 3.4)
---

# Approve Final Report

Review and approve the generated environmental scanning report to complete the workflow.

## Usage

```bash
/approve
```

## When To Use

This command is triggered at **Phase 3, Step 3.4** after the Korean report has been generated. It's the **FINAL** checkpoint before workflow completion.

## What Happens When You Approve

1. **Report is finalized** - No further changes
2. **Archiving completes** - Report copied to archive directory
3. **Notifications sent** - Email/Slack alerts (if configured)
4. **Workflow marked complete** - Status updated to "completed"
5. **Quality metrics generated** - Performance report saved

## Before Approving

Review the generated report:

```bash
# Primary report (Korean with inline English terms):
reports/daily/environmental-scan-{date}.md

# This report will be displayed automatically when you reach Step 3.4
```

## Completeness Checklist

Verify these items before approving:

**보고서 구조 (Report Structure)**:
- [ ] Section 1: 경영진 요약 (Top 3 signals + summary stats)
- [ ] Section 2: 신규 탐지 신호 (Top 10 with 9 fields each)
- [ ] Section 3: 기존 신호 업데이트 (강화/약화 추세)
- [ ] Section 4: 패턴 및 연결고리 (교차 영향 + 테마)
- [ ] Section 5: 전략적 시사점 (즉시/중기/모니터링 3-subsection)
- [ ] Section 7: 신뢰도 분석 (pSST or fallback)
- [ ] Section 8: 부록 (signal list + sources + methodology)

**품질 (Quality)**:
- [ ] Natural Korean phrasing (proper nouns in English)
- [ ] STEEPs terms preserved (S, T, E, E, P, s)
- [ ] Strategic implications are specific and actionable (not generic)
- [ ] Source links valid
- [ ] Top 10 signals each have all 9 required fields

## Example Interaction

```
═══════════════════════════════════════════════════
   최종 보고서 승인 / Final Report Approval
   (Phase 3, Step 3.4)
═══════════════════════════════════════════════════

생성된 보고서 / Generated Report:

  📄 reports/daily/environmental-scan-2026-01-30.md
     15,234 단어 (Korean with inline English terms)

보고서 섹션 / Report Sections:
  ✓ 1. 경영진 요약 / Executive Summary (Top 3 signals)
  ✓ 2. 신규 탐지 신호 / New Signals (79 signals, top 10 detailed)
  ✓ 3. 기존 신호 업데이트 / Signal Updates (12 updates)
  ✓ 4. 패턴 및 연결고리 / Patterns (5 cross-impact pairs, 3 themes)
  ✓ 5. 전략적 시사점 / Strategic Implications (3 subsections)
  ✓ 7. 신뢰도 분석 / Trust Analysis (pSST distribution)
  ✓ 8. 부록 / Appendix (full list + sources)

품질 검사 / Quality Checks:
  ✓ 모든 필수 섹션 포함 / All mandatory sections present (7/7)
  ✓ 상위 10개 신호 필드 완전 / Top 10 signal fields complete (9/9 each)
  ✓ 한국어 자연스러움 / Natural Korean phrasing
  ✓ STEEPs 용어 정확 / STEEPs terms accurate (100%)
  ✓ 전략적 시사점 3-구조 / Strategic implications 3-subsection ✓
  ✓ 출처 링크 유효 / Source links valid (98%)

─────────────────────────────────────────────────

[보고서 미리보기 / Report Preview]

# 일일 환경 스캐닝 보고서
**날짜**: 2026년 1월 30일

## 1. 경영진 요약

### 오늘의 핵심 발견 (Top 3 신호)
...

─────────────────────────────────────────────────
결정 필요 / Decision Required
─────────────────────────────────────────────────

명령 / Commands:
  /approve - 보고서 승인 및 워크플로우 완료
  /revision "피드백" - 수정 요청

> 결정을 기다리는 중 / Awaiting your decision...
```

## After Approval

```
✓ 보고서 승인됨 / Report approved

워크플로우 완료 중 / Finalizing workflow...
  ✓ 보고서 아카이브 / Report archived to reports/archive/2026/01/
  ✓ 신호 스냅샷 저장 / Signal snapshot saved
  ✓ 알림 발송 / Notifications sent (if configured)
  ✓ 품질 지표 저장 / Quality metrics saved

═══════════════════════════════════════════════════
✅ 워크플로우 성공적으로 완료 / Workflow Completed Successfully
═══════════════════════════════════════════════════

Workflow ID: scan-2026-01-30

요약 / Summary:
  • 신규 신호 탐지 / New signals detected: 79
  • 최우선 / High priority: 15
  • 중복 제거 / Duplicates removed: 168 (68%)

산출물 / Artifacts:

  📄 일일 보고서 / Daily Report:
     • reports/daily/environmental-scan-2026-01-30.md (Korean)

  📄 아카이브 / Archive:
     • reports/archive/2026/01/environmental-scan-2026-01-30.md

  💾 데이터베이스 / Database:
     • signals/database.json (updated)

  📸 스냅샷 / Snapshot:
     • signals/snapshots/database-2026-01-30.json

다음 단계 / Next Steps:
  • 이해관계자와 보고서 검토
  • 최우선 신호의 선행 지표 모니터링
  • 다음 스캔 예정 / Next scan scheduled: 내일 06:00

═══════════════════════════════════════════════════
```

## If You Need Changes

Instead of approving, use `/revision` command:

```bash
/revision "상위 5개 신호에 대해 시나리오 분석 추가"
```

This will:
1. Keep workflow in Step 3.4
2. Send feedback to report generator
3. Regenerate report with requested changes
4. Prompt for approval again

## Related Commands

- `/status` - Check if report is ready for approval
- `/revision "feedback"` - Request changes instead of approving

## Notes

- Approval is **final** - report cannot be changed after approval
- If unsure, request revision rather than approving prematurely
- Approved reports are archived with timestamp
- You can always regenerate with `/revision` before approving

## Report Language

The report is generated in **Korean** as the primary user-facing output.
English technical terms, proper nouns, and acronyms are preserved inline.
The internal data files (JSON) remain in English.

## Version
**Command Version**: 1.2.0
**Last Updated**: 2026-02-01
**Changelog**: v1.2.0 - Removed separate -ko.md file references. Single Korean report is the primary output. Updated checklist to match mandatory section structure.
