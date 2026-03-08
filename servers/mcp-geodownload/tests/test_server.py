"""Tests for mcp-geodownload server (DRY_RUN mode)."""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Import and init tests
# ---------------------------------------------------------------------------

def test_imports():
    """Test that server module imports successfully."""
    from mcp_geodownload import server

    assert server is not None


def test_dry_run_mode():
    """Test DRY_RUN mode is enabled by default in test environment."""
    from mcp_geodownload.server import DRY_RUN

    assert DRY_RUN is True, "DRY_RUN should be enabled by default"


def test_server_initialization():
    """Test FastMCP server initializes correctly."""
    from mcp_geodownload.server import mcp

    assert mcp is not None
    assert mcp.name == "geodownload"


# ---------------------------------------------------------------------------
# Mock data completeness
# ---------------------------------------------------------------------------

def test_mock_data_completeness():
    """Test that mock data dicts have consistent keys and structure."""
    from mcp_geodownload.mock_data import (
        MOCK_SEARCH_RESULTS,
        MOCK_METADATA,
        MOCK_SAMPLES,
        MOCK_EXPRESSION_MATRIX_INFO,
        MOCK_SOFT_INFO,
    )

    # Search results should have required fields
    assert len(MOCK_SEARCH_RESULTS) == 3
    for result in MOCK_SEARCH_RESULTS:
        assert "gse_id" in result
        assert result["gse_id"].startswith("GSE")
        assert "title" in result
        assert "summary" in result
        assert "sample_count" in result
        assert result["sample_count"] > 0

    # Metadata keys should match search result GSE IDs
    for result in MOCK_SEARCH_RESULTS:
        gse_id = result["gse_id"]
        assert gse_id in MOCK_METADATA, f"Missing metadata for {gse_id}"
        assert gse_id in MOCK_SAMPLES, f"Missing samples for {gse_id}"
        assert gse_id in MOCK_EXPRESSION_MATRIX_INFO, f"Missing matrix info for {gse_id}"
        assert gse_id in MOCK_SOFT_INFO, f"Missing SOFT info for {gse_id}"

    # Metadata should have required fields
    for gse_id, meta in MOCK_METADATA.items():
        assert "gse_id" in meta
        assert "title" in meta
        assert "summary" in meta
        assert "organism" in meta
        assert "sample_count" in meta
        assert "platform_id" in meta

    # Samples should be lists with required fields
    for gse_id, samples in MOCK_SAMPLES.items():
        assert isinstance(samples, list)
        assert len(samples) > 0
        for sample in samples:
            assert "gsm_id" in sample
            assert sample["gsm_id"].startswith("GSM")
            assert "title" in sample

    # Expression matrix info should have dimensions
    for gse_id, info in MOCK_EXPRESSION_MATRIX_INFO.items():
        assert "gene_count" in info
        assert "sample_count" in info
        assert info["gene_count"] > 0
        assert info["sample_count"] > 0


# ---------------------------------------------------------------------------
# DRY_RUN smoke tests for all 6 tools
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_geo_datasets_dry_run():
    """Test search_geo_datasets returns HGSOC datasets."""
    from mcp_geodownload.server import _search_geo_datasets_impl

    result = await _search_geo_datasets_impl(query="ovarian cancer")

    assert result["status"] == "success"
    assert "datasets" in result
    assert result["total_results"] > 0
    assert "_DRY_RUN_WARNING" in result
    # All mock datasets should match "ovarian"
    for ds in result["datasets"]:
        assert "gse_id" in ds
        assert ds["gse_id"].startswith("GSE")


@pytest.mark.asyncio
async def test_search_geo_datasets_specific_gse():
    """Test search_geo_datasets can find a specific GSE by ID."""
    from mcp_geodownload.server import _search_geo_datasets_impl

    result = await _search_geo_datasets_impl(query="GSE32062")

    assert result["status"] == "success"
    assert result["total_results"] >= 1
    gse_ids = [d["gse_id"] for d in result["datasets"]]
    assert "GSE32062" in gse_ids


@pytest.mark.asyncio
async def test_get_geo_metadata_dry_run():
    """Test get_geo_metadata returns full metadata for a known GSE."""
    from mcp_geodownload.server import _get_geo_metadata_impl

    result = await _get_geo_metadata_impl(gse_id="GSE32062")

    assert result["status"] == "success"
    assert result["gse_id"] == "GSE32062"
    assert "title" in result
    assert "summary" in result
    assert result["sample_count"] == 260
    assert result["platform_id"] == "GPL6480"
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_download_geo_expression_matrix_dry_run():
    """Test download_geo_expression_matrix returns matrix info."""
    from mcp_geodownload.server import _download_geo_expression_matrix_impl

    result = await _download_geo_expression_matrix_impl(gse_id="GSE32062")

    assert result["status"] == "success"
    assert result["gene_count"] == 20502
    assert result["sample_count"] == 260
    assert "download_url" in result
    assert "output_path" in result
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_list_geo_samples_dry_run():
    """Test list_geo_samples returns sample list."""
    from mcp_geodownload.server import _list_geo_samples_impl

    result = await _list_geo_samples_impl(gse_id="GSE26712")

    assert result["status"] == "success"
    assert result["gse_id"] == "GSE26712"
    assert "samples" in result
    assert len(result["samples"]) > 0
    for sample in result["samples"]:
        assert "gsm_id" in sample
        assert "characteristics" in sample
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_list_geo_samples_without_metadata():
    """Test list_geo_samples with include_metadata=False."""
    from mcp_geodownload.server import _list_geo_samples_impl

    result = await _list_geo_samples_impl(gse_id="GSE26712", include_metadata=False)

    assert result["status"] == "success"
    for sample in result["samples"]:
        assert "gsm_id" in sample
        assert "title" in sample
        # Should NOT have characteristics when metadata is excluded
        assert "characteristics" not in sample


