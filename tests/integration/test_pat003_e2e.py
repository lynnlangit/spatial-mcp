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
CARDIOMETABOLIC_DIR = REPO_ROOT / "servers" / "mcp-cardiometabolic"

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
            "CARDIOMETABOLIC_DRY_RUN": "true",
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
# 4-F: cardiometabolic — biomarker panel + risk scoring + Lp(a) + report
# ===================================================================


class TestCardiometabolicBiomarkers:
    """Cardiometabolic server: biomarker panel interpretation."""

    def test_assess_biomarker_panel(self) -> None:
        script = """
import asyncio, json
from mcp_cardiometabolic.server import _assess_biomarker_panel_impl
r = asyncio.run(_assess_biomarker_panel_impl(
    ldl_mg_dl=118, hdl_mg_dl=58, total_cholesterol_mg_dl=195,
    triglycerides_mg_dl=142, fasting_glucose_mg_dl=98,
    hba1c_percent=5.6, hscrp_mg_l=1.8, bp_systolic_mmhg=138))
print(json.dumps(r))
"""
        result = _run_in_server(CARDIOMETABOLIC_DIR, script)
        useful = result.get("status") == "success"
        record(
            server="cardiometabolic",
            tool="assess_biomarker_panel",
            input_summary="PAT003 full panel (8 biomarkers)",
            output_summary=f"status={result.get('status')}, "
                           f"flags={len(result.get('flags', []))}",
            clinically_useful=useful,
            gap_identified=None if useful else
                           f"Biomarker panel failed: {result.get('message', '')[:100]}",
        )


class TestCardiometabolicRiskScores:
    """Cardiometabolic server: CVD risk score calculation."""

    def test_calculate_cvd_risk_scores(self) -> None:
        script = """
import asyncio, json
from mcp_cardiometabolic.server import _calculate_cvd_risk_scores_impl
r = asyncio.run(_calculate_cvd_risk_scores_impl(
    age=67, systolic_bp=138, total_cholesterol=195, hdl=58, hscrp=1.8,
    patient_sex="female", bp_treated=True, current_smoker=False,
    diabetes=False, family_history_premature_mi=True))
print(json.dumps(r))
"""
        result = _run_in_server(CARDIOMETABOLIC_DIR, script)
        reynolds_cat = result.get("reynolds", {}).get("risk_category", "")
        framingham_cat = result.get("framingham", {}).get("risk_category", "")
        ascvd_cat = result.get("ascvd", {}).get("risk_category", "")
        all_intermediate = all(c == "intermediate" for c in [reynolds_cat, framingham_cat, ascvd_cat])
        useful = result.get("status") == "success" and all_intermediate

        record(
            server="cardiometabolic",
            tool="calculate_cvd_risk_scores",
            input_summary="PAT003 vitals (age=67, SBP=138, TC=195, HDL=58, hsCRP=1.8)",
            output_summary=(
                f"Reynolds={result.get('reynolds', {}).get('risk_10yr_percent', 'N/A')}%, "
                f"Framingham={result.get('framingham', {}).get('risk_10yr_percent', 'N/A')}%, "
                f"ASCVD={result.get('ascvd', {}).get('risk_10yr_percent', 'N/A')}%"
            ),
            clinically_useful=useful,
            gap_identified=None if useful else "Risk scores not all intermediate",
        )


class TestCardiometabolicLpa:
    """Cardiometabolic server: Lp(a) status assessment."""

    def test_assess_lpa_status(self) -> None:
        script = """
import asyncio, json
from mcp_cardiometabolic.server import _assess_lpa_status_impl
r = asyncio.run(_assess_lpa_status_impl(lpa_mg_dl=None))
print(json.dumps(r))
"""
        result = _run_in_server(CARDIOMETABOLIC_DIR, script)
        useful = (
            result.get("status") == "success"
            and result.get("lpa_measured") is False
        )
        record(
            server="cardiometabolic",
            tool="assess_lpa_status",
            input_summary="lpa_mg_dl=None (not yet measured)",
            output_summary=f"measured={result.get('lpa_measured')}, "
                           f"urgency={result.get('clinical_urgency', 'N/A')}",
            clinically_useful=useful,
            gap_identified=None if useful else
                           f"Lp(a) assessment failed: {result.get('message', '')[:100]}",
        )


class TestCardiometabolicReport:
    """Cardiometabolic server: preventive health report."""

    def test_generate_preventive_report(self) -> None:
        script = """
import asyncio, json
from mcp_cardiometabolic.server import _generate_preventive_report_impl
r = asyncio.run(_generate_preventive_report_impl(
    patient_id="PAT003", fh_ruled_out=True))
print(json.dumps(r))
"""
        result = _run_in_server(CARDIOMETABOLIC_DIR, script)
        has_keys = all(
            k in result for k in (
                "executive_summary", "risk_scores", "priority_actions",
                "monitoring_schedule", "lifestyle_recommendations", "disclaimer",
            )
        )
        useful = result.get("status") == "success" and has_keys

        record(
            server="cardiometabolic",
            tool="generate_preventive_report",
            input_summary="PAT003, fh_ruled_out=True",
            output_summary=f"status={result.get('status')}, "
                           f"keys={'all present' if has_keys else 'MISSING'}",
            clinically_useful=useful,
            gap_identified=None if useful else
                           f"Report missing keys or failed: {result.get('message', '')[:100]}",
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

        print("\n--- Status ---")
        useful_count = sum(1 for r in RESULTS if r["clinically_useful"])
        if useful_count == len(RESULTS):
            print("ALL CALLS CLINICALLY USEFUL -- no remaining gaps for PAT003 core workflow")
        else:
            print("Remaining gaps / new servers needed for PAT003:")
            for r in RESULTS:
                if r["gap_identified"]:
                    print(f"  - [{r['server']}] {r['gap_identified']}")
        print("=" * 90)
