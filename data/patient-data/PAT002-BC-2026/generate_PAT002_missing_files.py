#!/usr/bin/env python3
"""
Generate 6 missing synthetic data files for PAT002-BC-2026.

Patient: Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma
         Germline BRCA2 c.5946delT, on tamoxifen 20mg daily

Files generated:
  1. genomics/PAT002_cnv.cns        — CNVkit segmentation (BC CNV profile)
  2. genomics/PAT002_somatic.vcf    — Somatic variant calls (PIK3CA/GATA3/CDH1/MAP3K1/TP53)
  3. spatial/PAT002_expression.csv   — Patient-prefixed Visium expression matrix
  4. spatial/PAT002_coordinates.csv  — Patient-prefixed spot coordinates
  5. spatial/PAT002_regions.csv      — Patient-prefixed tissue region annotations
  6. perturbation/gears_pat002_results.json — GEARS perturbation predictions
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(2026)

BASE_DIR = Path(__file__).parent
GENOMICS_DIR = BASE_DIR / "genomics"
SPATIAL_DIR = BASE_DIR / "spatial"
PERTURB_DIR = BASE_DIR / "perturbation"

PATIENT_ID = "PAT002-BC-2026"


# ============================================================
# File 1: genomics/PAT002_cnv.cns
# ============================================================
def generate_cnv():
    print("[1/6] Generating genomics/PAT002_cnv.cns ...")

    segments = [
        # Gains
        ("chr8",  127700000, 128800000, "MYC",    0.9,  3, 489, 28, 0.94),
        ("chr11", 69400000,  69550000,  "CCND1",  1.2,  3, 478, 22, 0.93),
        ("chr3",  178900000, 179000000, "PIK3CA", 0.7,  3, 212, 25, 0.95),
        # Losses
        ("chr13", 32310000,  32400000,  "BRCA2", -1.1,  1, 98,  35, 0.92),
        ("chr16", 68700000,  68900000,  "CDH1",  -0.8,  1, 112, 20, 0.91),
        # HER2 neutral (important for HER2- status)
        ("chr17", 39690000,  39730000,  "ERBB2",  0.02, 2, 223, 20, 0.96),
        # Neutral background segments covering remaining autosomes
        ("chr1",  10000000,  50000000,  ".",       0.03, 2, 245, 40, 0.97),
        ("chr1",  50000000, 248956422,  ".",       0.01, 2, 252, 55, 0.98),
        ("chr2",  10000000, 242193529,  ".",      -0.02, 2, 238, 60, 0.97),
        ("chr4",  10000000, 190214555,  ".",       0.04, 2, 241, 50, 0.97),
        ("chr5",  10000000, 181538259,  ".",       0.01, 2, 195, 45, 0.96),
        ("chr6",  10000000, 170805979,  ".",      -0.01, 2, 256, 48, 0.97),
        ("chr7",  10000000, 159345973,  ".",       0.03, 2, 230, 42, 0.96),
        ("chr9",  10000000, 138394717,  ".",      -0.03, 2, 220, 38, 0.96),
        ("chr10", 10000000, 133797422,  ".",       0.02, 2, 235, 44, 0.97),
        ("chr12", 10000000, 133275309,  ".",       0.00, 2, 248, 46, 0.97),
        ("chr14", 10000000, 107043718,  ".",      -0.01, 2, 225, 36, 0.96),
        ("chr15", 10000000, 101991189,  ".",       0.02, 2, 232, 34, 0.96),
        ("chr17", 7570000,   7590000,   "TP53",   0.03, 2, 234, 20, 0.97),
        ("chr18", 10000000,  80373285,  ".",      -0.02, 2, 218, 32, 0.95),
        ("chr19", 10000000,  58617616,  ".",       0.01, 2, 240, 30, 0.96),
        ("chr20", 10000000,  64444167,  ".",       0.04, 2, 228, 28, 0.95),
        ("chr21", 10000000,  46709983,  ".",      -0.01, 2, 215, 22, 0.94),
        ("chr22", 10000000,  50818468,  ".",       0.02, 2, 210, 20, 0.94),
        ("chrX",  10000000, 156040895,  ".",       0.00, 2, 244, 50, 0.97),
    ]

    header = (
        f"## PAT002-BC-2026 — CNVkit segmentation\n"
        f"## Diagnosis: Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma\n"
        f"## Germline BRCA2 c.5946delT\n"
    )
    col_header = "chromosome\tstart\tend\tgene\tlog2\tcn\tdepth\tprobes\tweight"

    out = GENOMICS_DIR / "PAT002_cnv.cns"
    with open(out, "w") as f:
        f.write(header)
        f.write(col_header + "\n")
        for seg in segments:
            f.write("\t".join(str(v) for v in seg) + "\n")

    print(f"  -> {out}  ({len(segments)} segments)")


# ============================================================
# File 2: genomics/PAT002_somatic.vcf
# ============================================================
def generate_somatic_vcf():
    print("[2/6] Generating genomics/PAT002_somatic.vcf ...")

    # Read existing VCF header style from somatic_variants.vcf
    header_lines = [
        "##fileformat=VCFv4.2",
        "##fileDate=20260115",
        "##source=Mutect2",
        "##reference=hg38",
        f"##patient={PATIENT_ID}",
        "##contig=<ID=chr3,length=198295559>",
        "##contig=<ID=chr5,length=181538259>",
        "##contig=<ID=chr10,length=133797422>",
        "##contig=<ID=chr16,length=170805979>",
        "##contig=<ID=chr17,length=83257441>",
        '##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">',
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">',
        '##INFO=<ID=GENE,Number=1,Type=String,Description="Gene Symbol">',
        '##INFO=<ID=EFFECT,Number=1,Type=String,Description="Variant Effect">',
        '##INFO=<ID=COSMIC,Number=1,Type=String,Description="COSMIC ID">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic depths for the ref and alt alleles">',
        '##FORMAT=<ID=AF,Number=A,Type=Float,Description="Allele fractions">',
    ]
    col_header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tTUMOR\tNORMAL"

    # Somatic mutations — breast-cancer-appropriate
    variants = [
        # PIK3CA p.H1047R — most common ER+ BC driver
        ("chr3", 179234297, "PIK3CA_H1047R", "A", "G", "1245.6", "PASS",
         "DP=238;AF=0.42;GENE=PIK3CA;EFFECT=missense_variant;COSMIC=COSM775",
         "GT:AD:AF", "0/1:138,100:0.42", "0/0:210,0:0.00"),
        # GATA3 frameshift — common in luminal BC
        ("chr10", 8095656, "GATA3_fs", "GCTT", "G", "934.2", "PASS",
         "DP=203;AF=0.31;GENE=GATA3;EFFECT=frameshift_variant;COSMIC=COSV104733902",
         "GT:AD:AF", "0/1:140,63:0.31", "0/0:195,0:0.00"),
        # CDH1 splice site — common in lobular BC
        ("chr16", 68771967, "CDH1_splice", "G", "A", "678.4", "PASS",
         "DP=186;AF=0.28;GENE=CDH1;EFFECT=splice_donor_variant;COSMIC=COSV58014213",
         "GT:AD:AF", "0/1:134,52:0.28", "0/0:201,0:0.00"),
        # MAP3K1 nonsense — ER+ BC enriched
        ("chr5", 56798505, "MAP3K1_p.Q761X", "C", "T", "856.8", "PASS",
         "DP=197;AF=0.35;GENE=MAP3K1;EFFECT=stop_gained;COSMIC=COSV99009601",
         "GT:AD:AF", "0/1:128,69:0.35", "0/0:189,0:0.00"),
        # TP53 missense — subclonal
        ("chr17", 7675088, "TP53_R248W", "G", "A", "312.4", "PASS",
         "DP=220;AF=0.15;GENE=TP53;EFFECT=missense_variant;COSMIC=COSM10662",
         "GT:AD:AF", "0/1:187,33:0.15", "0/0:245,0:0.00"),
    ]

    out = GENOMICS_DIR / "PAT002_somatic.vcf"
    with open(out, "w") as f:
        for line in header_lines:
            f.write(line + "\n")
        f.write(col_header + "\n")
        for v in variants:
            f.write("\t".join(str(x) for x in v) + "\n")

    print(f"  -> {out}  ({len(variants)} somatic variants)")


# ============================================================
# File 3: spatial/PAT002_expression.csv
# ============================================================
def generate_expression():
    print("[3/6] Generating spatial/PAT002_expression.csv ...")

    src = SPATIAL_DIR / "visium_gene_expression.csv"
    df = pd.read_csv(src, index_col=0)

    # Rename spot barcodes to PAT002 prefix
    df.index = [f"PAT002_{b}" for b in df.index]
    df.index.name = "spot_id"

    # Add patient_id column at front
    df.insert(0, "patient_id", PATIENT_ID)

    # Ensure luminal A profile: elevate ESR1, PGR, GATA3, FOXA1
    luminal_genes = ["ESR1", "PGR", "GATA3", "FOXA1"]
    for gene in luminal_genes:
        if gene in df.columns:
            current = df[gene].values.astype(float)
            # Boost to luminal-A level: multiply by 2.5 + add baseline
            df[gene] = np.clip(current * 2.5 + np.random.poisson(8, len(current)), 5, 200)

    # Ensure ERBB2 (HER2) is NOT elevated
    if "ERBB2" in df.columns:
        df["ERBB2"] = np.clip(
            np.random.poisson(2, len(df)).astype(float), 0, 5
        )
    # Also check alternate name
    for col in df.columns:
        if col.upper() in ("HER2",):
            df[col] = np.clip(np.random.poisson(2, len(df)).astype(float), 0, 5)

    out = SPATIAL_DIR / "PAT002_expression.csv"
    df.to_csv(out)
    print(f"  -> {out}  ({df.shape[0]} spots x {df.shape[1] - 1} genes)")


# ============================================================
# File 4: spatial/PAT002_coordinates.csv
# ============================================================
def generate_coordinates():
    print("[4/6] Generating spatial/PAT002_coordinates.csv ...")

    src = SPATIAL_DIR / "visium_spatial_coordinates.csv"
    df = pd.read_csv(src)

    # Rename barcode column to use PAT002 prefix
    df["barcode"] = ["PAT002_" + b for b in df["barcode"]]
    df.rename(columns={"barcode": "spot_id"}, inplace=True)

    # Add patient_id column
    df.insert(0, "patient_id", PATIENT_ID)

    out = SPATIAL_DIR / "PAT002_coordinates.csv"
    df.to_csv(out, index=False)
    print(f"  -> {out}  ({len(df)} spots)")


# ============================================================
# File 5: spatial/PAT002_regions.csv
# ============================================================
def generate_regions():
    print("[5/6] Generating spatial/PAT002_regions.csv ...")

    src = SPATIAL_DIR / "visium_region_annotations.csv"
    df = pd.read_csv(src)

    # Rename barcode column
    df["barcode"] = ["PAT002_" + b for b in df["barcode"]]
    df.rename(columns={"barcode": "spot_id"}, inplace=True)

    # Add patient_id column
    df.insert(0, "patient_id", PATIENT_ID)

    # Map existing region labels to breast-cancer-appropriate labels
    region_map = {
        "adipose": "adipose",
        "tumor_invasive_front": "tumor_core",
        "stroma_fibrous": "stroma",
        "stroma_immune": "immune_infiltrate",
        "tumor_core_luminal": "tumor_core",
        "tumor_proliferative": "tumor_core",
        "ductal_normal": "normal_epithelium",
    }
    df["region"] = df["region"].map(region_map).fillna("stroma")

    out = SPATIAL_DIR / "PAT002_regions.csv"
    df.to_csv(out, index=False)

    print(f"  -> {out}  ({len(df)} spots)")
    region_counts = df["region"].value_counts()
    for r, n in region_counts.items():
        print(f"     {r}: {n}")


# ============================================================
# File 6: perturbation/gears_pat002_results.json
# ============================================================
def generate_gears():
    print("[6/6] Generating perturbation/gears_pat002_results.json ...")

    data = {
        "patient_id": PATIENT_ID,
        "model": "GEARS",
        "perturbations": [
            {
                "gene": "ESR1",
                "type": "knockout",
                "predicted_effect": "loss_of_luminal_identity",
                "top_affected_genes": ["PGR", "GATA3", "FOXA1", "TFF1", "XBP1"],
                "mean_expression_change": -2.8,
                "confidence": 0.91,
                "clinical_relevance":
                    "Models tamoxifen resistance via ESR1 loss",
            },
            {
                "gene": "PIK3CA",
                "type": "inhibition",
                "predicted_effect": "reduced_proliferation",
                "top_affected_genes": ["AKT1", "MTOR", "CCND1", "MKI67", "RPS6"],
                "mean_expression_change": -1.6,
                "confidence": 0.87,
                "clinical_relevance":
                    "Alpelisib sensitivity prediction (PIK3CA H1047R)",
            },
            {
                "gene": "CDK4",
                "type": "inhibition",
                "predicted_effect": "G1_arrest",
                "top_affected_genes": ["RB1", "E2F1", "CCND1", "MKI67", "PCNA"],
                "mean_expression_change": -1.9,
                "confidence": 0.93,
                "clinical_relevance":
                    "Palbociclib response prediction (CDK4/6i)",
            },
            {
                "gene": "BRCA2",
                "type": "knockout",
                "predicted_effect": "homologous_recombination_deficiency",
                "top_affected_genes": ["RAD51", "PALB2", "FANCD2", "CHEK2", "ATM"],
                "mean_expression_change": -2.1,
                "confidence": 0.89,
                "clinical_relevance":
                    "PARP inhibitor sensitivity (germline BRCA2 c.5946delT)",
            },
            {
                "gene": "FOXP3",
                "type": "overexpression",
                "predicted_effect": "immune_suppression",
                "top_affected_genes": ["IL2", "CD8A", "GZMB", "IFNG", "TNF"],
                "mean_expression_change": -1.3,
                "confidence": 0.82,
                "clinical_relevance":
                    "Treg expansion limiting immunotherapy response",
            },
        ],
        "summary": {
            "most_actionable_target": "CDK4",
            "hrd_score": 35,
            "immune_evasion_score": 0.41,
            "luminal_stability_score": 0.78,
        },
    }

    out = PERTURB_DIR / "gears_pat002_results.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  -> {out}  ({len(data['perturbations'])} perturbations)")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print(f"Generating 6 missing files for {PATIENT_ID}")
    print("=" * 60)

    # Ensure output dirs exist
    GENOMICS_DIR.mkdir(parents=True, exist_ok=True)
    SPATIAL_DIR.mkdir(parents=True, exist_ok=True)
    PERTURB_DIR.mkdir(parents=True, exist_ok=True)

    generate_cnv()
    generate_somatic_vcf()
    generate_expression()
    generate_coordinates()
    generate_regions()
    generate_gears()

    print("\n" + "=" * 60)
    print("All 6 files generated successfully.")
    print("=" * 60)
