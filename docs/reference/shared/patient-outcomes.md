# Patient Outcomes Reference

> **Canonical source.** This file is the single authoritative narrative for what the
> Precision Medicine MCP Platform found for each synthetic patient. All other docs must
> link to the relevant anchor rather than restating these findings.
>
> Source of truth for numeric values: `tests/fixtures/pat00X_canonical.py`
> Last updated: 2026-04-23 (v17 — PAT003 added)

---

## PAT001 — HGSOC Stage IV {#pat001}

**Profile:** 58-year-old female, Stage IV high-grade serous ovarian cancer (HGSOC),
BRCA1+, platinum-resistant. Standard workup found BRCA1 germline mutation and initiated
platinum-based chemotherapy. Standard liquid biopsy and genomic panels did not surface
additional therapeutic hypotheses.

**What standard workup missed:** Three independent, convergent investigational paths:

- **Personalized neoantigen vaccine** — TP53 R175H mutation produces the RMPEAAPPV
  peptide, which binds HLA-A*02:01 with IC50 7.8 nM (strong binder; < 50 nM threshold).
  The neoantigen burden (TMB POLE-corrected: 47.3 mut/Mb) supports vaccine candidacy.

- **NNMT/CAF inhibition** — Cancer-associated fibroblast (CAF) fraction: 18.2%.
  GEARS GNN perturbation modelling predicts that NNMT knockdown recovers immune
  infiltration markers, suggesting CAF remodelling as a combination strategy.

- **Convergent checkpoint blockade** — POLE-corrected TMB 47.3 mut/Mb (ultra-high)
  combined with spatial CD8+ T-cell exclusion pattern on Visium data supports
  dual anti-PD-1/CTLA-4 blockade.

**Canonical numeric outcomes** (source: `tests/fixtures/pat001_canonical.py`):

| Metric | Value | Unit |
|---|---|---|
| TMB (POLE-corrected) | 47.3 | mut/Mb |
| Top neoantigen IC50 | 7.8 | nM |
| HRD score | 54 | — |
| CAF fraction | 18.2 | % |

---

## PAT002 — ER+ Breast Cancer (Stage IIA) {#pat002}

**Profile:** Stage IIA invasive ductal carcinoma (IDC), ER+/PR+/HER2−, BRCA2+ germline,
PIK3CA H1047R somatic. Standard workup identified ER+ status and initiated endocrine
therapy (aromatase inhibitor). BRCA2 germline result was returned but HRD score of 35
fell below the myChoice CDx 42-point PARP-eligibility threshold, so olaparib was not
offered.

**What standard workup missed:** PARP inhibitor eligibility reclassification.

The platform cross-referenced the HRD 35 result with the germline BRCA2 variant
using the same server stack as PAT001 — zero architecture changes. Current FDA labeling
for olaparib (SOLO-1 and OlympiA trials) supports germline BRCA1/2-positive status as
an independent PARP eligibility criterion regardless of HRD score. PAT002 is
PARP-eligible on germline grounds alone.

This case validates the platform's architecture generalizability: the same 19-server
stack handles a second cancer type with different biology and a different key finding.

**Canonical numeric outcomes** (source: `tests/fixtures/pat002_canonical.py`):

| Metric | Value | Unit |
|---|---|---|
| HRD score | 35 | — |
| ESR1/PGR Moran's I | 0.42–0.45 | — |

---

## PAT003 — Preventive Cardiovascular Health {#pat003}

**Profile:** 67-year-old post-menopausal female. Standard annual physical + Helix Tier 1
population genetic screen — all results returned as "normal." Standard lipid panel
ordered to evaluate statin candidacy.

**What standard workup missed:** Three high-priority evidence gaps and intermediate
10-year CVD risk confirmed by three independent algorithms.

### Risk scores

| Algorithm | 10-yr Risk | Category | Notes |
|---|---|---|---|
| Reynolds Risk Score | 14.3% | Intermediate | Women-specific; incorporates hsCRP and family history |
| Framingham Risk Score | 12.0% | Intermediate | Standard community-based model |
| ACC/AHA Pooled Cohort Equation | 10.3% | Intermediate | Above 7.5% statin-consideration threshold |

All three algorithms converged on intermediate risk (7.5–20%). Convergence across
partially overlapping models strengthens the intermediate classification.

### Three high-priority gaps missed by standard workup

**Gap 1 — Serum Lp(a) not measured.**
Lp(a) is genetically determined, does not respond to standard LDL-lowering statins,
and is an independent cardiovascular risk factor. The 2023 ESC/EAS guidelines recommend
measuring Lp(a) once in every adult's lifetime. PAT003's standard lipid panel reported
LDL 118 mg/dL — Lp(a) was not included and not ordered.

**Gap 2 — APOE genotype unknown.**
APOE is the strongest common genetic determinant of both cardiovascular disease and
Alzheimer's risk. It is not included in the Helix Tier 1 panel or any current
population-level screening programme. The negative Tier 1 result ruled out monogenic
familial hypercholesterolaemia (FH) but did not address polygenic or APOE-mediated risk.

**Gap 3 — Coronary artery calcium (CAC) score not obtained.**
At intermediate CVD risk (7.5–20%), CAC is the best-validated reclassification tool
per the 2018 ACC/AHA cholesterol guidelines. A CAC of 0 would support deferring statins
("statin holiday"); a CAC > 100 or ≥ 75th percentile for age/sex would strengthen the
case for initiation. Not ordered; not mentioned in the standard workup.

### Clinical reframe: the negative genetic screen is not "nothing"

The Helix Tier 1 negative result ruled out monogenic FH — a high-penetrance, single-gene
cause of premature CVD. This shifts the clinical question: if monogenic risk is absent,
the primary remaining mechanisms are polygenic accumulation and modifiable risk factors.
That reframe makes Lp(a), APOE, and CAC the three tests most likely to change clinical
management — precisely the three the platform flagged.

### hsCRP and JUPITER trial context

hsCRP: 1.8 mg/L — just below the 2.0 mg/L threshold used in the JUPITER trial
(Ridker et al. NEJM 2008), at which rosuvastatin demonstrated significant cardiovascular
event reduction in patients with LDL < 130 mg/dL. This margin is clinically meaningful
to track: a repeat hsCRP measurement above 2.0 mg/L would bring PAT003 into JUPITER
criteria.

**Canonical numeric outcomes** (source: `tests/fixtures/pat003_canonical.py`):

| Metric | Value | Unit |
|---|---|---|
| Reynolds Risk Score | 14.3 | % (10-yr) |
| Framingham Risk Score | 12.0 | % (10-yr) |
| ACC/AHA ASCVD Risk | 10.3 | % (10-yr) |
| hsCRP | 1.8 | mg/L |
| LDL | 118 | mg/dL |
| HDL | 58 | mg/dL |
| Systolic BP | 138 | mmHg |

---

## Quick-reference table

| Patient | Use case | Key finding missed by standard workup | Anchor |
|---|---|---|---|
| PAT001 | HGSOC Stage IV | 3 investigational paths (neoantigen vaccine, NNMT/CAF, checkpoint) | [#pat001](#pat001) |
| PAT002 | ER+ breast cancer | PARP eligibility via BRCA2 germline despite HRD 35 < myChoice threshold | [#pat002](#pat002) |
| PAT003 | Preventive CVD | 3 evidence gaps (Lp(a), APOE, CAC) missed by lipid panel + Helix Tier 1 | [#pat003](#pat003) |

---

*To update this file: first update the fixture at `tests/fixtures/pat00X_canonical.py`,
then update the table above. All other docs should link here — do not copy these values.*
