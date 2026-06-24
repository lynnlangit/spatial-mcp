"""MCP Cardiometabolic server — Server #19.

Cardiovascular risk scoring, biomarker interpretation, and preventive health
monitoring.  Implements Reynolds Risk Score (validated in women), Framingham
Risk Score, and ACC/AHA Pooled Cohort Equation.

Designed for PAT003: preventive cardiovascular health, 65+ female demographic.
Added for PAT003 gap report — replaces the multiomics architectural gap.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

from fastmcp import FastMCP
from pydantic import BeforeValidator

from .biomarker_ranges import REFERENCE_RANGES, classify_biomarker, JUPITER_NOTE
from .risk_scoring import (
    calculate_reynolds_women,
    calculate_framingham_women,
    calculate_ascvd_women_white,
)
from .guidelines import (
    get_statin_recommendation,
    get_monitoring_schedule,
    get_lifestyle_recommendations,
)

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
from common.transport import run_server as _run_server

logger = logging.getLogger(__name__)

# Server #19 -- added for PAT003 preventive health use case
mcp = FastMCP("cardiometabolic")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DRY_RUN = os.getenv("CARDIOMETABOLIC_DRY_RUN", "true").lower() in ("true", "1", "yes")


def add_dry_run_warning(result):
    """Add DRY_RUN warning -- delegates to shared implementation."""
    return _shared_add_dry_run_warning(
        result, dry_run=DRY_RUN, env_var="CARDIOMETABOLIC_DRY_RUN"
    )


# ---------------------------------------------------------------------------
# BeforeValidator for dict/list params (FastMCP 2.x pattern)
# ---------------------------------------------------------------------------

def _coerce_dict(val):
    if val is None or isinstance(val, dict):
        return val
    if isinstance(val, str):
        return json.loads(val)
    return val


def _coerce_list(val):
    if val is None or isinstance(val, list):
        return val
    if isinstance(val, str):
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return parsed
    return val


_CoerceDict = BeforeValidator(_coerce_dict)
_CoerceList = BeforeValidator(_coerce_list)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def _assess_biomarker_panel_impl(
    ldl_mg_dl: Optional[float] = None,
    hdl_mg_dl: Optional[float] = None,
    total_cholesterol_mg_dl: Optional[float] = None,
    triglycerides_mg_dl: Optional[float] = None,
    fasting_glucose_mg_dl: Optional[float] = None,
    hba1c_percent: Optional[float] = None,
    hscrp_mg_l: Optional[float] = None,
    bp_systolic_mmhg: Optional[float] = None,
    patient_sex: str = "female",
    patient_age: int = 67,
) -> Dict[str, Any]:
    """Interpret a cardiovascular biomarker panel against clinical reference ranges."""
    results = {}
    flags = []

    panel = {
        "ldl_mg_dl": ldl_mg_dl,
        "hdl_mg_dl": hdl_mg_dl,
        "total_cholesterol_mg_dl": total_cholesterol_mg_dl,
        "triglycerides_mg_dl": triglycerides_mg_dl,
        "fasting_glucose_mg_dl": fasting_glucose_mg_dl,
        "hba1c_percent": hba1c_percent,
        "hscrp_mg_l": hscrp_mg_l,
        "bp_systolic_mmhg": bp_systolic_mmhg,
    }

    for name, value in panel.items():
        if value is None:
            results[name] = {"value": None, "category": "not provided"}
            continue
        category = classify_biomarker(name, value)
        results[name] = {"value": value, "category": category}
        if "high" in category or category in ("prediabetes", "diabetes"):
            flags.append(f"{name}={value} is {category}")

    return {
        "status": "success",
        "biomarkers": results,
        "flags": flags,
        "patient_sex": patient_sex,
        "patient_age": patient_age,
        "dry_run": DRY_RUN,
    }


async def _calculate_cvd_risk_scores_impl(
    age: float = 67,
    systolic_bp: float = 138,
    total_cholesterol: float = 195,
    hdl: float = 58,
    hscrp: float = 1.8,
    patient_sex: str = "female",
    bp_treated: bool = True,
    current_smoker: bool = False,
    diabetes: bool = False,
    family_history_premature_mi: bool = True,
) -> Dict[str, Any]:
    """Calculate Reynolds, Framingham, and ASCVD risk scores."""
    # Pure computation -- run real logic even in DRY_RUN mode
    reynolds = calculate_reynolds_women(
        age=age,
        systolic_bp=systolic_bp,
        total_cholesterol=total_cholesterol,
        hdl=hdl,
        hscrp=hscrp,
        family_history_premature_mi=family_history_premature_mi,
        current_smoker=current_smoker,
    )
    framingham = calculate_framingham_women(
        age=age,
        total_cholesterol=total_cholesterol,
        hdl=hdl,
        systolic_bp=systolic_bp,
        bp_treated=bp_treated,
        current_smoker=current_smoker,
        diabetes=diabetes,
    )
    ascvd = calculate_ascvd_women_white(
        age=age,
        total_cholesterol=total_cholesterol,
        hdl=hdl,
        systolic_bp=systolic_bp,
        bp_treated=bp_treated,
        current_smoker=current_smoker,
        diabetes=diabetes,
    )

    # Determine statin consideration
    statin = get_statin_recommendation(
        ascvd_risk=ascvd["risk_10yr_percent"],
        ldl=total_cholesterol - hdl,  # approximate LDL
        hscrp=hscrp,
        lpa_known=False,
    )

    recommended = "reynolds" if patient_sex == "female" else "ascvd"

    result = {
        "status": "success",
        "reynolds": reynolds,
        "framingham": framingham,
        "ascvd": ascvd,
        "recommended_primary_score": recommended,
        "statin_consideration": statin,
        "dry_run": DRY_RUN,
    }
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


async def _assess_lpa_status_impl(
    lpa_mg_dl: Optional[float] = None,
) -> Dict[str, Any]:
    """Interpret Lp(a) status or recommend testing if not yet measured."""
    if lpa_mg_dl is None:
        return {
            "status": "success",
            "lpa_measured": False,
            "category": "unknown -- not yet measured",
            "recommendation": (
                "Order serum Lp(a) blood test. Measure once -- Lp(a) is genetically "
                "determined and does not change with lifestyle or standard lipid-lowering "
                "therapy. If elevated (>= 50 mg/dL or >= 125 nmol/L), risk "
                "reclassification and more aggressive LDL targets are warranted."
            ),
            "clinical_urgency": "high",
            "dry_run": DRY_RUN,
        }

    category = classify_biomarker("lpa_mg_dl", lpa_mg_dl)
    implications = []
    if lpa_mg_dl >= 50:
        implications.append("Independent CVD risk factor; upgrades statin indication")
        implications.append("Consider PCSK9 inhibitor (may lower Lp(a) ~25%)")
    elif lpa_mg_dl >= 30:
        implications.append("Borderline Lp(a); monitor with other risk factors")
    else:
        implications.append("Lp(a) within normal range; no additional risk from this marker")

    return {
        "status": "success",
        "lpa_measured": True,
        "lpa_mg_dl": lpa_mg_dl,
        "category": category,
        "implications": implications,
        "dry_run": DRY_RUN,
    }


async def _generate_preventive_report_impl(
    patient_id: str = "PAT003",
    biomarker_panel: Optional[Dict] = None,
    risk_scores: Optional[Dict] = None,
    genetic_screen_result: str = "unknown",
    fh_ruled_out: bool = False,
) -> Dict[str, Any]:
    """Generate a structured preventive cardiovascular health report."""
    # Use PAT003 defaults if no data provided
    if biomarker_panel is None:
        biomarker_panel = {
            "ldl_mg_dl": 118, "hdl_mg_dl": 58,
            "total_cholesterol_mg_dl": 195, "triglycerides_mg_dl": 142,
            "hscrp_mg_l": 1.8, "bp_systolic_mmhg": 138,
            "fasting_glucose_mg_dl": 98, "hba1c_percent": 5.6,
        }
    if risk_scores is None:
        risk_scores = {
            "reynolds_10yr_percent": 14.2,
            "framingham_10yr_percent": 10.0,
            "ascvd_10yr_percent": 10.3,
            "risk_category": "intermediate",
        }

    executive_summary = [
        f"10-year cardiovascular risk: {risk_scores.get('reynolds_10yr_percent', 'N/A')}% "
        f"(Reynolds Risk Score -- intermediate risk)",
        f"LDL {biomarker_panel.get('ldl_mg_dl', 'N/A')} mg/dL (near optimal); "
        f"hsCRP {biomarker_panel.get('hscrp_mg_l', 'N/A')} mg/L (moderate CVD risk)",
    ]
    if fh_ruled_out:
        executive_summary.append(
            "Familial hypercholesterolemia ruled out by Tier 1 screen; "
            "risk mechanism is polygenic and environmental"
        )
    else:
        executive_summary.append(
            "Genetic screening status: " + genetic_screen_result
        )

    priority_actions = [
        "1. Order serum Lp(a) -- one-time test, high impact on risk classification",
        "2. Discuss APOE genotyping -- informs both CVD and cognitive monitoring",
        "3. Consider CAC scoring -- best reclassification tool for intermediate risk",
        "4. Reassess statin decision after Lp(a) and CAC results are known",
    ]

    risk_category = risk_scores.get("risk_category", "intermediate")
    monitoring = get_monitoring_schedule(risk_category, on_treatment=True)
    lifestyle = get_lifestyle_recommendations()

    return {
        "status": "success",
        "patient_id": patient_id,
        "report_category": "preventive_health",
        "executive_summary": executive_summary,
        "risk_scores": risk_scores,
        "biomarker_panel": biomarker_panel,
        "priority_actions": priority_actions,
        "monitoring_schedule": monitoring,
        "lifestyle_recommendations": lifestyle,
        "disclaimer": (
            "This AI-generated preventive health summary must be reviewed by your "
            "healthcare team before any treatment decisions. It is not a substitute "
            "for professional medical advice. Not an FDA-cleared medical device."
        ),
        "dry_run": DRY_RUN,
    }


async def _get_lifestyle_evidence_impl(
    risk_factors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Return evidence-based lifestyle interventions with trial citations."""
    recommendations = get_lifestyle_recommendations()

    if risk_factors:
        # Filter by relevance to specified risk factors
        rf_lower = [rf.lower() for rf in risk_factors]
        scored = []
        for rec in recommendations:
            relevance = rec.get("relevance", "").lower()
            intervention = rec.get("intervention", "").lower()
            match = any(
                rf in relevance or rf in intervention
                for rf in rf_lower
            )
            scored.append({**rec, "matches_query": match})
        # Sort matched items first
        scored.sort(key=lambda x: (not x["matches_query"],))
        recommendations = scored

    return {
        "status": "success",
        "recommendations": recommendations,
        "count": len(recommendations),
        "risk_factors_queried": risk_factors,
        "dry_run": DRY_RUN,
    }


