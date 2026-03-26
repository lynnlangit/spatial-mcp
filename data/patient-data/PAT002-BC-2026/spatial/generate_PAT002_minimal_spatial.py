#!/usr/bin/env python3
"""
Generate minimal spatial transcriptomics data for PAT002-BC-2026.
Lightweight h5ad for spatial analysis (fewer cells/genes than quantum version).
Breast cancer ER+/PR+/HER2- with Visium-style spatial coordinates.
"""

import numpy as np
import pandas as pd
import anndata as ad
from pathlib import Path

np.random.seed(44)

N_CELLS = 300
N_GENES = 200
OUTPUT_DIR = Path(__file__).parent
OUTPUT_FILE = OUTPUT_DIR / "PAT002_minimal_spatial.h5ad"

print("=" * 60)
print("Generating Minimal Spatial Data for PAT002-BC-2026")
print("=" * 60)

# --- Spatial coordinates and cell types ---
cell_types = []
spatial_x = []
spatial_y = []

# Tumor core (luminal, center)
n_tumor = 120
spatial_x.extend(np.random.normal(50, 10, n_tumor))
spatial_y.extend(np.random.normal(50, 10, n_tumor))
cell_types.extend(["tumor_luminal"] * n_tumor)

# Stroma / CAFs (ring around tumor)
n_stroma = 60
spatial_x.extend(np.random.normal(50, 20, n_stroma))
spatial_y.extend(np.random.normal(50, 20, n_stroma))
cell_types.extend(["stroma_CAF"] * n_stroma)

# CD8+ T cells (clustered at margin — warm TME)
n_cd8 = 40
spatial_x.extend(np.random.normal(30, 8, n_cd8))
spatial_y.extend(np.random.normal(70, 8, n_cd8))
cell_types.extend(["CD8_T"] * n_cd8)

# Macrophages (scattered)
n_macro = 30
spatial_x.extend(np.random.uniform(20, 80, n_macro))
spatial_y.extend(np.random.uniform(20, 80, n_macro))
cell_types.extend(["macrophage"] * n_macro)

# B cells (tertiary lymphoid structure)
n_b = 20
spatial_x.extend(np.random.normal(75, 5, n_b))
spatial_y.extend(np.random.normal(75, 5, n_b))
cell_types.extend(["B_cell"] * n_b)

# Fill remaining with endothelial + adipocytes
remaining = N_CELLS - len(cell_types)
n_endo = remaining // 2
n_adipo = remaining - n_endo
spatial_x.extend(np.random.uniform(15, 85, n_endo))
spatial_y.extend(np.random.uniform(15, 85, n_endo))
cell_types.extend(["endothelial"] * n_endo)
spatial_x.extend(np.random.normal(10, 5, n_adipo))
spatial_y.extend(np.random.normal(10, 5, n_adipo))
cell_types.extend(["adipocyte"] * n_adipo)

spatial_x = np.array(spatial_x[:N_CELLS])
spatial_y = np.array(spatial_y[:N_CELLS])
cell_types = cell_types[:N_CELLS]

# --- Gene expression ---
# Key genes for breast cancer spatial analysis
key_genes = [
    # Hormone receptors / luminal
    "ESR1", "PGR", "GATA3", "FOXA1", "XBP1", "TFF1",
    # Cytokeratins
    "KRT8", "KRT18", "KRT19", "EPCAM",
    # Oncogenes
    "PIK3CA", "AKT1", "CCND1", "MYC", "MTOR",
    # Proliferation
    "MKI67", "PCNA", "TOP2A",
    # Immune
    "CD8A", "CD4", "CD3E", "GZMB", "IFNG", "FOXP3",
    "CD68", "CD163", "CSF1R",
    "CD19", "MS4A1",
    # Stroma
    "COL1A1", "ACTA2", "FAP", "VIM",
    # Checkpoints
    "PDCD1", "CD274", "CTLA4", "TIGIT",
    # Endothelial
    "PECAM1", "VWF",
    # Adipocyte
    "ADIPOQ", "FABP4",
    # DNA repair
    "BRCA2", "RAD51",
    # Tamoxifen
    "CYP2D6",
]
n_background = N_GENES - len(key_genes)
gene_names = key_genes + [f"BG_{i:04d}" for i in range(n_background)]

# Base expression (low)
X = np.random.negative_binomial(3, 0.4, size=(N_CELLS, N_GENES)).astype(np.float32)

# Cell-type-specific upregulation
type_markers = {
    "tumor_luminal": ["ESR1", "PGR", "GATA3", "FOXA1", "XBP1", "TFF1",
                      "KRT8", "KRT18", "KRT19", "EPCAM", "PIK3CA", "AKT1",
                      "CCND1", "MYC"],
    "stroma_CAF": ["COL1A1", "ACTA2", "FAP", "VIM"],
    "CD8_T": ["CD8A", "CD3E", "GZMB", "IFNG", "PDCD1"],
    "macrophage": ["CD68", "CD163", "CSF1R"],
    "B_cell": ["CD19", "MS4A1"],
    "endothelial": ["PECAM1", "VWF"],
    "adipocyte": ["ADIPOQ", "FABP4"],
}

for i, ct in enumerate(cell_types):
    if ct in type_markers:
        for g in type_markers[ct]:
            if g in gene_names:
                idx = gene_names.index(g)
                X[i, idx] = np.random.negative_binomial(40, 0.2)

# ER/PR very high in tumor cells
for i, ct in enumerate(cell_types):
    if ct == "tumor_luminal":
        for g in ["ESR1", "PGR", "GATA3", "FOXA1"]:
            idx = gene_names.index(g)
            X[i, idx] = np.random.negative_binomial(60, 0.15)
        # Low-moderate proliferation (Luminal A)
        for g in ["MKI67", "PCNA", "TOP2A"]:
            idx = gene_names.index(g)
            X[i, idx] = np.random.negative_binomial(10, 0.3)
        # BRCA2 haploinsufficiency
        idx = gene_names.index("BRCA2")
        X[i, idx] = np.random.negative_binomial(15, 0.3)

# --- Build AnnData ---
obs = pd.DataFrame({
    "cell_type": cell_types,
    "tissue_region": ["tumor" if ct in ["tumor_luminal", "stroma_CAF"] else
                      "immune" if ct in ["CD8_T", "macrophage", "B_cell"] else
                      "stroma" for ct in cell_types],
    "n_genes": (X > 0).sum(axis=1),
    "total_counts": X.sum(axis=1).astype(int),
}, index=[f"cell_{i:04d}" for i in range(N_CELLS)])

var = pd.DataFrame(index=gene_names)

adata = ad.AnnData(X=X, obs=obs, var=var)
adata.obsm["spatial"] = np.column_stack([spatial_x, spatial_y])

adata.uns["patient_id"] = "PAT002-BC-2026"
adata.uns["diagnosis"] = "Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma"
adata.uns["spatial_technology"] = "10x Visium"
adata.uns["receptor_status"] = "ER+ (85%), PR+ (70%), HER2-"
adata.uns["brca2_status"] = "Germline pathogenic (c.5946delT)"
adata.uns["treatment"] = "Tamoxifen 20mg daily"

# Save
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
adata.write_h5ad(OUTPUT_FILE)

print(f"\nCreated: {OUTPUT_FILE}")
print(f"Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
print(f"Cells: {adata.n_obs}, Genes: {adata.n_vars}")
ct_counts = adata.obs["cell_type"].value_counts()
for ct, n in ct_counts.items():
    print(f"  {ct}: {n}")
print("Done.")
