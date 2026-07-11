# Multi-Omics Integration Prompts

Copy-paste prompts for integrating RNA, protein, and phosphoproteomics data.

**Servers used:** mcp-multiomics (10 tools), mcp-fgbio (4 tools)

---

## Data Loading & Validation

### 1. Load Multi-Omics Datasets

**Objective:** Load RNA, protein, and phospho data for a patient

```
Load multi-omics data for PatientOne (PAT001-OVC-2025):
- RNA: /data/patient-data/PAT001-OVC-2025/multiomics/rna_counts.csv
- Protein: /data/patient-data/PAT001-OVC-2025/multiomics/protein_abundance.csv
- Phospho: /data/patient-data/PAT001-OVC-2025/multiomics/phospho_abundance.csv

Summarize each dataset:
- Number of samples
- Number of features (genes/proteins)
- Sample groups (tumor vs. normal)
- Data quality metrics
```

**Expected Output:**
- RNA: 15 samples, 200 genes
- Protein: 15 samples, 150 proteins
- Phospho: 15 samples, 120 phosphosites
- Groups: 10 tumor, 5 normal samples
- Quality: All datasets normalized and QC-passed

**Customize:**
- Replace file paths with your data location
- Add specific QC checks: `Check for missing values, outliers`

---

### 2. Validate Data Format

**Objective:** Check that multi-omics files are properly formatted

```
Validate the format of PatientOne multi-omics files:

For each file (RNA, protein, phospho), check:
- CSV format with headers
- Sample IDs match across modalities
- Numeric values (no text in data columns)
- No excessive missing data (< 20% NAs)
- Appropriate value ranges (log2 for RNA, raw for protein/phospho)

Report any formatting issues or inconsistencies.
```

**Expected Output:**
- ✓ All files: Valid CSV format
- ✓ Sample IDs: Consistent across modalities (15 samples)
- ✓ Data types: All numeric
- ✓ Missing data: <5% per modality
- ⚠ Note: RNA data is log2-transformed, protein/phospho are raw abundances

**Customize:**
- Adjust missing data threshold
- Add specific validation rules

---

## Differential Expression Analysis

### 3. RNA Differential Expression

**Objective:** Find genes differentially expressed between conditions

```
Perform differential expression analysis on PatientOne RNA data:
- Compare: Tumor vs. Normal samples
- Method: Mann-Whitney U test (non-parametric)
- Correction: Benjamini-Hochberg FDR
- Threshold: FDR < 0.05, log2FC > 1

Return:
- Top 20 upregulated genes (ranked by fold change)
- Top 20 downregulated genes
- Total significant genes
- Volcano plot visualization
```

**Expected Output:**
- Significant genes: 45 (23 up, 22 down)
- Top upregulated: TP53, MYC, VEGFA, ...
- Top downregulated: BRCA1, PTEN, ...
- Volcano plot: [visualization]

**Customize:**
- Change comparison: `Compare: Pre-treatment vs. Post-treatment`
- Adjust thresholds: `FDR < 0.01, log2FC > 1.5`
- Change method: `Method: Welch's t-test`

---

### 4. Protein Differential Abundance

**Objective:** Find proteins differentially abundant between conditions

```
Perform differential abundance analysis on PatientOne protein data:
- Compare: Tumor vs. Normal samples
- Method: Mann-Whitney U test
- Correction: Benjamini-Hochberg FDR
- Threshold: FDR < 0.05, fold change > 1.5x

Return:
- Top 15 upregulated proteins
- Top 15 downregulated proteins
- Overlap with RNA findings (correlation)
```

**Expected Output:**
- Significant proteins: 28 (14 up, 14 down)
- Top upregulated: TP53, MYC, EGFR, ...
- RNA-protein correlation: 67% concordance

**Customize:**
- Adjust fold change: `fold change > 2x` (more stringent)
- Add protein families: `Focus on kinases and transcription factors`

---

### 5. Phosphoprotein Analysis

**Objective:** Identify differentially phosphorylated sites

```
Analyze phosphorylation changes in PatientOne:
- Compare: Tumor vs. Normal samples
- Method: Mann-Whitney U test
- Correction: FDR < 0.05
- Threshold: Fold change > 2x (phosphorylation often has larger changes)

Return:
- Top 10 hyperphosphorylated sites (increased phosphorylation)
- Top 10 hypophosphorylated sites (decreased phosphorylation)
- Kinase enrichment analysis (which kinases might be responsible)
```

