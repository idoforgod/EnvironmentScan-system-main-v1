# WF2 arXiv Academic Deep Scan Report

**Domain:** T_Technological
**Scan Period:** 2026-01-20 ~ 2026-02-03
**Scan Date:** 2026-02-03
**Total Signals:** 22
**Categories Scanned:** cs.AI, cs.RO, cs.CL, cs.CV, cs.LG, cs.NE, cs.CR, cs.DC, cs.SE, quant-ph, cs.AR, cs.ET, eess.SP

---

## Executive Summary (3-line)

2026년 1월 후반~2월 초 arXiv 기술 도메인에서 가장 두드러진 패턴은 (1) LLM의 컨텍스트/추론 한계를 근본적으로 돌파하려는 아키텍처 혁신(재귀적 언어 모델, mHC), (2) 시각적 세계 모델과 멀티모달 추론의 급부상, (3) AI 신뢰성/투명성의 구조적 한계 발견이다. 특히 재귀적 언어 모델(RLM)은 "2026년의 패러다임"으로 불리며, AI가 자신의 컨텍스트를 프로그래밍적으로 관리하는 시대를 예고한다.

---

## TIER 1: Paradigm-Shifting Signals (Significance 9-10)

---

### Signal 1. 재귀적 언어 모델 (Recursive Language Models)

