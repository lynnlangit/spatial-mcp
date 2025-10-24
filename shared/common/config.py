"""Configuration management for MCP servers."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """Base configuration for all MCP servers.

    This class provides common configuration options that all MCP servers
    need. Individual servers should inherit from this and add their own
    specific configuration fields.

    Environment variables can be used to override defaults by prefixing
    with the server name (e.g., FGBIO_LOG_LEVEL).
    """

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Python logging format string"
    )

    # Data paths
    data_dir: Path = Field(
        default=Path("/workspace/data"),
        description="Base directory for data storage"
    )

    cache_dir: Path = Field(
        default=Path("/workspace/cache"),
        description="Directory for caching temporary files"
    )

    # Resource limits
    max_file_size_gb: int = Field(
        default=10,
        description="Maximum file size in GB for uploads/downloads"
    )

    timeout_seconds: int = Field(
        default=300,
        description="Default timeout for operations in seconds"
    )

    # Performance tuning
    max_workers: int = Field(
        default=4,
        description="Maximum number of concurrent worker threads"
    )

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_gb * 1024 * 1024 * 1024


class FGbioConfig(BaseConfig):
    """Configuration specific to mcp-FGbio server."""

    reference_data_dir: Path = Field(
        default=Path("/workspace/data/reference"),
        description="Directory containing reference genome data"
    )

    fgbio_jar_path: Optional[Path] = Field(
        default=None,
        description="Path to FGbio JAR file (optional for mocking)"
    )

    java_executable: str = Field(
        default="java",
        description="Path to Java executable"
    )

    java_memory_gb: int = Field(
        default=8,
        description="Java heap memory allocation in GB"
    )

    # Reference genome sources
    ncbi_base_url: str = Field(
        default="https://ftp.ncbi.nlm.nih.gov/genomes",
        description="NCBI FTP base URL for reference genomes"
    )

    gencode_base_url: str = Field(
        default="https://ftp.ebi.ac.uk/pub/databases/gencode",
        description="GENCODE FTP base URL for annotations"
    )

    # Validation settings
    min_fastq_quality_score: int = Field(
        default=20,
        description="Minimum average quality score for FASTQ validation"
    )

    class Config:
        """Pydantic configuration."""
        env_prefix = "FGBIO_"
        env_file = ".env"
