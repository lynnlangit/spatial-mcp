# CLAUDE.md — Project Context for Claude Code

## Git Workflow

When committing and pushing changes, always complete the full git add/commit/push cycle before reporting task completion. If a usage limit is approaching, prioritize finishing the commit/push over starting new work.

## Session Management

When rate limits or usage limits are hit mid-task, save progress notes in a scratch file (e.g., `.claude/progress.md`) listing completed steps and remaining work so the next session can resume efficiently.

## What This Project Is

Precision Medicine MCP Platform — an AI-orchestrated system for precision oncology analysis. It provides specialized MCP (Model Context Protocol) servers that expose bioinformatics tools via natural language through Claude or Gemini.

**Primary use case:** Stage IV Ovarian Cancer analysis using synthetic patient data (PatientOne: PAT001-OVC-2025).

## Repository Structure

```
precision-medicine-mcp/
├── servers/                    # MCP servers (Python, FastMCP)
│   ├── mcp-fgbio/             # Genomic reference data (4 tools)
│   ├── mcp-multiomics/        # RNA/Protein/Phospho integration (10 tools)
│   ├── mcp-spatialtools/      # Spatial transcriptomics (14 tools)
│   ├── mcp-epic/              # Epic FHIR integration (4 tools, local-only)
│   ├── mcp-mockepic/          # Synthetic EHR for demos (3 tools)
│   ├── mcp-perturbation/      # Perturbation prediction (8 tools)
│   ├── mcp-quantum-celltype-fidelity/  # Quantum cell type fidelity (6 tools)
│   ├── mcp-openimagedata/     # Histology image processing (5 tools)
│   ├── mcp-deepcell/          # Cell segmentation (3 tools)
│   ├── mcp-cell-classify/     # Cell phenotype classification (3 tools)
│   ├── mcp-mocktcga/           # Mock TCGA cohort comparison (5 tools)
│   ├── mcp-patient-report/    # PDF report generation (5 tools)
│   ├── mcp-genomic-results/   # Somatic variant/CNV parsing (4 tools)
│   └── mcp-server-boilerplate/# Template for new servers
├── data/                       # Patient data and reference files
│   ├── patient-data/PAT001-OVC-2025/  # Synthetic PatientOne data
│   ├── reference/             # Reference genomes
│   └── cache/                 # Runtime caches
├── docs/                       # Documentation (by audience)
│   ├── for-developers/        # Developer guides
│   ├── for-educators/         # Teaching materials
│   ├── for-funders/           # Stakeholder docs
│   ├── for-hospitals/         # Hospital deployment
│   ├── for-researchers/       # Researcher guides
│   ├── getting-started/       # Installation and setup
│   └── reference/             # Architecture, testing, prompts
│       └── shared/server-registry.md  # Canonical server/tool counts
├── ui/                         # User interfaces
│   ├── streamlit-app/         # Main Streamlit web app
│   ├── streamlit-app-students/# Simplified student version
│   ├── dashboard/             # Monitoring dashboard
│   └── jupyter-notebook/      # Jupyter integration
├── infrastructure/             # Deployment configs (GCP, Docker)
└── tests/                      # Manual and integration tests
```

## How MCP Servers Work

Each server in `servers/mcp-*/` follows this pattern:

- **Entry point:** `src/mcp_<name>/server.py` using FastMCP
- **Config:** `pyproject.toml` with dependencies
- **Tests:** `tests/test_server.py` (pytest + pytest-asyncio)
- **Package manager:** `uv` (not pip/venv)

### Running a server locally

```bash
cd servers/mcp-fgbio
uv run python -m mcp_fgbio
```

### Running tests for a server

```bash
cd servers/mcp-multiomics
uv run pytest -v
```

### All servers use DRY_RUN mode by default

When `*_DRY_RUN=true`, servers return synthetic/simulated data without requiring real bioinformatics tools or large reference datasets. This is the default for safe testing.

## Key Conventions

- **Python 3.11+** required
- **FastMCP** framework for all servers (`@mcp.tool()` decorator)
- **`uv`** for dependency management (not pip/venv)
- **Source of truth for server/tool counts:** `docs/reference/shared/server-registry.md`
- **Synthetic data only** — no real patient data in repo (HIPAA safe)
- **Line length:** 100 chars (black + ruff)
- **Async:** All MCP tool functions are async
- **AI Skills:** `docs/reference/skills/` contains project-specific instruction sets (e.g., compliance, testing, data ops) that AI coding assistants can reference by name

## Common Tasks

### Run all tests for a specific server
```bash
cd servers/mcp-multiomics && uv run pytest -v
```

### Check which tools a server exposes
Look at `src/mcp_<name>/server.py` for `@mcp.tool()` decorated functions.

### Add a new tool to a server
1. Add async function with `@mcp.tool()` in `server.py`
2. Add tests in `tests/test_server.py`
3. Update the server's `README.md` tool count

### Explore PatientOne test data
```bash
ls data/patient-data/PAT001-OVC-2025/
```
