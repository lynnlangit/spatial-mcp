# Precision Medicine Platform Glossary

For educators and students. Each term includes a plain-English definition followed by a technical note. Terms are grouped by domain and alphabetized within each group.

Last reviewed: May 9, 2026. Suggest corrections via GitHub issue.

---

## Genomics & Mutations

### BRCA1/BRCA2

**Plain English:** BRCA1 and BRCA2 are genes that help repair damaged DNA. When a person inherits a broken copy (germline mutation), their cells accumulate DNA damage more quickly, raising cancer risk — especially for breast and ovarian cancer. Importantly, tumors with BRCA mutations are often vulnerable to PARP inhibitors.

**Technical note:** BRCA1 (chr17q21) and BRCA2 (chr13q13) encode proteins essential for homologous recombination repair. Germline pathogenic variants confer PARP inhibitor eligibility regardless of HRD score per OlympiA/SOLO-1 trial criteria.

### HGSOC

**Plain English:** High-Grade Serous Ovarian Cancer is the most common and most lethal subtype of ovarian cancer. It typically presents at advanced stage and is the primary oncology use case for this platform (PAT001).

**Technical note:** HGSOC accounts for ~70% of epithelial ovarian cancers and is characterized by near-universal TP53 mutation, frequent BRCA1/2 alterations, and extensive genomic instability (copy number changes).

### HRD

**Plain English:** Homologous Recombination Deficiency is a measure of how broken a cancer cell's DNA-repair machinery is. A higher score means the cell has more trouble fixing its own DNA, which paradoxically makes it more vulnerable to certain drugs (PARP inhibitors) that exploit this weakness.

**Technical note:** HRD score is a composite of three genomic scar signatures (LOH, TAI, LST); a score above 42 is generally considered clinically significant for PARP inhibitor sensitivity.

### myChoice CDx

**Plain English:** myChoice CDx is a laboratory test made by Myriad Genetics that measures a tumor's HRD score. An HRD score of 42 or above is the FDA-approved threshold for PARP inhibitor eligibility — but germline BRCA status can independently qualify a patient regardless of this score.

**Technical note:** myChoice CDx is an FDA-approved companion diagnostic that combines tumor BRCA1/2 sequencing with a genomic instability score (GIS) derived from LOH, TAI, and LST. PAT002 (HRD 35) illustrates the clinical nuance: below the 42-point threshold but PARP-eligible via germline BRCA2.

### PARP inhibitor

**Plain English:** PARP inhibitors are a class of cancer drugs (including olaparib and niraparib) that block a DNA-repair enzyme called PARP. In cells that already have broken DNA repair (like BRCA-mutant cancers), blocking PARP too creates an overload of damage that kills the cancer cell — a strategy called "synthetic lethality."

**Technical note:** PARP (poly ADP-ribose polymerase) mediates single-strand break repair. Inhibition in HRD-positive or BRCA-mutant cells forces reliance on error-prone repair pathways, leading to genomic catastrophe and apoptosis.

### PIK3CA

**Plain English:** PIK3CA is a gene that, when mutated, can drive cancer growth by overactivating a cell-growth signaling pathway. The H1047R mutation in PIK3CA is common in ER+ breast cancer and determines eligibility for PI3K inhibitors like inavolisib.

**Technical note:** PIK3CA encodes the p110α catalytic subunit of PI3-kinase. The H1047R hotspot mutation constitutively activates PI3K/AKT/mTOR signaling. Inavolisib received FDA approval in 2024 for PIK3CA-mutant ER+/HER2− breast cancer, superseding earlier PI3K inhibitors (alpelisib) for this genotype.

### POLE

**Plain English:** POLE is a gene encoding a DNA-copying enzyme. When POLE itself is mutated, the cell makes many more copying errors than normal, inflating the TMB count. POLE-corrected TMB adjusts for this, distinguishing true immune-relevant hypermutation from a faulty copy machine.

**Technical note:** POLE (DNA polymerase epsilon) proofreading domain mutations (e.g., P286R, V411L) cause an ultramutator phenotype (TMB often > 100 mut/Mb). PAT001's POLE-corrected TMB of 47.3 mut/Mb reflects this adjustment.

