"""Tests for mcp-cibersortx server (DRY_RUN mode)."""

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
    from mcp_cibersortx import server

    assert server is not None


def test_dry_run_mode():
    """Test DRY_RUN mode is enabled by default in test environment."""
    from mcp_cibersortx.server import DRY_RUN

    assert DRY_RUN is True, "DRY_RUN should be enabled by default"


def test_server_initialization():
    """Test FastMCP server initializes correctly."""
    from mcp_cibersortx.server import mcp

    assert mcp is not None
    assert mcp.name == "cibersortx"


# ---------------------------------------------------------------------------
# Mock data completeness
# ---------------------------------------------------------------------------

def test_mock_data_completeness():
    """Test that mock data dicts have consistent keys and structure."""
    from mcp_cibersortx.mock_data import (
        LM22_CELL_TYPES,
        MOCK_DECONVOLUTION_FRACTIONS,
        MOCK_DECONVOLUTION_PVALUES,
        MOCK_DECONVOLUTION_RMSE,
        MOCK_JOB_SUBMITTED,
        MOCK_SIGNATURE_UPLOAD,
    )

    # LM22 should have exactly 22 cell types
    assert len(LM22_CELL_TYPES) == 22

    # All mock samples should have fractions for all 22 LM22 cell types
    for sample_id, fractions in MOCK_DECONVOLUTION_FRACTIONS.items():
        assert len(fractions) == 22, f"Sample {sample_id} has {len(fractions)} types, expected 22"
        for cell_type in LM22_CELL_TYPES:
            assert cell_type in fractions, f"Missing {cell_type} in {sample_id}"
        # Fractions should sum approximately to 1.0
        total = sum(fractions.values())
        assert 0.95 <= total <= 1.05, f"Sample {sample_id} fractions sum to {total}"

    # P-values and RMSE should have same sample keys
    assert set(MOCK_DECONVOLUTION_FRACTIONS.keys()) == set(MOCK_DECONVOLUTION_PVALUES.keys())
    assert set(MOCK_DECONVOLUTION_FRACTIONS.keys()) == set(MOCK_DECONVOLUTION_RMSE.keys())

    # P-values should be between 0 and 1
    for sample_id, pval in MOCK_DECONVOLUTION_PVALUES.items():
        assert 0.0 <= pval <= 1.0, f"Invalid p-value for {sample_id}: {pval}"

    # Job metadata should have required fields
    assert "job_id" in MOCK_JOB_SUBMITTED
    assert "state" in MOCK_JOB_SUBMITTED
    assert MOCK_JOB_SUBMITTED["state"] == "COMPLETED"

    # Signature upload should have cell type info
    assert MOCK_SIGNATURE_UPLOAD["genes"] > 0
    assert MOCK_SIGNATURE_UPLOAD["cell_types"] > 0
    assert len(MOCK_SIGNATURE_UPLOAD["cell_type_names"]) == MOCK_SIGNATURE_UPLOAD["cell_types"]


def test_mock_hgsoc_biology():
    """Test that mock fractions reflect known HGSOC biology."""
    from mcp_cibersortx.mock_data import MOCK_DECONVOLUTION_FRACTIONS

    # HGSOC TME is known to have:
    # - High M2 macrophages (immunosuppressive)
    # - Low CD8 T cells (cold tumor)
    # - Moderate Tregs
    for sample_id, fractions in MOCK_DECONVOLUTION_FRACTIONS.items():
        # M2 macrophages should be the dominant population
        assert fractions["Macrophages_M2"] >= 0.25, (
            f"M2 macrophages too low in {sample_id}: {fractions['Macrophages_M2']}"
        )
        # CD8 T cells should be low (immunosuppressed TME)
        assert fractions["T_cells_CD8"] <= 0.15, (
            f"CD8 T cells too high for HGSOC in {sample_id}: {fractions['T_cells_CD8']}"
        )
        # Tregs should be present
        assert fractions["T_cells_regulatory_Tregs"] >= 0.03, (
            f"Tregs too low in {sample_id}: {fractions['T_cells_regulatory_Tregs']}"
        )


# ---------------------------------------------------------------------------
# DRY_RUN smoke tests for all 5 tools
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_cibersortx_deconvolution_dry_run():
    """Test run_cibersortx_deconvolution returns HGSOC immune fractions."""
    from mcp_cibersortx.server import _run_cibersortx_deconvolution_impl

    result = await _run_cibersortx_deconvolution_impl(
        mixture_path="/data/GSE32062_matrix.csv"
    )

    assert result["status"] == "success"
    assert "fractions" in result
    assert "p_values" in result
    assert "rmse" in result
    assert result["n_cell_types"] == 22
    assert result["job_id"] == "cb-mock-12345"
    assert result["state"] == "COMPLETED"
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_run_cibersortx_deconvolution_custom_signature():
    """Test deconvolution with custom signature matrix."""
    from mcp_cibersortx.server import _run_cibersortx_deconvolution_impl

    result = await _run_cibersortx_deconvolution_impl(
        mixture_path="/data/GSE32062_matrix.csv",
        signature_matrix="custom",
        custom_signature_path="/data/hgsoc_signature.csv",
        permutations=500,
    )

    assert result["status"] == "success"
    assert "fractions" in result


