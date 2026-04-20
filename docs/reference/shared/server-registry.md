# MCP Server Registry - Quick Reference

**Custom Servers:** 17 (99 tools) | **Production Ready:** 15 (88%) | **External Servers:** 6 (46 tools) | **Framework:** FastMCP ≥ 2.13

📁 **[Individual Server Documentation →](../../../servers/README.md)**

---

## Production Servers ✅

| Server | Tools | Status | Key Capabilities | Documentation |
|--------|-------|--------|------------------|---------------|
| **mcp-fgbio** | 4 | 95% Real | FASTQ/VCF QC, genome refs, variant calling | [README](../../../servers/mcp-fgbio/README.md) |
| **mcp-multiomics** | 10 | 95% Real | HAllA integration, Stouffer meta-analysis, upstream regulators, heatmap, PCA | [README](../../../servers/mcp-multiomics/README.md) |
| **mcp-spatialtools** | 16 | 95% Real | Spatial DE, STAR alignment, ComBat, pathway enrichment, patient-context resolution | [README](../../../servers/mcp-spatialtools/README.md) |
| **mcp-perturbation** | 8 | 100% Real | GEARS GNN treatment response, perturbation prediction | [README](../../../servers/mcp-perturbation/README.md) |
| **mcp-quantum-celltype-fidelity** | 6 | 100% Real | Quantum PQCs, fidelity analysis, Bayesian UQ, immune evasion | [README](../../../servers/mcp-quantum-celltype-fidelity/README.md) |
| **mcp-deepcell** | 3 | 100% Real | DeepCell-TF segmentation, nuclear/membrane models, per-cell marker quantification | [README](../../../servers/mcp-deepcell/README.md) |
| **mcp-cell-classify** | 3 | 100% Real | Cell phenotype classification, multi-marker phenotyping, phenotype visualization | [README](../../../servers/mcp-cell-classify/README.md) |
| **mcp-epic** | 4 | 100% Real | FHIR R4 API, real EHR integration (local deployment only) | [Source](../../../servers/mcp-epic/) |
| **mcp-openimagedata** | 5 | 100% Real | PIL image loading, scikit-image registration + feature extraction, MxIF compositing, H&E annotation | [README](../../../servers/mcp-openimagedata/README.md) |
| **mcp-patient-report** | 5 | 100% Real | Patient-facing PDF reports, plain-language summaries, clinician review gate | [README](../../../servers/mcp-patient-report/README.md) |
| **mcp-genomic-results** | 4 | 100% Real | Somatic variant/CNV parsing, clinical annotations, HRD scoring | [README](../../../servers/mcp-genomic-results/README.md) |
| **mcp-geodownload** | 6 | 100% Real | GEO/SRA dataset download, Entrez REST, expression matrices | [README](../../../servers/mcp-geodownload/README.md) |
| **mcp-opentargets** | 6 | 100% Real | Drug-target associations, disease ontology, GraphQL API | [README](../../../servers/mcp-opentargets/README.md) |
| **mcp-cibersortx** | 5 | 100% Real | Immune deconvolution, LM22 signatures, job polling | [README](../../../servers/mcp-cibersortx/README.md) |
| **mcp-neoantigen** | 6 | 100% Real | MHC binding prediction, IEDB API, neoantigen burden scoring | [README](../../../servers/mcp-neoantigen/README.md) |

---

## Mock Servers (For Workflow Testing) ❌

> **HOSPITAL1 deployment note:** These servers stay in the repository for CI,
> student Streamlit demos, and development-mode Cloud Run deployments. They
> are **automatically disabled in HOSPITAL1 production-mode deployments** by
> the profile filter in `infrastructure/deployment/deploy_to_gcp.sh`
> (`DEPLOYMENT_MODE=production` drops `mcp-mockepic` and `mcp-mocktcga`;
> `DEPLOYMENT_MODE=development` drops `mcp-epic`). Production mode ships
> `mcp-epic` (real Epic FHIR R4) and the external **cBioPortal** community
> MCP in their place.

| Server | Tools | Purpose | Documentation |
|--------|-------|---------|---------------|
| **mcp-mocktcga** | 5 | Mock TCGA cohort queries, survival analysis (synthetic) | [README](../../../servers/mcp-mocktcga/README.md) |
| **mcp-mockepic** | 3 | Synthetic FHIR data for testing (by design) | [Source](../../../servers/mcp-mockepic/) |