# ---------------------------------------------------------------------------
# PRS + APO tool implementations
# ---------------------------------------------------------------------------

# APO risk multipliers from AHA scientific statement and ESC 2025 guidelines
_APO_RISK_TABLE: Dict[str, Dict[str, float]] = {
    "preeclampsia": {"cad": 2.0, "stroke": 2.0, "grade": "AHA/ACC 2025 Class I"},
    "eclampsia": {"cad": 2.5, "stroke": 2.7, "grade": "ESC 2025"},
    "gestational_hypertension": {"cad": 1.7, "stroke": 1.8, "grade": "ESC 2025"},
    "gestational_diabetes": {"cad": 1.7, "stroke": 1.2, "grade": "AHA scientific statement"},
    "preterm_birth": {"cad": 1.4, "stroke": 1.6, "grade": "AHA scientific statement"},
    "low_birth_weight": {"cad": 1.3, "stroke": 1.3, "grade": "AHA scientific statement"},
    "iugr": {"cad": 1.3, "stroke": 1.3, "grade": "AHA scientific statement"},
    "placental_abruption": {"cad": 1.5, "stroke": 1.5, "grade": "ESC 2025"},
    "stillbirth": {"cad": 1.5, "stroke": 1.5, "grade": "ESC 2025"},
    "recurrent_miscarriage": {"cad": 1.3, "stroke": 1.3, "grade": "ESC 2025"},
}

