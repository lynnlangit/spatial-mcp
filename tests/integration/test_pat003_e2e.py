"""PAT003 end-to-end integration test — Preventive Cardiovascular Health.

PAT003 is a synthetic profile representing a 67-year-old post-menopausal
woman with controlled hypertension and bilateral family history of CVD.
This is a representative case for the "65+ female" demographic, not any
specific individual.

This test exercises existing MCP servers against PAT003 data and produces
a gap report showing which clinical questions the platform can and cannot
answer for a preventive cardiovascular use case.

Each server call is executed via ``uv run`` in the server's own virtualenv
so that FastMCP and server-specific dependencies are available.

Run:
    python -m pytest tests/integration/test_pat003_e2e.py -v --tb=short -s
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OPENTARGETS_DIR = REPO_ROOT / "servers" / "mcp-opentargets"
PATIENT_REPORT_DIR = REPO_ROOT / "servers" / "mcp-patient-report"
MULTIOMICS_DIR = REPO_ROOT / "servers" / "mcp-multiomics"

# Import PAT003 canonical data
sys.path.insert(0, str(REPO_ROOT))
from tests.fixtures.pat003_canonical import PAT003

# ---------------------------------------------------------------------------
# Shared results collector
# ---------------------------------------------------------------------------

RESULTS: List[Dict[str, Any]] = []


def record(server: str, tool: str, input_summary: str,
           output_summary: str, clinically_useful: bool,
           gap_identified: Optional[str] = None) -> None:
    """Append a result to the shared collector."""
    RESULTS.append({
        "server": server,
        "tool": tool,
        "input": input_summary,
        "output_summary": output_summary,
        "clinically_useful": clinically_useful,
        "gap_identified": gap_identified,
    })


def _run_in_server(server_dir: Path, script: str,
                   timeout: int = 30) -> Dict[str, Any]:
    """Execute a Python snippet via ``uv run`` inside a server virtualenv.

    Returns the parsed JSON that the script prints to stdout, or an error dict.
    """
    result = subprocess.run(
        ["uv", "run", "python", "-c", script],
        capture_output=True,
        text=True,
        cwd=str(server_dir),
        timeout=timeout,
        env={
            **dict(subprocess.os.environ),
            "OPENTARGETS_DRY_RUN": "true",
            "PATIENT_REPORT_DRY_RUN": "true",
            "MULTIOMICS_DRY_RUN": "true",
        },
    )
    if result.returncode != 0:
        return {"status": "error", "message": result.stderr.strip()[-500:]}
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"status": "error", "message": f"non-JSON output: {result.stdout.strip()[:300]}"}


# ===================================================================
# 4-A: opentargets — gene-disease associations for CVD risk genes
# ===================================================================


class TestOpenTargetsAssociations:
    """Query gene-disease associations for each PAT003 CVD risk gene."""

    @pytest.mark.parametrize("gene", PAT003["cvd_risk_genes"])
    def test_gene_disease_association(self, gene: str) -> None:
        script = f"""
import asyncio, json
from mcp_opentargets.server import _get_target_disease_associations_impl
r = asyncio.run(_get_target_disease_associations_impl(
    gene_symbol="{gene}", disease_id="EFO_0001071", top_n=3))
print(json.dumps(r))
"""
        result = _run_in_server(OPENTARGETS_DIR, script)

        assert "status" not in result or result["status"] != "error", (
            f"Server error for {gene}: {result.get('message', '')}"
        )

        score = result.get("overall_score", "N/A")

        # Score > 0.40 means gene-specific mock data exists (default is 0.40)
        has_specific_data = isinstance(score, (int, float)) and score > 0.40
        gap = None
        if not has_specific_data:
            gap = (f"DRY_RUN returns generic mock for {gene}; "
                   f"no gene-specific disease ontology entry")

        record(
            server="opentargets",
            tool="get_target_disease_associations",
            input_summary=f"gene={gene}, disease=EFO_0001071",
            output_summary=f"score={score}, status={result.get('status', 'ok')}",
            clinically_useful=has_specific_data,
            gap_identified=gap,
        )


# ===================================================================
# 4-B: opentargets — drug information for ACE (lisinopril target)
# ===================================================================


class TestOpenTargetsDrugsACE:
    """Query drugs for ACE gene to verify lisinopril appears."""

    def test_ace_drugs(self) -> None:
        script = """
