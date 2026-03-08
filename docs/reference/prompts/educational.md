# Educational Prompts

**Audience:** Students, Educators, New Users
**Purpose:** Learning and teaching precision medicine bioinformatics
**Time per prompt:** 5-20 minutes
**Expected output:** Tutorial-style results with explanations

---

## Beginner Level (Prompts 1-3)

### Prompt 1: Introduction to MCP - List Available Servers and Tools

**Time:** 5 minutes | **Learning Objective:** Understand MCP architecture

```
Welcome to Precision Medicine MCP! Let's explore what's available:

**Task 1: List All MCP Servers**
Show me all available MCP servers in this system.
For each server, tell me:
- Server name
- What type of data it handles
- How many tools it provides

**Task 2: Explore One Server in Detail**
Pick the mcp-spatialtools server and list all its tools.
For each tool, explain:
- What it does (in simple terms)
- What inputs it needs
- What outputs it produces

**Task 3: Understanding Server Relationships**
Explain how these servers work together. For example:
- Which servers would I use to analyze a cancer patient's data?
- How does clinical data (mcp-epic) connect to genomic data (mcp-fgbio)?

**Learning Questions:**
1. How many servers are available?
2. What's the difference between mcp-epic and mcp-mockepic?
3. Which server would I use for spatial transcriptomics analysis?
```

**Expected Output:**
```
Task 1 - MCP Servers Overview:

Found MCP servers:

1. mcp-fgbio (Genomics)
   - Handles: Reference genomes, FASTQ files, gene annotations
   - Tools: 4 tools
   - Status: Production-ready

2. mcp-multiomics (Multi-Omics Integration)
   - Handles: RNA-seq, proteomics, phosphoproteomics
   - Tools: 10 tools
   - Status: Production-ready

3. mcp-spatialtools (Spatial Transcriptomics)
   - Handles: 10x Visium spatial data
   - Tools: 14 tools
   - Status: Production-ready

... (18 total servers)

Task 2 - mcp-spatialtools Tools:

14 tools available:

1. align_spatial_data
   - What it does: Aligns raw sequencing reads to reference genome
   - Inputs: FASTQ files (R1, R2), genome index, output directory
   - Outputs: Aligned BAM file, alignment statistics

2. perform_batch_correction
   - What it does: Removes technical variation between batches
   - Inputs: Multiple expression matrices, batch labels
   - Outputs: Batch-corrected expression matrix

... (14 tools total)

Task 3 - Server Relationships:

For analyzing a cancer patient:
1. Clinical data: mcp-epic (real) or mcp-mockepic (demo)
2. Genomics: mcp-fgbio (variants, genes)
3. Multi-omics: mcp-multiomics (RNA/protein integration)
4. Spatial: mcp-spatialtools (tumor microenvironment)
5. Imaging: mcp-openimagedata + mcp-deepcell (pathology images)

Data flows: Clinical → Genomics → Multi-omics → Spatial → Imaging → Integrated Report

Learning Answers:
1. All servers (see [Server Registry](../shared/server-registry.md) for count)
2. mcp-epic = real FHIR data, mcp-mockepic = synthetic demo data
3. mcp-spatialtools for spatial transcriptomics
```

**Learning Objectives:**
- ✓ Understand MCP server architecture
- ✓ Know which servers handle which data types
- ✓ See how servers connect in workflows

---

### Prompt 2: First Analysis - Simple Gene Expression Query

**Time:** 5 minutes | **Learning Objective:** Perform basic analysis

```
Let's run your first bioinformatics analysis!

**Scenario:** You want to find out if the gene MKI67 (a proliferation marker) is highly expressed in PatientOne's tumor.

**Step 1: Load the Data**
Load spatial transcriptomics data for PatientOne (PAT001-OVC-2025):
- Expression file: visium_gene_expression.csv
- Coordinates file: visium_spatial_coordinates.csv
- How many spots (tissue locations) are there?
- How many genes are measured?

**Step 2: Find MKI67 Expression**
Look for the MKI67 gene:
- What is the average expression level across all spots?
- What is the highest expression value?
- What is the lowest expression value?

**Step 3: Compare Regions**
Compare MKI67 expression in different tumor regions:
- tumor_core
- tumor_proliferative
- stroma (normal tissue)

Which region has the highest MKI67? What does this tell us about cell division in different areas?

**Learning Questions:**
1. What does high MKI67 expression mean biologically?
2. Why is MKI67 higher in some regions than others?
3. How might this information help treat the patient?
```

**Expected Output:**
```
Step 1 - Data Loaded:
✓ 900 spots (tissue locations)
✓ 31 genes measured
✓ Data quality: No missing values

Step 2 - MKI67 Expression:
- Average expression: 3.45 (normalized log2 counts)
- Highest: 6.82 (in tumor_proliferative region)
- Lowest: 0.12 (in stroma region)
- Interpretation: MKI67 is actively expressed, indicating cell division

Step 3 - Regional Comparison:

MKI67 Expression by Region:
- tumor_proliferative: 5.91 (HIGHEST - active cell division)
- tumor_core: 4.23 (moderate proliferation)
- stroma: 0.85 (LOW - minimal cell division)

Biological Interpretation:
- tumor_proliferative region: Rapidly dividing cancer cells
- tumor_core: Established tumor with lower proliferation
- stroma: Normal tissue with minimal cell division

Learning Answers:
1. High MKI67 = cells are actively dividing (proliferating)
2. Cancer cells divide faster than normal cells, especially in "proliferative" zones
3. High proliferation regions might respond better to chemotherapy (which targets dividing cells)
```

