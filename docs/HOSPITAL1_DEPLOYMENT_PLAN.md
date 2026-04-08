# HOSPITAL1 FastMCP 2.x Migration Plan

**Date:** 2026-04-08
**Target version:** `fastmcp>=2.13.0`
**Repo:** `spatial-mcp` (precision-medicine-mcp)
**Scope:** 18 MCP servers under `servers/mcp-*/`
**Author:** Migration audit performed by Claude Code

---

## Summary

The audit found that **every server already resolves to FastMCP 2.14.x or 3.x
in its `uv.lock`**, even though many `pyproject.toml` files declare loose lower
bounds of `>=0.1.0` or `>=0.2.0`. No server uses a deprecated FastMCP 0.x API
pattern in its source code. This means the headline migration is overwhelmingly
a **lower-bound constraint tightening**, not a code rewrite.

- **Total servers:** 18
- **Already current (no changes of any kind):** 2 — `mcp-server-boilerplate`, `mcp-patient-report`
- **Requires `pyproject.toml` bump only (no code changes):** 16 — 13 Group B + 2 Group A + `mcp-epic`
- **Requires code changes for FastMCP itself:** 0
- **Requires adjacent fixes alongside the FastMCP bump:** 3 — `mcp-deepcell` (Python pin), `mcp-perturbation` (GEARS upstream + layout), `mcp-epic` (FHIR sandbox validation)
- **Requires architectural swap for HOSPITAL1:** 2 — `mcp-mockepic` → `mcp-epic`; `mcp-mocktcga` → cBioPortal / HOSPITAL1 data lake

### Why the migration is lower-risk than the raw version table suggests

1. **All 17 non-boilerplate servers import FastMCP the modern way:**
   `from fastmcp import FastMCP` — nobody is still using
   `from mcp.server.fastmcp import FastMCP` (the known 0.x pattern fixed in
   `mcp-perturbation` per its `DEPLOYMENT_SUCCESS.md`). A full-tree grep for
   `from mcp.server` / `mcp.server.fastmcp` returned **zero matches**.
2. **No server uses `lifespan=`, `on_startup`, `on_shutdown`, or the FastMCP
   `Context` parameter.** Grep hits for "Context", "lifespan", "progress", and
   "stream" resolved to project-local names (e.g. `SpatialContextGenerator`,
   disease progression fields, `httpx.AsyncClient().stream()`,
   `subprocess.run()`), not FastMCP framework features.
3. **All transport-aware `mcp.run(...)` calls already use the FastMCP 2.x
   keyword API:** `mcp.run(transport=..., port=..., host="0.0.0.0")`. Confirmed
   in `mcp-quantum-celltype-fidelity`, `mcp-perturbation`, `mcp-patient-report`,
   and the shared `shared/common/transport.py` helper used by `mcp-multiomics`.
4. **`@mcp.tool()`, `@mcp.resource(uri)`, and `@mcp.custom_route(...)`
   decorator signatures used in the codebase are all supported in 2.13+.**
5. **`uv.lock` already resolved every server to 2.14.1–3.1.0.** The constraint
   bump will not force any fresh resolution; it simply aligns the declared
   floor with what the platform is already running.

The dependency audit report's "three FastMCP generations" finding is **true at
the `pyproject.toml` level** but **stale at the actual-installed level**. The
danger is not that the code won't work — it's that a future clean install on
a machine that respects the declared lower bound (e.g., a locked-down HOSPITAL1
build system that rejects lockfile drift) could silently pull FastMCP 0.1.0.

---

## Per-Server Migration Table

