"""High-level prediction workflows for perturbation analysis."""

import scanpy as sc
import anndata as ad
try:
    ad.settings.allow_write_nullable_strings = True
except AttributeError:
    pass  # older anndata versions don't need this setting
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class DifferentialExpressionAnalyzer:
    """Analyze differential expression between baseline and predicted cells."""

    @staticmethod
    def compute_differential_expression(
        baseline_adata: ad.AnnData,
        predicted_adata: ad.AnnData,
        n_top_genes: int = 50,
        method: str = "wilcoxon"
    ) -> Dict[str, any]:
        """Compute differential expression analysis.

        Args:
            baseline_adata: Baseline cell states
            predicted_adata: Predicted cell states
            n_top_genes: Number of top genes to return
            method: Statistical test method ("wilcoxon" or "t-test")

        Returns:
            Dictionary with DE results
        """
        # Combine into single object for DE testing
        baseline_adata.obs["condition"] = "baseline"
        predicted_adata.obs["condition"] = "predicted"

        combined = ad.concat([baseline_adata, predicted_adata], label="source")

        # Run differential expression
        sc.tl.rank_genes_groups(
            combined,
            groupby="condition",
            reference="baseline",
            method=method,
            n_genes=n_top_genes
        )

        # Extract results
        de_results = sc.get.rank_genes_groups_df(combined, group="predicted")

        # Compute fold changes
        baseline_mean = baseline_adata.X.mean(axis=0).A1 if hasattr(baseline_adata.X, 'A1') else baseline_adata.X.mean(axis=0)
        predicted_mean = predicted_adata.X.mean(axis=0).A1 if hasattr(predicted_adata.X, 'A1') else predicted_adata.X.mean(axis=0)

        # Avoid log(0)
        baseline_mean = np.maximum(baseline_mean, 1e-10)
        predicted_mean = np.maximum(predicted_mean, 1e-10)

        log_fc = np.log2(predicted_mean / baseline_mean)

        # Get top upregulated
        top_up_idx = np.argsort(log_fc)[-n_top_genes:][::-1]
        upregulated = [
            {
                "gene": baseline_adata.var_names[i],
                "log2_fc": float(log_fc[i]),
                "baseline_mean": float(baseline_mean[i]),
                "predicted_mean": float(predicted_mean[i])
            }
            for i in top_up_idx if log_fc[i] > 0
        ]

        # Get top downregulated
        top_down_idx = np.argsort(log_fc)[:n_top_genes]
        downregulated = [
            {
                "gene": baseline_adata.var_names[i],
                "log2_fc": float(log_fc[i]),
                "baseline_mean": float(baseline_mean[i]),
                "predicted_mean": float(predicted_mean[i])
            }
            for i in top_down_idx if log_fc[i] < 0
        ]

        return {
            "upregulated_genes": upregulated[:n_top_genes],
            "downregulated_genes": downregulated[:n_top_genes],
            "n_significant_up": len([g for g in upregulated if abs(g["log2_fc"]) > 1]),
            "n_significant_down": len([g for g in downregulated if abs(g["log2_fc"]) > 1]),
            "method": method
        }


