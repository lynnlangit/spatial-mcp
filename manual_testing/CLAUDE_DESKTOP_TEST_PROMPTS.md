# Claude Desktop Test Prompts (with Absolute Paths)

**IMPORTANT:** Claude Desktop runs in a sandboxed environment. Always use **absolute paths** to your data files, not relative paths.

---

## Test Prompt #1: Validate FASTQ Files ✅ START HERE

**What it tests:** mcp-fgbio server, validate_fastq tool

**Paste this into Claude Desktop:**

```
Claude, I have a 10x Visium spatial transcriptomics dataset with paired FASTQ files. Please:

1. Validate FASTQ quality for both R1 and R2 files (target: mean Phred ≥30)
2. Check the barcode format and structure
3. Report the total number of reads and quality metrics

Files:
- /Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/fastq/sample_001_R1.fastq.gz
- /Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/fastq/sample_001_R2.fastq.gz

Use the mcp-fgbio server to validate these files.
```

**Expected result:**
- Total reads: 10,000 per file
- Mean quality: Q35-36
- Status: PASS
- Confirmation data is suitable for analysis

---

## Test Prompt #2: Extract UMIs

**What it tests:** mcp-fgbio server, extract_umis tool

**Paste this:**

```
Claude, please extract UMIs from the R1 FASTQ file using this read structure:
- 16bp spatial barcode
- 12bp UMI
- Remaining: polyT sequence

Input file:
/Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/fastq/sample_001_R1.fastq.gz

Output directory:
/Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/output/

Use the mcp-fgbio server's extract_umis tool.
```

---

## Test Prompt #3: Spatial Autocorrelation Analysis

**What it tests:** mcp-spatialtools server, calculate_spatial_autocorrelation tool

**Paste this:**

```
Claude, I have a spatial transcriptomics expression matrix. Please calculate spatial autocorrelation (Moran's I) for these marker genes:
- EPCAM (epithelial marker)
- VIM (stromal marker)
- CD3D (immune marker)
- KRT19 (tumor marker)

Expression matrix file:
/Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/spatial/expression_matrix.json

Use the mcp-spatialtools server to calculate spatial autocorrelation and tell me which genes show significant spatial clustering (p < 0.01).
```

**Expected result:**
- Moran's I statistics for each gene
- P-values showing significance
- Interpretation (clustered/dispersed/random)

---

## Test Prompt #4: TCGA Comparison

**What it tests:** mcp-tcga server, compare_to_cohort tool

**Paste this:**

```
Claude, I have breast cancer spatial transcriptomics data. Please compare the expression of key marker genes to the TCGA BRCA (Breast Cancer) cohort:

Genes to compare:
- EPCAM: 2500 TPM
- ESR1: 1800 TPM
- ERBB2: 950 TPM
- TP53: 450 TPM

Use the mcp-tcga server to:
1. Query the BRCA cohort
2. Compare my sample's expression to the population
3. Report z-scores and percentiles
4. Identify which genes are outliers (|z-score| > 2)
```

**Expected result:**
- TCGA cohort size (should be >500 samples)
- Z-scores for each gene
- Percentile ranks
- Interpretation (higher/lower/similar to population)

---

## Test Prompt #5: Differential Expression Analysis

**What it tests:** mcp-spatialtools server, perform_differential_expression tool

**Paste this:**

```
Claude, please perform differential expression analysis on my spatial transcriptomics data:

Expression matrix:
/Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/spatial/expression_matrix.json

Compare:
- Group 1: Tumor regions
- Group 2: Normal regions

Use the mcp-spatialtools server to:
1. Perform Wilcoxon rank-sum test
2. Filter for genes with |log2FC| ≥ 1 and FDR < 0.05
3. Report the top 10 upregulated and top 10 downregulated genes
```

**Expected result:**
- List of significant genes
- Log2 fold-changes
- Adjusted p-values
- Biological interpretation

---

## Test Prompt #6: Pathway Enrichment

**What it tests:** mcp-spatialtools server, perform_pathway_enrichment tool

**Paste this:**

```
Claude, I have a list of genes upregulated in tumor regions. Please perform pathway enrichment analysis:

Genes: EPCAM, KRT19, KRT7, MKI67, PCNA, TOP2A, CCND1, MYC

Use the mcp-spatialtools server to:
1. Query GO Biological Process database
2. Find enriched pathways (FDR < 0.05, fold enrichment ≥ 2.0)
3. Report the top 10 pathways with genes overlapping

What biological processes are enriched in these tumor-upregulated genes?
```

---

## Test Prompt #7: Cell Type Prediction

**What it tests:** mcp-huggingface server, predict_cell_type tool

**Paste this:**

```
Claude, please use the Geneformer model to predict cell types in my spatial transcriptomics data:

Expression matrix:
/Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/spatial/expression_matrix.json

Use the mcp-huggingface server to:
1. Load the Geneformer model
2. Predict cell types for all spots
3. Report the distribution of cell types
4. Identify spots with low confidence predictions (<0.7)

Expected cell types: Epithelial, Stromal, Immune, Normal
```

---

## Test Prompt #8: Complete End-to-End Workflow

**What it tests:** Multiple servers orchestrated together

**Paste this:**

```
Claude, I need a complete spatial transcriptomics analysis workflow:

Input data:
- FASTQ R1: /Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/fastq/sample_001_R1.fastq.gz
- FASTQ R2: /Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/fastq/sample_001_R2.fastq.gz
- Expression matrix: /Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/spatial/expression_matrix.json

Please perform this workflow:
1. Validate FASTQ quality (mcp-fgbio)
2. Calculate spatial autocorrelation for EPCAM, VIM, CD3D (mcp-spatialtools)
3. Perform differential expression: tumor vs normal (mcp-spatialtools)
4. Run pathway enrichment on top DE genes (mcp-spatialtools)
5. Compare key genes to TCGA BRCA cohort (mcp-tcga)

Provide a summary of findings at the end.
```

**This will demonstrate:**
- Multi-server orchestration
- Data flowing between tools
- AI-driven workflow execution
- Biological interpretation

---

## Troubleshooting

### Issue: "File not found" errors

**Solution:** Make sure you're using absolute paths starting with `/Users/lynnlangit/...`

### Issue: "Could not connect to MCP server"

**Solution:**
1. Check config is installed: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json`
2. Verify it uses full venv paths: `"command": "/Users/lynnlangit/.../venv/bin/python"`
3. Restart Claude Desktop

### Issue: Server not responding

**Solution:**
1. Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log`
2. Verify venvs exist: `ls servers/mcp-*/venv/bin/python`
3. Test manually: `cd servers/mcp-fgbio && source venv/bin/activate && python -m mcp_fgbio`

---

## All Available Servers

You can reference any of these in your prompts:

| Server | Tools | Use For |
|--------|-------|---------|
| mcp-fgbio | 4 | FASTQ validation, UMI extraction, reference genomes |
| mcp-spatialtools | 8 | Spatial analysis, DE, autocorrelation, pathways |
| mcp-openimagedata | 3 | Histology images, registration |
| mcp-seqera | 3 | Nextflow workflows |
| mcp-huggingface | 3 | ML predictions, embeddings |
| mcp-deepcell | 2 | Cell segmentation |
| mcp-mockepic | 3 | Clinical data integration |
| mcp-tcga | 5 | TCGA comparisons, survival, mutations |

---

**More examples:** See `docs/MCP_POC_Example_Prompts.md` for all 18 test prompts (update paths to absolute)

**Last Updated:** October 25, 2025