| Server | pyproject constraint | uv.lock resolved | Decorators / API used | Action | Complexity | Notes |
|---|---|---|---|---|---|---|
| mcp-server-boilerplate | `fastmcp>=2.13.0` | n/a | `@mcp.tool()`, `mcp.run()` | **None** | ✅ reference impl | Use as the canonical template |
| mcp-patient-report | `fastmcp>=2.13.0` | 2.14.5 | `@mcp.tool()`, `@mcp.custom_route()`, `mcp.run(transport=...)` | **None** | ✅ done | Verifies `@mcp.custom_route` works under 2.13+ |
| mcp-epic | `fastmcp>=2.0.0` | 2.14.1 | `@mcp.tool()`, bare `mcp.run()` | Bump to `>=2.13.0` | 🟢 trivial | Also has raw `mcp>=1.1.2` dep — leave as-is, it's a transitive need |
| mcp-fgbio | `fastmcp>=0.2.0` | 2.14.1 | `@mcp.tool()`, `@mcp.resource("reference://*")` | Bump to `>=2.13.0` | 🟢 trivial | Uses `subprocess.run` + `httpx.stream` — project code, unaffected |
| mcp-spatialtools | `fastmcp>=0.2.0` | 2.14.1 | `@mcp.tool()` × 16, `@mcp.resource("data://*")` | Bump to `>=2.13.0` | 🟢 trivial | Largest tool surface; no FastMCP-internal APIs touched |
| mcp-mockepic | `fastmcp>=0.2.0` | 2.14.1 | `@mcp.tool()`, `@mcp.resource("ehr://*")` | Bump + **deprecate for HOSPITAL1** | 🟢 trivial | Architectural swap: see §Architectural Swap |
| mcp-mocktcga | `fastmcp>=0.2.0` | 3.0.2 | `@mcp.tool()`, `@mcp.resource("tcga://*")` | Bump + **evaluate replacement** | 🟢 trivial | cBioPortal community MCP already in registry as replacement |
| mcp-geodownload | `fastmcp>=0.2.0` | 3.1.0 | `@mcp.tool()` × 6 | Bump to `>=2.13.0` | 🟢 trivial | — |
| mcp-genomic-results | `fastmcp>=0.2.0` | 2.14.5 | `@mcp.tool()` × 4 | Bump to `>=2.13.0` | 🟢 trivial | — |
| mcp-cibersortx | `fastmcp>=0.2.0` | 3.1.0 | `@mcp.tool()` × 5 | Bump to `>=2.13.0` | 🟢 trivial | — |
| mcp-opentargets | `fastmcp>=0.2.0` | 3.1.0 | `@mcp.tool()` × 6 | Bump to `>=2.13.0` | 🟢 trivial | — |
| mcp-neoantigen | `fastmcp>=0.2.0` | 3.1.0 | `@mcp.tool()` × 6 | Bump to `>=2.13.0` | 🟢 trivial | — |
| mcp-cell-classify | `fastmcp>=0.2.0` | 2.14.5 | `@mcp.tool()` × 3 | Bump to `>=2.13.0` | 🟢 trivial | — |
| mcp-openimagedata | `fastmcp>=0.2.0` | 2.14.1 | `@mcp.tool()` × 5, `@mcp.resource("image://*")` | Bump to `>=2.13.0` | 🟢 trivial | — |
| mcp-deepcell | `fastmcp>=0.2.0` | 2.14.1 | `@mcp.tool()`, `@mcp.resource("model://*")` | Bump + **Python pin fix** | 🟡 medium | `requires-python = ">=3.10,<3.11"` is a HOSPITAL1 landmine (see §Hidden Risks) |
| mcp-perturbation | `fastmcp>=0.2.0` | 2.14.3 | `@mcp.tool()` × 8, `mcp.run(transport=...)` | Bump + **GEARS upstream fix** + layout review | 🟡 medium | Non-`src/` layout, upstream GEARS `hidden_size` kwarg removed |
| mcp-multiomics | `fastmcp>=0.1.0` | 2.14.1 | `@mcp.tool()` × 10, `@mcp.resource("multiomics://*")`, shared `run_server()` | Bump to `>=2.13.0` | 🟢 trivial | Largest dep surface (pandas/scipy/statsmodels/rpy2) but no FastMCP-specific coupling |
| mcp-quantum-celltype-fidelity | `fastmcp>=0.1.0` | 2.14.4 | `@mcp.tool()` × 6, `mcp.run(transport=...)` | Bump to `>=2.13.0` | 🟢 trivial | Has optional `aer` / `gpu` extras; qiskit is independent of FastMCP |

**Group A → target in practice:** both servers already use the 2.x-style keyword
`mcp.run(transport=...)` signature and the modern import path. The `>=0.1.0`
declaration is cosmetic drift; the code has been written for 2.x since the
repository became active.

**Group B → target in practice:** identical story. Every server imports
`from fastmcp import FastMCP` and uses only `@mcp.tool()` / `@mcp.resource()`
decorators with no Context, no lifespan, no prompt decorator.

---

## Breaking-Change Matrix (evaluated against this codebase)

| FastMCP 0.x pattern | Status in this repo | Action |
|---|---|---|
| `from mcp.server.fastmcp import FastMCP` | **Not present** — full-tree grep: 0 matches | None |
| `from fastmcp import FastMCP` | Used by all 17 servers | Already 2.x-compatible |
| `@mcp.tool()` decorator | Used everywhere | Unchanged in 2.x |
| `@mcp.resource("scheme://path")` | Used in 8 servers | Unchanged in 2.x |
| `@mcp.prompt()` | **Not present** — 0 matches | N/A |
| `@mcp.custom_route()` | Used only in `mcp-patient-report` | 2.x-only; confirms target version works |
| `lifespan=` on `FastMCP(...)` | **Not present** — 0 matches | N/A |
| `on_startup` / `on_shutdown` hooks | **Not present** — 0 matches | N/A |
| `Context` (FastMCP dependency-injected) | **Not present** — 0 matches in tool signatures | N/A |
| `mcp.run()` bare | Used by `mcp-epic`, `mcp-server-boilerplate` | 2.x-compatible (stdio default) |
| `mcp.run(port=...)` (old 0.1.0 bug) | **Not present** | Fixed long ago (see `mcp-perturbation/DEPLOYMENT_SUCCESS.md`) |
| `mcp.run(transport=..., port=..., host=...)` | Used in quantum / perturbation / patient-report / `shared/common/transport.py` | Already 2.x keyword API |
| Streaming responses / progress reporting | **Not present** | N/A |

