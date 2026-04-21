# PAT001-OVC-2025: Synthetic Patient Data

## Overview

This directory contains **100% synthetic patient data** created for demonstration and testing purposes. The data represents a realistic but completely fabricated Stage IV High-Grade Serous Ovarian Carcinoma (HGSOC) patient case.

**Patient:** Sarah Anderson (synthetic) — Stage IV HGSOC, Platinum-Resistant
**Purpose:** Demonstrate precision medicine MCP server workflows
**Full profile:** See [PatientOne Profile](../../../docs/reference/shared/patientone-profile.md)

---

## Data Origin & Creation

### ⚠️ CRITICAL: ALL DATA IS SYNTHETIC

**This is NOT real patient data.** All files were artificially generated using:

1. **Statistical models** - Random number generators with clinically plausible distributions
2. **Expert knowledge** - Curated to reflect realistic ovarian cancer biology
3. **Published literature** - Based on TCGA ovarian cancer studies and clinical trial data
4. **No PHI/PII** - Contains zero protected health information or personally identifiable information

**Source:** Created by the Precision Medicine MCP development team for demonstration purposes.

---

## Data Modalities (5 types, 20 files)

### 1. Clinical Data (`clinical/`)

| File | Size | Description | Source |
|------|------|-------------|--------|
| `patient_demographics.json` | 4.7 KB | Patient demographics, stage, diagnosis, BRCA1 status | Synthetic |
| `lab_results.json` | 6.0 KB | CA-125 tumor marker trajectory and lab results | Modeled after clinical patterns |

**Generation method:**
- Demographics: Randomly generated name, age, dates
- CA-125 values: Gaussian noise around typical platinum-resistant trajectory

---

### 2. Genomic Data (`genomics/`)

| File | Size | Description | Source |
|------|------|-------------|--------|
| `somatic_variants.vcf` | 2.3 KB | Somatic mutations (TP53, PIK3CA, PTEN) | Based on TCGA-OV data |
| `copy_number_results.cns` | 1.0 KB | CNVkit segment results (amplifications/deletions) | Synthetic CNVkit output |

**Generation method:**
- Selected common ovarian cancer driver mutations from TCGA
- VCF format with realistic variant quality scores
- Germline BRCA1 mutation added to simulate HRD-positive phenotype
- CNVkit .cns file with MYC/CCNE1/AKT2 amplifications and RB1/CDKN2A/PTEN deletions

**Key mutations (realistic for HGSOC):**
- TP53 R175H (missense, chr17:7577538)
- PIK3CA E545K (missense, chr3:178936091)
- PTEN LOH (loss of heterozygosity, chr10)
- BRCA1 germline (c.5266dupC, pathogenic)

---

### 3. Multi-Omics Data (`multiomics/`)

#### Demonstration Data (Simplified PDX Model)

| File | Size | Description | Source |
|------|------|-------------|--------|
| `pdx_rna_seq.csv` | 279 KB | RNA-seq for 15 PDX samples | Synthetic |
| `pdx_proteomics.csv` | 140 KB | Proteomics for 15 PDX samples | Synthetic |
| `pdx_phosphoproteomics.csv` | 85 KB | Phosphoproteomics for 15 PDX samples | Synthetic |
| `sample_metadata.csv` | 799 B | Sample annotations (resistant vs sensitive) | Synthetic |

**Demonstration specifications:**
- 15 PDX samples (simplified comparative study)
- Pre-processed counts matrices (not raw files)
- Total size: ~505 KB

#### Production Data (Realistic Per-Patient)

**Typical hospital multi-omics dataset:**
- **RNA-seq:** ~2 GB raw FASTQ, ~500 MB aligned BAM, ~5-10 MB counts
- **Proteomics:** ~500 MB mass spec raw files
- **Phosphoproteomics:** ~200 MB mass spec raw files
- **Total per patient:** ~2.7 GB (raw files), ~15-20 MB (processed matrices)

**Generation method (demonstration):**
- Random sampling from log-normal distributions
- Resistant samples: Elevated PI3K/AKT/mTOR pathway genes
- Sensitive samples: Lower PI3K/AKT activation
- Noise added to simulate biological variability

**Simulated biology:**
- 7 resistant samples (high PIK3CA, AKT1, MTOR, ABCB1)
- 8 sensitive samples (lower pathway activation)
- Fold-changes calibrated to published PDX resistance studies

---

### 4. Spatial Transcriptomics (`spatial/`)

#### Demonstration Data (Simplified)

