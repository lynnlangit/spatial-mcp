"""Mock data for DRY_RUN mode — PatientOne neoantigen predictions."""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# PatientOne HLA type (synthetic but realistic for Caucasian ancestry)
# ---------------------------------------------------------------------------

MOCK_HLA_ALLELES: Dict[str, List[str]] = {
    "HLA-A": ["HLA-A*02:01", "HLA-A*03:01"],
    "HLA-B": ["HLA-B*07:02", "HLA-B*44:02"],
    "HLA-C": ["HLA-C*07:02", "HLA-C*05:01"],
}

MOCK_HLA_FLAT: List[str] = [
    "HLA-A*02:01", "HLA-A*03:01",
    "HLA-B*07:02", "HLA-B*44:02",
    "HLA-C*07:02", "HLA-C*05:01",
]

# ---------------------------------------------------------------------------
# Mock MHC class I binding predictions
# Based on PatientOne mutations: TP53 R175H, PIK3CA E545K
# ---------------------------------------------------------------------------

MOCK_MHC1_PREDICTIONS: List[Dict[str, Any]] = [
    {
        "peptide": "RMPEAAPPV",
        "allele": "HLA-A*02:01",
        "ic50_nm": 45.2,
        "percentile_rank": 0.8,
        "binder": True,
        "binder_level": "strong",
        "source_gene": "TP53",
        "source_mutation": "R175H",
    },
    {
        "peptide": "HMTEVVRHC",
        "allele": "HLA-A*02:01",
        "ic50_nm": 320.5,
        "percentile_rank": 2.1,
        "binder": True,
        "binder_level": "weak",
        "source_gene": "TP53",
        "source_mutation": "R175H",
    },
    {
        "peptide": "VVHCHQIIY",
        "allele": "HLA-A*03:01",
        "ic50_nm": 78.3,
        "percentile_rank": 1.2,
        "binder": True,
        "binder_level": "strong",
        "source_gene": "TP53",
        "source_mutation": "R175H",
    },
    {
        "peptide": "STKHQPQIV",
        "allele": "HLA-B*07:02",
        "ic50_nm": 180.7,
        "percentile_rank": 1.8,
        "binder": True,
        "binder_level": "weak",
        "source_gene": "PIK3CA",
        "source_mutation": "E545K",
    },
    {
        "peptide": "KITEESPFI",
        "allele": "HLA-A*02:01",
        "ic50_nm": 62.1,
        "percentile_rank": 0.9,
        "binder": True,
        "binder_level": "strong",
        "source_gene": "PIK3CA",
        "source_mutation": "E545K",
    },
    {
        "peptide": "IMKEKLLNY",
        "allele": "HLA-B*44:02",
        "ic50_nm": 890.3,
        "percentile_rank": 5.2,
        "binder": False,
        "binder_level": "non_binder",
        "source_gene": "TP53",
        "source_mutation": "R175H",
    },
    {
        "peptide": "LHSKHQPQI",
        "allele": "HLA-C*07:02",
        "ic50_nm": 420.8,
        "percentile_rank": 3.5,
        "binder": True,
        "binder_level": "weak",
        "source_gene": "PIK3CA",
        "source_mutation": "E545K",
    },
]

# ---------------------------------------------------------------------------
# Mock MHC class II binding predictions
# ---------------------------------------------------------------------------

MOCK_MHC2_PREDICTIONS: List[Dict[str, Any]] = [
    {
        "peptide": "VVRCPHHERCSTHH",
        "allele": "HLA-DRB1*01:01",
        "ic50_nm": 125.4,
        "percentile_rank": 1.5,
        "binder": True,
        "binder_level": "weak",
        "source_gene": "TP53",
        "source_mutation": "R175H",
    },
    {
        "peptide": "KITEESPFIDHNKAV",
        "allele": "HLA-DRB1*01:01",
        "ic50_nm": 85.2,
        "percentile_rank": 1.0,
        "binder": True,
        "binder_level": "strong",
        "source_gene": "PIK3CA",
        "source_mutation": "E545K",
    },
]

# ---------------------------------------------------------------------------
# Mock neoantigen burden estimates
# Based on TMB-to-neoantigen conversion (Samstein et al. 2019)
# ---------------------------------------------------------------------------