**Conclusion:** the migration is a `pyproject.toml` lower-bound tightening
exercise plus `uv lock --upgrade-package fastmcp` per server. No `.py` file
needs to change for FastMCP itself.

---

## High-Risk Items

### 1. `mcp-deepcell` — Python version pin (NOT a FastMCP issue, but a HOSPITAL1 blocker)

**File:** `servers/mcp-deepcell/pyproject.toml:6`
```
requires-python = ">=3.10,<3.11"
```

This upper-bounds Python to 3.10.x because of DeepCell-TF's TensorFlow
dependency chain. The platform CLAUDE.md says "Python 3.11+ required." If
HOSPITAL1's base image is 3.11 (or 3.12), **every other server will install
and this one will refuse to**. This is independent of the FastMCP bump but
will surface during the same containerization pass.

**Options:**
- **(A) Keep the pin, ship `mcp-deepcell` on its own 3.10 runtime** — containers
  isolate the Python version, so this is viable. Document the exception in the
  HOSPITAL1 deployment runbook.
- **(B) Upgrade DeepCell-TF** to a version compatible with Python 3.11 (check
  upstream changelog — as of 2025 the `DeepCell>=0.13` line added 3.11 support).
- **(C) Swap `DeepCell-TF` for `deepcell-imaging` or an ONNX export** — larger
  change, out of scope for this migration.

**Recommendation:** (A) for the initial HOSPITAL1 deployment, (B) as a
follow-up once the rest of the platform is stabilized.

### 2. `mcp-perturbation` — GEARS upstream `hidden_size` kwarg removal

**Files affected:**
- `servers/mcp-perturbation/mcp_perturbation/server.py:57` —
  `hidden_size: int = Field(default=64, ge=32, le=256)` on the Pydantic model
- `servers/mcp-perturbation/mcp_perturbation/server.py:201` —
  `hidden_size=params.hidden_size` passed to `GEARSWrapper.train(...)`
- `servers/mcp-perturbation/mcp_perturbation/gears_wrapper.py:131,152` —
  `hidden_size` forwarded into `GEARS(..., hidden_size=...)`
- `servers/mcp-perturbation/test_gears_patientone.py:175` — test passes
  `hidden_size=32` to `GEARS()`

**Upstream state:** the prompt reports that `cell-gears` (GEARS) removed the
`hidden_size` kwarg from `GEARS.__init__()`. A DRY_RUN call will not exercise
this, but any production `train_gears_model` call inside HOSPITAL1 will fail
with `TypeError: GEARS.__init__() got an unexpected keyword argument 'hidden_size'`.

**Claimed workaround:** the prompt references `mcp_perturbation_fix.py` in the
repo root. **This file does not exist in the current tree.** A `glob` for
`mcp_perturbation_fix.py` returned zero matches. Either the fix was never
committed, or it lives under a different name.

**Required follow-up (not FastMCP work but adjacent):**
1. Locate or write the GEARS compatibility shim inside
   `mcp_perturbation/gears_wrapper.py`: detect whether the installed GEARS
   accepts `hidden_size`, and either forward it or set it via attribute
   after construction / via its config object.
2. Pin `cell-gears` to a known-working version in `pyproject.toml`.
3. Add a non-DRY_RUN integration test that exercises `train_gears_model`.

### 3. `mcp-perturbation` — non-`src/` layout and `setuptools` backend

The server lives at `servers/mcp-perturbation/mcp_perturbation/server.py` (no
`src/`), uses a `setuptools` build backend, and depends on both `mcp>=1.0.0`
and `fastmcp>=0.2.0`. The rest of the platform standardizes on `hatchling` +
`src/mcp_<name>/` layout.

**This does not block the FastMCP bump**, but HOSPITAL1's build pipeline may
reject the inconsistency. Recommend a follow-up housekeeping PR after the
migration to:
- move source into `src/mcp_perturbation/`
- switch to hatchling (or align with whatever the target image expects)
- drop the redundant `mcp>=1.0.0` declaration unless still needed transitively

### 4. `mcp-multiomics` — large dependency surface (not FastMCP-related)

