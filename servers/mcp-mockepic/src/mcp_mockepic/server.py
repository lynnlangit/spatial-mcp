"""MCP Mock Epic server - Simulated EHR integration."""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
from common.transport import run_server as _run_server

# Configure logging
logger = logging.getLogger(__name__)

mcp = FastMCP("mockepic")

def _is_dry_run() -> bool:
    """Check if DRY_RUN mode is enabled."""
    return os.getenv("EPIC_DRY_RUN", "true").lower() == "true"

DRY_RUN = _is_dry_run()

# DRY_RUN warning wrapper
def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="MOCKEPIC_DRY_RUN")


# Patient-specific mock profiles keyed by normalised ID prefixes
_PATIENT_PROFILES = {
    "PAT001": {
        "demographics": {"age": 58, "sex": "F", "ethnicity": "Caucasian", "name": "Sarah Anderson"},
        "diagnoses": [
            {"icd10": "C56.9", "description": "Stage IV High-Grade Serous Ovarian Cancer", "date": "2024-06-15"},
            {"icd10": "Z15.01", "description": "Genetic susceptibility - BRCA1 mutation", "date": "2024-06-20"},
        ],
        "labs": {
            "CA-125": {"value": 389, "unit": "U/mL", "ref_range": "0-35"},
            "hemoglobin": {"value": 11.2, "unit": "g/dL", "ref_range": "12-16"},
            "wbc": {"value": 6.8, "unit": "K/uL", "ref_range": "4-11"},
        },
        "medications": [
            {"name": "Carboplatin", "dose": "AUC 5", "frequency": "q3w"},
            {"name": "Paclitaxel", "dose": "175 mg/m2", "frequency": "q3w"},
            {"name": "Bevacizumab", "dose": "15 mg/kg", "frequency": "q3w"},
        ],
    },
    "PAT002": {
        "demographics": {"age": 42, "sex": "F", "ethnicity": "Caucasian", "name": "Michelle Thompson"},
        "diagnoses": [
            {"icd10": "C50.9", "description": "Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma", "date": "2024-12-20"},
            {"icd10": "Z15.01", "description": "Genetic susceptibility - BRCA2 mutation", "date": "2024-12-22"},
        ],
        "labs": {
            "CEA": {"value": 2.1, "unit": "ng/mL", "ref_range": "0-5"},
            "CA 15-3": {"value": 18, "unit": "U/mL", "ref_range": "0-30"},
            "hemoglobin": {"value": 12.5, "unit": "g/dL", "ref_range": "12-16"},
            "wbc": {"value": 7.2, "unit": "K/uL", "ref_range": "4-11"},
        },
        "medications": [
            {"name": "Tamoxifen", "dose": "20 mg", "frequency": "daily"},
        ],
    },
    "PAT003": {
        "demographics": {
            "age": 67, "sex": "F", "ethnicity": "Caucasian", "name": "Patricia Wells",
            "bmi": 26.4, "menopausal_status": "post-menopausal",
        },
        "diagnoses": [
            {"icd10": "I10", "description": "Stage 1 Hypertension, controlled", "date": "2023-03-15"},
            {"icd10": "E78.5", "description": "Hyperlipidemia, unspecified", "date": "2023-03-15"},
        ],
        "vitals": {
            "bp_systolic_mmhg": 138,
            "bp_diastolic_mmhg": 82,
            "bp_status": "controlled on medication",
        },
        "labs": {
            "hsCRP": {"value": 1.8, "unit": "mg/L", "ref_range": "0-3"},
            "LDL": {"value": 118, "unit": "mg/dL", "ref_range": "0-130"},
            "HDL": {"value": 58, "unit": "mg/dL", "ref_range": "40-80"},
            "total_cholesterol": {"value": 195, "unit": "mg/dL", "ref_range": "0-200"},
            "triglycerides": {"value": 142, "unit": "mg/dL", "ref_range": "0-150"},
            "fasting_glucose": {"value": 98, "unit": "mg/dL", "ref_range": "70-100"},
            "HbA1c": {"value": 5.6, "unit": "%", "ref_range": "4.0-5.7"},
            "hemoglobin": {"value": 13.1, "unit": "g/dL", "ref_range": "12-16"},
            "wbc": {"value": 6.9, "unit": "K/uL", "ref_range": "4-11"},
        },
        "family_history": [
            {"relation": "father", "event": "myocardial_infarction", "age_at_event": 61},
            {"relation": "mother", "event": "ischemic_stroke", "age_at_event": 69},
        ],
        "lifestyle": {
            "smoking": "never",
            "exercise": "moderate (3x/week, 30 min)",
            "diet": "low-sodium",
            "alcohol_units_per_week": 3,
        },
        "medications": [
            {"name": "Lisinopril", "dose": "5 mg", "frequency": "daily",
             "class": "ACE inhibitor", "indication": "hypertension"},
        ],
    },
}

# Fallback for unrecognised patient IDs
_DEFAULT_PROFILE = {
    "demographics": {"age": 55, "sex": "Unknown", "ethnicity": "Unknown"},
    "diagnoses": [{"icd10": "Z03.89", "description": "Encounter for observation, unspecified", "date": "2025-01-01"}],
    "labs": {
        "hemoglobin": {"value": 13.0, "unit": "g/dL", "ref_range": "12-16"},
        "wbc": {"value": 6.5, "unit": "K/uL", "ref_range": "4-11"},
    },
    "medications": [],
}


