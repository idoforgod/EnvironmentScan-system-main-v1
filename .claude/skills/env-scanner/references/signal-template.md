# Signal Template Reference

## Standard Signal Structure

Every signal must conform to this template with all required fields completed.

---

## Required Fields

```json
{
  "id": "string - Unique identifier (e.g., 'signal-001')",
  "category": "string - STEEPs category (S, T, E, P, s)",
  "title": "string - Concise signal title",
  "date": "string - Detection date (YYYY-MM-DD)",
  "keyword": "array - List of key terms",
  "fact_qualitative": "string - Qualitative facts (what happened)",
  "fact_quantitative": "object - Quantitative metrics with values",
  "description": "string - Detailed explanation (200-500 words)",
  "inference": "string - Implications and projections",
  "writer_opinion": "string - Source author's perspective",
  "critical_thinking": "string - Critical analysis of claims",
  "status": "string - Signal maturity (emerging/developing/mature)",
  "stage_of_development": "string - Development stage",
  "technological_architecture": "string - (For tech signals) Technical structure",
  "application_area": "array - Potential application domains",
  "market_size_potential": "string - Estimated market size",
  "expansion_of_imagination": "string - Creative future possibilities",
  "actors_stakeholders": "array - Key actors and stakeholders",
  "first_detected": "string - First detection date",
  "source": "object - Source information",
  "leading_indicator": "string - Metrics to monitor signal evolution",
  "significance": "integer - Importance score (1-5)",
  "accuracy": "integer - Information reliability (1-5)",
  "confidence": "integer - Confidence level (1-5)",
  "innovative_capacity": "integer - Innovation potential (1-5)"
}
```

---

## Field Descriptions

### Basic Information

**id**: Unique identifier
- Format: `signal-NNN` (e.g., signal-001, signal-042)
- Auto-generated, never duplicate

**category**: STEEPs classification
- Must be one of: `S`, `T`, `E`, `P`, `s`
- See `steep-framework.md` for definitions

**title**: Signal headline
- Concise and descriptive (< 100 characters)
- Action-oriented when possible
- Example: "Quantum Computing Breakthrough in Drug Discovery"

**date**: Publication/detection date
- Format: YYYY-MM-DD
- Original source publication date

**keyword**: Key terms
- Array of 3-10 keywords
- Include: technology names, organizations, concepts
- Example: `["quantum computing", "drug discovery", "IBM"]`

---

### Facts and Analysis

**fact_qualitative**: What happened
- Objective description of the event/development
- 2-3 sentences
- Example: "IBM demonstrated a 1000-qubit quantum processor capable of simulating molecular interactions for drug discovery."

**fact_quantitative**: Measurable metrics
```json
{
  "metric": "qubits",
  "value": 1000,
  "change": "+300% vs 2025",
  "units": "qubits"
}
```

**description**: Detailed explanation
- 200-500 words
- Context, background, significance
- Technical details if applicable

**inference**: Implications
- What this signal means for the future
- Potential consequences (1st and 2nd order)
- Example: "May accelerate drug discovery timelines by 10x, disrupting pharmaceutical R&D models."

**writer_opinion**: Source perspective
- Original author's viewpoint
- Expert commentary from source
- Quote if available

**critical_thinking**: Critical analysis
- Evaluate claims skeptically
- Identify assumptions or gaps
- Note potential biases
- Example: "Claims require verification of quantum error correction rates. Previous breakthroughs had limited practical application."

---

### Development Stage

**status**: Maturity level
- `emerging`: Just appeared, low awareness
- `developing`: Gaining traction, evidence building
- `mature`: Widely recognized, established trend

**stage_of_development**: Specific stage
- Research/Prototype/Pilot/Commercial/Mature
- Varies by signal type

**technological_architecture**: (For tech signals)
- Technical structure or approach
- Example: "Superconducting qubit array with topological error correction"

---

### Impact and Applications

**application_area**: Potential uses
- Array of domains where signal applies
- Example: `["pharmaceuticals", "materials science", "cryptography"]`

**market_size_potential**: Economic scale
- Estimated market opportunity
- Include timeframe
- Example: "~$100B by 2035"

**expansion_of_imagination**: Future possibilities
- Creative, speculative applications
- Long-term transformative potential
- Example: "Could enable molecular-level drug design, simulating entire biological systems"

---

### Actors and Monitoring

**actors_stakeholders**: Key players
- Array of organizations, companies, institutions
- Example: `["IBM", "Pfizer", "NIST", "WHO"]`

**leading_indicator**: Monitoring metrics
- What to track for signal evolution
- Example: "Patent filings in quantum error correction, industry partnerships announced"

---

### Source Information

