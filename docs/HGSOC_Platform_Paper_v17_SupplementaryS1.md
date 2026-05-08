# Supplementary Table S1 — Full 19-Server Specification

**Table S1.** Complete server inventory for the precision medicine MCP platform.
Validation timestamps reflect no-dry_run execution unless noted.

| # | Server | Function | Mode | Stage | Validated |
|---|--------|----------|------|-------|-----------|
| 1 | mcp-mockepic | Patient clinical records (FHIR mock) | Synthetic (EPIC_DRY_RUN=true) | 1 | Apr 17, 2026 |
| 2 | mcp-fgbio | FASTQ QC, UMI extraction, genomic utilities | Live/Mock | 1 | Apr 17, 2026 (PAT001); deferred PAT002 — no FASTQ |
| 3 | mcp-geodownload | NCBI GEO dataset search and download | Live | 1 | Apr 17, 2026 |
| 4 | mcp-genomic-results | VCF/CNS parsing, HRD scoring | File-based | 1 | Apr 17, 2026 |
| 5 | mcp-mocktcga | TCGA cohort comparison | Mock | 1 | Apr 17, 2026 |
| 6 | mcp-spatialtools | Spatial QC, NNLS deconvolution, Moran's I, visualization | Live | 2 | Apr 17, 2026 |
| 7 | mcp-cibersortx | Immune deconvolution (NNLS; CIBERSORTx REST when token available) | NNLS/REST | 2 | Apr 17, 2026 |
| 8 | mcp-opentargets | Open Targets evidence scores, drug candidates (GraphQL) | Live GraphQL | 3 | Apr 17, 2026 |
| 9 | mcp-multiomics | Stouffer meta-analysis, upstream regulator inference, PCA | Live | 3 | Apr 17, 2026 |
| 10 | mcp-perturbation | GEARS GNN perturbation prediction (load→setup→train→predict) | GNN | 4 | Apr 17, 2026 |
| 11 | mcp-quantum-celltype-fidelity | Quantum circuit cell-type embeddings, immune evasion states | Live | 4 | Apr 17, 2026 (PAT001); May 8, 2026 (PAT002) |
| 12 | mcp-neoantigen | Neoantigen burden, IEDB MHC-I binding, HLA typing | Live (IEDB) | 4 | Apr 17, 2026 |
| 13 | mcp-cell-classify | Multi-marker cell state classification | Live | 4 | Apr 17, 2026 |
| 14 | mcp-openimagedata | H&E histology image features, spatial registration | Live | 4 | Apr 17, 2026 |
| 15 | mcp-clinicaltrials | ClinicalTrials.gov trial matching | Live | 5 | Apr 17, 2026 |
| 16 | mcp-patient-report | PDF precision oncology report generation with clinician review gate | Live | 5 | Apr 17, 2026 |
| 17 | mcp-cardiometabolic | CVD risk scoring (Reynolds/Framingham/PCE), biomarker panel, statin decision logic | Live | 1 (parallel) | Apr 23, 2026 |
| 18 | mcp-ethical-ai | AI ethics guideline search and learning path | Live | Cross-cutting | Apr 17, 2026 |
| 19 | mcp-session-info | Session transcript and provenance logging | Live | Cross-cutting | Apr 17, 2026 |

**Notes.** HRD threshold: LOH+TAI+LST >= 42 (simplified genomic scar; not Myriad myChoice validated).
GEARS model: trained on synthetic HGSOC-modeled Perturb-seq data; Pearson r = 0.976 on held-out singles.
FastMCP 2.x upgrade and GEARS API compatibility resolved April 17, 2026. PAT003 cardiometabolic
pipeline validated April 23, 2026 (no dry_run). PAT002 deep-stage (quantum + neoantigen) validated
May 8, 2026 (SYNTHETIC_DATA mode).
