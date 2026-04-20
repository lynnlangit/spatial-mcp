# MCP Perturbation Server

**Single-cell perturbation prediction using GEARS for precision medicine**

Predicts how patient cancer cells might respond to immunotherapy *in silico* using graph neural networks and biological knowledge graphs.

> **Powered by GEARS**: Uses GEARS (Graph-Enhanced Gene Activation and Repression Simulator), a state-of-the-art graph neural network approach published in Nature Biotechnology 2024.

---

## Overview

This MCP server uses **GEARS** (Graph-Enhanced Gene Activation and Repression Simulator) to predict cellular responses to perturbations (e.g., genetic modifications, drug treatments, immunotherapy) without actually performing the experiment. It integrates biological knowledge graphs of gene-gene relationships with deep learning to predict treatment effects.

### The GEARS Approach

GEARS uses graph neural networks (GNNs) combined with gene regulatory network knowledge to predict perturbation responses:

**Key advantages over VAE-based methods:**
- **40% higher precision** than previous approaches (Nature Biotechnology 2024)
- **Integrates biological knowledge**: Uses gene-gene relationship networks
- **Multi-gene perturbations**: Handles complex combinatorial effects
- **Uncertainty quantification**: Provides confidence estimates for predictions
- **Better generalization**: Leverages graph structure to predict unseen perturbations

**How it works:**
1. Encodes gene relationships as a knowledge graph
2. Uses GNN to learn how perturbations propagate through the network
3. Predicts gene expression changes for novel perturbations
4. Handles single and multi-gene perturbation combinations

### Key Applications

- **Treatment Response Prediction**: Predict how a patient's cells will respond to immunotherapy
- **Drug Screening**: Test multiple treatments *in silico* before clinical application
- **Personalized Medicine**: Identify optimal therapies based on patient-specific cellular profiles
- **Clinical Trial Design**: Pre-screen patients likely to respond to experimental therapies

---

## Installation

### Prerequisites

- Python >= 3.11
- PyTorch >= 2.0.0
- `uv` package manager
- CUDA (optional, for GPU acceleration)

### Install

```bash
cd servers/mcp-perturbation
uv sync
```

### Key Dependencies

- `cell-gears` - GEARS perturbation prediction (Nature Biotech 2024)
- `torch-geometric` - Graph neural network framework
- `scanpy`, `anndata` - Single-cell data handling
- `torch` - Deep learning framework (PyTorch)

---

## Quick Start

### 1. Load Dataset

Load scRNA-seq data from GEO or a local .h5ad file:

```json
{
  "tool": "perturbation_load_dataset",
  "params": {
    "dataset_id": "GSE184880",
    "normalize": true,
    "n_hvg": 7000,
    "cell_type_key": "cell_type",
    "condition_key": "condition"
  }
}
```

**Returns**: Dataset metadata (n_cells, n_genes, cell types, conditions)

### 2. Setup and Train Model

Initialize GEARS model:

```json
{
  "tool": "perturbation_setup_model",
  "params": {
    "dataset_id": "GSE184880",
    "hidden_size": 64,
    "model_name": "ovarian_cancer_model"
  }
}
```

Train the GEARS model:

```json
{
  "tool": "perturbation_train_model",
  "params": {
    "model_name": "ovarian_cancer_model",
    "epochs": 20,
    "learning_rate": 0.001
  }
}
```

**Note:** GEARS typically converges in 20 epochs. Training downloads a ~60 MB Gene Ontology graph on first run.

### 3. Compute Perturbation Effect

Calculate perturbation effect for specific genes:

```json
{
  "tool": "perturbation_compute_delta",
  "params": {
    "model_name": "ovarian_cancer_model",
    "treatment_key": "NNMT"
  }
}
```

**Note:** GEARS predicts effects of genetic perturbations (gene knockouts/upregulation). For drug treatments, map drugs to their target genes.

### 4. Predict Patient Response

Apply GEARS prediction to patient data:

```json
{
  "tool": "perturbation_predict_response",
  "params": {
    "model_name": "ovarian_cancer_model",
    "patient_data_path": "./data/patient_001.h5ad",
    "cell_type_to_predict": "T_cells",
    "treatment_key": "NNMT,STAT3"
  }
}
```

**Returns**: Predicted cell states, perturbation effect magnitude, number of cells predicted

**Multi-gene perturbations**: Specify multiple genes separated by commas. GEARS predicts combinatorial effects using its gene-gene interaction graph.

---

## Tool Reference

### 1. `perturbation_load_dataset`

Load and preprocess scRNA-seq data from GEO or local file.

