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
3. A Tier 1 genetic screen was negative for familial hypercholesterolemia — how does this change her risk picture?
4. Is lisinopril the optimal medication given her ACE gene pharmacogenomics?
5. What is the evidence for statin initiation at LDL = 118 mg/dL in intermediate-risk women post-negative FH screen?
6. What lifestyle interventions have the strongest evidence for polygenic cardiovascular risk?
7. Should serum Lp(a) be measured, and what would an elevated result change?
8. What is the role of APOE genotyping for a 67-year-old woman with bilateral CVD family history?
9. What is the role of coronary artery calcium (CAC) scoring for reclassification at intermediate Reynolds risk?
10. What should she monitor and at what frequency, now that FH is ruled out?

## Current server coverage

| Clinical question | Server | Coverage |
|-------------------|--------|----------|
| 10-year CVD risk scoring | cardiometabolic | Covered — `calculate_cvd_risk_scores` (Reynolds, Framingham, ACC/AHA PCE) |
| CVD gene-disease associations | opentargets | Covered — CVD disease ontology (EFO IDs) plus risk genes APOE, LDLR, APOB, PCSK9, LPA, ACE, CDKN2A/B |
| Drug targets and emerging therapies | opentargets | Covered — CVD drug data for ACE (lisinopril), PCSK9, LDLR |
| Medication safety profile | opentargets | Covered — ACE safety profile available in DRY_RUN |
| Serum Lp(a) interpretation | cardiometabolic | Covered — `assess_lpa_status` |
| Structured preventive health report | cardiometabolic | Covered — `generate_preventive_report` |
| Biomarker panel integration | cardiometabolic | Covered — `assess_biomarker_panel` |
| Polygenic risk score for CVD | cardiometabolic | Covered — `search_cvd_prs_scores`, `calculate_cvd_prs`, `interpret_cvd_prs_percentile` (PGS Catalog) |
| Lifestyle intervention evidence | cardiometabolic | Covered — `get_lifestyle_evidence`, curated interventions with trial citations |
| Longitudinal biomarker tracking | — | **Gap — still open** (see [ROADMAP](../../ROADMAP.md)) |

*Coverage last verified against server source on 2026-08-08. The gaps this table
originally recorded were closed by `mcp-cardiometabolic` and by the PAT003
cardiovascular additions to `mcp-opentargets`. Tool counts and status:
[Server Registry](../reference/shared/server-registry.md).*

## Genetic screen findings and their clinical significance

A Tier 1 population genetic screen (11 genes: HBOC, Lynch syndrome, familial
hypercholesterolemia panels) returned an overall **negative** result. This is
clinically meaningful in two directions.

**What the negative result clarifies:** Monogenic familial hypercholesterolemia
(FH) is effectively ruled out. PAT003's LDL of 118 mg/dL and bilateral family
history are not caused by a single high-impact variant in LDLR, APOB, LDLRAP1,
or PCSK9. Her risk profile is more likely driven by polygenic burden — many
small-effect common variants acting together — combined with shared family
environment. This shifts clinical management from "find the variant, treat
aggressively" toward "quantify polygenic and biomarker risk, then decide."

**What the negative result does not resolve:** Three high-priority gaps remain
that this screen does not address:

| Gap | Why it matters | Priority |
|-----|----------------|----------|
| APOE genotype | Strongest common genetic risk for CVD and Alzheimer's; not on population screens; highly relevant at 67 | HIGH |
| Serum Lp(a) | Independent CVD risk factor; genetically fixed; not on standard lipid panels; elevated Lp(a) would reclassify her risk upward | HIGH |
| Coronary artery calcium (CAC) score | Best single reclassification tool for intermediate-risk patients; CAC=0 would defer statin; CAC>100 would accelerate treatment | HIGH |

**Platform opportunity:** PAT003 demonstrates that the platform's value is not
only in analyzing what was tested, but in surfacing what was *not* tested and
why it matters. The three gaps above are the most actionable output of this
analysis — more useful than confirming a negative result.

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
