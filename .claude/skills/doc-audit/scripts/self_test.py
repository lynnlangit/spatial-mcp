#!/usr/bin/env python3
"""Self-test for the doc audit: every check must prove it can fail.

Why this exists
---------------
Three separate times, a check in audit.py reported a clean repo while being
structurally incapable of reporting anything else:

  * Check B skipped the entire `docs/` subtree -- where the documentation lives.
  * Check B's pattern was \\d{1,2}, so it stopped matching tool counts once they
    passed 100.
  * Check C applied a single-patient directory exemption to the WHOLE function,
    so the rule validating canonical patient values never looked at `docs/`,
    `servers/` or `tests/`.

Each was an exemption added to quiet noise in one sub-rule, then applied to the
whole check. Each left a green result that meant nothing, and each was found only
by deliberately breaking something and noticing the audit did not care.

This script automates that. It builds a small synthetic repo in a temp directory,
confirms the audit reports it clean, then introduces one specific defect at a time
and asserts the responsible check fires. The real repo is never touched.

Run:  python .claude/skills/doc-audit/scripts/self_test.py
"""

import contextlib
import importlib
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


# --------------------------------------------------------------------------- #
# A minimal repo that the audit should consider clean
# --------------------------------------------------------------------------- #

SERVER_PY = '''\
"""Synthetic server for the doc-audit self-test."""

from fastmcp import FastMCP

mcp = FastMCP("alpha")


@mcp.tool()
async def tool_one(x: int) -> dict:
    """First tool."""
    return {}


@mcp.tool()
async def tool_two(y: int) -> dict:
    """Second tool."""
    return {}
'''

SERVER_README = """\
# mcp-alpha

Synthetic server used by the doc-audit self-test. Provides 2 tools.

| Tool | Purpose |
|---|---|
| `tool_one` | First tool |
| `tool_two` | Second tool |
"""

REGISTRY_MD = """\
# MCP Server Registry - Quick Reference

**Custom Servers:** 1 (2 tools) | **Production Ready:** 1 (100%) | **External Servers:** 0 (0 tools)

## Production Servers

| Server | Tools | Status | Key Capabilities | Documentation |
|--------|-------|--------|------------------|---------------|
| **mcp-alpha** | 2 | 100% Real | Two synthetic tools | [README](../../../servers/mcp-alpha/README.md) |
"""

# Counts here must agree with the registry above.
AUDIENCE_DOC = """\
# Audience Guide

The platform ships 1 custom server (2 tools).

Server detail: mcp-alpha (2 tools).
"""

# Under docs/, so exempt from the completeness rule; the accuracy rule still
# applies, which is the half that was broken.
PATIENT_DOC = """\
# Outcomes

PAT001 tumour mutational burden is 47.3 mut/Mb and the top neoantigen binds at
IC50 7.8 nM. PAT002 HRD score is 35. PAT003 Reynolds risk is 14.3%.
"""

FILLER = " ".join(f"word{i}" for i in range(120))


def build_repo(root: Path) -> None:
    """Write a synthetic repo the audit should report clean."""
    (root / "servers/mcp-alpha/src/mcp_alpha").mkdir(parents=True)
    (root / "servers/mcp-alpha/src/mcp_alpha/server.py").write_text(SERVER_PY)
    (root / "servers/mcp-alpha/README.md").write_text(SERVER_README)

    (root / "docs/reference/shared").mkdir(parents=True)
    (root / "docs/reference/shared/server-registry.md").write_text(REGISTRY_MD)
    (root / "docs/guide.md").write_text(AUDIENCE_DOC)
    (root / "docs/outcomes.md").write_text(PATIENT_DOC)


# --------------------------------------------------------------------------- #
# Mutations -- one defect each, and the check that must catch it
# --------------------------------------------------------------------------- #