**Learning Objectives:**
- ✓ Load and explore gene expression data
- ✓ Compare expression across regions
- ✓ Interpret biological meaning

---

### Prompt 3: Understanding p-values and Statistical Significance

**Time:** 10 minutes | **Learning Objective:** Learn statistical concepts

```
Let's learn about statistical significance in bioinformatics!

**Scenario:** You want to know if MKI67 is SIGNIFICANTLY higher in tumor vs normal tissue (not just by random chance).

**Step 1: Set Up the Comparison**
Compare MKI67 expression:
- Group A: tumor regions (tumor_core + tumor_proliferative)
- Group B: stroma (normal tissue)

**Step 2: Run a Statistical Test**
Use a Mann-Whitney U test (non-parametric test for comparing two groups):
- What is the test statistic (U value)?
- What is the p-value?
- Is p < 0.05? (This is our significance threshold)

**Step 3: Interpret the Results**
Answer these questions:
- Is MKI67 significantly different between tumor and stroma?
- How confident are you in this result? (based on p-value)
- What does p = 0.001 mean in simple terms?

**Step 4: Multiple Testing Correction**
Now let's test ALL 31 genes (not just MKI67):
- How many genes are significant at p < 0.05? (without correction)
- How many are significant after FDR correction (q < 0.05)?
- Why do we need multiple testing correction?

**Learning Questions:**
1. What does p < 0.05 mean?
2. Why use 0.05 as the cutoff?
3. What's the difference between p-value and FDR-corrected q-value?
4. Can a result be "statistically significant" but biologically unimportant?
```

**Expected Output:**
```
Step 1 - Comparison Setup:
✓ Group A (tumor): 193 spots (tumor_core + tumor_proliferative)
✓ Group B (stroma): 180 spots
✓ Gene: MKI67

Step 2 - Statistical Test Results:
Test: Mann-Whitney U test
- U statistic: 2,456
- p-value: 8.3 × 10⁻¹² (0.0000000000083)
- Significance: YES (p < 0.05)

Step 3 - Interpretation:
✓ MKI67 IS significantly different (tumor vs stroma)
✓ Confidence: Very high (p < 0.001)
✓ What p = 0.001 means: "If there was NO real difference, we'd see this result by chance only 1 in 1,000 times"

Step 4 - Multiple Testing:
Testing all 31 genes (tumor vs stroma):
- Significant at p < 0.05 (uncorrected): 28 genes
- Significant at q < 0.05 (FDR-corrected): 17 genes
- Why correction needed: Testing 31 genes means 31 chances for false positives!

Example of Multiple Testing Problem:
- Test 1 gene at p < 0.05: 5% chance of false positive
- Test 31 genes: ~78% chance of at least 1 false positive!
- FDR correction: Controls false discovery rate to 5%

Learning Answers:
1. p < 0.05: Less than 5% chance this result is due to random chance
2. 0.05 = 5% false positive rate (accepted standard in science)
3. p-value = uncorrected, q-value = corrected for multiple testing
4. YES! A tiny difference can be "significant" with large sample size but clinically meaningless
```

**Learning Objectives:**
- ✓ Understand p-values and statistical significance
- ✓ Learn why multiple testing correction is crucial
- ✓ Distinguish statistical vs biological significance

---

## Intermediate Level (Prompts 4-6)

### Prompt 4: Pathway Enrichment Analysis Tutorial

**Time:** 15 minutes | **Learning Objective:** Learn pathway analysis

```
Let's learn how to identify biological pathways from gene lists!

**Background:** You've identified 10 upregulated genes in PatientOne's tumor. Now you want to know: What biological processes are these genes involved in?

**Step 1: Your Gene List**
Upregulated genes (tumor vs normal):
- TP53, PIK3CA, AKT1, MTOR, PTEN
- BRCA1, MYC, VEGFA, HIF1A, BCL2L1

**Step 2: Run Pathway Enrichment**
Use the pathway enrichment tool with:
- Input: Your 10 genes
- Background: All 31 genes in the dataset
- Database: GO Biological Process (GO_BP)
- Significance threshold: FDR < 0.05

**Step 3: Interpret Results**
For each enriched pathway, explain:
- Pathway name
- How many of your genes are in this pathway?
- What does this pathway do biologically?
- Why is it relevant to cancer?

**Step 4: Clinical Implications**
Based on enriched pathways, answer:
- Which pathways could be drug targets?
- Are there FDA-approved drugs for these pathways?
- What would you recommend testing?

**Learning Questions:**
1. What is "pathway enrichment"?
2. Why do we need a background gene set?
3. What does "fold enrichment" mean?
4. How is this different from just looking at individual genes?
```

