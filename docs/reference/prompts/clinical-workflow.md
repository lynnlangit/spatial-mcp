# Clinical Workflow Prompts

**Audience:** Oncologists, Clinical Researchers, Bioinformaticians
**Purpose:** Complete patient analysis workflows for precision oncology
**Time per prompt:** 5-45 minutes
**Expected output:** Clinical reports, treatment recommendations, scientific analysis
**Patient data:** [PatientOne Profile](../shared/patientone-profile.md) (PAT001-OVC-2025)

> **Data Mode Note:** These prompts reference **mcp-mockepic** (synthetic EHR) and **mcp-mocktcga** (synthetic TCGA) — both are always synthetic regardless of DRY_RUN setting. For real data: use **mcp-epic** for FHIR EHR access (local, HIPAA-compliant) and the **cBioPortal** external connector for real TCGA cohort comparisons. See [Connect External MCP Servers](../../for-researchers/CONNECT_EXTERNAL_MCP.md) for setup.

---

## Complete PatientOne Workflow (6 Prompts)

These prompts follow the TEST_1 through TEST_6 workflow for comprehensive multi-modal analysis. **Copy-paste prompt text** is maintained in the [DRY_RUN test prompts](../testing/patient-one/test-prompts/DRY_RUN/) — linked below for each prompt. Summaries and expected outputs are kept here for quick reference.

> **Sample Data Location:** PatientOne data is stored in GCS at `gs://sample-inputs-patientone/patient-data/PAT001-OVC-2025/`. Sub-directories include `multiomics/`, `spatial/`, and `imaging/`. MCP servers on Cloud Run can access these GCS URIs directly.

### Prompt 1: Clinical Data and Genomic Profiling

**Time:** 5-10 minutes | **Complexity:** Medium | **Output:** Clinical summary + genomic profile

Retrieves patient demographics, BRCA status, and CA-125 trends from mcp-mockepic, then parses somatic variants (TP53, PIK3CA, PTEN) and compares to TCGA-OV cohort using mcp-fgbio and mcp-mocktcga.

**Copy-paste prompt:** [Test 1 — Clinical & Genomic](../testing/patient-one/test-prompts/DRY_RUN/test-1-clinical-genomic.md)

**Expected Output:**
- Patient: Sarah Anderson, 58yo, BRCA1 germline mutation
- CA-125: 1456 → 22 → 389 U/mL (platinum resistance confirmed)
- Mutations: TP53 R175H, PIK3CA E545K, PTEN LOH
- TCGA subtype: C1/C2 (poor prognosis)
- Key insight: PI3K pathway activated → potential PI3K inhibitor target

---

### Prompt 2: Multi-Omics Resistance Mechanisms

**Time:** 15-25 minutes | **Complexity:** High | **Output:** Resistance pathway analysis

Runs the complete multi-omics pipeline via mcp-multiomics: data preprocessing (batch correction, imputation), integration of RNA-seq/proteomics/phosphoproteomics from 14 PDX samples, Stouffer's meta-analysis for resistance gene identification, and upstream regulator prediction for therapeutic targets.

**Copy-paste prompt:** [Test 2 — Multi-Omics Enhanced](../testing/patient-one/test-prompts/DRY_RUN/test-2-multiomics-enhanced.md)

**Expected Output:**
- Batch effects REDUCED: PC1-batch 0.82 → 0.15
- Resistance genes: PIK3CA (+2.3), AKT1 (+2.1), MTOR (+1.9), ABCB1 (+2.5) all q<0.001
- Tumor suppressors: PTEN (-2.1), TP53 (-1.5) both q<0.005
- Upstream regulators: AKT1/MTOR/PI3K activated (Z>2.5)
- Drug targets: Alpelisib (PI3K inhibitor), Capivasertib (AKT inhibitor)

---

### Prompt 3: Spatial Tumor Microenvironment Analysis

**Time:** 10-15 minutes | **Complexity:** Medium | **Output:** Spatial analysis report

