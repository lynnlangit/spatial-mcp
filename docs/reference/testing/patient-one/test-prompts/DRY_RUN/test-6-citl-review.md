TEST 6: Clinician-in-the-Loop (CitL) Review & Approval
========================================================

> **Prompt library:** This is the canonical prompt for [Clinical Workflow Prompt 6](../../../../prompts/clinical-workflow.md#prompt-6-clinician-in-the-loop-validation). See that page for clinical interpretation context and expected output summary.

Patient ID: PAT001-OVC-2025
Cancer Type: High-Grade Serous Ovarian Carcinoma (HGSOC), Stage IV, Platinum-Resistant

⚠️ PREREQUISITE: Complete TEST_5_INTEGRATION before running this test

## Overview

This test implements the formal Clinician-in-the-Loop (CitL) validation workflow where an oncologist reviews and validates the "stitched results" from TEST_1-5 before they are finalized into a clinical report. This demonstrates AI as a "co-pilot" rather than an autonomous decision-maker in high-stakes oncology care.

**Workflow:** Draft Report → Automated QC → Clinician Review → Approve/Revise/Reject → Final Report

**Time Estimate:** 30-45 minutes total
- Automated steps: ~40 seconds
- Manual clinician review: 20-30 minutes

**New Concepts:**
- Draft vs. Approved Reports
- Automated Quality Gates
- Structured Clinical Review
- Digital Signatures & Audit Trail
- HIPAA-Compliant 10-Year Retention

---

## STEP 1: Generate Draft Clinical Report (Automated, ~30 seconds)

### Run the Enhanced Report Generator

```bash
cd /Users/lynnlangit/Documents/GitHub/spatial-mcp

python servers/mcp-patient-report/scripts/generate_patient_report.py \
  --patient-id PAT001-OVC-2025 \
  --output-dir ./results \
  --generate-draft
```

**What this does:**
1. Consolidates findings from TEST_1 (clinical), TEST_2 (multiomics), TEST_3 (spatial), TEST_4 (imaging), TEST_5 (integration)
2. Runs automated quality checks (6 checks: sample size, FDR thresholds, data completeness, cross-modal consistency, etc.)
3. Generates structured JSON output for review workflow
4. Flags issues requiring clinician attention

### Expected Output Files

✅ **draft_report.json** - Structured findings for CitL review
- Contains: patient metadata, quality checks, clinical findings from all 5 tests, key molecular findings (top 10), treatment recommendations, quality flags

✅ **quality_checks.json** - Automated QC results
- Sample size check: ≥30 spots/region
- FDR thresholds: FDR < 0.05 for significant DEGs
- Data completeness: >95% non-missing
- Cross-modal consistency: RNA-protein correlation

✅ **clinical_summary.txt** - Human-readable summary
- Plain language summary of findings
- Treatment implications
- Monitoring recommendations

### Quality Gate Validation

Verify all quality checks passed (or flags documented):

- [ ] **Sample sizes adequate:** tumor_core ≥30 spots, stroma ≥30 spots
- [ ] **FDR thresholds met:** All significant DEGs have FDR < 0.05
- [ ] **Data completeness:** >95% of expression values present
- [ ] **Cross-modal consistency:** TP53 mutation (genomics) matches TP53+ cells (imaging)

**If quality checks fail:**
- Review `quality_checks.json` for details
- Assess whether flags are acceptable or require action
- Document assessment in clinician review (Section 4)

---

## STEP 2: Clinician Review (Manual, 20-30 minutes)

### Reviewer Role

**Primary Reviewer:** Dr. Sarah Johnson
**Credentials:** MD, Gynecologic Oncology
**Role:** Oncologist specializing in ovarian cancer

**Review Objectives:**
1. Validate molecular findings against clinical presentation
2. Assess NCCN guideline compliance
3. Evaluate treatment recommendation appropriateness
4. Review quality flags
5. Make final approval decision

### Review Process

#### 2A. Open Draft Report

```bash
# View draft report
open ./results/PAT001-OVC-2025/draft_report.json

# OR view in terminal
cat ./results/PAT001-OVC-2025/draft_report.json | python -m json.tool | less
```

#### 2B. Review Clinical Summary

```bash
cat ./results/PAT001-OVC-2025/clinical_summary.txt
```

**Key sections to review:**
- Patient demographics and clinical history
- Molecular findings summary
- Treatment recommendations
- Monitoring strategy
- Quality check results

#### 2C. Complete Review Form

```bash
# Copy template
cp docs/for-hospitals/citl-workflows/CITL_REVIEW_TEMPLATE.md ./results/PAT001-OVC-2025/citl_review_form.md

# Edit in your preferred editor
code ./results/PAT001-OVC-2025/citl_review_form.md
# OR
nano ./results/PAT001-OVC-2025/citl_review_form.md
```

**Complete all required sections:**

**Section 1: HIGH-LEVEL DECISION** ⭐ REQUIRED
- Select: APPROVE / REVISE / REJECT
- Provide 2-3 sentence rationale

**Section 2: PER-FINDING VALIDATION** ⭐ REQUIRED (top 10 findings)
For each finding, mark: CONFIRMED / UNCERTAIN / INCORRECT

**Expected PatientOne Findings to Validate:**
1. TP53 R175H mutation - CONFIRMED (genomics + imaging concordant)
2. PIK3CA E545K activation - CONFIRMED (RNA + protein evidence)
3. BRCA1 germline pathogenic variant - CONFIRMED (clinical history)
4. ABCB1 upregulation (4.3× log2FC) - CONFIRMED (explains platinum resistance)
5. BCL2L1 anti-apoptotic signaling - CONFIRMED (multiomics + spatial)
6. Immune exclusion phenotype - CONFIRMED (spatial + imaging: low CD8 infiltration)
7. Tumor hypoxia (VEGFA upregulated) - CONFIRMED (spatial patterns)
8. TP53+ proliferative cells (Ki67+) - CONFIRMED (imaging quantification)
9. PI3K/AKT pathway activation - CONFIRMED (multiomics integration)
10. MDR1 drug efflux pump expression - CONFIRMED (ABCB1 RNA + protein)

**Section 3: CLINICAL GUIDELINE COMPLIANCE** ⭐ REQUIRED
- NCCN alignment: ALIGNED / PARTIAL / NOT_ALIGNED
- Institutional alignment: ALIGNED / PARTIAL / NOT_ALIGNED
- Document any deviations

**Expected PatientOne Assessment:**
- NCCN: ALIGNED (BRCA1+ HGSOC → PARP inhibitor, PI3K inhibitor trial eligibility)
- Institutional: ALIGNED (all recommendations within formulary, trial available)

**Section 4: QUALITY FLAGS ASSESSMENT**
- Review each quality flag
- Mark: ACCEPTABLE / REQUIRES_ACTION
- Provide comments

**Expected PatientOne Flags:** (if any warnings raised)
- Sample size warning: tumor_necrotic region (35 spots) - ACCEPTABLE (strong effect sizes compensate)

**Section 5: TREATMENT RECOMMENDATIONS REVIEW**
For each recommendation, mark: AGREE / DISAGREE

**Expected PatientOne Recommendations:**
1. PI3K inhibitor (alpelisib) + PARP inhibitor (olaparib) - AGREE
2. Anti-VEGF therapy continuation (bevacizumab) - AGREE (no GI perforation risk)
3. MDR1 reversal agent consideration - AGREE (high ABCB1 expression)
4. Immunotherapy (pembrolizumab) - DISAGREE or conditional (low PD-L1, immune exclusion)

**Section 6: ATTESTATION & SIGNATURE** ⭐ REQUIRED
- Check all attestation boxes
- Provide reviewer information
- Leave signature_hash blank (auto-generated)

**Section 7: REVISION INSTRUCTIONS** (only if REVISE or REJECT)
- List specific issues to address
- Specify re-analysis parameters
- Set resubmission timeline

#### 2D. Convert Review to JSON Format

**Option 1: Manual JSON creation** (for POC, production would have web form)

Create `./results/PAT001-OVC-2025/citl_review_completed.json`:

```json
{
  "patient_id": "PAT001-OVC-2025",
  "report_date": "2026-01-13T14:00:00Z",
  "reviewer": {
    "name": "Dr. Sarah Johnson",
    "email": "sarah.johnson@hospital.org",
    "credentials": "MD, Gynecologic Oncology",
    "role": "oncologist"
  },
  "review_date": "2026-01-13T14:30:00Z",
  "decision": {
    "status": "APPROVE",
    "rationale": "All findings are consistent with clinical presentation and imaging. Molecular results align with observed platinum resistance. Treatment recommendations follow NCCN guidelines and are appropriate for patient's molecular profile."
  },
  "per_finding_validation": [
    {
      "finding_id": "DEG_1",
      "gene": "TP53",
      "validation_status": "CONFIRMED",
      "comments": "TP53 R175H mutation confirmed by genomics and TP53+ cells seen on IHC imaging. High confidence."
    },
    {
      "finding_id": "DEG_2",
      "gene": "PIK3CA",
      "validation_status": "CONFIRMED",
      "comments": "PIK3CA E545K activation consistent with PI3K/AKT pathway analysis across multiomics layers."
    },
    {
      "finding_id": "DEG_3",
      "gene": "BRCA1",
      "validation_status": "CONFIRMED",
      "comments": "BRCA1 germline pathogenic variant documented in clinical history. PARP inhibitor appropriate."
    },
    {
      "finding_id": "DEG_4",
      "gene": "ABCB1",
      "validation_status": "CONFIRMED",
      "comments": "ABCB1 (MDR1) 4.3× upregulation explains platinum resistance through drug efflux mechanism."
    },
    {
      "finding_id": "DEG_5",
      "gene": "BCL2L1",
      "validation_status": "CONFIRMED",
      "comments": "Anti-apoptotic signaling via BCL2L1 consistent across spatial and multiomics data."
    },
    {
      "finding_id": "DEG_6",
      "gene": "CD8A",
      "validation_status": "CONFIRMED",
      "comments": "Low CD8 infiltration (immune exclusion) confirmed by spatial transcriptomics and imaging. Limits immunotherapy efficacy."
    },
    {
      "finding_id": "DEG_7",
      "gene": "VEGFA",
      "validation_status": "CONFIRMED",
      "comments": "VEGFA upregulation indicates hypoxic microenvironment. Supports anti-VEGF therapy continuation."
    },
    {
      "finding_id": "DEG_8",
      "gene": "MKI67",
      "validation_status": "CONFIRMED",
      "comments": "High Ki67 proliferation rate (50%) confirmed by imaging quantification."
    },
    {
      "finding_id": "DEG_9",
      "gene": "AKT1",
      "validation_status": "CONFIRMED",
      "comments": "AKT1 activation (phospho-AKT) confirmed. PI3K/AKT pathway is validated therapeutic target."
    },
    {
      "finding_id": "DEG_10",
      "gene": "MTOR",
      "validation_status": "CONFIRMED",
      "comments": "mTOR pathway activation downstream of PI3K/AKT. Potential mTOR inhibitor combination."
    }
  ],
  "guideline_compliance": {
    "nccn_aligned": "ALIGNED",
    "nccn_deviations": [],
    "institutional_aligned": "ALIGNED",
    "institutional_deviations": []
  },
  "quality_flags_assessment": [],
  "treatment_recommendations_review": [
    {
      "recommendation_id": "REC_1",
      "therapy_name": "PI3K inhibitor (alpelisib) + PARP inhibitor (olaparib)",
      "agreement": "AGREE",
      "comments": "Combination is appropriate given PIK3CA E545K + BRCA1 germline status. Patient meets eligibility for clinical trial NCT12345678."
    },
    {
      "recommendation_id": "REC_2",
      "therapy_name": "Anti-VEGF therapy (bevacizumab) continuation",
      "agreement": "AGREE",
      "comments": "VEGFA upregulation supports continuation. No GI perforation risk factors noted."
    },
    {
      "recommendation_id": "REC_3",
      "therapy_name": "MDR1 reversal consideration",
      "agreement": "AGREE",
      "comments": "High ABCB1 expression warrants MDR1 reversal strategy to improve chemotherapy efficacy."
    }
  ],
  "attestation": {
    "reviewed_all_findings": true,
    "assessed_compliance": true,
    "clinical_judgment": true,
    "medical_record_acknowledgment": true
  },
  "revision_count": 0
}
```

---

## STEP 3: Submit Review (Automated, ~5 seconds)

### Run Review Submission Script

```bash
python servers/mcp-patient-report/scripts/citl_submit_review.py \
  --patient-id PAT001-OVC-2025 \
  --review-file ./results/PAT001-OVC-2025/citl_review_completed.json
```

**What this does:**
1. Validates review against JSON schema (`shared/schemas/citl_review_schema.json`)
2. Generates digital signature (SHA-256 hash)
3. Logs review to Cloud Logging for audit trail
4. Creates signed review record (`*_signed.json`)

### Expected Output

```
📋 CitL Review Submission
======================================================================
Patient ID:     PAT001-OVC-2025
Review File:    ./results/PAT001-OVC-2025/citl_review_completed.json
Schema:         shared/schemas/citl_review_schema.json
======================================================================

📂 Loading review data...
📋 Validating review against JSON schema...
✅ Schema validation passed
🔐 Generating digital signature...
   Signature: abc123def456789...
📝 Logging to audit trail...
✅ Logged to Cloud Logging: citl-reviews

======================================================================
Review Submission Summary
======================================================================
Patient ID:       PAT001-OVC-2025
Decision:         APPROVE
Reviewer:         Dr. Sarah Johnson (MD, Gynecologic Oncology)
Review Date:      2026-01-13T14:30:00Z
Signature Hash:   abc123def456789012345678901234567890...
Signed Review:    ./results/PAT001-OVC-2025/citl_review_completed_signed.json

Findings Validated: 10 total
  - Confirmed:  10
  - Uncertain:  0
  - Incorrect:  0

Guideline Compliance:
  - NCCN:          ALIGNED
  - Institutional: ALIGNED
======================================================================

✅ Review submitted successfully!

📍 Next Step: Finalize the approved report
   python servers/mcp-patient-report/scripts/finalize_patient_report.py --patient-id PAT001-OVC-2025
```

### Verification

Check that audit trail was logged:

```bash
# Local fallback (if Cloud Logging not available)
cat citl_review_audit_trail.jsonl | tail -1 | python -m json.tool

# Verify signed review was created
ls -lh ./results/PAT001-OVC-2025/*_signed.json
```

---

## STEP 4A: Finalize Approved Report (~10 seconds)

**Run this step ONLY if review status is APPROVE.**

### Generate Final Clinical Report

```bash
python servers/mcp-patient-report/scripts/finalize_patient_report.py \
  --patient-id PAT001-OVC-2025 \
  --output-dir ./results
```

**What this does:**
1. Loads draft report and signed review
2. Verifies approval status (fails if REVISE or REJECT)
3. Generates final approved report with attestation
4. Marks report as "CLINICALLY_APPROVED"

### Expected Output

```
📋 Report Finalization
======================================================================
Patient ID:         PAT001-OVC-2025
Output Directory:   ./results/PAT001-OVC-2025
======================================================================

📂 Loading draft report...
   Status: pending_review
📂 Loading signed review: citl_review_completed_signed.json
   Reviewer: Dr. Sarah Johnson
   Decision: APPROVE

✅ Review status: APPROVED
   Reviewer: Dr. Sarah Johnson

📝 Generating final approved report...
💾 Saving final report...

======================================================================
Final Report Summary
======================================================================
Patient ID:           PAT001-OVC-2025
Status:               clinically_approved
Reviewer:             Dr. Sarah Johnson (MD, Gynecologic Oncology)
Approval Date:        2026-01-13T15:00:00Z
Review Decision:      APPROVE
Draft Version:        1.0
Final Version:        1.0-approved

Guideline Compliance:
  NCCN Aligned:       ALIGNED
  Institutional:      ALIGNED

Findings Validation:
  Total Validated:    10
  - Confirmed:        10
  - Uncertain:        0
  - Incorrect:        0

Quality Checks:
  All Passed:         True

Audit Trail:
  Review ID:          abc123def456789012345678901234567890...
  Approval Timestamp: 2026-01-13T15:00:00Z

Final Report Saved: ./results/PAT001-OVC-2025/final_report_approved.json
======================================================================

✅ Report finalization complete!

📍 Next Steps:
   1. Review final report: ./results/PAT001-OVC-2025/final_report_approved.json
   2. Present findings at tumor board
   3. Document clinical decision in patient chart
   4. Archive audit trail (10-year retention)
```

### Verification

```bash
# View final report
cat ./results/PAT001-OVC-2025/final_report_approved.json | python -m json.tool | less

# Verify status
grep '"status"' ./results/PAT001-OVC-2025/final_report_approved.json
# Should show: "status": "clinically_approved"

# Verify attestation is included
grep -A 5 '"clinical_attestation"' ./results/PAT001-OVC-2025/final_report_approved.json
```

---

## STEP 4B: Handle Revisions (If review status = REVISE)

**Run this workflow ONLY if clinician requested revisions.**

### Review Revision Instructions

```bash
# View revision instructions from signed review
cat ./results/PAT001-OVC-2025/citl_review_completed_signed.json | python -m json.tool | grep -A 20 '"revision_instructions"'
```

**Example revision instructions:**
- Exclude tumor_necrotic region (insufficient sample size)
- Increase FDR threshold from 0.05 to 0.01
- Validate TP53 mutation with orthogonal sequencing

### Re-run Analysis with Adjusted Parameters

```bash
# Example: Re-run with stricter FDR and exclude regions
python servers/mcp-patient-report/scripts/generate_patient_report.py \
  --patient-id PAT001-OVC-2025 \
  --output-dir ./results \
  --generate-draft \
  --fdr-threshold 0.01 \
  --min-spots-per-region 50 \
  --exclude-regions tumor_necrotic,stroma_artifact
```

### Resubmit for Review

After addressing issues:

1. New draft report generated (version 2)
2. Return to STEP 2 (Clinician Review)
3. Complete new review with `revision_count: 1`
4. Submit review again (STEP 3)

---

## STEP 4C: Handle Rejection (If review status = REJECT)

**Run this workflow ONLY if clinician rejected the report.**

### Escalation Procedure

1. **Review rejection rationale:**
   ```bash
   cat ./results/PAT001-OVC-2025/citl_review_completed_signed.json | python -m json.tool | grep -A 5 '"rationale"'
   ```

2. **Document critical errors** from review form Section 7

3. **Alert team:**
   - Bioinformatics team lead
   - Principal Investigator
   - Clinical research coordinator

4. **Schedule review meeting** to determine:
   - Root cause of errors
   - Whether data re-collection needed
   - Alternative analysis approach
   - Expert consultation requirements

5. **Create corrective action plan**

6. **Timeline:** Major re-analysis may require 1-2 weeks

---

## Expected Results for PatientOne (APPROVE Scenario)

### Quality Checks: ✅ ALL PASS

- **Sample sizes:** tumor_core (350 spots), stroma (400 spots) - PASS
- **FDR thresholds:** 17 DEGs with FDR < 0.05 - PASS
- **Data completeness:** 99.2% - PASS
- **Cross-modal consistency:** TP53 mutation (genomics) + TP53+ cells (imaging) - PASS

### Expected Clinician Decision: APPROVE

**Rationale:** "All findings are consistent with clinical presentation and imaging. Molecular results align with observed platinum resistance. Treatment recommendations follow NCCN guidelines and are appropriate for patient's molecular profile."

### Key Findings Validated: 10/10 CONFIRMED

1. ✅ TP53 R175H mutation
2. ✅ PIK3CA E545K activation
3. ✅ BRCA1 germline pathogenic
4. ✅ ABCB1 upregulation (platinum resistance)
5. ✅ BCL2L1 anti-apoptotic signaling
6. ✅ Immune exclusion (low CD8)
7. ✅ Tumor hypoxia (VEGFA)
8. ✅ High Ki67 proliferation
9. ✅ PI3K/AKT pathway activation
10. ✅ MDR1 drug efflux

### Guideline Compliance: ALIGNED

- **NCCN:** ALIGNED (BRCA1+ HGSOC guidelines followed)
- **Institutional:** ALIGNED (all drugs in formulary, trial available)

### Expected Review Time: 25 minutes

- Draft review: 10 minutes
- Per-finding validation: 8 minutes
- Guideline assessment: 5 minutes
- Form completion: 2 minutes

### Expected Outcome

- ✅ Status: APPROVED
- ✅ Final report generated
- ✅ Audit trail complete with digital signature
- ✅ Ready for tumor board presentation

---

## Validation Checkpoints

✅ **Automated quality gates** run before human review (6 checks)  
✅ **Structured review** captured all 4 required review scopes:  
   - High-level decision (APPROVE)  
   - Per-finding validation (10 findings confirmed)  
   - Guideline compliance (NCCN + institutional aligned)  
   - Digital attestation with signature  

✅ **Audit trail** with immutable timestamp and signature hash  
✅ **10-year retention** compliance (logged to Cloud Logging)  
✅ **Final approved report** ready for clinical use  
✅ **Workflow integration** seamlessly extends TEST_1-5  

---

## Integration with Existing Workflow

### Previous Workflow (TEST_1-5):
```
TEST_1 (Clinical) → TEST_2 (Multiomics) → TEST_3 (Spatial) →
TEST_4 (Imaging) → TEST_5 (Integration) → Manual Review
```

### New Workflow with CitL (TEST_1-6):
```
TEST_1 (Clinical) → TEST_2 (Multiomics) → TEST_3 (Spatial) →
TEST_4 (Imaging) → TEST_5 (Integration) →
**TEST_6 (CitL Review)** → APPROVED CLINICAL REPORT
```

### Time Comparison

**Before CitL (informal review):**
- TEST_1-5: 10-15 minutes (LLM analysis)
- Manual review: Unstructured, no audit trail, variable quality
- **Total: 10-15 minutes** (but clinically insufficient)

**After CitL (formal review):**
- TEST_1-5: 10-15 minutes (LLM analysis)
- TEST_6 automated QC: 30 seconds
- TEST_6 clinician review: 20-30 minutes (structured, auditable)
- **Total: 30-45 minutes** (production-ready, clinically valid)

### Value Added by CitL

1. **Clinical accountability:** Oncologist validates AI findings  
2. **HIPAA compliance:** 10-year audit trail with signatures  
3. **Guideline alignment:** Explicit NCCN + institutional check  
4. **Quality assurance:** Automated QC gates before human review  
5. **Workflow transparency:** Clear approve/revise/reject process  
6. **AI as co-pilot:** Human expert in the loop, not autonomous AI  

---

## Troubleshooting

### Issue: Schema validation fails

**Solution:**
```bash
# Verify JSON syntax
python -m json.tool ./results/PAT001-OVC-2025/citl_review_completed.json

# Check required fields
grep -E '"patient_id"|"reviewer"|"decision"|"attestation"' ./results/PAT001-OVC-2025/citl_review_completed.json
```

### Issue: Cloud Logging not available

**Solution:** Script automatically falls back to local logging
```bash
# Check local audit trail
cat citl_review_audit_trail.jsonl
```

### Issue: Cannot finalize (status not APPROVE)

**Solution:** Check review decision
```bash
# View decision status
cat ./results/PAT001-OVC-2025/citl_review_completed_signed.json | python -m json.tool | grep -A 3 '"decision"'

# If REVISE: See STEP 4B
# If REJECT: See STEP 4C
```

### Issue: Draft report not found

**Solution:** Run generate_patient_report.py first
```bash
# Generate draft report
python servers/mcp-patient-report/scripts/generate_patient_report.py --patient-id PAT001-OVC-2025 --output-dir ./results --generate-draft
```

---

## Success Criteria

✅ Draft report generated with quality checks  
✅ Clinician completed structured review (6 sections)  
✅ Review validated against JSON schema  
✅ Digital signature generated (SHA-256)  
✅ Audit trail logged (Cloud Logging or local)  
✅ Signed review created with immutable timestamp  
✅ Final approved report generated  
✅ Report status: "clinically_approved"  
✅ Audit trail complete for 10-year retention  

---

## Next Steps After TEST_6

1. **Present at tumor board** with final approved report  
2. **Document clinical decision** in patient EHR  
3. **Archive complete audit trail** (draft → review → approval)  
4. **Track outcomes** for continuous learning  
5. **Refine workflow** based on clinician feedback  

---

**Test Completed:** TEST_6_CITL_REVIEW  
**Status:** Clinician-in-the-Loop validation implemented  
**Outcome:** AI as co-pilot, human expert validates before clinical use  
**Compliance:** HIPAA-compliant with 10-year audit trail  
