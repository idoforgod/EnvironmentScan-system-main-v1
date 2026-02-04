---
name: review-analysis
description: Review analysis results and adjust signal priorities (Phase 2, Step 2.5)
---

# Review Analysis Results

Review the top priority signals, verify STEEPs classifications, adjust priority rankings, and provide comments before proceeding to report generation.

## Usage

```bash
/review-analysis
```

## When To Use

This command is triggered at **Phase 2, Step 2.5** after signal classification, impact analysis, and priority ranking are complete. It's a **REQUIRED** checkpoint before moving to Phase 3.

## What You'll Review

### 1. Top 10 Priority Signals
Displayed with full details:
- Title and category (STEEPs)
- Priority score and component scores
- Impact assessment summary
- Current classification

### 2. STEEPs Distribution
Chart showing signal distribution across categories:
- S (Social): X signals
- T (Technological): Y signals
- E (Economic): Z signals
- Etc.

### 3. Cross-Impact Highlights
Key signal interactions identified in the cross-impact matrix

## Review Questions

You'll be asked:

1. **STEEPs Classification Accuracy**
   - "Are the STEEPs classifications correct for top 10 signals?"
   - Options: Yes / No, specify corrections

2. **Priority Adjustments**
   - "Do any signals need priority adjustment?"
   - Options: No adjustments / Adjust specific signals

3. **Additional Comments**
   - "Any additional insights or concerns?"
   - Free text input

## Example Interaction (Bilingual Display - KR Default)

```
═══════════════════════════════════════════════════
   분석 결과 검토 (Phase 2, Step 2.5)
   Analysis Review
═══════════════════════════════════════════════════

📊 데이터 파일 / Data Files:
   • 한국어 / Korean: analysis/priority-ranked-2026-01-30-ko.json
   • English: analysis/priority-ranked-2026-01-30.json

최우선 순위 신호 Top 10 / Top 10 Priority Signals:

─────────────────────────────────────────────────
순위 #1 / Rank #1: IBM의 1000큐빗 양자 프로세서 실증
IBM Demonstrates 1000-Qubit Quantum Processor
─────────────────────────────────────────────────

Category: T (Technological)
우선순위 점수 / Priority Score: 4.72 / 5.00
  • 영향도 / Impact: 4.8
  • 발생 가능성 / Probability: 4.5
  • 긴급도 / Urgency: 5.0
  • 신규성 / Novelty: 4.2

출처 / Source: Nature, 2026-01-28
중요도 / Significance: ⭐⭐⭐⭐⭐

영향도 요약 / Impact Summary:
  1차 영향 / 1st order: 제약 R&D 가속화
                        Drug R&D acceleration
  2차 영향 / 2nd order: 헬스케어 비용 감소 가능성
                        Healthcare cost reduction potential
  교차 영향 / Cross-impact: +4 with AI 모델 훈련 신호
                            +4 with AI model training signal

[2-10위 신호 계속 / Continue for ranks 2-10...]

─────────────────────────────────────────────────
STEEPs 분포 / STEEPs Distribution
─────────────────────────────────────────────────

T (Technological): 32개 신호 / 32 signals (41%)
E (Economic): 22개 신호 / 22 signals (28%)
P (Political): 14개 신호 / 14 signals (18%)
E (Environmental): 7개 신호 / 7 signals (9%)
S (Social): 3개 신호 / 3 signals (4%)
s (spiritual): 1개 신호 / 1 signal (1%)

─────────────────────────────────────────────────
📋 검토 질문 / Review Questions
─────────────────────────────────────────────────

질문 1 / Question 1: STEEPs 분류가 정확합니까?
                     Are STEEPs classifications accurate?
  ○ 예, 모두 정확함 / Yes, all correct
  ○ 아니오, 수정 필요 / No, corrections needed

> 선택 / Your selection: [입력 대기 / Wait for input]

[If "No"]:
수정이 필요한 신호 / Which signals need reclassification?
Signal ID: signal-042
현재 / Current: T (Technological)
수정 / Corrected: s (spiritual)
이유 / Reason: AI 윤리에 초점, 기술 자체가 아님
              Focuses on AI ethics, not technology itself

질문 2 / Question 2: 우선순위 조정이 필요합니까?
                     Priority adjustments needed?
  ○ 조정 불필요 / No adjustments
  ○ 우선순위 상향 / Boost signal priority: [Signal ID] +1 or +2
  ○ 우선순위 하향 / Lower signal priority: [Signal ID] -1 or -2

> 선택 / Your selection: [입력 대기 / Wait for input]

질문 3 / Question 3: 추가 의견이 있습니까?
                     Additional comments?
> [자유 텍스트 입력 / Free text input]

─────────────────────────────────────────────────
✓ 검토 완료 / Review Complete
─────────────────────────────────────────────────

적용된 변경사항 / Changes applied:
  • signal-042 재분류 / Reclassified: T → s
  • signal-015 우선순위 상향 / Boosted priority: +2

Phase 3로 진행 중 / Continuing to Phase 3: Implementation...

💡 팁 / Tip: 영어 원본을 확인하려면 위 파일 경로를 참조하세요
           To view English original, refer to file path above
```

## After Review

1. **Changes applied** to analysis results
2. **Workflow resumes** automatically
3. **Phase 3 begins**: Database update, report generation
4. **Updated rankings** reflected in final report

## Related Commands

- `/status` - Check if review is needed
- `/revision` - Request changes after report generation (Step 3.4)

## Notes

- This is a **required** checkpoint - workflow won't proceed without it
- Take time to carefully review top signals
- Your corrections improve future AI classification accuracy
- All changes are logged in `logs/human-corrections.json`

## Bilingual Display

By default, this command displays content in **Korean with English context**:
- Main interface: Korean (사용자 친화적)
- Technical terms: Preserved in English (STEEPs, category codes)
- File references: Both KR and EN paths provided
- User can access EN original files anytime

To view English-only display, use the EN version file path shown in output.

## Version
**Command Version**: 1.1.0 (Bilingual KR-First)
**Last Updated**: 2026-01-30
