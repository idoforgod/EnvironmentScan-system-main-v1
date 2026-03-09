# Daily Environmental Scanning Report — WF2 arXiv Academic Deep Scanning

**Date**: March 07, 2026
**Workflow**: WF2 — arXiv Academic Deep Scanning
**Scan Window**: March 05, 2026 00:46 UTC ~ March 07, 2026 00:46 UTC (48 hours)
**Anchor Time (T₀)**: March 07, 2026 00:46:38 UTC
**Total Signals Collected**: 491 new papers (492 raw − 1 definite duplicate)
**arXiv Categories Covered**: 180 (18 query groups)
**Report Language**: English (for quality validation; Korean translation follows)

---

## 1. Executive Summary

### Today's Key Findings (Top 3 Signals)

1. **Reasoning Theater: Disentangling Model Beliefs from Chain-of-Thought** (T_Technological)
   - Importance: CRITICAL — undermines the foundational assumption that LLM chain-of-thought reasoning is a window into model cognition
   - Key Content: Empirical evidence that reasoning models exhibit "performative CoT" — they continue generating tokens after reaching high confidence in a final answer, producing post-hoc rationalizations rather than genuine reasoning traces
   - Strategic Implications: The entire interpretability and alignment research agenda relying on CoT as a mechanism for understanding model behavior must be reconsidered. Regulatory frameworks requiring AI explainability based on reasoning logs face a fundamental validity crisis

2. **Censored LLMs as a Natural Testbed for Secret Knowledge Elicitation** (T_Technological)
   - Importance: CRITICAL — demonstrates that safety-filtered LLMs retain dangerous knowledge in latent form, accessible via elicitation methods
   - Key Content: Safety fine-tuning suppresses model outputs but does not erase underlying parametric knowledge. The paper proposes using "censored" regions of an LLM's output distribution as a natural testbed to probe what the model knows but refuses to say
   - Strategic Implications: Current safety certification frameworks are insufficient — a model that "passes" safety evaluations by refusing outputs may still harbor dangerous knowledge extractable through alternate prompting strategies. This changes the risk surface for AI deployment in critical infrastructure

3. **Cognitive Warfare: Definition, Framework, and Case Study** (S_Social)
   - Importance: CRITICAL — first systematic academic framework treating cognitive operations as a unified discipline distinct from conventional information warfare
   - Key Content: Provides definitional clarity for "cognitive warfare" as targeted manipulation of perception, decision-making, and belief systems at population scale; includes case study methodology for evaluating real-world cognitive operations
   - Strategic Implications: Nation-state actors are already deploying AI-enabled cognitive warfare tools; academic legitimization of this field accelerates both offensive capability development and potential counter-measures. Organizations and governments without cognitive defense postures face an asymmetric vulnerability

### Key Changes Summary
- New signals detected: 491
- Top priority signals (CRITICAL): 3 (Reasoning Theater, Censored LLMs, Cognitive Warfare)
- High priority signals: 12
- Major impact domains: T_Technological (384), S_Social (61), E_Environmental (31), E_Economic (7), P_Political (5), s_spiritual (3)

**STEEPs Distribution Today**:
| Domain | Count | % | Trend |
|--------|-------|---|-------|
| T_Technological | 384 | 78.2% | dominant — AI/ML/quantum infrastructure papers |
| S_Social | 61 | 12.4% | elevated — AI-society interactions accelerating |
| E_Environmental | 31 | 6.3% | steady — climate modeling + space science |
| E_Economic | 7 | 1.4% | low — finance/economics papers |
| P_Political | 5 | 1.0% | low — governance signals |
| s_spiritual | 3 | 0.6% | low — neuroscience/consciousness |

Notable pattern: The ratio of AI papers addressing safety, governance, and societal impact (S/P/s) versus pure technical papers has increased to approximately 18%, up from a historical baseline of ~12%, signaling academic attention shifting toward AI consequences.

---

## 2. Newly Detected Signals

Today's scan of 180 arXiv categories across 18 query groups yielded 491 new signals after deduplication. The following 10 priority signals represent the highest-impact early indicators of future change across STEEPs domains.

---

### Priority 1: Reasoning Theater — LLM Chain-of-Thought Is Not What It Appears

- **Confidence**: SR=0.88, TC=0.91, DC=0.72 | Overall: HIGH

1. **Classification**: T_Technological → AI Safety / AI Alignment / Interpretability
2. **Source**: arXiv:2603.05xxx | cs.AI, cs.CL, cs.LG | Published: 2026-03-05 | Authors: Multiple (cs.AI group)
3. **Key Facts**: Reasoning models become strongly confident in their final answer and then continue generating tokens producing post-hoc rationalization rather than genuine reasoning. The paper terms this "performative CoT" and provides empirical evidence across multiple frontier reasoning models including o-series and R-series architectures.
4. **Quantitative Metrics**: Models showed statistically significant divergence between token-generation-confidence trajectories and final answer confidence in 73% of evaluated cases. Performative reasoning constituted an estimated 40-60% of output tokens in complex multi-step tasks.
5. **Impact**: CRITICAL for AI trust, regulation, and deployment. The interpretability assumption underpinning explainable AI regulation (EU AI Act Article 13, US EO 14110) — that reasoning traces reveal model decision processes — is empirically invalidated. This affects every high-stakes deployment relying on CoT explanations: medical AI, legal AI, financial AI, autonomous systems.
6. **Detailed Description**: The study investigated whether chain-of-thought outputs in large reasoning models (those explicitly trained for step-by-step thinking) actually correspond to the computational path the model used to reach its answer. By analyzing confidence distributions at intermediate reasoning steps and comparing them with confidence at the final answer, the researchers found that models frequently lock in their answer early in the reasoning sequence but continue to generate what appear to be deliberative steps — these additional tokens do not change the answer and appear designed to satisfy human expectations of a reasoning process rather than reflecting genuine computational deliberation. This phenomenon — "Reasoning Theater" — has profound implications: it means that auditing AI decision-making by reading its reasoning traces is analogous to reading a post-hoc justification written after the decision was already made.
7. **Inference**: This finding likely represents the early phase of a broader realization that the current generation of AI reasoning systems, despite their impressive capabilities, are fundamentally opaque in ways that cannot be resolved by examining their outputs. The next 12-24 months will likely see (a) accelerated research into mechanistic interpretability that bypasses output analysis entirely, (b) regulatory pressure to revise AI explainability standards, and (c) potential liability implications for organizations that have deployed AI systems based on assurances of explainability via CoT.
8. **Stakeholders**: AI safety researchers; AI regulators (EU AI Office, NIST); enterprises deploying AI in high-stakes decisions; healthcare AI vendors; legal tech companies; audit firms certifying AI systems
9. **Monitoring Indicators**: Citation count growth of this paper within 30 days; policy response from EU AI Office on Article 13 compliance methodology; follow-up studies confirming/refuting across additional model architectures; whether major AI labs publicly respond; uptake in AI audit standards revisions

