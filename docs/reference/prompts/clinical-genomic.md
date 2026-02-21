# Clinical & Genomic Prompts

Copy-paste prompts for clinical data retrieval and genomic variant analysis.

**Servers used:** mcp-mockepic (3 tools), mcp-fgbio (4 tools), mcp-genomic-results (4 tools)

---

## Clinical Data Queries

### 1. Get Patient Demographics

**Objective:** Retrieve basic patient information (age, gender, diagnosis)

```
Get patient demographics for PatientOne (PAT001-OVC-2025) from the clinical database.
Include: age, gender, diagnosis, stage, and histology.
```

**Expected Output:**
- Patient ID: PAT001-OVC-2025
- Age: 58 years
- Gender: Female
- Diagnosis: High-Grade Serous Ovarian Carcinoma (HGSOC)
- Stage: IV
- Histology: Serous

**Customize:**
- Replace `PAT001-OVC-2025` with your patient ID

---

### 2. Get Treatment History

**Objective:** Retrieve previous treatments and responses

```
Get treatment history for PatientOne (PAT001-OVC-2025).
Include: medications, regimens, response status, and dates.
```

**Expected Output:**
- Carboplatin + Paclitaxel (first-line chemotherapy)
- Status: Platinum-resistant (progression within 6 months)
- Response: Initially responsive, then progressed

**Customize:**
- Replace `PAT001-OVC-2025` with your patient ID

---

### 3. Get Lab Results & Biomarkers

**Objective:** Retrieve relevant laboratory values

```
Get laboratory results and biomarkers for PatientOne (PAT001-OVC-2025).
Focus on cancer-related markers: CA-125, tumor markers, blood counts.
```

**Expected Output:**
- CA-125: Elevated (>35 U/mL)
- Complete blood count (CBC): Within normal limits
- Metabolic panel: Normal

**Customize:**
- Replace `PAT001-OVC-2025` with your patient ID
- Specify specific lab values: `Focus on CA-125 and CEA`

---

### 4. Link Clinical to Spatial Data

**Objective:** Connect clinical diagnosis to tissue regions

```
Link PatientOne's clinical diagnosis (Stage IV HGSOC) to available spatial
transcriptomics data. Identify which tissue regions correspond to tumor vs. normal.
```

**Expected Output:**
- Tumor regions: T1, T2, T3
- Normal regions: N1, N2
- Pathology: High-grade serous histology confirmed

**Customize:**
- Replace patient and diagnosis as needed

---

## Genomic Variant Queries

### 5. List Available Genomic Data

**Objective:** Check what genomic files are available

```
List available genomic data files for PatientOne (PAT001-OVC-2025).
Include VCF files, BAM alignments, and FASTQ reads if present.
```

**Expected Output:**
- VCF: `/data/patient-data/PAT001-OVC-2025/genomic/variants.vcf`
- Variants: 47 total (SNVs and indels)

**Customize:**
- Replace `PAT001-OVC-2025` with your patient ID

---

### 6. Validate VCF File Format

**Objective:** Check VCF file is properly formatted

```
Validate the VCF file format for PatientOne at:
/data/patient-data/PAT001-OVC-2025/genomic/variants.vcf

Check for:
- Proper VCF header
- Required columns (CHROM, POS, REF, ALT, QUAL)
- Valid chromosome names
- Consistent formatting
```

**Expected Output:**
- Valid VCF format: ✓
- Version: VCFv4.2
- Variants: 47
- Chromosomes: chr1-chr22, chrX

**Customize:**
- Replace file path with your VCF location

---

### 7. Identify Pathogenic Variants

**Objective:** Find clinically actionable mutations

```
Analyze the VCF file for PatientOne (PAT001-OVC-2025) and identify
pathogenic or likely pathogenic variants.

Focus on cancer-related genes:
- TP53
- BRCA1/BRCA2
- PIK3CA
- PTEN
- KRAS
- EGFR

For each variant, report:
- Gene and location
- Variant type (SNV, indel)
- Clinical significance
- Population frequency (if available)
```

**Expected Output:**
- TP53: chr17:7,674,220 C>A (pathogenic mutation)
- BRCA1: chr17:41,276,045 G>A (germline variant, likely pathogenic)
- PIK3CA: No variants detected
- PTEN: No variants detected

**Customize:**
- Add/remove genes from list
- Adjust variant filtering (e.g., `only report variants with MAF < 0.01`)

---

### 8. Interpret BRCA1 Variant

**Objective:** Get detailed interpretation of specific variant

