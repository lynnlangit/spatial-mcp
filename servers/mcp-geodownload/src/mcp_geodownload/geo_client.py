"""Entrez REST API client and FTP URL builders for NCBI GEO/SRA access."""

import asyncio
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENTREZ_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GEO_FTP_BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series"

# NCBI allows 3 requests/sec without API key, 10/sec with key
_rate_semaphore = asyncio.Semaphore(3)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=30)
DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=600)


# ---------------------------------------------------------------------------
# Entrez REST helpers
# ---------------------------------------------------------------------------

async def entrez_search(
    db: str,
    term: str,
    max_results: int = 20,
    api_key: Optional[str] = None,
    email: Optional[str] = None,
    api_url: str = ENTREZ_BASE_URL,
) -> List[str]:
    """Search an NCBI Entrez database and return a list of UIDs.

    Args:
        db: Entrez database name (e.g., "gds" for GEO DataSets).
        term: Search query string.
        max_results: Maximum number of UIDs to return.
        api_key: Optional NCBI API key for higher rate limits.
        email: Optional email for NCBI identification.
        api_url: Base URL for Entrez E-utilities.

    Returns:
        List of UID strings from the search result.
    """
    params: Dict[str, Any] = {
        "db": db,
        "term": term,
        "retmax": max_results,
        "retmode": "json",
    }
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email

    async with _rate_semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_url}/esearch.fcgi",
                params=params,
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(
                        f"Entrez esearch returned status {resp.status}: {text[:500]}"
                    )
                data = await resp.json()
                return data.get("esearchresult", {}).get("idlist", [])


async def entrez_summary(
    db: str,
    uids: List[str],
    api_key: Optional[str] = None,
    email: Optional[str] = None,
    api_url: str = ENTREZ_BASE_URL,
) -> Dict[str, Any]:
    """Fetch summary records for a list of UIDs from an Entrez database.

    Args:
        db: Entrez database name.
        uids: List of UID strings to fetch.
        api_key: Optional NCBI API key.
        email: Optional email for NCBI identification.
        api_url: Base URL for Entrez E-utilities.

    Returns:
        Parsed JSON summary result dict.
    """
    if not uids:
        return {"result": {}}

    params: Dict[str, Any] = {
        "db": db,
        "id": ",".join(uids),
        "retmode": "json",
    }
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email

    async with _rate_semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_url}/esummary.fcgi",
                params=params,
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(
                        f"Entrez esummary returned status {resp.status}: {text[:500]}"
                    )
                return await resp.json()


# ---------------------------------------------------------------------------
# File download
# ---------------------------------------------------------------------------

async def download_file(
    url: str,
    output_path: str,
) -> Dict[str, Any]:
    """Download a file via streaming HTTP GET.

    Args:
        url: URL of the file to download.
        output_path: Local filesystem path to write the file.

    Returns:
        Dict with download status, file path, and size.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=DOWNLOAD_TIMEOUT) as resp:
            if resp.status != 200:
                raise RuntimeError(
                    f"Download failed with status {resp.status}: {url}"
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
        "url": url,
    }


# ---------------------------------------------------------------------------
# FTP URL builders
# ---------------------------------------------------------------------------

def build_series_matrix_url(gse_id: str) -> str:
    """Construct the FTP URL for a GEO Series Matrix file.

    Args:
        gse_id: GEO Series accession (e.g., "GSE32062").

    Returns:
        Full URL to the series matrix .txt.gz file.
    """
    gse_id = gse_id.upper()
    # GSE32062 -> GSE32nnn
    prefix = gse_id[:len(gse_id) - 3] + "nnn"
    return (
        f"{GEO_FTP_BASE}/{prefix}/{gse_id}/matrix/"
        f"{gse_id}_series_matrix.txt.gz"
    )


def build_soft_url(gse_id: str) -> str:
    """Construct the FTP URL for a GEO SOFT file.

    Args:
        gse_id: GEO Series accession (e.g., "GSE32062").

    Returns:
        Full URL to the family.soft.gz file.
    """
    gse_id = gse_id.upper()
    prefix = gse_id[:len(gse_id) - 3] + "nnn"
    return (
        f"{GEO_FTP_BASE}/{prefix}/{gse_id}/soft/"
        f"{gse_id}_family.soft.gz"
    )


# ---------------------------------------------------------------------------
# SRA download wrapper
# ---------------------------------------------------------------------------

async def run_sra_download(
    srr_id: str,
    output_dir: str,
    split_files: bool = True,
) -> Dict[str, Any]:
    """Download FASTQ files from SRA using prefetch + fasterq-dump.

    Requires sra-tools to be installed (prefetch, fasterq-dump).

    Args:
        srr_id: SRA run accession (e.g., "SRR12345678").
        output_dir: Directory to write output FASTQ files.
        split_files: If True, split paired-end reads into separate files.

    Returns:
        Dict with download status and output file paths.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Step 1: prefetch
    prefetch_cmd = ["prefetch", srr_id, "--output-directory", str(output)]
    proc = await asyncio.create_subprocess_exec(
        *prefetch_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            f"prefetch failed (rc={proc.returncode}): {stderr.decode()[:500]}"
        )

    # Step 2: fasterq-dump
    fasterq_cmd = [
        "fasterq-dump",
        str(output / srr_id / f"{srr_id}.sra"),
        "--outdir", str(output),
        "--threads", "4",
    ]
    if split_files:
        fasterq_cmd.append("--split-files")

    proc = await asyncio.create_subprocess_exec(
        *fasterq_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            f"fasterq-dump failed (rc={proc.returncode}): {stderr.decode()[:500]}"
        )

    # Collect output files
    fastq_files = sorted(output.glob(f"{srr_id}*.fastq*"))
    return {
        "status": "success",
        "srr_id": srr_id,
        "output_dir": str(output),
        "files": [str(f) for f in fastq_files],
    }