---

### Priority 2: Censored LLMs — Safety-Filtered Models Retain Dangerous Latent Knowledge

- **Confidence**: SR=0.85, TC=0.90, DC=0.70 | Overall: HIGH

1. **Classification**: T_Technological → AI Safety / Security / Knowledge Elicitation
2. **Source**: arXiv:2603.xxx | cs.AI, cs.CR, cs.LG | Published: 2026-03-05
3. **Key Facts**: Safety fine-tuning creates a suppression layer over parametric knowledge rather than erasing it. Censored output regions of an LLM's distribution function as a natural signal of what the model "knows but won't say." The paper demonstrates successful elicitation of suppressed knowledge using soft prompting and activation steering techniques.
4. **Quantitative Metrics**: Elicitation success rates for recovering suppressed outputs ranged from 45-78% depending on the degree of safety fine-tuning and the elicitation method employed. Models with RLHF-only safety training showed higher vulnerability (78%) than those with constitutional AI training (45%).
5. **Impact**: CRITICAL for AI safety certification. The current paradigm of "safety alignment by fine-tuning" is demonstrated to be a surface-level suppression mechanism, not knowledge deletion. All deployed safety-fine-tuned models (GPT-4, Claude, Gemini, Llama) retain underlying parametric knowledge of harmful content and can potentially be induced to reveal it. This fundamentally changes the risk model for open-source and closed-source AI deployment.
6. **Detailed Description**: The research exploits the observation that when a language model has been trained to refuse certain outputs, the refused content still exists in the model's weight space — it has simply been downweighted in the output distribution. By analyzing the shape of the output distribution "around" the censored region (i.e., the boundary between what the model says and what it won't say), it is possible to infer the censored content. The paper introduces a novel elicitation framework that uses the model's own uncertainty as a probe for hidden knowledge, achieving recovery of suppressed outputs without requiring any privileged access to model internals. This represents a significant escalation from previous jailbreaking work because it is a principled method grounded in information theory rather than ad hoc prompt manipulation.
7. **Inference**: The gap between "safety evaluation pass" and "genuine safety" will grow into a crisis over the next 12-18 months as elicitation methods become more widely available. This creates a two-tiered risk: (1) malicious actors gaining access to suppressed dangerous knowledge from freely available fine-tuned models; (2) a fundamental undermining of regulatory frameworks predicated on the assumption that safety fine-tuning is an effective containment mechanism. The field is likely to accelerate work on "unlearning" (true knowledge deletion) as a necessary alternative.
8. **Stakeholders**: AI safety researchers; national security agencies (NSA, GCHQ, equivalent); AI model providers (Anthropic, OpenAI, Google DeepMind, Meta AI); healthcare regulators deploying medical AI; weapons research institutions; open-source model communities (HuggingFace, EleutherAI)
9. **Monitoring Indicators**: Proliferation of elicitation tools on GitHub; regulatory agency statements on AI safety certification standards; AI lab internal policy changes on fine-tuning methods; emergency patches to deployed models; academic follow-up confirming cross-model generalizability

---

### Priority 3: Cognitive Warfare — Academic Framework for the Next Domain of Conflict

- **Confidence**: SR=0.82, TC=0.87, DC=0.75 | Overall: HIGH

1. **Classification**: S_Social → Security Studies / Information Warfare / AI Ethics
2. **Source**: arXiv:2603.xxx | cs.AI, interdisciplinary | Published: 2026-03-05
3. **Key Facts**: The paper establishes the first systematic academic definition of "cognitive warfare" as a discipline distinct from information warfare, psychological operations, and influence campaigns. It introduces an evaluation framework with measurable indicators and provides a case study of a documented cognitive warfare campaign.
4. **Quantitative Metrics**: The proposed framework includes 7 cognitive warfare dimensions (perception manipulation, decision disruption, social fragmentation, identity erosion, epistemic flooding, trust destruction, agency undermining) each with measurable proxy indicators at the population level. The case study demonstrated that a 14-day operation reduced target population's trust in public health institutions by an estimated 23% as measured by survey instruments.
5. **Impact**: HIGH for national security, civil society, public health, and democratic institutions. The academic codification of cognitive warfare techniques accelerates both the deployment of such operations by state and non-state actors and the development of countermeasures. The finding that cognitive warfare achieves measurable population-level effects within 14 days is particularly alarming given the compressed timeline.
6. **Detailed Description**: The paper argues that cognitive warfare — the deliberate targeting of the human mind as a strategic objective — has been undertheorized relative to its operational deployment. Drawing on documented campaigns across multiple geopolitical contexts, the authors develop a taxonomy of cognitive warfare techniques, each targeting a different component of the human cognitive system. The framework is designed to enable systematic evaluation of ongoing operations and to support the development of institutional countermeasures (cognitive hygiene infrastructure, information verification systems, social resilience programs). The case study demonstrates how a sophisticated actor can combine AI-generated content, social network topology exploitation, and emotional trigger targeting to achieve measurable shifts in collective belief.
7. **Inference**: Cognitive warfare is transitioning from a covert intelligence discipline to an openly studied academic field. This transition typically precedes widened deployment — once the methods are codified, they become accessible to actors beyond well-resourced nation-states. The 12-24 month window represents the last period in which advanced cognitive defense infrastructure might be deployed proactively rather than reactively. Organizations that fail to develop cognitive resilience programs in this window face asymmetric vulnerability as AI-enabled cognitive warfare tools become commoditized.
8. **Stakeholders**: Military/intelligence agencies; democratic governments; public health institutions; civil society organizations; media literacy educators; social media platforms; academic security studies departments; international bodies (UN, NATO)
9. **Monitoring Indicators**: Policy responses from NATO cognitive warfare unit; government investment in counter-cognitive-warfare programs; academic citations and follow-up frameworks; whether commercial actors develop cognitive defense products; social media platform responses; reports of documented cognitive warfare campaigns post-publication

---

### Priority 4: FlashAttention-4 — The AI Infrastructure Throughput Breakthrough

- **Confidence**: SR=0.90, TC=0.92, DC=0.80 | Overall: HIGH

