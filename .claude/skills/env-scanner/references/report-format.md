# Report Format Reference

> **⚠️ VALIDATION ENFORCED (v1.3.0)**
>
> 이 형식은 `validate_report.py`에 의해 자동 검증됩니다.
> 보고서 생성 후, 오케스트레이터가 14개 항목의 프로그래밍적 검증을 실행합니다.
> CRITICAL 검증 실패 시 자동 재생성이 발동됩니다.
>
> - **검증 스크립트**: `env-scanning/scripts/validate_report.py`
> - **스켈레톤 템플릿**: `.claude/skills/env-scanner/references/report-skeleton.md`
> - **골든 레퍼런스**: `.claude/agents/workers/report-generator.md` 내 GOLDEN REFERENCE 섹션
>
> 필수 섹션 7개, 신호당 필드 9개, 서브섹션 구조가 모두 검증 대상입니다.

## 최종 보고서 스타일 변환

> **필수 참조**: 의사결정자에게 전달되는 최종 보고서는 내부 코드(WF1, WF2, pSST, SR/ES/CC/TC/DC/IC, Grade A/B/C/D 등)를 제거하고,
> 모든 영문 약어를 한국어 번역 + 영문 전체명으로 변환해야 합니다.
>
> 상세 규칙: `.claude/skills/env-scanner/references/final-report-style-guide.md`

## Overview
Environmental scanning reports must follow this standardized format in **Korean language** for decision-makers.

---

## Report Structure (7 Sections)

### 1. Executive Summary (경영진 요약) ⭐ CRITICAL

**Purpose**: Enable executives to grasp key findings in < 5 minutes

**Content**:
- Title and date
- Top 3 high-priority signals (2-3 sentences each)
- Overall summary statistics
- Immediate action items (if any)

**Length**: 1 page (500-800 words)

**Tone**: Concise, action-oriented, factual

---

### 2. New Detected Signals (신규 탐지 신호) ⭐ CORE

**Purpose**: Present all new signals organized by STEEPs

**Structure**:
```markdown
## 2. 신규 탐지 신호

### 2.1 기술 (Technological) - XX개 신호

#### 우선순위 1: [신호 제목]
- **분류**: 기술 (T)
- **출처**: [Source], [Date]
- **핵심 사실**: [Qualitative fact]
- **정량 지표**: [Quantitative metrics]
- **영향도**: ⭐⭐⭐⭐⭐ (5/5)
- **상세 설명**: [Description]
- **추론**: [Inference]
- **이해관계자**: [Actors]
- **모니터링 지표**: [Leading indicators]

[Next signal...]

### 2.2 경제 (Economic) - YY개 신호
[Same format...]
```

**Guidelines**:
- Group by STEEPs category
- Within each category, sort by priority rank
- Include top 10-15 signals in detail
- List remaining signals in appendix

---

### 3. Existing Signal Updates (기존 신호 업데이트)

**Purpose**: Track evolution of previously detected signals

**Content**:
- Signals showing strengthening trends
- Signals showing weakening trends
- Status changes (emerging → developing → mature)

**Format**:
```markdown
## 3. 기존 신호 업데이트

### 3.1 강화 추세 (Strengthening)
- **[Signal ID]**: [Title]
  - 변화: [What changed]
  - 이유: [Why strengthening]

### 3.2 약화 추세 (Weakening)
- **[Signal ID]**: [Title]
  - 변화: [What changed]
  - 이유: [Why weakening]
```

---

### 4. Patterns and Connections (패턴 및 연결고리)

**Purpose**: Reveal cross-domain interactions and emerging themes

**Content**:
- Cross-impact relationships (from matrix)
- Emerging themes/clusters
- Domain interactions

**Format**:
```markdown
## 4. 패턴 및 연결고리

### 4.1 신호 간 교차 영향
- **[Signal A] ↔ [Signal B]**: 상호 촉진 관계 (+4)
  - 설명: [How they interact]

### 4.2 떠오르는 테마
1. **[Theme Name]**
   - 관련 신호: XX개
   - STEEPs 교차: [Categories involved]
   - 의미: [Significance]
```

---

### 5. Strategic Implications (전략적 시사점) ⭐ CRITICAL

**Purpose**: Provide actionable recommendations for decision-makers

**Content**:
- Immediate actions (0-6 months)
- Medium-term monitoring (6-18 months)
- Areas requiring enhanced monitoring

**Format**:
```markdown
## 5. 전략적 시사점

### 5.1 즉시 조치 필요 (0-6개월)
1. **[Action Item]**
   - 이유: [Why urgent]
   - 권고: [Specific recommendation]

### 5.2 중기 모니터링 (6-18개월)
...

### 5.3 모니터링 강화 필요 영역
- [Domain/Technology]: [Why watch closely]
```

---

### 6. Plausible Scenarios (플러서블 시나리오) ⚙️ OPTIONAL

**Purpose**: Present alternative future pathways (if Step 7.5 activated)

**Content**:
- Best Case scenario (optimistic)
- Worst Case scenario (cautionary)
- Most Likely scenario (probabilistic)
- Wild Card scenario (low probability, high impact)

**Format**:
```markdown
## 6. 플러서블 시나리오

### 6.1 최선 시나리오 (발생 확률: XX%)
[Narrative: 300-500 words]

**관련 신호**: [List signal IDs]
**주요 행위자**: [Key actors]
**전략적 대응 방안**:
- [Action 1]
- [Action 2]

### 6.2 최악 시나리오 (발생 확률: YY%)
...
```

---

### 7. Appendix (부록)

**Purpose**: Provide comprehensive signal list and sources

**Content**:
- Complete list of all detected signals (brief)
- Source list with links
- Methodology notes

