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
        return {
            "patient_id": patient_id,
            "demographics": {
                "age": 64,
                "sex": "F",
                "ethnicity": "Caucasian",
                "mrn": f"MRN{patient_id}"
            },
            "diagnoses": [
                {"icd10": "C50.9", "description": "Breast cancer, unspecified", "date": "2024-01-15"},
                {"icd10": "E11.9", "description": "Type 2 diabetes", "date": "2020-03-22"}
            ],
            "labs": {
                "hemoglobin": {"value": 12.5, "unit": "g/dL", "ref_range": "12-16"},
                "wbc": {"value": 7.2, "unit": "K/uL", "ref_range": "4-11"}
            } if include_labs else {},
            "medications": [
                {"name": "Tamoxifen", "dose": "20mg", "frequency": "daily"},
                {"name": "Metformin", "dose": "500mg", "frequency": "BID"}
            ] if include_meds else [],
            "mode": "dry_run"
        }
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
                {"code": "C50.1", "description": "Malignant neoplasm of central portion of breast"}
            ],
            "E11": [
                {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
                {"code": "E11.65", "description": "Type 2 diabetes with hyperglycemia"}
            ]
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
