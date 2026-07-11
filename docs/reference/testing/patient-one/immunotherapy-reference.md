# PatientOne: Immunotherapy Research Reference

Next-generation immunotherapy candidates for Stage IV HGSOC with cold/immune-excluded tumor microenvironment.

---

## ⚠️ IMPORTANT: Research Use Only

```
This document is for RESEARCH AND EDUCATIONAL purposes only.
All treatment information requires validation by qualified oncologists.
See PatientOne disclaimers: ./README.md
```

---

## Overview

### PatientOne Immunotherapy Context

PatientOne (PAT001-OVC-2025) presents a challenging case for immunotherapy:

| Factor | Status | Implication |
|--------|--------|-------------|
| **BRCA1 germline** | Pathogenic | Higher neoantigen load, but not sufficient alone |
| **Platinum-resistant** | Yes (8-month recurrence) | Limited standard options remain |
| **TME phenotype** | Cold / immune-excluded | Low CD8+ infiltration (~5-15 cells/mm²), thick stromal barrier |
| **Checkpoint expression** | Low PD-L1 in tumor core | Standard anti-PD-1 monotherapy unlikely effective |
| **Proliferation** | High (Ki67 45-55%) | Aggressive tumor requiring rapid intervention |
| **Key mutations** | TP53 R175H, PIK3CA E545K, PTEN LOH | PI3K/AKT/mTOR pathway activation |

### Why Next-Gen Immunotherapy?

Standard checkpoint inhibitors (anti-PD-1/PD-L1 monotherapy) show limited efficacy in cold/immune-excluded HGSOC. Next-generation approaches aim to overcome immune exclusion through:

1. **Bispecific antibodies** — Simultaneously engage multiple targets to redirect immune cells
2. **Innate cell engagers** — Activate macrophages/NK cells that are already present in tumor
3. **Bispecific T-cell engagers (BiTEs)** — Force T-cell activation against tumor antigens in cold tumors
4. **Cancer vaccines** — Generate new immune responses against tumor-associated antigens
5. **Engineered TIL therapy** — Expand and enhance tumor-infiltrating lymphocytes ex vivo

---

## Five Promising Immunotherapy Candidates

### Summary Comparison

| # | Therapy | Type | Developer | Mechanism | Phase | Key Result | PatientOne Relevance |
|---|---------|------|-----------|-----------|-------|------------|---------------------|
| 1 | **Cadonilimab** | PD-1 x CTLA-4 bispecific | Akeso | Dual checkpoint blockade with single molecule | II | 94.1% ORR with chemo (cervical) | Overcomes PD-L1 low limitation |
| 2 | **NI-1801** | Mesothelin x CD47 ICE | Light Chain Bio | Activates macrophages against MSLN+ tumor | I | 75% 1-year OS platinum-resistant + pembro | Innate immune activation bypasses cold TME |
| 3 | **Ubamatamab** | MUC16 x CD3 BiTE | Regeneron | Forces T-cell killing of MUC16+ tumor cells | I/II | Activates T cells in cold tumors | MUC16 (CA-125) highly expressed in HGSOC |
| 4 | **IGFBP-2 Vaccine** | DNA plasmid vaccine | UW Medicine | Generates T-cell response against IGFBP2 | I (completed) | >50% alive at 8 years | Long-term immune memory |
| 5 | **TIL Therapy** | Engineered cell therapy | Multiple | Expand tumor-reactive T cells ex vivo | I/II | CD28/IL-15 methods improve persistence | Can rescue immune response from excluded cells |

---

## Detailed Candidate Profiles

### 1. Cadonilimab (AK104) — PD-1 x CTLA-4 Bispecific

**Developer:** Akeso Inc.
**Mechanism:** Bispecific antibody simultaneously blocking PD-1 and CTLA-4, providing dual checkpoint inhibition with a single molecule. The bispecific format enables cis-binding on the same T cell, potentially more effective than combination of two separate antibodies.

