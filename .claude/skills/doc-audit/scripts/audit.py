#!/usr/bin/env python3
"""
Precision Medicine MCP — Doc Audit Script
Runs five canonical-reference checks (A-E) against the repo.
Run from the repo root: python .claude/skills/doc-audit/scripts/audit.py

Set DOC_AUDIT_ROOT to point the checks at a different tree. self_test.py uses
this to run every check against a small synthetic repo, so each check has to
prove it still fires. Three times now a check in this file has reported a clean
repo while being structurally unable to fail.
"""

import os
import re
import sys
from collections import defaultdict
from hashlib import md5
from pathlib import Path

REPO_ROOT = Path(
    os.environ.get("DOC_AUDIT_ROOT") or Path(__file__).resolve().parents[4]
)
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

# A numeric match only counts as a patient-outcome claim if its line is about a
# patient metric. "11.8" once matched "CUDA 11.8+" in a GPU requirements list
# simply because the file mentioned PAT003 elsewhere.
METRIC_CONTEXT = (
    r"reynolds|framingham|ascvd|pooled cohort|hscrp|hs-crp|crp\b|"
    r"tmb|ic50|neoantigen|hrd|caf|risk|mut/mb|nm\b|mg/l|PAT00\d"
)

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
            and "docs/book" not in str(p.relative_to(REPO_ROOT))]


# Per-patient test prompts share boilerplate by design, so they are excluded from
# the DRY check only. Excluding them globally (as this once did) also hid stale
# counts and wrong patient values from checks B and C.
DRY_EXEMPT_PREFIXES = ("docs/reference/testing/",)

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

# A count in a doc is one of three things, and conflating them is why this check
# was first noisy and then switched off entirely:
#
#   1. a SERVER count ("19 custom servers")   -> compare to the registry
#   2. a per-server TOOL count named on the
#      same line ("mcp-spatialtools (16 tools)") -> compare to THAT server's code
#   3. anything else ("6 tools" for an external connector, a per-category
#      subtotal in a diagram)                 -> not a platform claim; skip
#
# Only 1 and 2 are checkable. Flagging 3 buries the real findings.
SERVER_COUNT_PATTERNS = [
    r"\b(\d{1,3})\s+custom\s+servers?\b",
    r"\b(\d{1,3})[- ]servers?\b",
    r"\ball\s+(\d{1,3})\s+(?:custom\s+)?(?:MCP\s+)?servers?\b",
    r"\b(\d{1,3})\s+(?:custom\s+)?MCP\s+servers?\b",
    # "**Servers:** 19 custom (127 tools)" -- the word "server" is in the label
    r"\b(\d{1,3})\s+custom\s*\(",
]

# A count describing a deliberate SUBSET is not a claim about the platform.
# "11 servers return per-tool XAI metadata" counts a capability subset, not the
# platform. Same for an explicitly-scoped MVP pipeline.
SUBSET_MARKERS = ("mvp", "subset", "minimum viable", "xai metadata")

# Test-prompt docs describe a scenario that exercises N servers on purpose
# ("test-7: 6 servers", "test-10: all 17"). Those server counts are scenario
# scope, not platform claims, so the server-count rule is skipped there. Tool
# counts are still checked -- these files can still carry a stale platform total.
SCOPED_SUBSET_PREFIXES = (
    "docs/reference/testing/",
    "docs/reference/prompts/",   # scenario prompts: "All 3 servers contributed?"
)
# \d{1,3}, not \d{1,2}: tool counts passed 100 in Aug 2026 and a two-digit
# pattern silently stopped matching them, so the check reported clean while a
# dozen docs carried a stale total.
TOOL_COUNT_PATTERN = r"\b(\d{1,3})\s+tools?\b"

# Lines that legitimately state a past count: a changelog row or a dated run log
# is a historical record, not a claim about the platform today.
HISTORICAL_MARKERS = (
    "at that release",
    "no dry_run | pass",
)


