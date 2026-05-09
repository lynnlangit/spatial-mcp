# Appendix A — Reproducibility Details

## Computational Environment

| Component | Version |
|-----------|---------|
| Python | >= 3.11 (uv-managed per server) |
| FastMCP | 2.x (upgraded April 17, 2026) |
| anndata | >= 0.10 (nullable strings fix April 17, 2026) |
| cell-gears | 0.1.2 |
| Claude Sonnet | 4.6 (orchestration) |
| Platform | macOS (local MCP servers via Claude Desktop) |

## Validation Timestamps

| Run | Date | Patients | Mode | Result |
|-----|------|----------|------|--------|
| Initial PAT001 validation | March 9, 2026 | PAT001 | SYNTHETIC_DATA | Pass |
| PAT001/PAT002 re-validation | April 17, 2026 | PAT001, PAT002 | No dry_run | Pass (0 errors, 104 tools) |
| PAT003 cardiometabolic | April 23, 2026 | PAT003 | No dry_run | Pass |
| PAT002 deep-stage (Stage 3+4) | May 8, 2026 | PAT002 | SYNTHETIC_DATA | Pass (quantum + neoantigen) |

## Synthetic Data Fixture Files

All synthetic fixture files are SHA-256 hashed and archived in the repository
at `data/patient-data/`. Hashes are recorded in `docs/for-researchers/paper-v17/MANIFEST.sha256`.

To regenerate fixture files from scratch:
```
python data/patient-data/PAT001-OVC-2025/generate_PAT001_missing_files.py
python data/patient-data/PAT002-BC-2026/generate_PAT002_missing_files.py
```

## Re-run Guidance

1. Clone: `git clone https://github.com/lynnlangit/precision-medicine-mcp`
2. Install servers: `uv run --directory servers/<server-name> python -m mcp_<server>`
3. Configure Claude Desktop: copy `config/claude_desktop_config.example.json`
   to `~/Library/Application Support/Claude/claude_desktop_config.json`
4. Set env vars per `docs/reference/ENV_VAR_REFERENCE.md`
5. Paste test prompts from `docs/reference/testing/` into Claude Desktop

Archived API response snapshots (April 17 + April 23, 2026 runs) are included
in `data/archived-responses/` for offline reproducibility verification.
