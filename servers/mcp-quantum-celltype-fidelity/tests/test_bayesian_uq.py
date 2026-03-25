"""Tests for Bayesian uncertainty quantification."""

import pytest
import numpy as np
from quantum_celltype_fidelity.bayesian_uq import (
    BayesianParameterDistribution,
    BayesianFidelityEstimator,
    EnsembleFidelityEstimator,
    UncertaintyEstimate,
    calibrate_uncertainty
)


class TestBayesianParameterDistribution:
    """Test Bayesian parameter distribution."""

    def test_initialization_with_mean_only(self):
        """Test initialization with mean parameters only."""
        param_mean = np.array([0.5, 1.0, 1.5])
        dist = BayesianParameterDistribution(param_mean)

        assert dist.n_params == 3
        assert np.allclose(dist.param_mean, param_mean)
        assert dist.param_cov.shape == (3, 3)
        # Should have diagonal covariance by default
        assert np.allclose(dist.param_cov, np.diag(np.diag(dist.param_cov)))

    def test_initialization_with_std(self):
        """Test initialization with standard deviations."""
        param_mean = np.array([0.5, 1.0, 1.5])
        param_std = np.array([0.1, 0.2, 0.15])
        dist = BayesianParameterDistribution(param_mean, param_std=param_std)

        expected_cov = np.diag(param_std ** 2)
        assert np.allclose(dist.param_cov, expected_cov)

    def test_sampling(self):
        """Test parameter sampling from distribution."""
        param_mean = np.array([1.0, 2.0, 3.0])
        param_std = np.array([0.1, 0.1, 0.1])
        dist = BayesianParameterDistribution(param_mean, param_std=param_std)

        # Sample parameters
        samples = dist.sample(n_samples=100, random_state=42)

        assert samples.shape == (100, 3)
        # Check that sample mean is close to true mean
        assert np.allclose(np.mean(samples, axis=0), param_mean, atol=0.1)
        # Check that sample std is close to true std
        assert np.allclose(np.std(samples, axis=0), param_std, atol=0.1)

    def test_sampling_reproducibility(self):
        """Test that sampling with same seed gives same results."""
        param_mean = np.array([1.0, 2.0])
        dist = BayesianParameterDistribution(param_mean)

        samples1 = dist.sample(n_samples=10, random_state=42)
        samples2 = dist.sample(n_samples=10, random_state=42)

        assert np.allclose(samples1, samples2)

    def test_update_from_gradient_history(self):
        """Test updating covariance from gradient history."""
        param_mean = np.array([1.0, 2.0])
        dist = BayesianParameterDistribution(param_mean)

        # Create mock gradient history with variance
        gradients = [
            np.array([0.1, 0.2]),
            np.array([0.15, 0.25]),
            np.array([0.08, 0.18]),
            np.array([0.12, 0.22])
        ]

        initial_cov = dist.param_cov.copy()
        dist.update_from_gradient_history(gradients, learning_rate=0.01)

        # Covariance should change
        assert not np.allclose(dist.param_cov, initial_cov)
        # Should be positive definite
        eigenvalues = np.linalg.eigvals(dist.param_cov)
        assert np.all(eigenvalues > 0)


class TestBayesianFidelityEstimator:
    """Test Bayesian fidelity estimator."""

    def test_fidelity_estimation_with_uncertainty(self):
        """Test fidelity estimation with uncertainty quantification."""
        # Create a simple parameter distribution
        param_mean = np.array([1.0, 2.0])
        param_std = np.array([0.2, 0.3])
        param_dist = BayesianParameterDistribution(param_mean, param_std=param_std)

        estimator = BayesianFidelityEstimator(param_dist, n_samples=50)

        # Mock fidelity function (depends on parameters)
        def mock_fidelity_fn(params, features_a, features_b):
            # Simple function: fidelity decreases with parameter magnitude
            return 1.0 / (1.0 + 0.1 * np.sum(params ** 2))

        features_a = np.array([0.5, 0.5])
        features_b = np.array([0.6, 0.4])

        result = estimator.estimate_fidelity_with_uncertainty(
            mock_fidelity_fn,
            features_a,
            features_b,
            random_state=42
        )

        # Check result structure
        assert isinstance(result, UncertaintyEstimate)
        assert 0 <= result.mean <= 1
        assert result.std >= 0
        assert result.confidence_interval_95[0] < result.mean < result.confidence_interval_95[1]
        assert result.confidence_interval_90[0] < result.mean < result.confidence_interval_90[1]
        # 90% CI should be narrower than 95% CI
        ci_90_width = result.confidence_interval_90[1] - result.confidence_interval_90[0]
        ci_95_width = result.confidence_interval_95[1] - result.confidence_interval_95[0]
        assert ci_90_width < ci_95_width

    def test_classification_confidence(self):
        """Test classification confidence estimation."""
        param_dist = BayesianParameterDistribution(np.array([1.0]))
        estimator = BayesianFidelityEstimator(param_dist, n_samples=100)

        # Create uncertainty estimate with samples
        samples = np.array([0.6, 0.65, 0.7, 0.55, 0.62])
        uncertainty = UncertaintyEstimate(
            mean=0.62,
            std=0.05,
            confidence_interval_95=(0.52, 0.72),
            confidence_interval_90=(0.54, 0.70),
            samples=samples
        )

        # Test confidence with threshold 0.5
        confidence = estimator.estimate_classification_confidence(
            uncertainty,
            threshold=0.5
        )

        assert 0 <= confidence <= 1
        # All samples are above 0.5, so confidence should be high
        assert confidence > 0.9


