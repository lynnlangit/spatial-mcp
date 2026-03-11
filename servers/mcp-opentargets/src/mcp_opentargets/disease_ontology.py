"""EFO disease ID mappings and mock data for DRY_RUN mode."""

# ---------------------------------------------------------------------------
# Disease name -> EFO ID mappings
# ---------------------------------------------------------------------------

DISEASE_IDS = {
    "ovarian carcinoma": "EFO_0001071",
    "high-grade serous ovarian carcinoma": "EFO_0001071",
    "HGSOC": "EFO_0001071",
    "breast carcinoma": "EFO_0000305",
    "lung adenocarcinoma": "EFO_0000571",
    "colorectal carcinoma": "EFO_0000365",
    "pancreatic carcinoma": "EFO_0002618",
    "melanoma": "EFO_0000756",
    "glioblastoma": "EFO_0000519",
    "prostate carcinoma": "EFO_0001663",
}

# ---------------------------------------------------------------------------
# Gene symbol -> Ensembl ID mappings
# Covers HGSOC genomic drivers + immunotherapy targets
# ---------------------------------------------------------------------------

HGSOC_GENE_SYMBOL_TO_ENSEMBL = {
    # --- HGSOC genomic drivers ---
    "TP53": "ENSG00000141510",
    "PIK3CA": "ENSG00000121879",
    "PTEN": "ENSG00000171862",
    "BRCA1": "ENSG00000012048",
    "BRCA2": "ENSG00000139618",
    "MYC": "ENSG00000136997",
    "CCNE1": "ENSG00000105173",
    "AKT2": "ENSG00000105221",
    "RB1": "ENSG00000139687",
    "CDKN2A": "ENSG00000147889",
    "BRAF": "ENSG00000157764",
    "KRAS": "ENSG00000133703",
    "ARID1A": "ENSG00000117713",
    "VEGFA": "ENSG00000112715",
    "CDK12": "ENSG00000167461",
    "NF1": "ENSG00000196712",
    "EMSY": "ENSG00000158636",
    "RAD51C": "ENSG00000108384",
    "RAD51D": "ENSG00000185379",
    "CD274": "ENSG00000120217",  # PD-L1
    # --- Checkpoint — T cell ---
    "PDCD1": "ENSG00000188389",   # PD-1
    "CTLA4": "ENSG00000163599",
    "TIGIT": "ENSG00000181847",
    "LAG3": "ENSG00000089692",
    "HAVCR2": "ENSG00000135077",  # TIM-3
    # --- Phagocytosis checkpoint ---
    "CD47": "ENSG00000196776",
    "SIRPA": "ENSG00000198053",
    "CD36": "ENSG00000135218",
    # --- TAM reprogramming ---
    "CSF1R": "ENSG00000182578",
    "IL10": "ENSG00000136634",
    "CD163": "ENSG00000177575",
    "PPARG": "ENSG00000132170",
    # --- Immune exclusion / stroma ---
    "TGFB1": "ENSG00000105329",
    "PTK2": "ENSG00000169398",   # FAK
    "COL6A3": "ENSG00000163359",
    # --- Treg recruitment ---
    "CCL22": "ENSG00000102962",
    "CCR4": "ENSG00000183813",
    "FOXP3": "ENSG00000049768",
    "IL2RA": "ENSG00000134460",
    # --- NK cell dysfunction ---
    "KLRC1": "ENSG00000204592",  # NKG2A
    "MICA": "ENSG00000204520",
    "MICB": "ENSG00000204516",
    "NCR1": "ENSG00000189430",
    # --- Epigenetic priming ---
    "DNMT1": "ENSG00000130816",
    "DNMT3A": "ENSG00000119772",
    "HDAC1": "ENSG00000116478",
    "HDAC2": "ENSG00000068305",
    # --- Antigen presentation ---
    "B2M": "ENSG00000166710",
    "TAP1": "ENSG00000168394",
    "TAP2": "ENSG00000204267",
}

# ---------------------------------------------------------------------------
# Mock data for DRY_RUN mode
# ---------------------------------------------------------------------------

