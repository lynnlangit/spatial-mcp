# mcp-cell-classify: Cell Phenotype Classification

MCP server for classifying cell phenotypes from segmentation masks and marker intensity images. Lightweight server (no TensorFlow/DeepCell dependency) designed to work downstream of `mcp-deepcell` segmentation output.

---

## Overview

`mcp-cell-classify` provides cell phenotype classification and visualization through the Model Context Protocol (MCP). It takes segmentation masks (from `mcp-deepcell` or any other segmentation tool) and marker intensity images, then classifies cells by marker expression.

### Why a Separate Server?

- **Lightweight:** No TensorFlow or DeepCell dependency (~200MB Docker image vs ~2GB for mcp-deepcell)
- **Swappable:** Users can substitute their own classification methods (FlowSOM, Leiden, scikit-learn)
- **Independent:** Some workflows only need segmentation + quantification, not classification
- **Python 3.11+:** No TensorFlow version constraints

---

## Tools

### 1. classify_cell_states

Classify cells into functional states (proliferating/quiescent/intermediate) based on a single marker's intensity.

**Parameters:**
- `segmentation_mask_path` (string): Path to segmentation mask (16-bit TIFF label image)
- `intensity_image_path` (string): Path to marker intensity image (16-bit TIFF)
- `marker_name` (string): Name of marker (default: "Ki67")
- `threshold_proliferating` (float): Intensity threshold for proliferating state (default: 50.0)
- `threshold_quiescent` (float): Intensity threshold for quiescent state (default: 20.0)

**Returns:**
```json
{
  "status": "success",
  "total_cells": 1247,
  "state_counts": {"proliferating": 523, "quiescent": 612, "intermediate": 112},
  "classifications_csv": "/output/classifications/classifications_Ki67_seg.csv",
  "classifications": [{"cell_id": 1, "state": "proliferating", "confidence": 0.92}]
}
```

### 2. classify_multi_marker

Classify cells by multiple markers simultaneously for multi-marker phenotyping (e.g., Ki67+/TP53-).

**Parameters:**
- `segmentation_mask_path` (string): Path to segmentation mask (16-bit TIFF label image)
- `marker_images` (list): List of `{"path": "...", "name": "..."}` dicts for each marker
- `thresholds` (dict): Marker name to intensity threshold mapping
- `output_filename` (string, optional): Custom output CSV filename

**Returns:**
```json
{
  "status": "success",
  "total_cells": 1247,
  "phenotype_counts": {
    "Ki67+/TP53+": 120,
    "Ki67+/TP53-": 340,
    "Ki67-/TP53+": 180,
    "Ki67-/TP53-": 607
  },
  "classifications_csv": "/output/classifications/multi_marker_Ki67_TP53_seg.csv",
  "markers_used": ["Ki67", "TP53"]
}
```

### 3. generate_phenotype_visualization

Generate a side-by-side visualization coloring cells by marker expression (positive vs negative).

**Parameters:**
- `original_image_path` (string): Path to original microscopy image
- `segmentation_mask_path` (string): Path to segmentation mask
- `marker_positive_cells` (list[int]): Cell IDs that are marker-positive
- `output_filename` (string, optional): Custom output filename
- `positive_color` (string): Color for positive cells (default: "green")
- `negative_color` (string): Color for negative cells (default: "red")

**Returns:**
```json
{
  "status": "success",
  "output_file": "/output/visualizations/phenotype_viz_20260209.png",
  "positive_cells": 523,
  "negative_cells": 724,
  "percent_positive": 41.9
}
```

---

## XAI Metadata

Every tool returns an `xai_metadata` field with explainability information:

| Field | Description |
|-------|-------------|
| `confidence_level` | `high`, `moderate`, or `low` — how reliable the result is given the inputs |
| `confidence_note` | Why this confidence level was assigned |
| `key_drivers` | 1-3 inputs that most influenced the result |
| `guideline_version` | Specific algorithm or method reference |
| `evidence_grade` | Algorithm-Predicted — Not Clinical Grade |
| `counterfactual` | What would change if a key input were different |

