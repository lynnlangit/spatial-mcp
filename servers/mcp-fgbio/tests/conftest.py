"""Pytest configuration and shared fixtures."""

import gzip
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests.

    Yields:
        Path to temporary directory

    The directory is automatically cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_fastq_file(temp_dir: Path) -> Path:
    """Create a mock FASTQ file for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to mock FASTQ file
    """
    fastq_path = temp_dir / "sample.fastq"

    # Create a valid FASTQ file with 100 reads
    with open(fastq_path, "w") as f:
        for i in range(100):
            f.write(f"@READ{i:05d}\n")
            f.write("ACGTACGTACGTACGTACGTACGTACGTACGTACGT\n")  # 36bp sequence
            f.write("+\n")
            f.write("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII\n")  # Quality scores (Phred+33)

    return fastq_path


@pytest.fixture
def mock_fastq_gz_file(temp_dir: Path) -> Path:
    """Create a mock gzipped FASTQ file for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to mock gzipped FASTQ file
    """
    fastq_gz_path = temp_dir / "sample.fastq.gz"

    # Create a valid gzipped FASTQ file
    with gzip.open(fastq_gz_path, "wt") as f:
        for i in range(100):
            f.write(f"@READ{i:05d}\n")
            f.write("ACGTACGTACGTACGTACGTACGTACGTACGTACGT\n")
            f.write("+\n")
            f.write("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII\n")

    return fastq_gz_path


@pytest.fixture
def mock_low_quality_fastq(temp_dir: Path) -> Path:
    """Create a mock FASTQ file with low quality scores.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to low quality FASTQ file
    """
    fastq_path = temp_dir / "low_quality.fastq"

    # Create FASTQ with low quality (Phred score ~10)
    with open(fastq_path, "w") as f:
        for i in range(100):
            f.write(f"@READ{i:05d}\n")
            f.write("ACGTACGTACGTACGTACGTACGTACGTACGTACGT\n")  # 36 bp
            f.write("+\n")
            f.write("++++++++++++++++++++++++++++++++++++\n")  # 36 quality scores (Phred ~10)

    return fastq_path


@pytest.fixture
def mock_invalid_fastq(temp_dir: Path) -> Path:
    """Create an invalid FASTQ file for testing error handling.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to invalid FASTQ file
    """
    fastq_path = temp_dir / "invalid.fastq"

    # Create invalid FASTQ (missing + line)
    with open(fastq_path, "w") as f:
        f.write("@READ00001\n")
        f.write("ACGTACGTACGT\n")
        f.write("IIIIIIIIIIII\n")  # Missing + separator

    return fastq_path


@pytest.fixture
def mock_reference_genome(temp_dir: Path) -> Path:
    """Create a mock reference genome file.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to mock reference genome FASTA file
    """
    fasta_path = temp_dir / "hg38.fna.gz"

    # Create a small mock genome
    with gzip.open(fasta_path, "wt") as f:
        f.write(">chr1\n")
        f.write("ACGTACGTACGTACGTACGTACGTACGTACGTACGT\n")
        f.write(">chr2\n")
        f.write("TGCATGCATGCATGCATGCATGCATGCATGCATGCA\n")

    return fasta_path


@pytest.fixture
def mock_fgbio_output() -> dict:
    """Mock FGbio command output.

    Returns:
        Dictionary with mock FGbio results
    """
    return {
        "stdout": "Successfully processed 1000000 reads\nExtracted 45000 unique UMIs\n",
        "stderr": "",
        "returncode": 0
    }


@pytest.fixture(autouse=True)
def set_env_vars(temp_dir: Path, monkeypatch) -> None:
    """Set environment variables for testing.

    Args:
        temp_dir: Temporary directory fixture
        monkeypatch: Pytest monkeypatch fixture

    This fixture automatically sets environment variables for all tests.
    """
    monkeypatch.setenv("FGBIO_REFERENCE_DATA_DIR", str(temp_dir / "reference"))
    monkeypatch.setenv("FGBIO_CACHE_DIR", str(temp_dir / "cache"))
    monkeypatch.setenv("FGBIO_DRY_RUN", "true")  # Enable dry-run mode for tests
    monkeypatch.setenv("FGBIO_TIMEOUT_SECONDS", "30")
