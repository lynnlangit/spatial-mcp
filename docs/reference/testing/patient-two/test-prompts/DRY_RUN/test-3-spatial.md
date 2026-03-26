TEST 3: Spatial Transcriptomics Analysis
=========================================

Patient ID: PAT002-BC-2026

## Spatial Analysis (use mcp-spatialtools)

For patient PAT002-BC-2026, analyze spatial gene expression patterns:

### Data Files Location:
Files at: `patient-data/PAT002-BC-2026/spatial/`
- visium_spatial_coordinates.csv
- visium_gene_expression.csv
- visium_region_annotations.csv

### Pre-Flight Validation:

1. **File existence check:**
   - Confirm all 3 CSV files are accessible

2. **Data integrity check:**
   - Coordinates file: Should have rows with barcode, in_tissue, array_row, array_col, pixel positions
   - Expression file: Should have rows with breast cancer-relevant gene columns
   - Regions file: Should have rows with region labels

3. **Expected genes present:**
   - Verify key breast cancer genes exist in expression file:
     ESR1, PGR, GATA3, MKI67, CCND1, PIK3CA, CD8A, CD68, VIM, KRT18, EPCAM, HER2/ERBB2

4. **Expected regions present:**
   - Breast tissue regions: tumor_core, tumor_invasive_front, stroma, immune_infiltrate, adipose, dcis
   - If any regions missing, report and adjust analysis accordingly

### Analysis Steps:

1. **Load spatial data:**
   - How many spatial spots?
   - What spatial regions are identified?
   - How many spots per region?

2. **Focus on KEY GENES** (breast cancer panel):
   - **Hormone receptors:** ESR1, PGR, GATA3, FOXA1
   - **Proliferation:** MKI67, PCNA, TOP2A
   - **PI3K pathway:** PIK3CA, AKT1, MTOR
   - **Immune:** CD3D, CD8A, CD4, FOXP3, CD68, CD163
   - **Stromal:** VIM, COL1A1, ACTA2, FAP
   - **Epithelial:** KRT8, KRT18, KRT19, EPCAM

3. **Gene expression by region:**
   - Which regions have high ER/PR expression?
   - Where are proliferation markers (MKI67) highest?
   - Where are immune cells (CD8A, CD68) located?
   - Stromal marker distribution?

4. **Spatial patterns:**
   - Is there spatial heterogeneity in hormone receptor expression?
   - Are immune cells infiltrating the tumor or excluded?
   - Tumor-stroma interface patterns?
   - Any DCIS vs invasive component differences?

5. **Generate visualizations:**
   ```
   Tool: generate_spatial_heatmap
   Inputs:
   - expression_file: visium_gene_expression.csv
   - coordinates_file: visium_spatial_coordinates.csv
   - genes: ["ESR1", "PGR", "MKI67", "PIK3CA", "CD8A", "CD68"]
   - colormap: "viridis"
   ```

   ```
   Tool: generate_region_composition_chart
   Inputs:
   - regions_file: visium_region_annotations.csv
   ```

   ```
   Tool: generate_gene_expression_heatmap
   Inputs:
   - expression_file: visium_gene_expression.csv
   - regions_file: visium_region_annotations.csv
   - genes: ["ESR1", "PGR", "GATA3", "MKI67", "PIK3CA", "CD8A", "CD68", "VIM"]
   ```

## Expected Results:

**Expression Patterns:**

| Gene   | High Expression Region | Pattern |
|--------|----------------------|---------|
| ESR1   | tumor_core, dcis     | Strong ER expression |
| PGR    | tumor_core, dcis     | Strong PR expression |
| GATA3  | tumor_core           | Luminal lineage |
| MKI67  | tumor_invasive_front | Moderate proliferation |
| PIK3CA | tumor regions        | PI3K activation |
| CD8A   | immune_infiltrate    | T cell presence |
| CD68   | immune_infiltrate, stroma | Macrophages |
| VIM    | stroma               | Stromal marker |

**Spatial Findings:**
- Hormone receptors: Strongly expressed in tumor regions (consistent with ER+/PR+ status)
- Proliferation: Moderate, heterogeneous (higher at invasive front)
- Immune cells: Present in immune_infiltrate region (mixed immune status)
- Tumor microenvironment: Immunologically "warm" — immune cells present but not deeply infiltrating

## Output Format:

1. **Spatial Structure:** Spot counts per region
2. **Gene Expression Heatmap:** Key genes x regions
3. **Key Spatial Findings:** ER/PR distribution, proliferation, immune patterns
4. **Visualizations:** Spatial heatmaps, region charts
5. **Clinical Interpretation:**
   - Is ER expression homogeneous? (Mostly yes — good for endocrine therapy)
   - Immune microenvironment classification: Warm (mixed infiltration)
   - Implications for treatment: Endocrine therapy likely effective; immunotherapy may have moderate benefit

## Validation Checkpoints:

- Loaded spatial data with region annotations
- ESR1/PGR: High in tumor regions (confirms ER+/PR+)
- MKI67: Moderate (consistent with Luminal A)
- Immune: Mixed infiltration pattern (not fully excluded)
- Heterogeneity: Some spatial variation in ER expression
