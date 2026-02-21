---
name: patient-data-ops
description: >
  Guide for managing single-cell and patient data (h5ad, CSV).
  Standardizes data loading, preprocessing, and path management.
---

# Patient Data Operations

This skill ensures consistent handling of sensitive patient data and bioinformatics datasets.

## 📁 Data Hierarchy

Always use these standard paths:
- `data/patient-data/`: Individual patient `.h5ad` or `.csv` files.
- `data/reports/`: Generated analysis reports (PDF/Markdown).
- `data/images/`: Visualizations (UMAP, Heatmaps, PCA).

## 🧬 Handling scRNA-seq Data (`.h5ad`)

When working with `AnnData` objects:
1.  **Normalization**: Ensure `scanpy.pp.normalize_total` and `scanpy.pp.log1p` are applied.
2.  **HVG Selection**: Standardize on 7,000 Highly Variable Genes (HVG) for GEARS compatibility.
3.  **Metadata**: Preserve `cell_type` and `condition` keys in `.obs`.

## 🛠️ Data Preprocessing Tools

Use these standard scripts where possible:
- `generate_synthetic_data.py`: For creating test-safe patient mocks.
- `data_loader.py`: Use the loaders in `src/mcp_[name]` to ensure consistent I/O.

## 🔒 Data Privacy & Security

- **Anonymization**: Never store PII (Patient Identifiable Information) in the repo.
- **Mocking**: Always use synthetic data for unit tests (`tests/unit/mcp-[name]/fixtures/`).
- **Audit Logs**: Every data access tool should trigger a log entry via `shared/common/logging.py`.

## 📊 Data Quality Checklist

Before running simulations:
- [ ] Check for `NaN` values in expression matrices.
- [ ] Verify cell-type labels match the project ontology.
- [ ] Ensure the file size fits within the 4Gi Cloud Run limit.

---

**Use this skill when:**
- Loading new patient datasets.
- Preprocessing scRNA-seq files for GEARS.
- Creating test data fixtures for bioinformatics tools.
