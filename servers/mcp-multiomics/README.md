# mcp-multiomics: Multi-Omics PDX Data Analysis

MCP server for integrating and analyzing multi-omics data from Patient-Derived Xenograft (PDX) models. Combines RNA, protein, and phosphorylation data using advanced statistical methods including data preprocessing, HAllA association testing, Stouffer's meta-analysis, and upstream regulator prediction.

**Enhanced with bioinformatician feedback (Erik Jessen PhD, Jessie Hohenstein, 2025)**

## Overview

This server enables:
- **Data Preprocessing** ⭐ NEW: Quality validation, batch correction, missing value imputation
- **Multi-Omics Integration**: Align and normalize RNA, protein, and phosphorylation data
- **HAllA Analysis** ⭐ ENHANCED: Chunking strategy (1000 features/chunk = 5 min vs days)
- **Stouffer's Meta-Analysis** ⭐ ENHANCED: Correct FDR timing (AFTER combination)
- **Upstream Regulator Analysis** ⭐ NEW: Predict kinases, TFs, and drug responses
- **Visualization**: Multi-omics heatmaps and PCA plots

## Tools

### Data Preprocessing Tools (Priority: Run FIRST)

**IMPORTANT**: Real-world proteomics data requires preprocessing before analysis. These tools address batch effects (~18 samples/MS run), missing values, and sample naming inconsistencies identified in clinical PDX studies.

#### 0. validate_multiomics_data ⭐ NEW

Validate data quality and consistency BEFORE analysis.

**Parameters:**
- `rna_path` (required): Path to RNA expression data
- `protein_path` (optional): Path to protein abundance data
- `phospho_path` (optional): Path to phosphorylation data
- `metadata_path` (optional): Path to sample metadata (must include 'Sample' and 'Batch' columns)

**Returns:**
- `validation_status`: Overall pass/fail/warning status
- `sample_overlap`: Sample name consistency check
- `missing_patterns`: Missing value analysis per modality
- `batch_effects`: Batch effect detection (CRITICAL for proteomics)
- `outliers`: Outlier samples identified
- `warnings`: List of issues found
- `recommendations`: Suggested preprocessing steps

**Example:**
```
Claude, please validate my multi-omics data quality:
- RNA: /data/pdx_rna_seq.csv
- Protein: /data/pdx_proteomics.csv
- Metadata: /data/sample_metadata.csv (includes Batch column)

Check for batch effects and sample naming issues.
```

#### 0b. preprocess_multiomics_data ⭐ NEW

Comprehensive preprocessing pipeline for real-world proteomics data.

**Parameters:**
- `rna_path`, `protein_path`, `phospho_path`: Data file paths
- `metadata_path`: Sample metadata with 'Batch' column (required for batch correction)
- `normalize_method`: "quantile", "median", "tmm", or "zscore" (default: quantile)
- `batch_correction`: Apply ComBat batch correction (default: True)
- `imputation_method`: "knn", "minimum", or "median" (default: knn)
- `outlier_threshold`: MAD threshold for outlier detection (default: 3.0)
- `output_dir`: Directory to save preprocessed data

**Returns:**
- `preprocessed_paths`: Paths to preprocessed data files
- `preprocessing_report`: Summary of transformations
- `qc_metrics`: Before/after quality metrics
- `batch_correction_results`: PC1-batch correlation (before/after)
- `imputation_stats`: Number of values imputed
- `outliers_removed`: List of outlier samples

**Example:**
```
Claude, preprocess my proteomics data with batch correction:
- RNA: /data/rna_raw.csv
- Protein: /data/protein_raw.csv
- Metadata: /data/metadata.csv (has Batch column)

Apply quantile normalization, KNN imputation, and ComBat batch correction.
Save to /data/preprocessed/
```

#### 0c. visualize_data_quality ⭐ NEW

Generate QC visualizations to verify preprocessing worked.

**Parameters:**
- `data_paths`: Dict of modality -> file path
- `metadata_path`: Sample metadata (for coloring by batch/phenotype)
- `output_dir`: Directory to save plots
- `compare_before_after`: Generate before/after comparison (default: False)
- `before_data_paths`: Dict of pre-preprocessing data paths

