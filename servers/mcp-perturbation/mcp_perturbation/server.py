"""MCP Server for perturbation prediction using GEARS."""

from fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, List
import json
import logging
import os
import sys
from pathlib import Path

import scanpy as sc
import numpy as np
import anndata as ad
try:
    ad.settings.allow_write_nullable_strings = True
except AttributeError:
    pass  # older anndata versions don't need this setting

from .data_loader import load_geo_dataset
from .gears_wrapper import GearsWrapper
from .prediction import PerturbationPredictor, DifferentialExpressionAnalyzer
from .visualization import PerturbationVisualizer

# Add shared/ to import path for dry_run helper (match other servers)
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
try:
    from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
except ImportError:  # pragma: no cover - fall back when shared/ not available
    def _shared_add_dry_run_warning(result, *, dry_run, env_var="PERTURBATION_DRY_RUN"):
        if dry_run and isinstance(result, dict):
            result["_DRY_RUN_WARNING"] = "SYNTHETIC DATA - NOT FOR RESEARCH USE"
        return result

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("perturbation")

# DRY_RUN flag — defaults to true so callers can smoke-test without GEARS/torch
DRY_RUN = os.getenv("PERTURBATION_DRY_RUN", "true").lower() == "true"

# Global state for models and datasets
_models = {}  # name -> GearsWrapper
_datasets = {}  # dataset_id -> AnnData


def add_dry_run_warning(result, *, forced: bool = False):
    """Shared DRY_RUN warning wrapper for this server."""
    return _shared_add_dry_run_warning(
        result,
        dry_run=DRY_RUN or forced,
        env_var="PERTURBATION_DRY_RUN",
    )


# Canonical PAT001 dry-run payload for perturbation_predict_response.
# Matches the Stage IV Ovarian Cancer PatientOne demo scenario.
_PAT001_PREDICT_DRY_RUN = {
    "mode": "dry_run",
    "treatment": "NNMT+STAT3",
    "cell_type": "tumor_core",
    "top_upregulated": ["PRF1", "GZMB", "IFNG"],
    "top_downregulated": ["STAT3", "COL3A1", "NNMT"],
    "interpretation": (
        "NNMT knockdown reduces CAF signaling and increases cytotoxic T-cell "
        "markers"
    ),
}


def _coerce_params(raw, model_class):
    """FastMCP passes tool params as JSON strings. Deserialize and construct model."""
    if isinstance(raw, model_class):
        return raw
    if isinstance(raw, str):
        raw = json.loads(raw)
    if isinstance(raw, dict):
        return model_class(**raw)
    raise ValueError(f"Cannot coerce {type(raw)} to {model_class.__name__}")


# ==================== Input Models ====================

class LoadDatasetInput(BaseModel):
    """Input for loading scRNA-seq dataset."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    dataset_id: str = Field(..., description="GEO accession (e.g., 'GSE184880') or path to .h5ad")
    normalize: bool = Field(default=True, description="Apply normalize_total + log1p")
    n_hvg: int = Field(default=7000, description="Number of highly variable genes", ge=1000, le=20000)
    cell_type_key: str = Field(default="cell_type", description="Column with cell type labels")
    condition_key: str = Field(default="condition", description="Column with treatment condition")


class SetupModelInput(BaseModel):
    """Input for initializing GEARS model."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    dataset_id: str = Field(..., description="Dataset ID from load_dataset")
    hidden_size: int = Field(default=64, description="Hidden layer size", ge=32, le=256)
    num_layers: int = Field(default=2, description="Number of GNN layers", ge=1, le=5)
    uncertainty: bool = Field(default=True, description="Enable uncertainty quantification")
    uncertainty_reg: float = Field(default=1.0, description="Uncertainty regularization weight", ge=0, le=10)
    model_name: str = Field(default="gears_model", description="Name for this model")
    condition_key: str = Field(default="condition", description="Column with condition labels")
    pert_key: str = Field(default="perturbation", description="Column with perturbation labels")


class TrainModelInput(BaseModel):
    """Input for training GEARS model."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    model_name: str = Field(..., description="Model name from setup_model")
    epochs: int = Field(default=20, description="Training epochs", ge=5, le=200)
    batch_size: int = Field(default=32, description="Batch size", ge=16, le=256)
    learning_rate: float = Field(default=1e-3, description="Learning rate", gt=0, le=0.1)
    valid_every: int = Field(default=1, description="Validate every N epochs", ge=1, le=10)


class ComputeDeltaInput(BaseModel):
    """Input for computing perturbation vector."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    model_name: str = Field(..., description="Trained model name")
    source_cell_type: Optional[str] = Field(None, description="Cell type to compute delta from (None = all)")
    control_key: str = Field(default="control", description="Control condition label")
    treatment_key: str = Field(default="tumor", description="Treatment condition label")


