# mcp-spatialtools: Spatial Transcriptomics Analysis

MCP server for comprehensive spatial transcriptomics data processing and analysis, including alignment, QC, batch correction, differential expression, pathway enrichment, and cell type deconvolution.

## Overview

`mcp-spatialtools` provides end-to-end spatial transcriptomics analysis through the Model Context Protocol (MCP). This server enables AI-driven orchestration of complex spatial analysis workflows for technologies like 10x Visium, Slide-seq, and MERFISH.

### Key Features

- 🧬 **STAR Alignment** - Align spatial FASTQ data to reference genomes
- ✅ **Quality Control** - Filter low-quality spots and genes
- 🧮 **Batch Correction** - ComBat batch effect removal
- 📊 **Differential Expression** - Statistical testing between regions/conditions
- 🧪 **Pathway Enrichment** - Gene set enrichment analysis (GO, KEGG, Hallmark)
- 🔬 **Cell Type Deconvolution** - Estimate cell type composition per spot
- 🗺️ **Spatial Autocorrelation** - Moran's I for spatial patterns
- 🔗 **Clinical Integration** - Bridge tool for patient→spatial data mapping

## GCP Cloud Run Deployment

**Production server available at:** https://mcp-spatialtools-ondu7mwjpa-uc.a.run.app

Use with Claude API (not Claude Desktop):
```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "What spatial transcriptomics tools are available?"
    }],
    mcp_servers=[{
        "type": "url",
        "url": "https://mcp-spatialtools-ondu7mwjpa-uc.a.run.app/sse",
        "name": "spatialtools",
    }],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "spatialtools"}],
    betas=["mcp-client-2025-11-20"]
)
```

See [GCP Integration Guide](../../docs/reference/testing/gcp-integration.md) for details.

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) STAR aligner for alignment functionality

> **Standard setup:** See [Server Installation Guide](../../docs/reference/shared/server-installation.md) for venv creation, pip install, and Claude Desktop config.

### Environment Variables

Create a `.env` file in the server directory:

```bash
# Required directories
SPATIAL_DATA_DIR=/path/to/spatial-mcp/data
SPATIAL_CACHE_DIR=/path/to/spatial-mcp/data/cache
SPATIAL_OUTPUT_DIR=/path/to/spatial-mcp/data/output

# Optional: STAR aligner path
STAR_PATH=/usr/local/bin/STAR
STAR_GENOME_INDEX=/path/to/reference/hg38_star_index

# Optional: Performance tuning
SPATIAL_TIMEOUT_SECONDS=600
SPATIAL_MAX_SPOTS=10000

# Development mode (uses mocks instead of real tools)
SPATIAL_DRY_RUN=true
```

> See [DRY_RUN Mode Guide](../../docs/reference/shared/dry-run-mode.md) for details on mock mode.

### Installing STAR (Optional)

For alignment functionality:

```bash
# Via conda (recommended)
conda install -c bioconda star

# Via homebrew (macOS)
brew install star

# Verify installation
STAR --version
```

See [INSTALL_STAR.md](INSTALL_STAR.md) for genome index setup.

## Usage

### Running the Server

**Standalone mode (stdio):**

```bash
python -m mcp_spatialtools
```