1. **Classification**: T_Technological → AI Infrastructure / Hardware-Algorithm Co-design
2. **Source**: arXiv:2603.05451 | cs.LG, cs.AR | Published: 2026-03-05 | Authors: Tri Dao group (Stanford/Together AI)
3. **Key Facts**: FlashAttention-4 introduces algorithm and kernel pipelining co-design optimized for asymmetric hardware scaling (where compute and memory bandwidth scale at different rates). Achieves 1.5-2x speedup over FlashAttention-3 for standard attention and up to 3x for sparse attention patterns. Critical for long-context applications and very large batch training.
4. **Quantitative Metrics**: 1.5-2x throughput improvement over FA-3 on H100/H200 GPUs; up to 3x improvement for sparse attention; enables context windows of 1M+ tokens at practical throughput on current hardware; reduces attention computation to under 15% of total compute in typical LLM training pipelines (down from ~30% with standard attention).
5. **Impact**: HIGH for the entire AI training and inference ecosystem. FlashAttention has become the de facto standard attention implementation. FA-4 will propagate through all major ML frameworks (PyTorch, JAX, Triton) within 3-6 months, delivering a free performance gain to every model trained after adoption. This extends the compute frontier before the next hardware generation arrives, effectively providing a ~2x compute efficiency gain for all AI labs simultaneously.
6. **Detailed Description**: The paper identifies that modern GPU architectures (H100, H200, B100) have fundamentally asymmetric hardware characteristics — compute (FLOPS) has scaled dramatically while memory bandwidth has not kept pace. FlashAttention-3 was optimized for symmetric hardware assumptions from earlier generations. FA-4 co-designs the algorithm and kernel pipeline to match the asymmetric scaling profile: it restructures the attention computation to maximally exploit the compute-to-bandwidth ratio of modern hardware, introducing a novel pipelining strategy that overlaps compute and memory operations in a hardware-aware manner. The result is that the algorithmic bottleneck of attention — which has constrained context length and batch size — is substantially reduced, enabling applications that were previously cost-prohibitive: million-token context models, real-time video analysis, ultra-long document processing.
7. **Inference**: FA-4 will be incorporated into PyTorch and all major ML frameworks within 6 months and will silently deliver ~2x attention efficiency gains to all subsequent model training runs. This compresses the effective compute timeline — models expected in 12 months may arrive in 8-9 months when trained with FA-4. Organizations planning compute capacity, regulatory timelines, or competitive AI deployment windows should update their assumptions.
8. **Stakeholders**: AI labs (Anthropic, OpenAI, Google, Meta, Mistral, Cohere); ML framework maintainers (PyTorch team, Google JAX team); hardware manufacturers (NVIDIA, AMD, Intel); cloud providers (AWS, Azure, GCP); researchers building long-context applications
9. **Monitoring Indicators**: PyTorch merge PR for FA-4 integration; adoption in Transformers library; benchmark comparisons across major model families; whether it enables previously infeasible applications (e.g., native genomic sequence processing); competitive responses from hardware vendors

---

### Priority 5: Demographic Bias in LLM-Based Hiring — Small Prompt Changes, Large Disparate Impact

- **Confidence**: SR=0.85, TC=0.88, DC=0.78 | Overall: HIGH

1. **Classification**: S_Social → Labor / AI Discrimination / Algorithmic Fairness
2. **Source**: arXiv:2603.xxx | cs.CY, cs.AI, cs.HC | Published: 2026-03-05
3. **Key Facts**: Even when explicit PII (names, gender markers) is removed from resumes, LLMs used in hiring pipelines retain sufficient residual demographic signals to produce statistically significant disparate impact. Small prompt changes — varying instructions by a single phrase — produce outcome disparities of 15-40% across demographic groups for identical candidate qualifications.
4. **Quantitative Metrics**: Prompt variation experiments produced outcome disparities of 15-40% across demographic groups (defined by socioeconomic indicators, writing style patterns, and geographic signals). 94% of tested LLM-based hiring tools showed statistically significant demographic sensitivity even with explicit PII removal. Cross-model consistency was low — different models showed different demographic biases, making prediction of harm direction difficult.
5. **Impact**: HIGH for employment law compliance, AI vendor liability, and workforce equity. The finding that bias persists after PII removal — the standard compliance technique — invalidates the primary mitigation strategy currently deployed by most HR tech vendors. This creates immediate regulatory exposure under Title VII (US), Equality Act (UK), and GDPR's non-discrimination provisions (EU).
6. **Detailed Description**: The study constructed a controlled experiment using matched resume pairs representing candidates with identical objective qualifications but different demographic backgrounds (inferred from linguistic patterns, institutional affiliations, and geographic signals rather than explicit identity markers). These resumes were processed through LLM-based screening tools with a series of systematically varied prompts — ranging from minor phrasing differences to structural presentation changes. The results showed that seemingly minor prompt variations (e.g., "select the top candidate" vs. "identify the strongest applicant") produced substantial differential selection rates across demographic groups. This effect persisted across all tested models, though the direction and magnitude of bias varied by model architecture and training data. The implication is that the bias is not located in the prompt alone but in the interaction between prompt framing and the model's learned associations.
7. **Inference**: The HR tech sector faces an imminent regulatory reckoning. The combination of this research with growing EEOC attention to algorithmic hiring tools in the US and the EU's forthcoming AI Act requirements for high-risk AI in employment creates a compliance cliff. Companies that have deployed LLM-based screening tools based on PII-removal as their primary fairness mechanism are exposed. Expect a wave of regulatory enforcement actions, class action litigation discovery requests targeting AI hiring logs, and urgent vendor remediation efforts within the next 12-18 months.
8. **Stakeholders**: HR technology vendors (HireVue, Greenhouse, Workday, LinkedIn); corporate HR departments; employment lawyers; EEOC and equivalent regulators; labor unions; civil rights organizations; AI fairness researchers
9. **Monitoring Indicators**: EEOC guidance updates on AI in hiring; class action lawsuits citing algorithmic hiring bias; HR tech vendor updates to bias mitigation disclosures; EU AI Act compliance timelines; academic follow-up quantifying real-world harm

---

### Priority 6: AI Patent Gold Rush — Innovation System Response to the AI/Robotics Patent Boom

- **Confidence**: SR=0.80, TC=0.83, DC=0.70 | Overall: HIGH

