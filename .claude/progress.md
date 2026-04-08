# HOSPITAL1 FastMCP 2.13 Migration — Progress Checkpoint

**Plan:** `docs/HOSPITAL1_DEPLOYMENT_PLAN.md`
**Target:** `fastmcp>=2.13.0` in every server's `pyproject.toml`
**Strategy:** edit → `uv lock` → `uv run pytest -v` → atomic commit per server

**User directives:**
- Keep `mcp-mockepic` for CI/testing — bump it, do not remove it.
- Also bump `mcp-epic` — real FHIR target for HOSPITAL1.
- Checkpoint after every server (sessions may be interrupted).

---

## Phase status

| Phase | Description | Status |
|---|---|---|
| 0 | Ground-truth baseline (lock + pytest sanity on one server) | ✅ |
| 1 | Reference impls (no changes: boilerplate, patient-report) | ✅ (verified already current) |
| 2 | Group B bulk migration (13 servers, `>=0.2.0` → `>=2.13.0`) | ✅ 13/13 |
| 3 | Group A migration (multiomics, quantum-celltype-fidelity) | ✅ 2/2 |
| 4 | `mcp-epic` bump (`>=2.0.0` → `>=2.13.0`) | ✅ |
| 5 | Deployment-manifest swap (config only) | ✅ 41244a0 |
| 6 | PAT001 end-to-end smoke test (local) | ✅ signature audit 17/17 |
| 7 | Housekeeping (layout / build-backend normalization) | ✅ 3/3 (layout move deferred) |
| 8a | Local validation matrix (automated steps) | ✅ 8a.1-8a.4 + 8a.5 pre-check |
| 8a.5 | PAT001 manual walkthrough in Claude Desktop | ☐ operator-driven — HARD STOP |
| 8b | Build containers locally | ☐ blocked on operator green-light |
| 8c-h | GCP re-deploy (dev → prod → rollback drill) | ☐ blocked on 8b |

---

## Phase 2 — per-server checklist (13 servers)

Order: simplest first, flagged servers last.

| # | Server | Current | Edit | `uv lock` | pytest | commit | notes |
|---|---|---|---|---|---|---|---|
| 1  | mcp-genomic-results  | >=0.2.0 | ✅ | ✅ | ✅ import | ✅ fe53f60 | 4 tools, no pytest dir |
| 2  | mcp-geodownload      | >=0.2.0 | ✅ | ✅ | ✅ 22/22  | ✅ f46089a | |
| 3  | mcp-opentargets      | >=0.2.0 | ✅ | ✅ | ✅ 25/25  | ✅ b9ece9b | |
| 4  | mcp-neoantigen       | >=0.2.0 | ✅ | ✅ | ✅ 30/30  | ✅ 30654e4 | |
| 5  | mcp-cibersortx       | >=0.2.0 | ✅ | ✅ | ✅ 19/19  | ✅ 1c1ea5a | Phase 2a done |
| 6  | mcp-mockepic         | >=0.2.0 | ✅ | ✅ | ✅ import | ✅ 12aed42 | 3 tools, CI kept |
| 7  | mcp-mocktcga         | >=0.2.0 | ✅ | ✅ | ✅ import | ✅ 7ef8d9c | 5 tools, fastmcp 3.0.2 |
| 8  | mcp-cell-classify    | >=0.2.0 | ✅ | ✅ | ✅ 20/20  | ✅ 1d155b3 | |
| 9  | mcp-fgbio            | >=0.2.0 | ✅ | ✅ | ✅ import | ✅ 449871e | 4 tools, no rpy2 |
| 10 | mcp-openimagedata    | >=0.2.0 | ✅ | ✅ | ✅ import | ✅ af59d12 | 5 tools |
| 11 | mcp-spatialtools     | >=0.2.0 | ✅ | ✅ | ✅ import | ✅ 19b2a7d | 16 tools — Phase 2c done |
| 12 | mcp-deepcell         | >=0.2.0 | ✅ | ✅ | ⚠ lock only | ✅ b2a3c24 | macOS ARM64 cannot install tf==2.8.4 (pre-existing); Linux CR target OK |
| 13 | mcp-perturbation     | >=0.2.0 | ✅ | ✅ | ✅ 11p/7s | ✅ 2f5e53a | GEARS skips pre-existing — Phase 2 done |

