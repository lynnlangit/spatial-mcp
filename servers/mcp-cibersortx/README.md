# mcp-cibersortx

MCP server for cell-type deconvolution via the [CIBERSORTx](https://cibersortx.stanford.edu/) web API. Infers immune and stromal cell-type fractions from bulk RNA-seq expression matrices, revealing the tumor microenvironment composition for HGSOC samples.

## Tools (5)

| Tool | Description |
|------|-------------|
| `run_cibersortx_deconvolution` | Submit bulk expression matrix for cell-type deconvolution |
| `upload_signature_matrix` | Upload custom scRNA-seq signature matrix |
| `get_job_status` | Poll CIBERSORTx job progress (QUEUED/RUNNING/COMPLETED/FAILED) |
| `download_results` | Download completed deconvolution results |
| `run_mock_deconvolution` | Local NNLS approximate deconvolution (no token needed) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CIBERSORTX_DRY_RUN` | `true` | Return synthetic data (set `false` for live API) |
| `CIBERSORTX_TOKEN` | _(none)_ | CIBERSORTx API token (required for production) |
| `CIBERSORTX_EMAIL` | _(none)_ | Email registered with CIBERSORTx |
| `CIBERSORTX_API_URL` | `https://cibersortx.stanford.edu/api` | CIBERSORTx API endpoint |
| `CIBERSORTX_CACHE_DIR` | `/data/cache/cibersortx` | Directory for downloaded results |
| `CIBERSORTX_POLL_INTERVAL` | `30` | Seconds between job status polls |
| `CIBERSORTX_MAX_WAIT` | `1800` | Max seconds to wait for job completion |
| `MCP_TRANSPORT` | `stdio` | Transport mode (`stdio`, `sse`, `streamable-http`) |
| `MCP_PORT` | `8000` | Port for SSE/HTTP transport |

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests (DRY_RUN mode, no API calls)
uv run pytest -v

# Start server (stdio mode)
uv run python -m mcp_cibersortx

# Start server (SSE mode)
MCP_TRANSPORT=sse MCP_PORT=3014 uv run python -m mcp_cibersortx
```

## Docker

```bash
docker build -t mcp-cibersortx .
docker run -p 3014:3014 -e CIBERSORTX_TOKEN=your_token mcp-cibersortx
```

## HGSOC Tumor Microenvironment

DRY_RUN mode returns biologically realistic HGSOC immune fractions:

| Cell Type | Typical Fraction | Significance |
|-----------|-----------------|--------------|
| Macrophages M2 | 28-40% | Immunosuppressive, dominant population |
| Neutrophils | 5-11% | Tumor-associated neutrophils |
| CD8 T cells | 5-12% | Low = "cold" tumor, poor ICI response |
| Macrophages M0/M1 | 6-10% each | Mixed polarization |
| Tregs | 4-7% | Immunosuppressive regulatory T cells |
| NK cells | 2-3% | Low natural killer cell infiltration |

## Production Requirements

- **CIBERSORTx token**: Register free at [cibersortx.stanford.edu](https://cibersortx.stanford.edu/)
- Token is validated at server startup when `CIBERSORTX_DRY_RUN=false`
- Jobs typically take 5-30 minutes depending on sample count