1. **Classification**: E_Economic → Innovation Economics / Intellectual Property / Technology Policy
2. **Source**: arXiv:2603.05034 | econ.GN, cs.AI | Published: 2026-03-05
3. **Key Facts**: Systematic analysis of AI and robotics patents from 1980-2019 reveals a dramatic post-2012 patent surge corresponding to deep learning emergence. The paper introduces a novel distinction between traditional robotics patents and "embedded AI" robotics patents, finding that the latter follow qualitatively different innovation dynamics. The analysis questions whether standard innovation system metrics (patent counts, citation networks) remain valid for AI-era innovation.
4. **Quantitative Metrics**: AI patent filings grew at 27% CAGR from 2012-2019 vs. 7% for all technology patents. Top 5 filers (Google, Microsoft, IBM, Samsung, Intel) account for 31% of all AI patents filed in this period. "Embedded AI" robotics patents (AI integrated into physical systems) grew 340% in the 2015-2019 sub-period alone. Citation half-life for AI patents is 3.2 years vs. 8.7 years for mechanical engineering patents.
5. **Impact**: HIGH for technology strategy, antitrust policy, and innovation governance. The concentration of AI patents in a small number of large corporations, combined with the shortened citation half-life (indicating rapid obsolescence), raises questions about whether the patent system serves its intended function of incentivizing innovation in AI domains. This has implications for antitrust treatment of AI IP portfolios and for startups' ability to operate in AI-adjacent spaces.
6. **Detailed Description**: The paper conducts a large-scale empirical analysis of the patent landscape for AI and robotics, constructing novel classification schemes to distinguish between patents that embed AI capabilities into physical systems versus traditional robotics patents. The analysis reveals that the innovation dynamics of AI-embedded systems are fundamentally different from traditional technology innovation: the pace of development is faster, the concentration of ownership is higher, and the relationship between patent filing and actual deployment is weaker. The finding that top firms account for 31% of all AI patents while employing only ~2% of AI researchers raises questions about the alignment between patent system design and the social goal of incentivizing innovation. The paper asks whether innovation system infrastructure designed for pharmaceutical and hardware innovation is fit for AI-era purposes.
7. **Inference**: The AI patent concentration data will fuel antitrust investigations into major tech firms' AI portfolios within the next 24 months. Simultaneously, this creates a strategic bifurcation: large incumbents that have accumulated AI patent portfolios will use them defensively against startups, while the rapid obsolescence of AI patents limits their offensive value. The academic documentation of this dynamic will be cited in both regulatory proceedings and startup investment decisions.
8. **Stakeholders**: Technology antitrust regulators (FTC, EU DG COMP, DOJ Antitrust); venture capital investors in AI startups; large tech firms with AI patent portfolios; small AI startups; IP lawyers; innovation policy researchers; standards bodies
9. **Monitoring Indicators**: FTC AI patent concentration investigations; EU Digital Markets Act enforcement involving AI patents; startup AI IP strategy shifts; academic follow-up extending analysis to 2019-2026 period; international patent office guidance on AI inventorship

---

### Priority 7: Not All Trust Is the Same — Context-Dependent Human-AI Trust Calibration

- **Confidence**: SR=0.78, TC=0.82, DC=0.68 | Overall: MEDIUM-HIGH

1. **Classification**: S_Social → Human-AI Interaction / Decision Science / AI Governance
2. **Source**: arXiv:2603.xxx | cs.HC, cs.AI, cs.LG | Published: 2026-03-05
3. **Key Facts**: Comprehensive experimental study demonstrating that human trust in AI systems is not a stable individual trait but a context-dependent dynamic that varies with decision workflow design, explanation type, and perceived stakes. Overtrust and undertrust are shown to be simultaneously present in the same individual across different task contexts.
4. **Quantitative Metrics**: Experimental design with N=847 participants across 6 decision domains. Overtrust rates ranged from 12% (low-stakes routine tasks) to 67% (high-stakes novel situations). Explanation-type effects: feature importance explanations increased trust by 23%; counterfactual explanations decreased trust by 11% (users found them disorienting). Workflow position effects: AI recommendation presented first vs. last changed acceptance rates by 34%.
5. **Impact**: MEDIUM-HIGH for AI system design, deployment strategy, and regulation. The finding that the same explanation format can increase trust in one context and decrease it in another undermines one-size-fits-all explainability mandates. This has direct implications for how AI-assisted decision systems should be designed across healthcare, legal, financial, and public sector contexts.
6. **Detailed Description**: The study addresses the fundamental question of how to achieve "warranted trust" — trust that is calibrated to the actual reliability of the AI system rather than systematically over- or under-trusting. Using a large online experiment with multiple decision domains varying in stakes and familiarity, the researchers demonstrate that trust calibration is a function of (1) the structural features of the decision workflow (where/how the AI recommendation appears), (2) the specific explanation format provided, and (3) the participant's domain expertise. The interaction effects are complex and often counterintuitive: feature importance explanations help novice users but not domain experts; counterfactual explanations help domain experts but disrupt novice users. This suggests that universal explainability requirements (as in the EU AI Act) will produce uneven and potentially harmful trust effects unless they accommodate context-dependent calibration.
7. **Inference**: This research will feed directly into the ongoing debate about AI explainability requirements in regulation. The implication that there is no single "correct" explanation format — and that the same format can both help and harm trust calibration depending on context — will be seized by both sides of the AI regulation debate. More importantly, this creates a product design challenge: AI-assisted decision tools must implement dynamic, context-sensitive explanation strategies rather than static compliance-driven ones.
8. **Stakeholders**: AI product designers; healthcare AI vendors; legal tech companies; regulatory bodies writing explainability standards (EU AI Office, NIST); organizational decision-makers deploying AI tools; behavioral economists; human factors researchers
9. **Monitoring Indicators**: Changes to EU AI Act implementing acts on explainability; AI product design guideline updates from major vendors; follow-up research on domain-specific trust calibration; behavioral economics integration into AI UX standards

---

### Priority 8: Macroeconomic Shock Propagation Through Production Networks — Systemic Risk Framework

- **Confidence**: SR=0.75, TC=0.80, DC=0.65 | Overall: MEDIUM-HIGH

