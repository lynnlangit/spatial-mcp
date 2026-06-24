"""Tests for mcp-deidentify server tools."""

import json
import os

import pytest

os.environ["DEIDENTIFY_DRY_RUN"] = "true"

# ---------------------------------------------------------------------------
# Phase 2 tool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deidentify_json_dry_run_returns_dict():
    """deidentify_json must return a dict with 'deidentified' and 'key_path' keys."""
    from mcp_deidentify.server import deidentify_json

    record = {"name": "Jane Doe Smith", "mrn": "12345678"}
    result = await deidentify_json(
        json_content=json.dumps(record),
        patient_id="PAT-SYNTHETIC-001",
    )
    assert "deidentified" in result
    assert "key_path" in result
    assert "entity_count" in result
    assert isinstance(result["deidentified"], dict)
    assert result["dry_run"] is True


@pytest.mark.asyncio
async def test_deidentify_json_invalid_json_returns_error():
    """deidentify_json with malformed JSON must return an error key, not raise."""
    from mcp_deidentify.server import deidentify_json

    result = await deidentify_json(
        json_content="not valid json {{{",
        patient_id="PAT-SYNTHETIC-001",
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_generate_anonymization_key_dry_run():
    """generate_anonymization_key must return code_map and key_path in DRY_RUN."""
    from mcp_deidentify.server import generate_anonymization_key

    result = await generate_anonymization_key(patient_id="PAT-SYNTHETIC-001")
    assert "code_map" in result
    assert "key_path" in result
    assert "entry_count" in result
    assert result["dry_run"] is True
    assert isinstance(result["code_map"], dict)
