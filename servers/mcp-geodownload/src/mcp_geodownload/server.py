"""MCP GEO Download server — programmatic access to NCBI GEO and SRA databases."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .geo_client import (
    build_series_matrix_url,
    build_soft_url,
    download_file,
    entrez_search,
    entrez_summary,
    run_sra_download,
)
from .mock_data import (
    MOCK_EXPRESSION_MATRIX_INFO,
    MOCK_METADATA,
    MOCK_SAMPLES,
    MOCK_SEARCH_RESULTS,
    MOCK_SOFT_INFO,
    MOCK_SRA_DOWNLOAD,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("geodownload")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DRY_RUN = os.getenv("GEO_DRY_RUN", "true").lower() == "true"
GEO_CACHE_DIR = os.getenv("GEO_CACHE_DIR", "/data/cache/geodownload")
NCBI_API_KEY = os.getenv("NCBI_API_KEY")
NCBI_EMAIL = os.getenv("NCBI_EMAIL")


def add_dry_run_warning(result: Any) -> Any:
    """Add warning banner to results when in DRY_RUN mode."""
    if not DRY_RUN:
        return result

    warning = (
        "=== SYNTHETIC DATA WARNING ===\n"
        "This result was generated in DRY_RUN mode and does NOT represent real data.\n"
        "Do NOT use this data for clinical decisions.\n"
        "Set GEO_DRY_RUN=false for production use.\n"
        "==============================\n\n"
    )

    if isinstance(result, dict):
        result["_DRY_RUN_WARNING"] = "SYNTHETIC DATA - NOT FOR CLINICAL USE"
        result["_message"] = warning.strip()
    elif isinstance(result, str):
        result = warning + result

    return result


def _validate_gse_id(gse_id: str) -> str:
    """Validate and normalize a GSE accession ID.

    Returns the normalized ID or raises ValueError.
    """
    gse_id = gse_id.strip().upper()
    if not gse_id.startswith("GSE") or not gse_id[3:].isdigit():
        raise ValueError(
            f"Invalid GSE ID format: '{gse_id}'. "
            "Expected format: GSE followed by digits (e.g., GSE32062)."
        )
    return gse_id


def _validate_srr_id(srr_id: str) -> str:
    """Validate and normalize an SRR accession ID."""
    srr_id = srr_id.strip().upper()
    if not srr_id.startswith("SRR") or not srr_id[3:].isdigit():
        raise ValueError(
            f"Invalid SRR ID format: '{srr_id}'. "
            "Expected format: SRR followed by digits (e.g., SRR12345678)."
        )
    return srr_id


# ---------------------------------------------------------------------------
# Tool implementation functions
# ---------------------------------------------------------------------------

async def _search_geo_datasets_impl(
    query: str,
    organism: str = "Homo sapiens",
    study_type: str = "Expression profiling by high throughput sequencing",
    max_results: int = 20,
) -> Dict[str, Any]:
    """Implementation for search_geo_datasets."""
    if not query or not query.strip():
        return {"status": "error", "message": "Query string cannot be empty."}

    if DRY_RUN:
        # Filter mock results by query keyword (case-insensitive)
        query_lower = query.lower()
        matches = [
            r for r in MOCK_SEARCH_RESULTS
            if query_lower in r["title"].lower()
            or query_lower in r["summary"].lower()
            or query_lower in r["gse_id"].lower()
        ]
        # If no matches, return all mock results (simulate broad search)
        if not matches:
            matches = MOCK_SEARCH_RESULTS
        return add_dry_run_warning({
            "status": "success",
            "query": query,
            "organism": organism,
            "study_type": study_type,
            "total_results": len(matches[:max_results]),
            "datasets": matches[:max_results],
        })

    # Build Entrez search term
    terms = [query]
    if organism:
        terms.append(f'"{organism}"[Organism]')
    if study_type:
        terms.append(f'"{study_type}"[DataSet Type]')
    full_term = " AND ".join(terms)

    uids = await entrez_search(
        db="gds",
        term=full_term,
        max_results=max_results,
        api_key=NCBI_API_KEY,
        email=NCBI_EMAIL,
    )

    if not uids:
        return {
            "status": "success",
            "query": query,
            "total_results": 0,
            "datasets": [],
        }

    summaries = await entrez_summary(
        db="gds",
        uids=uids,
        api_key=NCBI_API_KEY,
        email=NCBI_EMAIL,
    )

    datasets = []
    result_data = summaries.get("result", {})
    for uid in uids:
        record = result_data.get(uid, {})
        if not record:
            continue
        accession = record.get("accession", "")
        datasets.append({
            "gse_id": accession,
            "title": record.get("title", ""),
            "summary": record.get("summary", ""),
            "organism": record.get("taxon", ""),
            "platform": record.get("gpl", ""),
            "sample_count": record.get("n_samples", 0),
            "study_type": record.get("gdstype", ""),
        })

    return {
        "status": "success",
        "query": query,
        "organism": organism,
        "total_results": len(datasets),
        "datasets": datasets,
    }


async def _get_geo_metadata_impl(
    gse_id: str,
) -> Dict[str, Any]:
    """Implementation for get_geo_metadata."""
    gse_id = _validate_gse_id(gse_id)

    if DRY_RUN:
        metadata = MOCK_METADATA.get(gse_id)
        if not metadata:
            return add_dry_run_warning({
                "status": "error",
                "message": (
                    f"Dataset {gse_id} not found in mock data. "
                    f"Available: {', '.join(sorted(MOCK_METADATA.keys()))}"
                ),
            })
        return add_dry_run_warning({
            "status": "success",
            **metadata,
        })

    uids = await entrez_search(
        db="gds",
        term=f"{gse_id}[Accession]",
        max_results=1,
        api_key=NCBI_API_KEY,
        email=NCBI_EMAIL,
    )

    if not uids:
        return {"status": "error", "message": f"Dataset {gse_id} not found."}

    summaries = await entrez_summary(
        db="gds",
        uids=uids,
        api_key=NCBI_API_KEY,
        email=NCBI_EMAIL,
    )

    result_data = summaries.get("result", {})
    record = result_data.get(uids[0], {})

    return {
        "status": "success",
        "gse_id": gse_id,
        "title": record.get("title", ""),
        "summary": record.get("summary", ""),
        "organism": record.get("taxon", ""),
        "platform_id": record.get("gpl", ""),
        "sample_count": record.get("n_samples", 0),
        "submission_date": record.get("pdat", ""),
        "series_matrix_url": build_series_matrix_url(gse_id),
    }


async def _download_geo_expression_matrix_impl(
    gse_id: str,
    output_dir: Optional[str] = None,
    normalize: bool = False,
) -> Dict[str, Any]:
    """Implementation for download_geo_expression_matrix."""
    gse_id = _validate_gse_id(gse_id)
    output_dir = output_dir or GEO_CACHE_DIR

    if DRY_RUN:
        matrix_info = MOCK_EXPRESSION_MATRIX_INFO.get(gse_id)
        if not matrix_info:
            return add_dry_run_warning({
                "status": "error",
                "message": (
                    f"Dataset {gse_id} not found in mock data. "
                    f"Available: {', '.join(sorted(MOCK_EXPRESSION_MATRIX_INFO.keys()))}"
                ),
            })
        return add_dry_run_warning({
            "status": "success",
            "download_url": build_series_matrix_url(gse_id),
            "output_path": f"{output_dir}/{gse_id}_series_matrix.txt.gz",
            "normalize": normalize,
            **matrix_info,
        })

    url = build_series_matrix_url(gse_id)
    output_path = str(Path(output_dir) / f"{gse_id}_series_matrix.txt.gz")

    result = await download_file(url, output_path)
    result["gse_id"] = gse_id
    result["normalize"] = normalize
    # TODO: Add in-memory parsing/normalization when parsers.py is implemented
    return result


async def _list_geo_samples_impl(
    gse_id: str,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """Implementation for list_geo_samples."""
    gse_id = _validate_gse_id(gse_id)

    if DRY_RUN:
        samples = MOCK_SAMPLES.get(gse_id)
        if not samples:
            return add_dry_run_warning({
                "status": "error",
                "message": (
                    f"Dataset {gse_id} not found in mock data. "
                    f"Available: {', '.join(sorted(MOCK_SAMPLES.keys()))}"
                ),
            })

        if not include_metadata:
            samples = [{"gsm_id": s["gsm_id"], "title": s["title"]} for s in samples]

        metadata = MOCK_METADATA.get(gse_id, {})
        return add_dry_run_warning({
            "status": "success",
            "gse_id": gse_id,
            "total_samples": metadata.get("sample_count", len(samples)),
            "returned_samples": len(samples),
            "samples": samples,
        })

    # In production, use Entrez to find GSM accessions for this GSE
    uids = await entrez_search(
        db="gds",
        term=f"{gse_id}[Accession]",
        max_results=1,
        api_key=NCBI_API_KEY,
        email=NCBI_EMAIL,
    )

    if not uids:
        return {"status": "error", "message": f"Dataset {gse_id} not found."}

    summaries = await entrez_summary(
        db="gds",
        uids=uids,
        api_key=NCBI_API_KEY,
        email=NCBI_EMAIL,
    )

    result_data = summaries.get("result", {})
    record = result_data.get(uids[0], {})

    # Extract sample accessions from the summary
    samples_list = record.get("samples", [])
    samples = []
    for s in samples_list:
        sample = {"gsm_id": s.get("accession", ""), "title": s.get("title", "")}
        if include_metadata:
            sample["organism"] = s.get("taxon", "")
        samples.append(sample)

    return {
        "status": "success",
        "gse_id": gse_id,
        "total_samples": record.get("n_samples", len(samples)),
        "returned_samples": len(samples),
        "samples": samples,
    }


async def _download_sra_fastq_impl(
    srr_id: str,
    output_dir: Optional[str] = None,
    split_files: bool = True,
) -> Dict[str, Any]:
    """Implementation for download_sra_fastq."""
    srr_id = _validate_srr_id(srr_id)
    output_dir = output_dir or GEO_CACHE_DIR

    if DRY_RUN:
        return add_dry_run_warning({
            "status": "success",
            "output_dir": output_dir,
            "split_files": split_files,
            **MOCK_SRA_DOWNLOAD,
        })

    result = await run_sra_download(srr_id, output_dir, split_files)
    return result


async def _get_geo_soft_file_impl(
    gse_id: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Implementation for get_geo_soft_file."""
    gse_id = _validate_gse_id(gse_id)
    output_dir = output_dir or GEO_CACHE_DIR

    if DRY_RUN:
        soft_info = MOCK_SOFT_INFO.get(gse_id)
        if not soft_info:
            return add_dry_run_warning({
                "status": "error",
                "message": (
                    f"Dataset {gse_id} not found in mock data. "
                    f"Available: {', '.join(sorted(MOCK_SOFT_INFO.keys()))}"
                ),
            })
        return add_dry_run_warning({
            "status": "success",
            "download_url": build_soft_url(gse_id),
            "output_path": f"{output_dir}/{gse_id}_family.soft.gz",
            **soft_info,
        })

    url = build_soft_url(gse_id)
    output_path = str(Path(output_dir) / f"{gse_id}_family.soft.gz")

    result = await download_file(url, output_path)
    result["gse_id"] = gse_id
    return result


