"""Quantum circuit implementations for cell type embeddings.

Uses Qiskit to build parameterized quantum circuits (PQCs) for encoding
cell type features into quantum states for fidelity-based analysis.
"""

import numpy as np
from typing import Optional, List, Dict, Any
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, ParameterVector
from qiskit.quantum_info import Statevector


class QuCoWECircuit:
    """Quantum Contrastive Word Embedding (QuCoWE) style circuit for cell types.

    Implements a parameterized quantum circuit that encodes cell type features
    (gene expression vectors) into quantum states. The circuit consists of:
    1. Feature encoding layer (amplitude encoding)
    2. Variational layers with parameterized rotation gates
    3. Ring entanglement for capturing spatial relationships

    Attributes:
        n_qubits: Number of qubits (determines embedding dimension 2^n_qubits)
        n_layers: Number of variational layers
        feature_dim: Dimension of input feature vectors
        circuit: The Qiskit QuantumCircuit
        feature_params: Parameters for feature encoding
        theta_params: Variational parameters
    """

    def __init__(
        self,
        n_qubits: int = 8,
        n_layers: int = 3,
        feature_dim: int = 256,
        entanglement: str = "ring"
    ):
        """Initialize QuCoWE circuit.

        Args:
            n_qubits: Number of qubits (default: 8 for 256-dim Hilbert space)
            n_layers: Number of variational layers (default: 3)
            feature_dim: Dimension of input gene expression vectors
            entanglement: Entanglement pattern ("ring", "full", "linear")
        """
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.feature_dim = feature_dim
        self.entanglement = entanglement

        # Hilbert space dimension
        self.hilbert_dim = 2 ** n_qubits

        # Create parameter vectors
        # Feature encoding: one parameter per qubit for amplitude encoding
        self.feature_params = ParameterVector('x', n_qubits)

        # Variational parameters: 3 rotation angles per qubit per layer
        self.theta_params = ParameterVector(
            'θ',
            n_qubits * 3 * n_layers  # RX, RY, RZ per qubit per layer
        )

        # Build the circuit
        self.circuit = self._build_circuit()

    def _build_circuit(self) -> QuantumCircuit:
        """Build the parameterized quantum circuit.

        Returns:
            Qiskit QuantumCircuit with feature encoding and variational layers
        """
        qc = QuantumCircuit(self.n_qubits)

        # Layer 1: Feature encoding (amplitude encoding via rotations)
        for i in range(self.n_qubits):
            qc.ry(self.feature_params[i], i)

        # Variational layers
        for layer in range(self.n_layers):
            # Parameterized rotations
            for qubit in range(self.n_qubits):
                param_idx = layer * (self.n_qubits * 3) + qubit * 3
                qc.rx(self.theta_params[param_idx], qubit)
                qc.ry(self.theta_params[param_idx + 1], qubit)
                qc.rz(self.theta_params[param_idx + 2], qubit)

            # Entanglement layer
            if self.entanglement == "ring":
                for i in range(self.n_qubits):
                    qc.cx(i, (i + 1) % self.n_qubits)
            elif self.entanglement == "full":
                for i in range(self.n_qubits):
                    for j in range(i + 1, self.n_qubits):
                        qc.cx(i, j)
            elif self.entanglement == "linear":
                for i in range(self.n_qubits - 1):
                    qc.cx(i, i + 1)

        return qc

    def encode_features(self, features: np.ndarray) -> np.ndarray:
        """Encode high-dimensional features to qubit rotation angles.

        Uses PCA-style dimensionality reduction followed by normalization
        to map feature_dim -> n_qubits rotation angles.

        Args:
            features: Gene expression vector (feature_dim,)

        Returns:
            Encoded angles (n_qubits,) in range [0, 2π]
        """
        # Normalize features
        features = np.array(features)
        if features.shape[0] != self.feature_dim:
            raise ValueError(
                f"Expected features of dim {self.feature_dim}, got {features.shape[0]}"
            )

        # Simple dimensionality reduction: chunk averaging
        chunk_size = self.feature_dim // self.n_qubits
        encoded = []
        for i in range(self.n_qubits):
            start = i * chunk_size
            end = start + chunk_size if i < self.n_qubits - 1 else self.feature_dim
            chunk_mean = np.mean(features[start:end])
            encoded.append(chunk_mean)

        encoded = np.array(encoded)

        # Normalize to [0, 2π] using arctan scaling
        encoded = np.arctan(encoded) + np.pi / 2  # Maps to [0, π]
        encoded = encoded * 2  # Scale to [0, 2π]

        return encoded

    def bind_parameters(
        self,
        features: np.ndarray,
        theta: Optional[np.ndarray] = None
    ) -> QuantumCircuit:
        """Bind feature and variational parameters to circuit.

        Args:
            features: Gene expression features (feature_dim,)
            theta: Variational parameters (n_qubits * 3 * n_layers,)
                   If None, initializes randomly

        Returns:
            Bound QuantumCircuit ready for simulation
        """
        # Encode features to rotation angles
        encoded_features = self.encode_features(features)

        # Initialize theta if not provided
        if theta is None:
            theta = np.random.uniform(0, 2 * np.pi, len(self.theta_params))

        # Create parameter binding dictionary
        param_dict = {}
        for i, param in enumerate(self.feature_params):
            param_dict[param] = encoded_features[i]
        for i, param in enumerate(self.theta_params):
            param_dict[param] = theta[i]

        # Bind and return
        return self.circuit.assign_parameters(param_dict)

    def get_statevector(
        self,
        features: np.ndarray,
        theta: Optional[np.ndarray] = None,
        backend: str = "cpu"
    ) -> np.ndarray:
        """Get quantum state vector for given features.

        Args:
            features: Gene expression features (feature_dim,)
            theta: Variational parameters
            backend: Simulation backend ("cpu", "gpu", "mps", or "ibm")

        Returns:
            Complex state vector (2^n_qubits,)
        """
        # Bind parameters
        bound_circuit = self.bind_parameters(features, theta)

        # Simulate based on backend
        if backend == "cpu":
            # Use Qiskit Aer C++ multi-threaded statevector simulator
            from qiskit_aer import AerSimulator
            sim_circuit = bound_circuit.copy()
            sim_circuit.save_statevector()
            simulator = AerSimulator(method='statevector')
            result = simulator.run(sim_circuit).result()
            return np.array(result.get_statevector())

        elif backend == "gpu":
            # Use cuStateVec (requires CUDA + cuQuantum)
            try:
                from qiskit_aer import AerSimulator
                sim_circuit = bound_circuit.copy()
                sim_circuit.save_statevector()
                simulator = AerSimulator(method='statevector', device='GPU')
                result = simulator.run(sim_circuit).result()
                return np.array(result.get_statevector())
            except ImportError:
                raise ImportError(
                    "GPU backend requires qiskit-aer with cuQuantum. "
                    "Install with: pip install qiskit-aer-gpu"
                )

        elif backend == "mps":
            # Apple Silicon Metal Performance Shaders via PyTorch
            try:
                import torch
            except ImportError:
                raise ImportError(
                    "MPS backend requires PyTorch. "
                    "Install with: pip install torch"
                )
            if not torch.backends.mps.is_available():
                raise RuntimeError(
                    "MPS backend not available on this device. "
                    "Requires Apple Silicon (M1/M2/M3/M4) with macOS 12.3+."
                )
            from qiskit.quantum_info import Operator
            unitary = Operator(bound_circuit).data
            initial_state = np.zeros(2 ** self.n_qubits, dtype=np.complex64)
            initial_state[0] = 1.0
            device = torch.device("mps")
            u_tensor = torch.tensor(unitary, dtype=torch.complex64, device=device)
            s_tensor = torch.tensor(initial_state, dtype=torch.complex64, device=device)
            result = torch.matmul(u_tensor, s_tensor)
            return result.cpu().numpy()

        elif backend == "ibm":
            # IBM Quantum hardware (requires API token)
            raise NotImplementedError(
                "IBM Quantum hardware execution not yet implemented. "
                "Use backend='cpu', 'gpu', or 'mps' for simulation."
            )

        else:
            raise ValueError(f"Unknown backend: {backend}")

    def compute_fidelity(
        self,
        features_a: np.ndarray,
        features_b: np.ndarray,
        theta_a: Optional[np.ndarray] = None,
        theta_b: Optional[np.ndarray] = None,
        backend: str = "cpu"
    ) -> float:
        """Compute quantum fidelity between two cell type states.

        Fidelity F(|ψ_a⟩, |ψ_b⟩) = |⟨ψ_a|ψ_b⟩|²

        Args:
            features_a: Features for cell type A
            features_b: Features for cell type B
            theta_a: Variational parameters for A (if None, use same as B)
            theta_b: Variational parameters for B
            backend: Simulation backend

        Returns:
            Fidelity score in [0, 1]
        """
        # If theta_a not provided, use same parameters for both
        # (useful for comparing different cell types with same learned embedding)
        if theta_a is None:
            theta_a = theta_b

        # Get statevectors
        psi_a = self.get_statevector(features_a, theta_a, backend)
        psi_b = self.get_statevector(features_b, theta_b, backend)

        # Compute fidelity: |⟨ψ_a|ψ_b⟩|²
        inner_product = np.vdot(psi_a, psi_b)
        fidelity = np.abs(inner_product) ** 2

        return float(fidelity)

    def get_parameter_count(self) -> Dict[str, int]:
        """Get counts of different parameter types.

        Returns:
            Dictionary with parameter counts
        """
        return {
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers,
            "feature_params": len(self.feature_params),
            "variational_params": len(self.theta_params),
            "total_params": len(self.feature_params) + len(self.theta_params),
            "hilbert_dim": self.hilbert_dim
        }

    def visualize(self) -> str:
        """Get text representation of the circuit.

        Returns:
            Circuit diagram as string
        """
        return str(self.circuit.draw(output='text'))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize circuit configuration to dictionary.

        Returns:
            Dictionary with circuit configuration
        """
        return {
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers,
            "feature_dim": self.feature_dim,
            "entanglement": self.entanglement,
            "hilbert_dim": self.hilbert_dim,
            "parameter_counts": self.get_parameter_count()
        }

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "QuCoWECircuit":
        """Load circuit from configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            QuCoWECircuit instance
        """
        return cls(
            n_qubits=config["n_qubits"],
            n_layers=config["n_layers"],
            feature_dim=config["feature_dim"],
            entanglement=config.get("entanglement", "ring")
        )