def _get_mock_patient_profile(
    normalised_id: str, include_labs: bool, include_meds: bool
) -> Dict[str, Any]:
    """Return the mock profile for *normalised_id*, stripping labs/meds if asked."""
    # Match on prefix so "PAT001OVC2025" still hits "PAT001"
    profile = None
    for prefix, prof in _PATIENT_PROFILES.items():
        if normalised_id.startswith(prefix):
            profile = prof
            break
    if profile is None:
        profile = _DEFAULT_PROFILE

    result: Dict[str, Any] = {
        "demographics": {**profile["demographics"], "mrn": f"MRN{normalised_id}"},
        "diagnoses": profile["diagnoses"],
        "labs": profile["labs"] if include_labs else {},
        "medications": profile["medications"] if include_meds else [],
    }
    # Pass through extra keys (vitals, family_history, lifestyle, etc.)
    for key in profile:
        if key not in ("demographics", "diagnoses", "labs", "medications"):
            result[key] = profile[key]
    return result


@mcp.tool()
async def query_patient_records(
    patient_id: str,
    include_labs: bool = True,
    include_meds: bool = True
) -> Dict[str, Any]:
    """Retrieve mock patient demographics and clinical data.

    Args:
        patient_id: Patient identifier
        include_labs: Include laboratory results
        include_meds: Include medication history

    Returns:
        Dictionary with patient demographics, diagnoses, labs, medications
    """
    if DRY_RUN:
        pid = patient_id.upper().replace("-", "")
        record = _get_mock_patient_profile(pid, include_labs, include_meds)
        record["patient_id"] = patient_id
        record["mode"] = "dry_run"
        return record
    return {"patient_id": patient_id}

@mcp.tool()
async def link_spatial_to_clinical(
    spatial_sample_id: str,
    patient_id: str,
    tissue_site: str
) -> Dict[str, Any]:
    """Connect spatial data to clinical outcomes.

    Args:
        spatial_sample_id: Spatial transcriptomics sample identifier
        patient_id: Patient identifier
        tissue_site: Tissue biopsy site

    Returns:
        Dictionary with linked clinical and spatial metadata
    """
    if DRY_RUN:
        return {
            "link_id": f"link_{spatial_sample_id}_{patient_id}",
            "spatial_sample": spatial_sample_id,
            "patient_id": patient_id,
            "tissue_site": tissue_site,
            "biopsy_date": "2024-02-10",
            "treatment_status": "post-surgery, on adjuvant therapy",
            "outcome_data": {
                "progression_free_months": 18,
                "response": "partial_response",
                "toxicity_grade": 1
            },
            "mode": "dry_run"
        }
    return {"link_id": "unknown"}

@mcp.tool()
async def search_diagnoses(
    icd10_code: Optional[str] = None,
    keyword: Optional[str] = None
) -> Dict[str, Any]:
    """Query ICD-10 diagnosis codes.

    Args:
        icd10_code: Specific ICD-10 code to look up
        keyword: Search keyword (e.g., "cancer", "diabetes")

    Returns:
        Dictionary with matching diagnoses
    """
    if DRY_RUN:
        mock_diagnoses = {
            "C50": [
                {"code": "C50.9", "description": "Malignant neoplasm of breast, unspecified"},
                {"code": "C50.1", "description": "Malignant neoplasm of central portion of breast"},
            ],
            "C56": [
                {"code": "C56.9", "description": "Malignant neoplasm of ovary, unspecified"},
                {"code": "C56.1", "description": "Malignant neoplasm of right ovary"},
            ],
            "E11": [
                {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
                {"code": "E11.65", "description": "Type 2 diabetes with hyperglycemia"},
            ],
            "Z15": [
                {"code": "Z15.01", "description": "Genetic susceptibility to malignant neoplasm of breast"},
                {"code": "Z15.02", "description": "Genetic susceptibility to malignant neoplasm of ovary"},
            ],
        }

        if icd10_code:
            prefix = icd10_code[:3]
            results = mock_diagnoses.get(prefix, [])
        elif keyword:
            results = [d for codes in mock_diagnoses.values() for d in codes if keyword.lower() in d["description"].lower()]
        else:
            results = []

        return {
            "query": icd10_code or keyword,
            "results": results,
            "total_found": len(results),
            "mode": "dry_run"
        }
    return {"results": []}

@mcp.resource("ehr://patients/mock")
def get_mock_patient_info() -> str:
    """Mock patient database information."""
    return json.dumps({
        "resource": "ehr://patients/mock",
        "description": "Synthetic patient database (Synthea-generated)",
        "total_patients": 10000,
        "demographics": "Realistic age, sex, ethnicity distributions",
        "clinical_data": ["Diagnoses (ICD-10)", "Labs", "Medications", "Procedures"],
        "privacy": "No real PHI/PII - all synthetic data",
        "fhir_compliant": True,
        "use_cases": ["Clinical-spatial correlation", "Outcome prediction", "Treatment response modeling"]
    }, indent=2)

def main() -> None:
    """Run the MCP mcp-mockepic server."""
    _run_server(mcp, server_name="mcp-mockepic", dry_run=DRY_RUN, env_var="MOCKEPIC_DRY_RUN")

if __name__ == "__main__":
    main()
