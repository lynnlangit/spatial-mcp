"""MCP Cell Classify server - Cell phenotype classification from segmentation masks."""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
from common.transport import run_server as _run_server

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fastmcp import FastMCP
from google.cloud import storage
from matplotlib.patches import Patch
from PIL import Image

from .intensity_classifier import IntensityClassifier

# Configure logging
logger = logging.getLogger(__name__)

mcp = FastMCP("cell-classify")

def _is_dry_run() -> bool:
    """Check if DRY_RUN mode is enabled."""
    return os.getenv("CELL_CLASSIFY_DRY_RUN", "true").lower() == "true"

DRY_RUN = _is_dry_run()

# DRY_RUN warning wrapper
def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="CELL_CLASSIFY_DRY_RUN")


# ---------------------------------------------------------------------------
# XAI metadata helper
# ---------------------------------------------------------------------------

# Well-established cell markers with strong literature support (TCGA/GEP validated)
_ESTABLISHED_MARKERS = frozenset({
    "CD3", "CD4", "CD8", "CD19", "CD56", "CD68", "CD138",
    "FoxP3", "Ki67",
})


def _build_xai_metadata(
    confidence_level: str,
    confidence_note: str,
    key_drivers: list,
    guideline_version: str,
    evidence_grade: str,
    counterfactual: Optional[str] = None,
) -> dict:
    """Standardized XAI metadata for all mcp-cell-classify tool outputs.

    evidence_grade values:
      "Tier 1 Evidence (TCGA/GEP)"                -- Well-established marker panel
      "Algorithm-Predicted -- Not Clinical Grade"  -- Algorithmic result; not lab-confirmed
      "Visualization Only"                         -- No inference; display only
    """
    assert confidence_level in ("high", "moderate", "low"), \
        f"confidence_level must be 'high', 'moderate', or 'low' -- got: {confidence_level}"
    # Filter None from key_drivers
    key_drivers = [d for d in key_drivers if d is not None]
    assert 1 <= len(key_drivers) <= 3, \
        f"key_drivers must contain 1-3 items -- got: {len(key_drivers)}"

    return {
        "confidence_level": confidence_level,
        "confidence_note": confidence_note,
        "key_drivers": key_drivers,
        "counterfactual": counterfactual,
        "guideline_version": guideline_version,
        "evidence_grade": evidence_grade,
    }


OUTPUT_DIR = Path(os.getenv("CELL_CLASSIFY_OUTPUT_DIR", "/workspace/output"))