**Expected Output:**
```
Step 1 - Gene List Loaded:
✓ 10 upregulated genes
✓ All genes found in pathway databases

Step 2 - Pathway Enrichment Results:

Found 5 significantly enriched pathways (FDR < 0.05):

1. PI3K-Akt signaling pathway (KEGG)
   - Genes matched: 8/10 (PIK3CA, AKT1, MTOR, PTEN, BRCA1, MYC, VEGFA, BCL2L1)
   - Pathway size: 15 total genes
   - Fold enrichment: 5.33×
   - FDR: 1.2 × 10⁻⁴
   - Biology: Cell growth, survival, metabolism
   - Cancer relevance: Often activated in cancer (promotes tumor growth)

2. Regulation of apoptosis (GO_BP)
   - Genes matched: 6/10 (TP53, AKT1, BCL2L1, PTEN, MYC, BRCA1)
   - Fold enrichment: 4.80×
   - FDR: 3.4 × 10⁻⁴
   - Biology: Controls programmed cell death
   - Cancer relevance: Cancer cells evade apoptosis to survive

3. Response to hypoxia (GO_BP)
   - Genes matched: 5/10 (HIF1A, VEGFA, MYC, AKT1, MTOR)
   - Fold enrichment: 6.20×
   - FDR: 2.1 × 10⁻⁴
   - Biology: How cells respond to low oxygen
   - Cancer relevance: Tumors are hypoxic, triggers angiogenesis

... (5 pathways total)

Step 3 - Biological Interpretation:

Key Findings:
1. PI3K/Akt pathway is the most enriched
   - 8 out of your 10 genes are in this pathway!
   - This pathway is HYPERACTIVATED in the tumor
   - Drives cancer cell growth and survival

2. Apoptosis evasion
   - Cancer cells avoid dying (BCL2L1 anti-apoptotic)
   - TP53 tumor suppressor is mutated
   - Cells survive when they should die

3. Hypoxia response
   - Tumor is low in oxygen (HIF1A, VEGFA activated)
   - Triggers new blood vessel formation
   - Helps tumor grow despite poor oxygen

Step 4 - Clinical Implications:

Druggable Pathways:
1. ✓ PI3K/Akt/mTOR pathway
   - FDA-approved drugs: Alpelisib (PI3K inhibitor), Everolimus (mTOR inhibitor)
   - Recommendation: Consider alpelisib + chemotherapy

2. ✓ VEGF pathway (hypoxia response)
   - FDA-approved drug: Bevacizumab (anti-VEGF)
   - Recommendation: Continue bevacizumab to block angiogenesis

3. ✓ Apoptosis pathway
   - Experimental drugs: BCL2 inhibitors (venetoclax)
   - Recommendation: Clinical trial opportunity

Learning Answers:
1. Pathway enrichment: Finding if your genes cluster in specific biological processes more than expected by chance
2. Background set: Defines what genes COULD have been found (avoids bias)
3. Fold enrichment: How many times more genes than expected by chance (5.33× = 533% more than random)
4. Individual genes = pieces, pathways = the whole picture (tells you WHAT the tumor is doing)
```

**Learning Objectives:**
- ✓ Understand pathway enrichment analysis
- ✓ Interpret enrichment statistics (fold enrichment, FDR)
- ✓ Connect pathways to treatment options

---

### Prompt 5: Batch Effects and Data Preprocessing

**Time:** 15 minutes | **Learning Objective:** Learn data quality control

```
Let's learn why data preprocessing is crucial for accurate analysis!

**Scenario:** You have proteomics data from 2 different mass spectrometry runs (batches). You want to combine them, but there might be technical artifacts.

**Step 1: Visualize the Problem**
Load PatientOne multi-omics data:
- 14 samples total
- Batch 1: 7 samples (run in January)
- Batch 2: 7 samples (run in February)

Perform PCA (Principal Component Analysis):
- Plot PC1 vs PC2, color by batch
- Do samples cluster by batch or by biology (resistant vs sensitive)?

**Step 2: Quantify Batch Effects**
Calculate:
- Correlation between PC1 and batch label
- If correlation > 0.7: STRONG batch effect
- If correlation < 0.3: WEAK batch effect

**Step 3: Apply Batch Correction**
Use ComBat method to remove batch effects:
- Re-run PCA after correction
- New correlation between PC1 and batch?
- How much variance was removed?

**Step 4: Verify Biological Signal Preserved**
After correction:
- Do resistant vs sensitive samples still separate?
- Are known cancer genes still differentially expressed?

**Learning Questions:**
1. What causes batch effects?
2. Why are batch effects a problem?
3. When should you correct batch effects vs when to avoid it?
4. How do you know if correction worked?
```

