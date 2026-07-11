#!/usr/bin/env python3
"""
Precision Medicine MCP — Doc Audit Script
Runs four canonical-reference checks (A-D) against the repo.
Run from the repo root: python .claude/skills/doc-audit/scripts/audit.py
"""

import re
import sys
from collections import defaultdict
from hashlib import md5
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # adjust if skill moves
REGISTRY  = REPO_ROOT / "docs/reference/shared/server-registry.md"

# ── canonical patient outcome values (update when fixtures change) ────────────
CANONICAL_OUTCOMES = {
    "PAT001": {
        "TMB":            ("47.3",  "mut/Mb"),
        "IC50":           ("7.8",   "nM"),
        "HRD":            ("54",    ""),
        "CAF fraction":   ("18.2",  "%"),
    },
    "PAT002": {
        "HRD":            ("35",    ""),
    },
    "PAT003": {
        "Reynolds":       ("14.3",  "%"),
        "Framingham":     ("12.0",  "%"),
        "ASCVD":          ("10.3",  "%"),
        "hsCRP":          ("1.8",   "mg/L"),
    },
}

# numeric values the audit will flag if they appear near a patient ID
# maps (patient, wrong_value) → correct_value
KNOWN_WRONG_VALUES = {
    ("PAT001", "47.0"): "47.3",
    ("PAT001", "7.9"):  "7.8",
    ("PAT001", "HRD 72"): "HRD 54",   # README had 72 at one point
    ("PAT001", "4.2 mut"):  "47.3 mut",  # stale pre-POLE TMB
    ("PAT001", "3.2 mut"):  "47.3 mut",  # stale pre-POLE TMB
    ("PAT003", "14.2"): "14.3",        # earlier canonical estimate
    ("PAT003", "12.4"): "12.0",
    ("PAT003", "11.8"): "10.3",
}

PATIENT_IDS = {"PAT001", "PAT002", "PAT003"}

# patient-specific files that are expected to mention only one patient
SINGLE_PATIENT_FILES = {
    "PAT001_OVERVIEW.md", "PAT002_OVERVIEW.md", "PAT003_OVERVIEW.md",
    "PATIENT_JOURNEY.md", "CAREGIVER_FAQ.md",
    "pat001_canonical.py", "pat002_canonical.py", "pat003_canonical.py",
    "pat001_profile.json", "pat002_profile.json", "pat003_profile.json",
}

# Directories where single-patient focus is expected
SINGLE_PATIENT_DIRS = {
    "servers/",          # each server README covers one domain, not all patients
    ".claude/",          # skill and config files
    "docs/",             # audience docs, reference, testing — each focuses on specific use cases
    "tests/",            # fixture and test files are patient-specific by design
    "data/",             # per-patient data directories
    "ui/",               # UI docs reference specific demo workflows
    "infrastructure/",   # deployment configs reference specific demos
}

# ── helpers ───────────────────────────────────────────────────────────────────

def all_md_files():
    return [p for p in REPO_ROOT.rglob("*.md")
            if ".git" not in p.parts
            and "node_modules" not in p.parts
            and ".venv" not in p.parts
            and "venv" not in p.parts
            and not any(x in str(p.relative_to(REPO_ROOT)) for x in (
                "docs/book",
                "docs/reference/testing/",  # per-patient test prompts share boilerplate by design
            ))]

def registry_tool_counts():
    """Parse the registry table → {server_name: tool_count}."""
    counts = {}
    if not REGISTRY.exists():
        return counts
    for line in REGISTRY.read_text().splitlines():
        m = re.match(r"\|\s*\*\*mcp-([\w-]+)\*\*\s*\|\s*(\d+)\s*\|", line)
        if m:
            counts[f"mcp-{m.group(1)}"] = int(m.group(2))
    return counts

