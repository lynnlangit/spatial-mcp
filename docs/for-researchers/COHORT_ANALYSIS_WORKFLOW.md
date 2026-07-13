# Cohort Analysis Workflow with External MCP Servers

Use this guide when running the platform on a cohort of patients (2–100+) and
you want to layer in external MCP connectors — PubMed, ClinicalTrials.gov,
bioRxiv, and cBioPortal — alongside the platform's 19 custom servers.

**Prerequisites:**
- Platform installed and at least one patient running cleanly end-to-end
- External connectors enabled in Claude settings (see [CONNECT_EXTERNAL_MCP.md](CONNECT_EXTERNAL_MCP.md))
- For cBioPortal: community server running locally (`uv run cbioportal-mcp`)

---

## Which connectors to enable

Enable only what your cohort analysis actually needs. More connectors = more
context for Claude to manage, which can increase latency and cost.

| Connector | Enable for... | Skip for... |
|---|---|---|
| **ClinicalTrials.gov** | Any cohort where trial eligibility is a deliverable | Pure biomarker characterization runs |
| **PubMed** | Novel variants (no established guideline), post-May 2025 guideline updates, citation support for reports | Standard variants with well-established FDA/NCCN guidance (stable in Claude's training) |
| **bioRxiv / medRxiv** | Cutting-edge findings on novel targets, spatial/perturbation methods | Any analysis where only peer-reviewed evidence is acceptable |
| **cBioPortal** | Cohort-level TCGA comparison, population frequency validation | Single-patient analysis or when mcp-mocktcga is sufficient for development |
| **Seqera** | Cohort-scale nf-core pipeline runs (RNA-seq, WGS, ATAC-seq) | Analyses using pre-processed data already in the platform |
| **Hugging Face** | Finding novel foundation models for cohort-specific tasks (spatial, genomic) | Standard pipeline runs using the platform's built-in servers |

---

## What Claude already knows (no external lookup needed)

Claude's training includes biomedical literature through **May 2025**. For the
following, a live PubMed call is redundant — Claude's training knowledge is
sufficient and more reliable than a runtime lookup:

| Topic | Examples |
|---|---|
| Established FDA approvals | Olaparib (BRCA1/2, 2018), pembrolizumab TMB-H (2020), inavolisib (PIK3CA, 2024), alpelisib (PIK3CA, 2019) |
| NCCN guideline thresholds | HRD ≥42 (myChoice CDx), TMB ≥10 mut/Mb, MSI-H |
| Major clinical trial results | SOLO-1, OlympiA, SOLAR-1, KEYNOTE-158, OlympiAD |
| AMP/ASCO/CAP variant classification | Pathogenic/VUS/Benign criteria |
| IEDB/NetMHCpan binding thresholds | IC50 <50nM (strong binder), <500nM (weak binder) |
| Galon immune scoring | CD8:Treg ratio thresholds, Immunoscore framework |

**When you DO need a live PubMed lookup:**
- Variant first described or reclassified after May 2025
- Guideline update published after May 2025 (e.g., new NCCN version)
- Drug approval or label change after May 2025
- Preprint findings your team is specifically tracking

---

## Stage-by-stage workflow

The platform runs a 5-stage pipeline. External servers are most useful at
specific stages — don't enable them all for every stage.

### Stage 1 — Data Acquisition

**Custom servers used:** `mcp-epic`, `mcp-geodownload`, `mcp-mocktcga` (dev) / `cBioPortal` (prod)

**External connector: cBioPortal** — use here for cohort-level TCGA comparison.
Query once per cohort (not once per patient) to pull mutation frequencies,
survival benchmarks, and molecular subtypes for the relevant cancer type.

```
"Using cBioPortal, get mutation frequencies for TP53, BRCA1, BRCA2, PIK3CA,
and CCNE1 in the TCGA-OV cohort (serous ovarian). I'll use these as population
baselines when interpreting my cohort's genomic results."
```

### Stage 2 — Spatial Deconvolution

**Custom servers used:** `mcp-spatialtools`, `mcp-cibersortx`, `mcp-deepcell`, `mcp-cell-classify`

No external connectors typically needed at this stage. The platform's spatial
servers handle all deconvolution, segmentation, and phenotyping internally.

**Exception:** if you need a novel cell-type deconvolution signature not in
LM22, search Hugging Face for a published single-cell reference:

```
"Search Hugging Face datasets for single-cell RNA-seq references specific to
high-grade serous ovarian cancer tumor microenvironment, suitable for use
as a custom CIBERSORTx signature."
```

### Stage 3 — Target Profiling

**Custom servers used:** `mcp-opentargets`, `mcp-neoantigen`, `mcp-genomic-results`

This is where PubMed adds the most value — specifically for novel variants
that OpenTargets scores low due to sparse evidence, or for variants first
reported near or after Claude's training cutoff.

**Pattern: Novel variant literature check**

```
"The platform identified ARID1A p.Q456* (somatic, VAF 0.38) in patient PAT007.
OpenTargets gives it a low association score for ovarian cancer.

Search PubMed for recent papers on ARID1A loss-of-function in high-grade
serous ovarian cancer — specifically: (1) frequency in TCGA-OV, (2) any
synthetic lethality relationships with PARP inhibitors or ATR inhibitors,
(3) any clinical trials targeting ARID1A-deficient tumors."
```

**Pattern: Batch variant lookup across cohort**

For efficiency, group all novel/low-evidence variants across your cohort
and run ONE PubMed session rather than per-patient calls:

```
"Across my 12-patient HGSOC cohort, the following variants were flagged as
low-evidence by OpenTargets: [list]. For each, search PubMed and return:
actionability tier (FDA-approved / clinical trial / preclinical / no evidence),
most recent guideline or trial reference, and whether any evidence postdates
May 2025."
```

### Stage 4 — Causal Inference

**Custom servers used:** `mcp-perturbation`, `mcp-quantum-celltype-fidelity`, `mcp-multiomics`

**External connector: bioRxiv** — useful here if the perturbation target is a
novel gene or pathway where peer-reviewed evidence is sparse but preprints exist.

```
"The perturbation server predicts NNMT knockdown would reduce CAF activation
in PAT001's tumor microenvironment. Search bioRxiv and medRxiv for preprints
on NNMT inhibition in cancer-associated fibroblasts, published in the last
12 months. Flag any that have since been published in peer-reviewed journals."
```

### Stage 5 — Report Generation

**Custom servers used:** `mcp-patient-report`, `mcp-deidentify`

**External connector: ClinicalTrials.gov** — use here for per-patient trial
matching, after the report's investigational hypotheses are finalized.

**Pattern: Trial matching per patient**

```
"Patient PAT001 is a 52-year-old female with Stage IV HGSOC, BRCA1 germline
pathogenic, HRD=54, TMB=47.3, prior platinum + olaparib.

The platform's Stage 3 analysis identified these investigational hypotheses:
(1) neoantigen vaccine (RMPEAAPPV IC50 7.8nM), (2) NNMT/CAF inhibition,
(3) convergent checkpoint blockade.

Search ClinicalTrials.gov for recruiting Phase 1/2 trials matching this
patient profile. For each hypothesis, return: NCT ID, title, phase,
eligibility criteria that may exclude this patient, nearest site."
```

**Pattern: Batch trial matching across cohort**

```
"I have a 12-patient HGSOC cohort. For each patient I'll give you their
profile. Query ClinicalTrials.gov once per distinct investigational hypothesis
(not once per patient) and map which patients are potentially eligible
for each trial. Return a table: NCT ID × Patient ID × Eligible (Y/N/Check)."
```

---

## cBioPortal: switching from mock to real TCGA

In development mode, the platform uses `mcp-mocktcga` (synthetic cohort data).
For a real research cohort, switch to cBioPortal for population-level context.

**When to use cBioPortal vs. mcp-mocktcga:**

| Scenario | Use |
|---|---|
| Development, CI, student demos | `mcp-mocktcga` (no auth, no rate limits, fast) |
| Real cohort analysis, paper-quality statistics | `cBioPortal` community server |
| Hospital deployment (HOSPITAL1 production mode) | `cBioPortal` (auto-configured via `DEPLOYMENT_MODE=production`) |

**Setup for real cohort analysis:**

```bash
# Start the cBioPortal community server
cd cbioportal-mcp && uv run cbioportal-mcp

# Point at a local hospital instance if available
export CBIOPORTAL_BASE_URL=https://cbioportal.yourhospital.org/api
```

**Example: cohort-level mutation frequency comparison**

```
"Using cBioPortal, compare the mutation frequencies of TP53, BRCA1, BRCA2,
CCNE1, and NF1 in my 12-patient HGSOC cohort against TCGA-OV (n=316).
Flag any gene where my cohort frequency deviates more than 15 percentage
points from TCGA-OV — these may indicate a biologically distinct subgroup
or a cohort selection artifact."
```

---

## Cost and runtime guidance

External connectors are free to call (no per-call fees), but they add latency
and consume Claude's context window. Rules of thumb:

| Connector | Calls per cohort run | Context impact |
|---|---|---|
| cBioPortal | 1–3 (cohort-level) | Low — structured tabular returns |
| PubMed | 1 per unique novel variant | Medium — abstracts are verbose; use `search_articles` not `get_full_text_article` unless you need the full text |
| ClinicalTrials.gov | 1 per investigational hypothesis (not per patient) | Medium — batch across patients |
| bioRxiv | 1 per novel target | Low–medium |

**Context window tip:** run external connector queries in a fresh Claude
session after saving the platform's tool outputs. Don't mix Stage 3 tool
outputs + PubMed queries + Stage 5 report generation in a single long session —
context pressure degrades synthesis quality.

---

## Quick reference: which connector answers which question

| Research question | Best connector |
|---|---|
| What is the population frequency of this variant in TCGA? | cBioPortal |
| Is there a recruiting trial for this patient? | ClinicalTrials.gov |
| What does the recent literature say about this novel variant? | PubMed |
| Has this preprint been peer-reviewed yet? | bioRxiv / medRxiv |
| Is there a foundation model for this analysis task? | Hugging Face |
| What nf-core pipeline should I use for this data type? | Seqera |
| What is the FDA-approved indication for olaparib? | No lookup needed — ask Claude directly |

---

## Related docs

- [CONNECT_EXTERNAL_MCP.md](CONNECT_EXTERNAL_MCP.md) — setup instructions for each connector
- [Server Registry](../reference/shared/server-registry.md) — full list of custom and external servers
- [Installation Guide](../getting-started/installation.md) — platform setup
