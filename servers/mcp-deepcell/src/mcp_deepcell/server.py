"""MCP DeepCell server - Deep learning cell segmentation and quantification."""

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
from PIL import Image
from skimage import color, measure

from .deepcell_engine import DeepCellEngine
from .intensity_classifier import IntensityClassifier

# Configure logging
logger = logging.getLogger(__name__)

mcp = FastMCP("deepcell")

def _is_dry_run() -> bool:
    """Check if DRY_RUN mode is enabled."""
    return os.getenv("DEEPCELL_DRY_RUN", "true").lower() == "true"

DRY_RUN = _is_dry_run()

# DRY_RUN warning wrapper
def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="DEEPCELL_DRY_RUN")


OUTPUT_DIR = Path(os.getenv("DEEPCELL_OUTPUT_DIR", "/workspace/output"))
MODEL_CACHE_DIR = Path(os.getenv("DEEPCELL_MODEL_CACHE_DIR", Path.home() / ".deepcell" / "models"))
USE_GPU = os.getenv("DEEPCELL_USE_GPU", "true").lower() == "true"

def _ensure_output_dir() -> None:
    """Ensure output directory exists."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "visualizations").mkdir(exist_ok=True)
        (OUTPUT_DIR / "segmentations").mkdir(exist_ok=True)
        (OUTPUT_DIR / "quantifications").mkdir(exist_ok=True)
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
            f"The cell segmentation tool was unable to find the image at the provided path: {gcs_path}.\n\n"
            f"Please verify that the path is correct and accessible. "
            f"If you are running this in an environment that requires local file paths, "
            f"you may need to download the file first or provide a local path to the image."
        )

# Initialize DeepCell engine and classifier (lazy loading)
_deepcell_engine: Optional[DeepCellEngine] = None
_intensity_classifier: Optional[IntensityClassifier] = None

def _get_deepcell_engine() -> DeepCellEngine:
    """Get or create DeepCell engine instance (singleton pattern)."""
    global _deepcell_engine
    if _deepcell_engine is None:
        logger.info("Initializing DeepCell engine...")
        _deepcell_engine = DeepCellEngine(model_cache_dir=MODEL_CACHE_DIR, use_gpu=USE_GPU)
    return _deepcell_engine

def _get_intensity_classifier() -> IntensityClassifier:
    """Get or create IntensityClassifier instance (singleton pattern)."""
    global _intensity_classifier
    if _intensity_classifier is None:
        logger.info("Initializing IntensityClassifier...")
        _intensity_classifier = IntensityClassifier()
    return _intensity_classifier

@mcp.tool()
async def segment_cells(
    image_path: str,
    model_type: str = "nuclear",
    min_cell_size: int = 100,
    image_mpp: Optional[float] = None
) -> Dict[str, Any]:
    """Deep learning-based cell segmentation using DeepCell models.

    Args:
        image_path: Path to microscopy image (TIFF, PNG, or other formats)
        model_type: Model to use - "nuclear" or "membrane" (default: "nuclear")
        min_cell_size: Minimum cell size in pixels (default: 100)
        image_mpp: Microns per pixel for physical size calculation (optional)

    Returns:
        Dictionary with:
        - segmentation_mask: Path to saved segmentation mask (TIFF)
        - cells_detected: Number of cells found
        - cells_filtered: Number of small cells filtered out
        - mean_cell_area: Mean cell area in pixels
        - median_cell_area: Median cell area in pixels
        - processing_time_seconds: Time taken for segmentation
        - model_used: Which model was used
        - gpu_used: Whether GPU acceleration was used

    Example:
        >>> result = await segment_cells(
        ...     image_path="/data/DAPI_nuclear.tiff",
        ...     model_type="nuclear",
        ...     min_cell_size=100
        ... )
        >>> print(f"Found {result['cells_detected']} cells")
        >>> # Use result['segmentation_mask'] for downstream analysis
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "segmentation_mask": f"{image_path}.seg.tif",
            "cells_detected": 1247,
            "mean_cell_area": 850,
            "model_used": model_type,
            "processing_time_seconds": 15.3,
            "quality_metrics": {
                "mean_confidence": 0.89,
                "cells_filtered": 23
            },
            "mode": "dry_run"
        })

    try:
        # Download from GCS if needed
        local_image_path = _download_from_gcs(image_path)

        # Load image
        logger.info(f"Loading image: {local_image_path}")
        image = np.array(Image.open(local_image_path))
        logger.info(f"Image loaded: shape={image.shape}, dtype={image.dtype}")

        # Get DeepCell engine
        engine = _get_deepcell_engine()

        # Segment image
        logger.info(f"Segmenting with {model_type} model...")
        segmentation_mask, metadata = engine.segment_image(
            image=image,
            model_type=model_type,
            min_cell_size=min_cell_size,
            image_mpp=image_mpp
        )

        # Save segmentation mask as TIFF
        mask_filename = f"{Path(image_path).stem}_segmentation_{model_type}.tif"
        mask_path = OUTPUT_DIR / "segmentations" / mask_filename
        mask_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as 16-bit TIFF (supports up to 65535 cells)
        mask_img = Image.fromarray(segmentation_mask.astype(np.uint16))
        mask_img.save(mask_path)
        logger.info(f"Segmentation mask saved to: {mask_path}")

        result = {
            "status": "success",
            "segmentation_mask": str(mask_path),
            "cells_detected": metadata["cells_detected"],
            "cells_filtered": metadata["cells_filtered"],
            "mean_cell_area": metadata["mean_cell_area"],
            "median_cell_area": metadata["median_cell_area"],
            "min_cell_area": metadata["min_cell_area"],
            "max_cell_area": metadata["max_cell_area"],
            "processing_time_seconds": metadata["processing_time_seconds"],
            "model_used": metadata["model_used"],
            "gpu_used": metadata["gpu_used"],
            "image_mpp": metadata.get("image_mpp"),
            "description": f"Segmented {metadata['cells_detected']} cells using {model_type} model in {metadata['processing_time_seconds']:.1f}s"
        }

        logger.info(f"Segmentation complete: {result['cells_detected']} cells detected")
        return result

    except FileNotFoundError:
        error_msg = f"Image file not found: {image_path}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "message": "Please check the file path and try again."
        }
    except ValueError as e:
        error_msg = f"Invalid parameter: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "message": "Please check your parameters (model_type should be 'nuclear' or 'membrane')"
        }
    except Exception as e:
        error_msg = f"Segmentation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "error": error_msg,
            "message": "An unexpected error occurred during segmentation. Check logs for details."
        }


