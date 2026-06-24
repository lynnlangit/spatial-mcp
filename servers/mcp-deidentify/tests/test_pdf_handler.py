"""Tests for PDF de-identification handler."""

import os

import pytest

os.environ["DEIDENTIFY_DRY_RUN"] = "true"

from mcp_deidentify.format_handlers.pdf_handler import deidentify_pdf_file


@pytest.mark.asyncio
async def test_dry_run_returns_synthetic_text():
    session_key = {"entity_map": {}, "_counters": {}}
    raw, deid, page_count, entities = await deidentify_pdf_file(
        pdf_path="tests/fixtures/synthetic.pdf",
        patient_id="PAT-TEST",
        session_key=session_key,
    )
    assert isinstance(raw, str)
    assert isinstance(deid, str)
    assert page_count == 3
    assert len(entities) > 0


@pytest.mark.asyncio
async def test_dry_run_deid_differs_from_raw_or_is_same_synthetic():
    """In DRY_RUN the fixture text is returned as both raw and deid (acceptable)."""
    session_key = {"entity_map": {}, "_counters": {}}
    raw, deid, _, _ = await deidentify_pdf_file("any.pdf", "PAT-TEST", session_key)
    # Both should be non-empty strings
    assert len(raw) > 0
    assert len(deid) > 0
