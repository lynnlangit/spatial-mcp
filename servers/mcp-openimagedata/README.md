# mcp-openimagedata: Histology and MxIF Image Processing

MCP server for histology (H&E) and multiplexed immunofluorescence (MxIF) image processing, spatial registration, and visualization generation for microscopy analysis.

## Overview

`mcp-openimagedata` provides AI-accessible image processing tools through the Model Context Protocol (MCP). This server enables image fetching, spatial registration with transcriptomics data, feature extraction, MxIF channel compositing, and morphology annotation for brightfield and fluorescence microscopy.

### Imaging Workflows

**H&E (Brightfield Microscopy):**
- Chromogenic stains (Hematoxylin=blue nuclei, Eosin=pink cytoplasm)
- Use for: Tissue morphology assessment, necrosis identification, cellularity estimation
- Workflow: Load image → Annotate regions (`generate_he_annotation`) → Visual assessment
- **No cell segmentation required** for morphology assessment

**MxIF (Fluorescence Microscopy):**
- Multiple fluorescent antibody markers on single tissue section
- Use for: Quantitative cell phenotyping, marker co-expression analysis
- Workflow: Load channels → Composite (`generate_multiplex_composite`) → Segment with mcp-deepcell → Quantify
- **Requires mcp-deepcell** for cell segmentation and counting

### Key Features

- 📥 **Image Fetching** - Retrieve H&E and MxIF histology images
- 🖼️ **Spatial Registration** - Align histology images with spatial transcriptomics coordinates
- 🔍 **Feature Extraction** - Extract texture, morphology, and intensity features from images
- 🎨 **MxIF Compositing** - Combine 2-7 fluorescence channels into RGB composites (fluorescence only)
- 📍 **H&E Annotation** - Annotate necrotic regions and high cellularity areas on brightfield H&E
- ⚡ **DRY_RUN Mode** - Test workflows with synthetic data

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

> **Standard setup:** See [Server Installation Guide](../../docs/reference/shared/server-installation.md) for venv creation, pip install, and Claude Desktop config.

### Environment Variables

Create a `.env` file in the server directory:

```bash
# Data directories
IMAGE_DATA_DIR=data/patient-data/PAT001-OVC-2025/imaging
IMAGE_CACHE_DIR=data/patient-data/PAT001-OVC-2025/imaging/cache

# Output directory for visualizations
IMAGE_OUTPUT_DIR=/workspace/output

# Development mode (uses mocks instead of real processing)
IMAGE_DRY_RUN=true
```

> See [DRY_RUN Mode Guide](../../docs/reference/shared/dry-run-mode.md) for details on mock mode.

## Usage

### Running the Server

**Standalone mode (stdio):**

```bash
python -m mcp_openimagedata
```

