# 최종 보고서 스타일 가이드 (Final Report Style Guide)

> **용도**: 의사결정자에게 전달되는 최종 보고서(md, docx)에서 내부 스캐닝 코드를
> 제거하고, 모든 영문 약어를 전체 표기 + 한국어 번역으로 변환하기 위한 규칙.
>
> **적용 시점**: 보고서 생성의 마지막 단계 (스켈레톤 채운 후, 파일 저장 전)
>
> **참조 에이전트**: report-generator, report-merger

---

## 1. 내부 스캐닝 코드 변환 규칙

최종 보고서에는 내부 워크플로우 식별자가 노출되어서는 안 된다.
아래 표에 따라 모든 내부 코드를 한국어 서술로 변환한다.

### 1.1 워크플로우 식별자

| 내부 코드 | 최종 보고서 표기 | 비고 |
|-----------|-----------------|------|
| WF1 | 일반 환경스캐닝 | 괄호 설명 불필요 |
| WF2 | 학술 심층 분석 | 괄호 설명 불필요 |
| [WF1] | (일반 스캐닝) | 신호 출처 태그로 사용 시 |
| [WF2] | (학술 심층 분석) | 신호 출처 태그로 사용 시 |
| WF1+WF2 | 일반 환경스캐닝 + 학술 심층 분석 | 통합 표기 시 |

### 1.2 신뢰도 평가 코드

| 내부 코드 | 최종 보고서 표기 |
|-----------|-----------------|
| pSST | 신뢰도 |
| pSST 92 | 신뢰도 92 |
| pSST 미산출 | 신뢰도 미산출 |
| SR (출처 신뢰도) | 출처 신뢰도(Source Reliability) |
| ES (근거 강도) | 증거 강도(Evidence Strength) |
| CC (분류 신뢰도) | 분류 확신도(Classification Confidence) |
| TC (시간적 신뢰도) | 시간적 확신도(Temporal Confidence) |
| DC (고유성 신뢰도) | 독창성 확신도(Distinctiveness Confidence) |
| IC (영향 확신도) | 영향 확신도(Impact Confidence) |

### 1.3 등급 표기

| 내부 코드 | 최종 보고서 표기 |
|-----------|-----------------|
| Grade A | A등급 |
| Grade B | B등급 |
| Grade C | C등급 |
| Grade D | D등급 |
| 🟢 Grade A | A등급 (90점 이상) |
| 🔵 Grade B | B등급 (70-89점) |
| 🟡 Grade C | C등급 (50-69점) |
| 🔴 Grade D | D등급 (0-49점) |

### 1.4 STEEPs 카테고리 코드

| 내부 코드 | 최종 보고서 표기 |
|-----------|-----------------|
| S (Social) | 사회(Social) |
| T (Technological) | 기술(Technological) |
| E (Economic) | 경제(Economic) |
| E (Environmental) | 환경(Environmental) |
| P (Political) | 정치(Political) |
| s (Spiritual) | 가치관(Spiritual) |
| STEEPs | 사회·기술·경제·환경·정치·가치관 |

### 1.5 기타 내부 코드

| 내부 코드 | 최종 보고서 표기 |
|-----------|-----------------|
| VEV | 검증-실행-검증 프로토콜 |
| SOT | 단일 진실 원천 |
| SKEL-001 | (제거 -- 최종 보고서에 포함하지 않음) |
| SIG-002 | (제거 -- 최종 보고서에 포함하지 않음) |

---

## 2. 영문 약어 전체 표기 규칙

모든 영문 약어는 **한국어 번역 + 영문 전체명(괄호)**으로 표기한다.
동일 문서 내 최초 등장 시 전체 표기하고, 이후에는 한국어 명칭만 사용해도 무방하다.

### 2.1 군사/정치 기관