| File | Size | Description | Source |
|------|------|-------------|--------|
| `visium_gene_expression.csv` | 117 KB | Gene expression (31 genes × 900 spots) | Synthetic |
| `visium_spatial_coordinates.csv` | 34 KB | Spatial coordinates for 900 spots | Synthetic |
| `visium_region_annotations.csv` | 18 KB | Tissue region annotations (6 regions) | Synthetic |
| `filtered/visium_gene_expression_filtered.csv` | 146 KB | Filtered expression matrix | Synthetic |

**Demonstration specifications:**
- 900 spots (simplified from typical 3,000-5,000)
- 31 curated genes (simplified from typical 18,000-30,000)
- Total size: ~315 KB

#### Production Data (Realistic Visium)

**Typical hospital Visium dataset:**
- **Spots:** 3,000-5,000 per tissue section
- **Genes:** 18,000-30,000 (whole transcriptome)
- **File size:** 100-500 MB per patient (HDF5 feature-barcode matrix)
- **Histology image:** 500 MB - 1 GB (full resolution H&E)

**Generation method (demonstration):**
- Hexagonal Visium array layout (900 spots)
- 31 curated cancer-related genes
- Spatial patterns using Gaussian random fields:
  - Tumor core: High proliferation (Ki67, PCNA, TOP2A)
  - Tumor-stroma interface: Immune markers (CD3D, CD8A)
  - Necrotic regions: Hypoxia markers (HIF1A, CA9, VEGFA)
  - Stroma: Fibroblast markers (COL1A1, FAP, ACTA2)

**Tissue regions simulated (6):**
1. `tumor_core` - Central tumor, high proliferation
2. `tumor_proliferative` - Actively dividing tumor cells
3. `tumor_interface` - Invasion front
4. `stroma` - Fibroblast-rich connective tissue
5. `stroma_immune` - Immune infiltration
6. `necrotic_hypoxic` - Oxygen-deprived regions

**Genes profiled (31):**
- Proliferation: Ki67, PCNA, TOP2A, MYC
- Tumor suppressors: TP53, PTEN
- Oncogenes: PIK3CA, AKT1, MTOR
- Resistance: ABCB1 (MDR1), BCL2L1
- Hypoxia: HIF1A, CA9, VEGFA
- Immune: CD3D, CD8A, CD4, FOXP3, CD68
- Stromal: COL1A1, COL3A1, ACTA2, FAP
- Epithelial: EPCAM, KRT8, KRT18

---

### 5. Imaging Data (`imaging/`)

| File | Size | Description | Source |
|------|------|-------------|--------|
| `PAT001_tumor_HE_20x.tiff` | 300 KB | H&E histology 20× magnification | Synthetic placeholder |
| `PAT001_tumor_IF_DAPI.tiff` | 300 KB | Nuclear staining (DAPI) | Synthetic placeholder |
| `PAT001_tumor_IF_CD3.tiff` | 300 KB | T cell marker (CD3) | Synthetic placeholder |
| `PAT001_tumor_IF_CD8.tiff` | 300 KB | Cytotoxic T cell marker (CD8) | Synthetic placeholder |
| `PAT001_tumor_IF_KI67.tiff` | 300 KB | Proliferation marker (Ki67) | Synthetic placeholder |
| `PAT001_tumor_IF_PanCK.tiff` | 300 KB | Epithelial marker (PanCK) | Synthetic placeholder |
| `PAT001_tumor_multiplex_IF_TP53_KI67_DAPI.tiff` | 300 KB | Multiplex IF (TP53/Ki67/DAPI) | Synthetic placeholder |

**Note:** Image files are placeholder TIFFs. In DRY_RUN mode, MCP servers return synthetic segmentation/analysis results without processing actual images.

---

## Data Quality & Realism

### Realistic Features ✅

1. **Clinically plausible mutations** - Common HGSOC drivers (TP53, PIK3CA, BRCA1)
2. **Biologically coherent** - Resistant samples show expected pathway activation
3. **Spatial organization** - Tumor heterogeneity and microenvironment structure
4. **Temporal dynamics** - CA-125 trajectory matches platinum-resistant pattern

### Synthetic Limitations ❌

1. **No batch effects** - Real data would have technical variation
2. **Simplified biology** - Real tumors have >20,000 genes, not 31
3. **Idealized spatial patterns** - Real tissue is more heterogeneous
4. **No sequencing errors** - Real VCF would have quality issues
5. **Perfect correlations** - Real multi-omics has more noise

---

## Intended Use Cases

### ✅ Appropriate Uses

- **Workflow development** - Test MCP server integration
- **CI/CD testing** - Automated pipeline validation
- **Demonstration** - Show capabilities to stakeholders
- **Education** - Teach precision medicine concepts
- **Software testing** - Verify analysis algorithms

### ❌ Inappropriate Uses

- **Clinical decision-making** - NOT real patient data
- **Publications** - Cannot be cited as real data
- **Regulatory submissions** - Not suitable for FDA/EMA
- **Benchmarking** - Use established datasets instead
- **Training ML models** - Will not generalize to real data

