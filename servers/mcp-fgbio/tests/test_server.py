"""Unit tests for mcp-fgbio server tools."""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_fgbio import server
from mcp_fgbio.server import (
    _calculate_md5,
    _download_file,
    _run_fgbio_command,
)

# Get the underlying functions from the decorated tools
# FastMCP 2.11.4+ uses .fn attribute instead of __wrapped__
extract_umis = server.extract_umis.fn
fetch_reference_genome = server.fetch_reference_genome.fn
query_gene_annotations = server.query_gene_annotations.fn
validate_fastq = server.validate_fastq.fn


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_calculate_md5(self, mock_fastq_file: Path) -> None:
        """Test MD5 checksum calculation."""
        md5sum = _calculate_md5(mock_fastq_file)

        # MD5 should be a 32-character hex string
        assert isinstance(md5sum, str)
        assert len(md5sum) == 32
        assert all(c in "0123456789abcdef" for c in md5sum)

        # Same file should produce same checksum
        md5sum2 = _calculate_md5(mock_fastq_file)
        assert md5sum == md5sum2

    @patch("subprocess.run")
    def test_run_fgbio_command_success(self, mock_run: MagicMock) -> None:
        """Test successful FGbio command execution."""
        # Since we're in DRY_RUN mode, this should return mock result
        result = _run_fgbio_command(["--version"])

        assert result.returncode == 0
        assert "[DRY RUN]" in result.stdout

    @patch("subprocess.run")
    def test_run_fgbio_command_timeout(self, mock_run: MagicMock, monkeypatch) -> None:
        """Test FGbio command timeout handling."""
        # Disable dry-run for this test
        monkeypatch.setenv("FGBIO_DRY_RUN", "false")

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["java"], timeout=30
        )

        with pytest.raises(subprocess.TimeoutExpired):
            _run_fgbio_command(["--version"], timeout=30)

    @pytest.mark.asyncio
    async def test_download_file_success(self, temp_dir: Path) -> None:
        """Test successful file download."""
        output_path = temp_dir / "downloaded.fna.gz"
        url = "https://example.com/genome.fna.gz"

        # In DRY_RUN mode, this creates a mock file
        result = await _download_file(url, output_path)

        assert result["url"] == url
        assert Path(result["path"]) == output_path
        assert output_path.exists()
        assert "md5sum" in result
        assert "size_bytes" in result


# ============================================================================
# TOOL TESTS: fetch_reference_genome
# ============================================================================


class TestFetchReferenceGenome:
    """Test suite for fetch_reference_genome tool."""

    @pytest.mark.asyncio
    async def test_fetch_valid_genome(self, temp_dir: Path) -> None:
        """Test downloading a valid genome."""
        result = await fetch_reference_genome(
            genome="hg38",
            output_dir=str(temp_dir)
        )

        assert "path" in result
        assert "size_mb" in result
        assert "md5sum" in result
        assert "metadata" in result
        assert result["metadata"]["genome_id"] == "hg38"
        assert Path(result["path"]).exists()

    @pytest.mark.asyncio
    async def test_fetch_invalid_genome(self, temp_dir: Path) -> None:
        """Test error handling for invalid genome ID."""
        with pytest.raises(ValueError, match="Unsupported genome"):
            await fetch_reference_genome(
                genome="invalid_genome_123",
                output_dir=str(temp_dir)
            )

    @pytest.mark.asyncio
    async def test_fetch_already_exists(self, temp_dir: Path) -> None:
        """Test behavior when genome already downloaded."""
        # First download
        result1 = await fetch_reference_genome(
            genome="hg38",
            output_dir=str(temp_dir)
        )

        # Second download (should detect existing file)
        result2 = await fetch_reference_genome(
            genome="hg38",
            output_dir=str(temp_dir)
        )

        assert result1["path"] == result2["path"]
        assert result2["metadata"]["status"] == "already_exists"

    @pytest.mark.asyncio
    async def test_fetch_all_supported_genomes(self, temp_dir: Path) -> None:
        """Test downloading all supported genomes."""
        supported_genomes = ["hg38", "mm10", "hg19"]

        for genome in supported_genomes:
            result = await fetch_reference_genome(
                genome=genome,
                output_dir=str(temp_dir)
            )

            assert result["metadata"]["genome_id"] == genome
            assert Path(result["path"]).exists()


