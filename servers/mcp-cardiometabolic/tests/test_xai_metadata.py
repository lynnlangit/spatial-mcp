"""XAI metadata tests: per-tool presence, confidence logic, report integration."""

import pytest

from mcp_cardiometabolic.server import (
    _assess_biomarker_panel_impl,
    _calculate_cvd_risk_scores_impl,
    _assess_lpa_status_impl,
    _assess_pregnancy_complication_cv_risk_impl,
    _interpret_lipid_pattern_impl,
    _calculate_fh_clinical_score_impl,
    _assess_renal_drug_constraints_impl,
    _calculate_lipid_treatment_targets_impl,
    _assess_postcovid_cv_risk_impl,
    _generate_preventive_report_impl,
)


XAI_REQUIRED_KEYS = {
    "confidence_level", "confidence_note", "key_drivers",
    "guideline_version", "evidence_grade", "counterfactual",
}


def assert_xai_valid(result: dict, tool_name: str):
    """Helper: assert xai_metadata is present and well-formed."""
    assert "xai_metadata" in result, f"{tool_name}: missing xai_metadata"
    xai = result["xai_metadata"]
    for key in XAI_REQUIRED_KEYS:
        assert key in xai, f"{tool_name}: xai_metadata missing key '{key}'"
    assert xai["confidence_level"] in ("high", "moderate", "low"), \
        f"{tool_name}: invalid confidence_level '{xai['confidence_level']}'"
    assert isinstance(xai["key_drivers"], list), \
        f"{tool_name}: key_drivers must be a list"
    non_null = [d for d in xai["key_drivers"] if d is not None]
    assert 1 <= len(non_null) <= 3, \
        f"{tool_name}: key_drivers must have 1-3 non-null items, got {len(non_null)}"


# ── Per-tool xai_metadata presence ──────────────────────────────────────────


class TestXaiPresence:
    """Every tool must return valid xai_metadata."""

    @pytest.mark.asyncio
    async def test_xai_assess_biomarker_panel(self):
        result = await _assess_biomarker_panel_impl(
            fasting_glucose_mg_dl=98, ldl_mg_dl=118, apob_mg_dl=95,
        )
        assert_xai_valid(result, "assess_biomarker_panel")

    @pytest.mark.asyncio
    async def test_xai_calculate_cvd_risk_scores(self):
        result = await _calculate_cvd_risk_scores_impl()
        assert_xai_valid(result, "calculate_cvd_risk_scores")

    @pytest.mark.asyncio
    async def test_xai_assess_lpa_status_unmeasured(self):
        result = await _assess_lpa_status_impl(lpa_mg_dl=None)
        assert_xai_valid(result, "assess_lpa_status (unmeasured)")

    @pytest.mark.asyncio
    async def test_xai_assess_lpa_status_measured(self):
        result = await _assess_lpa_status_impl(lpa_mg_dl=35)
        assert_xai_valid(result, "assess_lpa_status (measured)")

    @pytest.mark.asyncio
    async def test_xai_pregnancy_complication_cv_risk(self):
        result = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003", complications=["preeclampsia"],
        )
        assert_xai_valid(result, "assess_pregnancy_complication_cv_risk")

    @pytest.mark.asyncio
    async def test_xai_interpret_lipid_pattern(self):
        result = await _interpret_lipid_pattern_impl(
            patient_id="PAT003", ldl_cholesterol=205, triglycerides=212,
            total_cholesterol=313, hdl_cholesterol=68, apob=140,
        )
        assert_xai_valid(result, "interpret_lipid_pattern")

    @pytest.mark.asyncio
    async def test_xai_calculate_fh_clinical_score(self):
        result = await _calculate_fh_clinical_score_impl(
            patient_id="PAT003", ldl_cholesterol_mgdl=205,
            family_hx_premature_cvd=True,
        )
        assert_xai_valid(result, "calculate_fh_clinical_score")

    @pytest.mark.asyncio
    async def test_xai_assess_renal_drug_constraints(self):
        result = await _assess_renal_drug_constraints_impl(
            patient_id="PAT003", egfr=68, functional_kidney_count=1,
        )
        assert_xai_valid(result, "assess_renal_drug_constraints")

    @pytest.mark.asyncio
    async def test_xai_calculate_lipid_treatment_targets(self):
        result = await _calculate_lipid_treatment_targets_impl(
            patient_id="PAT003", current_ldl=205,
            risk_tier="high", fh_status="possible",
        )
        assert_xai_valid(result, "calculate_lipid_treatment_targets")

    @pytest.mark.asyncio
    async def test_xai_assess_postcovid_cv_risk(self):
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="PAT003", severity="hospitalized",
            baseline_risk_tier="intermediate",
        )
        assert_xai_valid(result, "assess_postcovid_cv_risk")


# ── Confidence level logic ──────────────────────────────────────────────────


