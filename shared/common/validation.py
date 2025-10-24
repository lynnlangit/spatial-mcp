"""Input validation utilities for MCP servers."""

import re
from pathlib import Path
from typing import List, Optional


class MCPValidationError(ValueError):
    """Custom exception for MCP input validation errors."""

    pass


class MCPServerError(Exception):
    """Base exception for MCP server errors."""

    pass


def validate_file_path(
    path: str,
    must_exist: bool = False,
    allowed_extensions: Optional[List[str]] = None,
    max_size_bytes: Optional[int] = None
) -> Path:
    """Validate and sanitize a file path.

    This function prevents path traversal attacks and validates
    file properties.

    Args:
        path: File path to validate
        must_exist: If True, raises error if file doesn't exist
        allowed_extensions: List of allowed file extensions (e.g., ['.fastq', '.fasta'])
        max_size_bytes: Maximum allowed file size in bytes

    Returns:
        Validated Path object

    Raises:
        MCPValidationError: If validation fails

    Example:
        >>> path = validate_file_path(
        ...     "/data/sample.fastq",
        ...     must_exist=True,
        ...     allowed_extensions=['.fastq', '.fq']
        ... )
    """
    try:
        file_path = Path(path).resolve()
    except (ValueError, RuntimeError) as e:
        raise MCPValidationError(f"Invalid path '{path}': {e}") from e

    # Prevent path traversal
    if ".." in path:
        raise MCPValidationError(
            f"Path traversal detected in '{path}'. Paths containing '..' are not allowed."
        )

    # Check existence if required
    if must_exist and not file_path.exists():
        raise MCPValidationError(f"File not found: {file_path}")

    # Check file extension
    if allowed_extensions:
        if file_path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
            raise MCPValidationError(
                f"Invalid file extension '{file_path.suffix}'. "
                f"Allowed extensions: {', '.join(allowed_extensions)}"
            )

    # Check file size
    if max_size_bytes and file_path.exists():
        actual_size = file_path.stat().st_size
        if actual_size > max_size_bytes:
            raise MCPValidationError(
                f"File size {actual_size:,} bytes exceeds maximum {max_size_bytes:,} bytes"
            )

    return file_path


def validate_genome_id(genome_id: str) -> str:
    """Validate a genome reference identifier.

    Args:
        genome_id: Genome identifier (e.g., 'hg38', 'mm10', 'hg19')

    Returns:
        Validated genome ID

    Raises:
        MCPValidationError: If genome ID is invalid

    Example:
        >>> genome = validate_genome_id("hg38")
        >>> genome
        'hg38'
    """
    # Supported genome assemblies
    SUPPORTED_GENOMES = {
        "hg38",      # Human GRCh38
        "hg19",      # Human GRCh37
        "mm10",      # Mouse GRCm38
        "mm39",      # Mouse GRCm39
        "rn6",       # Rat
        "danRer11",  # Zebrafish
    }

    if genome_id not in SUPPORTED_GENOMES:
        raise MCPValidationError(
            f"Unsupported genome '{genome_id}'. "
            f"Supported genomes: {', '.join(sorted(SUPPORTED_GENOMES))}"
        )

    return genome_id


def validate_fastq_format(fastq_path: Path) -> bool:
    """Validate FASTQ file format.

    Performs basic validation of FASTQ file structure by checking
    the first few records.

    Args:
        fastq_path: Path to FASTQ file

    Returns:
        True if format is valid

    Raises:
        MCPValidationError: If format is invalid

    Example:
        >>> is_valid = validate_fastq_format(Path("sample.fastq"))
    """
    import gzip

    # Determine if file is gzipped
    is_gzipped = fastq_path.suffix == ".gz"

    try:
        if is_gzipped:
            file_handle = gzip.open(fastq_path, "rt")
        else:
            file_handle = open(fastq_path, "r")

        # Check first record (4 lines)
        with file_handle:
            for i in range(4):
                line = file_handle.readline()
                if not line:
                    raise MCPValidationError(
                        f"FASTQ file is truncated or empty: {fastq_path}"
                    )

                # First line should start with '@'
                if i == 0 and not line.startswith("@"):
                    raise MCPValidationError(
                        f"Invalid FASTQ format: first line should start with '@': {fastq_path}"
                    )

                # Third line should start with '+'
                if i == 2 and not line.startswith("+"):
                    raise MCPValidationError(
                        f"Invalid FASTQ format: third line should start with '+': {fastq_path}"
                    )

    except (OSError, IOError) as e:
        raise MCPValidationError(f"Error reading FASTQ file: {e}") from e

    return True


def sanitize_tool_input(value: str, param_name: str, max_length: int = 1000) -> str:
    """Sanitize string input for tool parameters.

    Prevents injection attacks by removing potentially dangerous characters.

    Args:
        value: Input string to sanitize
        param_name: Name of the parameter (for error messages)
        max_length: Maximum allowed string length

    Returns:
        Sanitized string

    Raises:
        MCPValidationError: If validation fails

    Example:
        >>> safe_value = sanitize_tool_input("sample_001", "sample_id")
    """
    if not isinstance(value, str):
        raise MCPValidationError(
            f"Parameter '{param_name}' must be a string, got {type(value).__name__}"
        )

    if len(value) > max_length:
        raise MCPValidationError(
            f"Parameter '{param_name}' exceeds maximum length of {max_length} characters"
        )

    # Remove potentially dangerous characters for shell commands
    # Allow: alphanumeric, underscore, hyphen, period, forward slash
    if not re.match(r"^[a-zA-Z0-9_\-./]+$", value):
        raise MCPValidationError(
            f"Parameter '{param_name}' contains invalid characters. "
            "Only alphanumeric, underscore, hyphen, period, and forward slash are allowed."
        )

    return value


def validate_thread_count(threads: int, max_threads: int = 64) -> int:
    """Validate thread count parameter.

    Args:
        threads: Number of threads requested
        max_threads: Maximum allowed threads

    Returns:
        Validated thread count

    Raises:
        MCPValidationError: If thread count is invalid

    Example:
        >>> threads = validate_thread_count(8)
    """
    if not isinstance(threads, int):
        raise MCPValidationError(
            f"Thread count must be an integer, got {type(threads).__name__}"
        )

    if threads < 1:
        raise MCPValidationError("Thread count must be at least 1")

    if threads > max_threads:
        raise MCPValidationError(
            f"Thread count {threads} exceeds maximum of {max_threads}"
        )

    return threads