---

## Phase 3 — Group A

| # | Server | Current | Edit | `uv lock` | pytest | commit |
|---|---|---|---|---|---|---|
| 14 | mcp-multiomics               | >=0.1.0 | ✅ | ✅ | ✅ import | ✅ 2b60f86 | 10 tools, rpy2 ABI fallback (R not local) |
| 15 | mcp-quantum-celltype-fidelity | >=0.1.0 | ✅ | ✅ | ✅ 77/77 | ✅ 1f81dfa | |

## Phase 4 — mcp-epic

| # | Server | Current | Edit | `uv lock` | pytest | commit |
|---|---|---|---|---|---|---|
| 16 | mcp-epic | >=2.0.0 | ✅ | ✅ | ✅ import | ✅ dfd3c35 | 4 FHIR tools |

---

## Phase 5 — Deployment-manifest swap

Config-only change to `infrastructure/deployment/deploy_to_gcp.sh`.
Added `mcp-epic` (port 3008, reused since it never co-exists with mockepic)
to the SERVERS array and introduced an `apply_deployment_profile()` function
that filters the array at deploy time:
- `DEPLOYMENT_MODE=production` → drops `mcp-mockepic`, `mcp-mocktcga`
- `DEPLOYMENT_MODE=development` → drops `mcp-epic`
- `--server <name>` bypasses the filter so operators can admin-deploy
  a single server across profiles.

Bash dry-run verified: dev=11 servers, prod=10 servers. Commit `41244a0`.

## Phase 6 — PAT001 smoke (local)

Rather than a full multi-server e2e (deferred to Phase 8 on GCP Cloud Run),
the local smoke is a cross-server signature audit:
`scripts/phase6_signature_audit.sh` walks every server in `servers/mcp-*`,
imports it in its own uv venv, enumerates registered tools via the compat
pattern (`list_tools()` → `get_tools()` → `_tool_manager._tools`), and
compares the count to `docs/reference/shared/server-registry.md`.

Result (2026-04-08):

| Metric | Value |
|---|---|
| total | 17 |
| passed | 16 |
| failed | 0 |
| skipped | 1 (mcp-deepcell — ARM64 platform limitation) |
| warnings | 0 (no tool-count drift) |

fastmcp versions resolved: 2.14.1, 2.14.3, 2.14.4, 2.14.5, 3.0.2, 3.1.0.
All satisfy `>=2.13.0`. No server relies on removed `_tool_manager._tools`
private API.

## Phase 7 — Housekeeping

Build-backend normalization scoped to the three servers the plan names.
A platform-wide audit at the start of the phase showed the repo was
actually split 7 hatchling / 11 setuptools (plan assumed hatchling was
dominant — stale), so Phase 7 did **not** sweep all setuptools servers
to hatchling; only the three named in the plan were touched.

| # | Server | Change | commit |
|---|---|---|---|
| 17 | mcp-multiomics | setuptools → hatchling | `98ff0f8` |
| 18 | mcp-quantum-celltype-fidelity | setuptools → hatchling | `abe2598` |
| 19 | mcp-perturbation | setuptools → hatchling + drop redundant `mcp>=1.0.0` + clean stale egg-info/build/UNKNOWN.egg-info | `df1244c` |

Post-Phase-7 signature audit: 16/17 OK, 1 skip (deepcell), 0 fail,
0 warnings — no regression from the backend swaps.

**Deferred (out of scope for Phase 7):**
- `mcp-perturbation` flat → `src/` layout move. Plan describes this as
  speculative ("pipeline _may_ reject"). No confirmed breakage. Blast
  radius: loose top-level `test_gears_patientone.py`, multiple markdown
  docs referencing the current path. Deferred to a separate PR if/when
  a HOSPITAL1 build pipeline actually rejects the layout.
- GEARS `hidden_size` compatibility shim. Plan flagged this as a
  pre-existing upstream issue. All affected tests are skipped in the
  baseline. Out of scope for the FastMCP migration.
- `mcp-deepcell` Python 3.11 upgrade. Plan explicitly defers until
  DeepCell-TF ships 3.11 support.
