# Full PatientOne Demo

> **Complete end-to-end demonstration of the Precision Medicine MCP Platform**
> **Stage IV High-Grade Serous Ovarian Cancer case study**

---

## Overview

This demo showcases the full capabilities of the platform using **PatientOne** - a synthetic Stage IV ovarian cancer patient with comprehensive multi-modal data:

- 📋 **Clinical data** (Epic FHIR)
- 🧬 **Genomic data** (VCF, FASTQ)
- 🔬 **Multi-omics** (RNA, Protein, Phosphoproteomics)
- 📍 **Spatial transcriptomics** (10x Visium)
- 🖼️ **Imaging** (H&E, MxIF)
- 📥 **External data** (GEO/SRA datasets)
- 🧫 **Immune deconvolution** (CIBERSORTx)
- 💊 **Drug-target analysis** (Open Targets)
- 🎯 **Neoantigen prediction** (HLA binding, antigen presentation)

**Time to complete:** 25-35 minutes
**Prerequisites:** Claude Desktop with MCP servers configured
**Data:** 100% synthetic (safe to use anywhere)

---

## Quick Links

### 🎬 Video Demo
- **[5-Minute Overview Video →](https://www.youtube.com/watch?v=LUldOHHX5Yo)** - Watch the full analysis

### 📖 Complete Documentation
- **[PatientOne Scenario README →](../reference/testing/patient-one/README.md)** - Full case study, architecture, workflow diagrams
- **[Data Modes Guide →](../reference/testing/patient-one/data-modes-guide.md)** - DRY_RUN vs Actual Data modes

### 📝 Test Prompts
- **[Clinical & Genomic Prompts →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-1-clinical-genomic.md)**
- **[Multi-omics Prompts →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-2-multiomics-enhanced.md)**
- **[Spatial Analysis Prompts →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-3-spatial.md)**
- **[Imaging Prompts →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-4-imaging.md)**
- **[Integration Prompts →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-5-integration.md)**
- **[E2E Test Prompt →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-7-e2e-claude-desktop.md)**
- **[Full Platform E2E (all 18 servers) →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-10-e2e-full-platform.md)**

---

## Demo Pathways

### Pathway 1: Quick Clinical Overview (5 minutes)
**Goal:** Understand PatientOne's clinical context and genomic profile

1. **Get clinical summary:**
   ```
   Using the mockepic server, give me a summary of PAT001-OVC-2025's
   clinical history, current medications, and treatment timeline.
   ```

2. **Identify genomic variants:**
   ```
   Load PAT001-OVC-2025 genomic data and identify pathogenic variants
   associated with ovarian cancer or treatment resistance.
   ```

**Expected output:** Clinical timeline, current treatment status, key genomic alterations

**Servers used:** `mcp-mockepic`, `mcp-fgbio`

---

### Pathway 2: Multi-Omics Integration (15 minutes)
**Goal:** Integrate RNA, protein, and phosphoproteomics to find therapeutic targets

1. **Load and validate data:**
   ```
   Load PAT001-OVC-2025 multi-omics data (RNA, protein, phospho)
   and show data quality metrics.
   ```

2. **Run Stouffer meta-analysis:**
   ```
   Run Stouffer meta-analysis across all three modalities to identify
   the most consistently dysregulated genes/proteins.
   ```

3. **Pathway enrichment:**
   ```
   Perform pathway enrichment on the top 50 hits from the Stouffer analysis.
   Focus on druggable pathways.
   ```

**Expected output:** Ranked list of dysregulated genes, enriched pathways, drug targets

**Servers used:** `mcp-multiomics`, `mcp-fgbio`

---

### Pathway 3: Spatial Transcriptomics (15 minutes)
**Goal:** Analyze tumor microenvironment and spatial heterogeneity

1. **Load spatial data:**
   ```
   Load PAT001-OVC-2025 Visium spatial transcriptomics data and show
   spatial regions (tumor, stroma, immune).
   ```

2. **Spatial differential expression:**
   ```
   Run spatial differential expression analysis comparing tumor regions
   to stromal regions.
   ```

3. **Spatial pathway enrichment:**
   ```
   Perform pathway enrichment on spatially variable genes. Identify
   pathways enriched in tumor vs immune-infiltrated regions.
   ```

**Expected output:** Spatial gene expression maps, region-specific pathways, immune signatures

**Servers used:** `mcp-spatialtools`, `mcp-fgbio`

---

### Pathway 4: Full Multi-Modal Analysis (35 minutes)
**Goal:** Complete precision medicine analysis integrating all modalities

**See:** [E2E Test Prompt →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-7-e2e-claude-desktop.md)

This workflow demonstrates:
- Clinical context extraction
- Genomic variant interpretation
- Multi-omics integration (Stouffer meta-analysis)
- Spatial transcriptomics analysis
- Treatment target prioritization
- Comprehensive patient report generation

---

### Pathway 5: Full Platform HGSOC Immunotherapy Analysis (45-60 minutes)
**Goal:** End-to-end analysis using all 18 servers — external data, immune profiling, drug targets, neoantigens

**See:** [Full Platform E2E Test →](../reference/testing/patient-one/test-prompts/DRY_RUN/test-10-e2e-full-platform.md)

This workflow demonstrates:
- Everything in Pathway 4, plus:
- GEO dataset search for comparable ovarian cancer cohorts
- Open Targets drug-target association lookup (VEGFA, BRCA1, TP53)
- CIBERSORTx immune cell deconvolution
- Neoantigen prediction and HLA binding analysis
- Antigen presentation pathway scoring

**Servers used:** All 18 internal MCP servers

---

## Data Modes

The platform supports three data modes for testing:

| Mode | Description | Use Case | Cost |
|------|-------------|----------|------|
| **DRY_RUN** | No real computation, returns mock schemas | Quick testing, CI/CD | Free |
| **MOCK** | Pre-computed results from cache | Demos, training | Free |
| **FULL** | Real computation on synthetic data | Validation, development | Low per-patient compute cost ([Cost Analysis](../reference/shared/cost-analysis.md)) |

**For demos, use MOCK mode** to show real results without compute costs.

**See:** [Data Modes Guide →](../reference/testing/patient-one/data-modes-guide.md)

---

## Expected Results

### Key Findings from PatientOne Analysis

1. **Genomic Alterations:**
   - TP53 R273H mutation (platinum resistance)
   - BRCA1 loss of heterozygosity
   - PI3K/AKT pathway activation

2. **Multi-Omics Integration:**
   - DNA repair pathway dysregulation (KEGG pathway enrichment p < 0.001)
   - Upregulated kinases: MAPK1, AKT1, mTOR
   - Downregulated: BRCA1, PTEN, ATM

3. **Spatial Transcriptomics:**
   - Tumor regions: High proliferation markers (MKI67, TOP2A)
   - Stromal regions: ECM remodeling, CAF signatures
   - Immune-infiltrated regions: T-cell exhaustion markers (PDCD1, CTLA4)

4. **Treatment Recommendations:**
   - Consider PARP inhibitors (given BRCA1 loss)
   - PI3K/AKT/mTOR inhibitors for pathway activation
   - Immune checkpoint blockade for exhausted T-cell populations

---

## Troubleshooting

### Servers not responding
```
Check server status:
  docs/reference/shared/server-registry.md

Verify Claude Desktop MCP configuration:
  docs/getting-started/installation.md
```

### Data not loading
```
Confirm you're using the correct patient ID:
  PAT001-OVC-2025 (not PatientOne or patient-001)

Check data mode:
  Use MOCK mode for demos (no computation required)
```

### Unexpected results
```
Compare with expected outputs:
  docs/testing/patient-one/test-prompts/

Each prompt file includes expected results and validation criteria
```

---

## Next Steps

After completing the demo:

1. **For Funders:** See [ROI Analysis →](../for-funders/ROI_ANALYSIS.md)
2. **For Hospital IT:** See [Deployment Checklist →](../for-hospitals/DEPLOYMENT_CHECKLIST.md)
3. **For Developers:** See [Architecture Guide →](../for-developers/ARCHITECTURE.md)
4. **For Researchers:** See [Analysis Workflows →](../for-researchers/README.md)

---

## Questions?

- **Technical issues:** See [README.md](../../README.md) for GitHub issues
- **Deployment questions:** See [Hospital Deployment Guide](../for-hospitals/README.md)
- **Funding inquiries:** See [FUNDING.md](../for-funders/FUNDING.md)

---

**Last Updated:** 2026-03-09