MOCK_TARGET_INFO = {
    "TP53": {
        "id": "ENSG00000141510",
        "symbol": "TP53",
        "name": "Tumor protein p53",
        "description": "Acts as a tumor suppressor in many tumor types; induces growth arrest "
        "or apoptosis depending on the physiological circumstances and cell type.",
        "biotype": "protein_coding",
        "tractability": {
            "smallMolecule": 0.7,
            "antibody": 0.3,
            "otherModalities": 0.2,
        },
    },
    "PIK3CA": {
        "id": "ENSG00000121879",
        "symbol": "PIK3CA",
        "name": "Phosphatidylinositol-4,5-bisphosphate 3-kinase catalytic subunit alpha",
        "description": "Catalytic subunit of PI3K involved in cell growth and survival signaling.",
        "biotype": "protein_coding",
        "tractability": {
            "smallMolecule": 0.95,
            "antibody": 0.1,
            "otherModalities": 0.3,
        },
    },
    "VEGFA": {
        "id": "ENSG00000112715",
        "symbol": "VEGFA",
        "name": "Vascular endothelial growth factor A",
        "description": "Growth factor active in angiogenesis, vasculogenesis and "
        "endothelial cell growth.",
        "biotype": "protein_coding",
        "tractability": {
            "smallMolecule": 0.6,
            "antibody": 0.95,
            "otherModalities": 0.4,
        },
    },
    "BRCA1": {
        "id": "ENSG00000012048",
        "symbol": "BRCA1",
        "name": "BRCA1 DNA repair associated",
        "description": "E3 ubiquitin-protein ligase involved in DNA repair, "
        "transcriptional regulation, and cell cycle checkpoint control.",
        "biotype": "protein_coding",
        "tractability": {
            "smallMolecule": 0.2,
            "antibody": 0.1,
            "otherModalities": 0.5,
        },
    },
}

MOCK_ASSOCIATION_SCORES = {
    "TP53": {
        "overall_score": 0.87,
        "evidence_scores": {
            "literature": 0.92,
            "rna_expression": 0.85,
            "genetic_association": 0.78,
            "somatic_mutation": 0.95,
            "known_drug": 0.45,
            "animal_model": 0.60,
            "affected_pathway": 0.88,
        },
    },
    "PIK3CA": {
        "overall_score": 0.72,
        "evidence_scores": {
            "literature": 0.80,
            "rna_expression": 0.65,
            "genetic_association": 0.55,
            "somatic_mutation": 0.88,
            "known_drug": 0.82,
            "animal_model": 0.50,
            "affected_pathway": 0.75,
        },
    },
    "PTEN": {
        "overall_score": 0.68,
        "evidence_scores": {
            "literature": 0.75,
            "rna_expression": 0.60,
            "genetic_association": 0.62,
            "somatic_mutation": 0.80,
            "known_drug": 0.35,
            "animal_model": 0.55,
            "affected_pathway": 0.70,
        },
    },
    "BRCA1": {
        "overall_score": 0.82,
        "evidence_scores": {
            "literature": 0.90,
            "rna_expression": 0.70,
            "genetic_association": 0.92,
            "somatic_mutation": 0.75,
            "known_drug": 0.80,
            "animal_model": 0.65,
            "affected_pathway": 0.85,
        },
    },
    "BRCA2": {
        "overall_score": 0.78,
        "evidence_scores": {
            "literature": 0.85,
            "rna_expression": 0.62,
            "genetic_association": 0.88,
            "somatic_mutation": 0.70,
            "known_drug": 0.75,
            "animal_model": 0.60,
            "affected_pathway": 0.80,
        },
    },
    "VEGFA": {
        "overall_score": 0.65,
        "evidence_scores": {
            "literature": 0.70,
            "rna_expression": 0.72,
            "genetic_association": 0.40,
            "somatic_mutation": 0.30,
            "known_drug": 0.90,
            "animal_model": 0.55,
            "affected_pathway": 0.60,
        },
    },
    "MYC": {
        "overall_score": 0.60,
        "evidence_scores": {
            "literature": 0.78,
            "rna_expression": 0.80,
            "genetic_association": 0.35,
            "somatic_mutation": 0.65,
            "known_drug": 0.15,
            "animal_model": 0.50,
            "affected_pathway": 0.72,
        },
    },
    "CCNE1": {
        "overall_score": 0.55,
        "evidence_scores": {
            "literature": 0.65,
            "rna_expression": 0.70,
            "genetic_association": 0.30,
            "somatic_mutation": 0.60,
            "known_drug": 0.20,
            "animal_model": 0.40,
            "affected_pathway": 0.58,
        },
    },
    "KRAS": {
        "overall_score": 0.50,
        "evidence_scores": {
            "literature": 0.60,
            "rna_expression": 0.45,
            "genetic_association": 0.40,
            "somatic_mutation": 0.55,
            "known_drug": 0.70,
            "animal_model": 0.45,
            "affected_pathway": 0.50,
        },
    },
    "CDK12": {
        "overall_score": 0.48,
        "evidence_scores": {
            "literature": 0.55,
            "rna_expression": 0.50,
            "genetic_association": 0.42,
            "somatic_mutation": 0.45,
            "known_drug": 0.30,
            "animal_model": 0.35,
            "affected_pathway": 0.52,
        },
    },
}

