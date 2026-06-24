# mcp-deidentify

HIPAA-aligned de-identification server for Precision Medicine MCP -- Stage 0 preprocessing.

## Status

**Phase 1** -- Engine + code generator + DRY_RUN fixture + tests. Tool stubs only.

## Quick Start

```bash
cd servers/mcp-deidentify
uv pip install -e ".[dev]"
uv run pytest tests/ -v
```

## Tools (Phase 2+)

6 tools planned -- see `server.py` for stubs.