**With Claude Desktop:**

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "openimagedata": {
      "command": "/path/to/spatial-mcp/servers/mcp-openimagedata/venv/bin/python",
      "args": ["-m", "mcp_openimagedata"],
      "cwd": "/path/to/spatial-mcp/servers/mcp-openimagedata",
      "env": {
        "PYTHONPATH": "/path/to/spatial-mcp/servers/mcp-openimagedata/src",
        "IMAGE_DATA_DIR": "data/patient-data/PAT001-OVC-2025/imaging",
        "IMAGE_OUTPUT_DIR": "/workspace/output",
        "IMAGE_DRY_RUN": "false"
      }
    }
  }
}
```

**Important:**
- Use the full path to the venv Python executable
- Set `IMAGE_DRY_RUN=false` for real image processing
- Ensure sufficient disk space for large TIFF files

## Available Tools

### 1. fetch_histology_image

Retrieve tissue histology images (H&E or immunofluorescence).

**Parameters:**
- `image_id` (string): Unique identifier for the image
- `stain_type` (string, optional): Type of staining - "he" (H&E) or "if" (immunofluorescence) (default: "he")
- `resolution` (string, optional): Image resolution - "high", "medium", or "low" (default: "high")

**Returns:**
```json
{
  "image_path": "/images/he/sample_001_high.tif",
  "dimensions": {"width": 4096, "height": 4096},
  "file_size_mb": 50.0,
  "metadata": {
    "stain_type": "he",
    "magnification": "20x",
    "format": "TIFF"
  }
}
```

**Example usage with Claude:**
```
Fetch the H&E histology image for patient PAT001:
- Image ID: PAT001_tumor_HE_20x
- Stain type: he
- Resolution: high
```

**Output:** Downloaded image file with metadata.

---

### 2. register_image_to_spatial

Align histology images with spatial transcriptomics spot coordinates.

**Parameters:**
- `image_path` (string): Path to histology image
- `spatial_coordinates_file` (string): Path to CSV file with spatial spot coordinates
- `output_file` (string): Path for registered image output
- `registration_method` (string, optional): Registration method - "affine", "rigid", or "deformable" (default: "affine")

**Returns:**
```json
{
  "registered_image": "/output/registered_image.tif",
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
    "method": "affine"
  }
}
```

**Example usage with Claude:**
```
Register H&E image to spatial transcriptomics coordinates:
- Image: /images/PAT001_HE.tif
- Coordinates: /data/spatial/visium_coordinates.csv
- Output: /images/registered/PAT001_HE_registered.tif
- Method: affine
```

**Output:** Spatially registered image aligned to transcriptomics spot coordinates.

**Use cases:**
- Correlate tissue morphology with gene expression patterns
- Overlay H&E features on spatial transcriptomics heatmaps
- Identify regions of interest for spatial analysis

---

### 3. extract_image_features

Extract computer vision features from histology images for analysis.

**Parameters:**
- `image_path` (string): Path to histology image
- `feature_type` (string, optional): Type of features - "texture", "morphology", or "intensity" (default: "texture")
- `roi_coordinates` (list, optional): List of ROI bounding boxes `[(x1,y1,x2,y2), ...]` (default: whole image)

**Returns:**
```json
{
  "features": [0.45, 0.67, 0.23, ...],
  "feature_names": ["texture_feature_0", "texture_feature_1", ...],
  "roi_count": 5,
  "processing_time_seconds": 2.5,
  "feature_statistics": {
    "mean": 0.5,
    "std": 0.15,
    "min": 0.05,
    "max": 0.95
  }
}
```

**Example usage with Claude:**
```
Extract texture features from tumor regions:
- Image: /images/PAT001_HE.tif
- Feature type: texture
- ROI coordinates: [(100,100,300,300), (500,200,700,400)]
```

**Feature types:**
- **texture** (25 features): LBP histogram (10) + GLCM properties across 2 distances (10) + summary stats (5)
- **morphology** (15 features): Connected-component regionprops — area, perimeter, solidity, eccentricity (mean/std/median each) + circularity (mean/std) + object count
- **intensity** (10 features): mean, std, median, min, max, skewness, kurtosis, p25, p75, Shannon entropy

**Output:** Feature vectors for downstream analysis (correlation with spatial expression, clustering)

---

## Visualization Tools

The following visualization tools generate publication-quality PNG images:

### 4. generate_multiplex_composite

Generate RGB composite from multiplex immunofluorescence (MxIF) channels.

**⚠️ FLUORESCENCE ONLY:** This tool is designed for MxIF fluorescence images. Do NOT use with H&E brightfield images.

**Parameters:**
- `channel_paths` (list): List of paths to fluorescence channel images (1-7 channels, grayscale TIFF/PNG)
- `channel_names` (list): List of marker names matching channel order (e.g., ["DAPI", "Ki67", "TP53"])
- `channel_colors` (list, optional): List of colors for each channel - "blue", "green", "red", "cyan", "magenta", "yellow", "white" (default: ["blue", "green", "red", ...])
- `output_filename` (string, optional): Custom output filename (default: auto-generated with timestamp)
- `normalize` (boolean, optional): Normalize each channel to 0-1 range (default: True)

**Returns:**
```json
{
  "status": "success",
  "output_file": "/workspace/output/visualizations/multiplex_composite_20250108_144200.png",
  "channels_combined": 3,
  "channel_info": [
    {"name": "DAPI", "color": "blue"},
    {"name": "Ki67", "color": "green"},
    {"name": "TP53", "color": "red"}
  ],
  "image_dimensions": {"width": 2048, "height": 2048},
  "description": "RGB composite combining 3 channels: DAPI (blue), Ki67 (green), TP53 (red).",
  "visualization_type": "multiplex_composite"
}
```

**Example usage with Claude:**
```
Create RGB composite from multiplex IF channels:
- Channels:
  * /data/Multiplex_DAPI.tiff (nuclear stain)
  * /data/Multiplex_Ki67.tiff (proliferation marker)
  * /data/Multiplex_TP53.tiff (tumor suppressor)
