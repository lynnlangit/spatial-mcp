"""Tests for quantum embeddings management."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from quantum_celltype_fidelity.embeddings import QuCoWECellTypeEmbedding


@pytest.fixture
def mock_circuit():
    """Create a mock QuCoWECircuit."""
    circuit = Mock()
    circuit.n_qubits = 8
    circuit.n_layers = 3
    circuit.feature_dim = 256
    circuit.hilbert_dim = 256
    circuit.theta_params = Mock()
    circuit.theta_params.__len__ = Mock(return_value=72)  # 8 * 3 * 3
    circuit.get_statevector = Mock(return_value=np.random.randn(256) + 1j * np.random.randn(256))
    circuit.compute_fidelity = Mock(return_value=0.75)
    circuit.to_dict = Mock(return_value={
        "n_qubits": 8,
        "n_layers": 3,
        "feature_dim": 256,
        "entanglement": "ring",
        "hilbert_dim": 256
    })
    return circuit


@pytest.fixture
def embedding(mock_circuit):
    """Create QuCoWECellTypeEmbedding with mocked circuit."""
    with patch('quantum_celltype_fidelity.embeddings.QuCoWECircuit', return_value=mock_circuit):
        return QuCoWECellTypeEmbedding(
            cell_types=["T_cell", "B_cell", "NK_cell"],
            n_qubits=8,
            n_layers=3,
            feature_dim=256
        )


def test_embedding_initialization(embedding):
    """Test embedding initialization."""
    assert len(embedding.cell_types) == 3
    assert "T_cell" in embedding.cell_types
    assert "B_cell" in embedding.cell_types
    assert "NK_cell" in embedding.cell_types
    assert embedding.feature_dim == 256
    assert embedding.backend == "cpu"


def test_theta_dict_initialization(embedding):
    """Test that variational parameters are initialized for all cell types."""
    assert len(embedding.theta_dict) == 3
    for cell_type in embedding.cell_types:
        assert cell_type in embedding.theta_dict
        theta = embedding.theta_dict[cell_type]
        assert len(theta) == 72  # 8 * 3 * 3
        assert np.all((theta >= 0) & (theta <= 2 * np.pi))


def test_get_parameters(embedding):
    """Test getting parameters for a cell type."""
    theta = embedding.get_parameters("T_cell")
    assert isinstance(theta, np.ndarray)
    assert len(theta) == 72


def test_get_parameters_unknown_type(embedding):
    """Test getting parameters for unknown cell type raises error."""
    with pytest.raises(ValueError, match="Unknown cell type"):
        embedding.get_parameters("Unknown_cell")


def test_update_parameters(embedding):
    """Test updating parameters for a cell type."""
    new_theta = np.random.uniform(0, 2 * np.pi, 72)
    embedding.update_parameters("T_cell", new_theta)

    retrieved = embedding.get_parameters("T_cell")
    assert np.allclose(retrieved, new_theta)


def test_update_parameters_wrong_size(embedding):
    """Test updating with wrong parameter size raises error."""
    wrong_size_theta = np.random.uniform(0, 2 * np.pi, 50)

    with pytest.raises(ValueError, match="Expected 72 parameters"):
        embedding.update_parameters("T_cell", wrong_size_theta)


def test_get_all_parameters(embedding):
    """Test getting all parameters."""
    all_params = embedding.get_all_parameters()

    assert len(all_params) == 3
    assert "T_cell" in all_params
    assert "B_cell" in all_params
    assert "NK_cell" in all_params

    for theta in all_params.values():
        assert len(theta) == 72


def test_get_summary(embedding):
    """Test getting summary statistics."""
    summary = embedding.get_summary()

    assert summary["n_cell_types"] == 3
    assert summary["cell_types"] == ["B_cell", "NK_cell", "T_cell"]  # Sorted
    assert summary["n_qubits"] == 8
    assert summary["n_layers"] == 3
    assert summary["feature_dim"] == 256
    assert summary["backend"] == "cpu"
    assert summary["trained"] == False
    assert summary["n_epochs"] == 0


def test_repr(embedding):
    """Test string representation."""
    repr_str = repr(embedding)

    assert "QuCoWECellTypeEmbedding" in repr_str
    assert "n_cell_types=3" in repr_str
    assert "n_qubits=8" in repr_str
    assert "n_layers=3" in repr_str
    assert "feature_dim=256" in repr_str


def test_compute_pairwise_fidelity(embedding, mock_circuit):
    """Test computing fidelity between two cells."""
    features_a = np.random.randn(256)
    features_b = np.random.randn(256)

    mock_circuit.compute_fidelity.return_value = 0.85

    fidelity = embedding.compute_pairwise_fidelity(
        "T_cell", "B_cell",
        features_a, features_b
    )

    assert fidelity == 0.85
    mock_circuit.compute_fidelity.assert_called_once()


def test_compute_pairwise_fidelity_unknown_type(embedding):
    """Test computing fidelity with unknown cell type raises error."""
    features_a = np.random.randn(256)
    features_b = np.random.randn(256)

    with pytest.raises(ValueError, match="Unknown cell type"):
        embedding.compute_pairwise_fidelity(
            "Unknown_cell", "T_cell",
            features_a, features_b
        )


def test_compute_fidelity_matrix(embedding, mock_circuit):
    """Test computing fidelity matrix."""
    # Create test data
    features_dict = {
        "T_cell": [np.random.randn(256) for _ in range(3)],
        "B_cell": [np.random.randn(256) for _ in range(2)]
    }

    # Mock fidelity computation
    mock_circuit.compute_fidelity.return_value = 0.75

    matrix = embedding.compute_fidelity_matrix(features_dict)

    assert matrix.shape == (5, 5)  # 3 + 2 cells
    assert np.all((matrix >= 0) & (matrix <= 1))
    # Matrix should be symmetric
    assert np.allclose(matrix, matrix.T)


def test_training_metadata(embedding):
    """Test training metadata initialization."""
    metadata = embedding.training_metadata

    assert metadata["trained"] == False
    assert metadata["n_epochs"] == 0
    assert isinstance(metadata["loss_history"], list)
    assert len(metadata["loss_history"]) == 0


def test_save_and_load(embedding, tmp_path):
    """Test saving and loading embeddings."""
    save_path = tmp_path / "test_embedding"

    # Modify some parameters
    new_theta = np.random.uniform(0, 2 * np.pi, 72)
    embedding.update_parameters("T_cell", new_theta)

    # Save
    embedding.save(str(save_path))

    # Check files exist
    assert (save_path / "circuit_config.json").exists()
    assert (save_path / "cell_types.json").exists()
    assert (save_path / "theta_T_cell.npy").exists()
    assert (save_path / "theta_B_cell.npy").exists()
    assert (save_path / "theta_NK_cell.npy").exists()
    assert (save_path / "training_metadata.json").exists()

    # Load
    with patch('quantum_celltype_fidelity.embeddings.QuCoWECircuit', return_value=embedding.circuit):
        loaded = QuCoWECellTypeEmbedding.load(str(save_path))

    assert loaded.cell_types == embedding.cell_types
    assert np.allclose(
        loaded.get_parameters("T_cell"),
        embedding.get_parameters("T_cell")
    )