@mcp.tool()
async def quantify_markers(
    segmentation_mask_path: str,
    marker_images: List[Dict[str, str]],
    output_filename: Optional[str] = None
) -> Dict[str, Any]:
    """Quantify marker intensities per cell from a segmentation mask.

    Measures mean, max, and min intensity for each marker in each segmented cell.
    Returns a per-cell intensity CSV suitable for downstream classification
    (e.g., with mcp-cell-classify or external tools like FlowSOM, Leiden, scikit-learn).

    Args:
        segmentation_mask_path: Path to segmentation mask (16-bit TIFF label image from segment_cells)
        marker_images: List of dicts, each with 'path' (image path) and 'name' (marker name).
            Example: [{"path": "/data/ki67.tif", "name": "Ki67"}, {"path": "/data/tp53.tif", "name": "TP53"}]
        output_filename: Custom output CSV filename (optional)

    Returns:
        Dictionary with:
        - quantification_csv: Path to exported CSV with per-cell intensities
        - total_cells: Number of cells quantified
        - markers_quantified: List of marker names
        - marker_summaries: Per-marker summary statistics (mean, std, min, max)
        - description: Summary description

    Example:
        >>> result = await quantify_markers(
        ...     segmentation_mask_path="/output/segmentations/DAPI_seg.tif",
        ...     marker_images=[
        ...         {"path": "/data/ki67.tif", "name": "Ki67"},
        ...         {"path": "/data/tp53.tif", "name": "TP53"}
        ...     ]
        ... )
        >>> print(f"Quantified {result['total_cells']} cells across {len(result['markers_quantified'])} markers")
        >>> # Use result['quantification_csv'] with mcp-cell-classify or other tools
    """
    if DRY_RUN:
        marker_names = [m["name"] for m in marker_images]
        return add_dry_run_warning({
            "quantification_csv": str(OUTPUT_DIR / "quantifications" / "quantification_dryrun.csv"),
            "total_cells": 1247,
            "markers_quantified": marker_names,
            "marker_summaries": {
                name: {"mean": 45.2, "std": 28.1, "min": 2.3, "max": 98.7}
                for name in marker_names
            },
            "description": f"DRY_RUN: Would quantify {len(marker_names)} markers for 1247 cells",
            "mode": "dry_run"
        })

    try:
        # Download and load segmentation mask
        local_seg_mask_path = _download_from_gcs(segmentation_mask_path)
        logger.info(f"Loading segmentation mask: {local_seg_mask_path}")
        seg_mask = np.array(Image.open(local_seg_mask_path))

        classifier = _get_intensity_classifier()
        marker_names = [m["name"] for m in marker_images]

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

        # Save to CSV
        marker_str = "_".join(marker_names)
        if output_filename is None:
            output_filename = f"quantification_{marker_str}_{Path(segmentation_mask_path).stem}.csv"

        csv_path = OUTPUT_DIR / "quantifications" / output_filename
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        combined_df.to_csv(csv_path, index=False)

        # Compute per-marker summary stats
        marker_summaries = {}
        for name in marker_names:
            col = f"{name}_mean_intensity"
            marker_summaries[name] = {
                "mean": round(float(combined_df[col].mean()), 2),
                "std": round(float(combined_df[col].std()), 2),
                "min": round(float(combined_df[col].min()), 2),
                "max": round(float(combined_df[col].max()), 2),
            }

        total_cells = len(combined_df)
        result = {
            "status": "success",
            "quantification_csv": str(csv_path),
            "total_cells": total_cells,
            "markers_quantified": marker_names,
            "marker_summaries": marker_summaries,
            "description": f"Quantified {len(marker_names)} markers ({', '.join(marker_names)}) for {total_cells} cells. CSV saved to {csv_path}"
        }

        logger.info(f"Quantification complete: {total_cells} cells, {len(marker_names)} markers")
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
            "message": "Image shapes don't match the segmentation mask or invalid parameters."
        }
    except Exception as e:
        error_msg = f"Quantification failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "error": error_msg,
            "message": "An unexpected error occurred during quantification. Check logs for details."
        }