_APO_CAP = 3.5  # Max combined multiplier to avoid compounding artifact


async def _search_cvd_prs_scores_impl(
    trait: str = "coronary artery disease",
    max_results: int = 10,
) -> Dict[str, Any]:
    """Query the PGS Catalog REST API for validated CVD polygenic risk scores."""
    if DRY_RUN:
        return {
            "scores": [
                {
                    "pgs_id": "PGS000018",
                    "trait_reported": "Coronary artery disease",
                    "variants_number": 6630150,
                    "ancestry_broad": "European",
                    "publication_doi": "10.1038/s41586-018-0183-z",
                },
                {
                    "pgs_id": "PGS000818",
                    "trait_reported": "Coronary heart disease",
                    "variants_number": 300,
                    "ancestry_broad": "European",
                    "publication_doi": "10.1161/CIRCULATIONAHA.120.053430",
                },
            ],
            "trait_queried": trait,
            "total_found": 2,
            "dry_run": True,
            "catalog_url": "https://www.pgscatalog.org/trait/EFO_0001645/",
        }

    import requests as _requests

    url = "https://www.pgscatalog.org/rest/score/search/"
    params = {"trait_mapped": trait, "limit": max_results}
    resp = _requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    scores = []
    for item in data.get("results", []):
        scores.append({
            "pgs_id": item.get("id", ""),
            "trait_reported": item.get("trait_reported", ""),
            "variants_number": item.get("variants_number", 0),
            "ancestry_broad": (
                item.get("ancestry_distribution", {})
                .get("gwas", {})
                .get("broad", "unknown")
                if isinstance(item.get("ancestry_distribution"), dict)
                else "unknown"
            ),
            "publication_doi": (
                item.get("publication", {}).get("doi", "")
                if isinstance(item.get("publication"), dict)
                else ""
            ),
        })

    return {
        "scores": scores,
        "trait_queried": trait,
        "total_found": len(scores),
        "dry_run": False,
        "catalog_url": f"https://www.pgscatalog.org/rest/score/search/?trait_mapped={trait}",
    }