- Channel colors: blue, green, red
- Normalize intensities for each channel
```

**Output:** Multi-panel figure showing:
1. Individual grayscale channels (one per marker)
2. Final RGB composite with all channels combined

**Use cases:**
- Visualize co-localization of multiple markers
- Identify double-positive cells (e.g., TP53+/Ki67+ = yellow in red+green composite)
- Generate publication-quality multiplex IF figures
- Validate channel alignment and crosstalk

**Color combinations:**
- **2 channels:** Blue + Green, Green + Red, Blue + Red
- **3 channels:** Blue (DAPI) + Green (marker 1) + Red (marker 2)
- **4+ channels:** Use cyan, magenta, yellow for additional markers

**Technical details:**
- Each channel is normalized to 0-1 range (if `normalize=True`)
- RGB composite is created by weighted addition: `RGB = Σ(channel_i × color_i)`
- Output is clipped to [0, 255] and saved as 8-bit RGB PNG
- Supports up to 7 channels (though 2-4 is typical)

---

### 5. generate_he_annotation

Generate annotated H&E morphology visualization with region overlays.

**Parameters:**
- `he_image_path` (string): Path to H&E histology image
- `necrotic_regions` (list, optional): List of bounding boxes for necrotic regions (default: [])
  - Each region: `{"x": int, "y": int, "width": int, "height": int}`
- `high_cellularity_regions` (list, optional): List of bounding boxes for high cellularity regions (default: [])
  - Each region: `{"x": int, "y": int, "width": int, "height": int}`
- `output_filename` (string, optional): Custom output filename (default: auto-generated)
- `necrotic_color` (string, optional): Color for necrotic region boxes (default: "red")
- `cellularity_color` (string, optional): Color for cellularity region boxes (default: "green")

**Returns:**
```json
{
  "status": "success",
  "output_file": "/workspace/output/visualizations/he_annotation_20250108_144230.png",
  "necrotic_regions_count": 2,
  "cellularity_regions_count": 3,
  "description": "H&E annotation showing 2 necrotic regions and 3 high cellularity regions.",
  "visualization_type": "he_morphology_annotation"
}
```

**Example usage with Claude:**
```
Annotate H&E slide with pathology findings:
- Image: /data/HE_slide.tif
- Necrotic regions (red dashed boxes):
  * {"x": 500, "y": 300, "width": 200, "height": 150}
  * {"x": 1200, "y": 800, "width": 180, "height": 140}
- High cellularity regions (green solid boxes):
  * {"x": 200, "y": 200, "width": 250, "height": 200}
  * {"x": 900, "y": 400, "width": 300, "height": 250}
  * {"x": 1500, "y": 600, "width": 220, "height": 180}
```

**Output:** Side-by-side figure showing:
1. Original H&E image (unmodified)
2. Annotated H&E with colored bounding boxes and legend

**Use cases:**
- Visualize pathologist annotations on H&E
- Highlight regions of interest for downstream analysis
- Document necrotic areas and tumor cellularity
- Generate annotated figures for pathology reports

**Region types:**
- **Necrotic regions** (default: red dashed boxes):
  - Cell death zones
  - Hypoxic areas
  - Therapy-induced necrosis

- **High cellularity regions** (default: green solid boxes):
  - Dense tumor areas
  - Lymphocyte infiltration
  - Proliferative zones

**Technical details:**
- Bounding boxes drawn as matplotlib rectangles
- Dashed lines for necrotic (pathology), solid for cellularity (biology)
- Legend shows counts for each region type
- Coordinates are in pixel units (x, y from top-left origin)

---

## Example Workflows

### Complete Multiplex IF Analysis Workflow

**End-to-end multiplex imaging analysis:**

```
Claude, analyze the multiplex IF slide (DAPI + Ki67 + TP53):