Analyzes 10x Visium spatial transcriptomics data (900 spots, 6 tissue regions) via mcp-spatialtools. Assesses spatial structure, expression of 8 key genes (proliferation, resistance, immune markers) across regions, and generates 4 visualizations including spatial heatmaps and autocorrelation plots.

**Copy-paste prompt:** [Test 3 — Spatial Transcriptomics](../testing/patient-one/test-prompts/DRY_RUN/test-3-spatial.md)

**Expected Output:**
- Structure: 900 spots (tumor_core: 69, tumor_proliferative: 124, stroma_immune: 212, etc.)
- Proliferation: HIGH in tumor_proliferative (MKI67/PCNA)
- Resistance: Concentrated in tumor regions (heterogeneous)
- Immune cells: EXCLUDED from tumor (located in stroma_immune)
- TME classification: "COLD" tumor (poor immunotherapy candidate)

---

### Prompt 4: Histopathology and Immunofluorescence

**Time:** 20-40 minutes | **Complexity:** High | **Output:** Imaging analysis report

Processes 4 microscopy images (H&E, CD8 IF, Ki67 IF, multiplex TP53/Ki67/DAPI) through the imaging pipeline: mcp-openimagedata for tissue-level analysis, mcp-deepcell for cell segmentation, and mcp-cell-classify for phenotype classification. Generates 5 visualization overlays.

**Copy-paste prompt:** [Test 4 — Imaging](../testing/patient-one/test-prompts/DRY_RUN/test-4-imaging.md)

**Expected Output:**
- H&E: 70-80% cellularity, 15-20% necrosis, HGSOC morphology confirmed
- CD8: LOW infiltration (5-15 cells/mm²), peripheral clustering, COLD phenotype
- Ki67: HIGH index (45-55%), heterogeneous distribution
- Multiplex: 65-75% TP53+, 45-55% Ki67+, 40-50% double-positive
- Interpretation: Aggressive, immune-excluded tumor

---

### Prompt 5: Integrated Multi-Modal Analysis

**Time:** 5-10 minutes | **Complexity:** Medium | **Output:** Clinical report + recommendations

Synthesizes findings from Tests 1-4: ranks resistance mechanisms by cross-modal evidence, builds a multi-modal consistency table (TP53, PI3K, proliferation, immune exclusion), generates top-3 treatment recommendations with evidence levels, and creates an integrated 4-panel visualization.

**Copy-paste prompt:** [Test 5 — Integration](../testing/patient-one/test-prompts/DRY_RUN/test-5-integration.md)

**Expected Output:**
- Top mechanisms: (1) PI3K/AKT activation (4 modalities), (2) Drug efflux/ABCB1 (2 modalities), (3) Immune exclusion (2 modalities)
- Consistency: TP53 (genomics+imaging ✓), PI3K (genomics+multiomics+spatial ✓), Proliferation (multiomics+spatial+imaging ✓)
- Recommendations: (1) PI3K inhibitor+PARP inhibitor (high evidence), (2) MDR1 reversal (medium), (3) Checkpoint inhibitor (low - cold tumor)
- Monitoring: CA-125, circulating tumor DNA, Ki67 index

---

### Prompt 6: Clinician-in-the-Loop Validation

**Time:** 30-45 minutes (includes 20-30 min manual review) | **Complexity:** High | **Output:** Approved clinical report

Implements the full clinician-in-the-loop (CitL) workflow via mcp-patient-report: generates a draft report consolidating Tests 1-5, runs automated quality checks, presents a structured review form (10 findings, guideline compliance, treatment validation), captures digital attestation, and produces a signed final clinical report with audit trail.

**Copy-paste prompt:** [Test 6 — CitL Review](../testing/patient-one/test-prompts/DRY_RUN/test-6-citl-review.md)