def _ensure_output_dir() -> None:
    """Ensure output directory exists."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "visualizations").mkdir(exist_ok=True)
        (OUTPUT_DIR / "classifications").mkdir(exist_ok=True)
    except (OSError, PermissionError):
        pass

_ensure_output_dir()

def _download_from_gcs(gcs_path: str) -> str:
    """Download file from GCS to temporary location.

    Args:
        gcs_path: GCS path in format gs://bucket/path/to/file

    Returns:
        Local temporary file path

    Raises:
        ValueError: If path is not a valid GCS path
        Exception: If download fails
    """
    if not gcs_path.startswith("gs://"):
        # Return as-is if not a GCS path
        return gcs_path

    try:
        # Parse GCS path: gs://bucket/path/to/file
        path_parts = gcs_path[5:].split("/", 1)
        if len(path_parts) != 2:
            raise ValueError(f"Invalid GCS path format: {gcs_path}")

        bucket_name, blob_name = path_parts

        logger.info(f"Downloading from GCS: {gcs_path}")

        # Initialize GCS client (uses default credentials)
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Create temp file with same extension
        suffix = Path(blob_name).suffix
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path = temp_file.name
        temp_file.close()

        # Download file
        blob.download_to_filename(temp_path)
        logger.info(f"Downloaded to: {temp_path}")

        return temp_path

    except Exception as e:
        logger.error(f"Failed to download from GCS: {e}")
        raise Exception(
            f"Unable to find the image at the provided path: {gcs_path}.\n\n"
            f"Please verify that the path is correct and accessible. "
            f"If you are running this in an environment that requires local file paths, "
            f"you may need to download the file first or provide a local path to the image."
        )

# Initialize classifier (lazy loading)
_intensity_classifier: Optional[IntensityClassifier] = None

def _get_intensity_classifier() -> IntensityClassifier:
    """Get or create IntensityClassifier instance (singleton pattern)."""
    global _intensity_classifier
    if _intensity_classifier is None:
        logger.info("Initializing IntensityClassifier...")
        _intensity_classifier = IntensityClassifier()
    return _intensity_classifier


@mcp.tool()
async def classify_cell_states(
    segmentation_mask_path: str,
    intensity_image_path: str,
    marker_name: str = "Ki67",
    threshold_proliferating: float = 50.0,
    threshold_quiescent: float = 20.0
) -> Dict[str, Any]:
    """Classify cells into functional states based on marker intensity.

    Classifies cells as proliferating, quiescent, or intermediate based on
    marker expression (e.g., Ki67 for proliferation).

    Args:
        segmentation_mask_path: Path to segmentation mask (TIFF from segment_cells)
        intensity_image_path: Path to marker intensity image (TIFF, PNG, etc.)
        marker_name: Name of the marker (default: "Ki67")
        threshold_proliferating: Intensity threshold for proliferating cells (default: 50)
        threshold_quiescent: Intensity threshold for quiescent cells (default: 20)

    Returns:
        Dictionary with:
        - classifications: List of cell states with cell_id, state, confidence
        - total_cells: Total number of cells classified
        - state_counts: Number of cells in each state
        - classifications_csv: Path to exported CSV file
        - description: Summary description

    Example:
        >>> result = await classify_cell_states(
        ...     segmentation_mask_path="/output/segmentations/DAPI_nuclear_seg.tif",
        ...     intensity_image_path="/data/Ki67_intensity.tiff",
        ...     marker_name="Ki67",
        ...     threshold_proliferating=50,
        ...     threshold_quiescent=20
        ... )
        >>> print(f"{result['state_counts']['proliferating']} proliferating cells")
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "classifications": [
                {"cell_id": 1, "state": "proliferating", "confidence": 0.92, "Ki67_intensity": 85.3},
                {"cell_id": 2, "state": "quiescent", "confidence": 0.87, "Ki67_intensity": 12.1},
                {"cell_id": 3, "state": "intermediate", "confidence": 0.75, "Ki67_intensity": 35.2}
            ],
            "total_cells": 1247,
            "state_counts": {
                "proliferating": 523,
                "quiescent": 612,
                "intermediate": 112
            },
            "mode": "dry_run"
        })

    try:
        # Download from GCS if needed
        local_seg_mask_path = _download_from_gcs(segmentation_mask_path)
        local_intensity_path = _download_from_gcs(intensity_image_path)

        # Load segmentation mask
        logger.info(f"Loading segmentation mask: {local_seg_mask_path}")
        seg_mask = np.array(Image.open(local_seg_mask_path))

        # Load intensity image
        logger.info(f"Loading intensity image: {local_intensity_path}")
        intensity_image = np.array(Image.open(local_intensity_path))

        logger.info(f"Mask shape: {seg_mask.shape}, Intensity shape: {intensity_image.shape}")

        # Get classifier
        classifier = _get_intensity_classifier()

        # Measure cell intensities
        logger.info("Measuring cell intensities...")
        intensities_df = classifier.measure_cell_intensities(
            image=intensity_image,
            segmentation_mask=seg_mask
        )

        # Classify cell states
        logger.info(f"Classifying cells using {marker_name} marker...")
        classifications = classifier.classify_cell_states(
            intensities=intensities_df,
            marker_name=marker_name,
            threshold_proliferating=threshold_proliferating,
            threshold_quiescent=threshold_quiescent
        )

        # Save classifications to CSV
        csv_filename = f"classifications_{marker_name}_{Path(segmentation_mask_path).stem}.csv"
        csv_path = OUTPUT_DIR / "classifications" / csv_filename
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        classifications_df = pd.DataFrame(classifications)
        classifications_df.to_csv(csv_path, index=False)
        logger.info(f"Classifications saved to: {csv_path}")

        # Calculate state counts
        state_counts = {}
        for c in classifications:
            state = c["state"]
            state_counts[state] = state_counts.get(state, 0) + 1

        # Create summary
        total_cells = len(classifications)
        states_list = list(state_counts.keys())

        result = {
            "status": "success",
            "classifications": classifications[:100],  # Return first 100 for brevity
            "total_cells": total_cells,
            "state_counts": state_counts,
            "states_identified": states_list,
            "classifications_csv": str(csv_path),
            "marker_used": marker_name,
            "threshold_proliferating": threshold_proliferating,
            "threshold_quiescent": threshold_quiescent,
            "description": f"Classified {total_cells} cells: {state_counts.get('proliferating', 0)} proliferating, {state_counts.get('quiescent', 0)} quiescent, {state_counts.get('intermediate', 0)} intermediate"
        }

        logger.info(f"Classification complete: {total_cells} cells classified")
        return result

    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "message": "Please check that both the segmentation mask and intensity image paths are correct."
        }
    except ValueError as e:
        error_msg = f"Invalid data: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "message": "Image and segmentation mask shapes don't match or invalid parameters."
        }
    except Exception as e:
        error_msg = f"Classification failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "error": error_msg,
            "message": "An unexpected error occurred during classification. Check logs for details."
        }