**With Claude Desktop:**

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "spatialtools": {
      "command": "/path/to/spatial-mcp/servers/mcp-spatialtools/venv/bin/python",
      "args": ["-m", "mcp_spatialtools"],
      "cwd": "/path/to/spatial-mcp/servers/mcp-spatialtools",
      "env": {
        "PYTHONPATH": "/path/to/spatial-mcp/servers/mcp-spatialtools/src",
        "SPATIAL_DATA_DIR": "/path/to/data/spatial",
        "SPATIAL_CACHE_DIR": "/path/to/data/cache",
        "SPATIAL_DRY_RUN": "false"
      }
    }
  }
}
```

**Important:**
- Use the full path to the venv Python executable
- Set `SPATIAL_DRY_RUN=false` for real analysis
- Claude Desktop uses STDIO transport (local only)

For GCP-deployed servers, use Claude API (see above).

For a complete working config with all servers, see [`docs/getting-started/desktop-configs/`](../../docs/getting-started/desktop-configs/).

## Available Tools

### 1. align_spatial_data

Align spatial transcriptomics FASTQ files using STAR aligner.

**Parameters:**
- `fastq_r1` (string): Path to Read 1 FASTQ file (spatial barcodes)
- `fastq_r2` (string): Path to Read 2 FASTQ file (cDNA)
- `reference_genome` (string): Path to STAR genome index directory
- `output_dir` (string): Directory for output files
- `threads` (integer, optional): Number of threads (default: 8)

**Returns:**
```json
{
  "alignment_file": "/output/Aligned.sortedByCoord.out.bam",
  "stats": {
    "total_reads": 50000000,
    "uniquely_mapped": 35000000,
    "uniquely_mapped_pct": 70.0,
    "multi_mapped": 5000000,
    "unmapped": 10000000
  }
}
```

**Example usage with Claude:**
```
Align my Visium spatial data using STAR:
- R1: /data/visium_spatial_R1.fastq.gz
- R2: /data/visium_cdna_R2.fastq.gz
- Genome: /reference/hg38_star_index
- Output: /analysis/alignment/
```

**Note:** Requires STAR aligner installed. Use DRY_RUN mode for testing without STAR.

### 2. filter_quality

Filter low-quality spots and genes based on QC metrics.

**Parameters:**
- `input_file` (string): Path to expression matrix (CSV/TSV)
- `output_dir` (string): Directory for filtered output
- `min_reads` (integer, optional): Minimum UMI count per spot (default: 100)
- `min_genes` (integer, optional): Minimum genes detected per spot (default: 50)
- `min_spots` (integer, optional): Minimum spots expressing a gene (default: 3)

**Returns:**
```json
{
  "filtered_file": "/output/filtered_expression.csv",
  "qc_stats": {
    "spots_before": 4992,
    "spots_after": 900,
    "spots_removed": 4092,
    "genes_before": 33538,
    "genes_after": 31,
    "genes_removed": 33507
  }
}
```

**Example usage with Claude:**
```
Filter my spatial data to remove low-quality spots:
- Input: /data/raw_expression.csv
- Keep spots with at least 200 UMIs and 100 genes
- Output to: /data/filtered/
```

### 3. split_by_region

Split spatial data into regions based on coordinates or annotations.

**Parameters:**
- `input_file` (string): Path to expression matrix
- `output_dir` (string): Directory for region-specific outputs
- `regions` (list, optional): List of region names to extract
- `coordinate_file` (string, optional): Path to spatial coordinates CSV
- `annotation_file` (string, optional): Path to region annotations CSV

**Returns:**
```json
{
  "region_files": {
    "tumor_core": "/output/tumor_core.csv",
    "tumor_margin": "/output/tumor_margin.csv",
    "immune_infiltrate": "/output/immune_infiltrate.csv"
  },
  "region_stats": {
    "tumor_core": {"spots": 219, "genes": 31},
    "tumor_margin": {"spots": 218, "genes": 31},
    "immune_infiltrate": {"spots": 214, "genes": 31}
  }
}
```

**Example usage with Claude:**
```
Split Patient-001 spatial data into three regions:
- Tumor core, tumor margin, and immune infiltrate
- Use annotations from: /data/PAT001-OVC-2025/visium_region_annotations.csv
```

### 4. calculate_spatial_autocorrelation

Calculate Moran's I spatial autocorrelation statistics for genes.

**Parameters:**
- `expression_file` (string): Path to expression matrix
- `genes` (list): List of gene names to analyze
- `coordinates_file` (string, optional): Path to spatial coordinates
- `method` (string, optional): Method - "morans_i" or "geary_c" (default: "morans_i")

**Returns:**
```json
{
  "results": [
    {
      "gene": "MUC16",
      "morans_i": 0.45,
      "p_value": 0.001,
      "z_score": 3.2,
      "significant": true,
      "pattern": "clustered"
    }
  ]
}
```

**Example usage with Claude:**
```
Calculate spatial autocorrelation for tumor markers:
- Genes: MUC16, TP53, BRCA1, CA125
- Data: /data/PAT001-OVC-2025/expression.csv
- Coordinates: /data/PAT001-OVC-2025/coordinates.csv
```

### 5. perform_differential_expression

Perform differential gene expression analysis between groups/regions.

**Parameters:**
- `expression_file` (string): Path to expression matrix
- `group1_samples` (list): Sample/spot IDs for group 1
- `group2_samples` (list): Sample/spot IDs for group 2
- `test_method` (string, optional): Statistical test - "wilcoxon", "ttest", or "deseq2" (default: "wilcoxon")
- `fdr_method` (string, optional): FDR correction - "fdr_bh" or "bonferroni" (default: "fdr_bh")

**Returns:**
```json
{
  "status": "success",
  "test_method": "wilcoxon",
  "total_genes_tested": 31,
  "significant_genes": 5,
  "top_upregulated": [
    {
      "gene": "FAP",
      "log2_fold_change": 2.34,
      "pvalue": 0.001,
      "qvalue": 0.031,
      "significant": true
    }
  ],
  "top_downregulated": [...]
}
```

**Example usage with Claude:**
```
Compare gene expression between tumor core and margin:
- Expression: /data/expression.csv
- Core spots: ["spot_001", "spot_002", ...]
- Margin spots: ["spot_300", "spot_301", ...]
- Use Wilcoxon rank-sum test with FDR correction
```

### 6. perform_batch_correction

Correct batch effects using ComBat or other methods.

**Parameters:**
- `expression_files` (list): List of expression file paths (one per batch)
- `batch_labels` (list): Batch identifiers (must match file list length)
- `output_file` (string): Path for corrected output
- `method` (string, optional): Method - "combat", "harmony", or "scanorama" (default: "combat")

**Returns:**
```json
{
  "corrected_file": "/output/batch_corrected.csv",
  "stats": {
    "batches_corrected": 3,
    "total_samples": 45,
    "variance_before": 0.85,
    "variance_after": 0.12,
    "variance_reduction_pct": 85.9
  }
}
```

**Example usage with Claude:**
```
Correct batch effects across 3 sequencing runs:
- Batch 1: /data/run1_expression.csv
- Batch 2: /data/run2_expression.csv
- Batch 3: /data/run3_expression.csv
- Use ComBat method and save to /data/corrected.csv
```

**Note:** ComBat is 95% implemented. Harmony/Scanorama are future enhancements.

### 7. perform_pathway_enrichment

Perform gene set enrichment analysis on differentially expressed genes.

**Parameters:**
- `gene_list` (list): List of gene symbols (e.g., from DE analysis)
- `background_genes` (list, optional): Background gene universe (default: all genes in database)
- `database` (string, optional): Database - "GO_BP", "KEGG", "Hallmark", or "Drug_Resistance" (default: "GO_BP")
- `p_value_cutoff` (float, optional): Significance threshold (default: 0.05)

**Returns:**
```json
{
  "enriched_pathways": [
    {
      "pathway_name": "DNA Repair",
      "p_value": 0.001,
      "q_value": 0.015,
      "genes_in_pathway": ["TP53", "BRCA1", "BRCA2"],
      "fold_enrichment": 3.45,
      "significant": true
    }
  ],
  "database": "GO_BP",
  "total_pathways_tested": 44,
  "significant_pathways": 3
}
```

**Example usage with Claude:**
```
Run pathway enrichment on upregulated genes from tumor margin:
- Genes: FAP, VIM, SNAI1, CD8A, CD3D (5 genes from DE analysis)
- Database: GO_BP (Biological Process)
- FDR cutoff: 0.05
```

**Available databases:**
- GO_BP: Gene Ontology Biological Process (10 curated pathways)
- KEGG: KEGG pathways (12 cancer-relevant pathways)
- Hallmark: MSigDB Hallmark gene sets (10 hallmark pathways)
- Drug_Resistance: Therapy resistance mechanisms (12 pathways)

Total: 44 curated pathways relevant to cancer biology

### 8. deconvolve_cell_types

Estimate cell type composition for each spot using signature genes.

**Parameters:**
- `expression_file` (string): Path to expression matrix
- `signatures` (dict, optional): Custom cell type signatures (default: ovarian cancer signatures)
- `normalize` (boolean, optional): Normalize expression before scoring (default: True)
- `include_spot_scores` (boolean, optional): Return per-spot scores (default: False)

**Returns:**
```json
{
  "status": "success",
  "spots_analyzed": 900,
  "cell_types": ["tumor_cells", "cd8_tcells", "endothelial_cells", ...],
  "summary_statistics": {
    "tumor_cells": {"mean": 0.12, "median": 0.09, "std": 0.45},
    "cd8_tcells": {"mean": 0.08, "median": 0.05, "std": 0.38}
  },
  "dominant_cell_type_distribution": {
    "tumor_cells": 181,
    "fibroblasts": 164,
    "endothelial_cells": 151
  }
}
```

**Example usage with Claude:**
```
Perform cell type deconvolution on Patient-001:
- Expression: /data/PAT001-OVC-2025/expression.csv
- Use ovarian cancer cell type signatures
- Return summary statistics only (not per-spot scores for efficiency)
```

**Built-in signatures (ovarian cancer):**
- Tumor cells: MUC16, PAX8, WT1, EPCAM
- CD8+ T-cells: CD8A, CD8B, GZMA
- CD4+ T-cells: CD4, IL7R, FOXP3
- Endothelial cells: PECAM1, VWF, CDH5
- Fibroblasts: COL1A1, FAP, DCN
- Mesothelial cells: MSLN, CALB2, KRT5
- Macrophages: CD68, CD163, MSR1
- B-cells: CD19, MS4A1

### 9. merge_tiles

Merge tiled spatial data from adjacent tissue sections.

**Parameters:**
- `tile_files` (list): List of expression file paths (one per tile)
- `output_file` (string): Path for merged output
- `overlap_resolution` (string, optional): How to handle overlaps - "average", "max", or "first" (default: "average")

**Returns:**
```json
{
  "merged_file": "/output/merged_expression.csv",
  "stats": {
    "tiles_merged": 4,
    "total_spots": 3996,
    "overlapping_spots": 96,
    "unique_spots": 3900
  }
}
```

**Example usage with Claude:**
```
Merge 4 adjacent Visium tiles into a single dataset:
- Tiles: [tile1.csv, tile2.csv, tile3.csv, tile4.csv]
- Handle overlaps by averaging expression values
- Output: /data/full_tissue_merged.csv
```

### 10. get_spatial_data_for_patient (Bridge Tool)

Retrieve spatial transcriptomics data linked to a patient's clinical record.

**Parameters:**
- `patient_id` (string): Patient identifier (e.g., "patient-001")
- `tissue_type` (string, optional): Tissue type - "tumor", "normal", or "metastasis" (default: "tumor")
- `include_clinical_context` (boolean, optional): Include clinical metadata (default: True)
- `conditions` (list, optional): Filter by conditions (e.g., ["ovarian cancer"])

**Returns:**
```json
{
  "patient_id": "patient-001",
  "spatial_dataset_id": "PAT001-OVC-2025",
  "expression_file": "/data/patient-data/PAT001-OVC-2025/spatial/visium_gene_expression.csv",
  "coordinates_file": "/data/patient-data/PAT001-OVC-2025/spatial/visium_spatial_coordinates.csv",
  "annotations_file": "/data/patient-data/PAT001-OVC-2025/spatial/visium_region_annotations.csv",
  "clinical_context": {
    "age": 57,
    "diagnosis": "Stage IV High-Grade Serous Ovarian Carcinoma",
    "treatment_status": "platinum-resistant"
  }
}
```

**Example usage with Claude:**
```
For Patient-001 with ovarian cancer, retrieve their spatial transcriptomics data.
Include clinical context to inform the analysis.
```

**Integration:** Works with `mcp-epic` server to link FHIR clinical data with spatial datasets.

---

## Visualization Tools

The following visualization tools generate publication-quality PNG images for spatial analysis results:

### 11. generate_spatial_heatmap

Generate spatial heatmaps showing gene expression overlaid on tissue coordinates.

**Parameters:**
- `expression_file` (string): Path to expression matrix CSV
- `coordinates_file` (string): Path to spatial coordinates CSV
- `genes` (list): List of gene names to visualize (max 6)
- `output_filename` (string, optional): Custom output filename
- `colormap` (string, optional): Matplotlib colormap (default: "viridis")

**Returns:**
```json
{
  "status": "success",
  "output_file": "/workspace/output/visualizations/spatial_heatmap_20250108_143022.png",
  "genes_plotted": ["MKI67", "PCNA", "CD8A", "CD68", "MUC16", "TP53"],
  "genes_not_found": [],
  "num_spots": 900,
  "description": "Spatial heatmap showing expression of 6 genes across tissue coordinates.",
  "visualization_type": "spatial_heatmap"
}
```

**Example usage with Claude:**
```
Generate spatial heatmaps for proliferation markers:
- Expression: /data/PAT001-OVC-2025/visium_gene_expression.csv
- Coordinates: /data/PAT001-OVC-2025/visium_spatial_coordinates.csv
- Genes: MKI67, PCNA, TOP2A, AURKA, CDK1, CCNB1
- Use "plasma" colormap
```

**Output:** Multi-panel figure with separate heatmap for each gene, showing spatial distribution across tissue.

### 12. generate_gene_expression_heatmap

Generate gene × region expression heatmap matrix.

**Parameters:**
- `expression_file` (string): Path to expression matrix CSV
- `regions_file` (string): Path to region annotations CSV
- `genes` (list): List of gene names to include
- `output_filename` (string, optional): Custom output filename
- `colormap` (string, optional): Seaborn colormap (default: "RdYlBu_r")

**Returns:**
```json
{
  "status": "success",
  "output_file": "/workspace/output/visualizations/gene_region_heatmap_20250108_143045.png",
  "genes_plotted": ["MKI67", "PCNA", "PIK3CA", "AKT1", "ABCB1", "CD3D", "CD8A", "CD68"],
  "genes_not_found": [],
  "regions": ["tumor_core", "tumor_proliferative", "tumor_interface", "stroma_immune", "stroma", "necrotic_hypoxic"],
  "num_spots": 900,
  "expression_matrix": {...},
  "description": "Gene expression heatmap showing 8 genes across 6 tissue regions with mean expression values.",
  "visualization_type": "gene_region_heatmap"
}
```

**Example usage with Claude:**
```
Create a heatmap showing key genes across tumor regions:
- Expression: /data/expression.csv
- Regions: /data/region_annotations.csv
- Genes: MKI67, PCNA, PIK3CA, AKT1, ABCB1, CD3D, CD8A, CD68
```

**Output:** Annotated heatmap with genes as rows, regions as columns, and mean expression values displayed.

### 13. generate_region_composition_chart

Generate bar chart showing spot counts per tissue region.

**Parameters:**
- `regions_file` (string): Path to region annotations CSV
- `output_filename` (string, optional): Custom output filename
- `colormap` (string, optional): Matplotlib colormap (default: "tab10")

**Returns:**
```json
{
  "status": "success",
  "output_file": "/workspace/output/visualizations/region_composition_20250108_143102.png",
  "region_counts": {
    "tumor_core": 69,
    "tumor_proliferative": 138,
    "tumor_interface": 200,
    "stroma_immune": 212,
    "stroma": 158,
    "necrotic_hypoxic": 123
  },
  "total_spots": 900,
  "num_regions": 6,
  "description": "Region composition showing 900 total spots across 6 regions.",
  "visualization_type": "region_composition_bar_chart"
}
```

**Example usage with Claude:**
```
Show the distribution of spots across tissue regions:
- Regions: /data/PAT001-OVC-2025/visium_region_annotations.csv
```

**Output:** Bar chart with region names on x-axis and spot counts on y-axis.

### 14. visualize_spatial_autocorrelation

Visualize Moran's I spatial autocorrelation statistics.

**Parameters:**
- `autocorrelation_results` (dict): Output from `calculate_spatial_autocorrelation` tool
- `output_filename` (string, optional): Custom output filename
- `top_n` (integer, optional): Show top N genes (default: 10)

**Returns:**
```json
{
  "status": "success",
  "output_file": "/workspace/output/visualizations/spatial_autocorr_20250108_143120.png",
  "genes_plotted": ["MUC16", "MKI67", "PCNA", "CD8A", "CD68", "PIK3CA"],
  "description": "Spatial autocorrelation (Moran's I) for 6 genes. Green bars indicate clustering, red indicate dispersion.",
  "visualization_type": "spatial_autocorrelation_bar_chart"
}
```

**Example usage with Claude:**
```
After running calculate_spatial_autocorrelation, visualize the results:
- Input: <results from previous autocorrelation analysis>
- Show top 10 genes
```

**Output:** Horizontal bar chart showing Moran's I values (green for positive/clustered, red for negative/dispersed).

---

### Visualization Workflow Example

**Complete workflow with visualizations:**

```
Claude, analyze Patient-001 spatial data and generate visualizations:

