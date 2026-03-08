"""CIBERSORTx REST API client for job submission, polling, and result download."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=60)
DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=300)


async def submit_job(
    mixture_path: str,
    signature_matrix: str,
    token: str,
    email: str,
    api_url: str,
    custom_signature_path: Optional[str] = None,
    permutations: int = 100,
    quantile_normalize: bool = True,
) -> Dict[str, Any]:
    """Submit a deconvolution job to the CIBERSORTx API.

    Args:
        mixture_path: Path to the bulk expression matrix CSV file.
        signature_matrix: Name of built-in signature matrix (e.g., "LM22").
        token: CIBERSORTx API authentication token.
        email: Email registered with CIBERSORTx.
        api_url: Base URL for the CIBERSORTx API.
        custom_signature_path: Path to custom signature matrix (overrides signature_matrix).
        permutations: Number of permutations for statistical analysis.
        quantile_normalize: Whether to apply quantile normalization.

    Returns:
        Dict with job_id and submission status.
    """
    headers = {
        "Authorization": f"Bearer {token}",
    }

    data = aiohttp.FormData()
    data.add_field("email", email)
    data.add_field("signature_matrix", signature_matrix)
    data.add_field("permutations", str(permutations))
    data.add_field("quantile_normalize", str(quantile_normalize).lower())

    mixture_file = Path(mixture_path)
    data.add_field(
        "mixture_file",
        open(mixture_file, "rb"),
        filename=mixture_file.name,
        content_type="text/csv",
    )

    if custom_signature_path:
        sig_file = Path(custom_signature_path)
        data.add_field(
            "custom_signature_file",
            open(sig_file, "rb"),
            filename=sig_file.name,
            content_type="text/csv",
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_url}/submit",
            data=data,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(
                    f"CIBERSORTx submit returned status {resp.status}: {text[:500]}"
                )
            return await resp.json()


async def poll_job_status(
    job_id: str,
    token: str,
    api_url: str,
) -> Dict[str, Any]:
    """Poll the status of a CIBERSORTx job.

    Args:
        job_id: Job identifier returned from submit_job.
        token: CIBERSORTx API authentication token.
        api_url: Base URL for the CIBERSORTx API.

    Returns:
        Dict with job state, progress, and timing info.
    """
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{api_url}/status/{job_id}",
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(
                    f"CIBERSORTx status returned {resp.status}: {text[:500]}"
                )
            return await resp.json()


async def wait_for_completion(
    job_id: str,
    token: str,
    api_url: str,
    poll_interval: int = 30,
    max_wait: int = 1800,
) -> Dict[str, Any]:
    """Poll a CIBERSORTx job until completion or timeout.

    Args:
        job_id: Job identifier.
        token: CIBERSORTx API authentication token.
        api_url: Base URL for the CIBERSORTx API.
        poll_interval: Seconds between status checks.
        max_wait: Maximum seconds to wait before returning.

    Returns:
        Final job status dict. State will be COMPLETED, FAILED, or last polled state.
    """
    elapsed = 0
    while elapsed < max_wait:
        status = await poll_job_status(job_id, token, api_url)
        state = status.get("state", "UNKNOWN")

        if state in ("COMPLETED", "FAILED"):
            return status

        logger.info(
            "Job %s: %s (%d%% complete, ~%ds remaining)",
            job_id,
            state,
            status.get("progress_pct", 0),
            status.get("estimated_remaining_seconds", 0),
        )

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    # Timed out — return last known status
    logger.warning("Job %s: timed out after %ds", job_id, max_wait)
    status["_timeout"] = True
    return status


async def download_results(
    job_id: str,
    token: str,
    api_url: str,
    output_path: str,
) -> Dict[str, Any]:
    """Download completed job results from CIBERSORTx.

    Args:
        job_id: Job identifier.
        token: CIBERSORTx API authentication token.
        api_url: Base URL for the CIBERSORTx API.
        output_path: Local path to save the results CSV.

    Returns:
        Dict with download status and file info.
    """
    headers = {"Authorization": f"Bearer {token}"}
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{api_url}/results/{job_id}",
            headers=headers,
            timeout=DOWNLOAD_TIMEOUT,
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(
                    f"CIBERSORTx results returned {resp.status}: {text[:500]}"
                )

            total_bytes = 0
            with open(output, "wb") as f:
                async for chunk in resp.content.iter_chunked(8192):
                    f.write(chunk)
                    total_bytes += len(chunk)

    return {
        "status": "success",
        "file_path": str(output),
        "size_bytes": total_bytes,
    }


async def upload_signature_matrix(
    matrix_path: str,
    matrix_name: str,
    token: str,
    email: str,
    api_url: str,
    description: str = "",
) -> Dict[str, Any]:
    """Upload a custom signature matrix to CIBERSORTx.

    Args:
        matrix_path: Path to the signature matrix CSV (genes x cell_types).
        matrix_name: Name to assign to the uploaded matrix.
        token: CIBERSORTx API authentication token.
        email: Email registered with CIBERSORTx.
        api_url: Base URL for the CIBERSORTx API.
        description: Optional description of the matrix.

    Returns:
        Dict with matrix_id and upload metadata.
    """
    headers = {"Authorization": f"Bearer {token}"}

    data = aiohttp.FormData()
    data.add_field("email", email)
    data.add_field("matrix_name", matrix_name)
    data.add_field("description", description)

    matrix_file = Path(matrix_path)
    data.add_field(
        "matrix_file",
        open(matrix_file, "rb"),
        filename=matrix_file.name,
        content_type="text/csv",
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_url}/signature/upload",
            data=data,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(
                    f"CIBERSORTx upload returned {resp.status}: {text[:500]}"
                )
            return await resp.json()
