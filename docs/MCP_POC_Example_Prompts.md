# Example Prompts for Spatial MCP Proof-of-Concept (POC)

These prompts are designed for the Model Context Protocol (MCP) framework to validate AI-assisted spatial multi-omics workflows. They include realistic data structures (Visium, CosMx, Slide-seq, OME-TIFF), spatial coordinates, barcodes, and genomic references.

---

## 1️⃣ Load and Validate Spatial Transcriptomics Dataset

**Metadata:**
- Sample ID: SPX001
- Platform: 10x Genomics Visium
- Reference Genome: GRCh38
- Data Type: FASTQ + Spatial Coordinates (JSON)

**Objective:** Validate input files and ensure spatial barcodes match reference coordinates.

**Expected Input:**
- Paired FASTQs (`sample_001_R1.fastq.gz`, `sample_001_R2.fastq.gz`)
- `spatial/tissue_positions_list.csv`
- `spatial/scalefactors_json.json`

**Action:**
- Run `mcp-fgbio` to check read quality
- Run `mcp-spatialtools` to validate barcode ↔ coordinate mapping

**Acceptance Criteria:**
- ≥95% barcodes match coordinate table
- FASTQ Phred ≥30 mean

**Rationale & Tools:** Ensures data integrity before alignment. Tools: FGbio, SpatialTools.

**Example Prompt:**
```
Claude, I have a 10x Visium dataset (SPX001) with paired FASTQ files and spatial
coordinates. Please:

1. Validate FASTQ quality (target: mean Phred ≥30)
2. Check barcode format and structure
3. Verify spatial barcodes match the tissue_positions_list.csv
4. Report any mismatches or quality issues

Files:
- fastq/sample_001_R1.fastq.gz
- fastq/sample_001_R2.fastq.gz
- spatial/tissue_positions_list.csv
- spatial/scalefactors_json.json
```

---

## 2️⃣ Perform Spatial Alignment of Reads

**Metadata:**
- Platform: 10x Visium
- Reference Genome: GRCh38 (STAR index)

**Objective:** Map reads to reference genome and generate feature–spot matrix.

**Expected Input:**
- Validated FASTQs from Step 1

**Action:**
- `mcp-seqera` pipeline invoking STARsolo

**Acceptance Criteria:**
- ≥80% uniquely mapped reads
- UMI duplication rate ≤10%

**Rationale & Tools:** Establishes base expression matrix for downstream spatial analysis.

**Example Prompt:**
```
Claude, align the validated Visium reads to GRCh38 using STAR:

1. Fetch GRCh38 reference genome
2. Launch STARsolo alignment via Seqera Platform
3. Generate feature × spot expression matrix
4. Report alignment statistics (unique mapping rate, UMI duplicates)

Requirements:
- Minimum 80% unique mapping rate
- UMI duplication ≤10%
- Preserve spatial barcode tags in BAM
```

---

## 3️⃣ Extract UMIs and Perform Quality Control

**Metadata:**
- Platform: 10x Visium
- Read Structure: 16bp barcode + 12bp UMI + cDNA

**Objective:** Extract UMIs from reads and filter low-quality spots.

**Expected Input:**
- `sample_001_R1.fastq.gz` (contains barcodes + UMIs)
- `sample_001_R2.fastq.gz` (contains cDNA)

**Action:**
- `mcp-fgbio` extract_umis with read structure "16M12M+T"
- `mcp-spatialtools` filter_quality

**Acceptance Criteria:**
- UMI extraction rate ≥95%
- Spots retained: ≥80% (after QC filtering)
- Min reads/spot: 1,000
- Min genes/spot: 200

**Rationale & Tools:** Removes low-quality spots that would confound downstream analysis.

**Example Prompt:**
```
Claude, extract UMIs and perform QC filtering:

1. Extract 12bp UMIs from R1 using read structure: 16bp barcode + 12bp UMI
2. Filter spots with:
   - Minimum 1,000 reads per spot
   - Minimum 200 genes detected per spot
   - Maximum 20% mitochondrial gene expression
3. Report QC metrics and retention rate

Target retention: ≥80% of spots
```

---

## 4️⃣ Segment Tissue Regions Using Histology Image

