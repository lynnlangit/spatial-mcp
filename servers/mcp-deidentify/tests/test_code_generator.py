"""Tests for deterministic code generator."""

from mcp_deidentify.code_generator import assign_code


def make_key():
    return {"entity_map": {}, "_counters": {}}


def test_same_triple_returns_same_code():
    key = make_key()
    code1 = assign_code("PAT001", "FACILITY_NAME", "City General", key)
    # Reset and regenerate -- same key dict so should return existing
    code2 = assign_code("PAT001", "FACILITY_NAME", "City General", key)
    assert code1 == code2


def test_different_entities_get_different_codes():
    key = make_key()
    code1 = assign_code("PAT001", "FACILITY_NAME", "Hospital A", key)
    code2 = assign_code("PAT001", "FACILITY_NAME", "Hospital B", key)
    assert code1 != code2


def test_different_patients_use_independent_counters():
    key_a = make_key()
    key_b = make_key()
    code_a = assign_code("PAT001", "FACILITY_NAME", "Same Hospital", key_a)
    code_b = assign_code("PAT002", "FACILITY_NAME", "Same Hospital", key_b)
    # Both should be FAC-001 since each key starts fresh
    assert code_a == code_b == "FAC-001"


def test_dob_always_fixed_replacement():
    key = make_key()
    code = assign_code("PAT001", "DATE_OF_BIRTH", "1980-01-01", key)
    assert code == "DOB-REDACTED"


def test_physician_prefix():
    key = make_key()
    code = assign_code("PAT001", "PERSON_NAME_PHYSICIAN", "Dr. Jane Test", key)
    assert code.startswith("Dr. ONC-")


def test_facility_prefix():
    key = make_key()
    code = assign_code("PAT001", "FACILITY_NAME", "Synthetic Hospital", key)
    assert code.startswith("FAC-")


def test_accession_prefix():
    key = make_key()
    code = assign_code("PAT001", "ACCESSION_NUMBER", "22X-TEST-001", key)
    assert code.startswith("ACCESSION-")


def test_entity_map_recorded():
    key = make_key()
    assign_code("PAT001", "MRN", "12345678", key)
    assert "12345678" in key["entity_map"]
    assert key["entity_map"]["12345678"]["entity_type"] == "MRN"
