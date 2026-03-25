"""MCP Spatial Tools server implementation.

This module provides an MCP server for spatial transcriptomics data processing,
including quality control, alignment, and spatial segmentation.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from fastmcp import FastMCP
from scipy.spatial.distance import cdist
from scipy.stats import norm, fisher_exact

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("spatialtools")

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
from common.transport import run_server as _run_server


def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="SPATIAL_DRY_RUN")


# Configuration
DATA_DIR = Path(os.getenv("SPATIAL_DATA_DIR", "/workspace/data"))
CACHE_DIR = Path(os.getenv("SPATIAL_CACHE_DIR", "/workspace/cache"))
_default_output = os.path.join(os.getenv("SPATIAL_DATA_DIR", "/workspace/data"), "output")
OUTPUT_DIR = Path(os.getenv("SPATIAL_OUTPUT_DIR", _default_output))
STAR_PATH = os.getenv("STAR_PATH", "STAR")
SAMTOOLS_PATH = os.getenv("SAMTOOLS_PATH", "samtools")
BEDTOOLS_PATH = os.getenv("BEDTOOLS_PATH", "bedtools")
THREADS = int(os.getenv("SPATIAL_THREADS", "8"))
DRY_RUN = os.getenv("SPATIAL_DRY_RUN", "false").lower() == "true"

# Quality control thresholds
MIN_READS_PER_BARCODE = int(os.getenv("MIN_READS_PER_BARCODE", "1000"))
MIN_GENES_PER_BARCODE = int(os.getenv("MIN_GENES_PER_BARCODE", "200"))
MAX_MT_PERCENT = float(os.getenv("MAX_MT_PERCENT", "20.0"))


def _ensure_directories() -> None:
    """Ensure required directories exist."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "raw").mkdir(exist_ok=True)
        (DATA_DIR / "filtered").mkdir(exist_ok=True)
        (DATA_DIR / "aligned").mkdir(exist_ok=True)
    except (OSError, PermissionError):
        # If DATA_DIR can't be created (e.g., using default /workspace path), skip
        pass

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError):
        # If CACHE_DIR can't be created (e.g., using default /workspace path), skip
        pass

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "visualizations").mkdir(exist_ok=True)
    except (OSError, PermissionError):
        # If OUTPUT_DIR can't be created (e.g., using default /workspace path), skip
        pass


# ============================================================================
# TOOL 1: filter_quality
# ============================================================================


