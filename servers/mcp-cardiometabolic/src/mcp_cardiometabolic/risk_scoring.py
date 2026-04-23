"""Validated CVD risk equations: Reynolds, Framingham, ASCVD Pooled Cohort.

All calculations are pure Python with no external dependencies.
"""

import math


# PAT003 DRY_RUN expected values (for test assertions)
PAT003_EXPECTED_REYNOLDS = 14.2
PAT003_EXPECTED_FRAMINGHAM = 10.0
PAT003_EXPECTED_ASCVD = 10.3


def calculate_reynolds_women(
    age: float,
    systolic_bp: float,
    total_cholesterol: float,
    hdl: float,
    hscrp: float,
    family_history_premature_mi: bool,
    current_smoker: bool,
) -> dict:
    """Reynolds Risk Score for women (10-year cardiovascular event risk).

    Validated in Women's Health Study (n=24,558).
    Reference: Ridker PM et al. JAMA. 2007;297(6):611-619.
    """
    fh = 1 if family_history_premature_mi else 0
    smoke = 1 if current_smoker else 0
    # Published coefficients (Ridker 2007, Women's Health Study)
    B = (
        0.0799 * age
        + 3.137 * math.log(systolic_bp)
        + 0.180 * math.log(max(hscrp, 0.01))
        + 1.382 * math.log(total_cholesterol)
        - 1.172 * math.log(hdl)
        + 0.818 * fh
        + 1.084 * smoke
        - 22.325
    )
    # Baseline 10-year survival from WHS cohort calibration
    risk_10yr = (1 - 0.9780 ** math.exp(B)) * 100
    risk_10yr = round(min(max(risk_10yr, 0.1), 99.9), 1)
    category = (
        "low" if risk_10yr < 7.5
        else "intermediate" if risk_10yr < 20.0
        else "high"
    )
    return {
        "score_name": "Reynolds Risk Score (women)",
        "risk_10yr_percent": risk_10yr,
        "risk_category": category,
        "citation": "Ridker PM et al. JAMA. 2007;297(6):611-619",
        "note": "Preferred risk score for women -- incorporates hsCRP and family history",
    }


def calculate_framingham_women(
    age: float,
    total_cholesterol: float,
    hdl: float,
    systolic_bp: float,
    bp_treated: bool,
    current_smoker: bool,
    diabetes: bool,
) -> dict:
    """Framingham 10-year coronary heart disease risk (women).

    Reference: Wilson PW et al. Circulation. 1998;97(18):1837-1847.
    Limitation: derived primarily from White participants in Framingham, MA.
    """
    # Age points
    age_pts = (
        -7 if age < 35 else
        -3 if age < 40 else
        0 if age < 45 else
        3 if age < 50 else
        6 if age < 55 else
        7 if age < 60 else
        8 if age < 65 else
        8 if age < 70 else
        8
    )
    # Total cholesterol points
    tc_pts = (
        0 if total_cholesterol < 160 else
        1 if total_cholesterol < 200 else
        2 if total_cholesterol < 240 else
        3 if total_cholesterol < 280 else
        4
    )
    # HDL points
    hdl_pts = (
        -1 if hdl >= 60 else
        0 if hdl >= 50 else
        1 if hdl >= 40 else
        2
    )
    # Systolic BP points
    if bp_treated:
        sbp_pts = (
            0 if systolic_bp < 120 else
            3 if systolic_bp < 130 else
            4 if systolic_bp < 140 else
            5 if systolic_bp < 160 else
            6
        )
    else:
        sbp_pts = (
            0 if systolic_bp < 120 else
            1 if systolic_bp < 130 else
            2 if systolic_bp < 140 else
            3 if systolic_bp < 160 else
            4
        )
    smoke_pts = 2 if current_smoker else 0
    diabetes_pts = 4 if diabetes else 0
    total_pts = age_pts + tc_pts + hdl_pts + sbp_pts + smoke_pts + diabetes_pts

    # 10-year risk lookup (women, points to %)
    risk_lookup = {
        -2: 1, -1: 1, 0: 1, 1: 1, 2: 1, 3: 1,
        4: 1, 5: 2, 6: 2, 7: 3, 8: 4, 9: 5,
        10: 6, 11: 8, 12: 10, 13: 12, 14: 16,
        15: 20, 16: 25, 17: 30,
    }
    pts_clamped = max(-2, min(total_pts, 17))
    risk_10yr = risk_lookup.get(pts_clamped, 30)
    category = (
        "low" if risk_10yr < 7.5
        else "intermediate" if risk_10yr < 20.0
        else "high"
    )
    return {
        "score_name": "Framingham Risk Score (women)",
        "risk_10yr_percent": float(risk_10yr),
        "risk_category": category,
        "total_points": total_pts,
        "citation": "Wilson PW et al. Circulation. 1998;97(18):1837-1847",
        "limitation": (
            "Derived primarily from White participants; "
            "may underestimate risk in other populations"
        ),
    }