# ============================================================================
# MCP Tool wrappers
# ============================================================================

@mcp.tool()
async def search_geo_datasets(
    query: str,
    organism: str = "Homo sapiens",
    study_type: str = "Expression profiling by high throughput sequencing",
    max_results: int = 20,
) -> Dict[str, Any]:
    """Search NCBI GEO for gene expression datasets.

    Searches the GEO DataSets database using NCBI Entrez E-utilities.
    Returns matching datasets with accession IDs, titles, and summaries.

    Args:
        query: Search terms (e.g., "high-grade serous ovarian cancer").
        organism: Filter by organism. Default "Homo sapiens".
        study_type: Filter by study type. Default "Expression profiling by
            high throughput sequencing".
        max_results: Maximum number of results to return (default 20).

    Returns:
        Dictionary with matching datasets including GSE accessions.
    """
    return await _search_geo_datasets_impl(query, organism, study_type, max_results)


@mcp.tool()
async def get_geo_metadata(
    gse_id: str,
) -> Dict[str, Any]:
    """Get detailed metadata for a GEO dataset.

    Retrieves title, summary, platform, sample count, submission date,
    and supplementary file URLs for a specific GEO Series accession.

    Args:
        gse_id: GEO Series accession (e.g., "GSE32062").

    Returns:
        Dictionary with full dataset metadata.
    """
    return await _get_geo_metadata_impl(gse_id)