@mcp.tool()
async def filter_quality(
    input_file: str,
    output_dir: str,
    min_reads: int = MIN_READS_PER_BARCODE,
    min_genes: int = MIN_GENES_PER_BARCODE,
    max_mt_percent: float = MAX_MT_PERCENT
) -> Dict[str, Any]:
    """QC filtering of spatial barcodes.

    Filters spatial transcriptomics data based on quality metrics including
    read count, gene count, and mitochondrial gene percentage.

    Args:
        input_file: Path to input spatial data file (CSV or H5)
        output_dir: Directory for filtered output files
        min_reads: Minimum reads per barcode (default: 1000)
        min_genes: Minimum genes detected per barcode (default: 200)
        max_mt_percent: Maximum mitochondrial gene percentage (default: 20.0)

    Returns:
        Dictionary with keys:
            - output_file: Path to filtered data
            - barcodes_before: Number of barcodes before filtering
            - barcodes_after: Number of barcodes after filtering
            - genes_detected: Number of genes detected
            - qc_metrics: Quality control statistics

    Raises:
        IOError: If input file not found
        ValueError: If invalid parameters

    Example:
        >>> result = await filter_quality(
        ...     input_file="/data/raw/spatial_data.csv",
        ...     output_dir="/data/filtered",
        ...     min_reads=1000
        ... )
        >>> print(f"Retained {result['barcodes_after']} of {result['barcodes_before']} barcodes")
    """
    _ensure_directories()

    # Check DRY_RUN mode first to avoid file checks
    if DRY_RUN:
        input_path = Path(input_file)
        output_path = Path(output_dir) / f"{input_path.stem}_filtered.csv"
        # Mock filtering results
        return {
            "output_file": str(output_path),
            "barcodes_before": 50000,
            "barcodes_after": 42500,
            "genes_detected": 15000,
            "qc_metrics": {
                "mean_reads_per_barcode": 2500,
                "median_genes_per_barcode": 850,
                "mean_mt_percent": 5.2,
                "filtering_rate": 0.85,
                "mode": "dry_run"
            }
        }

    # Real mode - validate inputs
    input_path = Path(input_file)
    if not input_path.exists():
        raise IOError(f"Input file not found: {input_file}")

    if min_reads < 0 or min_genes < 0 or max_mt_percent < 0 or max_mt_percent > 100:
        raise ValueError("Invalid QC parameters")

    output_path = Path(output_dir) / f"{input_path.stem}_filtered.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Real implementation would use scanpy or similar
    # For POC, simulate with pandas
    try:
        # Read spatial data - first column is barcode/spot ID
        if input_path.suffix == '.csv':
            data = pd.read_csv(input_path, index_col=0)
        else:
            raise ValueError(f"Unsupported file format: {input_path.suffix}")

        barcodes_before = len(data)

        # Real QC filtering logic
        data_filtered = data.copy()

        # Filter by minimum reads (if n_reads column exists)
        if 'n_reads' in data_filtered.columns:
            data_filtered = data_filtered[data_filtered['n_reads'] >= min_reads].copy()

        # Filter by minimum genes (if n_genes column exists or calculate from expression)
        if 'n_genes' in data_filtered.columns:
            data_filtered = data_filtered[data_filtered['n_genes'] >= min_genes].copy()
        else:
            # Calculate number of non-zero genes per spot
            # All columns should be numeric gene expression values now (barcode is index)
            gene_cols = [col for col in data_filtered.columns if col not in ['x', 'y', 'in_tissue', 'n_reads', 'n_genes', 'mt_percent']]
            if gene_cols:
                # For small gene panels (< min_genes total genes), adjust threshold intelligently
                total_genes = len(gene_cols)
                effective_min_genes = min(min_genes, max(1, total_genes // 4))  # Require at least 25% of genes

                # Convert to numeric, coerce errors to NaN
                numeric_data = data_filtered[gene_cols].apply(pd.to_numeric, errors='coerce')
                n_genes_per_spot = (numeric_data > 0).sum(axis=1)
                data_filtered = data_filtered[n_genes_per_spot >= effective_min_genes].copy()

        # Filter by mitochondrial percentage (if mt_percent column exists)
        if 'mt_percent' in data_filtered.columns:
            data_filtered = data_filtered[data_filtered['mt_percent'] <= max_mt_percent].copy()

        barcodes_after = len(data_filtered)

        # Save filtered data (preserve barcode index)
        data_filtered.to_csv(output_path, index=True)

        # Calculate QC metrics
        gene_cols = [col for col in data_filtered.columns if col not in ['x', 'y', 'in_tissue', 'n_reads', 'n_genes', 'mt_percent']]
        n_genes_detected = len(gene_cols) if gene_cols else 0

        return {
            "output_file": str(output_path),
            "barcodes_before": barcodes_before,
            "barcodes_after": barcodes_after,
            "genes_detected": n_genes_detected,
            "pass_rate": (barcodes_after / barcodes_before * 100) if barcodes_before > 0 else 0,
            "qc_metrics": {
                "mean_reads_per_barcode": float(data_filtered['n_reads'].mean()) if 'n_reads' in data_filtered.columns and len(data_filtered) > 0 else 0,
                "median_genes_per_barcode": float(data_filtered['n_genes'].median()) if 'n_genes' in data_filtered.columns and len(data_filtered) > 0 else 0,
                "mean_mt_percent": float(data_filtered['mt_percent'].mean()) if 'mt_percent' in data_filtered.columns and len(data_filtered) > 0 else 0,
                "filtering_rate": barcodes_after / barcodes_before if barcodes_before > 0 else 0,
            }
        }

    except Exception as e:
        raise IOError(f"Failed to filter quality: {e}") from e


# ============================================================================
# TOOL 2: split_by_region
# ============================================================================


@mcp.tool()
async def split_by_region(
    input_file: str,
    output_dir: str,
    regions: Optional[List[str]] = None,
    coordinate_file: Optional[str] = None
) -> Dict[str, Any]:
    """Segment data by spatial regions.

    Splits spatial transcriptomics data into regions based on spatial coordinates
    or predefined regions of interest (ROIs).

    Args:
        input_file: Path to input spatial data file
        output_dir: Directory for region-specific output files
        regions: Optional list of region names/IDs to extract
        coordinate_file: Optional path to file defining region coordinates

    Returns:
        Dictionary with keys:
            - regions: List of extracted regions with file paths
            - total_regions: Number of regions created
            - barcodes_per_region: Statistics on barcode distribution

    Raises:
        IOError: If input files not found
        ValueError: If invalid region specifications

    Example:
        >>> result = await split_by_region(
        ...     input_file="/data/filtered/spatial_data.csv",
        ...     output_dir="/data/regions",
        ...     regions=["tumor", "stroma", "immune"]
        ... )
        >>> print(f"Created {result['total_regions']} regions")
    """
    _ensure_directories()

    input_path = Path(input_file)
    if not input_path.exists():
        raise IOError(f"Input file not found: {input_file}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if DRY_RUN:
        # Mock region splitting
        mock_regions = regions or ["region_1", "region_2", "region_3"]
        return {
            "regions": [
                {
                    "name": region,
                    "file": str(output_path / f"{region}.csv"),
                    "barcode_count": np.random.randint(5000, 15000)
                }
                for region in mock_regions
            ],
            "total_regions": len(mock_regions),
            "barcodes_per_region": {
                "mean": 10000,
                "min": 5000,
                "max": 15000
            },
            "mode": "dry_run"
        }

    # Real implementation would use spatial coordinates
    try:
        # Read input data
        if input_path.suffix == '.csv':
            data = pd.read_csv(input_path)
        else:
            raise ValueError(f"Unsupported file format: {input_path.suffix}")

        # Mock region assignment (would use real spatial clustering)
        if 'region' not in data.columns:
            # Assign random regions for demonstration
            if regions:
                data['region'] = np.random.choice(regions, size=len(data))
            else:
                # Create spatial grid regions
                num_regions = 4
                data['region'] = pd.cut(
                    data.get('x_coord', np.random.rand(len(data))),
                    bins=num_regions,
                    labels=[f"region_{i}" for i in range(num_regions)]
                )

        # Split by region
        region_files = []
        region_stats = []

        for region_name in data['region'].unique():
            region_data = data[data['region'] == region_name]
            region_file = output_path / f"{region_name}.csv"
            region_data.to_csv(region_file, index=False)

            region_files.append({
                "name": str(region_name),
                "file": str(region_file),
                "barcode_count": len(region_data)
            })
            region_stats.append(len(region_data))

        return {
            "regions": region_files,
            "total_regions": len(region_files),
            "barcodes_per_region": {
                "mean": int(np.mean(region_stats)),
                "min": int(np.min(region_stats)),
                "max": int(np.max(region_stats))
            }
        }

    except Exception as e:
        raise IOError(f"Failed to split by region: {e}") from e


# ============================================================================
# TOOL 3: align_spatial_data
# ============================================================================


@mcp.tool()
async def align_spatial_data(
    fastq_r1: str,
    fastq_r2: str,
    reference_genome: str,
    output_dir: str,
    threads: int = THREADS
) -> Dict[str, Any]:
    """Align reads to reference genome using STAR aligner.

    Performs splice-aware alignment of spatial transcriptomics reads to a
    reference genome, producing BAM files with spatial barcode tags.

    Args:
        fastq_r1: Path to Read 1 FASTQ file (spatial barcodes)
        fastq_r2: Path to Read 2 FASTQ file (cDNA)
        reference_genome: Path to STAR genome index directory
        output_dir: Directory for alignment output files
        threads: Number of threads for alignment (default: 8)

    Returns:
        Dictionary with keys:
            - aligned_bam: Path to sorted BAM file
            - alignment_stats: Alignment statistics
            - log_file: Path to STAR log file

    Raises:
        IOError: If input files or genome index not found
        subprocess.CalledProcessError: If STAR fails

    Example:
        >>> result = await align_spatial_data(
        ...     fastq_r1="/data/sample_R1.fastq.gz",
        ...     fastq_r2="/data/sample_R2.fastq.gz",
        ...     reference_genome="/ref/hg38_star_index",
        ...     output_dir="/data/aligned"
        ... )
        >>> print(f"Alignment rate: {result['alignment_stats']['alignment_rate']:.2%}")
    """
    _ensure_directories()

    # Validate inputs
    r1_path = Path(fastq_r1)
    r2_path = Path(fastq_r2)
    genome_path = Path(reference_genome)
    output_path = Path(output_dir)

    if not r1_path.exists():
        raise IOError(f"FASTQ R1 not found: {fastq_r1}")
    if not r2_path.exists():
        raise IOError(f"FASTQ R2 not found: {fastq_r2}")

    if threads < 1 or threads > 64:
        raise ValueError(f"Invalid thread count: {threads}")

    output_path.mkdir(parents=True, exist_ok=True)

    if DRY_RUN:
        # Mock alignment results
        return {
            "aligned_bam": str(output_path / "Aligned.sortedByCoord.out.bam"),
            "alignment_stats": {
                "total_reads": 50000000,
                "uniquely_mapped": 42500000,
                "multi_mapped": 3750000,
                "unmapped": 3750000,
                "alignment_rate": 0.925,
                "unique_mapping_rate": 0.85
            },
            "log_file": str(output_path / "Log.final.out"),
            "mode": "dry_run"
        }

    # Real STAR alignment
    try:
        star_cmd = [
            STAR_PATH,
            "--runThreadN", str(threads),
            "--genomeDir", str(genome_path),
            "--readFilesIn", str(r2_path), str(r1_path),
            "--readFilesCommand", "zcat" if r1_path.suffix == ".gz" else "cat",
            "--outFileNamePrefix", str(output_path) + "/",
            "--outSAMtype", "BAM", "SortedByCoordinate",
            "--outSAMattributes", "NH", "HI", "AS", "nM", "NM", "MD",
            "--limitBAMsortRAM", "32000000000"
        ]

        # Execute STAR alignment
        result = subprocess.run(
            star_cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                star_cmd,
                result.stdout,
                result.stderr
            )

        # Parse STAR log file for alignment statistics
        log_file_path = output_path / "Log.final.out"
        alignment_stats = _parse_star_log(log_file_path)

        return {
            "aligned_bam": str(output_path / "Aligned.sortedByCoord.out.bam"),
            "alignment_stats": alignment_stats,
            "log_file": str(log_file_path)
        }

    except subprocess.TimeoutExpired as e:
        raise IOError(f"STAR alignment timeout: {e}") from e
    except Exception as e:
        raise IOError(f"STAR alignment failed: {e}") from e


def _parse_star_log(log_file_path: Path) -> Dict[str, Any]:
    """Parse STAR Log.final.out to extract alignment statistics.

    Args:
        log_file_path: Path to STAR Log.final.out file

    Returns:
        Dictionary with alignment statistics:
            - total_reads: Total number of input reads
            - uniquely_mapped: Number of uniquely mapped reads
            - multi_mapped: Number of multi-mapping reads
            - unmapped: Number of unmapped reads
            - alignment_rate: Fraction of reads aligned (unique + multi)
            - unique_mapping_rate: Fraction of reads uniquely mapped

    Raises:
        IOError: If log file not found or parsing fails

    Example STAR log format:
                              Number of input reads |       50000000
                   Uniquely mapped reads number |       42500000
       Number of reads mapped to multiple loci |       3750000
            Number of reads unmapped: too short |       3750000
    """
    if not log_file_path.exists():
        raise IOError(f"STAR log file not found: {log_file_path}")

    try:
        # Initialize counters
        total_reads = 0
        uniquely_mapped = 0
        multi_mapped = 0
        unmapped_mismatches = 0
        unmapped_short = 0
        unmapped_other = 0

        # Parse log file
        with open(log_file_path, 'r') as f:
            for line in f:
                line = line.strip()

                # Extract total input reads
                if "Number of input reads" in line:
                    total_reads = int(line.split('|')[1].strip())

                # Extract uniquely mapped reads
                elif "Uniquely mapped reads number" in line:
                    uniquely_mapped = int(line.split('|')[1].strip())

                # Extract multi-mapping reads
                elif "Number of reads mapped to multiple loci" in line:
                    multi_mapped = int(line.split('|')[1].strip())

                # Extract unmapped reads (3 categories)
                elif "Number of reads unmapped: too many mismatches" in line:
                    unmapped_mismatches = int(line.split('|')[1].strip())
                elif "Number of reads unmapped: too short" in line:
                    unmapped_short = int(line.split('|')[1].strip())
                elif "Number of reads unmapped: other" in line:
                    unmapped_other = int(line.split('|')[1].strip())

        # Calculate totals
        unmapped = unmapped_mismatches + unmapped_short + unmapped_other

        # Validate totals (should sum to total_reads)
        counted_total = uniquely_mapped + multi_mapped + unmapped
        if abs(counted_total - total_reads) > 100:  # Allow small rounding errors
            raise ValueError(
                f"STAR log parsing error: counted {counted_total} reads "
                f"but log reports {total_reads} total reads"
            )

        # Calculate rates
        if total_reads > 0:
            alignment_rate = (uniquely_mapped + multi_mapped) / total_reads
            unique_mapping_rate = uniquely_mapped / total_reads
        else:
            alignment_rate = 0.0
            unique_mapping_rate = 0.0

        return {
            "total_reads": total_reads,
            "uniquely_mapped": uniquely_mapped,
            "multi_mapped": multi_mapped,
            "unmapped": unmapped,
            "alignment_rate": alignment_rate,
            "unique_mapping_rate": unique_mapping_rate
        }

    except Exception as e:
        raise IOError(f"Failed to parse STAR log file {log_file_path}: {e}") from e


def _create_synthetic_fastq(
    output_r1: Path,
    output_r2: Path,
    num_reads: int = 1000,
    read_length: int = 100
) -> None:
    """Generate synthetic paired-end FASTQ files for testing.

    Creates minimal valid FASTQ files with random sequences and quality scores,
    suitable for testing alignment workflows without requiring large real datasets.

    Args:
        output_r1: Path for R1 FASTQ file (will be gzipped)
        output_r2: Path for R2 FASTQ file (will be gzipped)
        num_reads: Number of read pairs to generate (default: 1000)
        read_length: Length of each read in bp (default: 100)

    FASTQ format:
        @read_id
        SEQUENCE
        +
        QUALITY_SCORES

    Example:
        >>> _create_synthetic_fastq(
        ...     output_r1=Path("test_R1.fastq.gz"),
        ...     output_r2=Path("test_R2.fastq.gz"),
        ...     num_reads=1000
        ... )
    """
    import gzip
    import random

    # Nucleotides for random sequence generation
    nucleotides = ['A', 'C', 'G', 'T']

    # Phred+33 quality scores (ASCII 33-73 = Q0-Q40)
    # Using Q30 (ASCII 63 '?') for simplicity - high quality
    quality_char = '?' * read_length

    def generate_read(read_num: int, r_type: str) -> str:
        """Generate a single FASTQ read entry."""
        # Random sequence
        sequence = ''.join(random.choice(nucleotides) for _ in range(read_length))

        # FASTQ format (4 lines per read)
        return f"@read_{read_num}_{r_type}\n{sequence}\n+\n{quality_char}\n"

    # Generate R1 file
    with gzip.open(output_r1, 'wt') as f1:
        for i in range(num_reads):
            f1.write(generate_read(i, 'R1'))

    # Generate R2 file
    with gzip.open(output_r2, 'wt') as f2:
        for i in range(num_reads):
            f2.write(generate_read(i, 'R2'))

    logger.info(f"Created synthetic FASTQ files: {output_r1}, {output_r2}")
    logger.info(f"  Reads: {num_reads}, Length: {read_length}bp")
    logger.info(f"  R1 size: {output_r1.stat().st_size / 1024:.1f} KB")
    logger.info(f"  R2 size: {output_r2.stat().st_size / 1024:.1f} KB")


# ============================================================================
# TOOL 4: merge_tiles
# ============================================================================


@mcp.tool()
async def merge_tiles(
    tile_files: List[str],
    output_file: str,
    overlap_resolution: str = "average"
) -> Dict[str, Any]:
    """Combine multiple spatial tiles into a single dataset.

    Merges data from multiple spatial transcriptomics tiles, resolving
    overlapping regions and creating a unified expression matrix.

    Args:
        tile_files: List of paths to tile data files
        output_file: Path for merged output file
        overlap_resolution: Method for resolving overlaps - "average", "max", or "first"

    Returns:
        Dictionary with keys:
            - output_file: Path to merged data
            - tiles_merged: Number of tiles merged
            - total_barcodes: Total barcodes in merged data
            - overlap_regions: Statistics on overlapping regions

    Raises:
        IOError: If tile files not found
        ValueError: If invalid merge parameters

    Example:
        >>> result = await merge_tiles(
        ...     tile_files=["/data/tile_1.csv", "/data/tile_2.csv"],
        ...     output_file="/data/merged.csv",
        ...     overlap_resolution="average"
        ... )
        >>> print(f"Merged {result['tiles_merged']} tiles with {result['total_barcodes']} barcodes")
    """
    _ensure_directories()

    if not tile_files:
        raise ValueError("No tile files provided")

    if overlap_resolution not in ["average", "max", "first"]:
        raise ValueError(f"Invalid overlap resolution method: {overlap_resolution}")

    # Validate all tile files exist
    for tile_file in tile_files:
        if not Path(tile_file).exists():
            raise IOError(f"Tile file not found: {tile_file}")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if DRY_RUN:
        return {
            "output_file": str(output_path),
            "tiles_merged": len(tile_files),
            "total_barcodes": 85000,
            "overlap_regions": {
                "overlapping_barcodes": 5000,
                "overlap_percent": 5.9
            },
            "mode": "dry_run"
        }

    # Real implementation would merge tiles with spatial registration
    try:
        all_data = []

        for tile_file in tile_files:
            tile_path = Path(tile_file)
            if tile_path.suffix == '.csv':
                data = pd.read_csv(tile_path)
                all_data.append(data)

        # Concatenate all tiles
        merged_data = pd.concat(all_data, ignore_index=True)

        # Handle overlaps (simplified - real implementation would use spatial coords)
        if 'barcode' in merged_data.columns:
            # Remove duplicates based on overlap resolution strategy
            if overlap_resolution == "first":
                merged_data = merged_data.drop_duplicates(subset='barcode', keep='first')
            elif overlap_resolution == "average":
                # Would average expression values for overlapping barcodes
                merged_data = merged_data.groupby('barcode').mean().reset_index()
            elif overlap_resolution == "max":
                merged_data = merged_data.groupby('barcode').max().reset_index()

        # Save merged data
        merged_data.to_csv(output_path, index=False)

        return {
            "output_file": str(output_path),
            "tiles_merged": len(tile_files),
            "total_barcodes": len(merged_data),
            "overlap_regions": {
                "overlapping_barcodes": len(all_data[0]) + len(all_data[1]) - len(merged_data) if len(all_data) >= 2 else 0,
                "overlap_percent": ((len(all_data[0]) + len(all_data[1]) - len(merged_data)) / len(merged_data) * 100) if len(all_data) >= 2 and len(merged_data) > 0 else 0
            }
        }

    except Exception as e:
        raise IOError(f"Failed to merge tiles: {e}") from e


# ============================================================================
# TOOL 5: calculate_spatial_autocorrelation
# ============================================================================


def _calculate_morans_i(
    expression_values: np.ndarray,
    coordinates: np.ndarray,
    distance_threshold: float = 100.0
) -> tuple[float, float, float]:
    """Calculate Moran's I statistic for spatial autocorrelation.

    Args:
        expression_values: Gene expression values (1D array)
        coordinates: Spatial coordinates (Nx2 array)
        distance_threshold: Maximum distance for neighbors

    Returns:
        Tuple of (morans_i, z_score, p_value)
    """
    n = len(expression_values)

    if n == 0:
        return 0.0, 0.0, 1.0

    # Build spatial weights matrix (neighbors within threshold)
    distances = cdist(coordinates, coordinates)
    weights = (distances < distance_threshold).astype(float)
    np.fill_diagonal(weights, 0)  # No self-weighting

    # Normalize weights (row-standardization)
    row_sums = weights.sum(axis=1)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    weights = weights / row_sums[:, np.newaxis]

    # Calculate Moran's I
    mean_expr = expression_values.mean()
    deviations = expression_values - mean_expr

    numerator = np.sum(weights * np.outer(deviations, deviations))
    denominator = np.sum(deviations ** 2)

    if denominator == 0:
        return 0.0, 0.0, 1.0

    morans_i = (n / weights.sum()) * (numerator / denominator)

    # Calculate expected value and variance for z-score
    W = weights.sum()
    E_I = -1.0 / (n - 1)  # Expected value under null hypothesis

    # Simplified variance calculation
    S1 = 0.5 * np.sum((weights + weights.T) ** 2)
    S2 = np.sum((weights.sum(axis=1) + weights.sum(axis=0)) ** 2)

    var_I = ((n * S1 - S2 + 3 * W ** 2) / (W ** 2 * (n ** 2 - 1))) - E_I ** 2

    if var_I <= 0:
        return float(morans_i), 0.0, 1.0

    # Calculate z-score and p-value
    z_score = (morans_i - E_I) / np.sqrt(var_I)
    p_value = 2 * (1 - norm.cdf(abs(z_score)))  # Two-tailed test

    # Return Python native float types (not numpy types)
    return float(morans_i), float(z_score), float(p_value)


@mcp.tool()
async def calculate_spatial_autocorrelation(
    expression_file: str,
    genes: List[str],
    coordinates_file: Optional[str] = None,
    method: str = "morans_i",
    distance_threshold: float = 100.0
) -> Dict[str, Any]:
    """Calculate spatial autocorrelation statistics for gene expression.

    REAL IMPLEMENTATION: Uses scipy to compute Moran's I statistics.

    Computes Moran's I to detect spatial clustering patterns in gene expression.
    Moran's I ranges from -1 (dispersed) to +1 (clustered), with 0 indicating
    random spatial distribution.

    Args:
        expression_file: Path to spatial expression data (CSV with genes as columns)
        genes: List of genes to analyze
        coordinates_file: Path to spatial coordinates file (optional, can be embedded)
        method: Statistical method - "morans_i" (only Moran's I supported currently)
        distance_threshold: Maximum distance for defining neighbors (default: 100.0)

    Returns:
        Dictionary with autocorrelation statistics per gene:
        - morans_i: Moran's I statistic (-1 to +1)
        - z_score: Standardized test statistic
        - p_value: Statistical significance
        - interpretation: "clustered", "dispersed", or "random"

    Example:
        >>> result = await calculate_spatial_autocorrelation(
        ...     expression_file="/data/expression.csv",
        ...     coordinates_file="/data/coordinates.csv",
        ...     genes=["Ki67", "CD8A", "VIM"],
        ...     distance_threshold=150.0
        ... )
    """
    if DRY_RUN:
        # Return warning about dry run mode
        return add_dry_run_warning({
            "method": method,
            "genes_analyzed": 0,
            "results": [],
            "message": "DRY_RUN mode enabled. Set SPATIAL_DRY_RUN=false for real analysis."
        })

    try:
        # Load expression data
        expr_data = pd.read_csv(expression_file, index_col=0)

        # Load or extract coordinates
        if coordinates_file:
            coord_data = pd.read_csv(coordinates_file, index_col=0)
            # Detect coordinate columns (handle Visium and generic formats)
            col_lower = {c: c.lower() for c in coord_data.columns}
            # Priority 1: Visium pixel coordinates
            pxl_cols = [c for c, cl in col_lower.items() if 'pxl' in cl or 'pixel' in cl]
            # Priority 2: x/y named columns
            xy_cols = [c for c, cl in col_lower.items() if 'x' in cl or 'y' in cl]
            # Priority 3: array row/col
            array_cols = [c for c, cl in col_lower.items() if cl in ('array_row', 'array_col', 'row', 'col')]
            if len(pxl_cols) >= 2:
                coord_cols = pxl_cols[:2]
            elif len(xy_cols) >= 2:
                coord_cols = xy_cols[:2]
            elif len(array_cols) >= 2:
                coord_cols = array_cols[:2]
            else:
                # Last resort: first two numeric columns
                numeric_cols = [c for c in coord_data.columns if coord_data[c].dtype in ('int64', 'float64')]
                coord_cols = numeric_cols[:2] if len(numeric_cols) >= 2 else coord_data.columns[:2]
            coordinates = coord_data[coord_cols].values
            # Auto-adjust distance threshold if using pixel coordinates with large spacing
            coord_range = coordinates.max() - coordinates.min()
            if distance_threshold == 100.0 and coord_range.max() > 500:
                distance_threshold = coord_range.max() * 0.15
                logger.info(f"Auto-adjusted distance_threshold to {distance_threshold:.0f} for pixel coordinates")
        elif 'x_coord' in expr_data.columns and 'y_coord' in expr_data.columns:
            # Coordinates embedded in expression file
            coordinates = expr_data[['x_coord', 'y_coord']].values
            expr_data = expr_data.drop(['x_coord', 'y_coord'], axis=1)
        else:
            return {
                "status": "error",
                "error": "No spatial coordinates found",
                "message": "Provide coordinates_file or include x_coord/y_coord in expression file"
            }

        # Calculate autocorrelation for each gene
        autocorr_results = []

        for gene in genes:
            if gene not in expr_data.columns:
                autocorr_results.append({
                    "gene": gene,
                    "status": "not_found",
                    "message": f"Gene {gene} not found in expression data"
                })
                continue

            expression_values = expr_data[gene].values

            # Calculate Moran's I
            morans_i, z_score, p_value = _calculate_morans_i(
                expression_values,
                coordinates,
                distance_threshold
            )

            # Interpret result
            if p_value < 0.05:
                if morans_i > 0.3:
                    interpretation = "significantly clustered"
                elif morans_i < -0.3:
                    interpretation = "significantly dispersed"
                else:
                    interpretation = "weakly patterned"
            else:
                interpretation = "random (not significant)"

            # Explicitly convert to Python native types to avoid numpy serialization issues
            is_significant = float(p_value) < 0.05

            autocorr_results.append({
                "gene": str(gene),
                "morans_i": round(float(morans_i), 4),
                "z_score": round(float(z_score), 3),
                "p_value": round(float(p_value), 4),
                "significant": bool(is_significant),  # Convert to Python bool
                "interpretation": str(interpretation),
                "distance_threshold": float(distance_threshold)
            })

        # Summary statistics
        significant_clustered = sum(
            1 for r in autocorr_results
            if r.get("significant") and r.get("morans_i", 0) > 0.3
        )
        significant_dispersed = sum(
            1 for r in autocorr_results
            if r.get("significant") and r.get("morans_i", 0) < -0.3
        )

        return {
            "status": "success",
            "method": method,
            "genes_analyzed": int(len([r for r in autocorr_results if "morans_i" in r])),
            "genes_not_found": int(len([r for r in autocorr_results if r.get("status") == "not_found"])),
            "distance_threshold": float(distance_threshold),
            "num_spots": int(len(coordinates)),
            "results": autocorr_results,
            "summary": {
                "significantly_clustered": int(significant_clustered),
                "significantly_dispersed": int(significant_dispersed),
                "random_pattern": int(len(autocorr_results) - significant_clustered - significant_dispersed)
            }
        }

    except Exception as e:
        logger.error(f"Error calculating spatial autocorrelation: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to calculate spatial autocorrelation. Check file paths and format."
        }


# ============================================================================
# TOOL 6: perform_differential_expression
# ============================================================================


@mcp.tool()
async def perform_differential_expression(
    expression_file: str,
    group1_samples: List[str],
    group2_samples: List[str],
    test_method: str = "wilcoxon",
    min_log_fc: float = 0.5
) -> Dict[str, Any]:
    """Perform differential expression analysis between sample groups.

    REAL IMPLEMENTATION: Uses scipy for statistical testing and FDR correction.

    Args:
        expression_file: Path to expression matrix (CSV with spots as rows, genes as columns)
        group1_samples: Sample/spot IDs for group 1 (e.g., tumor core spots)
        group2_samples: Sample/spot IDs for group 2 (e.g., tumor margin spots)
        test_method: Statistical test - "wilcoxon" (Mann-Whitney U) or "t_test"
        min_log_fc: Minimum absolute log2 fold-change threshold for significance

    Returns:
        Dictionary with differential expression results including:
        - results: List of DEG results per gene
        - top_upregulated: Top genes upregulated in group1
        - top_downregulated: Top genes downregulated in group1
        - summary statistics

    Example:
        >>> result = await perform_differential_expression(
        ...     expression_file="/data/tumor_core.csv",
        ...     group1_samples=["SPOT_01_01", "SPOT_01_02"],
        ...     group2_samples=["SPOT_05_01", "SPOT_05_02"],
        ...     min_log_fc=0.5
        ... )
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "test_method": test_method,
            "results": [],
            "message": "DRY_RUN mode enabled. Set SPATIAL_DRY_RUN=false for real analysis."
        })

    try:
        from scipy.stats import mannwhitneyu, ttest_ind

        # Load expression data
        expr_data = pd.read_csv(expression_file, index_col=0)

        # Validate sample IDs
        available_samples = set(expr_data.index)
        group1_valid = [s for s in group1_samples if s in available_samples]
        group2_valid = [s for s in group2_samples if s in available_samples]

        if not group1_valid:
            return {
                "status": "error",
                "error": "No valid samples found in group1",
                "available_samples": list(available_samples)[:10]
            }

        if not group2_valid:
            return {
                "status": "error",
                "error": "No valid samples found in group2",
                "available_samples": list(available_samples)[:10]
            }

        # Perform differential expression for each gene
        deg_results = []

        # Get only numeric gene columns (exclude metadata columns)
        gene_cols = [col for col in expr_data.columns
                     if col not in ['x', 'y', 'in_tissue', 'region', 'n_reads', 'n_genes', 'mt_percent']]

        for gene in gene_cols:
            group1_expr = expr_data.loc[group1_valid, gene].values
            group2_expr = expr_data.loc[group2_valid, gene].values

            # Skip genes with no expression in either group
            if group1_expr.sum() == 0 and group2_expr.sum() == 0:
                continue

            # Calculate fold change
            pseudocount = 1e-10
            mean1 = float(group1_expr.mean() + pseudocount)
            mean2 = float(group2_expr.mean() + pseudocount)
            log2_fc = float(np.log2(mean1 / mean2))
            base_mean = float((mean1 + mean2) / 2)

            # Statistical test
            try:
                if test_method == "wilcoxon":
                    # Mann-Whitney U test (non-parametric)
                    stat, pval = mannwhitneyu(group1_expr, group2_expr, alternative='two-sided')
                else:  # t_test
                    # Independent t-test (parametric)
                    stat, pval = ttest_ind(group1_expr, group2_expr)

                pval = float(pval)
            except Exception as e:
                # If test fails (e.g., all identical values), set p=1
                pval = 1.0

            deg_results.append({
                'gene': gene,
                'log2_fold_change': log2_fc,
                'base_mean': base_mean,
                'mean_group1': mean1,
                'mean_group2': mean2,
                'pvalue': pval
            })

        # FDR correction using Benjamini-Hochberg
        if deg_results:
            pvalues = np.array([r['pvalue'] for r in deg_results])

            # Benjamini-Hochberg FDR correction
            n = len(pvalues)
            sorted_indices = np.argsort(pvalues)
            sorted_pvals = pvalues[sorted_indices]

            # Calculate q-values
            qvalues = np.zeros(n)
            for i in range(n):
                rank = i + 1
                qvalues[sorted_indices[i]] = min(sorted_pvals[i] * n / rank, 1.0)

            # Ensure monotonicity (q-values should not decrease)
            for i in range(n - 2, -1, -1):
                if qvalues[sorted_indices[i]] > qvalues[sorted_indices[i + 1]]:
                    qvalues[sorted_indices[i]] = qvalues[sorted_indices[i + 1]]

            # Add q-values and significance to results
            for i, result in enumerate(deg_results):
                result['qvalue'] = float(qvalues[i])
                result['significant'] = bool(
                    qvalues[i] < 0.05 and abs(result['log2_fold_change']) >= min_log_fc
                )

        # Sort by p-value
        deg_results_sorted = sorted(deg_results, key=lambda x: x['pvalue'])

        # Extract significant genes
        significant = [r for r in deg_results_sorted if r.get('significant', False)]
        upregulated = [r for r in significant if r['log2_fold_change'] > 0]
        downregulated = [r for r in significant if r['log2_fold_change'] < 0]

        # Round values for cleaner output
        for r in deg_results_sorted:
            r['log2_fold_change'] = round(r['log2_fold_change'], 4)
            r['base_mean'] = round(r['base_mean'], 2)
            r['mean_group1'] = round(r['mean_group1'], 2)
            r['mean_group2'] = round(r['mean_group2'], 2)
            r['pvalue'] = round(r['pvalue'], 6)
            r['qvalue'] = round(r['qvalue'], 6)

        return {
            "status": "success",
            "test_method": test_method,
            "group1_size": int(len(group1_valid)),
            "group2_size": int(len(group2_valid)),
            "total_genes_tested": int(len(deg_results)),
            "significant_genes": int(len(significant)),
            "upregulated_genes": int(len(upregulated)),
            "downregulated_genes": int(len(downregulated)),
            "results": deg_results_sorted,
            "top_upregulated": sorted(upregulated, key=lambda x: x['log2_fold_change'], reverse=True)[:10],
            "top_downregulated": sorted(downregulated, key=lambda x: x['log2_fold_change'])[:10],
            "significant_results": significant,
            "mode": "real_analysis"
        }

    except Exception as e:
        logger.error(f"Error performing differential expression: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to perform differential expression analysis"
        }


# ============================================================================
# TOOL 7: perform_batch_correction
# ============================================================================


def _calculate_batch_variance(data: np.ndarray, batch: np.ndarray) -> float:
    """Calculate variance explained by batch effects.

    Uses ANOVA-like approach to estimate what proportion of variance
    is explained by batch labels.

    Args:
        data: Sample × feature matrix
        batch: Batch labels for each sample

    Returns:
        Proportion of variance explained by batch (0-1)
    """
    # Overall mean
    grand_mean = np.mean(data, axis=0)

    # Total sum of squares
    ss_total = np.sum((data - grand_mean) ** 2)

    if ss_total == 0:
        return 0.0

    # Between-batch sum of squares
    ss_between = 0.0
    for b in np.unique(batch):
        batch_mask = (batch == b)
        batch_data = data[batch_mask]
        batch_mean = np.mean(batch_data, axis=0)
        n_batch = np.sum(batch_mask)
        ss_between += n_batch * np.sum((batch_mean - grand_mean) ** 2)

    # Variance explained by batch
    variance_explained = ss_between / ss_total

    return float(variance_explained)


def _combat_batch_correction(
    data: pd.DataFrame,
    batch: np.ndarray,
    parametric: bool = True
) -> pd.DataFrame:
    """Apply ComBat batch correction algorithm.

    ComBat uses empirical Bayes framework to adjust for batch effects.
    Based on Johnson et al. (2007) Biostatistics and the SVA R package.

    Args:
        data: Expression matrix (genes × samples)
        batch: Batch labels for each sample (1D array)
        parametric: Use parametric empirical Bayes (True) or non-parametric (False)

    Returns:
        Batch-corrected expression matrix
    """
    # Convert to numpy for computation
    dat = data.values
    n_genes, n_samples = dat.shape

    # Get unique batches
    batches = np.unique(batch)
    n_batch = len(batches)

    if n_batch == 1:
        logger.warning("Only one batch detected, returning original data")
        return data

    # Create batch design matrix
    batch_design = np.zeros((n_samples, n_batch))
    for i, b in enumerate(batches):
        batch_design[:, i] = (batch == b).astype(int)

    # Step 1: Standardize data across genes
    # Calculate gene-wise means and variances
    gene_mean = np.mean(dat, axis=1, keepdims=True)
    gene_var = np.var(dat, axis=1, keepdims=True)
    gene_var[gene_var == 0] = 1e-10  # Avoid division by zero

    # Standardize
    s_data = (dat - gene_mean) / np.sqrt(gene_var)

    # Step 2: Estimate batch effects (location and scale parameters)
    # For each batch, estimate gamma (location) and delta (scale)
    gamma_hat = np.zeros((n_genes, n_batch))
    delta_hat = np.zeros((n_genes, n_batch))

    for i, b in enumerate(batches):
        batch_samples = (batch == b)
        batch_data = s_data[:, batch_samples]

        # Location parameter (mean)
        gamma_hat[:, i] = np.mean(batch_data, axis=1)

        # Scale parameter (variance)
        delta_hat[:, i] = np.var(batch_data, axis=1)

    # Step 3: Empirical Bayes shrinkage
    if parametric:
        # Parametric prior: gamma ~ N(gamma_bar, tau^2)
        gamma_bar = np.mean(gamma_hat, axis=1, keepdims=True)
        tau_squared = np.var(gamma_hat, axis=1, keepdims=True)

        # Empirical Bayes adjustment for gamma
        # Shrink toward overall mean
        n_samples_per_batch = np.array([np.sum(batch == b) for b in batches])

        for i in range(n_batch):
            n_b = n_samples_per_batch[i]
            # Shrinkage factor
            shrink_factor = tau_squared[:, 0] / (tau_squared[:, 0] + gene_var[:, 0] / n_b)
            # Shrunk estimate
            gamma_star = shrink_factor * gamma_hat[:, i] + (1 - shrink_factor) * gamma_bar[:, 0]
            gamma_hat[:, i] = gamma_star

        # For delta (variance), use inverse gamma prior
        # Simpler approach: shrink toward pooled variance
        pooled_var = np.mean(delta_hat, axis=1, keepdims=True)
        for i in range(n_batch):
            n_b = n_samples_per_batch[i]
            # Simple shrinkage toward pooled variance
            weight = n_b / (n_b + 10)  # Regularization
            delta_star = weight * delta_hat[:, i] + (1 - weight) * pooled_var[:, 0]
            delta_hat[:, i] = delta_star

    # Step 4: Adjust the data
    corrected = s_data.copy()

    for i, b in enumerate(batches):
        batch_samples = (batch == b)

        # Subtract location effect
        corrected[:, batch_samples] -= gamma_hat[:, i:i+1]

        # Adjust for scale effect
        # scale = sqrt(delta)
        scale_ratio = np.sqrt(gene_var[:, 0] / (delta_hat[:, i] + 1e-10))
        corrected[:, batch_samples] *= scale_ratio[:, np.newaxis]

    # Step 5: Reverse standardization (back to original scale)
    corrected = corrected * np.sqrt(gene_var) + gene_mean

    # Return as DataFrame with original index/columns
    corrected_df = pd.DataFrame(
        corrected,
        index=data.index,
        columns=data.columns
    )

    return corrected_df


@mcp.tool()
async def perform_batch_correction(
    expression_files: List[str],
    batch_labels: List[str],
    output_file: str,
    method: str = "combat"
) -> Dict[str, Any]:
    """Perform batch correction across multiple samples.

    Args:
        expression_files: List of paths to expression matrices
        batch_labels: Batch identifier for each file
        output_file: Path for corrected expression matrix
        method: Batch correction method - "combat", "harmony", "scanorama"

    Returns:
        Dictionary with batch correction metrics

    Example:
        >>> result = await perform_batch_correction(
        ...     expression_files=["/data/batch1.csv", "/data/batch2.csv"],
        ...     batch_labels=["batch1", "batch2"],
        ...     output_file="/data/corrected.csv",
        ...     method="combat"
        ... )
    """
    if DRY_RUN:
        return {
            "method": method,
            "num_batches": len(set(batch_labels)),
            "num_samples": len(expression_files),
            "output_file": output_file,
            "batch_metrics": {
                "variance_before": 0.45,
                "variance_after": 0.12,
                "variance_reduction": 0.73,
                "kbet_score_before": 0.35,
                "kbet_score_after": 0.82
            },
            "genes_corrected": 15000,
            "mode": "dry_run"
        }

    # Real implementation: ComBat batch correction
    try:
        # Validate inputs
        if len(expression_files) != len(batch_labels):
            return {
                "status": "error",
                "error": "Number of expression files must match number of batch labels"
            }

        if method not in ["combat"]:
            return {
                "status": "error",
                "error": f"Method '{method}' not supported. Currently only 'combat' is implemented."
            }

        # Load and merge expression matrices
        expression_data = []
        sample_names = []

        for i, (file_path, batch_label) in enumerate(zip(expression_files, batch_labels)):
            try:
                # Load expression data
                expr_df = pd.read_csv(file_path, index_col=0)

                # Add batch suffix to column names to avoid conflicts
                expr_df.columns = [f"{col}_{batch_label}_{i}" for col in expr_df.columns]

                expression_data.append(expr_df)
                sample_names.extend(expr_df.columns.tolist())

            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Failed to load file {file_path}: {str(e)}"
                }

        # Merge all data (genes × samples)
        merged_data = pd.concat(expression_data, axis=1)

        # Ensure all genes are present across all batches
        # Fill missing values with 0
        merged_data = merged_data.fillna(0)

        logger.info(f"Merged data shape: {merged_data.shape} (genes × samples)")

        # Create batch array
        batch_array = []
        for i, (file_path, batch_label) in enumerate(zip(expression_files, batch_labels)):
            n_samples = expression_data[i].shape[1]
            batch_array.extend([batch_label] * n_samples)

        batch_array = np.array(batch_array)

        # Calculate batch effect metrics BEFORE correction
        # Calculate variance explained by batch
        variance_before = _calculate_batch_variance(merged_data.T.values, batch_array)

        # Apply ComBat batch correction
        logger.info(f"Applying ComBat batch correction with {len(set(batch_labels))} batches...")
        corrected_data = _combat_batch_correction(merged_data, batch_array, parametric=True)

        # Calculate batch effect metrics AFTER correction
        variance_after = _calculate_batch_variance(corrected_data.T.values, batch_array)

        # Calculate variance reduction
        variance_reduction = (variance_before - variance_after) / variance_before if variance_before > 0 else 0

        # Save corrected data
        corrected_data.to_csv(output_file)

        logger.info(f"Batch correction complete. Saved to: {output_file}")

        # Return metrics
        return {
            "status": "success",
            "method": method,
            "num_batches": len(set(batch_labels)),
            "num_samples": len(expression_files),
            "total_samples": len(sample_names),
            "genes_corrected": merged_data.shape[0],
            "output_file": output_file,
            "batch_metrics": {
                "variance_before": round(float(variance_before), 4),
                "variance_after": round(float(variance_after), 4),
                "variance_reduction": round(float(variance_reduction), 4)
            },
            "batches": {batch_label: batch_array.tolist().count(batch_label)
                       for batch_label in set(batch_labels)},
            "mode": "real_analysis"
        }

    except Exception as e:
        logger.error(f"Error performing batch correction: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to perform batch correction. Check file paths and formats."
        }


# ============================================================================
# TOOL 8: perform_pathway_enrichment
# ============================================================================

# Ovarian cancer-relevant pathway databases
# Based on KEGG, Hallmark (MSigDB), and GO Biological Process

OVARIAN_CANCER_PATHWAYS = {
    "KEGG": {
        "hsa05200": {
            "name": "Pathways in cancer",
            "genes": ["TP53", "PIK3CA", "PTEN", "AKT1", "AKT2", "MTOR", "KRAS", "NRAS",
                     "EGFR", "ERBB2", "MYC", "CCND1", "CCNE1", "CDK4", "CDK6", "RB1",
                     "BRCA1", "BRCA2", "VEGFA", "VEGFR2", "BCL2", "BCL2L1", "BAX"]
        },
        "hsa04151": {
            "name": "PI3K-Akt signaling pathway",
            "genes": ["PIK3CA", "PIK3CB", "PIK3R1", "AKT1", "AKT2", "AKT3", "MTOR",
                     "RPS6KB1", "PTEN", "PDK1", "TSC1", "TSC2", "FOXO3", "BCL2L1",
                     "BAD", "GSK3B", "CCND1", "MYC"]
        },
        "hsa04110": {
            "name": "Cell cycle",
            "genes": ["CCND1", "CCNE1", "CCNA2", "CCNB1", "CDK1", "CDK2", "CDK4", "CDK6",
                     "TP53", "RB1", "E2F1", "E2F3", "MYC", "PCNA", "MCM2", "MCM5", "CDKN1A", "CDKN2A"]
        },
        "hsa03030": {
            "name": "DNA replication",
            "genes": ["PCNA", "MCM2", "MCM3", "MCM4", "MCM5", "MCM6", "MCM7", "RFC1",
                     "POLD1", "POLE", "DNA2", "FEN1", "LIG1"]
        },
        "hsa03430": {
            "name": "Mismatch repair",
            "genes": ["MSH2", "MSH6", "MLH1", "PMS2", "PCNA", "RFC1", "EXO1", "POLD1", "LIG1"]
        },
        "hsa03420": {
            "name": "Nucleotide excision repair",
            "genes": ["XPA", "XPC", "ERCC1", "ERCC2", "ERCC3", "ERCC4", "ERCC5", "DDB1",
                     "DDB2", "PCNA", "RFC1", "POLD1", "LIG1"]
        },
        "hsa03440": {
            "name": "Homologous recombination",
            "genes": ["BRCA1", "BRCA2", "RAD51", "RAD52", "RAD54L", "XRCC2", "XRCC3",
                     "MRE11A", "RAD50", "NBN", "ATM", "POLD1"]
        },
        "hsa04210": {
            "name": "Apoptosis",
            "genes": ["TP53", "BAX", "BCL2", "BCL2L1", "BID", "CASP3", "CASP8", "CASP9",
                     "FADD", "FAS", "APAF1", "CYCS", "PARP1", "BAD"]
        },
        "hsa04066": {
            "name": "HIF-1 signaling pathway",
            "genes": ["HIF1A", "VEGFA", "EGLN1", "EGLN3", "VHL", "LDHA", "PFKL", "ENO1",
                     "PDK1", "EPO", "HMOX1", "NOS2", "REDD1"]
        },
        "hsa04010": {
            "name": "MAPK signaling pathway",
            "genes": ["KRAS", "NRAS", "BRAF", "RAF1", "MAP2K1", "MAP2K2", "MAPK1", "MAPK3",
                     "JUN", "FOS", "MYC", "ELK1", "TP53"]
        },
        "hsa04370": {
            "name": "VEGF signaling pathway",
            "genes": ["VEGFA", "VEGFB", "VEGFC", "KDR", "FLT1", "PIK3CA", "AKT1", "MAPK1",
                     "MAPK3", "PLA2G4A", "PTGS2", "NOS3"]
        }
    },
    "Hallmark": {
        "HALLMARK_PI3K_AKT_MTOR_SIGNALING": {
            "name": "PI3K/AKT/mTOR signaling",
            "genes": ["PIK3CA", "PIK3CB", "PIK3R1", "AKT1", "AKT2", "AKT3", "MTOR", "RPS6KB1",
                     "RPS6", "EIF4EBP1", "PTEN", "TSC1", "TSC2", "RHEB", "RPTOR", "RICTOR"]
        },
        "HALLMARK_MYC_TARGETS_V1": {
            "name": "MYC targets",
            "genes": ["MYC", "MYCN", "MAX", "E2F1", "E2F3", "CDK4", "CCND1", "CCNE1",
                     "PCNA", "MCM2", "MCM5", "MCM7", "LDHA", "PKM"]
        },
        "HALLMARK_E2F_TARGETS": {
            "name": "E2F targets (cell cycle)",
            "genes": ["E2F1", "E2F2", "E2F3", "CCNE1", "CCNE2", "CDK1", "CDK2", "PCNA",
                     "MCM2", "MCM3", "MCM4", "MCM5", "MCM6", "MCM7", "RRM2"]
        },
        "HALLMARK_G2M_CHECKPOINT": {
            "name": "G2/M checkpoint",
            "genes": ["CDK1", "CCNB1", "CCNB2", "CCNA2", "PLK1", "AURKA", "AURKB", "BUB1",
                     "BUB1B", "MAD2L1", "CDC20", "PTTG1", "TOP2A"]
        },
        "HALLMARK_APOPTOSIS": {
            "name": "Apoptosis",
            "genes": ["TP53", "BAX", "BCL2", "BCL2L1", "BID", "BIK", "CASP3", "CASP7",
                     "CASP8", "CASP9", "FAS", "FADD", "APAF1", "CYCS"]
        },
        "HALLMARK_P53_PATHWAY": {
            "name": "p53 pathway",
            "genes": ["TP53", "MDM2", "CDKN1A", "CDKN2A", "BAX", "PUMA", "NOXA", "GADD45A",
                     "BTG2", "ZMAT3", "RRM2B", "TIGAR"]
        },
        "HALLMARK_DNA_REPAIR": {
            "name": "DNA repair",
            "genes": ["BRCA1", "BRCA2", "RAD51", "XRCC1", "XRCC2", "XRCC3", "PARP1", "PARP2",
                     "ERCC1", "ERCC2", "XPA", "MSH2", "MLH1", "ATM", "ATR"]
        },
        "HALLMARK_HYPOXIA": {
            "name": "Hypoxia",
            "genes": ["HIF1A", "VEGFA", "LDHA", "PDK1", "BNIP3", "BNIP3L", "SLC2A1", "ENO1",
                     "PFKL", "ALDOA", "PGK1", "EGLN1", "EGLN3", "VHL"]
        },
        "HALLMARK_ANGIOGENESIS": {
            "name": "Angiogenesis",
            "genes": ["VEGFA", "VEGFB", "VEGFC", "KDR", "FLT1", "ANGPT1", "ANGPT2", "TEK",
                     "PDGFA", "PDGFB", "FGF2", "HIF1A", "NRP1"]
        },
        "HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION": {
            "name": "Epithelial-mesenchymal transition (EMT)",
            "genes": ["VIM", "SNAI1", "SNAI2", "TWIST1", "TWIST2", "ZEB1", "ZEB2", "CDH1",
                     "CDH2", "FN1", "MMP2", "MMP9", "TGFB1"]
        },
        "HALLMARK_INFLAMMATORY_RESPONSE": {
            "name": "Inflammatory response",
            "genes": ["IL6", "IL1B", "TNF", "NFKB1", "RELA", "CXCL8", "CCL2", "PTGS2",
                     "ICAM1", "VCAM1", "SELE", "IRF1"]
        },
        "HALLMARK_INTERFERON_GAMMA_RESPONSE": {
            "name": "Interferon gamma response",
            "genes": ["IFNG", "STAT1", "IRF1", "TAP1", "TAP2", "HLA-A", "HLA-B", "HLA-C",
                     "B2M", "CXCL9", "CXCL10", "CXCL11", "IDO1"]
        }
    },
    "GO_BP": {
        "GO:0006281": {
            "name": "DNA repair",
            "genes": ["BRCA1", "BRCA2", "RAD51", "XRCC1", "XRCC2", "PARP1", "ERCC1", "XPA",
                     "MSH2", "MLH1", "ATM", "ATR", "CHEK1", "CHEK2", "TP53BP1"]
        },
        "GO:0008283": {
            "name": "Cell proliferation",
            "genes": ["TP53", "MYC", "CCND1", "CCNE1", "CDK4", "CDK6", "RB1", "E2F1",
                     "PCNA", "Ki67", "MKI67", "TOP2A", "AURKA"]
        },
        "GO:0006974": {
            "name": "Cellular response to DNA damage stimulus",
            "genes": ["TP53", "ATM", "ATR", "BRCA1", "BRCA2", "CHEK1", "CHEK2", "RAD51",
                     "H2AFX", "TP53BP1", "MDC1", "NBN", "MRE11A", "RAD50"]
        },
        "GO:0045787": {
            "name": "Positive regulation of cell cycle",
            "genes": ["CCND1", "CCNE1", "CDK4", "CDK6", "MYC", "E2F1", "SKP2", "CDC25A",
                     "WEE1", "PLK1", "AURKA"]
        },
        "GO:0042981": {
            "name": "Regulation of apoptosis",
            "genes": ["TP53", "BCL2", "BCL2L1", "BAX", "BID", "CASP3", "CASP8", "CASP9",
                     "APAF1", "FAS", "TNFRSF10A", "TNFRSF10B", "MCL1"]
        },
        "GO:0001525": {
            "name": "Angiogenesis",
            "genes": ["VEGFA", "VEGFB", "VEGFC", "KDR", "FLT1", "ANGPT1", "ANGPT2", "TEK",
                     "FGF2", "HIF1A", "NRP1", "PDGFB", "SPHK1"]
        },
        "GO:0006954": {
            "name": "Inflammatory response",
            "genes": ["IL6", "IL1B", "TNF", "NFKB1", "RELA", "PTGS2", "CCL2", "CXCL8",
                     "ICAM1", "VCAM1", "TLR4", "MYD88"]
        },
        "GO:0030198": {
            "name": "Extracellular matrix organization",
            "genes": ["COL1A1", "COL3A1", "COL4A1", "FN1", "LAMA5", "MMP2", "MMP9", "MMP14",
                     "TIMP1", "TIMP2", "SPARC", "TNC"]
        },
        "GO:0001837": {
            "name": "Epithelial to mesenchymal transition",
            "genes": ["VIM", "SNAI1", "SNAI2", "TWIST1", "ZEB1", "ZEB2", "CDH1", "CDH2",
                     "FN1", "TGFB1", "TGFBR1", "SMAD2", "SMAD3"]
        },
        "GO:0006096": {
            "name": "Glycolysis",
            "genes": ["HK1", "HK2", "GPI", "PFKL", "PFKM", "ALDOA", "GAPDH", "PGK1", "ENO1",
                     "PKM", "LDHA", "LDHB"]
        }
    },
    "Drug_Resistance": {
        "PLATINUM_RESISTANCE": {
            "name": "Platinum resistance mechanisms",
            "genes": ["ERCC1", "XPA", "XPD", "GSTP1", "ABCB1", "ABCC1", "ABCC2", "ABCG2",
                     "BCL2L1", "BCL2", "XIAP", "SURVIVIN", "PTEN", "PIK3CA", "AKT1"]
        },
        "ABC_TRANSPORTERS": {
            "name": "ABC transporter drug efflux",
            "genes": ["ABCB1", "ABCC1", "ABCC2", "ABCC3", "ABCC4", "ABCC5", "ABCG2"]
        },
        "ANTI_APOPTOTIC": {
            "name": "Anti-apoptotic signaling",
            "genes": ["BCL2", "BCL2L1", "BCLW", "MCL1", "XIAP", "BIRC2", "BIRC3", "SURVIVIN"]
        },
        "PARP_RESISTANCE": {
            "name": "PARP inhibitor resistance",
            "genes": ["BRCA1", "BRCA2", "RAD51", "XRCC1", "PARP1", "TP53BP1", "RIF1",
                     "REV7", "SHLD1", "SHLD2", "SHLD3", "PIK3CA", "AKT1"]
        }
    }
}


@mcp.tool()
async def perform_pathway_enrichment(
    gene_list: List[str],
    background_genes: Optional[List[str]] = None,
    database: str = "GO_BP",
    p_value_cutoff: float = 0.05
) -> Dict[str, Any]:
    """Perform pathway enrichment analysis on gene lists.

    Args:
        gene_list: List of genes to analyze
        background_genes: Optional background gene set
        database: Pathway database - "GO_BP", "KEGG", "Reactome", "Hallmark"
        p_value_cutoff: P-value threshold for significance

    Returns:
        Dictionary with enriched pathways and statistics

    Example:
        >>> result = await perform_pathway_enrichment(
        ...     gene_list=["TP53", "BRCA1", "BRCA2"],
        ...     database="KEGG",
        ...     p_value_cutoff=0.05
        ... )
    """
    if DRY_RUN:
        # Mock pathway enrichment results
        pathways = [
            {
                "pathway_id": "GO:0008283",
                "pathway_name": "Cell proliferation",
                "genes_in_pathway": 450,
                "genes_overlapping": 12,
                "p_value": 0.00023,
                "p_adj": 0.0145,
                "fold_enrichment": 3.8,
                "genes": ["TP53", "BRCA1", "MYC", "CCND1"]
            },
            {
                "pathway_id": "GO:0006281",
                "pathway_name": "DNA repair",
                "genes_in_pathway": 280,
                "genes_overlapping": 8,
                "p_value": 0.00156,
                "p_adj": 0.0312,
                "fold_enrichment": 3.2,
                "genes": ["BRCA1", "BRCA2", "TP53", "ATM"]
            },
            {
                "pathway_id": "GO:0045787",
                "pathway_name": "Positive regulation of cell cycle",
                "genes_in_pathway": 195,
                "genes_overlapping": 6,
                "p_value": 0.0234,
                "p_adj": 0.0468,
                "fold_enrichment": 2.4,
                "genes": ["CCND1", "CDK4", "MYC"]
            }
        ]

        significant = [p for p in pathways if p["p_adj"] < p_value_cutoff]

        return {
            "database": database,
            "genes_analyzed": len(gene_list),
            "background_size": len(background_genes) if background_genes else 20000,
            "pathways_tested": 500,
            "pathways_enriched": len(significant),
            "p_value_cutoff": p_value_cutoff,
            "pathways": pathways,
            "top_pathway": pathways[0]["pathway_name"] if pathways else None,
            "mode": "dry_run"
        }

    # Real implementation: Fisher's exact test for pathway enrichment

    # Normalize gene lists (case-insensitive)
    gene_list_upper = [gene.upper() for gene in gene_list]

    # Default background: all genes in the pathway database
    if background_genes is None:
        all_pathway_genes = set()
        if database in OVARIAN_CANCER_PATHWAYS:
            for pathway_info in OVARIAN_CANCER_PATHWAYS[database].values():
                all_pathway_genes.update([g.upper() for g in pathway_info["genes"]])
        background_genes_upper = list(all_pathway_genes)
    else:
        background_genes_upper = [gene.upper() for gene in background_genes]

    # Get pathways for selected database
    if database not in OVARIAN_CANCER_PATHWAYS:
        return {
            "status": "error",
            "error": f"Unknown database: {database}",
            "available_databases": list(OVARIAN_CANCER_PATHWAYS.keys())
        }

    pathways_db = OVARIAN_CANCER_PATHWAYS[database]

    # Perform enrichment for each pathway
    enrichment_results = []

    for pathway_id, pathway_info in pathways_db.items():
        pathway_genes_upper = [g.upper() for g in pathway_info["genes"]]

        # 2x2 contingency table for Fisher's exact test:
        # | In gene list | Not in gene list |
        # |--------------|------------------|
        # | In pathway   | a                | b                |
        # | Not pathway  | c                | d                |

        genes_in_list_and_pathway = set(gene_list_upper) & set(pathway_genes_upper)
        genes_in_list_not_pathway = set(gene_list_upper) - set(pathway_genes_upper)
        genes_in_pathway_not_list = set(pathway_genes_upper) - set(gene_list_upper)
        genes_not_in_either = set(background_genes_upper) - set(gene_list_upper) - set(pathway_genes_upper)

        a = len(genes_in_list_and_pathway)
        b = len(genes_in_pathway_not_list)
        c = len(genes_in_list_not_pathway)
        d = len(genes_not_in_either)

        # Skip if no overlap
        if a == 0:
            continue

        # Fisher's exact test (one-sided for enrichment)
        contingency_table = [[a, b], [c, d]]
        try:
            _, p_value = fisher_exact(contingency_table, alternative='greater')
        except Exception as e:
            logger.warning(f"Fisher's exact test failed for {pathway_id}: {e}")
            continue

        # Calculate fold enrichment
        # (a / (a+c)) / (b / (b+d))
        # = proportion in gene list / proportion in background
        if a + c > 0 and b + d > 0:
            fold_enrichment = (a / (a + c)) / ((a + b) / (a + b + c + d))
        else:
            fold_enrichment = 0.0

        # Store result
        enrichment_results.append({
            "pathway_id": pathway_id,
            "pathway_name": pathway_info["name"],
            "genes_in_pathway": len(pathway_genes_upper),
            "genes_overlapping": a,
            "overlapping_genes": sorted(list(genes_in_list_and_pathway)),
            "p_value": float(p_value),
            "fold_enrichment": round(float(fold_enrichment), 2)
        })

    # Sort by p-value
    enrichment_results.sort(key=lambda x: x["p_value"])

    # Apply Benjamini-Hochberg FDR correction
    num_tests = len(enrichment_results)
    for i, result in enumerate(enrichment_results):
        rank = i + 1
        # BH correction: p_adj = p_value * num_tests / rank
        p_adj = min(1.0, result["p_value"] * num_tests / rank)
        result["p_adj"] = round(float(p_adj), 6)

    # Filter by significance
    significant_pathways = [p for p in enrichment_results if p["p_adj"] < p_value_cutoff]

    # Return results
    return {
        "database": database,
        "genes_analyzed": len(gene_list_upper),
        "background_size": len(background_genes_upper),
        "pathways_tested": len(pathways_db),
        "pathways_enriched": len(significant_pathways),
        "p_value_cutoff": p_value_cutoff,
        "pathways": significant_pathways[:20],  # Top 20 to avoid token bloat
        "top_pathway": significant_pathways[0]["pathway_name"] if significant_pathways else None,
        "mode": "real_analysis"
    }


# ============================================================================
# TOOL 9: deconvolve_cell_types (Cell Type Deconvolution)
# ============================================================================

# Ovarian cancer-specific cell type gene signatures
OVARIAN_CANCER_CELL_SIGNATURES = {
    "tumor_cells": {
        "markers": ["EPCAM", "KRT8", "KRT18", "PAX8", "TP53"],
        "description": "Epithelial tumor cells"
    },
    "cd8_tcells": {
        "markers": ["CD8A", "CD3D", "CD3E"],
        "description": "CD8+ cytotoxic T lymphocytes"
    },
    "cd4_tcells": {
        "markers": ["CD4", "CD3D", "CD3E"],
        "description": "CD4+ helper T lymphocytes"
    },
    "regulatory_tcells": {
        "markers": ["FOXP3", "CD4", "CD3D"],
        "description": "Regulatory T cells (Tregs)"
    },
    "macrophages": {
        "markers": ["CD68", "CD163"],
        "description": "Tumor-associated macrophages (TAMs)"
    },
    "endothelial_cells": {
        "markers": ["CD31", "VWF", "VEGFA", "KDR"],
        "description": "Endothelial cells (vasculature)"
    },
    "fibroblasts": {
        "markers": ["FAP", "COL1A1", "COL3A1", "ACTA2"],
        "description": "Cancer-associated fibroblasts (CAFs)"
    },
    "mesenchymal_cells": {
        "markers": ["VIM", "SNAI1", "TWIST1", "CDH2"],
        "description": "Mesenchymal/EMT cells"
    }
}


@mcp.tool()
async def deconvolve_cell_types(
    expression_file: str,
    signatures: Optional[Dict[str, List[str]]] = None,
    normalize: bool = True,
    include_spot_scores: bool = False
) -> Dict[str, Any]:
    """Estimate cell type proportions from bulk spatial transcriptomics data.

    REAL IMPLEMENTATION: Signature-based deconvolution using marker gene expression.

    Uses predefined gene signatures to estimate relative abundance of different
    cell types in each spatial spot. Particularly useful for ovarian cancer samples
    to quantify immune infiltration, tumor purity, and stromal components.

    Args:
        expression_file: Path to spatial expression matrix (CSV with spots × genes)
        signatures: Optional custom cell type signatures dict {cell_type: [genes]}
                   If None, uses ovarian cancer-specific signatures
        normalize: Whether to z-score normalize signature scores (default: True)
        include_spot_scores: Include per-spot scores in response (default: False)
                           WARNING: For large datasets (>100 spots), this creates
                           very large responses. Use False for token efficiency.

    Returns:
        Dictionary with cell type analysis:
        - spots_analyzed: Number of spots
        - cell_types: List of cell types analyzed
        - summary_statistics: Mean/median/std scores per cell type
        - dominant_cell_type_distribution: Count of spots per dominant cell type
        - spot_scores: Per-spot scores (only if include_spot_scores=True)

    Example:
        >>> result = await deconvolve_cell_types(
        ...     expression_file="/data/tumor_region.csv"
        ... )
        >>> print(result['summary_statistics']['cd8_tcells']['mean'])
        0.52  # High CD8+ T-cell infiltration
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "cell_types": [],
            "message": "DRY_RUN mode enabled. Set SPATIAL_DRY_RUN=false for real analysis."
        })

    try:
        # Load expression data
        expr_data = pd.read_csv(expression_file, index_col=0)

        # Use default ovarian cancer signatures if none provided
        if signatures is None:
            signatures = {
                cell_type: sig_info["markers"]
                for cell_type, sig_info in OVARIAN_CANCER_CELL_SIGNATURES.items()
            }

        # Filter out metadata columns
        gene_cols = [col for col in expr_data.columns
                     if col not in ['x', 'y', 'in_tissue', 'region', 'n_reads', 'n_genes', 'mt_percent']]
        expr_data_genes = expr_data[gene_cols]

        # Calculate signature scores for each cell type
        cell_type_scores = {}
        signatures_used = {}

        for cell_type, marker_genes in signatures.items():
            # Get genes that exist in data
            available_genes = [g for g in marker_genes if g in expr_data_genes.columns]

            if not available_genes:
                # No markers available for this cell type
                cell_type_scores[cell_type] = np.zeros(len(expr_data_genes))
                signatures_used[cell_type] = {
                    "markers_requested": marker_genes,
                    "markers_available": [],
                    "markers_used": 0
                }
                continue

            # Calculate average expression of signature genes
            signature_expr = expr_data_genes[available_genes].mean(axis=1)

            if normalize:
                # Z-score normalization
                mean_val = signature_expr.mean()
                std_val = signature_expr.std()
                if std_val > 0:
                    signature_expr = (signature_expr - mean_val) / std_val
                else:
                    signature_expr = signature_expr - mean_val

            cell_type_scores[cell_type] = signature_expr.values
            signatures_used[cell_type] = {
                "markers_requested": marker_genes,
                "markers_available": available_genes,
                "markers_used": len(available_genes)
            }

        # Create DataFrame of scores
        scores_df = pd.DataFrame(cell_type_scores, index=expr_data_genes.index)

        # Calculate summary statistics
        summary_stats = {}
        for cell_type in scores_df.columns:
            scores = scores_df[cell_type].values
            summary_stats[cell_type] = {
                "mean": float(scores.mean()),
                "median": float(np.median(scores)),
                "std": float(scores.std()),
                "min": float(scores.min()),
                "max": float(scores.max()),
                "markers_used": signatures_used[cell_type]["markers_used"]
            }

        # Identify dominant cell type per spot
        dominant_cell_types = scores_df.idxmax(axis=1).value_counts()

        # Prepare base response
        response = {
            "status": "success",
            "spots_analyzed": int(len(expr_data_genes)),
            "cell_types": [str(ct) for ct in signatures.keys()],  # Ensure strings
            "num_cell_types": int(len(signatures)),
            "normalized": bool(normalize),
            "summary_statistics": summary_stats,
            "dominant_cell_type_distribution": {
                str(cell_type): int(count)
                for cell_type, count in dominant_cell_types.items()
            },
            "mode": "real_analysis"
        }

        # Only include spot-level scores if explicitly requested
        # This prevents massive token usage for large datasets
        if include_spot_scores:
            spot_scores = []
            for spot_id in scores_df.index:
                spot_dict = {"spot_id": str(spot_id)}
                for cell_type in scores_df.columns:
                    spot_dict[str(cell_type)] = round(float(scores_df.loc[spot_id, cell_type]), 4)
                spot_scores.append(spot_dict)
            response["spot_scores"] = spot_scores
            response["warning"] = f"Returning {len(spot_scores)} spot-level scores. For large datasets, consider using summary_statistics instead."
        else:
            # Provide guidance on how to get spot-level data if needed
            response["note"] = "Spot-level scores excluded for token efficiency. Set include_spot_scores=True to include them."

        # Always include signatures metadata for transparency
        response["signatures_used"] = signatures_used

        return response

    except Exception as e:
        logger.error(f"Error performing cell type deconvolution: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to perform cell type deconvolution"
        }


# ============================================================================
# TOOL 10: get_spatial_data_for_patient (Clinical-Spatial Bridge)
# ============================================================================

# Clinical condition → Gene of Interest mapping
CONDITION_GENE_MAP = {
    "ovarian cancer": ["Ki67", "TP53", "BRCA1", "BRCA2", "EPCAM", "CA125", "PAX8"],
    "HGSOC": ["TP53", "Ki67", "FOXM1", "MYC", "CCNE1"],  # High-grade serous
    "platinum-resistant": ["ABCB1", "ERCC1", "GSTP1", "BRCA1"],
    "stage IV": ["Ki67", "MYC", "VIM", "CDH1"],  # Advanced cancer markers
    "serous carcinoma": ["TP53", "PAX8", "WT1", "CA125"]
}

# Treatment → Biomarker mapping
TREATMENT_BIOMARKER_MAP = {
    "bevacizumab": ["VEGFA", "CD31", "HIF1A", "KDR"],  # Anti-angiogenic
    "carboplatin": ["ERCC1", "XPA", "BRCA1", "BRCA2"],  # DNA repair
    "paclitaxel": ["TUBB3", "MAP2", "MAPT"],  # Microtubule targeting
    "avastin": ["VEGFA", "CD31", "HIF1A"]  # Brand name for bevacizumab
}

# Observation/Biomarker → Gene mapping
BIOMARKER_GENE_MAP = {
    "CA-125": ["CA125", "MUC16"],  # CA-125 is encoded by MUC16
    "BRCA": ["BRCA1", "BRCA2"],
    "high CA-125": ["CA125", "MUC16", "Ki67", "TP53"]  # Elevated tumor marker
}

# Patient ID → Spatial Dataset mapping
PATIENT_SPATIAL_MAP = {
    "patient-001": "PAT001-OVC-2025",
    "PAT001": "PAT001-OVC-2025"
}


@mcp.tool()
async def get_spatial_data_for_patient(
    patient_id: str,
    tissue_type: str = "tumor",
    include_clinical_context: bool = True,
    conditions: Optional[List[str]] = None,
    medications: Optional[List[str]] = None,
    biomarkers: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get spatial transcriptomics data for a patient with clinical context.

    This tool creates a bridge between clinical FHIR data (from mcp-epic) and
    spatial transcriptomics data, enriching spatial analysis with patient context.

    Args:
        patient_id: Patient identifier (e.g., "patient-001")
        tissue_type: Tissue type to analyze ("tumor", "normal", "margin")
        include_clinical_context: Include clinical metadata in response
        conditions: List of patient conditions (e.g., ["ovarian cancer", "HGSOC"])
        medications: List of current medications (e.g., ["Bevacizumab"])
        biomarkers: Dict of biomarker results (e.g., {"CA-125": 487})

    Returns:
        Dictionary containing:
        - spatial_data_path: Path to spatial expression data
        - coordinate_file: Path to spatial coordinates
        - annotation_file: Path to region annotations
        - genes_of_interest: Genes relevant to patient's condition
        - suggested_analyses: Recommended spatial analyses
        - clinical_summary: Patient clinical context (if requested)

    Example:
        >>> result = await get_spatial_data_for_patient(
        ...     patient_id="patient-001",
        ...     conditions=["ovarian cancer", "HGSOC"],
        ...     medications=["Bevacizumab"],
        ...     biomarkers={"CA-125": 487}
        ... )
        >>> print(result["genes_of_interest"])
        ['Ki67', 'TP53', 'VEGFA', 'CA125', 'BRCA1']
    """
    # Map patient ID to spatial dataset
    spatial_dataset = PATIENT_SPATIAL_MAP.get(patient_id, patient_id)

    # Build path to spatial data
    patient_data_dir = DATA_DIR / "patient-data" / spatial_dataset / "spatial"

    # Check if data exists
    if not patient_data_dir.exists():
        return {
            "status": "error",
            "error": f"No spatial data found for patient {patient_id}",
            "searched_path": str(patient_data_dir),
            "message": f"Expected spatial data at {patient_data_dir} but directory not found."
        }

    # Identify genes of interest based on clinical context
    genes_of_interest = set()

    if conditions:
        for condition in conditions:
            condition_lower = condition.lower()
            for key, genes in CONDITION_GENE_MAP.items():
                if key in condition_lower:
                    genes_of_interest.update(genes)

    if medications:
        for medication in medications:
            medication_lower = medication.lower()
            for key, genes in TREATMENT_BIOMARKER_MAP.items():
                if key in medication_lower:
                    genes_of_interest.update(genes)

    if biomarkers:
        for biomarker_name, value in biomarkers.items():
            biomarker_lower = biomarker_name.lower()
            # Check for elevated markers
            if isinstance(value, (int, float)) and value > 100:  # Arbitrary threshold
                key = f"high {biomarker_lower}"
                if key in BIOMARKER_GENE_MAP:
                    genes_of_interest.update(BIOMARKER_GENE_MAP[key])
            # Regular biomarker mapping
            for key, genes in BIOMARKER_GENE_MAP.items():
                if key in biomarker_lower:
                    genes_of_interest.update(genes)

    # Default genes if no clinical context provided
    if not genes_of_interest:
        genes_of_interest = {"Ki67", "CD8A", "VIM", "EPCAM"}  # General cancer markers

    # Build suggested analyses
    suggested_analyses = []

    if conditions and any("cancer" in c.lower() for c in conditions):
        suggested_analyses.extend([
            "Calculate spatial autocorrelation for proliferation markers (Ki67)",
            "Analyze immune infiltration patterns (CD8A, CD4)",
            "Assess tumor-stroma interaction (VIM, EPCAM)"
        ])

    if medications:
        if any("bevacizumab" in m.lower() or "avastin" in m.lower() for m in medications):
            suggested_analyses.append(
                "Evaluate angiogenesis markers (VEGFA, CD31) for treatment response"
            )
        if any("platinum" in m.lower() or "carboplatin" in m.lower() for m in medications):
            suggested_analyses.append(
                "Check DNA repair gene expression (BRCA1, ERCC1) for resistance markers"
            )

    # Build clinical summary
    clinical_summary = None
    if include_clinical_context:
        clinical_summary = {
            "patient_id": patient_id,
            "conditions": conditions or [],
            "medications": medications or [],
            "biomarkers": biomarkers or {},
            "tissue_type": tissue_type
        }

    # Prepare file paths
    expression_file = patient_data_dir / "visium_gene_expression.csv"
    coordinates_file = patient_data_dir / "visium_spatial_coordinates.csv"
    annotations_file = patient_data_dir / "visium_region_annotations.csv"

    result = {
        "status": "success",
        "patient_id": patient_id,
        "spatial_dataset": spatial_dataset,
        "data_directory": str(patient_data_dir),
        "files": {
            "expression": str(expression_file) if expression_file.exists() else None,
            "coordinates": str(coordinates_file) if coordinates_file.exists() else None,
            "annotations": str(annotations_file) if annotations_file.exists() else None
        },
        "genes_of_interest": sorted(list(genes_of_interest)),
        "num_genes_of_interest": len(genes_of_interest),
        "suggested_analyses": suggested_analyses,
        "tissue_type": tissue_type
    }

    if clinical_summary:
        result["clinical_summary"] = clinical_summary

    # Add available file info
    available_files = []
    for file_type, file_path in result["files"].items():
        if file_path and Path(file_path).exists():
            available_files.append(file_type)

    result["available_files"] = available_files
    result["data_ready"] = len(available_files) > 0

    return result


# ============================================================================
# VISUALIZATION TOOLS
# ============================================================================


@mcp.tool()
async def generate_spatial_heatmap(
    expression_file: str,
    coordinates_file: str,
    genes: List[str],
    output_filename: Optional[str] = None,
    colormap: str = "viridis"
) -> Dict[str, Any]:
    """Generate spatial heatmaps showing gene expression overlaid on tissue coordinates.

    Creates separate heatmap plots for each gene, showing expression intensity
    spatially distributed across the tissue. Useful for visualizing spatial
    expression patterns and identifying regional differences.

    Args:
        expression_file: Path to gene expression CSV (spots × genes)
        coordinates_file: Path to spatial coordinates CSV (spot_id, x, y)
        genes: List of gene names to visualize (max 6 recommended)
        output_filename: Custom output filename (default: spatial_heatmap_TIMESTAMP.png)
        colormap: Matplotlib colormap name (default: "viridis")

    Returns:
        Dictionary with:
        - output_file: Path to saved visualization
        - genes_plotted: List of genes successfully plotted
        - genes_not_found: List of requested genes not in data
        - description: Text description of the visualization

    Example:
        >>> result = await generate_spatial_heatmap(
        ...     expression_file="/data/expression.csv",
        ...     coordinates_file="/data/coordinates.csv",
        ...     genes=["Ki67", "CD8A", "VEGFA"],
        ...     colormap="plasma"
        ... )
        >>> print(result["output_file"])
        /workspace/output/visualizations/spatial_heatmap_20250108_123456.png
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "output_file": str(OUTPUT_DIR / "visualizations" / f"spatial_heatmap_dryrun.png"),
            "genes_plotted": genes[:6],
            "genes_not_found": [],
            "description": "DRY_RUN: Would generate spatial heatmap for " + ", ".join(genes[:6]),
            "message": "Set SPATIAL_DRY_RUN=false to generate real visualizations"
        })

    try:
        # Load data
        expr_data = pd.read_csv(expression_file, index_col=0)
        coord_data = pd.read_csv(coordinates_file, index_col=0)

        # Detect coordinate columns (handle Visium and generic formats)
        col_lower = {c: c.lower() for c in coord_data.columns}
        pxl_cols = [c for c, cl in col_lower.items() if 'pxl' in cl or 'pixel' in cl]
        xy_cols = [c for c, cl in col_lower.items()
                   if cl in ('x', 'y', 'x_coord', 'y_coord', 'spot_x', 'spot_y')]
        array_cols = [c for c, cl in col_lower.items()
                      if cl in ('array_row', 'array_col', 'row', 'col')]
        if len(pxl_cols) >= 2:
            x_col, y_col = pxl_cols[1], pxl_cols[0]  # col=x, row=y for Visium
        elif len(xy_cols) >= 2:
            x_col, y_col = xy_cols[0], xy_cols[1]
        elif len(array_cols) >= 2:
            x_col, y_col = array_cols[1], array_cols[0]
        else:
            numeric_cols = [c for c in coord_data.columns
                           if coord_data[c].dtype in ('int64', 'float64')]
            if len(numeric_cols) >= 2:
                x_col, y_col = numeric_cols[1], numeric_cols[0]
            else:
                return {
                    "status": "error",
                    "error": f"Could not find coordinate columns. Available: {list(coord_data.columns)}"
                }

        # Merge coordinates with expression
        merged = coord_data.join(expr_data, how="inner")

        # Identify available genes
        genes_plotted = [g for g in genes if g in expr_data.columns]
        genes_not_found = [g for g in genes if g not in expr_data.columns]

        if not genes_plotted:
            return {
                "status": "error",
                "error": "None of the requested genes found in expression data",
                "genes_requested": genes,
                "available_genes": list(expr_data.columns[:20])  # Show first 20
            }

        # Limit to max 6 genes for readability
        genes_to_plot = genes_plotted[:6]

        # Create subplot grid
        n_genes = len(genes_to_plot)
        n_cols = 3 if n_genes > 3 else n_genes
        n_rows = (n_genes + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
        if n_genes == 1:
            axes = np.array([axes])
        axes = axes.flatten()

        # Plot each gene
        for idx, gene in enumerate(genes_to_plot):
            ax = axes[idx]
            scatter = ax.scatter(
                merged[x_col],
                merged[y_col],
                c=merged[gene],
                cmap=colormap,
                s=50,
                alpha=0.8,
                edgecolors='none'
            )
            ax.set_title(f'{gene} Expression', fontsize=12, fontweight='bold')
            ax.set_xlabel('X Coordinate')
            ax.set_ylabel('Y Coordinate')
            ax.set_aspect('equal')
            plt.colorbar(scatter, ax=ax, label='Expression Level')

        # Hide unused subplots
        for idx in range(n_genes, len(axes)):
            axes[idx].axis('off')

        plt.tight_layout()

        # Save figure
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"spatial_heatmap_{timestamp}.png"

        output_path = OUTPUT_DIR / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Generate description
        description = f"Spatial heatmap showing expression of {len(genes_to_plot)} genes across tissue coordinates. "
        description += f"Genes plotted: {', '.join(genes_to_plot)}. "
        if genes_not_found:
            description += f"Genes not found: {', '.join(genes_not_found)}."

        return {
            "status": "success",
            "output_file": str(output_path),
            "genes_plotted": genes_to_plot,
            "genes_not_found": genes_not_found,
            "num_spots": len(merged),
            "description": description,
            "visualization_type": "spatial_heatmap",
            "colormap": colormap
        }

    except Exception as e:
        logger.error(f"Error generating spatial heatmap: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate spatial heatmap. Check file paths and formats."
        }


@mcp.tool()
async def generate_gene_expression_heatmap(
    expression_file: str,
    regions_file: str,
    genes: List[str],
    output_filename: Optional[str] = None,
    colormap: str = "RdYlBu_r"
) -> Dict[str, Any]:
    """Generate gene × region expression heatmap matrix.

    Creates a heatmap showing mean expression of selected genes across
    different tissue regions. Rows = genes, columns = regions, cell color =
    mean expression level. Useful for comparing regional gene expression patterns.

    Args:
        expression_file: Path to gene expression CSV (spots × genes)
        regions_file: Path to region annotations CSV (spot_id, region)
        genes: List of gene names to include in heatmap
        output_filename: Custom output filename (default: gene_region_heatmap_TIMESTAMP.png)
        colormap: Matplotlib colormap name (default: "RdYlBu_r")

    Returns:
        Dictionary with:
        - output_file: Path to saved visualization
        - genes_plotted: List of genes included
        - regions: List of tissue regions
        - expression_matrix: Gene × region mean expression values
        - description: Text description of the visualization

    Example:
        >>> result = await generate_gene_expression_heatmap(
        ...     expression_file="/data/expression.csv",
        ...     regions_file="/data/regions.csv",
        ...     genes=["Ki67", "PCNA", "CD8A", "CD68"],
        ...     colormap="coolwarm"
        ... )
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "output_file": str(OUTPUT_DIR / "visualizations" / f"gene_region_heatmap_dryrun.png"),
            "genes_plotted": genes,
            "regions": ["tumor_core", "stroma", "necrotic"],
            "description": "DRY_RUN: Would generate gene × region expression heatmap",
            "message": "Set SPATIAL_DRY_RUN=false to generate real visualizations"
        })

    try:
        # Load data
        expr_data = pd.read_csv(expression_file, index_col=0)
        region_data = pd.read_csv(regions_file, index_col=0)

        # Merge expression with regions
        merged = expr_data.join(region_data, how="inner")

        # Identify available genes
        genes_available = [g for g in genes if g in expr_data.columns]
        if not genes_available:
            return {
                "status": "error",
                "error": "None of the requested genes found in expression data",
                "genes_requested": genes
            }

        # Get region column (usually named 'region' or first column)
        region_col = 'region' if 'region' in merged.columns else merged.columns[-1]

        # Calculate mean expression per gene per region
        mean_expr = merged.groupby(region_col)[genes_available].mean()

        # Create heatmap
        fig, ax = plt.subplots(figsize=(max(8, len(mean_expr.columns) * 0.8),
                                        max(6, len(mean_expr) * 0.5)))

        sns.heatmap(
            mean_expr.T,  # Transpose so genes are rows, regions are columns
            annot=True,
            fmt='.2f',
            cmap=colormap,
            cbar_kws={'label': 'Mean Expression'},
            linewidths=0.5,
            linecolor='gray',
            ax=ax
        )

        ax.set_xlabel('Tissue Region', fontsize=12, fontweight='bold')
        ax.set_ylabel('Gene', fontsize=12, fontweight='bold')
        ax.set_title('Gene Expression by Tissue Region', fontsize=14, fontweight='bold')
        plt.tight_layout()

        # Save figure
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"gene_region_heatmap_{timestamp}.png"

        output_path = OUTPUT_DIR / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Generate description
        regions_list = list(mean_expr.index)
        description = f"Gene expression heatmap showing mean expression of {len(genes_available)} genes across {len(regions_list)} tissue regions. "
        description += f"Genes: {', '.join(genes_available)}. "
        description += f"Regions: {', '.join(regions_list)}."

        return {
            "status": "success",
            "output_file": str(output_path),
            "genes_plotted": genes_available,
            "regions": regions_list,
            "expression_matrix": mean_expr.T.to_dict(),
            "description": description,
            "visualization_type": "gene_region_heatmap",
            "colormap": colormap
        }

    except Exception as e:
        logger.error(f"Error generating gene expression heatmap: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate gene expression heatmap. Check file paths and formats."
        }


@mcp.tool()
async def generate_region_composition_chart(
    regions_file: str,
    output_filename: Optional[str] = None,
    colormap: str = "Set3"
) -> Dict[str, Any]:
    """Generate bar chart showing number of spots per tissue region.

    Creates a bar chart displaying the distribution of spatial spots across
    different tissue regions. Useful for understanding tissue composition and
    ensuring adequate sampling of each region.

    Args:
        regions_file: Path to region annotations CSV (spot_id, region)
        output_filename: Custom output filename (default: region_composition_TIMESTAMP.png)
        colormap: Matplotlib colormap name for bar colors (default: "Set3")

    Returns:
        Dictionary with:
        - output_file: Path to saved visualization
        - region_counts: Dict of region names to spot counts
        - total_spots: Total number of spots
        - description: Text description of the visualization

    Example:
        >>> result = await generate_region_composition_chart(
        ...     regions_file="/data/regions.csv",
        ...     colormap="pastel"
        ... )
        >>> print(result["region_counts"])
        {'tumor_core': 156, 'stroma': 312, 'necrotic': 87}
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "output_file": str(OUTPUT_DIR / "visualizations" / f"region_composition_dryrun.png"),
            "region_counts": {"tumor_core": 150, "stroma": 300, "necrotic": 100},
            "total_spots": 550,
            "description": "DRY_RUN: Would generate region composition bar chart",
            "message": "Set SPATIAL_DRY_RUN=false to generate real visualizations"
        })

    try:
        # Load region data
        region_data = pd.read_csv(regions_file, index_col=0)

        # Get region column
        region_col = 'region' if 'region' in region_data.columns else region_data.columns[0]

        # Count spots per region
        region_counts = region_data[region_col].value_counts().sort_index()

        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))

        colors = plt.cm.get_cmap(colormap)(np.linspace(0, 1, len(region_counts)))

        bars = ax.bar(
            range(len(region_counts)),
            region_counts.values,
            color=colors,
            edgecolor='black',
            linewidth=1.5
        )

        ax.set_xticks(range(len(region_counts)))
        ax.set_xticklabels(region_counts.index, rotation=45, ha='right')
        ax.set_xlabel('Tissue Region', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Spots', fontsize=12, fontweight='bold')
        ax.set_title('Tissue Region Composition', fontsize=14, fontweight='bold')

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{int(height)}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold'
            )

        ax.grid(axis='y', alpha=0.3, linestyle='--')
        plt.tight_layout()

        # Save figure
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"region_composition_{timestamp}.png"

        output_path = OUTPUT_DIR / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Generate description
        total_spots = int(region_counts.sum())
        description = f"Region composition bar chart showing distribution of {total_spots} spots across {len(region_counts)} tissue regions. "
        description += "Spot counts: " + ", ".join([f"{region}={count}" for region, count in region_counts.items()])

        return {
            "status": "success",
            "output_file": str(output_path),
            "region_counts": region_counts.to_dict(),
            "total_spots": total_spots,
            "num_regions": len(region_counts),
            "description": description,
            "visualization_type": "region_composition_bar_chart",
            "colormap": colormap
        }

    except Exception as e:
        logger.error(f"Error generating region composition chart: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate region composition chart. Check file path and format."
        }