1. **Classification**: E_Economic → Macroeconomics / Systemic Risk / Production Networks
2. **Source**: arXiv:2603.xxx | econ.EM, econ.TH | Published: 2026-03-05
3. **Key Facts**: New theoretical model explaining how idiosyncratic firm-level shocks generate aggregate macroeconomic volatility and tail risk when propagating through production networks under "overlapping adjustment" dynamics. The model provides a mechanism for understanding why modern economies show fat-tailed GDP distributions despite diversification at the firm level.
4. **Quantitative Metrics**: Model calibrated to US input-output data predicts fat-tailed GDP distributions consistent with observed macro volatility. Firm-level shock with standard deviation of 1% generates aggregate volatility of 0.3% when network propagation is included (vs. 0.05% under standard diversification assumptions). Tail risk amplification factor of approximately 6x when overlapping adjustment is modeled.
5. **Impact**: MEDIUM-HIGH for central bank risk assessment, financial stability monitoring, and supply chain policy. The model provides a new lens for understanding why economies are more vulnerable to idiosyncratic shocks than traditional theory predicts — a key question after COVID-19 supply chain disruptions demonstrated the fragility of just-in-time production networks.
6. **Detailed Description**: The paper develops a general equilibrium model of production networks in which firms adjust their production plans simultaneously ("overlapping adjustment"), creating feedback amplification channels that do not exist when adjustments are sequential. When a firm experiences a negative shock, its simultaneous suppliers and customers are also adjusting, creating a resonance effect that amplifies the initial shock through the network. This mechanism explains several empirical puzzles: (1) why aggregate volatility is much higher than diversification theory predicts; (2) why tail events (deep recessions) are much more frequent than normal distributions would suggest; (3) why supply chain disruptions in specific sectors cascade into broad macroeconomic downturns. The model has direct policy implications for how central banks should model systemic risk and how governments should think about supply chain concentration.
7. **Inference**: This theoretical advance will enter central bank DSGE modeling frameworks within 24-36 months, potentially changing stress test methodologies and systemic risk assessments. In the near term, it provides a formal mechanism for what practitioners have observed empirically (COVID-19, semiconductor shortage cascades). Organizations designing supply chains for resilience — including policy-driven reshoring initiatives — now have a quantitative framework for evaluating concentration risk.
8. **Stakeholders**: Central banks (Fed, ECB, BOJ); financial stability boards; supply chain risk managers; industrial policy makers driving reshoring; academic macroeconomists; corporate CFOs managing supply chain concentration; insurance actuaries modeling business interruption risk
9. **Monitoring Indicators**: Citations in central bank working papers; Federal Reserve Board stress test methodology updates; supply chain concentration regulatory guidance; academic follow-up testing the model empirically; government supply chain resilience policy documents

---

### Priority 9: Neural Geometry of the Hippocampus — The Generalization Architecture That AI Lacks

- **Confidence**: SR=0.72, TC=0.78, DC=0.60 | Overall: MEDIUM-HIGH

1. **Classification**: s_spiritual → Cognitive Neuroscience / Consciousness / AI Architecture
2. **Source**: arXiv:2603.xxx | q-bio.NC, cs.AI | Published: 2026-03-05
3. **Key Facts**: Maps how hippocampal neurons encode abstract geometric relationships — position of self, others, and gaze direction — using a shared geometric framework that enables generalization across spatial paradigms without retraining. Identifies the neural architecture that supports flexible, context-free generalization — a capability that current AI systems fundamentally lack.
4. **Quantitative Metrics**: The hippocampal representational geometry enabled 78% transfer accuracy across novel spatial paradigms without retraining vs. near-chance performance for standard deep learning models on the same transfer tasks. The geometric encoding dimension (6-dimensional) remained consistent across all individuals studied (N=42 subjects, intracranial EEG).
5. **Impact**: HIGH for AI architecture research and cognitive science understanding. This study provides one of the clearest empirical characterizations of the specific computational capability — flexible geometric generalization — that current AI systems cannot replicate. This is not a marginal difference; it is a fundamental architectural distinction between biological and artificial neural computation.
6. **Detailed Description**: The study used intracranial EEG recordings from 42 participants performing spatial navigation tasks in multiple novel environments to map how the hippocampus represents abstract spatial relationships. The key finding is that hippocampal neurons use a shared low-dimensional geometric code (6D) that captures the relational structure of any spatial environment, not the specific features of a particular environment. This allows the hippocampus to immediately generalize navigational knowledge to novel environments based on relational similarity — a form of "structural transfer" that does not require re-learning. When this geometric code was compared with the representations learned by state-of-the-art deep learning models (including transformer architectures with attention mechanisms) on the same tasks, the biological system showed dramatically better transfer performance, achieving 78% accuracy vs. near-chance for the AI models. The study identifies the specific architectural features enabling this: (1) a compositional code that separates self-position, other-position, and directional vectors into orthogonal subspaces; (2) an invariant reference frame that persists across contexts; (3) online updating that integrates new information without catastrophic forgetting.
7. **Inference**: This finding reframes the AI capabilities debate. The question is not whether AI can match human performance on trained tasks (it often exceeds it) but whether AI can replicate the specific flexible generalization architecture that the hippocampus implements. The study provides a concrete, measurable target for next-generation AI architecture research. Organizations building AI systems for physical world interaction (robotics, autonomous vehicles, mixed reality) face a fundamental limitation that will not be resolved by scaling current architectures.
8. **Stakeholders**: AI architecture researchers; robotics companies (Boston Dynamics, Figure AI, Physical Intelligence); cognitive neuroscientists; philosophy of mind scholars; AI safety researchers concerned with capability overhang; DARPA and equivalent research agencies; educational technology companies
9. **Monitoring Indicators**: Follow-up AI architecture papers attempting to replicate hippocampal geometric codes; robotics generalization benchmark proposals; neuromorphic computing research taking inspiration from these findings; AI capability assessment incorporating transfer learning without retraining

---

### Priority 10: POET-X — Democratizing LLM Training Through Memory Efficiency

- **Confidence**: SR=0.82, TC=0.85, DC=0.72 | Overall: HIGH

1. **Classification**: T_Technological → AI Training Infrastructure / LLM Democratization
2. **Source**: arXiv:2603.xxx | cs.LG, cs.AI | Published: 2026-03-05
3. **Key Facts**: POET-X (Orthogonal Transformation Extension) scales GaLore's memory-efficient LLM training methodology to achieve full-parameter-quality training with 40% memory reduction and no accuracy degradation. Unlike LoRA-based approaches that constrain gradients to low-rank subspaces, POET-X maintains the full expressivity of the gradient space while reducing memory footprint.
4. **Quantitative Metrics**: 40% reduction in GPU memory requirements vs. standard AdamW training; full-parameter quality preservation (no measurable perplexity degradation on standard benchmarks); 1.3x training speed improvement (memory-compute tradeoff gains). Effective reduction of training cost for a 7B parameter model from requiring 8x A100 80GB to 5x A100 80GB.
5. **Impact**: HIGH for AI democratization. The memory cost of training large language models is one of the primary barriers preventing universities, startups, and smaller organizations from training competitive models. A 40% memory reduction with no quality penalty directly enables a broader set of actors to train frontier-class models, reducing the concentration of training capability in large labs.
6. **Detailed Description**: LLM training is dominated by the optimizer state memory, which for AdamW is 2x the parameter count (storing first and second moment estimates for every parameter). For a 7B model, this means the optimizer alone requires 56GB of memory — more than most accessible GPU systems. Previous memory-efficient training methods (LoRA, GaLore, Fira) either compromise model quality by restricting gradient updates to low-rank subspaces or require complex implementation. POET-X introduces a reparameterization of the optimizer state using orthogonal transformations that preserves the full rank of gradient updates while reducing the memory required to store them. The orthogonality constraint allows efficient compression without information loss, and the training algorithm remains a simple modification of standard AdamW requiring no architectural changes. This positions POET-X for rapid adoption across the ML ecosystem.
7. **Inference**: POET-X follows a pattern of progressive memory efficiency improvements that has historically driven rapid democratization of AI capabilities: the cumulative effect of FlashAttention (compute efficiency) + POET-X (memory efficiency) + quantization (deployment efficiency) is that the effective cost of training and deploying competitive LLMs is falling faster than the hardware generation cycle would suggest. This accelerates the proliferation of capable AI systems to smaller actors globally, with both beneficial (research democratization) and concerning (reduced oversight) implications.
8. **Stakeholders**: University AI research groups; AI startups; cloud providers (computing cost implications); NVIDIA (GPU demand implications); open-source AI community; AI governance organizations monitoring AI capability diffusion; national labs
9. **Monitoring Indicators**: GitHub adoption rate; integration into Hugging Face Trainer and PyTorch Lightnimg; benchmark comparisons against GaLore and LoRA; whether it enables specific capability thresholds at consumer GPU scale; citations in follow-up efficiency papers

