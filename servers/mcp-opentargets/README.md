# mcp-opentargets

MCP server for querying the [Open Targets Platform](https://platform.opentargets.org/) GraphQL API. Retrieves drug-target evidence, association scores, safety data, and known drugs for gene targets — particularly HGSOC (high-grade serous ovarian carcinoma) targets.

## Tools (6)

| Tool | Description |
|------|-------------|
| `get_target_info` | Look up gene/target information and tractability |
| `get_target_disease_associations` | Association evidence scores between gene and disease |
| `get_target_drugs` | Approved and in-trial drugs for a gene target |
| `search_targets_by_disease` | Top gene targets associated with a disease |
| `get_target_safety` | Safety and adverse event profiles |
| `batch_score_targets` | Score multiple genes against a disease in batch |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENTARGETS_DRY_RUN` | `true` | Return synthetic data (set `false` for live API) |
| `OPENTARGETS_API_URL` | `https://api.platform.opentargets.org/api/v4/graphql` | GraphQL endpoint |
| `MCP_TRANSPORT` | `stdio` | Transport mode (`stdio`, `sse`, `streamable-http`) |
| `MCP_PORT` | `8000` | Port for SSE/HTTP transport |

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests (DRY_RUN mode, no API calls)
uv run pytest -v

# Start server (stdio mode)
uv run python -m mcp_opentargets

# Start server (SSE mode)
MCP_TRANSPORT=sse MCP_PORT=3015 uv run python -m mcp_opentargets
```

## Docker

```bash
docker build -t mcp-opentargets .
docker run -p 3015:3015 mcp-opentargets
```

## Default Disease

The default disease ID is **EFO_0001071** (ovarian carcinoma). Override via the `disease_id` parameter on any tool.

## No Authentication Required

The Open Targets Platform API is public and free. No API key needed.