**Returns:**
- `plot_paths`: Paths to generated plots (PCA, correlation, missing values)
- `qc_summary`: Quality metrics summary
- `batch_effect_assessment`: PC1 correlation with batch
- `recommendations`: Interpretation and next steps

**Example:**
```
Show me PCA plots before/after batch correction:
- After: /data/preprocessed/protein.csv
- Before: /data/raw/protein.csv
- Metadata: /data/metadata.csv

Verify PC1 no longer correlates with batch.
```

### Core Analysis Tools

### 1. integrate_omics_data

Integrate multi-omics data from RNA, protein, and phosphorylation datasets.

**Parameters:**
- `rna_path` (required): Path to RNA expression data (CSV/TSV, genes x samples)
- `protein_path` (optional): Path to protein abundance data
- `phospho_path` (optional): Path to phosphorylation data
- `metadata_path` (optional): Path to sample metadata (must include 'Sample' column)
- `normalize` (default: True): Apply Z-score normalization within each modality
- `filter_missing` (default: 0.5): Remove features with >X fraction missing (0.0-1.0)

**Returns:**
- `integrated_data`: Aligned data matrices per modality
- `common_samples`: List of samples present in all modalities
- `feature_counts`: Number of features per modality after filtering
- `metadata`: Sample metadata if provided
- `qc_metrics`: Quality control statistics
- `cache_path`: Path to cached integrated data (for downstream tools)

**Example:**
```
Claude, please integrate my multi-omics PDX data:
- RNA: /data/pdx_rna_seq.csv
- Protein: /data/pdx_proteomics.csv
- Phospho: /data/pdx_phosphoproteomics.csv
- Metadata: /data/sample_metadata.csv

Apply Z-score normalization and filter features with >50% missing data.
```

### 2. run_halla_analysis ⭐ ENHANCED

Run HAllA hierarchical all-against-all association testing with chunking strategy.

**IMPORTANT**: Returns NOMINAL p-values (not FDR-corrected). Apply FDR AFTER Stouffer's meta-analysis.

**Parameters:**
- `data_path` (required): Path to integrated multi-omics data (from integrate_omics_data)
- `modality1` (required): First modality ("rna", "protein", or "phospho")
- `modality2` (required): Second modality ("rna", "protein", or "phospho")
- `fdr_threshold` (default: 0.05): FDR threshold for reference (p-values returned are NOMINAL)
- `method` (default: "spearman"): Correlation method - "spearman", "pearson", or "mi"
- `chunk_size` ⭐ NEW (default: 1000): Features per chunk (~5 min/chunk vs days for full dataset)
- `use_r_halla` (default: False): Use R-based HAllA if available (otherwise Python alternative)

**Returns:**
- `associations`: List of feature pairs with **NOMINAL p-values**
- `chunks_processed`: Chunking strategy information (NEW)
- `clusters`: Hierarchical cluster assignments
- `statistics`: Summary statistics
- `nominal_p_values`: Flag indicating p-values are NOMINAL (not FDR-corrected)
- `recommendation`: "Apply FDR after Stouffer's"

**Chunking Strategy:**
- **Full dataset**: 20K RNA × 7K protein = 140M tests (would take DAYS)
- **Chunked**: 1000 features/chunk = ~5 min per chunk ✅

**Example:**
```
Using integrated data, run HAllA between RNA and Protein:
- Data: /workspace/cache/integrated_data.pkl
- Method: Spearman correlation
- Chunk size: 1000 features (for large datasets)

Returns NOMINAL p-values for Stouffer's meta-analysis.
```

### 3. calculate_stouffer_meta ⭐ ENHANCED

Combine p-values across omics modalities using Stouffer's Z-score method.

**CRITICAL**: Implements CORRECT FDR timing - accepts NOMINAL p-values, applies FDR AFTER combination.