# ============================================================================
# TOOL TESTS: validate_fastq
# ============================================================================


class TestValidateFastq:
    """Test suite for validate_fastq tool."""

    @pytest.mark.asyncio
    async def test_validate_good_fastq(self, mock_fastq_file: Path) -> None:
        """Test validation of a good quality FASTQ file."""
        result = await validate_fastq(
            fastq_path=str(mock_fastq_file),
            min_quality_score=20
        )

        assert result["valid"] is True
        assert result["total_reads"] > 0
        assert result["avg_quality"] > 20
        assert result["avg_read_length"] > 0
        assert len(result["warnings"]) == 0

    @pytest.mark.asyncio
    async def test_validate_gzipped_fastq(self, mock_fastq_gz_file: Path) -> None:
        """Test validation of gzipped FASTQ file."""
        result = await validate_fastq(
            fastq_path=str(mock_fastq_gz_file),
            min_quality_score=20
        )

        assert result["valid"] is True
        assert result["total_reads"] > 0

    @pytest.mark.asyncio
    async def test_validate_low_quality_fastq(
        self,
        mock_low_quality_fastq: Path,
        monkeypatch
    ) -> None:
        """Test validation of low quality FASTQ file."""
        # Disable dry-run to test actual validation
        monkeypatch.setenv("FGBIO_DRY_RUN", "false")

        result = await validate_fastq(
            fastq_path=str(mock_low_quality_fastq),
            min_quality_score=20
        )

        assert result["valid"] is False
        assert len(result["warnings"]) > 0
        assert "below threshold" in result["warnings"][0]

    @pytest.mark.asyncio
    async def test_validate_missing_file(self) -> None:
        """Test error handling for missing file."""
        with pytest.raises(IOError, match="not found"):
            await validate_fastq(
                fastq_path="/nonexistent/file.fastq",
                min_quality_score=20
            )

    @pytest.mark.asyncio
    async def test_validate_invalid_fastq_format(
        self,
        mock_invalid_fastq: Path,
        monkeypatch
    ) -> None:
        """Test error handling for invalid FASTQ format."""
        # Disable dry-run to test actual validation
        monkeypatch.setenv("FGBIO_DRY_RUN", "false")

        with pytest.raises(ValueError, match="validation failed"):
            await validate_fastq(
                fastq_path=str(mock_invalid_fastq),
                min_quality_score=20
            )

    @pytest.mark.asyncio
    async def test_validate_custom_quality_threshold(
        self,
        mock_fastq_file: Path,
        monkeypatch
    ) -> None:
        """Test validation with custom quality threshold."""
        # Disable dry-run
        monkeypatch.setenv("FGBIO_DRY_RUN", "false")

        result = await validate_fastq(
            fastq_path=str(mock_fastq_file),
            min_quality_score=30
        )

        # Quality scores are 'I' (Phred+33) = 40, so should pass
        assert result["valid"] is True
        assert result["avg_quality"] >= 30


# ============================================================================
# TOOL TESTS: extract_umis
# ============================================================================


class TestExtractUmis:
    """Test suite for extract_umis tool."""

    @pytest.mark.asyncio
    async def test_extract_umis_success(
        self,
        mock_fastq_file: Path,
        temp_dir: Path
    ) -> None:
        """Test successful UMI extraction."""
        result = await extract_umis(
            fastq_path=str(mock_fastq_file),
            output_dir=str(temp_dir),
            umi_length=12
        )

        assert "output_fastq" in result
        assert "umi_count" in result
        assert "reads_processed" in result
        assert result["umi_count"] > 0
        assert result["reads_processed"] > 0

    @pytest.mark.asyncio
    async def test_extract_umis_missing_file(self, temp_dir: Path) -> None:
        """Test error handling for missing input file."""
        with pytest.raises(IOError, match="not found"):
            await extract_umis(
                fastq_path="/nonexistent/file.fastq",
                output_dir=str(temp_dir),
                umi_length=12
            )

    @pytest.mark.asyncio
    async def test_extract_umis_invalid_length(
        self,
        mock_fastq_file: Path,
        temp_dir: Path
    ) -> None:
        """Test error handling for invalid UMI length."""
        with pytest.raises(ValueError, match="out of valid range"):
            await extract_umis(
                fastq_path=str(mock_fastq_file),
                output_dir=str(temp_dir),
                umi_length=100  # Invalid length
            )

    @pytest.mark.asyncio
    async def test_extract_umis_custom_read_structure(
        self,
        mock_fastq_file: Path,
        temp_dir: Path
    ) -> None:
        """Test UMI extraction with custom read structure."""
        result = await extract_umis(
            fastq_path=str(mock_fastq_file),
            output_dir=str(temp_dir),
            umi_length=8,
            read_structure="8M+T"
        )

        assert result["stats"]["umi_length"] == 8
        assert result["stats"]["read_structure"] == "8M+T"

    @pytest.mark.asyncio
    async def test_extract_umis_creates_output_dir(
        self,
        mock_fastq_file: Path,
        temp_dir: Path
    ) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_dir = temp_dir / "nested" / "output"

        result = await extract_umis(
            fastq_path=str(mock_fastq_file),
            output_dir=str(output_dir),
            umi_length=12
        )

        assert output_dir.exists()