def check_B():
    print("\n━━━━ CHECK B — Hardcoded counts in MD files ━━━━")
    reg_servers, reg_tools = registry_header_counts()
    code = code_tool_counts()
    violations = []
    for md in all_md_files():
        if md.name == "server-registry.md":
            continue
        # `docs/` is NOT skipped. It used to be, which disabled this check almost
        # entirely -- docs/ is where the documentation lives, so excluding it left
        # Check B looking at a handful of root files and reporting clean while a
        # dozen docs carried a stale tool count.
        #
        # `servers/` is skipped because a server's own README is canonical for
        # that server; check_E verifies it against the code instead.
        rel = str(md.relative_to(REPO_ROOT))
        if any(rel.startswith(p) for p in (
            "servers/", ".claude/", "ui/", "docs/reference/archive/",
        )):
            continue
        if md.name == "CLAUDE.md" and md.parent == REPO_ROOT:
            continue

        for line_no, line in enumerate(md.read_text().splitlines(), start=1):
            low = line.lower()
            if any(marker in low for marker in HISTORICAL_MARKERS):
                continue
            if any(marker in low for marker in SUBSET_MARKERS):
                continue
            here = f"  {md.relative_to(REPO_ROOT)}:{line_no}"

            # 1. server counts -- a platform claim, unless this doc describes a
            #    deliberately scoped scenario
            scoped = rel.startswith(SCOPED_SUBSET_PREFIXES)
            server_count_on_line = False
            for pat in SERVER_COUNT_PATTERNS:
                for m in re.finditer(pat, line, re.IGNORECASE):
                    n = int(m.group(1))
                    if not (1 <= n <= 200):
                        continue
                    # Set BEFORE any further filtering: the line carries a server
                    # count whatever its magnitude, and that is what tells the
                    # tool-count rule below that an adjacent "(N tools)" is a
                    # platform total. A `4 <= n` floor here previously meant a
                    # small server count silently disabled the tool-count rule on
                    # the same line -- invisible in this repo only because it has
                    # 19 servers.
                    server_count_on_line = True
                    if scoped:
                        continue
                    if reg_servers is not None and n != reg_servers:
                        v = f"{here}  '{n} servers'  →  registry says {reg_servers} servers"
                        if v not in violations:
                            violations.append(v)

            # 2/3. tool counts
            for m in re.finditer(TOOL_COUNT_PATTERN, line, re.IGNORECASE):
                n = int(m.group(1))
                if not (1 <= n <= 200):
                    continue
                col = m.start()
                named = [
                    mm.group(0)
                    for mm in re.finditer(r"mcp-[a-z0-9-]+", line)
                    if mm.start() < col
                ]
                if named and named[-1] in code:
                    owner = named[-1]
                    if n != code[owner]:
                        violations.append(
                            f"{here}  '{m.group(0).strip()}' for {owner}  →  code has {code[owner]}"
                        )
                elif server_count_on_line:
                    # "19 custom servers (119 tools)" -- a platform total
                    if reg_tools is not None and n != reg_tools:
                        violations.append(
                            f"{here}  '{m.group(0).strip()}'  →  registry says {reg_tools} tools"
                        )

    if violations:
        seen, uniq = set(), []
        for v in violations:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        print(f"  ✗ {len(uniq)} violation(s):")
        for v in uniq:
            print(v)
        return uniq
    print("  ✓ No stale server or tool counts found outside server-registry.md")
    return violations

# ── Check C: three patient outcomes ──────────────────────────────────────────

def check_C():
    print("\n━━━━ CHECK C — Three patient outcomes: completeness & accuracy ━━━━")
    violations = []
    for md in all_md_files():
        rel = str(md.relative_to(REPO_ROOT))
        text = md.read_text()

        # SINGLE_PATIENT_* exempts a doc from the COMPLETENESS rule only: a
        # per-patient overview is supposed to mention one patient. It must NOT
        # exempt the accuracy rule -- applied to the whole function (as it once
        # was) it skipped docs/, servers/, tests/ and more, so the check that
        # validates canonical patient values never looked at patient-outcomes.md,
        # the canonical patient file itself.
        single_patient_ok = (
            md.name in SINGLE_PATIENT_FILES
            or any(rel.startswith(d) for d in SINGLE_PATIENT_DIRS)
        )

        found = {p for p in PATIENT_IDS if p in text or p.lower() in text}
        # completeness: if any patient mentioned, all should be (in non-trivial files)
        if not single_patient_ok and 1 <= len(found) <= 2 and len(text) > 500:
            missing = PATIENT_IDS - found
            violations.append(
                f"  INCOMPLETE  {md.relative_to(REPO_ROOT)}  "
                f"mentions {sorted(found)} but not {sorted(missing)}"
            )
        # accuracy: check known wrong numeric values
        for (pat, wrong), correct in KNOWN_WRONG_VALUES.items():
            if pat not in text:
                continue
            # Numeric boundaries matter: a bare substring search made "7.9" match
            # inside "17.9%" in an unrelated confidence distribution, and would
            # equally match "7.85". Require the value not to sit inside a longer
            # number on either side.
            for m in re.finditer(
                r"(?<![\d.])" + re.escape(wrong) + r"(?![\d])", text
            ):
                line_no = text[: m.start()].count("\n") + 1
                line = text.splitlines()[line_no - 1]
                # The number must appear in a line that is actually about a
                # patient metric. Without this, "11.8" matched "CUDA 11.8+" in a
                # GPU requirements list purely because the file mentioned PAT003
                # somewhere else.
                if not re.search(METRIC_CONTEXT, line, re.IGNORECASE):
                    continue
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
        if str(md.relative_to(REPO_ROOT)).startswith(DRY_EXEMPT_PREFIXES):
            continue
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

