# Data Flow & Server Communication

← Back to [Architecture Overview](ARCHITECTURE.md)

---

## Data Flow

### 1. User Query → Analysis Results

```
User: "Identify treatment targets for PatientOne using spatial pathway enrichment"
  │
  ▼
Claude API parses intent:
  - Patient ID: PAT001-OVC-2025
  - Analysis: Spatial pathway enrichment
  - Output: Treatment recommendations
  │
  ▼
Claude orchestrates multi-server workflow:
  1. mcp-mockepic → Get clinical data
  2. mcp-spatialtools → Load spatial transcriptomics
  3. mcp-spatialtools → Run pathway enrichment
  4. mcp-multiomics → Cross-validate with bulk RNA
  5. mcp-fgbio → Map variants to pathways
  │
  ▼
Claude synthesizes results:
  - Top 3 pathways: PI3K/AKT/mTOR, DNA repair, immune response
  - Treatment recommendations: Everolimus, olaparib, checkpoint inhibitors
  - Evidence: Spatial expression patterns, mutation status, NCCN guidelines
  │
  ▼
User receives structured report with visualizations
```

### 2. Server → Data → Server Flow

```
mcp-epic (FHIR) → Patient clinical data
         │
         ├──> Patient demographics (age, stage, histology)
         ├──> Diagnoses (ICD-10 codes)
         ├──> Medications (RxNorm codes)
         └──> Lab results (LOINC codes)
                 │
                 ▼
        mcp-spatialtools (Spatial RNA-seq)
                 │
                 ├──> Load Visium data (patient tissue regions)
                 ├──> Spatial differential expression
                 ├──> Pathway enrichment (spatial context)
                 └──> Results: Activated pathways by region
                         │
                         ▼
                mcp-multiomics (Bulk RNA/Protein)
                         │
                         ├──> Validate pathway activation (bulk data)
                         ├──> Stouffer meta-analysis (RNA + Protein)
                         └──> Results: Concordance with spatial findings
                                 │
                                 ▼
                        mcp-fgbio (Genomic variants)
                                 │
                                 ├──> Load VCF (mutations)
                                 ├──> Map variants to pathways
                                 └──> Results: Mutation-pathway links
                                         │
                                         ▼
                                Final report synthesis by Claude
```

---

## Server Communication

### Key Principle: Servers Do Not Call Each Other

**Why:**
- Prevents circular dependencies
- Makes debugging easier
- Claude API acts as single orchestrator
- Each server is stateless and independent

**Communication Pattern:**

```python
# ❌ BAD: Server calling another server directly
@mcp.tool()
async def my_tool():
    # Don't do this!
    result = await other_server.call_tool()
    return process(result)

# ✅ GOOD: Server returns data, Claude orchestrates
@mcp.tool()
async def my_tool():
    # Return data, let Claude decide what to do next
    return {"data": my_results}
```

**Claude orchestrates multi-server workflows:**

```
User prompt → Claude decides workflow:
  1. Call mcp-epic.get_patient_demographics()
  2. Call mcp-spatialtools.get_spatial_data_for_patient()
  3. Call mcp-spatialtools.perform_pathway_enrichment()
  4. Synthesize results into report
```

### Server-to-Server Data Passing

**Use file paths, not file contents:**

```python
# ✅ GOOD: Return file path
@mcp.tool()
async def process_spatial_data():
    output_file = "/data/patient-001/spatial/enrichment.csv"
    # ... process data, save to output_file ...
    return {"output_file": output_file, "pathways": 23}

# Then next tool can reference the file
@mcp.tool()
async def integrate_with_bulk_rna(spatial_file: str):
    spatial_data = pd.read_csv(spatial_file)
    # ... integration logic ...
```

**Shared data conventions:**

```
/data/patient-data/
├── PAT001-OVC-2025/
│   ├── clinical/
│   │   └── fhir_bundle.json           # From mcp-epic
│   ├── genomic/
│   │   ├── variants.vcf               # From sequencing pipeline
│   │   └── fastq/                     # Raw reads
│   ├── multiomics/
│   │   ├── rna_counts.csv             # From mcp-multiomics
│   │   ├── protein_abundance.csv
│   │   └── phospho_abundance.csv
│   ├── spatial/
│   │   ├── tissue_positions.csv       # From mcp-spatialtools
│   │   ├── filtered_feature_matrix/
│   │   └── pathway_enrichment.csv
│   └── imaging/
│       ├── H_and_E_slide_001.tif      # From mcp-openimagedata
│       └── multiplex_IF_tumor.tif
```
