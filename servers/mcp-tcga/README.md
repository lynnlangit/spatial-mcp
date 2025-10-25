# mcp-tcga: TCGA Cancer Genomics Data Integration

MCP server providing access to The Cancer Genome Atlas (TCGA) datasets for cancer genomics analysis and spatial transcriptomics comparison.

## Overview

This server enables:
- **Cohort Discovery**: Search 33 TCGA cancer cohorts by type and tissue
- **Expression Data**: Retrieve gene expression for comparison with spatial data
- **Statistical Comparison**: Compare your samples to TCGA population statistics
- **Survival Analysis**: Correlate gene expression with clinical outcomes
- **Mutation Data**: Query somatic mutation frequencies

## Tools

### 1. query_tcga_cohorts

Search TCGA datasets by cancer type and tissue.

**Parameters:**
- `cancer_type` (optional): TCGA code (e.g., BRCA, LUAD, COAD)
- `tissue_type` (optional): primary_tumor, normal, metastatic
- `min_samples`: Minimum samples required (default: 10)

**Returns:**
- Matching cohorts with sample counts
- Available data types
- GDC portal URLs

**Example:**
```python
result = await query_tcga_cohorts(
    cancer_type="BRCA",
    tissue_type="primary_tumor",
    min_samples=100
)
# Returns: BRCA cohort with 1097 tumor samples
```

### 2. fetch_expression_data

Download gene expression data from TCGA cohorts.

**Parameters:**
- `cohort`: TCGA cohort code (e.g., BRCA)
- `genes`: List of gene symbols
- `tissue_type`: Sample type (default: primary_tumor)
- `normalization`: TPM, FPKM, or counts (default: TPM)

**Returns:**
- Expression matrix for requested genes
- Sample identifiers
- Sample metadata

**Example:**
```python
result = await fetch_expression_data(
    cohort="BRCA",
    genes=["EPCAM", "KRT19", "VIM"],
    tissue_type="primary_tumor",
    normalization="TPM"
)
# Returns: Expression data for 3 genes across 100+ samples
```

### 3. compare_to_cohort

Compare sample gene expression to TCGA cohort statistics.

**Parameters:**
- `sample_expression`: Dict of gene -> expression value
- `cohort`: TCGA cohort for comparison
- `genes`: Genes to compare
- `statistical_test`: t_test, wilcoxon, or z_score (default: t_test)

**Returns:**
- Z-scores and percentiles
- P-values for statistical significance
- Interpretation (higher/lower/similar)

**Example:**
```python
result = await compare_to_cohort(
    sample_expression={"EPCAM": 2500.0, "VIM": 800.0},
    cohort="BRCA",
    genes=["EPCAM", "VIM"],
    statistical_test="z_score"
)
# Returns: EPCAM is at 85th percentile (higher than average)
```

### 4. get_survival_data

Retrieve survival data correlated with gene expression.

**Parameters:**
- `cohort`: TCGA cohort code
- `gene`: Gene symbol for correlation
- `expression_threshold` (optional): Split into high/low groups
- `survival_type`: overall, progression_free, disease_specific

**Returns:**
- Median survival times
- 5-year survival rates
- Log-rank p-values and hazard ratios
- Kaplan-Meier curve data

**Example:**
```python
result = await get_survival_data(
    cohort="BRCA",
    gene="TP53",
    expression_threshold=1000.0,
    survival_type="overall"
)
# Returns: High TP53 → 48.5 months vs Low → 32.1 months (p=0.0043)
```

### 5. get_mutation_data

Retrieve mutation frequencies from TCGA cohort.

**Parameters:**
- `cohort`: TCGA cohort code
- `genes`: List of genes to query

**Returns:**
- Mutation frequencies per gene
- Mutation types (missense, nonsense, frameshift, splice_site)
- Sample counts

**Example:**
```python
result = await get_mutation_data(
    cohort="BRCA",
    genes=["TP53", "PIK3CA", "BRCA1"]
)
# Returns: TP53 mutated in 36%, PIK3CA in 33%, BRCA1 in 5%
```

## Resources

### tcga://cohorts

Catalog of all 33 TCGA cohorts with sample counts and data types.

**Example:**
```
Resource URI: tcga://cohorts
Returns: Comprehensive cohort list with 11,000+ total samples
```

### tcga://brca

Detailed information about the Breast Cancer (BRCA) cohort.

**Example:**
```
Resource URI: tcga://brca
Returns: 1097 tumor samples, molecular subtypes, key mutations
```

## Installation

```bash
cd servers/mcp-tcga
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Configuration

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tcga": {
      "command": "/absolute/path/to/spatial-mcp/servers/mcp-tcga/venv/bin/python",
      "args": ["-m", "mcp_tcga"],
      "cwd": "/absolute/path/to/spatial-mcp/servers/mcp-tcga",
      "env": {
        "PYTHONPATH": "/absolute/path/to/spatial-mcp/servers/mcp-tcga/src",
        "TCGA_DRY_RUN": "true"
      }
    }
  }
}
```

**Important:** Use the full path to the venv Python executable, not just `python`. Claude Desktop requires absolute paths.

For a complete working config with all 8 servers, see `../../configs/claude_desktop_config.json`.

## DRY_RUN Mode

Set `TCGA_DRY_RUN=true` to use realistic mock data without requiring:
- GDC Data Portal API access
- Large data downloads
- Authentication tokens

Perfect for development and testing!

## Example Workflows

### Compare Spatial Sample to TCGA Cohort

```
Claude, I have spatial transcriptomics data from a breast cancer sample. Can you:

1. Query the TCGA BRCA cohort to see how many samples are available
2. Fetch expression data for EPCAM, KRT19, VIM, and CD3D
3. Compare my sample's expression to the TCGA population
4. Show me which genes are significantly higher or lower in my sample
```

### Survival Correlation

```
For the BRCA cohort, can you analyze survival data for the TP53 gene?
Split samples into high/low expression groups and show me the difference
in overall survival.
```

### Mutation Analysis

```
What are the mutation frequencies for TP53, PIK3CA, and BRCA1 in the
TCGA breast cancer cohort? Show me the breakdown by mutation type.
```

## Data Sources

- **TCGA Data Portal**: https://portal.gdc.cancer.gov/
- **Cohorts**: 33 cancer types, 11,000+ samples
- **Data Types**: RNA-Seq, DNA-Seq, Methylation, Clinical, Pathology
- **Access**: Open access for research use

## Testing

```bash
pytest
pytest --cov=src --cov-report=html
pytest -v -k "test_query_cohorts"
```

## Integration with Other Servers

**Works with:**
- `mcp-fgbio`: Reference genomes for coordinate mapping
- `mcp-spatialtools`: Align spatial regions with TCGA subtypes
- `mcp-huggingface`: ML model predictions vs. TCGA labels
- `mcp-mockepic`: Clinical data comparison

## Technical Details

- **Framework**: FastMCP (Python 3.11+)
- **Data Format**: Pandas DataFrames, JSON
- **Statistics**: scipy, numpy for statistical tests
- **Performance**: Mock mode <100ms, real queries 1-5 seconds

## References

- TCGA Research Network: https://www.cancer.gov/tcga
- GDC Data Portal: https://portal.gdc.cancer.gov/
- TCGA Publications: https://www.cancer.gov/about-nci/organization/ccg/research/structural-genomics/tcga/publications

---

**Built for the Spatial MCP POC**
