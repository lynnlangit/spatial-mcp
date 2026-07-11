# System Architecture Overview

---

## Executive Summary

The Spatial Transcriptomics component processes gene expression data with spatial coordinates to enable precision medicine insights. The system supports two workflows:

1. **CSV/Tabular Workflow** (Current) - Processes pre-processed spatial data for immediate analysis
2. **FASTQ Alignment Workflow** (Available) - Processes raw sequencing data from scratch

The architecture uses the **Model Context Protocol (MCP)** to enable AI-orchestrated bioinformatics workflows through specialized microservices.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   MCP HOST (Claude Desktop or API)               │
│             Orchestrates Workflow Execution & Analysis           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ MCP Protocol (JSON-RPC 2.0)
                         │ Transport: SSE (HTTP Streaming)
                         │
        ┌────────────────┼────────────────────────────┐
        │                │                            │
        ▼                ▼                            ▼
┌───────────────┐ ┌───────────────┐         ┌───────────────┐
│  Data Input   │ │  Processing   │         │  Visualization│
│  MCP Servers  │ │  MCP Servers  │         │  MCP Servers  │
└───────────────┘ └───────────────┘         └───────────────┘
│               │ │               │         │               │
│ mcp-fgbio     │ │ mcp-spatial   │         │ mcp-spatial   │
│ (references)  │ │ tools         │         │ tools (viz)   │
│               │ │ (analysis)    │         │               │
│ mcp-epic      │ │ mcp-multiomics│         │ mcp-openimage │
│ (clinical)    │ │ (integration) │         │ data (imaging)│
└───────────────┘ └───────────────┘         └───────────────┘
```

---

## Design Principles

### 1. Single Responsibility
Each MCP server handles one specific domain:
- **mcp-spatialtools**: Spatial transcriptomics analysis only
- **mcp-multiomics**: Multi-omics integration only
- **mcp-openimagedata**: Image processing only

### 2. Modular & Composable
Servers can be:
- Used independently or combined
- Deployed selectively (not all 9 required)
- Replaced without affecting others

### 3. AI-Orchestrated
Claude (MCP host) coordinates:
- Tool selection and sequencing
- Data flow between servers
- Error handling and retries
- Result interpretation

### 4. Production-Ready
- Input validation with JSON schemas
- Comprehensive error handling
- DRY_RUN mode for safe testing
- Resource limits and monitoring

### 5. Cloud-Native
- Containerized deployment (Docker)
- Serverless execution (GCP Cloud Run)
- Horizontal scaling
- SSE transport for streaming

---

## Data Flow: CSV Workflow (Current)

```
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 1: Data Loading                                            │
├──────────────────────────────────────────────────────────────────┤
│ Input: 3 CSV files (coordinates, expression, annotations)        │
│ Tool: Load data from patient-data directory                      │
│ Output: In-memory spatial dataset (900 spots, 31 genes)          │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 2: Spatial Analysis                                        │
├──────────────────────────────────────────────────────────────────┤
│ Tools:                                                            │
│ • calculate_spatial_autocorrelation (Moran's I)                  │
│ • perform_differential_expression (Wilcoxon test)                │
│ • perform_pathway_enrichment (GO/KEGG)                           │
│ Output: Statistical results, enriched pathways                    │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 3: Visualization                                           │
├──────────────────────────────────────────────────────────────────┤
│ Tools:                                                            │
│ • generate_spatial_heatmap                                        │
│ • generate_gene_expression_heatmap                                │
│ • generate_region_composition_chart                               │
│ • visualize_spatial_autocorrelation                               │
│ Output: PNG visualizations with timestamps                        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 4: Integration                                             │
├──────────────────────────────────────────────────────────────────┤
│ Tool: get_spatial_data_for_patient (bridge to mcp-multiomics)    │
│ Output: Spatial findings integrated with genomic/proteomic data  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: FASTQ Workflow (Available)

```
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 1: Quality Control                                         │
├──────────────────────────────────────────────────────────────────┤
│ Input: Raw FASTQ files + spatial barcodes                        │
│ Tool: filter_quality                                              │
│ Output: Filtered reads with valid barcodes                        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 2: Alignment                                               │
├──────────────────────────────────────────────────────────────────┤
│ Input: Filtered FASTQ files                                      │
│ Tool: align_spatial_data (STAR aligner)                          │
│ Dependencies: Reference genome (hg38), STAR indices              │
│ Output: Aligned BAM file with spatial tags                        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 3: Expression Quantification                               │
├──────────────────────────────────────────────────────────────────┤
│ Input: Aligned BAM file                                           │
│ Tool: Count UMIs per spot/gene                                   │
│ Output: Gene × Spot expression matrix (CSV)                      │
└──────────────────────────────────────────────────────────────────┘
                              ↓
      (Proceeds to CSV Workflow Stage 2 for analysis)
```

---

## Technology Stack

### MCP Layer
- **Protocol**: Model Context Protocol 2025-11-20
- **Transport**: SSE (Server-Sent Events over HTTP)
- **Framework**: FastMCP 0.6.0+
- **Host**: Claude Desktop (local), Claude API (cloud)

### Processing Layer
- **Language**: Python 3.11+
- **Data**: NumPy, Pandas, SciPy
- **Stats**: statsmodels, scikit-learn
- **Viz**: matplotlib, seaborn
- **Bio**: STAR (FASTQ workflow), samtools, bedtools

### Deployment Layer
- **Platform**: GCP Cloud Run
- **Containers**: Docker (python:3.11-slim base)
- **Storage**: GCS buckets
- **Monitoring**: Cloud Logging, Cloud Monitoring

---

**See Also:**
- [mcp-spatialtools README](../../../../servers/mcp-spatialtools/README.md) - Spatial tools (16 tools)
- [mcp-fgbio README](../../../../servers/mcp-fgbio/README.md) - Reference genomes, FASTQ QC
- [Server Registry](../../shared/server-registry.md) - All servers and tool counts