```
Interpret the BRCA1 variant found in PatientOne (PAT001-OVC-2025):
- Location: chr17:41,276,045
- Change: G>A
- Type: Germline

Provide:
- Clinical significance (pathogenic, benign, VUS)
- Treatment implications (PARP inhibitors)
- Hereditary cancer risk (for family members)
- Relevant clinical guidelines (NCCN)
```

**Expected Output:**
- **Significance:** Likely pathogenic
- **Treatment:** PARP inhibitors (olaparib, rucaparib) recommended
- **Family Risk:** 50% chance of passing to offspring, genetic counseling advised
- **Guidelines:** NCCN recommends PARP inhibitors for BRCA-mutated ovarian cancer

**Customize:**
- Replace variant details with your variant of interest

---

### 9. Map Variants to Pathways

**Objective:** Connect mutations to biological pathways

```
Map PatientOne's genomic variants (TP53, BRCA1) to affected biological pathways.

For each pathway, report:
- Pathway name (e.g., DNA repair, cell cycle)
- Which genes/variants affect it
- How it contributes to cancer
- Potential therapeutic targets
```

**Expected Output:**
- **DNA Repair Pathway:** BRCA1 variant disrupts homologous recombination
  - Therapeutic target: PARP inhibitors exploit synthetic lethality
- **p53 Pathway:** TP53 mutation disrupts cell cycle checkpoints
  - Therapeutic target: MDM2 inhibitors (less relevant with TP53 loss)
- **Cell Cycle:** TP53 loss allows uncontrolled proliferation

**Customize:**
- Add specific variants to analyze
- Focus on specific pathways (e.g., `Focus on drug resistance pathways`)

---

### 10. Compare to Population Frequency

**Objective:** Determine if variants are rare or common

```
For PatientOne's variants (TP53, BRCA1), check population frequency in:
- gnomAD (general population)
- TCGA ovarian cancer cohort
- ClinVar (clinical databases)

Report:
- Population frequency (%)
- Rare vs. common classification
- Previous clinical reports
```

**Expected Output:**
- **TP53 chr17:7,674,220 C>A:**
  - gnomAD: Not found (very rare)
  - TCGA ovarian: 3.2% of HGSOC cases
  - ClinVar: Pathogenic (multiple reports)

- **BRCA1 chr17:41,276,045 G>A:**
  - gnomAD: 0.001% (rare)
  - TCGA ovarian: 11% of HGSOC cases (germline BRCA)
  - ClinVar: Likely pathogenic

**Customize:**
- Add specific databases to query
- Adjust frequency thresholds
- TCGA queries: Use cBioPortal connector for live cohort mutation frequencies.
  See [Connect External MCP](../../for-researchers/CONNECT_EXTERNAL_MCP.md).

---

## Clinical-Genomic Integration

### 11. Link Genotype to Phenotype

**Objective:** Connect mutations to clinical presentation

```
For PatientOne (PAT001-OVC-2025):

Clinical phenotype:
- Stage IV HGSOC
- Platinum-resistant
- CA-125 elevated

Genomic genotype:
- TP53 mutation
- BRCA1 germline variant

Explain how the genotype explains the phenotype:
- Why is this cancer aggressive (TP53)?
- Why platinum resistance might develop?
- What does BRCA status mean for prognosis?
```

**Expected Output:**
- **TP53 mutation:** Explains high-grade histology and aggressive behavior
  - p53 loss removes cell cycle checkpoints
  - Associated with 96% of HGSOC cases
- **BRCA1 germline:** Initially sensitive to platinum/PARP
  - Resistance develops via BRCA1 reversion mutations
  - Suggests continued PARP inhibitor benefit
- **Platinum resistance:** May be due to BRCA pathway restoration

**Customize:**
- Replace with your patient's phenotype and genotype

---

### 12. Generate Variant Report for Tumor Board

**Objective:** Create summary for clinical discussion

```
Generate a variant interpretation report for PatientOne (PAT001-OVC-2025)
suitable for presentation at a molecular tumor board.

Include:
1. Patient Summary (1 paragraph)
   - Age, diagnosis, stage, treatment history

2. Genomic Findings (bullet list)
   - Pathogenic variants with clinical significance
   - Germline vs. somatic classification

3. Treatment Implications (ranked list)
   - FDA-approved targeted therapies
   - Clinical trial opportunities
   - Off-label options with evidence

4. Prognostic Information
   - How variants affect prognosis
   - Resistance mechanisms to watch for

5. Family Implications
   - Hereditary cancer risk (BRCA1)
   - Genetic counseling recommendations
```

**Expected Output:**
*(Structured report, 2-3 pages)*

