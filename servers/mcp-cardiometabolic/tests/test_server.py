"""Unit tests for mcp-cardiometabolic server."""

import pytest
from mcp_cardiometabolic.risk_scoring import (
    calculate_reynolds_women,
    calculate_framingham_women,
    calculate_ascvd_women_white,
)
from mcp_cardiometabolic.biomarker_ranges import classify_biomarker
from mcp_cardiometabolic.server import (
    _assess_biomarker_panel_impl,
    _calculate_cvd_risk_scores_impl,
    _assess_lpa_status_impl,
    _generate_preventive_report_impl,
    _get_lifestyle_evidence_impl,
)

# PAT003 canonical input values
PAT003 = {
    "age": 67,
    "systolic_bp": 138,
    "total_cholesterol": 195,
    "hdl": 58,
    "hscrp": 1.8,
    "family_history_premature_mi": True,
    "current_smoker": False,
    "bp_treated": True,
    "diabetes": False,
}


class TestReynoldsScore:
    """Reynolds Risk Score for PAT003 values."""

    def test_reynolds_pat003_within_tolerance(self):
        r = calculate_reynolds_women(
            age=PAT003["age"],
            systolic_bp=PAT003["systolic_bp"],
            total_cholesterol=PAT003["total_cholesterol"],
            hdl=PAT003["hdl"],
            hscrp=PAT003["hscrp"],
            family_history_premature_mi=PAT003["family_history_premature_mi"],
            current_smoker=PAT003["current_smoker"],
        )
        assert abs(r["risk_10yr_percent"] - 14.2) < 2.0, (
            f"Reynolds {r['risk_10yr_percent']}% not within +/-2% of 14.2%"
        )

    def test_reynolds_intermediate_category(self):
        r = calculate_reynolds_women(
            age=PAT003["age"],
            systolic_bp=PAT003["systolic_bp"],
            total_cholesterol=PAT003["total_cholesterol"],
            hdl=PAT003["hdl"],
            hscrp=PAT003["hscrp"],
            family_history_premature_mi=PAT003["family_history_premature_mi"],
            current_smoker=PAT003["current_smoker"],
        )
        assert r["risk_category"] == "intermediate"

    def test_reynolds_has_citation(self):
        r = calculate_reynolds_women(
            age=PAT003["age"],
            systolic_bp=PAT003["systolic_bp"],
            total_cholesterol=PAT003["total_cholesterol"],
            hdl=PAT003["hdl"],
            hscrp=PAT003["hscrp"],
            family_history_premature_mi=PAT003["family_history_premature_mi"],
            current_smoker=PAT003["current_smoker"],
        )
        assert "Ridker" in r["citation"]


class TestFraminghamScore:
    """Framingham Risk Score for PAT003 values."""

    def test_framingham_pat003_within_tolerance(self):
        r = calculate_framingham_women(
            age=PAT003["age"],
            total_cholesterol=PAT003["total_cholesterol"],
            hdl=PAT003["hdl"],
            systolic_bp=PAT003["systolic_bp"],
            bp_treated=PAT003["bp_treated"],
            current_smoker=PAT003["current_smoker"],
            diabetes=PAT003["diabetes"],
        )
        assert abs(r["risk_10yr_percent"] - 12.4) < 3.0, (
            f"Framingham {r['risk_10yr_percent']}% not within +/-3% of 12.4%"
        )

    def test_framingham_intermediate_category(self):
        r = calculate_framingham_women(
            age=PAT003["age"],
            total_cholesterol=PAT003["total_cholesterol"],
            hdl=PAT003["hdl"],
            systolic_bp=PAT003["systolic_bp"],
            bp_treated=PAT003["bp_treated"],
            current_smoker=PAT003["current_smoker"],
            diabetes=PAT003["diabetes"],
        )
        assert r["risk_category"] == "intermediate"