**Expected Output:**
- Significant phosphosites: 18 (9 hyper, 9 hypo)
- Top hyper: AKT1_S473, mTOR_S2448, ERK1_T202, ...
- Enriched kinases: AKT, mTOR, MAPK pathway kinases

**Customize:**
- Add kinase prediction: `Use kinase-substrate databases (PhosphoSitePlus)`
- Focus on specific pathways: `Focus on PI3K/AKT/mTOR pathway`

---

## Multi-Omics Integration

### 6. Stouffer Meta-Analysis

**Objective:** Combine p-values across RNA, protein, and phospho

```
Perform Stouffer meta-analysis on PatientOne multi-omics data:
- Modalities: RNA, Protein, Phospho
- Method: Stouffer's Z-score method (weighted by sample size)
- Correction: FDR < 0.05
- Direction: Report concordant changes (same direction across modalities)

Return:
- Top 20 genes/proteins with concordant activation
- Top 20 with concordant repression
- Combined p-values and effect sizes
```

**Expected Output:**
- Concordant activated: 12 genes (significant in ≥2 modalities, same direction)
  - TP53: RNA ↑, Protein ↑ (combined p=1.2e-5)
  - MYC: RNA ↑, Protein ↑, Phospho ↑ (combined p=3.4e-6)
- Concordant repressed: 10 genes
  - BRCA1: RNA ↓, Protein ↓ (combined p=8.7e-4)

**Customize:**
- Require all 3 modalities: `Only report genes significant in all 3 modalities`
- Weight by effect size: `Weight by fold change, not just p-value`

---

### 7. HAllA Association Analysis

**Objective:** Find associations between RNA and protein abundances

```
Run HAllA (Hierarchical All-against-All association testing) on PatientOne data:
- Dataset 1: RNA expression
- Dataset 2: Protein abundance
- Method: Spearman correlation
- FDR: 0.1 (HAllA is exploratory)

Return:
- Top 10 RNA-protein associations
- Correlation coefficients and p-values
- Biological interpretation (known interactions vs. novel)
```

**Expected Output:**
- Significant associations: 23 RNA-protein pairs
- Top association: TP53_RNA ↔ TP53_Protein (r=0.82, p=1.2e-4)
- Novel finding: MYC_RNA ↔ AKT1_Protein (r=0.71, p=3.4e-3)

**Customize:**
- Add phospho: `3-way analysis: RNA, Protein, Phospho`
- Filter by pathway: `Focus on DNA repair pathway genes`

---

### 8. Pathway Enrichment on Integrated Data

**Objective:** Find pathways activated across multiple modalities

```
Perform pathway enrichment on PatientOne integrated multi-omics results:
- Input: Genes significant in Stouffer meta-analysis (FDR < 0.05)
- Databases: KEGG, Hallmark, GO_BP
- Method: Fisher's exact test
- Correction: Benjamini-Hochberg FDR
- Threshold: FDR < 0.05

Return:
- Top 10 enriched pathways
- Genes per pathway
- Overlap statistics (how many genes, expected vs. observed)
```

**Expected Output:**
- Enriched pathways (FDR < 0.05):
  1. PI3K/AKT/mTOR signaling (p=8.2e-5, 8 genes)
  2. DNA damage response (p=1.3e-4, 6 genes)
  3. Cell cycle checkpoints (p=4.7e-4, 5 genes)
  4. MAPK signaling (p=6.1e-3, 4 genes)

**Customize:**
- Add custom pathways: `Include drug resistance pathways`
- Focus on specific databases: `KEGG pathways only`

---

## Upstream Regulator Analysis

### 9. Identify Upstream Kinases

**Objective:** Predict kinases responsible for phosphorylation changes

```
Identify upstream kinases driving PatientOne phosphorylation changes:
- Input: Differentially phosphorylated sites (FDR < 0.05)
- Method: Kinase-substrate enrichment analysis
- Databases: PhosphoSitePlus, Kinase Library
- Threshold: Enrichment p < 0.01

Return:
- Top 5 predicted active kinases
- Target phosphosites per kinase
- Evidence level (known substrates vs. predicted)
```

**Expected Output:**
- Predicted active kinases:
  1. AKT1 (p=1.2e-4, 5 known substrates hyperphosphorylated)
  2. mTOR (p=3.4e-4, 3 known substrates)
  3. ERK1/2 (p=6.7e-3, 2 known substrates)

**Customize:**
- Add kinase inhibitors: `For each kinase, suggest FDA-approved inhibitors`
- Filter by pathway: `Focus on PI3K/AKT/mTOR pathway kinases`

---

### 10. Transcription Factor Activity

**Objective:** Infer transcription factor activity from gene expression

