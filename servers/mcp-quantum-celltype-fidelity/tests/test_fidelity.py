"""Tests for fidelity scoring and immune evasion detection."""

import pytest
import numpy as np

from quantum_celltype_fidelity.fidelity import (
    FidelityScore,
    FidelityHead,
    LogitFidelityHead,
    ImmuneEvasionDetector,
    compute_fidelity_summary_stats
)


class TestFidelityScore:
    """Tests for FidelityScore dataclass."""

    def test_creation(self):
        """Test creating a FidelityScore."""
        score = FidelityScore(
            raw_fidelity=0.85,
            logit_score=1.73,
            confidence=0.92,
            cell_type_a="T_cell",
            cell_type_b="B_cell"
        )

        assert score.raw_fidelity == 0.85
        assert score.logit_score == 1.73
        assert score.confidence == 0.92
        assert score.cell_type_a == "T_cell"
        assert score.cell_type_b == "B_cell"


class TestFidelityHead:
    """Tests for basic fidelity scoring head."""

    def test_initialization(self):
        """Test FidelityHead initialization."""
        head = FidelityHead(threshold=0.6)
        assert head.threshold == 0.6

    def test_score(self):
        """Test scoring a fidelity value."""
        head = FidelityHead(threshold=0.5)
        score = head.score(0.75)

        assert isinstance(score, FidelityScore)
        assert score.raw_fidelity == 0.75
        assert score.confidence == 0.25  # |0.75 - 0.5|

    def test_predict_positive(self):
        """Test positive prediction."""
        head = FidelityHead(threshold=0.5)
        assert head.predict(0.75) == True
        assert head.predict(0.5) == True

    def test_predict_negative(self):
        """Test negative prediction."""
        head = FidelityHead(threshold=0.5)
        assert head.predict(0.3) == False


class TestLogitFidelityHead:
    """Tests for logit-transformed fidelity head."""

    def test_initialization(self):
        """Test LogitFidelityHead initialization."""
        head = LogitFidelityHead(temperature=2.0, bias=0.5, threshold=0.0)

        assert head.temperature == 2.0
        assert head.bias == 0.5
        assert head.threshold == 0.0

    def test_initialization_invalid_temperature(self):
        """Test that negative temperature raises error."""
        with pytest.raises(ValueError, match="Temperature must be positive"):
            LogitFidelityHead(temperature=-1.0)

    def test_compute_logit(self):
        """Test logit computation."""
        head = LogitFidelityHead(temperature=1.0, bias=0.0)

        # For fidelity = 0.5, logit should be 0
        logit = head.compute_logit(0.5)
        assert abs(logit) < 1e-6

        # For fidelity > 0.5, logit should be positive
        logit = head.compute_logit(0.75)
        assert logit > 0

        # For fidelity < 0.5, logit should be negative
        logit = head.compute_logit(0.25)
        assert logit < 0

    def test_temperature_scaling(self):
        """Test that temperature scales logits."""
        head_low = LogitFidelityHead(temperature=0.5, bias=0.0)
        head_high = LogitFidelityHead(temperature=2.0, bias=0.0)

        fidelity = 0.75

        logit_low = head_low.compute_logit(fidelity)
        logit_high = head_high.compute_logit(fidelity)

        # Higher temperature should give smaller logit
        assert abs(logit_low) > abs(logit_high)

    def test_score(self):
        """Test scoring with logit transformation."""
        head = LogitFidelityHead(temperature=1.0, bias=0.0)
        score = head.score(0.75, "T_cell", "B_cell")

        assert isinstance(score, FidelityScore)
        assert score.raw_fidelity == 0.75
        assert score.cell_type_a == "T_cell"
        assert score.cell_type_b == "B_cell"
        assert score.logit_score > 0  # Since fidelity > 0.5

    def test_predict(self):
        """Test prediction using logit threshold."""
        head = LogitFidelityHead(temperature=1.0, bias=0.0, threshold=0.0)

        # Fidelity > 0.5 should give logit > 0, thus True
        assert head.predict(0.75) == True

        # Fidelity < 0.5 should give logit < 0, thus False
        assert head.predict(0.25) == False


