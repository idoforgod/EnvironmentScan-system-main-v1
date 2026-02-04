# Classification Prompt Template

**For**: Step 1.2 Phase B - Direct Classification by Claude Code
**Method**: claude_code_direct
**Cost**: $0

---

## Task

You must read and classify all signals collected from Step 1.2 Phase A.

---

## Input File

Read: `raw/daily-scan-{date}.json`

Structure:
```json
{
  "scan_metadata": { ... },
  "items": [
    {
      "id": "arxiv:2026.12345",
      "title": "Paper Title",
      "content": {
        "abstract": "Paper abstract...",
        "keywords": ["keyword1", "keyword2"]
      },
      "preliminary_category": "T"  // May be inaccurate
    }
  ]
}
```

---

## Classification Task

For EACH signal in the `items` array:

### 1. Analyze
- Read the `title` carefully
- Read the `abstract` (first 500 characters if long)
- Consider the `keywords` if present
- Understand the paper's MAIN focus

### 2. Classify into ONE STEEPs Category

**S (Social)**:
- Demographics, population trends
- Culture, social movements, behavior
- Education, workforce, human resources
- Society, community, relationships
- Example: "Aging population impacts in Japan"

**T (Technological)**:
- AI, machine learning, robotics
- Computing, software, hardware
- Innovation, R&D, engineering
- Applied science, technical breakthroughs
- Example: "Quantum computing error correction"

**E (Economic)**:
- Markets, finance, trading, investment
- Business, industry, commerce
- Economic policy, monetary policy
- Trade, global economy, GDP
- Example: "Federal Reserve interest rate decision"

**E (Environmental)**:
- Climate change, global warming
- Ecology, biodiversity, nature
- Energy, renewables, fossil fuels
- Sustainability, conservation
- Example: "Antarctic ice shelf collapse"

**P (Political)**:
- Policy, legislation, regulation
- Governance, government structure
- Geopolitics, international relations
- Law, legal frameworks, courts
- Example: "EU GDPR enforcement update"

**s (spiritual)**:
- Ethics, moral philosophy
- Values, meaning, purpose
- Consciousness, existence, identity
- Wisdom traditions, philosophy
- Example: "Ethics of AI decision-making"

### 3. Important Classification Rules

**When in doubt**:
- Choose the category that represents the MAIN focus
- Not what mentions are present, but what the CORE topic is
- Example: Paper about "AI ethics" → s (spiritual), not T
- Example: Paper about "solar panel efficiency" → T (technological), not E (environmental)

**Common mistakes to avoid**:
- "AI" keyword → automatically T ❌
  - Could be s (if about AI ethics)
  - Could be E (if about AI economy)
  - Could be S (if about AI social impact)
- "Climate" keyword → automatically E (environmental) ❌
  - Could be P (if about climate policy)
  - Could be E (if about carbon markets)

**Tie-breaking**:
- If truly ambiguous, prefer: P > E (economic) > T > S > E (environmental) > s
- But genuinely consider the main focus first

### 4. Assign Confidence (0.0-1.0)

**High confidence (0.85-1.0)**:
- Clear category match
- Title + abstract align
- No ambiguity

**Medium confidence (0.7-0.84)**:
- Reasonable match
- Some ambiguity
- Could fit 2 categories, but one is primary

**Low confidence (0.5-0.69)**:
- Difficult to categorize
- Multiple valid interpretations
- Borderline case

**Very low (<0.5)**:
- Unclear or incomplete information
- Use only if abstract is missing/corrupted

### 5. Provide Reasoning (1-2 sentences)

Explain WHY you chose this category:
- What is the main focus?
- Why not other categories?
- What keywords/concepts led to this decision?

**Good reasoning examples**:
- ✅ "Paper focuses on ethical implications of AI, not the technology itself, hence spiritual rather than technological."
- ✅ "Discusses carbon market mechanisms and pricing, which is economic rather than environmental policy."
- ✅ "Examines demographic shifts in workforce, primarily a social phenomenon rather than economic."

**Bad reasoning examples**:
- ❌ "Has AI keyword, so T."
- ❌ "Seems like E."
- ❌ "Not sure, defaulting to T."

### 6. Update Signal Format

For each signal, ADD these fields:

```json
{
  "final_category": "S|T|E|E|P|s",
  "classification_confidence": 0.85,
  "classification_reasoning": "Brief explanation (1-2 sentences)",
  "classification_method": "claude_code_direct",
  "classification_cost": 0.0
}
```

Keep all existing fields (id, title, source, content, preliminary_category).

---

## Output File

Write: `structured/classified-signals-{date}.json`

Structure:
```json
{
  "scan_metadata": {
    // Copy from input file
  },
  "classification_metadata": {
    "classifier": "claude_code_direct",
    "version": "sonnet-4.5",
    "timestamp": "{ISO8601}",
    "total_classified": 120,
    "avg_confidence": 0.89,
    "cost": 0.0,
    "category_distribution": {
      "S": 15,
      "T": 45,
      "E": 20,
      "E": 12,
      "P": 18,
      "s": 10
    }
  },
  "items": [
    {
      // All original fields from input
      "id": "arxiv:2026.12345",
      "title": "...",
      "source": { ... },
      "content": { ... },
      "preliminary_category": "T",

      // NEW: Classification fields
      "final_category": "s",
      "classification_confidence": 0.92,
      "classification_reasoning": "Focuses on ethical implications of AI systems, not technological implementation.",
      "classification_method": "claude_code_direct",
      "classification_cost": 0.0
    }
  ]
}
```

