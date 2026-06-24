"""Tests for text and DOCX de-identification handler."""

import os

import pytest

os.environ["DEIDENTIFY_DRY_RUN"] = "true"

from mcp_deidentify.format_handlers.text_handler import (
    _default_output_path,
    deidentify_docx_file,
    deidentify_text_string,
)


def test_default_output_path_format():
    path = _default_output_path("PAT004", "/some/dir/intake.docx")
    assert "PAT004" in path
    assert "intake_deid.docx" in path
    assert "deidentified" in path


@pytest.mark.asyncio
async def test_dry_run_text_string_returns_deid_text():
    session_key = {"entity_map": {}, "_counters": {}}
    result, entities = await deidentify_text_string("Jane Doe Smith", "PAT-TEST", session_key)
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(entities, list)


@pytest.mark.asyncio
async def test_dry_run_text_entities_not_empty():
    session_key = {"entity_map": {}, "_counters": {}}
    _, entities = await deidentify_text_string("any text", "PAT-TEST", session_key)
    assert len(entities) > 0


@pytest.mark.asyncio
async def test_dry_run_text_no_original_pii_in_result():
    """In DRY_RUN the synthetic result should not contain the original synthetic entity texts."""
    from mcp_deidentify.engine import SYNTHETIC_ENTITIES

    session_key = {"entity_map": {}, "_counters": {}}
    result, _ = await deidentify_text_string("any text", "PAT-TEST", session_key)
    for ent in SYNTHETIC_ENTITIES:
        assert ent["text"] not in result


@pytest.mark.asyncio
async def test_dry_run_docx_returns_synthetic_path():
    session_key = {"entity_map": {}, "_counters": {}}
    _, out_path, entities = await deidentify_docx_file(
        docx_path="tests/fixtures/synthetic_note.docx",
        patient_id="PAT-TEST",
        session_key=session_key,
    )
    assert "DRY_RUN" in out_path
    assert len(entities) > 0