**Metadata:**
- Image Type: H&E histology (OME-TIFF)
- Image ID: IMG00001
- Resolution: 4096×4096 pixels, 20× magnification

**Objective:** Register H&E image to spatial coordinates and segment into regions (tumor, stroma, immune, normal).

**Expected Input:**
- H&E histology image (TIFF)
- Spatial coordinates from Step 1

**Action:**
- `mcp-openimagedata` fetch_histology_image
- `mcp-openimagedata` register_image_to_spatial
- `mcp-deepcell` segment_cells
- `mcp-spatialtools` split_by_region

**Acceptance Criteria:**
- Image registration RMSE <5 pixels
- ≥4 distinct regions identified
- Cell segmentation: ≥1,000 cells detected

**Rationale & Tools:** Enables region-specific spatial analysis by combining morphology with transcriptomics.

**Example Prompt:**
```
Claude, segment the tissue using the H&E image:

1. Fetch H&E histology image (IMG00001, 20× magnification)
2. Register image to spatial coordinates (affine transformation)
3. Use DeepCell to segment individual cells
4. Identify tissue regions: tumor, stroma, immune infiltration, normal
5. Assign each spatial spot to a region

Requirements:
- Registration error <5 pixels RMSE
- Segment ≥1,000 cells
- Identify ≥4 distinct regions
```

---

## 5️⃣ Perform Differential Expression Between Regions

**Metadata:**
- Comparison: Tumor vs. Normal regions
- Statistical Test: Wilcoxon rank-sum test
- Multiple Testing Correction: Benjamini-Hochberg FDR

**Objective:** Identify genes differentially expressed between tumor and normal tissue regions.

**Expected Input:**
- Expression matrix from Step 2
- Region annotations from Step 4

**Action:**
- `mcp-spatialtools` perform_differential_expression

**Acceptance Criteria:**
- ≥20 significantly DE genes (FDR <0.05)
- Log2 fold-change threshold: |log2FC| ≥1
- Report top 10 upregulated and downregulated genes

**Rationale & Tools:** Identifies tumor-specific gene signatures for biological interpretation.

**Example Prompt:**
```
Claude, perform differential expression analysis:

1. Compare tumor regions vs. normal regions
2. Use Wilcoxon rank-sum test with Benjamini-Hochberg FDR correction
3. Filter for genes with |log2FC| ≥1 and FDR <0.05
4. Report:
   - Total significant genes
   - Top 10 upregulated in tumor
   - Top 10 downregulated in tumor
   - Summary statistics (mean expression, fold-change, p-values)

Expected: ≥20 significant DE genes
```

---

## 6️⃣ Calculate Spatial Autocorrelation

**Metadata:**
- Genes of Interest: EPCAM, VIM, CD3D, KRT19
- Method: Moran's I
- Spatial Weight Matrix: K-nearest neighbors (k=6)

**Objective:** Detect spatial clustering patterns for marker genes.

**Expected Input:**
- Expression matrix with spatial coordinates

**Action:**
- `mcp-spatialtools` calculate_spatial_autocorrelation

**Acceptance Criteria:**
- Moran's I calculated for all genes
- Report p-values and z-scores
- Identify genes with significant clustering (p<0.01)

**Rationale & Tools:** Reveals spatially organized gene expression patterns indicative of tissue architecture.

**Example Prompt:**
```
Claude, calculate spatial autocorrelation:

1. Compute Moran's I for genes: EPCAM, VIM, CD3D, KRT19
2. Use k-nearest neighbors (k=6) spatial weights
3. Test significance with permutation test (1,000 iterations)
4. Report for each gene:
   - Moran's I statistic
   - Z-score
   - P-value
   - Interpretation (clustered/dispersed/random)

Significance threshold: p<0.01
```

---

## 7️⃣ Predict Cell Types Using ML Model

**Metadata:**
- Model: Geneformer (Hugging Face)
- Model Type: Single-cell foundation model
- Input: Gene expression vectors

**Objective:** Predict cell types for each spatial spot using pre-trained model.

**Expected Input:**
- Expression matrix (TPM-normalized)

**Action:**
- `mcp-huggingface` load_genomic_model --model Geneformer
- `mcp-huggingface` predict_cell_type