class TestImmuneEvasionDetector:
    """Tests for immune evasion detection."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = ImmuneEvasionDetector(
            immune_cell_types=["T_cell", "B_cell"],
            exhausted_markers=["T_exhausted"],
            evasion_threshold=0.4
        )

        assert detector.immune_cell_types == ["T_cell", "B_cell"]
        assert detector.exhausted_markers == ["T_exhausted"]
        assert detector.evasion_threshold == 0.4

    def test_compute_evasion_score_low_immune_fidelity(self):
        """Test evasion score with low immune fidelity."""
        detector = ImmuneEvasionDetector(
            immune_cell_types=["T_cell", "B_cell"],
            evasion_threshold=0.3
        )

        # Low fidelity to immune cells
        fidelity_to_immune = {"T_cell": 0.2, "B_cell": 0.25}

        evasion_score, metadata = detector.compute_evasion_score(fidelity_to_immune)

        # Average immune fidelity = 0.225
        # Evasion score = 1 - 0.225 = 0.775
        assert evasion_score > 0.7
        assert metadata["is_evading"] == True
        assert metadata["avg_immune_fidelity"] < 0.3

    def test_compute_evasion_score_high_immune_fidelity(self):
        """Test evasion score with high immune fidelity."""
        detector = ImmuneEvasionDetector(
            immune_cell_types=["T_cell", "B_cell"],
            evasion_threshold=0.3
        )

        # High fidelity to immune cells
        fidelity_to_immune = {"T_cell": 0.8, "B_cell": 0.85}

        evasion_score, metadata = detector.compute_evasion_score(fidelity_to_immune)

        # Average immune fidelity = 0.825
        # Evasion score = 1 - 0.825 = 0.175
        assert evasion_score < 0.3
        assert metadata["is_evading"] == False

    def test_compute_evasion_score_with_exhaustion(self):
        """Test evasion score with exhaustion markers."""
        detector = ImmuneEvasionDetector(
            immune_cell_types=["T_cell"],
            exhausted_markers=["T_exhausted"],
            evasion_threshold=0.3
        )

        fidelity_to_immune = {"T_cell": 0.4}
        fidelity_to_exhausted = {"T_exhausted": 0.7}

        evasion_score, metadata = detector.compute_evasion_score(
            fidelity_to_immune,
            fidelity_to_exhausted
        )

        # Base evasion = 1 - 0.4 = 0.6
        # Exhaustion boost = 0.7 * 0.5 = 0.35
        # Total = min(0.6 + 0.35, 1.0) = 0.95
        assert evasion_score > 0.9
        assert metadata["exhaustion_boost"] > 0

    def test_detect_batch(self):
        """Test batch evasion detection."""
        detector = ImmuneEvasionDetector(
            immune_cell_types=["T_cell", "B_cell"],
            evasion_threshold=0.5
        )

        # Create mock fidelity matrix (5x5)
        # Cells 0, 1 = T_cell
        # Cells 2, 3 = B_cell
        # Cell 4 = Tumor (should have low fidelity to immune)
        fidelity_matrix = np.array([
            [1.0, 0.9, 0.8, 0.75, 0.3],  # T_cell 0
            [0.9, 1.0, 0.7, 0.8, 0.25],  # T_cell 1
            [0.8, 0.7, 1.0, 0.9, 0.35],  # B_cell 2
            [0.75, 0.8, 0.9, 1.0, 0.3],  # B_cell 3
            [0.3, 0.25, 0.35, 0.3, 1.0]  # Tumor 4
        ])

        cell_labels = ["T_cell", "T_cell", "B_cell", "B_cell", "Tumor"]

        results = detector.detect_batch(fidelity_matrix, cell_labels)

        assert len(results) == 5

        # Cell 4 (Tumor) should have high evasion score
        tumor_idx, evasion_score, metadata = results[4]
        assert tumor_idx == 4
        assert evasion_score > 0.5
        assert metadata["is_evading"] == True


class TestFidelitySummaryStats:
    """Tests for fidelity summary statistics."""

    def test_compute_summary_stats(self):
        """Test computing summary statistics."""
        # Create simple fidelity matrix
        fidelity_matrix = np.array([
            [1.0, 0.9, 0.5, 0.4],
            [0.9, 1.0, 0.6, 0.5],
            [0.5, 0.6, 1.0, 0.8],
            [0.4, 0.5, 0.8, 1.0]
        ])

        cell_labels = ["T_cell", "T_cell", "B_cell", "B_cell"]

        stats = compute_fidelity_summary_stats(fidelity_matrix, cell_labels)

        assert stats["n_cells"] == 4
        assert "mean_fidelity" in stats
        assert "std_fidelity" in stats
        assert "min_fidelity" in stats
        assert "max_fidelity" in stats
        assert "median_fidelity" in stats

        # Check per-cell-type stats
        assert "per_cell_type" in stats
        assert "T_cell" in stats["per_cell_type"]
        assert "B_cell" in stats["per_cell_type"]

    def test_within_vs_between_type_fidelity(self):
        """Test that within-type fidelity is higher than between-type."""
        # Create matrix with clear separation
        fidelity_matrix = np.array([
            [1.0, 0.95, 0.3, 0.25],
            [0.95, 1.0, 0.35, 0.3],
            [0.3, 0.35, 1.0, 0.9],
            [0.25, 0.3, 0.9, 1.0]
        ])

        cell_labels = ["T_cell", "T_cell", "B_cell", "B_cell"]

        stats = compute_fidelity_summary_stats(fidelity_matrix, cell_labels)

        t_cell_stats = stats["per_cell_type"]["T_cell"]
        b_cell_stats = stats["per_cell_type"]["B_cell"]

        # Within-type should be higher than between-type
        assert t_cell_stats["within_type_mean"] > t_cell_stats["between_type_mean"]
        assert b_cell_stats["within_type_mean"] > b_cell_stats["between_type_mean"]

        # Separation score should be positive
        assert t_cell_stats["separation_score"] > 0
        assert b_cell_stats["separation_score"] > 0
