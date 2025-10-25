"""Unit tests for mcp-fgbio server resources."""

import json

import pytest

from mcp_fgbio import server

# Get the underlying functions from the decorated resources
# FastMCP 2.11.4+ uses .fn attribute instead of __wrapped__
get_hg38_reference = server.get_hg38_reference.fn
get_mm10_reference = server.get_mm10_reference.fn
get_gencode_annotations = server.get_gencode_annotations.fn


class TestResources:
    """Test suite for MCP resources."""

    def test_hg38_reference_resource(self) -> None:
        """Test hg38 reference resource."""
        result = get_hg38_reference()

        # Parse JSON result
        data = json.loads(result)

        assert data["genome_id"] == "hg38"
        assert data["assembly"] == "GRCh38"
        assert data["organism"] == "Homo sapiens"
        assert data["chromosomes"] == 25
        assert "url" in data
        assert "annotations" in data
        assert "description" in data

    def test_mm10_reference_resource(self) -> None:
        """Test mm10 reference resource."""
        result = get_mm10_reference()

        # Parse JSON result
        data = json.loads(result)

        assert data["genome_id"] == "mm10"
        assert data["assembly"] == "GRCm38"
        assert data["organism"] == "Mus musculus"
        assert data["chromosomes"] == 22
        assert "url" in data
        assert "annotations" in data

    def test_gencode_annotations_resource(self) -> None:
        """Test GENCODE annotations resource."""
        result = get_gencode_annotations()

        # Parse JSON result
        data = json.loads(result)

        assert data["database"] == "GENCODE"
        assert "description" in data
        assert "supported_genomes" in data
        assert "hg38" in data["supported_genomes"]
        assert "mm10" in data["supported_genomes"]
        assert "features" in data
        assert len(data["features"]) > 0
        assert data["format"] == "GTF/GFF3"

    def test_all_resources_return_valid_json(self) -> None:
        """Test that all resources return valid JSON."""
        resources = [
            get_hg38_reference,
            get_mm10_reference,
            get_gencode_annotations,
        ]

        for resource_func in resources:
            result = resource_func()
            # Should not raise exception
            data = json.loads(result)
            assert isinstance(data, dict)
            assert len(data) > 0
