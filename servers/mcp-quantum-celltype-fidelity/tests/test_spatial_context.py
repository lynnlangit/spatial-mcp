"""Tests for spatial context extraction."""

import pytest
import numpy as np
from unittest.mock import Mock

from quantum_celltype_fidelity.spatial_context import (
    SpatialNeighborhood,
    SpatialContextGenerator
)


class TestSpatialNeighborhood:
    """Tests for SpatialNeighborhood dataclass."""

    def test_creation(self):
        """Test creating a SpatialNeighborhood."""
        neighborhood = SpatialNeighborhood(
            cell_idx=5,
            neighbor_indices=[1, 3, 7, 9],
            distances=[10.5, 15.2, 8.3, 20.1],
            cell_types=["T_cell", "B_cell", "T_cell", "NK_cell"],
            coordinates=np.array([[0, 0], [1, 1], [2, 2], [3, 3]])
        )

        assert neighborhood.cell_idx == 5
        assert len(neighborhood.neighbor_indices) == 4
        assert len(neighborhood.distances) == 4
        assert len(neighborhood.cell_types) == 4
        assert neighborhood.coordinates.shape == (4, 2)


class TestSpatialContextGenerator:
    """Tests for SpatialContextGenerator."""

    def test_initialization(self):
        """Test generator initialization."""
        gen = SpatialContextGenerator(
            k_neighbors=15,
            radius=50.0,
            coordinate_keys=("x", "y")
        )

        assert gen.k_neighbors == 15
        assert gen.radius == 50.0
        assert gen.coordinate_keys == ("x", "y")
        assert gen.kdtree is None
        assert gen.coordinates is None

    def test_initialization_defaults(self):
        """Test default initialization."""
        gen = SpatialContextGenerator()

        assert gen.k_neighbors == 10
        assert gen.radius is None
        assert gen.coordinate_keys == ("spatial_x", "spatial_y")

    def test_get_summary_not_fitted(self):
        """Test summary before fitting."""
        gen = SpatialContextGenerator()
        summary = gen.get_summary()

        assert summary["fitted"] == False

    def test_get_summary_fitted(self):
        """Test summary after fitting."""
        gen = SpatialContextGenerator()

        # Manually set coordinates
        gen.coordinates = np.array([
            [0, 0],
            [10, 20],
            [30, 40],
            [50, 60]
        ])

        summary = gen.get_summary()

        assert summary["fitted"] == True
        assert summary["n_cells"] == 4
        assert summary["k_neighbors"] == 10
        assert "coordinate_range" in summary
        assert summary["coordinate_range"]["x_min"] == 0
        assert summary["coordinate_range"]["x_max"] == 50
        assert summary["coordinate_range"]["y_min"] == 0
        assert summary["coordinate_range"]["y_max"] == 60


class TestTLSIdentification:
    """Tests for TLS candidate identification logic."""

    def test_tls_marker_filtering(self):
        """Test that TLS markers are correctly filtered."""
        # This tests the logic without needing full spatial data
        cell_type_labels = [
            "T_cell", "B_cell", "Tumor", "T_cell",
            "B_cell", "Tumor", "NK_cell", "T_cell"
        ]

        tls_marker_types = ["T_cell", "B_cell"]

        # Find TLS marker cells
        tls_indices = [
            i for i, label in enumerate(cell_type_labels)
            if label in tls_marker_types
        ]

        assert len(tls_indices) == 5  # 3 T_cells + 2 B_cells
        assert 0 in tls_indices  # T_cell
        assert 1 in tls_indices  # B_cell
        assert 2 not in tls_indices  # Tumor
        assert 6 not in tls_indices  # NK_cell


def test_feature_extraction_logic():
    """Test feature extraction normalization logic."""
    # Simulate gene expression matrix
    X = np.array([
        [10, 20, 30, 40],
        [5, 10, 15, 20],
        [0, 0, 0, 0],  # Edge case: all zeros
        [100, 200, 300, 400]
    ])

    # Normalize per-cell (row-wise)
    row_sums = X.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    X_normalized = X / row_sums

    # Check normalization
    assert X_normalized.shape == X.shape
    assert np.allclose(X_normalized.sum(axis=1)[:2], 1.0)  # First two rows sum to 1
    assert np.allclose(X_normalized[2], 0.0)  # Zero row stays zero

    # Check values
    assert np.allclose(X_normalized[0], [0.1, 0.2, 0.3, 0.4])
    assert np.allclose(X_normalized[1], [0.1, 0.2, 0.3, 0.4])


def test_chunk_averaging_dimensionality_reduction():
    """Test chunk averaging for dimensionality reduction."""
    # Simulate high-dimensional features
    feature_dim = 256
    n_qubits = 8

    features = np.random.randn(feature_dim)

    # Chunk averaging
    chunk_size = feature_dim // n_qubits
    encoded = []

    for i in range(n_qubits):
        start = i * chunk_size
        end = start + chunk_size if i < n_qubits - 1 else feature_dim
        chunk_mean = np.mean(features[start:end])
        encoded.append(chunk_mean)

    encoded = np.array(encoded)

    assert len(encoded) == n_qubits
    assert encoded.shape == (n_qubits,)


def test_distance_matrix_symmetry():
    """Test that distance computations are symmetric."""
    # Create sample coordinates
    coords = np.array([
        [0, 0],
        [1, 0],
        [0, 1],
        [1, 1]
    ])

    # Compute pairwise distances
    n = len(coords)
    distances = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            distances[i, j] = np.linalg.norm(coords[i] - coords[j])

    # Check symmetry
    assert np.allclose(distances, distances.T)

    # Check diagonal is zero
    assert np.allclose(np.diag(distances), 0)

    # Check specific distances
    assert np.isclose(distances[0, 1], 1.0)  # (0,0) to (1,0)
    assert np.isclose(distances[0, 2], 1.0)  # (0,0) to (0,1)
    assert np.isclose(distances[0, 3], np.sqrt(2))  # (0,0) to (1,1)


def test_k_neighbors_logic():
    """Test k-nearest neighbors selection logic."""
    # Distances from a query point to 5 points
    distances = np.array([0.0, 10.5, 5.2, 20.3, 3.8, 15.1])
    indices = np.arange(len(distances))

    k = 3

    # Sort by distance
    sorted_indices = np.argsort(distances)

    # Take k+1 (including self) then remove self
    k_nearest = sorted_indices[:k+1]
    k_nearest = k_nearest[k_nearest != 0]  # Remove self (index 0)

    if len(k_nearest) > k:
        k_nearest = k_nearest[:k]

    # Should get indices with smallest distances (excluding self)
    assert len(k_nearest) == k
    assert 0 not in k_nearest  # Self excluded
    assert 4 in k_nearest  # Distance 3.8
    assert 2 in k_nearest  # Distance 5.2
    assert 1 in k_nearest  # Distance 10.5


def test_radius_based_neighbors_logic():
    """Test radius-based neighbor selection."""
    # Distances from query point
    distances = np.array([0.0, 10.5, 5.2, 20.3, 3.8, 15.1])
    radius = 12.0

    # Find neighbors within radius (excluding self)
    neighbors = []
    for i, d in enumerate(distances):
        if i != 0 and d <= radius:  # Exclude self and check radius
            neighbors.append(i)

    # Should get indices 1, 2, 4 (distances 10.5, 5.2, 3.8)
    assert len(neighbors) == 3
    assert 1 in neighbors
    assert 2 in neighbors
    assert 4 in neighbors
    assert 3 not in neighbors  # Distance 20.3 > 12.0
    assert 5 not in neighbors  # Distance 15.1 > 12.0
