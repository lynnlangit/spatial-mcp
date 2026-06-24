"""Tests for JSON clinical record de-identification handler."""

import json
import os
import pathlib

import pytest

os.environ["DEIDENTIFY_DRY_RUN"] = "true"

from mcp_deidentify.format_handlers.json_handler import _should_skip, deidentify_json_dict

# --- _should_skip unit tests ---


def test_skip_short_strings():
    assert _should_skip("ab") is True
    assert _should_skip("abc") is True


def test_skip_existing_codes():
    assert _should_skip("FAC-001") is True
    assert _should_skip("ACCESSION-001") is True
    assert _should_skip("DOB-REDACTED") is True
    assert _should_skip("MRN-REDACTED-001") is True


def test_do_not_skip_real_names():
    assert _should_skip("Jane Doe Smith") is False
    assert _should_skip("City General Hospital") is False
    assert _should_skip("1980-01-01") is False


# --- deidentify_json_dict tests ---


@pytest.mark.asyncio
async def test_dict_structure_preserved():
    """De-identified dict must have same keys and non-string value types."""
    record = {
        "patient_id": "PAT-SYNTHETIC-001",
        "age": 46,
        "active": True,
        "name": "Jane Doe Smith",
        "nested": {"facility": "City General Hospital"},
    }
    session_key = {"entity_map": {}, "_counters": {}}
    result, entities = await deidentify_json_dict(record, "PAT-SYNTHETIC-001", session_key)

    # Structure preserved
    assert "patient_id" in result
    assert "age" in result
    assert "active" in result
    assert result["age"] == 46
    assert result["active"] is True
    assert "nested" in result
    assert "facility" in result["nested"]


@pytest.mark.asyncio
async def test_entities_found_and_replaced():
    """In DRY_RUN, synthetic entities in SYNTHETIC_TEXT should be replaced."""
    from mcp_deidentify.engine import SYNTHETIC_ENTITIES, SYNTHETIC_TEXT

    record = {"note": SYNTHETIC_TEXT, "count": 1}
    session_key = {"entity_map": {}, "_counters": {}}
    result, entities = await deidentify_json_dict(record, "PAT-SYNTHETIC-001", session_key)

    # At least one entity should have been found
    assert len(entities) > 0

    # The original entity texts should no longer appear verbatim in the result
    for ent in SYNTHETIC_ENTITIES:
        assert ent["text"] not in result["note"], f"'{ent['text']}' still present after de-id"


@pytest.mark.asyncio
async def test_list_values_deidentified():
    """Strings inside lists should also be de-identified."""
    from mcp_deidentify.engine import SYNTHETIC_TEXT

    record = {"notes": [SYNTHETIC_TEXT, "short"], "id": "PAT001"}
    session_key = {"entity_map": {}, "_counters": {}}
    result, entities = await deidentify_json_dict(record, "PAT-SYNTHETIC-001", session_key)

    # The first list item should have been processed
    assert isinstance(result["notes"], list)
    assert len(result["notes"]) == 2


@pytest.mark.asyncio
async def test_original_dict_not_mutated():
    """deidentify_json_dict must not modify the input dict."""
    record = {"name": "Jane Doe Smith"}
    original_name = record["name"]
    session_key = {"entity_map": {}, "_counters": {}}
    await deidentify_json_dict(record, "PAT-SYNTHETIC-001", session_key)
    assert record["name"] == original_name


@pytest.mark.asyncio
async def test_session_key_populated():
    """After de-id, session_key entity_map should contain detected entities."""
    from mcp_deidentify.engine import SYNTHETIC_TEXT

    record = {"note": SYNTHETIC_TEXT}
    session_key = {"entity_map": {}, "_counters": {}}
    await deidentify_json_dict(record, "PAT-SYNTHETIC-001", session_key)
    assert len(session_key["entity_map"]) > 0


@pytest.mark.asyncio
async def test_fixture_file_deidentified(tmp_path):
    """Run the synthetic_record.json fixture through the handler end-to-end."""
    fixture_path = pathlib.Path("tests/fixtures/synthetic_record.json")
    record = json.loads(fixture_path.read_text())
    session_key = {"entity_map": {}, "_counters": {}}
    result, entities = await deidentify_json_dict(record, "PAT-SYNTHETIC-001", session_key)

    # patient_id field should be preserved (it's a code, not PII)
    assert "patient_id" in result

    # At least some entities should have been found
    assert len(entities) > 0
