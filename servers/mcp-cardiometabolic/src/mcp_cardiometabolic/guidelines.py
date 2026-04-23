"""ACC/AHA guideline logic for statin decisions, monitoring, and lifestyle."""


def get_statin_recommendation(
    ascvd_risk: float,
    ldl: float,
    hscrp: float,
    lpa_known: bool,
    lpa_value: float = None,
    cac_score: float = None,
) -> dict:
    """ACC/AHA 2018 guideline statin decision logic for intermediate-risk patients.

    Incorporates risk-enhancing factors relevant to PAT003.
    """
    decision = "discuss with physician"
    rationale = []
    risk_enhancers = []

    if ascvd_risk >= 20.0:
        decision = "high-intensity statin recommended"
        rationale.append("10-year ASCVD risk >= 20%")
    elif ascvd_risk >= 7.5:
        decision = "discuss moderate-intensity statin"
        rationale.append("Intermediate ASCVD risk (7.5-19.9%)")
        if hscrp >= 2.0:
            risk_enhancers.append(
                "hsCRP >= 2.0 mg/L (JUPITER criteria -- rosuvastatin benefit shown "
                "even with normal LDL)"
            )
        if lpa_known and lpa_value and lpa_value >= 50:
            risk_enhancers.append(
                f"Lp(a) >= 50 mg/dL ({lpa_value} mg/dL) -- upgrades to high risk"
            )
            decision = "high-intensity statin recommended"
        if cac_score is not None:
            if cac_score == 0:
                decision = "statin may be deferred"
                rationale.append(
                    "CAC = 0 reclassifies to lower risk; reasonable to defer statin"
                )
            elif cac_score >= 100:
                decision = "high-intensity statin recommended"
                rationale.append(f"CAC = {cac_score} -- high atherosclerotic burden")

    if not lpa_known:
        risk_enhancers.append(
            "Lp(a) not measured -- order once; if >= 50 mg/dL, upgrades statin indication"
        )
    if cac_score is None:
        risk_enhancers.append(
            "CAC score not obtained -- most powerful reclassification tool for "
            "intermediate-risk patients; CAC=0 would support deferring statin"
        )

    return {
        "statin_decision": decision,
        "rationale": rationale,
        "risk_enhancing_factors": risk_enhancers,
        "guideline": "2018 ACC/AHA Guideline on the Management of Blood Cholesterol",
        "note": "This is AI-generated decision support. "
                "Clinical decision requires physician review.",
    }


def get_monitoring_schedule(risk_category: str, on_treatment: bool) -> dict:
    """Return evidence-based monitoring schedule for cardiovascular risk."""
    return {
        "lipid_panel_months": 12 if risk_category in ("low", "borderline") else 6,
        "bp_check_weeks": 8 if on_treatment else 26,
        "hba1c_months": 12,
        "hscrp_months": 24,
        "renal_function_months": 12,
        "lpa_timing": "once -- Lp(a) is genetically fixed and does not change with lifestyle",
        "cac_score": "once, if intermediate risk and statin decision uncertain",
        "apoe_genotyping": "once -- discuss with physician for cognitive + CVD risk context",
    }


def get_lifestyle_recommendations() -> list:
    """Evidence-based lifestyle recommendations for cardiovascular risk reduction.

    All recommendations cite guideline or trial source.
    """
    return [
        {
            "intervention": "Mediterranean or DASH diet",
            "evidence": "PREDIMED trial: 30% relative CVD risk reduction vs low-fat diet",
            "citation": "Estruch R et al. NEJM. 2013;368:1279-1290",
            "relevance": "Strong: addresses LDL, hsCRP, and blood pressure simultaneously",
        },
        {
            "intervention": "Aerobic exercise >= 150 min/week moderate intensity",
            "evidence": "AHA guidelines: 5-7 mmHg SBP reduction; HDL increase ~3-5 mg/dL",
            "citation": "2018 AHA/ACC Physical Activity Guidelines",
            "relevance": "Strong: addresses all PAT003 risk factors",
        },
        {
            "intervention": "Sodium restriction < 2.3g/day",
            "evidence": "DASH-sodium trial: 3-7 mmHg SBP reduction in stage 1 hypertension",
            "citation": "Sacks FM et al. NEJM. 2001;344:3-10",
            "relevance": "Strong: directly relevant to controlled hypertension",
        },
        {
            "intervention": "Weight maintenance (avoid gain post-menopause)",
            "evidence": "Post-menopausal weight gain of 5+ kg increases CVD risk 20-30%",
            "citation": "Colditz GA et al. Ann Intern Med. 1995;122:481-486",
            "relevance": "Moderate: BMI=26.4 is near optimal; maintain current weight",
        },
        {
            "intervention": "Omega-3 fatty acids (EPA+DHA >= 1g/day from fish)",
            "evidence": (
                "REDUCE-IT trial: icosapentaenoic acid reduced CVD events 25% "
                "in high-triglyceride patients; benefit less clear at TG=142"
            ),
            "citation": "Bhatt DL et al. NEJM. 2019;380:11-22",
            "relevance": "Moderate: triglycerides borderline; consider oily fish 2x/week",
        },
        {
            "intervention": "Moderate alcohol (<= 1 drink/day for women)",
            "evidence": (
                "Current evidence: 3 units/week is within safe range; "
                "no cardiovascular benefit from increasing; minimize further"
            ),
            "citation": "2021 Canadian Cardiovascular Society guidelines",
            "relevance": "Low: current intake acceptable; no change indicated",
        },
    ]