**Acceptance Criteria:**
- Cell type predictions for ≥95% spots
- Confidence scores ≥0.7 for ≥80% predictions
- Identify ≥5 distinct cell types

**Rationale & Tools:** Leverages ML to annotate spatial data with cell type identities.

**Example Prompt:**
```
Claude, predict cell types using Geneformer:

1. Load Geneformer model from Hugging Face
2. Normalize expression matrix (TPM)
3. Predict cell types for all spots
4. Report:
   - Cell type predictions with confidence scores
   - Distribution of cell types across tissue
   - Spatial distribution of major cell types
   - Low-confidence predictions (<0.7)

Requirements:
- Predictions for ≥95% spots
- Confidence ≥0.7 for ≥80% of predictions
```

---

## 8️⃣ Integrate Clinical Metadata

**Metadata:**
- Patient ID: PT00001
- Clinical Endpoint: Treatment response
- Sample Type: Pre-treatment tumor biopsy

**Objective:** Link spatial sample to clinical data and correlate gene expression with outcomes.

**Expected Input:**
- Spatial expression data
- Clinical metadata (patient records)

**Action:**
- `mcp-mockepic` query_patient_records PT00001
- `mcp-mockepic` link_spatial_to_clinical

**Acceptance Criteria:**
- Successful linkage of sample to patient record
- Clinical variables retrieved: age, diagnosis, treatment, response
- Ready for correlation analysis

**Rationale & Tools:** Enables translational research by connecting molecular data to clinical outcomes.

**Example Prompt:**
```
Claude, integrate clinical data:

1. Query patient record for PT00001
2. Retrieve:
   - Demographics (age, sex, ethnicity)
   - Diagnosis (ICD-10, stage)
   - Treatment history
   - Response status (complete/partial/stable/progressive)
3. Link spatial sample SAMPLE00001 to patient PT00001
4. Prepare data for correlation analysis between gene expression and treatment response

Verify all required clinical fields are present
```

---

## 9️⃣ Compare to TCGA Reference Cohort

**Metadata:**
- TCGA Cohort: BRCA (Breast Invasive Carcinoma)
- Genes: EPCAM, ESR1, PGR, ERBB2, TP53
- Tissue Type: Primary tumor

**Objective:** Compare sample gene expression to TCGA population statistics.

**Expected Input:**
- Tumor region expression data from Steps 4-5
- Gene list for comparison

**Action:**
- `mcp-tcga` query_tcga_cohorts --cancer-type BRCA
- `mcp-tcga` fetch_expression_data
- `mcp-tcga` compare_to_cohort

**Acceptance Criteria:**
- TCGA cohort data retrieved (≥500 samples)
- Statistical comparison for all requested genes
- Report z-scores and percentiles
- Identify outlier genes (|z-score| >2)

**Rationale & Tools:** Contextualizes sample within larger cancer genomics landscape.

**Example Prompt:**
```
Claude, compare to TCGA BRCA cohort:

1. Query TCGA BRCA cohort (primary tumors)
2. Fetch expression data for: EPCAM, ESR1, PGR, ERBB2, TP53
3. Compare my tumor sample expression to TCGA population
4. Report for each gene:
   - My sample expression (TPM)
   - TCGA mean ± SD
   - Z-score
   - Percentile rank
   - Interpretation (higher/lower/similar)

Cohort size requirement: ≥500 TCGA samples
```

---

## 🔟 Perform Pathway Enrichment Analysis

**Metadata:**
- Gene Set: Upregulated genes from Step 5 (tumor vs. normal)
- Database: GO Biological Process
- Enrichment Method: Fisher's exact test

**Objective:** Identify enriched biological pathways in tumor regions.

**Expected Input:**
- List of differentially expressed genes (upregulated in tumor)

**Action:**
- `mcp-spatialtools` perform_pathway_enrichment

**Acceptance Criteria:**
- ≥10 significantly enriched pathways (FDR <0.05)
- Fold enrichment ≥2.0
- Report top 10 pathways with gene overlap

**Rationale & Tools:** Translates gene lists into biological insights.

**Example Prompt:**
```
Claude, perform pathway enrichment:

1. Use upregulated genes from tumor vs. normal DE analysis
2. Query GO Biological Process database
3. Test enrichment using Fisher's exact test
4. Apply Benjamini-Hochberg FDR correction
5. Report top 10 pathways with:
   - Pathway ID and name
   - Genes overlapping
   - P-value and FDR
   - Fold enrichment
   - Biological interpretation

Filters: FDR <0.05, fold enrichment ≥2.0
```

