"""Alignment tools: STAR alignment and related utilities."""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

import numpy as np

logger = logging.getLogger(__name__)


def _parse_star_log(log_file_path: Path) -> Dict[str, Any]:
    """Parse STAR Log.final.out to extract alignment statistics.

    Args:
        log_file_path: Path to STAR Log.final.out file

    Returns:
        Dictionary with alignment statistics

    Raises:
        IOError: If log file not found or parsing fails
    """
    if not log_file_path.exists():
        raise IOError(f"STAR log file not found: {log_file_path}")

    try:
        total_reads = 0
        uniquely_mapped = 0
        multi_mapped = 0
        unmapped_mismatches = 0
        unmapped_short = 0
        unmapped_other = 0

        with open(log_file_path, 'r') as f:
            for line in f:
                line = line.strip()

                if "Number of input reads" in line:
                    total_reads = int(line.split('|')[1].strip())
                elif "Uniquely mapped reads number" in line:
                    uniquely_mapped = int(line.split('|')[1].strip())
                elif "Number of reads mapped to multiple loci" in line:
                    multi_mapped = int(line.split('|')[1].strip())
                elif "Number of reads unmapped: too many mismatches" in line:
                    unmapped_mismatches = int(line.split('|')[1].strip())
                elif "Number of reads unmapped: too short" in line:
                    unmapped_short = int(line.split('|')[1].strip())
                elif "Number of reads unmapped: other" in line:
                    unmapped_other = int(line.split('|')[1].strip())

        unmapped = unmapped_mismatches + unmapped_short + unmapped_other

        counted_total = uniquely_mapped + multi_mapped + unmapped
        if abs(counted_total - total_reads) > 100:
            raise ValueError(
                f"STAR log parsing error: counted {counted_total} reads "
                f"but log reports {total_reads} total reads"
            )

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
    """Generate synthetic paired-end FASTQ files for testing."""
    import gzip
    import random

    nucleotides = ['A', 'C', 'G', 'T']
    quality_char = '?' * read_length

    def generate_read(read_num: int, r_type: str) -> str:
        sequence = ''.join(random.choice(nucleotides) for _ in range(read_length))
        return f"@read_{read_num}_{r_type}\n{sequence}\n+\n{quality_char}\n"

    with gzip.open(output_r1, 'wt') as f1:
        for i in range(num_reads):
            f1.write(generate_read(i, 'R1'))

    with gzip.open(output_r2, 'wt') as f2:
        for i in range(num_reads):
            f2.write(generate_read(i, 'R2'))

    logger.info(f"Created synthetic FASTQ files: {output_r1}, {output_r2}")
    logger.info(f"  Reads: {num_reads}, Length: {read_length}bp")
    logger.info(f"  R1 size: {output_r1.stat().st_size / 1024:.1f} KB")
    logger.info(f"  R2 size: {output_r2.stat().st_size / 1024:.1f} KB")


async def align_spatial_data_impl(
    fastq_r1: str,
    fastq_r2: str,
    reference_genome: str,
    output_dir: str,
    threads: int,
    *,
    dry_run: bool,
    star_path: str,
    ensure_directories: callable,
) -> Dict[str, Any]:
    """Align reads to reference genome using STAR aligner."""
    ensure_directories()

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

    if dry_run:
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

    try:
        star_cmd = [
            star_path,
            "--runThreadN", str(threads),
            "--genomeDir", str(genome_path),
            "--readFilesIn", str(r2_path), str(r1_path),
            "--readFilesCommand", "zcat" if r1_path.suffix == ".gz" else "cat",
            "--outFileNamePrefix", str(output_path) + "/",
            "--outSAMtype", "BAM", "SortedByCoordinate",
            "--outSAMattributes", "NH", "HI", "AS", "nM", "NM", "MD",
            "--limitBAMsortRAM", "32000000000"
        ]

        result = subprocess.run(
            star_cmd,
            capture_output=True,
            text=True,
            timeout=1800
        )

        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                star_cmd,
                result.stdout,
                result.stderr
            )

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
