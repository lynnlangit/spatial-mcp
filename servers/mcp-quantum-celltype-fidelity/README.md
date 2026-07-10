# Quantum Cell Type Fidelity MCP Server

Quantum computing-based analysis of cell type fidelity in spatial transcriptomics data using Qiskit parameterized quantum circuits (PQCs).

## What This Server Does

`mcp-quantum-celltype-fidelity` encodes per-spot spatial transcriptomics profiles as quantum state vectors using variational quantum circuits, then computes fidelity scores to identify immune evasion states.

**It is a convergent validation layer, not a primary discovery tool.** It is designed to run *after* conventional spatial analysis (Moran's I autocorrelation, NNLS deconvolution) is complete. Agreement between the quantum layer and conventional spatial findings strengthens confidence in immune phenotype assignments. Disagreement between layers is itself clinically informative — it flags spatial heterogeneity that warrants further investigation.

The intended workflow is:

1. Run Moran's I autocorrelation (`mcp-spatialtools`) to identify spatial clustering patterns
2. Run NNLS deconvolution (`mcp-spatialtools`) to quantify cell-type composition
3. Run `mcp-quantum-celltype-fidelity` as an independent cross-check
4. Report concordance or discordance between layers in the findings

The server should not be the sole basis for any clinical classification.

## Overview

This MCP server implements **QuCoWE-style** (Quantum Contrastive Word Embeddings) quantum circuits to embed cell types from spatial transcriptomics data into Hilbert space. Quantum fidelity between states is used to measure cell type similarity, enabling:

- **Immune evasion detection**: Identifying tumor cells evading immune surveillance
- **TLS analysis**: Characterizing tertiary lymphoid structures with quantum signatures
- **Perturbation prediction**: Simulating drug/treatment effects on cell states
- **Spatial context integration**: Learning embeddings aware of spatial neighborhoods

### Key Features

- **Parameterized Quantum Circuits (PQCs)** with 4–10 qubits (4-qubit proof-of-concept; 8–10 for production runs)
- **Parameter-shift rule** for gradient estimation (works on real quantum hardware)
- **Contrastive learning** with InfoNCE loss for training embeddings
- **Bayesian uncertainty quantification** for confidence intervals on fidelity predictions
- **CPU/GPU/IBM Quantum** backend support
- **Spatial neighborhood** integration from AnnData objects
- **6 MCP tools** for complete quantum cell type analysis workflow

## Circuit Architecture

The platform validation runs used a 4-qubit proof-of-concept configuration. Full production runs support 8–10 qubits.

### Proof-of-concept configuration (platform validation)

| Parameter | Value |
|---|---|
| Qubits | 4 |
| Gate types | Rx, Ry, Rz (parameterised rotation gates) |
| Circuit depth | 3 layers |
| Fidelity metric | Squared inner product between spot embedding and reference immune-state vector |
| Evasion threshold | Fidelity < 0.30 → classified as immune evasion state |
| Reference vector | Derived from CD8+ effector and evasion signatures |

The reference immune-state vector is constructed from CD8+ T-cell effector markers (CD8A, GZMB, PRF1, IFNG) and immune evasion signatures (PDCD1, CTLA4, LAG3, TIGIT). A spot scoring below the 0.30 threshold indicates that its transcriptional profile has low fidelity to the reference effector state — consistent with an immune exclusion or suppressed phenotype.

### Production configuration

| Parameter | Value |
|---|---|
| Qubits | 8–10 |
| Hilbert space dimension | 256–1024 |
| Entanglement | Ring entanglement |
| Training | Contrastive learning (InfoNCE loss) |

## Scientific Background

### Quantum Fidelity

Quantum fidelity $F(|\psi_a\rangle, |\psi_b\rangle) = |\langle\psi_a|\psi_b\rangle|^2$ measures the "overlap" between two quantum states. For cell type analysis:

- $F = 1$: Identical cell states
- $F = 0$: Orthogonal cell states (maximally different)
- $0 < F < 1$: Partial similarity

### Parameterized Quantum Circuits

Each cell type is encoded via a PQC:
1. **Feature encoding layer**: Gene expression → rotation angles
2. **Variational layers**: Learnable parameters with RX, RY, RZ gates
3. **Entanglement**: Ring entanglement captures relationships

Training uses contrastive learning to maximize fidelity within cell types and minimize between types.

### Parameter-Shift Rule

Gradients are computed exactly without backpropagation:

$$\frac{\partial f}{\partial \theta} = \frac{f(\theta + \pi/2) - f(\theta - \pi/2)}{2}$$

This enables training on real quantum hardware.

### Bayesian Uncertainty Quantification

Fidelity predictions include confidence intervals via Monte Carlo sampling from parameter posteriors:
- **95%/90% credible intervals**: Quantify prediction uncertainty
- **Classification confidence**: Probability that binary decisions (e.g., immune evasion detected) are correct
- **Clinical impact**: Enables oncologists to assess confidence in treatment recommendations

## Interpreting Results

**Fidelity score range:** 0.0 (no similarity to reference state) → 1.0 (identical to reference state).

| Score range | Interpretation |
|---|---|
| ≥ 0.30 | Spot consistent with CD8+ effector / immune-infiltrated state |
| < 0.30 | Spot classified as immune evasion state (excluded, suppressed, or desert) |

**Always cross-reference with conventional spatial analysis.** The quantum layer is a convergent validation tool. Its findings should be interpreted alongside Moran's I and NNLS deconvolution results, not in isolation.

**Example (PAT001 — HGSOC validation):** Conventional spatial analysis identified a CD8 gradient (5.5× core-to-edge; Moran's I = 0.092) consistent with immune exclusion. Quantum fidelity analysis independently flagged 78% of sampled spots (234/300) as evasion states (fidelity < 0.30). Both layers converging on the same conclusion strengthened confidence in the immune exclusion phenotype and supported the therapeutic recommendation (NNMT inhibition + anti-PD-1 + neoepitope vaccine strategy). If the two layers had disagreed, that disagreement would itself be flagged as a finding warranting further investigation.

**Example (PAT002 — ER+/HER2− IDC cross-patient validation):** PAT002 showed a hormone-receptor-inflamed spatial pattern (ESR1/PGR Moran's I = 0.42–0.45) with limited but detectable CD8A. Quantum fidelity correctly assigned a distinct immune phenotype from PAT001, demonstrating that the fidelity scores are sensitive to real biological differences between patients and not merely an artefact of circuit parameterisation.

## Architecture

```
mcp-quantum-celltype-fidelity/
├── src/quantum_celltype_fidelity/
│   ├── circuits.py          # QuCoWECircuit (Qiskit implementation)
│   ├── embeddings.py         # QuCoWECellTypeEmbedding (parameter management)
│   ├── fidelity.py           # Fidelity scoring heads
│   ├── spatial_context.py    # Spatial neighborhood extraction
│   ├── training.py           # Parameter-shift gradient training
│   └── server.py             # MCP server with 6 tools
├── tests/                    # Unit and integration tests
├── examples/                 # Example notebooks and scripts
└── pyproject.toml            # Dependencies and configuration
```

## MCP Tools

### 1. `learn_spatial_cell_embeddings`

Train quantum embeddings from spatial transcriptomics data.

**Input:**
- `adata_path`: Path to AnnData (.h5ad) file or GCS URI
- `cell_type_key`: Key in adata.obs for cell type labels
- `n_qubits`: Number of qubits (default: 8)
- `n_layers`: Number of variational layers (default: 3)
- `n_epochs`: Training epochs (default: 50)
- `backend`: "cpu", "gpu", or "ibm"

**Output:**
- `embedding_id`: ID for referencing trained embeddings
- `training_summary`: Loss history and metrics
- `embedding_summary`: Circuit configuration

**Example:**
```python
result = learn_spatial_cell_embeddings(
    adata_path="gs://data/patientone_tcells.h5ad",
    cell_type_key="cell_type",
    n_qubits=8,
    n_epochs=50,
    backend="cpu"
)
```

### 2. `compute_cell_type_fidelity`

Compute quantum fidelity between cells with optional uncertainty quantification.

**Input:**
- `adata_path`: Path to AnnData file
- `embedding_id`: ID from training
- `compute_matrix`: Whether to compute full NxN fidelity matrix
- `with_uncertainty`: Enable Bayesian UQ for confidence intervals (default: False)
- `n_uncertainty_samples`: Monte Carlo samples for UQ (default: 100)

**Output:**
- `fidelity_matrix`: Pairwise fidelities (if compute_matrix=True)
- `uncertainty`: 95%/90% confidence intervals, epistemic uncertainty (if with_uncertainty=True)
- `summary_stats`: Mean, std, per-cell-type statistics

### 3. `identify_immune_evasion_states`

Detect cells in immune evasion states with optional classification confidence.

**Input:**
- `immune_cell_types`: List of canonical immune types (e.g., ["T_cell", "B_cell"])
- `exhausted_markers`: Optional exhausted cell types
- `evasion_threshold`: Threshold for flagging (default: 0.3)
- `with_confidence`: Include classification confidence scores (default: False)

**Output:**
- `evading_cells`: List of cells with high evasion scores
- `evasion_score`: Score in [0, 1] for each cell
- `classification_confidence`: Probability that evasion detection is correct (if with_confidence=True)

### 4. `predict_perturbation_effect`

Predict how perturbations affect fidelity.

**Input:**
- `perturbation_type`: "drug", "genetic", "environmental"
- `target_cell_types`: Cell types to perturb
- `perturbation_strength`: Strength (0-1)

**Output:**
- `effects`: Fidelity changes for each cell type
- `effect_direction`: "increase" or "decrease"

### 5. `analyze_tls_quantum_signature`

Analyze quantum signatures of tertiary lymphoid structures.

**Input:**
- `tls_marker_types`: Cell types indicating TLS (e.g., ["B_cell", "T_cell"])
- `min_cluster_size`: Minimum cells for TLS (default: 20)
- `max_distance`: Spatial distance threshold (default: 100)

**Output:**
- `tls_candidates`: List of TLS with quantum signatures
- `quantum_signature`: Mean fidelity, std, per-type composition

### 6. `export_for_downstream`

Export embeddings for downstream analysis.

**Input:**
- `output_format`: "numpy", "json", "pytorch"
- `output_path`: Path to save

**Output:**
- `exported_files`: List of exported file paths

## XAI Metadata

Every tool returns an `xai_metadata` field with explainability information:

| Field | Description |
|-------|-------------|
| `confidence_level` | `high`, `moderate`, or `low` — how reliable the result is given the inputs |
| `confidence_note` | Why this confidence level was assigned |
| `key_drivers` | 1-3 inputs that most influenced the result |
| `guideline_version` | QuCoWE-style PQC framework reference |
| `evidence_grade` | Research Only — Novel Method |
| `counterfactual` | What would change if a key input were different |

## Server Availability and Graceful Degradation

The quantum simulation backend requires a running server process. If the server is unavailable at pipeline execution time:

- The orchestrator records a `QUANTUM_PENDING_SERVER_RESTART` deferral in the session provenance log
- Pipeline execution continues using conventional spatial analysis (Moran's I) as the primary immune phenotype classification
- The quantum result is noted as pending in the patient report
- The report clearly distinguishes findings that have received quantum cross-validation from those that have not

**This is expected behaviour, not a pipeline failure.** The platform is designed so that the absence of the quantum validation layer degrades output quality gracefully rather than blocking the entire run. The conventional spatial analysis is the primary analytical layer; the quantum layer provides independent confirmation.

When the server is restarted, re-run `identify_immune_evasion_states` on the same patient data to obtain the quantum result and append it to the session log.

**Example (PAT002):** The quantum cell-type fidelity server was initially deferred for PAT002 due to server unavailability (`QUANTUM_PENDING_SERVER_RESTART`). The oncology pipeline proceeded with Moran's I and NNLS results as primary classification. When the server was restarted, `identify_immune_evasion_states` was re-run and its output was appended to the PAT002 session log. The deferred run and its timestamp are recorded in Supplementary Table S1.

## Installation

**Requires:** Python 3.11+

> **Standard setup:** See [Server Installation Guide](../../docs/reference/shared/server-installation.md) for venv creation, pip install, and Claude Desktop config.

### GPU Installation (CUDA + cuQuantum)

```bash
pip install -e ".[gpu]"
```

Requires:
- CUDA 11.8+
- cuQuantum SDK 23.3+
- NVIDIA GPU with Compute Capability 7.0+

### IBM Quantum Hardware

1. Get IBM Quantum API token from https://quantum-computing.ibm.com/
2. Set environment variable:
```bash
export IBM_QUANTUM_TOKEN="your_token_here"
```

## Usage Examples

### Example 1: Train Embeddings on PatientOne Data

```python
# Train quantum embeddings
result = await mcp.call_tool(
    "learn_spatial_cell_embeddings",
    {
        "adata_path": "gs://sample-inputs-patientone/perturbation/patientone_tcells.h5ad",
        "cell_type_key": "cell_type",
        "n_qubits": 8,
        "n_layers": 3,
        "n_epochs": 50,
        "learning_rate": 0.01,
        "backend": "cpu"
    }
)

embedding_id = result["embedding_id"]
print(f"Trained embeddings: {embedding_id}")
print(f"Final loss: {result['training_summary']['final_loss']:.4f}")
```

### Example 2: Detect Immune Evasion

```python
# Identify tumor cells evading immune surveillance
result = await mcp.call_tool(
    "identify_immune_evasion_states",
    {
        "adata_path": "gs://sample-inputs-patientone/perturbation/patientone_tcells.h5ad",
        "embedding_id": embedding_id,
        "immune_cell_types": ["T_cell", "B_cell", "NK_cell"],
        "exhausted_markers": ["T_exhausted", "T_regulatory"],
        "evasion_threshold": 0.3
    }
)

print(f"Found {result['n_evading_cells']} cells in evasion states")
for cell in result["evading_cells"][:5]:
    print(f"  Cell {cell['cell_idx']}: {cell['cell_type']} (score: {cell['evasion_score']:.3f})")
```

### Example 3: Analyze TLS Quantum Signatures

```python
# Find and characterize tertiary lymphoid structures
result = await mcp.call_tool(
    "analyze_tls_quantum_signature",
    {
        "adata_path": "gs://sample-inputs-patientone/perturbation/patientone_tcells.h5ad",
        "embedding_id": embedding_id,
        "tls_marker_types": ["B_cell", "T_cell", "Dendritic_cell"],
        "min_cluster_size": 20,
        "max_distance": 100.0
    }
)

print(f"Found {result['n_tls_candidates']} TLS candidates")
for tls in result["tls_candidates"]:
    print(f"\nTLS {tls['tls_id']}:")
    print(f"  Cells: {tls['n_cells']}")
    print(f"  Composition: {tls['cell_type_composition']}")
    print(f"  Mean fidelity: {tls['quantum_signature']['mean_fidelity']:.3f}")
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Performance

### Circuit Simulation

| Backend | n_qubits | Statevector Time | Fidelity Computation |
|---------|----------|------------------|---------------------|
| CPU     | 4        | ~2 ms           | ~5 ms               |
| CPU     | 8        | ~10 ms          | ~20 ms              |
| CPU     | 10       | ~50 ms          | ~100 ms             |
| GPU     | 8        | ~2 ms           | ~5 ms               |
| GPU     | 10       | ~5 ms           | ~10 ms              |

### Training

- **50 epochs, 500 cells, 5 cell types**: ~5 minutes (CPU), ~1 minute (GPU)
- **100 epochs, 1000 cells, 10 cell types**: ~30 minutes (CPU), ~6 minutes (GPU)

### Memory

- **4 qubits**: ~0.5 MB per statevector
- **8 qubits**: ~2 MB per statevector
- **10 qubits**: ~8 MB per statevector
- **Training**: ~100-500 MB depending on dataset size

## Deployment

### Cloud Run (Production)

```bash
cd infrastructure/deployment
./deploy_to_gcp.sh --server quantum-celltype-fidelity
```

### Local Development

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your_key_here"

# Run server
cd servers/mcp-quantum-celltype-fidelity
python -m quantum_celltype_fidelity.server
```

## Scientific References

1. **QuCoWE**: Quantum Contrastive Word Embeddings approach adapted for cell types
2. **Parameter-shift rule**: Mitarai et al., Physical Review A 98, 032309 (2018)
3. **Variational quantum algorithms**: Cerezo et al., Nature Reviews Physics 3, 625–644 (2021)
4. **Spatial transcriptomics**: Moses & Pachter, Nature Methods 19, 534–546 (2022)
5. **Immune exclusion in HGSOC**: Vázquez-García et al., Cancer Cell 41, 1692–1710 (2023)

## Use Case: HGSOC Immunotherapy Targets

This server was developed for high-grade serous ovarian cancer (HGSOC) research:

- **Identify immune evasion**: Tumor cells with low T-cell fidelity
- **Characterize TLS**: Immune-rich regions for therapy targeting
- **Predict drug response**: Effects of checkpoint inhibitors on cell states
- **Spatial context**: How tumor-immune boundaries affect fidelity

## Synthetic Data and Research Status

All validation results in this repository were produced in `SYNTHETIC_DATA` mode. The quantum circuit implementation is a proof-of-concept demonstration of variational quantum classification applied to spatial transcriptomics. It has not been validated on real patient specimens and is **not approved for clinical use**.

The fidelity threshold (0.30) and reference vector construction were calibrated on the synthetic HGSOC and ER+/HER2− IDC datasets. Real-world deployment would require recalibration against labelled spatial transcriptomics data with ground-truth immune phenotype calls from a clinically annotated cohort.

All patient identifiers (PAT001, PAT002, PAT003) refer to fully synthetic records. No real patient data was used in any stage of development or validation.

## Limitations

- **Circuit depth**: Limited by decoherence on real quantum hardware
- **Scalability**: Current implementation handles ~10,000 cells; for larger datasets, use sampling
- **Feature encoding**: Simple amplitude encoding; future work will explore other encodings
- **Training time**: Parameter-shift rule requires 2N forward passes per gradient
- **Threshold calibration**: The 0.30 evasion threshold was set on synthetic data and will require prospective recalibration before clinical use
- **Convergent validation only**: Quantum fidelity scores should always be interpreted alongside conventional spatial analysis results, not as standalone diagnostic outputs

## Future Work

- [ ] Add support for 3D spatial coordinates
- [ ] Implement amplitude amplification for rare cell types
- [ ] Integrate with GEARS perturbation server for combined analysis
- [ ] Add Bayesian optimization for hyperparameter tuning
- [ ] Support for IBM Quantum hardware execution
- [ ] Prospective recalibration study on real clinical spatial transcriptomics cohort

## License

Apache 2.0

## Contributing

Contributions welcome! Please see the main repository's CONTRIBUTING.md for guidelines.

## Support

- **Issues**: https://github.com/lynnlangit/precision-medicine-mcp/issues
- **Discussions**: https://github.com/lynnlangit/precision-medicine-mcp/discussions
- **Documentation**: https://github.com/lynnlangit/precision-medicine-mcp/tree/main/docs