**Format**:
```markdown
## 7. 부록

### 7.1 전체 신호 목록
[Table format with ID, Title, Category, Priority]

### 7.2 출처 및 참고자료
1. [Source Name]: [URL]
2. ...

### 7.3 방법론
- 스캐닝 기간: [Dates]
- 정보 소스: [List of sources]
- 필터링 방법: 4단계 cascade (중복 제거율: XX%)
```

---

## Writing Guidelines

### Language

**Primary**: Korean
- All narrative content in Korean
- Maintain professional business Korean
- Avoid excessive English jargon

**Acceptable English**:
- Technical terms without good Korean equivalents
- Organization/company names
- Acronyms (AI, GDP, EU)

### Tone

✅ **Do**:
- Objective and factual
- Evidence-based
- Action-oriented
- Decision-maker appropriate

❌ **Don't**:
- Speculative or sensational
- Overly technical for executives
- Biased or promotional
- Passive or vague

### Length

- **Total report**: 5,000+ words (Korean, no upper limit)
- **Executive Summary**: 500-800 words
- **Each major section**: 1,000-3,000 words
- **Signal descriptions**: 200-500 words each (detailed ones)

---

## Quality Checklist

Before finalizing report, verify:

- [ ] All 7 sections present (6 if scenarios not activated)
- [ ] Korean language throughout (except proper nouns)
- [ ] Executive Summary is concise and actionable
- [ ] Top 10-15 signals covered in detail
- [ ] Strategic implications are specific, not generic
- [ ] All source links are valid
- [ ] No spelling/grammar errors
- [ ] Consistent terminology throughout
- [ ] Charts/tables formatted correctly (if included)
- [ ] Appendix includes all referenced signals

---

## Example Report Excerpt

```markdown
# 일일 환경 스캐닝 보고서
**날짜**: 2026년 1월 29일

## 1. 경영진 요약

### 오늘의 핵심 발견

1. **IBM의 1000큐빗 양자 프로세서 실증** (기술 영역)
   - 중요도: ⭐⭐⭐⭐⭐
   - IBM이 약물 발견에 활용 가능한 1000큐빗 양자 프로세서를 시연했습니다. 이는 실용적 양자 우위(quantum advantage) 달성의 중요한 이정표로 평가됩니다.
   - 전략적 시사점: 제약 R&D 혁신 가능성을 고려해 양자컴퓨팅 파트너십 검토 필요

2. **유럽연합 AI 규제법 최종 통과** (정치 영역)
   - 중요도: ⭐⭐⭐⭐
   - EU가 세계 최초로 포괄적 AI 규제 프레임워크를 확정했습니다. 위험 기반 분류 체계를 도입하며, 2026년 하반기부터 단계적 시행 예정입니다.
   - 전략적 시사점: EU 시장 진출 기업은 컴플라이언스 대응 체계 구축 시급

3. [...]

### 주요 변화 요약
- 발견된 신규 신호: 79개
- 우선순위 상위 신호: 15개
- 주요 영향 도메인: 기술(32%), 경제(28%), 정치(18%), 환경(12%), 사회(7%), 영적/윤리(3%)
```

---

---

## Validation Rules (Machine-Readable)

> Used by the orchestrator's VEV Layer 3 to validate report quality.
> These rules are authoritative — any report failing these checks must be regenerated.

```yaml
validation:
  # Required section headers (exact strings to search for in the report)
  required_sections:
    - header: "## 1. 경영진 요약"
      critical: true
      min_words: 300
    - header: "## 2. 신규 탐지 신호"
      critical: true
      min_words: 2000
    - header: "## 3. 기존 신호 업데이트"
      critical: true
      min_words: 100
    - header: "## 4. 패턴 및 연결고리"
      critical: true
      min_words: 200
    - header: "## 5. 전략적 시사점"
      critical: true
      min_words: 300
    - header: "## 6. 플러서블 시나리오"
      critical: false  # Optional - only if scenarios input exists
      min_words: 0
    - header: "## 7. 신뢰도 분석"
      critical: true
      min_words: 100
    - header: "## 8. 부록"
      critical: true
      min_words: 200

  # Section 2 signal detail requirements
  signal_detail:
    top_10_required_fields: 9
    top_10_fields:
      - "분류"
      - "출처"
      - "핵심 사실"
      - "정량 지표"
      - "영향도"
      - "상세 설명"
      - "추론"
      - "이해관계자"
      - "모니터링 지표"
    min_detailed_signals: 10
    min_condensed_signals: 5  # Signals 11-15 in condensed format

  # Section 5 structure requirements
  strategic_implications:
    required_subsections:
      - "### 5.1"
      - "### 5.2"
      - "### 5.3"
    min_items_per_subsection: 2

  # Section 3 requirements
  existing_signals:
    required_subsections:
      - "### 3.1"  # 강화 추세
      - "### 3.2"  # 약화 추세
    must_reference: "database.json"

  # Section 4 requirements
  patterns:
    min_cross_impact_pairs: 3
    min_emerging_themes: 2
    required_subsections:
      - "### 4.1"  # 교차 영향
      - "### 4.2"  # 떠오르는 테마

  # Overall report quality
  overall:
    min_total_words: 5000
    max_total_words: null  # No upper limit
    min_korean_char_ratio: 0.5  # At least 50% Korean characters in body text
    required_metadata:
      - "날짜"
      - "분석 신호 수"
```

---

## Version
**Format Version**: 1.1.0
**Output Language**: Korean
**Last Updated**: 2026-02-01
**Changelog**: v1.1.0 - Added machine-readable Validation Rules section for VEV Layer 3 quality checking