def code_tool_counts():
    """Count @mcp.tool() decorators in every server's server.py."""
    counts = {}
    for server_dir in (REPO_ROOT / "servers").iterdir():
        if not server_dir.is_dir() or server_dir.name == "mcp-server-boilerplate":
            continue
        for server_py in server_dir.rglob("server.py"):
            text = server_py.read_text()
            n = len(re.findall(r"@mcp\.tool\(\)", text))
            if n:
                counts[server_dir.name] = n
    return counts

def registry_header_counts():
    """Return (custom_server_count, tool_count) from registry header line."""
    if not REGISTRY.exists():
        return None, None
    for line in REGISTRY.read_text().splitlines():
        m = re.search(r"\*\*Custom Servers:\*\*\s*(\d+)\s*\((\d+)\s*tools\)", line)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None, None

def paragraphs(text, min_words=80):
    """Split markdown text into paragraph-ish blocks of at least min_words."""
    blocks = re.split(r"\n{2,}", text)
    return [b.strip() for b in blocks
            if len(b.split()) >= min_words and not b.strip().startswith("|")]

# ── Check A: code vs registry tool counts ────────────────────────────────────

def check_A():
    print("\n━━━━ CHECK A — Tool counts: server code vs registry ━━━━")
    code    = code_tool_counts()
    registry = registry_tool_counts()
    violations = []
    all_servers = sorted(set(code) | set(registry))
    for srv in all_servers:
        c = code.get(srv)
        r = registry.get(srv)
        if c is None:
            violations.append(f"  MISSING IN CODE  {srv}  (registry says {r})")
        elif r is None:
            violations.append(f"  MISSING IN REGISTRY  {srv}  (code has {c} tools)")
        elif c != r:
            violations.append(f"  MISMATCH  {srv}  code={c}  registry={r}")
    if violations:
        print(f"  ✗ {len(violations)} violation(s):")
        for v in violations:
            print(v)
    else:
        code_total = sum(code.values())
        print(f"  ✓ All {len(code)} servers match registry  (total tools: {code_total})")
    return violations

# ── Check B: hardcoded counts in MD files ─────────────────────────────────────

COUNT_PATTERNS = [
    r"\b(\d{1,2})\s+custom\s+server",
    r"\b(\d{1,2})-server\b",
    r"\ball\s+(\d{1,2})\s+(custom\s+)?server",
    r"\b(\d{1,2})\s+tool",
    r"\bFull\s+(\d{1,2})-server",
]

def check_B():
    print("\n━━━━ CHECK B — Hardcoded counts in MD files ━━━━")
    reg_servers, reg_tools = registry_header_counts()
    violations = []
    for md in all_md_files():
        if md.name == "server-registry.md":
            continue
        # skip per-server docs, developer config, UI, and all docs/ subtrees —
        # per-server, per-subsystem, and audience-specific counts are intentional
        rel = str(md.relative_to(REPO_ROOT))
        if any(rel.startswith(p) for p in (
            "servers/", ".claude/", "ui/", "docs/",
        )):
            continue
        # CLAUDE.md at repo root lists per-server tool counts — skip it
        if md.name == "CLAUDE.md" and md.parent == REPO_ROOT:
            continue
        # README.md at repo root: "46 tools" is external connectors, not custom servers
        if md.name == "README.md" and md.parent == REPO_ROOT:
            continue
        text = md.read_text()
        for pat in COUNT_PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                n = int(m.group(1))
                # flag if the number looks like a stale server or tool count (4–200)
                # skip counts that match the current registry values
                if n in (reg_servers, reg_tools):
                    continue
                if 4 <= n <= 200:
                    line_no = text[:m.start()].count("\n") + 1
                    violations.append(
                        f"  {md.relative_to(REPO_ROOT)}:{line_no}  "
                        f"'{m.group(0).strip()}'  →  replace with registry link"
                    )
    if violations:
        # deduplicate (same file+line can match multiple patterns)
        seen = set()
        uniq = []
        for v in violations:
            key = v.split("  '")[0]
            if key not in seen:
                seen.add(key)
                uniq.append(v)
        print(f"  ✗ {len(uniq)} violation(s):")
        for v in uniq:
            print(v)
    else:
        print("  ✓ No hardcoded counts found outside server-registry.md")
    return violations

