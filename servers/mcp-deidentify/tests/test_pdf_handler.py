"""Tests for PDF de-identification handler."""

import os

import pytest

os.environ["DEIDENTIFY_DRY_RUN"] = "true"

from mcp_deidentify.format_handlers.pdf_handler import deidentify_pdf_file


@pytest.mark.asyncio
async def test_dry_run_returns_synthetic_text():
    session_key = {"entity_map": {}, "_counters": {}}
    result = await deidentify_pdf_file(
        pdf_path="tests/fixtures/synthetic.pdf",
        patient_id="PAT-TEST",
        session_key=session_key,
    )
    assert result["status"] == "ok"
    assert isinstance(result["raw_text"], str)
    assert isinstance(result["deidentified_text"], str)
    assert result["page_count"] == 3
    assert len(result["entities_found"]) > 0
    assert result["pages_without_text"] == []


@pytest.mark.asyncio
async def test_dry_run_fixture_is_not_derived_from_input():
    """Documents the DRY_RUN fixture's defining limitation.

    The fixture ignores pdf_path entirely. That is acceptable ONLY because
    DRY_RUN output is now prefixed SYNTHETIC: and flagged at the tool boundary.
    See test_dry_run_safety.py for the live path, where output must be derived
    from the input file.
    """
    session_key = {"entity_map": {}, "_counters": {}}
    result = await deidentify_pdf_file("nonexistent-path.pdf", "PAT-TEST", session_key)
    assert len(result["raw_text"]) > 0
    assert len(result["deidentified_text"]) > 0
    assert "SYNTHETIC" in result["raw_text"]