```
Infer transcription factor (TF) activity from PatientOne RNA data:
- Input: Differentially expressed genes (FDR < 0.05)
- Method: TF target enrichment analysis
- Databases: ENCODE, ChEA
- Threshold: Enrichment p < 0.01

Return:
- Top 5 predicted active TFs
- Target genes per TF
- Concordance with protein changes (if TF protein is measured)
```

**Expected Output:**
- Predicted active TFs:
  1. TP53 (p=2.1e-5, 12 target genes upregulated)
  2. MYC (p=4.3e-4, 8 target genes upregulated)
  3. HIF1A (p=8.6e-3, 5 target genes upregulated)

- Concordance check:
  - TP53: Protein mutated (activity loss expected, but targets still upregulated - paradox to investigate)
  - MYC: Protein ↑ (concordant with activity prediction)

**Customize:**
- Add chromatin data: `Integrate with ATAC-seq to confirm open chromatin`
- Focus on druggable TFs: `Prioritize TFs with known inhibitors`

---

## Visualization Prompts

### 11. Create Heatmap of Integrated Data

**Objective:** Visualize multi-omics data together

```
Create a heatmap showing PatientOne multi-omics data:
- Rows: Top 50 genes from Stouffer meta-analysis
- Columns: Samples (tumor vs. normal) × Modalities (RNA, Protein, Phospho)
- Color scale: Z-scores (standardized within each modality)
- Clustering: Hierarchical clustering of genes and samples

Save as: /results/patientone_multiomics_heatmap.png
```

**Expected Output:**
- Heatmap showing concordant changes across modalities
- Tumor samples cluster separately from normal
- Gene clusters: Activated pathways, Repressed pathways

**Customize:**
- Filter by pathway: `Only show PI3K/AKT/mTOR pathway genes`
- Adjust clustering: `Use k-means with k=3 clusters`

---

### 12. Correlation Plot (RNA vs. Protein)

**Objective:** Visualize RNA-protein correlation

```
Create scatter plot comparing RNA vs. Protein for PatientOne:
- X-axis: RNA log2 fold change (tumor vs. normal)
- Y-axis: Protein fold change (tumor vs. normal)
- Points: All measured genes/proteins
- Highlight: Significant in both (FDR < 0.05)
- Add: Correlation coefficient (Spearman r)

Save as: /results/patientone_rna_protein_correlation.png
```

**Expected Output:**
- Correlation: r = 0.67 (moderate positive correlation)
- Concordant genes: 45 (both RNA and protein significant, same direction)
- Discordant genes: 12 (significant in one modality only)

**Customize:**
- Add labels: `Label top 10 genes with largest discordance`
- Filter by pathway: `Only show DNA repair genes`

---

## Advanced Integration

### 13. Identify Post-Translational Regulation

**Objective:** Find genes with protein changes not explained by RNA

```
Identify post-transcriptional regulation in PatientOne:
- Compare: RNA vs. Protein fold changes
- Threshold: |RNA FC| < 1.5 AND |Protein FC| > 2 (protein change without RNA change)
- Mechanism: Possible post-translational regulation (PTM, stability, translation)

Return:
- Genes with protein-only changes
- Phosphorylation status (if phospho data available)
- Predicted regulation mechanisms
```

**Expected Output:**
- Post-translationally regulated genes: 8
  - AKT1: RNA FC=1.2 (NS), Protein FC=2.3 (p=0.003), Phospho ↑↑ (S473)
    - Mechanism: Phosphorylation-mediated activation
  - PTEN: RNA FC=0.9 (NS), Protein FC=0.4 (p=0.008)
    - Mechanism: Protein degradation (ubiquitination?)

**Customize:**
- Adjust thresholds: `Protein FC > 3 for stronger effect`
- Add validation: `Check protein half-life databases`

---

### 14. Time-Series Multi-Omics

**Objective:** Analyze multi-omics changes over time (if longitudinal data)

```
If PatientOne has longitudinal samples (pre-treatment, on-treatment, post-treatment):

Analyze temporal changes across modalities:
- Time points: Pre, Week 4, Week 12, Progression
- Modalities: RNA, Protein, Phospho
- Method: Linear mixed models or spline fitting
- Focus: Genes with dynamic changes

Return:
- Early response genes (change by Week 4)
- Late resistance genes (change at progression)
- Temporal patterns (sustained activation, transient, etc.)
```

**Expected Output:**
- Early response (Week 4):
  - Apoptosis genes ↑ (RNA + Protein)
  - DNA repair genes ↓
