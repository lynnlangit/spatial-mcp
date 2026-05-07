TEST 2: Multi-Omics Endocrine Resistance Analysis (SYNTHETIC_DATA Mode)
========================================================================

> **Data Mode:** This test uses **SYNTHETIC_DATA** — `*_DRY_RUN=false`. The multiomics server parses the actual CSV files in `/data/patient-data/PAT002-BC-2026/multiomics/`. No heavy bioinformatics tools required, but Python parsing dependencies (pandas, numpy, scipy) must be installed. See [Data Modes Guide](../../data-modes-guide.md) for details.

Patient ID: PAT002-BC-2026

## Prerequisites

| Requirement | Details |
|------------|---------|
| `MULTIOMICS_DRY_RUN` | `false` |
| Python deps | pandas, numpy, scipy (for CSV parsing, stats) |
| Data files | `data/patient-data/PAT002-BC-2026/multiomics/` |

## Data Files (Real CSVs)

Files parsed by the server from `data/patient-data/PAT002-BC-2026/multiomics/`:
- `sample_metadata.csv` — Sample annotations (includes Batch column)
- `tumor_rna_seq.csv` — RNA-seq expression values
- `tumor_proteomics.csv` — TMT proteomics data
- `tumor_phosphoproteomics.csv` — Phosphoproteomics data

Note: PAT002 uses `tumor_*.csv` naming convention.

## Analysis Steps

### STEP 0: DATA PREPROCESSING

1. **Validate Data Quality:**
   ```
   Use mcp-multiomics tool: validate_multiomics_data

   Inputs:
   - rna_path: data/patient-data/PAT002-BC-2026/multiomics/tumor_rna_seq.csv
   - protein_path: data/patient-data/PAT002-BC-2026/multiomics/tumor_proteomics.csv
   - phospho_path: data/patient-data/PAT002-BC-2026/multiomics/tumor_phosphoproteomics.csv
   - metadata_path: data/patient-data/PAT002-BC-2026/multiomics/sample_metadata.csv
   ```

   Check for batch effects, missing value patterns, sample consistency, and outliers.

2. **Preprocess Data:**
   ```
   Use mcp-multiomics tool: preprocess_multiomics_data

   Apply: Batch correction (ComBat), KNN imputation, quantile normalization, outlier removal
   ```

3. **Visualize QC:**
   ```
   Use mcp-multiomics tool: visualize_data_quality

   Generate before/after PCA plots, correlation heatmaps, missing value patterns
   ```

### STEP 1: DATA INTEGRATION

4. **Integrate Preprocessed Data:**
   ```
   Use mcp-multiomics tool: integrate_omics_data

   Load preprocessed files from all 3 modalities
   ```

### STEP 2: ASSOCIATION TESTING & META-ANALYSIS

5. **Focus on KEY BREAST CANCER GENES:**
   - **Hormone receptor:** ESR1, PGR, FOXA1, GATA3
   - **PI3K pathway:** PIK3CA, AKT1, MTOR, PTEN
   - **Proliferation:** MKI67, CCND1, CDK4
   - **Drug resistance:** ABCB1, ESR1 (resistance mutations)

6. **Run Stouffer's Meta-Analysis:**
   ```
   Use mcp-multiomics tool: calculate_stouffer_meta

   For each gene: combine p-values from RNA, Protein, Phospho
   Method: Stouffer's Z-score with FDR correction after combination
   ```

### STEP 3: UPSTREAM REGULATOR PREDICTION

7. **Predict Therapeutic Targets:**
   ```
   Use mcp-multiomics tool: predict_upstream_regulators

   Input: Significant genes from Stouffer's (q < 0.05)
   Analyze for kinases, transcription factors, drug responses
   ```

## How This Differs from DRY_RUN

| Aspect | DRY_RUN | SYNTHETIC_DATA (this test) |
|--------|---------|---------------------------|
| Data source | Hardcoded inline values | Parsed from actual CSVs on disk |
| CSV files | Any path (returns mock) | `tumor_rna_seq.csv`, `tumor_proteomics.csv`, `tumor_phosphoproteomics.csv` |
| Naming convention | N/A | `tumor_*.csv` (breast cancer convention) |
| CSV parsing | Returns fixed sample counts | Reads real CSV structure and values |
| Batch effects | Returns simulated correlation | Calculates actual PCA from data |
| Stouffer's | Returns predetermined Z-scores | Calculates from actual expression values |
| File I/O | None | Reads 4 CSV files from `data/` directory |

## Expected Results

Results come from parsing the actual synthetic CSV files. Values may differ slightly from DRY_RUN hardcoded values but should show the same biological patterns:

**Sample Summary:**
- 12 samples: 6 pre-treatment + 6 post-treatment
- Pre-treatment: High proliferation, high ER/PR
- Post-treatment: Low proliferation, slightly reduced ER/PR, increased immune markers

**Gene-Level Results (Stouffer's Meta-Analysis):**
- ESR1, PGR, GATA3: Strongly upregulated (luminal signature)
- PIK3CA: Activated (consistent with H1047R mutation)
- CCND1: Elevated (consistent with chr11q13 gain)
- MKI67: Low/moderate (Luminal A pattern)
- PTEN: Not significantly altered

**Drug Sensitivity Predictions:**
- **PI3K inhibitor (alpelisib):** Sensitive — PIK3CA H1047R activating mutation
- **CDK4/6 inhibitor (palbociclib/ribociclib):** Sensitive — CCND1 amplified, CDK4 active
- **PARP inhibitor (olaparib):** Eligible — BRCA2 germline mutation, HRD phenotype
- **Tamoxifen continuation:** Supported — ESR1 strongly expressed, no resistance mutations

**Pathway Analysis:**
- ER signalling pathway: ACTIVE (ESR1, PGR, FOXA1 high)
- PI3K/AKT pathway: MODERATELY ACTIVE (PIK3CA mutant)
- Proliferation: LOW (MKI67 not significantly elevated — consistent with Luminal A)
- Endocrine therapy prediction: SENSITIVE (high ER/PR, low proliferation)

## Output Format

Please provide:

1. **Preprocessing Summary** — Validation results from actual CSV parsing
2. **Sample Summary** — Counts from real metadata file
3. **Gene-Level Results** — Stouffer's Z-scores computed from actual data
4. **Upstream Regulator Predictions** — Based on computed significant genes
5. **Drug Sensitivity Assessment** — PI3Ki, CDK4/6i, PARPi, endocrine therapy predictions

## Validation Checkpoints

- [ ] Server correctly reads CSVs from `data/patient-data/PAT002-BC-2026/multiomics/`
- [ ] Server reads `tumor_*.csv` files (not `pdx_*.csv`)
- [ ] Sample metadata parsed with correct pre/post treatment groups
- [ ] Expression values are real numbers (not hardcoded mock)
- [ ] Stouffer's Z-scores calculated from actual per-modality p-values
- [ ] ER pathway activation pattern preserved (ESR1, PGR, GATA3 high)
- [ ] PIK3CA activated consistent with H1047R mutation
- [ ] FDR correction applied after Stouffer's combination
- [ ] Drug sensitivity predictions include PI3Ki, CDK4/6i, and PARPi
