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


# ---------------------------------------------------------------------------
# Phase 3 tool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deidentify_text_txt_dry_run():
    from mcp_deidentify.server import deidentify_text

    result = await deidentify_text(text="Jane Doe Smith was seen today.", patient_id="PAT-TEST")
    assert "deidentified_text" in result
    assert "key_path" in result
    assert "entity_count" in result
    assert result["dry_run"] is True
    assert result["source_format"] == "txt"


@pytest.mark.asyncio
async def test_deidentify_text_docx_dry_run():
    from mcp_deidentify.server import deidentify_text

    result = await deidentify_text(
        text="tests/fixtures/synthetic_note.docx",
        patient_id="PAT-TEST",
        source_format="docx",
    )
    assert "deidentified_text" in result
    assert "output_path" in result
    assert result["source_format"] == "docx"


@pytest.mark.asyncio
async def test_deidentify_pdf_dry_run():
    from mcp_deidentify.server import deidentify_pdf_text

    result = await deidentify_pdf_text(
        pdf_path="tests/fixtures/synthetic.pdf", patient_id="PAT-TEST"
    )
    assert "extracted_text" in result
    assert "deidentified_text" in result
    assert "page_count" in result
    assert result["page_count"] == 3


# ---------------------------------------------------------------------------
# Phase 4 tool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deidentify_genomics_vcf_dry_run():
    from mcp_deidentify.server import deidentify_genomics_file

    result = await deidentify_genomics_file(
        file_path="any.vcf", patient_id="PAT-TEST", file_type="vcf"
    )
    assert "deidentified_content" in result
    assert "fields_modified" in result
    assert result["file_type"] == "vcf"
    assert result["dry_run"] is True


@pytest.mark.asyncio
async def test_deidentify_genomics_h5ad_dry_run():
    from mcp_deidentify.server import deidentify_genomics_file

    result = await deidentify_genomics_file(
        file_path="any.h5ad", patient_id="PAT-TEST", file_type="h5ad"
    )
    assert "deidentified_content" in result
    assert result["file_type"] == "h5ad"


@pytest.mark.asyncio
async def test_deidentify_genomics_invalid_type_returns_error():
    from mcp_deidentify.server import deidentify_genomics_file

    result = await deidentify_genomics_file(
        file_path="any.xyz", patient_id="PAT-TEST", file_type="xyz"
    )
    assert "error" in result


# ---------------------------------------------------------------------------
# Phase 5 tool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_deidentification_clean_text():
    from mcp_deidentify.server import validate_deidentification

    result = await validate_deidentification(
        content="GNA11 R183C mutation detected. Treatment: Trametinib.",
        patient_id="PAT-TEST",
    )
    assert "status" in result
    assert "passed" in result
    assert "confidence" in result
    assert "layers" in result
    # DRY_RUN cannot yield a verdict: the Haiku red-team layer did not run.
    assert result["status"] == "unavailable_in_dry_run"
    assert result["passed"] is None
    assert result["dry_run"] is True


@pytest.mark.asyncio
async def test_validate_deidentification_ssn_fails():
    from mcp_deidentify.server import validate_deidentification

    result = await validate_deidentification(
        content="Patient SSN: 123-45-6789",
        patient_id="PAT-TEST",
    )
    assert result["passed"] is not True
    assert len(result["residual_pii_found"]) > 0
    # confidence is None in DRY_RUN: a score computed from 2 of 3 layers would
    # imply a completeness the run does not have.
    assert result["confidence"] is None


@pytest.mark.asyncio
async def test_all_six_tools_no_longer_raise():
    """Confirm all six tools are implemented -- none raise NotImplementedError."""
    from mcp_deidentify.server import (
        deidentify_genomics_file,
        deidentify_json,
        deidentify_pdf_text,
        deidentify_text,
        generate_anonymization_key,
        validate_deidentification,
    )

    # Each call should return a dict, not raise
    r1 = await deidentify_json(json_content='{"name": "test"}', patient_id="PAT-TEST")
    assert isinstance(r1, dict)

    r2 = await deidentify_text(text="some note", patient_id="PAT-TEST")
    assert isinstance(r2, dict)

    r3 = await deidentify_pdf_text(pdf_path="any.pdf", patient_id="PAT-TEST")
    assert isinstance(r3, dict)

    r4 = await deidentify_genomics_file(file_path="any.vcf", patient_id="PAT-TEST", file_type="vcf")
    assert isinstance(r4, dict)

    r5 = await generate_anonymization_key(patient_id="PAT-TEST")
    assert isinstance(r5, dict)

    r6 = await validate_deidentification(content="clean text", patient_id="PAT-TEST")
    assert isinstance(r6, dict)