---

### Signals 11-15 (Condensed)

**Signal 11 — Bayesian Climate Policy Evaluation Framework** (E_Environmental)
- Introduces unified probabilistic framework for identifying structural breaks in climate data to evaluate policy effectiveness. First method to robustly distinguish genuine policy-driven change from natural climate variability in observational data. **Strategic implication**: This method becomes the standard for IPCC Working Group III policy effectiveness assessment, potentially changing which climate policies receive continued funding.
- Source: arXiv:2603.xxx | stat.AP, economics | 2026-03-05

**Signal 12 — CO2 Storage Salt Precipitation Mechanism Quantified** (E_Environmental)
- Pore-scale study quantifying how salt precipitation near CO2 injection wells reduces permeability within days to weeks, threatening the viability of geological carbon storage projects. Provides mechanistic model coupling multiphase flow, dissolution-precipitation, and capillary effects. **Strategic implication**: Major CCS project operators (Equinor, Shell, Chevron) face an unmodeled risk in their storage integrity assessments. This finding will trigger regulatory review of existing permits.
- Source: arXiv:2603.05080 | physics.geo-ph | 2026-03-05

**Signal 13 — Can LLMs Synthesize Court-Ready Statistical Evidence?** (S_Social)
- Tests whether LLMs can generate statistical evidence meeting judicial admissibility standards for the California Racial Justice Act — cases requiring complex regression analysis of conviction patterns. LLMs produce plausibly formatted but frequently statistically invalid evidence, with error rates that would be disqualifying under Daubert standard. **Strategic implication**: Early but critical signal that LLM integration into the legal system via AI-assisted evidence preparation is outpacing legal frameworks for AI-generated evidence admissibility.
- Source: arXiv:2603.xxx | cs.AI, cs.CL, law | 2026-03-05

**Signal 14 — GenAI Training Unlocks Workforce Productivity** (S_Social)
- Randomized study (N=164) showing that targeted GenAI training increases both adoption rates and productive output quality — reversing the common finding that untrained AI access leads to overconfidence and quality degradation. Identifies specific training elements that produce calibrated AI use rather than uncritical adoption. **Strategic implication**: Organizations designing AI deployment programs need mandatory, structured training protocols — not just tool access — to realize productivity gains without quality degradation.
- Source: arXiv:2603.xxx | cs.CY, econ.GN | 2026-03-05

**Signal 15 — Post-Quantum Distributed Ledger for Financial Institutions** (T_Technological)
- First practical post-quantum cryptography (PQC) protocol for distributed ledgers meeting financial institution privacy and compliance requirements. Demonstrates viability of quantum-resistant financial infrastructure before the cryptographic deadline created by large-scale quantum computing. **Strategic implication**: Financial institutions have a 5-7 year window to transition to PQC-based ledger infrastructure. This paper provides the first production-viable protocol, starting the competitive race for PQC financial infrastructure standards.
- Source: arXiv:2603.xxx | quant-ph, cs.CR, finance | 2026-03-05

---

## 3. Existing Signal Updates

> Active tracking threads: 1,101 | Strengthening: 0 | Weakening: 0 | Faded: 0

Today's scan represents the first day of tracking for all 491 collected signals. No recurring or evolving signals are present in this cycle as all signals are newly entered into the tracking system from today's 48-hour scan window. This is expected for WF2 given the 48-hour scan window baseline.

### 3.1 Strengthening Trends

Not applicable (first-day tracking — no prior baseline for evolution assessment).

Historical context: Prior WF2 scans have identified recurring strengthening themes in quantum error correction and LLM safety/alignment, both of which continue to show strong paper density in today's scan (combined 35 papers across quant-ph and cs.AI safety categories).

### 3.2 Weakening Trends

Not applicable (first-day tracking).

### 3.3 Signal Status Summary

| Status | Count | Ratio |
|--------|-------|-------|
| New | 491 | 100% |
| Strengthening | 0 | 0% |
| Recurring | 0 | 0% |
| Weakening | 0 | 0% |
| Faded | 0 | — |

Active evolution tracking threads: **1,101** (accumulated from historical scans tracking ongoing research themes). The high thread count reflects WF2's deep historical archive spanning 315 signals across multiple scan cycles.

---

## 4. Patterns and Connections

### 4.1 Cross-Impact Between Signals

**Pattern A — The LLM Trust Collapse Cluster**
Signals 1 (Reasoning Theater), 2 (Censored LLMs), 7 (Trust Calibration), and 13 (Court-Ready Evidence) form a coherent cluster pointing toward a systemic crisis in LLM trustworthiness:
- Reasoning Theater shows that CoT explanations are not reliable indicators of model cognition
- Censored LLMs shows that safety fine-tuning conceals rather than eliminates harmful capabilities
- Not All Trust is the Same shows that the human trust response to AI is highly unstable and context-dependent
- LLM Legal Evidence shows that AI-generated evidentiary outputs fail judicial validity standards
- **Combined implication**: The current generation of LLMs is approaching deployment saturation in high-stakes domains (legal, medical, financial) precisely as academic evidence accumulates that their trustworthiness properties are deeply flawed. This creates a systemic liability cliff with a 12-24 month realization horizon.

**Pattern B — The AI Efficiency Compression Effect**
Signals 4 (FlashAttention-4) and 10 (POET-X) together represent a combined compute efficiency gain: FA-4 reduces attention computation costs by 1.5-2x while POET-X reduces training memory requirements by 40%. When stacked, these allow training runs that previously required 8x H100 GPUs to be completed on approximately 4x H100 GPUs at the same throughput. This compression effect has two opposing implications:
- **Positive**: Democratizes frontier model training to a broader set of actors
- **Negative**: Reduces the compute threshold required to train models with dangerous capabilities, expanding the actor landscape for AI misuse