**Customize:**
- Adjust sections based on tumor board format
- Add institution-specific guidelines

---

## Quality Control Prompts

### 13. Check Data Completeness

**Objective:** Verify all required data is present

```
For PatientOne (PAT001-OVC-2025), verify data completeness:

Clinical data:
- [ ] Demographics (age, gender)
- [ ] Diagnosis and staging
- [ ] Treatment history
- [ ] Lab results and biomarkers

Genomic data:
- [ ] VCF file present and valid
- [ ] Key genes covered (TP53, BRCA1, PIK3CA, PTEN)
- [ ] Variant annotations available

Report any missing data or gaps.
```

**Expected Output:**
- ✓ Clinical data: Complete
- ✓ Genomic data: VCF present, 47 variants
- ⚠ Missing: BAM alignment file (not critical)
- ✓ Key genes: All covered

**Customize:**
- Add specific data requirements for your analysis

---

### 14. Validate Variant Calls

**Objective:** Check for common VCF errors

```
Validate variant calls in PatientOne VCF file:
/data/patient-data/PAT001-OVC-2025/genomic/variants.vcf

Check for:
- Quality scores (QUAL > 30)
- Read depth (DP > 10)
- Variant allele frequency (VAF > 0.2 for somatic, 0.4-0.6 for germline)
- Filter status (PASS)

Flag any low-quality variants for review.
```

**Expected Output:**
- Total variants: 47
- High quality (QUAL>30): 45 (95.7%)
- Low quality: 2 flagged for review
  - chr3:123456 (QUAL=25, marginal)
  - chr15:789012 (DP=8, low coverage)

**Customize:**
- Adjust quality thresholds based on sequencing platform
- Add specific filters (e.g., `VAF > 0.05 for tumor samples`)

---

## Advanced Queries

### 15. Identify Druggable Variants

**Objective:** Find variants targetable with FDA-approved drugs

```
Analyze PatientOne's variants (TP53, BRCA1) and identify which are
targetable with FDA-approved drugs or drugs in clinical trials.

For each druggable variant, report:
- Gene and variant
- Drug name and mechanism
- FDA approval status (approved, trial, preclinical)
- Evidence level (NCCN, clinical guidelines)
- Expected response rate (if available)
```

**Expected Output:**
- **BRCA1 variant:**
  - Drug: Olaparib (PARP inhibitor)
  - Status: FDA-approved for BRCA-mutated ovarian cancer
  - Evidence: Level 1 (NCCN Category 1)
  - Response rate: 60-70% in BRCA carriers

- **TP53 mutation:**
  - Not directly druggable (loss-of-function)
  - Potential: MDM2 inhibitors (not applicable for null mutation)
  - Focus: Target downstream pathways instead

**Customize:**
- Expand drug database (include investigational agents)
- Filter by approval status: `Only FDA-approved drugs`

**Extend with external sources:** Use ClinicalTrials.gov connector to find
active trials for each druggable variant. Use PubMed connector to retrieve
latest efficacy data. See [Connect External MCP](../../for-researchers/CONNECT_EXTERNAL_MCP.md).

---

### 16. Identify Resistance Mechanisms

**Objective:** Find mutations explaining treatment failure

```
PatientOne developed platinum resistance after initial response.
Analyze VCF file for variants that might explain resistance:

Look for:
- BRCA1/2 reversion mutations (restore function)
- Drug efflux pump overexpression (MDR1)
- Cell cycle checkpoint alterations
- DNA repair pathway changes

Report any variants associated with platinum or PARP resistance.
```

**Expected Output:**
- No BRCA1 reversion mutations detected (resistance mechanism unclear)
- TP53 mutation: Associated with increased genomic instability
- Recommendation: Consider repeat biopsy to check for new mutations

**Customize:**
- Specify which drugs to check resistance for
- Add specific resistance genes to query

---

### 17. Identify Immunotherapy Targets and Biomarkers

**Objective:** Assess PatientOne's tumor for immunotherapy target expression to evaluate candidacy for next-generation immunotherapies (bispecifics, vaccines, TIL therapy)

