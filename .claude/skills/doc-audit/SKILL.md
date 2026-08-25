---
name: precision-medicine-doc-audit
description: >
  Audits all Markdown files in the precision-medicine-mcp repo against five
  canonical principles: (A) server Python code is the authoritative tool count,
  (B) server-registry.md is the authoritative server/tool summary, (C) all
  three patient outcomes (PAT001/PAT002/PAT003) must be represented consistently,
  (D) no content block may appear in more than one MD file (DRY),
  (E) each server's own README documents every tool in its server.py. Use this skill
  whenever a new version of the platform ships, a new server is added, a new
  patient use case is validated, or before any major doc update. Trigger phrases:
  "audit the docs", "check docs are correct", "doc cleanup", "canonical check",
  "are the docs up to date", "DRY check on markdown".
---

# Precision Medicine MCP — Doc Audit Skill

## Purpose

After every platform version update, run this audit to catch stale numbers,
missing patient references, and repeated content before they spread further.
The audit has five checks (A–E) that map directly to the five canonical principles.
Run them in order: A feeds B, and B+C together surface D violations.

---

## Step 0 — Prove the checks still fire

A green audit is only meaningful if the checks are capable of going red. Three
times a check in this suite reported a clean repo while being structurally unable
to fail — an exemption added to quiet noise in one sub-rule, then applied to the
whole check. Run this first:

```bash
python .claude/skills/doc-audit/scripts/self_test.py
```

It builds a small synthetic repo in a temp directory, confirms the audit reports
it clean, then introduces one defect at a time and asserts the responsible check
catches it. The real repo is never touched.

**If any check does not fire, stop.** Fix that check before reading the audit
output — a check that cannot fail reports green and stops anyone looking.

---

## Step 1 — Run the automated audit script

The bundled script does the mechanical work. Run it from the repo root:

```bash
python .claude/skills/doc-audit/scripts/audit.py 2>&1 | tee /tmp/doc-audit-report.txt
```

The script outputs a structured report with five sections. Read the output — it
will tell you exactly which files have violations and what the correct values are.

If the script is not yet installed (first run), see **Installation** below.

---

## Step 2 — Interpret the five check sections

### Check A — Tool counts: code vs registry

The script greps `@mcp.tool()` in every `servers/mcp-*/src/*/server.py` and
compares to the count in `docs/reference/shared/server-registry.md`.

**A violation means:** someone added or removed a tool in Python code but forgot
to update the registry table. The server code is always right; update the registry.

### Check B — Hardcoded counts: all MD files

The script greps all `*.md` files for patterns like `\d+ (custom )?server`,
`\d+ tool`, `\d+-server`, `all \d+ server`, then flags any file that isn't
`docs/reference/shared/server-registry.md` itself.

**A violation means:** a doc is stating a count directly instead of pointing at
the registry. The fix is one of:
- Replace with: `see [Server Registry](../reference/shared/server-registry.md)`
- Or if a specific count is needed for context, verify it matches the registry
  and add a note: `(N as of vXX — see registry for current count)`

### Check C — Three patient outcomes: completeness and accuracy