**source**: Origin details
```json
{
  "url": "https://nature.com/articles/quantum-2026",
  "type": "academic",
  "name": "Nature",
  "published_date": "2026-01-28"
}
```

**first_detected**: When we first saw this
- Our detection date (may differ from publication date)

---

### Scores (1-5 scale)

**significance**: How important is this signal?
- 1: Minor, niche impact
- 3: Moderate importance
- 5: Major, transformative impact

**accuracy**: How reliable is the information?
- 1: Unverified, speculative
- 3: Reasonable evidence
- 5: Peer-reviewed, verified

**confidence**: How confident are we in this signal?
- 1: Low confidence, many assumptions
- 3: Moderate confidence
- 5: High confidence, strong evidence

**innovative_capacity**: How innovative/disruptive?
- 1: Incremental improvement
- 3: Significant innovation
- 5: Paradigm-shifting, disruptive

---

### pSST (predicted Signal Scanning Trust)

**psst_score**: Composite confidence score (0-100)
- Weighted average of 6 dimensions
- Accumulated across 5 pipeline stages
- Calibrated via Platt Scaling when human feedback available

**psst_grade**: Letter grade derived from psst_score
- `A` (≥90): Very high confidence - auto-approve candidate
- `B` (70-89): Confident - standard processing
- `C` (50-69): Low confidence - flag for review
- `D` (<50): Very low confidence - require human review

**psst_dimensions**: Individual dimension scores (0-100 each)
```json
{
    "SR": 85,   // Source Reliability - trustworthiness of origin
    "ES": 70,   // Evidence Strength - supporting evidence quality
    "CC": 85,   // Classification Confidence - STEEPs category certainty
    "TC": 100,  // Temporal Confidence - freshness and timeliness
    "DC": 100,  // Distinctiveness Confidence - uniqueness after dedup
    "IC": 72    // Impact Confidence - impact prediction certainty
}
```

**Dimension sources** (which pipeline stage produces each):
| Dimension | Agent | Pipeline Stage |
|-----------|-------|----------------|
| SR | @multi-source-scanner | Stage 1: Collection |
| TC | @multi-source-scanner | Stage 1: Collection |
| DC | @deduplication-filter | Stage 2: Filtering |
| ES | @signal-classifier | Stage 3: Classification |
| CC | @signal-classifier | Stage 3: Classification |
| IC | @impact-analyzer | Stage 4: Impact Analysis |

---

## Example Complete Signal

```json
{
  "id": "signal-001",
  "category": "T",
  "title": "IBM Demonstrates 1000-Qubit Quantum Processor",
  "date": "2026-01-28",
  "keyword": ["quantum computing", "IBM", "drug discovery", "qubits"],
  "fact_qualitative": "IBM announced a breakthrough 1000-qubit quantum processor capable of maintaining coherence for 100 microseconds.",
  "fact_quantitative": {
    "metric": "qubit_count",
    "value": 1000,
    "change": "+300% vs 2025",
    "coherence_time": "100 microseconds"
  },
  "description": "IBM Research published results in Nature demonstrating... (detailed description)",
  "inference": "This development may accelerate computational drug discovery by enabling molecular simulation at unprecedented scales.",
  "writer_opinion": "Lead researcher states this is 'the threshold for practical quantum advantage in chemistry.'",
  "critical_thinking": "While impressive, practical applications require further validation of error correction claims. Previous announcements have overestimated near-term impact.",
  "status": "emerging",
  "stage_of_development": "prototype",
  "technological_architecture": "Superconducting transmon qubits with surface code error correction",
  "application_area": ["pharmaceutical R&D", "materials science", "cryptography"],
  "market_size_potential": "Quantum computing market projected at $125B by 2035",
  "expansion_of_imagination": "Could eventually simulate entire biological systems, revolutionizing personalized medicine and synthetic biology.",
  "actors_stakeholders": ["IBM", "pharmaceutical companies", "NIST", "competing quantum firms"],
  "first_detected": "2026-01-29",
  "source": {
    "url": "https://nature.com/articles/quantum-breakthrough-2026",
    "type": "academic",
    "name": "Nature",
    "published_date": "2026-01-28"
  },
  "leading_indicator": "Monitor: patent filings in quantum error correction, pharmaceutical partnerships, academic citations",
  "significance": 5,
  "accuracy": 4,
  "confidence": 4,
  "innovative_capacity": 5,
  "psst_score": 87.3,
  "psst_grade": "B",
  "psst_dimensions": {
    "SR": 85,
    "ES": 70,
    "CC": 85,
    "TC": 100,
    "DC": 100,
    "IC": 72
  }
}
```

---

## Version
**Template Version**: 2.0
**pSST Integration**: psst_score, psst_grade, psst_dimensions fields added
**Last Updated**: 2026-01-30
