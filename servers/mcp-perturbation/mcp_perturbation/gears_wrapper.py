"""Wrapper for GEARS model operations."""

import scanpy as sc
import anndata as ad
try:
    ad.settings.allow_write_nullable_strings = True
except AttributeError:
    pass  # older anndata versions don't need this setting
import numpy as np
import torch
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import logging

try:
    from gears import PertData, GEARS
except ImportError:
    raise ImportError(
        "GEARS not installed. Install with: pip install cell-gears torch-geometric"
    )

logger = logging.getLogger(__name__)

# Labels that GEARS treats as "no perturbation" (control)
_CONTROL_LABELS = frozenset({"control", "ctrl", "normal", "baseline", "unperturbed"})


def _is_gears_format(condition: str) -> bool:
    """Check if a condition label is already in GEARS format.

    GEARS format examples: "ctrl", "NNMT+ctrl", "STAT3+NNMT"
    Non-GEARS format: "tumor", "treated", "control"
    """
    if condition == "ctrl":
        return True
    # GEARS perturbation labels always contain '+'
    return "+" in condition


def _ensure_gears_conditions(adata: ad.AnnData, ctrl_key: str = "control") -> ad.AnnData:
    """Convert phenotype labels to GEARS perturbation format if needed.

    GEARS' prepare_split() expects condition labels like "ctrl",
    "GENE+ctrl", "GENE1+GENE2". Phenotype labels such as "tumor",
    "treated", "control" cause an IndexError inside the split logic.

    Args:
        adata: AnnData with obs['condition'] column.
        ctrl_key: Original control label (e.g. "control").

    Returns:
        AnnData with GEARS-compatible condition labels.
    """
    conditions = adata.obs["condition"].unique().tolist()

    # Check if already in GEARS format
    if all(_is_gears_format(str(c)) for c in conditions):
        return adata

    # Build mapping: control labels → "ctrl", everything else → "LABEL+ctrl"
    mapping = {}
    for c in conditions:
        if str(c).lower() in _CONTROL_LABELS:
            mapping[c] = "ctrl"
        else:
            mapping[c] = f"{c}+ctrl"

    logger.info(
        "Remapping condition labels to GEARS format: %s",
        {k: v for k, v in mapping.items() if k != v},
    )
    adata.obs["condition"] = adata.obs["condition"].map(mapping)
    return adata


@dataclass
class PredictionResult:
    """Results from perturbation prediction."""
    predicted_adata: ad.AnnData
    perturbation_effect: np.ndarray
    output_path: str