@pytest.mark.asyncio
async def test_upload_signature_matrix_dry_run():
    """Test upload_signature_matrix returns mock upload info."""
    from mcp_cibersortx.server import _upload_signature_matrix_impl

    result = await _upload_signature_matrix_impl(
        matrix_path="/data/hgsoc_signature.csv",
        matrix_name="HGSOC_TME_signature",
        description="Custom HGSOC tumor microenvironment signature",
    )

    assert result["status"] == "success"
    assert result["matrix_id"] == "sig-custom-001"
    assert result["genes"] == 547
    assert result["cell_types"] == 12
    assert len(result["cell_type_names"]) == 12
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_get_job_status_completed():
    """Test get_job_status for a completed job."""
    from mcp_cibersortx.server import _get_job_status_impl

    result = await _get_job_status_impl(job_id="cb-mock-12345")

    assert result["status"] == "success"
    assert result["state"] == "COMPLETED"
    assert result["progress_pct"] == 100
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_get_job_status_running():
    """Test get_job_status for a running job."""
    from mcp_cibersortx.server import _get_job_status_impl

    result = await _get_job_status_impl(job_id="cb-mock-67890")

    assert result["status"] == "success"
    assert result["state"] == "RUNNING"
    assert result["progress_pct"] == 45
    assert result["estimated_remaining_seconds"] > 0


@pytest.mark.asyncio
async def test_download_results_dry_run():
    """Test download_results returns mock fractions."""
    from mcp_cibersortx.server import _download_results_impl

    result = await _download_results_impl(job_id="cb-mock-12345")

    assert result["status"] == "success"
    assert result["job_id"] == "cb-mock-12345"
    assert "fractions" in result
    assert "output_path" in result
    assert result["summary"]["n_samples"] == 3
    assert result["summary"]["n_cell_types"] == 22
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_run_mock_deconvolution_dry_run():
    """Test run_mock_deconvolution returns NNLS approximate results."""
    from mcp_cibersortx.server import _run_mock_deconvolution_impl

    result = await _run_mock_deconvolution_impl(
        mixture_path="/data/GSE32062_matrix.csv",
        signature_path="/data/hgsoc_signature.csv",
    )

    assert result["status"] == "success"
    assert result["method"] == "scipy_nnls"
    assert "fractions" in result
    assert "rmse" in result
    assert "warning" in result
    assert "approximate" in result["warning"].lower()
    assert "_DRY_RUN_WARNING" in result


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_mixture_path():
    """Test that empty mixture_path returns error."""
    from mcp_cibersortx.server import _run_cibersortx_deconvolution_impl

    result = await _run_cibersortx_deconvolution_impl(mixture_path="")

    assert result["status"] == "error"
    assert "empty" in result["message"].lower()


@pytest.mark.asyncio
async def test_empty_matrix_path_upload():
    """Test that empty matrix_path returns error for upload."""
    from mcp_cibersortx.server import _upload_signature_matrix_impl

    result = await _upload_signature_matrix_impl(
        matrix_path="",
        matrix_name="test",
    )

    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_empty_matrix_name_upload():
    """Test that empty matrix_name returns error for upload."""
    from mcp_cibersortx.server import _upload_signature_matrix_impl

    result = await _upload_signature_matrix_impl(
        matrix_path="/data/test.csv",
        matrix_name="",
    )

    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_empty_job_id():
    """Test that empty job_id raises ValueError."""
    from mcp_cibersortx.server import _get_job_status_impl

    with pytest.raises(ValueError, match="empty"):
        await _get_job_status_impl(job_id="")


@pytest.mark.asyncio
async def test_empty_mixture_path_nnls():
    """Test that empty paths return error for NNLS."""
    from mcp_cibersortx.server import _run_mock_deconvolution_impl

    result = await _run_mock_deconvolution_impl(
        mixture_path="",
        signature_path="/data/sig.csv",
    )
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_empty_signature_path_nnls():
    """Test that empty signature_path returns error for NNLS."""
    from mcp_cibersortx.server import _run_mock_deconvolution_impl

    result = await _run_mock_deconvolution_impl(
        mixture_path="/data/mix.csv",
        signature_path="",
    )
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_download_results_custom_output_dir():
    """Test download_results with custom output directory."""
    from mcp_cibersortx.server import _download_results_impl

    result = await _download_results_impl(
        job_id="cb-mock-12345",
        output_dir="/tmp/custom_output",
    )

    assert result["status"] == "success"
    assert "/tmp/custom_output" in result["output_path"]
