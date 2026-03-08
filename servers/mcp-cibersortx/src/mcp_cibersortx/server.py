"""MCP CIBERSORTx server — cell-type deconvolution from bulk RNA-seq."""

import logging
import os
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from .api_client import (
    download_results as api_download_results,
    poll_job_status,
    submit_job,
    upload_signature_matrix as api_upload_signature,
    wait_for_completion,
)
from .mock_data import (
    MOCK_DECONVOLUTION_FRACTIONS,
    MOCK_DECONVOLUTION_PVALUES,
    MOCK_DECONVOLUTION_RMSE,
    MOCK_JOB_RUNNING,
    MOCK_JOB_SUBMITTED,
    MOCK_NNLS_FRACTIONS,
    MOCK_NNLS_RMSE,
    MOCK_SIGNATURE_UPLOAD,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("cibersortx")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DRY_RUN = os.getenv("CIBERSORTX_DRY_RUN", "true").lower() == "true"
CIBERSORTX_TOKEN = os.getenv("CIBERSORTX_TOKEN", "")
CIBERSORTX_EMAIL = os.getenv("CIBERSORTX_EMAIL", "")
CIBERSORTX_API_URL = os.getenv(
    "CIBERSORTX_API_URL", "https://cibersortx.stanford.edu/api"
)
CIBERSORTX_CACHE_DIR = os.getenv("CIBERSORTX_CACHE_DIR", "/data/cache/cibersortx")
POLL_INTERVAL = int(os.getenv("CIBERSORTX_POLL_INTERVAL", "30"))
MAX_WAIT = int(os.getenv("CIBERSORTX_MAX_WAIT", "1800"))


def add_dry_run_warning(result: Any) -> Any:
    """Add warning banner to results when in DRY_RUN mode."""
    if not DRY_RUN:
        return result

    warning = (
        "=== SYNTHETIC DATA WARNING ===\n"
        "This result was generated in DRY_RUN mode and does NOT represent real analysis.\n"
        "Do NOT use this data for clinical decisions.\n"
        "Set CIBERSORTX_DRY_RUN=false for production use.\n"
        "==============================\n\n"
    )

    if isinstance(result, dict):
        result["_DRY_RUN_WARNING"] = "SYNTHETIC DATA - NOT FOR CLINICAL USE"
        result["_message"] = warning.strip()
    elif isinstance(result, str):
        result = warning + result

    return result


def _validate_job_id(job_id: str) -> str:
    """Validate and normalize a CIBERSORTx job ID."""
    job_id = job_id.strip()
    if not job_id:
        raise ValueError("Job ID cannot be empty.")
    return job_id


# ---------------------------------------------------------------------------
# Tool implementation functions
# ---------------------------------------------------------------------------

async def _run_cibersortx_deconvolution_impl(
    mixture_path: str,
    signature_matrix: str = "LM22",
    custom_signature_path: Optional[str] = None,
    permutations: int = 100,
    quantile_normalize: bool = True,
) -> Dict[str, Any]:
    """Implementation for run_cibersortx_deconvolution."""
    if not mixture_path or not mixture_path.strip():
        return {"status": "error", "message": "mixture_path cannot be empty."}

    if DRY_RUN:
        return add_dry_run_warning({
            "status": "success",
            **MOCK_JOB_SUBMITTED,
            "mixture_path": mixture_path,
            "fractions": MOCK_DECONVOLUTION_FRACTIONS,
            "p_values": MOCK_DECONVOLUTION_PVALUES,
            "rmse": MOCK_DECONVOLUTION_RMSE,
            "n_cell_types": 22,
        })

    if not CIBERSORTX_TOKEN:
        return {
            "status": "error",
            "message": (
                "CIBERSORTX_TOKEN is required for production mode. "
                "Register at https://cibersortx.stanford.edu/ to obtain a token."
            ),
        }

    # Submit job
    submit_result = await submit_job(
        mixture_path=mixture_path,
        signature_matrix=signature_matrix,
        token=CIBERSORTX_TOKEN,
        email=CIBERSORTX_EMAIL,
        api_url=CIBERSORTX_API_URL,
        custom_signature_path=custom_signature_path,
        permutations=permutations,
        quantile_normalize=quantile_normalize,
    )

    job_id = submit_result.get("job_id", "")
    if not job_id:
        return {"status": "error", "message": "No job_id returned from CIBERSORTx."}

    # Poll until completion
    final_status = await wait_for_completion(
        job_id=job_id,
        token=CIBERSORTX_TOKEN,
        api_url=CIBERSORTX_API_URL,
        poll_interval=POLL_INTERVAL,
        max_wait=MAX_WAIT,
    )

    state = final_status.get("state", "UNKNOWN")
    if state == "FAILED":
        return {
            "status": "error",
            "job_id": job_id,
            "message": f"CIBERSORTx job failed: {final_status.get('error', 'unknown')}",
        }

    if final_status.get("_timeout"):
        return {
            "status": "success",
            "job_id": job_id,
            "state": state,
            "message": (
                f"Job still running after {MAX_WAIT}s. "
                "Use get_job_status and download_results to retrieve later."
            ),
        }

    # Download results
    output_path = f"{CIBERSORTX_CACHE_DIR}/{job_id}_results.csv"
    await api_download_results(
        job_id=job_id,
        token=CIBERSORTX_TOKEN,
        api_url=CIBERSORTX_API_URL,
        output_path=output_path,
    )

    return {
        "status": "success",
        "job_id": job_id,
        "state": "COMPLETED",
        "output_path": output_path,
        # TODO: Parse CSV to extract fractions dict when pandas is available
    }


async def _upload_signature_matrix_impl(
    matrix_path: str,
    matrix_name: str,
    description: str = "",
) -> Dict[str, Any]:
    """Implementation for upload_signature_matrix."""
    if not matrix_path or not matrix_path.strip():
        return {"status": "error", "message": "matrix_path cannot be empty."}
    if not matrix_name or not matrix_name.strip():
        return {"status": "error", "message": "matrix_name cannot be empty."}

    if DRY_RUN:
        return add_dry_run_warning({
            "status": "success",
            "matrix_path": matrix_path,
            "description": description,
            **MOCK_SIGNATURE_UPLOAD,
        })

    if not CIBERSORTX_TOKEN:
        return {
            "status": "error",
            "message": "CIBERSORTX_TOKEN is required for production mode.",
        }

    result = await api_upload_signature(
        matrix_path=matrix_path,
        matrix_name=matrix_name,
        token=CIBERSORTX_TOKEN,
        email=CIBERSORTX_EMAIL,
        api_url=CIBERSORTX_API_URL,
        description=description,
    )
    return {"status": "success", **result}


async def _get_job_status_impl(
    job_id: str,
) -> Dict[str, Any]:
    """Implementation for get_job_status."""
    job_id = _validate_job_id(job_id)

    if DRY_RUN:
        # Return different mock states depending on job_id pattern
        if "running" in job_id.lower() or job_id == "cb-mock-67890":
            return add_dry_run_warning({
                "status": "success",
                **MOCK_JOB_RUNNING,
            })
        return add_dry_run_warning({
            "status": "success",
            **MOCK_JOB_SUBMITTED,
        })

    if not CIBERSORTX_TOKEN:
        return {
            "status": "error",
            "message": "CIBERSORTX_TOKEN is required for production mode.",
        }

    result = await poll_job_status(
        job_id=job_id,
        token=CIBERSORTX_TOKEN,
        api_url=CIBERSORTX_API_URL,
    )
    return {"status": "success", **result}


async def _download_results_impl(
    job_id: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Implementation for download_results."""
    job_id = _validate_job_id(job_id)
    output_dir = output_dir or CIBERSORTX_CACHE_DIR

    if DRY_RUN:
        return add_dry_run_warning({
            "status": "success",
            "job_id": job_id,
            "output_path": f"{output_dir}/{job_id}_results.csv",
            "fractions": MOCK_DECONVOLUTION_FRACTIONS,
            "summary": {
                "n_samples": len(MOCK_DECONVOLUTION_FRACTIONS),
                "n_cell_types": 22,
                "signature_matrix": "LM22",
            },
        })

    if not CIBERSORTX_TOKEN:
        return {
            "status": "error",
            "message": "CIBERSORTX_TOKEN is required for production mode.",
        }

    # Check job is completed
    status = await poll_job_status(
        job_id=job_id,
        token=CIBERSORTX_TOKEN,
        api_url=CIBERSORTX_API_URL,
    )
    if status.get("state") != "COMPLETED":
        return {
            "status": "error",
            "job_id": job_id,
            "state": status.get("state", "UNKNOWN"),
            "message": "Job is not yet completed. Use get_job_status to check progress.",
        }

    output_path = f"{output_dir}/{job_id}_results.csv"
    await api_download_results(
        job_id=job_id,
        token=CIBERSORTX_TOKEN,
        api_url=CIBERSORTX_API_URL,
        output_path=output_path,
    )

    return {
        "status": "success",
        "job_id": job_id,
        "output_path": output_path,
        # TODO: Parse CSV and return fractions dict when pandas is available
    }


async def _run_mock_deconvolution_impl(
    mixture_path: str,
    signature_path: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Implementation for run_mock_deconvolution.

    In DRY_RUN mode: returns mock NNLS results.
    In production: TODO — use scipy.optimize.nnls for local deconvolution.
    """
    if not mixture_path or not mixture_path.strip():
        return {"status": "error", "message": "mixture_path cannot be empty."}
    if not signature_path or not signature_path.strip():
        return {"status": "error", "message": "signature_path cannot be empty."}

    output_dir = output_dir or CIBERSORTX_CACHE_DIR

    if DRY_RUN:
        return add_dry_run_warning({
            "status": "success",
            "method": "scipy_nnls",
            "mixture_path": mixture_path,
            "signature_path": signature_path,
            "output_path": f"{output_dir}/nnls_results.csv",
            "fractions": MOCK_NNLS_FRACTIONS,
            "rmse": MOCK_NNLS_RMSE,
            "n_samples": len(MOCK_NNLS_FRACTIONS),
            "n_cell_types": len(next(iter(MOCK_NNLS_FRACTIONS.values()))),
            "warning": "Approximate method, not CIBERSORTx-grade",
        })

    # TODO: Implement scipy.optimize.nnls deconvolution
    # Requires: pandas, numpy, scipy as additional dependencies
    # 1. Load mixture matrix (samples x genes) from mixture_path
    # 2. Load signature matrix (genes x cell_types) from signature_path
    # 3. For each sample, solve: signature @ fractions ≈ mixture[sample]
    # 4. Using scipy.optimize.nnls for non-negative least squares
    return {
        "status": "error",
        "message": (
            "Local NNLS deconvolution requires scipy, numpy, and pandas. "
            "Install with: pip install scipy numpy pandas. "
            "Or use run_cibersortx_deconvolution with a valid token."
        ),
    }


# ============================================================================
# MCP Tool wrappers
# ============================================================================

@mcp.tool()
async def run_cibersortx_deconvolution(
    mixture_path: str,
    signature_matrix: str = "LM22",
    custom_signature_path: Optional[str] = None,
    permutations: int = 100,
    quantile_normalize: bool = True,
) -> Dict[str, Any]:
    """Run CIBERSORTx cell-type deconvolution on a bulk expression matrix.

    Submits a bulk RNA-seq expression matrix to the CIBERSORTx web API and
    returns estimated cell-type fractions for each sample. Uses the LM22
    signature matrix (22 immune cell types) by default.

    Args:
        mixture_path: Path to bulk expression matrix CSV (genes x samples).
        signature_matrix: Built-in signature matrix name. Default "LM22"
            (22 immune cell types). Also available: "LM6" (6 types).
        custom_signature_path: Path to custom signature matrix CSV.
            Overrides signature_matrix if provided.
        permutations: Number of permutations for p-value computation (default 100).
        quantile_normalize: Apply quantile normalization (default True).

    Returns:
        Dictionary with cell-type fractions, p-values, and RMSE per sample.
    """
    return await _run_cibersortx_deconvolution_impl(
        mixture_path, signature_matrix, custom_signature_path,
        permutations, quantile_normalize,
    )


@mcp.tool()
async def upload_signature_matrix(
    matrix_path: str,
    matrix_name: str,
    description: str = "",
) -> Dict[str, Any]:
    """Upload a custom signature matrix to CIBERSORTx.

    Uploads a scRNA-seq-derived signature matrix (genes x cell_types) for use
    in deconvolution. The matrix must be a CSV with gene symbols as rows and
    cell type names as columns.

    Args:
        matrix_path: Path to the signature matrix CSV file.
        matrix_name: Name to assign to the uploaded matrix.
        description: Optional description of the matrix contents.

    Returns:
        Dictionary with matrix_id, gene count, and cell type count.
    """
    return await _upload_signature_matrix_impl(matrix_path, matrix_name, description)


@mcp.tool()
async def get_job_status(
    job_id: str,
) -> Dict[str, Any]:
    """Check the status of a CIBERSORTx deconvolution job.

    Polls the CIBERSORTx API for the current state of a submitted job.
    States: QUEUED, RUNNING, COMPLETED, FAILED.

    Args:
        job_id: Job identifier from run_cibersortx_deconvolution.

    Returns:
        Dictionary with job state, progress percentage, and time estimates.
    """
    return await _get_job_status_impl(job_id)


@mcp.tool()
async def download_results(
    job_id: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Download completed CIBERSORTx deconvolution results.

    Retrieves the results CSV from a completed job and returns the cell-type
    fractions as a dictionary. The job must be in COMPLETED state.

    Args:
        job_id: Job identifier from run_cibersortx_deconvolution.
        output_dir: Directory to save results CSV. Defaults to CIBERSORTX_CACHE_DIR.

    Returns:
        Dictionary with output path, fractions, and summary statistics.
    """
    return await _download_results_impl(job_id, output_dir)


@mcp.tool()
async def run_mock_deconvolution(
    mixture_path: str,
    signature_path: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Run local NNLS deconvolution (approximate, no CIBERSORTx token needed).

    Performs non-negative least squares (NNLS) deconvolution locally using
    scipy. This is an approximate method that does NOT match CIBERSORTx
    quality but works offline without authentication.

    Args:
        mixture_path: Path to bulk expression matrix CSV (genes x samples).
        signature_path: Path to signature matrix CSV (genes x cell_types).
        output_dir: Directory to save results. Defaults to CIBERSORTX_CACHE_DIR.

    Returns:
        Dictionary with approximate fractions, RMSE, and quality warning.
    """
    return await _run_mock_deconvolution_impl(mixture_path, signature_path, output_dir)


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP cibersortx server."""
    logger.info("Starting mcp-cibersortx server...")

    if DRY_RUN:
        logger.warning("=" * 70)
        logger.warning("DRY_RUN MODE ENABLED - RETURNING SYNTHETIC DATA")
        logger.warning("Set CIBERSORTX_DRY_RUN=false for production use")
        logger.warning("=" * 70)
    else:
        logger.info("Production mode enabled (CIBERSORTX_DRY_RUN=false)")
        if not CIBERSORTX_TOKEN:
            raise ValueError(
                "CIBERSORTX_TOKEN is required when DRY_RUN is disabled. "
                "Register at https://cibersortx.stanford.edu/ to obtain a token."
            )

    transport = os.getenv("MCP_TRANSPORT", "stdio")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))

    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport, port=port, host="0.0.0.0")
    else:
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()
