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

Standard oncology workup (BRCA1/2, HRD panel, tumor genomic panel) generates **no immunotherapy or investigational hypotheses**. For preventive health, standard lipid panels and population genetic screens miss key risk factors. Manual multi-modal analysis across genomics, spatial transcriptomics, and clinical data is clinically impractical -- the platform automates it.

### Architecture at a glance

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

All tools accessible via natural language. Every AI result requires **clinician APPROVE/REVISE/REJECT**. HIPAA-compliant. 11 servers return per-tool **XAI metadata** (confidence levels, evidence grades, counterfactuals). Current server and tool counts: **[Server Registry](docs/reference/shared/server-registry.md)**.

## The Results

The platform surfaces clinically actionable findings that standard workup cannot reach — **6 investigational hypotheses across 2 cancer types** plus 3 preventive health evidence gaps, validated across three independent use cases:

| Use Case | Patient | Key Finding Missed by Standard Workup |
|---|---|---|
| **HGSOC (Stage IV)** | PAT001 | 3 investigational paths: neoantigen vaccine (RMPEAAPPV IC50 7.8 nM), NNMT/CAF inhibition, convergent checkpoint blockade |
| **ER+ Breast Cancer** | PAT002 | 3 investigational hypotheses: inavolisib over alpelisib (PIK3CA H1047R, 2024 FDA approval), MYC-driven triple therapy, YSAPLSSSL neoepitope vaccine + CAF depletion + anti-PD-1 — zero disease-specific code changes |
| **Preventive Cardiovascular** | PAT003 | Intermediate CVD risk (Reynolds 14.3%) with 3 high-priority gaps missed by standard lipid panel AND population genetic screen: Lp(a), APOE genotype, CAC score |

The same 20-server architecture runs all three. No disease-specific code changes between use cases.

**[How we validate our results →](https://lynnlangit.github.io/precision-medicine-mcp/proof-layers.html)**

### Validated results — PAT001 (HGSOC)

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

All servers default to **DRY_RUN mode** (mock responses, no API keys needed) for quick validation. Set `*_DRY_RUN=false` to use **synthetic patient data** for end-to-end testing.

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

**Apache 2.0** | **Python 3.11+** | **FastMCP >= 2.13** | **uv** for package management
