"""Phase B tests: renal drug constraints, lipid treatment targets, post-COVID CV risk, pregnancy update."""

import pytest

from mcp_cardiometabolic.server import (
    _assess_renal_drug_constraints_impl,
    _calculate_lipid_treatment_targets_impl,
    _assess_postcovid_cv_risk_impl,
    _assess_pregnancy_complication_cv_risk_impl,
)


# ── assess_renal_drug_constraints ────────────────────────────────────────────


class TestRenalDrugConstraints:
    """Tool: assess_renal_drug_constraints."""

    @pytest.mark.asyncio
    async def test_single_kidney_egfr68(self):
        """PAT003: eGFR 68, single kidney — atorvastatin preferred, dabigatran avoided."""
        result = await _assess_renal_drug_constraints_impl(
            patient_id="PAT003", egfr=68, functional_kidney_count=1,
        )
        assert result["single_kidney_modifier_applied"] is True
        assert result["egfr_stage"] == "G2"

        statins = result["assessments"]["statins"]
        assert any("atorvastatin" in p.lower() for p in statins["preferred"]), \
            "Atorvastatin should be in preferred statins"

        anticoag = result["assessments"]["anticoagulants"]
        avoid_list = " ".join(anticoag.get("avoid", [])).lower()
        assert "dabigatran" in avoid_list, "Dabigatran should be in avoid list"

        preferred_anticoag = " ".join(anticoag.get("preferred", [])).lower()
        assert "apixaban" in preferred_anticoag, "Apixaban should be preferred anticoagulant"

    @pytest.mark.asyncio
    async def test_nsaids_contraindicated_single_kidney(self):
        """NSAIDs must be contraindicated for single-kidney patient."""
        result = await _assess_renal_drug_constraints_impl(
            patient_id="PAT003", egfr=68, functional_kidney_count=1,
        )
        nsaids = result["assessments"].get("nsaids", {})
        status = nsaids.get("class_status", "").lower()
        assert "contraindicated" in status, \
            f"NSAIDs should be contraindicated for single kidney, got: {status}"

    @pytest.mark.asyncio
    async def test_pcsk9_safe_any_egfr(self):
        """PCSK9 inhibitors have no renal clearance — safe at any eGFR."""
        result = await _assess_renal_drug_constraints_impl(
            patient_id="SYNTH01", egfr=20, functional_kidney_count=2,
        )
        pcsk9 = result["assessments"].get("pcsk9_inhibitors", {})
        assert "contraindicated" not in pcsk9.get("class_status", "").lower(), \
            "PCSK9 inhibitors should not be contraindicated at any eGFR"

    @pytest.mark.asyncio
    async def test_metformin_safe_egfr68(self):
        """Metformin is safe at eGFR 68."""
        result = await _assess_renal_drug_constraints_impl(
            patient_id="PAT003", egfr=68, functional_kidney_count=1,
        )
        metformin = result["assessments"].get("metformin", {})
        status = metformin.get("class_status", "").lower()
        assert "safe" in status or "acceptable" in status, \
            f"Metformin should be safe at eGFR 68, got: {status}"

    @pytest.mark.asyncio
    async def test_egfr_stage_g4(self):
        """eGFR 20 → G4 stage."""
        result = await _assess_renal_drug_constraints_impl(
            patient_id="SYNTH01", egfr=20, functional_kidney_count=2,
        )
        assert result["egfr_stage"] == "G4"
        assert result["single_kidney_modifier_applied"] is False

    @pytest.mark.asyncio
    async def test_metformin_contraindicated_low_egfr(self):
        """Metformin contraindicated at eGFR <30."""
        result = await _assess_renal_drug_constraints_impl(
            patient_id="SYNTH01", egfr=25, functional_kidney_count=2,
        )
        metformin = result["assessments"].get("metformin", {})
        assert "contraindicated" in metformin.get("class_status", "").lower()


# ── calculate_lipid_treatment_targets ────────────────────────────────────────


class TestLipidTreatmentTargets:
    """Tool: calculate_lipid_treatment_targets."""

    @pytest.mark.asyncio
    async def test_fh_upgrade(self):
        """Possible FH + high risk tier → upgrade to very_high → LDL target 55."""
        result = await _calculate_lipid_treatment_targets_impl(
            patient_id="PAT003",
            current_ldl=205,
            risk_tier="high",
            fh_status="possible",
        )
        assert result["fh_risk_upgrade_applied"] is True
        assert result["effective_risk_tier"] == "very_high"
        assert result["targets"]["ldl"] == 55

    @pytest.mark.asyncio
    async def test_pathway_pat003(self):
        """PAT003: LDL 205 with very_high target → multi-step pathway reaching target."""
        result = await _calculate_lipid_treatment_targets_impl(
            patient_id="PAT003",
            current_ldl=205,
            current_apob=140,
            risk_tier="high",
            fh_status="possible",
            currently_on_statin=False,
            renal_constraint=True,
        )
        pathway = result["therapy_pathway"]
        assert len(pathway) >= 2, "Should require at least 2 steps"
        final_step = pathway[-1]
        assert final_step["target_reached"] is True, "Final step must reach the target"

    @pytest.mark.asyncio
    async def test_renal_constraint_prefers_atorvastatin(self):
        """When renal_constraint=True, atorvastatin should be explicitly mentioned."""
        result = await _calculate_lipid_treatment_targets_impl(
            patient_id="PAT003",
            current_ldl=205,
            risk_tier="high",
            fh_status="possible",
            renal_constraint=True,
        )
        statin_note = result.get("statin_preference_note", "") or ""
        assert "atorvastatin" in statin_note.lower(), \
            "Atorvastatin preference should be flagged when renal_constraint=True"

    @pytest.mark.asyncio
    async def test_low_risk_ldl130(self):
        """Low risk patient → LDL target 130."""
        result = await _calculate_lipid_treatment_targets_impl(
            patient_id="SYNTH01",
            current_ldl=160,
            risk_tier="low",
            fh_status="unlikely",
        )
        assert result["targets"]["ldl"] == 130

    @pytest.mark.asyncio
    async def test_no_fh_upgrade_for_unlikely(self):
        """FH unlikely should not trigger risk upgrade."""
        result = await _calculate_lipid_treatment_targets_impl(
            patient_id="SYNTH01",
            current_ldl=160,
            risk_tier="intermediate",
            fh_status="unlikely",
        )
        assert result["fh_risk_upgrade_applied"] is False
        assert result["effective_risk_tier"] == "intermediate"

    @pytest.mark.asyncio
    async def test_guideline_references_present(self):
        """Guideline references should be present."""
        result = await _calculate_lipid_treatment_targets_impl(
            patient_id="PAT003",
            current_ldl=205,
            risk_tier="high",
        )
        assert len(result["guideline_references"]) == 4
        assert any("ACC" in ref for ref in result["guideline_references"])