STEP 1: Load data
- Get spatial dataset for patient-001

STEP 2: Generate spatial heatmaps
- Genes: MKI67, PCNA, CD8A, CD68, MUC16, TP53
- Show expression across tissue coordinates

STEP 3: Calculate spatial autocorrelation
- Same genes as heatmaps
- Then visualize Moran's I results

STEP 4: Generate gene-region heatmap
- Show mean expression per region
- Include immune markers and proliferation markers

STEP 5: Show region composition
- Bar chart of spot distribution

This provides complete spatial analysis with publication-ready figures.
```

## Available Resources

### spatial://config

Get current server configuration and analysis parameters.

**Example:**
```
What are the current spatial analysis settings?
```

### spatial://example-data

Get information about example datasets and data format requirements.

**Example:**
```
What data formats does the spatial server expect?
```

## Data Format Requirements

### Expression Matrix (CSV/TSV)
```
Gene,spot_001,spot_002,spot_003,...
MUC16,123.4,234.5,345.6,...
TP53,456.7,567.8,678.9,...
BRCA1,89.0,90.1,101.2,...
```
- First column: Gene symbols
- Other columns: Expression values per spot (raw UMI counts or normalized)

### Spatial Coordinates (CSV)
```
spot_id,x,y
spot_001,1200,3400
spot_002,1250,3400
spot_003,1300,3400
```
- `spot_id`: Must match column names in expression matrix
- Coordinate columns are auto-detected (priority order):
  1. Visium pixel columns: `pxl_row_in_fullres`, `pxl_col_in_fullres`
  2. Named x/y columns: `x`, `y`, `x_coord`, `y_coord`, `spot_x`, `spot_y`
  3. Array columns: `array_row`, `array_col`
  4. Fallback: first two numeric columns

### Region Annotations (CSV)
```
spot_id,region
spot_001,tumor_core
spot_002,tumor_core
spot_003,tumor_margin
```
- `spot_id`: Must match expression matrix and coordinates
- `region`: Region label (e.g., "tumor_core", "tumor_margin", "immune_infiltrate")

## Example Workflows

### Complete Patient Analysis Workflow

**End-to-end precision medicine analysis:**

```
Claude, analyze spatial data for Patient-001 (ovarian cancer):