### Somatic vs germline mutation

**Plain English:** A germline mutation is inherited from a parent and present in every cell of the body. A somatic mutation arises only in specific cells (like a tumor) during a person's lifetime. The distinction matters clinically: germline BRCA2 affects PARP eligibility; somatic PIK3CA H1047R affects PI3K inhibitor selection.

**Technical note:** Germline variants are detected in paired tumor-normal sequencing by their presence in the normal sample at ~50% variant allele frequency. Somatic variants are tumor-specific and absent from the normal comparator.

### TMB

**Plain English:** Tumor Mutational Burden counts how many mutations exist in a region of the cancer's DNA. Cancers with lots of mutations sometimes respond better to immunotherapy because the immune system has more "targets" to recognize.

**Technical note:** TMB is expressed as mutations per megabase (mut/Mb) of sequenced DNA; thresholds vary by assay, but 10 mut/Mb is a common cutoff for "TMB-high." POLE correction is necessary when polymerase proofreading mutations inflate the raw count.

---

## Immunology & Tumor Microenvironment

### CAF

**Plain English:** Cancer-Associated Fibroblasts are support cells that tumors recruit to build a protective environment around themselves. CAFs can shield the tumor from immune attack and promote drug resistance. Disrupting CAFs (e.g., via NNMT inhibition) is a strategy to make tumors more vulnerable.

**Technical note:** CAFs produce extracellular matrix, secrete immunosuppressive cytokines (TGF-β, IL-6), and remodel the stroma to exclude T cells. CAF fraction is estimated by deconvolution tools (CIBERSORTx) and perturbation models (GEARS) predict the effect of CAF-targeting interventions.

### CD8+ T cell

**Plain English:** CD8+ T cells (also called cytotoxic T lymphocytes) are immune cells that directly kill cancer cells by recognizing foreign proteins on their surface. Higher CD8+ T cell counts in a tumor generally indicate the immune system is actively fighting the cancer.

**Technical note:** CD8+ CTLs recognize peptide-MHC-I complexes via their T-cell receptor and kill target cells through perforin/granzyme pathways. Spatial distribution (clustered vs excluded) may predict checkpoint immunotherapy response.

### Checkpoint blockade

**Plain English:** Checkpoint blockade is an immunotherapy strategy that removes the "brakes" cancer puts on the immune system. Drugs like anti-PD-1 and anti-CTLA-4 antibodies release these brakes, allowing T cells to attack the tumor.

**Technical note:** Immune checkpoints (PD-1/PD-L1, CTLA-4) are inhibitory receptors that normally prevent autoimmunity. Tumors co-opt these pathways to evade immune destruction. Monoclonal antibodies (pembrolizumab, nivolumab, ipilimumab) block these interactions to restore anti-tumor immunity.

### HLA

**Plain English:** Human Leukocyte Antigen genes determine which protein fragments a person's immune cells can "see." Everyone has a different set of HLA alleles, which means the same mutation may produce an immune-visible neoantigen in one patient but not another.

**Technical note:** HLA class I genes (HLA-A, -B, -C) encode MHC-I molecules. Allele-specific binding prediction (e.g., NetMHCpan) determines which mutant peptides are presented. PAT001 is HLA-A*02:01; PAT002 carries HLA-A*02:01 and HLA-A*03:01.

### IC50

**Plain English:** IC50 tells you how tightly a molecule (like a neoantigen peptide) binds to its target. A lower number means stronger binding. For cancer vaccines, lower IC50 values mean the immune system is more likely to notice and attack that peptide.

**Technical note:** IC50 is the half-maximal inhibitory concentration in nM; for MHC-I binding predictions, IC50 < 50 nM is typically classified as a strong binder, 50-500 nM as weak, and > 500 nM as non-binder.

### Immune evasion

**Plain English:** Immune evasion refers to the tricks cancer cells use to hide from or shut down the immune system. The platform calculates an immune evasion score — higher values indicate the tumor is more actively suppressing immune responses.

**Technical note:** Evasion mechanisms include PD-L1 upregulation, MHC-I downregulation, Treg recruitment, and immunosuppressive cytokine secretion. The quantum server's evasion score (0–1 scale) integrates multiple evasion signals; PAT002 scored 0.41, indicating partial immune engagement despite ER+ BC's conventionally cold phenotype.