**Expected Output:**
- Quality checks: ALL PASS (sample sizes OK, FDR<0.05, completeness 99%)
- Decision: APPROVE (expected for PatientOne)
- Findings validated: 10/10 CONFIRMED
- Guideline compliance: NCCN ALIGNED, Institutional ALIGNED
- Treatments: 3 AGREE, 1 conditional
- Final report: CLINICALLY_APPROVED status
- Audit trail: Complete with 10-year retention

---

## Stage 5: Report Synthesis (PatientReportData v2 Schema)

**IMPORTANT — Always call `get_report_template_schema` first before constructing
report JSON.** The `PatientReportData` Pydantic schema (mcp-patient-report v2)
requires specific nested structures (`PatientInfo`, `DiagnosisSummary`,
`TreatmentOption`, `MonitoringPlan`) that differ from the flat dicts used in
v1. Callers that hand-roll JSON from pre-v2 field names will hit 20+ "Field
required" validation errors.

### Required fields that changed in v2

- **`patient_info`**: `name`, `age`, `sex` (all required), plus `patient_id`
  and `diagnosis`
- **`diagnosis_summary`**: `cancer_type` (required — separate from `subtype`),
  `stage`, `plain_language_description`, `key_positive_factors[]` and
  `key_challenges[]` (both required arrays, not optional)
- **`treatment_options[].evidence_level`** must be an `EvidenceLevel` enum
  value — one of:
  `FDA_APPROVED`, `NCCN_1`, `NCCN_2A`, `NCCN_2B`,
  `ESCAT_I`, `ESCAT_II`, `ESCAT_III`, `ESCAT_IV`, `ESCAT_V`,
  `CLINICAL_TRIAL`
- **`treatment_options[].plain_language_description`** (required — was
  `plain_language` in v1; the rename is the single most common source of
  validation errors)
- **`monitoring_plan.schedule[]`** must be a list of `MonitoringScheduleItem`
  objects with `test_name`, `frequency`, `purpose` — NOT bare strings

### Workflow

1. **Call `get_report_template_schema`** → read `required_sections` and the
   `example` field. Do not guess field names.
2. **Construct JSON** matching the schema exactly. When in doubt, diff your
   payload against the canonical fixture.
3. **Call `validate_report_data`** → confirm the response includes
   `valid=true` before proceeding. Fix any `errors[]` entries before
   generating.
4. **Call `generate_patient_report`** with the validated JSON → expect
   `{"status": "success", "is_draft": true}`.
5. **Route the draft through Prompt 6 (Clinician-in-the-Loop Validation)**
   above to capture attestation and produce the final `CLINICALLY_APPROVED`
   report.

### Reference fixture

A complete valid `PatientReportData` example lives at:

```
servers/mcp-patient-report/tests/fixtures/pat001_report_data.json
```

Use this as a template for hand-constructed payloads, and as a regression
anchor when the schema evolves.

---

## Additional Clinical Use Cases (9 Prompts)

### Prompt 7: BRCA1/2 Testing and PARP Inhibitor Eligibility

**Time:** 5 minutes | **Complexity:** Low | **Output:** BRCA status + treatment eligibility

```
For patient [ID] with ovarian cancer:

1. Check BRCA1/2 germline mutation status (mcp-mockepic clinical history)
2. Check for somatic BRCA1/2 mutations (mcp-fgbio VCF analysis)
3. Assess homologous recombination deficiency (HRD) score
4. Determine PARP inhibitor eligibility:
   - BRCA1/2 germline: First-line maintenance (Category 1)
   - BRCA1/2 somatic: First-line maintenance (Category 1)
   - HRD+/BRCA-: Consider maintenance (Category 2A)
   - HRD-/BRCA-: Not recommended
5. List approved PARP inhibitors: Olaparib, Niraparib, Rucaparib
6. Provide NCCN guideline reference

Output: BRCA status, HRD score, PARP inhibitor eligibility, specific drug recommendations
```

---

### Prompt 8: Bevacizumab Continuation Assessment

**Time:** 5 minutes | **Complexity:** Low | **Output:** Anti-VEGF recommendation

