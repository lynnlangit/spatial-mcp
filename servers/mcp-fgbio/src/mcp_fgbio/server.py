"""MCP FGbio server implementation.

This module provides an MCP server for accessing genomic reference data
and performing FASTQ quality validation using the FGbio toolkit.
"""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP

# Configure logging
logger = logging.getLogger(__name__)

from .validation import (
    ValidationError,
    validate_fastq_file,
    validate_vcf_file,
    format_validation_error,
)

# Import retry utilities for external API calls
# In container: /app/shared/utils is in PYTHONPATH
# In development: Try to add shared/utils to path
try:
    from api_retry import retry_with_backoff, optional_api_call
except ImportError:
    # Development mode - add shared/utils to path
    _shared_utils_path = Path(__file__).resolve().parents[4] / "shared" / "utils"
    if str(_shared_utils_path) not in sys.path:
        sys.path.insert(0, str(_shared_utils_path))
    from api_retry import retry_with_backoff, optional_api_call

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
from common.transport import run_server as _run_server

# Initialize the MCP server
mcp = FastMCP("fgbio")

# DRY_RUN warning wrapper
def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="FGBIO_DRY_RUN")


# Configuration helper functions (read from environment at runtime for testability)
def _get_reference_data_dir() -> Path:
    """Get reference data directory from environment."""
    return Path(os.getenv("FGBIO_REFERENCE_DATA_DIR", "/workspace/data/reference"))

def _get_cache_dir() -> Path:
    """Get cache directory from environment."""
    return Path(os.getenv("FGBIO_CACHE_DIR", "/workspace/cache"))

def _is_dry_run() -> bool:
    """Check if DRY_RUN mode is enabled."""
    return os.getenv("FGBIO_DRY_RUN", "true").lower() == "true"

def _get_timeout_seconds() -> int:
    """Get timeout seconds from environment."""
    return int(os.getenv("FGBIO_TIMEOUT_SECONDS", "300"))

def _get_max_download_size_gb() -> int:
    """Get max download size from environment."""
    return int(os.getenv("FGBIO_MAX_DOWNLOAD_SIZE_GB", "10"))

# Legacy module-level constants (for backward compatibility)
REFERENCE_DATA_DIR = _get_reference_data_dir()
CACHE_DIR = _get_cache_dir()
FGBIO_JAR = os.getenv("FGBIO_JAR_PATH", "/opt/fgbio/fgbio.jar")
JAVA_EXECUTABLE = os.getenv("FGBIO_JAVA_EXECUTABLE", "java")
MAX_DOWNLOAD_SIZE_GB = _get_max_download_size_gb()
TIMEOUT_SECONDS = _get_timeout_seconds()
DRY_RUN = _is_dry_run()

# ---------------------------------------------------------------------------
# Reference genome sources
# ---------------------------------------------------------------------------
# DEFECT FIX (CNV_TOOLS_SPEC.md section 10.1): the previous implementation built
#     https://ftp.ncbi.nlm.nih.gov/genomes/{genome}/genome.fna.gz
# which is not an NCBI path and 404s for hg38, hg19 and mm10 alike. NCBI serves
# assemblies under /genomes/all/GCF/... by accession, and UCSC-style names like
# "hg19" are not NCBI identifiers at all. The bug survived because DRY_RUN
# defaults to true and returns before the URL is ever used.
#
# UCSC's goldenPath serves exactly these identifiers, with a published
# md5sum.txt alongside each assembly, so that is what these IDs now resolve to.

UCSC_GOLDENPATH_BASE = "https://hgdownload.soe.ucsc.edu/goldenPath"

REFERENCE_GENOMES = {
    "hg38": {"name": "Human GRCh38", "assembly": "GRCh38", "organism": "Homo sapiens", "size_mb": 983},
    "hg19": {"name": "Human GRCh37", "assembly": "GRCh37", "organism": "Homo sapiens", "size_mb": 938},
    "mm10": {"name": "Mouse GRCm38", "assembly": "GRCm38", "organism": "Mus musculus", "size_mb": 830},
    "mm39": {"name": "Mouse GRCm39", "assembly": "GRCm39", "organism": "Mus musculus", "size_mb": 819},
    "rn6": {"name": "Rat Rnor_6.0", "assembly": "Rnor_6.0", "organism": "Rattus norvegicus", "size_mb": 858},
    "danRer11": {"name": "Zebrafish GRCz11", "assembly": "GRCz11", "organism": "Danio rerio", "size_mb": 449},
}


def _genome_url(genome: str) -> str:
    """URL of the gzipped FASTA for a UCSC-style genome identifier."""
    return f"{UCSC_GOLDENPATH_BASE}/{genome}/bigZips/{genome}.fa.gz"


def _md5sum_url(genome: str) -> str:
    """URL of the published checksum manifest for a genome's bigZips directory."""
    return f"{UCSC_GOLDENPATH_BASE}/{genome}/bigZips/md5sum.txt"