STEP 1: Quality assessment
- Check all 3 channels for artifacts
- Verify signal-to-noise ratio

STEP 2: Generate RGB composite
- Combine channels: DAPI (blue) + Ki67 (green) + TP53 (red)
- Normalize intensities
- Look for yellow cells (Ki67+/TP53+ double-positive)

STEP 3: Cell segmentation
- Use DAPI channel for nuclear segmentation (deepcell server)
- Generate segmentation mask

STEP 4: Measure marker intensities
- For each segmented cell:
  - Measure mean Ki67 intensity
  - Measure mean TP53 intensity

STEP 5: Phenotype classification and visualization
- Classify cells: TP53+/Ki67+, TP53+/Ki67-, TP53-/Ki67+, TP53-/Ki67-
- Generate phenotype visualization (deepcell server)

STEP 6: Report results
- Distribution of 4 phenotypes
- Spatial patterns (clustered vs. dispersed)
- Clinical interpretation
```

### H&E Registration and Annotation Workflow

**Correlate H&E morphology with IF markers:**

```
Claude, correlate H&E and CD8 IF for Patient-001:

STEP 1: Register images
- Fixed: /data/HE_slide.tif (reference)
- Moving: /data/IF_CD8.tiff
- Use affine registration

STEP 2: Assess H&E quality
- Check for tissue folding or artifacts

STEP 3: Identify regions on H&E
- Necrotic regions: Low cellularity, eosinophilic debris
- High cellularity regions: Dense tumor nests

STEP 4: Annotate H&E
- Draw bounding boxes around:
  * Necrotic areas (red dashed)
  * High cellularity areas (green solid)

STEP 5: Correlate with CD8 IF
- Overlay CD8+ cell locations on annotated H&E
- Quantify CD8+ density in each region type

STEP 6: Report findings
- CD8+ infiltration in high vs. low cellularity regions
- Necrotic areas exclude immune cells
- Spatial correlation between morphology and immune landscape
```

### Multi-Channel Composite Workflow

**Generate composite for 5-plex IF:**

```
Claude, create composite from 5-plex IF panel:

Channels:
1. DAPI (nuclear) → blue
2. CD3 (T-cells) → green
3. CD8 (cytotoxic T-cells) → red
4. PD-L1 (checkpoint) → cyan
5. Ki67 (proliferation) → magenta

Generate multiplex composite:
- Normalize all channels
- Save individual channels and composite
- Look for:
  * CD3+/CD8+ cells (green + red = yellow)
  * PD-L1+/Ki67+ cells (cyan + magenta)
  * Spatial distribution patterns

Expected output:
- 6-panel figure (5 individual + 1 composite)
- Multi-colored cells indicating co-expression
```

## XAI Metadata

Every tool returns an `xai_metadata` field with explainability information:

| Field | Description |
|-------|-------------|
| `confidence_level` | `high`, `moderate`, or `low` — how reliable the result is given the inputs |
| `confidence_note` | Why this confidence level was assigned |
| `key_drivers` | 1-3 inputs that most influenced the result |
| `guideline_version` | Specific algorithm or method reference |
| `evidence_grade` | Visualization Only or Algorithm-Predicted — Not Clinical Grade |
| `counterfactual` | What would change if a key input were different |

## Available Resources

### image://formats

Get information about supported imaging formats and requirements.

**Example:**
```
What image formats are supported?
```

### image://registration-methods

Get details about available registration algorithms.

**Example:**
```
What registration methods are available?
```

## Data Format Requirements

### Input Images

**Fluorescence (IF):**
- **Formats:** TIFF (16-bit preferred), PNG (8-bit)
- **Channels:** Single-channel grayscale per marker
- **Size:** Up to 4096 × 4096 pixels per channel
- **Bit depth:** 8-bit or 16-bit

**Brightfield (H&E):**
- **Formats:** TIFF, PNG, JPEG
- **Channels:** RGB color image
- **Size:** Variable (whole slide images supported via tiling)
- **Resolution:** Typically 0.25-0.5 microns/pixel

### Bounding Box Format

For region annotations:
```json
{
  "x": 500,        // X coordinate of top-left corner (pixels)
  "y": 300,        // Y coordinate of top-left corner (pixels)
  "width": 200,    // Width in pixels
  "height": 150    // Height in pixels
}
```

Origin is top-left corner (0, 0). Positive X goes right, positive Y goes down.

## Development

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=src/mcp_openimagedata --cov-report=html
```