```
For patient [ID] currently on bevacizumab:

1. Assess VEGFA expression (mcp-spatialtools spatial analysis)
2. Check for contraindications:
   - History of bowel perforation/fistula?
   - Recent surgery (<28 days)?
   - Uncontrolled hypertension?
   - Proteinuria (>2g/24hr)?
3. Evaluate response:
   - CA-125 trend (decreasing?)
   - Imaging response (RECIST)?
4. Recommendation:
   - Continue if VEGFA high + no contraindications + responding
   - Discontinue if progressing or contraindications present
5. Provide NCCN guideline reference

Output: VEGFA level, contraindications check, response status, continue/discontinue recommendation
```

---

### Prompt 9: Immunotherapy Eligibility (PD-L1, TMB, MSI)

**Time:** 10 minutes | **Complexity:** Medium | **Output:** Immunotherapy assessment

```
For patient [ID] with ovarian cancer:

1. **PD-L1 Assessment:**
   - Check PD-L1 expression (mcp-openimagedata IHC image or mcp-spatialtools)
   - Tumor proportion score (TPS): <1%, 1-49%, ≥50%

2. **Tumor Mutational Burden (TMB):**
   - Calculate from VCF (mcp-fgbio)
   - TMB-H threshold: ≥10 mutations/Mb

3. **Microsatellite Instability (MSI):**
   - Check MSI status (mcp-fgbio)
   - MSI-H or dMMR?

4. **Immune Infiltration:**
   - Quantify CD8+ T cells (mcp-deepcell)
   - Tumor microenvironment: Hot/Warm/Cold?

5. **Recommendation:**
   - Pembrolizumab if: PD-L1 CPS≥10 OR TMB-H OR MSI-H
   - Dostarlimab if: dMMR/MSI-H
   - NOT recommended if: PD-L1 negative + TMB low + MSS + cold TME

Output: PD-L1 score, TMB value, MSI status, CD8 count, immune phenotype, checkpoint inhibitor recommendation
```

---

### Prompt 10: Platinum Re-Challenge vs Alternative Chemotherapy

**Time:** 5-10 minutes | **Complexity:** Medium | **Output:** Chemotherapy recommendation

```
For patient [ID] with platinum-resistant ovarian cancer:

1. **Define Platinum Resistance:**
   - Progression-free interval: <6 months = resistant, 6-12 months = partially sensitive, >12 months = sensitive
   - Calculate PFI from clinical data (mcp-mockepic)

2. **Assess Resistance Mechanisms:**
   - ABCB1/MDR1 expression (mcp-multiomics or mcp-spatialtools)
   - Anti-apoptotic signaling (BCL2 family)
   - DNA repair pathway activation

3. **Treatment Options:**
   - If resistant (<6 months): Non-platinum agents (paclitaxel, pegylated liposomal doxorubicin, topotecan, gemcitabine)
   - If partially sensitive (6-12 months): Consider platinum re-challenge or non-platinum
   - If sensitive (>12 months): Platinum re-challenge recommended

4. **Combination Strategies:**
   - PARP inhibitor + chemotherapy (if BRCA+)
   - Bevacizumab + chemotherapy
   - PI3K inhibitor + chemotherapy (if PIK3CA mutant)

Output: PFI, resistance status, resistance mechanisms, recommended chemotherapy regimen
```

---

### Prompt 11: Clinical Trial Matching

**Time:** 10 minutes | **Complexity:** Medium | **Output:** Trial recommendations

