# Imaging Analysis Prompts

Cell segmentation, quantification, and phenotyping for H&E and multiplexed immunofluorescence (MxIF) images.

**Servers used:** mcp-openimagedata (5 tools), mcp-deepcell (3 tools: segment_cells, quantify_markers, generate_segmentation_overlay), mcp-cell-classify (3 tools: classify_cell_states, classify_multi_marker, generate_phenotype_visualization)

---

## Quick Start: Test Data

**GCS Location:** `gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/`

**Available Test Images:**
- `dapi_512x512.tif` - Nuclear stain (DAPI), ~30 cells
- `dapi_1024x1024.tif` - Nuclear stain, ~120 cells
- `dapi_2048x2048.tif` - Nuclear stain, ~480 cells (large image test)
- `ki67_512x512.tif` - Proliferation marker (Ki67)
- `tp53_512x512.tif` - Tumor suppressor marker (TP53)
- `membrane_512x512.tif` - Membrane stain

All images are 16-bit TIFF, synthetic data with known characteristics.

---

## Cell Segmentation

### Nuclear Segmentation (Basic)

Segment cells from DAPI nuclear staining:

```
Segment cells in the test image:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif
- Use nuclear segmentation model
- Minimum cell size: 100 pixels
```

**Expected:** ~30 cells detected with unique IDs and quality metrics.

---

### Membrane Segmentation

Segment whole cells from membrane staining:

```
Segment cells using membrane marker:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/membrane_512x512.tif
- Model: membrane (Mesmer)
- Minimum cell size: 150 pixels
```

**Expected:** ~30 cells with larger masks (whole cell vs nuclear only).

---

### Large Image Segmentation

Process large images with automatic tiling:

```
Segment the large test image:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_2048x2048.tif
- Model: nuclear
- Minimum cell size: 200 pixels
- Tile size: 512x512
```

**Expected:** ~480 cells, automatic tiling, longer processing time (~30-60s first run).

---

## Cell State Classification (mcp-cell-classify)

### Single Marker Phenotyping

Classify proliferating vs quiescent cells using Ki67 (requires segmentation mask from mcp-deepcell):

```
Classify cell states using Ki67 marker:
- Nuclear image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif
- Marker image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/ki67_512x512.tif
- Marker name: Ki67
- Intensity threshold: 5000
```

**Expected:** ~30% Ki67+ (proliferating), ~70% Ki67- (quiescent).

---

### Multi-Marker Phenotyping

Classify cells with multiple markers (uses mcp-deepcell for segmentation, mcp-cell-classify for classification):

```
Perform multi-marker cell phenotyping:
1. Segment cells from: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_1024x1024.tif
2. Classify with Ki67: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/ki67_1024x1024.tif (threshold: 5000)
3. Classify with TP53: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/tp53_1024x1024.tif (threshold: 4000)
4. Generate phenotype visualization
```

**Expected:** ~120 cells with 4 phenotypes (Ki67+/TP53+, Ki67+/TP53-, Ki67-/TP53+, Ki67-/TP53-).

---

## MxIF (Multiplexed Immunofluorescence) Workflow

### Complete MxIF Analysis

End-to-end segmentation (mcp-deepcell) and phenotyping (mcp-cell-classify):

```
For PatientOne MxIF data:
1. Load composite MxIF image (DAPI + Ki67 + TP53 channels)
2. Segment cells using nuclear model (DAPI channel)
3. Classify proliferation status (Ki67 threshold: 5000)
4. Classify TP53 status (TP53 threshold: 4000)
5. Generate segmentation overlay showing cell boundaries
6. Generate phenotype visualization with color-coded markers
7. Report cell counts per phenotype and spatial distribution
```

**Expected:** Cell masks, phenotype classifications, visualizations, spatial statistics.

---

## Visualization

### Segmentation Overlay

Create boundary overlays on original images:

```
Generate segmentation overlay:
- Original image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif
- Segmentation mask: [from previous segmentation]
- Boundary color: red
- Boundary thickness: 2 pixels
```

**Expected:** Original image with cell boundaries highlighted.

---

### Phenotype Visualization (mcp-cell-classify)

Multi-marker phenotype visualization:

```
Generate phenotype visualization:
- Segmentation mask: [from previous segmentation]
- Phenotype classifications: [from multi-marker classification]
- Color scheme: Ki67+ (green), TP53+ (red), Both (yellow), Neither (blue)
```

**Expected:** Color-coded visualization showing phenotype distribution.

---

## Performance Benchmarks

**First Run (Cold Start):**
- Model download: ~30-45s
- 512x512 segmentation: ~5-10s
- Total: ~35-55s

**Subsequent Runs (Warm):**
- 512x512: ~2-5s
- 1024x1024: ~8-15s
- 2048x2048: ~30-60s (with tiling)

---

## Best Practices

### Image Requirements
- **Format:** 16-bit TIFF (grayscale)
- **Size:** Any (auto-tiling for >2048x2048)
- **Staining:** Nuclear (DAPI, Hoechst) or Membrane (pan-cytokeratin, CD45)

### Parameter Selection
- **Nuclear min_cell_size:** 50-200 pixels (depends on magnification)
- **Membrane min_cell_size:** 100-300 pixels (whole cells larger than nuclei)
- **Intensity threshold:** Test on control samples to calibrate

### Quality Control
1. Verify cell count matches manual count (±10%)
2. Check segmentation mask visually for over/under-segmentation
3. Validate marker thresholds on positive/negative controls
4. Compare phenotype percentages to known markers

---

## Common Variables

### Image Paths
- Test data: `gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/`
- PatientOne: `gs://sample-inputs-patientone/PAT001-OVC-2025/imaging/`

### Model Types
- `nuclear` - Nuclear segmentation (DAPI, Hoechst, etc.)
- `membrane` - Whole cell segmentation (Mesmer model)

### Typical Thresholds
- Ki67 (proliferation): 3000-8000 (calibrate per antibody)
- TP53: 2000-6000
- CD8 (T cells): 4000-8000
- Membrane markers: 5000-10000

---

## Related Resources

- **[DeepCell Server README](../../../servers/mcp-deepcell/README.md)** - Segmentation + quantification tools
- **[Cell Classify Server README](../../../servers/mcp-cell-classify/README.md)** - Classification + visualization tools
- **[Imaging Architecture](../architecture/imaging/README.md)** - Complete imaging pipeline including MxIF
- **[Imaging Architecture](../architecture/imaging/README.md)** - H&E vs MxIF comparison

---

**Last Updated:** 2026-02-09
**Status:** ✅ Production ready (mcp-deepcell: segmentation + quantification, mcp-cell-classify: classification + visualization)
