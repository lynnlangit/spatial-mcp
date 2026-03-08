"""Mock data for DRY_RUN mode — HGSOC immune cell fractions and job metadata."""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# LM22 cell type reference — the 22 immune cell types in the standard
# CIBERSORTx LM22 signature matrix
# ---------------------------------------------------------------------------

LM22_CELL_TYPES: List[str] = [
    "B_cells_naive",
    "B_cells_memory",
    "Plasma_cells",
    "T_cells_CD8",
    "T_cells_CD4_naive",
    "T_cells_CD4_memory_resting",
    "T_cells_CD4_memory_activated",
    "T_cells_follicular_helper",
    "T_cells_regulatory_Tregs",
    "T_cells_gamma_delta",
    "NK_cells_resting",
    "NK_cells_activated",
    "Monocytes",
    "Macrophages_M0",
    "Macrophages_M1",
    "Macrophages_M2",
    "Dendritic_cells_resting",
    "Dendritic_cells_activated",
    "Mast_cells_resting",
    "Mast_cells_activated",
    "Eosinophils",
    "Neutrophils",
]

# ---------------------------------------------------------------------------
# Mock deconvolution results — biologically realistic HGSOC immune fractions
# Based on published HGSOC deconvolution studies (TCGA-OV, GSE32062)
# High TAM-M2, low CD8+ T cells, moderate Tregs — typical immunosuppressive TME
# ---------------------------------------------------------------------------

MOCK_DECONVOLUTION_FRACTIONS: Dict[str, Dict[str, float]] = {
    "HGSOC_Sample_01": {
        "B_cells_naive": 0.02,
        "B_cells_memory": 0.01,
        "Plasma_cells": 0.03,
        "T_cells_CD8": 0.08,
        "T_cells_CD4_naive": 0.01,
        "T_cells_CD4_memory_resting": 0.04,
        "T_cells_CD4_memory_activated": 0.02,
        "T_cells_follicular_helper": 0.01,
        "T_cells_regulatory_Tregs": 0.05,
        "T_cells_gamma_delta": 0.01,
        "NK_cells_resting": 0.02,
        "NK_cells_activated": 0.01,
        "Monocytes": 0.03,
        "Macrophages_M0": 0.08,
        "Macrophages_M1": 0.06,
        "Macrophages_M2": 0.35,
        "Dendritic_cells_resting": 0.02,
        "Dendritic_cells_activated": 0.01,
        "Mast_cells_resting": 0.02,
        "Mast_cells_activated": 0.01,
        "Eosinophils": 0.01,
        "Neutrophils": 0.10,
    },
    "HGSOC_Sample_02": {
        "B_cells_naive": 0.03,
        "B_cells_memory": 0.02,
        "Plasma_cells": 0.04,
        "T_cells_CD8": 0.12,
        "T_cells_CD4_naive": 0.02,
        "T_cells_CD4_memory_resting": 0.05,
        "T_cells_CD4_memory_activated": 0.03,
        "T_cells_follicular_helper": 0.02,
        "T_cells_regulatory_Tregs": 0.04,
        "T_cells_gamma_delta": 0.01,
        "NK_cells_resting": 0.03,
        "NK_cells_activated": 0.02,
        "Monocytes": 0.02,
        "Macrophages_M0": 0.06,
        "Macrophages_M1": 0.08,
        "Macrophages_M2": 0.28,
        "Dendritic_cells_resting": 0.03,
        "Dendritic_cells_activated": 0.02,
        "Mast_cells_resting": 0.01,
        "Mast_cells_activated": 0.01,
        "Eosinophils": 0.01,
        "Neutrophils": 0.05,
    },
    "HGSOC_Sample_03": {
        "B_cells_naive": 0.01,
        "B_cells_memory": 0.01,
        "Plasma_cells": 0.02,
        "T_cells_CD8": 0.05,
        "T_cells_CD4_naive": 0.01,
        "T_cells_CD4_memory_resting": 0.03,
        "T_cells_CD4_memory_activated": 0.01,
        "T_cells_follicular_helper": 0.01,
        "T_cells_regulatory_Tregs": 0.07,
        "T_cells_gamma_delta": 0.01,
        "NK_cells_resting": 0.01,
        "NK_cells_activated": 0.01,
        "Monocytes": 0.04,
        "Macrophages_M0": 0.10,
        "Macrophages_M1": 0.04,
        "Macrophages_M2": 0.40,
        "Dendritic_cells_resting": 0.01,
        "Dendritic_cells_activated": 0.01,
        "Mast_cells_resting": 0.03,
        "Mast_cells_activated": 0.01,
        "Eosinophils": 0.01,
        "Neutrophils": 0.11,
    },
}

