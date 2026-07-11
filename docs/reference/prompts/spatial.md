# Spatial Transcriptomics Prompts

Copy-paste prompts for Visium spatial RNA-seq analysis.

**Servers used:** mcp-spatialtools (14 tools), mcp-openimagedata (5 tools)

---

## Data Loading & QC

### 1. Load Visium Spatial Data

```
Load Visium spatial transcriptomics data for PatientOne (PAT001-OVC-2025):
- Data directory: /data/patient-data/PAT001-OVC-2025/spatial/
- Include: Expression matrix, spatial coordinates, tissue images

Summarize:
- Number of spots
- Number of genes detected
- Tissue regions (tumor, normal, stroma)
- Quality metrics (UMI counts, gene counts per spot)
```

**Expected Output:**
- Spots: 900
- Genes: 31 (demonstration) or 18,000+ (production)
- Regions: T1 (tumor core), T2 (tumor edge), N1 (normal)
- Median UMI/spot: 5,000-15,000

---

### 2. Quality Control Spatial Data

```
Perform quality control on PatientOne spatial data:
- Filter low-quality spots (< 500 UMI or < 200 genes)
- Identify outlier spots (extreme UMI counts)
- Check spatial distribution (any technical artifacts?)
- Visualize QC metrics on tissue

Return:
- Number of spots before/after filtering
- QC visualization overlaid on tissue
```

**Expected Output:**
- Before: 900 spots
- After: 875 spots (25 low-quality removed)
- Artifacts: None detected

---

## Spatial Differential Expression

### 3. Compare Tumor vs. Normal Regions

```
Perform spatial differential expression comparing PatientOne tumor (T1, T2) vs. normal (N1) regions:
- Method: Mann-Whitney U test
- Correction: Benjamini-Hochberg FDR
- Threshold: FDR < 0.05, log2FC > 1

Return:
- Top 20 upregulated genes in tumor
- Top 20 downregulated genes in tumor
- Spatial expression maps for top 5 genes
```

**Expected Output:**
- Significant genes: 45 (23 up, 22 down)
- Top upregulated: MYC, VEGFA, HIF1A
- Spatial pattern: High expression in tumor core, low at edges

---

### 4. Identify Spatially Variable Genes (Moran's I)

```
Identify spatially variable genes in PatientOne using Moran's I spatial autocorrelation:
- Spatial graph: k=6 nearest neighbors
- Threshold: p < 0.05
- Filter: Only genes expressed in > 20% of spots

Return:
- List of spatially variable genes
- Moran's I statistic for each
- Spatial expression pattern (clustered, dispersed, random)
```

**Expected Output:**
- Spatially variable genes: 12
- Top genes: VEGFA (I=0.68, p=1.2e-5, clustered in hypoxic regions)
- Pattern: Most show clustering in tumor core

---

## Spatial Pathway Analysis

### 5. Spatial Pathway Enrichment

```
Perform pathway enrichment on PatientOne spatial data by region:
- Regions: Tumor core (T1), Tumor edge (T2), Normal (N1)
- Method: Fisher's exact test on 44 curated pathways
- Threshold: FDR < 0.05

Return:
- Enriched pathways per region
- Spatial visualization showing pathway scores
- Heatmap: Regions × Pathways
```

**Expected Output:**
- Tumor core: Hypoxia, angiogenesis, EMT
- Tumor edge: Immune response, cell adhesion
- Normal: Metabolic pathways, homeostasis

---

### 6. Pathway Score Spatial Mapping

```
Calculate and visualize pathway scores for PatientOne:
- Pathways: PI3K/AKT/mTOR, DNA repair, Immune response
- Method: Gene set enrichment per spot
- Visualization: Overlay scores on tissue image

Save spatial maps for each pathway.
```

**Expected Output:**
- PI3K/AKT/mTOR: High in tumor core (hypoxic regions)
- DNA repair: Moderate throughout tumor
- Immune response: High at tumor edges, low in core

---

## Cell Type Analysis

### 7. Cell Type Deconvolution

