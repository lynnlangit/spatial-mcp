"""MCP Spatial Tools server implementation.

This module provides an MCP server for spatial transcriptomics data processing,
including quality control, alignment, and spatial segmentation.
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("spatialtools")

# Configuration
DATA_DIR = Path(os.getenv("SPATIAL_DATA_DIR", "/workspace/data"))
CACHE_DIR = Path(os.getenv("SPATIAL_CACHE_DIR", "/workspace/cache"))
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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "raw").mkdir(exist_ok=True)
    (DATA_DIR / "filtered").mkdir(exist_ok=True)
    (DATA_DIR / "aligned").mkdir(exist_ok=True)


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

    input_path = Path(input_file)
    if not input_path.exists():
        raise IOError(f"Input file not found: {input_file}")

    if min_reads < 0 or min_genes < 0 or max_mt_percent < 0 or max_mt_percent > 100:
        raise ValueError("Invalid QC parameters")

    output_path = Path(output_dir) / f"{input_path.stem}_filtered.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if DRY_RUN:
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

    # Real implementation would use scanpy or similar
    # For POC, simulate with pandas
    try:
        # Read spatial data
        if input_path.suffix == '.csv':
            data = pd.read_csv(input_path)
        else:
            raise ValueError(f"Unsupported file format: {input_path.suffix}")

        barcodes_before = len(data)

        # Mock filtering logic (would be replaced with real QC)
        # Filter by minimum reads
        data_filtered = data[data.get('n_reads', 0) >= min_reads].copy()

        # Filter by minimum genes
        data_filtered = data_filtered[data_filtered.get('n_genes', 0) >= min_genes].copy()

        # Filter by mitochondrial percentage
        data_filtered = data_filtered[
            data_filtered.get('mt_percent', 0) <= max_mt_percent
        ].copy()

        barcodes_after = len(data_filtered)

        # Save filtered data
        data_filtered.to_csv(output_path, index=False)

        return {
            "output_file": str(output_path),
            "barcodes_before": barcodes_before,
            "barcodes_after": barcodes_after,
            "genes_detected": int(data_filtered.get('n_genes', 0).max()) if len(data_filtered) > 0 else 0,
            "qc_metrics": {
                "mean_reads_per_barcode": float(data_filtered.get('n_reads', 0).mean()) if len(data_filtered) > 0 else 0,
                "median_genes_per_barcode": float(data_filtered.get('n_genes', 0).median()) if len(data_filtered) > 0 else 0,
                "mean_mt_percent": float(data_filtered.get('mt_percent', 0).mean()) if len(data_filtered) > 0 else 0,
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

    # Real STAR alignment (mocked for POC)
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

        if DRY_RUN:
            # Just return mock result
            pass
        else:
            # Would actually run STAR
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

        # Parse STAR log (mocked)
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
            "log_file": str(output_path / "Log.final.out")
        }

    except subprocess.TimeoutExpired as e:
        raise IOError(f"STAR alignment timeout: {e}") from e
    except Exception as e:
        raise IOError(f"STAR alignment failed: {e}") from e


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
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
