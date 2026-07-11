# Scientific References

Curated list of key publications, datasets, and technical resources for precision medicine bioinformatics.

---

## Core Publications

### Model Context Protocol & AI Orchestration

**BioinfoMCP: Bioinformatics Workflows with Model Context Protocol**
- **Citation:** arXiv:2510.02139v1 (2025)
- **Link:** https://arxiv.org/html/2510.02139v1
- **Summary:** Pioneering work demonstrating how MCP can orchestrate complex bioinformatics workflows using natural language. Foundation for this repository's architecture.
- **Key Contributions:** Server design patterns, workflow orchestration, integration strategies

### Spatial Transcriptomics

**Spatial Transcriptomics: Technologies, Applications, and Experimental Considerations**
- **Citation:** Nucleic Acids Research, Volume 53, Issue 12 (2025)
- **Link:** https://academic.oup.com/nar/article/53/12/gkaf536/8174767
- **Summary:** Comprehensive review of spatial transcriptomics technologies including Visium, MERFISH, and seqFISH+
- **Relevance:** Technical foundation for mcp-spatialtools implementation

**STAR: Ultrafast Universal RNA-seq Aligner**
- **Citation:** Dobin et al., Bioinformatics (2013)
- **DOI:** 10.1093/bioinformatics/bts635
- **Summary:** Spliced alignment algorithm for RNA-seq data
- **Implementation:** Used in `mcp-spatialtools.align_spatial_data()`

### Batch Effect Correction

**ComBat: Adjusting Batch Effects in Microarray Expression Data**
- **Citation:** Johnson et al., Biostatistics (2007)
- **DOI:** 10.1093/biostatistics/kxj037
- **Summary:** Empirical Bayes method for removing batch effects while preserving biological variation
- **Implementation:** Used in `mcp-spatialtools.perform_batch_correction()`

### Multi-Omics Integration

**HAllA: Hierarchical All-against-All Association Discovery**
- **Citation:** Rahnavard et al., PLOS Computational Biology (2017)
- **DOI:** 10.1371/journal.pcbi.1005308
- **Summary:** Method for discovering associations between high-dimensional datasets
- **Implementation:** Core algorithm in `mcp-multiomics` (95% real)

**Meta-Analysis with Stouffer's Method**
- **Citation:** Stouffer et al., "The American Soldier" (1949)
- **Summary:** Combines p-values from independent tests using Z-score transformation
- **Implementation:** Used in `mcp-multiomics.calculate_stouffer_meta()`

---

## Public Datasets

### Cancer Genomics

**The Cancer Genome Atlas (TCGA) - Ovarian Cancer**
- **Project:** TCGA-OV
- **Link:** https://portal.gdc.cancer.gov/projects/TCGA-OV
- **Data Types:** WXS, RNA-seq, SNP arrays, clinical data
- **Sample Size:** 600+ High-Grade Serous Ovarian Carcinoma samples
- **Relevance:** Reference cohort for mcp-mocktcga server, pathway curation

**TCGA Publications:**
- Integrated genomic analyses of ovarian carcinoma (Nature, 2011)
- DOI: 10.1038/nature10166

### Spatial Transcriptomics Datasets

**10x Genomics Public Datasets**
- **Link:** https://www.10xgenomics.com/datasets
- **Platforms:** Visium, Xenium, Chromium
- **Data Types:** Spatial gene expression, histology images, spatial coordinates
- **Use Cases:** Validation data for mcp-spatialtools, educational examples

**Visium Spatial Gene Expression**
- Human breast cancer datasets
- Mouse brain tissue datasets
- Human ovarian cancer (if available)

---

## Pathway & Annotation Databases

### KEGG (Kyoto Encyclopedia of Genes and Genomes)
- **Link:** https://www.genome.jp/kegg/
- **Pathways Used:** PI3K-Akt signaling, p53 signaling, cell cycle, apoptosis
- **Implementation:** 44 curated pathways in mcp-spatialtools pathway enrichment

### Gene Ontology (GO)
- **Link:** http://geneontology.org/
- **Categories Used:** Biological Process (GO_BP), Molecular Function, Cellular Component
- **Implementation:** Pathway enrichment in mcp-spatialtools

### MSigDB (Molecular Signatures Database)
- **Link:** https://www.gsea-msigdb.org/gsea/msigdb/
- **Collections Used:** Hallmark gene sets, drug resistance signatures
- **Implementation:** Custom curated pathways in mcp-spatialtools

---

## Genome References

### GENCODE Human Genome Annotation
- **Link:** https://www.gencodegenes.org/
- **Version Used:** GRCh38.p14 (hg38)
- **Components:** Gene annotations, transcript models, regulatory elements
- **Implementation:** STAR genome index preparation, gene ID mapping

### Ensembl Genome Browser
- **Link:** https://www.ensembl.org/
- **Use Case:** Alternative genome annotations, variant effect prediction

---

## Statistical Methods

### Multiple Testing Correction

**Benjamini-Hochberg FDR Control**
- **Citation:** Benjamini & Hochberg, Journal of the Royal Statistical Society (1995)
- **DOI:** 10.1111/j.2517-6161.1995.tb02031.x
- **Implementation:** FDR correction in pathway enrichment, differential expression

### Spatial Statistics

**Moran's I Spatial Autocorrelation**
- **Citation:** Moran, Biometrika (1950)
- **DOI:** 10.2307/2332142
- **Summary:** Measures spatial autocorrelation (clustering vs random distribution)
- **Implementation:** `mcp-spatialtools.calculate_spatial_autocorrelation()`

### Non-Parametric Tests

**Mann-Whitney U Test**
- **Citation:** Mann & Whitney, Annals of Mathematical Statistics (1947)
- **Summary:** Non-parametric test for comparing two independent groups
- **Implementation:** Differential expression in mcp-spatialtools

**Fisher's Exact Test**
- **Citation:** Fisher, Journal of the Royal Statistical Society (1922)
- **Summary:** Test for independence in 2×2 contingency tables
- **Implementation:** Pathway enrichment (gene overlap significance)

---

## Technical Specifications

### FHIR (Fast Healthcare Interoperability Resources)
- **Link:** https://hl7.org/fhir/
- **Version:** R4
- **Resources Used:** Patient, Condition, Observation, MedicationStatement
- **Implementation:** mcp-mockepic server structure

### Model Context Protocol
- **Specification:** https://modelcontextprotocol.io/specification/2025-06-18
- **GitHub:** https://github.com/modelcontextprotocol
- **Python SDK:** FastMCP framework

---

## Clinical Resources (For Context Only)

**ClinicalTrials.gov - Ovarian Cancer**
- **Link:** https://clinicaltrials.gov/
- **Search:** "ovarian cancer" + "precision medicine"
- **Note:** For educational reference only - not clinical recommendations

**National Cancer Institute (NCI) - Ovarian Cancer**
- **Link:** https://www.cancer.gov/types/ovarian
- **Resources:** Treatment information, clinical trial finder

---

## How to Cite

If you use any of these references in your research with this repository, please cite both the original publication and this repository:

```bibtex
@software{langit2026precision,
  author = {Langit, Lynn},
  title = {Precision Medicine MCP Servers: AI-Orchestrated Clinical Bioinformatics},
  year = {2026},
  url = {https://github.com/lynnlangit/precision-medicine-mcp},
  note = {PatientOne - In memory of a dear friend}
}
```

---

**Maintained by:** Lynn Langit  
**Contributions:** Pull requests welcome to add relevant publications  