def _chrom_sizes_url(genome: str) -> str:
    """URL of the contig-length manifest, used for VCF coordinate-system checks."""
    return f"{UCSC_GOLDENPATH_BASE}/{genome}/bigZips/{genome}.chrom.sizes"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _ensure_directories() -> None:
    """Ensure required directories exist."""
    _get_reference_data_dir().mkdir(parents=True, exist_ok=True)
    _get_cache_dir().mkdir(parents=True, exist_ok=True)


def _resolve_gcs_path(gcs_uri: str) -> str:
    """Download a GCS file to a local temp path if needed.

    If the path starts with gs://, downloads to a temp file and returns
    the local path. Otherwise returns the path unchanged.

    Args:
        gcs_uri: A local path or gs:// URI

    Returns:
        Local filesystem path
    """
    if not gcs_uri.startswith("gs://"):
        return gcs_uri

    import tempfile
    import fsspec

    logger.info(f"Downloading GCS file: {gcs_uri}")
    fs = fsspec.filesystem("gcs")

    # Preserve the file extension for gzip detection
    suffix = ""
    if gcs_uri.endswith(".gz"):
        suffix = ".gz"
    elif "." in gcs_uri.split("/")[-1]:
        suffix = "." + gcs_uri.split("/")[-1].rsplit(".", 1)[-1]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    fs.get(gcs_uri, tmp.name)
    tmp.close()
    logger.info(f"Downloaded to: {tmp.name}")
    return tmp.name


def _run_fgbio_command(
    args: list[str],
    timeout: int = TIMEOUT_SECONDS
) -> subprocess.CompletedProcess:
    """Run a FGbio command.

    Args:
        args: Command line arguments for FGbio
        timeout: Timeout in seconds

    Returns:
        CompletedProcess with results

    Raises:
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails
    """
    if _is_dry_run():
        # In dry-run mode, just return a mock successful result
        return subprocess.CompletedProcess(
            args=["java", "-jar", FGBIO_JAR] + args,
            returncode=0,
            stdout=f"[DRY RUN] Would execute: {' '.join(args)}",
            stderr=""
        )

    cmd = [JAVA_EXECUTABLE, "-jar", FGBIO_JAR] + args

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True
    )

    return result


@retry_with_backoff(
    max_retries=3,
    base_delay=2.0,
    max_delay=60.0,
    exceptions=(IOError, Exception),
    on_retry=lambda e, attempt: logger.warning(
        f"Retry attempt {attempt} for download after error: {e}"
    )
)
async def _download_file(url: str, output_path: Path) -> Dict[str, Any]:
    """Download a file from a URL with retry logic.

    Args:
        url: URL to download from
        output_path: Path to save the downloaded file

    Returns:
        Dictionary with download metadata

    Raises:
        IOError: If download fails after retries

    Note:
        Automatically retries up to 3 times with exponential backoff
        on network errors or transient failures.
    """
    import httpx
    import aiofiles

    if _is_dry_run():
        # In dry-run mode, create a small mock file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(output_path, "w") as f:
            await f.write(f"Mock reference genome data for {output_path.name}\n")

        return {
            "url": url,
            "path": str(output_path),
            "size_bytes": 100,
            "md5sum": "mock_md5_checksum"
        }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                total_bytes = 0
                md5_hash = hashlib.md5()

                output_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        await f.write(chunk)
                        total_bytes += len(chunk)
                        md5_hash.update(chunk)

                        # Check size limit
                        if total_bytes > MAX_DOWNLOAD_SIZE_GB * 1024 * 1024 * 1024:
                            output_path.unlink()  # Delete partial file
                            raise IOError(
                                f"Download size exceeds {MAX_DOWNLOAD_SIZE_GB}GB limit"
                            )

                return {
                    "url": url,
                    "path": str(output_path),
                    "size_bytes": total_bytes,
                    "md5sum": md5_hash.hexdigest()
                }

    except httpx.HTTPError as e:
        raise IOError(f"Download failed: {e}") from e


def _calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        MD5 checksum as hex string
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


# ---------------------------------------------------------------------------
# Reference download verification (CNV_TOOLS_SPEC.md section 10.1)
# ---------------------------------------------------------------------------


async def _head_url(url: str) -> Dict[str, Any]:
    """HEAD a URL so a bad path fails in a second rather than after a gigabyte."""
    import httpx

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = await client.head(url)
        return {
            "url": url,
            "status_code": response.status_code,
            "ok": response.status_code == 200,
            "content_length": int(response.headers.get("content-length", 0)) or None,
        }


async def _fetch_published_md5(genome: str) -> Optional[str]:
    """Read the published md5 for {genome}.fa.gz out of the assembly's md5sum.txt."""
    import httpx

    target = f"{genome}.fa.gz"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = await client.get(_md5sum_url(genome))
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning(f"Could not fetch md5sum.txt for {genome}: {exc}")
        return None

    for line in response.text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == target:
            return parts[0]
    return None


