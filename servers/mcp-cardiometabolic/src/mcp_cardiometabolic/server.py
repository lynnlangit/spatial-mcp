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

from .biomarker_ranges import (
    REFERENCE_RANGES, classify_biomarker, JUPITER_NOTE, LOW_FLAG_CATEGORIES,
)
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
# XAI metadata helpers
# ---------------------------------------------------------------------------

def _build_xai_metadata(
    confidence_level: str,
    confidence_note: str,
    key_drivers: list,
    guideline_version: str,
    evidence_grade: str,
    counterfactual: Optional[str] = None,
) -> dict:
    """Standardized XAI metadata for all mcp-cardiometabolic tool outputs.

    evidence_grade values:
      "Class I (AHA/ACC)"     -- Strong recommendation; benefit clearly outweighs risk; RCT evidence
      "Class I (ESC/EAS)"     -- Same strength, European guideline source
      "Class IIa (AHA/ACC)"   -- Moderate recommendation; benefit likely outweighs risk
      "Class IIb (AHA/ACC)"   -- Weak recommendation; benefit may outweigh risk
      "Expert Consensus"      -- No RCT; guideline committee agreement
      "Observational Data"    -- Cohort/epidemiological data; no RCT; higher uncertainty
      "Research Only"         -- Platform-specific research estimate; no external guideline
    """
    assert confidence_level in ("high", "moderate", "low"), \
        f"confidence_level must be 'high', 'moderate', or 'low' -- got: {confidence_level}"
    # Filter None from key_drivers
    key_drivers = [d for d in key_drivers if d is not None]
    assert 1 <= len(key_drivers) <= 3, \
        f"key_drivers must contain 1-3 items -- got: {len(key_drivers)}"

    return {
        "confidence_level": confidence_level,
        "confidence_note": confidence_note,
        "key_drivers": key_drivers,
        "counterfactual": counterfactual,
        "guideline_version": guideline_version,
        "evidence_grade": evidence_grade,
    }


def _inline_confidence(value_str: str, xai: dict) -> str:
    """Append confidence marker to a finding string when not high."""
    level = xai.get("confidence_level", "high")
    note = xai.get("confidence_note", "")
    short_note = note.split(".")[0] if note else ""

    if level == "moderate":
        return f"{value_str} *(confidence: moderate -- {short_note})*"
    elif level == "low":
        return f"{value_str} !! *(confidence: low -- {short_note})*"
    else:
        return value_str


_TOOL_LABELS = {
    "biomarker_panel": "Biomarker Panel",
    "cvd_risk_scores": "CVD Risk Score (Reynolds/ASCVD)",
    "fh_clinical_score": "FH Clinical Score (DLCN)",
    "lpa_status": "Lp(a) Status",
    "lipid_pattern": "Lipid Pattern",
    "lipid_treatment_targets": "Lipid Treatment Targets",
    "renal_drug_constraints": "Renal Drug Constraints",
    "postcovid_cv_risk": "Post-COVID CV Risk Adjustment",
    "pregnancy_complication_risk": "Pregnancy Complication CV Risk",
}

_CONFIDENCE_ICONS = {"high": "OK", "moderate": "!!", "low": "XX"}