class TestConfidenceLogic:
    """Confidence level must follow spec for each scenario."""

    @pytest.mark.asyncio
    async def test_friedewald_low_confidence_lipid_pattern(self):
        """TG >200 with calculated LDL -> low confidence."""
        result = await _interpret_lipid_pattern_impl(
            patient_id="PAT003", ldl_cholesterol=205, triglycerides=212,
            ldl_measured_directly=False,
        )
        assert result["xai_metadata"]["confidence_level"] == "low", \
            "TG >200 with calculated LDL must produce low confidence"

    @pytest.mark.asyncio
    async def test_direct_ldl_high_confidence(self):
        """Direct LDL measurement with complete panel -> high confidence."""
        result = await _interpret_lipid_pattern_impl(
            patient_id="SYNTH01", ldl_cholesterol=150, triglycerides=120,
            hdl_cholesterol=55, total_cholesterol=220, ldl_measured_directly=True,
        )
        assert result["xai_metadata"]["confidence_level"] == "high"

    @pytest.mark.asyncio
    async def test_single_kidney_moderate_confidence(self):
        """Single kidney -> renal drug constraints confidence 'moderate'."""
        result = await _assess_renal_drug_constraints_impl(
            patient_id="PAT003", egfr=68, functional_kidney_count=1,
        )
        assert result["xai_metadata"]["confidence_level"] == "moderate"

    @pytest.mark.asyncio
    async def test_two_kidneys_high_confidence(self):
        """Two kidneys -> renal drug constraints confidence 'high'."""
        result = await _assess_renal_drug_constraints_impl(
            patient_id="SYNTH01", egfr=68, functional_kidney_count=2,
        )
        assert result["xai_metadata"]["confidence_level"] == "high"

    @pytest.mark.asyncio
    async def test_postcovid_hospitalized_moderate(self):
        """Hospitalized COVID -> moderate confidence."""
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="PAT003", severity="hospitalized",
            baseline_risk_tier="intermediate",
        )
        assert result["xai_metadata"]["confidence_level"] == "moderate"

    @pytest.mark.asyncio
    async def test_postcovid_mild_low(self):
        """Mild COVID -> low confidence."""
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="SYNTH01", severity="mild",
            baseline_risk_tier="low",
        )
        assert result["xai_metadata"]["confidence_level"] == "low"

    @pytest.mark.asyncio
    async def test_preeclampsia_alone_high(self):
        """Preeclampsia without COVID -> high confidence."""
        result = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003", complications=["preeclampsia"],
            covid_severe_history=False,
        )
        assert result["xai_metadata"]["confidence_level"] == "high"

    @pytest.mark.asyncio
    async def test_preeclampsia_plus_covid_moderate(self):
        """Preeclampsia + COVID double injury -> moderate confidence."""
        result = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003", complications=["preeclampsia"],
            covid_severe_history=True,
        )
        assert result["xai_metadata"]["confidence_level"] == "moderate"

    @pytest.mark.asyncio
    async def test_lipid_treatment_targets_always_moderate(self):
        """Lipid treatment targets are always moderate (population averages)."""
        result = await _calculate_lipid_treatment_targets_impl(
            patient_id="PAT003", current_ldl=118,
            risk_tier="intermediate", fh_status="unlikely",
        )
        assert result["xai_metadata"]["confidence_level"] == "moderate"

    @pytest.mark.asyncio
    async def test_lpa_measured_high_confidence(self):
        """Directly measured Lp(a) -> high confidence."""
        result = await _assess_lpa_status_impl(lpa_mg_dl=35)
        assert result["xai_metadata"]["confidence_level"] == "high"


# ── Report XAI integration ──────────────────────────────────────────────────


class TestReportXaiIntegration:
    """generate_preventive_report must produce XAI-enhanced output."""

    @pytest.mark.asyncio
    async def test_report_has_evidence_strength_summary(self):
        """Report must include evidence_strength_summary field."""
        result = await _generate_preventive_report_impl()
        assert "evidence_strength_summary" in result, \
            "generate_preventive_report must include evidence_strength_summary"
        summary = result["evidence_strength_summary"]
        assert "table_text" in summary
        assert "confidence_counts" in summary
        assert set(summary["confidence_counts"].keys()) == {"high", "moderate", "low"}

    @pytest.mark.asyncio
    async def test_report_confidence_counts_sum_positive(self):
        """Total confidence counts must be > 0."""
        result = await _generate_preventive_report_impl()
        counts = result["evidence_strength_summary"]["confidence_counts"]
        total = sum(counts.values())
        assert total > 0, "At least one tool must contribute to the report"

    @pytest.mark.asyncio
    async def test_report_action_required_logic(self):
        """action_required is True iff any low confidence items exist."""
        result = await _generate_preventive_report_impl()
        summary = result["evidence_strength_summary"]
        if summary["confidence_counts"]["low"] > 0:
            assert summary["action_required"] is True
        else:
            assert summary["action_required"] is False

    @pytest.mark.asyncio
    async def test_report_evidence_table_non_empty(self):
        """Evidence table text must be a non-empty string."""
        result = await _generate_preventive_report_impl()
        table_text = result["evidence_strength_summary"]["table_text"]
        assert isinstance(table_text, str) and len(table_text) > 100, \
            "Evidence table text should be a substantial string"

    @pytest.mark.asyncio
    async def test_report_has_xai_metadata_moderate(self):
        """Report itself must have xai_metadata with confidence_level 'moderate'."""
        result = await _generate_preventive_report_impl()
        assert "xai_metadata" in result
        assert result["xai_metadata"]["confidence_level"] == "moderate"
