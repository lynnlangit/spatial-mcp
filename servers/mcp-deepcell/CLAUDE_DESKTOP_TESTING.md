# Testing mcp-deepcell with Claude Desktop

**Cloud Run Service:** https://mcp-deepcell-ondu7mwjpa-uc.a.run.app

This guide walks through testing the production mcp-deepcell deployment via Claude Desktop.

---

## Setup

### 1. Update Claude Desktop Config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "deepcell": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-fetch",
        "https://mcp-deepcell-ondu7mwjpa-uc.a.run.app/sse"
      ]
    }
  }
}
```

**Note:** This connects to the Cloud Run production service, not local.

### 2. Restart Claude Desktop

Quit and relaunch Claude Desktop completely.

### 3. Verify Connection

Prompt:
```
What MCP servers are available?
```

Expected: Should list "deepcell" with 3 tools.

---

## Test Suite

### Test 1: List Available Tools

**Prompt:**
```
What tools are available from the deepcell server?
```

**Expected Output:**
- `segment_cells` - Nuclear and membrane segmentation
- `quantify_markers` - Per-cell marker intensity quantification
- `generate_segmentation_overlay` - Boundary visualization

> **Note:** Classification tools (`classify_cell_states`, `generate_phenotype_visualization`) have moved to **mcp-cell-classify**.

---

### Test 2: Nuclear Segmentation (512×512)

**Prompt:**
```
Use the deepcell server to segment cells in this image:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif
- Model: nuclear
- Minimum cell size: 100 pixels

Tell me how many cells were detected and where the segmentation mask was saved.
```

**Expected Results:**
- First request: ~35s (includes model download)
- Cells detected: ~28-30
- Segmentation mask saved to `/app/data/output/`
- Processing time reported

**Success Criteria:**
- ✅ Request completes without errors
- ✅ Cell count is reasonable (~25-35)
- ✅ Segmentation mask path returned
- ✅ Quality metrics included

---

### Test 3: Segmentation Overlay Visualization

**Prompt:**
```
Generate a segmentation overlay visualization:
- Original image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif
- Segmentation mask: [use path from Test 2]
- Use yellow boundaries with 40% transparency

Show me the visualization.
```

**Expected Results:**
- Processing time: <2s
- PNG visualization created
- Shows side-by-side: original + overlay
- Yellow cell boundaries visible

**Success Criteria:**
- ✅ Visualization generated
- ✅ Boundaries appear on image
- ✅ Cell count matches Test 2

---

### Test 4: Cell State Classification

**Prompt:**
```
Classify cells based on Ki67 marker intensity:
- Segmentation mask: [use path from Test 2]
- Ki67 intensity image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/ki67_512x512.tif
- Marker name: Ki67
- Use median intensity as threshold

Report the percentage of proliferating vs quiescent cells.
```

**Expected Results:**
- Processing time: <2s
- ~25% proliferating (Ki67+)
- ~75% quiescent (Ki67-)
- CSV file created with per-cell classifications

**Success Criteria:**
- ✅ Classification completes
- ✅ Percent proliferating is ~20-30%
- ✅ CSV path returned
- ✅ Summary statistics included

---

### Test 5: Phenotype Visualization

**Prompt:**
```
Generate a phenotype visualization showing proliferating vs quiescent cells:
- Original image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif
- Segmentation mask: [use path from Test 2]
- Classifications CSV: [use path from Test 4]
- Classification column: cell_state
- Color proliferating cells green, quiescent cells red

Show me the visualization.
```

**Expected Results:**
- Processing time: <2s
- PNG with colored cells
- Green cells: proliferating (~25%)
- Red cells: quiescent (~75%)
- Legend with statistics

**Success Criteria:**
- ✅ Visualization created
- ✅ Colors applied correctly
- ✅ Percentages match Test 4

---

### Test 6: Large Image (1024×1024)

**Prompt:**
```
Segment cells in a larger image:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_1024x1024.tif
- Model: nuclear
- Minimum cell size: 100 pixels

How many cells were detected?
```

**Expected Results:**
- First warm request: ~5s (models already cached)
- Cells detected: ~115-125
- No memory issues

**Success Criteria:**
- ✅ Faster than Test 2 (models cached)
- ✅ Cell count scales appropriately (4× area = ~4× cells)
- ✅ No errors or timeouts

---

### Test 7: Membrane Segmentation

**Prompt:**
```
Segment cells using the membrane model:
- Image: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/membrane_512x512.tif
- Model: membrane
- Minimum cell size: 100 pixels