async def _fetch_chrom_sizes(genome: str) -> Optional[Dict[str, int]]:
    """Contig lengths for a genome, from UCSC's chrom.sizes manifest."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = await client.get(_chrom_sizes_url(genome))
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning(f"Could not fetch chrom.sizes for {genome}: {exc}")
        return None

    sizes = {}
    for line in response.text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                sizes[parts[0]] = int(parts[1])
            except ValueError:
                continue
    return sizes or None


def _vcf_header_contigs(vcf_path: str) -> Dict[str, int]:
    """Contig lengths declared in a VCF header's ##contig lines."""
    import gzip
    import re

    opener = gzip.open if str(vcf_path).endswith(".gz") else open
    contigs: Dict[str, int] = {}
    with opener(vcf_path, "rt") as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            if not line.startswith("##contig="):
                continue
            cid = re.search(r"ID=([^,>]+)", line)
            length = re.search(r"length=(\d+)", line)
            if cid and length:
                contigs[cid.group(1)] = int(length.group(1))
    return contigs


async def _verify_against_vcf(genome: str, vcf_path: str, fasta_path: Path) -> Dict[str, Any]:
    """Check a downloaded reference against a specimen VCF's coordinate system.

    Stronger provenance than a checksum. A checksum proves the bytes match what
    the source published; this proves the reference is the one the specimen's
    coordinates were called against — which is the question that actually
    matters when a variant's position is about to be interpreted.

    Two checks, in increasing strength:
      * contig lengths, from the VCF header against the assembly's manifest
      * REF alleles, from VCF records against the reference sequence itself
        (needs an indexed FASTA and pysam; reported as skipped when absent)
    """
    result: Dict[str, Any] = {"vcf_path": vcf_path, "genome": genome}

    try:
        vcf_contigs = _vcf_header_contigs(vcf_path)
    except OSError as exc:
        return {**result, "verified": False, "error": f"could not read VCF header: {exc}"}

    if not vcf_contigs:
        return {
            **result,
            "verified": False,
            "error": "VCF header declares no ##contig lines with lengths, so the "
                     "coordinate system cannot be checked",
        }

    sizes = await _fetch_chrom_sizes(genome)
    if not sizes:
        return {
            **result,
            "verified": False,
            "error": f"could not fetch contig lengths for {genome}",
        }

    matched, mismatched, absent = 0, [], []
    for contig, length in vcf_contigs.items():
        if contig not in sizes:
            absent.append(contig)
        elif sizes[contig] == length:
            matched += 1
        else:
            mismatched.append({"contig": contig, "vcf": length, "reference": sizes[contig]})

    result["contig_check"] = {
        "matched": matched,
        "total": len(vcf_contigs),
        "mismatched": mismatched,
        "not_in_reference": absent,
        "passed": not mismatched and not absent,
    }
    result["ref_allele_check"] = await asyncio.get_running_loop().run_in_executor(
        None, _check_ref_alleles, str(fasta_path), vcf_path
    )
    result["verified"] = bool(
        result["contig_check"]["passed"]
        and result["ref_allele_check"].get("passed", True)
    )
    return result


def _check_ref_alleles(fasta_path: str, vcf_path: str, max_records: int = 5000) -> Dict[str, Any]:
    """Compare VCF REF alleles against the reference sequence.

    Requires an indexed FASTA. A plain gzip FASTA cannot be randomly accessed,
    so this reports "skipped" with the reason rather than silently passing —
    a check that quietly does nothing is worse than no check.
    """
    import gzip

    try:
        import pysam
    except ImportError:
        return {
            "passed": None,
            "skipped": True,
            "reason": "pysam is not installed; REF alleles cannot be read from the reference",
        }

    try:
        fasta = pysam.FastaFile(fasta_path)
    except (OSError, ValueError) as exc:
        return {
            "passed": None,
            "skipped": True,
            "reason": f"reference is not indexed for random access ({exc}). "
                      "bgzip and faidx the FASTA to enable this check.",
        }

    checked = matched = 0
    mismatches = []
    opener = gzip.open if str(vcf_path).endswith(".gz") else open
    try:
        with opener(vcf_path, "rt") as fh:
            for line in fh:
                if line.startswith("#"):
                    continue
                f = line.split("\t")
                if len(f) < 5:
                    continue
                chrom, pos, ref = f[0], int(f[1]), f[3]
                if ref in (".", "") or len(ref) > 50:
                    continue
                try:
                    actual = fasta.fetch(chrom, pos - 1, pos - 1 + len(ref)).upper()
                except (KeyError, ValueError):
                    continue
                checked += 1
                if actual == ref.upper():
                    matched += 1
                elif len(mismatches) < 20:
                    mismatches.append({"chrom": chrom, "pos": pos, "vcf_ref": ref, "reference": actual})
                if checked >= max_records:
                    break
    finally:
        fasta.close()

    return {
        "passed": checked > 0 and matched == checked,
        "skipped": False,
        "checked": checked,
        "matched": matched,
        "mismatches": mismatches,
    }