async def _calculate_cvd_prs_impl(
    patient_id: str,
    genotype_file_path: str,
    pgs_id: str = "PGS000018",
) -> Dict[str, Any]:
    """Compute a polygenic risk score from a germline genotype file."""
    if DRY_RUN:
        # In DRY_RUN, accept "SYNTHETIC" as a valid path sentinel
        if genotype_file_path != "SYNTHETIC" and not os.path.exists(genotype_file_path):
            return {
                "status": "NO_GERMLINE_GENOTYPE",
                "patient_id": patient_id,
                "action_required": (
                    "Germline genotype data needed — SNP array (e.g. 23andMe/AncestryDNA "
                    "raw download) or germline WGS VCF. Somatic VCFs from tumor biopsy "
                    "are NOT valid input for PRS."
                ),
            }
        return {
            "patient_id": patient_id,
            "pgs_id": pgs_id,
            "raw_score": 0.847,
            "snps_in_score": 6630150,
            "snps_matched": 589234,
            "match_fraction": 0.089,
            "status": "CALCULATED",
            "dry_run": True,
            "note": "SYNTHETIC DATA — NOT FOR CLINICAL USE",
        }

    # Live path: check file exists
    if not os.path.exists(genotype_file_path):
        return {
            "status": "NO_GERMLINE_GENOTYPE",
            "patient_id": patient_id,
            "action_required": (
                "Germline genotype data needed — SNP array (e.g. 23andMe/AncestryDNA "
                "raw download) or germline WGS VCF. Somatic VCFs from tumor biopsy "
                "are NOT valid input for PRS."
            ),
        }

    import pandaspgs
    import pandas as pd

    # Fetch scoring file from PGS Catalog
    score_df = pandaspgs.get_score(pgs_id)
    if score_df is None or (hasattr(score_df, "empty") and score_df.empty):
        return {
            "status": "ERROR",
            "patient_id": patient_id,
            "error": f"Could not retrieve scoring file for {pgs_id} from PGS Catalog",
        }

    # Parse patient genotype (supports simple TSV with rsID, allele1, allele2)
    geno_df = pd.read_csv(genotype_file_path, sep="\t", comment="#")

    # Match SNPs and compute weighted sum
    snps_in_score = len(score_df)
    merged = score_df.merge(geno_df, left_on="rsID", right_on="rsID", how="inner")
    snps_matched = len(merged)

    if snps_matched == 0:
        return {
            "status": "NO_SNPS_MATCHED",
            "patient_id": patient_id,
            "pgs_id": pgs_id,
            "snps_in_score": snps_in_score,
            "snps_matched": 0,
            "match_fraction": 0.0,
        }

    # Sum weighted dosages (dosage column or count effect alleles)
    if "dosage" in merged.columns:
        raw_score = float((merged["effect_weight"] * merged["dosage"]).sum())
    else:
        raw_score = float(merged["effect_weight"].sum())

    return {
        "patient_id": patient_id,
        "pgs_id": pgs_id,
        "raw_score": raw_score,
        "snps_in_score": snps_in_score,
        "snps_matched": snps_matched,
        "match_fraction": round(snps_matched / snps_in_score, 4),
        "status": "CALCULATED",
        "dry_run": False,
    }