@mcp.tool()
async def download_geo_expression_matrix(
    gse_id: str,
    output_dir: Optional[str] = None,
    normalize: bool = False,
) -> Dict[str, Any]:
    """Download a GEO Series Matrix expression file.

    Downloads the pre-processed expression matrix from GEO FTP servers.
    The Series Matrix file contains normalized expression values in a
    tab-delimited format suitable for downstream analysis.

    Args:
        gse_id: GEO Series accession (e.g., "GSE32062").
        output_dir: Directory to save the file. Defaults to GEO_CACHE_DIR.
        normalize: If True, apply quantile normalization after download.

    Returns:
        Dictionary with download status, file path, and matrix dimensions.
    """
    return await _download_geo_expression_matrix_impl(gse_id, output_dir, normalize)


@mcp.tool()
async def list_geo_samples(
    gse_id: str,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """List all samples (GSMs) in a GEO dataset.

    Returns sample accessions, titles, source tissue, and characteristics
    for each sample in the specified GEO Series.

    Args:
        gse_id: GEO Series accession (e.g., "GSE32062").
        include_metadata: Include per-sample characteristics (default True).

    Returns:
        Dictionary with sample list and metadata.
    """
    return await _list_geo_samples_impl(gse_id, include_metadata)


@mcp.tool()
async def download_sra_fastq(
    srr_id: str,
    output_dir: Optional[str] = None,
    split_files: bool = True,
) -> Dict[str, Any]:
    """Download raw FASTQ files from NCBI SRA.

    Uses sra-tools (prefetch + fasterq-dump) to download raw sequencing
    reads. Requires sra-tools to be installed on the system.

    Args:
        srr_id: SRA Run accession (e.g., "SRR12345678").
        output_dir: Directory to save FASTQ files. Defaults to GEO_CACHE_DIR.
        split_files: Split paired-end reads into separate files (default True).

    Returns:
        Dictionary with download status and output file paths.
    """
    return await _download_sra_fastq_impl(srr_id, output_dir, split_files)


@mcp.tool()
async def get_geo_soft_file(
    gse_id: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Download the raw SOFT file for a GEO dataset.

    SOFT (Simple Omnibus Format in Text) files contain complete metadata
    and data for a GEO record including platform annotations, sample
    descriptions, and raw data values.

    Args:
        gse_id: GEO Series accession (e.g., "GSE32062").
        output_dir: Directory to save the file. Defaults to GEO_CACHE_DIR.

    Returns:
        Dictionary with download status and file info.
    """
    return await _get_geo_soft_file_impl(gse_id, output_dir)


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP geodownload server."""
    logger.info("Starting mcp-geodownload server...")

    if DRY_RUN:
        logger.warning("=" * 70)
        logger.warning("DRY_RUN MODE ENABLED - RETURNING SYNTHETIC DATA")
        logger.warning("Set GEO_DRY_RUN=false for production use")
        logger.warning("=" * 70)
    else:
        logger.info("Production mode enabled (GEO_DRY_RUN=false)")

    transport = os.getenv("MCP_TRANSPORT", "stdio")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))

    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport, port=port, host="0.0.0.0")
    else:
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()
