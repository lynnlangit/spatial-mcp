"""Tests for three-layer de-identification validator."""

import os

import pytest

os.environ["DEIDENTIFY_DRY_RUN"] = "true"

from mcp_deidentify.validator import _run_key_lookup_layer, _run_regex_layer, validate

# --- Layer 2: regex tests ---


def test_regex_clean_text_passes():
    passed, hits = _run_regex_layer("The patient has a tumour in the right eye.")
    assert passed is True
    assert hits == []


def test_regex_detects_ssn():
    passed, hits = _run_regex_layer("SSN is 123-45-6789")
    assert passed is False
    assert any(h["pattern"] == "SSN" for h in hits)


def test_regex_detects_email():
    passed, hits = _run_regex_layer("Contact: doctor@hospital.example.com for results.")
    assert passed is False
    assert any(h["pattern"] == "EMAIL" for h in hits)


def test_regex_detects_us_phone():
    passed, hits = _run_regex_layer("Call (555) 123-4567 for appointments.")
    assert passed is False
    assert any("PHONE" in h["pattern"] for h in hits)


def test_regex_detects_iso_date():
    passed, hits = _run_regex_layer("Date of birth: 1980-01-01")
    assert passed is False
    assert any(h["pattern"] == "DATE_ISO" for h in hits)


def test_regex_detects_slashed_date():
    passed, hits = _run_regex_layer("DOB: 01/15/1980")
    assert passed is False
    assert any(h["pattern"] == "DATE_SLASHED" for h in hits)


def test_regex_passes_on_anonymization_codes():
    """Codes like FAC-001 and DOB-REDACTED should not trigger regex hits."""
    passed, _hits = _run_regex_layer(
        "Patient PAT-NAME-001 seen at FAC-001. DOB-REDACTED. MRN-REDACTED-001."
    )
    # Codes should not contain raw SSN/phone/email patterns
    assert passed is True


# --- Layer 3: key reverse lookup tests ---


def test_key_lookup_clean_content_passes():
    session_key = {
        "entity_map": {
            "Jane Doe Smith": {"code": "PAT-NAME-001", "entity_type": "PERSON_NAME_PATIENT"}
        }
    }
    passed, _hits = _run_key_lookup_layer("Patient: PAT-NAME-001", session_key)
    assert passed is True


def test_key_lookup_detects_verbatim_entity():
    session_key = {
        "entity_map": {
            "Jane Doe Smith": {"code": "PAT-NAME-001", "entity_type": "PERSON_NAME_PATIENT"}
        }
    }
    passed, hits = _run_key_lookup_layer("Patient Jane Doe Smith was seen.", session_key)
    assert passed is False
    assert any(h["entity_text"] == "Jane Doe Smith" for h in hits)


def test_key_lookup_case_insensitive():
    session_key = {
        "entity_map": {"CITY GENERAL HOSPITAL": {"code": "FAC-001", "entity_type": "FACILITY_NAME"}}
    }
    passed, _hits = _run_key_lookup_layer("Seen at city general hospital.", session_key)
    assert passed is False


def test_key_lookup_skips_short_entities():
    """Entities shorter than 4 chars should not trigger lookup hits."""
    session_key = {
        "entity_map": {"Jo": {"code": "PAT-NAME-001", "entity_type": "PERSON_NAME_PATIENT"}}
    }
    passed, _hits = _run_key_lookup_layer("Patient Jo was seen.", session_key)
    assert passed is True


# --- Full validate() integration ---


@pytest.mark.asyncio
async def test_validate_clean_text_yields_no_verdict_in_dry_run():
    """DRY_RUN cannot produce a pass: the Haiku layer never ran.

    This previously asserted passed=True at confidence 1.0, which is exactly the
    rubber-stamp the validator must not issue.
    """
    session_key = {"entity_map": {}}
    result = await validate("The tumor showed GNA11 R183C mutation.", session_key)
    assert result["status"] == "unavailable_in_dry_run"
    assert result["passed"] is None
    assert result["confidence"] is None
    assert result["layers"]["regex_sweep"]["passed"] is True
    assert result["layers"]["key_reverse_lookup"]["passed"] is True
    assert result["layers"]["haiku_red_team"]["passed"] is None


@pytest.mark.asyncio
async def test_validate_with_ssn_fails():
    session_key = {"entity_map": {}}
    result = await validate("Patient SSN: 123-45-6789 confirmed.", session_key)
    # No verdict in DRY_RUN, but hits from layers that DID run are still reported.
    assert result["passed"] is not True
    assert result["layers"]["regex_sweep"]["passed"] is False
    assert len(result["residual_pii_found"]) > 0


@pytest.mark.asyncio
async def test_validate_with_key_hit_fails():
    session_key = {
        "entity_map": {
            "Jane Doe Smith": {"code": "PAT-NAME-001", "entity_type": "PERSON_NAME_PATIENT"}
        }
    }
    result = await validate("Patient Jane Doe Smith is enrolled.", session_key)
    assert result["passed"] is not True
    assert result["layers"]["key_reverse_lookup"]["passed"] is False


@pytest.mark.asyncio
async def test_validate_result_schema():
    session_key = {"entity_map": {}}
    result = await validate("clean text", session_key)
    assert "status" in result
    assert "passed" in result
    assert "confidence" in result
    assert "layers" in result
    assert "layers_skipped" in result
    assert "date_policy" in result
    assert "residual_pii_found" in result
    assert set(result["layers"].keys()) == {"haiku_red_team", "regex_sweep", "key_reverse_lookup"}