```
For patient [ID] with Stage IV platinum-resistant HGSOC:

**Patient Molecular Profile:**
- BRCA1 germline mutation
- TP53 R175H somatic mutation
- PI3K/AKT pathway activation
- Immune exclusion phenotype

**Search Clinical Trials:**
1. **PI3K/AKT Inhibitor Trials:**
   - Alpelisib + Olaparib (NCT03740165 or similar)
   - Capivasertib + Olaparib
   - Eligibility: PIK3CA mutation or pathway activation + BRCA1/2 mutation

2. **PARP Inhibitor Trials:**
   - Novel PARP inhibitors
   - PARP + immune checkpoint combinations
   - Eligibility: BRCA1/2 or HRD+

3. **Immunotherapy Combination Trials:**
   - Checkpoint inhibitor + VEGF inhibitor
   - Checkpoint inhibitor + PARP inhibitor
   - Eligibility: Usually allows cold tumors if combination

4. **Novel Targeted Therapy:**
   - ATR inhibitors
   - WEE1 inhibitors
   - Eligibility: TP53 mutant

Provide:
- Top 3 matching trials with NCT numbers
- Eligibility criteria match assessment
- Trial phase and location
- Contact information
```

---

### Prompt 12: Circulating Tumor DNA (ctDNA) Monitoring

**Time:** 5 minutes | **Complexity:** Low | **Output:** ctDNA monitoring plan

```
For patient [ID] starting new treatment:

1. **Baseline ctDNA Panel:**
   - Track mutations found in tumor: TP53, PIK3CA, BRCA1, PTEN
   - Establish baseline ctDNA level (copies/mL)

2. **Monitoring Schedule:**
   - Cycle 2 (week 6): First on-treatment assessment
   - Cycle 4 (week 12): Confirm molecular response
   - Every 3 months during maintenance
   - At progression or symptoms

3. **Interpretation:**
   - Decreasing ctDNA: Molecular response (positive prognostic)
   - Stable ctDNA: Stable disease
   - Increasing ctDNA: Molecular progression (may precede imaging by 2-4 months)

4. **Action Plan:**
   - If ctDNA rises: Consider imaging, biopsy for resistance mechanisms
   - If new mutations appear: Update treatment plan

Output: Mutations to track, monitoring schedule, interpretation guide, action thresholds
```

---

### Prompt 13: Comprehensive Molecular Tumor Board Presentation

**Time:** 15 minutes | **Complexity:** High | **Output:** Tumor board presentation

```
Prepare molecular tumor board presentation for patient [ID]:

**Slide 1: Case Summary**
- Patient demographics
- Cancer type, stage, prior treatments
- Current status (progression, response, stable)

**Slide 2: Clinical Timeline**
- Diagnosis date
- Treatment history with responses
- CA-125 trajectory graph
- Current problem (resistance, progression)

**Slide 3: Genomic Landscape**
- Germline mutations (BRCA1/2, Lynch)
- Somatic mutations (TP53, PIK3CA, etc.)
- Copy number alterations
- Comparison to TCGA cohort

**Slide 4: Multi-Omics Resistance Profile**
- Activated pathways (PI3K/AKT, WNT, etc.)
- Drug resistance genes (ABCB1, BCL2L1)
- Upstream regulator prediction
- Pathway visualization

**Slide 5: Spatial Tumor Microenvironment**
- Spatial heatmap showing gene expression
- Immune infiltration patterns
- Proliferation zones
- Tumor heterogeneity assessment

**Slide 6: Histopathology & Imaging**
- H&E morphology
- Ki67 proliferation index
- CD8 infiltration quantification
- Multiplex IF phenotyping

**Slide 7: Integrated Findings**
- Multi-modal consistency table
- Primary resistance mechanisms (ranked)
- Druggable targets identified

**Slide 8: Treatment Recommendations**
- First-line: Drug + evidence + expected response
- Second-line: Alternative + rationale
- Clinical trial opportunities
- NCCN guideline compliance

**Slide 9: Monitoring Plan**
- Biomarkers to track
- Imaging schedule
- ctDNA monitoring
- Response assessment criteria

Output: 9-slide presentation with visualizations, suitable for oncology tumor board
```

---

### Prompt 14: Adverse Event Management - Hypersensitivity Reaction

**Time:** 3 minutes | **Complexity:** Low | **Output:** AE management plan