# P-values per sample (CIBERSORTx permutation test)
MOCK_DECONVOLUTION_PVALUES: Dict[str, float] = {
    "HGSOC_Sample_01": 0.001,
    "HGSOC_Sample_02": 0.003,
    "HGSOC_Sample_03": 0.002,
}

# RMSE per sample (CIBERSORTx reconstruction error)
MOCK_DECONVOLUTION_RMSE: Dict[str, float] = {
    "HGSOC_Sample_01": 0.142,
    "HGSOC_Sample_02": 0.128,
    "HGSOC_Sample_03": 0.155,
}

# ---------------------------------------------------------------------------
# Mock job metadata
# ---------------------------------------------------------------------------

MOCK_JOB_SUBMITTED: Dict[str, Any] = {
    "job_id": "cb-mock-12345",
    "state": "COMPLETED",
    "progress_pct": 100,
    "estimated_remaining_seconds": 0,
    "submitted_at": "2025-01-15T10:30:00Z",
    "completed_at": "2025-01-15T10:42:00Z",
    "signature_matrix": "LM22",
    "n_samples": 3,
    "permutations": 100,
    "quantile_normalize": True,
}

MOCK_JOB_RUNNING: Dict[str, Any] = {
    "job_id": "cb-mock-67890",
    "state": "RUNNING",
    "progress_pct": 45,
    "estimated_remaining_seconds": 360,
    "submitted_at": "2025-01-15T11:00:00Z",
    "completed_at": None,
    "signature_matrix": "LM22",
    "n_samples": 260,
    "permutations": 100,
    "quantile_normalize": True,
}

# ---------------------------------------------------------------------------
# Mock signature matrix upload response
# ---------------------------------------------------------------------------

MOCK_SIGNATURE_UPLOAD: Dict[str, Any] = {
    "matrix_id": "sig-custom-001",
    "matrix_name": "HGSOC_TME_signature",
    "genes": 547,
    "cell_types": 12,
    "upload_size_kb": 245,
    "cell_type_names": [
        "CD8_T_cells",
        "CD4_T_cells",
        "Tregs",
        "NK_cells",
        "B_cells",
        "Plasma_cells",
        "Macrophages_M1",
        "Macrophages_M2",
        "Dendritic_cells",
        "CAFs",
        "Endothelial",
        "Epithelial_tumor",
    ],
}

# ---------------------------------------------------------------------------
# Mock NNLS fallback result
# ---------------------------------------------------------------------------

MOCK_NNLS_FRACTIONS: Dict[str, Dict[str, float]] = {
    "HGSOC_Sample_01": {
        "CD8_T_cells": 0.09,
        "CD4_T_cells": 0.07,
        "Tregs": 0.06,
        "NK_cells": 0.03,
        "B_cells": 0.04,
        "Plasma_cells": 0.03,
        "Macrophages_M1": 0.07,
        "Macrophages_M2": 0.33,
        "Dendritic_cells": 0.03,
        "CAFs": 0.15,
        "Endothelial": 0.04,
        "Epithelial_tumor": 0.06,
    },
}

MOCK_NNLS_RMSE: Dict[str, float] = {
    "HGSOC_Sample_01": 0.185,
}