def calculate_ascvd_women_white(
    age: float,
    total_cholesterol: float,
    hdl: float,
    systolic_bp: float,
    bp_treated: bool,
    current_smoker: bool,
    diabetes: bool,
) -> dict:
    """ACC/AHA Pooled Cohort Equations -- White women, 10-year ASCVD risk.

    Used for statin initiation decisions per 2018 ACC/AHA guidelines.
    Reference: Goff DC Jr et al. JACC. 2014;63(25 Pt B):2935-59.
    """
    ln_age = math.log(age)
    ln_tc = math.log(total_cholesterol)
    ln_hdl = math.log(hdl)
    ln_sbp = math.log(systolic_bp)
    smoke = 1 if current_smoker else 0
    diab = 1 if diabetes else 0

    # Published mean coefficient for White women derivation cohort: -29.18
    # Formula: B = sum(beta_i * x_i) - mean_coeff = sum(...) + 29.18
    if bp_treated:
        B = (
            -29.799 * ln_age
            + 4.884 * (ln_age ** 2)
            + 13.540 * ln_tc
            - 3.114 * ln_age * ln_tc
            - 13.578 * ln_hdl
            + 3.149 * ln_age * ln_hdl
            + 2.019 * ln_sbp
            + 7.574 * smoke
            - 1.665 * ln_age * smoke
            + 0.661 * diab
            + 29.18
        )
    else:
        B = (
            -29.799 * ln_age
            + 4.884 * (ln_age ** 2)
            + 13.540 * ln_tc
            - 3.114 * ln_age * ln_tc
            - 13.578 * ln_hdl
            + 3.149 * ln_age * ln_hdl
            + 1.957 * ln_sbp
            + 7.574 * smoke
            - 1.665 * ln_age * smoke
            + 0.661 * diab
            + 29.18
        )
    risk_10yr = (1 - (0.9665 ** math.exp(B))) * 100
    risk_10yr = round(min(max(risk_10yr, 0.1), 99.9), 1)
    category = (
        "low" if risk_10yr < 5.0
        else "borderline" if risk_10yr < 7.5
        else "intermediate" if risk_10yr < 20.0
        else "high"
    )
    statin_recommendation = (
        "high-intensity statin recommended" if risk_10yr >= 20.0
        else "moderate-intensity statin recommended" if risk_10yr >= 7.5
        else "discuss risk-benefit with physician" if risk_10yr >= 5.0
        else "lifestyle modification; statin not indicated by score alone"
    )
    return {
        "score_name": "ACC/AHA Pooled Cohort Equation (White women)",
        "risk_10yr_percent": risk_10yr,
        "risk_category": category,
        "statin_recommendation_by_score": statin_recommendation,
        "citation": "Goff DC Jr et al. JACC. 2014;63(25 Pt B):2935-59",
        "guideline": "2018 ACC/AHA Guideline on the Management of Blood Cholesterol",
    }
