"""Tests for mcp-cell-classify server (DRY_RUN mode + IntensityClassifier unit tests)."""

import pytest
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Section 1: Import & Init (3 tests)
# ---------------------------------------------------------------------------

def test_imports():
    """Test that server module imports successfully."""
    from mcp_cell_classify import server

    assert server is not None


def test_dry_run_mode():
    """Test DRY_RUN mode is enabled by default in test environment."""
    from mcp_cell_classify.server import DRY_RUN

    assert DRY_RUN is True, "DRY_RUN should be enabled by default"


def test_server_initialization():
    """Test FastMCP server initializes correctly."""
    from mcp_cell_classify.server import mcp

    assert mcp is not None
    assert mcp.name == "cell-classify"


# ---------------------------------------------------------------------------
# Section 2: IntensityClassifier Unit Tests (8 tests)
# ---------------------------------------------------------------------------

def _make_mask_and_image(n_cells=5, size=50):
    """Helper: create a synthetic segmentation mask and intensity image.

    Returns:
        (mask, image) where mask has `n_cells` labeled regions and image has
        varying intensities per cell.
    """
    mask = np.zeros((size, size), dtype=np.int32)
    image = np.zeros((size, size), dtype=np.float64)

    region_size = size // n_cells
    for i in range(n_cells):
        r_start = i * region_size
        r_end = (i + 1) * region_size
        cell_id = i + 1
        mask[r_start:r_end, :] = cell_id
        # Give each cell a different intensity (10, 20, 30, ...)
        image[r_start:r_end, :] = cell_id * 10.0

    return mask, image


def test_measure_cell_intensities():
    """Test measuring per-cell intensities from a synthetic mask + image."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    mask, image = _make_mask_and_image(n_cells=5, size=50)

    df = classifier.measure_cell_intensities(image=image, segmentation_mask=mask)

    assert isinstance(df, pd.DataFrame)
    assert "cell_id" in df.columns
    assert "mean_intensity" in df.columns
    assert "max_intensity" in df.columns
    assert "min_intensity" in df.columns
    assert len(df) == 5


def test_classify_cell_states_proliferating():
    """Test that high intensity cells are classified as proliferating."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    # Cell with intensity 80 — above default proliferating threshold (50)
    df = pd.DataFrame({"cell_id": [1], "mean_intensity": [80.0]})

    results = classifier.classify_cell_states(df)

    assert len(results) == 1
    assert results[0]["state"] == "proliferating"
    assert results[0]["cell_id"] == 1


def test_classify_cell_states_quiescent():
    """Test that low intensity cells are classified as quiescent."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    # Cell with intensity 5 — below default quiescent threshold (20)
    df = pd.DataFrame({"cell_id": [1], "mean_intensity": [5.0]})

    results = classifier.classify_cell_states(df)

    assert len(results) == 1
    assert results[0]["state"] == "quiescent"


def test_classify_cell_states_intermediate():
    """Test that mid-intensity cells are classified as intermediate."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    # Cell with intensity 35 — between quiescent (20) and proliferating (50)
    df = pd.DataFrame({"cell_id": [1], "mean_intensity": [35.0]})

    results = classifier.classify_cell_states(df)

    assert len(results) == 1
    assert results[0]["state"] == "intermediate"


def test_classify_by_threshold():
    """Test single marker threshold classification."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    df = pd.DataFrame({
        "cell_id": [1, 2, 3],
        "mean_intensity": [10.0, 60.0, 30.0],
    })

    result = classifier.classify_by_threshold(df, marker_name="Ki67", threshold=25.0)

    assert "Ki67_positive" in result.columns
    assert "Ki67_intensity" in result.columns
    # Cell 1 (10) < 25 → negative, Cell 2 (60) > 25 → positive, Cell 3 (30) > 25 → positive
    assert result["Ki67_positive"].tolist() == [False, True, True]


def test_auto_threshold_otsu():
    """Test Otsu thresholding on bimodal synthetic data."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    # Create clearly bimodal distribution: low group at 10, high group at 200
    low = np.full(100, 10.0)
    high = np.full(100, 200.0)
    values = np.concatenate([low, high])
    df = pd.DataFrame({"cell_id": range(200), "mean_intensity": values})

    threshold = classifier.auto_threshold_otsu(df)

    # Otsu should find a threshold between the two modes
    assert 10 < threshold < 200, f"Otsu threshold {threshold} not between modes"


