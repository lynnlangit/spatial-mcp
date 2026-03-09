# Test Prompts for Claude Desktop

Copy and paste these into Claude Desktop to test your MCP server integration.

## ✅ Test 1: Verify MCP Servers are Loaded

```
What MCP servers are currently available? List each one with a brief description.
```

**Expected:** You should see all servers listed (spatialtools, epic, fgbio, etc.)

---

## ✅ Test 2: List Spatialtools Capabilities

```
Using the spatialtools MCP server, what tools are available? Please organize them by category (differential expression, spatial analysis, etc.)
```

**Expected:** Should list all 14 tools organized by Phase 2A-2E categories

---

## ✅ Test 3: Retrieve FHIR Patient Data

```
Using the epic MCP server, retrieve Patient-001 data from the GCP Healthcare API.

Show me:
1. Patient demographics
2. Diagnosis/conditions
3. Laboratory observations (CA-125, BRCA)
4. Medications

Patient ID: patient-001
```

**Expected:** Patient data from GCP Healthcare API (Jane TestPatient, Stage IV HGSOC, medications, etc.)

---

## ✅ Test 4: Simple Differential Expression

```
Using the spatialtools server, run differential expression analysis on Patient-001:

Data location: /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial/

Compare:
- Group 1: tumor_core region
- Group 2: stroma region

Tell me:
1. How many genes are significantly differentially expressed (FDR < 0.05)?
2. What are the top 5 upregulated genes in tumor?
3. Are any drug resistance markers present (ABCB1, PIK3CA, AKT1)?
```

**Expected:**
- ~17 DEGs identified
- Top genes: TP53, KRT8, ABCB1, BCL2L1, MKI67
- Drug resistance markers detected

---

## ✅ Test 5: Spatial Autocorrelation Analysis

```
Using spatialtools, calculate spatial autocorrelation for Patient-001 hypoxia markers:

Data: /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial/

Genes to analyze: HIF1A, CA9, VEGFA

For each gene:
1. Moran's I statistic
2. Statistical significance
3. What it means biologically
```

**Expected:**
- HIF1A: Moran's I ≈ 0.141 (highly significant)
- CA9: Moran's I ≈ 0.103 (highly significant)
- Interpretation: Hypoxic zones are spatially defined

---

## ✅ Test 6: Cell Type Deconvolution

```
Using spatialtools deconvolve_cell_types, analyze Patient-001:

Data: /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial/

Use these signatures:
- Hypoxic cells: HIF1A, CA9, VEGFA
- Immune cells: CD3D, CD8A
- Fibroblasts: COL1A1, COL3A1, ACTA2
- Resistant cells: ABCB1, PIK3CA, AKT1

Compare scores across tissue regions:
- tumor_core
- stroma
- stroma_immune
- necrotic_hypoxic

Which cell types are enriched in which regions?
```

**Expected:**
- Fibroblasts highest in stroma (748.6)
- Immune cells highest in stroma_immune (603.3)
- Hypoxic signature highest in necrotic_hypoxic (607.5)
- Resistant signature highest in tumor regions (700+)

---

## ✅ Test 7: Complete Clinical Workflow

```
I need a complete spatial transcriptomics analysis for Patient-001 (PAT001-OVC-2025).

Patient info from epic server:
- Retrieve patient demographics and clinical history

Spatial analysis from spatialtools:
1. Load data from /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial/
2. Differential expression (tumor_core vs stroma)
3. Pathway enrichment on upregulated genes
4. Spatial autocorrelation for top DEGs
5. Cell type deconvolution

Generate a clinical summary including:
- Key molecular findings
- Spatial organization patterns
- Drug resistance markers
- Treatment recommendations

Keep it concise but clinically actionable.
```

**Expected:**
- Full workflow execution
- Clinical summary with molecular features
- Treatment recommendations (PI3K/AKT inhibitors, hypoxia targeting, BCL2 inhibitors)
- Spatial insights (hypoxic zones, immune exclusion)

---

## ✅ Test 8: Exploratory Questions

Try asking Claude to explore and interpret:

```
Looking at Patient-001 spatial data, are there any genes that are both:
1. Highly differentially expressed (tumor vs stroma)
2. Strongly spatially clustered (high Moran's I)

What does this dual pattern suggest clinically?
```

**Expected:** Claude should identify genes like HIF1A, BCL2L1, KRT8 and explain the clinical significance

---

## ✅ Test 9: Pathway Focus

```
Using spatialtools, analyze the PI3K/AKT pathway in Patient-001:

1. Check if PIK3CA, AKT1, MTOR are differentially expressed
2. Calculate their fold changes
3. Are they spatially clustered?
4. What targeted therapies would you recommend?
```