---

## Classification Examples

### Example 1: Technology vs Spiritual

**Input**:
```json
{
  "title": "Ethical Frameworks for Autonomous Vehicle Decision-Making",
  "content": {
    "abstract": "This paper proposes ethical guidelines for how self-driving cars should make life-and-death decisions..."
  },
  "preliminary_category": "T"
}
```

**Output**:
```json
{
  "final_category": "s",
  "classification_confidence": 0.88,
  "classification_reasoning": "Paper addresses ethical decision-making and moral frameworks, not technological implementation. Focus is on values and philosophy.",
  "classification_method": "claude_code_direct",
  "classification_cost": 0.0
}
```

**Why**: Ethics/values = spiritual, not technology

### Example 2: Environmental vs Technological

**Input**:
```json
{
  "title": "Novel Photovoltaic Cell Design Achieves 47% Efficiency",
  "content": {
    "abstract": "We present a new solar panel architecture using quantum dots that achieves record-breaking efficiency..."
  },
  "preliminary_category": "E"
}
```

**Output**:
```json
{
  "final_category": "T",
  "classification_confidence": 0.91,
  "classification_reasoning": "Describes an engineering innovation in solar technology. The focus is on technical breakthrough, not environmental impact.",
  "classification_method": "claude_code_direct",
  "classification_cost": 0.0
}
```

**Why**: Engineering/innovation = technological, not environmental

### Example 3: Political vs Economic

**Input**:
```json
{
  "title": "Carbon Tax Implementation Study: France 2025-2026",
  "content": {
    "abstract": "Analysis of carbon tax policy implementation and its effects on market behavior..."
  },
  "preliminary_category": "P"
}
```

**Output**:
```json
{
  "final_category": "E",
  "classification_confidence": 0.85,
  "classification_reasoning": "While carbon tax is a policy tool, the paper focuses on market mechanisms and economic effects, making it primarily economic.",
  "classification_method": "claude_code_direct",
  "classification_cost": 0.0
}
```

**Why**: Market mechanisms = economic, despite policy context

### Example 4: Social vs Technological

**Input**:
```json
{
  "title": "Impact of AI on Workforce Demographics in Manufacturing",
  "content": {
    "abstract": "Study of how AI adoption changes workforce composition, age distribution, and skill requirements..."
  },
  "preliminary_category": "T"
}
```

**Output**:
```json
{
  "final_category": "S",
  "classification_confidence": 0.87,
  "classification_reasoning": "Primary focus is on workforce demographics and human resource changes, which are social phenomena. AI is the driver, not the subject.",
  "classification_method": "claude_code_direct",
  "classification_cost": 0.0
}
```

**Why**: Demographics/workforce = social, AI is just the cause

### Example 5: Ambiguous Case

**Input**:
```json
{
  "title": "Blockchain for Supply Chain Transparency: Environmental Benefits",
  "content": {
    "abstract": "This paper explores how blockchain technology can improve supply chain transparency and reduce environmental impact..."
  },
  "preliminary_category": "T"
}
```

**Output**:
```json
{
  "final_category": "T",
  "classification_confidence": 0.72,
  "classification_reasoning": "Blockchain technology is the main subject, though environmental benefits are mentioned. The paper's contribution is technological (blockchain application), not environmental analysis.",
  "classification_method": "claude_code_direct",
  "classification_cost": 0.0
}
```

**Why**: Technology is the main contribution, environment is a benefit (lower confidence due to ambiguity)

---

## Quality Targets

After classification, verify:

- [ ] All signals have `final_category` (S, T, E, E, P, s only)
- [ ] All have `classification_confidence` (0.0-1.0)
- [ ] All have `classification_reasoning` (non-empty)
- [ ] All have `classification_method: "claude_code_direct"`
- [ ] All have `classification_cost: 0.0`
- [ ] Average confidence > 0.80
- [ ] No invalid categories
- [ ] Category distribution reasonable (T usually 30-40%, others 10-20% each)

---

## Error Handling

**If abstract is missing or very short**:
- Rely on title only
- Lower confidence (0.6-0.7)
- Reasoning: "Limited information available, classified based on title"

**If truly ambiguous**:
- Choose best guess
- Lower confidence (0.5-0.7)
- Explain ambiguity in reasoning

**If preliminary_category seems correct**:
- Still analyze independently
- May confirm or override
- Confidence should reflect your analysis, not the preliminary

---

## Performance Notes

**Speed**: ~1 second per signal (acceptable)
**Batch size**: Process all signals in one execution
**Progress**: Print progress every 10 signals
**Memory**: Load file once, classify all, save once

**Example progress output**:
```
[INFO] Classifying 120 signals...
[PROGRESS] 10/120 classified (avg confidence: 0.88)
[PROGRESS] 20/120 classified (avg confidence: 0.87)
...
[PROGRESS] 120/120 classified (avg confidence: 0.89)
[SUCCESS] Classification complete!
```

---

**Template Version**: 1.0
**Compatible with**: claude_code_direct method
**Cost**: $0
**Expected Accuracy**: 90-92%