---

## 1️⃣1️⃣ Cell Segmentation with Deep Learning

**Metadata:**
- Model: DeepCell Membrane Segmentation
- Input: H&E image (4096×4096)
- Minimum Cell Size: 100 pixels

**Objective:** Segment individual cells from histology image.

**Expected Input:**
- Registered H&E image from Step 4

**Action:**
- `mcp-deepcell` segment_cells --model-type membrane

**Acceptance Criteria:**
- ≥1,000 cells segmented
- Mean cell area: 500-2,000 pixels
- Model confidence ≥0.85
- Export segmentation masks (GeoJSON)

**Rationale & Tools:** Enables single-cell spatial analysis from tissue images.

**Example Prompt:**
```
Claude, segment cells using DeepCell:

1. Load DeepCell membrane segmentation model
2. Process registered H&E image (IMG00001)
3. Segment individual cells (min size: 100 pixels)
4. Generate segmentation mask
5. Report:
   - Total cells detected
   - Mean cell area and distribution
   - Model confidence scores
   - Quality metrics (cells filtered)

Target: ≥1,000 cells, confidence ≥0.85
```

---

## 1️⃣2️⃣ Multi-Sample Batch Correction

**Metadata:**
- Samples: 3 patients (PT00001, PT00002, PT00003)
- Batch Effect: Sample processing date
- Method: ComBat

**Objective:** Remove batch effects while preserving biological variation.

**Expected Input:**
- Expression matrices from 3 samples
- Batch labels (processing dates)

**Action:**
- `mcp-spatialtools` perform_batch_correction

**Acceptance Criteria:**
- Batch variance reduction ≥60%
- kBET score improvement ≥0.3
- Biological signal preserved (tested via known markers)

**Rationale & Tools:** Enables multi-sample integration for population-level studies.

**Example Prompt:**
```
Claude, perform batch correction:

1. Load expression data from 3 patient samples
2. Batch labels:
   - PT00001: Batch A (2024-01-15)
   - PT00002: Batch A (2024-01-15)
   - PT00003: Batch B (2024-02-10)
3. Apply ComBat batch correction
4. Report:
   - Variance before/after correction
   - kBET score before/after
   - PCA plots (before/after)
   - Known marker gene expression preservation

Target: ≥60% variance reduction, kBET improvement ≥0.3
```

---

## 1️⃣3️⃣ Nextflow Pipeline Orchestration

**Metadata:**
- Pipeline: nf-core/rnaseq v3.12
- Compute Environment: AWS Batch
- Reference: GRCh38

**Objective:** Execute complete RNA-seq analysis pipeline via Seqera Platform.

**Expected Input:**
- FASTQ files from Step 1
- Sample sheet (CSV)

**Action:**
- `mcp-seqera` launch_nextflow_pipeline
- `mcp-seqera` monitor_workflow_status

**Acceptance Criteria:**
- Pipeline completes successfully
- All QC metrics PASS
- Generate: counts, BAMs, MultiQC report
- Execution time <2 hours (for 10K reads)

**Rationale & Tools:** Demonstrates scalable, reproducible workflow orchestration.

**Example Prompt:**
```
Claude, launch Nextflow RNA-seq pipeline:

1. List available nf-core/rnaseq pipelines
2. Launch version 3.12 with parameters:
   - Input: FASTQ files (sample_001_R1, R2)
   - Reference: GRCh38
   - Compute: AWS Batch
   - Output: S3 bucket
3. Monitor workflow status
4. Report:
   - Pipeline execution status
   - Resource usage (CPU, memory)
   - QC metrics from MultiQC
   - Output file locations

Expected completion: <2 hours
```

---

## 1️⃣4️⃣ Generate Comprehensive QC Report

**Metadata:**
- Report Type: Multi-stage QC aggregation
- Stages: FASTQ QC, Alignment QC, Expression QC, Spatial QC

**Objective:** Aggregate QC metrics from all pipeline stages into single report.

**Expected Input:**
- QC outputs from Steps 1-13

