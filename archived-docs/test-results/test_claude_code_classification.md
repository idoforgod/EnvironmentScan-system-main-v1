# Test: Claude Code Direct Classification

**Purpose**: Validate the new architecture where Claude Code classifies papers directly
**Date**: 2026-01-30
**Status**: Ready for execution

---

## Test Plan

### Test 1: Full Workflow (Step 1.2 Phase A + B)

**Objective**: Verify complete scan-and-classify workflow

**Steps**:
1. Run Step 1.2 Phase A (Collection):
   ```bash
   cd env-scanning
   python3 scripts/run_multi_source_scan.py --days-back 7
   ```

2. Verify output file created:
   ```bash
   ls -lh raw/daily-scan-2026-01-30.json
   ```

3. Read the file and classify papers (Step 1.2 Phase B):
   - Use Claude Code to read `raw/daily-scan-2026-01-30.json`
   - Apply classification logic from `.claude/agents/workers/classification-prompt-template.md`
   - Save to `structured/classified-signals-2026-01-30.json`

4. Verify classifications:
   - All signals have `final_category`
   - All have `classification_confidence`
   - All have `classification_reasoning`
   - All have `classification_method: "claude_code_direct"`
   - All have `classification_cost: 0.0`

**Expected Result**:
- ✅ 100-150 papers collected
- ✅ All papers classified
- ✅ Average confidence > 0.80
- ✅ Cost: $0.00

---

### Test 2: Sample Paper Classification

**Objective**: Verify classification accuracy on specific examples

**Test Cases**:

#### Case 1: AI Ethics Paper (should be 's', not 'T')
```json
{
  "title": "Ethical Considerations in Large Language Model Deployment",
  "content": {
    "abstract": "This paper examines the ethical implications of deploying large language models..."
  },
  "preliminary_category": "T"
}
```

**Expected**:
- `final_category: "s"`
- `classification_confidence: > 0.85`
- Reasoning mentions ethics/values

#### Case 2: Solar Technology Paper (should be 'T', not 'E')
```json
{
  "title": "High-Efficiency Perovskite Solar Cells with Novel Architecture",
  "content": {
    "abstract": "We demonstrate a new solar cell design that achieves 45% efficiency..."
  },
  "preliminary_category": "E"
}
```

**Expected**:
- `final_category: "T"`
- `classification_confidence: > 0.85`
- Reasoning mentions engineering/innovation

#### Case 3: Economic Policy Paper
```json
{
  "title": "Central Bank Digital Currencies and Monetary Policy",
  "content": {
    "abstract": "Analysis of how central bank digital currencies affect monetary policy effectiveness..."
  },
  "preliminary_category": "P"
}
```

**Expected**:
- `final_category: "E"` (could be P, but E is primary)
- `classification_confidence: > 0.75`
- Reasoning mentions monetary/economic mechanisms

---

### Test 3: Performance Metrics

**Objective**: Measure speed and cost

**Metrics to collect**:
1. Collection time (Phase A): Should be ~15 seconds for 120 papers
2. Classification time (Phase B): Should be ~1-2 minutes for 120 papers
3. Total time: Should be < 3 minutes
4. Cost: Should be $0.00

**Commands**:
```bash
# Time the full workflow
time (cd env-scanning && python3 scripts/run_multi_source_scan.py --days-back 7)

# Then classify (manual timing)
# Start time: [record]
# ... classification ...
# End time: [record]
```

---

### Test 4: Quality Verification

**Objective**: Ensure classification quality meets targets

**Checks**:
1. **Category distribution** (should be reasonable):
   - T (Technological): 30-45%
   - E (Economic): 10-20%
   - E (Environmental): 5-15%
   - S (Social): 10-20%
   - P (Political): 10-20%
   - s (spiritual): 5-15%

2. **Confidence distribution**:
   - Average: > 0.80
   - High (>0.85): > 60%
   - Medium (0.7-0.85): 20-40%
   - Low (<0.7): < 20%

3. **Reasoning quality**:
   - All non-empty
   - All explain the choice
   - Most are 1-2 sentences

4. **No errors**:
   - All categories valid (S, T, E, E, P, s only)
   - All confidence values 0.0-1.0
   - All required fields present

---

### Test 5: Comparison with Preliminary

**Objective**: Measure improvement over preliminary classification

**Process**:
1. Load classified signals
2. Compare `preliminary_category` vs `final_category`
3. Calculate:
   - Match rate: How often they agree
   - Correction rate: How often Claude Code changed it
   - Typical corrections: Which categories get corrected most

**Expected Results**:
- Match rate: 70-80% (preliminary is 75% accurate)
- Correction rate: 20-30%
- Common corrections:
  - T → s (AI ethics papers)
  - E (environmental) → T (climate tech papers)
  - P → E (economic policy papers)
  - T → S (AI social impact papers)

---

## Test Execution Checklist

### Pre-test
- [ ] arXiv scanner is configured and enabled
- [ ] `config/sources.yaml` has arXiv enabled
- [ ] `config/domains.yaml` has STEEPs categories
- [ ] Working directory is `env-scanning/`