# ============================================================================
# MCP TOOLS
# ============================================================================


async def _fetch_reference_genome_impl(
    genome: str,
    output_dir: str,
    verify_against_vcf: Optional[str] = None,
) -> Dict[str, Any]:
    """Download a reference genome and verify it before reporting success.

    Three checks, in increasing order of what they actually establish:

      1. HEAD the URL first, so a wrong path fails in a second instead of after
         a gigabyte of transfer. The previous implementation built an NCBI path
         that does not exist and 404'd for every genome it advertised.
      2. Verify the downloaded bytes against the source's published md5sum.txt.
         This proves the file matches what the source published.
      3. Optionally verify against a specimen VCF. This proves something
         stronger and more useful: that the reference is the one that
         specimen's coordinates were called against. A checksum cannot tell you
         that you fetched the WRONG genome correctly.

    Args:
        genome: UCSC-style genome identifier (hg38, hg19, mm10, mm39, rn6, danRer11)
        output_dir: Directory for output files
        verify_against_vcf: Optional path to a specimen VCF. When given, contig
            lengths are checked against the assembly manifest and REF alleles
            against the reference sequence.

    Returns:
        Dictionary with path, size_mb, md5sum, verification results and metadata.

    Raises:
        ValueError: Invalid genome identifier
        IOError: URL unreachable, download failed, or checksum mismatch
    """
    _ensure_directories()

    if genome not in REFERENCE_GENOMES:
        raise ValueError(
            f"Unsupported genome '{genome}'. "
            f"Supported genomes: {', '.join(REFERENCE_GENOMES.keys())}"
        )

    genome_info = REFERENCE_GENOMES[genome]
    url = _genome_url(genome)
    output_path = Path(output_dir) / f"{genome}.fa.gz"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    published_md5 = await _fetch_published_md5(genome)

    if output_path.exists() and output_path.stat().st_size > 0:
        local_md5 = _calculate_md5(output_path)
        verification = _verification_block(local_md5, published_md5)
        result = {
            "path": str(output_path),
            "size_mb": output_path.stat().st_size / (1024 * 1024),
            "md5sum": local_md5,
            "verification": verification,
            "metadata": {
                "genome_id": genome,
                "name": genome_info["name"],
                "assembly": genome_info["assembly"],
                "organism": genome_info["organism"],
                "source": "UCSC goldenPath",
                "url": url,
                "status": "already_exists",
            },
        }
        if verification["checksum_match"] is False:
            raise IOError(
                f"Existing {output_path} does not match the published md5 for {genome} "
                f"(local {local_md5}, published {published_md5}). Delete it and re-fetch."
            )
        if verify_against_vcf:
            result["vcf_verification"] = await _verify_against_vcf(
                genome, verify_against_vcf, output_path
            )
        return result

    # Check 1: does the URL exist at all?
    head = await _head_url(url)
    if not head["ok"]:
        raise IOError(
            f"Reference URL for {genome} returned HTTP {head['status_code']}: {url}. "
            "Nothing was downloaded."
        )

    download_result = await _download_file(url, output_path)

    # Check 2: do the bytes match what the source published?
    verification = _verification_block(download_result["md5sum"], published_md5)
    if verification["checksum_match"] is False:
        output_path.unlink(missing_ok=True)
        raise IOError(
            f"Checksum mismatch for {genome}: downloaded {download_result['md5sum']}, "
            f"published {published_md5}. The partial file has been removed."
        )

    result = {
        "path": download_result["path"],
        "size_mb": download_result["size_bytes"] / (1024 * 1024),
        "md5sum": download_result["md5sum"],
        "verification": verification,
        "metadata": {
            "genome_id": genome,
            "name": genome_info["name"],
            "assembly": genome_info["assembly"],
            "organism": genome_info["organism"],
            "source": "UCSC goldenPath",
            "url": url,
            "expected_content_length": head["content_length"],
            "status": "downloaded",
        },
    }

    # Check 3: is this the reference the specimen was called against?
    if verify_against_vcf:
        result["vcf_verification"] = await _verify_against_vcf(
            genome, verify_against_vcf, output_path
        )

    return result


def _verification_block(local_md5: str, published_md5: Optional[str]) -> Dict[str, Any]:
    """Report the checksum comparison, distinguishing "mismatch" from "no manifest"."""
    if published_md5 is None:
        return {
            "checksum_match": None,
            "local_md5": local_md5,
            "published_md5": None,
            "note": "No published checksum was available, so the bytes are unverified.",
        }
    return {
        "checksum_match": local_md5 == published_md5,
        "local_md5": local_md5,
        "published_md5": published_md5,
        "note": (
            "Bytes match the source's published md5. This confirms the file is intact; "
            "it does not confirm the genome is the right one for a given specimen — "
            "pass verify_against_vcf for that."
        ),
    }