**Parameters:**
- `p_values_dict` (required): Dict of modality -> list of **NOMINAL p-values** (e.g., from HAllA)
- `effect_sizes_dict` (optional): Dict of modality -> list of effect sizes (log2FC or correlation)
- `weights` (optional): Dict of modality -> weight (default: equal weights)
- `use_directionality` (default: True): Incorporate effect size sign into Z-scores

**Returns:**
- `meta_p_values`: Combined p-values (**NOMINAL**, before FDR)
- `meta_z_scores`: Combined Z-scores with directionality
- `q_values`: **FDR-corrected p-values** (USE THESE for significance calls)
- `significant_features`: Features passing FDR threshold
- `statistics`: Summary including workflow_confirmation
- `p_value_types`: Clarifies nominal vs FDR-corrected
- `recommendation`: "Use q_values for significance"

**Workflow:**
```
Step 1: HAllA → NOMINAL p-values
Step 2: THIS TOOL → Combine nominal p-values → meta_p_values
Step 3: THIS TOOL → Apply FDR correction → q_values
```

**Example:**
```
Combine NOMINAL p-values from HAllA using Stouffer's method:
- RNA p-values: [0.001, 0.05, 0.3] (NOMINAL from HAllA)
- Protein p-values: [0.002, 0.04, 0.25] (NOMINAL from HAllA)
- Phospho p-values: [0.01, 0.06, 0.28] (NOMINAL from HAllA)

With log2 fold changes:
- RNA log2FC: [2.5, 1.2, -0.3]
- Protein log2FC: [1.8, 1.5, -0.2]
- Phospho log2FC: [1.2, 0.8, -0.4]

Returns meta_p_values (nominal) and q_values (FDR-corrected).
USE q_values for identifying significant features!
```

### 3b. predict_upstream_regulators ⭐ NEW

Predict kinases, transcription factors, and drug responses from differential genes.

**Provides IPA-like insights** for therapeutic target identification.

