"""Tests for quantum circuits."""

import pytest
import numpy as np

from quantum_celltype_fidelity.circuits import QuCoWECircuit


def test_circuit_initialization():
    """Test circuit initialization with default parameters."""
    circuit = QuCoWECircuit(n_qubits=8, n_layers=3, feature_dim=256)

    assert circuit.n_qubits == 8
    assert circuit.n_layers == 3
    assert circuit.feature_dim == 256
    assert circuit.hilbert_dim == 256  # 2^8

    # Check parameter counts
    params = circuit.get_parameter_count()
    assert params["n_qubits"] == 8
    assert params["feature_params"] == 8
    assert params["variational_params"] == 8 * 3 * 3  # qubits * gates_per_qubit * layers


def test_encode_features():
    """Test feature encoding."""
    circuit = QuCoWECircuit(n_qubits=8, feature_dim=256)

    # Create random features
    features = np.random.randn(256)

    # Encode
    encoded = circuit.encode_features(features)

    assert encoded.shape == (8,)
    assert np.all((encoded >= 0) & (encoded <= 2 * np.pi))


def test_encode_features_wrong_dim():
    """Test encoding with wrong feature dimension."""
    circuit = QuCoWECircuit(n_qubits=8, feature_dim=256)

    # Wrong dimension
    features = np.random.randn(128)

    with pytest.raises(ValueError, match="Expected features of dim 256"):
        circuit.encode_features(features)


def test_bind_parameters():
    """Test parameter binding."""
    circuit = QuCoWECircuit(n_qubits=8, n_layers=3, feature_dim=256)

    features = np.random.randn(256)
    theta = np.random.uniform(0, 2 * np.pi, 8 * 3 * 3)

    # Bind parameters
    bound_circuit = circuit.bind_parameters(features, theta)

    # Should have no free parameters
    assert len(bound_circuit.parameters) == 0


def test_get_statevector():
    """Test statevector computation."""
    circuit = QuCoWECircuit(n_qubits=4, n_layers=2, feature_dim=64)

    features = np.random.randn(64)

    # Get statevector
    statevector = circuit.get_statevector(features, backend="cpu")

    # Check properties
    assert statevector.shape == (16,)  # 2^4
    assert np.allclose(np.linalg.norm(statevector), 1.0)  # Normalized
    assert statevector.dtype == np.complex128


def test_compute_fidelity():
    """Test fidelity computation."""
    circuit = QuCoWECircuit(n_qubits=4, n_layers=2, feature_dim=64)

    features_a = np.random.randn(64)
    features_b = np.random.randn(64)

    # Same parameters for both
    theta = np.random.uniform(0, 2 * np.pi, 4 * 3 * 2)

    fidelity = circuit.compute_fidelity(features_a, features_b, theta, theta, backend="cpu")

    # Fidelity should be in [0, 1]
    assert 0 <= fidelity <= 1


def test_self_fidelity():
    """Test that self-fidelity is 1.0."""
    circuit = QuCoWECircuit(n_qubits=4, n_layers=2, feature_dim=64)

    features = np.random.randn(64)
    theta = np.random.uniform(0, 2 * np.pi, 4 * 3 * 2)

    fidelity = circuit.compute_fidelity(features, features, theta, theta, backend="cpu")

    # Self-fidelity should be 1.0
    assert np.allclose(fidelity, 1.0, atol=1e-6)


def test_circuit_serialization():
    """Test circuit serialization and deserialization."""
    circuit = QuCoWECircuit(n_qubits=8, n_layers=3, feature_dim=256, entanglement="ring")

    # Serialize
    config = circuit.to_dict()

    # Deserialize
    circuit2 = QuCoWECircuit.from_dict(config)

    assert circuit2.n_qubits == circuit.n_qubits
    assert circuit2.n_layers == circuit.n_layers
    assert circuit2.feature_dim == circuit.feature_dim
    assert circuit2.entanglement == circuit.entanglement


def test_different_entanglement_patterns():
    """Test different entanglement patterns."""
    for entanglement in ["ring", "linear", "full"]:
        circuit = QuCoWECircuit(n_qubits=4, n_layers=2, feature_dim=64, entanglement=entanglement)
        features = np.random.randn(64)
        statevector = circuit.get_statevector(features, backend="cpu")

        # Should still produce valid statevector
        assert statevector.shape == (16,)
        assert np.allclose(np.linalg.norm(statevector), 1.0)


def test_visualize():
    """Test circuit visualization."""
    circuit = QuCoWECircuit(n_qubits=4, n_layers=2)
    diagram = circuit.visualize()

    assert isinstance(diagram, str)
    assert len(diagram) > 0
