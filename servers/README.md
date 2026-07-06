# 🧬 MCP Server Implementation

Specialized MCP servers for precision medicine analysis. For current server and tool counts, see the [Server Registry](../docs/reference/shared/server-registry.md).

---

## 📊 Server Status

| Server | Tools | Status | Documentation |
|--------|-------|--------|---------------|
| 🔒 **mcp-deidentify** | 6 | ✅ 100% real | [README →](mcp-deidentify/README.md) |
| 🏥 **mcp-epic** | 4 | ✅ 100% real (local only) | [Testing Guide →](mcp-epic/CLAUDE_DESKTOP_TESTING.md) |
| 🎭 **mcp-mockepic** | 3 | 🎭 Mock by design (GCP) | — |
| 🧬 **mcp-fgbio** | 4 | ✅ 95% real | [README →](mcp-fgbio/README.md) |
| 🔬 **mcp-multiomics** | 10 | ✅ 95% real | [README →](mcp-multiomics/README.md) |
| 📍 **mcp-spatialtools** | 16 | ✅ 95% real | [README →](mcp-spatialtools/README.md) |
| 🧪 **mcp-perturbation** | 8 | ✅ 100% real (GEARS) | [README →](mcp-perturbation/README.md) |
| ⚛️ **mcp-quantum-celltype-fidelity** | 6 | ✅ 100% real (Qiskit) | [README →](mcp-quantum-celltype-fidelity/README.md) |
| 🖼️ **mcp-openimagedata** | 5 | ✅ 100% real | [README →](mcp-openimagedata/README.md) |
| 🖼️ **mcp-deepcell** | 3 | ✅ 100% real (Cloud Run) | [README →](mcp-deepcell/README.md) |
| 🔬 **mcp-cell-classify** | 3 | ✅ 100% real | [README →](mcp-cell-classify/README.md) |
| 🧪 **mcp-mocktcga** | 5 | ❌ Mocked (GDC-ready) | [README →](mcp-mocktcga/README.md) |
| 📄 **mcp-patient-report** | 5 | ✅ 100% real | [README →](mcp-patient-report/README.md) |
| 🧬 **mcp-genomic-results** | 4 | ✅ 100% real | [README →](mcp-genomic-results/README.md) |
| 🧬 **mcp-geodownload** | 6 | ✅ 100% real | [README →](mcp-geodownload/README.md) |
| 🎯 **mcp-opentargets** | 6 | ✅ 100% real | [README →](mcp-opentargets/README.md) |
| 🧫 **mcp-cibersortx** | 5 | ✅ 100% real | [README →](mcp-cibersortx/README.md) |
| 💉 **mcp-neoantigen** | 6 | ✅ 100% real | [README →](mcp-neoantigen/README.md) |
| ❤️ **mcp-cardiometabolic** | 14 | ✅ 100% real | [README →](mcp-cardiometabolic/README.md) |

**Production Ready:** See [Server Registry](../docs/reference/shared/server-registry.md) for current production readiness status.

---

## 🚀 Quick Navigation

### ✅ Production Servers
Use these for real analysis:
- 🔒 **mcp-deidentify** - Stage 0 HIPAA Safe Harbor de-identification for JSON, DOCX, PDF, VCF, h5ad — runs before all pipeline stages ([README](mcp-deidentify/README.md))
- 🏥 **mcp-epic** - Real Epic FHIR with HIPAA de-identification ([Testing Guide](mcp-epic/CLAUDE_DESKTOP_TESTING.md))
- 🧬 **mcp-fgbio** - Reference genomes, FASTQ QC ([README](mcp-fgbio/README.md))
- 🔬 **mcp-multiomics** - RNA/Protein/Phospho integration - 91 tests ✅ ([README](mcp-multiomics/README.md))
- 📍 **mcp-spatialtools** - Spatial transcriptomics analysis ([README](mcp-spatialtools/README.md))
- 🧪 **mcp-perturbation** - Perturbation prediction using GEARS (GNN, Nature Biotech 2024) ([README](mcp-perturbation/README.md))
- ⚛️ **mcp-quantum-celltype-fidelity** - Quantum computing-based cell type fidelity analysis using Qiskit - 56 tests ✅ ([README](mcp-quantum-celltype-fidelity/README.md))
- 🖼️ **mcp-deepcell** - DeepCell-TF cell segmentation on Cloud Run ☁️ ([README](mcp-deepcell/README.md))
- 🔬 **mcp-cell-classify** - Cell phenotype classification and multi-marker phenotyping ([README](mcp-cell-classify/README.md))
- 🖼️ **mcp-openimagedata** - Histology image processing: registration, feature extraction, MxIF compositing - 30 tests ✅ ([README](mcp-openimagedata/README.md))
- 🧬 **mcp-genomic-results** - Somatic variant/CNV parsing with clinical annotations and HRD scoring ([README](mcp-genomic-results/README.md))
- 🧬 **mcp-geodownload** - GEO/SRA dataset download, Entrez REST, expression matrices ([README](mcp-geodownload/README.md))
- 🎯 **mcp-opentargets** - Open Targets drug-target associations, disease ontology, GraphQL API ([README](mcp-opentargets/README.md))
- 🧫 **mcp-cibersortx** - CIBERSORTx immune deconvolution, LM22 signatures, job polling ([README](mcp-cibersortx/README.md))
- 💉 **mcp-neoantigen** - Neoantigen prediction, MHC binding, IEDB API, neoantigen burden scoring ([README](mcp-neoantigen/README.md))
- 📄 **mcp-patient-report** - Patient-facing PDF reports, plain-language summaries, clinician review gate ([README](mcp-patient-report/README.md))
- ❤️ **mcp-cardiometabolic** - CVD risk scoring, biomarker panels, lipid patterns, FH scoring, renal drug constraints, lipid treatment targets, post-COVID CV risk, PRS, APO risk - 82 tests ✅ ([README](mcp-cardiometabolic/README.md))

### 🎭 Development/Demo Servers
Mock implementations for workflow demonstration:
- 🎭 **mcp-mockepic** - Synthetic FHIR data (by design)
- 🧪 **mcp-mocktcga** - Mock TCGA cohort comparison ([README](mcp-mocktcga/README.md))

---