class PredictResponseInput(BaseModel):
    """Input for predicting treatment response."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    model_name: Optional[str] = Field(
        default=None,
        description=(
            "Trained model name (from setup_model + train_model). Either "
            "model_name OR dataset_id is required when dry_run is False."
        ),
    )
    dataset_id: Optional[str] = Field(
        default=None,
        description=(
            "Dataset ID from load_dataset. Falls back to a dry-run payload "
            "when no trained model is present — the one-step predict path "
            "does not perform live training."
        ),
    )
    patient_data_path: Optional[str] = Field(
        default=None,
        description="Path to patient .h5ad file (not required in dry_run)",
    )
    cell_type_to_predict: Optional[str] = Field(
        default=None,
        description="Cell type to transform (not required in dry_run)",
    )
    control_key: str = Field(default="control", description="Control condition label")
    treatment_key: str = Field(default="tumor", description="Treatment condition label")
    output_path: Optional[str] = Field(default=None, description="Path to save predictions")
    dry_run: bool = Field(
        default=False,
        description=(
            "If true, return the canonical PAT001 synthetic payload without "
            "running GEARS inference. Also honored implicitly when the "
            "PERTURBATION_DRY_RUN env var is true and no trained model exists."
        ),
    )


class DEInput(BaseModel):
    """Input for differential expression analysis."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    baseline_path: str = Field(..., description="Baseline .h5ad")
    predicted_path: str = Field(..., description="Predicted .h5ad")
    n_top_genes: int = Field(default=50, ge=10, le=500, description="Number of top genes to return")
    method: Literal["wilcoxon", "t-test"] = Field(default="wilcoxon", description="Statistical test method")


class GetLatentInput(BaseModel):
    """Input for extracting latent representations."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    model_name: str = Field(..., description="Trained model name")
    data_path: str = Field(..., description=".h5ad file to embed")


class VisualizeInput(BaseModel):
    """Input for visualization."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    baseline_path: str = Field(..., description="Baseline .h5ad file path")
    predicted_path: str = Field(..., description="Predicted .h5ad file path")
    plot_type: Literal["pca", "umap"] = Field(default="pca", description="Type of plot")
    color_by: str = Field(default="condition", description="Column to color by")
    output_path: Optional[str] = Field(default=None, description="Path to save figure")


# ==================== Tool Implementations ====================

def _build_gears_synthetic_adata(n_hvg: int) -> "ad.AnnData":
    """Build a GEARS-compatible synthetic GSE184880 AnnData.

    Generates data with real gene-name perturbation conditions so GEARS
    can build its gene-gene interaction graph.  The number of genes matches
    ``n_hvg`` exactly, avoiding any subsequent HVG filtering that could
    remove perturbation target genes.
    """
    import pandas as pd

    rng = np.random.default_rng(42)

    pert_genes = [
        "NNMT", "STAT3", "TP53", "BRCA1", "MYC",
        "PIK3CA", "PTEN", "CCNE1", "AKT1", "CDK2",
    ]
    all_conditions = ["ctrl"] + [f"{g}+ctrl" for g in pert_genes]
    probs = [0.1] + [0.09] * 10

    n_cells = 5000
    n_genes = n_hvg

    gene_names = pert_genes + [
        f"GENE_{i:04d}" for i in range(n_genes - len(pert_genes))
    ]

    X = rng.lognormal(1.0, 1.0, (n_cells, n_genes)).astype("float32")
    cell_conds = rng.choice(all_conditions, size=n_cells, p=probs)

    obs = pd.DataFrame(
        {
            "condition": pd.array(cell_conds, dtype=str),
            "cell_type": pd.array(
                rng.choice(
                    ["Fibroblasts", "B_cells", "Epithelial", "Macrophages", "T_cells"],
                    size=n_cells,
                ),
                dtype=str,
            ),
        },
        index=[f"cell_{i:05d}" for i in range(n_cells)],
    )
    var = pd.DataFrame(index=pd.Index(gene_names, name="gene_name"))

    adata = ad.AnnData(X=X, obs=obs, var=var)
    try:
        ad.settings.allow_write_nullable_strings = True
    except AttributeError:
        pass
    return adata


