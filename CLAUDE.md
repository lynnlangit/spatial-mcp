# CLAUDE.md — Project Context for Claude Code

## Git Workflow

When committing and pushing changes, always complete the full git add/commit/push cycle before reporting task completion. If a usage limit is approaching, prioritize finishing the commit/push over starting new work.

## Session Management

When rate limits or usage limits are hit mid-task, save progress notes in a scratch file (e.g., `.claude/progress.md`) listing completed steps and remaining work so the next session can resume efficiently.

## What This Project Is

Precision Medicine MCP Platform — an AI-orchestrated system for precision medicine analysis across oncology and preventive health. It provides specialized MCP (Model Context Protocol) servers that expose bioinformatics and clinical risk tools via natural language through Claude or Gemini. See [Server Registry](docs/reference/shared/server-registry.md) for current server and tool counts.

**Validated use cases (three synthetic patients, all live e2e tested):**
- **PAT001** (PAT001-OVC-2025) — Stage IV HGSOC; 3 investigational treatment hypotheses surfaced
- **PAT002** (PAT002-BC-2026) — ER+/HER2− breast cancer; cross-cancer architecture validation
- **PAT003** (PAT003-CVD-2026) — Preventive cardiovascular health, 67F post-menopausal; 3 evidence gaps identified (Lp(a), APOE, CAC score) missed by standard lipid panel and Helix Tier 1 genetic screen

## Repository Structure

```
precision-medicine-mcp/
├── servers/                    # MCP servers (Python, FastMCP) — see server-registry.md for tool counts
│   ├── mcp-fgbio/             # Genomic reference data
│   ├── mcp-multiomics/        # RNA/Protein/Phospho integration
│   ├── mcp-spatialtools/      # Spatial transcriptomics
│   ├── mcp-epic/              # Epic FHIR integration (local-only)
│   ├── mcp-mockepic/          # Synthetic EHR for demos
│   ├── mcp-perturbation/      # Perturbation prediction
│   ├── mcp-quantum-celltype-fidelity/  # Quantum cell type fidelity
│   ├── mcp-openimagedata/     # Histology image processing
│   ├── mcp-deepcell/          # Cell segmentation
│   ├── mcp-cell-classify/     # Cell phenotype classification
│   ├── mcp-mocktcga/          # Mock TCGA cohort comparison
│   ├── mcp-patient-report/    # PDF report generation
│   ├── mcp-genomic-results/   # Somatic variant/CNV parsing
│   ├── mcp-geodownload/       # GEO/SRA dataset download
│   ├── mcp-opentargets/       # Open Targets drug-target associations
│   ├── mcp-cibersortx/        # CIBERSORTx immune deconvolution
│   ├── mcp-neoantigen/        # Neoantigen prediction & HLA binding
│   ├── mcp-cardiometabolic/   # CVD risk scoring & preventive health
│   ├── mcp-deidentify/        # Stage 0: HIPAA Safe Harbor de-identification (JSON, DOCX, PDF, VCF, h5ad)
│   └── mcp-server-boilerplate/# Template for new servers
├── data/                       # Patient data and reference files
│   ├── patient-data/PAT001-OVC-2025/  # Synthetic PatientOne data (HGSOC)
│   ├── pat002/                        # Synthetic PAT002 data (ER+ breast cancer)
│   ├── pat003/                        # Synthetic PAT003 data (preventive CVD)
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

## Pydantic / FastMCP Conventions

When fixing bugs in Pydantic models, always use `field_validator` or `model_validator` on the model class—never place coercion/guard logic inside function bodies. Validate fixes by calling `.run()` (not `.fn()`) so Pydantic validation is actually exercised.

## Cross-Server Fix Strategy

When applying a fix pattern (e.g., DRY_RUN guard, coercion logic) across multiple servers, first confirm the correct placement on ONE server with a passing test, then replicate that exact pattern to all other servers. Do not improvise per-server variations.

## Post-Change Verification

After any multi-file refactor or file-move operation, verify all relative paths and internal links still resolve correctly before committing. Run `grep -r` for old paths to catch stale references.

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
