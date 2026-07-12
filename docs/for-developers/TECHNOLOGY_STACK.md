# Technology Stack

← Back to [Architecture Overview](ARCHITECTURE.md)

---

## Core Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI** | Streamlit | Web-based chat interface |
| **UI** | Jupyter Notebook | Data science workflows |
| **AI** | Claude API (Sonnet 4.6) | Natural language orchestration |
| **Protocol** | MCP (Model Context Protocol) | AI-tool integration standard |
| **Framework** | FastMCP (Python) | Build MCP servers |
| **Transport** | STDIO (local) / SSE (cloud) | MCP communication |
| **Compute** | GCP Cloud Run | Serverless container platform |
| **Storage** | GCS (Google Cloud Storage) | Patient data, analysis results |
| **Healthcare** | GCP Healthcare API | FHIR store for clinical data |
| **Monitoring** | GCP Cloud Logging + Monitoring | Observability |

## Python Libraries by Server

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

## External APIs (Mocked in Current Version)

| API | Server | Status | Purpose |
|-----|--------|--------|---------|
| **GDC API** | mcp-mocktcga | ❌ Mocked | TCGA cohort data retrieval |
| **DeepCell API** | mcp-deepcell | ✅ Real | Cell segmentation + quantification |

**Production Roadmap:** Replace mocks with real API integrations (6-12 months)

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
