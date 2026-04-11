# Phase 8b-8c — GCP Cloud Run Deployment Status

**Started:** 2026-04-11
**Completed:** 2026-04-11
**Project:** `precision-medicine-poc` / `us-central1`
**Mode:** development (public access, DRY_RUN=true for new servers)

---

## Pre-deployment

| Step | Description | Status |
|------|-------------|--------|
| 0a | Add 5 missing servers to deploy_to_gcp.sh | done (b3c1a26) |
| 0b | Commit deploy script update | done (b3c1a26) |
| 0c | Create this status document | done |
| 0d | Fix Dockerfiles: add shared/common staging | done (56d1e5a) |
| 0e | Fix quantum .dockerignore README.md exclusion | done (ba29145) |

---

## Batch 1 — Regression-fix servers (code changes)

| # | Server | Deploy | Health | Notes |
|---|--------|--------|--------|-------|
| 1 | mcp-multiomics | done | 200 | BeforeValidator coercion |
| 2 | mcp-spatialtools | done | 200 | distance_threshold + Moran's I |
| 3 | mcp-perturbation | done | 200 | DRY_RUN path |
| 4 | mcp-quantum-celltype-fidelity | done | 200 | dry_run + training offload; .dockerignore fix |
| 5 | mcp-genomic-results | done | 200 | effect allowlist |
| 6 | mcp-neoantigen | done | 200 | BeforeValidator + input-aware mock |

## Batch 2 — Version-only servers (pyproject.toml bump)

| # | Server | Deploy | Health | Notes |
|---|--------|--------|--------|-------|
| 7 | mcp-fgbio | done | 200 | |
| 8 | mcp-mockepic | done | 200 | |
| 9 | mcp-mocktcga | done | 200 | |
| 10 | mcp-openimagedata | done | 200 | |
| 11 | mcp-deepcell | done | 200 | |
| 12 | mcp-patient-report | done | 200 | |

## Batch 3 — Not-yet-deployed servers

| # | Server | Deploy | Health | Notes |
|---|--------|--------|--------|-------|
| 13 | mcp-cell-classify | done | 200 | First deploy with nested layout |
| 14 | mcp-geodownload | done | 200 | First Cloud Run deploy |
| 15 | mcp-opentargets | done | 200 | First Cloud Run deploy |
| 16 | mcp-cibersortx | done | 200 | First Cloud Run deploy |

## Batch 4 — Client applications

| # | App | Deploy | Health | Notes |
|---|-----|--------|--------|-------|
| 17 | streamlit-app | done | 403 (auth required) | Keys extracted from existing service |
| 18 | streamlit-app-students | done | 200 | Public access |
| 19 | dashboard | done | 200 | Public access |
| 20 | jupyter-notebook | done | 302 (redirect to lab) | Public access |

---

## Final Verification

| Check | Status |
|-------|--------|
| gcloud run services list shows 20+ services | done — 21 services |
| All MCP server health checks pass (SSE 200) | done — 16/16 |
| deployment_urls.txt populated | done — 21 URLs |
| Streamlit app accessible (via proxy) | done — 403 (authenticated) |
| Student app loads | done — 200 |
| Dashboard loads | done — 200 |
| progress.md updated | done |

## Issues Encountered & Fixed

1. **shared/common not staged** — All Dockerfiles only copied `shared/utils/` but not
   `shared/common/` (needed for `from common.dry_run` and `from common.transport`).
   Fixed by adding `COPY _shared_temp/common/` to all 16 Dockerfiles and updating
   the deploy script to stage `shared/common/`.

2. **mcp-quantum .dockerignore** — Had `*.md` glob that excluded `README.md` which
   hatchling needs during `pip install -e .`. Removed the glob.

3. **mcp-deepcell / mcp-cell-classify flat layout** — These used `COPY . /app` instead
   of the nested `COPY . /app/servers/mcp-<name>/` layout, breaking `parents[4]` path
   resolution. Switched to nested layout.

4. **Cold start timeouts** — Three larger servers (spatialtools, perturbation, quantum)
   need >10s cold start. All respond 200 with 30s timeout.