import asyncio, json
from mcp_opentargets.server import _get_target_drugs_impl
r = asyncio.run(_get_target_drugs_impl(gene_symbol="ACE", phase_min=0))
print(json.dumps(r))
"""
        result = _run_in_server(OPENTARGETS_DIR, script)
        assert "status" not in result or result["status"] != "error", (
            f"Server error: {result.get('message', '')}"
        )

        drugs = result.get("drugs", [])
        drug_names = [d.get("name", "").lower() for d in drugs]
        has_ace_inhibitor = any(
            kw in n for n in drug_names
            for kw in ("lisinopril", "ace", "captopril", "enalapril")
        )

        gap = None
        if not has_ace_inhibitor:
            gap = ("ACE gene drug lookup returns no ACE inhibitors in DRY_RUN; "
                   "mock data is oncology-focused, not cardiovascular")

        record(
            server="opentargets",
            tool="get_target_drugs",
            input_summary="gene=ACE, phase_min=0",
            output_summary=f"{len(drugs)} drugs, ACE-inh={has_ace_inhibitor}",
            clinically_useful=has_ace_inhibitor,
            gap_identified=gap,
        )


# ===================================================================
# 4-C: opentargets — PCSK9 emerging therapies
# ===================================================================


class TestOpenTargetsDrugsPCSK9:
    """Query PCSK9 drugs for emerging lipid-lowering therapies."""

    def test_pcsk9_drugs(self) -> None:
        script = """