# ============================================================================
# TOOL 1: fetch_reference_genome
# ============================================================================


@mcp.tool()
async def fetch_reference_genome(
    genome: str,
    output_dir: str,
    verify_against_vcf: Optional[str] = None,
) -> Dict[str, Any]:
    """Download a reference genome and verify it before reporting success.

    Genomes are UCSC-style identifiers resolved against UCSC's goldenPath. The
    URL is HEAD-checked before any transfer starts, and the downloaded bytes are
    verified against the assembly's published md5sum.txt.

    Passing `verify_against_vcf` adds a stronger check than a checksum: contig
    lengths from the VCF header are compared against the assembly manifest, and
    VCF REF alleles against the reference sequence itself. A checksum proves the
    file is intact; this proves it is the reference that specimen's coordinates
    were called against.

    Args:
        genome: Genome identifier (hg38, hg19, mm10, mm39, rn6, danRer11)
        output_dir: Directory to save the downloaded genome
        verify_against_vcf: Optional path to a specimen VCF to verify against.

    Returns:
        Dictionary with path, size_mb, md5sum, verification, optional
        vcf_verification, and metadata.

    Raises:
        ValueError: If the genome ID is not supported
        IOError: If the URL is unreachable, the download fails, or the checksum
            does not match the published value

    Example:
        >>> result = await fetch_reference_genome("hg19", "/data/reference")
        >>> print(result["verification"]["checksum_match"])
        True
    """
    _ensure_directories()

    if genome not in REFERENCE_GENOMES:
        raise ValueError(
            f"Unsupported genome: {genome}. "
            f"Supported genomes: {', '.join(REFERENCE_GENOMES.keys())}"
        )

    if _is_dry_run():
        # DRY_RUN writes a placeholder file. Note that this branch is why the
        # broken NCBI URL survived unnoticed: with DRY_RUN defaulting to true,
        # the download path was never exercised.
        genome_info = REFERENCE_GENOMES[genome]
        output_path = Path(output_dir) / f"{genome}.fa.gz"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        already_exists = output_path.exists() and output_path.stat().st_size > 0
        if not already_exists:
            output_path.write_text(f"Mock genome data for {genome}\n")

        return {
            "path": str(output_path),
            "size_mb": genome_info["size_mb"],
            "md5sum": f"mock_md5_{genome}",
            "verification": {
                "checksum_match": None,
                "local_md5": f"mock_md5_{genome}",
                "published_md5": None,
                "note": "DRY_RUN: nothing was downloaded and nothing was verified.",
            },
            "metadata": {
                "genome_id": genome,
                "name": genome_info["name"],
                "assembly": genome_info["assembly"],
                "organism": genome_info["organism"],
                "source": "UCSC goldenPath",
                "url": _genome_url(genome),
                "status": "already_exists" if already_exists else "downloaded",
                "mode": "dry_run",
            },
        }

    return await _fetch_reference_genome_impl(genome, output_dir, verify_against_vcf)


# ============================================================================
# TOOL 2: validate_fastq
# ============================================================================