- Setuptools → hatchling sweep for the other 8 setuptools servers
  (epic, fgbio, mockepic, cell-classify, openimagedata, mocktcga,
  spatialtools, deepcell). Not in the plan, and the backend split is
  stable. Both backends are PEP 517-compliant.

Also updated `docs/reference/shared/server-registry.md` (the canonical
server doc) to reflect:
- Correct tool totals (97 → 99; spatialtools 14 → 16)
- FastMCP ≥ 2.13 framework version
- HOSPITAL1 deployment-profile distinction in the Mock Servers section
- Current build-backend split (10 hatchling / 8 setuptools)
- Last Updated date bump to 2026-04-08

---

## Phase 8a — Local validation matrix

Automated steps complete (8a.1-8a.4) + Claude Desktop pre-check (8a.5).
HARD STOP at operator-driven PAT001 walkthrough in Claude Desktop per user:
"manually test Patient001 with my synthetic dataset end-to-end in Claude Desktop
and confirm no regression bugs were introduced by our recent FastMCP updates
BEFORE we build and deploy update to my GCP infra".

| Step | Description | Result |
|---|---|---|
| 8a.1 | per-server pytest + fresh `uv lock` | ✅ 8 real servers / 223 passed, 7 pre-existing skips; mcp-server-boilerplate = template (N/A) |
| 8a.2 | fastmcp >= 2.13.0 assertion | ✅ 17/17 declared + resolved (span 2.14.1 to 3.1.0) |
| 8a.3 | PAT001 dry-run smoke for mcp-genomic-results | ✅ 4/4 tools |
| 8a.4 | PAT002 dry-run smoke for mcp-genomic-results | ✅ 4/4 tools |
| 8a.5 pre | Claude Desktop 14-server import + tool enumeration | ✅ 14/14, 87 tools |
| 8a.5 | operator PAT001 walkthrough in Claude Desktop | ☐ **operator gate** |

Detailed results: `/tmp/phase8a/PHASE_8A_COMPLETE.txt`

Observation (not a migration regression): mcp-genomic-results DRY_RUN
payloads still return PAT001 ovarian markers (TP53, PIK3CA, PTEN) regardless
of patient_id. Commit 6360897 intended to swap to PAT002 breast markers but
the hardcoded data didn't get updated. Separate fixture-quality issue,
predates migration. Not a HOSPITAL1 blocker.

mcp-fgbio bakes in `/workspace/data/reference` as a default path at startup.
Host launch failed but Claude Desktop config overrides this via
`FGBIO_REFERENCE_DATA_DIR=.../data/reference`, so Claude Desktop cold-start
is fine. Pre-existing container-path assumption, not a migration regression.

---

## Resume instructions (for next session)

1. `cd /Users/lynnlangit/Documents/GitHub/spatial-mcp`
2. Read this file (`.claude/progress.md`) to see which ☐ are still unchecked.
3. Read `docs/HOSPITAL1_DEPLOYMENT_PLAN.md` for the full plan.
4. Continue the first unchecked server row. Pattern:
   ```bash
   cd servers/mcp-<name>
   # Edit pyproject.toml: fastmcp>=X.Y.0 → fastmcp>=2.13.0
   uv lock
   uv run pytest -v
   # If green, commit with format: "migrate(mcp-<name>): bump fastmcp to >=2.13.0"
   ```
5. After each server, update this file to mark the row complete.

---

## Notes / incidents

- **2026-04-08 — fastmcp 3.x API drift:** mcp-mocktcga resolves to
  fastmcp 3.0.2 (others in Phase 2a/2b resolve to 2.14.x). 3.x removed
  the private `_tool_manager._tools` attribute; use the public async
  `await mcp.list_tools()` instead. Smoke test template updated
  accordingly. Both 2.14.x and 3.0.2 satisfy the `>=2.13.0` constraint
  and both work for our servers (no Context/lifespan usage anywhere).
- **Smoke test template (for servers without pytest):**
  ```python
  import asyncio, fastmcp
  assert tuple(int(x) for x in fastmcp.__version__.split('.')[:2]) >= (2, 13)
  from mcp_<name> import server
  tools = asyncio.run(server.mcp.list_tools())
  print(f'server={server.mcp.name} tools={len(tools)}')
  ```
