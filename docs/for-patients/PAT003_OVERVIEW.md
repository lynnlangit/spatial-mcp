<!-- REVIEW CHECKLIST: [ ] Reviewed by patient advocate [ ] Reviewed by clinician -->

# PAT003: Preventive Cardiovascular Health — 65+ Female

## What this case represents

PAT003 is a synthetic patient profile representing a 67-year-old post-menopausal
woman with controlled hypertension and significant bilateral family history of
cardiovascular disease. She is otherwise in good health and actively engaged in
preventive care.

This case was designed to address a documented gap in cardiovascular medicine:
women over 65 are underrepresented in the clinical trials that underpin current
risk scoring tools. The Framingham Risk Score, the most widely used cardiovascular
risk calculator, was derived primarily from a male cohort. The Reynolds Risk Score,
specifically validated in women and incorporating both hsCRP and family history,
is used as the primary risk estimate for PAT003.

## How PAT003 differs from PAT001 and PAT002

| Dimension | PAT001/PAT002 | PAT003 |
|-----------|--------------|--------|
| Disease state | Active HGSOC (acute oncology) | Pre-disease (preventive) |
| Time horizon | Immediate treatment decisions | 10-year risk reduction |
| Primary data types | Tumor genomics, spatial transcriptomics | Biomarkers, CVD risk genes, lifestyle |
| Goal | Slow or halt disease | Prevent first event |
| Platform role | Therapeutic hypothesis generation | Risk monitoring + intervention guidance |

## Key clinical questions

1. What is PAT003's 10-year cardiovascular event risk using the Reynolds Risk Score?
2. Which genetic variants (APOE, LDLR, PCSK9, LPA, 9p21) most elevate her risk?
3. Is lisinopril the optimal medication given her ACE gene pharmacogenomics?
4. What is the evidence for statin initiation at LDL = 118 mg/dL in intermediate-risk women?
5. What lifestyle interventions have the strongest evidence for her specific profile?
6. Should Lp(a) be measured? (It is not captured by standard lipid panels.)
7. What is the role of coronary artery calcium (CAC) scoring for reclassification?

## Current server coverage

| Clinical question | Server | Coverage |
|-------------------|--------|----------|
| CVD gene-disease associations | opentargets | Partial — generic mock, no CVD ontology |
| Drug targets and emerging therapies | opentargets | Partial — no CVD drug mock data |
| Medication safety profile | opentargets | Partial — no ACE safety data in DRY_RUN |
| Structured preventive health report | patient-report | Gap — schema is oncology-only |
| Biomarker panel integration | multiomics | Gap — expects omics matrices, not biomarkers |
| Polygenic risk score for CVD | — | **Gap — new server needed** |
| Longitudinal biomarker tracking | — | **Gap — new server needed** |
| Lifestyle intervention evidence | — | **Gap — new server needed** |

## Scientific rationale for this demographic

Post-menopausal women experience a significant increase in cardiovascular risk
due to estrogen decline, which affects lipid metabolism, vascular tone, and
inflammatory markers. Women more frequently present with atypical MI symptoms
(fatigue, nausea, jaw pain) that lead to underdiagnosis. For these reasons,
AI-assisted preventive monitoring has particular value for this demographic.

---
*PAT003 is a synthetic patient profile. All values are representative of a
population-level use case and do not represent any specific individual.
This is not a clinical tool. All findings should be reviewed by a qualified
clinician.*
