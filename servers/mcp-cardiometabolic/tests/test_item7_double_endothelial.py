"""Item 7 tests: covid_severe_history flag + double endothelial injury detection."""

import pytest

from mcp_cardiometabolic.server import _assess_pregnancy_complication_cv_risk_impl


@pytest.mark.asyncio
async def test_double_endothelial_injury_fires_for_preeclampsia_plus_covid():
    """Preeclampsia + covid_severe_history=True must set double_endothelial_injury_flag=True
    and add a warning to screening_recommendations."""
    result = await _assess_pregnancy_complication_cv_risk_impl(
        patient_id="PAT003",
        complications=["preeclampsia"],
        age_at_complication=38,
        num_affected_pregnancies=1,
        covid_severe_history=True,
    )
    assert result["double_endothelial_injury_flag"] is True, \
        "Flag should be True for preeclampsia + severe COVID"

    assert result["double_endothelial_injury_note"] is not None, \
        "Note should not be None when flag is True"

    recs_text = " ".join(result.get("screening_recommendations", [])).lower()
    assert "double endothelial" in recs_text or "covid" in recs_text, \
        "screening_recommendations should contain the double injury warning"


@pytest.mark.asyncio
async def test_double_endothelial_injury_does_not_fire_without_covid():
    """Preeclampsia alone (covid_severe_history=False) must NOT set the double injury flag."""
    result = await _assess_pregnancy_complication_cv_risk_impl(
        patient_id="PAT003",
        complications=["preeclampsia"],
        age_at_complication=38,
        covid_severe_history=False,
    )
    assert result["double_endothelial_injury_flag"] is False, \
        "Flag should be False without COVID history"
    assert result["double_endothelial_injury_note"] is None


@pytest.mark.asyncio
async def test_double_endothelial_injury_does_not_fire_for_gestational_diabetes_plus_covid():
    """Gestational diabetes + covid_severe_history=True must NOT set the flag.
    Double injury only applies when preeclampsia or eclampsia is present."""
    result = await _assess_pregnancy_complication_cv_risk_impl(
        patient_id="SYNTH01",
        complications=["gestational_diabetes"],
        covid_severe_history=True,
    )
    assert result["double_endothelial_injury_flag"] is False, \
        "Flag should be False — gestational diabetes does not trigger double endothelial injury"


@pytest.mark.asyncio
async def test_double_endothelial_injury_fires_for_eclampsia_plus_covid():
    """Eclampsia (not just preeclampsia) + covid_severe_history=True must also fire the flag."""
    result = await _assess_pregnancy_complication_cv_risk_impl(
        patient_id="SYNTH02",
        complications=["eclampsia"],
        covid_severe_history=True,
    )
    assert result["double_endothelial_injury_flag"] is True, \
        "Flag should fire for eclampsia + COVID, not only for preeclampsia"


@pytest.mark.asyncio
async def test_return_dict_always_has_flag_field():
    """Both flag fields must be present in the return dict even when flag is False.
    Callers must be able to check the key without KeyError."""
    result = await _assess_pregnancy_complication_cv_risk_impl(
        patient_id="SYNTH03",
        complications=["preterm_birth"],
        covid_severe_history=False,
    )
    assert "double_endothelial_injury_flag" in result, \
        "double_endothelial_injury_flag must always be present in return dict"
    assert "double_endothelial_injury_note" in result, \
        "double_endothelial_injury_note must always be present in return dict"


@pytest.mark.asyncio
async def test_existing_preeclampsia_behavior_unchanged():
    """Adding the new parameter must not change the existing tool behavior.
    Risk enhancement for preeclampsia alone must still return category 'High' with cad_multiplier 2.0."""
    result = await _assess_pregnancy_complication_cv_risk_impl(
        patient_id="PAT003",
        complications=["preeclampsia"],
        age_at_complication=38,
        num_affected_pregnancies=1,
        # covid_severe_history omitted — tests that default=False is backward-compatible
    )
    assert result["risk_enhancement"]["category"] == "High"
    assert result["risk_enhancement"]["cad_multiplier"] == 2.0
    assert len(result["screening_recommendations"]) > 0
