# Documentation Cleanup Plan

**Canonical sources:** Paper v16 (`HGSOC_Platform_Paper_v16.pdf`) + actual `server.py` code
**Date:** 2026-04-11

---

## Audit Summary

| Source | Server Count | Tool Count |
|--------|-------------|------------|
| Paper v16 | 18 servers | "38 tool calls across 13 servers" |
| server-registry.md | 17 custom + 6 external | 99 custom tools |
| Actual code audit | 17 custom (16 real + 1 boilerplate) | 99 tools confirmed |

### Cross-Reference: Paper Table 2.2 vs Actual Servers

| Paper Name | Actual Name | In Paper Table? | Stage | Issues |
|-----------|-------------|-----------------|-------|--------|
| mcp-mockepic | mcp-mockepic | Yes | 1 | None |
| mcp-fgbio | mcp-fgbio | Yes | 1 | None |
| mcp-mocktcga | mcp-mocktcga | Yes (implied) | 1 | None |
| mcp-geodownload | mcp-geodownload | Yes | 1 | None |
| mcp-genomic-results | mcp-genomic-results | Yes | 1 | None |
| mcp-spatialtools | mcp-spatialtools | Yes | 2 | README says 14 tools, code has 16 |
| mcp-cibersortx | mcp-cibersortx | Yes | 2 | None |
| mcp-opentargets | mcp-opentargets | Yes | 3 | None |
| mcp-multiomics | mcp-multiomics | Yes | 3 | None |
| mcp-perturbation | mcp-perturbation | Yes | 4 | **README severely outdated** |
| mcp-quantum | mcp-quantum-celltype-fidelity | Yes | 4 | Paper uses short name |
| mcp-cell-classify | mcp-cell-classify | Yes (implied) | 4 | None |
| mcp-neoantigen | mcp-neoantigen | Yes | 4 | None |
| mcp-openimagedata | mcp-openimagedata | Yes (implied) | 4 | None |
| mcp-patient-report | mcp-patient-report | Yes | 5 | None |
| mcp-clinicaltrials | External (Anthropic connector) | Yes | 5 | Not a custom server |
| mcp-epic | mcp-epic | Not in table | — | No README |
| mcp-deepcell | mcp-deepcell | Not in table | — | None |

---

## Server-by-Server Cleanup Tasks

### Priority 1: Major Rewrite Needed

#### 1. mcp-perturbation README.md
**Status:** Severely outdated — pre-dates all 10 GEARS pipeline fixes
**File:** `servers/mcp-perturbation/README.md`

| Section | Problem | Fix |
|---------|---------|-----|
| Quick Start §2 (setup_model) | `num_layers: 2, uncertainty: true` | Change to `num_layers: 1, uncertainty: false` (actual defaults) |
| Quick Start §2 (train_model) | Lists `batch_size: 32` | Remove — GEARS.train() doesn't accept batch_size |
| Tool Reference §2 (setup_model) | `num_layers` default 2, `uncertainty` default true | Fix to 1 and false |
| Tool Reference §3 (train_model) | Lists `batch_size` and `valid_every` params | Remove both — not supported by GEARS |
| Conditions section | Says `"control"` / `"tumor"` | Change to GEARS format: `"ctrl"` / `"GENE+ctrl"` |
| Example Workflow Step 2 | `n_epochs: 100` param name | Change to `epochs: 20` |
| Example Workflow Step 3 | `control_key: "control", treatment_key: "tumor"` | Change to perturbation gene list format |
| Performance table | `n_latent` column | Remove — GEARS uses `hidden_size` |
| Troubleshooting | Mentions `n_latent`, `batch_size` | Fix to use GEARS terminology |
| Scientific Background | Lists scVI as related | Remove — server uses GEARS, not scVI |
| Installation | `pip install -e ".[dev]"` | Change to `uv` |

**Action:** Full rewrite of Quick Start, Tool Reference §§2-3, Example Workflow, Performance, and Troubleshooting sections.

---

### Priority 2: Tool Count Mismatch

#### 2. mcp-spatialtools README.md
**Status:** Documents 14 tools, code has 16
**File:** `servers/mcp-spatialtools/README.md`

