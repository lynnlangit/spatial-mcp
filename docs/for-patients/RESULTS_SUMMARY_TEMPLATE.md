<!-- REVIEW CHECKLIST: [ ] Reviewed by patient advocate [ ] Reviewed by oncology nurse [ ] Approved by PatientOne — do NOT publish without all three checkboxes filled -->

# Patient Results Summary -- Template for Clinician Use

*Fill in all `{{PLACEHOLDER}}` values before sharing with patient or family.*

*Note: PAT001 reference values shown below are synthetic and do not represent any
real patient's data. They are included to help clinicians contextualize results.*

## Your sample
- Date analyzed: {{ANALYSIS_DATE}}
- Sample ID: {{SAMPLE_ID}}
- Tumor type: High-Grade Serous Ovarian Cancer (HGSOC)

## DNA Repair Score (HRD): {{HRD_SCORE}}

| Range | Interpretation |
|-------|---------------|
| Below 40 | Low -- repair mostly intact |
| 40-60 | Intermediate |
| Above 60 | High -- significant repair deficiency |

*PAT001 synthetic reference value: 72 (High)*

Implication: {{HRD_INTERPRETATION}}

## Tumor Mutation Burden: {{TMB}} mutations per megabase

| Range | Interpretation |
|-------|---------------|
| Below 5 | Low |
| 5-10 | Intermediate |
| Above 10 | High |

*PAT001 synthetic reference value: 4.2 (Low)*

Implication: {{TMB_INTERPRETATION}}

## Immune Activity in Your Tumor

| Cell type | Count | Role |
|-----------|-------|------|
| Tumor cells | {{TUMOR_COUNT}} | Cancer cells identified |
| CD8+ T cells | {{CD8_COUNT}} | Immune "guard" cells |
| Macrophages | {{MACRO_COUNT}} | Immune support cells |
| Endothelial cells | {{ENDO_COUNT}} | Blood vessel lining |
| Fibroblasts | {{FIBRO_COUNT}} | Structural support |

## Top Neoantigen
- Peptide: {{TOP_PEPTIDE}}
- IC50 binding strength: {{IC50_NM}} nM (lower = stronger immune recognition)
- *PAT001 synthetic reference: RMPEAAPPV at 7.8 nM*

## Top Therapeutic Hypothesis
{{THERAPEUTIC_HYPOTHESIS}}

## Recommended Next Steps
- {{NEXT_STEP_1}}
- {{NEXT_STEP_2}}
- {{NEXT_STEP_3}}

---

*This is not a clinical report. Discuss all findings with your oncology team.*
