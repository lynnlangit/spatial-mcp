"""Mock data for DRY_RUN mode — HGSOC reference datasets from GEO."""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Mock GEO search results — 3 key HGSOC cohort datasets
# ---------------------------------------------------------------------------

MOCK_SEARCH_RESULTS: List[Dict[str, Any]] = [
    {
        "gse_id": "GSE32062",
        "title": "Gene expression profiling of high-grade serous ovarian cancer",
        "summary": (
            "Expression profiling of 260 high-grade serous ovarian cancer samples "
            "from the Japanese Gynecologic Oncology Group (JGOG). Tothill et al. "
            "molecular subtype classification of ovarian cancer."
        ),
        "organism": "Homo sapiens",
        "platform": "GPL6480",
        "platform_name": "Agilent-014850 Whole Human Genome Microarray 4x44K G4112F",
        "sample_count": 260,
        "pubmed_ids": ["18698038"],
        "study_type": "Expression profiling by array",
        "submission_date": "2011-09-09",
    },
    {
        "gse_id": "GSE26712",
        "title": "Gene expression in epithelial ovarian cancer",
        "summary": (
            "Genome-wide expression analysis of 185 primary ovarian tumors "
            "(mostly high-grade serous) and 10 normal ovarian surface epithelium "
            "samples. Bonome et al. 2008."
        ),
        "organism": "Homo sapiens",
        "platform": "GPL96",
        "platform_name": "Affymetrix Human Genome U133A Array",
        "sample_count": 195,
        "pubmed_ids": ["18245496"],
        "study_type": "Expression profiling by array",
        "submission_date": "2011-01-15",
    },
    {
        "gse_id": "GSE9899",
        "title": "Novel molecular subtypes of serous and endometrioid ovarian cancer",
        "summary": (
            "Expression profiling of 285 ovarian cancer samples from the "
            "Australian Ovarian Cancer Study (AOCS). Identification of molecular "
            "subtypes with distinct clinical outcomes."
        ),
        "organism": "Homo sapiens",
        "platform": "GPL6848",
        "platform_name": "Agilent-012391 Whole Human Genome Oligo Microarray G4112A",
        "sample_count": 285,
        "pubmed_ids": ["18451181"],
        "study_type": "Expression profiling by array",
        "submission_date": "2008-01-09",
    },
]

# ---------------------------------------------------------------------------
# Mock per-GSE metadata
# ---------------------------------------------------------------------------

MOCK_METADATA: Dict[str, Dict[str, Any]] = {
    "GSE32062": {
        "gse_id": "GSE32062",
        "title": "Gene expression profiling of high-grade serous ovarian cancer",
        "summary": (
            "Expression profiling of 260 high-grade serous ovarian cancer samples "
            "from the Japanese Gynecologic Oncology Group (JGOG). This dataset "
            "has been widely used for molecular subtype classification and "
            "survival analysis in HGSOC."
        ),
        "overall_design": (
            "260 primary serous ovarian cancer samples profiled on Agilent 4x44K "
            "whole human genome microarrays."
        ),
        "organism": "Homo sapiens",
        "platform_id": "GPL6480",
        "platform_name": "Agilent-014850 Whole Human Genome Microarray 4x44K G4112F",
        "sample_count": 260,
        "pubmed_ids": ["18698038"],
        "submission_date": "2011-09-09",
        "last_update_date": "2019-05-03",
        "contact_name": "Tothill RW",
        "contact_institute": "Peter MacCallum Cancer Centre",
        "supplementary_files": [
            "GSE32062_series_matrix.txt.gz",
            "GSE32062_RAW.tar",
        ],
        "series_matrix_url": (
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE32nnn/GSE32062/"
            "matrix/GSE32062_series_matrix.txt.gz"
        ),
    },
    "GSE26712": {
        "gse_id": "GSE26712",
        "title": "Gene expression in epithelial ovarian cancer",
        "summary": (
            "Genome-wide expression analysis of 185 primary ovarian tumors "
            "and 10 normal ovarian surface epithelium samples. Used for "
            "identification of prognostic gene signatures."
        ),
        "overall_design": (
            "185 primary ovarian tumor samples and 10 normal ovarian surface "
            "epithelium samples profiled on Affymetrix U133A arrays."
        ),
        "organism": "Homo sapiens",
        "platform_id": "GPL96",
        "platform_name": "Affymetrix Human Genome U133A Array",
        "sample_count": 195,
        "pubmed_ids": ["18245496"],
        "submission_date": "2011-01-15",
        "last_update_date": "2019-05-03",
        "contact_name": "Bonome T",
        "contact_institute": "Fox Chase Cancer Center",
        "supplementary_files": [
            "GSE26712_series_matrix.txt.gz",
            "GSE26712_RAW.tar",
        ],
        "series_matrix_url": (
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE26nnn/GSE26712/"
            "matrix/GSE26712_series_matrix.txt.gz"
        ),
    },
    "GSE9899": {
        "gse_id": "GSE9899",
        "title": "Novel molecular subtypes of serous and endometrioid ovarian cancer",
        "summary": (
            "Expression profiling of 285 ovarian cancer samples from AOCS. "
            "Identified molecular subtypes (C1-C5) with distinct survival "
            "outcomes and pathway activation patterns."
        ),
        "overall_design": (
            "285 ovarian cancer samples from the Australian Ovarian Cancer "
            "Study profiled on Agilent whole human genome oligo microarrays."
        ),
        "organism": "Homo sapiens",
        "platform_id": "GPL6848",
        "platform_name": "Agilent-012391 Whole Human Genome Oligo Microarray G4112A",
        "sample_count": 285,
        "pubmed_ids": ["18451181"],
        "submission_date": "2008-01-09",
        "last_update_date": "2019-05-03",
        "contact_name": "Tothill RW",
        "contact_institute": "Peter MacCallum Cancer Centre",
        "supplementary_files": [
            "GSE9899_series_matrix.txt.gz",
            "GSE9899_RAW.tar",
        ],
        "series_matrix_url": (
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE9nnn/GSE9899/"
            "matrix/GSE9899_series_matrix.txt.gz"
        ),
    },
}

