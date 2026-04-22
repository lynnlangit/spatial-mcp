"""Canonical PAT003 test values — Preventive Cardiovascular Health.

PAT003 is a synthetic patient profile representing a 67-year-old
post-menopausal woman with controlled hypertension and bilateral
family history of cardiovascular disease.  This is a representative
case for the "healthy aging, 65+ female" demographic — a population
significantly underrepresented in cardiovascular clinical research.

Usage::

    from tests.fixtures.pat003_canonical import PAT003

    def test_reynolds_risk():
        assert result["reynolds_risk_score"] == PAT003["reynolds_risk_score_percent"]
"""

PAT003 = {
    # --- Demographics ---
    "patient_id": "PAT003",
    "age": 67,
    "sex": "female",
    "bmi": 26.4,
    "menopausal_status": "post-menopausal",

    # --- Cardiovascular biomarkers ---
    "bp_systolic_mmhg": 138,
    "bp_diastolic_mmhg": 82,
    "bp_status": "controlled",
    "ldl_mg_dl": 118,
    "hdl_mg_dl": 58,
    "total_cholesterol_mg_dl": 195,
    "triglycerides_mg_dl": 142,
    "fasting_glucose_mg_dl": 98,
    "hba1c_percent": 5.6,
    "crp_mg_l": 1.8,  # high-sensitivity CRP; <1 low, 1-3 moderate, >3 high

    # --- Family history (first-degree) ---
    "family_history": [
        {"relation": "father", "event": "myocardial_infarction", "age_at_event": 61},
        {"relation": "mother", "event": "ischemic_stroke", "age_at_event": 69},
    ],

    # --- Current medications ---
    "medications": [
        {
            "name": "lisinopril",
            "dose_mg": 5.0,
            "frequency": "daily",
            "indication": "hypertension",
            "gene_target": "ACE",
        },
    ],

    # --- Lifestyle ---
    "smoking_status": "never",
    "exercise_frequency": "moderate",  # 3x/week, 30 min
    "diet_pattern": "low-sodium",
    "alcohol_units_per_week": 3,

    # --- Key cardiovascular risk genes (for opentargets queries) ---
    "cvd_risk_genes": ["APOE", "LDLR", "ACE", "PCSK9", "CDKN2A", "CDKN2B", "LPA"],

    # --- Estimated risk scores (for verification) ---
    "framingham_10yr_risk_percent": 12.4,   # intermediate risk (7.5-20%)
    "ascvd_10yr_risk_percent": 11.8,        # ACC/AHA pooled cohort equation
    "reynolds_risk_score_percent": 14.2,    # Reynolds (includes CRP + family hx)
    # What makes Reynolds higher than Framingham: bilateral family history + CRP
    # Reynolds was specifically validated in women — use it as primary risk estimate

    # --- Preventive health questions this profile should answer ---
    "clinical_questions": [
        "What is her 10-year cardiovascular event risk?",
        "Which genetic variants most elevate her risk?",
        "Is lisinopril the optimal medication given her genetic profile?",
        "What evidence exists for statin initiation at LDL=118 in intermediate-risk women?",
        "What lifestyle interventions have the strongest evidence for her profile?",
        "What biomarkers should she monitor and at what frequency?",
        "Are there emerging therapies (PCSK9 inhibitors, inclisiran) relevant to her?",
    ],
}