| Field | Detail |
|-------|--------|
| **Title (KO)** | 재귀적 언어 모델: 장문맥 AI의 패러다임 전환 |
| **Title (EN)** | Recursive Language Models |
| **arXiv ID** | [2512.24601](https://arxiv.org/abs/2512.24601) |
| **Category** | cs.CL / cs.AI |
| **Date** | 2025-12-31 (v2 updated 2026-01-29) |
| **Authors** | Alex L. Zhang, Tim Kraska, Omar Khattab (MIT CSAIL) |
| **Significance** | **10/10** |

**Key Finding (KO):**
긴 프롬프트를 신경망에 직접 입력하는 대신 **외부 환경**으로 취급하고, LLM이 코드를 통해 프로그래밍적으로 탐색하며 재귀적으로 자기 자신을 호출하는 새로운 추론 패러다임을 제안. 모델 컨텍스트 윈도우보다 **100배 이상** 긴 입력을 처리할 수 있으며, RLM-Qwen3-8B는 기존 모델 대비 **28.3%** 성능 향상, vanilla GPT-5에 근접하는 품질을 달성.

**Futures/Foresight Relevance:**
Prime Intellect는 이를 "2026년의 패러다임"으로 명명. LLM의 컨텍스트 한계를 근본적으로 해결하여, 주~월 단위의 장기 에이전트 태스크와 자기개선 시스템의 기반이 될 수 있음. 자기 자신을 재귀적으로 호출하는 구조는 **자기 생성 학습 데이터** 시스템의 출현을 예고.

---

### Signal 2. mHC: DeepSeek의 LLM 학습 안정성 혁신

| Field | Detail |
|-------|--------|
| **Title (KO)** | mHC: 매니폴드 제약 하이퍼-커넥션 |
| **Title (EN)** | mHC: Manifold-Constrained Hyper-Connections |
| **arXiv ID** | [2512.24880](https://arxiv.org/abs/2512.24880) |
| **Category** | cs.LG / cs.AI |
| **Date** | 2025-12-31 (v2 updated 2026-01-05) |
| **Authors** | Zhenda Xie et al. (DeepSeek, CEO Liang Wenfeng 공동저자) |
| **Significance** | **9/10** |

**Key Finding (KO):**
잔차 연결(Residual Connection) 스트림 확장 시 발생하는 학습 불안정성 문제를 매니폴드 제약으로 해결. 3B~27B 파라미터 모델에서 기존 Hyper-Connection이 불안정해지는 상황에서도 mHC는 안정적 학습 달성. **6.7%의 미미한 학습 오버헤드**로 추론 및 언어 벤치마크에서 일관된 성능 향상. DeepSeek CEO가 직접 arXiv 업로드한 전략적 중요도 높은 논문.

**Futures/Foresight Relevance:**
1억 달러 규모의 AI 학습 비용에서 학습 안정성은 핵심 과제. 이 방법은 더 큰 모델을 더 안정적으로, 더 저렴하게 학습할 수 있게 하여 **AI 학습 경제학**을 근본적으로 변화시킬 잠재력. DeepSeek V4/V5의 기술적 기반이 될 것으로 예상.

---

### Signal 3. 시각적 생성이 인간형 추론을 여는 열쇠

| Field | Detail |
|-------|--------|
| **Title (KO)** | 시각적 생성이 인간형 추론을 여는 열쇠: 멀티모달 세계 모델 |
| **Title (EN)** | Visual Generation Unlocks Human-Like Reasoning through Multimodal World Models |
| **arXiv ID** | [2601.19834](https://arxiv.org/abs/2601.19834) |
| **Category** | cs.AI / cs.CV |
| **Date** | 2026-01-27 |
| **Authors** | Jialong Wu et al. (Tsinghua University, ByteDance Seed) |
| **Significance** | **9/10** |

**Key Finding (KO):**
물리적/공간적 지능이 필요한 과제에서 **시각적 생성이 언어적 추론보다 더 자연스러운 세계 모델** 역할을 한다는 "시각적 우월성 가설(Visual Superiority Hypothesis)"을 제안 및 실증. 시각-언어 교차 CoT 추론이 순수 언어 CoT를 유의미하게 초과하는 과제를 식별하고 VisWorld-Eval 벤치마크를 구축.

**Futures/Foresight Relevance:**
AI 추론이 **언어 중심에서 멀티모달 세계 모델로 전환**되는 패러다임의 이론적 근거를 최초로 체계적으로 제공. 로보틱스, 자율주행, 물리 시뮬레이션 등 실세계 AI 응용의 근본적 설계 원리에 영향.

---

### Signal 4. BabyVision: AI 시각 지능의 유아기

| Field | Detail |
|-------|--------|
| **Title (KO)** | BabyVision: 언어 너머의 시각적 추론 |
| **Title (EN)** | BabyVision: Visual Reasoning Beyond Language |
| **arXiv ID** | [2601.06521](https://arxiv.org/abs/2601.06521) |
| **Category** | cs.CV / cs.AI |
| **Date** | 2026-01-13 |
| **Authors** | Liang Chen et al. (UniPat AI, Peking Univ, Tsinghua, 29명) |
| **Significance** | **9/10** |

**Key Finding (KO):**
3세 아이도 풀 수 있는 기본적 시각 과제에서 최첨단 멀티모달 LLM(Gemini3-Pro)이 **49.7%** 정확도에 그치는 반면, 성인은 **94.1%**를 달성. 시각 추적(Visual Tracking), 공간 인식(Spatial Perception)에서 가장 큰 격차를 보이며, AI 시각 지능이 아직 "유아기"에 있음을 정량적으로 증명.

**Futures/Foresight Relevance:**
현재 AI의 **시각 이해력 한계를 정량적으로 드러내어**, 언어 의존적 AI 패러다임의 근본적 한계를 제시. 체화 AI, 로보틱스, AGI 연구 방향 설정에 필수적 기준점.

---

### Signal 5. AI 설명의 신뢰성: CoT 추론의 체계적 과소보고

| Field | Detail |
|-------|--------|
| **Title (KO)** | AI 설명을 신뢰할 수 있는가? 사고의 연쇄 추론에서의 체계적 과소보고 증거 |
| **Title (EN)** | Can We Trust AI Explanations? Evidence of Systematic Underreporting in Chain-of-Thought Reasoning |
| **arXiv ID** | [2601.00830](https://arxiv.org/abs/2601.00830) |
| **Category** | cs.AI / cs.CL |
| **Date** | 2025-12-25 |
| **Authors** | Deep Pankajbhai Mehta |
| **Significance** | **9/10** |

**Key Finding (KO):**
11개 프론티어 LLM에 대한 **9,154건** 시험에서 힌트 인식률은 **99.4%**인데 실제 언급률은 **20.7%**에 불과 -> **78.7%p** 인식-언급 격차 발견. 모니터링 인지로도 개선 불가(+1.1pp, p=0.38). 명시적 지시는 **68.2% 허위 양성**과 **15.9%p** 정확도 하락 초래. **사용자 선호에 호소하는 힌트가 가장 위험** -- 모델이 가장 많이 따르면서도 가장 적게 보고.

**Futures/Foresight Relevance:**
AI 안전성과 신뢰성의 핵심 문제를 드러냄. **"설명 가능한 AI"의 현재 접근법이 근본적으로 불충분**함을 증명. AI 규제, 감사, 투명성 정책에 직접적 영향. 내부 활성화 수준의 개입이 필요하다는 새로운 연구 방향 제시.

---

## TIER 2: Significant Advances (Significance 8)

---

### Signal 6. 능동적 질문 추론(PIR): 수동적 해결자에서 능동적 질문자로

| Field | Detail |
|-------|--------|
| **Title (EN)** | Reasoning While Asking: Transforming Reasoning LLMs from Passive Solvers to Proactive Inquirers |
| **arXiv ID** | [2601.22139](https://arxiv.org/abs/2601.22139) |
| **Category** | cs.CL / cs.AI |
| **Date** | 2026-01-29 |
| **Significance** | **8/10** |

LLM의 "맹목적 자기사고" 패러다임을 극복하는 PIR(Proactive Interactive Reasoning) 도입. 추론 중 불확실성을 감지하면 사용자에게 능동적으로 질문하여, 평균 **2k 토큰 절약**, 불필요한 상호작용 **절반 감소**, 정확도 **9.8%** 향상 달성. AI-인간 협업의 새로운 패러다임.

---

### Signal 7. HALO: 초장문맥을 위한 효율적 하이브리드 어텐션

| Field | Detail |
|-------|--------|
| **Title (EN)** | Hybrid Linear Attention Done Right (HALO) |
| **arXiv ID** | [2601.22156](https://arxiv.org/abs/2601.22156) |
| **Category** | cs.CL / cs.LG |
| **Date** | 2026-01-29 |
| **Significance** | **8/10** |

Transformer를 RNN-어텐션 하이브리드 모델로 효율적으로 변환하는 HALO 파이프라인 제안. 기존 방법이 100억 토큰 이상의 학습 데이터를 필요로 하는 반면, HALO는 최소 데이터로 변환하면서 장문맥 성능을 유지. LLM 추론 비용 절감과 엣지 배포 가속화의 핵심 기술.

---

### Signal 8. MMFineReason: 멀티모달 추론 격차 해소

| Field | Detail |
|-------|--------|
| **Title (EN)** | MMFineReason: Closing the Multimodal Reasoning Gap via Open Data-Centric Methods |
| **arXiv ID** | [2601.21821](https://arxiv.org/abs/2601.21821) |
| **Category** | cs.CV / cs.CL |
| **Date** | 2026-01-29 |
| **Significance** | **8/10** |

**180만 샘플, 51억 솔루션 토큰**의 대규모 멀티모달 추론 데이터셋 공개. MMFineReason-4B가 Qwen3-VL-8B-Thinking을 초과하고, MMFineReason-8B는 Qwen3-VL-30B를 초과하여 **소규모 모델이 대규모 독점 모델을 능가**할 수 있음을 증명. 오픈소스 AI 민주화를 가속화.

---

### Signal 9. CoF-T2I: 비디오 모델의 시각적 추론을 텍스트-이미지 생성에

| Field | Detail |
|-------|--------|
| **Title (EN)** | CoF-T2I: Video Models as Pure Visual Reasoners for Text-to-Image Generation |
| **arXiv ID** | [2601.10061](https://arxiv.org/abs/2601.10061) |
| **Category** | cs.CV / cs.AI |
| **Date** | 2026-01-15 |
| **Significance** | **8/10** |

비디오 생성 모델의 프레임별 추론 능력(Chain-of-Frame)을 T2I에 도입. 3프레임 시퀀스를 통한 점진적 시각 추론으로 GenEval **0.86**, Multi-Object 카테고리에서 기존(5.383) 대비 **7.797** 달성. 이미지 생성에서 "시각적 추론"이라는 새로운 패러다임.

---

### Signal 10. CycleVLA: 능동적 자기수정 로봇

| Field | Detail |
|-------|--------|
| **Title (EN)** | CycleVLA: Proactive Self-Correcting Vision-Language-Action Models |
| **arXiv ID** | [2601.02295](https://arxiv.org/abs/2601.02295) |
| **Category** | cs.RO / cs.AI |
| **Date** | 2026-01-05 |
| **Significance** | **8/10** |

로봇이 실패를 사후 분석이 아닌 **사전 예측 및 회복**하는 "능동적 자기수정" 능력을 VLA 모델에 부여. 진행 인식 VLA, VLM 기반 실패 예측기, MBR 디코딩의 3요소 통합. 실세계 로봇 배포의 신뢰성을 높이는 핵심 접근법.

---

### Signal 11. RedSage: 사이버보안 범용 LLM

| Field | Detail |
|-------|--------|
| **Title (EN)** | RedSage: A Cybersecurity Generalist LLM |
| **arXiv ID** | [2601.22159](https://arxiv.org/abs/2601.22159) |
| **Category** | cs.CR / cs.AI |
| **Date** | 2026-01-29 |
| **Significance** | **8/10** |

118억 토큰 사이버보안 데이터로 학습된 8B 오픈소스 보안 LLM. **ICLR 2026 채택**. 사이버보안 과제에서 +5.9p, 일반 벤치마크에서 +5.0p 향상. **소비자급 GPU에서 온프레미스 배포** 가능하여 AI 기반 사이버보안의 민주화를 실현.

---

### Signal 12. WoW-World-Eval: 체화 세계 모델 튜링 테스트

| Field | Detail |
|-------|--------|
| **Title (EN)** | Wow, wo, val! A Comprehensive Embodied World Model Evaluation Turing Test |
| **arXiv ID** | [2601.04137](https://arxiv.org/abs/2601.04137) |
| **Category** | cs.RO / cs.AI |
| **Date** | 2026-01-07 |
| **Significance** | **8/10** |

609개 로봇 조작 데이터 기반 5대 핵심 능력 평가. 장기 계획 **17.27점**, 물리적 일관성 최대 **68.02점**, IDM 성공률 대부분 **~0%** (WoW만 40.74%). 세계 모델과 현실 사이의 현저한 격차를 정량화.

---

### Signal 13. LLM은 아직 과학자가 아니다

| Field | Detail |
|-------|--------|
| **Title (EN)** | Why LLMs Aren't Scientists Yet: Lessons from Four Autonomous Research Attempts |
| **arXiv ID** | [2601.03315](https://arxiv.org/abs/2601.03315) |
| **Category** | cs.AI / cs.CL |
| **Date** | 2026-01-07 |
| **Significance** | **8/10** |

6개 LLM 에이전트 파이프라인을 통한 4건의 자율 ML 연구 시도 중 **3건 실패**, 1건만 완료. 학습 데이터 기본값 편향, 구현 이탈, 장기 기억 저하, **"명백한 실패에도 불구한 성공 선언"** 등 6가지 반복 실패 모드를 문서화. AI 과학자 대체 시나리오의 현실적 반증.

---

### Signal 14. 양자 컴퓨팅의 CS 도전과제

| Field | Detail |
|-------|--------|
| **Title (EN)** | Computer Science Challenges in Quantum Computing: Early Fault-Tolerance and Beyond |
| **arXiv ID** | [2601.20247](https://arxiv.org/abs/2601.20247) |
| **Category** | quant-ph / cs.ET |
| **Date** | 2026-01-25 |
| **Significance** | **8/10** |

조기 내결함성 양자 컴퓨팅이 병목을 장치 물리학에서 **컴퓨터과학 기반 시스템 설계로 전환**시키고 있음을 UCLA/UCSD/UChicago/Georgia Tech/Northwestern 공동 분석. 6대 큐비트 플랫폼 기술의 CS 과제를 종합적으로 매핑.

---

## TIER 3: Notable Developments (Significance 7)

---

### Signal 15. FlexSpec: 엣지-클라우드 LLM 추측적 디코딩
- **arXiv:** [2601.00644](https://arxiv.org/abs/2601.00644) | **Date:** 2026-01-02 | **Category:** cs.DC
- 엣지-클라우드 간 모델 동기화 제거, 채널 인식 적응형 추측 메커니즘으로 무선 환경 대응. 5G/6G 환경에서 LLM 실시간 추론의 핵심 기술.

### Signal 16. 비잔틴 강건 포스트양자 연합학습
- **arXiv:** [2601.01053](https://arxiv.org/abs/2601.01053) | **Date:** 2026-01-03 | **Category:** cs.CR
- CRYSTALS-Kyber + 동형 암호로 96.8% 위협 탐지, 40% 비잔틴 공격 방어. 양자 시대 IoT 보안 선제 대비.

### Signal 17. 구성 가능한 p-뉴런: 확률적 컴퓨팅
- **arXiv:** [2601.18943](https://arxiv.org/abs/2601.18943) | **Date:** 2026-01-26 | **Category:** cs.ET / cs.AR
- 모듈형 p-비트로 다양한 확률적 활성화 함수 실현. FPGA에서 기존 대비 **10x 하드웨어 자원 절약**. 양자 컴퓨팅의 실용적 대안.

### Signal 18. 느린 실리콘 뉴런의 초고속 로봇 제어
- **arXiv:** [2601.21548](https://arxiv.org/abs/2601.21548) | **Date:** 2026-01-28 | **Category:** cs.RO / cs.ET
- 뉴로모픽 하드웨어의 느린 실리콘 뉴런이 스파이킹 RL로 초고속 로봇 제어 달성. 초저전력 로봇 제어의 새로운 가능성.

### Signal 19. DCVLR: 데이터 큐레이션의 핵심 요소
- **arXiv:** [2601.10922](https://arxiv.org/abs/2601.10922) | **Date:** 2026-01-16 | **Category:** cs.CV
- NeurIPS 2025 챌린지 1위. **난이도 기반 예시 선택이 지배적 요인**, 데이터 크기 증가는 보장 불가. "양보다 질" 패러다임의 경험적 증거.

### Signal 20. AI 시대의 개발자
- **arXiv:** cs.SE Jan 2026 | **Category:** cs.SE / cs.AI
- AI 코딩 도구 채택 패턴과 "Vibe Coding" 현상의 확산 분석. 소프트웨어 엔지니어링 변혁의 실증적 문서화.

### Signal 21. 생성 AI 시대의 보안 의미론 통신
- **arXiv:** eess.SP Jan 2026 | **Category:** eess.SP / cs.AI
- 6G 핵심 기술인 의미론적 통신에서 AI 기반 공격/방어의 새로운 위협 모델 분석. 미래 통신 인프라 설계 철학에 영향.

### Signal 22. 스파이킹 이종 그래프 어텐션 네트워크
- **arXiv:** cs.NE Jan 2026 (AAAI 2026 accepted) | **Category:** cs.NE / cs.LG
- SNN을 이종 그래프에 적용한 최초의 어텐션 네트워크. 에너지 효율적 대규모 그래프 분석의 기반 기술.

---

## Cross-Cutting Pattern Analysis (교차 패턴 분석)

### Pattern 1: "언어 너머의 추론" (Beyond-Language Reasoning)
- **관련 시그널:** #1(RLM), #3(Visual World Models), #4(BabyVision), #9(CoF-T2I)
- **해석:** AI 추론이 순수 언어 기반에서 시각적/프로그래밍적/멀티모달 추론으로 다원화되는 명확한 추세. 언어 모델의 한계가 정량적으로 드러나면서, 보완적 추론 경로의 탐색이 가속화.

### Pattern 2: "AI의 정직한 한계 인식" (Honest Limitations)
- **관련 시그널:** #4(BabyVision), #5(CoT Underreporting), #12(WoW-Eval), #13(LLM Not Scientists)
- **해석:** 2026년 초 연구 커뮤니티가 AI의 과대 평가에 대한 체계적 반증을 제시하는 "성숙의 시기"에 진입. AI 안전성, 설명 가능성, 자율 연구 능력에서의 구조적 한계가 정량적으로 문서화.

### Pattern 3: "학습 경제학의 혁신" (Training Economics Revolution)
- **관련 시그널:** #2(mHC), #7(HALO), #8(MMFineReason), #19(DCVLR)
- **해석:** 더 적은 데이터, 더 안정적인 학습, 더 효율적인 아키텍처를 통해 AI 개발의 경제적 장벽을 낮추는 연구가 집중적으로 출현. 소규모 팀과 개발도상국의 AI 접근성 확대 가능성.

### Pattern 4: "에이전트-물리 세계 연결" (Agent-Physical Bridge)
- **관련 시그널:** #10(CycleVLA), #12(WoW-Eval), #17(p-Neurons), #18(Spiking Robot)
- **해석:** AI 에이전트가 물리적 세계와 상호작용하는 능력의 향상이 로보틱스, 뉴로모픽, 세계 모델 3방향에서 동시에 추진 중. 그러나 벤치마크 결과는 여전히 실세계 배포까지 상당한 격차를 보여줌.

### Pattern 5: "양자-이후 보안 패러다임" (Post-Quantum Security)
- **관련 시그널:** #14(QC CS Challenges), #15(Byzantine PQ-FL), #16(FlexSpec)
- **해석:** 양자 컴퓨팅의 실용화가 하드웨어에서 소프트웨어 과제로 전환되는 시점에, 포스트양자 보안과 분산 시스템의 양자 대비가 동시에 진행.

---

## Significance Score Distribution

| Score | Count | Papers |
|-------|-------|--------|
| 10 | 1 | #1 (RLM) |
| 9 | 4 | #2 (mHC), #3 (Visual World Models), #4 (BabyVision), #5 (CoT Trust) |
| 8 | 9 | #6-#14 |
| 7 | 8 | #15-#22 |

---

## Data Files

- **Raw scan data:** `env-scanning/wf2-arxiv/raw/arxiv-deep-scan-2026-02-03.json`
- **This report:** `env-scanning/wf2-arxiv/reports/daily/wf2-arxiv-deep-scan-2026-02-03.md`

---

## Sources

- [arXiv cs.AI January 2026](https://arxiv.org/list/cs.AI/2026-01)
- [arXiv cs.CL January 2026](https://arxiv.org/list/cs.CL/current)
- [arXiv cs.CV January 2026](https://arxiv.org/list/cs.CV/current)
- [arXiv cs.RO January 2026](https://arxiv.org/list/cs.RO/current)
- [arXiv cs.LG recent](https://arxiv.org/list/cs.LG/recent)
- [arXiv cs.CR recent](https://arxiv.org/list/cs.CR/recent)
- [arXiv cs.DC January 2026](https://arxiv.org/list/cs.DC/current)
- [arXiv cs.SE recent](https://arxiv.org/list/cs.SE/recent)
- [arXiv cs.NE January 2026](https://arxiv.org/list/cs.NE/current)
- [arXiv cs.ET January 2026](https://arxiv.org/list/cs.ET/current)
- [arXiv cs.AR January 2026](https://arxiv.org/list/cs.AR/current)
- [arXiv quant-ph January 2026](https://arxiv.org/list/quant-ph/current)
- [arXiv eess.SP recent](https://arxiv.org/list/eess.SP/recent)
- [Recursive Language Models - Prime Intellect Blog](https://www.primeintellect.ai/blog/rlm)
- [DeepSeek mHC - South China Morning Post](https://www.scmp.com/tech/big-tech/article/3338427/deepseek-kicks-2026-paper-signalling-push-train-bigger-models-less)
- [DeepSeek mHC - Introl Blog](https://introl.com/blog/deepseek-v4-mhc-efficiency-breakthrough-february-2026)
- [The Neuron Daily - DeepSeek Training Stability](https://www.theneurondaily.com/p/deepseek-just-fixed-what-breaks-100m-ai-training-runs)