The largest dep graph on the platform: `pandas`, `scipy`, `scikit-learn`,
`statsmodels`, `matplotlib`, `seaborn`, `plotly`, `rpy2`, `fsspec`, `gcsfs`.
None of these couple to FastMCP internals. The FastMCP bump is trivial; the
residual risk is that HOSPITAL1's base image constrains one of the scientific
packages (particularly `rpy2`, which needs an R installation, and is already
gated with `; platform_system != 'Windows'`).

**Recommendation:** unchanged — the `RPY2_CFFI_MODE=ABI` environment trick in
`servers/mcp-multiomics/Dockerfile:24` already handles the "no R at build time"
case. Carry the same flag into the HOSPITAL1 image.

### 5. `mcp-quantum-celltype-fidelity` — numpy 2.x pin

`servers/mcp-quantum-celltype-fidelity/pyproject.toml:18`:
```
"numpy>=1.24.0,<2.0",
```

Again independent of FastMCP, but worth knowing: qiskit 1.x is not yet
universally numpy-2-compatible, so this server will hold the platform on
numpy 1.x unless containerized separately. It already has optional `aer`
and `gpu` extras and uses `mcp.run(transport=..., port=..., host=...)` — the
2.x API. FastMCP bump itself is one-line.

### 6. `mcp-epic` — FHIR sandbox validation (separate workstream)

`mcp-epic` is on `fastmcp>=2.0.0` (not `>=2.13.0`), so it gets the same bump
treatment as Group A/B. The real HOSPITAL1 risk for this server is not
FastMCP — it's that its `mcp.run()` is bare (stdio only), it has no streaming
transport path, and its FHIR client code has never been exercised against a
real Epic FHIR endpoint inside the HOSPITAL1 perimeter. The bump is trivial;
**the validation burden is the bottleneck**.

---

## Architectural Swap for HOSPITAL1

HOSPITAL1 has a de-identified clinical data lake (~15.1M patients) and a real
Epic deployment, which changes what the platform needs to expose:

| Current (dev / demo) | HOSPITAL1 target | Notes |
|---|---|---|
| `mcp-mockepic` | `mcp-epic` | Real FHIR R4; already on `>=2.0.0`. Becomes `>=2.13.0` after this migration. The mock server stays in the repo for CI and student Streamlit UIs but is **disabled in HOSPITAL1 deployment manifests**. |
| `mcp-mocktcga` | External `cBioPortal` community MCP server (already documented in the server registry as the "real data" replacement) **+** optional in-house wrapper over HOSPITAL1 data lake | The registry at `docs/reference/shared/server-registry.md:76` already lists cBioPortal as the replacement. The in-house wrapper is a new server, out of scope for this migration. |
| ClinicalTrials.gov (Anthropic connector) | Unchanged | Already external HTTP MCP; nothing to migrate. |
| `bioRxiv / medRxiv`, `PubMed`, `Seqera`, `Hugging Face` (external) | Unchanged | Not in this repo. |

**What the migration owns vs. what it does not:**
- **Owns:** bumping every `fastmcp>=0.x` / `>=2.0.0` to `>=2.13.0` and
  regenerating lock files.
- **Owns:** wiring `mcp-epic` into HOSPITAL1 deployment manifests in place of
  `mcp-mockepic` (config change, not code change).
- **Does NOT own:** building the HOSPITAL1 data-lake wrapper server.
- **Does NOT own:** FHIR sandbox credentials / certificates (HOSPITAL1 IT task).
- **Does NOT own:** the cBioPortal server itself (community, self-hosted).

---

## Recommended Build Order

1. **Phase 0 — Ground truth check (pre-flight).**
   - Run `uv lock` in each server and confirm the resolved fastmcp version is
     ≥ 2.13.0. This audit shows all 17 already are (2.14.1–3.1.0), but re-run
     on the HOSPITAL1 build host to catch any environment-specific resolver
     difference.
   - Run each server's existing `uv run pytest -v` under DRY_RUN mode and
     confirm the baseline is green before touching `pyproject.toml`.

2. **Phase 1 — Reference implementations (no changes, used for comparison).**
   - `mcp-server-boilerplate` — template
   - `mcp-patient-report` — proves `@mcp.custom_route` + transport-keyword
     `mcp.run()` under 2.13+
   - Use these as the copy-paste source of truth when editing other servers.

3. **Phase 2 — Group B bulk migration (13 servers, lowest risk).**
   Order by dependency weight ascending so early failures surface in simple
   servers first:
   1. `mcp-genomic-results`
   2. `mcp-geodownload`
   3. `mcp-opentargets`
   4. `mcp-neoantigen`
   5. `mcp-cibersortx`
   6. `mcp-mockepic` (still bump it; deprecation happens at deployment-config level)
   7. `mcp-mocktcga` (ditto)
   8. `mcp-cell-classify`
   9. `mcp-fgbio`
   10. `mcp-openimagedata`
   11. `mcp-spatialtools`
   12. `mcp-deepcell` (**also fix or document the Python pin here**)
   13. `mcp-perturbation` (**also land GEARS `hidden_size` shim here**)

   For each: edit `pyproject.toml`, run `uv lock`, run `uv run pytest -v`,
   commit atomically.