**Expected Output:**
```
Step 1 - Visualizing Batch Effects:

PCA Before Correction:
- PC1 explains 45% variance
- PC2 explains 18% variance
- Samples cluster by BATCH (not biology!)
- Batch 1 samples: Left side of PC1
- Batch 2 samples: Right side of PC1
- Problem: Can't see biological differences (resistant vs sensitive)

Step 2 - Quantifying Batch Effect:

Correlation Analysis:
- PC1 vs Batch label: r = 0.82 (STRONG batch effect!)
- PC1 vs Treatment response: r = 0.23 (biology is hidden)

Interpretation:
- PC1 captures batch differences (technical artifact)
- Biological signal is masked by batch effect
- MUST correct before biological analysis

Step 3 - Applying ComBat Correction:

ComBat Batch Correction Results:
✓ Correction completed
✓ 2 batches harmonized
✓ 2,147 protein features adjusted

PCA After Correction:
- PC1 vs Batch label: r = 0.15 (batch effect REMOVED!)
- PC1 vs Treatment response: r = 0.68 (biology now visible!)
- Variance removed: 27% (batch-related variance)
- Variance preserved: 73% (biological variance)

Visual Change:
- Before: Samples separate by batch (technical)
- After: Samples separate by resistant vs sensitive (biological)

Step 4 - Verifying Biological Signal:

After Correction:
✓ Resistant vs sensitive samples clearly separate
✓ Known cancer genes still significant:
  - PIK3CA: log2FC = 2.3, p = 0.0001 (preserved)
  - AKT1: log2FC = 2.1, p = 0.0003 (preserved)
  - PTEN: log2FC = -2.1, p = 0.0001 (preserved)

Quality Control:
✓ Biological differences preserved
✓ Technical artifacts removed
✓ Ready for downstream analysis

Learning Answers:
1. Batch effects caused by: Different instruments, operators, reagent lots, run dates
2. Problem: Batch differences can be larger than biological differences, leading to false discoveries
3. Correct when: Known batch design, confounded with biology. Avoid when: Batch perfectly matches biology (can't separate)
4. Correction worked if: PC1-batch correlation drops, biology still separates, known genes preserved
```

**Learning Objectives:**
- ✓ Understand batch effects and their impact
- ✓ Use PCA to visualize data quality
- ✓ Apply and validate batch correction

---

### Prompt 6: Multi-Omics Integration - Combining Evidence

**Time:** 20 minutes | **Learning Objective:** Integrate multiple data types

```
Let's learn how to combine evidence from multiple sources (multi-omics integration)!

**Scenario:** You want to find genes that are consistently upregulated in resistant tumors across RNA, protein, AND phosphoprotein data.

**Step 1: Individual Analyses**
Run differential expression for resistant vs sensitive in each modality:
- RNA-seq: Which genes are upregulated? (log2FC > 1, p < 0.05)
- Proteomics: Which proteins are upregulated?
- Phosphoproteomics: Which phosphorylated proteins are upregulated?

**Step 2: Find Overlapping Genes**
Create a Venn diagram (conceptually):
- How many genes significant in RNA only?
- How many in protein only?
- How many in ALL THREE modalities?

**Step 3: Meta-Analysis with Stouffer's Method**
Use Stouffer's method to combine p-values:
- For each gene, combine p-values from RNA, protein, phospho
- Calculate meta p-value and meta Z-score
- Apply FDR correction to meta p-values

**Step 4: Interpret Multi-Modal Evidence**
Compare single-modality vs multi-modal approach:
- Single modality (RNA only): How many significant genes?
- Multi-modal (integrated): How many significant genes?
- Which approach gives stronger evidence?

**Learning Questions:**
1. Why combine multiple data types instead of using just RNA-seq?
2. What does it mean if a gene is significant in RNA but not protein?
3. How does Stouffer's method work (conceptually)?
4. When is multi-omics integration worth the cost?
```

**Expected Output:**
```
Step 1 - Individual Analyses:

RNA-seq (Resistant vs Sensitive):
- Significant genes (p < 0.05): 45 genes
- Top gene: ABCB1 (log2FC = 2.5, p = 0.0001)

Proteomics:
- Significant proteins (p < 0.05): 38 proteins
- Top protein: PIK3CA (log2FC = 2.0, p = 0.0002)

Phosphoproteomics:
- Significant phospho-proteins (p < 0.05): 32 phospho-sites
- Top: AKT1 (pS473) (log2FC = 2.3, p = 0.0001)

Step 2 - Overlap Analysis:

Venn Diagram (Conceptual):
- RNA only: 18 genes
- Protein only: 11 genes
- Phospho only: 5 genes
- RNA + Protein: 12 genes
- RNA + Phospho: 8 genes
- Protein + Phospho: 9 genes
- ALL THREE: 7 genes ⭐ (Highest confidence!)

7 Genes in All Three Modalities:
1. PIK3CA - PI3K catalytic subunit
2. AKT1 - Serine/threonine kinase
3. MTOR - mTOR pathway
4. ABCB1 - Drug efflux pump (MDR1)
5. BCL2L1 - Anti-apoptotic protein
6. PTEN - Tumor suppressor (DOWNREGULATED)
7. TP53 - Tumor suppressor (DOWNREGULATED)

Step 3 - Stouffer's Meta-Analysis:

Combined P-values:

Gene: PIK3CA
- RNA p-value: 0.001 (NOMINAL from HAllA)
- Protein p-value: 0.0002 (NOMINAL)
- Phospho p-value: 0.0005 (NOMINAL)
- Meta Z-score: 4.2
- Meta p-value: 2.7 × 10⁻⁵ (NOMINAL combined)
- FDR q-value: 0.0001 (FDR applied AFTER combination)

Gene: AKT1
- Meta Z-score: 4.5
- FDR q-value: <0.0001

... (7 genes with multi-modal evidence)

Step 4 - Single vs Multi-Modal Comparison:

Single Modality (RNA only):
- Significant genes: 45
- Confidence: Medium (one data type)
- False positives: Higher risk

Multi-Modal (Integrated):
- Significant genes: 7
- Confidence: HIGH (three data types agree!)
- False positives: Much lower risk

Example: Why Multi-Modal Matters

Gene X:
- RNA: p = 0.02 (marginally significant)
- Protein: p = 0.40 (not significant)
- Phospho: p = 0.50 (not significant)
- Meta p-value: 0.15 (not significant after integration)
- Conclusion: Likely a false positive in RNA data alone

Gene PIK3CA:
- RNA: p = 0.001 (significant)
- Protein: p = 0.0002 (significant)
- Phospho: p = 0.0005 (significant)
- Meta p-value: 2.7 × 10⁻⁵ (VERY significant!)
- Conclusion: HIGH CONFIDENCE - real biological change

Learning Answers:
1. Multiple data types: RNA measures transcription, protein measures translation, phospho measures activation - all tell different parts of the story!
2. RNA high but protein low: Post-transcriptional regulation, protein degradation, or technical noise
3. Stouffer's method: Combines p-values while accounting for directionality (increases statistical power)
4. Multi-omics worth it when: Need high confidence (drug targets), complex biology, budget allows ($2-3K per sample)
```