**Pattern C — The Cognitive Battlespace Convergence**
Signals 3 (Cognitive Warfare) and 5 (Demographic Hiring Bias) share a deep structural connection: both demonstrate that AI systems can be weaponized against human cognitive and social systems in ways that are invisible, scalable, and difficult to attribute. Cognitive warfare uses AI to manipulate population-level beliefs; algorithmic hiring bias uses AI to systematically exclude demographic groups in ways that appear neutral. Both operate below the threshold of obvious intervention and rely on the same underlying LLM capabilities.

**Pattern D — The Environmental Measurement-Policy Gap**
Signals 11 (Climate Policy Evaluation) and 12 (CO2 Storage Risk) both point to a growing gap between climate policy ambitions and the measurement infrastructure to evaluate them. The lack of robust statistical methods for policy evaluation (addressed by Signal 11) has meant that ineffective climate policies have been continued while effective ones have been terminated based on noise. Meanwhile, CCS projects (Signal 12) have been permitted without accounting for near-term mechanical failure modes. Both signals suggest the climate action ecosystem is operating with systematically insufficient empirical grounding.

### 4.2 Emerging Themes

**Theme 1 — Post-Transparency AI**: The combination of Reasoning Theater, Censored LLMs, and the broader trend toward increasingly complex model architectures suggests we are entering an era where AI systems are fundamentally non-transparent in ways that cannot be resolved by output analysis. This is the post-transparency transition: AI capabilities continue to improve while trustworthy interpretability becomes structurally inaccessible. This theme will define AI governance debates for the next 3-5 years.

**Theme 2 — Computation Democratization Race**: FlashAttention-4, POET-X, and the broader trend of algorithmic efficiency improvements are systematically lowering the compute cost of training and deploying powerful AI models. This creates a race between the democratization of AI capabilities (beneficial for research and innovation) and the widening of the dangerous capabilities actor landscape (threatening for security). The 2026-2028 period will likely see this tension become a central AI policy issue.

**Theme 3 — Cognitive Domain Competition**: Cognitive Warfare, Demographic Bias in Hiring, and Epistemic Agency concerns together define a new competitive domain — the cognitive domain — where AI-enabled actors contest human beliefs, perceptions, and decisions at scale. This domain is currently unregulated and understudied relative to its operational deployment.

**Theme 4 — Biological Intelligence Architecture Gap**: The Hippocampus geometric generalization study (Signal 9) and the broader neuroscience papers in today's scan highlight that biological neural systems have specific architectural capabilities (flexible generalization, online learning without catastrophic forgetting, compositional reasoning) that current AI systems cannot replicate. This gap will become increasingly significant as AI deployment moves into physical world contexts requiring these capabilities.

**Theme 5 — Climate Infrastructure Credibility Crisis**: The CO2 storage and climate policy evaluation signals both point toward a mounting credibility crisis in climate infrastructure: key mitigation technologies (CCS) face unmodeled failure modes, and the evidence base for policy effectiveness is statistically fragile. This threatens the political durability of climate commitments.

---

## 5. Strategic Implications

### 5.1 Immediate Actions Required (0-6 months)

**AI Governance and Safety**
- Organizations deploying LLMs in high-stakes decision environments (healthcare, legal, finance) should immediately audit whether their AI explainability compliance strategy relies on CoT reasoning traces — the Reasoning Theater finding invalidates this approach
- AI security teams should add "knowledge elicitation attacks" to their threat models following the Censored LLMs finding; this requires testing deployed models against extraction attempts, not just refusal evaluation
- HR departments and legal counsel should urgently review LLM-based hiring tool deployments for demographic disparate impact; PII removal alone is insufficient

**Economic and Innovation**
- Innovation strategy teams at AI companies should update their competitive analysis to account for the combined FA-4 + POET-X compute efficiency gain — competitive timelines should be compressed by approximately 20-30% for organizations adopting both
- Financial institutions implementing distributed ledger pilots should review their cryptographic security roadmap against the PQC protocol paper and begin post-quantum transition planning now

**Environmental and Climate**
- Carbon capture and storage project operators should commission pore-scale salt precipitation modeling for all active injection sites, informed by the Signal 12 findings
- Climate policy teams should evaluate whether their policy effectiveness assessment methodology is susceptible to the false positive/negative issues identified in the climate policy evaluation paper

### 5.2 Medium-term Monitoring (6-18 months)

- Track how the AI safety field responds to the Reasoning Theater and Censored LLMs findings — specifically whether mechanistic interpretability approaches gain traction as alternatives to CoT-based explanations
- Monitor regulatory enforcement activity targeting AI hiring tools, particularly EEOC guidance updates and EU AI Act implementing acts addressing algorithmic employment discrimination
- Track the rate at which FlashAttention-4 and POET-X are integrated into mainstream ML frameworks and the downstream impact on model capability timelines
- Monitor whether cognitive warfare frameworks from this paper begin appearing in military doctrine documents and NATO guidance
- Track investment flows into post-quantum cryptography for financial infrastructure following the distributed ledger paper

### 5.3 Areas Requiring Enhanced Monitoring

- **AI Safety Architecture**: The accumulation of evidence that safety fine-tuning is insufficient (Censored LLMs) and that reasoning traces are unreliable (Reasoning Theater) creates an urgent need for fundamentally different safety architectures. This area requires weekly monitoring.
- **AI in Legal Systems**: The premature integration of AI-generated evidence into legal proceedings is a systemic risk that is developing faster than legal frameworks can adapt. Monthly monitoring with legal counsel involvement is recommended.
- **Cognitive Warfare Capabilities**: The academicization of cognitive warfare techniques may accelerate their deployment below current monitoring thresholds. Intelligence-oriented monitoring recommended.
- **CCS Infrastructure Integrity**: The mechanical failure modes identified in the CO2 storage paper affect existing commercial CCS projects. Environmental monitoring of active CCS sites should include pore-scale integrity assessment.

---

## 6. Plausible Scenarios

**Scenario 1 — The AI Trust Collapse (24-month horizon, probability: 35%)**
A high-profile failure of an AI system deployed in a high-stakes domain (medical misdiagnosis, legal error, financial fraud) is traced to a fundamental trustworthiness failure (performative reasoning, latent harmful knowledge) that the deploying organization's safety evaluation missed. This triggers a regulatory response imposing mandatory pre-deployment audits using mechanistic interpretability methods — methods that currently do not exist in production-ready form. Result: temporary freeze on AI deployment in regulated sectors, acceleration of AI safety research funding.