### MHC-I

**Plain English:** Major Histocompatibility Complex class I is a display shelf on the surface of every cell in your body. It holds up small pieces of proteins for immune cells to inspect. If an immune cell sees a foreign fragment (like a neoantigen), it can trigger an attack on that cell.

**Technical note:** MHC-I molecules (encoded by HLA-A, -B, -C genes in humans) present endogenous peptides to CD8+ cytotoxic T lymphocytes; allele-specific binding affinity determines which peptides are presented.

### Neoantigen

**Plain English:** A neoantigen is a tiny piece of a mutated protein that appears on the surface of a cancer cell. Because it comes from a mutation, the immune system can potentially recognize it as foreign and attack the cancer cell.

**Technical note:** Neoantigens are peptide fragments (typically 8-11 amino acids for MHC-I) generated from somatic mutations, presented via MHC molecules, and recognized by T-cell receptors.

### Tumor microenvironment (TME)

**Plain English:** The tumor microenvironment is the cellular neighborhood surrounding and within a tumor. It includes immune cells, fibroblasts, blood vessels, and signaling molecules. The composition of the TME strongly influences whether immunotherapy will work.

**Technical note:** TME characterization uses deconvolution (CIBERSORTx), spatial transcriptomics (Visium), and cell classification to quantify immune infiltration, stromal content, and spatial organization. Immune-inflamed vs immune-excluded vs immune-desert phenotypes have distinct therapeutic implications.

---

## Spatial Biology

### CIBERSORTx

**Plain English:** CIBERSORTx is a computational tool that estimates the proportions of different immune and stromal cell types in a tissue sample from gene expression data alone — without physically separating the cells.

**Technical note:** CIBERSORTx uses nu-support vector regression with the LM22 signature matrix (22 immune cell types) to deconvolve bulk or spatial gene expression into cell-type fractions. It extends the original CIBERSORT with batch correction for cross-platform compatibility.

### Deconvolution

**Plain English:** Deconvolution is a computational technique that takes a mixed signal from a tissue sample and figures out what cell types are present and in what proportions. It is like hearing a choir and working out how many sopranos, altos, tenors, and basses are singing.

**Technical note:** Immune deconvolution (e.g., CIBERSORTx with LM22 signature matrix) uses constrained linear regression or support vector regression to infer cell-type fractions from bulk or spatial gene expression data.

### Moran's I

**Plain English:** Moran's I is a number that tells you whether nearby spots in a tissue have similar gene activity (clustered), different activity (dispersed), or no pattern (random). Values near zero mean random; positive means clustered; negative means dispersed.

**Technical note:** Moran's I is a spatial autocorrelation statistic ranging from -1 (perfect dispersion) to +1 (perfect clustering), with an expected value of -1/(n-1) under the null hypothesis of spatial randomness.

### Spatial transcriptomics

**Plain English:** Spatial transcriptomics is a technique that measures which genes are active in a tissue sample while preserving the physical location of each measurement. Think of it as creating a map where each pin shows what genes are turned on at that exact spot in the tissue.

**Technical note:** Technologies like 10x Visium capture mRNA at spatially barcoded spots (~55 um diameter, ~5,000 spots per capture area), enabling spatially resolved gene expression profiling.

### Visium

**Plain English:** Visium is a spatial transcriptomics product made by 10x Genomics. A thin tissue slice is placed on a special slide with thousands of barcoded spots. Each spot captures the RNA from the cells above it, producing a gene-expression map of the tissue.

**Technical note:** Visium v1 slides contain ~5,000 barcoded spots of 55 µm diameter with 100 µm center-to-center spacing. The platform's spatial server processes Visium outputs (filtered feature matrix, tissue positions, spatial images) for downstream analysis.

---

## Computational Methods

### GEARS

**Plain English:** GEARS is a machine-learning model that predicts how cells will behave when specific genes are knocked out. It can forecast the effect of gene combinations that have never been tested in a lab, helping researchers prioritize which experiments to run.