**Learning Objectives:**
- ✓ Understand multi-omics integration rationale
- ✓ Apply Stouffer's meta-analysis
- ✓ Interpret multi-modal evidence strength

---

## Advanced Level (Prompts 7-10)

### Prompt 7: Spatial Transcriptomics - Tumor Microenvironment

**Time:** 20 minutes | **Learning Objective:** Analyze spatial gene expression

```
Let's explore how genes are expressed in different regions of a tumor!

**Learning Goal:** Understand tumor spatial heterogeneity and the microenvironment.

**Step 1: Load Spatial Data**
For PatientOne Visium data:
- How many spots (tissue locations)?
- How many genes?
- What are the 6 tissue regions?

**Step 2: Visualize Spatial Patterns**
Create spatial heatmaps for:
- MKI67 (proliferation marker)
- CD8A (T cell marker)
- VEGFA (angiogenesis marker)

For each gene:
- Where is it highly expressed (which regions)?
- Is the expression uniform or clustered?

**Step 3: Calculate Spatial Autocorrelation**
For each of the 3 genes above:
- Calculate Moran's I statistic
- Interpret: I > 0.5 = strong spatial clustering
- Which genes show spatial patterns?

**Step 4: Biological Interpretation**
Answer these questions:
- Why is MKI67 high in tumor_proliferative but low in stroma?
- Why are CD8 cells (immune cells) in stroma but NOT in tumor?
- What does this "immune exclusion" mean for immunotherapy?
- Why is VEGFA high in certain regions?

**Learning Questions:**
1. What is spatial transcriptomics?
2. Why does spatial location matter for gene expression?
3. What is Moran's I and what does it measure?
4. How can spatial data guide treatment decisions?
```

**Expected Output:**
```
Step 1 - Spatial Data Summary:
✓ 900 spots (tissue locations)
✓ 31 genes measured
✓ 6 tissue regions:
  - tumor_core (69 spots)
  - tumor_proliferative (124 spots)
  - tumor_interface (112 spots)
  - stroma_immune (212 spots)
  - stroma (180 spots)
  - necrotic_hypoxic (203 spots)

Step 2 - Spatial Expression Patterns:

MKI67 (Proliferation):
- Highest: tumor_proliferative region (avg = 5.91)
- Moderate: tumor_core (avg = 4.23)
- Lowest: stroma (avg = 0.85)
- Pattern: Concentrated in actively dividing tumor areas

CD8A (T Cells):
- Highest: stroma_immune region (avg = 4.12)
- Moderate: stroma (avg = 2.34)
- Lowest: tumor_core (avg = 0.23)
- Pattern: Excluded from tumor! Immune cells can't get in.

VEGFA (Angiogenesis):
- Highest: necrotic_hypoxic region (avg = 6.45)
- Moderate: tumor_core (avg = 3.87)
- Lowest: stroma (avg = 1.12)
- Pattern: High where oxygen is low (hypoxic regions)

Step 3 - Spatial Autocorrelation:

Moran's I Statistics:

MKI67:
- Moran's I: 0.623
- p-value: 1.2 × 10⁻⁸
- Interpretation: STRONG spatial clustering (proliferation zones)

CD8A:
- Moran's I: 0.581
- p-value: 4.5 × 10⁻⁷
- Interpretation: STRONG spatial clustering (immune zones separate from tumor)

VEGFA:
- Moran's I: 0.692
- p-value: 2.1 × 10⁻¹⁰
- Interpretation: VERY STRONG spatial clustering (hypoxic zones)

Step 4 - Biological Interpretation:

Q1: Why is MKI67 high in tumor_proliferative but low in stroma?
A: tumor_proliferative has rapidly dividing cancer cells (high MKI67 = high proliferation)
   stroma is normal tissue with minimal cell division (low MKI67)

Q2: Why are CD8 cells in stroma but NOT tumor?
A: "Immune exclusion" - Tumor creates barriers preventing T cells from entering:
   - Physical barriers (dense tumor stroma)
   - Immunosuppressive factors (TGF-β, IDO)
   - Lack of T cell attracting signals
   Result: CD8 T cells stuck at periphery, can't kill tumor cells

Q3: What does immune exclusion mean for immunotherapy?
A: Poor prognosis for checkpoint inhibitors (pembrolizumab, nivolumab)
   - Checkpoint inhibitors help T cells kill cancer
   - BUT if T cells can't reach tumor (excluded), no benefit
   - This patient unlikely to respond to immunotherapy alone
   - May need combination therapy to "heat up" cold tumor

Q4: Why is VEGFA high in certain regions?
A: Tumor outgrows blood supply → Low oxygen (hypoxia)
   - Hypoxia triggers HIF1A → Activates VEGFA
   - VEGFA stimulates new blood vessel growth (angiogenesis)
   - necrotic_hypoxic region: Most hypoxic, highest VEGFA
   - Treatment opportunity: Anti-VEGF drugs (bevacizumab)

Learning Answers:
1. Spatial transcriptomics: Measures gene expression while preserving tissue location information
2. Location matters: Tumor is heterogeneous - different regions have different biology
3. Moran's I: Statistical test for spatial clustering (0 = random, 1 = perfect clustering, -1 = dispersed)
4. Spatial data guides treatment: Identifies immune exclusion (skip immunotherapy), hypoxia (use anti-VEGF), proliferation zones (target with chemo)
```

