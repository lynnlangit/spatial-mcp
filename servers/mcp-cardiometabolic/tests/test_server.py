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
    _search_cvd_prs_scores_impl,
    _calculate_cvd_prs_impl,
    _interpret_cvd_prs_percentile_impl,
    _assess_pregnancy_complication_cv_risk_impl,
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


class TestSearchCvdPrsScores:
    """Tool: search_cvd_prs_scores."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_fixture(self):
        r = await _search_cvd_prs_scores_impl(trait="coronary artery disease")
        assert r["dry_run"] is True
        assert r["scores"][0]["pgs_id"] == "PGS000018"
        assert r["total_found"] == 2

    @pytest.mark.asyncio
    async def test_trait_echoed(self):
        r = await _search_cvd_prs_scores_impl(trait="atrial fibrillation")
        assert r["trait_queried"] == "atrial fibrillation"


class TestCalculateCvdPrs:
    """Tool: calculate_cvd_prs."""

    @pytest.mark.asyncio
    async def test_no_germline_file(self):
        r = await _calculate_cvd_prs_impl(
            patient_id="PAT003",
            genotype_file_path="/nonexistent/PAT003_germline.txt",
            pgs_id="PGS000018",
        )
        assert r["status"] == "NO_GERMLINE_GENOTYPE"
        assert "Somatic VCFs" in r["action_required"]

    @pytest.mark.asyncio
    async def test_dry_run_synthetic(self):
        r = await _calculate_cvd_prs_impl(
            patient_id="PAT003",
            genotype_file_path="SYNTHETIC",
            pgs_id="PGS000018",
        )
        assert r["status"] == "CALCULATED"
        assert r["dry_run"] is True
        assert r["raw_score"] == 0.847
        assert r["match_fraction"] == 0.089


class TestInterpretCvdPrsPercentile:
    """Tool: interpret_cvd_prs_percentile."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_percentile(self):
        r = await _interpret_cvd_prs_percentile_impl(
            patient_id="PAT003",
            pgs_id="PGS000018",
            raw_score=0.847,
        )
        assert r["percentile"] == 73.2
        assert r["risk_tier"] == "Intermediate"
        assert r["dry_run"] is True

    @pytest.mark.asyncio
    async def test_has_reference(self):
        r = await _interpret_cvd_prs_percentile_impl(
            patient_id="PAT003",
            pgs_id="PGS000018",
            raw_score=0.847,
        )
        assert "Khera" in r["reference"]


class TestAssessPregnancyComplicationCvRisk:
    """Tool: assess_pregnancy_complication_cv_risk."""

    @pytest.mark.asyncio
    async def test_preeclampsia_high_risk(self):
        r = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003",
            complications=["preeclampsia"],
            age_at_complication=32,
            num_affected_pregnancies=1,
        )
        assert r["risk_enhancement"]["category"] == "High"
        assert r["risk_enhancement"]["cad_multiplier"] == 2.0
        assert r["risk_enhancement"]["stroke_multiplier"] == 2.0
        assert "preeclampsia" in r["complications_recognized"]
        assert len(r["screening_recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_unknown_complication(self):
        r = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003",
            complications=["morning_sickness"],
        )
        assert r["complications_recognized"] == []
        assert r["risk_enhancement"]["category"] == "None"
        assert r["risk_enhancement"]["cad_multiplier"] == 1.0

    @pytest.mark.asyncio
    async def test_multiple_complications_additive(self):
        r = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003",
            complications=["preeclampsia", "gestational_diabetes"],
        )
        assert r["risk_enhancement"]["category"] == "High"
        # Additive: (2.0-1) + (1.7-1) + 1.0 = 2.7
        assert r["risk_enhancement"]["cad_multiplier"] == 2.7
        assert len(r["complications_recognized"]) == 2

    @pytest.mark.asyncio
    async def test_cap_applied(self):
        r = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003",
            complications=[
                "preeclampsia", "eclampsia", "gestational_diabetes",
                "gestational_hypertension",
            ],
        )
        # Sum would exceed 3.5 cap
        assert r["risk_enhancement"]["cad_multiplier"] <= 3.5
        assert r["risk_enhancement"]["stroke_multiplier"] <= 3.5

    @pytest.mark.asyncio
    async def test_guideline_sources_present(self):
        r = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003",
            complications=["preeclampsia"],
        )
        assert len(r["guideline_sources"]) == 3
        assert any("AHA" in s for s in r["guideline_sources"])
        assert any("ESC" in s for s in r["guideline_sources"])