**Expected:**
- All three genes upregulated in tumor
- Log2FC > 3 for AKT1
- Spatial clustering detected
- Recommend Alpelisib, Capivasertib, or Everolimus

---

## ✅ Test 10: Batch Correction (Advanced)

**Note:** This requires multiple batch files. Skip if you only have single-batch data.

```
I have spatial data from 3 hospitals that need batch correction:

Using spatialtools perform_batch_correction with ComBat:

Files:
- /path/to/hospital1.csv (batch: site1)
- /path/to/hospital2.csv (batch: site2)
- /path/to/hospital3.csv (batch: site3)

Output: /path/to/corrected_merged.csv

Tell me:
1. Variance explained by batch (before vs after)
2. Percent variance reduction
3. Should I trust the corrected data?
```

**Expected:**
- Batch variance reduction of 30-50%
- Validation that biological signal is preserved

---

## ✅ Test 11: GEO Download — Search Datasets

```
Using the geodownload server, search GEO for datasets related to
"ovarian cancer platinum resistant". Show the top 5 results with
accession IDs, titles, and organism.
```

**Expected:**
- Returns GEO dataset search results
- Each result includes GSE accession, title, platform
- Results relevant to ovarian cancer

**Server used:** `mcp-geodownload`

---

## ✅ Test 12: Open Targets — Drug-Target Associations

```
Using the opentargets server, look up the target VEGFA and find
its associations with ovarian carcinoma. What drugs target VEGFA
and what is the overall association score?
```

**Expected:**
- VEGFA target information (Ensembl ID, description)
- Disease associations with ovarian carcinoma
- Known drugs (e.g., bevacizumab)
- Association scores

**Server used:** `mcp-opentargets`

---

## ✅ Test 13: CIBERSORTx — Immune Deconvolution

```
Using the cibersortx server, run immune cell deconvolution on
PatientOne (PAT001-OVC-2025) using the LM22 signature matrix.
Show the estimated immune cell proportions.
```

**Expected:**
- Immune cell type proportions (T cells, macrophages, NK cells, etc.)
- DRY_RUN mode returns simulated deconvolution results
- Proportions sum to ~1.0

**Server used:** `mcp-cibersortx`

---

## ✅ Test 14: Neoantigen — MHC-I Binding Prediction

```
Using the neoantigen server, predict MHC-I binding for the peptide
YLQLVFGIEV with HLA allele HLA-A*02:01. What is the predicted
binding affinity and is this a strong binder?
```

**Expected:**
- Binding affinity prediction (IC50 in nM)
- Binding classification (strong/weak/non-binder)
- HLA allele confirmation
- Percentile rank

**Server used:** `mcp-neoantigen`

---

## 🎯 Quick Diagnostic Tests

If something isn't working, try these:

### Check Server Status
```
Are the spatialtools and epic MCP servers currently connected?
```

### Verify File Access
```
Can you check if this file exists and is readable:
/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial/visium_gene_expression.csv

How many rows and columns does it have?
```

### Test GCP Connection
```
Using the epic server, can you connect to the GCP Healthcare API and verify the precision-medicine-poc project is accessible?
```

---

## 📊 Expected Performance

**Response Times:**
- Simple queries (list tools): <1 second
- FHIR data retrieval: 2-5 seconds
- Differential expression: 5-10 seconds
- Spatial autocorrelation (31 genes): 10-15 seconds
- Complete workflow: 20-30 seconds

**Data Scale:**
- Patient-001: 900 spots, 31 genes
- Fast enough for interactive analysis

---

## 💡 Creative Prompts to Try

Once basic tests work, try these exploratory prompts:

```
What can you tell me about the tumor microenvironment in Patient-001 based on the spatial data?
```

```
If I wanted to design a clinical trial targeting the PI3K pathway in HGSOC, what patient selection criteria would you recommend based on this spatial analysis?
```

```
Compare the immune infiltration patterns between tumor_core and stroma_immune regions. Are the immune cells excluded from the tumor? What does that mean for immunotherapy?
```

```
Based on the spatial organization of hypoxia markers, where in the tumor would you expect the highest drug resistance?
```

---

## 🐛 Troubleshooting

**If tests fail:**

1. **Check Claude Desktop logs:**
   - Settings → MCP Servers → View Logs

2. **Manually test server:**
   ```bash
   cd /Users/lynnlangit/Documents/GitHub/spatial-mcp/servers/mcp-spatialtools
   uv run python -m mcp_spatialtools
   ```
   Should print: `Server running on stdio...`

3. **Restart Claude Desktop:**
   - Cmd+Q to quit
   - Reopen from Applications

4. **Verify config:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep -A 10 spatialtools
   ```

---

**🚀 Start with Test 1 and work your way through!**
