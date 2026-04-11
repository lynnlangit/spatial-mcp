"""Cell type embedding management using quantum circuits.

Manages quantum embeddings for multiple cell types, including
parameter storage, training state, and fidelity computations.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path

from .circuits import QuCoWECircuit


class QuCoWECellTypeEmbedding:
    """Manages quantum embeddings for all cell types in a spatial dataset.

    Maintains:
    - One shared QuCoWECircuit architecture
    - Per-cell-type variational parameters (theta)
    - Training state and metadata
    - Fidelity computation interface

    Attributes:
        circuit: Shared QuCoWECircuit for all cell types
        cell_types: List of cell type names
        theta_dict: Dict mapping cell_type -> variational parameters
        feature_dim: Dimension of input gene expression features
        backend: Simulation backend ("cpu", "gpu", "mps", "ibm")
    """

    def __init__(
        self,
        cell_types: List[str],
        n_qubits: int = 8,
        n_layers: int = 3,
        feature_dim: int = 256,
        entanglement: str = "ring",
        backend: str = "cpu"
    ):
        """Initialize embeddings for multiple cell types.

        Args:
            cell_types: List of cell type names (e.g., ["T_cell", "B_cell", ...])
            n_qubits: Number of qubits in circuit
            n_layers: Number of variational layers
            feature_dim: Dimension of input features
            entanglement: Entanglement pattern
            backend: Simulation backend
        """
        self.cell_types = sorted(cell_types)  # Sort for consistency
        self.feature_dim = feature_dim
        self.backend = backend

        # Create shared circuit architecture
        self.circuit = QuCoWECircuit(
            n_qubits=n_qubits,
            n_layers=n_layers,
            feature_dim=feature_dim,
            entanglement=entanglement
        )

        # Initialize variational parameters for each cell type
        n_params = len(self.circuit.theta_params)
        self.theta_dict: Dict[str, np.ndarray] = {
            cell_type: np.random.uniform(0, 2 * np.pi, n_params)
            for cell_type in self.cell_types
        }

        # Training metadata
        self.training_metadata: Dict[str, Any] = {
            "trained": False,
            "n_epochs": 0,
            "loss_history": [],
            "fidelity_stats": {}
        }

    def get_embedding_for_cell_type(
        self,
        cell_type: str,
        features: np.ndarray
    ) -> np.ndarray:
        """Get quantum state vector for a specific cell type.

        Args:
            cell_type: Name of cell type
            features: Gene expression features (feature_dim,)

        Returns:
            Complex state vector (2^n_qubits,)
        """
        if cell_type not in self.theta_dict:
            raise ValueError(f"Unknown cell type: {cell_type}")

        theta = self.theta_dict[cell_type]
        return self.circuit.get_statevector(features, theta, self.backend)

    def compute_pairwise_fidelity(
        self,
        cell_type_a: str,
        cell_type_b: str,
        features_a: np.ndarray,
        features_b: np.ndarray
    ) -> float:
        """Compute fidelity between two cell instances.

        Args:
            cell_type_a: Cell type label for instance A
            cell_type_b: Cell type label for instance B
            features_a: Gene expression for instance A
            features_b: Gene expression for instance B

        Returns:
            Fidelity score in [0, 1]
        """
        if cell_type_a not in self.theta_dict:
            raise ValueError(f"Unknown cell type: {cell_type_a}")
        if cell_type_b not in self.theta_dict:
            raise ValueError(f"Unknown cell type: {cell_type_b}")

        theta_a = self.theta_dict[cell_type_a]
        theta_b = self.theta_dict[cell_type_b]

        return self.circuit.compute_fidelity(
            features_a, features_b,
            theta_a, theta_b,
            self.backend
        )

    def compute_fidelity_matrix(
        self,
        features_dict: Dict[str, List[np.ndarray]]
    ) -> np.ndarray:
        """Compute all pairwise fidelities for cell instances.

        Args:
            features_dict: Dict mapping cell_type -> list of feature vectors

        Returns:
            Fidelity matrix (n_cells, n_cells)
        """
        # Flatten to list of (cell_type, features) tuples
        cell_list = []
        for cell_type, features_list in features_dict.items():
            for features in features_list:
                cell_list.append((cell_type, features))

        n_cells = len(cell_list)
        fidelity_matrix = np.zeros((n_cells, n_cells))

        # Compute pairwise fidelities
        for i in range(n_cells):
            for j in range(i, n_cells):
                cell_type_i, features_i = cell_list[i]
                cell_type_j, features_j = cell_list[j]

                fidelity = self.compute_pairwise_fidelity(
                    cell_type_i, cell_type_j,
                    features_i, features_j
                )

                fidelity_matrix[i, j] = fidelity
                fidelity_matrix[j, i] = fidelity  # Symmetric

        return fidelity_matrix

    def update_parameters(
        self,
        cell_type: str,
        new_theta: np.ndarray
    ) -> None:
        """Update variational parameters for a cell type.

        Args:
            cell_type: Cell type name
            new_theta: New variational parameters
        """
        if cell_type not in self.theta_dict:
            raise ValueError(f"Unknown cell type: {cell_type}")

        expected_len = len(self.circuit.theta_params)
        if len(new_theta) != expected_len:
            raise ValueError(
                f"Expected {expected_len} parameters, got {len(new_theta)}"
            )

        self.theta_dict[cell_type] = np.array(new_theta)

    def get_parameters(self, cell_type: str) -> np.ndarray:
        """Get current variational parameters for a cell type.

        Args:
            cell_type: Cell type name

        Returns:
            Variational parameters
        """
        if cell_type not in self.theta_dict:
            raise ValueError(f"Unknown cell type: {cell_type}")
        return self.theta_dict[cell_type].copy()

    def get_all_parameters(self) -> Dict[str, np.ndarray]:
        """Get all variational parameters.

        Returns:
            Dictionary mapping cell_type -> parameters
        """
        return {ct: theta.copy() for ct, theta in self.theta_dict.items()}

    def save(self, path: str) -> None:
        """Save embeddings to disk.

        Args:
            path: Directory path to save to
        """
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)

        # Save circuit configuration
        circuit_config = self.circuit.to_dict()
        with open(path_obj / "circuit_config.json", "w") as f:
            json.dump(circuit_config, f, indent=2)

        # Save cell types
        with open(path_obj / "cell_types.json", "w") as f:
            json.dump(self.cell_types, f, indent=2)

        # Save variational parameters
        for cell_type, theta in self.theta_dict.items():
            np.save(
                path_obj / f"theta_{cell_type}.npy",
                theta
            )

        # Save training metadata
        with open(path_obj / "training_metadata.json", "w") as f:
            # Convert numpy types to Python types for JSON serialization
            metadata_serializable = {
                k: (v.tolist() if isinstance(v, np.ndarray) else v)
                for k, v in self.training_metadata.items()
            }
            json.dump(metadata_serializable, f, indent=2)

        print(f"Saved embeddings to {path}")

    @classmethod
    def load(cls, path: str, backend: str = "cpu") -> "QuCoWECellTypeEmbedding":
        """Load embeddings from disk.

        Args:
            path: Directory path to load from
            backend: Simulation backend to use

        Returns:
            Loaded QuCoWECellTypeEmbedding instance
        """
        path_obj = Path(path)

        # Load circuit configuration
        with open(path_obj / "circuit_config.json", "r") as f:
            circuit_config = json.load(f)

        # Load cell types
        with open(path_obj / "cell_types.json", "r") as f:
            cell_types = json.load(f)

        # Create instance
        instance = cls(
            cell_types=cell_types,
            n_qubits=circuit_config["n_qubits"],
            n_layers=circuit_config["n_layers"],
            feature_dim=circuit_config["feature_dim"],
            entanglement=circuit_config["entanglement"],
            backend=backend
        )

        # Load variational parameters
        for cell_type in cell_types:
            theta_path = path_obj / f"theta_{cell_type}.npy"
            if theta_path.exists():
                instance.theta_dict[cell_type] = np.load(theta_path)

        # Load training metadata
        metadata_path = path_obj / "training_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                instance.training_metadata = json.load(f)

        print(f"Loaded embeddings from {path}")
        return instance

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the embeddings.

        Returns:
            Dictionary with summary information
        """
        return {
            "n_cell_types": len(self.cell_types),
            "cell_types": self.cell_types,
            "n_qubits": self.circuit.n_qubits,
            "n_layers": self.circuit.n_layers,
            "feature_dim": self.feature_dim,
            "hilbert_dim": self.circuit.hilbert_dim,
            "n_params_per_cell_type": len(self.circuit.theta_params),
            "total_params": len(self.cell_types) * len(self.circuit.theta_params),
            "backend": self.backend,
            "trained": self.training_metadata.get("trained", False),
            "n_epochs": self.training_metadata.get("n_epochs", 0)
        }

    def __repr__(self) -> str:
        """String representation."""
        summary = self.get_summary()
        return (
            f"QuCoWECellTypeEmbedding(\n"
            f"  n_cell_types={summary['n_cell_types']},\n"
            f"  n_qubits={summary['n_qubits']},\n"
            f"  n_layers={summary['n_layers']},\n"
            f"  feature_dim={summary['feature_dim']},\n"
            f"  total_params={summary['total_params']},\n"
            f"  trained={summary['trained']}\n"
            f")"
        )
