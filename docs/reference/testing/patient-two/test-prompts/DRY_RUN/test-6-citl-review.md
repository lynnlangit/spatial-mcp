TEST 6: Clinician-in-the-Loop (CitL) Review & Approval
========================================================

Patient ID: PAT002-BC-2026
Cancer Type: Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma, BRCA2 Germline Mutation

**PREREQUISITE:** Complete TEST_5_INTEGRATION before running this test

## Overview

This test implements the formal Clinician-in-the-Loop (CitL) validation workflow where an oncologist reviews and validates the "stitched results" from TEST_1-5 before they are finalized into a clinical report. This demonstrates AI as a "co-pilot" rather than an autonomous decision-maker in high-stakes oncology care.

**Workflow:** Draft Report > Automated QC > Clinician Review > Approve/Revise/Reject > Final Report

**Time Estimate:** 30-45 minutes total
- Automated steps: ~40 seconds
- Manual clinician review: 20-30 minutes

---

## STEP 1: Generate Draft Clinical Report (Automated, ~30 seconds)

### Run the Enhanced Report Generator

```bash
cd /Users/lynnlangit/Documents/GitHub/spatial-mcp

python servers/mcp-patient-report/scripts/generate_patient_report.py \
  --patient-id PAT002-BC-2026 \
  --output-dir ./results \
  --generate-draft
```

**What this does:**
1. Consolidates findings from TEST_1 (clinical), TEST_2 (multiomics), TEST_3 (spatial), TEST_4 (imaging), TEST_5 (integration)
2. Runs automated quality checks
3. Generates structured JSON output for review workflow
4. Flags issues requiring clinician attention

### Quality Gate Validation

Verify all quality checks passed (or flags documented):

- [ ] **Sample sizes adequate:** tumor_core >= 30 spots, stroma >= 30 spots
- [ ] **FDR thresholds met:** All significant DEGs have FDR < 0.05
- [ ] **Data completeness:** >95% of expression values present
- [ ] **Cross-modal consistency:** ER status (genomics) matches ER+ cells (imaging)

---

## STEP 2: Clinician Review (Manual, 20-30 minutes)

### Reviewer Role

**Primary Reviewer:** Dr. Maria Chen
**Credentials:** MD, Breast Surgical Oncology
**Role:** Breast oncologist specializing in hereditary breast cancer

### Review Process

#### 2A. Open Draft Report

```bash
cat ./results/PAT002-BC-2026/clinical_summary.txt
```

#### 2B. Complete Review Form

```bash
cp docs/for-hospitals/citl-workflows/CITL_REVIEW_TEMPLATE.md ./results/PAT002-BC-2026/citl_review_form.md
```

**Complete all required sections:**

**Section 1: HIGH-LEVEL DECISION** (REQUIRED)
- Select: APPROVE / REVISE / REJECT
- Provide 2-3 sentence rationale

**Section 2: PER-FINDING VALIDATION** (REQUIRED, top 10 findings)

**Expected PatientTwo Findings to Validate:**
1. BRCA2 c.5946delT germline mutation - CONFIRMED (clinical history + genomics)
2. PIK3CA H1047R activating mutation - CONFIRMED (somatic variant calling)
3. ER+ strong expression (85-95%) - CONFIRMED (imaging + spatial concordant)
4. PR+ expression (70%) - CONFIRMED (clinical + spatial)
5. HER2-negative status - CONFIRMED (imaging IF score 0-1+)
6. Low proliferation (Ki67 10-20%) - CONFIRMED (imaging + spatial)
7. GATA3 frameshift mutation - CONFIRMED (luminal lineage marker, common in ER+ BC)
8. MYC/CCND1 amplification - CONFIRMED (CNV analysis)
9. CDKN2A deletion - CONFIRMED (CNV analysis)
10. Moderate CD8 infiltration (15-30/mm2) - CONFIRMED (imaging + spatial, warm TME)

**Section 3: CLINICAL GUIDELINE COMPLIANCE** (REQUIRED)
- NCCN alignment: ALIGNED / PARTIAL / NOT_ALIGNED
- Institutional alignment: ALIGNED / PARTIAL / NOT_ALIGNED

**Expected PatientTwo Assessment:**
- NCCN: ALIGNED (BRCA2+ ER+ BC: tamoxifen adjuvant, PARP eligibility if recurrence, BRCA carrier surveillance)
- Institutional: ALIGNED (tamoxifen in formulary, genetic counselling active, MRI surveillance per protocol)

**Section 4: TREATMENT RECOMMENDATIONS REVIEW**