MOCK_DRUGS = {
    "PIK3CA": [
        {
            "name": "Alpelisib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PI3K alpha selective inhibitor",
            "indications": ["breast cancer"],
            "clinical_trial_count": 45,
        },
        {
            "name": "Copanlisib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PI3K inhibitor (pan-class I)",
            "indications": ["follicular lymphoma"],
            "clinical_trial_count": 22,
        },
    ],
    "VEGFA": [
        {
            "name": "Bevacizumab",
            "phase": 4,
            "status": "Approved",
            "mechanism": "VEGF-A inhibitor (monoclonal antibody)",
            "indications": ["ovarian cancer", "colorectal cancer", "NSCLC"],
            "clinical_trial_count": 320,
        },
        {
            "name": "Aflibercept",
            "phase": 4,
            "status": "Approved",
            "mechanism": "VEGF trap (decoy receptor)",
            "indications": ["colorectal cancer", "macular degeneration"],
            "clinical_trial_count": 85,
        },
    ],
    "BRCA1": [
        {
            "name": "Olaparib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PARP inhibitor",
            "indications": ["ovarian cancer", "breast cancer", "prostate cancer"],
            "clinical_trial_count": 180,
        },
        {
            "name": "Niraparib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PARP inhibitor",
            "indications": ["ovarian cancer"],
            "clinical_trial_count": 75,
        },
        {
            "name": "Rucaparib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PARP inhibitor",
            "indications": ["ovarian cancer", "prostate cancer"],
            "clinical_trial_count": 55,
        },
    ],
    "BRCA2": [
        {
            "name": "Olaparib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PARP inhibitor",
            "indications": ["ovarian cancer", "breast cancer", "prostate cancer"],
            "clinical_trial_count": 180,
        },
        {
            "name": "Talazoparib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PARP inhibitor",
            "indications": ["breast cancer"],
            "clinical_trial_count": 40,
        },
    ],
    "KRAS": [
        {
            "name": "Sotorasib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "KRAS G12C inhibitor",
            "indications": ["non-small cell lung cancer"],
            "clinical_trial_count": 35,
        },
        {
            "name": "Adagrasib",
            "phase": 3,
            "status": "Approved",
            "mechanism": "KRAS G12C inhibitor",
            "indications": ["non-small cell lung cancer"],
            "clinical_trial_count": 28,
        },
    ],
    "BRAF": [
        {
            "name": "Vemurafenib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "BRAF V600E inhibitor",
            "indications": ["melanoma"],
            "clinical_trial_count": 120,
        },
        {
            "name": "Dabrafenib",
            "phase": 4,
            "status": "Approved",
            "mechanism": "BRAF inhibitor",
            "indications": ["melanoma", "NSCLC"],
            "clinical_trial_count": 95,
        },
    ],
    "TP53": [
        {
            "name": "APR-246 (Eprenetapopt)",
            "phase": 3,
            "status": "Investigational",
            "mechanism": "p53 reactivator (restores wild-type conformation)",
            "indications": ["MDS", "AML", "ovarian cancer (investigational)"],
            "clinical_trial_count": 15,
        },
    ],
    "CD274": [
        {
            "name": "Pembrolizumab",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PD-1 antibody (blocks PD-L1/PD-1 interaction)",
            "indications": ["melanoma", "NSCLC", "various solid tumors"],
            "clinical_trial_count": 500,
        },
        {
            "name": "Nivolumab",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PD-1 antibody",
            "indications": ["melanoma", "RCC", "NSCLC"],
            "clinical_trial_count": 400,
        },
        {
            "name": "Atezolizumab",
            "phase": 4,
            "status": "Approved",
            "mechanism": "PD-L1 antibody",
            "indications": ["bladder cancer", "NSCLC", "breast cancer"],
            "clinical_trial_count": 250,
        },
    ],
}

