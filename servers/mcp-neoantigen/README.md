# mcp-neoantigen

MCP server for neoantigen prediction, HLA-peptide binding, and antigen presentation pathway scoring. Predicts which tumor-specific peptides are presented by MHC molecules, estimates neoantigen burden, and computes an integrative immunotherapy responsiveness score.

## Tools (6)

| Tool | Description |
|------|-------------|
| `predict_mhc1_binding` | MHC class I binding prediction via IEDB API |
| `predict_mhc2_binding` | MHC class II binding prediction via IEDB API |
| `run_pvacseq` | Neoantigen prediction pipeline from VCF |
| `estimate_neoantigen_burden` | TMB-to-neoantigen conversion (no API needed) |
| `get_hla_typing_from_rna` | HLA typing from RNA-seq via OptiType |
| `score_antigen_presentation_pathway` | Integrative immunotherapy responsiveness score |

## XAI Metadata

Every tool returns an `xai_metadata` field with explainability information:

| Field | Description |
|-------|-------------|
| `confidence_level` | `high`, `moderate`, or `low` — how reliable the result is given the inputs |
| `confidence_note` | Why this confidence level was assigned |
| `key_drivers` | 1-3 inputs that most influenced the result |
| `guideline_version` | Specific algorithm or database reference (e.g., IEDB, NetMHCpan) |
| `evidence_grade` | Algorithm-Predicted — Not Clinical Grade or Computational Prediction — Research Only |
| `counterfactual` | What would change if a key input were different |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEOANTIGEN_DRY_RUN` | `true` | Return synthetic data (set `false` for live API) |
| `NEOANTIGEN_CACHE_DIR` | `/data/cache/neoantigen` | Directory for output files |
| `NEOANTIGEN_IEDB_API_URL` | `http://tools-cluster-interface.iedb.org/tools_api` | IEDB API endpoint |
| `NEOANTIGEN_IEDB_BATCH_SIZE` | `100` | Peptides per IEDB API call |
| `NEOANTIGEN_PVACTOOLS_PATH` | _(none)_ | Path to pVACseq binary (optional) |
| `NEOANTIGEN_OPTITYPE_PATH` | _(none)_ | Path to OptiType binary (optional) |
| `NEOANTIGEN_STRONG_BINDER_NM` | `50.0` | IC50 threshold for strong binder (nM) |
| `NEOANTIGEN_WEAK_BINDER_NM` | `500.0` | IC50 threshold for weak binder (nM) |
| `MCP_TRANSPORT` | `stdio` | Transport mode (`stdio`, `sse`, `streamable-http`) |
| `MCP_PORT` | `8000` | Port for SSE/HTTP transport |

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests (DRY_RUN mode, no API calls)
uv run pytest -v

# Start server (stdio mode)
uv run python -m mcp_neoantigen

# Start server (SSE mode)
MCP_TRANSPORT=sse MCP_PORT=3016 uv run python -m mcp_neoantigen
```

## Docker

```bash
docker build -t mcp-neoantigen .
docker run -p 3016:3016 mcp-neoantigen
```

## PatientOne Mock Data

DRY_RUN mode returns predictions based on synthetic PatientOne mutations:

| Mutation | Gene | Top Peptide | HLA | IC50 (nM) | Classification |
|----------|------|-------------|-----|-----------|----------------|
| R175H | TP53 | RMPEAAPPV | HLA-A*02:01 | 45.2 | Strong binder |
| R175H | TP53 | VVHCHQIIY | HLA-A*03:01 | 78.3 | Strong binder |
| E545K | PIK3CA | KITEESPFI | HLA-A*02:01 | 62.1 | Strong binder |

## Production Requirements

- **IEDB API** (free, no auth): Used by `predict_mhc1_binding` and `predict_mhc2_binding`
- **pVACtools** (optional): Local neoantigen prediction pipeline
- **OptiType** (optional): HLA typing from RNA-seq data
- **samtools** (optional): Required by OptiType