```
For PatientOne (PAT001-OVC-2025), analyze expression of immunotherapy-relevant
targets and biomarkers across available multi-omics and spatial data.

Data location: gs://sample-inputs-patientone/patient-data/PAT001-OVC-2025/

Check the following target categories:

1. Checkpoint ligands (cadonilimab PD-1xCTLA-4 candidacy):
   - CD274 (PD-L1): Expression level and spatial distribution
   - CTLA4: Expression on T cells in stroma/periphery
   - LAG3, HAVCR2 (TIM3), TIGIT: Alternative checkpoint targets
   → If PD-L1 low but CTLA-4 present: dual blockade (cadonilimab) may be effective

2. BiTE targets (ubamatamab MUC16xCD3 candidacy):
   - MUC16: Expression level (correlates with CA-125 serum levels)
   - CD3D, CD3E: T-cell presence (even if excluded from tumor)
   → If MUC16 high + CD3+ cells in stroma: ubamatamab can redirect T cells

3. Innate immune targets (NI-1801 MSLNxCD47 candidacy):
   - MSLN (mesothelin): Tumor cell expression
   - CD47: "Don't eat me" signal on tumor cells
   - CD68: Macrophage presence in tumor/stroma
   → If MSLN+ tumor + CD68+ macrophages present: NI-1801 can activate phagocytosis

4. Vaccine targets (IGFBP-2 vaccine candidacy):
   - IGFBP2: Overexpression in tumor vs. normal tissue
   → If IGFBP2 overexpressed: vaccine can generate targeted T-cell response

5. TIL feasibility markers (TIL therapy candidacy):
   - CD8A: Presence at tumor periphery/stroma (TIL harvest site)
   - Exhaustion markers: PDCD1 (PD-1), LAG3, HAVCR2, TIGIT on CD8+ cells
   - Activation markers: GZMB, PRF1 (if available)
   → If CD8+ at periphery with moderate exhaustion: TIL can be expanded ex vivo

For each target, report:
- Expression level (High/Medium/Low/Not detected/Not in panel)
- Spatial distribution (tumor core, stroma, periphery, interface)
- Immunotherapy candidacy assessment
- Data source (Visium spatial, multi-omics RNA, multi-omics protein)

NOTE: Not all targets may be present in PatientOne's synthetic 31-gene Visium
panel. For targets not in the spatial panel, check multi-omics RNA data.
If unavailable in both, note as "Not in current panel — requires additional assay."
```

**Expected Output:**

| Target | Expression | Location | Source | Therapy Candidacy |
|--------|-----------|----------|--------|-------------------|
| CD274 (PD-L1) | Low | Stroma interface | Spatial/RNA | Low for mono; consider combination |
| CTLA4 | Low-Medium | T cells in stroma | RNA | Supports dual blockade (cadonilimab) |
| MUC16 | High | Tumor core + periphery | Clinical (CA-125) | Strong ubamatamab candidate |
| CD3D/CD3E | Medium | Stroma, excluded from tumor | Spatial | T cells present for BiTE redirection |
| MSLN | Medium-High | Tumor cells | RNA | NI-1801 candidate (verify expression) |
| CD47 | High | Tumor cells | RNA | CD47 blockade relevant |
| CD68 | Medium | Stroma | Spatial/Imaging | Macrophages available for NI-1801 |
| IGFBP2 | Check RNA | Tumor | RNA | Vaccine candidate if overexpressed |
| CD8A | Low (tumor), Medium (stroma) | Periphery/stroma | Spatial/Imaging | TIL harvest feasible from periphery |
| PDCD1 (PD-1) | Medium | CD8+ T cells | RNA | Moderate exhaustion — TIL expandable |

**Customize:**
- Add/remove targets based on available panel genes
- Adjust for different cancer types (different target priorities)
- Focus on specific therapy: e.g., `Focus only on BiTE targets for ubamatamab assessment`

**Extend with external sources:** Search ClinicalTrials.gov for recruiting
trials matching each immunotherapy candidate (e.g., ubamatamab, cadonilimab).
Search PubMed and bioRxiv for latest efficacy and safety data.
See [Connect External MCP](../../for-researchers/CONNECT_EXTERNAL_MCP.md).

**Reference:** See [Immunotherapy Reference](../testing/patient-one/immunotherapy-reference.md) for detailed candidate profiles and decision framework.

---

## Troubleshooting

**"VCF file not found"**
- Check file path is correct
- Verify patient ID matches directory name
- Use: `List available genomic data files` first

**"No pathogenic variants found"**
- Expand gene list (include more cancer genes)
- Lower variant quality threshold (check low-quality calls)
- Check if VCF is annotated (clinical significance field)

**"FHIR data empty"**
- Verify patient ID exists in clinical database
- Check DRY_RUN mode (uses synthetic data)
- Try mcp-mockepic instead of mcp-epic for demos

---

**Related Prompts:**
- [Multi-Omics Prompts](multiomics.md) - Integrate genomic with expression data
- [Spatial Prompts](spatial.md) - Add spatial context
- [Complete Workflows](workflows.md) - End-to-end analyses

---

**Last Updated:** 2026-01-14