Compare the results to nuclear segmentation.
```

**Expected Results:**
- Processing time: ~35s (first membrane model use) or ~2s (if cached)
- Different cell boundaries than nuclear
- Similar cell count

**Success Criteria:**
- ✅ Membrane model loads successfully
- ✅ Segmentation completes
- ✅ Results differ from nuclear model

---

### Test 8: Multi-Marker Analysis

**Prompt:**
```
Perform a complete multi-marker analysis:

1. Segment nuclei from: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/dapi_512x512.tif

2. Classify Ki67 expression using: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/ki67_512x512.tif

3. Classify TP53 expression using: gs://sample-inputs-patientone/mcp-deepcell-test-data/test_data/tp53_512x512.tif

4. Identify cells that are:
   - Ki67+/TP53+ (proliferating mutant)
   - Ki67+/TP53- (proliferating wild-type)
   - Ki67-/TP53+ (quiescent mutant)
   - Ki67-/TP53- (quiescent wild-type)

Report the distribution of all 4 phenotypes.
```

**Expected Results:**
- Total cells: ~28-30
- Ki67+ ~25%, TP53+ ~40%
- 4 phenotype categories quantified
- Multiple CSV files created

**Success Criteria:**
- ✅ All segmentation and classification steps complete
- ✅ Multi-marker phenotypes identified
- ✅ Percentages match synthetic data characteristics
- ✅ Workflow demonstrates integrated analysis

---

## Performance Verification

### Expected Timing (Cloud Run, 2 vCPU, 4Gi)

| Operation | First Request | Subsequent |
|-----------|---------------|------------|
| Segment 512×512 | ~35s | ~2s |
| Segment 1024×1024 | ~40s | ~5s |
| Classify cells | - | <1s |
| Generate overlay | - | <1s |
| Generate phenotype viz | - | <1s |

**First request includes model download (~30s)**

### Memory & Resources

- Cloud Run should NOT hit memory limit (4Gi sufficient for test images)
- No timeouts (300s limit not reached)
- No 500 errors

---

## Troubleshooting

### Connection Issues

**Symptom:** "Could not connect to deepcell server"

**Solutions:**
1. Verify Cloud Run service is running:
   ```bash
   gcloud run services describe mcp-deepcell \
     --region=us-central1 \
     --format='value(status.conditions[0].status)'
   ```
   Should return: `True`

2. Check Claude Desktop logs for connection errors

3. Verify SSE endpoint responds:
   ```bash
   curl -N -H "Accept: text/event-stream" \
     https://mcp-deepcell-ondu7mwjpa-uc.a.run.app/sse
   ```

### Slow Performance

**Symptom:** All requests take >30s

**Check:**
1. First request is slow (model download) - normal
2. Subsequent requests should be fast (2-5s for small images)
3. Check Cloud Run logs for model cache hits:
   ```bash
   gcloud logging read "resource.labels.service_name=mcp-deepcell \
     AND textPayload=~'Loading cached model'" \
     --limit=10
   ```

### Image Not Found

**Symptom:** "Image file not found" errors

**Solution:**
- Verify GCS paths are correct
- Check Cloud Run has access to GCS bucket
- Use full `gs://` paths, not local paths

### Model Download Timeout

**Symptom:** Request times out after 300s

**Solution:**
- First request may timeout if network is slow
- Retry - models will be cached for next attempt
- Consider increasing timeout in cloudbuild.yaml

---

## Success Checklist

After completing all tests:

- [ ] All 8 tests pass without errors
- [ ] First request ~35s (model download)
- [ ] Subsequent requests <5s
- [ ] Cell counts match expected ranges
- [ ] Visualizations generate correctly
- [ ] Multi-marker workflow completes
- [ ] No memory or timeout errors
- [ ] Cloud Run logs show healthy operation

---

## Next Steps

Once all tests pass:

1. ✅ Mark "Test mcp-deepcell with Claude Desktop" as complete
2. Proceed to update Streamlit apps
3. Test Streamlit integration locally
4. Deploy Streamlit apps to Cloud Run
5. Update high-level documentation

---

**Status:** Ready for testing
