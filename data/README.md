# Data Directory

This directory contains sample data for testing and demonstrating the Precision Medicine MCP servers.

**⚠️ All data is 100% synthetic** - Created for demonstration and testing purposes only.

---

## 🏥 Synthetic Patient Datasets

| Patient ID | Use Case | Key Features | Documentation |
|------------|----------|--------------|---------------|
| **PAT001-OVC-2025** | Stage IV Ovarian Cancer | BRCA1+, platinum-resistant | [📖 Details →](patient-data/PAT001-OVC-2025/README.md) |
| **PAT002-BC-2026** | Stage IIA Breast Cancer | BRCA2+, ER+/PR+/HER2- | [📖 Details →](patient-data/PAT002-BC-2026/README.md) |
| **PAT003-CVD-2026** | Preventive Cardiovascular Health | 65+ female, bilateral CVD family history, controlled hypertension | [📖 Details →](patient-data/PAT003-CVD-2026/README.md) |

---

## PAT001: Stage IV Ovarian Cancer (Patient One)

**Diagnosis:** High-Grade Serous Ovarian Carcinoma, platinum-resistant

**Data modalities:**
- Clinical data (demographics, CA-125 timeline)
- Genomic variants (VCF with BRCA1, TP53, PIK3CA mutations)
- Multi-omics data (RNA-seq, proteomics, phosphoproteomics)
- Spatial transcriptomics (10x Visium, 900 spots, 31 genes)
- Imaging data (H&E, immunofluorescence)

---

## PAT002: Stage IIA Breast Cancer (Patient Two)

**Diagnosis:** ER+/PR+/HER2- Invasive Ductal Carcinoma, BRCA2 germline mutation

**Data modalities:**
- Clinical data (FHIR resources, CEA/CA 15-3 markers)
- Genomic variants (VCF with BRCA2, PIK3CA mutations)
- Multi-omics data (RNA-seq, proteomics, phosphoproteomics - pre/post treatment)
- Spatial transcriptomics (10x Visium, 900 spots, 35 genes)
- Imaging data (H&E, ER/PR/HER2/Ki67 immunofluorescence)
- Perturbation data (PD-1 knockout CRISPR screen)

---

## PAT003: Preventive Cardiovascular Health (Patient Three)

**Profile:** 67-year-old post-menopausal woman with controlled hypertension and bilateral family history of CVD

**Data modalities:**
- Clinical data (lipid panel, glucose metabolism, hsCRP, blood pressure)
- CVD risk genes (APOE, LDLR, ACE, PCSK9, LPA, 9p21 locus)
- Risk scores (Reynolds 14.3%, Framingham 12.0%, ASCVD 10.3%)
- Tier 1 genetic screen (negative for FH, HBOC, Lynch — shifts risk model to polygenic)
- Lifestyle and medication data (lisinopril, Mediterranean diet, exercise)

---


