# Educator Quick-Start

Get the platform running in your classroom in under 10 minutes.

---

## Prerequisites

| Requirement | Minimum version | Notes |
|-------------|-----------------|-------|
| Python | 3.11 | 3.12 also tested |
| uv | 0.4+ | `pip install uv` |
| Claude Desktop | Latest | API key required |
| RAM | 16 GB | 8 GB minimum for DRY_RUN only |

---

## Three-command setup

```bash
git clone https://github.com/lynnlangit/precision-medicine-mcp
cd precision-medicine-mcp
uv sync && python3 -m pytest tests/ -x --tb=short
```

---

## First demo in 10 minutes

1. Open Claude Desktop and confirm the 19 MCP servers are connected.
2. Open `docs/for-educators/PAT001_walkthrough.ipynb` in JupyterLab or VS Code.
3. Run all cells. All assertions should pass using DRY_RUN synthetic data.
4. Compare output values to the table in README.md under "Validated results (PAT001)."

---

## Common classroom problems

| Symptom | Cause | Fix |
|---------|-------|-----|
| IC50 returns 999999 for multi-peptide input | Bytecode cache stale after code update | `uv sync --reinstall` then fully restart Claude Desktop (not just the server) |
| Quantum server raises RuntimeError about GPU | CUDA not available on the machine | Set `backend="cpu"` explicitly in the tool call |
| GEARS perturbation times out | n_hvg set too high | Reduce to `n_hvg=1000` in the synthetic dataset config |
| Notebook assertions fail | Canonical fixture not on Python path | Run `uv sync` from repo root, then re-open notebook kernel |
| "anndata nullable strings" error | anndata version mismatch | Add `anndata.settings.allow_write_nullable_strings = True` at module top |