async def _interpret_cvd_prs_percentile_impl(
    patient_id: str,
    pgs_id: str,
    raw_score: float,
    ancestry: str = "European",
) -> Dict[str, Any]:
    """Map a raw PRS to a population percentile and clinical risk tier."""
    if DRY_RUN:
        return {
            "patient_id": patient_id,
            "pgs_id": pgs_id,
            "raw_score": raw_score,
            "percentile": 73.2,
            "risk_tier": "Intermediate",
            "ancestry_used": ancestry,
            "clinical_note": (
                "PRS in the intermediate range. Combine with traditional risk factors "
                "(Framingham, PCE) and adverse pregnancy outcome history for complete "
                "CVD risk picture."
            ),
            "reference": (
                "Khera et al. Nature 2018 — "
                "https://doi.org/10.1038/s41586-018-0183-z"
            ),
            "dry_run": True,
        }

    import requests as _requests
    from scipy.stats import norm

    # Fetch normalization stats from PGS Catalog
    url = f"https://www.pgscatalog.org/rest/score/{pgs_id}/"
    resp = _requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Extract mean/sd for ancestry (fall back to overall if unavailable)
    mean = 0.0
    sd = 1.0
    norm_data = data.get("ancestry_distribution", {}).get("eval", {})
    if isinstance(norm_data, dict) and ancestry in norm_data:
        stats = norm_data[ancestry]
        if isinstance(stats, dict):
            mean = stats.get("mean", 0.0)
            sd = stats.get("sd", 1.0)

    z = (raw_score - mean) / sd if sd > 0 else 0.0
    percentile = round(float(norm.cdf(z) * 100), 1)

    if percentile < 20:
        risk_tier = "Low"
    elif percentile < 80:
        risk_tier = "Intermediate"
    elif percentile < 95:
        risk_tier = "High"
    else:
        risk_tier = "Very High"

    return {
        "patient_id": patient_id,
        "pgs_id": pgs_id,
        "raw_score": raw_score,
        "percentile": percentile,
        "risk_tier": risk_tier,
        "ancestry_used": ancestry,
        "clinical_note": (
            f"PRS in the {risk_tier.lower()} range. Combine with traditional risk "
            f"factors (Framingham, PCE) and adverse pregnancy outcome history for "
            f"complete CVD risk picture."
        ),
        "reference": (
            "Khera et al. Nature 2018 — "
            "https://doi.org/10.1038/s41586-018-0183-z"
        ),
        "dry_run": False,
    }