**Action:**
- Aggregate metrics from all MCP servers
- Generate summary report (Markdown/HTML)

**Acceptance Criteria:**
- All QC stages represented
- Traffic light indicators (PASS/WARN/FAIL)
- Interactive visualizations
- Export as HTML report

**Rationale & Tools:** Provides holistic view of data quality for publication/sharing.

**Example Prompt:**
```
Claude, generate comprehensive QC report:

1. Aggregate QC metrics from all pipeline stages:
   - FASTQ quality (mean Phred, read counts)
   - Alignment stats (mapping rate, duplicates)
   - Expression QC (spots, genes, UMIs)
   - Spatial QC (registration error, region detection)
   - Cell segmentation (cells detected, confidence)

2. Generate report with:
   - Executive summary (PASS/WARN/FAIL for each stage)
   - Detailed metrics tables
   - Visualization plots (quality distributions)
   - Recommendations for failed checks

3. Export as HTML report with embedded plots

All stages should PASS for publication-ready data
```

---

## 1️⃣5️⃣ Survival Analysis with Gene Expression

**Metadata:**
- TCGA Cohort: BRCA
- Gene: TP53
- Survival Type: Overall survival
- Split: High vs. Low expression (median cutoff)

**Objective:** Correlate gene expression with patient survival outcomes.

**Expected Input:**
- Gene expression data
- TCGA survival data

**Action:**
- `mcp-tcga` get_survival_data --gene TP53 --expression-threshold median

**Acceptance Criteria:**
- Survival curves for high/low expression groups
- Log-rank p-value <0.05
- Hazard ratio with 95% CI
- Median survival times for each group

**Rationale & Tools:** Links molecular features to clinical outcomes.

**Example Prompt:**
```
Claude, perform survival analysis:

1. Query TCGA BRCA cohort survival data
2. Gene of interest: TP53
3. Split patients by TP53 expression (median cutoff)
4. Compare overall survival between:
   - High TP53 expression group
   - Low TP53 expression group
5. Report:
   - Median survival (months) for each group
   - 5-year survival rates
   - Log-rank test p-value
   - Hazard ratio (95% CI)
   - Kaplan-Meier curves

Significance threshold: p<0.05
```

---

## 1️⃣6️⃣ Complete End-to-End Pipeline

**Metadata:**
- Sample: Breast cancer spatial transcriptomics
- Complete workflow from FASTQ to biological insights

**Objective:** Execute complete analysis pipeline integrating all MCP servers.

**Expected Input:**
- Raw FASTQ files
- H&E histology image
- Patient clinical data

**Action:**
- All MCP servers in sequence

**Acceptance Criteria:**
- All 15 previous steps complete successfully
- Final deliverables:
  - Quality-controlled expression matrix
  - Cell type annotations
  - Differential expression results
  - Pathway enrichment analysis
  - Clinical correlations
  - TCGA comparison
  - Comprehensive QC report

**Rationale & Tools:** Demonstrates complete AI-orchestrated spatial transcriptomics analysis.

**Example Prompt:**
```
Claude, execute complete end-to-end analysis:

Starting data:
- FASTQ files: sample_001_R1.fastq.gz, sample_001_R2.fastq.gz
- H&E image: IMG00001
- Patient: PT00001
- Platform: 10x Visium
- Tissue: Breast cancer

Execute full pipeline:
1. Validate FASTQ files (target: Phred ≥30)
2. Extract UMIs (read structure: 16M12M+T)
3. Align reads to GRCh38 (target: ≥80% mapped)
4. QC filtering (min 1,000 reads, 200 genes per spot)
5. Register H&E to spatial coordinates
6. Segment tissue regions (tumor, stroma, immune, normal)
7. Cell type prediction using Geneformer
8. Differential expression (tumor vs. normal)
9. Spatial autocorrelation (marker genes)
10. Pathway enrichment (tumor-specific genes)
11. Link to clinical data (PT00001)
12. Compare to TCGA BRCA cohort
13. Generate comprehensive QC report

Provide final summary with:
- Key biological findings
- QC status (all stages)
- Publication-ready figures
- Recommended next steps
```

---

## 1️⃣7️⃣ Mutation Data Integration