# Cancer-type-specific TMB-to-neoantigen conversion factors
TMB_CONVERSION_FACTORS: Dict[str, float] = {
    "HGSOC": 12.0,       # ~12 neoantigens per mut/Mb
    "melanoma": 15.0,
    "NSCLC": 13.0,
    "colorectal": 14.0,
    "breast": 10.0,
    "pancreatic": 8.0,
    "glioblastoma": 6.0,
    "default": 11.0,
}

MOCK_NEOANTIGEN_BURDEN: Dict[str, Any] = {
    "tmb": 3.5,
    "estimated_neoantigens": 42,
    "estimated_strong_binders": 8,
    "conversion_factor": 12.0,
    "cancer_type": "HGSOC",
    "interpretation": (
        "Low-moderate neoantigen burden for HGSOC. "
        "Typical range for serous ovarian is 2-5 mut/Mb. "
        "Moderate neoantigen load may support partial checkpoint inhibitor response."
    ),
}

# ---------------------------------------------------------------------------
# Mock OptiType HLA typing result
# ---------------------------------------------------------------------------

MOCK_HLA_TYPING: Dict[str, Any] = {
    "hla_alleles": MOCK_HLA_ALLELES,
    "method": "OptiType",
    "confidence": 0.95,
    "input_reads": 45_000_000,
    "hla_reads_extracted": 125_000,
}

# ---------------------------------------------------------------------------
# Mock pVACseq result
# ---------------------------------------------------------------------------

MOCK_PVACSEQ_RESULT: Dict[str, Any] = {
    "total_neoantigens": 45,
    "strong_binders": 12,
    "weak_binders": 18,
    "non_binders": 15,
    "top_neoantigens": [
        {
            "gene": "TP53",
            "mutation": "R175H",
            "peptide": "RMPEAAPPV",
            "hla": "HLA-A*02:01",
            "binding_affinity": 45.2,
            "percentile_rank": 0.8,
            "tumor_dna_vaf": 0.45,
            "tumor_rna_vaf": 0.38,
        },
        {
            "gene": "PIK3CA",
            "mutation": "E545K",
            "peptide": "KITEESPFI",
            "hla": "HLA-A*02:01",
            "binding_affinity": 62.1,
            "percentile_rank": 0.9,
            "tumor_dna_vaf": 0.32,
            "tumor_rna_vaf": 0.28,
        },
        {
            "gene": "TP53",
            "mutation": "R175H",
            "peptide": "VVHCHQIIY",
            "hla": "HLA-A*03:01",
            "binding_affinity": 78.3,
            "percentile_rank": 1.2,
            "tumor_dna_vaf": 0.45,
            "tumor_rna_vaf": 0.38,
        },
    ],
}

# ---------------------------------------------------------------------------
# Mock antigen presentation pathway scoring
# PatientOne: moderate capacity (0.72) reflecting HGSOC's typical partial
# antigen presentation with some MHC downregulation
# ---------------------------------------------------------------------------

MOCK_PATHWAY_SCORE: Dict[str, Any] = {
    "pathway_score": 0.72,
    "components": {
        "neoantigen_score": 0.65,
        "mhc_expression_score": 0.80,
        "antigen_processing_score": 0.85,
        "hla_integrity_score": 1.0,
    },
    "interpretation": (
        "Moderate antigen presentation capacity. "
        "Neoantigen burden is low-moderate (42 predicted neoantigens). "
        "MHC class I expression is preserved. "
        "Antigen processing machinery (TAP1/TAP2) is functional. "
        "No HLA loss of heterozygosity detected."
    ),
    "recommendation": (
        "Checkpoint inhibitor may have moderate benefit. "
        "Consider combination with PARP inhibitor given HGSOC context. "
        "Monitor for acquired resistance via HLA-LOH."
    ),
}

# Pathway scoring weights (from published literature)
PATHWAY_WEIGHTS: Dict[str, float] = {
    "neoantigen_score": 0.30,
    "mhc_expression_score": 0.30,
    "antigen_processing_score": 0.20,
    "hla_integrity_score": 0.20,
}