**Learning Objectives:**
- ✓ Understand spatial transcriptomics technology
- ✓ Interpret spatial gene expression patterns
- ✓ Apply Moran's I spatial statistics
- ✓ Connect spatial patterns to treatment decisions

---

### Prompt 8: Clinician-in-the-Loop Workflow (Educational Version)

**Time:** 15 minutes | **Learning Objective:** Understand clinical validation process

```
Let's learn why clinician validation is crucial for AI-driven analysis!

**Learning Goal:** Understand the Clinician-in-the-Loop (CitL) workflow and why human oversight is essential.

**Step 1: The Problem with Autonomous AI**
Discuss these scenarios:
- Scenario A: AI recommends treatment based on analysis
- Scenario B: AI generates analysis, oncologist reviews and approves

Which is safer? Why?

**Step 2: Understanding Quality Gates**
For PatientOne analysis, review these automated checks:
1. Sample size check: ≥30 spots per region
2. FDR threshold: q < 0.05 for significant genes
3. Data completeness: >95% non-missing values
4. Cross-modal consistency: Genomics matches imaging

Why is each check important?

**Step 3: Clinician Review Checklist**
As a clinician reviewing PatientOne's report, you would check:

□ Per-Finding Validation (10 key findings):
  - TP53 R175H mutation confirmed?
  - PIK3CA pathway activated (multiple evidence)?
  - Immune exclusion phenotype validated?

□ Guideline Compliance:
  - NCCN guidelines followed?
  - Institutional protocols followed?

□ Treatment Recommendations:
  - Are recommendations evidence-based?
  - Are they appropriate for this patient?

**Step 4: Approval Decision**
Three possible outcomes:
- APPROVE: All findings validated, ready for patient care
- REVISE: Minor issues, request re-analysis with changes
- REJECT: Major errors, full re-analysis needed

For PatientOne, which decision would you make and why?

**Learning Questions:**
1. Why can't we let AI make treatment decisions autonomously?
2. What are the risks of skipping clinician review?
3. How does CitL improve patient safety?
4. How long should clinician review take?
```

**Expected Output:**
```
Step 1 - AI Safety Discussion:

Scenario A (Autonomous AI):
❌ Risks:
- AI might miss contraindications (e.g., patient allergies)
- No clinical judgment (individual patient factors)
- Legal liability unclear
- Patient trust issues

Scenario B (Clinician-in-the-Loop):
✓ Benefits:
- Expert validates AI findings
- Clinical context considered
- Human accountability
- Catches AI errors before patient harm

Winner: Scenario B (human oversight essential)

Step 2 - Quality Gates Explained:

Check 1: Sample Size ≥30 spots per region
- Why: Small samples → unreliable statistics
- Example: 5 spots in tumor_core → Can't trust differential expression
- Action if failed: Exclude region or merge with adjacent region

Check 2: FDR < 0.05
- Why: Controls false discoveries
- Example: Without FDR, 50% of "significant" genes might be false positives
- Action if failed: Report no significant findings

Check 3: Data Completeness >95%
- Why: Too many missing values → biased results
- Example: If MKI67 missing in 50% of samples, can't analyze properly
- Action if failed: Impute missing values or exclude incomplete features

Check 4: Cross-Modal Consistency
- Why: Multi-modal evidence should agree
- Example: TP53 mutation (genomics) should match TP53+ cells (imaging)
- Action if failed: Investigate discrepancy, may indicate technical error

Step 3 - Clinician Review Example:

Reviewing PatientOne Report:

Finding 1: TP53 R175H mutation
- Genomic data: ✓ Confirmed in VCF
- Imaging data: ✓ TP53+ cells 65-75%
- Validation: CONFIRMED ✓
- Comment: "Consistent across modalities, high confidence"

Finding 2: PI3K/AKT pathway activation
- RNA: ✓ PIK3CA, AKT1, MTOR upregulated
- Protein: ✓ Confirmed in proteomics
- Phospho: ✓ pAKT increased
- Spatial: ✓ PIK3CA high in tumor regions
- Validation: CONFIRMED ✓
- Comment: "Strong multi-modal evidence for PI3K inhibitor"

Finding 3: Immune exclusion phenotype
- Spatial: ✓ CD8 in stroma, not tumor
- Imaging: ✓ Low CD8+ infiltration (5-15 cells/mm²)
- Validation: CONFIRMED ✓
- Comment: "Poor immunotherapy candidate, consider combination strategies"

Guideline Compliance:
- NCCN: ALIGNED ✓
  - BRCA1+ → PARP inhibitor (Category 1 recommendation)
  - PI3K pathway activated → Clinical trial eligible
- Institutional: ALIGNED ✓
  - All recommended drugs in formulary

Treatment Recommendations Review:
1. PI3K inhibitor + PARP inhibitor: AGREE ✓
   - Strong molecular evidence
   - NCT clinical trial available
   - Patient meets eligibility

2. Continue bevacizumab: AGREE ✓
   - VEGFA upregulated (hypoxia evidence)
   - No contraindications noted

3. Immunotherapy: CONDITIONAL ⚠
   - Immune exclusion phenotype = poor candidate
   - Consider only in combination with drugs that "heat up" tumor
   - Not as monotherapy

Step 4 - Approval Decision:

Decision: APPROVE ✓

Rationale:
"All 10 key findings validated with multi-modal evidence. Treatment recommendations align with NCCN guidelines and are appropriate for patient's molecular profile. Immune exclusion phenotype accurately identified, correctly limiting immunotherapy to conditional use only. High-quality analysis ready for tumor board presentation."

Review Time: 25 minutes

Learning Answers:
1. Why not autonomous AI: Patients are complex, need clinical context, legal/ethical concerns, AI can make mistakes
2. Risks of skipping review: Wrong treatment, contraindications missed, AI errors not caught, patient harm
3. CitL improves safety: Expert oversight, clinical judgment, catches errors, maintains accountability
4. Review time: 20-30 minutes for comprehensive multi-modal analysis (well worth it for patient safety)
```

