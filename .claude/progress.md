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
| 3 | Group A migration (multiomics, quantum-celltype-fidelity) | 🟡 in progress |
| 4 | `mcp-epic` bump (`>=2.0.0` → `>=2.13.0`) | ☐ |
| 5 | Deployment-manifest swap (config only) | ☐ |
| 6 | PAT001 end-to-end smoke test (local) | ☐ |
| 7 | Housekeeping (layout / build-backend normalization) | ☐ |
| 8 | Local validation + intermediate GCP re-deploy | ☐ |

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
| 14 | mcp-multiomics               | >=0.1.0 | ☐ | ☐ | ☐ | ☐ |
| 15 | mcp-quantum-celltype-fidelity | >=0.1.0 | ☐ | ☐ | ☐ | ☐ |

## Phase 4 — mcp-epic

| # | Server | Current | Edit | `uv lock` | pytest | commit |
|---|---|---|---|---|---|---|
| 16 | mcp-epic | >=2.0.0 | ☐ | ☐ | ☐ | ☐ |

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
