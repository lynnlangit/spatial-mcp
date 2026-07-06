"""Phase A tests: assess_biomarker_panel fix + interpret_lipid_pattern + calculate_fh_clinical_score."""

import pytest

from mcp_cardiometabolic.server import (
    _assess_biomarker_panel_impl,
    _interpret_lipid_pattern_impl,
    _calculate_fh_clinical_score_impl,
)


# ── assess_biomarker_panel fixes ─────────────────────────────────────────────


class TestBiomarkerPanelBidirectional:
    """Bidirectional range flags, ApoB, Non-HDL."""

    @pytest.mark.asyncio
    async def test_flags_low_glucose(self):
        """Glucose 60 must be flagged as low_hypoglycemia, not normal."""
        r = await _assess_biomarker_panel_impl(fasting_glucose_mg_dl=60)
        cat = r["biomarkers"]["fasting_glucose_mg_dl"]["category"]
        assert cat == "low_hypoglycemia", f"Expected low_hypoglycemia, got: {cat}"
        assert any("low" in f for f in r["flags"]), "Low glucose not in flags"

    @pytest.mark.asyncio
    async def test_flags_high_glucose(self):
        """High glucose must still be flagged."""
        r = await _assess_biomarker_panel_impl(fasting_glucose_mg_dl=130)
        cat = r["biomarkers"]["fasting_glucose_mg_dl"]["category"]
        assert cat == "diabetes"

    @pytest.mark.asyncio
    async def test_normal_glucose_not_flagged(self):
        """Glucose 85 should be normal, not flagged."""
        r = await _assess_biomarker_panel_impl(fasting_glucose_mg_dl=85)
        cat = r["biomarkers"]["fasting_glucose_mg_dl"]["category"]
        assert cat == "normal"
        assert not any("fasting_glucose" in f for f in r["flags"])

    @pytest.mark.asyncio
    async def test_apob_above_target(self):
        """ApoB 140 should be significantly_elevated."""
        r = await _assess_biomarker_panel_impl(apob_mg_dl=140)
        cat = r["biomarkers"]["apob_mg_dl"]["category"]
        assert cat == "significantly_elevated"
        assert "risk_tier_context" in r["biomarkers"]["apob_mg_dl"]

    @pytest.mark.asyncio
    async def test_apob_at_target(self):
        """ApoB 75 should be at_target_high_risk."""
        r = await _assess_biomarker_panel_impl(apob_mg_dl=75)
        cat = r["biomarkers"]["apob_mg_dl"]["category"]
        assert cat == "at_target_high_risk"

    @pytest.mark.asyncio
    async def test_non_hdl_computed(self):
        """Non-HDL computed from TC - HDL when not provided."""
        r = await _assess_biomarker_panel_impl(
            total_cholesterol_mg_dl=313, hdl_mg_dl=68,
        )
        non_hdl = r["biomarkers"]["non_hdl_cholesterol_mg_dl"]
        assert non_hdl["value"] == 245
        assert non_hdl["category"] == "very_high"
        assert "therapeutic_target_note" in non_hdl

    @pytest.mark.asyncio
    async def test_non_hdl_direct_input(self):
        """Non-HDL passed directly should be used as-is."""
        r = await _assess_biomarker_panel_impl(non_hdl_cholesterol_mg_dl=125)
        assert r["biomarkers"]["non_hdl_cholesterol_mg_dl"]["value"] == 125
        assert r["biomarkers"]["non_hdl_cholesterol_mg_dl"]["category"] == "normal"


# ── interpret_lipid_pattern ──────────────────────────────────────────────────


class TestInterpretLipidPattern:
    """Tool: interpret_lipid_pattern."""

    @pytest.mark.asyncio
    async def test_mixed_dyslipidemia(self):
        """PAT003's panel: LDL 205 + TG 212 = mixed_dyslipidemia."""
        r = await _interpret_lipid_pattern_impl(
            patient_id="PAT003",
            ldl_cholesterol=205,
            total_cholesterol=313,
            hdl_cholesterol=68,
            triglycerides=212,
            apob=140,
            ldl_measured_directly=False,
            patient_risk_tier="high",
        )
        assert r["pattern"] == "mixed_dyslipidemia"
        assert r["friedewald_ldl_valid"] is False
        assert "200" in (r.get("friedewald_note") or "")

    @pytest.mark.asyncio
    async def test_concordant_elevated(self):
        """Both ApoB and LDL elevated → concordant_elevated."""
        r = await _interpret_lipid_pattern_impl(
            patient_id="PAT003",
            ldl_cholesterol=205,
            apob=140,
            patient_risk_tier="high",
        )
        assert r["apob_ldl_concordance"]["status"] == "concordant_elevated"

    @pytest.mark.asyncio
    async def test_friedewald_valid_low_tg(self):
        """TG 120 → Friedewald should be valid."""
        r = await _interpret_lipid_pattern_impl(
            patient_id="SYNTH01",
            ldl_cholesterol=150,
            triglycerides=120,
            ldl_measured_directly=False,
        )
        assert r["friedewald_ldl_valid"] is True

    @pytest.mark.asyncio
    async def test_non_hdl_computed(self):
        """Non-HDL computed from TC=313, HDL=68 → 245."""
        r = await _interpret_lipid_pattern_impl(
            patient_id="PAT003",
            total_cholesterol=313,
            hdl_cholesterol=68,
            ldl_cholesterol=205,
            triglycerides=212,
        )
        assert r["non_hdl_cholesterol"] == 245

    @pytest.mark.asyncio
    async def test_isolated_hypercholesterolemia(self):
        """LDL elevated + TG normal = isolated_hypercholesterolemia."""
        r = await _interpret_lipid_pattern_impl(
            patient_id="SYNTH01",
            ldl_cholesterol=200,
            triglycerides=100,
            patient_risk_tier="high",
        )
        assert r["pattern"] == "isolated_hypercholesterolemia"

    @pytest.mark.asyncio
    async def test_normal_pattern(self):
        """All values within targets = normal_pattern."""
        r = await _interpret_lipid_pattern_impl(
            patient_id="SYNTH01",
            ldl_cholesterol=60,
            triglycerides=100,
            hdl_cholesterol=65,
            patient_risk_tier="high",
        )
        assert r["pattern"] == "normal_pattern"

    @pytest.mark.asyncio
    async def test_discordant_apob_high(self):
        """ApoB high but LDL normal → discordant_apob_high."""
        r = await _interpret_lipid_pattern_impl(
            patient_id="SYNTH01",
            ldl_cholesterol=60,
            apob=100,
            patient_risk_tier="high",
        )
        assert r["apob_ldl_concordance"]["status"] == "discordant_apob_high"

    @pytest.mark.asyncio
    async def test_dry_run_flag_set(self):
        """dry_run flag reflects CARDIOMETABOLIC_DRY_RUN (pure computation, no fixture)."""
        r = await _interpret_lipid_pattern_impl(
            patient_id="PAT003",
            ldl_cholesterol=205,
            triglycerides=212,
            total_cholesterol=313,
            hdl_cholesterol=68,
        )
        assert r["dry_run"] is True
        assert r["pattern"] == "mixed_dyslipidemia"