**Learning Objectives:**
- ✓ Understand importance of clinician oversight
- ✓ Learn quality gate concepts
- ✓ Practice clinical validation workflow
- ✓ Appreciate AI as "co-pilot" not autonomous decision-maker

---

### Prompt 9: Cost-Effectiveness Analysis (Educational)

**Time:** 10 minutes | **Learning Objective:** Understand healthcare economics

```
Let's learn about the cost-effectiveness of precision medicine!

**Learning Goal:** Understand how to evaluate cost vs benefit of advanced testing.

**Scenario:** A hospital is deciding whether to adopt the MCP system for precision oncology.

**Step 1: Calculate Costs**

Traditional Manual Approach (per patient):
- Bioinformatician time: 40 hours × $75/hr = ?
- Compute resources: $2,000-4,000
- External sequencing: $1,000-2,000
- Total per patient: ?

MCP Approach (per patient):
- Compute (GCP Cloud Run): $22-99
- External APIs: $1
- Claude tokens: $1-2
- Total per patient: ?

What is the cost savings per patient?

**Step 2: Calculate Value**

Better Treatment Selection:
- Without precision medicine: 30% response rate (standard chemo)
- With precision medicine: 50% response rate (targeted therapy)
- Improvement: 20 percentage points

Cost of Treatment Failure:
- Failed treatment cycle: $50,000-100,000
- Additional suffering, delayed effective treatment
- Value of avoided failure: ?

**Step 3: Return on Investment (ROI)**

Initial Investment:
- Setup costs: $50K-75K (one-time)
- Annual operational: $24K-72K

For 100 patients per year:
- Total savings: ?
- Payback period: ?
- 5-year ROI: ?

**Step 4: Beyond Money**

What else matters besides cost?
- Time to results (40 hours → 2-5 hours production)
- Patient outcomes (better treatment selection)
- Research productivity (more analyses possible)
- Clinician satisfaction

**Learning Questions:**
1. Is the cheapest option always the best?
2. How do you balance upfront costs vs long-term savings?
3. What is "value-based healthcare"?
4. Should cost influence treatment decisions?
```