| Issue | Fix |
|-------|-----|
| Missing tool: `resolve_patient_data_paths` | Add tool documentation section |
| Missing tool: `set_patient_context` | Add tool documentation section |
| Architecture section lists 10 tools | Update to 16 |

**Action:** Add 2 new tool sections + update tool count references.

#### 3. server-registry.md
**Status:** Says spatialtools has 16 tools (correct for code), but README says 14
**File:** `docs/reference/shared/server-registry.md`

| Issue | Fix |
|-------|-----|
| Total tool count "99 tools" | Verify after spatialtools README update |
| Last Updated: 2026-04-08 | Update date |

**Action:** Verify all tool counts after individual README fixes; update date.

---

### Priority 3: Missing Documentation

#### 4. mcp-epic README.md
**Status:** No README exists
**File:** `servers/mcp-epic/README.md` (create)

| Content needed |
|---------------|
| 4 tools: get_patient_demographics, get_patient_conditions, get_patient_observations, get_patient_medications |
| FHIR R4 API integration description |
| Local-only deployment note (hospital FHIR secrets required) |
| Env vars: EPIC_BASE_URL, EPIC_CLIENT_ID, etc. |

**Action:** Create minimal README (tool list, description, env vars, local-only note).

---

### Priority 4: Minor Fixes

#### 5. mcp-fgbio README.md
**File:** `servers/mcp-fgbio/README.md`
- Verify 4 tools match code ✓
- No known issues

#### 6. mcp-multiomics README.md
**File:** `servers/mcp-multiomics/README.md`
- Verify 10 tools match code ✓
- No known issues

#### 7. mcp-quantum-celltype-fidelity README.md
**File:** `servers/mcp-quantum-celltype-fidelity/README.md`
- Verify 6 tools match code ✓
- Check if training cap notes (n_qubits<=4, negative_samples=1) are documented

#### 8. mcp-deepcell README.md
**File:** `servers/mcp-deepcell/README.md`
- Verify 3 tools match code ✓
- No known issues

#### 9. mcp-cell-classify README.md
**File:** `servers/mcp-cell-classify/README.md`
- Verify 3 tools match code ✓
- No known issues

#### 10. mcp-openimagedata README.md
**File:** `servers/mcp-openimagedata/README.md`
- Verify 5 tools match code ✓
- No known issues

#### 11. mcp-patient-report README.md
**File:** `servers/mcp-patient-report/README.md`
- Verify 5 tools match code ✓
- No known issues

#### 12. mcp-genomic-results README.md
**File:** `servers/mcp-genomic-results/README.md`
- Verify 4 tools match code ✓
- No known issues

#### 13. mcp-geodownload README.md
**File:** `servers/mcp-geodownload/README.md`
- Verify 6 tools match code ✓
- No known issues

#### 14. mcp-opentargets README.md
**File:** `servers/mcp-opentargets/README.md`
- Verify 6 tools match code ✓
- No known issues

#### 15. mcp-cibersortx README.md
**File:** `servers/mcp-cibersortx/README.md`
- Verify 5 tools match code ✓
- No known issues

#### 16. mcp-neoantigen README.md
**File:** `servers/mcp-neoantigen/README.md`
- Verify 6 tools match code ✓
- No known issues

#### 17. mcp-mockepic README.md (if exists)
- Verify 3 tools match code ✓

#### 18. mcp-mocktcga README.md
**File:** `servers/mcp-mocktcga/README.md`
- Verify 5 tools match code ✓
- No known issues

---

### Priority 5: Cross-Cutting Fixes

#### 19. CLAUDE.md
**File:** `CLAUDE.md`
- Update server list if tool counts changed
- Verify `uv run` instructions are consistent

#### 20. All READMEs: Installation section
- Ensure all say `uv` (not `pip install -e .`)
- Ensure all reference FastMCP >= 2.13.0

---

## Execution Order

1. **mcp-perturbation README** — biggest delta, most user-visible
2. **mcp-spatialtools README** — add 2 missing tools
3. **mcp-epic README** — create from scratch
4. **server-registry.md** — final counts + date
5. **Quick scan** of remaining 14 READMEs (Priority 4) — fix any `pip` → `uv` references
6. **CLAUDE.md** — update if any counts changed

**Estimated edits:** ~3 files major, ~2 files minor, ~14 files verify-only