# ---------------------------------------------------------------------------
# Mock per-GSE sample lists
# ---------------------------------------------------------------------------

MOCK_SAMPLES: Dict[str, List[Dict[str, Any]]] = {
    "GSE32062": [
        {
            "gsm_id": "GSM793463",
            "title": "JGOG-OV001",
            "source": "primary ovarian tumor",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "high-grade serous",
                "stage": "III",
            },
        },
        {
            "gsm_id": "GSM793464",
            "title": "JGOG-OV002",
            "source": "primary ovarian tumor",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "high-grade serous",
                "stage": "IV",
            },
        },
        {
            "gsm_id": "GSM793465",
            "title": "JGOG-OV003",
            "source": "primary ovarian tumor",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "high-grade serous",
                "stage": "III",
            },
        },
    ],
    "GSE26712": [
        {
            "gsm_id": "GSM658451",
            "title": "OVC-T001",
            "source": "primary ovarian tumor",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "serous",
                "grade": "3",
            },
        },
        {
            "gsm_id": "GSM658452",
            "title": "OVC-T002",
            "source": "primary ovarian tumor",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "serous",
                "grade": "3",
            },
        },
        {
            "gsm_id": "GSM658453",
            "title": "OVC-N001",
            "source": "normal ovarian surface epithelium",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "normal",
                "grade": "N/A",
            },
        },
    ],
    "GSE9899": [
        {
            "gsm_id": "GSM249759",
            "title": "AOCS-001",
            "source": "primary ovarian tumor",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "serous",
                "subtype": "C1-mesenchymal",
            },
        },
        {
            "gsm_id": "GSM249760",
            "title": "AOCS-002",
            "source": "primary ovarian tumor",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "serous",
                "subtype": "C2-immunoreactive",
            },
        },
        {
            "gsm_id": "GSM249761",
            "title": "AOCS-003",
            "source": "primary ovarian tumor",
            "organism": "Homo sapiens",
            "characteristics": {
                "tissue": "ovary",
                "histology": "serous",
                "subtype": "C5-proliferative",
            },
        },
    ],
}

# ---------------------------------------------------------------------------
# Mock expression matrix info (shape/dimensions, not actual data)
# ---------------------------------------------------------------------------

MOCK_EXPRESSION_MATRIX_INFO: Dict[str, Dict[str, Any]] = {
    "GSE32062": {
        "gse_id": "GSE32062",
        "gene_count": 20502,
        "sample_count": 260,
        "platform": "GPL6480",
        "normalization": "quantile normalized",
        "file_format": "series_matrix",
        "file_size_mb": 85.2,
    },
    "GSE26712": {
        "gse_id": "GSE26712",
        "gene_count": 12625,
        "sample_count": 195,
        "platform": "GPL96",
        "normalization": "MAS5.0",
        "file_format": "series_matrix",
        "file_size_mb": 42.1,
    },
    "GSE9899": {
        "gse_id": "GSE9899",
        "gene_count": 18626,
        "sample_count": 285,
        "platform": "GPL6848",
        "normalization": "lowess normalized",
        "file_format": "series_matrix",
        "file_size_mb": 78.9,
    },
}

# ---------------------------------------------------------------------------
# Mock SOFT file info
# ---------------------------------------------------------------------------

MOCK_SOFT_INFO: Dict[str, Dict[str, Any]] = {
    "GSE32062": {
        "gse_id": "GSE32062",
        "file_name": "GSE32062_family.soft.gz",
        "file_size_mb": 120.5,
        "record_count": 261,
        "format": "SOFT",
    },
    "GSE26712": {
        "gse_id": "GSE26712",
        "file_name": "GSE26712_family.soft.gz",
        "file_size_mb": 65.3,
        "record_count": 196,
        "format": "SOFT",
    },
    "GSE9899": {
        "gse_id": "GSE9899",
        "file_name": "GSE9899_family.soft.gz",
        "file_size_mb": 98.7,
        "record_count": 286,
        "format": "SOFT",
    },
}

# ---------------------------------------------------------------------------
# Mock SRA download info
# ---------------------------------------------------------------------------

MOCK_SRA_DOWNLOAD: Dict[str, Any] = {
    "srr_id": "SRR12345678",
    "experiment_id": "SRX12345678",
    "study_id": "SRP123456",
    "organism": "Homo sapiens",
    "library_strategy": "RNA-Seq",
    "library_source": "TRANSCRIPTOMIC",
    "platform": "ILLUMINA",
    "instrument": "Illumina NovaSeq 6000",
    "read_count": 45_000_000,
    "base_count": 6_750_000_000,
    "files": [
        {"filename": "SRR12345678_1.fastq.gz", "size_mb": 1250.0},
        {"filename": "SRR12345678_2.fastq.gz", "size_mb": 1320.0},
    ],
}