import asyncio, json
from mcp_opentargets.server import _get_target_drugs_impl
r = asyncio.run(_get_target_drugs_impl(gene_symbol="PCSK9", phase_min=0))
print(json.dumps(r))
"""
        result = _run_in_server(OPENTARGETS_DIR, script)
        assert "status" not in result or result["status"] != "error", (
            f"Server error: {result.get('message', '')}"
        )

        drugs = result.get("drugs", [])
        drug_names = [d.get("name", "").lower() for d in drugs]
        has_pcsk9_inhibitor = any(
            kw in n for n in drug_names
            for kw in ("evolocumab", "alirocumab", "inclisiran", "pcsk9")
        )

        gap = None
        if not has_pcsk9_inhibitor:
            gap = ("PCSK9 drug lookup returns no PCSK9 inhibitors in DRY_RUN; "
                   "mock data lacks cardiovascular drug entries")

        record(
            server="opentargets",
            tool="get_target_drugs",
            input_summary="gene=PCSK9, phase_min=0",
            output_summary=f"{len(drugs)} drugs, PCSK9-inh={has_pcsk9_inhibitor}",
            clinically_useful=has_pcsk9_inhibitor,
            gap_identified=gap,
        )


# ===================================================================
# 4-D: opentargets — safety profile for ACE
# ===================================================================


class TestOpenTargetsSafetyACE:
    """Query safety data for ACE gene (lisinopril's target)."""

    def test_ace_safety(self) -> None:
        script = """
import asyncio, json
from mcp_opentargets.server import _get_target_safety_impl
r = asyncio.run(_get_target_safety_impl(gene_symbol="ACE"))
print(json.dumps(r))
"""
        result = _run_in_server(OPENTARGETS_DIR, script)
        assert "status" not in result or result["status"] != "error", (
            f"Server error: {result.get('message', '')}"
        )

        liabilities = result.get("safety_liabilities", [])
        adverse = result.get("adverse_events", [])
        risk = result.get("risk_level", "unknown")
        has_data = len(liabilities) > 0 or len(adverse) > 0

        gap = None
        if not has_data:
            gap = ("ACE safety returns empty in DRY_RUN; "
                   "mock safety data only covers oncology targets")

        record(
            server="opentargets",
            tool="get_target_safety",
            input_summary="gene=ACE",
            output_summary=f"risk={risk}, liabilities={len(liabilities)}, ae={len(adverse)}",
            clinically_useful=has_data,
            gap_identified=gap,
        )


# ===================================================================
# 4-E: patient-report — generate PAT003 preventive health summary
# ===================================================================


class TestPatientReport:
    """Attempt to generate a report for PAT003."""

    def test_check_pdf_capability(self) -> None:
        script = """
import asyncio, json
from mcp_patient_report.server import check_pdf_capability
fn = getattr(check_pdf_capability, "fn", check_pdf_capability)
r = asyncio.run(fn())
print(json.dumps(r))
"""
        result = _run_in_server(PATIENT_REPORT_DIR, script)

        record(
            server="patient-report",
            tool="check_pdf_capability",
            input_summary="(no args)",
            output_summary=f"pdf={result.get('pdf_available')}, "
                           f"dry_run={result.get('dry_run_mode')}",
            clinically_useful=result.get("status") != "error",
            gap_identified=None if result.get("status") != "error" else
                           f"check_pdf_capability failed: {result.get('message', '')[:100]}",
        )

    def test_validate_report_data(self) -> None:
        report_data = {
            "report_category": "preventive_health",
            "metadata": {
                "patient_id": "PAT003",
                "generated_date": "2026-04-21",
                "report_version": "1.0",
            },
            "patient_info": {
                "name": "Synthetic CVD Patient",
                "age": 67,
                "sex": "Female",
                "patient_id": "PAT003",
                "diagnosis": "Preventive cardiovascular monitoring",
            },
            "diagnosis_summary": {
                "plain_language_description":
                    "This is a preventive health profile, not an active cancer case.",
            },
            "monitoring_plan": {
                "schedule": [
                    {"test_name": "Lipid panel", "frequency": "Every 12 months",
                     "purpose": "Track LDL, HDL, triglycerides"},
                    {"test_name": "Blood pressure", "frequency": "Every 8 weeks",
                     "purpose": "Monitor hypertension control"},
                    {"test_name": "HbA1c", "frequency": "Every 12 months",
                     "purpose": "Monitor prediabetes progression"},
                    {"test_name": "hsCRP", "frequency": "Every 24 months",
                     "purpose": "Track cardiovascular inflammation"},
                ],
                "warning_signs": [
                    "Chest pain or pressure",
                    "Sudden shortness of breath",
                    "Unexplained fatigue or dizziness",
                ],
                "who_to_contact": "Your primary care physician or cardiologist",
            },
        }
        data_json = json.dumps(report_data).replace("'", "\\'").replace('"', '\\"')
        script = f"""
import asyncio, json
from mcp_patient_report.server import validate_report_data
fn = getattr(validate_report_data, "fn", validate_report_data)
r = asyncio.run(fn(report_data_json='{data_json}'))
print(json.dumps(r))
"""
        result = _run_in_server(PATIENT_REPORT_DIR, script)

        valid = result.get("valid", False)

        gap = None
        if not valid:
            gap = ("Patient report schema requires oncology fields (cancer_type, stage); "
                   "preventive health use case needs a new report_type or schema extension")

        record(
            server="patient-report",
            tool="validate_report_data",
            input_summary="PAT003 minimal report (preventive health)",
            output_summary=f"valid={valid}, errors={result.get('errors', [])}",
            clinically_useful=valid,
            gap_identified=gap,
        )


# ===================================================================
# 4-F: multiomics — biomarker panel integration
# ===================================================================


class TestMultiomics:
    """Attempt to use multiomics server with PAT003 biomarker data."""

    def test_validate_multiomics_data(self) -> None:
        script = """
import json
from mcp_multiomics.server import validate_multiomics_data
fn = getattr(validate_multiomics_data, "__wrapped__", validate_multiomics_data)
try:
    r = fn(rna_path="/nonexistent/pat003_biomarkers.csv")
except Exception as e:
    r = {"status": "error", "message": str(e)}
print(json.dumps(r))
"""
        result = _run_in_server(MULTIOMICS_DIR, script)

        accepted = result.get("status") != "error"

        gap = None
        if not accepted:
            gap = ("Multiomics server expects omics matrix file paths (RNA/protein/phospho); "
                   "simple biomarker panels (lipid, glucose, CRP) need a new server "
                   "or adapter for preventive health use cases")

        record(
            server="multiomics",
            tool="validate_multiomics_data",
            input_summary="rna_path=/nonexistent/pat003_biomarkers.csv",
            output_summary=f"status={result.get('status', 'unknown')}",
            clinically_useful=accepted,
            gap_identified=gap,
        )


# ===================================================================
# Gap report — runs last (z_ prefix ensures alphabetical ordering)
# ===================================================================


class TestZGapReport:
    """Print the PAT003 gap report table.  Named z_ so it runs last."""

    def test_z_print_gap_report(self) -> None:
        """Collect and display gap analysis results from all server tests."""
        assert len(RESULTS) > 0, "No results collected — other tests may have been skipped"

        print("\n")
        print("=" * 90)
        print("PAT003 Gap Report — Preventive Cardiovascular Health (65+ Female)")
        print("=" * 90)
        print(f"{'Server':<18} {'Tool':<35} {'Useful?':<10} {'Gap'}")
        print("-" * 90)
        for r in RESULTS:
            useful = "Yes" if r["clinically_useful"] else "NO"
            gap = r["gap_identified"] or "—"
            print(f"{r['server']:<18} {r['tool']:<35} {useful:<10} {gap}")
        print("-" * 90)

        gaps = [r for r in RESULTS if r["gap_identified"]]
        print(f"\nTotal calls: {len(RESULTS)}, Clinically useful: "
              f"{sum(1 for r in RESULTS if r['clinically_useful'])}, "
              f"Gaps identified: {len(gaps)}")

        print("\n--- Remaining gaps / new servers needed for PAT003 ---")
        print("1. Cardiometabolic server (biomarker panels, CVD risk scoring, Lp(a), longitudinal tracking)")
        print("2. Polygenic risk score server (CVD-specific)")
        print("3. Lifestyle intervention evidence server")
        print("=" * 90)