def _sub(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text, f"self-test anchor missing in {path.name}: {old!r}"
    path.write_text(text.replace(old, new, 1))


def mut_registry_drifts(root):
    _sub(root / "docs/reference/shared/server-registry.md",
         "| **mcp-alpha** | 2 |", "| **mcp-alpha** | 7 |")


def mut_stale_platform_tool_count(root):
    _sub(root / "docs/guide.md", "1 custom server (2 tools)", "1 custom server (9 tools)")


def mut_stale_platform_server_count(root):
    _sub(root / "docs/guide.md", "1 custom server", "4 custom servers")


def mut_stale_per_server_tool_count(root):
    _sub(root / "docs/guide.md", "mcp-alpha (2 tools)", "mcp-alpha (5 tools)")


def mut_wrong_patient_value_in_docs(root):
    _sub(root / "docs/outcomes.md", "IC50 7.8 nM", "IC50 7.9 nM")


def mut_wrong_patient_value_in_servers(root):
    """servers/ was one of the trees Check C used to skip entirely."""
    p = root / "servers/mcp-alpha/README.md"
    p.write_text(p.read_text() + "\nPAT001 TMB measured at 47.0 mut/Mb.\n")


def mut_duplicate_block(root):
    block = f"\n\n## Shared\n\n{FILLER}\n"
    for name in ("docs/guide.md", "docs/outcomes.md"):
        p = root / name
        p.write_text(p.read_text() + block)


def mut_server_readme_drops_tool(root):
    _sub(root / "servers/mcp-alpha/README.md", "`tool_two`", "`tool_renamed`")


def mut_server_readme_total_wrong(root):
    _sub(root / "servers/mcp-alpha/README.md", "Provides 2 tools.", "Provides 6 tools.")


def mut_server_readme_missing(root):
    (root / "servers/mcp-alpha/README.md").unlink()


CASES = [
    ("A", "registry tool count drifts from code", mut_registry_drifts),
    ("B", "stale platform tool count in a doc", mut_stale_platform_tool_count),
    ("B", "stale platform server count in a doc", mut_stale_platform_server_count),
    ("B", "stale per-server tool count in a doc", mut_stale_per_server_tool_count),
    ("C", "wrong patient value under docs/", mut_wrong_patient_value_in_docs),
    ("C", "wrong patient value under servers/", mut_wrong_patient_value_in_servers),
    ("D", "same block in two files", mut_duplicate_block),
    ("E", "server README drops a tool", mut_server_readme_drops_tool),
    ("E", "server README states a wrong total", mut_server_readme_total_wrong),
    ("E", "server has no README", mut_server_readme_missing),
]


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #


def run_checks(root: Path) -> dict:
    """Run every check against `root`, returning {letter: violation_count}."""
    os.environ["DOC_AUDIT_ROOT"] = str(root)
    import audit

    importlib.reload(audit)
    out = {}
    with contextlib.redirect_stdout(io.StringIO()):
        for letter in "ABCDE":
            out[letter] = len(getattr(audit, f"check_{letter}")())
    return out


@contextlib.contextmanager
def fresh_repo():
    tmp = Path(tempfile.mkdtemp(prefix="doc-audit-selftest-"))
    try:
        build_repo(tmp)
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    print("=" * 60)
    print("Doc Audit — self-test")
    print("Every check must prove it can fail.")
    print("=" * 60)

    failures = []

    # 1. The synthetic repo must be clean, or nothing below means anything.
    with fresh_repo() as root:
        baseline = run_checks(root)
    if any(baseline.values()):
        print(f"\n✗ BASELINE NOT CLEAN: {baseline}")
        print("  The synthetic repo should report zero violations. Fix it first —")
        print("  a dirty baseline makes every result below meaningless.")
        return 1
    print("\n  ✓ baseline: synthetic repo reports clean on all five checks")

    # 2. Each defect must be caught by its check.
    print()
    for letter, description, mutate in CASES:
        with fresh_repo() as root:
            mutate(root)
            result = run_checks(root)
        caught = result[letter] > 0
        others = {k: v for k, v in result.items() if k != letter and v > 0}
        status = "✓" if caught else "✗ NOT CAUGHT"
        print(f"  {status:<14} Check {letter} — {description}")
        if not caught:
            failures.append((letter, description, result))
        elif others:
            # Not a failure, but worth seeing: a mutation that trips other checks
            # too may be less specific than intended.
            print(f"                 (also tripped: {others})")

    print("\n" + "=" * 60)
    if failures:
        print(f"✗ {len(failures)} check(s) did not fire:")
        for letter, description, result in failures:
            print(f"    Check {letter} — {description}  → counts {result}")
        print("\n  A check that cannot fail is worse than no check: it reports")
        print("  green and stops anyone looking.")
        return 1

    print(f"✓ All {len(CASES)} defects caught. Every check can still fail.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