def test_auto_threshold_percentile():
    """Test percentile-based thresholding."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    df = pd.DataFrame({
        "cell_id": range(100),
        "mean_intensity": np.arange(100, dtype=float),
    })

    threshold = classifier.auto_threshold_percentile(df, percentile=75)

    # 75th percentile of 0..99 should be ~74.25
    assert 73.0 < threshold < 76.0, f"Percentile threshold {threshold} unexpected"


def test_get_marker_positive_cells():
    """Test extracting positive cell IDs from classified DataFrame."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    df = pd.DataFrame({
        "cell_id": [1, 2, 3, 4],
        "mean_intensity": [10.0, 60.0, 70.0, 5.0],
    })

    classified = classifier.classify_by_threshold(df, marker_name="CD8", threshold=30.0)
    positive = classifier.get_marker_positive_cells(classified, marker_name="CD8")

    assert positive == [2, 3]


# ---------------------------------------------------------------------------
# Section 3: DRY_RUN Smoke Tests (3 tests)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_classify_cell_states_dry_run():
    """Test classify_cell_states returns mock data in DRY_RUN mode."""
    from mcp_cell_classify.server import classify_cell_states

    result = await classify_cell_states.fn(
        segmentation_mask_path="/fake/mask.tif",
        intensity_image_path="/fake/intensity.tif",
    )

    assert "state_counts" in result
    assert "classifications" in result
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_classify_multi_marker_dry_run():
    """Test classify_multi_marker returns mock data in DRY_RUN mode."""
    from mcp_cell_classify.server import classify_multi_marker

    result = await classify_multi_marker.fn(
        segmentation_mask_path="/fake/mask.tif",
        marker_images=[
            {"path": "/fake/ki67.tif", "name": "Ki67"},
            {"path": "/fake/tp53.tif", "name": "TP53"},
        ],
        thresholds={"Ki67": 50.0, "TP53": 100.0},
    )

    assert "phenotype_counts" in result
    assert "markers_used" in result
    assert result["markers_used"] == ["Ki67", "TP53"]
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_generate_phenotype_visualization_dry_run():
    """Test generate_phenotype_visualization returns mock data in DRY_RUN mode."""
    from mcp_cell_classify.server import generate_phenotype_visualization

    result = await generate_phenotype_visualization.fn(
        original_image_path="/fake/original.tif",
        segmentation_mask_path="/fake/mask.tif",
        marker_positive_cells=[1, 2, 3],
    )

    assert "output_file" in result
    assert "positive_cells" in result
    assert "negative_cells" in result
    assert "_DRY_RUN_WARNING" in result


# ---------------------------------------------------------------------------
# Section 4: Edge Cases (6 tests)
# ---------------------------------------------------------------------------

def test_measure_empty_mask():
    """Test that a mask with no cells produces an empty DataFrame."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    # All-zeros mask (no cells)
    mask = np.zeros((20, 20), dtype=np.int32)
    image = np.ones((20, 20), dtype=np.float64) * 50.0

    df = classifier.measure_cell_intensities(image=image, segmentation_mask=mask)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_classify_states_empty_dataframe():
    """Test classify_cell_states with empty input returns empty list."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    df = pd.DataFrame({"cell_id": [], "mean_intensity": []})

    results = classifier.classify_cell_states(df)

    assert results == []


def test_get_marker_positive_no_positives():
    """Test get_marker_positive_cells when all cells are below threshold."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    df = pd.DataFrame({
        "cell_id": [1, 2, 3],
        "mean_intensity": [5.0, 10.0, 15.0],
    })

    classified = classifier.classify_by_threshold(df, marker_name="TP53", threshold=100.0)
    positive = classifier.get_marker_positive_cells(classified, marker_name="TP53")

    assert positive == []


def test_classify_by_threshold_missing_column():
    """Test classify_by_threshold raises ValueError for missing column."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    df = pd.DataFrame({"cell_id": [1], "mean_intensity": [10.0]})

    with pytest.raises(ValueError, match="not found"):
        classifier.classify_by_threshold(
            df, marker_name="X", threshold=5.0, intensity_column="nonexistent"
        )


def test_get_marker_positive_missing_marker():
    """Test get_marker_positive_cells raises ValueError for unknown marker."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    df = pd.DataFrame({"cell_id": [1], "mean_intensity": [10.0]})

    with pytest.raises(ValueError, match="not found"):
        classifier.get_marker_positive_cells(df, marker_name="UNKNOWN")


def test_measure_shape_mismatch():
    """Test that mismatched mask/image shapes raise ValueError."""
    from mcp_cell_classify.intensity_classifier import IntensityClassifier

    classifier = IntensityClassifier()
    mask = np.zeros((10, 10), dtype=np.int32)
    image = np.zeros((20, 20), dtype=np.float64)

    with pytest.raises(ValueError, match="doesn't match"):
        classifier.measure_cell_intensities(image=image, segmentation_mask=mask)