- Resistance (Week 12):
  - PI3K/AKT/mTOR ↑↑ (RNA, Protein, Phospho)
  - Drug efflux pumps ↑ (RNA, Protein)

**Customize:**
- Add treatment information: `Correlate changes with drug exposure`
- Predict resistance: `Identify early markers of eventual resistance`

---

## Quality Control

### 15. Batch Effect Assessment

**Objective:** Check for technical batch effects across modalities

```
Assess batch effects in PatientOne multi-omics data:
- Check for: Sample processing batch, run date, instrument
- Method: PCA, visualize PC1 vs. PC2 colored by batch
- Quantify: Variance explained by batch vs. biology

If batch effects detected, recommend correction method (ComBat, limma).
```

**Expected Output:**
- Batch effects detected: Minimal (< 5% variance)
- PCA: PC1 separates tumor/normal (biology), batch has minor effect
- Recommendation: No batch correction needed

**Customize:**
- Apply correction: `Apply ComBat batch correction to all modalities`
- Assess severity: `Calculate silhouette coefficient for batch separation`

---

### 16. Missing Data Analysis

**Objective:** Understand patterns of missing data

```
Analyze missing data patterns in PatientOne multi-omics:
- RNA: % missing per gene, per sample
- Protein: % missing (common in proteomics)
- Phospho: % missing (often higher)

Identify:
- Genes with excessive missingness (> 30%)
- Samples with excessive missingness (> 20%)
- Whether missingness is random (MCAR) or systematic (MNAR)

Recommend imputation strategy if needed.
```

**Expected Output:**
- RNA: 2% missing (minimal)
- Protein: 15% missing (typical for proteomics)
- Phospho: 22% missing (low-abundance phosphosites)
- Pattern: MCAR (missing at random)
- Recommendation: Use k-nearest neighbors imputation for protein/phospho

**Customize:**
- Impute: `Impute missing values using KNN with k=5`
- Filter: `Remove features with >50% missing data`

---

## Clinical Translation

### 17. Druggable Targets from Multi-Omics

**Objective:** Identify treatment opportunities from integrated data

```
From PatientOne multi-omics analysis, identify druggable targets:
- Input: Activated pathways (PI3K/AKT/mTOR, MAPK)
- Criteria:
  * Significant across ≥2 modalities
  * Fold change > 2
  * Known drug targets (FDA-approved or clinical trials)

Return:
- Ranked list of drug targets
- Available drugs (approved, trial, preclinical)
- Evidence level (NCCN, clinical guidelines)
- Expected efficacy based on multi-omics signature
```

**Expected Output:**
1. **mTOR (activated across RNA, Protein, Phospho)**
   - Drug: Everolimus (FDA-approved)
   - Evidence: Level 2 (NCCN Category 2A for PI3K/mTOR activation)
   - Expected response: 30-40% based on signature

2. **AKT1 (hyperphosphorylated at S473)**
   - Drug: Capivasertib (clinical trials)
   - Evidence: Phase III trials in AKT-activated cancers
   - Expected response: 25-35%

**Customize:**
- Combination therapy: `Suggest drug combinations for activated pathways`
- Clinical trials: Use ClinicalTrials.gov connector to search for trials
  targeting activated pathways. Use PubMed for published efficacy data.
  See [Connect External MCP](../../for-researchers/CONNECT_EXTERNAL_MCP.md).

---

## Troubleshooting

**"Sample IDs don't match across modalities"**
- Check: Sample naming conventions (e.g., "Sample_01" vs. "Sample01")
- Solution: Standardize IDs before loading
- Prompt: `Rename samples to match: Sample_01 → Sample01`

**"Too many significant genes (> 1000)"**
- Issue: Threshold too lenient or large effect sizes
- Solution: Increase stringency (FDR < 0.01) or add fold change filter
- Prompt: `Re-analyze with FDR < 0.01 and log2FC > 1.5`

**"No concordance between RNA and protein"**
- Issue: Post-translational regulation, technical noise, or batch effects
- Solution: Check batch effects, assess protein data quality
- Prompt: `Assess batch effects and protein data quality for PatientOne`

**"Stouffer meta-analysis finds nothing"**
- Issue: Effects in opposite directions across modalities
- Solution: Check individual modalities first, may be biology (PTM regulation)
- Prompt: `Compare RNA vs. Protein direction for top DE genes`

---

**Related Prompts:**
- [Clinical-Genomic Prompts](clinical-genomic.md) - Link genomic variants to multi-omics
- [Spatial Prompts](spatial.md) - Add spatial context to omics
- [Complete Workflows](workflows.md) - Integrate everything