**Clinical Evidence:**
- **Phase II cervical cancer:** 94.1% ORR when combined with chemotherapy (practice-changing results)
- **Phase II recurrent ovarian (NCT06560112):** Recruiting, 172 patients, combination with AK112, estimated completion 2026
- **Phase I/II ovarian + radiation (NCT06940921):** Low-dose radiation + SBRT + cadonilimab for advanced ovarian with peritoneal metastases
- **Approved:** NMPA-approved (China) for cervical cancer (2022)

**NCT IDs:**
- [NCT06560112](https://clinicaltrials.gov/study/NCT06560112) — Phase II, recurrent ovarian cancer, AK104 + AK112 + chemo (Recruiting)
- [NCT06940921](https://clinicaltrials.gov/study/NCT06940921) — Phase I/II, LDRT + SBRT + cadonilimab, ovarian with peritoneal mets

**Relevance to PatientOne:**
- Dual checkpoint blockade may overcome low PD-L1 expression in cold TME
- CTLA-4 blockade can prime new T-cell responses (vs. PD-1 which reactivates existing)
- Combined with chemotherapy may convert cold → hot TME
- Platinum-resistant ovarian cancer is an active enrollment indication

**Platform Tool Analysis Approach:**
1. **mcp-spatialtools:** Map PD-L1 (CD274), CTLA-4, PD-1 (PDCD1) spatial expression across tumor regions
2. **mcp-multiomics:** Check CTLA-4 and PD-1 RNA/protein expression levels in resistant vs. sensitive samples
3. **mcp-perturbation (GEARS):** Predict effect of dual PD-1/CTLA-4 blockade on immune activation genes
4. **ClinicalTrials.gov MCP** *(external)*: Search for recruiting cadonilimab + ovarian cancer trials
5. **PubMed MCP** *(external)*: Review latest cadonilimab efficacy data in gynecologic cancers

---

### 2. NI-1801 — Mesothelin x CD47 Innate Cell Engager

**Developer:** Light Chain Bioscience (Novimmune SA)
**Mechanism:** Bispecific antibody targeting mesothelin (MSLN) on tumor cells and CD47 ("don't eat me" signal). By blocking CD47, NI-1801 enables macrophage-mediated phagocytosis of MSLN-expressing tumor cells. This innate cell engager (ICE) approach bypasses the need for T-cell infiltration — critical for cold tumors.

**Clinical Evidence:**
- **Phase 1b (NCT05403554):** NI-1801 + pembrolizumab in platinum-resistant ovarian cancer showed 75% 1-year overall survival rate (2025 data)
- Single agent and combination arms with paclitaxel also being evaluated
- Recruiting across epithelial ovarian, pancreatic, NSCLC, and TNBC

**NCT IDs:**
- [NCT05403554](https://clinicaltrials.gov/study/NCT05403554) — Phase 1, NI-1801 as single agent, + anti-PD-1, + paclitaxel in MSLN+ cancers including ovarian (Recruiting, 70 patients, 7 sites)

**Relevance to PatientOne:**
- Activates innate immune system (macrophages) which ARE present in PatientOne's stroma
- Does not require T-cell infiltration — ideal for immune-excluded/cold TME
- Mesothelin frequently overexpressed in HGSOC
- Combination with pembrolizumab addresses both innate and adaptive immunity
- Platinum-resistant ovarian cancer is a primary study population

**Platform Tool Analysis Approach:**
1. **mcp-spatialtools:** Map MSLN spatial expression (check if in Visium panel); map CD68 (macrophage marker) distribution
2. **mcp-multiomics:** Check MSLN and CD47 RNA/protein levels across tumor samples
3. **mcp-deepcell:** Quantify macrophage density and distribution from imaging (CD68+ cells)
4. **ClinicalTrials.gov MCP** *(external)*: Verify NCT05403554 enrollment status and eligibility criteria
5. **PubMed MCP** *(external)*: Search NI-1801 clinical data and mesothelin-targeting in ovarian cancer

> **Note:** MSLN and CD47 may not be present in PatientOne's synthetic 31-gene Visium panel. If unavailable, check multi-omics RNA data or note as a gene panel limitation.

---

### 3. Ubamatamab (REGN4018) — MUC16 x CD3 Bispecific T-cell Engager

**Developer:** Regeneron Pharmaceuticals
**Mechanism:** Bispecific antibody binding MUC16 (membrane-bound CA-125) on tumor cells and CD3 on T cells, forcing T-cell activation and tumor killing regardless of T-cell receptor specificity. This BiTE (bispecific T-cell engager) approach can activate T cells even in cold tumors where natural tumor recognition is absent.

**Clinical Evidence:**
- **Phase I/II (NCT03564340):** 890-patient study of ubamatamab alone and with cemiplimab in recurrent ovarian cancer, recruiting since 2018
- **Phase I/II (NCT04590326):** REGN5668 (MUC16xCD28) + ubamatamab + cemiplimab combinations, 612 patients
- **Phase II (NCT06787612):** Multi-arm study in platinum-resistant ovarian cancer, 220 patients, combinations with bevacizumab, cemiplimab, PLD (Recruiting 2025)
- Demonstrated T-cell activation in MUC16+ cold tumors in early data

**NCT IDs:**
- [NCT03564340](https://clinicaltrials.gov/study/NCT03564340) — Phase 1/2, ubamatamab ± cemiplimab, recurrent ovarian (Recruiting, 890 patients, 51 sites)
- [NCT04590326](https://clinicaltrials.gov/study/NCT04590326) — Phase 1/2, MUC16xCD28 + ubamatamab combos, MUC16+ malignancies (Recruiting, 612 patients)
- [NCT06787612](https://clinicaltrials.gov/study/NCT06787612) — Phase 2, ubamatamab ± agents, platinum-resistant ovarian (Recruiting, 220 patients)
- [NCT06444880](https://clinicaltrials.gov/study/NCT06444880) — Phase 2, ubamatamab in SMARCB1-deficient MUC16+ malignancies

**Relevance to PatientOne:**
- MUC16 (CA-125) is the most established ovarian cancer biomarker — PatientOne has elevated CA-125
- BiTE mechanism forces T-cell activation in cold tumors regardless of pre-existing immune infiltration
- Platinum-resistant ovarian cancer is a primary study population (NCT06787612)
- Combination with checkpoint inhibitors may provide synergistic benefit
- Largest clinical program of any next-gen immunotherapy for ovarian cancer

**Platform Tool Analysis Approach:**
1. **mcp-spatialtools:** Map MUC16 spatial expression if available in Visium panel; check CD3D, CD3E expression
2. **mcp-multiomics:** Quantify MUC16 RNA/protein levels in tumor vs. stroma
3. **mcp-perturbation (GEARS):** Predict T-cell activation gene changes upon MUC16-CD3 engagement
4. **mcp-mockepic:** Retrieve CA-125 (MUC16) trends from clinical data as proxy for target expression
5. **ClinicalTrials.gov MCP** *(external)*: Check eligibility and recruiting sites for NCT03564340, NCT06787612

---

### 4. IGFBP-2 Vaccine — DNA Plasmid Cancer Vaccine

**Developer:** UW Medicine (University of Washington)
**Mechanism:** DNA plasmid vaccine encoding IGFBP-2 (insulin-like growth factor binding protein 2), a protein overexpressed in many ovarian cancers. The vaccine generates de novo T-cell responses against IGFBP-2-expressing tumor cells, creating long-term immune memory.

**Clinical Evidence:**
- **Phase I (NCT01322802, Completed):** 25 patients with advanced ovarian cancer. >50% of vaccinated patients alive at 8+ years — remarkable long-term survival
- **Phase II (NCT03029611, Terminated):** Concurrent IGFBP-2 vaccination + neoadjuvant chemo in Stage III/IV ovarian cancer. Terminated after 11 patients (enrollment challenges, not safety)
- Durable immune responses detected in Phase I responders

**NCT IDs:**
- [NCT01322802](https://clinicaltrials.gov/study/NCT01322802) — Phase I, IGFBP-2 vaccine in advanced ovarian cancer (Completed, 25 patients)
- [NCT03029611](https://clinicaltrials.gov/study/NCT03029611) — Phase II, IGFBP-2 vaccine + neoadjuvant chemo (Terminated, 11 patients)

**Relevance to PatientOne:**
- Vaccine approach generates new T-cell responses — does not depend on existing infiltration
- Long-term immune memory may provide durable protection against recurrence
- IGFBP-2 overexpression common in HGSOC
- Could be combined with checkpoint inhibitors to enhance vaccine-generated T-cell activity
- Particularly relevant post-debulking surgery as maintenance/adjuvant strategy

**Platform Tool Analysis Approach:**
1. **mcp-multiomics:** Check IGFBP2 RNA and protein expression levels in PatientOne tumor samples
2. **mcp-spatialtools:** Map IGFBP2 spatial expression if available in Visium panel
3. **mcp-genomic-results (fgbio):** Check for IGFBP2 genomic alterations (amplification, overexpression)
4. **ClinicalTrials.gov MCP** *(external)*: Search for next-generation IGFBP-2 vaccine trials
5. **PubMed MCP** *(external)*: Review long-term follow-up data from NCT01322802

> **Note:** IGFBP2 may not be in PatientOne's synthetic 31-gene Visium panel. Check multi-omics RNA data for expression levels.

---

### 5. TIL Therapy — Tumor-Infiltrating Lymphocyte Adoptive Cell Therapy

**Developer:** Multiple academic centers and companies (NCI, Iovance Biotherapeutics, Leiden UMC)
**Mechanism:** Tumor-infiltrating lymphocytes (TILs) are extracted from a tumor biopsy, expanded ex vivo to billions of cells, and re-infused after lymphodepletion. Modern engineered TIL approaches (2025+) use CD28 co-stimulatory domains and IL-15 cytokine support to improve T-cell persistence and anti-tumor activity, even from cold tumors with limited initial infiltration.

**Clinical Evidence:**
- **Phase II NCI (NCT01174121):** TIL + pembrolizumab in metastatic ovarian cancer, 332-patient multi-cancer study (Recruiting, estimated completion 2028)
- **Phase I/II Denmark (NCT03287674, Completed):** TIL + ipilimumab/nivolumab in metastatic ovarian, 7 patients
- **Phase I/II Leiden (NCT04072263):** Adoptive T-cell therapy in recurrent ovarian cancer, 12 patients
- **Phase Ib Toronto (NCT03158935, Completed):** TIL + pembrolizumab in advanced ovarian and melanoma
- **2025 advances:** CD28/IL-15 engineering methods improve TIL expansion from cold tumors and in vivo persistence

**NCT IDs:**
- [NCT01174121](https://clinicaltrials.gov/study/NCT01174121) — Phase II, TIL + pembrolizumab, metastatic ovarian and other cancers (Recruiting, NCI, 332 patients)
- [NCT03287674](https://clinicaltrials.gov/study/NCT03287674) — Phase I/II, TIL + ipilimumab/nivolumab, metastatic ovarian (Completed)
- [NCT04072263](https://clinicaltrials.gov/study/NCT04072263) — Phase I/II, adoptive T-cell therapy, recurrent ovarian (Leiden UMC)
- [NCT03158935](https://clinicaltrials.gov/study/NCT03158935) — Phase Ib, TIL + pembrolizumab, advanced ovarian (Completed)

**Relevance to PatientOne:**
- Can recover tumor-reactive T cells even from immune-excluded tumors
- PatientOne has CD8+ T cells at tumor periphery/stroma — these can be harvested for TIL expansion
- Engineered TIL with CD28/IL-15 improvements may overcome exhaustion markers
- Combination with checkpoint inhibitors prevents re-exhaustion after infusion
- NCI Phase II (NCT01174121) is actively recruiting for metastatic ovarian cancer

**Platform Tool Analysis Approach:**
1. **mcp-spatialtools:** Map CD8A, CD8B, GZMB (granzyme B) expression at tumor periphery — identifies TIL harvest site
2. **mcp-deepcell:** Quantify CD8+ cell density in stroma vs. tumor; assess TIL harvest feasibility
3. **mcp-quantum-celltype-fidelity:** Assess T-cell exhaustion markers (PDCD1, LAG3, HAVCR2/TIM3, TIGIT) to predict TIL quality
4. **mcp-perturbation (GEARS):** Predict gene expression changes after TIL + checkpoint combination
5. **ClinicalTrials.gov MCP** *(external)*: Check NCT01174121 eligibility criteria and recruiting sites

---

## Platform Tool Availability

### Tool Categories for Immunotherapy Research

| Tool | Type | Server | Immunotherapy Use |
|------|------|--------|-------------------|
| **Spatial expression mapping** | Built-in | mcp-spatialtools | Map immune markers, checkpoint ligands, target antigens across tissue |
| **Perturbation prediction** | Built-in | mcp-perturbation (GEARS) | Predict treatment response, immune activation |
| **Cell type fidelity** | Built-in | mcp-quantum-celltype-fidelity | Assess T-cell states, exhaustion, activation |
| **Multi-omics integration** | Built-in | mcp-multiomics | Check target RNA/protein expression levels |
| **Cell segmentation** | Built-in | mcp-deepcell | Quantify immune cell density and distribution |
| **Image analysis** | Built-in | mcp-openimagedata | Analyze IF/MxIF immune staining |
| **Genomic analysis** | Built-in | mcp-fgbio | Check genomic alterations in immunotherapy targets |
| **Clinical data** | Built-in | mcp-mockepic | Retrieve biomarkers (CA-125/MUC16), treatment history |
| **TCGA comparison** | Built-in | mcp-mocktcga | Compare immune profiles to TCGA ovarian cohort |
| **Clinical trial search** | External MCP | ClinicalTrials.gov MCP | Search recruiting trials, check eligibility |
| **Literature search** | External MCP | PubMed MCP | Find clinical evidence, review articles |
| **Mutation analysis** | Future work | cBioPortal MCP | Cross-reference mutations across cancer cohorts |
| **Reasoning chains** | Future work | SequentialThinking MCP | Multi-step treatment decision reasoning |

**Built-in servers** are part of the Precision Medicine MCP platform and available in Claude Desktop when configured.

**External MCP tools** (ClinicalTrials.gov, PubMed) are available as separate MCP servers in Claude Desktop and Claude Code — they are not bundled with the platform but can be added to `claude_desktop_config.json`.

**Future work** tools (cBioPortal, SequentialThinking) are planned but not yet implemented.

---

## Decision Framework for PatientOne

### Therapy-to-Patient Matching

| Therapy | Cold TME | BRCA1 Mutation | Platinum Resistance | Target Expression | Overall Fit |
|---------|----------|----------------|--------------------|--------------------|-------------|
| **Cadonilimab** | ★★★ Dual checkpoint may convert cold→hot | ★★ BRCA1 increases neoantigens | ★★★ Active in resistant disease | ★★ Requires PD-1/CTLA-4 on T cells | **High** |
| **NI-1801** | ★★★ Bypasses T-cell requirement (innate) | ★ Independent of BRCA | ★★★ Active in platinum-resistant | ★★★ MSLN common in HGSOC | **High** |
| **Ubamatamab** | ★★★ Forces T-cell activation in cold tumors | ★ Independent of BRCA | ★★★ Phase 2 in platinum-resistant | ★★★ MUC16/CA-125 highly expressed | **Very High** |
| **IGFBP-2 Vaccine** | ★★ Generates new responses, slow onset | ★ Independent of BRCA | ★ Better as maintenance | ★★ IGFBP2 common in HGSOC | **Moderate** |
| **TIL Therapy** | ★★★ Recovers T cells from periphery | ★★ BRCA1 tumors have more neoantigens | ★★ Independent of prior therapy | ★★★ CD8+ present at periphery | **High** |

### Recommended Evaluation Priority

1. **Ubamatamab** — Strongest evidence (largest trials), directly targets CA-125/MUC16, designed for platinum-resistant ovarian
2. **NI-1801** — Uniquely addresses cold TME via innate immunity, promising early survival data
3. **Cadonilimab** — Dual checkpoint may overcome PD-L1-low limitation, active ovarian trials
4. **TIL Therapy** — Personalized approach, NCI trial recruiting, requires specialized centers
5. **IGFBP-2 Vaccine** — Long-term potential, better suited as maintenance after initial response

---

## References

### Clinical Trial References (Verified via ClinicalTrials.gov MCP)

| NCT ID | Therapy | Phase | Status |
|--------|---------|-------|--------|
| [NCT06560112](https://clinicaltrials.gov/study/NCT06560112) | Cadonilimab + AK112, recurrent ovarian | Phase II | Recruiting |
| [NCT06940921](https://clinicaltrials.gov/study/NCT06940921) | Cadonilimab + radiation, advanced ovarian | Phase I/II | Active |
| [NCT05403554](https://clinicaltrials.gov/study/NCT05403554) | NI-1801 ± pembrolizumab ± paclitaxel, MSLN+ cancers | Phase 1 | Recruiting |
| [NCT03564340](https://clinicaltrials.gov/study/NCT03564340) | Ubamatamab ± cemiplimab, recurrent ovarian | Phase 1/2 | Recruiting |
| [NCT04590326](https://clinicaltrials.gov/study/NCT04590326) | REGN5668 + ubamatamab combos, MUC16+ cancers | Phase 1/2 | Recruiting |
| [NCT06787612](https://clinicaltrials.gov/study/NCT06787612) | Ubamatamab multi-arm, platinum-resistant ovarian | Phase 2 | Recruiting |
| [NCT01322802](https://clinicaltrials.gov/study/NCT01322802) | IGFBP-2 vaccine, advanced ovarian | Phase I | Completed |
| [NCT03029611](https://clinicaltrials.gov/study/NCT03029611) | IGFBP-2 vaccine + neoadjuvant chemo, ovarian | Phase II | Terminated |
| [NCT01174121](https://clinicaltrials.gov/study/NCT01174121) | TIL + pembrolizumab, metastatic ovarian | Phase II | Recruiting |
| [NCT03287674](https://clinicaltrials.gov/study/NCT03287674) | TIL + ipilimumab/nivolumab, metastatic ovarian | Phase I/II | Completed |

### Related PatientOne Documentation

- **[PatientOne Quick Start Guide](./README.md)** — Complete patient overview and workflow
- **[Data Modes Guide](./data-modes-guide.md)** — DRY_RUN vs. Actual Data configuration
- **[TEST 5: Integration](./test-prompts/DRY_RUN/test-5-integration.md)** — Integrated analysis including immunotherapy recommendations
- **[Prompt Library: Clinical & Genomic](../../prompts/clinical-genomic.md)** — Prompt 17: Immunotherapy targets
- **[Prompt Library: Workflows](../../prompts/workflows.md)** — Section 5b: Immunotherapy research workflow
- **[Prompt Library README](../../prompts/README.md)** — Full prompt index

---

**NCT IDs Verified:** Via ClinicalTrials.gov MCP (February 2026)
**Data:** All analysis approaches reference PatientOne synthetic data (PAT001-OVC-2025)