**Expected PatientTwo Recommendations:**
1. Continue tamoxifen 20mg daily (adjuvant endocrine therapy) - AGREE
2. BRCA2 carrier surveillance (annual breast MRI + mammography) - AGREE
3. Consider ovarian function suppression if premenopausal high-risk criteria met - AGREE
4. Olaparib eligibility if disease recurrence (OlympiAD/OlympiA evidence) - AGREE
5. CDK4/6 inhibitor + AI if endocrine-resistant recurrence - AGREE
6. Alpelisib consideration given PIK3CA H1047R - AGREE (if progression on CDK4/6i + AI)

**Section 5: ATTESTATION & SIGNATURE** (REQUIRED)
- Check all attestation boxes
- Provide reviewer information

---

## STEP 3: Submit Review (Automated, ~5 seconds)

```bash
python servers/mcp-patient-report/scripts/citl_submit_review.py \
  --patient-id PAT002-BC-2026 \
  --review-file ./results/PAT002-BC-2026/citl_review_completed.json
```

### Expected Output

```
Patient ID:       PAT002-BC-2026
Decision:         APPROVE
Reviewer:         Dr. Maria Chen (MD, Breast Surgical Oncology)
Findings Validated: 10 total
  - Confirmed:  10
  - Uncertain:  0
  - Incorrect:  0

Guideline Compliance:
  - NCCN:          ALIGNED
  - Institutional: ALIGNED

Review submitted successfully!
```

---

## STEP 4A: Finalize Approved Report (~10 seconds)

**Run this step ONLY if review status is APPROVE.**

```bash
python servers/mcp-patient-report/scripts/finalize_patient_report.py \
  --patient-id PAT002-BC-2026 \
  --output-dir ./results
```

---

## Expected Results for PatientTwo (APPROVE Scenario)

### Quality Checks: ALL PASS

- **Sample sizes:** tumor_core (200+ spots), stroma (100+ spots) - PASS
- **FDR thresholds:** DEGs with FDR < 0.05 - PASS
- **Data completeness:** >95% - PASS
- **Cross-modal consistency:** ER expression (spatial) + ER positivity (imaging) concordant - PASS

### Expected Clinician Decision: APPROVE

**Rationale:** "All findings are consistent with the clinical presentation of early-stage ER+/PR+/HER2- breast cancer with BRCA2 germline mutation. Molecular profile confirms Luminal A biology. Treatment recommendations align with NCCN guidelines for BRCA-mutant ER+ breast cancer. Surveillance plan appropriate for hereditary breast cancer."

### Key Findings Validated: 10/10 CONFIRMED

1. BRCA2 c.5946delT germline mutation
2. PIK3CA H1047R activating mutation
3. ER+ strong expression (85-95%)
4. PR+ expression (70%)
5. HER2-negative status
6. Low proliferation (Ki67 10-20%)
7. GATA3 frameshift (luminal marker)
8. MYC/CCND1 amplification
9. CDKN2A deletion
10. Moderate CD8 infiltration (warm TME)

### Guideline Compliance: ALIGNED

- **NCCN:** ALIGNED (BRCA2+ ER+ breast cancer guidelines followed)
- **Institutional:** ALIGNED (tamoxifen in formulary, genetic counselling program active)

---

## Validation Checkpoints

- Automated quality gates run before human review
- Structured review captured all required scopes:
  - High-level decision (APPROVE)
  - Per-finding validation (10 findings confirmed)
  - Guideline compliance (NCCN + institutional aligned)
  - Digital attestation with signature
- Audit trail with immutable timestamp and signature hash
- Final approved report ready for clinical use
- Workflow integration seamlessly extends TEST_1-5

---

## Key Differences from PatientOne CitL Review

| Aspect | PatientOne (Ovarian) | PatientTwo (Breast) |
|--------|---------------------|-------------------|
| Reviewer specialty | Gynecologic Oncology | Breast Surgical Oncology |
| Key validated finding | TP53 R175H + platinum resistance | BRCA2 germline + ER+ expression |
| Treatment focus | Targeted therapy for resistant disease | Adjuvant endocrine + surveillance |
| Guideline framework | NCCN Ovarian Cancer | NCCN Breast Cancer |
| Disease status | Active progression | Disease-free surveillance |
| Primary concern | Resistance mechanisms | Recurrence prevention |

---

**Test Completed:** TEST_6_CITL_REVIEW
**Status:** Clinician-in-the-Loop validation implemented
**Outcome:** AI as co-pilot, human expert validates before clinical use
**Compliance:** HIPAA-compliant with audit trail
