# MCP-SpatialTools Quick Start Guide

Get started with spatial transcriptomics analysis in **5-10 minutes**.

---

## Prerequisites

- **Python:** ≥3.11
- **Operating System:** macOS or Linux
- **Disk Space:** 20GB minimum (100GB for STAR alignment)
- **RAM:** 16GB minimum (32GB+ for STAR alignment)

---

## 1. Installation (5 minutes)

### Install MCP-SpatialTools

```bash
# Clone repository
cd ~/Documents/GitHub
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp/servers/mcp-spatialtools

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Verify installation
python -c "from mcp_spatialtools import server; print('✅ Installation successful!')"
```

**Expected output:**
```
✅ Installation successful!
```

---

### Optional: Install STAR Aligner

**Only needed if you want to align raw FASTQ files. Skip if you have pre-aligned data.**

```bash
# Install STAR via conda (recommended)
conda install -c bioconda star

# Verify
STAR --version
# Expected: 2.7.11a or later
```

**Full STAR setup:** See `INSTALL_STAR.md` for genome index preparation.

---

## 2. Quick Test (2 minutes)

### Test with Patient-001 Synthetic Data

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run quick integration test
python -m pytest tests/test_complete_integration.py::TestDataIntegrity -v
```

**Expected output:**
```
tests/test_complete_integration.py::TestDataIntegrity::test_batch_correction_preserves_genes PASSED
tests/test_complete_integration.py::TestDataIntegrity::test_differential_expression_preserves_genes PASSED

==================== 2 passed in 0.15s ====================
```

---

## 3. Usage Examples

### Example 1: Batch Correction

**Use case:** Remove technical variation across multiple batches

```python
from mcp_spatialtools.server import perform_batch_correction
import asyncio

async def correct_batch_effects():
    result = await perform_batch_correction.fn(
        data_files=[
            "/path/to/batch1_expression.csv",
            "/path/to/batch2_expression.csv",
            "/path/to/batch3_expression.csv"
        ],
        batch_labels=["batch1", "batch2", "batch3"],
        parametric=True  # Use parametric ComBat (faster)
    )

    print(f"✅ Batch correction complete!")
    print(f"   Variance reduction: {result['variance_reduction']:.1%}")
    print(f"   Output file: {result['output_file']}")

# Run
asyncio.run(correct_batch_effects())
```

**Expected output:**
```
✅ Batch correction complete!
   Variance reduction: 22.4%
   Output file: /path/to/batch_corrected_expression.csv
```

---

### Example 2: Pathway Enrichment Analysis

**Use case:** Identify enriched biological pathways in differentially expressed genes

```python
from mcp_spatialtools.server import perform_pathway_enrichment
import asyncio

async def analyze_pathways():
    # Your differential expression results
    de_genes = [
        "TP53", "PIK3CA", "AKT1", "PTEN", "BRCA1",
        "HIF1A", "CA9", "VEGFA", "BCL2L1", "ABCB1"
    ]

    # All genes profiled in your experiment
    all_genes = de_genes + [
        "MYC", "KRAS", "EGFR", "ERBB2", "RB1",
        # ... (include all genes in your dataset)
    ]

    result = await perform_pathway_enrichment.fn(
        differential_genes=de_genes,
        all_genes=all_genes,
        fdr_threshold=0.05
    )

    print(f"✅ Pathway enrichment complete!")
    print(f"   Pathways tested: {result['num_pathways_tested']}")
    print(f"   Significant pathways: {result['num_significant_pathways']}")

    print("\nTop 5 enriched pathways:")
    for pathway in result['enriched_pathways'][:5]:
        print(f"  • {pathway['pathway_name']}")
        print(f"    Overlap: {pathway['overlap_count']}/{pathway['pathway_size']} genes")
        print(f"    Fold enrichment: {pathway['fold_enrichment']:.2f}x")
        print(f"    FDR: {pathway['fdr']:.2e}")
        print()

# Run
asyncio.run(analyze_pathways())
```

**Expected output:**
```
✅ Pathway enrichment complete!
   Pathways tested: 44
   Significant pathways: 5

Top 5 enriched pathways:
  • PI3K-Akt signaling pathway
    Overlap: 8/15 genes
    Fold enrichment: 5.33x
    FDR: 1.23e-04

  • Hypoxia response
    Overlap: 6/12 genes
    Fold enrichment: 5.00x
    FDR: 3.45e-04
  ...
```

---

### Example 3: Spatial Autocorrelation

**Use case:** Identify spatially variable genes (genes with non-random spatial patterns)

```python
from mcp_spatialtools.server import calculate_spatial_autocorrelation
import asyncio

