"""Training loop with parameter-shift rule for gradient estimation.

Implements contrastive learning for quantum cell type embeddings
using parameter-shift rule for computing gradients on quantum circuits.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
import time

from .circuits import QuCoWECircuit
from .embeddings import QuCoWECellTypeEmbedding
from .fidelity import FidelityScore


@dataclass
class TrainingConfig:
    """Configuration for training quantum embeddings.

    Attributes:
        n_epochs: Number of training epochs
        learning_rate: Learning rate for parameter updates
        batch_size: Number of cell pairs per batch
        contrastive_margin: Margin for contrastive loss
        shift_amount: Shift amount for parameter-shift rule (π/2)
        optimizer: Optimizer type ("sgd", "adam")
        temperature: Temperature for InfoNCE loss
        negative_samples: Number of negative samples per positive
    """
    n_epochs: int = 100
    learning_rate: float = 0.01
    batch_size: int = 32
    contrastive_margin: float = 0.5
    shift_amount: float = np.pi / 2
    optimizer: str = "sgd"
    temperature: float = 0.1
    negative_samples: int = 5


class ParameterShiftGradientEstimator:
    """Estimate gradients using parameter-shift rule.

    For a parameterized quantum circuit, the gradient of an expectation
    value with respect to a parameter θ can be computed as:

    ∂f/∂θ = [f(θ + π/2) - f(θ - π/2)] / 2

    This avoids backpropagation and works on real quantum hardware.
    """

    def __init__(self, shift_amount: float = np.pi / 2):
        """Initialize gradient estimator.

        Args:
            shift_amount: Parameter shift amount (default: π/2)
        """
        self.shift_amount = shift_amount

    def estimate_gradient(
        self,
        loss_fn: Callable[[np.ndarray], float],
        params: np.ndarray,
        param_idx: int
    ) -> float:
        """Estimate gradient for a single parameter.

        Args:
            loss_fn: Loss function that takes parameters and returns scalar loss
            params: Current parameter values
            param_idx: Index of parameter to compute gradient for

        Returns:
            Estimated gradient value
        """
        # Shift parameter forward
        params_plus = params.copy()
        params_plus[param_idx] += self.shift_amount
        loss_plus = loss_fn(params_plus)

        # Shift parameter backward
        params_minus = params.copy()
        params_minus[param_idx] -= self.shift_amount
        loss_minus = loss_fn(params_minus)

        # Compute gradient
        gradient = (loss_plus - loss_minus) / 2.0

        return gradient

    def estimate_full_gradient(
        self,
        loss_fn: Callable[[np.ndarray], float],
        params: np.ndarray
    ) -> np.ndarray:
        """Estimate gradient for all parameters.

        Args:
            loss_fn: Loss function
            params: Current parameter values

        Returns:
            Gradient vector (same shape as params)
        """
        gradients = np.zeros_like(params)

        for i in range(len(params)):
            gradients[i] = self.estimate_gradient(loss_fn, params, i)

        return gradients


class QuCoWETrainer:
    """Train quantum cell type embeddings with contrastive learning.

    Uses parameter-shift rule for gradient estimation and contrastive
    loss to learn embeddings where:
    - High fidelity between same cell type
    - Low fidelity between different cell types
    """

    def __init__(
        self,
        embedding: QuCoWECellTypeEmbedding,
        config: Optional[TrainingConfig] = None
    ):
        """Initialize trainer.

        Args:
            embedding: QuCoWECellTypeEmbedding to train
            config: Training configuration (uses defaults if None)
        """
        self.embedding = embedding
        self.config = config or TrainingConfig()
        self.gradient_estimator = ParameterShiftGradientEstimator(
            shift_amount=self.config.shift_amount
        )

        # Training state
        self.loss_history: List[float] = []
        self.current_epoch = 0

        # Gradient history for Bayesian UQ
        self.gradient_history: Dict[str, List[np.ndarray]] = {
            ct: [] for ct in self.embedding.cell_types
        }
        self.track_gradients = True  # Enable gradient tracking for UQ

        # Optimizer state (for Adam)
        self.optimizer_state: Dict[str, Any] = {}
        if self.config.optimizer == "adam":
            self._init_adam_state()

    def _init_adam_state(self):
        """Initialize Adam optimizer state."""
        n_params = len(self.embedding.circuit.theta_params)
        self.optimizer_state = {
            "m": {ct: np.zeros(n_params) for ct in self.embedding.cell_types},
            "v": {ct: np.zeros(n_params) for ct in self.embedding.cell_types},
            "beta1": 0.9,
            "beta2": 0.999,
            "epsilon": 1e-8,
            "t": 0
        }

    def contrastive_loss(
        self,
        fidelity_positive: float,
        fidelity_negative: float
    ) -> float:
        """Compute contrastive loss for a pair.

        Loss encourages:
        - High fidelity for positive pairs (same cell type)
        - Low fidelity for negative pairs (different cell types)

        Args:
            fidelity_positive: Fidelity for positive pair
            fidelity_negative: Fidelity for negative pair

        Returns:
            Contrastive loss value
        """
        # We want: fidelity_pos > fidelity_neg + margin
        # Loss = max(0, margin + fidelity_neg - fidelity_pos)
        loss = max(0.0, self.config.contrastive_margin + fidelity_negative - fidelity_positive)
        return loss

    def infonce_loss(
        self,
        fidelity_positive: float,
        fidelities_negative: List[float]
    ) -> float:
        """Compute InfoNCE (contrastive) loss.

        More stable than margin-based contrastive loss.

        Args:
            fidelity_positive: Fidelity for positive pair
            fidelities_negative: Fidelities for negative pairs

        Returns:
            InfoNCE loss
        """
        # Convert fidelities to logits with temperature
        logit_pos = fidelity_positive / self.config.temperature

        logits_neg = [f / self.config.temperature for f in fidelities_negative]

        # Compute log-sum-exp for stability
        all_logits = [logit_pos] + logits_neg
        max_logit = max(all_logits)

        exp_pos = np.exp(logit_pos - max_logit)
        exp_neg_sum = sum(np.exp(l - max_logit) for l in logits_neg)

        # InfoNCE: -log(exp(pos) / (exp(pos) + sum(exp(neg))))
        loss = -np.log(exp_pos / (exp_pos + exp_neg_sum))

        return float(loss)

    def train_epoch(
        self,
        training_data: Dict[str, List[np.ndarray]],
        verbose: bool = True
    ) -> float:
        """Train for one epoch.

        Args:
            training_data: Dict mapping cell_type -> list of feature vectors
            verbose: Whether to print progress

        Returns:
            Average loss for epoch
        """
        epoch_losses = []
        start_time = time.time()

        # Generate batches
        batches = self._generate_batches(training_data)

        for batch_idx, batch in enumerate(batches):
            batch_loss = 0.0

            # Process each example in batch
            for cell_type, features_anchor, features_positive, negatives in batch:
                # Compute fidelity for positive pair
                fidelity_pos = self.embedding.compute_pairwise_fidelity(
                    cell_type, cell_type,
                    features_anchor, features_positive
                )

                # Compute fidelities for negative pairs
                fidelities_neg = []
                for neg_cell_type, features_neg in negatives:
                    fidelity_neg = self.embedding.compute_pairwise_fidelity(
                        cell_type, neg_cell_type,
                        features_anchor, features_neg
                    )
                    fidelities_neg.append(fidelity_neg)

                # Compute loss
                loss = self.infonce_loss(fidelity_pos, fidelities_neg)
                batch_loss += loss

                # Compute gradients and update parameters
                self._update_parameters(
                    cell_type, features_anchor, features_positive, negatives
                )

            # Average loss for batch
            batch_loss /= len(batch)
            epoch_losses.append(batch_loss)

            if verbose and batch_idx % 10 == 0:
                print(f"  Batch {batch_idx}/{len(batches)}, Loss: {batch_loss:.4f}")

        # Average loss for epoch
        avg_loss = np.mean(epoch_losses)
        self.loss_history.append(avg_loss)
        self.current_epoch += 1

        epoch_time = time.time() - start_time

        if verbose:
            print(f"Epoch {self.current_epoch}: Loss={avg_loss:.4f}, Time={epoch_time:.1f}s")

        return avg_loss

    def _generate_batches(
        self,
        training_data: Dict[str, List[np.ndarray]]
    ) -> List[List[Tuple]]:
        """Generate training batches with positive and negative pairs.

        Args:
            training_data: Dict mapping cell_type -> feature vectors

        Returns:
            List of batches, each containing (cell_type, anchor, positive, negatives)
        """
        all_examples = []

        # Generate examples for each cell type
        for cell_type, features_list in training_data.items():
            if len(features_list) < 2:
                continue  # Need at least 2 examples for positive pairs

            # For each example, create anchor-positive pair
            for i, features_anchor in enumerate(features_list):
                # Pick a different example as positive
                j = (i + 1) % len(features_list)
                features_positive = features_list[j]

                # Sample negatives from other cell types
                negatives = []
                other_types = [ct for ct in training_data.keys() if ct != cell_type]

                for _ in range(min(self.config.negative_samples, len(other_types))):
                    # Random negative cell type
                    neg_type = np.random.choice(other_types)
                    # Random example from that type
                    neg_idx = np.random.choice(len(training_data[neg_type]))
                    neg_features = training_data[neg_type][neg_idx]
                    negatives.append((neg_type, neg_features))

                all_examples.append((
                    cell_type,
                    features_anchor,
                    features_positive,
                    negatives
                ))

        # Shuffle and batch
        np.random.shuffle(all_examples)
        batches = [
            all_examples[i:i + self.config.batch_size]
            for i in range(0, len(all_examples), self.config.batch_size)
        ]

        return batches

    def _update_parameters(
        self,
        cell_type: str,
        features_anchor: np.ndarray,
        features_positive: np.ndarray,
        negatives: List[Tuple[str, np.ndarray]]
    ) -> None:
        """Update parameters for one training example.

        Args:
            cell_type: Cell type being updated
            features_anchor: Anchor features
            features_positive: Positive example features
            negatives: List of (cell_type, features) for negatives
        """
        # Get current parameters
        theta = self.embedding.get_parameters(cell_type)

        # Define loss function for this example
        def loss_fn(params):
            # Temporarily set parameters
            old_params = self.embedding.get_parameters(cell_type)
            self.embedding.update_parameters(cell_type, params)

            # Compute fidelities
            fid_pos = self.embedding.compute_pairwise_fidelity(
                cell_type, cell_type,
                features_anchor, features_positive
            )

            fids_neg = [
                self.embedding.compute_pairwise_fidelity(
                    cell_type, neg_type,
                    features_anchor, neg_features
                )
                for neg_type, neg_features in negatives
            ]

            loss = self.infonce_loss(fid_pos, fids_neg)

            # Restore old parameters
            self.embedding.update_parameters(cell_type, old_params)

            return loss

        # Estimate gradient
        gradient = self.gradient_estimator.estimate_full_gradient(loss_fn, theta)

        # Track gradients for Bayesian UQ
        if self.track_gradients:
            self.gradient_history[cell_type].append(gradient.copy())

        # Update parameters based on optimizer
        if self.config.optimizer == "sgd":
            theta_new = theta - self.config.learning_rate * gradient
        elif self.config.optimizer == "adam":
            theta_new = self._adam_update(cell_type, theta, gradient)
        else:
            raise ValueError(f"Unknown optimizer: {self.config.optimizer}")

        # Set new parameters
        self.embedding.update_parameters(cell_type, theta_new)

    def _adam_update(
        self,
        cell_type: str,
        theta: np.ndarray,
        gradient: np.ndarray
    ) -> np.ndarray:
        """Perform Adam optimizer update.

        Args:
            cell_type: Cell type being updated
            theta: Current parameters
            gradient: Gradient

        Returns:
            Updated parameters
        """
        state = self.optimizer_state
        state["t"] += 1

        # Update biased first moment estimate
        state["m"][cell_type] = (
            state["beta1"] * state["m"][cell_type] + (1 - state["beta1"]) * gradient
        )

        # Update biased second moment estimate
        state["v"][cell_type] = (
            state["beta2"] * state["v"][cell_type]
            + (1 - state["beta2"]) * (gradient ** 2)
        )

        # Compute bias-corrected estimates
        m_hat = state["m"][cell_type] / (1 - state["beta1"] ** state["t"])
        v_hat = state["v"][cell_type] / (1 - state["beta2"] ** state["t"])

        # Update parameters
        theta_new = theta - self.config.learning_rate * m_hat / (np.sqrt(v_hat) + state["epsilon"])

        return theta_new

    def train(
        self,
        training_data: Dict[str, List[np.ndarray]],
        n_epochs: Optional[int] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Train for multiple epochs.

        Args:
            training_data: Dict mapping cell_type -> feature vectors
            n_epochs: Number of epochs (uses config if None)
            verbose: Whether to print progress

        Returns:
            Training summary dictionary
        """
        n_epochs = n_epochs or self.config.n_epochs

        if verbose:
            print(f"Training for {n_epochs} epochs...")
            print(f"Cell types: {self.embedding.cell_types}")
            print(f"Training samples: {sum(len(v) for v in training_data.values())}")

        start_time = time.time()

        for epoch in range(n_epochs):
            epoch_loss = self.train_epoch(training_data, verbose=False)

            if verbose and epoch % 10 == 0:
                print(f"Epoch {epoch + 1}/{n_epochs}: Loss={epoch_loss:.4f}")

        total_time = time.time() - start_time

        # Update embedding metadata
        self.embedding.training_metadata["trained"] = True
        self.embedding.training_metadata["n_epochs"] = self.current_epoch
        self.embedding.training_metadata["loss_history"] = self.loss_history

        summary = {
            "n_epochs": n_epochs,
            "final_loss": self.loss_history[-1] if self.loss_history else None,
            "training_time": total_time,
            "loss_history": self.loss_history
        }

        if verbose:
            print(f"\nTraining complete!")
            print(f"Final loss: {summary['final_loss']:.4f}")
            print(f"Total time: {total_time:.1f}s")

        return summary

    def get_bayesian_parameter_distributions(self) -> Dict[str, 'BayesianParameterDistribution']:
        """Get Bayesian parameter distributions for each cell type.

        Uses gradient history to estimate parameter uncertainties.

        Returns:
            Dict mapping cell_type -> BayesianParameterDistribution
        """
        from .bayesian_uq import BayesianParameterDistribution

        distributions = {}

        for cell_type in self.embedding.cell_types:
            # Get final parameter values
            param_mean = self.embedding.get_parameters(cell_type)

            # Initialize distribution
            param_dist = BayesianParameterDistribution(param_mean)

            # Update covariance from gradient history if available
            if self.track_gradients and len(self.gradient_history.get(cell_type, [])) > 1:
                param_dist.update_from_gradient_history(
                    gradient_history=self.gradient_history[cell_type],
                    learning_rate=self.config.learning_rate
                )

            distributions[cell_type] = param_dist

        return distributions
