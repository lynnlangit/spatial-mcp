# Precision Medicine MCP Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-%E2%89%A5%202.13-green.svg)](https://github.com/jlowin/fastmcp)
[![MCP](https://img.shields.io/badge/MCP-2025--06--18-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

<img src="https://github.com/lynnlangit/precision-medicine-mcp/blob/main/data/images/repo-image.png">

> **Dedicated to PatientOne** -- a dear friend who passed from High-Grade Serous Ovarian Carcinoma in 2025.

*This platform automates multi-modal data processing for clinical decision **support** — all results require clinician review before any clinical action.*

---

## The Problem

A patient can spend months moving between referrals, imaging, repeat evaluations, and denials without reaching a decision. Much of that motion starts at the workup — the test that would have settled the question was never ordered, or the finding that would have opened a door was never generated.

Standard oncology panels (BRCA1/2, HRD, tumor genomic) surface **no immunotherapy or investigational hypotheses**. Standard lipid panels and population genetic screens miss the tests most likely to change preventive management. Integrating genomics, spatial transcriptomics, imaging, and clinical data by hand is clinically impractical — the platform automates it.

## What This Changes for the Patient

This platform does not triage patients or route referrals. It makes the analysis behind a decision complete on the first pass, instead of spread across a sequence of visits.

| Where the loop starts | What the platform does | Evidence |
|---|---|---|
| **The decisive test was never ordered** | Reports what was *not* tested, and why it would change management | PAT003 — Lp(a), APOE, CAC flagged after a "normal" panel ([detail](docs/reference/shared/patient-outcomes.md#pat003)) |
| **A threshold closed the door** | Re-checks eligibility against current labeling, not just the panel's cutoff | PAT002 — HRD 35 fell below the myChoice 42 cutoff; OlympiA labeling reopens it ([detail](docs/reference/shared/patient-outcomes.md#pat002)) |
| **No hypothesis was ever generated** | Synthesizes genomic, spatial, immune, and perturbation data into investigational paths | PAT001 + PAT002 — 6 hypotheses standard workup did not reach ([detail](docs/reference/shared/patient-outcomes.md)) |
| **The decision can't survive review** | Every result carries XAI metadata behind a clinician APPROVE/REVISE/REJECT gate, with an audit trail | [Proof layers →](https://lynnlangit.github.io/precision-medicine-mcp/proof-layers.html) |
| **Every modality is another handoff** | One orchestrated session replaces a multi-day relay across specialists | An estimated 40 hours → an estimated 2–5 hours ([modeled](docs/reference/shared/value-proposition.md)) |

**Fewer tests is also a result.** A CAC score of 0 would support *deferring* statin therapy for PAT003. The same analysis that adds a test can remove one — the goal is the decision, not the volume of workup.

**Scope of the claim.** These are three synthetic patients analyzed end-to-end, not clinical outcomes. Time and cost figures are modeled and pending clinical validation. The platform's contribution is to the quality and completeness of the decision, not to the referral pathway around it.

---

## The Results

The platform surfaces clinically actionable findings that standard workup cannot reach — **6 investigational hypotheses across 2 cancer types** plus 3 preventive health evidence gaps, validated across three independent use cases:

| Use Case | Patient | Key Finding Missed by Standard Workup |
|---|---|---|
| **HGSOC (Stage IV)** | PAT001 | 3 investigational paths: neoantigen vaccine (RMPEAAPPV IC50 7.8 nM), NNMT/CAF inhibition, convergent checkpoint blockade |
| **ER+ Breast Cancer** | PAT002 | 3 investigational hypotheses: inavolisib over alpelisib (PIK3CA H1047R, 2024 FDA approval), MYC-driven triple therapy, YSAPLSSSL neoepitope vaccine + CAF depletion + anti-PD-1 — zero disease-specific code changes |
| **Preventive Cardiovascular** | PAT003 | Intermediate CVD risk (Reynolds 14.3%) with 3 high-priority gaps missed by standard lipid panel AND population genetic screen: Lp(a), APOE genotype, CAC score |

The same 19-server architecture runs all three, with no disease-specific code changes. All tools are accessible via natural language, every AI result requires clinician **APPROVE/REVISE/REJECT**, and 11 servers return per-tool **XAI metadata** (confidence levels, evidence grades, counterfactuals). Current counts: **[Server Registry](docs/reference/shared/server-registry.md)**.

**[How we validate our results →](https://lynnlangit.github.io/precision-medicine-mcp/proof-layers.html)**

---

## Try It

```bash
# Clone and explore
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp

# Run tests for any server (DRY_RUN mode, no external deps needed)
cd servers/mcp-multiomics && uv run pytest -v

# Or use Claude Code to explore interactively
claude
```

Most servers default to **DRY_RUN mode** (mock responses, no API keys needed) for quick validation. Set `*_DRY_RUN=false` to use **synthetic patient data** for end-to-end testing. `mcp-deidentify` is the exception — it runs live by default, because a de-identification tool that silently returns fabricated data is a safety failure rather than a safe default.

---

## Learn More

| Audience | Start Here |
|----------|------------|
| **Getting Started** | [Installation Guide](docs/getting-started/installation.md) |
| **Funders** | [Executive Summary](docs/for-funders/EXECUTIVE_SUMMARY.md) |
| **Hospitals** | [Hospital Guide](docs/for-hospitals/README.md) |
| **Developers** | [Architecture](docs/for-developers/ARCHITECTURE.md) |
| **Researchers** | [Researcher Guide](docs/for-researchers/README.md) |
| **Educators** | [Educator Guide](docs/for-educators/README.md) |
| **All docs** | [Documentation Index](docs/INDEX.md) |

**Video:** [5-minute demo](https://www.youtube.com/watch?v=LUldOHHX5Yo) | **Paper:** [Why MCP for Healthcare](docs/reference/architecture/WHY_MCP_FOR_HEALTHCARE.md) | **External connectors:** [Setup guide](docs/for-researchers/CONNECT_EXTERNAL_MCP.md)

---

<details>
<summary><b>Architecture at a glance</b></summary>

```
                  +--------------------------------------+
                  |           CLIENT LAYER               |
                  |  Claude Desktop / Hospital EHR       |
                  |  Adapter / Research Notebook         |
                  +----------------+-----------------+
                                   |
                         MCP (FastMCP >= 2.13)
                                   |
   +---------------------------------------------------------------+
   |                                                               |
   |  PRE-PROCESSING (Stage 0)                                     |
   |  deidentify                                                   |
   |                                                               |
   |  DATA ACQUISITION      ANALYSIS & INFERENCE      REPORTING   |
   |                                                               |
   |  mockepic              spatialtools              patient-     |
   |  epic                  multiomics                report       |
   |  geodownload           perturbation                           |
   |  mocktcga              quantum-fidelity                       |
   |  genomic-results       opentargets                            |
   |  fgbio                 neoantigen                             |
   |                        cibersortx                             |
   |                        openimagedata                          |
   |                        deepcell                               |
   |                        cell-classify                          |
   |                        cardiometabolic                        |
   +---------------------------------------------------------------+
```

Full detail: **[Architecture](docs/for-developers/ARCHITECTURE.md)** · **[Server Registry](docs/reference/shared/server-registry.md)**

</details>

<details>
<summary><b>Validated results — PAT001 (HGSOC)</b></summary>

| Metric | Value | Source server |
|--------|-------|---------------|
| HRD score | 54 | mcp-genomic-results |
| TMB (POLE-corrected) | 47.3 mut/Mb | mcp-genomic-results |
| Top neoantigen IC50 (RMPEAAPPV) | 7.8 nM | mcp-neoantigen |
| Spatial spot count | 900 | mcp-spatialtools |
| Moran's I (global) | -0.0033 | mcp-spatialtools |
| Deconvolution: tumor | 56 cells | mcp-cibersortx |
| Deconvolution: endothelial | 44 cells | mcp-cibersortx |
| Deconvolution: macrophages | 43 cells | mcp-cibersortx |
| Deconvolution: fibroblasts | 41 cells | mcp-cibersortx |
| Deconvolution: CD8+ T cells | 30 cells | mcp-cibersortx |

Canonical values for all three patients: **[Patient Outcomes](docs/reference/shared/patient-outcomes.md)** (source of truth: `tests/fixtures/pat00X_canonical.py`)

</details>

---

**Apache 2.0** | **Python 3.11+** | **FastMCP >= 2.13** | **uv** for package management