# ============================================================================
# VISUALIZATION TOOLS
# ============================================================================


@mcp.tool()
async def generate_segmentation_overlay(
    original_image_path: str,
    segmentation_mask_path: str,
    output_filename: Optional[str] = None,
    overlay_color: str = "yellow",
    overlay_alpha: float = 0.4
) -> Dict[str, Any]:
    """Generate segmentation overlay visualization.

    Overlays segmentation boundaries on the original microscopy image.
    Useful for validating segmentation quality and visualizing cell boundaries.

    Args:
        original_image_path: Path to original microscopy image
        segmentation_mask_path: Path to segmentation mask (label image)
        output_filename: Custom output filename (default: segmentation_overlay_TIMESTAMP.png)
        overlay_color: Color for cell boundaries (default: "yellow")
        overlay_alpha: Transparency of overlay (0=transparent, 1=opaque, default: 0.4)

    Returns:
        Dictionary with:
        - output_file: Path to saved overlay image
        - cells_visualized: Number of cells shown
        - description: Text description

    Example:
        >>> result = await generate_segmentation_overlay(
        ...     original_image_path="/data/IF_CD8.tiff",
        ...     segmentation_mask_path="/data/IF_CD8.tiff.seg.tif",
        ...     overlay_color="green"
        ... )
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "output_file": str(OUTPUT_DIR / "visualizations" / "segmentation_overlay_dryrun.png"),
            "cells_visualized": 1247,
            "description": "DRY_RUN: Would generate segmentation overlay",
            "message": "Set DEEPCELL_DRY_RUN=false to generate real visualizations"
        })

    try:
        # Download from GCS if needed
        local_original_path = _download_from_gcs(original_image_path)
        local_seg_mask_path = _download_from_gcs(segmentation_mask_path)

        # Load original image
        original_img = Image.open(local_original_path)
        original_arr = np.array(original_img)

        # Convert grayscale to RGB if needed
        if len(original_arr.shape) == 2:
            original_rgb = color.gray2rgb(original_arr)
        elif original_arr.shape[2] == 1:
            original_rgb = color.gray2rgb(original_arr[:, :, 0])
        else:
            original_rgb = original_arr[:, :, :3]

        # Load segmentation mask
        seg_mask = np.array(Image.open(local_seg_mask_path))

        # Find cell boundaries
        boundaries = measure.find_boundaries(seg_mask, mode='outer')

        # Create color map for overlay
        color_map = {
            'yellow': [255, 255, 0],
            'green': [0, 255, 0],
            'red': [255, 0, 0],
            'cyan': [0, 255, 255],
            'magenta': [255, 0, 255]
        }
        overlay_rgb = color_map.get(overlay_color.lower(), [255, 255, 0])

        # Create overlay
        overlay = original_rgb.copy().astype(float)
        overlay[boundaries] = overlay_rgb

        # Blend original and overlay
        blended = (1 - overlay_alpha) * original_rgb + overlay_alpha * overlay
        blended = np.clip(blended, 0, 255).astype(np.uint8)

        # Plot
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))

        axes[0].imshow(original_rgb)
        axes[0].set_title('Original Image', fontsize=12, fontweight='bold')
        axes[0].axis('off')

        axes[1].imshow(blended)
        axes[1].set_title(f'Segmentation Overlay ({len(np.unique(seg_mask)) - 1} cells)',
                         fontsize=12, fontweight='bold')
        axes[1].axis('off')

        plt.tight_layout()

        # Save
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"segmentation_overlay_{timestamp}.png"

        output_path = OUTPUT_DIR / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        num_cells = len(np.unique(seg_mask)) - 1  # Subtract background
        description = f"Segmentation overlay showing {num_cells} segmented cells with {overlay_color} boundaries overlaid on original image."

        return {
            "status": "success",
            "output_file": str(output_path),
            "cells_visualized": int(num_cells),
            "description": description,
            "visualization_type": "segmentation_overlay",
            "overlay_color": overlay_color
        }

    except Exception as e:
        logger.error(f"Error generating segmentation overlay: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate segmentation overlay. Check file paths and formats."
        }


@mcp.resource("model://deepcell/membrane")
def get_membrane_model_info() -> str:
    """Membrane segmentation model information."""
    return json.dumps({
        "model": "DeepCell Membrane Segmentation",
        "description": "Deep learning model for cell membrane detection",
        "architecture": "ResNet50 + Feature Pyramid Network",
        "training_data": "10,000+ annotated cell images",
        "accuracy": "95% IoU on test set",
        "use_cases": ["Cell counting", "Morphology analysis", "Cell tracking"]
    }, indent=2)

def main() -> None:
    """Run the MCP mcp-deepcell server."""
    _run_server(mcp, server_name="mcp-deepcell", dry_run=DRY_RUN, env_var="DEEPCELL_DRY_RUN")

if __name__ == "__main__":
    main()