4. **Phase 3 — Group A migration (2 servers).**
   1. `mcp-multiomics` — bump; run full test suite (largest test surface)
   2. `mcp-quantum-celltype-fidelity` — bump; run full test suite including
      the spatial context + circuit execution paths

5. **Phase 4 — `mcp-epic` bump (`>=2.0.0` → `>=2.13.0`).**
   Trivial edit, but gate this behind a live smoke test against HOSPITAL1's
   Epic FHIR sandbox (not just the unit tests). Without that, `mcp-epic` is
   still "unproven in HOSPITAL1" even if FastMCP is current.

6. **Phase 5 — Deployment-manifest swap.**
   In the HOSPITAL1 deployment config (not repo code): disable `mcp-mockepic`,
   enable `mcp-epic`; disable `mcp-mocktcga`, enable cBioPortal external MCP.

7. **Phase 6 — End-to-end PAT001 smoke test.**
   Run the PatientOne workflow against the newly-built images and confirm it
   still produces the three investigational findings documented in the paper
   and in the committed example reports (`60e1218 PAT002 report example`,
   `4b86a17 PAT001 example report`). No prompt or tool signature should have
   changed, so the expected output should be byte-stable modulo timestamps.

8. **Phase 7 — Follow-up housekeeping (not migration-critical).**
   - Normalize `mcp-perturbation` to `src/` + hatchling layout.
   - Normalize `mcp-multiomics` and `mcp-quantum-celltype-fidelity` from
     `setuptools` to `hatchling` to match the rest of the platform.
   - Re-evaluate `mcp-deepcell` Python upgrade when DeepCell-TF ships 3.11.

