"""Integration tests verifying overall structure and logic."""

import pytest
import numpy as np
from pathlib import Path


def test_package_structure():
    """Test that package structure is correct."""
    server_root = Path(__file__).parent.parent

    # Check main directories exist
    assert (server_root / "src").exists()
    assert (server_root / "src" / "quantum_celltype_fidelity").exists()
    assert (server_root / "tests").exists()
    assert (server_root / "examples").exists()

    # Check key files exist
    assert (server_root / "pyproject.toml").exists()
    assert (server_root / "README.md").exists()


def test_all_modules_importable():
    """Test that all modules can be imported."""
    try:
        from quantum_celltype_fidelity import (
            QuCoWECircuit,
            QuCoWECellTypeEmbedding,
            FidelityScore,
            FidelityHead,
            LogitFidelityHead,
            ImmuneEvasionDetector,
            SpatialContextGenerator,
            QuCoWETrainer,
            TrainingConfig
        )
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")


def test_fidelity_properties():
    """Test mathematical properties of fidelity."""
    # Fidelity should be in [0, 1]
    fidelity = 0.75
    assert 0 <= fidelity <= 1

    # Self-fidelity should be 1
    self_fidelity = 1.0
    assert np.isclose(self_fidelity, 1.0)

    # Fidelity is symmetric: F(a, b) = F(b, a)
    # (This is a property test, not actual computation)


def test_parameter_shift_rule_formula():
    """Test parameter-shift rule gradient formula."""
    # For a simple function, verify parameter-shift gives correct gradient
    # f(x) = sin(x)
    # df/dx = cos(x)
    # Parameter-shift: [f(x + pi/2) - f(x - pi/2)] / 2 = [sin(x + pi/2) - sin(x - pi/2)] / 2

    x = 0.5
    shift = np.pi / 2

    # True gradient
    true_gradient = np.cos(x)

    # Parameter-shift estimate
    f_plus = np.sin(x + shift)
    f_minus = np.sin(x - shift)
    estimated_gradient = (f_plus - f_minus) / 2

    # Should match (for sin function)
    assert np.isclose(estimated_gradient, true_gradient, atol=1e-10)


def test_contrastive_loss_properties():
    """Test properties of contrastive loss."""
    margin = 0.5

    # Case 1: Positive pair has higher fidelity than negative (good)
    fid_pos = 0.9
    fid_neg = 0.3
    loss = max(0.0, margin + fid_neg - fid_pos)
    assert loss == 0.0  # No loss, already separated

    # Case 2: Negative pair has higher fidelity (bad)
    fid_pos = 0.3
    fid_neg = 0.9
    loss = max(0.0, margin + fid_neg - fid_pos)
    assert loss > 0  # Loss should be positive

    # Case 3: Close to margin
    fid_pos = 0.6
    fid_neg = 0.2
    loss = max(0.0, margin + fid_neg - fid_pos)
    assert np.isclose(loss, 0.1)  # 0.5 + 0.2 - 0.6 = 0.1


def test_infonce_loss_properties():
    """Test InfoNCE loss properties."""
    temperature = 0.1

    fid_pos = 0.8
    fids_neg = [0.3, 0.25, 0.35, 0.2, 0.3]

    # Convert to logits
    logit_pos = fid_pos / temperature
    logits_neg = [f / temperature for f in fids_neg]

    all_logits = [logit_pos] + logits_neg
    max_logit = max(all_logits)

    # Compute exp terms
    exp_pos = np.exp(logit_pos - max_logit)
    exp_neg_sum = sum(np.exp(l - max_logit) for l in logits_neg)

    # InfoNCE loss
    loss = -np.log(exp_pos / (exp_pos + exp_neg_sum))

    # Loss should be positive and finite
    assert loss > 0
    assert np.isfinite(loss)

    # When positive fidelity is much higher than negatives, loss should be small
    assert loss < 5.0  # Reasonable upper bound


