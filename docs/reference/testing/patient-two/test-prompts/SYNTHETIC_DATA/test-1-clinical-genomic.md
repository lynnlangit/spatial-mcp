TEST 1: Clinical Data and Genomic Analysis (SYNTHETIC_DATA Mode)
=================================================================

> **Data Mode:** This test uses **SYNTHETIC_DATA** — `*_DRY_RUN=false`. Servers parse the actual generated files in `/data/patient-data/PAT002-BC-2026/`. No heavy bioinformatics tools required, but Python parsing dependencies must be installed. See [Data Modes Guide](../../data-modes-guide.md) for details.

Patient ID: PAT002-BC-2026

## Prerequisites

| Requirement | Details |
|------------|---------|
| `MOCKEPIC_DRY_RUN` | `false` |
| `FGBIO_DRY_RUN` | `false` |
| `GENOMIC_RESULTS_DRY_RUN` | `false` |
| `MOCKTCGA_DRY_RUN` | `false` |
| Python deps | Standard libraries (json, csv parsing) |
| Data files | `data/patient-data/PAT002-BC-2026/clinical/` and `genomics/` |

## PART 1: Clinical Data (use mcp-mockepic)

The patient data files are located at `data/patient-data/PAT002-BC-2026/clinical/`.

1. For patient PAT002-BC-2026, retrieve:
   - Patient demographics (name, age, family history)
   - Genetic mutations noted in family history
   - BRCA2 status

2. Retrieve lab results for this patient:
   - CEA and CA 15-3 tumor marker levels
   - What do the marker levels indicate about disease status?
   - Any evidence of recurrence?

Files parsed by the server:
- `data/patient-data/PAT002-BC-2026/clinical/patient_demographics.json`
- `data/patient-data/PAT002-BC-2026/clinical/lab_results.json`

## PART 2: Genomic Analysis (use mcp-genomic-results and mcp-mocktcga)

3. Parse somatic variants for patient PAT002-BC-2026:
   Use genomic-results to read the **patient-prefixed VCF** file:
   - File: `data/patient-data/PAT002-BC-2026/genomics/PAT002_somatic.vcf`
   - Look for PIK3CA H1047R, GATA3 frameshift, CDH1 splice donor, MAP3K1 nonsense, TP53 R248W (subclonal)

   Parse copy number alterations from the **patient-prefixed CNS** file:
   - File: `data/patient-data/PAT002-BC-2026/genomics/PAT002_cnv.cns`
   - Look for BRCA2 loss (cn=1), MYC gain, CCND1 gain, PIK3CA gain, CDH1 loss
   - Confirm ERBB2 (HER2) neutral (cn=2) — validates HER2-negative status
   - 25 segments spanning all autosomes

4. Compare to TCGA-BRCA cohort (use mcp-mocktcga):
   For a patient with:
   - BRCA2 germline mutation (c.5946delT)
   - PIK3CA H1047R somatic mutation
   - ER+/PR+/HER2- subtype
   - Stage IIA (T2N0M0)

   Questions:
   - What TCGA molecular subtype does this match? (Expect Luminal A or Luminal B)
   - What is the typical prognosis for BRCA2-mutant, PIK3CA-mutant ER+ breast cancer?
   - What pathways are commonly activated in luminal breast cancer?

## How This Differs from DRY_RUN

| Aspect | DRY_RUN | SYNTHETIC_DATA (this test) |
|--------|---------|---------------------------|
| Data source | Hardcoded inline mock values | Parsed from actual files on disk |
| VCF parsing | Returns fixed variant list | Reads and parses `PAT002_somatic.vcf` |
| CNS parsing | Returns fixed CNV list | Reads and parses `PAT002_cnv.cns` |
| JSON parsing | Returns fixed demographics | Reads and parses `patient_demographics.json` |
| File I/O | None | Real file reads from `data/` directory |
| VCF file | `somatic_variants.vcf` (any path) | `PAT002_somatic.vcf` (patient-prefixed) |
| CNS file | `copy_number_results.cns` (any path) | `PAT002_cnv.cns` (patient-prefixed, 25 segments) |

## Expected Results

Results should match the synthetic data files. Validate that the server correctly parsed:

**Clinical (from JSON files):**
- Patient: Michelle Anne Thompson, 42 years old
- BRCA2: Pathogenic germline mutation (c.5946delT)
- Family history: Mother breast cancer (age 58), maternal aunt gyn cancer (age 52), sister BRCA2 carrier
- CEA: 2.1 ng/mL (normal)
- CA 15-3: 18 U/mL (normal)
- Disease status: Disease-free under surveillance

**Genomic (from PAT002_somatic.vcf):**
- PIK3CA H1047R (chr3:179234297, VAF 0.42) — ER+ BC driver
- GATA3 frameshift (chr10:8095656, VAF 0.31) — luminal BC
- CDH1 splice donor (chr16:68771967, VAF 0.28) — lobular BC
- MAP3K1 nonsense Q761X (chr5:56798505, VAF 0.35) — ER+ enriched
- TP53 R248W (chr17:7675088, VAF 0.15) — subclonal

**CNV (from PAT002_cnv.cns):**
- BRCA2 loss: log2 -1.1, cn=1 (germline LOH)
- MYC gain: log2 +0.9, cn=3
- CCND1 gain: log2 +1.2, cn=3
- PIK3CA gain: log2 +0.7, cn=3
- CDH1 loss: log2 -0.8, cn=1
- ERBB2 neutral: log2 ~0, cn=2 (HER2-negative confirmed)
- 25 total segments

**TCGA:**
- Subtype: Luminal A or Luminal B
- Prognosis: Favourable with early-stage ER+ disease + adjuvant endocrine therapy
- Activated pathways: PI3K/AKT/mTOR, Estrogen receptor signalling

## Output Format

Please provide:
1. Patient summary (demographics, genetic risk) — from parsed JSON
2. CEA/CA 15-3 analysis — from parsed lab results
3. Key somatic mutations identified — from parsed PAT002_somatic.vcf
4. Copy number alterations — from parsed PAT002_cnv.cns
5. TCGA subtype and pathway analysis
6. Note any discrepancies between parsed values and expected synthetic data

## Validation Checkpoints

- [ ] Server correctly reads files from `data/patient-data/PAT002-BC-2026/`
- [ ] VCF parsing reads `PAT002_somatic.vcf` (not `somatic_variants.vcf`)
- [ ] VCF parsing returns 5 somatic variants with correct positions and VAFs
- [ ] CNS parsing reads `PAT002_cnv.cns` (not `copy_number_results.cns`)
- [ ] CNS parsing returns 25 segments including BRCA2 loss and ERBB2 neutral
- [ ] JSON parsing returns patient demographics (not hardcoded mock)
- [ ] Results are consistent with the synthetic data design