STEP 1: Clinical-Spatial Integration
- Get patient clinical data (epic server)
- Retrieve spatial dataset (bridge tool)

STEP 2: Quality Control
- Filter low-quality spots (min 200 UMIs, 100 genes)
- Check spatial patterns with Moran's I for tumor markers

STEP 3: Regional Analysis
- Split into tumor core, margin, and immune zones
- Perform differential expression between regions

STEP 4: Cell Type Deconvolution
- Estimate cell types per spot
- Quantify endothelial cells (bevacizumab targets)
- Assess CD8+ T-cell infiltration (immunotherapy potential)

STEP 5: Pathway Enrichment
- Run enrichment on upregulated genes from tumor margin
- Identify resistance mechanisms

STEP 6: Integrated Report
- Link spatial findings to clinical context
- Provide treatment recommendations
```

### Quick Cell Type Analysis

**Rapid cell type profiling:**

```
Perform cell type deconvolution on Patient-001:
- Expression: /data/PAT001-OVC-2025/expression.csv
- Use ovarian cancer signatures
- Return summary statistics

Focus on:
- Endothelial cells (bevacizumab targets)
- CD8+ T-cells (immunotherapy)
- Tumor purity
```

### Regional Comparison Workflow

**Compare tumor regions:**

```
Compare tumor core vs margin for Patient-001:

1. Split data by region
2. Run differential expression (Wilcoxon test)
3. Perform pathway enrichment on significant genes
4. Interpret results in clinical context
```

## Development

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=src/mcp_spatialtools --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_deconvolution.py -v
```

**Skip slow tests:**
```bash
pytest -m "not slow"
```

### Code Quality

**Format code:**
```bash
black src/ tests/
```

**Lint code:**
```bash
ruff check src/ tests/
```

**Type checking:**
```bash
mypy src/
```

## Architecture

### Implementation Status: 95% Real

- **align_spatial_data**: 95% real (STAR execution, log parsing, tested)
- **filter_quality**: 95% real (statistical filtering implemented)
- **split_by_region**: 95% real (coordinate-based splitting)
- **calculate_spatial_autocorrelation**: 95% real (Moran's I calculation)
- **perform_differential_expression**: 95% real (Wilcoxon/t-test implemented)
- **perform_batch_correction**: 95% real (ComBat implemented, tested)
- **perform_pathway_enrichment**: 95% real (Fisher's exact test, 44 curated pathways)
- **deconvolve_cell_types**: 95% real (signature scoring implemented)
- **merge_tiles**: 95% real (coordinate-based merging)
- **get_spatial_data_for_patient**: 95% real (file mapping bridge)

See [SERVER_IMPLEMENTATION_STATUS.md](SERVER_IMPLEMENTATION_STATUS.md) for details.

### Design Principles

1. **Clinical Integration** - Bridge tool links spatial data to patient records
2. **Token Efficiency** - Summary statistics by default, full data optional
3. **Reproducibility** - All parameters logged, deterministic results
4. **Comprehensive Validation** - All inputs validated before processing

### Directory Structure

```
mcp-spatialtools/
├── src/
│   └── mcp_spatialtools/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py              # MCP server entry point and tool wrappers
│       └── tools/                 # Implementation modules (refactored from server.py)
│           ├── __init__.py
│           ├── alignment.py       # STAR alignment
│           ├── analysis.py        # DE, batch correction, autocorrelation
│           ├── clinical_bridge.py # Patient-spatial data mapping
│           ├── deconvolution.py   # Cell type deconvolution
│           ├── enrichment.py      # Pathway enrichment (GO, KEGG, Hallmark)
│           ├── preprocessing.py   # QC filtering, region splitting, tile merging
│           └── visualization.py   # Heatmaps, charts, spatial plots
├── tests/
│   ├── conftest.py                # Pytest fixtures
│   ├── test_server.py             # Tool tests
│   ├── test_deconvolution.py      # Cell type tests
│   └── test_integration.py        # End-to-end workflow tests
├── pyproject.toml                 # Project configuration
├── README.md
└── SERVER_IMPLEMENTATION_STATUS.md
```

## Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SPATIAL_DATA_DIR` | `/workspace/data` | Directory for spatial datasets |
| `SPATIAL_CACHE_DIR` | `/workspace/cache` | Directory for cached files |
| `SPATIAL_OUTPUT_DIR` | `$SPATIAL_DATA_DIR/output` | Directory for visualization output |
| `STAR_PATH` | `STAR` | Path to STAR executable |
| `STAR_GENOME_INDEX` | `/reference/hg38_star_index` | STAR genome index directory |
| `SPATIAL_DRY_RUN` | `false` | Enable mock mode (no real tool calls) |
| `SPATIAL_LOG_LEVEL` | `INFO` | Logging level |
| `SPATIAL_TIMEOUT_SECONDS` | `600` | Default operation timeout |
| `SPATIAL_MAX_SPOTS` | `10000` | Maximum spots per analysis |

> See [DRY_RUN Mode Guide](../../docs/reference/shared/dry-run-mode.md) for details on mock mode.

## Troubleshooting

### Server won't start

- **Check Python version:** Must be 3.11+
- **Verify dependencies:** Run `pip install -e .`
- **Check environment variables:** Ensure directories exist

### Tools return errors

- **Enable dry-run mode:** Set `SPATIAL_DRY_RUN=true` for testing
- **Check file paths:** Ensure absolute paths are used
- **Review logs:** Check stderr output for details

### STAR alignment fails

- **Verify STAR installed:** Run `STAR --version`
- **Check genome index:** Ensure index exists at `STAR_GENOME_INDEX`
- **Use DRY_RUN mode:** Test without STAR for workflow validation
- **See:** [INSTALL_STAR.md](INSTALL_STAR.md) for installation guide

### Cell type deconvolution seems off

- **Check input normalization:** Expression should be log-normalized
- **Verify signatures:** Ensure gene names match expression matrix
- **Use custom signatures:** Provide tissue-specific signatures if available
- **Check spot quality:** Filter low-quality spots first

### Differential expression shows no significance

- **Check sample sizes:** Need sufficient spots per group (>20 recommended)
- **Verify biological variation:** Real differences may be small
- **Try different test:** Wilcoxon for non-normal, t-test for normal
- **Relax FDR:** Try q < 0.1 instead of 0.05

## License

See the main repository LICENSE file.

## Support

- **Issues:** https://github.com/lynnlangit/precision-medicine-mcp/issues
- **Documentation:** See main repository docs/
- **MCP Specification:** https://modelcontextprotocol.io/

## Related Servers

Part of the Precision Medicine MCP suite (demonstrated in [PatientOne](../../docs/reference/testing/patient-one/README.md) workflow):

- **mcp-epic** - Clinical EHR data (FHIR)
- **mcp-fgbio** - Genomic reference data and FASTQ validation
- **mcp-mocktcga** - Mock TCGA cancer genomics data
- **mcp-multiomics** - Multi-omics integration (RNA/protein/phospho)
- **mcp-deepcell** - Cell segmentation for imaging

---

**Built for the Precision Medicine MCP suite** - Enables AI-driven spatial transcriptomics analysis integrated with clinical data for personalized cancer treatment.
