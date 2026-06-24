"""Tests for genomics file de-identification handler."""

import os

import pytest

os.environ["DEIDENTIFY_DRY_RUN"] = "true"

from mcp_deidentify.format_handlers.genomics_handler import (
    deidentify_cns,
    deidentify_genomics_file,
    deidentify_h5ad,
    deidentify_vcf,
)


@pytest.mark.asyncio
async def test_vcf_dry_run_returns_synthetic_header():
    session_key = {"entity_map": {}, "_counters": {}}
    content, fields, entities = await deidentify_vcf("any.vcf", "PAT-TEST", session_key)
    assert "SPECIMEN-001" in content
    assert len(fields) > 0
    assert len(entities) > 0


@pytest.mark.asyncio
async def test_h5ad_dry_run_returns_synthetic_uns():
    session_key = {"entity_map": {}, "_counters": {}}
    uns, fields, entities = await deidentify_h5ad("any.h5ad", "PAT-TEST", session_key)
    assert "patient_id" in uns
    assert uns["synthetic_data"] is True
    assert len(fields) > 0


@pytest.mark.asyncio
async def test_cns_dry_run_returns_synthetic_header():
    session_key = {"entity_map": {}, "_counters": {}}
    content, fields, entities = await deidentify_cns("any.cns", "PAT-TEST", session_key)
    assert "SPECIMEN-001" in content
    assert len(fields) > 0


@pytest.mark.asyncio
async def test_dispatcher_vcf():
    session_key = {"entity_map": {}, "_counters": {}}
    content, fields, entities = await deidentify_genomics_file(
        "any.vcf", "PAT-TEST", session_key, "vcf"
    )
    assert isinstance(content, str)


@pytest.mark.asyncio
async def test_dispatcher_h5ad():
    session_key = {"entity_map": {}, "_counters": {}}
    content, fields, entities = await deidentify_genomics_file(
        "any.h5ad", "PAT-TEST", session_key, "h5ad"
    )
    assert isinstance(content, str)


@pytest.mark.asyncio
async def test_dispatcher_cns():
    session_key = {"entity_map": {}, "_counters": {}}
    content, fields, entities = await deidentify_genomics_file(
        "any.cns", "PAT-TEST", session_key, "cns"
    )
    assert isinstance(content, str)


@pytest.mark.asyncio
async def test_dispatcher_invalid_type_raises():
    session_key = {"entity_map": {}, "_counters": {}}
    with pytest.raises(ValueError, match="Unsupported file_type"):
        await deidentify_genomics_file("any.xyz", "PAT-TEST", session_key, "xyz")