**Parameters:**
- `differential_genes` (required): Dict of gene -> {"log2fc": float, "p_value": float}
  (Use significant genes from Stouffer's meta-analysis)
- `regulator_types` (optional): List of ["kinase", "transcription_factor", "drug"] (default: all)
- `fdr_threshold` (default: 0.05): FDR threshold for significant regulators
- `activation_zscore_threshold` (default: 2.0): |Z-score| threshold for activation/inhibition

**Returns:**
- `kinases`: List of predicted kinases with activation state (Activated/Inhibited)
- `transcription_factors`: List of predicted TFs with activation state
- `drugs`: List of predicted drug responses with mechanism
- `statistics`: Summary statistics (counts, methods)
- `method`: Enrichment method details (Fisher's exact + Z-score)
- `recommendation`: Top therapeutic recommendation

**Method:**
1. Fisher's exact test - are regulator's targets enriched in DEGs?
2. Activation Z-score - based on target expression direction
3. FDR correction across all regulators
4. Rank by significance and activation strength

**Example:**
```
From Stouffer's significant genes, predict upstream regulators:
- Input: 50 significant genes with log2FC and p-values
- Analyze: Kinases, transcription factors, and drug responses

Returns:
- Kinases: AKT1 (Activated), MTOR (Activated), TP53 (Inhibited)
- Drugs: Alpelisib (PI3K inhibitor) - targets activated pathway
```

### 4. create_multiomics_heatmap

Create integrated heatmap visualization across multiple omics modalities.

**Parameters:**
- `data_path` (required): Path to integrated multi-omics data
- `features` (optional): List of feature names to include (default: top significant features)
- `cluster_rows` (default: True): Apply hierarchical clustering to rows (features)
- `cluster_cols` (default: True): Apply hierarchical clustering to columns (samples)
- `output_path` (optional): Path to save plot (PNG or PDF)

**Returns:**
- `plot_path`: Path to saved visualization
- `cluster_info`: Cluster assignments
- `figure_data`: Plotly JSON for interactive plot

**Example:**
```
Please create a multi-omics heatmap for the integrated data showing
TP53, MYC, EGFR, and KRAS across all modalities. Cluster both rows
and columns and save to /workspace/plots/multiomics_heatmap.png.
```

### 5. run_multiomics_pca

Run Principal Component Analysis on integrated multi-omics data.

**Parameters:**
- `data_path` (required): Path to integrated multi-omics data
- `modalities` (optional): List of modalities to include (default: all available)
- `n_components` (default: 3): Number of principal components to compute
- `scale_features` (default: True): Apply feature scaling before PCA
- `output_path` (optional): Path to save 2D and 3D PCA plots

**Returns:**
- `variance_explained`: Fraction of variance per component
- `loadings`: Feature loadings on each PC
- `sample_coordinates`: PC coordinates for each sample
- `plot_path`: Path to saved visualization

**Example:**
```
Run PCA on the integrated RNA + Protein data to visualize sample clustering.
Compute 3 components and color samples by treatment response.
```

## XAI Metadata

Every tool returns an `xai_metadata` field with explainability information:

| Field | Description |
|-------|-------------|
| `confidence_level` | `high`, `moderate`, or `low` — how reliable the result is given the inputs |
| `confidence_note` | Why this confidence level was assigned |
| `key_drivers` | 1-3 inputs that most influenced the result |
| `guideline_version` | Specific algorithm or method reference (e.g., HAllA, Stouffer) |
| `evidence_grade` | Tier 1 Evidence (TCGA/GEP) or Algorithm-Predicted — Not Clinical Grade |
| `counterfactual` | What would change if a key input were different |

## Resources

### multiomics://config

Get current server configuration and analysis parameters.

**Example:**
```
What are the current multi-omics server settings?
```

### multiomics://example-data

Get information about example datasets and data format requirements.

**Example:**
```
What data formats does the multi-omics server expect?
```

## Installation

> **Standard setup:** See [Server Installation Guide](../../docs/reference/shared/server-installation.md) for venv creation, pip install, and Claude Desktop config. For a complete working config with all servers, see [`docs/getting-started/desktop-configs/`](../../docs/getting-started/desktop-configs/).

**Server-specific environment variables:** `MULTIOMICS_DATA_DIR`, `MULTIOMICS_CACHE_DIR`, `MULTIOMICS_DRY_RUN`

## DRY_RUN Mode

Set `MULTIOMICS_DRY_RUN=true` to use realistic mock data without requiring:
- R installation and rpy2
- HAllA R package
- Large data downloads
- Real file I/O operations

Perfect for development, testing, and demonstrations!

> See [DRY_RUN Mode Guide](../../docs/reference/shared/dry-run-mode.md) for details on mock mode.

## Data Format Requirements

### RNA Expression Data (CSV/TSV)
```
Gene,Sample_01,Sample_02,Sample_03,...
TP53,1234.5,2341.2,987.3,...
MYC,5432.1,4321.9,3210.4,...
EGFR,876.4,1023.8,1156.2,...
```
- First column: Gene symbols
- Other columns: FPKM, TPM, or normalized counts per sample
- Missing values: Leave empty or use NA/NaN

### Protein Abundance (TMT/Label-Free)
```
Protein,Sample_01,Sample_02,Sample_03,...
TP53,45.2,67.8,34.1,...
MYC,123.4,145.6,98.7,...
```
- First column: Protein names (preferably matching gene symbols)
- Other columns: TMT intensities or LFQ values

### Phosphorylation Data
```
Phosphosite,Sample_01,Sample_02,Sample_03,...
TP53_S15,12.3,23.4,8.7,...
AKT1_S473,89.2,102.3,76.5,...
```
- First column: Phosphosite notation (PROTEIN_RESIDUE_POSITION)
- Other columns: Phosphorylation intensities

### Sample Metadata
```
Sample,Response,Batch,Age,Sex
Sample_01,Resistant,1,65,M
Sample_02,Sensitive,1,58,F
Sample_03,Resistant,2,72,M
```
- Must include `Sample` column matching sample names in omics data
- Recommended columns: Treatment response, batch, clinical variables

## Example Workflows

### Complete Clinical PDX Analysis (RECOMMENDED)

**Full precision medicine workflow with preprocessing** (based on real-world clinical studies):

```
Claude, analyze my PDX treatment response data with complete pipeline:

STEP 0: Preprocessing (CRITICAL for real proteomics data)
========================================================
1. Validate data quality:
   - RNA: /data/pdx_rna_seq_raw.csv
   - Protein: /data/pdx_proteomics_raw.csv (TMT, 2 batches, ~18 samples/run)
   - Phospho: /data/pdx_phosphoproteomics_raw.csv
   - Metadata: /data/sample_metadata.csv (includes Batch column)

   Check for batch effects and sample naming issues.

2. Preprocess the data:
   - Apply KNN imputation for missing values
   - ComBat batch correction (CRITICAL - proteomics has batch effects)
   - Quantile normalization
   - Save to /data/preprocessed/

3. Visualize QC before/after:
   - Generate PCA plots colored by batch
   - Verify PC1 no longer correlates with batch (should be < 0.3)

STEP 1: Integration
===================
4. Integrate preprocessed data:
   - RNA: /data/preprocessed/rna.csv
   - Protein: /data/preprocessed/protein.csv
   - Phospho: /data/preprocessed/phospho.csv
   - Metadata: /data/metadata.csv

STEP 2: Association Testing (HAllA)
====================================
5. Run HAllA between RNA and Protein:
   - Chunk size: 1000 features (~5 min/chunk)
   - Method: Spearman correlation
   - Returns NOMINAL p-values

STEP 3: Meta-Analysis (Stouffer's)
===================================
6. Combine NOMINAL p-values from HAllA:
   - RNA p-values (nominal)
   - Protein p-values (nominal)
   - Phospho p-values (nominal)
   - Include log2 fold changes for directionality
   - FDR correction applied AFTER combination → q-values

STEP 4: Upstream Regulator Analysis
====================================
7. From significant genes (q < 0.05), predict regulators:
   - Identify activated/inhibited kinases
   - Find transcription factors driving changes
   - Predict drug responses

8. Generate final report with therapeutic recommendations
```

### Quick Preprocessing-Only Workflow

**For users with batch effects in proteomics data:**

```
Claude, I have proteomics batch effects to fix:

1. Validate my protein data:
   - Data: /data/protein_raw.csv
   - Metadata: /data/metadata.csv (has Batch column)

2. Preprocess with batch correction:
   - Method: ComBat
   - Imputation: KNN
   - Normalization: Quantile
   - Output: /data/protein_corrected.csv

3. Show me before/after PCA plots to verify batch correction worked
   (PC1 should no longer correlate with batch)
```

### HAllA + Stouffer's Workflow (Correct FDR Timing)

**Demonstrates correct FDR workflow:**

```
Run HAllA and Stouffer's with CORRECT FDR timing:

1. HAllA between RNA and Protein:
   - Returns NOMINAL p-values (NOT FDR-corrected)
   - Chunk size: 1000 for large datasets

2. Stouffer's meta-analysis:
   - Input: NOMINAL p-values from HAllA
   - Combines across modalities
   - Applies FDR correction AFTER combination
   - Output: Use q_values for significance calls

This is the CORRECT workflow per bioinformatician feedback.
DO NOT apply FDR before Stouffer's!
```

### Upstream Regulator Discovery

**For therapeutic target identification:**

```
From my 50 significant genes (from Stouffer's meta-analysis),
predict upstream regulators:

Input genes with log2FC and p-values:
- AKT1, MTOR, TP53, MYC, FOXO1, etc.

Analyze:
- Kinases (activated/inhibited)
- Transcription factors
- Drug responses

Expected output:
- AKT1/MTOR activated → Alpelisib (PI3K inhibitor) recommendation
- TP53 inhibited → Loss of tumor suppression
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/test_stouffer.py -v
pytest tests/test_integration.py -v
```

## Integration with Other Servers

**Works with:**
- `mcp-fgbio`: Reference genome data for gene annotations
- `mcp-spatialtools`: Spatial transcriptomics analysis and clustering
- `mcp-mocktcga`: Compare PDX results to TCGA cohorts

## Preprocessing Requirements (IMPORTANT)

**Based on real-world clinical PDX studies (Erik Jessen PhD, Jessie Hohenstein)**

### Why Preprocessing Matters

Real proteomics data has critical issues that MUST be addressed before analysis:

1. **Batch Effects** (~18 samples/MS run creates batches)
   - **Problem**: PC1 correlates with batch (r > 0.7), not biology
   - **Solution**: ComBat batch correction
   - **Verification**: PC1-batch correlation < 0.3 after correction

2. **Missing Values** (different proteins detected per batch)
   - **Problem**: Batch 1: 7000 proteins, Batch 2: 5000 proteins, 80% overlap
   - **Solution**: KNN imputation (k=5) before integration
   - **Alternative**: Minimum or median imputation

3. **Sample Naming Inconsistencies**
   - **Problem**: RNA uses "Sample-01", Protein uses "Sample_01"
   - **Solution**: Automatic harmonization in preprocess tool

4. **Outlier Samples**
   - **Problem**: Technical failures, mislabeled samples
   - **Solution**: MAD-based outlier detection (threshold: 3.0)

### Recommended Preprocessing Workflow

```
1. validate_multiomics_data → Identify issues
2. preprocess_multiomics_data → Fix issues
3. visualize_data_quality → Verify fixes worked
4. integrate_omics_data → Proceed with analysis
```

**DO NOT skip preprocessing for clinical proteomics data!**

## Technical Details

- **Framework**: FastMCP (Python 3.11+)
- **Statistical Methods**:
  - **Preprocessing** ⭐ NEW:
    - ComBat batch correction (statsmodels)
    - KNN imputation (scikit-learn)
    - Quantile/TMM/median normalization
    - MAD-based outlier detection
  - **Association Testing**:
    - HAllA with chunking (1000 features/chunk)
    - Spearman/Pearson correlation
    - Fisher's exact test enrichment
  - **Meta-Analysis**:
    - Stouffer's Z-score method (scipy)
    - FDR correction AFTER combination (Benjamini-Hochberg)
    - Directionality from effect sizes
  - **Upstream Regulators** ⭐ NEW:
    - Fisher's exact test enrichment
    - Activation Z-scores
    - Kinase/TF/drug databases
- **R Integration**: rpy2 for R-based HAllA (optional, Python alternative available)
- **Data Handling**: pandas, numpy
- **Visualization**: matplotlib, seaborn, plotly
- **Performance**:
  - Mock mode: <100ms per tool call
  - Preprocessing: 30-60 seconds for 15 samples
  - Integration: 1-5 seconds for 1000 features
  - HAllA (chunked): ~5 min per 1000 features
  - Stouffer's: <1 second for 10,000 features
  - Upstream regulators: <5 seconds for 50 genes

## References

### Core Statistical Methods

- **Stouffer's Method**: Whitlock MC (2005). Combining probability from independent tests: the weighted Z-method is superior to Fisher's approach. *J Evol Biol* 18(5):1368-73.
- **HAllA**: Rahnavard et al. (2017). High-sensitivity pattern discovery in large, paired multiomic datasets. *Bioinformatics* 33(14):i81-i89.
- **Multi-Omics Integration**: Menyh\u00e1rt et al. (2023). Multi-omics approaches in cancer research with applications in tumor subtyping, prognosis, and diagnosis. *Comput Struct Biotechnol J* 21:1864-1883.
- **Benjamini-Hochberg FDR**: Benjamini Y, Hochberg Y (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *J R Stat Soc Series B Stat Methodol* 57(1):289-300.

### Preprocessing Methods ⭐ NEW

- **ComBat Batch Correction**: Johnson WE, Li C, Rabinovic A (2007). Adjusting batch effects in microarray expression data using empirical Bayes methods. *Biostatistics* 8(1):118-127.
- **KNN Imputation**: Troyanskaya et al. (2001). Missing value estimation methods for DNA microarrays. *Bioinformatics* 17(6):520-525.
- **Quantile Normalization**: Bolstad BM et al. (2003). A comparison of normalization methods for high density oligonucleotide array data based on variance and bias. *Bioinformatics* 19(2):185-193.
- **MAD Outlier Detection**: Leys et al. (2013). Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median. *J Exp Soc Psychol* 49(4):764-766.

### Upstream Regulator Analysis ⭐ NEW

- **Ingenuity Pathway Analysis (IPA)**: Krämer et al. (2014). Causal analysis approaches in Ingenuity Pathway Analysis. *Bioinformatics* 30(4):523-530.
- **Fisher's Exact Test**: Fisher RA (1922). On the interpretation of χ² from contingency tables, and the calculation of P. *J R Stat Soc* 85(1):87-94.
- **Activation Z-score**: Chindelevitch et al. (2012). Causal reasoning on biological networks: interpreting transcriptional changes. *Bioinformatics* 28(8):1114-1121.

## Troubleshooting

### Server won't start
- Check Python version: Must be 3.11+
- Verify dependencies: Run `pip install -e .`
- Check environment variables: Ensure paths exist

### Integration fails
- Verify file formats: First column must be feature names
- Check sample names: Must match exactly across files
- Enable DRY_RUN: Set `MULTIOMICS_DRY_RUN=true` for testing

### HAllA not available
- Install R and rpy2: `pip install rpy2` (Unix/Mac only)
- Install HAllA R package: See HAllA documentation
- Use DRY_RUN mode: Works without R installation

### Batch effects detected ⭐ NEW
- **Symptom**: PC1 correlates with batch (r > 0.7) in validation
- **Solution**: Use `preprocess_multiomics_data` with `batch_correction=True`
- **Verification**: Run `visualize_data_quality` - PC1-batch correlation should be < 0.3
- **Note**: ComBat requires metadata with 'Batch' column

### Preprocessing fails
- **Missing scikit-learn**: Run `pip install scikit-learn` for KNN imputation
- **Missing statsmodels**: Run `pip install statsmodels` for ComBat batch correction
- **No Batch column**: Batch correction requires metadata.csv with 'Batch' column
- **Too many missing values**: If > 80% missing in a feature, consider excluding it
- **Sample mismatch**: Ensure sample names match between data and metadata

### PC1 still correlates with batch after correction
- **Cause**: Batch effects too strong for ComBat alone
- **Solutions**:
  1. Check if batch confounds with biology (e.g., all treated samples in batch 1)
  2. Try different normalization: Change `normalize_method` to "quantile" or "tmm"
  3. Remove outlier samples first: Lower `outlier_threshold` to 2.5
  4. Consider removing problematic batch entirely if < 3 samples

### Imputation takes too long
- **For large datasets**: KNN imputation is O(n²) - can be slow for > 10,000 features
- **Solutions**:
  1. Use `imputation_method="median"` (much faster, less accurate)
  2. Filter features with > 50% missing before imputation
  3. Use chunking: Preprocess modalities separately

### Stouffer's p-values look wrong
- **Common mistake**: Passed FDR-corrected p-values instead of NOMINAL
- **Check**: Look at minimum p-value - if > 0.001, likely already FDR-corrected
- **Solution**: Use NOMINAL p-values from HAllA (look for `p_value_nominal` field)
- **Note**: Stouffer's applies FDR internally - don't apply it twice!

### Upstream regulator predictions seem weak
- **Cause**: Too few significant genes (< 10)
- **Solutions**:
  1. Relax FDR threshold: Try q < 0.1 instead of 0.05
  2. Check input genes: Must include log2FC for activation Z-score
  3. Use more modalities: Combine RNA + Protein + Phospho for more power
- **Note**: Need at least 20-30 significant genes for meaningful predictions

## License

See the main repository LICENSE file.

## Support

- **Issues**: https://github.com/lynnlangit/precision-medicine-mcp/issues
- **Documentation**: See main repository docs/
- **MCP Specification**: https://modelcontextprotocol.io/

---

**Built for the Precision Medicine MCP suite** (key component of the [PatientOne](../../docs/reference/testing/patient-one/README.md) precision medicine workflow)
