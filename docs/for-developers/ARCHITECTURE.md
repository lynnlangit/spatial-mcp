# System Architecture Overview

High-level architecture for developers building or extending the precision-medicine-mcp platform.

---

## Table of Contents

1. [System Layers](#system-layers)
2. [Data Flow](#data-flow)
3. [Server Communication](#server-communication)
4. [Integration Patterns](#integration-patterns)
5. [Technology Stack](#technology-stack)

---

## System Layers

The precision-medicine-mcp platform consists of 5 architectural layers:

```
┌──────────────────────────────────────────────────────────────┐
│                   USER INTERFACE LAYER                        │
│  Streamlit UI (web) | Jupyter Notebook (data science)        │
│  Claude Desktop (local) | Claude API (production)            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                  AI ORCHESTRATION LAYER                       │
│         Claude API (Anthropic Sonnet 4.5)                    │
│         • Natural language query parsing                      │
│         • Multi-server workflow orchestration                │
│         • Result synthesis and reporting                     │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                    MCP PROTOCOL LAYER                         │
│         Tool discovery | Input validation | Error handling   │
│         STDIO (local) or SSE (cloud) transport               │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                   SERVER EXECUTION LAYER                      │
│         MCP Servers (FastMCP-based)                           │
│         • Most production-ready (see Server Registry)        │
│         • Some mocked (tcga, mockepic)                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                      DATA LAYER                               │
│         • GCS buckets (patient data, analysis results)       │
│         • GCP Healthcare API (FHIR stores)                   │
│         • Reference data (genomes, pathways, ontologies)     │
│         • External APIs (TCGA, DeepCell, HuggingFace)        │
└──────────────────────────────────────────────────────────────┘
```

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

## Technology Stack

### Core Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI** | Streamlit | Web-based chat interface |
| **UI** | Jupyter Notebook | Data science workflows |
| **AI** | Claude API (Sonnet 4.5) | Natural language orchestration |
| **Protocol** | MCP (Model Context Protocol) | AI-tool integration standard |
| **Framework** | FastMCP (Python) | Build MCP servers |
| **Transport** | STDIO (local) / SSE (cloud) | MCP communication |
| **Compute** | GCP Cloud Run | Serverless container platform |
| **Storage** | GCS (Google Cloud Storage) | Patient data, analysis results |
| **Healthcare** | GCP Healthcare API | FHIR store for clinical data |
| **Monitoring** | GCP Cloud Logging + Monitoring | Observability |

### Python Libraries by Server

**mcp-fgbio:**
- `pysam` - BAM/VCF file handling
- `pyfaidx` - FASTA reference genome indexing

**mcp-multiomics:**
- `pandas`, `numpy` - Data manipulation
- `scipy` - Statistical testing
- `statsmodels` - Meta-analysis (Stouffer's method)
- `HAllA` - Multi-omics integration

**mcp-spatialtools:**
- `scanpy` - Single-cell/spatial transcriptomics analysis
- `squidpy` - Spatial statistics (Moran's I, spatial graphs)
- `numpy`, `scipy` - Numerical computing

**mcp-openimagedata:**
- `opencv-python` - Image processing
- `Pillow` - Image I/O
- `numpy` - Array operations

**mcp-epic:**
- `google-cloud-healthcare` - GCP Healthcare API
- `fhir.resources` - FHIR data models
- `google-cloud-logging` - HIPAA-compliant audit logging

**All servers:**
- `fastmcp` - MCP server framework
- `pytest`, `pytest-asyncio` - Testing
- `pytest-cov` - Code coverage

### External APIs (Mocked in Current Version)

| API | Server | Status | Purpose |
|-----|--------|--------|---------|
| **GDC API** | mcp-mocktcga | ❌ Mocked | TCGA cohort data retrieval |
| **DeepCell API** | mcp-deepcell | ✅ Real | Cell segmentation + quantification |

**Production Roadmap:** Replace mocks with real API integrations (6-12 months)

---

## Key Design Principles

### 1. Stateless Servers
Each tool call is independent. Servers don't maintain session state.

**Why:** Simplifies debugging, enables horizontal scaling, makes caching easier.

### 2. DRY_RUN Mode
All servers support synthetic data mode for demos without real data or API keys.

**Why:** Instant demos, education use cases, CI/CD testing without credentials.

### 3. Tool-Centric Design
Each tool does one thing well. Prefer many small tools over few large ones.

**Why:** Claude can compose complex workflows from simple building blocks.

### 4. Data-Last Philosophy
Tools return data and metadata. Claude interprets and presents to users.

**Why:** Separates computation from presentation, enables flexible UI layers.

### 5. Error Messages for Humans
Error messages explain what went wrong and suggest fixes.

**Why:** Claude needs actionable error messages to retry or adjust workflows.

**Example:**
```python
# ❌ BAD: Cryptic error
raise ValueError("Invalid input")

# ✅ GOOD: Actionable error
raise ValueError(
    "Invalid VCF file format. Expected columns: CHROM, POS, REF, ALT. "
    "Found: {actual_columns}. "
    "Try: mcp-fgbio.validate_vcf(file_path) to check format."
)
```

### 6. Observability & Traceability

Every tool call is logged with full context — no AI routing decision is invisible.

The platform captures traceability data at three layers:

1. **Structured tool logging** (`shared/common/logging.py`) — JSON-formatted logs emitted by each MCP server recording tool name, request ID, parameters, duration, and success/failure.
2. **HIPAA audit events** (`ui/streamlit-app/utils/audit_logger.py`) — 10 event types (login, query, response, error, server/model selection, session lifecycle, benchmarks) sent to Cloud Logging with 10-year retention.
3. **UI orchestration traces** (`ui/streamlit-app/utils/trace_utils.py` + `trace_display.py`) — per-call trace data extracted from AI responses, displayed in 4 visualization modes (log, cards, timeline, Mermaid sequence diagram), and exportable as JSON or Mermaid.

A live monitoring dashboard (`ui/dashboard/`) provides server health, cost analysis, performance metrics, and optimization recommendations.

**See also:** [Server Registry](../reference/shared/server-registry.md)

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

---

## Performance Considerations

### Latency Budget (per tool call)

| Operation | Target | Notes |
|-----------|--------|-------|
| **Tool call overhead** | <1 sec | MCP protocol + FastMCP |
| **Data loading** | 1-5 sec | Local files, <100MB |
| **Statistical analysis** | 5-30 sec | Differential expression, pathway enrichment |
| **Heavy computation** | 30-300 sec | Batch correction, dimensionality reduction |
| **External API calls** | 1-10 sec | NCBI, KEGG (with caching) |

**Total workflow:** 25-35 min DRY_RUN / an estimated 2-5 hours production for comprehensive multi-modal analysis

### Scalability

**Current capacity (single instance):**
- 1-2 concurrent analyses
- 10-20 tool calls/minute
- 100GB patient data

**Production scaling (GCP Cloud Run):**
- Auto-scales to 100+ instances
- Handles 100+ concurrent analyses
- Petabyte-scale data with GCS

---

## Next Steps for Developers

1. **Understand the architecture** (this doc + README.md) - 30 min
2. **Study a reference server** (mcp-multiomics recommended) - 30 min
3. **Build a new server** (follow ADD_NEW_MODALITY_SERVER.md) - 4-8 hours
4. **Write tests** (≥50% coverage for production) - 1-2 hours
5. **Deploy to GCP** (Cloud Run deployment) - 30 min
6. **Integrate with workflow** (test with PatientOne) - 30 min

**See:** [README.md](README.md) for quick start paths and resources.

---

**Related Resources:**
- **[ADD_NEW_MODALITY_SERVER.md](ADD_NEW_MODALITY_SERVER.md)** - Step-by-step guide for building new servers
- **[Server Registry](../reference/shared/server-registry.md)** - Canonical server/tool counts
- **[Server Implementations](../../servers/README.md)** - Code examples

---

**Last Updated:** 2026-04-11