**Parameters:**
- `dataset_id` (str): GEO accession (e.g., "GSE184880") or path to .h5ad
- `normalize` (bool): Apply normalization (default: true)
- `n_hvg` (int): Number of highly variable genes (default: 7000)
- `cell_type_key` (str): Column with cell type labels
- `condition_key` (str): Column with treatment condition

**Returns:** JSON with dataset metadata

---

### 2. `perturbation_setup_model`

Initialize GEARS graph neural network model.

**Parameters:**
- `dataset_id` (str, required): Dataset ID from load_dataset
- `hidden_size` (int): Hidden layer size for GNN (default: 64)
- `num_layers` (int): Number of GNN layers for both GO and gene graphs (default: 1)
- `uncertainty` (bool): Enable uncertainty quantification (default: false)
- `uncertainty_reg` (float): Uncertainty regularization weight (default: 1.0)
- `model_name` (str): Name for this model (default: "gears_model")
- `condition_key` (str): Column with condition labels (default: "condition")
- `pert_key` (str): Column with perturbation labels (default: "perturbation")

**Returns:** Model configuration summary

---

### 3. `perturbation_train_model`

Train GEARS graph neural network on perturbation data.

**Parameters:**
- `model_name` (str, required): Model name from setup_model
- `epochs` (int): Training epochs (default: 20)
- `learning_rate` (float): Learning rate (default: 0.001)

**Returns:** Training metrics (epochs completed, model path)

**Note:** GEARS sets batch size at dataloader creation (during setup_model) and validates every epoch internally.

---

### 4. `perturbation_compute_delta`

Calculate perturbation vector (Δ) between conditions.

**Parameters:**
- `model_name` (str): Trained model name
- `source_cell_type` (str): Cell type to compute delta from (None = all)
- `control_key` (str): Control condition label
- `treatment_key` (str): Treatment condition label

**Returns:** Delta vector statistics (norm, mean, std, cell counts)

---

### 5. `perturbation_predict_response`

Apply Δ to patient's baseline cells to predict treated state.

**Parameters:**
- `model_name` (str): Trained model name
- `patient_data_path` (str): Path to patient .h5ad file
- `cell_type_to_predict` (str): Cell type to transform
- `control_key` (str): Control condition label
- `treatment_key` (str): Treatment condition label
- `output_path` (str, optional): Path to save predictions

**Returns:** Prediction summary with file path, delta norm, changed genes

---

### 6. `perturbation_differential_expression`

Compare baseline vs. predicted expression.

**Parameters:**
- `baseline_path` (str): Baseline .h5ad file
- `predicted_path` (str): Predicted .h5ad file
- `n_top_genes` (int): Number of top genes to return (default: 50)
- `method` (str): Statistical test ("wilcoxon" or "t-test")

**Returns:** Top upregulated/downregulated genes with fold changes

---

### 7. `perturbation_get_latent`

Extract latent representations for visualization.

**Parameters:**
- `model_name` (str): Trained model name
- `data_path` (str): .h5ad file to embed

**Returns:** Path to .h5ad with latent embeddings in .obsm["X_gears"]

---

### 8. `perturbation_visualize`

Generate PCA/UMAP plots of baseline vs. predicted.

**Parameters:**
- `baseline_path` (str): Baseline .h5ad file
- `predicted_path` (str): Predicted .h5ad file
- `plot_type` (str): "pca" or "umap" (default: "pca")
- `color_by` (str): Column to color by (default: "condition")
- `output_path` (str, optional): Path to save figure

**Returns:** Path to saved figure

---

## Primary Dataset: GSE184880

**Synthetic HGSOC-modeled Perturb-seq data** for GEARS training.

**Cells**: 5,000 synthetic cells across 5 cell types
**Genes**: Configurable via `n_hvg` (default 7,000); includes 10 real HGSOC-relevant genes as perturbation targets

**Cell Types**: T_cells, B_cells, Macrophages, Epithelial, Fibroblasts

**Perturbation Conditions** (GEARS format):
- `ctrl` — unperturbed control cells
- `NNMT+ctrl`, `STAT3+ctrl`, `TP53+ctrl`, `BRCA1+ctrl`, `MYC+ctrl`, `PIK3CA+ctrl`, `PTEN+ctrl`, `CCNE1+ctrl`, `AKT1+ctrl`, `CDK2+ctrl` — single-gene knockdown perturbations

Each perturbation condition applies a knockdown effect (0.05x) on the target gene, allowing GEARS to learn gene-gene interaction effects.

---

## Example Workflow: PatientOne (NNMT Knockdown)

### Scenario

PatientOne has HGSOC ovarian cancer with 18.2% CAF fraction. We predict the effect of NNMT knockdown on the CAF barrier using GEARS.

