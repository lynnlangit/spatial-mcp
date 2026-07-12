# Integration Patterns

← Back to [Architecture Overview](ARCHITECTURE.md)

---

## Integration Patterns

### Pattern 1: Clinical → Genomic Workflow

```
mcp-epic: Get patient diagnosis (ovarian cancer, stage IV)
    ↓
mcp-fgbio: Load reference genome + patient VCF
    ↓
mcp-fgbio: Identify pathogenic variants (TP53, BRCA1)
    ↓
Claude synthesizes: Treatment implications (PARP inhibitors for BRCA1)
```

**Server responsibilities:**
- mcp-epic: FHIR data retrieval, de-identification
- mcp-fgbio: Variant calling, annotation, reference data
- Claude: Clinical interpretation, treatment matching

### Pattern 2: Multi-Omics Integration

```
mcp-multiomics: Load RNA, Protein, Phospho data
    ↓
mcp-multiomics: Stouffer meta-analysis (combine p-values)
    ↓
mcp-multiomics: Pathway enrichment (KEGG)
    ↓
mcp-fgbio: Map variants to enriched pathways
    ↓
Claude synthesizes: Mutation-pathway-drug connections
```

**Server responsibilities:**
- mcp-multiomics: Data integration, statistical testing, pathway analysis
- mcp-fgbio: Variant-pathway mapping
- Claude: Connect pathways to actionable treatments

### Pattern 3: Spatial → Clinical Bridge

```
mcp-spatialtools: Load Visium spatial transcriptomics
    ↓
mcp-spatialtools: Identify tumor vs. normal regions
    ↓
mcp-spatialtools: Spatial pathway enrichment (tumor microenvironment)
    ↓
mcp-mockepic: Link spatial findings to clinical presentation
    ↓
Claude synthesizes: Spatial heterogeneity implications for treatment
```

**Server responsibilities:**
- mcp-spatialtools: Spatial analysis, microenvironment characterization
- mcp-mockepic: Clinical context (stage, histology, treatment history)
- Claude: Interpret spatial patterns for clinical decisions

### Pattern 4: Imaging → Classification → Spatial Integration

```
mcp-openimagedata: Load H&E slide + MxIF images
    ↓
mcp-deepcell: Cell segmentation (nuclear/membrane models)
    ↓
mcp-deepcell: Quantify per-cell marker intensities (Ki67, TP53, CD8)
    ↓
mcp-cell-classify: Classify phenotypes (Ki67+/TP53+ double-positive)
    ↓
mcp-spatialtools: Overlay spatial transcriptomics on segmentation
    ↓
Claude synthesizes: Immune contexture and treatment implications
```

**Server responsibilities:**
- mcp-openimagedata: Image retrieval, preprocessing
- mcp-deepcell: Cell segmentation + per-cell marker quantification
- mcp-cell-classify: Phenotype classification + visualization (lightweight, no TensorFlow)
- mcp-spatialtools: Spatial statistics, cell-type deconvolution
- Claude: Integrate imaging + transcriptomics for immune profiling

---

## PatientOne Example Workflow

**User Prompt:**
> "Perform comprehensive multi-modal analysis for PatientOne (PAT001-OVC-2025) and identify top 3 treatment targets."

**Orchestrated Workflow (DRY_RUN: ~35 minutes / Production: an estimated 2-5 hours):**

```
[Stage 0] De-identification (prerequisite — run once per patient onboarding)
  → mcp-deidentify.deidentify_json(json_content=patient_record, patient_id="PAT001-OVC-2025")
  → mcp-deidentify.generate_anonymization_key(patient_id="PAT001-OVC-2025")
  → Writes PAT001-OVC-2025_anonymization_key.json (stored separately from pipeline data)

[0-5 min] Clinical Context
  → mcp-mockepic.query_patient_records(patient_id="PAT001-OVC-2025")
  → Returns: Stage IV HGSOC, platinum-resistant, CA-125 elevated

[5-12 min] Genomic Analysis
  → mcp-fgbio.fetch_reference_genome(build="GRCh38")
  → mcp-genomic-results.parse_somatic_variants(vcf_path="/data/PAT001/genomic/variants.vcf")
  → Returns: TP53 mutation, BRCA1 germline variant

[12-22 min] Multi-Omics Integration
  → mcp-multiomics.integrate_omics_data(patient_id="PAT001-OVC-2025")
  → mcp-multiomics.calculate_stouffer_meta(modalities=["rna","protein","phospho"])
  → mcp-multiomics.predict_upstream_regulators(method="gsea")
  → Returns: PI3K/AKT/mTOR pathway activation (p<0.001)

[22-32 min] Spatial Transcriptomics
  → mcp-spatialtools.get_spatial_data_for_patient(patient_id="PAT001-tumor-region-1")
  → mcp-spatialtools.perform_pathway_enrichment()
  → Returns: Spatial heterogeneity, immune exhaustion in tumor core

[32-35 min] Report Synthesis
  → Claude synthesizes results:
    1. BRCA1 variant → PARP inhibitor (olaparib)
    2. PI3K/AKT/mTOR activation → mTOR inhibitor (everolimus)
    3. Immune exhaustion → Checkpoint inhibitor (pembrolizumab)
```

**Server Call Summary:**
- 2 calls to mcp-deidentify (Stage 0, one-time per patient onboarding)
- 2 calls to mcp-mockepic
- 3 calls to mcp-fgbio
- 4 calls to mcp-multiomics
- 3 calls to mcp-spatialtools
- **Total: 14 tool calls, ~35 min DRY_RUN / an estimated 2-5 hrs production**