**Run specific test:**
```bash
pytest tests/test_registration.py -v
```

### Code Quality

**Format code:**
```bash
black src/ tests/
```

**Lint code:**
```bash
ruff check src/ tests/
```

**Type checking:**
```bash
mypy src/
```

## Architecture

### Implementation Status: 100% Real (all 5 tools production-ready)

- **fetch_histology_image**: PIL-based image loading with glob fallback for partial ID matching
- **register_image_to_spatial**: scikit-image registration — Otsu tissue detection, bbox-based affine/rigid estimation, phase-cross-correlation refinement for deformable; supports Visium and generic x/y coordinate formats
- **extract_image_features**: scikit-image feature extraction — LBP + GLCM texture (25 features), connected-component morphology (15 features), intensity statistics + entropy (10 features); per-ROI support
- **generate_multiplex_composite**: Full RGB channel blending for 1-7 fluorescence channels
- **generate_he_annotation**: matplotlib-based morphology annotation with region overlays

### Design Principles

1. **Visual Validation** - Always generate visualizations for quality control
2. **Flexible Compositing** - Support 1-7 channels with customizable colors
3. **Publication Quality** - 300 DPI PNG outputs suitable for papers
4. **Modular Design** - Tools work independently or as part of workflows

### Directory Structure

```
mcp-openimagedata/
├── src/
│   └── mcp_openimagedata/
│       ├── __init__.py
│       ├── __main__.py
│       └── server.py          # Main server implementation
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   └── test_server.py         # Tool tests
├── pyproject.toml             # Project configuration
└── README.md
```

## Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `IMAGE_DATA_DIR` | `data/patient-data/PAT001-OVC-2025/imaging` | Directory for image datasets |
| `IMAGE_CACHE_DIR` | `data/patient-data/PAT001-OVC-2025/imaging/cache` | Directory for cached files |
| `IMAGE_OUTPUT_DIR` | `/workspace/output` | Directory for output files |
| `IMAGE_DRY_RUN` | `false` | Enable mock mode (no real processing) |
| `IMAGE_LOG_LEVEL` | `INFO` | Logging level |

> See [DRY_RUN Mode Guide](../../docs/reference/shared/dry-run-mode.md) for details on mock mode.

## Troubleshooting

### Server won't start

- **Check Python version:** Must be 3.11+
- **Verify dependencies:** Run `pip install -e .`
- **Check environment variables:** Ensure directories exist or are writable

### Image registration fails

- **Enable dry-run mode:** Set `IMAGE_DRY_RUN=true` for testing
- **Check image formats:** Ensure both images are readable
- **Verify dimensions:** Images should be roughly same size
- **Review logs:** Check stderr output for details

### Multiplex composite looks wrong

- **Check channel order:** Ensure channels match marker names
- **Verify normalization:** Try `normalize=true` if intensities differ greatly
- **Check channel alignment:** Ensure channels are spatially aligned
- **Adjust colors:** Try different color combinations for clarity

### H&E annotation not visible

- **Check bounding box coordinates:** Ensure boxes are within image bounds
- **Verify box sizes:** Very small boxes may not be visible
- **Check colors:** Use contrasting colors (red, green work well on H&E)
- **Increase linewidth:** Modify code to use thicker lines if needed

## License

See the main repository LICENSE file.

## Support

- **Issues:** https://github.com/lynnlangit/precision-medicine-mcp/issues
- **Documentation:** See main repository docs/
- **MCP Specification:** https://modelcontextprotocol.io/

## Related Servers

Part of the Precision Medicine MCP suite:

- **mcp-deepcell** - Cell segmentation and phenotype visualization
- **mcp-spatialtools** - Spatial transcriptomics analysis
- **mcp-epic** - Clinical EHR data (FHIR)
- **mcp-multiomics** - Multi-omics integration
- **mcp-fgbio** - Genomic reference data

---

**Built for the Precision Medicine MCP suite** - Enables AI-driven histology image processing integrated with spatial, cellular, and clinical data.
