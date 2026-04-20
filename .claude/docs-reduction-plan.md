# Documentation Reduction & Re-Focus Plan

**Goal:** Shorten, de-duplicate, and re-focus all docs (excluding `docs/book/`) on the
paper's compelling narrative: *our platform surfaces clinically actionable findings that
standard workup cannot reach.*

**Canonical sources:** Paper v16 + actual server Python code
**Out of scope:** `docs/book/` (no changes)

---

## Current State

| Metric | Count |
|--------|-------|
| Total .md files in `docs/` (excl. book) | ~113 |
| Total .md files in `docs/book/` (excluded) | ~17 |
| `for-operations/` files (SLA templates) | 32 |
| `for-hospitals/` files | 15 |
| `for-funders/` files | 8 |
| Lines in longest single file (ETHICS_AND_BIAS.md) | 2,003 |

---

## The Paper's Core Narrative (What Docs Should Reinforce)

The paper tells a 3-act story:

**Act 1 — The Problem:** Standard HGSOC workup (BRCA1/2, HRD, CT) generates no
immunotherapy hypotheses. Manual multi-modal analysis takes 40 hours and $6,000-9,000.

**Act 2 — The Platform:** 18-server MCP architecture executes 5 stages automatically:
Data Acquisition → Spatial Deconvolution → Target Profiling → Causal Inference → Report.

**Act 3 — The Findings:** Three treatment hypotheses unreachable by standard workup:
1. Personalized neoantigen vaccine (TP53 R175H → RMPEAAPPV, IC50 7.8 nM)
2. NNMT/CAF inhibition (18.2% CAF fraction → immune recovery)
3. Convergent checkpoint blockade (POLE-corrected TMB 47.3 + spatial CD8 exclusion)

Plus: cross-cancer validation on PAT002 with zero code changes.

**Every doc should either advance this narrative, or be a concise reference that
supports someone trying to reproduce or extend it.**

---

## Five Redundancy Clusters to Eliminate

### Cluster 1: "Value Proposition" repeated 6 times

These files all say "40 hours → 35 min, $6K → $324, 5 data modalities":

| File | Lines | Action |
|------|-------|--------|
| `reference/shared/value-proposition.md` | 56 | **KEEP as single source of truth** |
| `for-funders/EXECUTIVE_SUMMARY.md` | 249 | Shorten to 1-page; link to value-proposition.md |
| `for-funders/FUNDING.md` | 136 | Shorten to 1-page; link to value-proposition.md |
| `for-funders/GRANT_TALKING_POINTS.md` | 331 | Shorten; link to value-proposition.md + patientone-profile.md |
| `for-funders/NINETY_SECOND_PITCH.md` | 214 | Shorten; link to value-proposition.md |
| Root `README.md` (value section) | — | Link to value-proposition.md instead of inlining |

**Rule:** `value-proposition.md` is canonical. Every other doc links to it with a one-line summary.

### Cluster 2: PatientOne profile repeated 4 times

| File | Lines | Action |
|------|-------|--------|
| `reference/shared/patientone-profile.md` | 72 | **KEEP as single source of truth** |
| `for-funders/FULL_PATIENTONE_DEMO.md` | 249 | Shorten to demo script only; link to patientone-profile.md for clinical details |
| `for-funders/GRANT_TALKING_POINTS.md` (prelim data) | — | Link to patientone-profile.md |
| `reference/testing/patient-one/README.md` | 150+ | Link to patientone-profile.md for clinical details |

**Rule:** `patientone-profile.md` is canonical. Demo scripts and test guides link to it.

### Cluster 3: HIPAA/Compliance repeated 4+ times

| File | Lines | Action |
|------|-------|--------|
| `reference/shared/hipaa-summary.md` | 61 | **KEEP as single source of truth** |
| `for-hospitals/compliance/hipaa.md` | 591 | Shorten to hospital-specific procedures; link to hipaa-summary.md for baseline |
| `for-hospitals/SECURITY_OVERVIEW.md` | 264 | Shorten; link to hipaa-summary.md |
| `for-operations/04_COMPLIANCE_REGULATORY.md` | ? | Link to hipaa-summary.md |
| `for-operations/05_DATA_PROTECTION.md` | ? | Link to hipaa-summary.md |

### Cluster 4: Architecture described in 5+ places

| File | Lines | Action |
|------|-------|--------|
| `for-developers/ARCHITECTURE.md` | 100+ | **KEEP as canonical architecture doc** |
| `reference/architecture/README.md` | 361 | Merge unique content into ARCHITECTURE.md; make this a redirect |
| `reference/architecture/platform/workflow.md` | 36 | Fold into ARCHITECTURE.md |
| Modality-specific arch docs (6 files in architecture/) | ~2,000 | See Phase 3 below |