# ── Check E: server code vs the server's own README ──────────────────────────

def check_E():
    """A server's README is canonical for that server, so it must match the code.

    Check A compares code to the aggregate registry. This compares code to the
    per-server doc, which is where a reader actually looks up what a server can
    do -- a README listing 4 tools for a 12-tool server is drift even when it
    states no total.
    """
    print("\n━━━━ CHECK E — Server code vs server README ━━━━")
    violations = []
    for srv_dir in sorted(REPO_ROOT.glob("servers/mcp-*/")):
        if srv_dir.name == "mcp-server-boilerplate":
            continue
        server_py = None
        for p in srv_dir.rglob("server.py"):
            if any(x in p.parts for x in ("venv", ".venv", "build", "site-packages")):
                continue
            server_py = p
            break
        if server_py is None:
            continue
        src = server_py.read_text(encoding="utf-8", errors="replace")
        names = re.findall(r"@mcp\.tool\(\)\s*\n\s*(?:async\s+)?def\s+(\w+)", src)
        readme = srv_dir / "README.md"
        if not readme.exists():
            violations.append(f"  {srv_dir.name}  has no README.md ({len(names)} tools undocumented)")
            continue
        text = readme.read_text(encoding="utf-8", errors="replace")
        missing = [n for n in names if n not in text]
        for n in missing:
            violations.append(f"  {srv_dir.name}/README.md  does not document tool '{n}'")
        # A stated total, if present, must match the code.
        for m in re.finditer(r"\b(\d{1,3})\s+tools?\b", text, re.IGNORECASE):
            stated = int(m.group(1))
            if stated != len(names) and 1 <= stated <= 200:
                line_no = text[: m.start()].count("\n") + 1
                violations.append(
                    f"  {srv_dir.name}/README.md:{line_no}  says '{m.group(0)}' "
                    f"but code has {len(names)}"
                )
    if violations:
        print(f"  ✗ {len(violations)} violation(s):")
        for v in violations:
            print(v)
    else:
        print("  ✓ Every server README matches its server.py")
    return violations


# ── Check F: link integrity ──────────────────────────────────────────────────
#
# Every one of these was a real defect that survived a local check, because on
# disk the file is there and only GitHub's renderer disagrees:
#
#   * a `blob` URL in an <img> tag serves the file VIEWER page (text/html), so
#     the image silently does not render
#   * Pandoc's {#custom-id} heading syntax is not supported by GitHub Flavored
#     Markdown: the braces render as literal text and GitHub derives its own
#     slug, so links to the intended short anchor land on the page but not the
#     section
#
# Deliberately offline: external http(s) URLs are not fetched. A check that
# needs the network is a check that fails for the wrong reasons.

_LINK_RE = re.compile(r"(!?)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_HTML_IMG_RE = re.compile(r"<img[^>]*src=\"([^\"]+)\"", re.I)
_HTML_ANCHOR_RE = re.compile(r"<a[^>]*\b(?:id|name)=\"([^\"]+)\"", re.I)
_PANDOC_ID_RE = re.compile(r"^#{1,6} .*\{#([\w-]+)\}\s*$", re.M)


