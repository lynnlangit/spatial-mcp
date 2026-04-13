"""Tests for dataset loading functionality."""

import pytest
import pytest_asyncio
from mcp_perturbation.data_loader import DatasetLoader, load_geo_dataset


class TestDatasetLoader:
    """Test DatasetLoader class."""

    def test_load_gse184880_synthetic(self):
        """Test loading synthetic GSE184880 dataset."""
        loader = DatasetLoader()
        adata = loader.load_geo_dataset("GSE184880", normalize=True, n_hvg=2000)

        assert adata.n_obs > 0, "Should have cells"
        assert adata.n_vars > 0, "Should have genes"
        assert "cell_type" in adata.obs.columns, "Should have cell_type annotation"
        assert "condition" in adata.obs.columns, "Should have condition annotation"

    def test_preprocessing_parameters(self):
        """Test preprocessing with different parameters."""
        loader = DatasetLoader()

        # With normalization
        adata_norm = loader.load_geo_dataset(
            "GSE184880",
            normalize=True,
            n_hvg=1000
        )
        assert adata_norm.n_vars <= 1000, "Should have selected HVGs"

        # Without normalization
        adata_raw = loader.load_geo_dataset(
            "GSE184880",
            normalize=False,
            n_hvg=0
        )
        assert adata_raw.n_vars > 1000, "Should keep all genes when n_hvg=0"

    def test_cell_type_distribution(self):
        """Test that synthetic data has expected cell types."""
        loader = DatasetLoader()
        adata = loader.load_geo_dataset("GSE184880")

        cell_types = adata.obs["cell_type"].unique()
        assert len(cell_types) > 0, "Should have cell types"

        # Check expected cell types from synthetic data
        expected_types = {"T_cells", "B_cells", "Macrophages", "Epithelial", "Fibroblasts"}
        assert set(cell_types).issubset(expected_types), "Should have expected cell types"

    def test_condition_distribution(self):
        """Test that synthetic data has GEARS-format perturbation conditions."""
        loader = DatasetLoader()
        adata = loader.load_geo_dataset("GSE184880")

        conditions = set(adata.obs["condition"].unique())
        assert "ctrl" in conditions, "Should have ctrl condition"
        # At least one gene+ctrl perturbation condition
        pert_conds = [c for c in conditions if c != "ctrl" and "+ctrl" in c]
        assert len(pert_conds) >= 5, f"Should have gene perturbations, got {pert_conds}"


@pytest.mark.asyncio
async def test_async_load_geo_dataset():
    """Test async wrapper for dataset loading."""
    adata = await load_geo_dataset("GSE184880", normalize=True, n_hvg=2000)

    assert adata.n_obs > 0
    assert adata.n_vars <= 2000
    assert "cell_type" in adata.obs.columns


@pytest.mark.asyncio
async def test_load_nonexistent_geo():
    """Test loading non-existent GEO dataset."""
    with pytest.raises(NotImplementedError):
        await load_geo_dataset("GSE999999", normalize=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