# ============================================================================
# TOOL TESTS: query_gene_annotations
# ============================================================================


class TestQueryGeneAnnotations:
    """Test suite for query_gene_annotations tool."""

    @pytest.mark.asyncio
    async def test_query_gene_by_name(self) -> None:
        """Test querying gene annotations by gene name."""
        result = await query_gene_annotations(
            genome="hg38",
            gene_name="TP53"
        )

        assert result["total_genes"] > 0
        assert len(result["annotations"]) > 0
        assert result["annotations"][0]["gene_name"] == "TP53"
        assert result["genome"] == "hg38"

    @pytest.mark.asyncio
    async def test_query_gene_by_chromosome(self) -> None:
        """Test querying gene annotations by chromosome."""
        result = await query_gene_annotations(
            genome="hg38",
            gene_name="BRCA1",
            chromosome="chr17"
        )

        assert result["total_genes"] > 0
        assert result["annotations"][0]["chromosome"] == "chr17"

    @pytest.mark.asyncio
    async def test_query_invalid_genome(self) -> None:
        """Test error handling for invalid genome."""
        with pytest.raises(ValueError, match="Unsupported genome"):
            await query_gene_annotations(
                genome="invalid_genome",
                gene_name="TP53"
            )

    @pytest.mark.asyncio
    async def test_query_invalid_annotation_source(self) -> None:
        """Test error handling for invalid annotation source."""
        with pytest.raises(ValueError, match="Invalid annotation source"):
            await query_gene_annotations(
                genome="hg38",
                gene_name="TP53",
                annotation_source="invalid_source"
            )

    @pytest.mark.asyncio
    async def test_query_different_annotation_sources(self) -> None:
        """Test querying different annotation sources."""
        sources = ["gencode", "ensembl", "refseq"]

        for source in sources:
            result = await query_gene_annotations(
                genome="hg38",
                gene_name="TP53",
                annotation_source=source
            )

            assert result["source"] == source
            assert result["total_genes"] >= 0


# ============================================================================
# INTEGRATION-LIKE TESTS
# ============================================================================


class TestEndToEndWorkflow:
    """Test suite for end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_reference_workflow(self, temp_dir: Path) -> None:
        """Test complete workflow: download genome → validate FASTQ → extract UMIs."""
        # Step 1: Fetch reference genome
        genome_result = await fetch_reference_genome(
            genome="hg38",
            output_dir=str(temp_dir)
        )
        assert genome_result["metadata"]["genome_id"] == "hg38"

        # Step 2: Create a test FASTQ file
        fastq_path = temp_dir / "sample.fastq"
        with open(fastq_path, "w") as f:
            for i in range(100):
                f.write(f"@READ{i:05d}\n")
                f.write("ACGTACGTACGTACGTACGTACGTACGTACGTACGT\n")
                f.write("+\n")
                f.write("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII\n")

        # Step 3: Validate FASTQ
        validation_result = await validate_fastq(
            fastq_path=str(fastq_path),
            min_quality_score=20
        )
        assert validation_result["valid"] is True

        # Step 4: Extract UMIs
        umi_result = await extract_umis(
            fastq_path=str(fastq_path),
            output_dir=str(temp_dir),
            umi_length=12
        )
        assert umi_result["umi_count"] > 0

        # Step 5: Query gene annotations
        annotation_result = await query_gene_annotations(
            genome="hg38",
            gene_name="TP53"
        )
        assert annotation_result["total_genes"] > 0