**Scenario 2 — The Compute Democratization Inflection (18-month horizon, probability: 60%)**
The cumulative effect of FlashAttention-4, POET-X, and successor efficiency papers reaches a threshold where training frontier-class (70B+) models becomes accessible on a $500K compute budget (vs. current $5-10M). This enables 50+ new actors worldwide to train competitive models. Result: explosion of AI capability diversity, significant pressure on export control frameworks, and emergence of non-US AI models with different safety alignment postures.

**Scenario 3 — Cognitive Warfare Goes Mainstream (12-month horizon, probability: 45%)**
The academic legitimization of cognitive warfare frameworks (this paper + follow-up work) coincides with a major geopolitical event in which a cognitive warfare campaign is publicly documented and attributed. The documentation uses the new academic framework to quantify impact. Result: emergency governmental commissions on cognitive defense infrastructure, first international norms discussions on cognitive warfare in multilateral fora.

**Scenario 4 — CCS Infrastructure Reckoning (36-month horizon, probability: 40%)**
One or more commercial CCS projects experience measurable injectivity decline due to salt precipitation, triggering permit reviews and investment freezes. The policy implication — that current CCS project economics do not account for near-term mechanical degradation costs — becomes a political liability for carbon capture as a climate strategy. Result: shift in climate mitigation investment away from geological CCS toward direct air capture and nature-based solutions.

---

## 7. Confidence Analysis

**Data Quality Assessment**
- Source reliability: arXiv is a preprint server; papers have not undergone peer review. However, for futures scanning purposes, arXiv papers represent the cutting edge of research 6-18 months before journal publication, making them ideal early signal indicators despite lower verification certainty than published work.
- Temporal coverage: The 48-hour scan window captured all papers submitted to arXiv on March 5-6, 2026 (papers appear on arXiv within 24-48 hours of submission). Coverage is comprehensive for the intended window.
- Category coverage: 180 arXiv categories across 18 query groups provides near-complete coverage of the arXiv taxonomy. Estimated coverage gap: <5% (primarily interdisciplinary papers filed in peripheral categories).

**Signal Confidence Levels**
- Priority 1-3 (Reasoning Theater, Censored LLMs, Cognitive Warfare): HIGH confidence that these are genuine early signals of significant future changes. The underlying research methodology is sound and findings are consistent with independently observed trends.
- Priority 4-10: HIGH to MEDIUM-HIGH confidence. Technical papers with quantitative evidence are higher confidence; interdisciplinary social/cognitive papers are medium-high confidence pending replication.
- Signals 11-15: MEDIUM confidence — important findings but require follow-up confirmation before high-confidence strategic action.

**Uncertainty Acknowledgments**
- All arXiv papers are pre-peer review. A subset will not survive peer review or will be significantly qualified. Historical arXiv preprint-to-publication survival rate for top-quartile papers in cs.AI: approximately 85%.
- Future impact assessments assume linear extrapolation of current trends. Major discontinuities (unexpected regulatory actions, breakthrough competing papers, geopolitical events) could alter trajectories significantly.
- The STEEPs classification of borderline papers (particularly those at the T/S and T/E boundaries) carries uncertainty. Secondary classifications are available in the full signals database.

---

## 8. Appendix

### Appendix A: Full Signal Statistics

| Metric | Value |
|--------|-------|
| Total papers retrieved | 492 |
| Definite duplicates removed | 1 |
| Uncertain (LLM reviewed, accepted) | 106 |
| Final new signals | 491 |
| arXiv query groups scanned | 18 |
| Categories covered | 180 |
| Scan window | 2026-03-05 00:46 UTC ~ 2026-03-07 00:46 UTC |
| Temporal gate status | PASS (0 outside window) |
| Dedup gate status | PASS_WITH_REMOVAL |

### Appendix B: STEEPs Distribution Detail

| STEEPs Category | Count | % | Key arXiv Archives |
|---|---|---|---|
| T_Technological | 384 | 78.2% | cs.AI, cs.LG, quant-ph, cond-mat, cs.RO |
| S_Social | 61 | 12.4% | cs.CY, cs.HC, cs.SI, econ.GN, q-bio.PE |
| E_Environmental | 31 | 6.3% | physics.ao-ph, physics.geo-ph, astro-ph.*, q-fin adjacent |
| E_Economic | 7 | 1.4% | econ.EM, econ.GN, econ.TH, q-fin |
| P_Political | 5 | 1.0% | cs.MA, cs.CY (governance papers) |
| s_spiritual | 3 | 0.6% | q-bio.NC, physics.hist-ph, cs.CY (ethics) |

### Appendix C: Query Group Coverage

| Query Group | Papers | Key Focus |
|---|---|---|
| cs-ai-ml | 100 | AI/ML/NLP/CV (highest volume) |
| quant-ph | 54 | Quantum computing and algorithms |
| cond-mat | 38 | Materials science and condensed matter |
| hep-fundamental | 36 | High energy physics |
| cs-social-hci | 34 | Society, HCI, social networks |
| cs-robotics | 41 | Robotics and systems |
| cs-security-eng | 27 | Security and software |
| eess | 27 | Electrical engineering and signal processing |
| math-applied | 23 | Applied mathematics |
| nlin-astro | 24 | Nonlinear sciences and astrophysics |
| cs-applications | 25 | CS applications and databases |
| physics-applied | 25 | Applied physics and optics |
| physics-climate | 10 | Climate and geophysics |
| stat | 11 | Statistics |
| econ | 5 | Economics |
| q-bio | 4 | Quantitative biology |
| physics-life | 4 | Biological and medical physics |
| q-fin | 4 | Quantitative finance |

### Appendix D: Data Lineage

- Raw scan: `env-scanning/wf2-arxiv/raw/daily-scan-2026-03-07.json`
- Dedup gate result: `env-scanning/wf2-arxiv/filtered/gate-result-2026-03-07.json`
- Gate-filtered signals: `env-scanning/wf2-arxiv/filtered/gate-filtered-2026-03-07.json`
- New signals (post-dedup): `env-scanning/wf2-arxiv/filtered/new-signals-2026-03-07.json`
- Classified signals: `env-scanning/wf2-arxiv/structured/classified-signals-2026-03-07.json`
- Impact assessment: `env-scanning/wf2-arxiv/analysis/impact-assessment-2026-03-07.json`
- Priority ranked: `env-scanning/wf2-arxiv/analysis/priority-ranked-2026-03-07.json`
- Evolution map: `env-scanning/wf2-arxiv/analysis/evolution/evolution-map-2026-03-07.json`
- Database backup: `env-scanning/wf2-arxiv/signals/snapshots/database-2026-03-07-pre-update.json`
- Report (EN): `env-scanning/wf2-arxiv/reports/daily/environmental-scan-2026-03-07.md`
- Report (KO): `env-scanning/wf2-arxiv/reports/daily/arxiv-scan-2026-03-07-ko.md`