### Test 1: Full Workflow
- [ ] Phase A completes successfully
- [ ] Output file `raw/daily-scan-{date}.json` created
- [ ] File contains 50-500 signals
- [ ] Phase B classification executes
- [ ] Output file `structured/classified-signals-{date}.json` created
- [ ] All signals classified

### Test 2: Sample Classifications
- [ ] Case 1 (AI Ethics): Classified as 's' ✅
- [ ] Case 2 (Solar Tech): Classified as 'T' ✅
- [ ] Case 3 (CBDC): Classified appropriately ✅

### Test 3: Performance
- [ ] Collection time < 30s
- [ ] Classification time < 3 min for 100 papers
- [ ] Total workflow time < 5 min
- [ ] Cost = $0.00 ✅

### Test 4: Quality
- [ ] Category distribution reasonable
- [ ] Average confidence > 0.80
- [ ] All reasoning fields populated
- [ ] No invalid categories

### Test 5: Comparison
- [ ] Preliminary match rate calculated
- [ ] Correction rate calculated
- [ ] Common correction patterns identified

---

## Success Criteria

**Pass if**:
- ✅ All signals successfully classified
- ✅ Average confidence > 0.80
- ✅ No invalid categories
- ✅ All reasoning populated
- ✅ Cost = $0.00
- ✅ Execution time < 5 minutes
- ✅ >20% corrections from preliminary (shows improvement)

**Fail if**:
- ❌ Classification fails or errors
- ❌ Average confidence < 0.70
- ❌ Invalid categories present
- ❌ Missing required fields
- ❌ Cost > $0.00
- ❌ Execution time > 10 minutes

---

## Expected Results Summary

### Quantitative
| Metric | Target | Expected |
|--------|--------|----------|
| **Papers collected** | 50-500 | 100-150 |
| **Classification accuracy** | >90% | 90-92% |
| **Average confidence** | >0.80 | 0.85-0.90 |
| **Collection time** | <30s | ~15s |
| **Classification time** | <5min | ~2min |
| **Total time** | <10min | ~3min |
| **Cost** | $0 | $0 ✅ |

### Qualitative
- Classifications should be **context-aware** (not just keyword matching)
- Reasoning should be **explanatory** (not just repetitive)
- Category distribution should be **realistic** (T dominates, s is rare)
- Corrections from preliminary should make **semantic sense**

---

## Post-Test Analysis

After completing tests, analyze:

### 1. Accuracy Assessment
- Review sample of classifications manually
- Check if final_category makes sense
- Identify any systematic errors

### 2. Performance Optimization
- Identify bottlenecks
- Consider batch processing improvements
- Evaluate if parallel classification is needed

### 3. Quality Improvements
- Review low-confidence cases
- Update classification guidelines if needed
- Add examples for ambiguous cases

### 4. Documentation Updates
- Update metrics in `CLAUDE_CODE_DIRECT_CLASSIFICATION.md`
- Document any issues or edge cases
- Create FAQ if needed

---

## Next Steps After Test

**If tests pass**:
1. ✅ Mark system as production-ready
2. ✅ Update system readiness: 97% → 99%
3. ✅ Run full end-to-end workflow test
4. ✅ Schedule first production scan

**If tests fail**:
1. ❌ Review failure modes
2. ❌ Adjust classification logic
3. ❌ Re-run tests
4. ❌ Document issues

---

## Test Log Template

```
TEST EXECUTION LOG
==================
Date: 2026-01-30
Tester: [Name or "Automated"]
Environment: EnvironmentScan-system-main

Test 1: Full Workflow
---------------------
✅ Phase A: Collection
   - Papers collected: 120
   - Time: 15.47s
   - File: raw/daily-scan-2026-01-30.json

✅ Phase B: Classification
   - Papers classified: 120/120
   - Time: 2m 15s
   - File: structured/classified-signals-2026-01-30.json
   - Avg confidence: 0.89
   - Cost: $0.00

Test 2: Sample Classifications
-------------------------------
✅ Case 1 (AI Ethics): s (confidence: 0.92)
✅ Case 2 (Solar Tech): T (confidence: 0.91)
✅ Case 3 (CBDC): E (confidence: 0.85)

Test 3: Performance
-------------------
✅ Collection: 15.47s (<30s target)
✅ Classification: 2m 15s (<5m target)
✅ Total: 2m 30s (<10m target)
✅ Cost: $0.00

Test 4: Quality
---------------
✅ Category distribution:
   - T: 42 (35%)
   - E: 24 (20%)
   - P: 18 (15%)
   - S: 16 (13%)
   - E: 12 (10%)
   - s: 8 (7%)

✅ Confidence distribution:
   - High (>0.85): 78 (65%)
   - Medium (0.7-0.85): 35 (29%)
   - Low (<0.7): 7 (6%)
   - Average: 0.89

✅ Reasoning: All populated, appropriate

Test 5: Comparison
------------------
✅ Preliminary match: 85/120 (71%)
✅ Corrections: 35/120 (29%)
   - T→s: 12 (AI ethics)
   - E→T: 8 (climate tech)
   - P→E: 7 (economic policy)
   - T→S: 5 (AI social impact)
   - Other: 3

OVERALL: ✅ PASS
All success criteria met.
System ready for production.
```

---

**Test Document Version**: 1.0
**Status**: Ready for execution
**Expected Outcome**: ✅ Pass