| 약어 | 최종 보고서 표기 (최초) | 이후 약칭 |
|------|------------------------|-----------|
| CMC | 중앙군사위원회(Central Military Commission) | 중앙군사위원회 |
| PLA | 인민해방군(People's Liberation Army) | 인민해방군 |
| CCP | 중국 공산당(Chinese Communist Party) | 중국 공산당 |
| Pentagon | 미국 국방부(Pentagon) | 미국 국방부 |
| NATO | 북대서양조약기구(North Atlantic Treaty Organization, NATO) | NATO |
| EU | 유럽연합(European Union, EU) | EU |
| UN | 유엔(United Nations, UN) | 유엔 |

### 2.2 싱크탱크/연구기관

| 약어 | 최종 보고서 표기 |
|------|-----------------|
| RUSI | 영국 왕립합동군사연구소(Royal United Services Institute) |
| AEI | 미국기업연구소(American Enterprise Institute) |
| CFR | 미국외교협회(Council on Foreign Relations) |
| CNA | 미국해군분석센터(Center for Naval Analyses) |
| CSIS | 전략국제문제연구소(Center for Strategic and International Studies) |
| RAND | 랜드연구소(RAND Corporation) |
| Brookings | 브루킹스 연구소(Brookings Institution) |
| V-Dem | 민주주의 다양성 연구소(Varieties of Democracy Institute) |
| Hoover Institution | 후버연구소(Hoover Institution) |
| Hudson Institute | 허드슨연구소(Hudson Institute) |

### 2.3 학술지/저널

| 약어 | 최종 보고서 표기 |
|------|-----------------|
| BJPS | 영국정치학저널(British Journal of Political Science) |
| APSR | 미국정치학리뷰(American Political Science Review) |
| IO | 국제기구(International Organization) |
| JCE | 비교경제학저널(Journal of Comparative Economics) |

### 2.4 중국 방위산업

| 약어 | 최종 보고서 표기 |
|------|-----------------|
| NORINCO | 중국북방공업집단(NORINCO, China North Industries Group) |
| AVIC | 중국항공공업집단(AVIC, Aviation Industry Corporation of China) |
| CASC | 중국항천과기집단(CASC, China Aerospace Science and Technology) |
| CNNC | 중국핵공업집단(CNNC, China National Nuclear Corporation) |
| CASIC | 중국항천과공집단(CASIC, China Aerospace Science and Industry) |
| CETC | 중국전자과기집단(CETC, China Electronics Technology Group) |

### 2.5 기타 빈출 약어

| 약어 | 최종 보고서 표기 |
|------|-----------------|
| GDP | 국내총생산(GDP) |
| AI | 인공지능(AI) |
| R&D | 연구개발(R&D) |
| BIS | 미국 산업안보국(Bureau of Industry and Security) |
| ASML | ASML(네덜란드 반도체 장비 기업) |
| EUV | 극자외선(Extreme Ultraviolet, EUV) |

---

## 3. 적용 절차

### 3.1 보고서 생성 에이전트 (report-generator, report-merger)

1. 스켈레톤 채우기 완료 (기존 절차)
2. **최종 스타일 변환 적용** (이 가이드 참조)
   - 내부 코드 → 한국어 서술 변환 (섹션 1)
   - 영문 약어 → 전체 표기 변환 (섹션 2)
3. 검증 및 저장

### 3.2 외부 보고서 변환 시 (docx/md 최종 전달물)

1. 통합 보고서(integrated-scan) 읽기
2. 이 스타일 가이드의 모든 변환 규칙 적용
3. 최종 파일 생성

### 3.3 변환하지 않는 파일

다음 파일들은 내부 코드를 그대로 유지한다:
- `signals/database.json` (내부 데이터)
- `analysis/*.json` (분석 데이터)
- `structured/*.json` (분류 데이터)
- `logs/*.log` (로그)
- 에이전트 지침 파일 (`.claude/agents/`)
- 스켈레톤 템플릿 (`.claude/skills/env-scanner/references/*-skeleton.md`)

---

## 4. 품질 체크리스트

최종 보고서 제출 전 확인 사항:

- [ ] "WF1", "WF2"가 본문에 나타나지 않는다
- [ ] "pSST"가 본문에 나타나지 않는다 ("신뢰도"로 대체)
- [ ] "SR", "ES", "CC", "TC", "DC", "IC"가 약어 단독으로 나타나지 않는다
- [ ] "Grade A/B/C/D"가 나타나지 않는다 ("A등급/B등급/C등급/D등급"으로 대체)
- [ ] 모든 영문 기관명에 한국어 번역이 병기되어 있다
- [ ] 모든 영문 약어에 전체 영문명이 최소 1회 표기되어 있다
- [ ] STEEPs 카테고리 코드(S, T, E, P, s)가 단독으로 나타나지 않는다

---

## Version
**Style Guide Version**: 1.0.0
**Last Updated**: 2026-02-04
**Changelog**: v1.0.0 - 초기 생성. 내부 코드 변환 규칙, 영문 약어 전체 표기 규칙, 적용 절차, 품질 체크리스트 포함.
