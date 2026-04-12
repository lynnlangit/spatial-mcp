"""Quantum circuit implementations for cell type embeddings.

Uses Qiskit to build parameterized quantum circuits (PQCs) for encoding
cell type features into quantum states for fidelity-based analysis.
"""

import os
import warnings

import numpy as np
from typing import Optional, List, Dict, Any
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, ParameterVector


def _has_cuda_gpu() -> bool:
    """Check if an NVIDIA CUDA GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def _build_simulator(backend: str):
    """Return the best available AerSimulator for the requested backend.

    - "cpu": Qiskit Aer statevector with max_parallel_threads (auto-detected).
    - "gpu"/"mps": NVIDIA CUDA via cuStateVec if available. On Apple Silicon,
      falls back to multi-threaded CPU with a warning.

    Args:
        backend: One of "cpu", "gpu", "mps".

    Returns:
        Configured AerSimulator instance.
    """
    from qiskit_aer import AerSimulator

    if backend in ("gpu", "mps"):
        # NVIDIA CUDA path
        if _has_cuda_gpu():
            return AerSimulator(
                method="statevector",
                device="GPU",
                cuStateVec_enable=True,
            )
        # Apple Silicon path — AerSimulator itself runs on CPU with parallelism
        _is_apple_silicon = False
        try:
            import torch
            _is_apple_silicon = torch.backends.mps.is_available()
        except ImportError:
            pass

        if _is_apple_silicon:
            warnings.warn(
                "Apple Silicon detected: AerSimulator does not support Metal GPU "
                "natively. Using CPU statevector with max_parallel_threads. "
                "For true GPU acceleration, use an NVIDIA GPU with cuStateVec.",
                RuntimeWarning,
                stacklevel=3,
            )
            # Fall through to CPU with max threads
        else:
            raise RuntimeError(
                f"backend='{backend}' requested but no compatible GPU found.\n"
                "  NVIDIA: install qiskit-aer-gpu and cuQuantum\n"
                "  Apple Silicon: install torch for MPS detection (falls back to CPU)\n"
                "  Use backend='cpu' to suppress this error."
            )

    # CPU path (default and Apple Silicon fallback)
    n_threads = min(8, os.cpu_count() or 1)
    return AerSimulator(
        method="statevector",
        max_parallel_threads=n_threads,
        max_parallel_experiments=1,
        statevector_parallel_threshold=4,
    )


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
            backend: Simulation backend.
                - "cpu": Qiskit Aer statevector with max_parallel_threads
                         (auto-detected, up to 8 threads).
                - "gpu": NVIDIA CUDA via cuStateVec if available.
                         On Apple Silicon, falls back to multi-threaded CPU
                         with a warning (Aer does not support Metal natively).
                - "mps": Alias for "gpu" on Apple Silicon (CPU fallback).
                - "ibm": IBM Quantum cloud (requires IBMQ credentials).

        Returns:
            Complex state vector (2^n_qubits,)
        """
        if backend == "ibm":
            raise NotImplementedError(
                "IBM Quantum hardware execution not yet implemented. "
                "Use backend='cpu', 'gpu', or 'mps' for simulation."
            )

        if backend not in ("cpu", "gpu", "mps"):
            raise ValueError(f"Unknown backend: {backend}")

        # Bind parameters and prepare circuit for simulation
        bound_circuit = self.bind_parameters(features, theta)
        sim_circuit = bound_circuit.copy()

        # Append SaveStatevector instruction (explicit import avoids
        # relying on qiskit-aer monkey-patching of QuantumCircuit)
        from qiskit_aer.library import SaveStatevector
        sim_circuit.append(
            SaveStatevector(sim_circuit.num_qubits),
            list(range(sim_circuit.num_qubits)),
        )

        simulator = _build_simulator(backend)
        result = simulator.run(sim_circuit).result()
        return np.array(result.get_statevector())

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