```
Perform cell type deconvolution on PatientOne spatial data:
- Signatures: Tumor epithelial, Fibroblasts, T-cells, Macrophages, Hypoxic
- Method: Signature-based scoring
- Threshold: Score > 0.5 for positive assignment

Return:
- Cell type proportions per spot
- Spatial distribution of each cell type
- Co-localization analysis (which cell types are near each other)
```

**Expected Output:**
- Tumor epithelial: 60% of spots (concentrated in core)
- Fibroblasts: 25% (stromal regions)
- T-cells: 10% (tumor edges, not core - immune exclusion)
- Macrophages: 5% (scattered)

---

### 8. Tumor-Immune Interaction Zones

```
Identify tumor-immune interaction zones in PatientOne:
- Define: Spots with both tumor cells AND immune cells (T-cells, macrophages)
- Analyze: Gene expression signatures in interaction zones
- Compare: Interaction zones vs. immune-excluded tumor core

What genes are upregulated in interaction zones?
Are immune checkpoint genes expressed?
```

**Expected Output:**
- Interaction zones: 85 spots at tumor-normal boundary
- Upregulated: PD-L1, CTLA4, LAG3 (immune checkpoints)
- Core: PD-L1 high but NO immune cells (immune exclusion)
- Recommendation: Checkpoint inhibitors might work at edges, but core is protected

---

## Batch Correction

### 9. Apply ComBat Batch Correction

```
Apply ComBat batch correction to PatientOne spatial data:
- Batch variable: Tissue section (if multiple sections)
- Preserve: Biological variation (tumor vs. normal)
- Method: Empirical Bayes batch correction

Compare:
- PCA before batch correction
- PCA after batch correction
- Verify tumor/normal separation preserved
```

**Expected Output:**
- Batch effect: 12% of variance (PC2)
- After ComBat: Batch effect reduced to 3%
- Biology preserved: Tumor/normal still separate (PC1)

---

## Spatial Neighborhood Analysis

### 10. Identify Spatial Neighborhoods

```
Identify spatial neighborhoods in PatientOne tissue:
- Method: Graph-based clustering (Leiden algorithm)
- Spatial graph: k=6 nearest neighbors
- Resolution: 0.5 (moderate granularity)

Return:
- Number of neighborhoods identified
- Spatial map of neighborhoods
- Characterization: What cell types/pathways define each neighborhood?
```

**Expected Output:**
- Neighborhoods: 5
  1. Tumor core (hypoxic, proliferative)
  2. Tumor edge (invasive, EMT)
  3. Stromal (fibroblasts, ECM)
  4. Immune-rich (T-cells, macrophages)
  5. Normal tissue

---

### 11. Cell-Cell Communication

```
Infer cell-cell communication in PatientOne spatial data:
- Method: Ligand-receptor pair analysis
- Focus: Tumor-stroma interactions, tumor-immune interactions
- Database: CellPhoneDB, NicheNet

Return:
- Significant ligand-receptor pairs
- Spatial proximity of interacting cell types
- Predicted signaling pathways activated
```

**Expected Output:**
- Tumor→Stroma: VEGFA→VEGFR2 (angiogenesis)
- Tumor→Immune: PD-L1→PD-1 (immune suppression)
- Stroma→Tumor: TGF-β→TGF-βR (EMT induction)

---

## Visualization

### 12. Create Spatial Expression Heatmap

```
Create spatial gene expression heatmap for PatientOne:
- Genes: Top 20 from differential expression
- Layout: Spot coordinates on tissue
- Color scale: Normalized expression (Z-score)
- Overlay: Tissue H&E image (semi-transparent)

Save as high-resolution PNG.
```

---

### 13. 3D Spatial Visualization

```
Create 3D visualization of PatientOne spatial data (if multiple tissue sections):
- X, Y: Spot coordinates within section
- Z: Section depth
- Color: Gene expression or pathway score
- Interactive: Rotate, zoom, select regions

Focus on: PI3K/AKT/mTOR pathway score across sections.
```

---

## Advanced Spatial Analysis

### 14. Spatial Gradient Analysis