### Cluster 5: Navigation pages duplicated

| File | Lines | Action |
|------|-------|--------|
| `docs/README.md` | 39 | **DELETE** — redundant with INDEX.md |
| `docs/INDEX.md` | 240 | **KEEP as sole navigation page** |
| `getting-started/README.md` | 41 | Fold into `getting-started/installation.md` as opening section |

---

## Phase-by-Phase Execution Plan

### Phase 1: Delete / Archive Aspirational Bulk (~32 files → archive)

**Rationale:** `for-operations/` contains 32 SLA template files for a hospital deployment
that doesn't exist. These are speculative operational docs (incident runbooks, DR failover,
PHI breach response, contract termination, etc.) that don't advance the paper's narrative
and aren't grounded in actual code.

**Action:** Move `docs/for-operations/` to `docs/_archive/for-operations/`. Add a
one-line README explaining these are templates for future hospital deployment.

**Similarly archive these aspirational hospital docs:**
- `for-hospitals/RUNBOOKS/` (3 runbook files) → archive
- `for-hospitals/citl-workflows/` → archive
- `for-hospitals/operations/cost-and-budget.md` → archive (duplicate of shared/cost-analysis.md)

**Estimated reduction:** ~35 files moved to archive, ~4,500 lines removed from active docs.

### Phase 2: Consolidate Funders Directory (8 files → 3 files)

Current `for-funders/` has 8 files with massive overlap. Consolidate to:

| Keep | Source | Action |
|------|--------|--------|
| `README.md` | Existing | Shorten to index of the 2 remaining docs |
| `EXECUTIVE_SUMMARY.md` | Existing | Cut to ~100 lines; fold in FUNDING.md's investment tiers; link to value-proposition.md and patientone-profile.md |
| `DEMO_AND_PITCH.md` | Merge of NINETY_SECOND_PITCH + FULL_PATIENTONE_DEMO | Combine into one demo script doc |

**Delete/merge away:**
- `FUNDING.md` → fold unique content (investment tiers) into EXECUTIVE_SUMMARY.md
- `GRANT_TALKING_POINTS.md` → fold unique content (specific aims template) into EXECUTIVE_SUMMARY.md
- `NINETY_SECOND_PITCH.md` → merge into DEMO_AND_PITCH.md
- `FULL_PATIENTONE_DEMO.md` → merge into DEMO_AND_PITCH.md
- `COMPETITIVE_LANDSCAPE.md` → archive (market analysis, not platform narrative)
- `ROI_ANALYSIS.md` → archive (financial modeling, not platform narrative)

**Estimated reduction:** 8 → 3 files, ~1,400 lines → ~300 lines.

### Phase 3: Flatten Architecture Docs (15+ files → 5 files)

The `reference/architecture/` tree has 15+ files across 6 subdirectories. Most repeat
content from server READMEs. Consolidate to:

| Keep | Covers | Source |
|------|--------|--------|
| `for-developers/ARCHITECTURE.md` | System overview, 5-stage pipeline, data flow | Merge in reference/architecture/README.md + platform/workflow.md |
| `reference/architecture/WHY_MCP_FOR_HEALTHCARE.md` | Business case for MCP | Keep as-is (unique) |
| `reference/architecture/clinical/ehr-integration.md` | Epic FHIR architecture | Keep (links to server READMEs) |
| `reference/architecture/spatial/OVERVIEW.md` | Spatial pipeline overview | Keep (links to server README) |
| `reference/architecture/imaging/README.md` | Imaging pipeline overview | Keep |

**Delete (content lives in server READMEs):**
- `clinical/clinical-spatial-bridge.md` → content is in spatialtools README
- `dna/genomic-results.md` → content is in genomic-results README
- `dna/genomic-cohorts.md` → content is in mocktcga README
- `rna/perturbation.md` → content is in perturbation README (just updated)
- `rna/quantum-fidelity.md` → content is in quantum-celltype-fidelity README
- `rna/multiomics.md` → content is in multiomics README
- `spatial/SERVERS.md` → 77-line link page, unnecessary
- `spatial/CSV_WORKFLOW.md`, `spatial/FASTQ_WORKFLOW.md`, `spatial/DEPLOYMENT.md`, `spatial/GLOSSARY.md` → fold into spatial/OVERVIEW.md or delete
- `platform/error-handling.md`, `platform/observability.md`, `platform/ai-ml.md` → fold into ARCHITECTURE.md or delete
- `imaging/GLOSSARY.md`, `imaging/HE_WORKFLOW.md`, `imaging/MXIF_WORKFLOW.md` → fold into imaging/README.md

