# Platform Overview (Canonical Reference)

The Precision Medicine MCP platform uses multiple MCP servers providing specialized tools for AI-orchestrated precision oncology analysis. For current counts, see the [Server Registry](server-registry.md).

---

## Server Status Matrix

See [Server Registry](server-registry.md) for current server names, tool counts, and production status.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              User Interface Layer                │
│   Streamlit App │ Jupyter Notebook │ Dashboard   │
├─────────────────────────────────────────────────┤
│           AI Orchestration (Claude/Gemini)        │
│   Natural language → tool calls → integration    │
├─────────────────────────────────────────────────┤
│          MCP Servers (see server-registry.md)      │
│   Clinical │ Genomic │ Spatial │ Imaging │ ...   │
├─────────────────────────────────────────────────┤
│                 Data Layer                        │
│   GCS │ Epic FHIR │ Local Files │ TCGA/GDC      │
└─────────────────────────────────────────────────┘
```

## Data Modalities

1. **Clinical** — Epic FHIR with automatic de-identification
2. **Genomic** — WES/WGS somatic variants, CNV, germline risk, HRD scoring
3. **Multi-omics** — RNA-seq + proteomics + phosphoproteomics integration
4. **Spatial** — 10x Visium spatial transcriptomics, cell deconvolution
5. **Imaging** — H&E histopathology, multiplex immunofluorescence