### Step 1: Load Reference Data

```json
{
  "tool": "perturbation_load_dataset",
  "params": {
    "dataset_id": "GSE184880",
    "normalize": true,
    "n_hvg": 7000
  }
}
```

### Step 2: Setup and Train Model

```json
{
  "tool": "perturbation_setup_model",
  "params": {
    "dataset_id": "GSE184880",
    "model_name": "patient_one_model"
  }
}
```

```json
{
  "tool": "perturbation_train_model",
  "params": {
    "model_name": "patient_one_model",
    "epochs": 20
  }
}
```

### Step 3: Predict NNMT Knockdown Response

```json
{
  "tool": "perturbation_predict_response",
  "params": {
    "model_name": "patient_one_model",
    "patient_data_path": "./data/patient_one_baseline.h5ad",
    "cell_type_to_predict": "Fibroblasts",
    "treatment_key": "NNMT"
  }
}
```

### Expected Results (from Paper v16, Section 3.5)

**NNMT knockdown predicted effects:**
- STAT3 (−0.24), COL3A1 (−0.21) — CAF barrier dismantlement
- PRF1 (+0.27), FOXP3 (+0.20) — immune recovery markers

**Clinical Interpretation**: NNMT inhibition reduces CAF signaling and increases cytotoxic T-cell markers, indicating potential for CAF-targeted therapy in HGSOC.

---

## Architecture

### Model: GEARS (Graph Neural Network)

**Type**: Graph Neural Network (GNN) for perturbation prediction

**Components**:
1. **Gene Relationship Graph**: Encodes biological knowledge (GO terms, PPI networks)
2. **GNN Layers**: Message passing over gene-gene relationships
3. **Prediction Head**: Predicts gene expression changes
4. **Uncertainty Module**: Provides confidence estimates (optional)

**How GEARS Works**:
```
1. Build gene relationship graph (20,000+ genes)
2. GNN propagates perturbation effects through network
3. Predict expression changes for each gene
4. Handle multi-gene perturbations (combinatorial effects)
```

### Prediction Process

```
Input: Gene perturbations (e.g., ["NNMT", "STAT3"])
       ↓
Gene Graph: Encode GO + gene-gene relationships
       ↓
GNN Layers: Message passing (1 layer default)
       ↓
Output: Predicted gene expression changes Δ
       ↓
Apply to baseline: Predicted cell state
```

---

## Testing

### Run All Tests

```bash
cd servers/mcp-perturbation
uv run pytest -v
```

### Run Specific Test File

```bash
uv run pytest tests/test_gears_wrapper.py -v
```

---

## Performance

### Training Time

| Dataset Size | hidden_size | epochs | GPU Time | CPU Time |
|--------------|-------------|--------|----------|----------|
| 5K cells | 64 | 20 | ~1 min | ~5 min |
| 20K cells | 64 | 20 | ~3 min | ~15 min |

### Prediction Time

| Operation | Time |
|-----------|------|
| Single perturbation | ~1 second |
| Combo perturbation | ~2 seconds |

---

## Troubleshooting

### Issue: CUDA out of memory

**Solution**: Reduce hidden_size (default 64, try 32)

### Issue: Model not converging

**Solutions**:
1. Increase epochs (default 20, try 50)
2. Reduce learning rate (default 0.001, try 0.0001)
3. Increase hidden_size (default 64, try 128)

### Issue: Poor predictions

**Solutions**:
1. Ensure data has GEARS-format conditions (`ctrl`, `GENE+ctrl`)
2. Check that cell types are annotated correctly
3. Increase n_hvg (more genes = better signal)
4. Verify perturbation target genes are present in the dataset

---

## Scientific Background

### Key Papers

1. **GEARS**: Roohani et al., "Predicting transcriptional outcomes of novel multigene perturbations with GEARS", Nature Biotechnology (2024)
2. **HGSOC scRNA-seq**: Izar et al., "A single-cell landscape of high-grade serous ovarian cancer", Nature Medicine (2020)

---

## Related Servers

- **mcp-spatialtools**: Spatial transcriptomics analysis
- **mcp-multiomics**: Multi-omics integration
- **mcp-epic**: Clinical data from FHIR
- **mcp-mocktcga**: Mock TCGA cohort data

---

## Contributing

See [CONTRIBUTING.md](../../docs/for-developers/CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
cd servers/mcp-perturbation
uv sync
```

---

## License

Apache 2.0 - See [LICENSE](../../LICENSE)

---

**Part of the Precision Medicine MCP suite** - Enabling AI-driven bioinformatics for cancer research.