**Estimated reduction:** 15+ → 5 files, ~4,000 lines → ~1,000 lines.

### Phase 4: Trim Hospital Docs (15 files → 6 files)

Keep the grounded, useful hospital docs. Archive the rest.

| Keep | Lines | Why |
|------|-------|-----|
| `README.md` | 278 → ~100 | Shorten; links to remaining docs |
| `DEPLOYMENT_CHECKLIST.md` | 260 → ~150 | Practical; trim aspirational milestones |
| `USER_GUIDE.md` | 838 → ~300 | Useful for clinicians; trim verbose sections |
| `SECURITY_OVERVIEW.md` | 264 → ~100 | Keep as concise security summary; link to hipaa-summary.md |
| `compliance/README.md` | keep | Index only |
| `compliance/hipaa.md` | 591 → ~200 | Shorten; link to shared/hipaa-summary.md for baseline |

**Archive:**
- `OPERATIONS_MANUAL.md` (1,004 lines) — aspirational
- `compliance/data-governance.md` — aspirational
- `compliance/risk-assessment.md` — completed work log, not reference doc
- `compliance/disclaimers.md` — can live in a single NOTICES section
- `ethics/` directory (3 files, ~2,500 lines) — aspirational framework
- `RUNBOOKS/` (3 files) — already moved in Phase 1
- `citl-workflows/` — already moved in Phase 1
- `operations/` — already moved in Phase 1

**Estimated reduction:** 15 → 6 files, ~5,500 lines → ~850 lines.

### Phase 5: Clean Remaining Small Files

| File | Action |
|------|--------|
| `docs/README.md` | Delete (INDEX.md is the nav page) |
| `docs/email-summary.md` | Archive (dated snapshot) |
| `docs/HOSPITAL1_DEPLOYMENT_PLAN.md` | Archive (completed migration log) |
| `getting-started/README.md` | Fold into installation.md |
| `for-developers/benchmark-findings-2026-02-19.md` | Archive (dated benchmark) |
| `for-developers/token-benchmark-cache-optimization.md` | Archive (dated benchmark) |
| `for-developers/SEQERA_OFFICIAL_MCP.md` | Archive or fold into CONNECT_EXTERNAL_MCP.md |
| `for-developers/automation-guides/` (5 files) | Keep (practical, grounded) |
| `reference/architecture/next-steps.md` | Archive (speculative roadmap) |
| `reference/references.md` | Keep (bibliography) |

### Phase 6: Re-Focus Root README.md

Rewrite the root `README.md` around the paper's 3-act narrative:

1. **The Problem** (2-3 sentences): Standard HGSOC workup misses immunotherapy hypotheses
2. **The Platform** (table): 18 servers, 5 stages, link to server-registry.md
3. **The Results** (bullet list): 3 findings not reachable by standard workup
4. **Try It** (3 commands): Quick start with DRY_RUN mode
5. **Learn More** (links): Paper, getting-started, for-developers, for-researchers

Current README is 149 lines of generic "what is this" text. Target: 80 lines focused on
the compelling story.

---

## Estimated Impact

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Active .md files in docs/ (excl. book) | ~113 | ~45 | **60%** |
| Approximate total lines (excl. book) | ~18,000 | ~5,000 | **72%** |
| for-operations/ files | 32 | 0 (archived) | **100%** |
| for-funders/ files | 8 | 3 | **62%** |
| architecture/ files | 15+ | 5 | **67%** |
| for-hospitals/ files | 15 | 6 | **60%** |

---

## Execution Order

1. **Phase 1** (archive aspirational bulk) — biggest win, lowest risk
2. **Phase 5** (clean small files) — quick wins
3. **Phase 2** (consolidate funders) — moderate effort
4. **Phase 3** (flatten architecture) — needs careful content review
5. **Phase 4** (trim hospital docs) — moderate effort
6. **Phase 6** (re-focus root README) — final polish

---

## Questions for User

Before executing, I'd like to confirm:

1. **Archive vs Delete?** Plan uses `docs/_archive/` to preserve content. Should I
   instead delete outright? (Git history preserves everything regardless.)

2. **for-operations/ (32 SLA files):** These are extensive but 100% aspirational.
   Archive the entire directory, or keep the README as a placeholder?

3. **COMPETITIVE_LANDSCAPE.md and ROI_ANALYSIS.md:** These are business docs, not
   platform narrative. Archive, or keep in for-funders/?

4. **Ethics docs (2,003 lines):** The ETHICS_AND_BIAS.md + BIAS_AUDIT_GUIDE.md are
   thorough but aspirational. Archive, or keep a shortened version?