class TestEnsembleFidelityEstimator:
    """Test ensemble-based uncertainty quantification."""

    def test_ensemble_estimation(self):
        """Test ensemble fidelity estimation."""
        # Create ensemble of parameter distributions
        param_dists = [
            BayesianParameterDistribution(np.array([1.0, 2.0])),
            BayesianParameterDistribution(np.array([1.1, 1.9])),
            BayesianParameterDistribution(np.array([0.9, 2.1]))
        ]

        estimator = EnsembleFidelityEstimator(param_dists)

        # Mock fidelity function
        def mock_fidelity_fn(params, features_a, features_b):
            return 1.0 / (1.0 + 0.1 * np.sum((params - 1.0) ** 2))

        features_a = np.array([0.5, 0.5])
        features_b = np.array([0.6, 0.4])

        result = estimator.estimate_fidelity_with_uncertainty(
            mock_fidelity_fn,
            features_a,
            features_b
        )

        # Check that we got reasonable uncertainty from ensemble
        assert result.std > 0  # Should have some disagreement
        assert result.epistemic_uncertainty > 0


class TestUncertaintyEstimate:
    """Test uncertainty estimate dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        estimate = UncertaintyEstimate(
            mean=0.75,
            std=0.05,
            confidence_interval_95=(0.65, 0.85),
            confidence_interval_90=(0.67, 0.83),
            epistemic_uncertainty=0.04,
            aleatoric_uncertainty=0.03
        )

        result_dict = estimate.to_dict()

        assert result_dict["mean"] == 0.75
        assert result_dict["std"] == 0.05
        assert result_dict["confidence_interval_95"]["lower"] == 0.65
        assert result_dict["confidence_interval_95"]["upper"] == 0.85
        assert result_dict["epistemic_uncertainty"] == 0.04
        assert result_dict["total_uncertainty"] == 0.05


class TestCalibrateUncertainty:
    """Test uncertainty calibration."""

    def test_perfect_calibration(self):
        """Test calibration with well-calibrated predictions."""
        np.random.seed(42)

        # Generate well-calibrated predictions: noise matches stated uncertainty
        true_values = np.random.normal(0, 1, 100)
        noise = np.random.normal(0, 1, 100)  # Noise with std=1
        predictions = true_values + noise  # Predictions with realistic error
        uncertainties = np.ones(100)  # Stated uncertainty matches actual noise

        calibration = calibrate_uncertainty(
            predictions.tolist(),
            uncertainties.tolist(),
            true_values.tolist()
        )

        # With true std=1 and predicted std=1, coverage should be close to expected
        assert 0.6 < calibration["coverage_68"] < 0.75  # Should be ~68%
        assert 0.85 < calibration["coverage_90"] < 0.95  # Should be ~90%
        assert 0.90 < calibration["coverage_95"] < 0.98  # Should be ~95%

    def test_underconfident_calibration(self):
        """Test detection of under-confident predictions."""
        np.random.seed(42)

        # Generate predictions that are too uncertain
        true_values = np.random.normal(0, 1, 100)
        predictions = true_values
        uncertainties = np.ones(100) * 2.0  # Too high

        calibration = calibrate_uncertainty(
            predictions.tolist(),
            uncertainties.tolist(),
            true_values.tolist()
        )

        # Coverage should be higher than expected (under-confident)
        assert calibration["coverage_95"] > 0.97


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