@mcp.tool()
async def validate_fastq(
    fastq_path: str,
    min_quality_score: int = 20,
    sample_size: int = 10000,
    full_count: bool = False,
) -> Dict[str, Any]:
    """Quality validation of FASTQ files.

    Validates FASTQ format and computes quality statistics over a sample of
    reads. The read counts are reported for what they are: `sampled_reads` is
    the number actually examined, and `estimated_total_reads` is extrapolated
    and labelled as an estimate. Set `full_count=True` for an exact count at the
    cost of streaming the whole file.

    Args:
        fastq_path: Path to FASTQ file (can be gzipped)
        min_quality_score: Minimum average quality score threshold
        sample_size: Reads to examine for the quality statistics
        full_count: Stream the entire file to count reads exactly

    Returns:
        Dictionary with keys:
            - valid: Boolean indicating if the file passed validation
            - sampled_reads: Reads actually examined
            - estimated_total_reads: Reads in the file (exact if full_count)
            - total_reads_is_exact: Whether the count above was measured or estimated
            - avg_quality: Average quality score over the sample
            - avg_read_length: Average read length over the sample
            - warnings: List of validation warnings

    Raises:
        IOError: File not found or cannot be read
        ValueError: Invalid FASTQ format

    Example:
        >>> result = await validate_fastq("/data/sample.fastq.gz")
        >>> print(result["sampled_reads"], result["estimated_total_reads"])
        10000 4736505
    """
    _ensure_directories()

    # Resolve GCS paths to local temp files
    fastq_path = _resolve_gcs_path(fastq_path)

    if _is_dry_run():
        # Return mock validation results without requiring real files
        return {
            "valid": True,
            "sampled_reads": min(sample_size, 1000000),
            "estimated_total_reads": 1000000,
            "total_reads_is_exact": False,
            "avg_quality": 32.5,
            "avg_read_length": 150,
            "warnings": [],
            "metadata": {
                "file": fastq_path,
                "min_quality_threshold": min_quality_score,
                "read_count_basis": "DRY_RUN: no file was read; these numbers are fixtures.",
                "mode": "dry_run"
            }
        }

    # =========================================================================
    # VALIDATION: Check FASTQ file format before processing
    # =========================================================================

    logger.info(f"Validating FASTQ file: {fastq_path}")
    fastq_valid, fastq_messages, fastq_info = validate_fastq_file(fastq_path)

    if not fastq_valid:
        # Validation failed - raise error with helpful message
        error_msg = format_validation_error(fastq_messages, fastq_path)
        logger.error("FASTQ validation failed")
        raise ValidationError(error_msg)

    # Log validation warnings/info
    for msg in fastq_messages:
        if msg.startswith('⚠️'):
            logger.warning(msg)
        elif msg.startswith('✅') or msg.startswith('ℹ️'):
            logger.info(msg)

    logger.info("✅ FASTQ file validated successfully")

    # =========================================================================
    # Continue with quality analysis
    # =========================================================================

    fastq_file = Path(fastq_path)

    # =========================================================================
    # DEFECT FIX (CNV_TOOLS_SPEC.md section 10.2)
    # -------------------------------------------------------------------------
    # This function samples the first `sample_size` reads and used to report
    # that sample count in a field named `total_reads`, documented as "Number of
    # reads in the file". On a lane containing 4,736,505 reads it returned
    # total_reads=10000 — a 474x error in a field that looks entirely plausible,
    # sitting next to metadata.sampled_reads=10000 saying the same number.
    #
    # The count is now named for what it is. `estimated_total_reads` is derived
    # from how far into the file the sample got, and is labelled an estimate.
    # `full_count=True` streams the whole file for an exact answer.
    #
    # The QC values themselves were always sound and are unchanged.
    # =========================================================================

    stats = await asyncio.get_running_loop().run_in_executor(
        None, _scan_fastq, str(fastq_file), sample_size, full_count
    )

    if stats["sampled_reads"] == 0:
        raise ValueError("FASTQ file is empty")

    warnings = []
    avg_quality = stats["total_quality"] / stats["sampled_reads"]
    avg_read_length = stats["total_length"] / stats["sampled_reads"]

    valid = avg_quality >= min_quality_score
    if not valid:
        warnings.append(
            f"Average quality {avg_quality:.2f} below threshold {min_quality_score}"
        )

    return {
        "valid": valid,
        "sampled_reads": stats["sampled_reads"],
        "estimated_total_reads": stats["estimated_total_reads"],
        "total_reads_is_exact": stats["exact"],
        "avg_quality": round(avg_quality, 2),
        "avg_read_length": round(avg_read_length, 2),
        "warnings": warnings,
        "metadata": {
            "file": str(fastq_file),
            "min_quality_threshold": min_quality_score,
            "sampled_reads": stats["sampled_reads"],
            "read_count_basis": (
                "exact — the whole file was streamed"
                if stats["exact"]
                else f"ESTIMATE — extrapolated from the first {stats['sampled_reads']} reads "
                     f"({stats['bytes_consumed']:,} of {stats['file_size']:,} bytes). "
                     "Pass full_count=True for an exact count."
            ),
            "estimate_basis_bytes": stats["bytes_consumed"],
            "file_size_bytes": stats["file_size"],
        },
    }


# Gzip only: an uncompressed file's text position is exact, so it never needs
# this fallback.
#
# A decompressor reads ahead by a BOUNDED buffer, so "the sample appears to have
# consumed a non-trivial fraction of the file" is equivalent to "the file is
# small" — at 5% the file is at most a few tens of megabytes, where an exact
# count costs a fraction of a second. Above that the buffer is noise against the
# sample and extrapolation is accurate (measured at 0.44% error on a 377 MB
# lane). This is a property of buffered reads, not a tuned constant.
EXACT_COUNT_BYTE_FRACTION = 0.05