async def find_spatial_genes():
    result = await calculate_spatial_autocorrelation.fn(
        expression_file="/path/to/visium_gene_expression.csv",
        coordinates_file="/path/to/visium_spatial_coordinates.csv",
        genes=["HIF1A", "CA9", "VEGFA", "Ki67", "CD8A"],
        method="morans_i",
        distance_threshold=1500.0  # Pixels (Visium spot spacing)
    )

    print(f"✅ Spatial autocorrelation complete!")
    print(f"   Method: {result['method']}")
    print(f"   Genes analyzed: {len(result['results'])}")

    print("\nSpatially variable genes (p < 0.05):")
    for gene_result in result['results']:
        if gene_result['p_value'] < 0.05:
            print(f"  • {gene_result['gene']}")
            print(f"    Moran's I: {gene_result['morans_i']:.4f}")
            print(f"    p-value: {gene_result['p_value']:.2e}")
            print()

# Run
asyncio.run(find_spatial_genes())
```

**Expected output:**
```
✅ Spatial autocorrelation complete!
   Method: morans_i
   Genes analyzed: 5

Spatially variable genes (p < 0.05):
  • HIF1A
    Moran's I: 0.6234
    p-value: 1.23e-08

  • CA9
    Moran's I: 0.5891
    p-value: 4.56e-07
  ...
```

---

### Example 4: STAR Alignment (Optional)

**Use case:** Align raw FASTQ files to reference genome

**Prerequisites:** STAR installed + genome index prepared (see `INSTALL_STAR.md`)

```python
from mcp_spatialtools.server import align_spatial_data
import asyncio

async def align_fastq():
    result = await align_spatial_data.fn(
        r1_fastq="/path/to/sample_R1.fastq.gz",
        r2_fastq="/path/to/sample_R2.fastq.gz",
        genome_index="/path/to/STAR_genome_index",  # e.g., ~/genome_indices/hg38/star
        output_dir="/path/to/output",
        threads=8  # Adjust based on your CPU
    )

    print(f"✅ Alignment complete!")
    print(f"   BAM file: {result['aligned_bam']}")
    print(f"   Total reads: {result['alignment_stats']['total_reads']:,}")
    print(f"   Uniquely mapped: {result['alignment_stats']['uniquely_mapped']:,}")
    print(f"   Alignment rate: {result['alignment_stats']['alignment_rate']:.1%}")

# Run
asyncio.run(align_fastq())
```

**Expected output:**
```
✅ Alignment complete!
   BAM file: /path/to/output/Aligned.sortedByCoord.out.bam
   Total reads: 50,000,000
   Uniquely mapped: 42,500,000
   Alignment rate: 92.5%
```

**Time:** 30-60 minutes for 50M reads on 8 cores

---

## 4. Working with Patient-001 Demo Data

### Load Demo Data

```python
from pathlib import Path
import pandas as pd

# Set data directory
data_dir = Path("/path/to/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial")

# Load expression data (genes × spots)
expr_file = data_dir / "visium_gene_expression.csv"
expr_df = pd.read_csv(expr_file, index_col=0)
expr_df = expr_df.T  # Transpose to genes × spots

print(f"Expression data: {expr_df.shape[0]} genes × {expr_df.shape[1]} spots")

# Load metadata
meta_file = data_dir / "visium_region_annotations.csv"
meta_df = pd.read_csv(meta_file)

print(f"Regions: {meta_df['region'].unique()}")
# Output: ['tumor_core', 'tumor_proliferative', 'tumor_interface',
#          'stroma', 'stroma_immune', 'necrotic_hypoxic']
```

---

### Run Complete Workflow

```bash
# Run full Patient-001 integration workflow
python test_patient001_complete_workflow.py
```

**What this does:**
1. Loads Patient-001 spatial transcriptomics data
2. Performs differential expression (tumor_core vs stroma)
3. Calculates spatial autocorrelation (Moran's I)
4. Performs cell type deconvolution
5. Generates clinical interpretation

**Expected time:** 2-3 minutes

---

## 5. Common Workflows

### Workflow 1: Pre-Aligned Data → Insights

**You have:** Expression matrix (CSV), spatial coordinates, metadata

**Steps:**
```
1. Load data (pandas)
2. Batch correction (if multiple batches)
3. Differential expression (compare groups)
4. Pathway enrichment (interpret DEGs)
5. Spatial autocorrelation (find spatial genes)
6. Cell type deconvolution (identify cell types)
```

**Tools:** `perform_batch_correction`, differential expression (Mann-Whitney U), `perform_pathway_enrichment`, `calculate_spatial_autocorrelation`

**Time:** 10-20 minutes

---

### Workflow 2: Raw FASTQ → Insights

**You have:** Raw sequencing files (FASTQ)

**Steps:**
```
1. STAR alignment (FASTQ → BAM) → 30-60 min
2. Generate expression matrix (BAM → CSV) → use Space Ranger or external tools
3. Follow Workflow 1 (Pre-Aligned Data → Insights)
```

**Tools:** `align_spatial_data` + external tools (Space Ranger, STARsolo)

**Time:** 1-2 hours

---

### Workflow 3: Multi-Batch Analysis

**You have:** Expression matrices from 3 different batches

**Steps:**
```
1. Batch correction (ComBat) → Remove technical variation
2. Differential expression → Find DEGs across conditions
3. Pathway enrichment → Interpret biological meaning
```

**Example:**
```python
# 1. Batch correction
batch_corrected = await perform_batch_correction.fn(
    data_files=["batch1.csv", "batch2.csv", "batch3.csv"],
    batch_labels=["batch1", "batch2", "batch3"]
)