@mcp.tool()
async def classify_multi_marker(
    segmentation_mask_path: str,
    marker_images: List[Dict[str, str]],
    thresholds: Dict[str, float],
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """Classify cells by multiple markers simultaneously for multi-marker phenotyping.

    Takes a segmentation mask and multiple marker intensity images, measures per-cell
    intensity for each marker, then applies thresholds to assign phenotypes
    (e.g., "Ki67+/TP53-").

    Args:
        segmentation_mask_path: Path to segmentation mask (16-bit TIFF label image)
        marker_images: List of dicts, each with 'path' (image path) and 'name' (marker name).
            Example: [{"path": "/data/ki67.tif", "name": "Ki67"}, {"path": "/data/tp53.tif", "name": "TP53"}]
        thresholds: Dict mapping marker name to intensity threshold.
            Example: {"Ki67": 50.0, "TP53": 100.0}
        output_filename: Custom output CSV filename (optional)

    Returns:
        Dictionary with:
        - classifications_csv: Path to exported CSV with phenotype assignments
        - total_cells: Number of cells classified
        - phenotype_counts: Dict of phenotype → count
        - markers_used: List of marker names
        - description: Summary description

    Example:
        >>> result = await classify_multi_marker(
        ...     segmentation_mask_path="/output/segmentations/DAPI_seg.tif",
        ...     marker_images=[
        ...         {"path": "/data/ki67.tif", "name": "Ki67"},
        ...         {"path": "/data/tp53.tif", "name": "TP53"}
        ...     ],
        ...     thresholds={"Ki67": 50.0, "TP53": 100.0}
        ... )
        >>> print(result['phenotype_counts'])
        {"Ki67+/TP53+": 120, "Ki67+/TP53-": 340, "Ki67-/TP53+": 180, "Ki67-/TP53-": 607}
    """
    if DRY_RUN:
        marker_names = [m["name"] for m in marker_images]
        return add_dry_run_warning({
            "classifications_csv": str(OUTPUT_DIR / "classifications" / "multi_marker_dryrun.csv"),
            "total_cells": 1247,
            "phenotype_counts": {
                "Ki67+/TP53+": 120,
                "Ki67+/TP53-": 340,
                "Ki67-/TP53+": 180,
                "Ki67-/TP53-": 607
            },
            "markers_used": marker_names,
            "description": f"DRY_RUN: Would classify 1247 cells using {len(marker_names)} markers: {', '.join(marker_names)}",
            "mode": "dry_run"
        })

    try:
        # Download and load segmentation mask
        local_seg_mask_path = _download_from_gcs(segmentation_mask_path)
        logger.info(f"Loading segmentation mask: {local_seg_mask_path}")
        seg_mask = np.array(Image.open(local_seg_mask_path))

        classifier = _get_intensity_classifier()

        # Measure intensities for first marker to get base DataFrame
        first_marker = marker_images[0]
        local_first_path = _download_from_gcs(first_marker["path"])
        first_image = np.array(Image.open(local_first_path))

        logger.info(f"Measuring intensities for {first_marker['name']}...")
        combined_df = classifier.measure_cell_intensities(
            image=first_image,
            segmentation_mask=seg_mask
        )
        # Rename intensity columns with marker prefix
        combined_df = combined_df.rename(columns={
            "mean_intensity": f"{first_marker['name']}_mean_intensity",
            "max_intensity": f"{first_marker['name']}_max_intensity",
            "min_intensity": f"{first_marker['name']}_min_intensity",
        })

        # Measure intensities for remaining markers
        for marker_info in marker_images[1:]:
            local_path = _download_from_gcs(marker_info["path"])
            marker_image = np.array(Image.open(local_path))

            logger.info(f"Measuring intensities for {marker_info['name']}...")
            marker_df = classifier.measure_cell_intensities(
                image=marker_image,
                segmentation_mask=seg_mask
            )
            # Rename and merge
            marker_df = marker_df.rename(columns={
                "mean_intensity": f"{marker_info['name']}_mean_intensity",
                "max_intensity": f"{marker_info['name']}_max_intensity",
                "min_intensity": f"{marker_info['name']}_min_intensity",
            })
            combined_df = combined_df.merge(
                marker_df[["cell_id", f"{marker_info['name']}_mean_intensity",
                           f"{marker_info['name']}_max_intensity",
                           f"{marker_info['name']}_min_intensity"]],
                on="cell_id"
            )

        # Apply multi-marker classification using per-marker mean_intensity columns
        # The classify_multi_marker method expects a single intensity_column, so we
        # apply threshold classification manually per marker
        marker_names = [m["name"] for m in marker_images]
        for marker_name in marker_names:
            col = f"{marker_name}_mean_intensity"
            threshold = thresholds.get(marker_name, 50.0)
            combined_df[f"{marker_name}_positive"] = combined_df[col] > threshold

        # Build phenotype labels
        phenotype_parts = []
        for marker_name in marker_names:
            pos_col = f"{marker_name}_positive"
            phenotype_parts.append(
                combined_df[pos_col].apply(lambda x, m=marker_name: f"{m}+" if x else f"{m}-")
            )

        combined_df["phenotype"] = phenotype_parts[0]
        for part in phenotype_parts[1:]:
            combined_df["phenotype"] = combined_df["phenotype"] + "/" + part

        # Save to CSV
        marker_str = "_".join(marker_names)
        if output_filename is None:
            output_filename = f"multi_marker_{marker_str}_{Path(segmentation_mask_path).stem}.csv"

        csv_path = OUTPUT_DIR / "classifications" / output_filename
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        combined_df.to_csv(csv_path, index=False)

        # Phenotype counts
        phenotype_counts = combined_df["phenotype"].value_counts().to_dict()

        total_cells = len(combined_df)
        result = {
            "status": "success",
            "classifications_csv": str(csv_path),
            "total_cells": total_cells,
            "phenotype_counts": phenotype_counts,
            "markers_used": marker_names,
            "thresholds_used": thresholds,
            "description": f"Classified {total_cells} cells using {len(marker_names)} markers ({', '.join(marker_names)}). Found {len(phenotype_counts)} phenotypes."
        }

        logger.info(f"Multi-marker classification complete: {total_cells} cells, {len(phenotype_counts)} phenotypes")
        return result

    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "message": "Please check that the segmentation mask and all marker image paths are correct."
        }
    except ValueError as e:
        error_msg = f"Invalid data: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "message": "Image shapes don't match or invalid parameters."
        }
    except Exception as e:
        error_msg = f"Multi-marker classification failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "error": error_msg,
            "message": "An unexpected error occurred. Check logs for details."
        }