# ── Check C: three patient outcomes ──────────────────────────────────────────

def check_C():
    print("\n━━━━ CHECK C — Three patient outcomes: completeness & accuracy ━━━━")
    violations = []
    for md in all_md_files():
        rel = str(md.relative_to(REPO_ROOT))
        if md.name in SINGLE_PATIENT_FILES:
            continue
        if any(rel.startswith(d) for d in SINGLE_PATIENT_DIRS):
            continue
        text = md.read_text()
        found = {p for p in PATIENT_IDS if p in text or p.lower() in text}
        # completeness: if any patient mentioned, all should be (in non-trivial files)
        if 1 <= len(found) <= 2 and len(text) > 500:
            missing = PATIENT_IDS - found
            violations.append(
                f"  INCOMPLETE  {md.relative_to(REPO_ROOT)}  "
                f"mentions {sorted(found)} but not {sorted(missing)}"
            )
        # accuracy: check known wrong numeric values
        for (pat, wrong), correct in KNOWN_WRONG_VALUES.items():
            if pat in text and wrong in text:
                line_no = text.find(wrong)
                line_no = text[:line_no].count("\n") + 1
                violations.append(
                    f"  WRONG VALUE  {md.relative_to(REPO_ROOT)}:{line_no}  "
                    f"'{wrong}' for {pat} should be '{correct}'"
                )
    if violations:
        print(f"  ✗ {len(violations)} violation(s):")
        for v in violations:
            print(v)
    else:
        print("  ✓ All patient references are complete and consistent")
    return violations

# ── Check D: DRY — duplicate content blocks ───────────────────────────────────

def check_D():
    print("\n━━━━ CHECK D — DRY: duplicate content blocks (>80 words) ━━━━")
    fingerprint_to_files = defaultdict(list)
    for md in all_md_files():
        text = md.read_text()
        for block in paragraphs(text):
            # normalise whitespace before hashing
            key = md5(re.sub(r"\s+", " ", block).encode()).hexdigest()
            fingerprint_to_files[key].append(
                (md.relative_to(REPO_ROOT), block[:120].replace("\n", " "))
            )
    violations = []
    for key, locations in fingerprint_to_files.items():
        if len(locations) > 1:
            files = [str(f) for f, _ in locations]
            preview = locations[0][1]
            violations.append((files, preview))
    if violations:
        print(f"  ✗ {len(violations)} duplicate block(s) found:")
        for files, preview in violations:
            print(f"\n  Block: \"{preview}...\"")
            print(f"  Found in:")
            for f in files:
                print(f"    {f}")
            print(f"  Fix: keep in one canonical file; replace others with a link")
    else:
        print("  ✓ No duplicate content blocks found")
    return violations

# ── Summary ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Precision Medicine MCP — Doc Audit")
    print(f"Repo root: {REPO_ROOT}")
    print("=" * 60)

    if not REPO_ROOT.exists():
        print(f"\nERROR: repo root not found at {REPO_ROOT}")
        print("Run this script from the repo root or adjust REPO_ROOT.")
        sys.exit(1)

    a = check_A()
    b = check_B()
    c = check_C()
    d = check_D()

    total = len(a) + len(b) + len(c) + len(d)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Check A (code vs registry):     {len(a):3d} violation(s)")
    print(f"  Check B (hardcoded counts):     {len(b):3d} violation(s)")
    print(f"  Check C (patient outcomes):     {len(c):3d} violation(s)")
    print(f"  Check D (DRY duplicates):       {len(d):3d} violation(s)")
    print(f"  {'─'*36}")
    print(f"  Total:                          {total:3d} violation(s)")

    if total == 0:
        print("\n✓ Repo docs are clean and canonical. Ship it.")
    else:
        print(f"\n✗ {total} violation(s) found.")
        print("  Run the doc-audit skill in Claude Code to generate a fix prompt.")

    return 0 if total == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