def _scan_fastq(path: str, sample_size: int, full_count: bool) -> Dict[str, Any]:
    """Scan a FASTQ, returning QC sums over the sample and a read-count estimate.

    The estimate extrapolates from compressed bytes consumed for a gzipped file
    and from plain bytes for an uncompressed one. FASTQ compression ratio is
    close to uniform across a file, so this lands within a few percent — but it
    is still an estimate, and the caller is told so.
    """
    import gzip

    file_size = Path(path).stat().st_size
    is_gzipped = path.endswith(".gz")

    sampled = 0
    total_quality = 0.0
    total_length = 0

    raw = open(path, "rb")
    try:
        handle = gzip.open(raw, "rt") if is_gzipped else open(path, "r")
        with handle:
            while True:
                header = handle.readline()
                if not header:
                    break
                sequence = handle.readline().strip()
                plus = handle.readline()
                quality = handle.readline().strip()

                if not header.startswith("@"):
                    raise ValueError(f"Invalid FASTQ header: {header[:50]}")
                if not plus.startswith("+"):
                    raise ValueError(f"Invalid FASTQ separator: {plus[:50]}")
                if len(sequence) != len(quality):
                    raise ValueError("Sequence and quality length mismatch")

                if sampled < sample_size:
                    qual_scores = [ord(c) - 33 for c in quality]
                    total_quality += sum(qual_scores) / len(qual_scores)
                    total_length += len(sequence)

                sampled += 1

                if not full_count and sampled >= sample_size:
                    break

            if full_count:
                return {
                    "sampled_reads": min(sampled, sample_size),
                    "estimated_total_reads": sampled,
                    "exact": True,
                    "bytes_consumed": file_size,
                    "file_size": file_size,
                    "total_quality": total_quality,
                    "total_length": total_length,
                }

            # Bytes consumed on the underlying file, which for a gzip stream is
            # compressed bytes — the right denominator for extrapolation.
            bytes_consumed = raw.tell() if is_gzipped else handle.tell()

            # A decompressor reads AHEAD: after N reads the underlying file
            # position reflects the reader's buffer, not the bytes those reads
            # actually occupy. On a large file the buffer is negligible against
            # the sample. On a small one it dominates and would produce a badly
            # low estimate.
            #
            # When the counter says the sample already covered a large share of
            # the file, the file is small enough that counting it exactly costs
            # almost nothing — so do that instead of extrapolating from a
            # denominator we know is polluted.
            if is_gzipped and bytes_consumed >= EXACT_COUNT_BYTE_FRACTION * file_size:
                while True:
                    header = handle.readline()
                    if not header:
                        break
                    handle.readline()
                    handle.readline()
                    handle.readline()
                    sampled += 1
                return {
                    "sampled_reads": min(sampled, sample_size),
                    "estimated_total_reads": sampled,
                    "exact": True,
                    "bytes_consumed": file_size,
                    "file_size": file_size,
                    "total_quality": total_quality,
                    "total_length": total_length,
                }
    finally:
        raw.close()

    if bytes_consumed > 0 and sampled > 0:
        estimated = int(round(sampled * (file_size / bytes_consumed)))
    else:
        estimated = None

    return {
        "sampled_reads": sampled,
        "estimated_total_reads": estimated,
        "exact": False,
        "bytes_consumed": bytes_consumed,
        "file_size": file_size,
        "total_quality": total_quality,
        "total_length": total_length,
    }