---

## Status Legend

- ✅ **Production Ready**: Real APIs, extensively tested, validated outputs
- ⚠️ **Partial**: Core features real, some components mocked
- ❌ **Mocked**: Demonstration/workflow testing only - **DO NOT USE FOR RESEARCH**

---

## Quick Find

### By Analysis Type
- **Clinical Data**: mcp-epic (real EHR), mcp-mockepic (synthetic)
- **Genomics**: mcp-fgbio (QC/variants), mcp-genomic-results (somatic/CNV/HRD), mcp-geodownload (GEO/SRA download), mcp-opentargets (drug-target associations), mcp-mocktcga (cohort comparison - mocked)
- **Multi-omics**: mcp-multiomics (integration/meta-analysis)
- **Spatial**: mcp-spatialtools (spatial transcriptomics)
- **Imaging**: mcp-deepcell (cell segmentation + quantification), mcp-cell-classify (phenotype classification), mcp-openimagedata (histology + registration + features)
- **Immunology**: mcp-cibersortx (immune deconvolution), mcp-neoantigen (neoantigen prediction & HLA binding)
- **Treatment**: mcp-perturbation (GEARS prediction), mcp-quantum-celltype-fidelity (quantum fidelity)
- **Reports**: mcp-patient-report (patient-facing summaries)
### By Production Readiness
- **Ready for Research**: mcp-fgbio, mcp-multiomics, mcp-spatialtools, mcp-perturbation, mcp-quantum-celltype-fidelity, mcp-deepcell, mcp-cell-classify, mcp-epic, mcp-openimagedata, mcp-patient-report, mcp-genomic-results, mcp-geodownload, mcp-opentargets, mcp-cibersortx, mcp-neoantigen
- **Not Ready**: mcp-mocktcga (synthetic data)
- **Mock by Design**: mcp-mockepic (testing only)

---

## External MCP Servers

Six external servers complement the custom servers above. These are either Anthropic-hosted connectors (toggle on in Claude settings) or community open-source servers (self-hosted).

| Server | Tools | Type | Description |
|--------|-------|------|-------------|
| **ClinicalTrials.gov** | 6 | Anthropic connector | Search 500K+ trials by condition, sponsor, phase, eligibility |
| **bioRxiv & medRxiv** | 9 | Anthropic connector | Search 260K+ preprints, track publication status |
| **PubMed** | 5 | Anthropic connector | Search 36M+ biomedical citations, full text via PMC |
| **Seqera** | 7 | Anthropic connector | Nextflow pipeline orchestration, nf-core modules |
| **cBioPortal** | 12 | Community (self-hosted) | Real TCGA and cancer genomics data (replaces mcp-mocktcga for real data) |
| **Hugging Face** | 7 | Community (self-hosted) | ML model/dataset/paper search |

**Setup & details:** [Connect External MCP Servers](../../for-researchers/CONNECT_EXTERNAL_MCP.md)

---

## Framework Version

All 17 custom servers declare `fastmcp>=2.13.0` in their `pyproject.toml`
as of 2026-04-08 (HOSPITAL1 migration — see `docs/HOSPITAL1_DEPLOYMENT_PLAN.md`).
Resolved versions in `uv.lock` span 2.14.1 through 3.1.0; every server has
been verified by `scripts/phase6_signature_audit.sh` to import cleanly,
enumerate the expected tool count, and use only public FastMCP APIs
(no reliance on the removed `_tool_manager._tools` private attribute).

| Build backend | Count | Servers |
|---|---|---|
| `hatchling.build` | 10 | server-boilerplate, patient-report, genomic-results, cibersortx, geodownload, neoantigen, opentargets, multiomics, quantum-celltype-fidelity, perturbation |
| `setuptools.build_meta` | 8 | epic, fgbio, mockepic, cell-classify, openimagedata, mocktcga, spatialtools, deepcell |

Both backends are PEP 517-compliant and work with `uv build` and
`pip install -e .`. The platform does not require a single backend.

---

**Last Updated:** 2026-04-11
**Maintained By:** Precision Medicine MCP Team