---

## Data Contract

### Input from mcp-deepcell

- **Segmentation mask:** 16-bit TIFF label image (cell IDs as pixel values, 0 = background)
- **Intensity images:** 16-bit TIFF (single channel per marker)

### Output

- **Classification CSV:** Columns include `cell_id`, per-marker intensities, `phenotype`
- **Visualization PNG:** Side-by-side original + phenotype-colored cells (300 DPI)

---

## Workflow

```
mcp-deepcell                          mcp-cell-classify
┌──────────────────────┐              ┌──────────────────────────┐
│  segment_cells       │              │  classify_cell_states    │
│  (DAPI image)        │──mask.tif──►│  (single marker)         │
│                      │              │                          │
│  quantify_markers    │              │  classify_multi_marker   │
│  (mask + markers)    │──csv──────►  │  (multi-marker phenotype)│
│                      │              │                          │
│  generate_seg_overlay│              │  generate_phenotype_viz  │
│  (QC visualization)  │              │  (phenotype coloring)    │
└──────────────────────┘              └──────────────────────────┘
```

### Example: Complete MxIF Analysis

```
Step 1: Segment nuclei (mcp-deepcell)
  Tool: segment_cells
  Input: dapi_1024x1024.tif, model=nuclear
  Output: segmentation_mask.tif

Step 2: Quantify markers (mcp-deepcell)
  Tool: quantify_markers
  Input: segmentation_mask.tif + [ki67.tif, tp53.tif]
  Output: per_cell_intensities.csv

Step 3: Classify phenotypes (mcp-cell-classify)
  Tool: classify_multi_marker
  Input: segmentation_mask.tif + [ki67.tif, tp53.tif] + thresholds
  Output: phenotype_classifications.csv

Step 4: Visualize (mcp-cell-classify)
  Tool: generate_phenotype_visualization
  Input: original_image + mask + positive cell IDs
  Output: phenotype_visualization.png
```

---

## Installation

> **Standard setup:** See [Server Installation Guide](../../docs/reference/shared/server-installation.md) for venv creation, pip install, and Claude Desktop config.

### Docker

```bash
docker build -t mcp-cell-classify .
docker run -p 3009:3009 \
  -e CELL_CLASSIFY_DRY_RUN=false \
  -e MCP_TRANSPORT=sse \
  mcp-cell-classify
```

### Cloud Run

```bash
./deploy.sh precision-medicine-poc us-central1
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CELL_CLASSIFY_OUTPUT_DIR` | `/workspace/output` | Output directory |
| `CELL_CLASSIFY_DRY_RUN` | `true` | Enable mock mode (no real processing) |
| `MCP_TRANSPORT` | `stdio` | Transport protocol (stdio or sse) |
| `MCP_PORT` | `3009` | Server port (SSE mode) |

### Resource Requirements

- **Memory:** 2 GiB (lightweight, no TensorFlow)
- **CPU:** 1 vCPU
- **Disk:** Minimal (no model cache needed)

---

## MCP Client Configuration

### Claude Desktop (Local)

```json
{
  "mcpServers": {
    "cell-classify": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/servers/mcp-cell-classify", "python", "-m", "mcp_cell_classify"],
      "env": {
        "CELL_CLASSIFY_OUTPUT_DIR": "/workspace/output",
        "CELL_CLASSIFY_DRY_RUN": "true"
      }
    }
  }
}
```

### Cloud Run (Production)

```json
{
  "mcpServers": {
    "cell-classify": {
      "url": "https://mcp-cell-classify-<hash>.a.run.app/sse",
      "transport": "sse"
    }
  }
}
```

---

## Related Servers

- **mcp-deepcell** — Deep learning cell segmentation + marker quantification (upstream)
- **mcp-spatialtools** — Spatial transcriptomics analysis
- **mcp-openimagedata** — Histology image processing

---

**Built for the Precision Medicine MCP suite** — Lightweight cell phenotype classification that pairs with mcp-deepcell segmentation.