---

## Data License & Attribution

**License:** Apache 2.0 (same as repository)

**Attribution:** If using this synthetic dataset in presentations or educational materials, please cite:

```
Precision Medicine MCP Synthetic Patient Dataset (PAT001-OVC-2025)
Generated for demonstration purposes
https://github.com/lynnlangit/precision-medicine-mcp
2025-12
```

---

## Real Data Alternatives

For **actual** ovarian cancer datasets, use these public resources:

### Genomics
- **TCGA-OV** - The Cancer Genome Atlas Ovarian Cancer
  - https://portal.gdc.cancer.gov/projects/TCGA-OV
  - 489 patients, WGS/RNA-seq/clinical
  - Free, public access via GDC API

### Spatial Transcriptomics
- **10x Genomics Public Datasets**
  - https://www.10xgenomics.com/datasets
  - Human ovarian cancer samples
  - Visium platform, download FASTQ/BAM

### Multi-Omics
- **CPTAC Ovarian Cancer**
  - https://proteomics.cancer.gov/programs/cptac
  - Proteomics + genomics + phosphoproteomics
  - 174 HGSOC samples

### Imaging
- **The Cancer Imaging Archive (TCIA)**
  - https://www.cancerimagingarchive.net/
  - H&E, CT, MRI for ovarian cancer
  - Free download with registration

---

## Technical Details

### File Formats

- **JSON** - Clinical demographics (RFC 8259 compliant)
- **CSV** - Tabular data (comma-delimited, UTF-8)
- **VCF** - Variant Call Format v4.2 (SAMtools spec)
- **CNS** - CNVkit segment format (TSV with log2 ratios and copy number calls)
- **TIFF** - Tagged Image File Format (16-bit grayscale)

### Data Size

#### Demonstration Data (This Synthetic Dataset)

**Total:** ~4.9 MB uncompressed
- Clinical: 10.7 KB
- Genomics: 2.3 KB
- Multi-omics: 505 KB (15 PDX samples, simplified)
- Spatial: 315 KB (900 spots × 31 genes)
- Imaging: ~2.1 MB (placeholders)

#### Production Data (Realistic Hospital Volumes)

**Total per patient:** ~3-8 GB uncompressed

| Modality | Demonstration | Production Reality | Notes |
|----------|--------------|-------------------|-------|
| **Clinical** | <1 KB | <1 KB | FHIR JSON, minimal |
| **Genomics (VCF)** | 2.3 KB | 50-500 KB | WGS VCF larger, WES similar |
| **Multi-omics** | 505 KB | **2.7 GB** | See breakdown below |
| **Spatial** | 315 KB | **100-500 MB** | See breakdown below |
| **Imaging** | 4.1 MB | **500 MB - 2 GB** | Full resolution histology |

**Multi-omics Breakdown (Production):**
- RNA-seq (raw FASTQ): ~2 GB per sample
- RNA-seq (aligned BAM): ~500 MB per sample
- RNA-seq (counts matrix): ~5-10 MB
- Proteomics: ~500 MB (mass spec raw files)
- Phosphoproteomics: ~200 MB (mass spec raw files)
- **Total multi-omics:** ~2.7 GB per patient

**Spatial Transcriptomics Breakdown (Production):**
- **Visium standard:** 3,000-5,000 spots × 18,000-30,000 genes
- Raw FASTQ: ~10-30 GB (not stored long-term)
- Aligned BAM: ~2-5 GB
- Feature-barcode matrix: ~100-500 MB (HDF5 format)
- Spatial coordinates: ~100 KB
- Histology image (H&E): ~500 MB - 1 GB (full resolution)
- **Total spatial (processed):** ~100-500 MB per patient

**Cost Implications:**
- **Storage:** 100 patients × 3-8 GB = **300 GB - 800 GB** total
- **Processing:** Larger files = longer compute time and higher Cloud Run costs
- **Transfer:** Network egress costs for GCS → Cloud Run data movement

### Checksums

For data integrity verification:
```bash
cd /path/to/spatial-mcp/data/patient-data/PAT001-OVC-2025
find . -type f -exec sha256sum {} \; > checksums.txt
```

---

## Related Documentation

- **PatientOne Test Prompts:** [Test prompts](../../../docs/reference/testing/patient-one/test-prompts/)
- **Data Modes Guide:** [DRY_RUN vs synthetic data](../../../docs/reference/testing/patient-one/data-modes-guide.md)
- **PatientOne Profile:** [Clinical profile](../../../docs/reference/shared/patientone-profile.md)

---

**Last Updated:** 2026-02 | **Version:** 1.0 | **Status:** 100% Synthetic — Research/Demo Only
