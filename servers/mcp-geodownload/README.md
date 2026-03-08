# mcp-geodownload

MCP server for downloading gene expression datasets from [NCBI GEO](https://www.ncbi.nlm.nih.gov/geo/) and [SRA](https://www.ncbi.nlm.nih.gov/sra/) databases. Provides the data ingestion gateway for bulk RNA-seq expression matrices used in CIBERSORTx deconvolution and HGSOC reference cohort analysis (GSE32062, GSE26712).

## Tools (6)

| Tool | Description |
|------|-------------|
| `search_geo_datasets` | Search GEO for gene expression datasets by keyword |
| `get_geo_metadata` | Get detailed metadata for a GEO Series accession |
| `download_geo_expression_matrix` | Download Series Matrix expression file |
| `list_geo_samples` | List all samples (GSMs) in a dataset |
| `download_sra_fastq` | Download raw FASTQ files from SRA |
| `get_geo_soft_file` | Download raw SOFT metadata file |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEO_DRY_RUN` | `true` | Return synthetic data (set `false` for live API) |
| `GEO_CACHE_DIR` | `/data/cache/geodownload` | Directory for downloaded files |
| `NCBI_API_KEY` | _(none)_ | NCBI API key for higher rate limits (10 req/sec vs 3) |
| `NCBI_EMAIL` | _(none)_ | Email for NCBI E-utilities identification |
| `MCP_TRANSPORT` | `stdio` | Transport mode (`stdio`, `sse`, `streamable-http`) |
| `MCP_PORT` | `8000` | Port for SSE/HTTP transport |

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests (DRY_RUN mode, no API calls)
uv run pytest -v

# Start server (stdio mode)
uv run python -m mcp_geodownload

# Start server (SSE mode)
MCP_TRANSPORT=sse MCP_PORT=3013 uv run python -m mcp_geodownload
```

## Docker

```bash
docker build -t mcp-geodownload .
docker run -p 3013:3013 mcp-geodownload
```

## Key HGSOC Reference Datasets

| GSE ID | Cohort | Samples | Description |
|--------|--------|---------|-------------|
| GSE32062 | JGOG (Tothill) | 260 | HGSOC molecular subtypes |
| GSE26712 | Bonome | 195 | Epithelial ovarian cancer |
| GSE9899 | AOCS | 285 | Serous/endometrioid subtypes |

## Production Requirements

For non-DRY_RUN mode:
- **NCBI API key** recommended (free at [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/))
- **sra-tools** required for `download_sra_fastq` (`prefetch`, `fasterq-dump`)
