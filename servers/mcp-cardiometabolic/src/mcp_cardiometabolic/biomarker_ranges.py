"""Clinical reference ranges and cutoffs for cardiovascular biomarkers."""

REFERENCE_RANGES = {
    "ldl_mg_dl": {
        "optimal": (0, 100),
        "near_optimal": (100, 129),
        "borderline_high": (130, 159),
        "high": (160, 189),
        "very_high": (190, float("inf")),
        "pat003_value": 118,
        "pat003_category": "near_optimal",
    },
    "hdl_mg_dl": {
        "low_risk_women": (60, float("inf")),
        "acceptable": (50, 59),
        "low_women": (0, 49),
        "pat003_value": 58,
        "pat003_category": "acceptable",
    },
    "total_cholesterol_mg_dl": {
        "desirable": (0, 200),
        "borderline_high": (200, 239),
        "high": (240, float("inf")),
        "pat003_value": 195,
        "pat003_category": "desirable",
    },
    "triglycerides_mg_dl": {
        "normal": (0, 150),
        "borderline_high": (150, 199),
        "high": (200, 499),
        "very_high": (500, float("inf")),
        "pat003_value": 142,
        "pat003_category": "normal",
    },
    "fasting_glucose_mg_dl": {
        "normal": (0, 100),
        "prediabetes": (100, 125),
        "diabetes": (126, float("inf")),
        "pat003_value": 98,
        "pat003_category": "normal_upper",
    },
    "hba1c_percent": {
        "normal": (0, 5.7),
        "prediabetes": (5.7, 6.4),
        "diabetes": (6.5, float("inf")),
        "pat003_value": 5.6,
        "pat003_category": "normal_upper",
    },
    "hscrp_mg_l": {
        "low_cvd_risk": (0, 1.0),
        "moderate_cvd_risk": (1.0, 3.0),
        "high_cvd_risk": (3.0, float("inf")),
        "pat003_value": 1.8,
        "pat003_category": "moderate_cvd_risk",
    },
    "lpa_mg_dl": {
        "normal": (0, 30),
        "borderline": (30, 50),
        "high": (50, float("inf")),
        "pat003_value": None,
        "pat003_category": "unknown -- test recommended",
    },
    "bp_systolic_mmhg": {
        "normal": (0, 120),
        "elevated": (120, 130),
        "stage1_htn": (130, 140),
        "stage2_htn": (140, float("inf")),
        "pat003_value": 138,
        "pat003_category": "stage1_htn_controlled",
    },
}

STATIN_CONSIDERATION_THRESHOLDS = {
    "ascvd_10yr_high_risk": 20.0,
    "ascvd_10yr_intermediate": 7.5,
    "reynolds_intermediate_women": 10.0,
    "ldl_fh_threshold": 190,
    "ldl_diabetes_threshold": 70,
    "hscrp_jupiter_threshold": 2.0,
}

JUPITER_NOTE = (
    "The JUPITER trial (Ridker et al., NEJM 2008) demonstrated rosuvastatin benefit "
    "in patients with LDL < 130 mg/dL AND hsCRP >= 2.0 mg/L. PAT003 hsCRP = 1.8 mg/L "
    "(just below threshold). Monitor; if hsCRP rises above 2.0, JUPITER criteria apply."
)


def classify_biomarker(name: str, value: float) -> str:
    """Return the clinical category for a biomarker value."""
    ranges = REFERENCE_RANGES.get(name)
    if not ranges:
        return "unknown"
    for category, bounds in ranges.items():
        if category.startswith("pat003"):
            continue
        if isinstance(bounds, tuple) and len(bounds) == 2:
            low, high = bounds
            if low <= value < high:
                return category
    return "unknown"