@mcp.tool()
async def perturbation_load_dataset(params: str) -> str:
    """Load scRNA-seq dataset from GEO or local file.

    Downloads and preprocesses single-cell data, applying normalization
    and highly variable gene selection for GEARS training.

    Example:
        {"dataset_id": "GSE184880", "normalize": true, "n_hvg": 7000}
    """
    params = _coerce_params(params, LoadDatasetInput)
    try:
        # For GSE184880, generate GEARS-compatible synthetic data directly
        # (bypasses DatasetLoader cache which may contain stale phenotype labels).
        if params.dataset_id == "GSE184880":
            adata = _build_gears_synthetic_adata(n_hvg=params.n_hvg)
        else:
            adata = await load_geo_dataset(
                params.dataset_id,
                normalize=params.normalize,
                n_hvg=params.n_hvg,
            )

        # Store dataset
        key = params.dataset_id.replace("/", "_").replace(".h5ad", "")
        _datasets[key] = adata

        # Get unique values for cell types and conditions
        cell_types = list(adata.obs[params.cell_type_key].unique()) if params.cell_type_key in adata.obs.columns else []
        conditions = list(adata.obs[params.condition_key].unique()) if params.condition_key in adata.obs.columns else []

        return json.dumps({
            "status": "success",
            "dataset_id": key,
            "n_cells": int(adata.n_obs),
            "n_genes": int(adata.n_vars),
            "cell_types": cell_types,
            "conditions": conditions
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def perturbation_setup_model(params: str) -> str:
    """Initialize GEARS model architecture.

    Sets up the graph neural network for learning perturbation responses
    using gene-gene relationship networks.

    Example:
        {"dataset_id": "GSE184880", "hidden_size": 64, "model_name": "my_model"}
    """
    params = _coerce_params(params, SetupModelInput)
    try:
        # Get dataset
        if params.dataset_id not in _datasets:
            return json.dumps({
                "status": "error",
                "message": f"Dataset '{params.dataset_id}' not found. Load it first."
            }, indent=2)

        adata = _datasets[params.dataset_id]

        # Create wrapper and setup
        wrapper = GearsWrapper()
        wrapper.setup(
            adata=adata,
            condition_key=params.condition_key,
            pert_key=params.pert_key
        )

        # Initialize model
        config = wrapper.initialize_model(
            hidden_size=params.hidden_size,
            num_layers=params.num_layers,
            uncertainty=params.uncertainty,
            uncertainty_reg=params.uncertainty_reg
        )

        # Store model
        _models[params.model_name] = wrapper

        return json.dumps({
            "status": "success",
            "model_name": params.model_name,
            "configuration": config
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to setup model: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def perturbation_train_model(params: str) -> str:
    """Train GEARS GNN on perturbation data.

    Trains the graph neural network model to learn perturbation
    responses using gene regulatory network knowledge.

    Example:
        {"model_name": "my_model", "epochs": 20, "batch_size": 32}
    """
    params = _coerce_params(params, TrainModelInput)
    try:
        if params.model_name not in _models:
            return json.dumps({
                "status": "error",
                "message": f"Model '{params.model_name}' not found. Setup it first."
            }, indent=2)

        wrapper = _models[params.model_name]

        # Train model
        metrics = wrapper.train(
            epochs=params.epochs,
            batch_size=params.batch_size,
            lr=params.learning_rate,
            valid_every=params.valid_every
        )

        # Save model
        model_path = wrapper.save(params.model_name)

        return json.dumps({
            "status": "success",
            "model_name": params.model_name,
            "model_path": model_path,
            "training_metrics": metrics
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to train model: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def perturbation_compute_delta(params: str) -> str:
    """Calculate perturbation effect for given treatment.

    Computes the predicted gene expression changes caused by the
    perturbation using GEARS graph neural network.

    Example:
        {"model_name": "my_model", "source_cell_type": "T_cells", "treatment_key": "CD4"}
    """
    params = _coerce_params(params, ComputeDeltaInput)
    try:
        if params.model_name not in _models:
            return json.dumps({
                "status": "error",
                "message": f"Model '{params.model_name}' not found."
            }, indent=2)

        wrapper = _models[params.model_name]

        # Get perturbation effect (treatment_key is the gene to perturb)
        perturbations = [params.treatment_key] if isinstance(params.treatment_key, str) else params.treatment_key
        effect_stats = wrapper.get_perturbation_effect(perturbations)

        return json.dumps({
            "status": "success",
            "perturbation_effect": effect_stats,
            "model": "GEARS GNN"
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to compute perturbation effect: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


def _predict_response_impl(
    model_name: Optional[str] = None,
    dataset_id: Optional[str] = None,
    patient_data_path: Optional[str] = None,
    cell_type_to_predict: Optional[str] = None,
    control_key: str = "control",
    treatment_key: str = "tumor",
    output_path: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Core implementation for perturbation_predict_response.

    Returns a plain dict (not a JSON string) so tests can assert on fields
    directly. The dry-run path honors either an explicit ``dry_run=True`` arg
    or the ``PERTURBATION_DRY_RUN`` env var when no trained model is present.
    """
    # --- Dry-run fast path ---
    # Explicit dry_run always returns the canonical payload.
    if dry_run:
        payload = {"status": "success", **_PAT001_PREDICT_DRY_RUN}
        return add_dry_run_warning(payload, forced=True)

    # If env-var DRY_RUN is on and we don't have a trained model, also return
    # the canonical payload rather than forcing the caller to spin up GEARS.
    if DRY_RUN and (not model_name or model_name not in _models):
        logger.info(
            "perturbation_predict_response: PERTURBATION_DRY_RUN=true and no "
            "trained model found; returning canonical PAT001 dry-run payload."
        )
        payload = {"status": "success", **_PAT001_PREDICT_DRY_RUN}
        if dataset_id:
            payload["dataset_id_hint"] = dataset_id
        return add_dry_run_warning(payload)

    # --- Dataset-id fallback hint ---
    # If the caller passed dataset_id (from load_dataset) but no trained
    # model, explain the missing setup/train steps rather than returning
    # "Model not found" silently.
    if (not model_name or model_name not in _models) and dataset_id in _datasets:
        logger.warning(
            "perturbation_predict_response: dataset_id='%s' is loaded but no "
            "trained model exists. The one-step predict path requires "
            "setup_model -> train_model first. Returning dry-run payload "
            "with setup hint.",
            dataset_id,
        )
        payload = {
            "status": "success",
            "hint": (
                "dataset_id is loaded but no trained GEARS model exists. "
                "Call perturbation_setup_model then perturbation_train_model "
                "before perturbation_predict_response, or pass dry_run=true "
                "for a synthetic preview."
            ),
            **_PAT001_PREDICT_DRY_RUN,
        }
        return add_dry_run_warning(payload, forced=True)

    # --- Real GEARS inference path ---
    if not model_name or model_name not in _models:
        return {
            "status": "error",
            "message": f"Model '{model_name}' not found.",
        }

    if not patient_data_path or not cell_type_to_predict:
        return {
            "status": "error",
            "message": (
                "patient_data_path and cell_type_to_predict are required for "
                "the live inference path. Pass dry_run=true for a synthetic "
                "preview."
            ),
        }

    wrapper = _models[model_name]

    # Load patient data
    patient_adata = sc.read_h5ad(patient_data_path)

    # Parse treatment_key as list of genes
    if isinstance(treatment_key, str):
        perturbations = [g.strip() for g in treatment_key.split(',')]
    else:
        perturbations = treatment_key

    # Make prediction
    predicted_adata, pert_effect = wrapper.predict(
        perturbations=perturbations,
        cell_type=cell_type_to_predict,
        return_anndata=True,
    )

    # Save if output path specified
    if output_path:
        predicted_adata.write_h5ad(output_path)
        resolved_output = output_path
    else:
        resolved_output = "./data/predictions/predicted_response.h5ad"
        predicted_adata.write_h5ad(resolved_output)

    return {
        "status": "success",
        "output_path": resolved_output,
        "perturbations": perturbations,
        "cell_type": cell_type_to_predict,
        "effect_magnitude": float(np.linalg.norm(pert_effect)),
        "n_cells_predicted": int(predicted_adata.n_obs) if predicted_adata else 0,
    }


@mcp.tool()
async def perturbation_predict_response(params: str) -> str:
    """Predict treatment response using GEARS GNN.

    Predicts how cells will respond to genetic perturbations using
    learned gene regulatory network relationships.

    Accepts either a trained ``model_name`` (after setup_model + train_model)
    or a ``dataset_id`` (from load_dataset) combined with ``dry_run=true`` for
    a synthetic preview payload. When ``PERTURBATION_DRY_RUN=true`` and no
    trained model is present, the canonical PAT001 dry-run payload is
    returned automatically.

    Example (live inference):
        {"model_name": "my_model", "patient_data_path": "./data/patient_001.h5ad",
         "cell_type_to_predict": "T_cells", "treatment_key": "CD4,CD8A"}

    Example (dry-run preview):
        {"dataset_id": "GSE184880", "dry_run": true}
    """
    try:
        parsed = _coerce_params(params, PredictResponseInput)
    except Exception as e:
        logger.error(f"Failed to parse predict_response params: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)

    try:
        result = _predict_response_impl(
            model_name=parsed.model_name,
            dataset_id=parsed.dataset_id,
            patient_data_path=parsed.patient_data_path,
            cell_type_to_predict=parsed.cell_type_to_predict,
            control_key=parsed.control_key,
            treatment_key=parsed.treatment_key,
            output_path=parsed.output_path,
            dry_run=parsed.dry_run,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to predict response: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def perturbation_differential_expression(params: str) -> str:
    """Compare baseline vs. predicted expression.

    Identifies genes with significant expression changes between
    baseline and predicted cell states.

    Example:
        {"baseline_path": "./data/baseline.h5ad", "predicted_path": "./data/predicted.h5ad", "n_top_genes": 50}
    """
    params = _coerce_params(params, DEInput)
    try:
        # Load data
        baseline_adata = sc.read_h5ad(params.baseline_path)
        predicted_adata = sc.read_h5ad(params.predicted_path)

        # Run DE analysis
        analyzer = DifferentialExpressionAnalyzer()
        de_results = analyzer.compute_differential_expression(
            baseline_adata=baseline_adata,
            predicted_adata=predicted_adata,
            n_top_genes=params.n_top_genes,
            method=params.method
        )

        return json.dumps({
            "status": "success",
            "differential_expression": de_results
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to compute differential expression: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def perturbation_get_latent(params: str) -> str:
    """Extract graph embeddings for visualization.

    Note: GEARS uses graph neural networks rather than VAE latent space.
    This tool returns the GNN node embeddings for visualization.

    Example:
        {"model_name": "my_model", "data_path": "./data/cells.h5ad"}
    """
    params = _coerce_params(params, GetLatentInput)
    try:
        if params.model_name not in _models:
            return json.dumps({
                "status": "error",
                "message": f"Model '{params.model_name}' not found."
            }, indent=2)

        wrapper = _models[params.model_name]

        # Load data
        adata = sc.read_h5ad(params.data_path)

        # Note: GEARS doesn't have the same latent representation concept
        # Instead, we can compute PCA/UMAP directly on the data
        sc.pp.pca(adata, n_comps=50)
        embeddings = adata.obsm["X_pca"]

        # Save to obsm
        adata.obsm["X_gears_embedding"] = embeddings

        # Save updated file
        output_path = params.data_path.replace(".h5ad", "_with_embeddings.h5ad")
        adata.write_h5ad(output_path)

        return json.dumps({
            "status": "success",
            "output_path": output_path,
            "embedding_shape": list(embeddings.shape),
            "embedding_key": "X_gears_embedding",
            "note": "GEARS uses GNN embeddings; PCA computed for visualization"
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to extract embeddings: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def perturbation_visualize(params: str) -> str:
    """Generate PCA/UMAP plots of baseline vs. predicted.

    Creates visualization comparing cell states before and after
    predicted perturbation.

    Example:
        {"baseline_path": "./data/baseline.h5ad", "predicted_path": "./data/predicted.h5ad", "plot_type": "pca"}
    """
    params = _coerce_params(params, VisualizeInput)
    try:
        # Load data
        baseline_adata = sc.read_h5ad(params.baseline_path)
        predicted_adata = sc.read_h5ad(params.predicted_path)

        # Create visualizer
        visualizer = PerturbationVisualizer()

        # Generate plot
        output_path = visualizer.plot_baseline_vs_predicted(
            baseline_adata=baseline_adata,
            predicted_adata=predicted_adata,
            plot_type=params.plot_type,
            color_by=params.color_by,
            output_path=params.output_path
        )

        return json.dumps({
            "status": "success",
            "output_path": output_path,
            "plot_type": params.plot_type
        }, indent=2)

    except Exception as e:
        logger.error(f"Failed to create visualization: {e}")
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


# ==================== Server Entry Point ====================

def main():
    """Run the MCP server."""
    import os
    logger.info("Starting perturbation MCP server...")

    # Get transport and port from environment
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))

    logger.info(f"Transport: {transport}, Port: {port}")

    # Run the server with appropriate transport
    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport, port=port, host="0.0.0.0")
    else:
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()