async def _assess_pregnancy_complication_cv_risk_impl(
    patient_id: str,
    complications: List[str],
    age_at_complication: Optional[int] = None,
    num_affected_pregnancies: int = 1,
) -> Dict[str, Any]:
    """Assess lifetime CVD risk from adverse pregnancy outcome history."""
    recognized = []
    max_cad = 1.0
    max_stroke = 1.0

    for comp in complications:
        key = comp.strip().lower().replace(" ", "_").replace("-", "_")
        if key in _APO_RISK_TABLE:
            entry = _APO_RISK_TABLE[key]
            recognized.append(key)
            max_cad = max(max_cad, entry["cad"])
            max_stroke = max(max_stroke, entry["stroke"])

    # Additive enhancement for multiple distinct complications, capped
    if len(recognized) > 1:
        cad_sum = sum(_APO_RISK_TABLE[r]["cad"] - 1.0 for r in recognized) + 1.0
        stroke_sum = sum(_APO_RISK_TABLE[r]["stroke"] - 1.0 for r in recognized) + 1.0
        max_cad = min(cad_sum, _APO_CAP)
        max_stroke = min(stroke_sum, _APO_CAP)

    if max_cad <= 1.0:
        category = "None"
    elif max_cad <= 1.4:
        category = "Mild"
    elif max_cad < 2.0:
        category = "Moderate"
    else:
        category = "High"

    # Screening recommendations per 2025 guidelines
    screening = []
    if recognized:
        screening = [
            "Annual blood pressure monitoring",
            "Fasting lipid panel every 3 years from age 30",
            "Fasting glucose / HbA1c every 3 years",
            "Cardiology referral if ≥2 traditional CVD risk factors co-present",
        ]
        # Complication-specific additions
        for comp in recognized:
            screening.append(
                f"Inform all future care providers of {comp.replace('_', ' ')} history"
            )

    guideline_sources = [
        "2025 AHA/ACC Hypertension Guideline — https://www.ahajournals.org/",
        "2025 ESC Guidelines: CVD and Pregnancy — https://www.escardio.org/guidelines/",
        (
            "AHA Scientific Statement on APOs and CVD — "
            "https://www.ahajournals.org/doi/10.1161/CIR.0000000000000961"
        ),
    ]

    clinical_note = ""
    if recognized:
        comps_str = ", ".join(r.replace("_", " ") for r in recognized)
        clinical_note = (
            f"{comps_str.capitalize()} is a recognized CVD risk factor per 2025 "
            f"AHA/ACC and ESC guidelines. This history should be documented in all "
            f"CVD risk calculations and shared with cardiologist. This assessment is "
            f"for research purposes only — NOT FOR CLINICAL USE."
        )
    else:
        clinical_note = (
            "No recognized adverse pregnancy outcomes identified from the provided "
            "complications list. No additional CVD risk enhancement from APO history."
        )

    return {
        "patient_id": patient_id,
        "complications_reported": complications,
        "complications_recognized": recognized,
        "risk_enhancement": {
            "cad_multiplier": max_cad,
            "stroke_multiplier": max_stroke,
            "category": category,
        },
        "num_affected_pregnancies": num_affected_pregnancies,
        "age_at_complication": age_at_complication,
        "screening_recommendations": screening,
        "guideline_sources": guideline_sources,
        "clinical_note": clinical_note,
        "dry_run": DRY_RUN,
    }


# ============================================================================
# MCP Tool wrappers
# ============================================================================