**Expected Output:**
```
Step 1 - Cost Calculation:

Traditional Manual Approach: Thousands per patient (labor + compute + sequencing)

MCP Approach: Low per-patient compute cost (compute + APIs + Claude tokens)

See Cost Analysis (docs/reference/shared/cost-analysis.md) and
Value Proposition (docs/reference/shared/value-proposition.md)
for detailed cost breakdowns and savings projections.

Step 2 - Value Calculation:

Improved Response Rates:
- Standard: 30% response → 70% fail treatment
- Precision: 50% response → 50% fail treatment
- Improvement: 20% fewer treatment failures

Cost of Treatment Failure:
- Failed chemo cycle: ~$75,000 average
- 20% reduction in failures (20 fewer failures per 100 patients)
- Value of avoided failures: 20 × $75,000 = $1,500,000

Total Value Per 100 Patients:
- Direct cost savings: Significant projected savings per patient (see Value Proposition)
- Avoided treatment failures: Major additional value
- See Value Proposition (docs/reference/shared/value-proposition.md) for detailed projections

Step 3 - ROI Calculation:

See Value Proposition (docs/reference/shared/value-proposition.md) and
ROI Analysis (docs/for-funders/ROI_ANALYSIS.md) for detailed
investment tiers, payback period, and ROI projections.

ROI Calculations:
- Payback period: 0.06 years = 3 weeks!
- Year 1 ROI: ($1,813,700 - $110,500) / $110,500 = 1,541% return
- 5-year cumulative value: $9,068,500 value - $302,500 cost = $8,766,000 net benefit

Step 4 - Beyond Money:

Intangible Benefits:

1. Time Savings:
   - Traditional: 40 hours per analysis
   - MCP production: 2-5 hours (DRY_RUN demo: 25-35 minutes)
   - Time saved: 3,500-3,800 hours per year (100 patients)
   - = 2 full-time bioinformaticians freed up for other work

2. Patient Outcomes:
   - Faster time to results: 2 days vs 2 weeks
   - Better treatment selection: 50% vs 30% response
   - Fewer treatment failures: 20% reduction
   - Quality of life: Less suffering from ineffective treatments

3. Research Productivity:
   - 10× more analyses possible with same staff
   - Faster publication timelines
   - More clinical trials enabled
   - Competitive advantage for cancer center

4. Clinician Satisfaction:
   - Less time on manual analysis
   - More time for patient care
   - Better tools for decision-making
   - Improved confidence in treatment plans

Learning Answers:
1. Cheapest not always best: Must consider quality, outcomes, long-term value
   - $100 test that prevents $75,000 failed treatment = excellent value!

2. Balancing costs: Upfront investment can have massive long-term ROI
   - Example: $110K investment → $8.7M value over 5 years

3. Value-based healthcare: Optimize outcomes per dollar spent, not just minimize spending
   - Better outcomes at lower cost = value-based care
   - MCP achieves both: better outcomes AND 96% cost reduction

4. Should cost influence decisions:
   - Patient care decisions: NO (ethics-first, cost-second)
   - System-level decisions: YES (allocate resources to maximize population benefit)
   - Example: Adopting MCP benefits ALL patients, ethical to consider cost-effectiveness
```

**Learning Objectives:**
- ✓ Calculate cost savings and ROI
- ✓ Understand value beyond direct costs
- ✓ Learn value-based healthcare principles
- ✓ Balance economic and ethical considerations

---

### Prompt 10: Final Project - Complete Patient Analysis

**Time:** 45 minutes | **Learning Objective:** Apply all learned concepts

```
**Capstone Learning Exercise:** Perform a complete precision medicine analysis for a hypothetical patient.

**Your Patient:** PAT002-BRCA-2026
- 62-year-old woman
- Stage III breast cancer (HER2+, ER+, PR+)
- Post-surgery, completing adjuvant chemotherapy
- BRCA2 germline mutation detected
- Now considering targeted therapy + endocrine therapy

**Your Task:** As a bioinformatician working with an oncologist, analyze this patient's data and provide treatment recommendations.

**Available Data:**
- Clinical: Demographics, treatment history, CA 15-3 tumor marker
- Genomic: VCF file with somatic mutations
- Spatial: 10x Visium tumor sample (if available)
- Imaging: H&E slides, HER2 IHC, Ki67 staining

**Steps to Complete:**

1. **Clinical Context** (5 min)
   - Summarize patient history
   - Note key clinical features (HER2+, ER+, BRCA2+)
   - Identify treatment goals

2. **Genomic Analysis** (10 min)
   - Parse VCF for somatic mutations
   - Check HER2 (ERBB2) amplification status
   - Check hormone receptor pathway genes
   - Identify other actionable mutations

3. **Spatial Analysis** (if data available, 10 min)
   - Load spatial transcriptomics
   - Assess HER2 expression heterogeneity
   - Check immune infiltration
   - Evaluate proliferation zones

4. **Statistical Analysis** (10 min)
   - Perform differential expression (tumor vs normal)
   - Calculate pathway enrichment
   - Apply appropriate statistical corrections
   - Interpret p-values and FDR

5. **Treatment Recommendations** (10 min)
   - Rank treatment options by evidence strength
   - Consider: Anti-HER2, endocrine, PARP inhibitors
   - Assess clinical trial eligibility
   - Provide NCCN-aligned recommendations

6. **Final Report** (5 min)
   - Write 1-page clinical summary
   - Include: Key findings, treatment recommendations, monitoring plan
   - Ready for oncologist review

**Learning Assessment:**
After completing this exercise, can you:
- □ Integrate multiple data types?
- □ Apply appropriate statistical methods?
- □ Interpret biological significance?
- □ Connect molecular findings to treatments?
- □ Communicate results clearly to clinicians?

If you answered YES to all: Congratulations! You've mastered precision medicine bioinformatics basics.
```

**Learning Objectives:**
- ✓ Apply all learned concepts in integrated workflow
- ✓ Demonstrate end-to-end analysis skills
- ✓ Practice clinical communication
- ✓ Build confidence for real-world applications

---

## Summary: Educational Pathway

### Beginner Level (3 prompts)
- Understand MCP architecture
- Perform basic gene queries
- Learn statistical concepts

### Intermediate Level (3 prompts)
- Pathway enrichment analysis
- Data preprocessing and batch correction
- Multi-omics integration

### Advanced Level (4 prompts)
- Spatial transcriptomics
- Clinician-in-the-loop workflow
- Cost-effectiveness analysis
- Complete patient analysis project

**Total Learning Time:** ~2-3 hours (self-paced)

**Prerequisites:** Basic biology, some statistics background helpful
**Outcomes:** Ready to perform real precision medicine analyses with oversight

---

**Document Version:** 1.0
**Date:** 2026-01-16
**Target Audience:** Students, Educators, New Users