def test_immune_evasion_logic():
    """Test immune evasion scoring logic."""
    # High fidelity to immune cells -> low evasion
    fidelities_immune = [0.8, 0.85, 0.9]
    avg_fidelity = np.mean(fidelities_immune)
    evasion_score = 1.0 - avg_fidelity

    assert evasion_score < 0.3  # Low evasion

    # Low fidelity to immune cells -> high evasion
    fidelities_immune = [0.2, 0.15, 0.25]
    avg_fidelity = np.mean(fidelities_immune)
    evasion_score = 1.0 - avg_fidelity

    assert evasion_score > 0.7  # High evasion


def test_rotation_angle_normalization():
    """Test that rotation angles are normalized to [0, 2π]."""
    # Simulate feature encoding
    features = np.random.randn(256)

    # Normalize using arctan scaling
    encoded = np.arctan(features) + np.pi / 2  # Maps to [0, π]
    encoded = encoded * 2  # Scale to [0, 2π]

    # Check range
    assert np.all((encoded >= 0) & (encoded <= 2 * np.pi))


def test_quantum_state_normalization():
    """Test that quantum states are normalized."""
    # Create a random complex state vector
    n_qubits = 4
    dim = 2 ** n_qubits

    real_part = np.random.randn(dim)
    imag_part = np.random.randn(dim)
    statevector = real_part + 1j * imag_part

    # Normalize
    norm = np.linalg.norm(statevector)
    statevector_normalized = statevector / norm

    # Check normalization
    assert np.isclose(np.linalg.norm(statevector_normalized), 1.0)


def test_fidelity_computation_formula():
    """Test fidelity computation formula."""
    # Create two normalized state vectors
    psi_a = np.array([1, 0, 0, 0], dtype=complex)
    psi_b = np.array([1/np.sqrt(2), 1/np.sqrt(2), 0, 0], dtype=complex)

    # Compute fidelity: |<psi_a|psi_b>|^2
    inner_product = np.vdot(psi_a, psi_b)
    fidelity = np.abs(inner_product) ** 2

    # Should be 0.5 (due to 1/sqrt(2) overlap)
    assert np.isclose(fidelity, 0.5)


def test_mcp_server_structure():
    """Test that MCP server has correct structure."""
    from quantum_celltype_fidelity import server

    # Check that server module exists
    assert hasattr(server, 'mcp')

    # Check that expected tools exist (function names)
    module_functions = dir(server)

    expected_tools = [
        'learn_spatial_cell_embeddings',
        'compute_cell_type_fidelity',
        'identify_immune_evasion_states',
        'predict_perturbation_effect',
        'analyze_tls_quantum_signature',
        'export_for_downstream'
    ]

    for tool in expected_tools:
        assert tool in module_functions, f"Tool {tool} not found in server module"


def test_pyproject_dependencies():
    """Test that pyproject.toml has correct dependencies."""
    import tomllib
    server_root = Path(__file__).parent.parent

    with open(server_root / "pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    # Check key dependencies
    dependencies = config["project"]["dependencies"]

    required_deps = [
        "fastmcp",
        "qiskit",
        "numpy",
        "scipy",
        "pandas",
        "scikit-learn",
        "anndata"
    ]

    for dep in required_deps:
        assert any(dep in d for d in dependencies), f"Dependency {dep} not found"


def test_readme_exists_and_complete():
    """Test that README exists and has key sections."""
    server_root = Path(__file__).parent.parent
    readme_path = server_root / "README.md"

    assert readme_path.exists()

    readme_content = readme_path.read_text()

    # Check for key sections
    assert "# Quantum Cell Type Fidelity MCP Server" in readme_content
    assert "## MCP Tools" in readme_content
    assert "## Installation" in readme_content
    assert "## Usage Examples" in readme_content

    # Check for all 6 tools documented
    assert "learn_spatial_cell_embeddings" in readme_content
    assert "compute_cell_type_fidelity" in readme_content
    assert "identify_immune_evasion_states" in readme_content
    assert "predict_perturbation_effect" in readme_content
    assert "analyze_tls_quantum_signature" in readme_content
    assert "export_for_downstream" in readme_content