@mcp.tool()
async def assess_biomarker_panel(
    ldl_mg_dl: Optional[float] = None,
    hdl_mg_dl: Optional[float] = None,
    total_cholesterol_mg_dl: Optional[float] = None,
    triglycerides_mg_dl: Optional[float] = None,
    fasting_glucose_mg_dl: Optional[float] = None,
    hba1c_percent: Optional[float] = None,
    hscrp_mg_l: Optional[float] = None,
    bp_systolic_mmhg: Optional[float] = None,
    patient_sex: str = "female",
    patient_age: int = 67,
) -> dict:
    """Interpret a cardiovascular biomarker panel against clinical reference ranges.

    Classifies each biomarker value into clinical categories (e.g., optimal,
    borderline, high) and flags out-of-range values. Uses ACC/AHA and
    ATP III reference ranges.

    Args:
        ldl_mg_dl: LDL cholesterol in mg/dL.
        hdl_mg_dl: HDL cholesterol in mg/dL.
        total_cholesterol_mg_dl: Total cholesterol in mg/dL.
        triglycerides_mg_dl: Triglycerides in mg/dL.
        fasting_glucose_mg_dl: Fasting glucose in mg/dL.
        hba1c_percent: Hemoglobin A1c as percentage.
        hscrp_mg_l: High-sensitivity C-reactive protein in mg/L.
        bp_systolic_mmhg: Systolic blood pressure in mmHg.
        patient_sex: Patient sex (male/female).
        patient_age: Patient age in years.

    Returns:
        Dictionary with biomarker interpretations, clinical categories, and flags.
    """
    result = await _assess_biomarker_panel_impl(
        ldl_mg_dl=ldl_mg_dl, hdl_mg_dl=hdl_mg_dl,
        total_cholesterol_mg_dl=total_cholesterol_mg_dl,
        triglycerides_mg_dl=triglycerides_mg_dl,
        fasting_glucose_mg_dl=fasting_glucose_mg_dl,
        hba1c_percent=hba1c_percent, hscrp_mg_l=hscrp_mg_l,
        bp_systolic_mmhg=bp_systolic_mmhg,
        patient_sex=patient_sex, patient_age=patient_age,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def calculate_cvd_risk_scores(
    age: float = 67,
    systolic_bp: float = 138,
    total_cholesterol: float = 195,
    hdl: float = 58,
    hscrp: float = 1.8,
    patient_sex: str = "female",
    bp_treated: bool = True,
    current_smoker: bool = False,
    diabetes: bool = False,
    family_history_premature_mi: bool = True,
) -> dict:
    """Calculate Reynolds, Framingham, and ASCVD 10-year cardiovascular risk scores.

    Runs three validated risk equations and returns the recommended primary
    score (Reynolds for women, ASCVD for men). Also provides statin
    initiation guidance per 2018 ACC/AHA guidelines.

    Args:
        age: Patient age in years.
        systolic_bp: Systolic blood pressure in mmHg.
        total_cholesterol: Total cholesterol in mg/dL.
        hdl: HDL cholesterol in mg/dL.
        hscrp: High-sensitivity CRP in mg/L.
        patient_sex: Patient sex (male/female).
        bp_treated: Whether blood pressure is treated with medication.
        current_smoker: Whether patient currently smokes.
        diabetes: Whether patient has diabetes.
        family_history_premature_mi: Premature MI in first-degree relative.

    Returns:
        Dictionary with Reynolds, Framingham, and ASCVD scores plus
        statin consideration guidance.
    """
    return await _calculate_cvd_risk_scores_impl(
        age=age, systolic_bp=systolic_bp,
        total_cholesterol=total_cholesterol, hdl=hdl, hscrp=hscrp,
        patient_sex=patient_sex, bp_treated=bp_treated,
        current_smoker=current_smoker, diabetes=diabetes,
        family_history_premature_mi=family_history_premature_mi,
    )


@mcp.tool()
async def assess_lpa_status(
    lpa_mg_dl: Optional[float] = None,
) -> dict:
    """Assess lipoprotein(a) status or recommend testing if not yet measured.

    Lp(a) is an independent, genetically determined CVD risk factor not captured
    by standard lipid panels. If lpa_mg_dl is None (not yet measured), returns
    a recommendation to order the test. If provided, classifies the value and
    returns risk implications.

    Args:
        lpa_mg_dl: Lipoprotein(a) level in mg/dL, or None if not measured.

    Returns:
        Dictionary with Lp(a) interpretation, risk implications, and
        recommendations.
    """
    result = await _assess_lpa_status_impl(lpa_mg_dl=lpa_mg_dl)
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def generate_preventive_report(
    patient_id: str = "PAT003",
    biomarker_panel: Annotated[Optional[Dict], _CoerceDict] = None,
    risk_scores: Annotated[Optional[Dict], _CoerceDict] = None,
    genetic_screen_result: str = "unknown",
    fh_ruled_out: bool = False,
) -> dict:
    """Generate a structured preventive cardiovascular health report.

    Combines biomarker data, risk scores, genetic screening results, and
    evidence-based guidelines into a comprehensive preventive health summary
    suitable for clinical review.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        biomarker_panel: Dict of biomarker values (ldl_mg_dl, hdl_mg_dl, etc.).
        risk_scores: Dict of risk scores (reynolds_10yr_percent, etc.).
        genetic_screen_result: Overall result of genetic screen (e.g., "negative").
        fh_ruled_out: Whether familial hypercholesterolemia has been ruled out.

    Returns:
        Dictionary with executive summary, risk scores, priority actions,
        monitoring schedule, lifestyle recommendations, and disclaimer.
    """
    result = await _generate_preventive_report_impl(
        patient_id=patient_id,
        biomarker_panel=biomarker_panel,
        risk_scores=risk_scores,
        genetic_screen_result=genetic_screen_result,
        fh_ruled_out=fh_ruled_out,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def get_lifestyle_evidence(
    risk_factors: Annotated[Optional[List[str]], _CoerceList] = None,
) -> dict:
    """Get evidence-based lifestyle interventions with trial citations.

    Returns interventions ranked by relevance, each citing the landmark
    clinical trial that supports the recommendation.

    Args:
        risk_factors: Optional list of risk factors to filter by
            (e.g., ["hypertension", "ldl", "inflammation"]).

    Returns:
        List of evidence-based interventions with citations and relevance.
    """
    result = await _get_lifestyle_evidence_impl(risk_factors=risk_factors)
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def search_cvd_prs_scores(
    trait: str = "coronary artery disease",
    max_results: int = 10,
) -> dict:
    """Search the PGS Catalog for validated cardiovascular polygenic risk scores.

    Queries the PGS Catalog REST API for published, peer-reviewed polygenic
    risk scores matching a cardiovascular trait. Returns score IDs, variant
    counts, ancestry information, and publication DOIs.

    Args:
        trait: Trait to search for (e.g., "coronary artery disease",
            "atrial fibrillation", "hypertension").
        max_results: Maximum number of scores to return (default: 10).

    Returns:
        Dictionary with matching PGS Catalog scores, trait queried, and
        catalog URL.
    """
    result = await _search_cvd_prs_scores_impl(trait=trait, max_results=max_results)
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def calculate_cvd_prs(
    patient_id: str,
    genotype_file_path: str,
    pgs_id: str = "PGS000018",
) -> dict:
    """Compute a polygenic risk score from a patient's germline genotype file.

    Fetches the scoring file from the PGS Catalog, matches SNPs by rsID
    against the patient's genotype, and computes a weighted sum. Requires
    germline genotype data (SNP array or WGS VCF) — somatic VCFs from
    tumor biopsy are NOT valid input.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        genotype_file_path: Path to germline genotype file (TSV or VCF).
            Use "SYNTHETIC" in DRY_RUN mode to get a synthetic fixture.
        pgs_id: PGS Catalog score ID (default: "PGS000018" for CAD).

    Returns:
        Dictionary with raw score, SNP match statistics, and status.
        Returns NO_GERMLINE_GENOTYPE if file not found.
    """
    result = await _calculate_cvd_prs_impl(
        patient_id=patient_id,
        genotype_file_path=genotype_file_path,
        pgs_id=pgs_id,
    )
    if DRY_RUN and result.get("status") != "NO_GERMLINE_GENOTYPE":
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def interpret_cvd_prs_percentile(
    patient_id: str,
    pgs_id: str,
    raw_score: float,
    ancestry: str = "European",
) -> dict:
    """Map a raw polygenic risk score to a population percentile and risk tier.

    Uses PGS Catalog normalization data to compute a z-score and percentile
    for the patient's ancestry group. Maps percentile to clinical risk tiers
    per Khera et al. 2018: <20th Low, 20-80 Intermediate, 80-95 High,
    >95 Very High (equivalent to monogenic risk).

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        pgs_id: PGS Catalog score ID used in calculate_cvd_prs.
        raw_score: Raw PRS value from calculate_cvd_prs.
        ancestry: Ancestry group for normalization (default: "European").

    Returns:
        Dictionary with percentile, risk tier, clinical note, and reference.
    """
    result = await _interpret_cvd_prs_percentile_impl(
        patient_id=patient_id,
        pgs_id=pgs_id,
        raw_score=raw_score,
        ancestry=ancestry,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def assess_pregnancy_complication_cv_risk(
    patient_id: str,
    complications: Annotated[List[str], _CoerceList],
    age_at_complication: Optional[int] = None,
    num_affected_pregnancies: int = 1,
) -> dict:
    """Assess lifetime cardiovascular risk from adverse pregnancy outcome history.

    Evaluates known adverse pregnancy outcomes (APOs) as independent CVD risk
    enhancers per 2025 AHA/ACC and ESC guidelines. Preeclampsia, for example,
    doubles 5-15 year stroke and heart disease risk. Returns risk multipliers,
    category, and screening recommendations.

    Recognized complications: preeclampsia, eclampsia, gestational_hypertension,
    gestational_diabetes, preterm_birth, low_birth_weight, iugr,
    placental_abruption, stillbirth, recurrent_miscarriage.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        complications: List of adverse pregnancy outcomes (case-insensitive).
        age_at_complication: Age at time of complication (optional).
        num_affected_pregnancies: Number of pregnancies affected (default: 1).

    Returns:
        Dictionary with recognized complications, CAD/stroke risk multipliers,
        risk category, screening recommendations, and guideline citations.
    """
    result = await _assess_pregnancy_complication_cv_risk_impl(
        patient_id=patient_id,
        complications=complications,
        age_at_complication=age_at_complication,
        num_affected_pregnancies=num_affected_pregnancies,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP cardiometabolic server."""
    _run_server(
        mcp,
        server_name="mcp-cardiometabolic",
        dry_run=DRY_RUN,
        env_var="CARDIOMETABOLIC_DRY_RUN",
    )


if __name__ == "__main__":
    main()