class GearsWrapper:
    """Manages GEARS model lifecycle and predictions.

    GEARS (Graph-Enhanced Gene Activation and Repression Simulator) uses
    graph neural networks with gene-gene relationship knowledge graphs to
    predict transcriptional responses to perturbations.

    Key differences from scGen:
    - Uses GNN architecture instead of VAE
    - Integrates biological knowledge graphs
    - Better performance on multi-gene perturbations
    - Published Nature Biotechnology 2024
    """

    def __init__(
        self,
        model_dir: str = "./data/models",
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """Initialize wrapper.

        Args:
            model_dir: Directory to save/load models
            device: 'cuda' or 'cpu'
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        self.model: Optional[GEARS] = None
        self.pert_data: Optional[PertData] = None
        self.adata: Optional[ad.AnnData] = None
        self.model_name: Optional[str] = None

        logger.info(f"Initialized GEARS wrapper on device: {device}")

    def setup(
        self,
        adata: ad.AnnData,
        condition_key: str = "condition",
        ctrl_key: str = "control",
        pert_key: str = "perturbation",
        split: str = "simulation",
        split_seed: int = 1
    ) -> None:
        """Configure AnnData for GEARS.

        Args:
            adata: Annotated data matrix
            condition_key: Column in adata.obs with condition labels
            ctrl_key: Label for control condition
            pert_key: Column in adata.obs with perturbation labels (gene names)
            split: Data split strategy ('simulation', 'combo_seen0', etc.)
            split_seed: Random seed for splitting
        """
        self.adata = adata.copy()

        # Verify required keys exist
        if condition_key not in adata.obs.columns:
            raise ValueError(f"condition_key '{condition_key}' not found in adata.obs")
        if pert_key not in adata.obs.columns:
            # If no perturbation column, create from condition
            logger.warning(f"pert_key '{pert_key}' not found, using condition_key")
            self.adata.obs[pert_key] = self.adata.obs[condition_key]

        # Ensure AnnData has the columns GEARS expects:
        #   obs: 'condition' (with 'ctrl' for controls), 'cell_type'
        #   var: 'gene_name'
        if condition_key != "condition":
            self.adata.obs["condition"] = self.adata.obs[condition_key]
        if "cell_type" not in self.adata.obs.columns:
            self.adata.obs["cell_type"] = "unknown"
        if "gene_name" not in self.adata.var.columns:
            self.adata.var["gene_name"] = self.adata.var_names

        # GEARS expects perturbation-style condition labels:
        #   control cells → "ctrl"
        #   single perturbation → "GENE+ctrl"
        #   combo perturbation  → "GENE1+GENE2"
        # Phenotype labels like "tumor", "treated" must be remapped.
        self.adata = _ensure_gears_conditions(self.adata, ctrl_key)

        # GEARS expects sparse X (calls X.toarray() internally)
        import scipy.sparse as sp
        if not sp.issparse(self.adata.X):
            self.adata.X = sp.csr_matrix(self.adata.X)

        # Clear stale GEARS artifacts from previous runs so cached splits
        # or PyG objects from a different dataset don't get reloaded.
        import shutil
        stale_dir = self.model_dir / "custom_pert"
        if stale_dir.exists():
            shutil.rmtree(stale_dir, ignore_errors=True)

        # Use GEARS' own new_data_process to build the PertData object.
        # This computes DE genes, creates PyG graph objects, and saves
        # perturb_processed.h5ad — everything that load() would expect.
        self.pert_data = PertData(str(self.model_dir))
        self.pert_data.new_data_process(
            dataset_name="custom_pert",
            adata=self.adata,
        )

        # Store split params — dataloaders are built in _ensure_dataloader()
        # which is called by initialize_model() before GEARS needs them.
        self._split = split
        self._split_seed = split_seed

        logger.info(
            f"Setup AnnData with condition_key={condition_key}, "
            f"ctrl_key={ctrl_key}, pert_key={pert_key}"
        )

    def setup_from_dataset(
        self,
        data_name: str = "norman",
        split: str = "simulation",
        split_seed: int = 1
    ) -> None:
        """Load pre-configured GEARS dataset.

        Args:
            data_name: Dataset name ('norman', 'adamson', 'dixit', etc.)
            split: Data split strategy
            split_seed: Random seed for splitting
        """
        self.pert_data = PertData(str(self.model_dir))
        self.pert_data.load(data_name=data_name)
        self.pert_data.prepare_split(split=split, seed=split_seed)
        self.pert_data.get_dataloader(batch_size=32, test_batch_size=128)
        self.adata = self.pert_data.adata

        logger.info(f"Loaded GEARS dataset: {data_name}")

    def _ensure_dataloader(self, batch_size: int = 32) -> None:
        """Prepare data split and build dataloaders if not already done.

        GEARS model initialization requires pert_data.dataloader to exist.
        This is called automatically by initialize_model().
        """
        if hasattr(self.pert_data, "dataloader") and self.pert_data.dataloader:
            return

        split = getattr(self, "_split", "simulation")
        seed = getattr(self, "_split_seed", 1)

        # 'simulation' split requires many distinct perturbation conditions
        # to populate train/val/test sets.  Fall back to 'no_test' for
        # datasets with fewer than 10 non-ctrl perturbations.
        if split == "simulation" and hasattr(self.pert_data, "adata"):
            conditions = self.pert_data.adata.obs["condition"].unique()
            n_perts = sum(1 for c in conditions if c != "ctrl")
            if n_perts < 10:
                logger.info(
                    "Only %d perturbation conditions — using split='no_test' "
                    "instead of 'simulation'",
                    n_perts,
                )
                split = "no_test"

        # GEARS may call .nonzero() on adata.X during prepare_split;
        # sparse matrices work, but if new_data_process stored a pandas
        # object we need to ensure it's a numpy array.
        if hasattr(self.pert_data, "adata") and self.pert_data.adata is not None:
            _x = self.pert_data.adata.X
            if hasattr(_x, "toarray"):
                self.pert_data.adata.X = _x.toarray()
            elif not isinstance(_x, np.ndarray):
                self.pert_data.adata.X = np.array(_x)

        try:
            self.pert_data.prepare_split(split=split, seed=seed)
            self.pert_data.get_dataloader(
                batch_size=batch_size,
                test_batch_size=min(128, batch_size * 4),
            )
        except (IndexError, KeyError) as exc:
            conditions = (
                self.pert_data.adata.obs["condition"].unique().tolist()
                if hasattr(self.pert_data, "adata") and self.pert_data.adata is not None
                else "N/A"
            )
            raise RuntimeError(
                f"GEARS prepare_split/get_dataloader failed (split={split!r}). "
                f"Condition labels: {conditions!r}. "
                f"Original error: {exc}"
            ) from exc

    def initialize_model(
        self,
        hidden_size: int = 64,
        num_layers: int = 1,
        uncertainty: bool = False,
        uncertainty_reg: float = 1.0
    ) -> Dict[str, any]:
        """Create GEARS model instance.

        Args:
            hidden_size: Hidden layer dimension
            num_layers: Number of GNN layers (applied to both GO and gene graphs)
            uncertainty: Enable uncertainty quantification
            uncertainty_reg: Uncertainty regularization weight

        Returns:
            Model configuration summary
        """
        if self.pert_data is None:
            raise ValueError("Call setup() or setup_from_dataset() before initializing model")

        self._ensure_dataloader()
        self.model = GEARS(self.pert_data, device=self.device)
        self.model.model_initialize(
            hidden_size=hidden_size,
            num_go_gnn_layers=num_layers,
            num_gene_gnn_layers=num_layers,
            uncertainty=uncertainty,
            uncertainty_reg=uncertainty_reg,
        )

        config = {
            "hidden_size": hidden_size,
            "num_layers": num_layers,
            "uncertainty": uncertainty,
            "n_genes": self.adata.n_vars if self.adata else self.pert_data.adata.n_vars,
            "n_cells": self.adata.n_obs if self.adata else self.pert_data.adata.n_obs,
            "device": self.device
        }

        logger.info(f"Initialized GEARS model: {config}")
        return config

    def train(
        self,
        epochs: int = 20,
        lr: float = 1e-3,
        batch_size: int = 32,
        valid_every: int = 1
    ) -> Dict[str, any]:
        """Train the GEARS model.

        Args:
            epochs: Number of training epochs
            lr: Learning rate
            batch_size: Batch size for training
            valid_every: Validate every N epochs

        Returns:
            Training metrics
        """
        if self.model is None:
            raise ValueError("Call initialize_model() before training")

        logger.info(f"Training GEARS for {epochs} epochs")

        # GEARS training
        self.model.train(
            epochs=epochs,
            lr=lr,
            batch_size=batch_size,
            valid_every=valid_every
        )

        # Get training history
        history = self.model.history if hasattr(self.model, 'history') else {}

        metrics = {
            "epochs_completed": epochs,
            "learning_rate": lr,
            "batch_size": batch_size,
            "final_metrics": history.get('test', {}) if history else {}
        }

        logger.info(f"Training complete: {metrics}")
        return metrics

    def save(self, name: str) -> str:
        """Save model to disk.

        Args:
            name: Model name (without extension)

        Returns:
            Path to saved model
        """
        if self.model is None:
            raise ValueError("No model to save")

        save_path = self.model_dir / f"{name}.pt"

        # Save GEARS model
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': {
                'hidden_size': self.model.hidden_size if hasattr(self.model, 'hidden_size') else 64,
                'num_layers': getattr(self.model, 'num_layers', 2)
            }
        }, save_path)

        self.model_name = name
        logger.info(f"Saved model to {save_path}")
        return str(save_path)

    def load(self, name: str) -> None:
        """Load model from disk.

        Args:
            name: Model name (without extension)
        """
        load_path = self.model_dir / f"{name}.pt"

        if not load_path.exists():
            raise FileNotFoundError(f"Model not found: {load_path}")

        if self.model is None:
            raise ValueError("Initialize model before loading weights")

        checkpoint = torch.load(load_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model_name = name

        logger.info(f"Loaded model from {load_path}")

    def predict(
        self,
        perturbations: List[str],
        cell_type: Optional[str] = None,
        return_anndata: bool = True
    ) -> Tuple[ad.AnnData, np.ndarray]:
        """Generate perturbation prediction.

        Args:
            perturbations: List of gene names to perturb (e.g., ['CD4', 'CD8A'])
            cell_type: Optional cell type to filter predictions
            return_anndata: Return results as AnnData object

        Returns:
            Tuple of (predicted_adata, perturbation_effect)
        """
        if self.model is None:
            raise ValueError("No trained model available")

        logger.info(f"Predicting response to perturbations: {perturbations}")

        # GEARS prediction
        predictions = self.model.predict(perturbations)

        # Convert to numpy array
        if isinstance(predictions, torch.Tensor):
            pred_array = predictions.cpu().detach().numpy()
        else:
            pred_array = np.array(predictions)

        # Create AnnData object with predictions
        if return_anndata:
            base_adata = self.adata if self.adata is not None else self.pert_data.adata

            # Filter by cell type if specified
            if cell_type is not None:
                if 'cell_type' in base_adata.obs:
                    mask = base_adata.obs['cell_type'] == cell_type
                    base_adata = base_adata[mask].copy()

            # Create predicted AnnData
            predicted_adata = ad.AnnData(
                X=pred_array,
                obs=base_adata.obs.copy() if len(pred_array) == base_adata.n_obs else None,
                var=base_adata.var.copy()
            )
            predicted_adata.obs['perturbation'] = ','.join(perturbations)
        else:
            predicted_adata = None

        # Compute perturbation effect (difference from control)
        if self.adata is not None and 'condition' in self.adata.obs:
            ctrl_mask = self.adata.obs['condition'] == 'control'
            if ctrl_mask.sum() > 0:
                ctrl_mean = self.adata[ctrl_mask].X.mean(axis=0)
                if isinstance(ctrl_mean, np.matrix):
                    ctrl_mean = np.array(ctrl_mean).flatten()
                pert_effect = pred_array.mean(axis=0) - ctrl_mean
            else:
                pert_effect = pred_array.mean(axis=0)
        else:
            pert_effect = pred_array.mean(axis=0)

        logger.info(
            f"Prediction complete. "
            f"Effect magnitude: {np.linalg.norm(pert_effect):.4f}"
        )

        return predicted_adata, pert_effect

    def predict_perturbation_response(
        self,
        ctrl_key: str,
        stim_key: str,
        celltype_to_predict: Optional[str] = None
    ) -> Tuple[ad.AnnData, np.ndarray]:
        """Predict perturbation response (scGen-compatible interface).

        Args:
            ctrl_key: Control condition label
            stim_key: Perturbation/treatment label (gene name or treatment)
            celltype_to_predict: Optional cell type to predict for

        Returns:
            Tuple of (predicted_adata, perturbation_effect)
        """
        # Convert stim_key to list of genes if it's a gene name
        perturbations = [stim_key] if isinstance(stim_key, str) else stim_key

        return self.predict(
            perturbations=perturbations,
            cell_type=celltype_to_predict,
            return_anndata=True
        )

    def get_perturbation_effect(
        self,
        perturbations: List[str]
    ) -> Dict[str, any]:
        """Compute perturbation effect statistics.

        Args:
            perturbations: List of genes to perturb

        Returns:
            Dictionary with effect statistics
        """
        if self.model is None:
            raise ValueError("Model not trained")

        _, effect = self.predict(perturbations, return_anndata=False)

        result = {
            "perturbations": perturbations,
            "effect_norm": float(np.linalg.norm(effect)),
            "effect_mean": float(effect.mean()),
            "effect_std": float(effect.std()),
            "top_affected_genes": self._get_top_affected_genes(effect, top_n=10)
        }

        logger.info(f"Computed perturbation effect: {result}")
        return result

    def _get_top_affected_genes(
        self,
        effect: np.ndarray,
        top_n: int = 10
    ) -> List[Dict[str, any]]:
        """Get top affected genes by perturbation effect.

        Args:
            effect: Perturbation effect vector
            top_n: Number of top genes to return

        Returns:
            List of dicts with gene names and effect sizes
        """
        if self.adata is None:
            return []

        # Get absolute effect sizes
        abs_effect = np.abs(effect)
        top_indices = np.argsort(abs_effect)[-top_n:][::-1]

        genes = []
        for idx in top_indices:
            genes.append({
                "gene": self.adata.var_names[idx],
                "effect": float(effect[idx]),
                "abs_effect": float(abs_effect[idx])
            })

        return genes