**Technical note:** GEARS (Graph-Enhanced Gene Activation and Repression Simulator) is a GNN (graph neural network) model by Roohani et al. (2023) that leverages gene-gene interaction graphs to predict combinatorial perturbation outcomes from single-gene Perturb-seq training data.

### Perturbation

**Plain English:** A perturbation is a deliberate change made to a biological system to see what happens. In this platform, we simulate what would happen if specific genes were knocked down (turned off) in cancer cells, to predict whether that change would make the cancer more treatable.

**Technical note:** In silico perturbation prediction uses graph neural networks (e.g., GEARS) trained on Perturb-seq data to predict post-perturbation gene expression shifts without wet-lab experiments.

### Quantum circuit

**Plain English:** A quantum circuit is a sequence of operations on quantum bits (qubits) that processes information using quantum physics. In this platform, quantum circuits are used to classify cell types, potentially offering advantages for certain pattern-recognition tasks.

**Technical note:** Parameterized quantum circuits (PQCs) use tunable rotation gates (RY, RZ) and entangling gates (CNOT) to embed classical feature vectors into Hilbert space for supervised classification via variational optimization.

### Variational autoencoder

**Plain English:** A variational autoencoder (VAE) is an AI model that learns to compress complex data into a compact summary and then reconstruct it. In biology, VAEs can learn meaningful representations of gene expression data, revealing hidden patterns like cell subtypes.

**Technical note:** A VAE consists of an encoder q(z|x) and decoder p(x|z) trained by maximizing the evidence lower bound (ELBO); the latent space z provides a low-dimensional, continuous embedding of high-dimensional input data.

---

## Cardiovascular & Preventive Health

### APOE

**Plain English:** APOE (apolipoprotein E) is a gene with three common variants (e2, e3, e4). The e4 variant raises risk for both cardiovascular disease and Alzheimer's. APOE is not included in standard population genetic screens like Helix Tier 1, making it a gap the platform flags.

**Technical note:** APOE e4 carriers have elevated LDL cholesterol via reduced hepatic LDL receptor recycling. Homozygous e4/e4 confers ~3x cardiovascular and ~12x Alzheimer's risk. The platform identifies APOE genotyping as a high-priority gap when population screening rules out monogenic FH.

### ASCVD risk

**Plain English:** ASCVD (Atherosclerotic Cardiovascular Disease) risk is a 10-year percentage estimate of heart attack or stroke probability, calculated by the ACC/AHA Pooled Cohort Equations. A score above 7.5% triggers consideration of statin therapy.

**Technical note:** The ACC/AHA PCE (2013, updated 2018) uses age, sex, race, total cholesterol, HDL, SBP, treatment status, diabetes, and smoking. The platform calculates PCE alongside Reynolds and Framingham scores; convergence across algorithms strengthens risk classification. PAT003: 10.3%.

### CAC score

**Plain English:** A Coronary Artery Calcium score is a CT scan measurement of calcium deposits in heart arteries. For patients at intermediate cardiovascular risk, a CAC score of zero can justify deferring statins, while a high score strengthens the case for treatment.

**Technical note:** CAC scoring uses non-contrast cardiac CT with Agatston scoring. Per 2018 ACC/AHA guidelines, CAC is the best-validated reclassification tool for patients in the intermediate-risk range (7.5–20% 10-year ASCVD). The platform flags missing CAC as a gap in PAT003.

### hsCRP

**Plain English:** High-sensitivity C-reactive protein is a blood marker of inflammation. Elevated hsCRP indicates systemic inflammation that may contribute to cardiovascular risk independently of cholesterol levels. The JUPITER trial showed statins benefit patients with hsCRP above 2.0 mg/L.

**Technical note:** hsCRP is measured by high-sensitivity immunoassay (range 0.1–10+ mg/L). The Reynolds Risk Score incorporates hsCRP; the platform notes PAT003's value of 1.8 mg/L as marginally below the 2.0 mg/L JUPITER trial threshold.

### Lp(a)

**Plain English:** Lipoprotein(a) is a cholesterol particle whose blood level is almost entirely determined by genetics and does not respond to standard statin therapy. Elevated Lp(a) is an independent cardiovascular risk factor that most routine lipid panels do not measure.

