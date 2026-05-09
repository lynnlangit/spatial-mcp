"""Canonical PAT002-BC-2026 test values.

These are the validated reference values for synthetic PatientTwo (Stage IIA
ER+/PR+/HER2- Invasive Ductal Carcinoma, BRCA2 germline) produced by
end-to-end pipeline runs with DRY_RUN=false (April-May 2026).

Usage::

    from tests.fixtures.pat002_canonical import PAT002

    def test_hrd_score():
        assert result["hrd_score"] == PAT002["hrd_score"]
"""

PAT002 = {
    # --- Demographics ---
    "patient_id": "PAT002-BC-2026",
    "patient_name": "Michelle Anne Thompson",
    "age": 42,
    "sex": "female",
    "diagnosis": "Stage IIA (T2N0M0) ER+/PR+/HER2- IDC",

    # --- Receptor status ---
    "er_percent": 85,
    "pr_percent": 70,
    "her2_status": "negative",

    # --- Key mutations (mcp-genomic-results) ---
    "brca2_germline": "c.5946delT",
    "pik3ca_somatic": "H1047R",
    "hrd_score": 35,  # below myChoice 42 threshold
    "tmb_mut_per_mb": 2.8,  # low TMB (typical Luminal)

    # --- HLA typing (genomics/PAT002_hla_typing.json) ---
    "hla_a": ["HLA-A*02:01", "HLA-A*03:01"],
    "hla_b": ["HLA-B*07:02", "HLA-B*44:02"],
    "hla_c": ["HLA-C*07:02", "HLA-C*05:01"],

    # --- Neoantigen prediction (mcp-neoantigen, deep-stage) ---
    "top_neoantigen_peptide": "YSAPLSSSL",
    "top_neoantigen_hla": "HLA-A*02:01",

    # --- Spatial transcriptomics (mcp-spatialtools) ---
    "spatial_spot_count": 900,
    "spatial_gene_count": 35,
    "spatial_regions": 7,  # BC tissue types

    # --- Immune deconvolution (mcp-cibersortx) ---
    "immune_evasion_score": 0.41,
    "luminal_stability_score": 0.78,

    # --- Perturbation (mcp-perturbation, GEARS) ---
    "gears_most_actionable": "CDK4",
    "gears_perturbations_tested": 5,

    # --- 3 investigational hypotheses (deep-stage, May 2026) ---
    "investigational_hypotheses": [
        {
            "id": "H1",
            "name": "inavolisib_over_alpelisib",
            "rationale": "PIK3CA H1047R + 2024 FDA approval; superior to alpelisib",
        },
        {
            "id": "H2",
            "name": "myc_triple_therapy",
            "rationale": "MYC amplification + CDK4/6i + PI3Ki + endocrine",
        },
        {
            "id": "H3",
            "name": "neoepitope_vaccine_plus_caf_depletion",
            "rationale": "YSAPLSSSL neoepitope + CAF depletion + anti-PD-1",
        },
    ],
}
