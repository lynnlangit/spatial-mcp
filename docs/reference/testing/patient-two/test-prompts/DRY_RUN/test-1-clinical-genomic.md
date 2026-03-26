TEST 1: Clinical Data and Genomic Analysis
===========================================

> **Data Mode:** This test uses **synthetic data** — DRY_RUN mode for mcp-fgbio, plus mock servers (mcp-mockepic and mcp-mocktcga are always synthetic).

Patient ID: PAT002-BC-2026

## PART 1: Clinical Data (use mcp-mockepic)

The patient data files are located at `patient-data/PAT002-BC-2026/`.

1. For patient PAT002-BC-2026, retrieve:
   - Patient demographics (name, age, family history)
   - Genetic mutations noted in family history
   - BRCA2 status

2. Retrieve lab results for this patient:
   - CEA and CA 15-3 tumor marker levels
   - What do the marker levels indicate about disease status?
   - Any evidence of recurrence?

Files to read:
- patient_demographics.json (contains Michelle Thompson, age 42, BRCA2 germline mutation)
- lab_results.json (contains CEA: 2.1 ng/mL, CA 15-3: 18 U/mL — within normal limits)

## PART 2: Genomic Analysis (use mcp-fgbio and mcp-mocktcga)

3. Parse somatic variants for patient PAT002-BC-2026:
   Use fgbio to read the VCF file with these expected mutations:
   - BRCA2 c.5946delT (chr13:32,339,811) — frameshift, germline
   - PIK3CA H1047R (chr3:178,952,085 G>A) — hotspot activating mutation
   - GATA3 frameshift (chr10:8,100,656) — transcription factor disruption
   - MAP3K1 R264H (chr5:56,111,569 C>T) — missense variant

   Copy number alterations to look for:
   - MYC, CCND1 amplifications
   - CDKN2A deletion
   - Note: TP53 is WILD-TYPE (important contrast with HGSOC)

4. Compare to TCGA-BRCA cohort (use mcp-mocktcga):
   For a patient with:
   - BRCA2 germline mutation
   - PIK3CA H1047R somatic mutation
   - ER+/PR+/HER2- subtype
   - Stage IIA

   Questions:
   - What TCGA molecular subtype does this match? (Expect Luminal A or Luminal B)
   - What is the typical prognosis for BRCA2-mutant, PIK3CA-mutant ER+ breast cancer?
   - What pathways are commonly activated in luminal breast cancer?

## Expected Results to Validate:

**Clinical:**
- Patient: Michelle Anne Thompson
- Age: 42 years old
- BRCA2: Pathogenic germline mutation (c.5946delT)
- Family history: Mother — breast cancer at 58; maternal aunt — ovarian cancer at 52; sister — BRCA2 carrier
- CEA: 2.1 ng/mL (normal)
- CA 15-3: 18 U/mL (normal)
- Disease status: Disease-free under surveillance

**Genomic:**
- BRCA2 mutation: c.5946delT (frameshift)
- PIK3CA mutation: H1047R (activating hotspot)
- GATA3 mutation: Frameshift (common in luminal BC)
- MAP3K1 mutation: R264H (missense)
- Copy number: MYC, CCND1 amplified; CDKN2A deleted
- TP53: Wild-type

**TCGA:**
- Subtype: Luminal A or Luminal B
- Prognosis: Favourable with early-stage ER+ disease + adjuvant endocrine therapy
- Activated pathways: PI3K/AKT/mTOR, Estrogen receptor signalling

## Output Format:
Please provide:
1. Patient summary (demographics, genetic risk, family history)
2. Tumor marker analysis (CEA and CA 15-3 interpretation)
3. Key somatic mutations identified
4. TCGA subtype and pathway analysis
5. Clinical significance summary