**Technical note:** Lp(a) contains an LDL-like particle bound to apolipoprotein(a). Levels > 50 mg/dL (~125 nmol/L) double cardiovascular risk. ESC/EAS 2023 guidelines recommend measuring Lp(a) once per lifetime. The platform identifies unmeasured Lp(a) as a primary gap in PAT003.

### Reynolds Risk Score

**Plain English:** The Reynolds Risk Score is a cardiovascular risk calculator designed specifically for women. Unlike other calculators, it includes hsCRP (an inflammation marker) and family history of premature heart disease, which can reclassify women missed by simpler models.

**Technical note:** Developed by Ridker et al. (2007) from the Women's Health Study cohort (n=24,558). Inputs: age, SBP, hsCRP, total cholesterol, HDL, smoking, family history, HbA1c (if diabetic). PAT003 scored 14.3% (intermediate risk).

### Statin

**Plain English:** Statins are cholesterol-lowering drugs that reduce LDL by blocking a liver enzyme (HMG-CoA reductase). They are the most widely prescribed cardiovascular preventive medication. The decision to start a statin depends on risk scores, and can be influenced by CAC, Lp(a), and other factors the platform evaluates.

**Technical note:** Statins reduce LDL by 30–50% and have demonstrated cardiovascular event reduction across primary and secondary prevention trials. The 2018 ACC/AHA guidelines recommend shared decision-making for statin initiation at 7.5–20% 10-year ASCVD risk, with CAC as a tiebreaker.

---

## Platform & Infrastructure

### Clinician-in-the-loop (CITL)

**Plain English:** Clinician-in-the-loop means that every AI-generated result must be reviewed by a qualified clinician who can APPROVE, REVISE, or REJECT it before any clinical action is taken. The AI suggests; the human decides.

**Technical note:** CITL is implemented as a mandatory gate in the patient-report server. All tool outputs include a `requires_review: true` flag. The platform never auto-executes clinical recommendations.

### DRY_RUN mode

**Plain English:** DRY_RUN mode makes every server return realistic-looking but entirely synthetic results, without connecting to external databases or running heavy computations. It is the safe default for teaching, testing, and development.

**Technical note:** Controlled by per-server environment variables (e.g., `FGBIO_DRY_RUN=true`), DRY_RUN mode returns mock payloads that match the live schema, with a `"dry_run": true` flag so callers can distinguish synthetic from real results.

### FastMCP

**Plain English:** FastMCP is a Python framework that makes it easy to build MCP servers. Developers write a Python function, add a decorator, and FastMCP handles all the networking and protocol details so AI assistants like Claude can call that function.

**Technical note:** FastMCP wraps the Model Context Protocol Python SDK, providing `@mcp.tool()` decorators, automatic Pydantic validation, and transport auto-detection (stdio, SSE) for rapid server development.

### FHIR

**Plain English:** Fast Healthcare Interoperability Resources is a standard for exchanging electronic health records. The platform uses FHIR-formatted data (via the mockepic server) to represent clinical information like diagnoses, medications, and lab results.

**Technical note:** FHIR R4 uses RESTful APIs with JSON resources (Patient, Observation, Condition, etc.). The mcp-epic server targets real Epic FHIR R4 endpoints; mcp-mockepic provides synthetic FHIR bundles for development and teaching.

### HIPAA

**Plain English:** The Health Insurance Portability and Accountability Act is the US federal law governing the privacy and security of health information. Any system handling real patient data must comply with HIPAA's rules on access control, encryption, and audit logging.

**Technical note:** HIPAA's Security Rule requires administrative, physical, and technical safeguards for protected health information (PHI). The platform uses de-identified synthetic data (Safe Harbor method) to avoid PHI exposure. See `docs/for-hospitals/compliance/hipaa.md` for the compliance checklist.

### MCP server

**Plain English:** An MCP server is a small program that exposes specific analysis tools over the Model Context Protocol. Each server in this platform handles one domain (genomics, imaging, spatial analysis, etc.) and can be called by an AI assistant using natural language.

**Technical note:** MCP servers implement the Model Context Protocol specification, exposing tools as JSON-RPC endpoints with typed input/output schemas, discoverable by any MCP-compatible client.