def _build_evidence_table(xai_collection: dict) -> str:
    """Build a plain-text Evidence Strength Summary table from collected xai_metadata."""
    rows = []
    for tool_key, xai in xai_collection.items():
        if not xai:
            continue
        label = _TOOL_LABELS.get(tool_key, tool_key)
        level = xai.get("confidence_level", "--")
        icon = _CONFIDENCE_ICONS.get(level, "--")
        grade = xai.get("evidence_grade", "--")
        drivers = "; ".join(xai.get("key_drivers", []) or [])[:80]
        rows.append((label, f"{icon} {level.capitalize()}", grade, drivers))

    if not rows:
        return ""

    header = f"{'Finding':<40} {'Confidence':<18} {'Evidence Grade':<28} {'Key Drivers'}"
    divider = "-" * 120
    table_lines = [
        "\n\nEVIDENCE STRENGTH SUMMARY",
        "=" * 120,
        header,
        divider,
    ]
    for label, conf, grade, drivers in rows:
        table_lines.append(f"{label:<40} {conf:<18} {grade:<28} {drivers}")

    table_lines += [
        divider,
        "!!  Items with moderate/low confidence require additional clinical judgment.",
        "XX  Low confidence items are research estimates only.",
        "=" * 120,
    ]
    return "\n".join(table_lines)


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
    apob_mg_dl: Optional[float] = None,
    non_hdl_cholesterol_mg_dl: Optional[float] = None,
    patient_sex: str = "female",
    patient_age: int = 67,
    ldl_measured_directly: bool = False,
) -> Dict[str, Any]:
    """Interpret a cardiovascular biomarker panel against clinical reference ranges."""
    results = {}
    flags = []

    # Compute Non-HDL if not provided but TC and HDL are available
    if non_hdl_cholesterol_mg_dl is None and (
        total_cholesterol_mg_dl is not None and hdl_mg_dl is not None
    ):
        non_hdl_cholesterol_mg_dl = total_cholesterol_mg_dl - hdl_mg_dl

    panel = {
        "ldl_mg_dl": ldl_mg_dl,
        "hdl_mg_dl": hdl_mg_dl,
        "total_cholesterol_mg_dl": total_cholesterol_mg_dl,
        "triglycerides_mg_dl": triglycerides_mg_dl,
        "fasting_glucose_mg_dl": fasting_glucose_mg_dl,
        "hba1c_percent": hba1c_percent,
        "hscrp_mg_l": hscrp_mg_l,
        "bp_systolic_mmhg": bp_systolic_mmhg,
        "apob_mg_dl": apob_mg_dl,
        "non_hdl_cholesterol_mg_dl": non_hdl_cholesterol_mg_dl,
    }

    for name, value in panel.items():
        if value is None:
            results[name] = {"value": None, "category": "not provided"}
            continue
        category = classify_biomarker(name, value)
        entry: Dict[str, Any] = {"value": value, "category": category}

        # Flag high values
        if "high" in category or "elevated" in category or category in (
            "prediabetes", "diabetes",
        ):
            flags.append(f"{name}={value} is {category}")

        # Flag low values (bidirectional)
        if category in LOW_FLAG_CATEGORIES:
            flags.append(f"{name}={value} is {category}")

        # ApoB risk-tier context
        if name == "apob_mg_dl" and value is not None:
            entry["risk_tier_context"] = (
                "ApoB targets are risk-tier dependent. For very high CVD risk "
                "(possible FH, multiple risk factors), target is <70-80 mg/dL. "
                "For high risk, <80 mg/dL. For intermediate risk, <100 mg/dL."
            )

        # Non-HDL therapeutic target note
        if name == "non_hdl_cholesterol_mg_dl" and value is not None:
            entry["therapeutic_target_note"] = (
                "For high-risk patients, Non-HDL target = LDL target + 30 mg/dL. "
                "For very high-risk (LDL target <70 mg/dL), Non-HDL target = <100 mg/dL."
            )

        results[name] = entry

    # XAI confidence logic
    friedewald_invalid = (
        triglycerides_mg_dl is not None
        and triglycerides_mg_dl > 200
        and ldl_mg_dl is not None
        and not ldl_measured_directly
    )
    panel_values = [
        ldl_mg_dl, hdl_mg_dl, total_cholesterol_mg_dl, triglycerides_mg_dl,
        fasting_glucose_mg_dl, hba1c_percent, hscrp_mg_l, bp_systolic_mmhg,
    ]
    panel_incomplete = sum(1 for v in panel_values if v is not None) < 4

    if friedewald_invalid:
        conf = "low"
        conf_note = (
            "Calculated LDL (Friedewald equation) is unreliable at triglycerides >200 mg/dL. "
            "LDL value may be underestimated. Direct LDL measurement recommended."
        )
    elif panel_incomplete or (ldl_mg_dl is not None and not ldl_measured_directly):
        conf = "moderate"
        conf_note = (
            "One or more values are calculated rather than directly measured, "
            "or panel is incomplete. Direct measurement preferred."
        )
    else:
        conf = "high"
        conf_note = "All values are directly measured laboratory results against validated reference ranges."

    bio_drivers = [
        f"Glucose {fasting_glucose_mg_dl} mg/dL" if fasting_glucose_mg_dl else None,
        f"LDL {ldl_mg_dl} mg/dL" if ldl_mg_dl else None,
        f"ApoB {apob_mg_dl} mg/dL" if apob_mg_dl else None,
    ]
    # Fallback if none of the primary drivers are available
    if not any(bio_drivers):
        provided = [k for k, v in panel.items() if v is not None]
        bio_drivers = [f"Panel inputs: {', '.join(provided[:3]) if provided else 'none'}"]

    xai = _build_xai_metadata(
        confidence_level=conf,
        confidence_note=conf_note,
        key_drivers=bio_drivers,
        guideline_version="AHA/ACC 2018 Cholesterol Guideline; ADA Standards of Care 2024",
        evidence_grade="Class I (AHA/ACC)",
        counterfactual=(
            f"If LDL were reduced to target (<70 mg/dL for high-risk), "
            f"atherogenic burden would decrease by approximately "
            f"{round((ldl_mg_dl - 70) / ldl_mg_dl * 100)}%."
        ) if ldl_mg_dl and ldl_mg_dl > 70 else None,
    )

    return {
        "status": "success",
        "biomarkers": results,
        "flags": flags,
        "patient_sex": patient_sex,
        "patient_age": patient_age,
        "xai_metadata": xai,
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

    # XAI confidence logic
    outside_validation = []
    if age > 79 or age < 40:
        outside_validation.append(f"age {age} is outside validated range (40-79)")
    if patient_sex == "female":
        outside_validation.append(
            "Reynolds validated only in women; less robust for non-female patients"
        ) if patient_sex != "female" else None

    if not outside_validation:
        conf = "high"
        conf_note = "Patient characteristics fit the validated population range for this risk calculator."
    else:
        outside_validation = [v for v in outside_validation if v is not None]
        conf = "moderate"
        conf_note = (
            f"Calculator may underestimate true risk. Known limitations: "
            f"{'; '.join(outside_validation)}."
        )

    xai = _build_xai_metadata(
        confidence_level=conf,
        confidence_note=conf_note,
        key_drivers=[
            f"Systolic BP {systolic_bp} mmHg",
            f"Total cholesterol {total_cholesterol} mg/dL, HDL {hdl} mg/dL",
            f"hsCRP {hscrp} mg/L" if patient_sex == "female" else f"Diabetes: {diabetes}",
        ],
        guideline_version="Reynolds Risk Score (Ridker 2007); ACC/AHA PCE 2013",
        evidence_grade="Class I (AHA/ACC)",
        counterfactual=None,
    )

    result = {
        "status": "success",
        "reynolds": reynolds,
        "framingham": framingham,
        "ascvd": ascvd,
        "recommended_primary_score": recommended,
        "statin_consideration": statin,
        "xai_metadata": xai,
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
            "xai_metadata": _build_xai_metadata(
                confidence_level="high",
                confidence_note=(
                    "Recommendation to measure Lp(a) is a Class I guideline recommendation. "
                    "No measurement data to interpret yet."
                ),
                key_drivers=["Lp(a) not yet measured -- recommend one-time test"],
                guideline_version="EAS Lp(a) Consensus Statement 2022; ACC/AHA Cholesterol Guideline 2018",
                evidence_grade="Class I (ESC/EAS)",
                counterfactual=None,
            ),
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
        "xai_metadata": _build_xai_metadata(
            confidence_level="high",
            confidence_note=(
                "Lp(a) is a direct laboratory measurement. Interpretation thresholds "
                "are from EAS 2022 Lp(a) Consensus Statement and ACC/AHA 2018 Cholesterol "
                "Guideline. Lp(a) is genetically fixed -- a single lifetime measurement is sufficient."
            ),
            key_drivers=[f"Lp(a): {lpa_mg_dl} mg/dL (threshold for elevated risk: >=50 mg/dL)"],
            guideline_version="EAS Lp(a) Consensus Statement 2022; ACC/AHA Cholesterol Guideline 2018",
            evidence_grade="Class I (ESC/EAS)",
            counterfactual=(
                f"If Lp(a) were >=50 mg/dL, it would be flagged as an independent "
                "cardiovascular risk factor requiring targeted therapy consideration."
            ) if lpa_mg_dl < 50 else None,
        ),
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

    # Harvest XAI metadata by internally calling _impl functions
    xai_collection = {}

    biomarker_result = await _assess_biomarker_panel_impl(
        ldl_mg_dl=biomarker_panel.get("ldl_mg_dl"),
        hdl_mg_dl=biomarker_panel.get("hdl_mg_dl"),
        total_cholesterol_mg_dl=biomarker_panel.get("total_cholesterol_mg_dl"),
        triglycerides_mg_dl=biomarker_panel.get("triglycerides_mg_dl"),
        fasting_glucose_mg_dl=biomarker_panel.get("fasting_glucose_mg_dl"),
        hba1c_percent=biomarker_panel.get("hba1c_percent"),
        hscrp_mg_l=biomarker_panel.get("hscrp_mg_l"),
        bp_systolic_mmhg=biomarker_panel.get("bp_systolic_mmhg"),
        apob_mg_dl=biomarker_panel.get("apob_mg_dl"),
    )
    xai_collection["biomarker_panel"] = biomarker_result.get("xai_metadata", {})

    risk_score_result = await _calculate_cvd_risk_scores_impl(
        age=67,
        systolic_bp=biomarker_panel.get("bp_systolic_mmhg", 138),
        total_cholesterol=biomarker_panel.get("total_cholesterol_mg_dl", 195),
        hdl=biomarker_panel.get("hdl_mg_dl", 58),
        hscrp=biomarker_panel.get("hscrp_mg_l", 1.8),
    )
    xai_collection["cvd_risk_scores"] = risk_score_result.get("xai_metadata", {})

    # Apply inline confidence markers to executive summary
    executive_summary = [
        _inline_confidence(executive_summary[0], xai_collection.get("cvd_risk_scores", {})),
        _inline_confidence(executive_summary[1], xai_collection.get("biomarker_panel", {})),
    ] + executive_summary[2:]

    # Build evidence table
    evidence_table_str = _build_evidence_table(xai_collection)

    # Evidence strength summary
    evidence_strength_summary = {
        "table_text": evidence_table_str,
        "confidence_counts": {
            "high": sum(1 for x in xai_collection.values() if x.get("confidence_level") == "high"),
            "moderate": sum(1 for x in xai_collection.values() if x.get("confidence_level") == "moderate"),
            "low": sum(1 for x in xai_collection.values() if x.get("confidence_level") == "low"),
        },
        "lowest_confidence_items": [
            _TOOL_LABELS.get(k, k)
            for k, v in xai_collection.items()
            if v.get("confidence_level") == "low"
        ],
        "action_required": any(
            v.get("confidence_level") == "low"
            for v in xai_collection.values()
        ),
    }

    report_xai = _build_xai_metadata(
        confidence_level="moderate",
        confidence_note=(
            "Report aggregates findings of varying confidence. "
            "See evidence_strength_summary for per-finding breakdown."
        ),
        key_drivers=[
            "See evidence_strength_summary.lowest_confidence_items for items requiring clinical judgment"
        ],
        guideline_version="Multiple -- see individual tool citations",
        evidence_grade="Expert Consensus",
    )

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
        "evidence_strength_summary": evidence_strength_summary,
        "disclaimer": (
            "This AI-generated preventive health summary must be reviewed by your "
            "healthcare team before any treatment decisions. It is not a substitute "
            "for professional medical advice. Not an FDA-cleared medical device."
        ),
        "xai_metadata": report_xai,
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
    covid_severe_history: bool = False,
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

    # Double endothelial injury: preeclampsia/eclampsia + severe COVID
    has_pe = any(c in recognized for c in ("preeclampsia", "eclampsia"))
    double_injury = covid_severe_history and has_pe

    if double_injury:
        screening.append(
            "DOUBLE ENDOTHELIAL INJURY IDENTIFIED — preeclampsia + severe COVID-19: "
            "Two independent endothelial injury events are present. Preeclampsia (AHA/ACC "
            "Class I, 2× CAD/stroke risk) damaged vascular endothelium at the time of "
            "pregnancy. Severe COVID-19 caused a second wave of endothelial injury via "
            "ACE2 receptor disruption and angiotensin II accumulation. Standard risk "
            "calculators apply the preeclampsia 2× multiplier but cannot capture this "
            "compounding — true cardiovascular risk likely exceeds any calculated estimate. "
            "Preventive cardiology referral strongly recommended."
        )

    # XAI confidence logic
    has_preeclampsia = any(c in recognized for c in ("preeclampsia", "eclampsia"))
    if has_preeclampsia and not double_injury:
        preg_conf = "high"
        preg_conf_note = (
            "Preeclampsia cardiovascular risk multiplier (2x) is a 2025 AHA/ACC Class I "
            "recommendation grounded in large meta-analyses. High confidence for this complication."
        )
    elif double_injury:
        preg_conf = "moderate"
        preg_conf_note = (
            "Preeclampsia multiplier is AHA/ACC Class I (high evidence). The additional "
            "compounding effect of severe COVID-19 endothelial injury is supported by "
            "mechanism-based evidence but no combined validated risk calculator exists."
        )
    else:
        preg_conf = "moderate"
        preg_conf_note = (
            "Non-preeclampsia adverse pregnancy outcomes carry Class IIa evidence for "
            "CV risk enhancement. Effect sizes are less precisely characterized than preeclampsia."
        )

    xai = _build_xai_metadata(
        confidence_level=preg_conf,
        confidence_note=preg_conf_note,
        key_drivers=[
            f"Complications recognized: {', '.join(recognized)}" if recognized else "No recognized complications",
            f"Risk enhancement: {category} (CAD multiplier: {max_cad}x)",
            "Double endothelial injury (preeclampsia + COVID)" if double_injury else None,
        ],
        guideline_version="2025 AHA/ACC Hypertension Guideline; 2025 ESC CVD and Pregnancy Guidelines",
        evidence_grade="Class I (AHA/ACC)" if has_preeclampsia else "Class IIa (AHA/ACC)",
        counterfactual=(
            "Without the preeclampsia history, the 2x CAD/stroke risk multiplier "
            "would not apply and standard risk calculators would be uncorrected."
        ) if has_preeclampsia else None,
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
        "double_endothelial_injury_flag": double_injury,
        "double_endothelial_injury_note": (
            "Two independent endothelial injury events: preeclampsia (2025 AHA/ACC Class I, "
            "2× CAD and stroke risk) and severe COVID-19 (ACE2-mediated endothelial activation "
            "and RAAS disruption). The combined atherogenic burden is not modeled by any standard "
            "risk calculator. This is a research flag — requires clinician review."
        ) if double_injury else None,
        "xai_metadata": xai,
        "dry_run": DRY_RUN,
    }


# ---------------------------------------------------------------------------
# Lipid pattern + FH clinical score implementations
# ---------------------------------------------------------------------------

# ApoB targets by risk tier (mg/dL)
_APOB_TARGETS = {"very_high": 70, "high": 80, "intermediate": 90, "low": 100}

# LDL targets by risk tier (mg/dL)
_LDL_TARGETS = {"very_high": 55, "high": 70, "intermediate": 100, "low": 116}

# Non-HDL targets by risk tier (mg/dL) — LDL target + 30
_NON_HDL_TARGETS = {"very_high": 85, "high": 100, "intermediate": 130, "low": 146}


async def _interpret_lipid_pattern_impl(
    patient_id: str,
    ldl_cholesterol: Optional[float] = None,
    total_cholesterol: Optional[float] = None,
    hdl_cholesterol: Optional[float] = None,
    triglycerides: Optional[float] = None,
    non_hdl_cholesterol: Optional[float] = None,
    apob: Optional[float] = None,
    ldl_measured_directly: bool = False,
    patient_risk_tier: str = "high",
    patient_sex: str = "female",
) -> Dict[str, Any]:
    """Classify clinical dyslipidemia pattern from a full lipid panel."""
    # Pure computation -- run real logic even in DRY_RUN mode (no external APIs)

    # Compute Non-HDL if not provided
    if non_hdl_cholesterol is None and (
        total_cholesterol is not None and hdl_cholesterol is not None
    ):
        non_hdl_cholesterol = total_cholesterol - hdl_cholesterol

    # Friedewald LDL validity
    friedewald_valid = True
    friedewald_note = None
    if triglycerides is not None and not ldl_measured_directly:
        if triglycerides > 400:
            friedewald_valid = False
            friedewald_note = (
                "Calculated LDL is UNRELIABLE at TG >400 mg/dL. Direct LDL "
                "measurement required."
            )
        elif triglycerides > 200:
            friedewald_valid = False
            friedewald_note = (
                "Calculated LDL may be INACCURATE at TG >200 mg/dL. The Friedewald "
                "equation (LDL = TC - HDL - TG/5) assumes VLDL = TG/5, which "
                "underestimates VLDL when triglycerides are elevated. A direct LDL "
                "blood test is recommended to confirm."
            )

    # Determine LDL target for risk tier
    ldl_target = _LDL_TARGETS.get(patient_risk_tier, 100)
    ldl_elevated = ldl_cholesterol is not None and ldl_cholesterol > ldl_target
    tg_elevated = triglycerides is not None and triglycerides >= 150

    # HDL sex-specific target
    hdl_target = 50 if patient_sex == "female" else 40
    hdl_low = hdl_cholesterol is not None and hdl_cholesterol < hdl_target

    # Pattern classification (first match wins)
    if ldl_elevated and tg_elevated and hdl_low:
        pattern = "atherogenic_dyslipidemia"
        pattern_desc = (
            "Classic metabolic syndrome lipid triad: elevated TG, low HDL, "
            "borderline-to-elevated LDL. ApoB often elevated even when LDL "
            "appears normal."
        )
    elif ldl_elevated and tg_elevated:
        pattern = "mixed_dyslipidemia"
        pattern_desc = (
            "Elevated LDL combined with elevated triglycerides (>=150 mg/dL). "
            "Higher CV risk than either alone; implies both hepatic overproduction "
            "and impaired triglyceride clearance."
        )
    elif ldl_elevated and not tg_elevated:
        pattern = "isolated_hypercholesterolemia"
        pattern_desc = (
            "Elevated LDL with normal triglycerides. Classic pattern for familial "
            "hypercholesterolemia or dietary hypercholesterolemia."
        )
    elif tg_elevated and not ldl_elevated:
        pattern = "isolated_hypertriglyceridemia"
        pattern_desc = (
            "Elevated triglycerides with normal LDL. Associated with metabolic "
            "syndrome, type 2 diabetes, alcohol, CKD."
        )
    elif hdl_low:
        pattern = "low_hdl_syndrome"
        pattern_desc = (
            "HDL below sex-specific target with otherwise unremarkable panel. "
            "Residual CV risk; associated with metabolic syndrome."
        )
    else:
        pattern = "normal_pattern"
        pattern_desc = "All values within targets for the stated risk tier."

    # Non-HDL vs target
    non_hdl_vs_target = None
    if non_hdl_cholesterol is not None:
        nhdl_target = _NON_HDL_TARGETS.get(patient_risk_tier, 130)
        if non_hdl_cholesterol >= 190:
            nhdl_status = "Very High"
        elif non_hdl_cholesterol >= 160:
            nhdl_status = "High"
        elif non_hdl_cholesterol >= 130:
            nhdl_status = "Borderline High"
        else:
            nhdl_status = "Normal"
        ratio = round(non_hdl_cholesterol / nhdl_target, 2) if nhdl_target > 0 else 0
        non_hdl_vs_target = {
            "value": non_hdl_cholesterol,
            "target_for_risk_tier": nhdl_target,
            "status": f"{nhdl_status} — {ratio}x target for {patient_risk_tier}-risk patients",
        }

    # ApoB / LDL concordance
    apob_ldl_concordance = None
    if apob is not None and ldl_cholesterol is not None:
        apob_target = _APOB_TARGETS.get(patient_risk_tier, 90)
        apob_high = apob > apob_target
        if apob_high and ldl_elevated:
            apob_ldl_concordance = {
                "status": "concordant_elevated",
                "note": (
                    f"Both ApoB ({apob} mg/dL) and LDL ({ldl_cholesterol} mg/dL) "
                    f"are elevated — concordant. Confirms high atherogenic particle "
                    f"burden."
                ),
            }
        elif not apob_high and not ldl_elevated:
            apob_ldl_concordance = {
                "status": "concordant_normal",
                "note": "Both ApoB and LDL within targets — lower atherogenic risk.",
            }
        elif apob_high and not ldl_elevated:
            apob_ldl_concordance = {
                "status": "discordant_apob_high",
                "note": (
                    f"ApoB ({apob} mg/dL) elevated but LDL ({ldl_cholesterol} mg/dL) "
                    f"appears normal. Suggests small dense LDL particles — each "
                    f"particle carries less cholesterol but is more atherogenic. "
                    f"ApoB is the more reliable risk marker here."
                ),
            }
        else:
            apob_ldl_concordance = {
                "status": "discordant_ldl_high",
                "note": (
                    f"LDL ({ldl_cholesterol} mg/dL) elevated but ApoB ({apob} mg/dL) "
                    f"within target. Suggests large buoyant LDL particles — fewer "
                    f"particles carrying more cholesterol per particle; lower "
                    f"atherogenic risk than LDL number implies."
                ),
            }

    # Treatment implications
    implications = []
    if pattern == "mixed_dyslipidemia":
        implications = [
            "Mixed dyslipidemia requires addressing both LDL and triglycerides.",
            "Statin is first-line for LDL reduction; also reduces TG 10-30%.",
            (
                "If TG remain >=150 on statin, consider prescription omega-3 "
                "(icosapentaenoic acid / Vascepa) — REDUCE-IT trial: 25% CV event "
                "reduction vs placebo in patients with TG >=150 on statin."
            ),
            (
                "Non-HDL cholesterol is the preferred treatment target in mixed "
                "dyslipidemia because it captures VLDL in addition to LDL."
            ),
        ]
        if not friedewald_valid:
            implications.append(
                "Direct LDL measurement recommended to confirm LDL given TG >200."
            )
    elif pattern == "isolated_hypercholesterolemia":
        implications = [
            "Consider FH evaluation (DLCN score) if LDL persistently >190 mg/dL.",
            "High-intensity statin first-line; ezetimibe add-on if target not reached.",
        ]
    elif pattern == "isolated_hypertriglyceridemia":
        implications = [
            "Evaluate for secondary causes: diabetes, alcohol, CKD, hypothyroidism.",
            "Lifestyle (weight loss, reduced refined carbs, alcohol reduction) first-line.",
            "If TG >500, fibrate or prescription omega-3 to reduce pancreatitis risk.",
        ]
    elif pattern == "atherogenic_dyslipidemia":
        implications = [
            "Classic metabolic syndrome triad — evaluate for insulin resistance.",
            "ApoB may be more informative than LDL in this pattern.",
            "Statin + lifestyle; consider adding ezetimibe or PCSK9 if needed.",
        ]

    # XAI confidence logic
    apob_ldl_concordance_status = (
        apob_ldl_concordance.get("status", "unknown") if apob_ldl_concordance else "not assessed"
    )
    if not friedewald_valid:
        lipid_conf = "low"
        lipid_conf_note = (
            "Pattern classification is based on a calculated LDL that may be inaccurate "
            f"(triglycerides {triglycerides} mg/dL > 200 mg/dL threshold). "
            "Direct LDL measurement recommended to confirm pattern."
        )
    elif ldl_measured_directly and all([ldl_cholesterol, hdl_cholesterol, triglycerides]):
        lipid_conf = "high"
        lipid_conf_note = "Complete panel with directly measured LDL. Pattern classification is reliable."
    else:
        lipid_conf = "moderate"
        lipid_conf_note = "Calculated LDL within acceptable range, but panel may be incomplete."

    xai = _build_xai_metadata(
        confidence_level=lipid_conf,
        confidence_note=lipid_conf_note,
        key_drivers=[
            f"Triglycerides {triglycerides} mg/dL -- drove pattern classification" if triglycerides else None,
            f"LDL {ldl_cholesterol} mg/dL ({'directly measured' if ldl_measured_directly else 'calculated'})" if ldl_cholesterol else None,
            f"ApoB/LDL concordance: {apob_ldl_concordance_status}" if apob else None,
        ],
        guideline_version="ESC/EAS Dyslipidaemia Guidelines 2023",
        evidence_grade="Expert Consensus",
        counterfactual=(
            f"If triglycerides were <150 mg/dL, pattern would change from '{pattern}' "
            "to 'isolated_hypercholesterolemia' and Friedewald LDL would be reliable."
        ) if triglycerides and triglycerides >= 150 else None,
    )

    return {
        "patient_id": patient_id,
        "pattern": pattern,
        "pattern_description": pattern_desc,
        "friedewald_ldl_valid": friedewald_valid,
        "friedewald_note": friedewald_note,
        "non_hdl_cholesterol": non_hdl_cholesterol,
        "non_hdl_vs_target": non_hdl_vs_target,
        "apob_ldl_concordance": apob_ldl_concordance,
        "treatment_implications": implications,
        "clinical_note": "RESEARCH ONLY — NOT FOR CLINICAL USE",
        "xai_metadata": xai,
        "dry_run": DRY_RUN,
    }


async def _calculate_fh_clinical_score_impl(
    patient_id: str,
    ldl_cholesterol_mgdl: float,
    family_hx_premature_cvd: bool = False,
    family_hx_high_ldl: bool = False,
    family_hx_tendon_xanthomas: bool = False,
    personal_premature_cvd: bool = False,
    personal_cerebrovascular_disease: bool = False,
    tendon_xanthomas: bool = False,
    corneal_arcus_under_45: bool = False,
    genetic_test_performed: bool = False,
    genetic_test_type: Optional[str] = None,
    genetic_test_variants_tested: Optional[str] = None,
    genetic_test_result: Optional[str] = None,
    causative_mutation_identified: bool = False,
) -> Dict[str, Any]:
    """Calculate Dutch Lipid Clinic Network (DLCN) score for FH diagnosis."""
    # Category 1 — Family history (max 2 points, take highest)
    fam_hx_points = 0
    if family_hx_tendon_xanthomas:
        fam_hx_points = 2
    elif family_hx_premature_cvd:
        fam_hx_points = 1
    elif family_hx_high_ldl:
        fam_hx_points = 1

    # Category 2 — Clinical history (max 2 points, take highest)
    clinical_points = 0
    if personal_premature_cvd:
        clinical_points = 2
    elif personal_cerebrovascular_disease:
        clinical_points = 1

    # Category 3 — Physical exam (max 6 points, take highest)
    exam_points = 0
    if tendon_xanthomas:
        exam_points = 6
    elif corneal_arcus_under_45:
        exam_points = 4

    # Category 4 — LDL Cholesterol (max 8 points, take highest)
    ldl_mmol = ldl_cholesterol_mgdl / 38.67
    ldl_points = 0
    if ldl_mmol >= 8.5:       # >=330 mg/dL
        ldl_points = 8
    elif ldl_mmol >= 6.5:     # 250-329 mg/dL
        ldl_points = 5
    elif ldl_mmol >= 5.0:     # 190-249 mg/dL
        ldl_points = 3
    elif ldl_mmol >= 4.0:     # 155-189 mg/dL
        ldl_points = 1

    # Category 5 — DNA analysis (max 8 points)
    dna_points = 8 if causative_mutation_identified else 0

    total = fam_hx_points + clinical_points + exam_points + ldl_points + dna_points

    # Score interpretation
    if total >= 9:
        tier = "Definite FH"
        tier_note = (
            "Score >=9. Strong clinical evidence for FH. Cascade screening "
            "of first-degree relatives is indicated."
        )
    elif total >= 6:
        tier = "Probable FH"
        tier_note = (
            "Score 6-8. Probable FH. Full diagnostic genetic panel recommended "
            "if not already done."
        )
    elif total >= 3:
        tier = "Possible FH"
        tier_note = (
            "Score 3-5. Possible FH. Clinical treatment should proceed regardless "
            "of genetic result. Full diagnostic panel may be warranted."
        )
    else:
        tier = "Unlikely FH"
        tier_note = (
            "Score <3. FH unlikely on clinical criteria, though other causes of "
            "elevated LDL should still be evaluated."
        )

    # Genetic test interpretation
    genetic_interpretation = None
    if genetic_test_performed and genetic_test_result == "negative":
        if genetic_test_type == "population_screening":
            genetic_interpretation = {
                "result": "NEGATIVE SCREENING — does NOT rule out FH",
                "warning": (
                    "A negative population screening result does NOT reduce the DLCN "
                    "score and does NOT rule out Familial Hypercholesterolemia. "
                    "Population screening tests check a small, predefined subset of "
                    "variants. For example, the Helix Molecular Screen checks only 2 "
                    "APOB variants (c.10580G>A and c.10579C>T) and misses the vast "
                    "majority of pathogenic LDLR and APOB variants. The DLCN score is "
                    "a clinical diagnosis — it does not require genetic confirmation. "
                    "A Probable or Possible FH score warrants a FULL DIAGNOSTIC panel "
                    "(comprehensive LDLR sequencing + large rearrangement analysis + "
                    "full APOB + PCSK9) regardless of screening result."
                ),
                "action": (
                    "Full diagnostic FH panel recommended"
                    if total >= 3
                    else "Discuss with clinician"
                ),
            }
        elif genetic_test_type in ("diagnostic", "panel"):
            genetic_interpretation = {
                "result": "NEGATIVE DIAGNOSTIC PANEL",
                "note": (
                    "A negative full diagnostic panel reduces but does not eliminate "
                    "the probability of monogenic FH — approximately 20-40% of "
                    "clinically definite FH cases have no identifiable variant with "
                    "current panels (polygenic or unknown variants). Clinical DLCN "
                    "score remains valid. Treatment decisions should be based on the "
                    "clinical score and LDL level, not solely on genetic result."
                ),
            }

    if causative_mutation_identified:
        genetic_interpretation = {
            "result": "CAUSATIVE MUTATION IDENTIFIED",
            "note": (
                "Genetic diagnosis confirmed. DLCN score elevated by 8 points "
                "(DNA category). Cascade family screening indicated."
            ),
        }

    # PCSK9 inhibitor eligibility note
    pcsk9_note = None
    if total >= 3:
        pcsk9_note = (
            "Patients with Possible, Probable, or Definite FH (DLCN >=3) may "
            "qualify for PCSK9 inhibitor (evolocumab/Repatha or alirocumab/Praluent) "
            "insurance coverage on clinical grounds, even without genetic "
            "confirmation. Eligibility typically also requires documented statin "
            "intolerance or failure to reach LDL target on maximally tolerated "
            "statin + ezetimibe. Some payers require an FH diagnosis code "
            "(ICD-10: E78.01) — clinical DLCN score >=3 supports this code. "
            "Confirm with cardiologist and insurer."
        )

    # XAI confidence logic
    assessed_categories = sum([
        1 if (family_hx_premature_cvd or family_hx_high_ldl or family_hx_tendon_xanthomas) else 0,
        1 if (personal_premature_cvd or personal_cerebrovascular_disease) else 0,
        1 if (tendon_xanthomas or corneal_arcus_under_45) else 0,
        1,  # LDL always assessed
        1 if genetic_test_performed else 0,
    ])

    if assessed_categories >= 4 and genetic_test_performed:
        fh_conf = "high"
        fh_conf_note = "All or nearly all DLCN categories assessed including genetic test result."
    elif assessed_categories >= 3:
        fh_conf = "moderate"
        fh_conf_note = (
            f"{assessed_categories} of 5 DLCN categories assessed. "
            "Physical exam findings and/or genetic test may be missing -- score may be underestimated."
        )
    else:
        fh_conf = "low"
        fh_conf_note = (
            "Only LDL and limited history available. Physical exam (xanthomas, corneal arcus) "
            "and genetic test not provided -- DLCN score is a floor estimate only."
        )

    top_drivers = sorted([
        (ldl_points, f"LDL {ldl_cholesterol_mgdl} mg/dL (+{ldl_points} DLCN pts)"),
        (fam_hx_points, f"Family history (+{fam_hx_points} DLCN pts)"),
        (clinical_points, f"Clinical CVD history (+{clinical_points} DLCN pts)"),
        (exam_points, f"Physical exam (+{exam_points} DLCN pts)"),
        (dna_points, f"DNA/genetic result (+{dna_points} DLCN pts)"),
    ], reverse=True)
    top_3_drivers = [d[1] for d in top_drivers if d[0] > 0][:3]

    xai = _build_xai_metadata(
        confidence_level=fh_conf,
        confidence_note=fh_conf_note,
        key_drivers=top_3_drivers if top_3_drivers else [f"LDL {ldl_cholesterol_mgdl} mg/dL (only input provided)"],
        guideline_version="EAS Familial Hypercholesterolaemia Guidelines 2023; ACC/AHA Cholesterol 2018",
        evidence_grade="Class I (ESC/EAS)" if total >= 6 else "Expert Consensus",
        counterfactual=(
            f"If LDL were <155 mg/dL (0 LDL points), score would be {total - ldl_points} "
            f"({'Unlikely FH' if (total - ldl_points) < 3 else 'Possible FH'})."
        ),
    )

    return {
        "patient_id": patient_id,
        "dlcn_score": total,
        "dlcn_tier": tier,
        "tier_note": tier_note,
        "score_components": {
            "family_history": fam_hx_points,
            "clinical_history": clinical_points,
            "physical_exam": exam_points,
            "ldl_cholesterol": ldl_points,
            "ldl_mmol": round(ldl_mmol, 2),
            "dna_analysis": dna_points,
        },
        "genetic_test_interpretation": genetic_interpretation,
        "pcsk9_inhibitor_eligibility_note": pcsk9_note,
        "diagnostic_panel_recommended": (total >= 3 and not causative_mutation_identified),
        "cascade_screening_recommended": (total >= 6 or causative_mutation_identified),
        "guideline_references": [
            "EAS FH Guidelines 2023 — https://doi.org/10.1093/eurheartj/ehab099",
            "ACC/AHA 2018 Cholesterol Guideline — https://doi.org/10.1016/j.jacc.2018.11.003",
            (
                "DLCN Score — Familial Hypercholesterolaemia: summary of guidance — "
                "https://www.nice.org.uk/guidance/cg71"
            ),
        ],
        "clinical_note": (
            "RESEARCH ONLY — NOT FOR CLINICAL USE. DLCN score is a clinical "
            "research tool — requires clinician review before any diagnostic or "
            "treatment decision."
        ),
        "xai_metadata": xai,
        "dry_run": DRY_RUN,
    }


# ---------------------------------------------------------------------------
# Phase B tool implementations
# ---------------------------------------------------------------------------

# eGFR stage classification (KDIGO 2024)
def _classify_egfr_stage(egfr: float) -> tuple:
    if egfr >= 90:
        return "G1", "Normal or high"
    if egfr >= 60:
        return "G2", "Mildly decreased"
    if egfr >= 45:
        return "G3a", "Mildly to moderately decreased"
    if egfr >= 30:
        return "G3b", "Moderately to severely decreased"
    if egfr >= 15:
        return "G4", "Severely decreased"
    return "G5", "Kidney failure"


# Single-kidney status upgrade map
_SINGLE_KIDNEY_UPGRADE = {
    "safe": "safe_with_monitoring",
    "safe_with_preference": "safe_with_monitoring",
    "acceptable": "use_with_caution",
    "use_with_caution": "use_with_caution",
    "dose_reduce": "dose_reduce_and_monitor_closely",
    "avoid": "avoid",
    "contraindicated": "contraindicated",
}

_SINGLE_KIDNEY_NOTE = (
    "This patient has one functioning kidney (eGFR on a single kidney is more "
    "precarious than the same eGFR on two — there is no functional reserve). "
    "All renally-cleared drugs carry amplified risk. Any further eGFR decline "
    "has no compensatory mechanism."
)


def _assess_statin_drugs(egfr: float) -> dict:
    """Assess individual statins by eGFR."""
    drugs = {}

    # Atorvastatin — >98% hepatic, safe at any eGFR
    drugs["atorvastatin"] = {
        "status": "safe", "renal_clearance": "<2%",
        "note": "First choice in CKD — >98% hepatic metabolism, no renal adjustment at any eGFR",
    }

    # Rosuvastatin — ~10% renal
    if egfr >= 60:
        drugs["rosuvastatin"] = {"status": "safe", "renal_clearance": "~10%", "note": "Standard dose"}
    elif egfr >= 30:
        drugs["rosuvastatin"] = {"status": "dose_reduce", "renal_clearance": "~10%", "note": "Lower dose preferred"}
    elif egfr >= 15:
        drugs["rosuvastatin"] = {"status": "dose_reduce", "renal_clearance": "~10%", "note": "Max 10mg"}
    else:
        drugs["rosuvastatin"] = {"status": "avoid", "renal_clearance": "~10%", "note": "Avoid at eGFR <15"}

    # Pravastatin
    if egfr >= 60:
        drugs["pravastatin"] = {"status": "safe", "renal_clearance": "~20%", "note": "Standard dose"}
    elif egfr >= 30:
        drugs["pravastatin"] = {"status": "use_with_caution", "renal_clearance": "~20%", "note": "Monitor"}
    elif egfr >= 15:
        drugs["pravastatin"] = {"status": "dose_reduce", "renal_clearance": "~20%", "note": "Reduce dose"}
    else:
        drugs["pravastatin"] = {"status": "avoid", "renal_clearance": "~20%", "note": "Avoid at eGFR <15"}

    # Simvastatin
    if egfr >= 60:
        drugs["simvastatin"] = {"status": "safe", "renal_clearance": "~13%", "note": "Standard dose"}
    elif egfr >= 30:
        drugs["simvastatin"] = {"status": "use_with_caution", "renal_clearance": "~13%", "note": "Monitor"}
    elif egfr >= 15:
        drugs["simvastatin"] = {"status": "dose_reduce", "renal_clearance": "~13%", "note": "Max 10mg"}
    else:
        drugs["simvastatin"] = {"status": "avoid", "renal_clearance": "~13%", "note": "Avoid at eGFR <15"}

    # Pitavastatin
    if egfr >= 15:
        drugs["pitavastatin"] = {"status": "safe", "renal_clearance": "<2%", "note": "Safe; minimal renal clearance"}
    else:
        drugs["pitavastatin"] = {"status": "use_with_caution", "renal_clearance": "<2%", "note": "Monitor at eGFR <15"}

    # Fluvastatin
    if egfr >= 30:
        drugs["fluvastatin"] = {"status": "safe", "renal_clearance": "~6%", "note": "Safe"}
    elif egfr >= 15:
        drugs["fluvastatin"] = {"status": "use_with_caution", "renal_clearance": "~6%", "note": "Monitor"}
    else:
        drugs["fluvastatin"] = {"status": "avoid", "renal_clearance": "~6%", "note": "Avoid at eGFR <15"}

    return {
        "class_status": "safe_with_preference",
        "preferred": ["atorvastatin — >98% hepatic, no renal adjustment at any eGFR"],
        "drugs": drugs,
        "note": (
            "Atorvastatin is the statin of choice in CKD and single-kidney patients "
            "due to >98% hepatic metabolism — renal function does not affect its "
            "clearance or accumulation."
        ),
    }


def _assess_anticoagulant_drugs(egfr: float) -> dict:
    """Assess anticoagulants by eGFR."""
    drugs = {}

    # Apixaban — ~27% renal
    if egfr >= 50:
        drugs["apixaban"] = {"status": "safe", "renal_clearance": "~27%", "note": "Standard dose; PREFERRED DOAC in CKD"}
    elif egfr >= 30:
        drugs["apixaban"] = {"status": "dose_reduce", "renal_clearance": "~27%", "note": "Dose-reduce or monitor"}
    elif egfr >= 15:
        drugs["apixaban"] = {"status": "use_with_caution", "renal_clearance": "~27%", "note": "Use with caution"}
    else:
        drugs["apixaban"] = {"status": "avoid", "renal_clearance": "~27%", "note": "Avoid at eGFR <15"}

    # Rivaroxaban — ~33% renal
    if egfr >= 50:
        drugs["rivaroxaban"] = {"status": "safe", "renal_clearance": "~33%", "note": "Standard dose"}
    elif egfr >= 30:
        drugs["rivaroxaban"] = {"status": "dose_reduce", "renal_clearance": "~33%", "note": "Dose-reduce"}
    else:
        drugs["rivaroxaban"] = {"status": "avoid", "renal_clearance": "~33%", "note": "Avoid at eGFR <30"}

    # Edoxaban — ~50% renal
    if egfr >= 50:
        drugs["edoxaban"] = {"status": "safe", "renal_clearance": "~50%", "note": "Standard dose"}
    elif egfr >= 30:
        drugs["edoxaban"] = {"status": "dose_reduce", "renal_clearance": "~50%", "note": "Dose-reduce"}
    else:
        drugs["edoxaban"] = {"status": "avoid", "renal_clearance": "~50%", "note": "Avoid at eGFR <30"}

    # Dabigatran — ~80% renal
    if egfr >= 50:
        drugs["dabigatran"] = {"status": "use_with_caution", "renal_clearance": "~80%", "note": "Use with caution; ~80% renal"}
    elif egfr >= 30:
        drugs["dabigatran"] = {"status": "avoid", "renal_clearance": "~80%", "note": "Avoid if possible"}
    else:
        drugs["dabigatran"] = {"status": "contraindicated", "renal_clearance": "~80%", "note": "CONTRAINDICATED"}

    # Warfarin — no renal clearance
    if egfr >= 15:
        drugs["warfarin"] = {"status": "safe", "renal_clearance": "0%", "note": "No renal clearance; requires INR monitoring"}
    else:
        drugs["warfarin"] = {"status": "safe", "renal_clearance": "0%", "note": "Safe with dialysis adjustment; requires INR monitoring"}

    return {
        "class_status": "safe_with_preference",
        "preferred": ["apixaban (Eliquis) — ~27% renal, lowest renal clearance of DOACs"],
        "acceptable": ["warfarin — no renal clearance; requires INR monitoring"],
        "avoid": ["dabigatran — ~80% renal; avoid in CKD"],
        "drugs": drugs,
        "note": "Apixaban is the preferred DOAC in CKD due to lowest renal clearance (~27%).",
    }


def _assess_ace_arb(egfr: float, single_kidney: bool) -> dict:
    """Assess ACE inhibitors and ARBs by eGFR."""
    if egfr >= 60:
        status = "safe"
        note = "Safe; renoprotective in proteinuric CKD"
    elif egfr >= 30:
        status = "use_with_caution"
        note = "Monitor eGFR + K+; up to 20% eGFR decline on initiation acceptable"
    elif egfr >= 15:
        status = "use_with_caution"
        note = "Use with specialist guidance"
    else:
        status = "avoid"
        note = "Generally avoid at eGFR <15"

    result = {
        "class_status": status,
        "note": note,
    }

    if single_kidney:
        result["single_kidney_ace_arb_note"] = (
            "In single-kidney patients, ACE inhibitors and ARBs can be used (they are "
            "often renoprotective) but eGFR and potassium must be monitored closely at "
            "initiation and dose changes. A >30% acute eGFR decline on initiation "
            "should prompt evaluation for renal artery stenosis."
        )

    return result


def _assess_metformin(egfr: float) -> dict:
    """Assess metformin by eGFR."""
    if egfr >= 60:
        return {"class_status": "safe", "note": "Safe at standard dose (500-2000 mg/day)"}
    if egfr >= 45:
        return {"class_status": "safe", "note": "Continue with monitoring; consider reducing dose if approaching 45"}
    if egfr >= 30:
        return {"class_status": "dose_reduce", "note": "Reduce dose to maximum 500-1000 mg/day"}
    return {"class_status": "contraindicated", "note": "CONTRAINDICATED — lactic acidosis risk"}


def _assess_fibrates(egfr: float) -> dict:
    """Assess fibrates by eGFR."""
    drugs = {}
    if egfr >= 60:
        drugs["fenofibrate"] = {
            "status": "safe",
            "note": (
                "Safe; monitor creatinine (fenofibrate increases serum creatinine ~10% "
                "via tubular secretion — not true renal damage but confounds monitoring)"
            ),
        }
    elif egfr >= 30:
        drugs["fenofibrate"] = {"status": "dose_reduce", "note": "Dose-reduce; avoid if eGFR declining"}
    else:
        drugs["fenofibrate"] = {"status": "contraindicated", "note": "CONTRAINDICATED at eGFR <30"}

    drugs["gemfibrozil"] = {
        "status": "avoid",
        "note": (
            "Avoid with statins (significant rhabdomyolysis/myopathy risk with any statin). "
            "Consider prescription omega-3 (Vascepa) as alternative for triglyceride reduction."
        ),
    }

    overall = "avoid" if egfr < 30 else ("dose_reduce" if egfr < 60 else "use_with_caution")
    return {
        "class_status": overall,
        "drugs": drugs,
        "note": (
            "For patients requiring both fibrate and statin therapy, fenofibrate "
            "(not gemfibrozil) is the only acceptable combination."
        ),
    }


def _assess_nsaids(egfr: float, single_kidney: bool) -> dict:
    """Assess NSAIDs by eGFR and kidney count."""
    if single_kidney:
        return {
            "class_status": "contraindicated",
            "note": "CONTRAINDICATED — reduce blood flow to only functioning kidney",
        }
    if egfr >= 60:
        return {
            "class_status": "use_with_caution",
            "note": "Short-term use acceptable with caution",
        }
    return {
        "class_status": "avoid",
        "note": "AVOID — reduce renal blood flow, worsen CKD",
    }


def _assess_contrast_iodinated(egfr: float, single_kidney: bool) -> dict:
    """Assess iodinated contrast by eGFR."""
    if egfr >= 60:
        status = "safe"
        note = "Generally safe with adequate hydration"
    elif egfr >= 30:
        status = "use_with_caution"
        note = "Pre-hydration required; hold metformin 48h before/after; monitor eGFR post-procedure"
    else:
        status = "avoid"
        note = "High risk — weigh benefit vs. risk with nephrology"

    result = {"class_status": status, "note": note}
    if single_kidney:
        result["single_kidney_contrast_note"] = (
            "Even at eGFR 68, iodinated contrast carries heightened risk in "
            "single-kidney patients due to absence of functional reserve. Ensure "
            "pre-hydration, post-procedure eGFR monitoring, and consider "
            "non-contrast alternatives where available."
        )
    return result


def _assess_contrast_gadolinium(egfr: float, single_kidney: bool) -> dict:
    """Assess gadolinium contrast by eGFR."""
    if egfr >= 30:
        result = {
            "class_status": "safe",
            "note": "Macrocyclic agents (gadobutrol, gadoteridol, gadoterate) are safe",
            "linear_agents_note": "Avoid linear agents (gadodiamide, gadopentetate)",
        }
    else:
        result = {
            "class_status": "use_with_caution",
            "note": (
                "Macrocyclic agents preferred if contrast required. "
                "Linear agents CONTRAINDICATED — nephrogenic systemic fibrosis risk."
            ),
        }
    if single_kidney:
        result["single_kidney_note"] = "Note single kidney status in radiology referral."
    return result


async def _assess_renal_drug_constraints_impl(
    patient_id: str,
    egfr: float,
    functional_kidney_count: int = 2,
    drug_classes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Assess cardiovascular drug safety based on eGFR and kidney count."""
    stage, stage_desc = _classify_egfr_stage(egfr)
    single_kidney = functional_kidney_count == 1

    # All assessable drug classes
    all_classes = {
        "statins": lambda: _assess_statin_drugs(egfr),
        "anticoagulants": lambda: _assess_anticoagulant_drugs(egfr),
        "ace_inhibitors": lambda: _assess_ace_arb(egfr, single_kidney),
        "arbs": lambda: _assess_ace_arb(egfr, single_kidney),
        "metformin": lambda: _assess_metformin(egfr),
        "fibrates": lambda: _assess_fibrates(egfr),
        "pcsk9_inhibitors": lambda: {
            "class_status": "safe",
            "note": "Monoclonal antibodies — no renal clearance. Safe at all eGFR levels including dialysis. No dose adjustment required.",
        },
        "ezetimibe": lambda: {
            "class_status": "safe",
            "note": "No renal clearance. Safe at all eGFR levels. No dose adjustment required.",
        },
        "omega3": lambda: {
            "class_status": "safe",
            "note": "No renal clearance. Safe at all eGFR levels. No dose adjustment required.",
        },
        "glp1_agonists": lambda: {
            "class_status": "safe" if egfr >= 15 else "use_with_caution",
            "note": (
                "Generally safe; no dose adjustment required"
                if egfr >= 15
                else "Limited data at eGFR <15; use with caution"
            ),
            "hydration_note": (
                "GLP-1 agonists can cause nausea and vomiting → dehydration risk → "
                "transient eGFR decline. Patients with single kidney or borderline "
                "eGFR should monitor hydration carefully, especially at initiation."
            ) if single_kidney else None,
        },
        "nsaids": lambda: _assess_nsaids(egfr, single_kidney),
        "contrast_iodinated": lambda: _assess_contrast_iodinated(egfr, single_kidney),
        "contrast_gadolinium": lambda: _assess_contrast_gadolinium(egfr, single_kidney),
    }

    # Filter to requested classes if specified
    if drug_classes:
        requested = {c.strip().lower().replace(" ", "_").replace("-", "_") for c in drug_classes}
    else:
        requested = set(all_classes.keys())

    assessments = {}
    for cls_name, assess_fn in all_classes.items():
        if cls_name not in requested:
            continue
        assessment = assess_fn()

        # Apply single-kidney modifier
        if single_kidney and "class_status" in assessment:
            original = assessment["class_status"]
            assessment["class_status"] = _SINGLE_KIDNEY_UPGRADE.get(original, original)

        assessments[cls_name] = assessment

    # Top-line recommendations
    top_line = [
        "Preferred statin: atorvastatin (hepatic only, safe at any eGFR)",
        "Preferred anticoagulant if indicated: apixaban (lowest renal DOAC)",
        "Avoid: dabigatran, gemfibrozil, NSAIDs" + (" (single kidney)" if single_kidney else " (eGFR <60)") + ", iodinated contrast without pre-hydration protocol",
        "Safe without dose adjustment: ezetimibe, PCSK9 inhibitors, prescription omega-3",
    ]
    if egfr >= 45:
        top_line.append(f"Metformin safe at eGFR {egfr} — monitor if eGFR approaches 45")
    elif egfr >= 30:
        top_line.append(f"Metformin requires dose reduction at eGFR {egfr}")

    # XAI confidence logic
    if single_kidney:
        renal_conf = "moderate"
        renal_conf_note = (
            "eGFR-based thresholds are from FDA prescribing information and KDIGO guidelines "
            "(high evidence). The single-kidney risk modifier is a clinical extrapolation -- "
            "patients with one functioning kidney are underrepresented in drug safety trials."
        )
    else:
        renal_conf = "high"
        renal_conf_note = (
            "Drug thresholds derived directly from FDA prescribing information "
            "and KDIGO 2024 CKD guidelines."
        )

    xai = _build_xai_metadata(
        confidence_level=renal_conf,
        confidence_note=renal_conf_note,
        key_drivers=[
            f"eGFR {egfr} mL/min/1.73m2 (Stage {stage})",
            f"Functional kidney count: {functional_kidney_count}",
        ],
        guideline_version="KDIGO 2024 CKD Guidelines; FDA Prescribing Information",
        evidence_grade="Class I (AHA/ACC)" if not single_kidney else "Expert Consensus",
        counterfactual=(
            f"If eGFR recovers to >90 mL/min/1.73m2, all drugs currently flagged "
            "'use with monitoring' would return to fully acceptable status."
        ) if egfr < 90 else None,
    )

    result = {
        "patient_id": patient_id,
        "egfr": egfr,
        "egfr_stage": stage,
        "egfr_stage_description": stage_desc,
        "functional_kidney_count": functional_kidney_count,
        "single_kidney_modifier_applied": single_kidney,
        "assessments": assessments,
        "top_line_recommendations": top_line,
        "clinical_note": (
            "RESEARCH ONLY — NOT FOR CLINICAL USE. Drug selection requires "
            "clinician review of full medication list, allergies, and individual "
            "risk/benefit assessment."
        ),
        "xai_metadata": xai,
        "dry_run": DRY_RUN,
    }

    if single_kidney:
        result["single_kidney_note"] = _SINGLE_KIDNEY_NOTE

    return result


# Lipid treatment target tables (2022 ACC + 2023 ESC)
_LIPID_TARGETS = {
    "very_high": {
        "ldl": 55, "apob": 65, "non_hdl": 85,
        "tier_criteria": (
            "Very high risk: established ASCVD, OR Definite/Probable FH + CVD, "
            "OR 10-year CVD risk >20%, OR LDL >190 mg/dL with multiple risk factors"
        ),
    },
    "high": {
        "ldl": 70, "apob": 80, "non_hdl": 100,
        "tier_criteria": (
            "High risk: 10-year CVD risk 7.5-20%, OR Possible FH (DLCN 3-5), "
            "OR diabetes with risk factors, OR CKD G3-G4"
        ),
    },
    "intermediate": {
        "ldl": 100, "apob": 90, "non_hdl": 130,
        "tier_criteria": "Intermediate risk: 10-year CVD risk 5-7.5%",
    },
    "low": {
        "ldl": 130, "apob": 100, "non_hdl": 160,
        "tier_criteria": "Low risk: 10-year CVD risk <5%",
    },
}

# Expected LDL reduction by therapy (from landmark trials)
_THERAPY_REDUCTIONS = {
    "high_intensity_statin": 0.50,
    "moderate_intensity_statin": 0.35,
    "low_intensity_statin": 0.25,
    "ezetimibe": 0.20,
    "pcsk9_inhibitor": 0.60,
}

_TIER_ORDER = ["low", "intermediate", "high", "very_high"]


def _model_therapy_pathway(
    starting_ldl: float,
    ldl_target: float,
    already_on_statin: bool,
    statin_intensity: Optional[str],
    already_on_ezetimibe: bool,
    already_on_pcsk9: bool,
    renal_constraint: bool,
) -> tuple:
    """Model stepwise lipid-lowering therapy to reach target."""
    steps = []
    current = starting_ldl

    if not already_on_statin:
        intensity = "high_intensity_statin"
        label = (
            "atorvastatin 40-80mg"
            if renal_constraint
            else "atorvastatin 40-80mg or rosuvastatin 20-40mg"
        )
        reduction = _THERAPY_REDUCTIONS[intensity]
        projected = round(current * (1 - reduction), 1)
        steps.append({
            "step": 1,
            "add": f"High-intensity statin ({label})",
            "expected_ldl": projected,
            "ldl_reduction_pct": round(reduction * 100),
            "target_reached": projected <= ldl_target,
        })
        current = projected
    else:
        if statin_intensity in ("low", "moderate"):
            current_reduction = _THERAPY_REDUCTIONS.get(
                f"{statin_intensity}_intensity_statin", 0.30
            )
            additional_reduction = _THERAPY_REDUCTIONS["high_intensity_statin"] - current_reduction
            projected = round(current * (1 - additional_reduction), 1)
            steps.append({
                "step": 1,
                "add": "Intensify to high-intensity statin",
                "expected_ldl": projected,
                "target_reached": projected <= ldl_target,
            })
            current = projected

    if current > ldl_target and not already_on_ezetimibe:
        reduction = _THERAPY_REDUCTIONS["ezetimibe"]
        projected = round(current * (1 - reduction), 1)
        steps.append({
            "step": len(steps) + 1,
            "add": "Add ezetimibe 10mg",
            "expected_ldl": projected,
            "ldl_reduction_pct": round(reduction * 100),
            "target_reached": projected <= ldl_target,
        })
        current = projected

    if current > ldl_target and not already_on_pcsk9:
        reduction = _THERAPY_REDUCTIONS["pcsk9_inhibitor"]
        projected = round(current * (1 - reduction), 1)
        steps.append({
            "step": len(steps) + 1,
            "add": "Add PCSK9 inhibitor (evolocumab/Repatha or alirocumab/Praluent)",
            "expected_ldl": projected,
            "ldl_reduction_pct": round(reduction * 100),
            "target_reached": projected <= ldl_target,
            "renal_note": (
                "PCSK9 inhibitors are safe at any eGFR — monoclonal antibodies "
                "with no renal clearance."
            ),
        })
        current = projected

    return steps, current


async def _calculate_lipid_treatment_targets_impl(
    patient_id: str,
    current_ldl: float,
    current_apob: Optional[float] = None,
    current_non_hdl: Optional[float] = None,
    current_triglycerides: Optional[float] = None,
    risk_tier: str = "high",
    fh_status: str = "possible",
    currently_on_statin: bool = False,
    current_statin_intensity: Optional[str] = None,
    currently_on_ezetimibe: bool = False,
    currently_on_pcsk9_inhibitor: bool = False,
    renal_constraint: bool = False,
) -> Dict[str, Any]:
    """Calculate lipid treatment targets and model therapy pathway."""
    # FH risk upgrade — definite, probable, or possible FH warrants tier upgrade
    fh_upgrade = False
    effective_tier = risk_tier
    if fh_status in ("definite", "probable", "possible"):
        idx = _TIER_ORDER.index(risk_tier) if risk_tier in _TIER_ORDER else 1
        new_idx = min(idx + 1, len(_TIER_ORDER) - 1)
        if new_idx != idx:
            effective_tier = _TIER_ORDER[new_idx]
            fh_upgrade = True

    targets = _LIPID_TARGETS.get(effective_tier, _LIPID_TARGETS["high"])
    ldl_target = targets["ldl"]
    apob_target = targets["apob"]
    non_hdl_target = targets["non_hdl"]

    # Current vs target gaps
    ldl_gap = round(current_ldl - ldl_target, 1)
    ldl_reduction_pct = round((current_ldl - ldl_target) / current_ldl * 100, 1) if current_ldl > 0 else 0

    apob_gap = round(current_apob - apob_target, 1) if current_apob is not None else None
    non_hdl_gap = round(current_non_hdl - non_hdl_target, 1) if current_non_hdl is not None else None

    # Model therapy pathway
    pathway, final_ldl = _model_therapy_pathway(
        starting_ldl=current_ldl,
        ldl_target=ldl_target,
        already_on_statin=currently_on_statin,
        statin_intensity=current_statin_intensity,
        already_on_ezetimibe=currently_on_ezetimibe,
        already_on_pcsk9=currently_on_pcsk9_inhibitor,
        renal_constraint=renal_constraint,
    )

    # Minimum steps to target
    min_steps = None
    for step in pathway:
        if step["target_reached"]:
            min_steps = step["step"]
            break
    if min_steps is None and pathway:
        min_steps = len(pathway)

    statin_note = None
    if renal_constraint:
        statin_note = (
            "Atorvastatin preferred due to renal constraint (>98% hepatic "
            "metabolism, safe at any eGFR)."
        )

    xai = _build_xai_metadata(
        confidence_level="moderate",
        confidence_note=(
            "LDL target thresholds are from ACC/AHA Class I guidelines (high evidence). "
            "Projected LDL reductions at each therapy step are population averages from "
            "landmark RCTs (FOURIER, ODYSSEY-OUTCOMES, IMPROVE-IT, 4S). Individual "
            "response varies +/-15-20%. Actual LDL on therapy requires measurement."
        ),
        key_drivers=[
            f"Starting LDL: {current_ldl} mg/dL",
            f"Effective risk tier: {effective_tier} (LDL target: {ldl_target} mg/dL)",
            f"FH status: {fh_status}" + (" -- risk tier upgraded" if fh_upgrade else ""),
        ],
        guideline_version="ACC Expert Consensus 2022; ESC Dyslipidaemias 2023",
        evidence_grade="Class I (AHA/ACC)",
        counterfactual=(
            f"If starting LDL were already at {ldl_target} mg/dL (target), "
            "no additional lipid-lowering therapy would be required for LDL alone."
        ),
    )

    return {
        "patient_id": patient_id,
        "current_ldl": current_ldl,
        "current_apob": current_apob,
        "current_non_hdl": current_non_hdl,
        "current_triglycerides": current_triglycerides,
        "risk_tier_input": risk_tier,
        "fh_status": fh_status,
        "fh_risk_upgrade_applied": fh_upgrade,
        "effective_risk_tier": effective_tier,
        "targets": {
            "ldl": ldl_target,
            "apob": apob_target,
            "non_hdl": non_hdl_target,
            "tier_criteria": targets["tier_criteria"],
        },
        "current_vs_target": {
            "ldl_gap": ldl_gap,
            "ldl_reduction_needed_pct": ldl_reduction_pct,
            "apob_gap": apob_gap,
            "non_hdl_gap": non_hdl_gap,
        },
        "therapy_pathway": pathway,
        "minimum_steps_to_target": min_steps,
        "statin_preference_note": statin_note,
        "guideline_references": [
            "2022 ACC Expert Consensus Decision Pathway on Statin Therapy — https://doi.org/10.1016/j.jacc.2022.07.006",
            "2023 ESC Guidelines on Dyslipidaemias — https://doi.org/10.1093/eurheartj/ehac468",
            "FOURIER trial (evolocumab) — https://doi.org/10.1056/NEJMoa1615664",
            "IMPROVE-IT trial (ezetimibe) — https://doi.org/10.1056/NEJMoa1410489",
        ],
        "clinical_note": (
            "RESEARCH ONLY — NOT FOR CLINICAL USE. LDL reduction estimates are "
            "population averages from clinical trials. Individual response varies. "
            "Drug selection requires clinician assessment."
        ),
        "xai_metadata": xai,
        "dry_run": DRY_RUN,
    }


# Post-COVID CV risk tier adjustment tables
_SEVERITY_UPGRADE = {
    "mild": 0,
    "moderate": 1,
    "severe": 1,
    "hospitalized": 1,
    "icu": 2,
}

_COMPLICATION_UPGRADES = {
    "myocarditis_documented": 1,
    "bp_crisis_during_covid": 0,
    "new_prediabetes_post_covid": 0,
    "new_arrhythmia_during_covid": 1,
}


async def _assess_postcovid_cv_risk_impl(
    patient_id: str,
    severity: str,
    year_of_infection: Optional[int] = None,
    myocarditis_documented: bool = False,
    bp_crisis_during_covid: bool = False,
    new_prediabetes_post_covid: bool = False,
    new_arrhythmia_during_covid: bool = False,
    adverse_pregnancy_outcome_history: bool = False,
    baseline_risk_tier: str = "intermediate",
) -> Dict[str, Any]:
    """Assess post-COVID cardiovascular risk with tier adjustment."""
    # Risk tier adjustment
    base_idx = _TIER_ORDER.index(baseline_risk_tier) if baseline_risk_tier in _TIER_ORDER else 1
    upgrade = _SEVERITY_UPGRADE.get(severity, 0)

    complication_flags = {
        "myocarditis_documented": myocarditis_documented,
        "bp_crisis_during_covid": bp_crisis_during_covid,
        "new_prediabetes_post_covid": new_prediabetes_post_covid,
        "new_arrhythmia_during_covid": new_arrhythmia_during_covid,
    }
    upgrade += sum(
        _COMPLICATION_UPGRADES[k] for k, v in complication_flags.items() if v
    )

    adjusted_idx = min(base_idx + upgrade, len(_TIER_ORDER) - 1)
    adjusted_tier = _TIER_ORDER[adjusted_idx]

    # Mechanism flags
    mechanisms = [
        {
            "mechanism": "ACE2-mediated endothelial injury",
            "present": severity in ("moderate", "severe", "hospitalized", "icu"),
            "explanation": (
                "SARS-CoV-2 binds and downregulates ACE2 receptors on vascular endothelium, "
                "causing angiotensin II accumulation → acute vasoconstriction, oxidative stress, "
                "and pro-inflammatory endothelial activation. This accelerates atherosclerosis "
                "independently of traditional risk factors. Effect persists years after acute illness."
            ),
        },
        {
            "mechanism": "RAAS disruption / hypertensive crisis",
            "present": bp_crisis_during_covid,
            "explanation": (
                "ACE2 downregulation → angiotensin II excess → acute hypertensive crisis. "
                "Compounded by any pre-existing renovascular disease (e.g., renal artery stenosis). "
                "Evaluate for structural renal causes that may have been unmasked by COVID-19."
            ),
        },
        {
            "mechanism": "COVID-associated myocarditis",
            "present": myocarditis_documented or severity in ("severe", "hospitalized", "icu"),
            "explanation": (
                "Direct viral invasion of cardiomyocytes via ACE2. Can leave ventricular and atrial "
                "fibrosis detectable on cardiac MRI (late gadolinium enhancement) years after acute illness. "
                "Associated with arrhythmia, reduced ejection fraction, and exercise intolerance."
            ),
        },
        {
            "mechanism": "Post-COVID beta cell damage / prediabetes",
            "present": new_prediabetes_post_covid,
            "explanation": (
                "COVID-19 directly infects pancreatic beta cells via ACE2, reducing insulin secretion. "
                "New-onset prediabetes or diabetes emerging after COVID may reflect this mechanism "
                "rather than purely lifestyle-driven insulin resistance. Fasting insulin and C-peptide "
                "can help distinguish post-COVID beta cell damage from insulin resistance."
            ),
        },
        {
            "mechanism": "Post-COVID dyslipidemia",
            "present": severity in ("severe", "hospitalized", "icu"),
            "explanation": (
                "COVID-19 hepatic inflammation impairs LDL receptor expression and VLDL clearance, "
                "potentially worsening LDL and triglyceride levels independently of diet or genetics. "
                "Lipid panel after COVID recovery may not reflect true pre-COVID baseline."
            ),
        },
        {
            "mechanism": "Double endothelial injury (preeclampsia + COVID)",
            "present": adverse_pregnancy_outcome_history and severity in ("severe", "hospitalized", "icu"),
            "explanation": (
                "Two independent endothelial injury events: (1) preeclampsia causes sustained endothelial "
                "dysfunction and vascular remodeling (2x CAD and stroke risk per 2025 AHA/ACC Class I); "
                "(2) severe COVID-19 causes a second wave of endothelial injury via ACE2 disruption. "
                "Standard risk calculators apply the preeclampsia multiplier but cannot capture this "
                "compounding. True cardiovascular risk likely exceeds any calculated estimate."
            ),
        },
    ]

    # Cardiac workup recommendations
    workup = []

    if severity in ("severe", "hospitalized", "icu"):
        workup.append({
            "test": "Echocardiogram (transthoracic)",
            "priority": "HIGH",
            "rationale": (
                "Assess LV ejection fraction and wall motion abnormalities after severe COVID "
                "+ possible myocarditis. Foundational baseline missing if not done since acute illness."
            ),
        })
        workup.append({
            "test": "Cardiac MRI with late gadolinium enhancement",
            "priority": "HIGH" if myocarditis_documented else "MODERATE",
            "rationale": (
                "Detects myocardial fibrosis/scarring from COVID myocarditis, which may persist "
                "years after infection. Safe at eGFR >=30 with macrocyclic gadolinium agents — "
                "confirm agent with radiology."
            ),
        })

    if bp_crisis_during_covid:
        workup.append({
            "test": "Renal artery Doppler ultrasound or MRA kidneys",
            "priority": "HIGH",
            "rationale": (
                "COVID-induced RAAS disruption + possible renal artery stenosis = "
                "compounded BP crisis mechanism. Evaluate structural cause."
            ),
        })

    if new_arrhythmia_during_covid:
        workup.append({
            "test": "24-48 hour Holter monitor or extended event monitor",
            "priority": "HIGH",
            "rationale": (
                "Screen for recurrent or silent arrhythmia following documented "
                "COVID-associated arrhythmia."
            ),
        })

    if new_prediabetes_post_covid:
        workup.append({
            "test": "Fasting insulin + C-peptide",
            "priority": "MODERATE",
            "rationale": (
                "Distinguishes post-COVID beta cell damage (reduced insulin secretion) "
                "from insulin resistance. Guides treatment: GLP-1 agonists preferred "
                "if beta cell damage identified."
            ),
        })

    if severity != "mild":
        workup.append({
            "test": "Fasting lipid panel + HbA1c + eGFR trend",
            "priority": "MODERATE",
            "rationale": (
                "COVID hepatic inflammation may have altered lipid levels post-recovery. "
                "eGFR trend establishes whether any COVID-related AKI occurred."
            ),
        })

    double_injury = (
        adverse_pregnancy_outcome_history
        and severity in ("severe", "hospitalized", "icu")
    )

    # XAI confidence logic
    active_mechanisms = [m["mechanism"] for m in mechanisms if m["present"]]
    severity_upgrade = _SEVERITY_UPGRADE.get(severity, 0)
    if severity in ("severe", "hospitalized", "icu"):
        covid_conf = "moderate"
        covid_conf_note = (
            "Risk tier adjustment is based on large observational cohort studies "
            "(Xie & Al-Aly 2022, N>150,000; Bhatt et al. 2022). However, no "
            "RCT-validated COVID-19 cardiovascular risk calculator exists."
        )
    else:
        covid_conf = "low"
        covid_conf_note = (
            "Limited data exists for mild/moderate COVID-19 cardiovascular risk "
            "quantification. This is a research estimate only."
        )

    xai = _build_xai_metadata(
        confidence_level=covid_conf,
        confidence_note=covid_conf_note,
        key_drivers=[
            f"COVID severity: {severity} (drove {severity_upgrade}-step risk tier change)",
            f"Double endothelial injury: {'present' if double_injury else 'absent'}",
            f"Complications: {', '.join(active_mechanisms[:2]) if active_mechanisms else 'none'}",
        ],
        guideline_version="Xie & Al-Aly 2022 (Nature Medicine); Bhatt et al. 2022 (Lancet); ACC COVID-19 CV Task Force 2023",
        evidence_grade="Observational Data",
        counterfactual=(
            f"If COVID severity were 'mild', no risk tier upgrade would be applied "
            f"(baseline tier '{baseline_risk_tier}' would be unchanged)."
        ),
    )

    return {
        "patient_id": patient_id,
        "covid_severity": severity,
        "year_of_infection": year_of_infection,
        "baseline_risk_tier": baseline_risk_tier,
        "adjusted_risk_tier": adjusted_tier,
        "risk_tier_changed": adjusted_tier != baseline_risk_tier,
        "risk_tier_change_summary": (
            f"{baseline_risk_tier} → {adjusted_tier}"
            if adjusted_tier != baseline_risk_tier
            else "No change"
        ),
        "mechanisms_flagged": mechanisms,
        "active_mechanisms": active_mechanisms,
        "double_endothelial_injury_present": double_injury,
        "cardiac_workup_recommended": workup,
        "calculator_limitation_note": (
            "Standard risk calculators (Reynolds Risk Score, ASCVD Pooled Cohort Equations, "
            "Framingham) were developed before the COVID-19 pandemic and do not capture: "
            "post-COVID endothelial injury, COVID-associated myocarditis, post-COVID "
            "prediabetes, RAAS disruption, or the compounding of preeclampsia + COVID "
            "endothelial injury. The adjusted risk tier above is a research estimate "
            "only and must be reviewed by a clinician."
        ),
        "guideline_references": [
            "Xie & Al-Aly 2022 — Long COVID CV outcomes — https://doi.org/10.1038/s41591-022-01689-3",
            "Bhatt et al. 2022 — COVID-19 and MI/stroke risk — https://doi.org/10.1016/S0140-6736(22)00403-5",
            "ACC COVID-19 CV Task Force 2023 — https://www.jacc.org/doi/10.1016/j.jacc.2023.04.003",
            "2023 AHA Scientific Statement: COVID-19 and CVD — https://doi.org/10.1161/CIR.0000000000001123",
        ],
        "clinical_note": (
            "RESEARCH ONLY — NOT FOR CLINICAL USE. Risk tier adjustment is a "
            "research estimate. Requires clinician review."
        ),
        "xai_metadata": xai,
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
    apob_mg_dl: Optional[float] = None,
    non_hdl_cholesterol_mg_dl: Optional[float] = None,
    patient_sex: str = "female",
    patient_age: int = 67,
) -> dict:
    """Interpret a cardiovascular biomarker panel against clinical reference ranges.

    Classifies each biomarker value into clinical categories (e.g., optimal,
    borderline, high) and flags both high AND low out-of-range values.
    Computes Non-HDL cholesterol if total cholesterol and HDL are provided.
    Uses ACC/AHA and ATP III reference ranges.

    Args:
        ldl_mg_dl: LDL cholesterol in mg/dL.
        hdl_mg_dl: HDL cholesterol in mg/dL.
        total_cholesterol_mg_dl: Total cholesterol in mg/dL.
        triglycerides_mg_dl: Triglycerides in mg/dL.
        fasting_glucose_mg_dl: Fasting glucose in mg/dL.
        hba1c_percent: Hemoglobin A1c as percentage.
        hscrp_mg_l: High-sensitivity C-reactive protein in mg/L.
        bp_systolic_mmhg: Systolic blood pressure in mmHg.
        apob_mg_dl: Apolipoprotein B in mg/dL (risk-tier-dependent targets).
        non_hdl_cholesterol_mg_dl: Non-HDL cholesterol in mg/dL (auto-computed
            from TC - HDL if not provided).
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
        apob_mg_dl=apob_mg_dl,
        non_hdl_cholesterol_mg_dl=non_hdl_cholesterol_mg_dl,
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
    covid_severe_history: bool = False,
) -> dict:
    """Assess lifetime cardiovascular risk from adverse pregnancy outcome history.

    Evaluates known adverse pregnancy outcomes (APOs) as independent CVD risk
    enhancers per 2025 AHA/ACC and ESC guidelines. Preeclampsia, for example,
    doubles 5-15 year stroke and heart disease risk. Returns risk multipliers,
    category, and screening recommendations.

    When covid_severe_history=True and preeclampsia/eclampsia is present, flags
    double endothelial injury (two independent vascular damage events).

    Recognized complications: preeclampsia, eclampsia, gestational_hypertension,
    gestational_diabetes, preterm_birth, low_birth_weight, iugr,
    placental_abruption, stillbirth, recurrent_miscarriage.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        complications: List of adverse pregnancy outcomes (case-insensitive).
        age_at_complication: Age at time of complication (optional).
        num_affected_pregnancies: Number of pregnancies affected (default: 1).
        covid_severe_history: True if patient had severe/hospitalized/ICU COVID.

    Returns:
        Dictionary with recognized complications, CAD/stroke risk multipliers,
        risk category, screening recommendations, and guideline citations.
        Includes double_endothelial_injury_flag when applicable.
    """
    result = await _assess_pregnancy_complication_cv_risk_impl(
        patient_id=patient_id,
        complications=complications,
        age_at_complication=age_at_complication,
        num_affected_pregnancies=num_affected_pregnancies,
        covid_severe_history=covid_severe_history,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def interpret_lipid_pattern(
    patient_id: str,
    ldl_cholesterol: Optional[float] = None,
    total_cholesterol: Optional[float] = None,
    hdl_cholesterol: Optional[float] = None,
    triglycerides: Optional[float] = None,
    non_hdl_cholesterol: Optional[float] = None,
    apob: Optional[float] = None,
    ldl_measured_directly: bool = False,
    patient_risk_tier: str = "high",
    patient_sex: str = "female",
) -> dict:
    """Classify the clinical dyslipidemia pattern from a full lipid panel.

    Treats the lipid panel as a system rather than individual values. Identifies
    the clinical pattern (mixed dyslipidemia, isolated hypercholesterolemia,
    etc.), checks Friedewald LDL validity, evaluates ApoB/LDL concordance,
    and provides treatment implications. All lipid values in mg/dL.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        ldl_cholesterol: LDL cholesterol in mg/dL.
        total_cholesterol: Total cholesterol in mg/dL.
        hdl_cholesterol: HDL cholesterol in mg/dL.
        triglycerides: Triglycerides in mg/dL.
        non_hdl_cholesterol: Non-HDL in mg/dL (auto-computed from TC - HDL).
        apob: Apolipoprotein B in mg/dL.
        ldl_measured_directly: True if LDL was directly measured (not Friedewald).
        patient_risk_tier: "low", "intermediate", "high", or "very_high".
        patient_sex: Patient sex for HDL targets (male/female).

    Returns:
        Dictionary with pattern classification, Friedewald validity,
        ApoB/LDL concordance, Non-HDL vs target, and treatment implications.
    """
    result = await _interpret_lipid_pattern_impl(
        patient_id=patient_id,
        ldl_cholesterol=ldl_cholesterol,
        total_cholesterol=total_cholesterol,
        hdl_cholesterol=hdl_cholesterol,
        triglycerides=triglycerides,
        non_hdl_cholesterol=non_hdl_cholesterol,
        apob=apob,
        ldl_measured_directly=ldl_measured_directly,
        patient_risk_tier=patient_risk_tier,
        patient_sex=patient_sex,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def calculate_fh_clinical_score(
    patient_id: str,
    ldl_cholesterol_mgdl: float,
    family_hx_premature_cvd: bool = False,
    family_hx_high_ldl: bool = False,
    family_hx_tendon_xanthomas: bool = False,
    personal_premature_cvd: bool = False,
    personal_cerebrovascular_disease: bool = False,
    tendon_xanthomas: bool = False,
    corneal_arcus_under_45: bool = False,
    genetic_test_performed: bool = False,
    genetic_test_type: Optional[str] = None,
    genetic_test_variants_tested: Optional[str] = None,
    genetic_test_result: Optional[str] = None,
    causative_mutation_identified: bool = False,
) -> dict:
    """Calculate the Dutch Lipid Clinic Network (DLCN) score for Familial Hypercholesterolemia.

    The DLCN score is the most widely used clinical scoring system for FH,
    validated in EAS 2023 and ACC/AHA 2018 guidelines. It is a clinical
    diagnosis — it does not require genetic confirmation. A negative population
    screening test (e.g., Helix checking 2 APOB variants) does NOT reduce the
    score or rule out FH.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        ldl_cholesterol_mgdl: LDL cholesterol in mg/dL.
        family_hx_premature_cvd: 1st-degree relative with CVD <55 (M) or <60 (F).
        family_hx_high_ldl: 1st-degree relative with LDL above 95th percentile.
        family_hx_tendon_xanthomas: 1st-degree relative has tendon xanthomas.
        personal_premature_cvd: Patient has premature CAD/stroke.
        personal_cerebrovascular_disease: Premature peripheral/cerebrovascular disease.
        tendon_xanthomas: Patient has tendon xanthomas.
        corneal_arcus_under_45: Patient has corneal arcus and is under 45.
        genetic_test_performed: Whether any genetic test was done.
        genetic_test_type: "population_screening", "diagnostic", or "panel".
        genetic_test_variants_tested: Description of variants tested.
        genetic_test_result: "positive", "negative", or "vus".
        causative_mutation_identified: True only if full diagnostic panel confirmed
            a pathogenic variant.

    Returns:
        Dictionary with DLCN score, tier, genetic interpretation, PCSK9
        eligibility note, and guideline references.
    """
    result = await _calculate_fh_clinical_score_impl(
        patient_id=patient_id,
        ldl_cholesterol_mgdl=ldl_cholesterol_mgdl,
        family_hx_premature_cvd=family_hx_premature_cvd,
        family_hx_high_ldl=family_hx_high_ldl,
        family_hx_tendon_xanthomas=family_hx_tendon_xanthomas,
        personal_premature_cvd=personal_premature_cvd,
        personal_cerebrovascular_disease=personal_cerebrovascular_disease,
        tendon_xanthomas=tendon_xanthomas,
        corneal_arcus_under_45=corneal_arcus_under_45,
        genetic_test_performed=genetic_test_performed,
        genetic_test_type=genetic_test_type,
        genetic_test_variants_tested=genetic_test_variants_tested,
        genetic_test_result=genetic_test_result,
        causative_mutation_identified=causative_mutation_identified,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def assess_renal_drug_constraints(
    patient_id: str,
    egfr: float,
    functional_kidney_count: int = 2,
    drug_classes: Annotated[Optional[List[str]], _CoerceList] = None,
) -> dict:
    """Assess cardiovascular drug safety based on eGFR and functional kidney count.

    For patients with CKD or a single functioning kidney, determines which
    cardiovascular drug classes are safe, require dose adjustment, or should
    be avoided. Key insight: eGFR 68 on one kidney carries fundamentally
    different risk than eGFR 68 on two kidneys — no functional reserve.

    Assessed drug classes: statins, anticoagulants, ace_inhibitors, arbs,
    metformin, fibrates, pcsk9_inhibitors, ezetimibe, omega3, glp1_agonists,
    nsaids, contrast_iodinated, contrast_gadolinium.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        egfr: Estimated glomerular filtration rate in mL/min/1.73m².
        functional_kidney_count: Number of functioning kidneys (1 or 2).
        drug_classes: List of drug classes to assess (None = assess all).

    Returns:
        Dictionary with eGFR stage, per-class assessments, single-kidney
        modifier status, top-line recommendations, and clinical note.
    """
    result = await _assess_renal_drug_constraints_impl(
        patient_id=patient_id,
        egfr=egfr,
        functional_kidney_count=functional_kidney_count,
        drug_classes=drug_classes,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def calculate_lipid_treatment_targets(
    patient_id: str,
    current_ldl: float,
    current_apob: Optional[float] = None,
    current_non_hdl: Optional[float] = None,
    current_triglycerides: Optional[float] = None,
    risk_tier: str = "high",
    fh_status: str = "possible",
    currently_on_statin: bool = False,
    current_statin_intensity: Optional[str] = None,
    currently_on_ezetimibe: bool = False,
    currently_on_pcsk9_inhibitor: bool = False,
    renal_constraint: bool = False,
) -> dict:
    """Calculate LDL/ApoB/Non-HDL treatment targets and model therapy pathway.

    Given current lipid values, risk tier, and FH status, calculates treatment
    targets per 2022 ACC Expert Consensus and 2023 ESC guidelines. Models which
    combination of therapies (statin → ezetimibe → PCSK9 inhibitor) is needed
    to reach targets step by step.

    FH status "definite" or "probable" upgrades risk tier one step.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        current_ldl: Current LDL cholesterol in mg/dL.
        current_apob: Current ApoB in mg/dL (optional).
        current_non_hdl: Current Non-HDL cholesterol in mg/dL (optional).
        current_triglycerides: Current triglycerides in mg/dL (optional).
        risk_tier: "very_high", "high", "intermediate", or "low".
        fh_status: "definite", "probable", "possible", "unlikely", or "unknown".
        currently_on_statin: Whether patient is currently on a statin.
        current_statin_intensity: "high", "moderate", or "low" (if on statin).
        currently_on_ezetimibe: Whether patient is currently on ezetimibe.
        currently_on_pcsk9_inhibitor: Whether patient is on a PCSK9 inhibitor.
        renal_constraint: True if single kidney or eGFR <60 (prefer atorvastatin).

    Returns:
        Dictionary with targets, current-vs-target gaps, stepwise therapy
        pathway, guideline references, and statin preference note.
    """
    result = await _calculate_lipid_treatment_targets_impl(
        patient_id=patient_id,
        current_ldl=current_ldl,
        current_apob=current_apob,
        current_non_hdl=current_non_hdl,
        current_triglycerides=current_triglycerides,
        risk_tier=risk_tier,
        fh_status=fh_status,
        currently_on_statin=currently_on_statin,
        current_statin_intensity=current_statin_intensity,
        currently_on_ezetimibe=currently_on_ezetimibe,
        currently_on_pcsk9_inhibitor=currently_on_pcsk9_inhibitor,
        renal_constraint=renal_constraint,
    )
    if DRY_RUN:
        result = add_dry_run_warning(result)
    return result


@mcp.tool()
async def assess_postcovid_cv_risk(
    patient_id: str,
    severity: str,
    year_of_infection: Optional[int] = None,
    myocarditis_documented: bool = False,
    bp_crisis_during_covid: bool = False,
    new_prediabetes_post_covid: bool = False,
    new_arrhythmia_during_covid: bool = False,
    adverse_pregnancy_outcome_history: bool = False,
    baseline_risk_tier: str = "intermediate",
) -> dict:
    """Assess post-COVID cardiovascular risk with tier adjustment and workup.

    Standard risk calculators predate COVID-19 and cannot capture post-COVID
    endothelial injury, myocarditis, RAAS disruption, or the compounding of
    preeclampsia + COVID vascular damage. This tool adjusts a patient's
    baseline cardiovascular risk tier based on COVID severity and complications,
    flags active pathophysiological mechanisms, and generates a structured
    post-COVID cardiac workup recommendation.

    Args:
        patient_id: Patient identifier (e.g., "PAT003").
        severity: COVID severity — "mild", "moderate", "severe",
            "hospitalized", or "icu".
        year_of_infection: Year of COVID infection (optional).
        myocarditis_documented: Chest pain, troponin elevation, or imaging.
        bp_crisis_during_covid: Acute hypertensive event (SBP >180).
        new_prediabetes_post_covid: HbA1c elevation first appearing post-COVID.
        new_arrhythmia_during_covid: New arrhythmia during or within 30 days.
        adverse_pregnancy_outcome_history: Preeclampsia or other APO history.
        baseline_risk_tier: Pre-COVID risk tier — "low", "intermediate",
            "high", or "very_high".

    Returns:
        Dictionary with adjusted risk tier, mechanism flags, double endothelial
        injury detection, cardiac workup recommendations, and guideline refs.
    """
    result = await _assess_postcovid_cv_risk_impl(
        patient_id=patient_id,
        severity=severity,
        year_of_infection=year_of_infection,
        myocarditis_documented=myocarditis_documented,
        bp_crisis_during_covid=bp_crisis_during_covid,
        new_prediabetes_post_covid=new_prediabetes_post_covid,
        new_arrhythmia_during_covid=new_arrhythmia_during_covid,
        adverse_pregnancy_outcome_history=adverse_pregnancy_outcome_history,
        baseline_risk_tier=baseline_risk_tier,
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