# ── assess_postcovid_cv_risk ─────────────────────────────────────────────────


class TestPostcovidCvRisk:
    """Tool: assess_postcovid_cv_risk."""

    @pytest.mark.asyncio
    async def test_pat003_tier_upgrade(self):
        """PAT003: hospitalized COVID + intermediate baseline → should upgrade to high."""
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="PAT003",
            severity="hospitalized",
            year_of_infection=2020,
            bp_crisis_during_covid=True,
            new_prediabetes_post_covid=True,
            adverse_pregnancy_outcome_history=True,
            baseline_risk_tier="intermediate",
        )
        assert result["adjusted_risk_tier"] in ("high", "very_high"), \
            f"Expected tier upgrade from intermediate, got: {result['adjusted_risk_tier']}"
        assert result["risk_tier_changed"] is True

    @pytest.mark.asyncio
    async def test_double_endothelial_injury(self):
        """Preeclampsia + severe COVID → double endothelial injury flag."""
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="PAT003",
            severity="hospitalized",
            adverse_pregnancy_outcome_history=True,
            baseline_risk_tier="intermediate",
        )
        assert result["double_endothelial_injury_present"] is True
        mechanisms = [m["mechanism"] for m in result["mechanisms_flagged"] if m["present"]]
        assert any("double endothelial" in m.lower() for m in mechanisms)

    @pytest.mark.asyncio
    async def test_workup_includes_echo_for_severe(self):
        """Severe/hospitalized COVID → echocardiogram in workup."""
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="PAT003",
            severity="hospitalized",
            baseline_risk_tier="intermediate",
        )
        tests = [w["test"].lower() for w in result["cardiac_workup_recommended"]]
        assert any("echo" in t for t in tests), "Echo should be in workup for hospitalized COVID"

    @pytest.mark.asyncio
    async def test_mild_no_tier_upgrade(self):
        """Mild COVID without complications → no tier upgrade."""
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="SYNTH01",
            severity="mild",
            baseline_risk_tier="low",
        )
        assert result["adjusted_risk_tier"] == "low"
        assert result["risk_tier_changed"] is False

    @pytest.mark.asyncio
    async def test_calculator_limitation_note_present(self):
        """Calculator limitation note must always be present."""
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="SYNTH01",
            severity="moderate",
            baseline_risk_tier="intermediate",
        )
        assert "calculator_limitation_note" in result
        assert len(result["calculator_limitation_note"]) > 50

    @pytest.mark.asyncio
    async def test_icu_double_upgrade(self):
        """ICU COVID → 2-step tier upgrade."""
        result = await _assess_postcovid_cv_risk_impl(
            patient_id="SYNTH01",
            severity="icu",
            baseline_risk_tier="low",
        )
        assert result["adjusted_risk_tier"] == "high"  # low + 2 steps


# ── assess_pregnancy_complication_cv_risk update ─────────────────────────────


class TestPregnancyComplicationCovidUpdate:
    """Update: assess_pregnancy_complication_cv_risk with covid_severe_history."""

    @pytest.mark.asyncio
    async def test_covid_double_injury_flag(self):
        """Preeclampsia + covid_severe_history=True → double endothelial injury flagged."""
        result = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003",
            complications=["preeclampsia"],
            age_at_complication=38,
            num_affected_pregnancies=1,
            covid_severe_history=True,
        )
        assert result.get("double_endothelial_injury_flag") is True
        recs = " ".join(result.get("screening_recommendations", [])).lower()
        assert "double endothelial" in recs or "covid" in recs, \
            "COVID compound note should appear in screening_recommendations"

    @pytest.mark.asyncio
    async def test_no_covid_no_flag(self):
        """Preeclampsia without covid_severe_history → no double injury flag."""
        result = await _assess_pregnancy_complication_cv_risk_impl(
            patient_id="PAT003",
            complications=["preeclampsia"],
            covid_severe_history=False,
        )
        assert result.get("double_endothelial_injury_flag") is not True