@mcp.tool()
async def visualize_spatial_autocorrelation(
    autocorrelation_results: Dict[str, Any],
    output_filename: Optional[str] = None,
    top_n: int = 15
) -> Dict[str, Any]:
    """Generate bar chart of Moran's I spatial autocorrelation statistics.

    Creates a bar chart showing Moran's I values for genes, sorted by
    autocorrelation strength. Positive values = clustered, negative = dispersed.
    Useful for identifying which genes have the strongest spatial patterns.

    Args:
        autocorrelation_results: Output from calculate_spatial_autocorrelation tool
        output_filename: Custom output filename (default: morans_i_plot_TIMESTAMP.png)
        top_n: Number of top genes to display (default: 15)

    Returns:
        Dictionary with:
        - output_file: Path to saved visualization
        - genes_plotted: List of genes included in plot
        - description: Text description of the visualization

    Example:
        >>> autocorr = await calculate_spatial_autocorrelation(...)
        >>> result = await visualize_spatial_autocorrelation(
        ...     autocorrelation_results=autocorr,
        ...     top_n=10
        ... )
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "output_file": str(OUTPUT_DIR / "visualizations" / f"morans_i_plot_dryrun.png"),
            "genes_plotted": ["Ki67", "CD8A", "VEGFA"],
            "description": "DRY_RUN: Would generate Moran's I bar chart",
            "message": "Set SPATIAL_DRY_RUN=false to generate real visualizations"
        })

    try:
        # Extract results from autocorrelation output
        if "results" not in autocorrelation_results:
            return {
                "status": "error",
                "error": "Invalid autocorrelation_results format. Expected 'results' key.",
                "message": "Provide output from calculate_spatial_autocorrelation tool"
            }

        results = autocorrelation_results["results"]

        # Convert to DataFrame
        df = pd.DataFrame(results)

        # Filter out genes not found
        df = df[df.get("morans_i").notna()].copy()

        if len(df) == 0:
            return {
                "status": "error",
                "error": "No valid Moran's I results found",
                "message": "All genes may be missing from expression data"
            }

        # Sort by absolute Moran's I value and take top N
        df['abs_morans_i'] = df['morans_i'].abs()
        df = df.sort_values('abs_morans_i', ascending=False).head(top_n)

        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))

        # Color bars based on sign (positive = clustered, negative = dispersed)
        colors = ['#d62728' if x < 0 else '#2ca02c' for x in df['morans_i']]

        bars = ax.barh(range(len(df)), df['morans_i'], color=colors, edgecolor='black', linewidth=1.2)

        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df['gene'])
        ax.set_xlabel("Moran's I Statistic", fontsize=12, fontweight='bold')
        ax.set_ylabel('Gene', fontsize=12, fontweight='bold')
        ax.set_title("Spatial Autocorrelation (Moran's I)", fontsize=14, fontweight='bold')

        # Add vertical line at 0
        ax.axvline(x=0, color='black', linestyle='-', linewidth=1.5)

        # Add value labels
        for idx, (bar, value) in enumerate(zip(bars, df['morans_i'])):
            x_pos = value + (0.02 if value > 0 else -0.02)
            ha = 'left' if value > 0 else 'right'
            ax.text(
                x_pos,
                bar.get_y() + bar.get_height() / 2.,
                f'{value:.3f}',
                ha=ha,
                va='center',
                fontsize=9,
                fontweight='bold'
            )

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ca02c', edgecolor='black', label='Clustered (I > 0)'),
            Patch(facecolor='#d62728', edgecolor='black', label='Dispersed (I < 0)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        ax.grid(axis='x', alpha=0.3, linestyle='--')
        plt.tight_layout()

        # Save figure
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"morans_i_plot_{timestamp}.png"

        output_path = OUTPUT_DIR / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Generate description
        genes_plotted = df['gene'].tolist()
        clustered_genes = df[df['morans_i'] > 0.3]['gene'].tolist()
        dispersed_genes = df[df['morans_i'] < -0.3]['gene'].tolist()

        description = f"Moran's I spatial autocorrelation plot showing top {len(genes_plotted)} genes. "
        if clustered_genes:
            description += f"Significantly clustered: {', '.join(clustered_genes)}. "
        if dispersed_genes:
            description += f"Significantly dispersed: {', '.join(dispersed_genes)}."

        return {
            "status": "success",
            "output_file": str(output_path),
            "genes_plotted": genes_plotted,
            "num_genes": len(genes_plotted),
            "description": description,
            "visualization_type": "morans_i_bar_chart"
        }

    except Exception as e:
        logger.error(f"Error visualizing spatial autocorrelation: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to visualize spatial autocorrelation. Check input format."
        }


# ============================================================================
# MCP RESOURCES
# ============================================================================


@mcp.resource("data://spatial/raw")
def get_raw_spatial_data() -> str:
    """Raw spatial transcriptomics data resource.

    Provides information about raw spatial transcriptomics data format
    and access patterns.

    Returns:
        JSON string with raw data metadata
    """
    return json.dumps({
        "resource": "data://spatial/raw",
        "description": "Raw spatial transcriptomics data files",
        "data_directory": str(DATA_DIR / "raw"),
        "supported_formats": ["FASTQ", "CSV", "H5AD"],
        "typical_files": {
            "fastq_r1": "Spatial barcodes + UMIs",
            "fastq_r2": "cDNA sequences",
            "barcodes": "Spatial barcode whitelist",
            "coordinates": "Spot/cell coordinates"
        },
        "example_workflow": "1. Quality control → 2. Barcode extraction → 3. Alignment"
    }, indent=2)


@mcp.resource("data://spatial/filtered")
def get_filtered_spatial_data() -> str:
    """Quality-filtered spatial data resource.

    Provides information about QC-filtered spatial transcriptomics data.

    Returns:
        JSON string with filtered data metadata
    """
    return json.dumps({
        "resource": "data://spatial/filtered",
        "description": "Quality-filtered spatial transcriptomics data",
        "data_directory": str(DATA_DIR / "filtered"),
        "filtering_criteria": {
            "min_reads_per_barcode": MIN_READS_PER_BARCODE,
            "min_genes_per_barcode": MIN_GENES_PER_BARCODE,
            "max_mt_percent": MAX_MT_PERCENT
        },
        "format": "CSV with spatial coordinates and QC metrics",
        "typical_retention_rate": "80-90% of barcodes"
    }, indent=2)


@mcp.resource("data://spatial/aligned")
def get_aligned_spatial_data() -> str:
    """Aligned spatial expression data resource.

    Provides information about aligned spatial transcriptomics data with
    gene expression matrices.

    Returns:
        JSON string with aligned data metadata
    """
    return json.dumps({
        "resource": "data://spatial/aligned",
        "description": "Aligned spatial transcriptomics expression matrices",
        "data_directory": str(DATA_DIR / "aligned"),
        "file_types": {
            "bam": "Aligned reads with spatial tags",
            "matrix": "Gene × Barcode expression matrix",
            "spatial_coords": "Barcode spatial coordinates"
        },
        "downstream_analysis": [
            "Clustering and cell type annotation",
            "Differential expression",
            "Spatial pattern detection",
            "Cell-cell communication"
        ]
    }, indent=2)


# ============================================================================
# SERVER ENTRYPOINT
# ============================================================================


def main() -> None:
    """Run the MCP Spatial Tools server."""
    _ensure_directories()
    _run_server(mcp, server_name="mcp-spatialtools", dry_run=DRY_RUN, env_var="SPATIAL_DRY_RUN")


if __name__ == "__main__":
    main()