# 2. Differential expression (use corrected data)
# ... perform Mann-Whitney U test on corrected_df

# 3. Pathway enrichment
enrichment = await perform_pathway_enrichment.fn(
    differential_genes=de_genes,
    all_genes=all_genes
)
```

---

## 6. Troubleshooting

### Issue: Import Error

**Error:** `ModuleNotFoundError: No module named 'mcp_spatialtools'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall
pip install -e .
```

---

### Issue: STAR Not Found

**Error:** `FileNotFoundError: STAR executable not found`

**Solution:**
```bash
# Install STAR
conda install -c bioconda star

# Verify
which STAR
# /opt/homebrew/bin/STAR

# Set STAR path (if needed)
export STAR_PATH=/path/to/STAR
```

---

### Issue: Out of Memory

**Error:** `MemoryError` or `not enough memory for genome generation`

**Solution:**
- **STAR alignment:** Use smaller genome index or reduce `--genomeSAindexNbases`
- **Batch correction:** Reduce number of batches or use non-parametric mode
- **Upgrade RAM:** Minimum 16GB, recommended 32GB+

---

### Issue: Slow Performance

**Symptoms:** Analysis takes >30 minutes for 900 spots

**Solution:**
- **Check CPU usage:** Use `top` or Activity Monitor
- **Increase threads:** For STAR alignment, use `--runThreadN 8` (or more)
- **Optimize data:** Filter genes to reduce matrix size

---

## 7. Next Steps

### Learn More

- **SERVER_IMPLEMENTATION_STATUS.md** - Detailed implementation status (95% real)
- **INSTALL_STAR.md** - Complete STAR installation guide
- **COST_ANALYSIS.md** - Performance and cost analysis
- **Patient-001 Manual Tests** - Complete workflow examples

### Test Your Data

```python
# Adapt Example 2 (Pathway Enrichment) to your data:
1. Replace `de_genes` with your differentially expressed genes
2. Replace `all_genes` with all genes in your experiment
3. Run pathway enrichment

# Expected time: <1 second for 31 genes, <10 seconds for 1000 genes
```

### Integrate with Claude Desktop

1. Add `mcp-spatialtools` to Claude Desktop config
2. Use natural language to request analysis:
   - "Perform batch correction on these 3 files"
   - "Find enriched pathways in these differentially expressed genes"
   - "Calculate spatial autocorrelation for HIF1A and CA9"

### Scale Up

- **10x Genomics Visium:** ~5,000 spots → 2-5 minutes (batch correction + DE)
- **High-resolution spatial:** ~50,000 spots → 10-30 minutes
- **Multi-patient cohort:** Use batch processing scripts

---

## 8. Getting Help

### Documentation

- **Main README:** `../../README.md`
- **Architecture:** `../../docs/architecture/spatial/README.md`
- **Manual Testing Guide:** `../../manual_testing/PatientOne-OvarianCancer/README.md`

### Issues & Support

- **GitHub Issues:** https://github.com/lynnlangit/precision-medicine-mcp/issues
- **Discussions:** https://github.com/lynnlangit/precision-medicine-mcp/discussions

### Example Datasets

- **Patient-001:** `/data/patient-data/PAT001-OVC-2025/`
  - Clinical data, genomics, multiomics, spatial, imaging
  - 100% synthetic, safe for testing

---

## Quick Reference

### Commands

```bash
# Install
pip install -e .

# Test
pytest tests/ -v

# Run Patient-001 workflow
python test_patient001_complete_workflow.py

# Install STAR
conda install -c bioconda star
```

### File Formats

| Format | Example | Tool |
|--------|---------|------|
| Expression (CSV) | `visium_gene_expression.csv` | Batch correction, DE |
| Coordinates (CSV) | `visium_spatial_coordinates.csv` | Spatial autocorrelation |
| FASTQ (gzipped) | `sample_R1.fastq.gz` | STAR alignment |
| VCF | `somatic_variants.vcf` | Genomic analysis (other servers) |

### Key Functions

| Function | Use Case | Time |
|----------|----------|------|
| `align_spatial_data` | FASTQ → BAM | 30-60 min |
| `perform_batch_correction` | Remove batch effects | 10-30 sec |
| `perform_pathway_enrichment` | Find enriched pathways | <1 sec |
| `calculate_spatial_autocorrelation` | Find spatial genes | 2-5 min |

---

**Status:** Production-ready for research use ✅
**Implementation:** 95% real algorithms