MOCK_SAFETY = {
    "VEGFA": {
        "safety_liabilities": [
            {
                "event": "Hypertension",
                "biosamples": ["cardiovascular system"],
                "effects": ["blood pressure increase", "proteinuria"],
            },
            {
                "event": "Hemorrhage",
                "biosamples": ["vascular system"],
                "effects": ["GI bleeding", "epistaxis"],
            },
            {
                "event": "Wound healing complications",
                "biosamples": ["connective tissue"],
                "effects": ["delayed wound healing", "wound dehiscence"],
            },
        ],
        "adverse_events": [
            {"event": "Hypertension", "count": 1250, "frequency": "very_common"},
            {"event": "Proteinuria", "count": 680, "frequency": "common"},
            {"event": "GI perforation", "count": 120, "frequency": "uncommon"},
        ],
        "risk_level": "moderate",
    },
    "PIK3CA": {
        "safety_liabilities": [
            {
                "event": "Hyperglycemia",
                "biosamples": ["pancreas", "liver"],
                "effects": ["insulin resistance", "glucose elevation"],
            },
            {
                "event": "Diarrhea",
                "biosamples": ["gastrointestinal tract"],
                "effects": ["GI toxicity"],
            },
        ],
        "adverse_events": [
            {"event": "Hyperglycemia", "count": 890, "frequency": "very_common"},
            {"event": "Diarrhea", "count": 720, "frequency": "very_common"},
            {"event": "Rash", "count": 450, "frequency": "common"},
        ],
        "risk_level": "moderate",
    },
    "TP53": {
        "safety_liabilities": [],
        "adverse_events": [],
        "risk_level": "low",
    },
    "BRCA1": {
        "safety_liabilities": [
            {
                "event": "Myelosuppression",
                "biosamples": ["bone marrow"],
                "effects": ["anemia", "neutropenia", "thrombocytopenia"],
            },
        ],
        "adverse_events": [
            {"event": "Anemia", "count": 950, "frequency": "very_common"},
            {"event": "Nausea", "count": 1100, "frequency": "very_common"},
            {"event": "Fatigue", "count": 880, "frequency": "very_common"},
        ],
        "risk_level": "moderate",
    },
}

# Default mock data for genes not in the specific lookup tables
MOCK_DEFAULT_TARGET_INFO = {
    "description": "Protein-coding gene implicated in cancer biology.",
    "biotype": "protein_coding",
    "tractability": {
        "smallMolecule": 0.5,
        "antibody": 0.3,
        "otherModalities": 0.2,
    },
}

MOCK_DEFAULT_ASSOCIATION = {
    "overall_score": 0.40,
    "evidence_scores": {
        "literature": 0.45,
        "rna_expression": 0.40,
        "genetic_association": 0.30,
        "somatic_mutation": 0.35,
        "known_drug": 0.10,
        "animal_model": 0.25,
        "affected_pathway": 0.40,
    },
}

MOCK_DEFAULT_SAFETY = {
    "safety_liabilities": [],
    "adverse_events": [],
    "risk_level": "unknown",
}

# Mock disease-to-targets mapping for search_targets_by_disease
MOCK_DISEASE_TARGETS = [
    {"symbol": "TP53", "score": 0.87, "top_evidence": "somatic_mutation"},
    {"symbol": "BRCA1", "score": 0.82, "top_evidence": "genetic_association"},
    {"symbol": "BRCA2", "score": 0.78, "top_evidence": "genetic_association"},
    {"symbol": "PIK3CA", "score": 0.72, "top_evidence": "somatic_mutation"},
    {"symbol": "PTEN", "score": 0.68, "top_evidence": "somatic_mutation"},
    {"symbol": "VEGFA", "score": 0.65, "top_evidence": "known_drug"},
    {"symbol": "MYC", "score": 0.60, "top_evidence": "rna_expression"},
    {"symbol": "KRAS", "score": 0.50, "top_evidence": "known_drug"},
    {"symbol": "CCNE1", "score": 0.55, "top_evidence": "rna_expression"},
    {"symbol": "BRAF", "score": 0.52, "top_evidence": "known_drug"},
    {"symbol": "RB1", "score": 0.50, "top_evidence": "somatic_mutation"},
    {"symbol": "AKT2", "score": 0.48, "top_evidence": "affected_pathway"},
    {"symbol": "CDK12", "score": 0.48, "top_evidence": "literature"},
    {"symbol": "CDKN2A", "score": 0.45, "top_evidence": "somatic_mutation"},
    {"symbol": "ARID1A", "score": 0.44, "top_evidence": "somatic_mutation"},
    {"symbol": "NF1", "score": 0.42, "top_evidence": "genetic_association"},
    {"symbol": "CD274", "score": 0.40, "top_evidence": "known_drug"},
    {"symbol": "EMSY", "score": 0.38, "top_evidence": "literature"},
    {"symbol": "RAD51C", "score": 0.36, "top_evidence": "genetic_association"},
    {"symbol": "RAD51D", "score": 0.34, "top_evidence": "genetic_association"},
]
