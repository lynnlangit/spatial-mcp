"""Canonical PAT001-OVC-2025 test values.

These are the validated reference values for synthetic PatientOne (Stage IV
HGSOC) produced by end-to-end pipeline runs with DRY_RUN=false.  Import this
dict in any test that needs to assert against expected PAT001 outputs instead
of hard-coding magic numbers.

Usage::

    from tests.fixtures.pat001_canonical import PAT001

    def test_hrd_score():
        assert result["hrd_score"] == PAT001["hrd_score"]
"""

PAT001 = {
    # --- Genomic results (mcp-genomic-results) ---
    "patient_id": "PAT001-OVC-2025",
    "hrd_score": 72,
    "tmb_mut_per_mb": 4.2,

    # --- Neoantigen prediction (mcp-neoantigen) ---
    "top_neoantigen_peptide": "RMPEAAPPV",
    "top_neoantigen_ic50_nm": 7.8,
    "hla_allele": "HLA-A*02:01",

    # --- Spatial transcriptomics (mcp-spatialtools) ---
    "spatial_spot_count": 300,
    "morans_i_global": -0.0033,

    # --- Immune deconvolution (mcp-cibersortx) ---
    "deconvolution": {
        "tumor": 56,
        "endothelial": 44,
        "macrophages": 43,
        "fibroblasts": 41,
        "cd8_t_cells": 30,
    },
}