The script checks two things:
1. **Completeness:** Any MD file that mentions one or two patient IDs but not all
   three is flagged (unless it's a patient-specific file like `PAT003_OVERVIEW.md`).
2. **Accuracy:** Any file that states a numeric outcome for PAT001, PAT002, or PAT003
   is checked against the canonical values below.

**Canonical patient outcome values** (update this section when fixtures change):

| Patient | Metric | Canonical value | Source file |
|---|---|---|---|
| PAT001 | TMB (POLE-corrected) | 47.3 mut/Mb | `tests/fixtures/pat001_canonical.py` |
| PAT001 | Top neoantigen IC50 | 7.8 nM | `tests/fixtures/pat001_canonical.py` |
| PAT001 | HRD score | 54 | `tests/fixtures/pat001_canonical.py` |
| PAT001 | CAF fraction | 18.2% | `tests/fixtures/pat001_canonical.py` |
| PAT002 | HRD score | 35 | `tests/fixtures/pat002_canonical.py` |
| PAT003 | Reynolds risk | 14.3% | `tests/fixtures/pat003_canonical.py` |
| PAT003 | Framingham risk | 12.0% | `tests/fixtures/pat003_canonical.py` |
| PAT003 | ASCVD risk | 10.3% | `tests/fixtures/pat003_canonical.py` |
| PAT003 | hsCRP | 1.8 mg/L | `tests/fixtures/pat003_canonical.py` |

**A violation means:** a doc states an outcome that differs from the canonical
fixture. The canonical fixture (which matches the live server output) is always
right — update the doc.

### Check D — DRY: duplicate content blocks

The script extracts paragraph-length text blocks (>80 words) from every MD file
and computes fingerprints. Any fingerprint appearing in more than one file is
flagged with both locations.

**A violation means:** the same content block lives in two places. One must
become the canonical location and the other must be replaced with a link.

**Standard fix pattern:**
```markdown
<!-- was: [full text of the repeated block] -->
> For PAT001 findings see [Patient Outcomes Reference](../reference/shared/patient-outcomes.md#pat001).
```

The canonical single-source for patient outcome narratives is:
`docs/reference/shared/patient-outcomes.md`

If that file doesn't exist yet, create it before resolving D violations — see
**Creating patient-outcomes.md** below.

### Check E — Server code vs the server's own README

The script lists every `@mcp.tool()` in each `servers/mcp-*/**/server.py` and checks
that the server's own `README.md` names each one, and that any total it states
matches the code.

**A violation means:** a server gained or lost a tool and its README was not
updated, or the server has no README at all. A server's README is canonical for
that server — it is where a reader looks up what the server can do — so Check B
deliberately skips `servers/` and this check covers it instead.

The fix is to document the tool in the server README. Do not "fix" it by editing
the code to match the doc: **the code is canonical.**

---

## Step 3 — Generate the fix prompt

After reading the audit output, generate a targeted Claude Code fix prompt.
Use this template:

```
# Doc Cleanup — [version] audit findings

## Violations found
[paste the audit report table here]

## Fix instructions

For each B violation:
  Find: [exact stale count string]
  Replace: [link to server-registry.md or corrected count]

For each C violation:
  Find: [wrong numeric value]
  Replace: [canonical value from audit table]

For each D violation:
  In [secondary file]: replace [repeated block] with link to [canonical file#anchor]

## Verification
grep -rn "[old count]" [affected files]
# Expected: zero matches
```

---

## Creating patient-outcomes.md (one-time setup)

If `docs/reference/shared/patient-outcomes.md` does not exist, create it before
resolving any D violations. It should contain exactly three sections, one per
patient, each with:
- One-sentence clinical profile
- What standard workup found (and its limitations)
- What the platform found that standard workup missed (3 bullets max)
- Canonical numeric outcomes (linked to the fixture file)

Keep each section under 200 words. Other docs link to the relevant anchor
(`#pat001`, `#pat002`, `#pat003`) rather than restating the findings.

---

## Installation (first run only)

Copy the skill into the repo:

```bash
mkdir -p .claude/skills/doc-audit/scripts
cp <this-skill-directory>/SKILL.md .claude/skills/doc-audit/SKILL.md
cp <this-skill-directory>/scripts/audit.py .claude/skills/doc-audit/scripts/audit.py
cp <this-skill-directory>/scripts/self_test.py .claude/skills/doc-audit/scripts/self_test.py
git add .claude/skills/doc-audit/
git commit -m "chore: add doc-audit skill for canonical reference checks"
```

Both scripts have no dependencies beyond the Python standard library.

When you add a check, add a matching case to `self_test.py`'s `CASES` list. A
check with no self-test case is one refactor away from being silently inert.

---

## Quick reference: the 5 principles

| # | Principle | Source of truth | Fix when violated |
|---|---|---|---|
| A | Code is canonical for tool counts | `servers/mcp-*/src/*/server.py` | Update registry to match code |
| B | Registry is canonical for counts in docs | `docs/reference/shared/server-registry.md` | Replace inline count with registry link |
| C | Three patients, consistent outcomes | `tests/fixtures/pat00X_canonical.py` | Update doc to match fixture value |
| D | No repeated content blocks | Designated canonical file per topic | Keep in one place; replace others with link |
| E | Server README documents its own tools | `servers/mcp-*/**/server.py` | Document the tool in that server's README |