9. **Phase 8 — Local validation, then intermediate GCP re-deployment.**
   This is a **hard gate before HOSPITAL1**. Phases 2–4 each run their own
   server-local pytest pass, but Phase 8 is the first time the whole platform
   is exercised together post-migration, and the first time the upgraded
   containers touch GCP. The goal is to catch any regression in a safe,
   disposable environment before HOSPITAL1 sees it.

   ### 8a. Local validation matrix (run on a clean checkout)

   Run these in order — each step must pass before the next.

   1. **Per-server unit tests, every server, fresh lock.**
      ```bash
      for s in servers/mcp-*/; do
        ( cd "$s" && uv lock && uv run pytest -v ) || { echo "FAIL: $s"; break; }
      done
      ```
      Every server must land green under DRY_RUN. This is the same loop as
      the existing verification script, plus the `uv lock` refresh.

   2. **FastMCP version assertion across all servers.**
      Re-run the verification script at the bottom of this document and
      confirm every server prints `fastmcp >= 2.13 OK`. No warnings about
      resolver drift.

   3. **PAT001 dry-run end-to-end through the Streamlit UI.**
      ```bash
      cd ui/streamlit-app && uv run streamlit run app.py
      ```
      Walk the PatientOne workflow to completion and diff the generated
      patient report against the committed example (`4b86a17 PAT001 example
      report`). The report text should be byte-stable modulo timestamps and
      UUIDs. Any narrative drift is a regression — **stop and investigate
      before continuing**.

   4. **PAT002 dry-run end-to-end.** Same as above against the
      `60e1218 PAT002 report example` committed report. Both patients must
      pass locally before spending money on GCP.

   5. **Cross-server smoke test.** Start every server in a local
      multi-process launch (or the existing test harness) and confirm the
      orchestration path (Claude → multiple MCP servers → report) completes
      without transport errors. The shared `shared/common/transport.py`
      helper will log the DRY_RUN banner on each startup — confirm all 17
      banners appear.

   **Exit criterion for 8a:** all five steps green, and `git diff --stat` on
   the generated example reports shows only timestamp/UUID churn.

   ### 8b. Build containers locally (staged base images first)

   The platform uses layered Docker base images under
   `infrastructure/docker/base-images/` (`python-base`, `r-base`,
   `tensorflow-base`). Build the bases first so per-server rebuilds are
   fast and the FastMCP upgrade actually gets pulled:

   1. Rebuild base images (only those affected by the Python/scientific
      stack — the FastMCP bump alone does not invalidate them, but a clean
      rebuild removes any stale wheel cache that might shadow the new
      constraint):
      ```bash
      cd infrastructure/docker/base-images
      # Build each base image per the README in this directory
      ```

   2. Rebuild every per-server image locally:
      ```bash
      for s in servers/mcp-*/; do
        name=$(basename "$s")
        [ -f "$s/Dockerfile" ] || continue
        docker build -t "local/$name:hospital1-rc" "$s" || { echo "FAIL: $name"; break; }
      done
      ```
      16 servers have Dockerfiles (per the audit); `mcp-server-boilerplate`
      and `mcp-epic` do not — skip them here.

   3. **Sanity check: inside each built image, import fastmcp and assert
      the version.**
      ```bash
      for s in servers/mcp-*/; do
        name=$(basename "$s")
        [ -f "$s/Dockerfile" ] || continue
        docker run --rm "local/$name:hospital1-rc" \
          python -c "import fastmcp; v=fastmcp.__version__; \
            assert tuple(int(x) for x in v.split('.')[:2]) >= (2,13), v; \
            print(f'{name}: fastmcp {v} OK')"
      done
      ```

   4. **Run one server container in SSE mode locally** and hit its MCP
      endpoint with a simple JSON-RPC `tools/list` probe to confirm the
      transport layer starts without regressions. `mcp-fgbio` on port 3000
      is the lightest smoke-test target.

   **Exit criterion for 8b:** every built image reports `fastmcp >= 2.13`
   and at least one server responds to a live MCP probe.

   ### 8c. Push to GCP Artifact Registry + Cloud Run — development mode

   Use the existing deploy script in **development mode first** (public
   access, no VPC, no secrets — exactly what it was built for as an
   intermediate test environment):

   ```bash
   cd infrastructure/deployment
   # Confirm the target project is the intermediate one, NOT a prod project
   echo "Target project: ${GCP_PROJECT_ID:-precision-medicine-poc}"
   echo "Target region:  ${GCP_REGION:-us-central1}"

   # Deploy all servers in development mode
   ./deploy_to_gcp.sh --development
   ```

   The script already understands the per-server port / memory / CPU /
   env-var matrix (see `deploy_to_gcp.sh:77–…`) and will update
   `infrastructure/deployment/deployment_urls.txt` with the Cloud Run URLs
   on success. That file currently contains only a stub
   (`mcp-fgbio=`, empty value) — after this phase it should be populated
   for every deployed server.

   **Do not run `--production` mode in this phase.** Production mode on
   this GCP project is the dress rehearsal for HOSPITAL1 (VPC, secrets,
   authenticated) and belongs in 8e, after the development-mode smoke
   test passes.

   **Single-server retry pattern** (if any one server fails deployment):
   ```bash
   ./deploy_to_gcp.sh --development --server mcp-<name>
   ```

   ### 8d. Cloud Run smoke test — development mode

   1. **URL liveness.** For every URL written to `deployment_urls.txt`,
      confirm the Cloud Run service is `READY`:
      ```bash
      gcloud run services list \
        --project "${GCP_PROJECT_ID:-precision-medicine-poc}" \
        --region "${GCP_REGION:-us-central1}" \
        --filter="metadata.name ~ ^mcp-" \
        --format="table(metadata.name, status.conditions[0].type, status.conditions[0].status, status.url)"
      ```
      Every row must show `Ready / True`.

   2. **FastMCP version assertion inside each live container.**
      Cloud Run images are immutable — if the build step pulled the right
      fastmcp, the running container has it. But verify with a per-service
      probe via `gcloud run services proxy` or by hitting the SSE
      transport directly and reading the server's initialization message.

   3. **Startup logs.** For each service, confirm the `DRY_RUN MODE` banner
      from `shared/common/transport.py` either appears (if DRY_RUN is still
      on) or does not appear (if the deploy script set
      `*_DRY_RUN=false` per the SERVERS array — it does). Mismatches
      indicate an env-var plumbing regression.
      ```bash
      gcloud run services logs read mcp-multiomics \
        --project "${GCP_PROJECT_ID:-precision-medicine-poc}" \
        --region "${GCP_REGION:-us-central1}" --limit 50
      ```

   4. **End-to-end PAT001 against the Cloud Run URLs.** Point the
      Streamlit app (or the orchestrator) at the Cloud Run SSE endpoints
      instead of local processes, and run the full PatientOne workflow.
      The generated report must match the committed example within the
      same byte-stability tolerance as step 8a.3.

   5. **Cost sanity check.** Look at Cloud Run billing after the smoke
      test and confirm idle scale-to-zero is working. Any service that
      didn't scale down within ~15 minutes of the smoke test is a
      misconfiguration (likely `min-instances > 0`) and should be fixed
      before HOSPITAL1 inherits the same pattern.

   **Exit criterion for 8d:** all 16 Cloud Run services `Ready/True`, one
   full PAT001 workflow green against the live URLs, and the billing
   dashboard shows the services scaled to zero after the test window.

   ### 8e. Intermediate GCP re-deployment — production mode (HOSPITAL1 dress rehearsal)

   Only after 8d is fully green, re-deploy the same images into the **same
   GCP project** in production mode. This exercises the VPC connector,
   Secret Manager, authenticated invocation, and audit logging code paths
   that HOSPITAL1 will use for real:

   ```bash
   # From the same deployment directory
   ./deploy_to_gcp.sh --production
   ```

   This uses the supporting scripts under `infrastructure/hospital-deployment/`:
   - `setup-project.sh` — GCP project initialization (idempotent)
   - `setup-vpc.sh` — VPC + serverless connector (`mcp-connector`)
   - `setup-secrets.sh` — Secret Manager bindings
   - `setup-audit-logging.sh` — HIPAA-style audit log sinks
   - `deploy-oauth2-proxy.sh` — Azure AD SSO proxy (swap for HOSPITAL1 IdP later)
   - `verify-fhir-data.sh` — Epic FHIR connectivity check (uses the
     intermediate project's sandbox credentials, **not HOSPITAL1's**)

   **Do not use HOSPITAL1 credentials, endpoints, or data in this phase.**
   The intermediate GCP project must have its own sandbox secrets so that
   if anything leaks, it leaks in a disposable environment.

   ### 8f. Validation in production mode

   1. Re-run steps 8d.1–8d.5 against the authenticated URLs (you will
      need an identity token on every probe:
      `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" ...`).
   2. **VPC egress check.** Confirm each service's outbound traffic goes
      through the VPC connector by inspecting
      `gcloud run services describe <name> --format='value(spec.template.metadata.annotations)'`
      for `run.googleapis.com/vpc-access-connector` and
      `run.googleapis.com/vpc-access-egress=all-traffic`.
   3. **Secret Manager wiring.** Confirm each service that needs secrets
      (e.g., `mcp-epic`, `mcp-cibersortx` token) has the secret mounted as
      an env var, not baked into the image.
   4. **Audit log presence.** Confirm `setup-audit-logging.sh` created the
      log sink and that the smoke-test invocations show up in it. This is
      the HIPAA control HOSPITAL1 cares about most.
   5. **Full PAT001 workflow under authenticated SSE.** If this passes
      end-to-end in production mode, the platform is HOSPITAL1-ready from
      an application perspective. Any HOSPITAL1-specific failures from
      this point forward are infrastructure or credential issues, not
      migration issues.

   **Exit criterion for 8e/8f:** the same workflow that passed in 8d
   passes again with VPC + auth + secrets + audit logging enabled, and
   the audit log contains one clean trail of the PAT001 run.

   ### 8g. Rollback posture

   Because Cloud Run keeps previous revisions, rollback is one command per
   service:
   ```bash
   gcloud run services update-traffic mcp-<name> \
     --project "${GCP_PROJECT_ID:-precision-medicine-poc}" \
     --region "${GCP_REGION:-us-central1}" \
     --to-revisions=<previous-revision>=100
   ```
   Record the pre-migration revision IDs **before** pushing the new
   images, so rollback is trivial if 8d or 8f uncovers a regression.
   For local iteration, the old FastMCP constraint is in git history —
   `git revert` the Phase 2/3/4 commits individually if a specific server
   needs to go back.

   ### 8h. Promotion gate to HOSPITAL1

   The platform promotes to an actual HOSPITAL1 install only when:
   1. 8a through 8f are all green on the intermediate GCP project.
   2. `deployment_urls.txt` is populated for every server that should be
      deployed (i.e., not `mcp-mockepic` and not `mcp-mocktcga`).
   3. The audit log from 8f.4 has been reviewed and archived.
   4. A rollback drill has been performed at least once on a
      non-critical server (e.g., `mcp-fgbio`) to prove the procedure works.
   5. HOSPITAL1 IT has provided the real Epic FHIR sandbox credentials and
      the HOSPITAL1-side VPC / project layout is ready to receive the
      images. The same `deploy_to_gcp.sh --production` call retargets to
      the HOSPITAL1 project via `GCP_PROJECT_ID` / `GCP_REGION`.

