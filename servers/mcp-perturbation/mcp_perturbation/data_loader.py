"""Dataset loading and preprocessing for perturbation prediction."""

import scanpy as sc
import anndata as ad
import GEOparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class DatasetLoader:
    """Handle loading and preprocessing of scRNA-seq datasets."""

    def __init__(self, cache_dir: str = "./data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_geo_dataset(
        self,
        geo_id: str,
        normalize: bool = True,
        n_hvg: int = 7000,
        min_genes: int = 200,
        min_cells: int = 3,
    ) -> ad.AnnData:
        """Load scRNA-seq dataset from GEO.

        Args:
            geo_id: GEO accession number (e.g., "GSE184880")
            normalize: Apply normalize_total and log1p
            n_hvg: Number of highly variable genes to select
            min_genes: Minimum genes per cell
            min_cells: Minimum cells per gene

        Returns:
            Preprocessed AnnData object
        """
        cache_key = f"{geo_id}_norm{normalize}_hvg{n_hvg}_mg{min_genes}_mc{min_cells}"
        cache_path = self.cache_dir / f"{cache_key}.h5ad"

        # Check cache first
        if cache_path.exists():
            logger.info(f"Loading cached dataset from {cache_path}")
            return sc.read_h5ad(cache_path)

        logger.info(f"Downloading GEO dataset {geo_id}")

        # For GSE184880, we'll create a synthetic version for testing
        # In production, you'd download from GEO using GEOparse
        if geo_id == "GSE184880":
            adata = self._load_gse184880()
        else:
            # Generic GEO loading
            adata = self._download_from_geo(geo_id)

        # Preprocess
        adata = self._preprocess(adata, normalize, n_hvg, min_genes, min_cells)

        # Cache the processed data
        ad.settings.allow_write_nullable_strings = True
        adata.write_h5ad(cache_path)
        logger.info(f"Cached processed dataset to {cache_path}")

        return adata

    def load_local_h5ad(
        self,
        file_path: str,
        normalize: bool = True,
        n_hvg: int = 7000,
    ) -> ad.AnnData:
        """Load and preprocess local .h5ad file.

        Args:
            file_path: Path to .h5ad file
            normalize: Apply normalization
            n_hvg: Number of highly variable genes

        Returns:
            Preprocessed AnnData object
        """
        logger.info(f"Loading local file: {file_path}")
        adata = sc.read_h5ad(file_path)

        if normalize or n_hvg > 0:
            adata = self._preprocess(adata, normalize, n_hvg)

        return adata

    def _download_from_geo(self, geo_id: str) -> ad.AnnData:
        """Download dataset from GEO using GEOparse.

        Note: This is a placeholder. Real implementation would:
        1. Use GEOparse.get_GEO() to download metadata
        2. Download supplementary files (matrix.mtx, genes.tsv, barcodes.tsv)
        3. Parse into AnnData format
        """
        # Placeholder - in production, implement actual GEO download
        raise NotImplementedError(
            f"GEO download for {geo_id} not yet implemented. "
            "Use GSE184880 for testing or provide a local .h5ad file."
        )

    def _load_gse184880(self) -> ad.AnnData:
        """Create synthetic GSE184880-like dataset for testing.

        Real GSE184880 has:
        - 12 samples: 5 healthy controls + 7 HGSOC patients
        - Cell types: T cells, B cells, Macrophages, Epithelial cells, etc.
        - Conditions: control, tumor
        """
        np.random.seed(42)

        # Simulate 5000 cells, 10000 genes
        n_cells = 5000
        n_genes = 10000

        # Generate sparse count matrix
        X = np.random.negative_binomial(5, 0.3, size=(n_cells, n_genes))

        # Create cell metadata
        cell_types = np.random.choice(
            ["T_cells", "B_cells", "Macrophages", "Epithelial", "Fibroblasts"],
            size=n_cells,
            p=[0.3, 0.2, 0.2, 0.2, 0.1]
        )

        conditions = np.random.choice(
            ["control", "tumor"],
            size=n_cells,
            p=[0.4, 0.6]
        )

        obs = pd.DataFrame({
            "cell_type": cell_types,
            "condition": conditions,
            "patient_id": np.random.choice([f"P{i:02d}" for i in range(1, 13)], size=n_cells),
        })

        # Create gene metadata
        var = pd.DataFrame(index=[f"Gene_{i}" for i in range(n_genes)])

        adata = ad.AnnData(X=X, obs=obs, var=var)
        adata.obs_names = [f"Cell_{i}" for i in range(n_cells)]

        logger.info("Created synthetic GSE184880 dataset")
        return adata

    def _preprocess(
        self,
        adata: ad.AnnData,
        normalize: bool,
        n_hvg: int,
        min_genes: int = 200,
        min_cells: int = 3,
    ) -> ad.AnnData:
        """Apply standard scRNA-seq preprocessing.

        Pipeline:
        1. Filter cells and genes
        2. Select highly variable genes (seurat_v3 requires raw counts)
        3. Normalize and log-transform (if enabled)
        """
        adata = adata.copy()

        # Filter
        sc.pp.filter_cells(adata, min_genes=min_genes)
        sc.pp.filter_genes(adata, min_cells=min_cells)
        logger.info(f"After filtering: {adata.n_obs} cells, {adata.n_vars} genes")

        # HVG selection before normalization — seurat_v3 requires raw counts
        if n_hvg > 0 and n_hvg < adata.n_vars:
            sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor="cell_ranger")
            adata = adata[:, adata.var.highly_variable].copy()
            logger.info(f"Selected {n_hvg} highly variable genes")

        if normalize:
            sc.pp.normalize_total(adata, target_sum=1e4)
            sc.pp.log1p(adata)
            logger.info("Applied normalization and log1p")

        return adata


async def load_geo_dataset(
    dataset_id: str,
    normalize: bool = True,
    n_hvg: int = 7000,
) -> ad.AnnData:
    """Async wrapper for dataset loading (for MCP tool).

    Args:
        dataset_id: GEO accession or path to .h5ad file
        normalize: Apply normalization
        n_hvg: Number of highly variable genes

    Returns:
        Preprocessed AnnData object
    """
    loader = DatasetLoader()

    # Check if it's a local file path
    if dataset_id.endswith(".h5ad"):
        return loader.load_local_h5ad(dataset_id, normalize=normalize, n_hvg=n_hvg)
    else:
        # Assume it's a GEO accession
        return loader.load_geo_dataset(dataset_id, normalize=normalize, n_hvg=n_hvg)