def _mask_code(text: str) -> str:
    """Blank out code fences and inline spans, preserving offsets.

    Links inside code are examples, not links. The doc-audit SKILL.md documents
    the standard fix as a fenced markdown sample containing
    `(../reference/shared/patient-outcomes.md#pat001)`; checking that path would
    report a broken link in a snippet whose whole job is to be illustrative.
    Offsets are preserved so line numbers stay accurate.
    """
    out = list(text)
    for m in re.finditer(r"^```.*?^```", text, re.S | re.M):
        for i in range(m.start(), m.end()):
            if out[i] != "\n":
                out[i] = " "
    masked = "".join(out)
    for m in re.finditer(r"`[^`\n]*`", masked):
        for i in range(m.start(), m.end()):
            out[i] = " "
    return "".join(out)


def _github_slug(heading: str) -> str:
    """Reproduce GitHub's heading -> anchor slug.

    Lowercase, drop everything that is not a word character, space or hyphen,
    then spaces to hyphens. An em dash surrounded by spaces therefore collapses
    to a double hyphen, which is why the real anchors look like
    "pat001--hgsoc-stage-iv".
    """
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return re.sub(r"\s", "-", s)


def _anchors_in(path: Path) -> set:
    """Every fragment that resolves inside `path`: headings plus HTML anchors."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    out = {m.group(1) for m in _HTML_ANCHOR_RE.finditer(text)}
    for line in text.splitlines():
        if line.startswith("#"):
            out.add(_github_slug(line.lstrip("#")))
    return out


# Archived docs are frozen snapshots; their links point at the layout that
# existed when they were archived. Check B skips this tree for the same reason.
LINK_EXEMPT_PREFIXES = ("docs/reference/archive/",)


def check_F():
    print("\n━━━━ CHECK F — Link integrity ━━━━")
    violations = []
    anchor_cache = {}

    for md in all_md_files():
        rel = str(md.relative_to(REPO_ROOT))
        if rel.startswith(LINK_EXEMPT_PREFIXES):
            continue
        raw = md.read_text(encoding="utf-8", errors="replace")
        text = _mask_code(raw)

        for m in _PANDOC_ID_RE.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            violations.append(
                f"  {rel}:{line_no}  Pandoc '{{#{m.group(1)}}}' heading id — GitHub "
                f"ignores this; use <a id=\"{m.group(1)}\"></a> above the heading"
            )

        found = [(m.group(1) == "!", m.group(2), m.start()) for m in _LINK_RE.finditer(text)]
        found += [(True, m.group(1), m.start()) for m in _HTML_IMG_RE.finditer(text)]

        for is_image, href, pos in found:
            line_no = text[:pos].count("\n") + 1
            here = f"  {rel}:{line_no}"

            if is_image and re.match(r"https?://github\.com/[^/]+/[^/]+/blob/", href):
                violations.append(
                    f"{here}  image points at a GitHub 'blob' URL, which serves "
                    f"text/html not an image: {href}"
                )
                continue
            if href.startswith(("http://", "https://", "mailto:", "tel:")):
                continue  # external: not fetched, on purpose

            target_part, _, frag = href.partition("#")
            if target_part:
                target = (md.parent / target_part).resolve()
                if not target.exists():
                    violations.append(f"{here}  target does not exist: {href}")
                    continue
            else:
                target = md

            if frag and target.is_file() and target.suffix == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = {a.lower() for a in _anchors_in(target)}
                if frag.lower() not in anchor_cache[target]:
                    violations.append(
                        f"{here}  fragment '#{frag}' not found in {target_part or md.name}"
                    )

    if violations:
        seen, uniq = set(), []
        for v in violations:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        print(f"  ✗ {len(uniq)} violation(s):")
        for v in uniq:
            print(v)
        return uniq
    print("  ✓ All relative links and fragments resolve; no blob-URL images")
    return violations


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
    e = check_E()
    f = check_F()

    total = len(a) + len(b) + len(c) + len(d) + len(e) + len(f)
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Check A (code vs registry):     {len(a):3d} violation(s)")
    print(f"  Check B (hardcoded counts):     {len(b):3d} violation(s)")
    print(f"  Check C (patient outcomes):     {len(c):3d} violation(s)")
    print(f"  Check D (DRY duplicates):       {len(d):3d} violation(s)")
    print(f"  Check E (server README):        {len(e):3d} violation(s)")
    print(f"  Check F (link integrity):       {len(f):3d} violation(s)")
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