---

## Verification Script (success criteria)

After migration, this should pass for every server:

```bash
for server in servers/mcp-*/; do
  echo "--- $server ---"
  ( cd "$server" && uv run python -c \
    "import fastmcp; v=fastmcp.__version__; \
     assert tuple(int(x) for x in v.split('.')[:2]) >= (2,13), v; \
     print(f'fastmcp {v} OK')" )
done
```

And the PAT001 end-to-end smoke test should reproduce the committed example
reports. The platform is ready for HOSPITAL1 deployment when **all** of the
following hold:

1. All 18 servers resolve `fastmcp>=2.13.0` in their lock files **and declare
   it in their `pyproject.toml`**. (Today: 2 of 18 declare it; 17 of 17
   non-boilerplate already resolve to ≥ 2.14.1.)
2. The PAT001 dry-run produces the same three investigational findings as
   documented in the paper and the committed example reports (verified
   locally in Phase 8a).
3. The same workflow reproduces against live Cloud Run URLs on the
   intermediate GCP project in **development mode** (Phase 8d) and again in
   **production mode** with VPC, Secret Manager, authenticated invocation,
   and audit logging enabled (Phase 8e/8f).
4. `infrastructure/deployment/deployment_urls.txt` is populated for every
   server that should be deployed (not `mcp-mockepic`, not `mcp-mocktcga`).
