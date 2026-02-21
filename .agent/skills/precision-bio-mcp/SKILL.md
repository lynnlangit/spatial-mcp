---
name: precision-bio-mcp
description: >
  Expert guide for building and maintaining Precision Medicine MCP servers.
  Ensures consistency across bioinformatics tools, data handling, and deployment.
---

# Precision Bio-MCP Server Builder

This skill codifies the architectural patterns used in the Precision Medicine MCP project.

## 🔄 Technical vs. Collaboration Guide

Use this table to choose the right skill for your task:

| Feature | **@precision-bio-mcp** | **@universal-collaboration** |
| :--- | :--- | :--- |
| **Primary Focus** | Technical server implementation. | Team workflow and PR hygiene. |
| **When to Use** | Creating/Refactoring MCP servers. | Onboarding, PRs, ADRs, Scaffolding. |
| **Server Pattern** | Defines *how* things work (`uv`, SDK). | Defines *where* things go (Paths/Naming). |
| **Compliance** | Technical data validation logic. | Workflow triggers (Checks & Notes). |
| **Testing** | Specific `pytest` setups and bio-mocking. | General coverage and scenario patterns. |

---

## 🏗️ Server Structure

This skill implements the **Scaffolding New MCP Servers** pattern defined in **@universal-collaboration**. Every new server MUST follow this standard structure:

```text
servers/mcp-[name]/
├── pyproject.toml      # Managed by uv
├── uv.lock
├── Dockerfile          # Multi-stage build
├── deploy.sh           # Cloud Run deployment script
├── README.md           # Documentation with examples
└── src/
    └── mcp_[name]/
        ├── __init__.py
        ├── server.py   # Main MCP entry point
        └── [logic].py  # Domain-specific bioinformatics logic
```

## 🛠️ Core Patterns

### 1. Dependency Management (`uv`)
- Always use `uv` for package management.
- Initialize with `uv init --lib`.
- Standard dependencies: `mcp`, `pydantic`, `python-dotenv`.
- Bio dependencies: `scanpy`, `anndata`, `cell-gears` (if relevant).

### 2. Shared Utilities
- **Configuration**: Use `shared/common/config.py`.
- **Logging**: Use `shared/common/logging.py`.
- **Validation**: Use `shared/common/validation.py` for patient data checks.

### 3. Server Implementation
- Use the MCP Python SDK.
- Tools should be descriptive: `perturbation_predict`, `cell_classify`.
- Always include `n_top_genes` or similar limits for bio-data to prevent memory issues.

## 🚀 Deployment

- Use the standardized `Dockerfile` template from `servers/mcp-server-boilerplate`.
- Use `deploy.sh` to target Google Cloud Run.
- Default resources: 2 CPU, 4Gi Memory for bioinformatics workloads.

## 🧪 Testing

- Place tests in the project-root `tests/` or local `servers/mcp-[name]/tests/`.
- Use `pytest` for unit and integration tests.
- Mock external biological databases (GEO, TCGA) during CI.

---

**Use this skill when:**
- Creating a new MCP server.
- Refactoring an existing bioinformatics tool.
- Debugging deployment or shared utility issues.
