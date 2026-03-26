TEST 2: Multi-Omics Endocrine Resistance Analysis (ENHANCED WORKFLOW)
=====================================================================

Patient ID: PAT002-BC-2026

## Multi-Omics Tumor Analysis (use mcp-multiomics - 10 tools)

For patient PAT002-BC-2026, analyze endocrine therapy resistance potential using the COMPLETE workflow:

### Data Files Location:
Files at: `patient-data/PAT002-BC-2026/multiomics/`
- sample_metadata.csv (includes Batch column)
- tumor_rna_seq.csv (raw, not preprocessed)
- tumor_proteomics.csv (raw TMT data, BATCH EFFECTS EXPECTED)
- tumor_phosphoproteomics.csv (raw)

### Analysis Steps (Enhanced Workflow):

## STEP 0: DATA PREPROCESSING

1. **Validate Data Quality:**
   ```
   Use mcp-multiomics tool: validate_multiomics_data

   Inputs:
   - rna_path: tumor_rna_seq.csv
   - protein_path: tumor_proteomics.csv
   - phospho_path: tumor_phosphoproteomics.csv
   - metadata_path: sample_metadata.csv
   ```

2. **Preprocess Data:**
   ```
   Use mcp-multiomics tool: preprocess_multiomics_data

   Apply preprocessing pipeline:
   - Batch correction: ComBat
   - Imputation: KNN (k=5)
   - Normalization: Quantile normalization
   - Outlier removal: MAD threshold 3.0
   ```

3. **Visualize QC:**
   ```
   Use mcp-multiomics tool: visualize_data_quality
   Verify: PC1-batch correlation < 0.3 after preprocessing
   ```

## STEP 1: DATA INTEGRATION

4. **Integrate Preprocessed Data:**
   ```
   Use mcp-multiomics tool: integrate_omics_data
   Load PREPROCESSED files from /preprocessed/ directory
   ```

## STEP 2: ASSOCIATION TESTING & META-ANALYSIS

5. **Focus on KEY BREAST CANCER GENES:**
   - **Hormone receptor:** ESR1, PGR, FOXA1, GATA3
   - **PI3K pathway:** PIK3CA, AKT1, MTOR, PTEN
   - **Proliferation:** MKI67, CCND1, CDK4
   - **Drug resistance:** ABCB1, ESR1 (resistance mutations)

6. **Run Stouffer's Meta-Analysis:**
   ```
   Use mcp-multiomics tool: calculate_stouffer_meta

   For each gene:
   - Input: NOMINAL p-values from differential expression (RNA, Protein, Phospho)
   - Input: log2 fold changes (for directionality)
   - Method: Stouffer's Z-score method
   - FDR correction: Applied AFTER combination
   ```

## STEP 3: UPSTREAM REGULATOR PREDICTION

7. **Predict Therapeutic Targets:**
   ```
   Use mcp-multiomics tool: predict_upstream_regulators

   Analyze for:
   - Kinases (activation state)
   - Transcription factors (ESR1, FOXA1 activity)
   - Drug responses (endocrine therapy, CDK4/6 inhibitors)
   ```

## Expected Results:

**Gene-Level Results (Stouffer's Meta-Analysis):**
| Gene   | RNA FC | Prot FC | Phos FC | Z-score | q-value | Direction |
|--------|--------|---------|---------|---------|---------|-----------|
| ESR1   | +3.1   | +2.8    | +2.5    | 5.2     | <0.0001 | UP        |
| PGR    | +2.5   | +2.2    | +1.9    | 4.1     | 0.0001  | UP        |
| GATA3  | +2.3   | +2.0    | +1.7    | 3.8     | 0.0003  | UP        |
| PIK3CA | +1.8   | +1.6    | +2.1    | 3.5     | 0.0005  | UP        |
| CCND1  | +2.0   | +1.8    | +1.5    | 3.2     | 0.001   | UP        |
| MKI67  | +0.8   | +0.6    | +0.5    | 1.2     | 0.15    | UP (NS)   |
| PTEN   | -0.5   | -0.3    | -0.4    | -0.8    | 0.25    | DOWN (NS) |

**Upstream Regulators:**
- **Activated TFs:** ESR1 (Z=4.5), FOXA1 (Z=3.8), GATA3 (Z=3.2)
- **Activated Kinases:** PI3K (Z=2.8), CDK4/6 (Z=2.5)
- **Drug Targets Identified:**
  - Continue tamoxifen (ER strongly expressed)
  - CDK4/6 inhibitor (palbociclib/ribociclib) if recurrence
  - PI3K inhibitor (alpelisib) given PIK3CA H1047R mutation

**Pathway Analysis:**
- ER signalling pathway: ACTIVE (ESR1, PGR, FOXA1 high)
- PI3K/AKT pathway: MODERATELY ACTIVE (PIK3CA mutant)
- Proliferation: LOW (MKI67 not significantly elevated — consistent with Luminal A)
- Endocrine therapy prediction: SENSITIVE (high ER/PR, low proliferation)

## Output Format:

1. **Preprocessing Summary**
2. **Sample Summary** (tumor samples analysed)
3. **Gene-Level Results** (Stouffer's Z-scores and q-values)
4. **Upstream Regulator Predictions**
5. **Pathway Interpretation** (ER pathway, PI3K, proliferation status)

## Validation Checkpoints:

**Analysis:**
- ER pathway genes: ESR1, PGR, GATA3 strongly upregulated
- PIK3CA: Activated (consistent with H1047R mutation)
- Proliferation: Low (Luminal A pattern)
- Stouffer's FDR correction: Applied AFTER combination
- Drug targets: Tamoxifen continuation, CDK4/6i and PI3Ki options identified