```
Analyze spatial gradients in PatientOne tumor:
- Direction: Core → Edge → Normal
- Genes: Hypoxia markers (HIF1A, VEGFA, CA9)
- Method: Calculate expression gradient along tumor axis

Return:
- Gradient profile (distance from core vs. expression)
- Genes with strongest gradients
- Interpretation: Hypoxic gradient from center outward
```

**Expected Output:**
- HIF1A: Strong gradient (high in core, low at edges)
- VEGFA: Moderate gradient
- Interpretation: Hypoxic core driving angiogenesis

---

### 15. Spatial Heterogeneity Quantification

```
Quantify spatial heterogeneity in PatientOne tumor:
- Metric: Shannon entropy of gene expression per spot
- Compare: Tumor core vs. edge vs. normal
- Interpretation: High heterogeneity = complex microenvironment

Return:
- Heterogeneity scores per region
- Genes contributing most to heterogeneity
- Clinical implications (heterogeneity associated with resistance)
```

**Expected Output:**
- Tumor core: High heterogeneity (entropy=3.2)
- Tumor edge: Moderate (entropy=2.4)
- Normal: Low (entropy=1.1)
- Top heterogeneous genes: MYC, EGFR, HIF1A

---

### 16. Spatial Co-expression Networks

```
Build spatial co-expression networks for PatientOne:
- Method: Calculate gene-gene correlations within spatial neighborhoods
- Threshold: |r| > 0.7, p < 0.01
- Visualization: Network graph (nodes=genes, edges=correlations)

Identify:
- Hub genes (highly connected)
- Modules (gene clusters)
- Spatial modules (genes co-expressed in specific regions)
```

**Expected Output:**
- Hub genes: TP53, MYC, VEGFA (>10 connections each)
- Modules: 3
  1. Hypoxia module (HIF1A, VEGFA, CA9)
  2. Proliferation module (MYC, CCND1, E2F1)
  3. Immune module (CD3D, CD8A, GZMB)

---

## Integration with Other Modalities

### 17. Link Spatial to H&E Histology

```
Integrate PatientOne spatial transcriptomics with H&E histology:
- Load: H&E slide image
- Register: Align H&E with spatial coordinates
- Annotate: Tumor regions, necrosis, stroma from pathologist
- Correlate: Gene expression with histological features

Do high-proliferation spots correspond to densely cellular H&E regions?
```

**Expected Output:**
- Alignment: Successful (RMSE < 10 pixels)
- Correlation: High VEGFA → hypoxic/necrotic regions on H&E
- Validation: Pathologist annotations match spatial clusters

---

### 18. Combine Spatial + Bulk Multi-Omics

```
Integrate PatientOne spatial transcriptomics with bulk multi-omics:
- Spatial: Regional gene expression
- Bulk RNA: Confirm overall expression patterns
- Bulk Protein: Validate protein-level changes

Question: Do spatial upregulated genes match bulk RNA/protein?
Are there region-specific effects not captured in bulk?
```

**Expected Output:**
- Concordance: 70% of spatial DE genes significant in bulk RNA
- Region-specific: Immune genes high at edges, not detected in bulk (diluted by tumor-dominant signal)
- Protein validation: VEGFA high in both spatial and bulk protein

---

## Troubleshooting

**"Spatial coordinates missing"**
- Check: `tissue_positions.csv` file present
- Solution: Ensure Visium output includes spatial folder

**"Too few spatially variable genes"**
- Issue: Spatial graph too sparse or threshold too stringent
- Solution: Increase k (neighbors) or relax p-value
- Prompt: `Re-run Moran's I with k=10 and p < 0.1`

**"Batch effects dominate PCA"**
- Issue: Technical variation > biological variation
- Solution: Apply ComBat before downstream analysis
- Prompt: `Apply ComBat batch correction using section ID as batch variable`

**"No enriched pathways found"**
- Issue: Gene set too small or pathways not relevant
- Solution: Use gene-level results or expand pathway databases
- Prompt: `Try GO Biological Process instead of KEGG`

---

**Related Prompts:**
- [Clinical-Genomic](clinical-genomic.md) - Link spatial to clinical phenotype
- [Multi-Omics](multiomics.md) - Integrate spatial with bulk RNA/protein
- [Workflows](workflows.md) - Complete spatial workflows