@pytest.mark.asyncio
async def test_download_sra_fastq_dry_run():
    """Test download_sra_fastq returns mock download info."""
    from mcp_geodownload.server import _download_sra_fastq_impl

    result = await _download_sra_fastq_impl(srr_id="SRR12345678")

    assert result["status"] == "success"
    assert result["srr_id"] == "SRR12345678"
    assert "files" in result
    assert len(result["files"]) == 2
    assert result["library_strategy"] == "RNA-Seq"
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_get_geo_soft_file_dry_run():
    """Test get_geo_soft_file returns SOFT file info."""
    from mcp_geodownload.server import _get_geo_soft_file_impl

    result = await _get_geo_soft_file_impl(gse_id="GSE9899")

    assert result["status"] == "success"
    assert result["gse_id"] == "GSE9899"
    assert "download_url" in result
    assert "output_path" in result
    assert result["format"] == "SOFT"
    assert "_DRY_RUN_WARNING" in result


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_gse_id_format():
    """Test that invalid GSE ID raises ValueError."""
    from mcp_geodownload.server import _get_geo_metadata_impl

    with pytest.raises(ValueError, match="Invalid GSE ID format"):
        await _get_geo_metadata_impl(gse_id="INVALID123")


@pytest.mark.asyncio
async def test_invalid_gse_id_no_digits():
    """Test that GSE without digits raises ValueError."""
    from mcp_geodownload.server import _get_geo_metadata_impl

    with pytest.raises(ValueError, match="Invalid GSE ID format"):
        await _get_geo_metadata_impl(gse_id="GSEabc")


@pytest.mark.asyncio
async def test_invalid_srr_id_format():
    """Test that invalid SRR ID raises ValueError."""
    from mcp_geodownload.server import _download_sra_fastq_impl

    with pytest.raises(ValueError, match="Invalid SRR ID format"):
        await _download_sra_fastq_impl(srr_id="INVALID")


@pytest.mark.asyncio
async def test_empty_query():
    """Test that empty query returns error."""
    from mcp_geodownload.server import _search_geo_datasets_impl

    result = await _search_geo_datasets_impl(query="")

    assert result["status"] == "error"
    assert "empty" in result["message"].lower()


@pytest.mark.asyncio
async def test_unknown_gse_returns_error():
    """Test that unknown GSE ID returns error in DRY_RUN mode."""
    from mcp_geodownload.server import _get_geo_metadata_impl

    result = await _get_geo_metadata_impl(gse_id="GSE99999999")

    assert result["status"] == "error"
    assert "not found" in result["message"].lower()


@pytest.mark.asyncio
async def test_gse_id_case_insensitive():
    """Test that GSE IDs are normalized to uppercase."""
    from mcp_geodownload.server import _get_geo_metadata_impl

    result = await _get_geo_metadata_impl(gse_id="gse32062")

    assert result["status"] == "success"
    assert result["gse_id"] == "GSE32062"


# ---------------------------------------------------------------------------
# geo_client URL builder tests
# ---------------------------------------------------------------------------

def test_build_series_matrix_url():
    """Test Series Matrix FTP URL construction."""
    from mcp_geodownload.geo_client import build_series_matrix_url

    url = build_series_matrix_url("GSE32062")
    assert "GSE32nnn" in url
    assert "GSE32062" in url
    assert url.endswith("GSE32062_series_matrix.txt.gz")


def test_build_series_matrix_url_short_id():
    """Test Series Matrix URL for short GSE IDs."""
    from mcp_geodownload.geo_client import build_series_matrix_url

    url = build_series_matrix_url("GSE9899")
    assert "GSE9nnn" in url
    assert "GSE9899" in url


def test_build_soft_url():
    """Test SOFT file FTP URL construction."""
    from mcp_geodownload.geo_client import build_soft_url

    url = build_soft_url("GSE26712")
    assert "GSE26nnn" in url
    assert "GSE26712" in url
    assert url.endswith("GSE26712_family.soft.gz")


def test_build_series_matrix_url_case_insensitive():
    """Test that URL builder normalizes case."""
    from mcp_geodownload.geo_client import build_series_matrix_url

    url = build_series_matrix_url("gse32062")
    assert "GSE32062" in url