class PerturbationPredictor:
    """High-level workflow for perturbation predictions."""

    def __init__(self, output_dir: str = "./data/predictions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def apply_perturbation_to_patient(
        self,
        wrapper,  # trained model wrapper (e.g., GEARSWrapper)
        patient_adata: ad.AnnData,
        ctrl_key: str,
        stim_key: str,
        celltype_to_predict: str,
        output_name: Optional[str] = None
    ) -> Dict[str, any]:
        """Apply learned perturbation to patient data.

        Args:
            wrapper: Trained model wrapper (e.g., GEARSWrapper)
            patient_adata: Patient's baseline scRNA-seq data
            ctrl_key: Control condition label
            stim_key: Treatment condition label
            celltype_to_predict: Cell type to predict
            output_name: Optional name for output files

        Returns:
            Dictionary with prediction results and file paths
        """
        logger.info(f"Predicting {celltype_to_predict} response for patient")

        # Generate predictions
        predicted_adata, delta = wrapper.predict(
            ctrl_key=ctrl_key,
            stim_key=stim_key,
            celltype_to_predict=celltype_to_predict
        )

        # Save predicted data
        if output_name is None:
            output_name = f"{celltype_to_predict}_predicted"

        output_path = self.output_dir / f"{output_name}.h5ad"
        predicted_adata.write_h5ad(output_path)

        # Compute delta statistics
        delta_stats = wrapper.compute_delta(
            ctrl_key=ctrl_key,
            stim_key=stim_key,
            cell_type=celltype_to_predict
        )

        # Get top changed genes
        baseline_cells = patient_adata[
            patient_adata.obs["cell_type"] == celltype_to_predict
        ]

        if baseline_cells.n_obs > 0:
            de_results = self._analyze_predictions(
                baseline_cells,
                predicted_adata,
                n_top_genes=20
            )
        else:
            de_results = None

        return {
            "status": "success",
            "output_path": str(output_path),
            "n_cells_predicted": predicted_adata.n_obs,
            "cell_type": celltype_to_predict,
            "delta_norm": delta_stats["delta_norm"],
            "differential_expression": de_results
        }

    def _analyze_predictions(
        self,
        baseline: ad.AnnData,
        predicted: ad.AnnData,
        n_top_genes: int = 20
    ) -> Dict[str, any]:
        """Analyze prediction results."""
        analyzer = DifferentialExpressionAnalyzer()

        try:
            de_results = analyzer.compute_differential_expression(
                baseline,
                predicted,
                n_top_genes=n_top_genes
            )
            return de_results
        except Exception as e:
            logger.warning(f"DE analysis failed: {e}")
            return None

    def batch_predict_cell_types(
        self,
        wrapper,
        patient_adata: ad.AnnData,
        cell_types: List[str],
        ctrl_key: str,
        stim_key: str
    ) -> List[Dict[str, any]]:
        """Predict multiple cell types in batch.

        Args:
            wrapper: Trained model wrapper
            patient_adata: Patient data
            cell_types: List of cell types to predict
            ctrl_key: Control condition label
            stim_key: Treatment condition label

        Returns:
            List of prediction results for each cell type
        """
        results = []

        for cell_type in cell_types:
            try:
                result = self.apply_perturbation_to_patient(
                    wrapper=wrapper,
                    patient_adata=patient_adata,
                    ctrl_key=ctrl_key,
                    stim_key=stim_key,
                    celltype_to_predict=cell_type,
                    output_name=f"patient_{cell_type}"
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to predict {cell_type}: {e}")
                results.append({
                    "status": "error",
                    "cell_type": cell_type,
                    "error": str(e)
                })

        return results


def get_top_changed_genes(
    baseline_adata: ad.AnnData,
    predicted_adata: ad.AnnData,
    n_genes: int = 10
) -> Tuple[List[str], List[str]]:
    """Get top upregulated and downregulated genes.

    Args:
        baseline_adata: Baseline cells
        predicted_adata: Predicted cells
        n_genes: Number of genes to return

    Returns:
        Tuple of (upregulated_genes, downregulated_genes)
    """
    baseline_mean = baseline_adata.X.mean(axis=0)
    predicted_mean = predicted_adata.X.mean(axis=0)

    if hasattr(baseline_mean, 'A1'):
        baseline_mean = baseline_mean.A1
        predicted_mean = predicted_mean.A1

    # Compute fold change
    diff = predicted_mean - baseline_mean

    # Top upregulated
    top_up_idx = np.argsort(diff)[-n_genes:][::-1]
    upregulated = [baseline_adata.var_names[i] for i in top_up_idx]

    # Top downregulated
    top_down_idx = np.argsort(diff)[:n_genes]
    downregulated = [baseline_adata.var_names[i] for i in top_down_idx]

    return upregulated, downregulated