class TestASCVDScore:
    """ASCVD Pooled Cohort Equation for PAT003 values."""

    def test_ascvd_pat003_within_tolerance(self):
        r = calculate_ascvd_women_white(
            age=PAT003["age"],
            total_cholesterol=PAT003["total_cholesterol"],
            hdl=PAT003["hdl"],
            systolic_bp=PAT003["systolic_bp"],
            bp_treated=PAT003["bp_treated"],
            current_smoker=PAT003["current_smoker"],
            diabetes=PAT003["diabetes"],
        )
        assert abs(r["risk_10yr_percent"] - 11.8) < 3.0, (
            f"ASCVD {r['risk_10yr_percent']}% not within +/-3% of 11.8%"
        )

    def test_ascvd_intermediate_category(self):
        r = calculate_ascvd_women_white(
            age=PAT003["age"],
            total_cholesterol=PAT003["total_cholesterol"],
            hdl=PAT003["hdl"],
            systolic_bp=PAT003["systolic_bp"],
            bp_treated=PAT003["bp_treated"],
            current_smoker=PAT003["current_smoker"],
            diabetes=PAT003["diabetes"],
        )
        assert r["risk_category"] == "intermediate"


class TestBiomarkerClassification:
    """Biomarker panel interpretation."""

    def test_ldl_near_optimal(self):
        assert classify_biomarker("ldl_mg_dl", 118) == "near_optimal"

    def test_hdl_acceptable(self):
        assert classify_biomarker("hdl_mg_dl", 58) == "acceptable"

    def test_hscrp_moderate(self):
        assert classify_biomarker("hscrp_mg_l", 1.8) == "moderate_cvd_risk"

    def test_glucose_normal(self):
        assert classify_biomarker("fasting_glucose_mg_dl", 98) == "normal"

    def test_hba1c_normal(self):
        assert classify_biomarker("hba1c_percent", 5.6) == "normal"


class TestAssessBiomarkerPanel:
    """Tool: assess_biomarker_panel."""

    @pytest.mark.asyncio
    async def test_pat003_panel(self):
        r = await _assess_biomarker_panel_impl(
            ldl_mg_dl=118, hdl_mg_dl=58, hscrp_mg_l=1.8,
        )
        assert r["status"] == "success"
        assert r["biomarkers"]["ldl_mg_dl"]["category"] == "near_optimal"

    @pytest.mark.asyncio
    async def test_dry_run_flag(self):
        r = await _assess_biomarker_panel_impl(ldl_mg_dl=118)
        assert "dry_run" in r


class TestLpaStatus:
    """Tool: assess_lpa_status."""

    @pytest.mark.asyncio
    async def test_lpa_none_recommends_testing(self):
        r = await _assess_lpa_status_impl(lpa_mg_dl=None)
        assert r["status"] == "success"
        assert r["lpa_measured"] is False
        assert "order" in r["recommendation"].lower() or "measure" in r["recommendation"].lower()

    @pytest.mark.asyncio
    async def test_lpa_high_category(self):
        r = await _assess_lpa_status_impl(lpa_mg_dl=75)
        assert r["status"] == "success"
        assert r["category"] == "high"
        assert any("statin" in imp.lower() for imp in r["implications"])


class TestGeneratePreventiveReport:
    """Tool: generate_preventive_report."""

    @pytest.mark.asyncio
    async def test_report_has_required_keys(self):
        r = await _generate_preventive_report_impl()
        for key in (
            "executive_summary", "risk_scores", "priority_actions",
            "monitoring_schedule", "lifestyle_recommendations", "disclaimer",
        ):
            assert key in r, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_dry_run_flag(self):
        r = await _generate_preventive_report_impl()
        assert r["dry_run"] is True


class TestGetLifestyleEvidence:
    """Tool: get_lifestyle_evidence."""

    @pytest.mark.asyncio
    async def test_returns_recommendations(self):
        r = await _get_lifestyle_evidence_impl()
        assert r["status"] == "success"
        assert r["count"] >= 5

    @pytest.mark.asyncio
    async def test_dry_run_flag(self):
        r = await _get_lifestyle_evidence_impl()
        assert r["dry_run"] is True


class TestCalculateCVDRiskScores:
    """Tool: calculate_cvd_risk_scores."""

    @pytest.mark.asyncio
    async def test_all_three_scores_present(self):
        r = await _calculate_cvd_risk_scores_impl()
        assert "reynolds" in r
        assert "framingham" in r
        assert "ascvd" in r

    @pytest.mark.asyncio
    async def test_all_intermediate(self):
        r = await _calculate_cvd_risk_scores_impl()
        assert r["reynolds"]["risk_category"] == "intermediate"
        assert r["framingham"]["risk_category"] == "intermediate"
        assert r["ascvd"]["risk_category"] == "intermediate"

    @pytest.mark.asyncio
    async def test_dry_run_flag(self):
        r = await _calculate_cvd_risk_scores_impl()
        assert r["dry_run"] is True