# ── calculate_fh_clinical_score ──────────────────────────────────────────────


class TestCalculateFhClinicalScore:
    """Tool: calculate_fh_clinical_score (DLCN scoring)."""

    @pytest.mark.asyncio
    async def test_pat003_possible_fh(self):
        """PAT003: LDL 205 + family hx premature CVD = DLCN 4 = Possible FH."""
        r = await _calculate_fh_clinical_score_impl(
            patient_id="PAT003",
            ldl_cholesterol_mgdl=205,
            family_hx_premature_cvd=True,
            genetic_test_performed=True,
            genetic_test_type="population_screening",
            genetic_test_variants_tested="APOB c.10580G>A and c.10579C>T only",
            genetic_test_result="negative",
            causative_mutation_identified=False,
        )
        assert r["dlcn_score"] == 4
        assert r["dlcn_tier"] == "Possible FH"
        assert r["diagnostic_panel_recommended"] is True

    @pytest.mark.asyncio
    async def test_negative_screening_does_not_rule_out(self):
        """Negative population screening must trigger a warning."""
        r = await _calculate_fh_clinical_score_impl(
            patient_id="PAT003",
            ldl_cholesterol_mgdl=205,
            family_hx_premature_cvd=True,
            genetic_test_performed=True,
            genetic_test_type="population_screening",
            genetic_test_result="negative",
            causative_mutation_identified=False,
        )
        interp = r.get("genetic_test_interpretation", {})
        assert interp is not None
        result_text = interp.get("result", "").lower()
        assert "does not rule out" in result_text or "screening" in result_text

    @pytest.mark.asyncio
    async def test_definite_fh_with_mutation(self):
        """Causative mutation → Definite FH (score >=9)."""
        r = await _calculate_fh_clinical_score_impl(
            patient_id="SYNTH02",
            ldl_cholesterol_mgdl=310,
            family_hx_premature_cvd=True,
            tendon_xanthomas=True,
            causative_mutation_identified=True,
        )
        assert r["dlcn_score"] >= 9
        assert r["dlcn_tier"] == "Definite FH"
        assert r["cascade_screening_recommended"] is True

    @pytest.mark.asyncio
    async def test_unlikely_fh_low_ldl(self):
        """Low LDL + no family history = Unlikely FH."""
        r = await _calculate_fh_clinical_score_impl(
            patient_id="SYNTH03",
            ldl_cholesterol_mgdl=100,
        )
        assert r["dlcn_score"] < 3
        assert r["dlcn_tier"] == "Unlikely FH"
        assert r["diagnostic_panel_recommended"] is False

    @pytest.mark.asyncio
    async def test_pcsk9_note_present_for_possible_fh(self):
        """PCSK9 eligibility note should appear for Possible FH and above."""
        r = await _calculate_fh_clinical_score_impl(
            patient_id="PAT003",
            ldl_cholesterol_mgdl=205,
            family_hx_premature_cvd=True,
        )
        assert r["pcsk9_inhibitor_eligibility_note"] is not None
        assert len(r["pcsk9_inhibitor_eligibility_note"]) > 50

    @pytest.mark.asyncio
    async def test_guideline_references(self):
        """Guideline references should be present."""
        r = await _calculate_fh_clinical_score_impl(
            patient_id="PAT003",
            ldl_cholesterol_mgdl=205,
        )
        assert len(r["guideline_references"]) == 3
        assert any("EAS" in ref for ref in r["guideline_references"])

    @pytest.mark.asyncio
    async def test_score_components_present(self):
        """Score components should break down by category."""
        r = await _calculate_fh_clinical_score_impl(
            patient_id="PAT003",
            ldl_cholesterol_mgdl=205,
            family_hx_premature_cvd=True,
        )
        comp = r["score_components"]
        assert comp["family_history"] == 1
        assert comp["ldl_cholesterol"] == 3  # LDL 205 → 5.3 mmol/L → 3 points
        assert "ldl_mmol" in comp