**Metadata:**
- TCGA Cohort: BRCA
- Genes: TP53, PIK3CA, BRCA1, BRCA2
- Mutation Types: All (missense, nonsense, frameshift)

**Objective:** Query mutation frequencies in TCGA and correlate with gene expression.

**Expected Input:**
- Gene list from differential expression analysis

**Action:**
- `mcp-tcga` get_mutation_data

**Acceptance Criteria:**
- Mutation frequencies retrieved for all genes
- Breakdown by mutation type
- Comparison with sample expression levels

**Rationale & Tools:** Links expression patterns to known mutation landscapes.

**Example Prompt:**
```
Claude, retrieve mutation data from TCGA:

1. Query TCGA BRCA cohort for mutation data
2. Genes: TP53, PIK3CA, BRCA1, BRCA2
3. Report for each gene:
   - Overall mutation frequency
   - Mutation types (missense, nonsense, frameshift, splice)
   - Number of mutated samples
   - Hotspot mutations (if known)
4. Correlate with my sample's expression:
   - High expression + high mutation frequency
   - Potential driver alterations

Cohort: TCGA BRCA (≥500 samples)
```

---

## 1️⃣8️⃣ CosMx Platform Data Integration

**Metadata:**
- Platform: NanoString CosMx SMI
- Panel: 1,000-plex human whole transcriptome
- Resolution: Single-cell

**Objective:** Validate compatibility with alternative spatial platform.

**Expected Input:**
- CosMx FOV (field of view) data
- Cell-by-gene expression matrix
- Cell segmentation boundaries (polygon coordinates)

**Action:**
- `mcp-spatialtools` with CosMx format adaptation
- `mcp-deepcell` for cell boundary validation

**Acceptance Criteria:**
- Successful data import
- Cell segmentation matches CosMx boundaries
- Expression correlation with Visium data ≥0.7 (for shared genes)

**Rationale & Tools:** Demonstrates platform flexibility and cross-validation.

**Example Prompt:**
```
Claude, process CosMx SMI data:

1. Load CosMx FOV data (1,000-plex panel)
2. Import cell segmentation boundaries (polygon coordinates)
3. Validate cell-by-gene expression matrix
4. Compare with Visium data from same tissue:
   - Correlate shared genes
   - Compare cell type distributions
   - Validate spatial patterns
5. Report:
   - Number of cells detected
   - Genes measured
   - Spatial resolution comparison
   - Cross-platform correlation

Target correlation: ≥0.7 for shared genes
```

---

## Summary

### Key Characteristics

✅ **Auditable:** Every step has measurable acceptance criteria
✅ **Realistic:** All tools and models map to actual MCP servers and bioinformatics software
✅ **Extensible:** Can adapt to other spatial or multimodal assays (CosMx, MERFISH, Slide-seq)
✅ **Testable:** Ready for use in MCP orchestration and benchmarking
✅ **Comprehensive:** Covers complete workflow from raw data to biological insights

### MCP Server Coverage

| Server | Prompts Using |
|--------|---------------|
| mcp-fgbio | 1, 2, 3, 13, 16 |
| mcp-spatialtools | 1, 3, 4, 5, 6, 10, 12, 16, 18 |
| mcp-openimagedata | 4, 16, 18 |
| mcp-seqera | 2, 13, 16 |
| mcp-huggingface | 7, 16 |
| mcp-deepcell | 4, 11, 16, 18 |
| mcp-mockepic | 8, 16 |
| mcp-tcga | 9, 15, 17, 16 |

### Validation Metrics

All prompts include quantitative acceptance criteria:
- FASTQ quality: Phred ≥30
- Alignment rate: ≥80%
- UMI duplication: ≤10%
- Barcode matching: ≥95%
- QC retention: ≥80%
- Statistical significance: p<0.05, FDR<0.05
- Spatial correlation: ≥0.7
- Model confidence: ≥0.7 for ≥80% predictions

### Platform Support

- ✅ 10x Genomics Visium
- ✅ NanoString CosMx SMI
- ✅ Slide-seq (adaptable)
- ✅ MERFISH (adaptable)
- ✅ Standard formats: FASTQ, BAM, OME-TIFF, GeoJSON

---

**Document Version:** 2.0
**Last Updated:** October 24, 2025
**Status:** ✅ Complete - All 8 MCP servers covered