5. A rollback drill has been performed at least once on a non-critical
   Cloud Run service (Phase 8g) and the procedure works end-to-end.
6. `mcp-epic` passes a live smoke test against HOSPITAL1's Epic FHIR sandbox
   (not just mock data, not just the intermediate GCP project's sandbox).
7. `mcp-perturbation`'s `train_gears_model` tool executes successfully against
   a real GEARS model with the hidden-size parameter properly handled.
8. `mcp-deepcell` either runs under Python 3.11 **or** is containerized on
   Python 3.10 with an explicit exemption noted in the HOSPITAL1 runbook.

---

## HOSPITAL1-Specific Infrastructure Notes

- **Python runtime:** 3.11+ required everywhere except `mcp-deepcell`
  (3.10.x) unless that server is upgraded. Use `uv` as package manager per
  CLAUDE.md; do not introduce `pip install -r requirements.txt` style
  workflows.
- **Containers:** every server has its own `Dockerfile` (16 present;
  `mcp-server-boilerplate` and `mcp-epic` intentionally do not — `mcp-epic`
  is documented as local-only in the server registry). None of the
  Dockerfiles pin FastMCP directly — they use `pip install -e .` against
  `pyproject.toml`, so bumping the constraint is sufficient; a clean `docker
  build` will pull the new version automatically.
- **Transport in the HOSPITAL1 cluster:** standard pattern in this repo is
  `MCP_TRANSPORT=sse` with `MCP_PORT` or `PORT` env var. The shared
  `shared/common/transport.py` helper (used by `mcp-multiomics`) and the
  per-server `main()` functions in `mcp-quantum-celltype-fidelity`,
  `mcp-perturbation`, and `mcp-patient-report` all honor this. Keep it.
- **HIPAA posture:** synthetic data only in the repo (PAT001, PAT002);
  real HOSPITAL1 data is accessed at runtime through the FHIR / data-lake
  MCP layer. This migration does not change that boundary.
- **Authentication:** `mcp-epic` needs HOSPITAL1 Epic FHIR sandbox
  credentials (`EPIC_FHIR_ENDPOINT`, `EPIC_CLIENT_ID`, `EPIC_CLIENT_SECRET`).
  The server logs a `NOT CONFIGURED` warning on startup if these are absent
  (`servers/mcp-epic/src/mcp_epic/server.py:226`), so misconfiguration is
  at least visible.
- **Source of truth for tool counts post-migration:**
  `docs/reference/shared/server-registry.md`. The registry currently reports
  17 custom servers / 97 tools + 6 external / 46 tools. This migration does
  not change the tool count; if it appears to, something regressed.

---

## Appendix A — Caveats about this plan

1. **The prompt referenced `mcp_perturbation_fix.py` in the repo root; that
   file does not currently exist** (`glob mcp_perturbation_fix.py` → 0
   results). Before Phase 2 item 13, confirm whether the GEARS shim lives
   under another name (e.g., inside `gears_wrapper.py` under a feature flag),
   or whether it still needs to be written from scratch.
2. **The prompt listed `mcp-perturbation` in Group B (`>=0.2.0`).** Confirmed:
   `pyproject.toml:8` declares `fastmcp>=0.2.0` and `uv.lock` resolves to
   2.14.3. The server code itself already uses the 2.x `mcp.run(transport=...)`
   API, so the FastMCP half is a one-line change.
3. **The audit expected `mcp-spatialtools` might use streaming / progress
   APIs.** It does not — all 16 `@mcp.tool()` methods are plain async
   functions returning dicts.
4. **No `Context` parameter is used anywhere in the codebase.** If a future
   FastMCP release renames or removes the `Context` type, this repo is
   unaffected.
5. **FastMCP 3.x has already silently landed in 4 servers** (`mcp-cibersortx`,
   `mcp-geodownload`, `mcp-opentargets`, `mcp-neoantigen`, `mcp-mocktcga` →
   3.0.2/3.1.0). They are running fine against the same `@mcp.tool()` surface.
   This suggests the 2.13 target is conservative — the platform could in
   practice adopt `fastmcp>=3.0.0`, but the prompt pins 2.13 and there is no
   business reason to go further for this migration.