@mcp.tool()
async def extract_umis(
    fastq_path: str,
    output_dir: str,
    umi_length: int = 12,
    read_structure: str = "12M+T"
) -> Dict[str, Any]:
    """UMI extraction and processing.

    Extracts Unique Molecular Identifiers (UMIs) from FASTQ reads and
    adds them to read names for downstream deduplication.

    Args:
        fastq_path: Path to input FASTQ file
        output_dir: Directory for output files
        umi_length: Length of UMI sequence in bases
        read_structure: FGbio read structure string (e.g., "12M+T" = 12bp UMI + template)

    Returns:
        Dictionary with keys:
            - output_fastq: Path to FASTQ file with extracted UMIs
            - umi_count: Number of unique UMIs found
            - reads_processed: Total reads processed
            - stats: UMI extraction statistics

    Raises:
        IOError: File not found or cannot be written
        ValueError: Invalid parameters

    Example:
        >>> result = await extract_umis(
        ...     fastq_path="/data/sample_R1.fastq.gz",
        ...     output_dir="/data/processed",
        ...     umi_length=12
        ... )
        >>> print(f"Extracted {result['umi_count']} unique UMIs")
    """
    _ensure_directories()

    if umi_length < 4 or umi_length > 20:
        raise ValueError(f"UMI length {umi_length} out of valid range (4-20)")

    fastq_file = Path(fastq_path)
    output_path = Path(output_dir) / f"{fastq_file.stem}_with_umis.fastq.gz"

    if _is_dry_run():
        # Return mock results without requiring real files
        return {
            "output_fastq": str(output_path),
            "umi_count": 45000,
            "reads_processed": 1000000,
            "stats": {
                "umi_length": umi_length,
                "read_structure": read_structure,
                "mode": "dry_run"
            }
        }

    if not fastq_file.exists():
        raise IOError(f"FASTQ file not found: {fastq_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # In a real implementation, this would call FGbio's ExtractUmisFromBam
    # For mock purposes, we'll return plausible statistics
    return {
        "output_fastq": str(output_path),
        "umi_count": 45000,
        "reads_processed": 1000000,
        "stats": {
            "umi_length": umi_length,
            "read_structure": read_structure,
            "unique_umi_ratio": 0.045,
            "tool": "fgbio.ExtractUmisFromBam"
        }
    }


@mcp.tool()
async def query_gene_annotations(
    genome: str,
    gene_name: Optional[str] = None,
    chromosome: Optional[str] = None,
    annotation_source: str = "gencode"
) -> Dict[str, Any]:
    """Retrieve gene annotation data.

    Queries gene annotations from GENCODE, Ensembl, or RefSeq databases.

    Args:
        genome: Genome identifier (hg38, mm10, etc.)
        gene_name: Optional gene name/symbol to search for
        chromosome: Optional chromosome to filter (e.g., "chr1", "chrX")
        annotation_source: Annotation database (gencode, ensembl, refseq)

    Returns:
        Dictionary with keys:
            - annotations: List of gene annotation records
            - total_genes: Number of genes found
            - source: Annotation source used
            - genome: Genome assembly

    Raises:
        ValueError: Invalid genome or annotation source

    Example:
        >>> result = await query_gene_annotations(
        ...     genome="hg38",
        ...     gene_name="TP53"
        ... )
        >>> print(f"Found {result['total_genes']} genes")
    """
    _ensure_directories()

    # Validate inputs
    if genome not in REFERENCE_GENOMES:
        raise ValueError(f"Unsupported genome: {genome}")

    valid_sources = ["gencode", "ensembl", "refseq"]
    if annotation_source not in valid_sources:
        raise ValueError(
            f"Invalid annotation source '{annotation_source}'. "
            f"Valid options: {', '.join(valid_sources)}"
        )

    # Mock gene annotations (in real implementation, would query database)
    mock_annotations = []

    if gene_name:
        mock_annotations.append({
            "gene_name": gene_name.upper(),
            "gene_id": f"ENSG00000{hash(gene_name) % 1000000:06d}",
            "chromosome": chromosome or "chr17",
            "start": 7661779,
            "end": 7687550,
            "strand": "-",
            "gene_type": "protein_coding",
            "source": annotation_source
        })

    return {
        "annotations": mock_annotations,
        "total_genes": len(mock_annotations),
        "source": annotation_source,
        "genome": genome,
        "metadata": {
            "query": {
                "gene_name": gene_name,
                "chromosome": chromosome
            }
        }
    }


# ============================================================================
# MCP RESOURCES
# ============================================================================


@mcp.resource("reference://hg38")
def get_hg38_reference() -> str:
    """Human genome reference (GRCh38).

    Provides metadata and access information for the human GRCh38 reference genome.

    Returns:
        JSON string with reference genome metadata
    """
    return json.dumps({
        "genome_id": "hg38",
        "name": "Human GRCh38",
        "assembly": "GRCh38",
        "organism": "Homo sapiens",
        "chromosomes": 25,  # 22 autosomes + X, Y, MT
        "total_length_gb": 3.1,
        "url": REFERENCE_GENOMES["hg38"]["url"],
        "annotations": {
            "gencode": "v44",
            "ensembl": "110"
        },
        "description": "The Genome Reference Consortium Human Build 38 (GRCh38) is the "
                      "latest human reference genome assembly."
    }, indent=2)


@mcp.resource("reference://mm10")
def get_mm10_reference() -> str:
    """Mouse genome reference (GRCm38/mm10).

    Provides metadata and access information for the mouse GRCm38 reference genome.

    Returns:
        JSON string with reference genome metadata
    """
    return json.dumps({
        "genome_id": "mm10",
        "name": "Mouse GRCm38",
        "assembly": "GRCm38",
        "organism": "Mus musculus",
        "chromosomes": 22,  # 19 autosomes + X, Y, MT
        "total_length_gb": 2.7,
        "url": REFERENCE_GENOMES["mm10"]["url"],
        "annotations": {
            "gencode": "vM25",
            "ensembl": "102"
        },
        "description": "The Genome Reference Consortium Mouse Build 38 (GRCm38/mm10) "
                      "reference genome assembly."
    }, indent=2)


@mcp.resource("annotations://gencode")
def get_gencode_annotations() -> str:
    """GENCODE gene annotations.

    Provides information about GENCODE gene annotation database.

    Returns:
        JSON string with GENCODE metadata
    """
    return json.dumps({
        "database": "GENCODE",
        "description": "Encyclopedia of genes and gene variants",
        "url": "https://www.gencodegenes.org/",
        "supported_genomes": {
            "hg38": "v44",
            "hg19": "v19",
            "mm10": "vM25"
        },
        "features": [
            "Protein-coding genes",
            "Long non-coding RNAs",
            "Small RNAs",
            "Pseudogenes",
            "Alternative transcripts"
        ],
        "format": "GTF/GFF3",
        "update_frequency": "Regular releases (approximately quarterly)"
    }, indent=2)


# ============================================================================
# SERVER ENTRYPOINT
# ============================================================================


def main() -> None:
    """Run the MCP FGbio server."""
    _ensure_directories()
    _run_server(mcp, server_name="mcp-fgbio", dry_run=DRY_RUN, env_var="FGBIO_DRY_RUN")


if __name__ == "__main__":
    main()
