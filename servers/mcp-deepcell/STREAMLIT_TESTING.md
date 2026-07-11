# Streamlit App Testing Guide - mcp-deepcell Integration

## Test Environment

**Deployed Streamlit Apps:**
- Main: https://streamlit-mcp-chat-305650208648.us-central1.run.app
- Students: https://streamlit-mcp-chat-students-305650208648.us-central1.run.app

**mcp-deepcell Service:**
- URL: https://mcp-deepcell-ondu7mwjpa-uc.a.run.app
- Status: Production (real DeepCell-TF segmentation)
- Tools: 3 (segment_cells, quantify_markers, generate_segmentation_overlay)

**Test Data:**
- Location: `gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/`
- Permissions: Cloud Run service account has Storage Object Viewer role

---

## Test Cases

### Test 1: Nuclear Segmentation (Basic)
**Prompt:**
```
Segment cells in the test image:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif
- Use nuclear segmentation model
- Minimum cell size: 100 pixels
```

**Expected Results:**
- ~30 cells detected
- Segmentation mask with unique cell IDs
- Quality metrics (mean cell size, total cells)

---

### Test 2: Cell State Classification
**Prompt:**
```
Classify cell states using Ki67 marker:
- Nuclear image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif
- Marker image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/ki67_512x512.tif
- Marker name: Ki67
- Intensity threshold: 5000
```

**Expected Results:**
- ~30% proliferating cells (Ki67+)
- ~70% quiescent cells (Ki67-)
- Classification results with cell counts per phenotype

---

### Test 3: Large Image Segmentation
**Prompt:**
```
Segment the large test image:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_2048x2048.tif
- Model: nuclear
- Minimum cell size: 200 pixels
- Tile size: 512x512
```

**Expected Results:**
- ~480 cells detected
- Automatic tiling for large image
- Longer processing time (~30-60s on first run, ~5-10s subsequent runs)

---

### Test 4: Multi-Marker Phenotyping
**Prompt:**
```
Perform multi-marker cell phenotyping:
1. Segment cells from: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_1024x1024.tif
2. Classify with Ki67: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/ki67_1024x1024.tif (threshold: 5000)
3. Classify with TP53: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/tp53_1024x1024.tif (threshold: 4000)
4. Generate phenotype visualization
```

**Expected Results:**
- ~120 cells with multi-marker phenotypes
- Combinations: Ki67+/TP53+, Ki67+/TP53-, Ki67-/TP53+, Ki67-/TP53-
- Visualization showing phenotype distribution

---

### Test 5: Membrane Segmentation
**Prompt:**
```
Segment cells using membrane marker:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/membrane_512x512.tif
- Model: membrane (Mesmer)
- Minimum cell size: 150 pixels
```

**Expected Results:**
- ~30 cells with membrane boundaries
- Larger segmentation masks (whole cell vs nuclear only)
- Quality metrics showing cell size distribution

---

## Verification Checklist

After running each test, verify:

- [ ] Tool executed without errors
- [ ] Cell counts match expected ranges
- [ ] Classification percentages match synthetic data characteristics
- [ ] GCS images loaded successfully
- [ ] DeepCell models cached (faster on subsequent runs)
- [ ] Output includes quality metrics

---

## Performance Benchmarks

**First Run (Cold Start):**
- Model download: ~30-45s
- 512x512 segmentation: ~5-10s
- Total: ~35-55s

**Subsequent Runs (Warm):**
- 512x512 segmentation: ~2-5s
- 1024x1024 segmentation: ~8-15s
- 2048x2048 segmentation: ~30-60s (with tiling)

---

## Troubleshooting

**Issue: "Permission denied" for GCS images**
- Verify service account has Storage Object Viewer role:
  ```bash
  gsutil iam get gs://sample-inputs-patientone
  ```

**Issue: "Model download timeout"**
- Cloud Run timeout is 300s - should be sufficient
- Check Cloud Run logs for errors

**Issue: "Tool not found"**
- Verify mcp-deepcell status is "production" in mcp_config.py
- Confirm service is in "Production Servers" category

**Issue: "Segmentation quality poor"**
- Try adjusting min_cell_size parameter
- Check that image is 16-bit TIFF format
- Verify correct model type (nuclear vs membrane)

---

## Next Steps After Testing

1. Document any issues or unexpected behavior
2. Update prompt library with successful examples
3. Update high-level documentation (README, EXEC_SUMMARY)
4. Consider adding more diverse test images
5. Benchmark performance with real MxIF images
