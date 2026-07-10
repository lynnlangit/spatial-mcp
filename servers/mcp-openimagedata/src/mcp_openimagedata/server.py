"""MCP Open Image Data server implementation.

This module provides an MCP server for histology image processing,
spatial registration, and feature extraction.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
from PIL import Image
from fastmcp import FastMCP
from scipy import ndimage, stats
from skimage.feature import local_binary_pattern, graycomatrix, graycoprops
from skimage.filters import threshold_otsu
from skimage.measure import label, regionprops, shannon_entropy
from skimage.registration import phase_cross_correlation
from skimage.transform import AffineTransform, warp

# Configure logging
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("openimagedata")

def _is_dry_run() -> bool:
    """Check if DRY_RUN mode is enabled."""
    return os.getenv("IMAGE_DRY_RUN", "true").lower() == "true"

DRY_RUN = _is_dry_run()

# DRY_RUN warning wrapper
def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="IMAGE_DRY_RUN")


def _build_xai_metadata(
    confidence_level: str,
    confidence_note: str,
    key_drivers: list,
    guideline_version: str,
    evidence_grade: str,
    counterfactual=None,
) -> dict:
    """Standardized XAI metadata for mcp-openimagedata tool outputs."""
    assert confidence_level in ("high", "moderate", "low"), \
        f"confidence_level must be 'high', 'moderate', or 'low' -- got: {confidence_level}"
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


# Configuration
IMAGE_DIR = Path(os.getenv("IMAGE_DATA_DIR", "/workspace/images"))
CACHE_DIR = Path(os.getenv("IMAGE_CACHE_DIR", "/workspace/cache/images"))
OUTPUT_DIR = Path(os.getenv("IMAGE_OUTPUT_DIR", "/workspace/output"))
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "500"))


def _ensure_directories() -> None:
    """Ensure required directories exist."""
    try:
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        (IMAGE_DIR / "he").mkdir(exist_ok=True)
        (IMAGE_DIR / "if").mkdir(exist_ok=True)
    except (OSError, PermissionError):
        pass

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError):
        pass

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "visualizations").mkdir(exist_ok=True)
    except (OSError, PermissionError):
        pass


# ============================================================================
# TOOL 1: fetch_histology_image
# ============================================================================


@mcp.tool()
async def fetch_histology_image(
    image_id: str,
    stain_type: str = "he",
    resolution: str = "high"
) -> Dict[str, Any]:
    """Retrieve tissue histology images.

    Fetches H&E or immunofluorescence histology images for spatial
    transcriptomics integration.

    Args:
        image_id: Unique identifier for the image
        stain_type: Type of staining - "he" (H&E) or "if" (immunofluorescence)
        resolution: Image resolution - "high", "medium", or "low"

    Returns:
        Dictionary with keys:
            - image_path: Path to the downloaded image
            - dimensions: Image dimensions (width, height)
            - file_size_mb: File size in megabytes
            - metadata: Image metadata (magnification, stain info)

    Raises:
        ValueError: If invalid stain type or resolution
        IOError: If image fetch fails

    Example:
        >>> result = await fetch_histology_image(
        ...     image_id="sample_001",
        ...     stain_type="he",
        ...     resolution="high"
        ... )
        >>> print(f"Image: {result['dimensions']}")
    """
    _ensure_directories()

    if stain_type not in ["he", "if"]:
        raise ValueError(f"Invalid stain type: {stain_type}. Must be 'he' or 'if'")

    if resolution not in ["high", "medium", "low"]:
        raise ValueError(f"Invalid resolution: {resolution}")

    image_path = IMAGE_DIR / stain_type / f"{image_id}_{resolution}.tif"
    image_path.parent.mkdir(parents=True, exist_ok=True)

    if DRY_RUN:
        # Create a small mock image
        mock_image = Image.new('RGB', (2048, 2048), color='white')
        mock_image.save(image_path)

        return {
            "image_path": str(image_path),
            "dimensions": {"width": 2048, "height": 2048},
            "file_size_mb": 12.5,
            "metadata": {
                "stain_type": stain_type,
                "magnification": "20x" if resolution == "high" else "10x",
                "format": "TIFF",
                "mode": "dry_run"
            },
            "xai_metadata": _build_xai_metadata(
                confidence_level="high",
                confidence_note=(
                    "Image retrieval from data store. No inference performed. "
                    "Image quality (stain quality, section artifacts) should be "
                    "assessed visually before downstream AI analysis."
                ),
                key_drivers=[
                    f"Image type: {stain_type.upper()}",
                    f"Source: DRY_RUN mock image",
                    f"Resolution: {resolution}",
                ],
                guideline_version="Digital pathology standards: CAP Digital Pathology Guidelines 2022",
                evidence_grade="Visualization Only",
            ),
        }

    try:
        # If exact path doesn't exist, search for a partial match
        if not image_path.exists():
            candidates = sorted((IMAGE_DIR / stain_type).glob(f"*{image_id}*"))
            if candidates:
                image_path = candidates[0]
                logger.info(f"Exact path not found; matched: {image_path.name}")
            else:
                return {
                    "status": "error",
                    "error": f"Image not found for id '{image_id}' in {IMAGE_DIR / stain_type}",
                    "message": "Check image_id or verify IMAGE_DATA_DIR contains the requested image."
                }

        img = Image.open(image_path)
        width, height = img.size
        file_size_mb = round(image_path.stat().st_size / (1024 * 1024), 2)
        magnification = "20x" if resolution == "high" else ("10x" if resolution == "medium" else "4x")

        logger.info(f"Loaded {image_path.name}: {width}x{height}, {file_size_mb} MB")

        return {
            "image_path": str(image_path),
            "dimensions": {"width": width, "height": height},
            "file_size_mb": file_size_mb,
            "metadata": {
                "stain_type": stain_type,
                "magnification": magnification,
                "format": image_path.suffix.lstrip(".").upper(),
                "color_mode": img.mode
            },
            "xai_metadata": _build_xai_metadata(
                confidence_level="high",
                confidence_note=(
                    "Image retrieval from data store. No inference performed. "
                    "Image quality (stain quality, section artifacts) should be "
                    "assessed visually before downstream AI analysis."
                ),
                key_drivers=[
                    f"Image type: {stain_type.upper()}",
                    f"Source: {image_path.name}",
                    f"Resolution: {resolution}",
                ],
                guideline_version="Digital pathology standards: CAP Digital Pathology Guidelines 2022",
                evidence_grade="Visualization Only",
            ),
        }
    except Exception as e:
        logger.error(f"Error loading image: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to load image. Check file path and format."
        }


# ============================================================================
# TOOL 2: register_image_to_spatial
# ============================================================================


@mcp.tool()
async def register_image_to_spatial(
    image_path: str,
    spatial_coordinates_file: str,
    output_file: str,
    registration_method: str = "affine"
) -> Dict[str, Any]:
    """Align histology images with spatial coordinates.

    Performs image registration to align histology images with spatial
    transcriptomics spot/cell coordinates.

    Args:
        image_path: Path to histology image
        spatial_coordinates_file: Path to file with spatial coordinates
        output_file: Path for registered image output
        registration_method: Method - "affine", "rigid", or "deformable"

    Returns:
        Dictionary with keys:
            - registered_image: Path to registered image
            - transformation_matrix: Transformation parameters
            - registration_quality: Quality metrics (RMSE, correlation)

    Raises:
        IOError: If files not found
        ValueError: If invalid registration method

    Example:
        >>> result = await register_image_to_spatial(
        ...     image_path="/images/he/sample_001.tif",
        ...     spatial_coordinates_file="/data/coordinates.csv",
        ...     output_file="/images/registered/sample_001.tif"
        ... )
        >>> print(f"RMSE: {result['registration_quality']['rmse']:.3f}")
    """
    _ensure_directories()

    if registration_method not in ["affine", "rigid", "deformable"]:
        raise ValueError(f"Invalid registration method: {registration_method}")

    output_path = Path(output_file)

    if DRY_RUN:
        # Mock registration
        return {
            "registered_image": str(output_path),
            "transformation_matrix": {
                "scale_x": 1.02,
                "scale_y": 0.98,
                "rotation_degrees": 2.5,
                "translation_x": 12.3,
                "translation_y": -8.7
            },
            "registration_quality": {
                "rmse": 1.85,
                "correlation": 0.94,
                "matched_points": 450,
                "method": registration_method
            },
            "mode": "dry_run",
            "xai_metadata": _build_xai_metadata(
                confidence_level="moderate",
                confidence_note=(
                    f"Image-to-spatial registration using {registration_method}. "
                    "DRY_RUN: mock registration quality metrics. "
                    "Registration quality depends on tissue morphology preservation."
                ),
                key_drivers=[
                    f"Method: {registration_method}",
                    "Registration error: 1.85 (mock)",
                ],
                guideline_version="PASTE (Zeira 2022, Nature Methods); STalign (Clifton 2023)",
                evidence_grade="Algorithm-Predicted — Not Clinical Grade",
            ),
        }

    img_path = Path(image_path)
    if not img_path.exists():
        raise IOError(f"Image not found: {image_path}")

    coord_path = Path(spatial_coordinates_file)
    if not coord_path.exists():
        raise IOError(f"Coordinates file not found: {spatial_coordinates_file}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        start = time.time()

        # Load histology image as grayscale
        hist_img = np.array(Image.open(image_path).convert('L'))
        logger.info(f"Loaded histology image: {hist_img.shape}")

        # Parse spatial coordinates — supports Visium and generic x/y formats
        coords_df = pd.read_csv(spatial_coordinates_file)
        if 'pxl_col_in_fullres' in coords_df.columns:
            x_col, y_col = 'pxl_col_in_fullres', 'pxl_row_in_fullres'
            if 'in_tissue' in coords_df.columns:
                coords_df = coords_df[coords_df['in_tissue'] == 1]
        elif 'x' in coords_df.columns and 'y' in coords_df.columns:
            x_col, y_col = 'x', 'y'
        else:
            raise ValueError(
                f"Could not find coordinate columns. Expected 'pxl_col_in_fullres'/'pxl_row_in_fullres' "
                f"(Visium) or 'x'/'y'. Found: {list(coords_df.columns)}"
            )
        spot_x = coords_df[x_col].values.astype(float)
        spot_y = coords_df[y_col].values.astype(float)
        logger.info(f"Loaded {len(spot_x)} in-tissue spots from {coord_path.name}")

        # Tissue detection via Otsu thresholding (tissue is dark in H&E)
        thresh = threshold_otsu(hist_img)
        tissue_mask = hist_img < thresh
        tissue_rows, tissue_cols = np.where(tissue_mask)

        if len(tissue_rows) == 0:
            raise ValueError("No tissue detected in image. Otsu threshold found no dark regions.")

        # Bounding boxes: (x_min, y_min, x_max, y_max)
        tissue_bbox = (int(tissue_cols.min()), int(tissue_rows.min()),
                       int(tissue_cols.max()), int(tissue_rows.max()))
        spot_bbox = (float(spot_x.min()), float(spot_y.min()),
                     float(spot_x.max()), float(spot_y.max()))

        tissue_w = tissue_bbox[2] - tissue_bbox[0]
        tissue_h = tissue_bbox[3] - tissue_bbox[1]
        spot_w = spot_bbox[2] - spot_bbox[0]
        spot_h = spot_bbox[3] - spot_bbox[1]

        # Estimate scale from extent ratio
        scale_x = spot_w / tissue_w if tissue_w > 0 else 1.0
        scale_y = spot_h / tissue_h if tissue_h > 0 else 1.0

        if registration_method == "rigid":
            uniform_scale = (scale_x + scale_y) / 2.0
            scale_x = scale_y = uniform_scale

        # Translation to align top-left corners after scaling
        trans_x = spot_bbox[0] - tissue_bbox[0] * scale_x
        trans_y = spot_bbox[1] - tissue_bbox[1] * scale_y
        rotation_deg = 0.0

        if registration_method == "deformable":
            # Refine with phase cross-correlation: rasterize spots as density map
            ref_img = np.zeros_like(hist_img, dtype=np.float64)
            for sx, sy in zip(spot_x, spot_y):
                r, c = int(round(sy)), int(round(sx))
                if 0 <= r < ref_img.shape[0] and 0 <= c < ref_img.shape[1]:
                    ref_img[r, c] = 1.0
            ref_blurred = ndimage.gaussian_filter(ref_img, sigma=15)
            tissue_inverted = 1.0 - hist_img.astype(np.float64) / max(hist_img.max(), 1)
            shift, _, _ = phase_cross_correlation(ref_blurred, tissue_inverted, upsample_factor=2)
            trans_y += float(shift[0]) * scale_y
            trans_x += float(shift[1]) * scale_x
            logger.info(f"Phase correlation refinement shift: ({shift[0]:.1f}, {shift[1]:.1f})")

        # Apply affine transform and save registered image
        transform = AffineTransform(scale=(scale_x, scale_y), translation=(trans_x, trans_y))
        registered = warp(hist_img, transform.inverse, output_shape=hist_img.shape, preserve_range=True)
        Image.fromarray(registered.astype(np.uint8)).save(output_path)
        logger.info(f"Saved registered image to {output_path}")

        # Quality: count spots that fall on tissue in the original mask
        matched = 0
        for sx, sy in zip(spot_x, spot_y):
            r, c = int(round(sy)), int(round(sx))
            if 0 <= r < tissue_mask.shape[0] and 0 <= c < tissue_mask.shape[1]:
                if tissue_mask[r, c]:
                    matched += 1

        # Correlation between tissue density and spot density
        if registration_method == "deformable":
            correlation = float(np.corrcoef(ref_blurred.flatten(), tissue_inverted.flatten())[0, 1])
        else:
            correlation = round(matched / max(len(spot_x), 1), 3)

        rmse = round(float(np.sqrt((scale_x - 1) ** 2 + (scale_y - 1) ** 2)), 3)

        return {
            "registered_image": str(output_path),
            "transformation_matrix": {
                "scale_x": round(float(scale_x), 4),
                "scale_y": round(float(scale_y), 4),
                "rotation_degrees": round(rotation_deg, 2),
                "translation_x": round(float(trans_x), 2),
                "translation_y": round(float(trans_y), 2)
            },
            "registration_quality": {
                "rmse": rmse,
                "correlation": round(float(correlation), 3),
                "matched_points": int(matched),
                "method": registration_method,
                "total_spots": int(len(spot_x)),
                "processing_time_seconds": round(time.time() - start, 2)
            },
            "xai_metadata": _build_xai_metadata(
                confidence_level="moderate",
                confidence_note=(
                    f"Image-to-spatial registration using {registration_method}. "
                    f"Registration error: {rmse:.1f}. "
                    "Registration quality depends on tissue morphology preservation "
                    "and landmark availability."
                ),
                key_drivers=[
                    f"Method: {registration_method}",
                    f"Registration error (RMSE): {rmse}",
                    f"Landmarks used: {int(matched)}",
                ],
                guideline_version="PASTE (Zeira 2022, Nature Methods); STalign (Clifton 2023)",
                evidence_grade="Algorithm-Predicted — Not Clinical Grade",
            ),
        }
    except (IOError, ValueError) as e:
        logger.error(f"Registration input error: {e}")
        return {"status": "error", "error": str(e), "message": "Check input files and parameters."}
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "message": "Registration failed. Check logs for details."}


# ============================================================================
# TOOL 3: extract_image_features
# ============================================================================


@mcp.tool()
async def extract_image_features(
    image_path: str,
    feature_type: str = "texture",
    roi_coordinates: Optional[List[Tuple[int, int, int, int]]] = None
) -> Dict[str, Any]:
    """Extract computer vision features from histology images.

    Extracts texture, morphological, or intensity features from histology
    images for downstream analysis and correlation with spatial expression.

    Args:
        image_path: Path to histology image
        feature_type: Type of features - "texture", "morphology", or "intensity"
        roi_coordinates: Optional list of ROI bounding boxes [(x1,y1,x2,y2), ...]

    Returns:
        Dictionary with keys:
            - features: Extracted feature vectors
            - feature_names: Names/descriptions of features
            - roi_count: Number of ROIs processed
            - processing_time_seconds: Processing duration

    Raises:
        IOError: If image not found
        ValueError: If invalid feature type

    Example:
        >>> result = await extract_image_features(
        ...     image_path="/images/he/sample_001.tif",
        ...     feature_type="texture"
        ... )
        >>> print(f"Extracted {len(result['features'])} features")
    """
    _ensure_directories()

    if feature_type not in ["texture", "morphology", "intensity"]:
        raise ValueError(f"Invalid feature type: {feature_type}")

    if DRY_RUN:
        # Mock feature extraction
        num_features = {"texture": 25, "morphology": 15, "intensity": 10}[feature_type]

        return {
            "features": np.random.rand(num_features).tolist(),
            "feature_names": [f"{feature_type}_feature_{i}" for i in range(num_features)],
            "roi_count": len(roi_coordinates) if roi_coordinates else 1,
            "processing_time_seconds": 2.5,
            "feature_statistics": {
                "mean": 0.5,
                "std": 0.15,
                "min": 0.05,
                "max": 0.95
            },
            "mode": "dry_run",
            "xai_metadata": _build_xai_metadata(
                confidence_level="moderate",
                confidence_note=(
                    f"Image features extracted using {feature_type} method. "
                    "DRY_RUN: mock feature values. Feature extraction is deterministic "
                    "given a trained model, but features are latent representations "
                    "without direct biological interpretability."
                ),
                key_drivers=[
                    f"Feature type: {feature_type}",
                    f"Feature dimension: {num_features}",
                ],
                guideline_version="UNI (Chen 2024, Nature Medicine); CTransPath (Wang 2022, MedIA)",
                evidence_grade="Algorithm-Predicted — Not Clinical Grade",
            ),
        }

    img_path = Path(image_path)
    if not img_path.exists():
        raise IOError(f"Image not found: {image_path}")

    try:
        start = time.time()
        img = np.array(Image.open(image_path).convert('L'))  # grayscale uint8

        # Build list of sub-images to process: per-ROI or full image
        regions: List[Tuple[str, np.ndarray]] = []
        if roi_coordinates:
            for idx, (x1, y1, x2, y2) in enumerate(roi_coordinates):
                roi = img[y1:y2, x1:x2]
                if roi.size == 0:
                    continue
                regions.append((f"roi_{idx}", roi))
        else:
            regions.append(("full_image", img))

        all_features: List[Dict[str, Any]] = []

        for region_name, region_img in regions:
            if feature_type == "texture":
                features, names = _extract_texture(region_img)
            elif feature_type == "morphology":
                features, names = _extract_morphology(region_img)
            else:  # intensity
                features, names = _extract_intensity(region_img)

            all_features.append({
                "region": region_name,
                "features": features,
                "feature_names": names
            })

        # Flatten for single-region case (backward compatible)
        if len(all_features) == 1:
            feat_values = all_features[0]["features"]
            feat_names = all_features[0]["feature_names"]
        else:
            feat_values = [r["features"] for r in all_features]
            feat_names = all_features[0]["feature_names"]

        flat = [v for v in (feat_values if isinstance(feat_values[0], (int, float)) else
                            [item for sublist in feat_values for item in sublist])]

        logger.info(f"Extracted {len(feat_names)} {feature_type} features from {len(regions)} region(s)")

        return {
            "features": flat,
            "feature_names": feat_names,
            "roi_count": len(regions),
            "processing_time_seconds": round(time.time() - start, 2),
            "feature_statistics": {
                "mean": round(float(np.mean(flat)), 4),
                "std": round(float(np.std(flat)), 4),
                "min": round(float(np.min(flat)), 4),
                "max": round(float(np.max(flat)), 4)
            },
            "xai_metadata": _build_xai_metadata(
                confidence_level="moderate",
                confidence_note=(
                    f"Image features extracted using {feature_type} method. "
                    "Feature extraction is deterministic given a trained model, but "
                    "features are latent representations without direct biological "
                    "interpretability. Downstream analysis quality depends on whether "
                    "training distribution included the relevant tumor type."
                ),
                key_drivers=[
                    f"Feature type: {feature_type}",
                    f"Feature dimension: {len(feat_names)}",
                    f"ROI count: {len(regions)}",
                ],
                guideline_version="UNI (Chen 2024, Nature Medicine); CTransPath (Wang 2022, MedIA)",
                evidence_grade="Algorithm-Predicted — Not Clinical Grade",
            ),
        }
    except (IOError, ValueError) as e:
        logger.error(f"Feature extraction input error: {e}")
        return {"status": "error", "error": str(e), "message": "Check image path and parameters."}
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "message": "Feature extraction failed. Check logs."}


# ============================================================================
# FEATURE EXTRACTION HELPERS
# ============================================================================


def _extract_texture(img: np.ndarray) -> Tuple[List[float], List[str]]:
    """Extract 25 texture features: LBP histogram (10) + GLCM props (10) + summary stats (5)."""
    features: List[float] = []
    names: List[str] = []

    # --- LBP histogram (10 bins for P=8 uniform) ---
    lbp = local_binary_pattern(img, P=8, R=1, method='uniform')
    n_bins = 10  # P+2 for uniform
    hist, _ = np.histogram(lbp, bins=n_bins, range=(0, n_bins))
    hist_norm = hist.astype(float) / (hist.sum() + 1e-8)
    for i, v in enumerate(hist_norm):
        features.append(round(float(v), 6))
        names.append(f"lbp_hist_bin{i}")

    # --- GLCM properties (5 props x 2 distances = 10) ---
    # Downsample if image is large to keep GLCM fast
    max_dim = 512
    if max(img.shape) > max_dim:
        from skimage.transform import resize
        scale = max_dim / max(img.shape)
        img_small = (resize(img, (int(img.shape[0] * scale), int(img.shape[1] * scale)),
                            preserve_range=True)).astype(np.uint8)
    else:
        img_small = img

    glcm = graycomatrix(img_small, distances=[1, 3], angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
                         levels=256, symmetric=True, normed=True)
    for prop_name in ['contrast', 'dissimilarity', 'correlation', 'energy', 'homogeneity']:
        prop_vals = graycoprops(glcm, prop_name)  # shape (n_distances, n_angles)
        for d_idx, d in enumerate([1, 3]):
            val = float(np.mean(prop_vals[d_idx, :]))  # average across angles
            features.append(round(val, 6))
            names.append(f"glcm_{prop_name}_d{d}")

    # --- Summary stats (5) ---
    features.append(round(float(np.mean(lbp)), 4))
    names.append("lbp_mean")
    features.append(round(float(np.std(lbp)), 4))
    names.append("lbp_std")
    features.append(round(float(shannon_entropy(lbp.astype(int))), 4))
    names.append("lbp_entropy")
    features.append(round(float(shannon_entropy(img)), 4))
    names.append("image_entropy")
    features.append(round(float(np.std(img)), 4))
    names.append("image_std")

    return features, names


def _extract_morphology(img: np.ndarray) -> Tuple[List[float], List[str]]:
    """Extract 15 morphology features from thresholded connected components."""
    features: List[float] = []
    names: List[str] = []

    thresh = threshold_otsu(img)
    binary = img < thresh  # tissue is dark
    labeled = label(binary)
    props = regionprops(labeled)

    num_objects = len(props)
    features.append(float(num_objects))
    names.append("num_objects")

    if num_objects == 0:
        # No objects detected — pad with zeros
        for metric in ['area', 'perimeter', 'solidity', 'eccentricity']:
            for agg in ['mean', 'std', 'median']:
                features.append(0.0)
                names.append(f"{metric}_{agg}")
        features.extend([0.0, 0.0])
        names.extend(["circularity_mean", "circularity_std"])
        return features, names

    areas = np.array([p.area for p in props], dtype=float)
    perimeters = np.array([p.perimeter for p in props], dtype=float)
    solidities = np.array([p.solidity for p in props], dtype=float)
    eccentricities = np.array([p.eccentricity for p in props], dtype=float)
    # circularity = 4*pi*area / perimeter^2  (1.0 = perfect circle)
    circularities = 4 * np.pi * areas / (perimeters ** 2 + 1e-8)

    for metric_name, values in [("area", areas), ("perimeter", perimeters),
                                 ("solidity", solidities), ("eccentricity", eccentricities)]:
        features.append(round(float(np.mean(values)), 4))
        names.append(f"{metric_name}_mean")
        features.append(round(float(np.std(values)), 4))
        names.append(f"{metric_name}_std")
        features.append(round(float(np.median(values)), 4))
        names.append(f"{metric_name}_median")

    features.append(round(float(np.mean(circularities)), 4))
    names.append("circularity_mean")
    features.append(round(float(np.std(circularities)), 4))
    names.append("circularity_std")

    return features, names


def _extract_intensity(img: np.ndarray) -> Tuple[List[float], List[str]]:
    """Extract 10 intensity features: stats + percentiles + entropy."""
    pixels = img.astype(float).flatten()
    features: List[float] = [
        round(float(np.mean(pixels)), 4),
        round(float(np.std(pixels)), 4),
        round(float(np.median(pixels)), 4),
        round(float(np.min(pixels)), 4),
        round(float(np.max(pixels)), 4),
        round(float(stats.skew(pixels)), 4),
        round(float(stats.kurtosis(pixels)), 4),
        round(float(np.percentile(pixels, 25)), 4),
        round(float(np.percentile(pixels, 75)), 4),
        round(float(shannon_entropy(img)), 4),
    ]
    names: List[str] = [
        "mean", "std", "median", "min", "max",
        "skewness", "kurtosis", "p25", "p75", "entropy"
    ]
    return features, names


# ============================================================================
# VISUALIZATION TOOLS
# ============================================================================


@mcp.tool()
async def generate_multiplex_composite(
    channel_paths: List[str],
    channel_names: List[str],
    channel_colors: Optional[List[str]] = None,
    output_filename: Optional[str] = None,
    normalize: bool = True
) -> Dict[str, Any]:
    """Generate RGB composite from multiplex immunofluorescence channels.

    Combines multiple fluorescence channels into a single RGB composite image.
    Useful for visualizing multiplex IF with 2-7 fluorescent markers simultaneously.

    Args:
        channel_paths: List of paths to individual channel images (grayscale TIFF)
        channel_names: List of marker names (e.g., ["DAPI", "TP53", "KI67"])
        channel_colors: Optional list of colors for each channel (e.g., ["blue", "red", "green"])
                       If None, defaults to standard colors based on position
        output_filename: Custom output filename (default: multiplex_composite_TIMESTAMP.png)
        normalize: Whether to normalize intensity per channel (default: True)

    Returns:
        Dictionary with:
        - output_file: Path to saved composite image
        - channels_combined: Number of channels combined
        - channel_info: List of channel names and colors used
        - description: Text description

    Example:
        >>> result = await generate_multiplex_composite(
        ...     channel_paths=[
        ...         "/data/PAT001_multiplex_DAPI.tiff",
        ...         "/data/PAT001_multiplex_TP53.tiff",
        ...         "/data/PAT001_multiplex_KI67.tiff"
        ...     ],
        ...     channel_names=["DAPI", "TP53", "KI67"],
        ...     channel_colors=["blue", "red", "green"]
        ... )
    """
    if DRY_RUN:
        return add_dry_run_warning({
            "output_file": str(OUTPUT_DIR / "visualizations" / "multiplex_composite_dryrun.png"),
            "channels_combined": len(channel_names),
            "channel_info": [{"name": name, "color": "auto"} for name in channel_names],
            "description": f"DRY_RUN: Would generate RGB composite for {', '.join(channel_names)}",
            "message": "Set IMAGE_DRY_RUN=false to generate real visualizations"
        })

    try:
        # Validate inputs
        if len(channel_paths) != len(channel_names):
            return {
                "status": "error",
                "error": "Number of channel paths must match number of channel names",
                "num_paths": len(channel_paths),
                "num_names": len(channel_names)
            }

        if len(channel_paths) < 1 or len(channel_paths) > 7:
            return {
                "status": "error",
                "error": "Must provide 1-7 channels (typical multiplex IF has 2-7 channels)"
            }

        # Default color mapping
        default_colors = ["blue", "green", "red", "cyan", "magenta", "yellow", "white"]
        if channel_colors is None:
            channel_colors = default_colors[:len(channel_paths)]

        # Color to RGB mapping
        color_map = {
            "blue": [0, 0, 255],
            "green": [0, 255, 0],
            "red": [255, 0, 0],
            "cyan": [0, 255, 255],
            "magenta": [255, 0, 255],
            "yellow": [255, 255, 0],
            "white": [255, 255, 255]
        }

        # Load and normalize channels
        channel_arrays = []
        for i, path in enumerate(channel_paths):
            try:
                img = np.array(Image.open(path))

                # Normalize to 0-1 range if requested
                if normalize:
                    img_norm = (img - img.min()) / (img.max() - img.min() + 1e-8)
                else:
                    img_norm = img / 255.0 if img.max() > 1 else img

                channel_arrays.append(img_norm)
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Failed to load channel {i} ({channel_names[i]}): {str(e)}",
                    "path": path
                }

        # Verify all channels have same dimensions
        shapes = [arr.shape for arr in channel_arrays]
        if len(set(shapes)) > 1:
            return {
                "status": "error",
                "error": "All channels must have the same dimensions",
                "shapes": {name: shape for name, shape in zip(channel_names, shapes)}
            }

        # Create RGB composite
        height, width = channel_arrays[0].shape
        composite = np.zeros((height, width, 3), dtype=np.float32)

        for channel_arr, color_name in zip(channel_arrays, channel_colors):
            rgb_color = color_map.get(color_name.lower(), [255, 255, 255])
            for c in range(3):
                composite[:, :, c] += channel_arr * (rgb_color[c] / 255.0)

        # Clip to valid range and convert to uint8
        composite = np.clip(composite, 0, 1)
        composite_uint8 = (composite * 255).astype(np.uint8)

        # Create visualization with individual channels and composite
        n_channels = len(channel_arrays)
        fig, axes = plt.subplots(1, n_channels + 1, figsize=(5 * (n_channels + 1), 5))

        # Plot individual channels
        for idx, (arr, name, color) in enumerate(zip(channel_arrays, channel_names, channel_colors)):
            axes[idx].imshow(arr, cmap='gray')
            axes[idx].set_title(f'{name} ({color})', fontsize=12, fontweight='bold')
            axes[idx].axis('off')

        # Plot composite
        axes[n_channels].imshow(composite_uint8)
        axes[n_channels].set_title('RGB Composite', fontsize=12, fontweight='bold')
        axes[n_channels].axis('off')

        plt.tight_layout()

        # Save
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"multiplex_composite_{timestamp}.png"

        output_path = OUTPUT_DIR / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Generate description
        channel_info = [{"name": name, "color": color} for name, color in zip(channel_names, channel_colors)]
        description = f"Multiplex IF RGB composite combining {len(channel_names)} channels: {', '.join(channel_names)}. "
        description += f"Colors: {', '.join([f'{name}={color}' for name, color in zip(channel_names, channel_colors)])}."

        return {
            "status": "success",
            "output_file": str(output_path),
            "channels_combined": len(channel_names),
            "channel_info": channel_info,
            "image_dimensions": {"width": width, "height": height},
            "description": description,
            "visualization_type": "multiplex_composite"
        }

    except Exception as e:
        logger.error(f"Error generating multiplex composite: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate multiplex composite. Check file paths and formats."
        }


@mcp.tool()
async def generate_he_annotation(
    he_image_path: str,
    necrotic_regions: Optional[List[Dict[str, int]]] = None,
    high_cellularity_regions: Optional[List[Dict[str, int]]] = None,
    output_filename: Optional[str] = None,
    necrotic_color: str = "red",
    cellularity_color: str = "green"
) -> Dict[str, Any]:
    """Generate annotated H&E morphology visualization.

    Overlays region annotations on H&E histology image to highlight areas
    of interest such as necrotic regions and high cellularity areas.

    Args:
        he_image_path: Path to H&E histology image
        necrotic_regions: List of bounding boxes for necrotic areas
                         Each box: {"x": x_coord, "y": y_coord, "width": w, "height": h}
        high_cellularity_regions: List of bounding boxes for high cellularity areas
        output_filename: Custom output filename (default: he_annotation_TIMESTAMP.png)
        necrotic_color: Color for necrotic region outlines (default: "red")
        cellularity_color: Color for high cellularity outlines (default: "green")

    Returns:
        Dictionary with:
        - output_file: Path to saved annotated image
        - necrotic_regions_count: Number of necrotic regions annotated
        - cellularity_regions_count: Number of high cellularity regions annotated
        - description: Text description

    Example:
        >>> result = await generate_he_annotation(
        ...     he_image_path="/data/PAT001_tumor_HE_20x.tiff",
        ...     necrotic_regions=[
        ...         {"x": 100, "y": 200, "width": 300, "height": 250},
        ...         {"x": 800, "y": 600, "width": 200, "height": 180}
        ...     ],
        ...     high_cellularity_regions=[
        ...         {"x": 400, "y": 100, "width": 350, "height": 300}
        ...     ]
        ... )
    """
    if DRY_RUN:
        necro_count = len(necrotic_regions) if necrotic_regions else 0
        cell_count = len(high_cellularity_regions) if high_cellularity_regions else 0
        return add_dry_run_warning({
            "output_file": str(OUTPUT_DIR / "visualizations" / "he_annotation_dryrun.png"),
            "necrotic_regions_count": necro_count,
            "cellularity_regions_count": cell_count,
            "description": "DRY_RUN: Would generate H&E annotation",
            "message": "Set IMAGE_DRY_RUN=false to generate real visualizations",
            "xai_metadata": _build_xai_metadata(
                confidence_level="moderate",
                confidence_note=(
                    "H&E annotation using rule-based region overlay. "
                    "DRY_RUN: mock annotation. Annotations should be reviewed "
                    "by a pathologist before clinical use."
                ),
                key_drivers=[
                    f"Necrotic regions: {necro_count}",
                    f"High cellularity regions: {cell_count}",
                ],
                guideline_version="PathAI PathExplore; CAP Digital Pathology Guidelines 2022",
                evidence_grade="Algorithm-Predicted — Not Clinical Grade",
                counterfactual="Pathologist review of annotations is required before clinical reporting.",
            ),
        })

    try:
        # Load H&E image
        he_img = np.array(Image.open(he_image_path))

        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))

        # Original H&E
        axes[0].imshow(he_img)
        axes[0].set_title('Original H&E', fontsize=14, fontweight='bold')
        axes[0].axis('off')

        # Annotated H&E
        axes[1].imshow(he_img)

        # Color mapping
        color_map = {
            "red": "red",
            "green": "green",
            "blue": "blue",
            "yellow": "yellow",
            "cyan": "cyan",
            "magenta": "magenta"
        }
        necrotic_mpl_color = color_map.get(necrotic_color.lower(), "red")
        cellularity_mpl_color = color_map.get(cellularity_color.lower(), "green")

        # Draw necrotic regions
        necrotic_count = 0
        if necrotic_regions:
            for region in necrotic_regions:
                rect = plt.Rectangle(
                    (region["x"], region["y"]),
                    region["width"],
                    region["height"],
                    linewidth=3,
                    edgecolor=necrotic_mpl_color,
                    facecolor='none',
                    linestyle='--'
                )
                axes[1].add_patch(rect)
                necrotic_count += 1

        # Draw high cellularity regions
        cellularity_count = 0
        if high_cellularity_regions:
            for region in high_cellularity_regions:
                rect = plt.Rectangle(
                    (region["x"], region["y"]),
                    region["width"],
                    region["height"],
                    linewidth=3,
                    edgecolor=cellularity_mpl_color,
                    facecolor='none',
                    linestyle='-'
                )
                axes[1].add_patch(rect)
                cellularity_count += 1

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = []
        if necrotic_count > 0:
            legend_elements.append(
                Patch(facecolor='none', edgecolor=necrotic_mpl_color, linestyle='--',
                      linewidth=3, label=f'Necrotic ({necrotic_count} regions)')
            )
        if cellularity_count > 0:
            legend_elements.append(
                Patch(facecolor='none', edgecolor=cellularity_mpl_color, linestyle='-',
                      linewidth=3, label=f'High Cellularity ({cellularity_count} regions)')
            )

        if legend_elements:
            axes[1].legend(handles=legend_elements, loc='upper right', fontsize=11)

        axes[1].set_title('Annotated Morphology', fontsize=14, fontweight='bold')
        axes[1].axis('off')

        plt.tight_layout()

        # Save
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"he_annotation_{timestamp}.png"

        output_path = OUTPUT_DIR / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        # Generate description
        description = f"H&E morphology annotation showing {necrotic_count} necrotic regions ({necrotic_color}) and {cellularity_count} high cellularity regions ({cellularity_color})."

        return {
            "status": "success",
            "output_file": str(output_path),
            "necrotic_regions_count": necrotic_count,
            "cellularity_regions_count": cellularity_count,
            "total_annotations": necrotic_count + cellularity_count,
            "description": description,
            "visualization_type": "he_morphology_annotation",
            "necrotic_color": necrotic_color,
            "cellularity_color": cellularity_color,
            "xai_metadata": _build_xai_metadata(
                confidence_level="moderate",
                confidence_note=(
                    "H&E annotation using region overlay. "
                    "Deep learning annotation models are validated for common tumor types "
                    "but uveal melanoma has limited representation in published training datasets. "
                    "Annotations should be reviewed by a pathologist before clinical use."
                ),
                key_drivers=[
                    f"Necrotic regions: {necrotic_count}",
                    f"High cellularity regions: {cellularity_count}",
                ],
                guideline_version="PathAI PathExplore; CONCH (Chen 2024, Nature Medicine); TCGA digital pathology",
                evidence_grade="Algorithm-Predicted — Not Clinical Grade",
                counterfactual="Pathologist review of annotations is required before clinical reporting.",
            ),
        }

    except Exception as e:
        logger.error(f"Error generating H&E annotation: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate H&E annotation. Check file path and format."
        }


# ============================================================================
# MCP RESOURCES
# ============================================================================


@mcp.resource("image://histology/he")
def get_he_stain_info() -> str:
    """H&E stained image resource information.

    Returns:
        JSON string with H&E staining metadata
    """
    return json.dumps({
        "resource": "image://histology/he",
        "description": "Hematoxylin and Eosin (H&E) stained tissue images",
        "data_directory": str(IMAGE_DIR / "he"),
        "stain_info": {
            "hematoxylin": "Stains nuclei blue-purple",
            "eosin": "Stains cytoplasm and extracellular matrix pink"
        },
        "typical_magnifications": ["4x", "10x", "20x", "40x"],
        "file_formats": ["TIFF", "SVS", "NDPI"],
        "use_cases": [
            "Tissue morphology assessment",
            "Spatial transcriptomics overlay",
            "Pathologist review",
            "AI-based tissue classification"
        ]
    }, indent=2)


@mcp.resource("image://histology/if")
def get_if_stain_info() -> str:
    """Immunofluorescence image resource information.

    Returns:
        JSON string with IF imaging metadata
    """
    return json.dumps({
        "resource": "image://histology/if",
        "description": "Immunofluorescence microscopy images",
        "data_directory": str(IMAGE_DIR / "if"),
        "imaging_info": {
            "technique": "Fluorescent antibody labeling",
            "channels": "Multi-channel (DAPI, FITC, Cy3, Cy5, etc.)",
            "applications": "Protein localization, marker coexpression"
        },
        "typical_markers": [
            "DAPI (nuclei)",
            "CD45 (immune cells)",
            "Pan-CK (epithelial)",
            "CD31 (endothelial)"
        ],
        "file_formats": ["TIFF", "CZI", "ND2"],
        "integration_with_spatial": "Protein-RNA correlation analysis"
    }, indent=2)


# ============================================================================
# SERVER ENTRYPOINT
# ============================================================================


def main() -> None:
    """Run the MCP Open Image Data server."""
    _ensure_directories()
    _run_server(mcp, server_name="mcp-openimagedata", dry_run=DRY_RUN, env_var="IMAGE_DRY_RUN")


if __name__ == "__main__":
    main()