```
Patient [ID] developed hypersensitivity reaction during paclitaxel infusion:

1. **Grade Assessment:**
   - Grade 1: Mild transient rash, drug fever <38°C
   - Grade 2: Moderate rash, fever ≥38°C, dyspnea
   - Grade 3: Severe bronchospasm, hypotension, generalized urticaria
   - Grade 4: Anaphylaxis

2. **Immediate Management (if Grade 3-4):**
   - Stop infusion immediately
   - Epinephrine 0.3-0.5 mg IM
   - Diphenhydramine 50 mg IV
   - Hydrocortisone 100-200 mg IV
   - O2, IV fluids, monitor vitals

3. **Future Treatment:**
   - Grade 1-2: Consider re-challenge with aggressive premedication
   - Grade 3-4: Avoid paclitaxel, use alternative (docetaxel, carboplatin, PLD)

4. **Premedication Protocol (if re-challenge):**
   - Dexamethasone 20 mg PO 12h + 6h before
   - Diphenhydramine 50 mg IV 30 min before
   - H2 blocker (ranitidine 50 mg IV or famotidine 20 mg IV) 30 min before
   - Slow infusion rate (3-6 hours)

Output: AE grade, immediate management, re-challenge decision, premedication protocol
```

---

### Prompt 15: End-of-Treatment Summary and Survivorship Plan

**Time:** 10 minutes | **Complexity:** Low | **Output:** Survivorship care plan

```
For patient [ID] completing front-line treatment for ovarian cancer:

**Treatment Summary:**
1. Diagnosis: Stage, grade, histology
2. Treatment received:
   - Surgery: Type, date, outcome
   - Chemotherapy: Regimen, cycles, completion date
   - Targeted therapy: Drug, duration
3. Response: Complete/partial/stable/progressive
4. Residual disease: None / measurable

**Surveillance Plan:**
1. **Clinical Exams:**
   - Every 3 months for 2 years
   - Every 6 months for years 3-5
   - Annually thereafter

2. **CA-125:**
   - Every 3 months for 2 years (if elevated at diagnosis)
   - Note: Rising CA-125 alone not indication for treatment (GCIG criteria)

3. **Imaging:**
   - CT chest/abdomen/pelvis every 6 months for 2 years
   - Then annually or as clinically indicated
   - PET not routinely recommended

4. **Genetic Counseling:**
   - If BRCA1/2+: Family testing, cascade screening
   - Risk-reducing salpingo-oophorectomy for relatives

5. **Quality of Life:**
   - Neuropathy management (if present)
   - Fatigue assessment
   - Psychosocial support
   - Fertility preservation discussion (if applicable)

6. **Recurrence Signs:**
   - New/worsening abdominal pain or bloating
   - GI symptoms (obstruction, nausea)
   - Unexplained weight loss
   - **Instruct patient to report symptoms promptly**

Output: Treatment summary, surveillance schedule, genetic counseling referral, QOL plan
```

---

## Summary of Clinical Workflow Prompts

### By Clinical Phase:
- **Diagnosis & Molecular Profiling:** Prompts 1, 7
- **Treatment Planning:** Prompts 2, 3, 4, 5, 8, 9, 10, 11
- **Treatment Validation:** Prompt 6
- **Monitoring:** Prompt 12
- **Tumor Board:** Prompt 13
- **Adverse Events:** Prompt 14
- **Survivorship:** Prompt 15

### By Complexity:
- **Low (3-5 min):** Prompts 7, 8, 10, 12, 14, 15
- **Medium (5-15 min):** Prompts 1, 3, 5, 9, 11
- **High (15-45 min):** Prompts 2, 4, 6, 13

### By Output Type:
- **Clinical Reports:** Prompts 1, 2, 3, 4, 5, 6, 13
- **Treatment Recommendations:** Prompts 7, 8, 9, 10, 11
- **Monitoring Plans:** Prompts 12, 15
- **Acute Management:** Prompt 14

---

**Document Version:** 1.0
**Date:** 2026-01-16
**Target Audience:** Oncologists, Clinical Researchers, Bioinformaticians
