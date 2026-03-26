"""Clinical-spatial bridge: map patient data to spatial transcriptomics."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Clinical condition -> Gene of Interest mapping
CONDITION_GENE_MAP = {
    # Ovarian cancer
    "ovarian cancer": ["Ki67", "TP53", "BRCA1", "BRCA2", "EPCAM", "CA125", "PAX8"],
    "HGSOC": ["TP53", "Ki67", "FOXM1", "MYC", "CCNE1"],  # High-grade serous
    "platinum-resistant": ["ABCB1", "ERCC1", "GSTP1", "BRCA1"],
    "serous carcinoma": ["TP53", "PAX8", "WT1", "CA125"],
    # Breast cancer
    "breast cancer": ["ESR1", "PGR", "ERBB2", "Ki67", "GATA3", "FOXA1", "EPCAM"],
    "invasive ductal": ["ESR1", "PGR", "ERBB2", "Ki67", "CCND1", "PIK3CA"],
    "er+": ["ESR1", "PGR", "GATA3", "FOXA1", "CCND1"],
    "her2-": ["ERBB2", "ESR1", "PGR"],
    "luminal": ["ESR1", "PGR", "GATA3", "FOXA1", "KRT18", "KRT19"],
    # General
    "stage IV": ["Ki67", "MYC", "VIM", "CDH1"],  # Advanced cancer markers
    "stage II": ["Ki67", "EPCAM", "CDH1"],  # Early-stage markers
}

# Treatment -> Biomarker mapping
TREATMENT_BIOMARKER_MAP = {
    "bevacizumab": ["VEGFA", "CD31", "HIF1A", "KDR"],  # Anti-angiogenic
    "carboplatin": ["ERCC1", "XPA", "BRCA1", "BRCA2"],  # DNA repair
    "paclitaxel": ["TUBB3", "MAP2", "MAPT"],  # Microtubule targeting
    "avastin": ["VEGFA", "CD31", "HIF1A"],  # Brand name for bevacizumab
    "tamoxifen": ["ESR1", "PGR", "CYP2D6"],  # ER antagonist
    "letrozole": ["ESR1", "CYP19A1"],  # Aromatase inhibitor
    "palbociclib": ["CDK4", "CDK6", "CCND1", "RB1"],  # CDK4/6 inhibitor
    "trastuzumab": ["ERBB2", "EGFR"],  # Anti-HER2
    "doxorubicin": ["TOP2A", "TP53"],  # Anthracycline
}

# Observation/Biomarker -> Gene mapping
BIOMARKER_GENE_MAP = {
    "CA-125": ["CA125", "MUC16"],  # CA-125 is encoded by MUC16
    "BRCA": ["BRCA1", "BRCA2"],
    "high CA-125": ["CA125", "MUC16", "Ki67", "TP53"],  # Elevated tumor marker
    "CEA": ["CEACAM5"],  # Carcinoembryonic antigen
    "CA 15-3": ["MUC1"],  # Breast cancer marker
    "ER": ["ESR1"],  # Estrogen receptor
    "PR": ["PGR"],  # Progesterone receptor
    "HER2": ["ERBB2"],  # Human epidermal growth factor receptor 2
}

# Patient ID -> Spatial Dataset mapping
# Add aliases for known patients; unknown IDs fall through via .get(id, id)
PATIENT_SPATIAL_MAP = {
    "patient-001": "PAT001-OVC-2025",
    "PAT001": "PAT001-OVC-2025",
    "patient-002": "PAT002-BC-2026",
    "PAT002": "PAT002-BC-2026",
}


async def get_spatial_data_for_patient_impl(
    patient_id: str,
    tissue_type: str,
    include_clinical_context: bool,
    conditions: Optional[List[str]],
    medications: Optional[List[str]],
    biomarkers: Optional[Dict[str, Any]],
    *,
    data_dir: Path,
) -> Dict[str, Any]:
    """Get spatial transcriptomics data for a patient with clinical context."""
    # Map patient ID to spatial dataset
    spatial_dataset = PATIENT_SPATIAL_MAP.get(patient_id, patient_id)

    # Build path to spatial data
    patient_data_dir = data_dir / "patient-data" / spatial_dataset / "spatial"

    # Check if data exists
    if not patient_data_dir.exists():
        return {
            "status": "error",
            "error": f"No spatial data found for patient {patient_id}",
            "searched_path": str(patient_data_dir),
            "message": f"Expected spatial data at {patient_data_dir} but directory not found."
        }

    # Identify genes of interest based on clinical context
    genes_of_interest = set()

    if conditions:
        for condition in conditions:
            condition_lower = condition.lower()
            for key, genes in CONDITION_GENE_MAP.items():
                if key in condition_lower:
                    genes_of_interest.update(genes)

    if medications:
        for medication in medications:
            medication_lower = medication.lower()
            for key, genes in TREATMENT_BIOMARKER_MAP.items():
                if key in medication_lower:
                    genes_of_interest.update(genes)

    if biomarkers:
        for biomarker_name, value in biomarkers.items():
            biomarker_lower = biomarker_name.lower()
            if isinstance(value, (int, float)) and value > 100:
                key = f"high {biomarker_lower}"
                if key in BIOMARKER_GENE_MAP:
                    genes_of_interest.update(BIOMARKER_GENE_MAP[key])
            for key, genes in BIOMARKER_GENE_MAP.items():
                if key in biomarker_lower:
                    genes_of_interest.update(genes)

    # Default genes if no clinical context provided
    if not genes_of_interest:
        genes_of_interest = {"Ki67", "CD8A", "VIM", "EPCAM"}

    # Build suggested analyses
    suggested_analyses = []

    if conditions and any("cancer" in c.lower() for c in conditions):
        suggested_analyses.extend([
            "Calculate spatial autocorrelation for proliferation markers (Ki67)",
            "Analyze immune infiltration patterns (CD8A, CD4)",
            "Assess tumor-stroma interaction (VIM, EPCAM)"
        ])

    if medications:
        if any("bevacizumab" in m.lower() or "avastin" in m.lower() for m in medications):
            suggested_analyses.append(
                "Evaluate angiogenesis markers (VEGFA, CD31) for treatment response"
            )
        if any("platinum" in m.lower() or "carboplatin" in m.lower() for m in medications):
            suggested_analyses.append(
                "Check DNA repair gene expression (BRCA1, ERCC1) for resistance markers"
            )

    # Build clinical summary
    clinical_summary = None
    if include_clinical_context:
        clinical_summary = {
            "patient_id": patient_id,
            "conditions": conditions or [],
            "medications": medications or [],
            "biomarkers": biomarkers or {},
            "tissue_type": tissue_type
        }

    # Prepare file paths
    expression_file = patient_data_dir / "visium_gene_expression.csv"
    coordinates_file = patient_data_dir / "visium_spatial_coordinates.csv"
    annotations_file = patient_data_dir / "visium_region_annotations.csv"

    result = {
        "status": "success",
        "patient_id": patient_id,
        "spatial_dataset": spatial_dataset,
        "data_directory": str(patient_data_dir),
        "files": {
            "expression": str(expression_file) if expression_file.exists() else None,
            "coordinates": str(coordinates_file) if coordinates_file.exists() else None,
            "annotations": str(annotations_file) if annotations_file.exists() else None
        },
        "genes_of_interest": sorted(list(genes_of_interest)),
        "num_genes_of_interest": len(genes_of_interest),
        "suggested_analyses": suggested_analyses,
        "tissue_type": tissue_type
    }

    if clinical_summary:
        result["clinical_summary"] = clinical_summary

    # Add available file info
    available_files = []
    for file_type, file_path in result["files"].items():
        if file_path and Path(file_path).exists():
            available_files.append(file_type)

    result["available_files"] = available_files
    result["data_ready"] = len(available_files) > 0

    return result