@mcp.tool()
async def generate_phenotype_visualization(
    original_image_path: str,
    segmentation_mask_path: str,
    marker_positive_cells: List[int],
    output_filename: Optional[str] = None,
    positive_color: str = "green",
    negative_color: str = "red"
) -> Dict[str, Any]:
    """Generate cell phenotype visualization.

    Colors cells based on marker expression (positive vs negative).
    Useful for visualizing marker-positive cell distribution (e.g., CD8+, Ki67+).

    Args:
        original_image_path: Path to original microscopy image
        segmentation_mask_path: Path to segmentation mask
        marker_positive_cells: List of cell IDs that are marker-positive
        output_filename: Custom output filename (default: phenotype_viz_TIMESTAMP.png)
        positive_color: Color for marker-positive cells (default: "green")
        negative_color: Color for marker-negative cells (default: "red")

    Returns:
        Dictionary with:
        - output_file: Path to saved visualization
        - positive_cells: Number of marker-positive cells
        - negative_cells: Number of marker-negative cells
        - percent_positive: Percentage of positive cells
        - description: Text description

    Example:
        >>> result = await generate_phenotype_visualization(
        ...     original_image_path="/data/IF_Ki67.tiff",
        ...     segmentation_mask_path="/data/IF_Ki67.tiff.seg.tif",
        ...     marker_positive_cells=[1, 5, 12, 18, 25],
        ...     positive_color="yellow",
        ...     negative_color="blue"
        ... )
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "output_file": str(OUTPUT_DIR / "visualizations" / "phenotype_viz_dryrun.png"),
            "positive_cells": 623,
            "negative_cells": 624,
            "percent_positive": 50.0,
            "description": "DRY_RUN: Would generate phenotype visualization",
            "message": "Set CELL_CLASSIFY_DRY_RUN=false to generate real visualizations"
        })

    try:
        # Download from GCS if needed
        local_original_path = _download_from_gcs(original_image_path)
        local_seg_mask_path = _download_from_gcs(segmentation_mask_path)

        # Load images
        original_img = np.array(Image.open(local_original_path))
        seg_mask = np.array(Image.open(local_seg_mask_path))

        # Get unique cell IDs
        cell_ids = np.unique(seg_mask)[1:]  # Exclude background (0)
        positive_set = set(marker_positive_cells)

        # Create colored phenotype mask
        phenotype_mask = np.zeros(seg_mask.shape + (3,), dtype=np.uint8)

        color_map = {
            'green': [0, 255, 0],
            'red': [255, 0, 0],
            'yellow': [255, 255, 0],
            'blue': [0, 0, 255],
            'cyan': [0, 255, 255],
            'magenta': [255, 0, 255]
        }
        pos_color = color_map.get(positive_color.lower(), [0, 255, 0])
        neg_color = color_map.get(negative_color.lower(), [255, 0, 0])

        for cell_id in cell_ids:
            mask = seg_mask == cell_id
            if cell_id in positive_set:
                phenotype_mask[mask] = pos_color
            else:
                phenotype_mask[mask] = neg_color

        # Plot
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))

        # Original image
        if len(original_img.shape) == 2:
            axes[0].imshow(original_img, cmap='gray')
        else:
            axes[0].imshow(original_img)
        axes[0].set_title('Original Image', fontsize=12, fontweight='bold')
        axes[0].axis('off')

        # Phenotype visualization
        axes[1].imshow(phenotype_mask)
        num_positive = len(positive_set.intersection(set(cell_ids)))
        num_negative = len(cell_ids) - num_positive
        pct_positive = 100 * num_positive / len(cell_ids) if len(cell_ids) > 0 else 0

        axes[1].set_title(f'Cell Phenotypes ({pct_positive:.1f}% Positive)',
                         fontsize=12, fontweight='bold')
        axes[1].axis('off')

        # Add legend
        legend_elements = [
            Patch(facecolor=np.array(pos_color)/255, label=f'Marker+ ({num_positive} cells)'),
            Patch(facecolor=np.array(neg_color)/255, label=f'Marker- ({num_negative} cells)')
        ]
        axes[1].legend(handles=legend_elements, loc='upper right')

        plt.tight_layout()

        # Save
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"phenotype_viz_{timestamp}.png"

        output_path = OUTPUT_DIR / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        description = f"Phenotype visualization showing {num_positive} marker-positive cells ({positive_color}) and {num_negative} marker-negative cells ({negative_color}). {pct_positive:.1f}% of cells are positive."

        return {
            "status": "success",
            "output_file": str(output_path),
            "positive_cells": int(num_positive),
            "negative_cells": int(num_negative),
            "total_cells": int(len(cell_ids)),
            "percent_positive": round(float(pct_positive), 2),
            "description": description,
            "visualization_type": "phenotype_coloring",
            "positive_color": positive_color,
            "negative_color": negative_color
        }

    except Exception as e:
        logger.error(f"Error generating phenotype visualization: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate phenotype visualization. Check file paths and formats."
        }


def main() -> None:
    """Run the MCP cell-classify server."""
    _run_server(mcp, server_name="mcp-cell-classify", dry_run=DRY_RUN, env_var="CELL_CLASSIFY_DRY_RUN", default_port=3009)

if __name__ == "__main__":
    main()
