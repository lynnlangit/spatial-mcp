# For Educators & Students

**This section is for:** Professors, instructors, students, and anyone teaching or learning precision medicine, bioinformatics, or computational biology.

---

## What You Can Accomplish Here

```mermaid
graph LR
    A["📋 Prepare<br/>synthetic data, no IRB"] --> B["🎓 Teach<br/>case studies"] --> C["🧪 Practice<br/>AI-assisted research"] --> D["📄 Publish<br/>educational materials"]

    style A fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style B fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style C fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style D fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
```

> **Prepare:** 100% synthetic data, no IRB needed, DRY_RUN mode ~$0.32/analysis | **Teach:** Real-world precision medicine case studies and bioinformatics workflows | **Practice:** Natural language → diff expression, pathway enrichment, spatial analysis | **Publish:** No patient privacy concerns — safe for papers, demos, sharing

---

## Why This Is Perfect for Teaching

### 100% Synthetic Data
- **No patient privacy concerns** - Safe for classroom use, public demos, publications
- **No IRB approval needed** - Freely shareable with students
- **Realistic but synthetic** - Clinically plausible scenarios without real PHI
- **Three patient datasets available:** (see [PatientOne Profile](../reference/shared/patientone-profile.md) for full details)
  - **PAT001-OVC-2025:** 58-year-old with Stage IV ovarian cancer (BRCA1+, platinum-resistant) — oncology pipeline, all 5 stages
  - **PAT002-BC-2026:** Stage IIA breast cancer (BRCA2+, ER+/PR+/HER2−) — cross-cancer validation; tests architecture generalizability
  - **PAT003-CVD-2026:** 67-year-old post-menopausal female, preventive cardiovascular health — cardiometabolic pipeline; teaches risk algorithm comparison, gap analysis, and the clinical value of a negative genetic screening result

> **Teaching note (v17):** PAT003 is particularly effective for introducing students
> to the concept of *evidence gaps* — the negative Helix Tier 1 genetic screen result
> is not "nothing"; it shifts the clinical question from variant discovery to
> polygenic risk quantification. Pairs well with a discussion of why Lp(a), APOE,
> and CAC score are absent from standard screening panels.

### Low Cost for Education
- **DRY_RUN mode:** ~$0.32 per student per case (synthetic data, no API costs)
- **Classroom pricing:** 20 students × $0.32 = **$6.40 per class session** (single case). Running all three cases (PAT001 + PAT002 + PAT003) for 20 students costs ~$19.20
- **Semester course:** 15 sessions × 20 students = **$96 total**
- **Compare to:** Commercial platforms ($500-2,000 per student)
- See [Cost Analysis](../reference/shared/cost-analysis.md) and [DRY_RUN Mode Guide](../reference/shared/dry-run-mode.md) for details

### Comprehensive Coverage
All major bioinformatics domains in one platform:
- Clinical data (FHIR standards)
- Genomics (VCF variant calling)
- Multi-omics (RNA, protein, phospho integration)
- Spatial transcriptomics (Visium analysis)
- Imaging (H&E, multiplex IF)
- AI orchestration (natural language queries)
- Cloud deployment (GCP, Docker, serverless)

### Well-Documented
- Step-by-step tutorials with expected outputs
- Example prompts for common analyses
- Architecture diagrams showing data flow
- Statistical methods fully explained
- Reproducible workflows

---

## Quick Start for Instructors

### 1. Set Up Class Environment (30-60 minutes)

**Option A: Claude Code CLI (Recommended for study groups and workshops)**
```bash
# Prerequisites: Python 3.11+, git, Node.js 18+
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Clone and start exploring
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp
claude    # Launch Claude Code — it reads CLAUDE.md automatically
```
Students can explore the codebase, run tests, and ask questions in the terminal. Time: 5-10 minutes per student.

**Option B: Cloud-Based (Recommended for large classes)**
```bash
# Deploy to GCP with DRY_RUN mode (synthetic data)
./infrastructure/deployment/deploy_to_gcp.sh --development

# Students access via web interface (Streamlit UI)
# No local installation needed
```

**Option C: Claude Desktop GUI (Best for non-technical users)**
```bash
# Students install Claude Desktop locally
# Follow installation guide: docs/getting-started/installation.md
# Time: 10-15 minutes per student
```

**Option D: Gemini in VSCode (For teams without Claude access)**
```bash
# For organizations with Google Gemini licenses but no Claude approval
# Students use VSCode + Gemini Code Assist extension with MCP servers
# Follow Gemini setup guide: docs/getting-started/gemini-setup.md
# IMPORTANT: Students must enable "Agent Mode" in the Gemini panel
# Time: 10-15 minutes per student
```

### 2. Assign PatientOne Case Study (25-35 minutes)

**Case:** PAT001-OVC-2025 - 58-year-old female, Stage IV HGSOC, platinum-resistant

**Learning objectives:**
- Interpret clinical FHIR data
- Analyze genomic variants (TP53, BRCA1)
- Integrate multi-omics datasets
- Perform spatial transcriptomics analysis
- Generate treatment recommendations

**Student deliverable:**
- Written report with:
  - Clinical summary
  - Genomic findings
  - Pathway analysis results
  - Treatment recommendations with rationale
  - Visualizations (plots, heatmaps)

**See:** [PatientOne Guide](../reference/testing/patient-one/README.md)

### 3. Assess Student Work

**Rubric categories:**
- Clinical interpretation (20%) - Correct understanding of FHIR data
- Genomic analysis (20%) - Variant identification and interpretation
- Pathway analysis (20%) - Correct statistical methods and interpretation
- Integration (20%) - Synthesis across modalities
- Presentation (20%) - Clear visualizations and reporting

---

## Quick Start for Students

### 1. Install & Setup (5-15 minutes)

Follow: [Installation Guide](../getting-started/installation.md)

**What you'll install (pick one):**
- **Claude Code** (CLI, recommended) — explore and run tests from your terminal
- **Claude Desktop** (GUI) — visual interface for running analyses
- **Gemini in VSCode** — for teams with Gemini licenses ([setup guide](../getting-started/gemini-setup.md))
- **Streamlit UI** (cloud) — browser-based, no local install needed

### 2. Try Your First Analysis (5 minutes)

**Prompt:**
```
What clinical data is available for PatientOne (PAT001-OVC-2025)?
```

**Expected output:**
- Demographics: 58-year-old female
- Diagnosis: Stage IV High-Grade Serous Ovarian Carcinoma (HGSOC)
- Treatment history: Platinum-based chemotherapy (carboplatin + paclitaxel)
- Biomarkers: Elevated CA-125
- Genetic: BRCA1 germline variant

### 3. Complete PatientOne Workflow (25-35 minutes)

Follow: [PatientOne Guide](../reference/testing/patient-one/README.md)

**What you'll learn:**
- Load and interpret clinical data
- Analyze genomic variants
- Integrate multi-omics datasets
- Perform spatial pathway enrichment
- Generate treatment recommendations

**Cost:** ~$0.32 (using DRY_RUN mode with synthetic data)

---

## Educational Topics Covered

### Bioinformatics Fundamentals
- **Data formats:** FHIR, VCF, CSV matrices, Visium spatial format
- **Quality control:** VCF validation, expression matrix QC
- **Normalization:** Batch correction, log transformation
- **Visualization:** Heatmaps, volcano plots, spatial maps

### Statistical Methods
- **Differential expression:** Mann-Whitney U test
- **Multiple testing:** Benjamini-Hochberg FDR correction
- **Pathway enrichment:** Fisher's exact test
- **Spatial statistics:** Moran's I spatial autocorrelation
- **Meta-analysis:** Stouffer's Z-score method
- **Effect sizes:** Log2 fold change, odds ratios

### Precision Medicine Workflows
- **Clinical → Genomic integration:** FHIR + VCF analysis
- **Multi-modal analysis:** RNA + Protein + Spatial
- **Treatment matching:** Pathway → Drug recommendations
- **Biomarker discovery:** Differential expression → Validation
- **Tumor microenvironment:** Spatial transcriptomics + Imaging

### AI & Orchestration
- **Natural language queries:** Prompting best practices
- **Tool composition:** Chaining multiple bioinformatics tools
- **Error handling:** Interpreting and fixing errors
- **Workflow design:** Building reproducible pipelines

### Cloud & DevOps
- **Serverless deployment:** GCP Cloud Run
- **Containerization:** Docker basics
- **API design:** RESTful APIs, MCP protocol
- **Cost optimization:** DRY_RUN mode, caching strategies

---

## Classroom Activities

### Activity 1: PatientOne Case Study (1-2 class sessions)

**Format:** Individual or group (2-3 students)

**Time:** 25-35 minutes analysis + 30-60 minutes report writing

**Assignment:**
1. Analyze PatientOne using platform
2. Write clinical report with treatment recommendations
3. Present findings to class (5-minute presentation)

**Learning outcomes:**
- Interpret multi-modal cancer data
- Apply statistical methods correctly
- Communicate findings to non-technical audience

### Activity 2: Compare Real vs. Synthetic Data (1 class session)

**Format:** Class discussion

**Time:** 50-75 minutes

**Assignment:**
1. Run PatientOne in DRY_RUN mode (synthetic data)
2. Review real data examples (instructor provides)
3. Discuss differences and limitations

**Learning outcomes:**
- Understand data synthesis methods
- Recognize limitations of synthetic data
- Appreciate importance of real data validation

### Activity 3: Design Custom Workflow (1-2 class sessions)

**Format:** Group project (3-4 students)

**Time:** 2-3 hours

**Assignment:**
1. Choose research question (e.g., "Identify biomarkers for platinum resistance")
2. Design workflow using available tools
3. Test with PatientOne data
4. Present workflow design and results

**Learning outcomes:**
- Plan bioinformatics analyses
- Chain tools into workflows
- Document reproducible methods

### Activity 4: Real-World Data with External Connectors (Advanced, 1 class session)

**Format:** Individual or group (2-3 students)

**Time:** 45-60 minutes

**Assignment:**
1. Enable external connectors (PubMed, bioRxiv, ClinicalTrials.gov) — see [Connect External MCP Servers](../for-researchers/CONNECT_EXTERNAL_MCP.md)
2. Search PubMed for papers related to PatientOne's mutations (TP53, BRCA1, PIK3CA)
3. Find recruiting clinical trials for platinum-resistant ovarian cancer
4. Compare PatientOne findings to real TCGA data via cBioPortal

**Learning outcomes:**
- Understand the difference between synthetic (mock) and real data sources
- Use literature search in a research workflow
- Connect AI-orchestrated analysis to real-world evidence

### Activity 5: Extend Platform (Advanced, 2-3 class sessions)

**Format:** Individual project

**Time:** 4-8 hours

**Assignment:**
1. Identify missing functionality (e.g., "Add metabolomics analysis")
2. Implement new server using boilerplate template
3. Write tests (≥35% coverage)
4. Document new tools

**Learning outcomes:**
- Software engineering best practices
- API design and implementation
- Testing and documentation

**See:** [Add New Modality Server Guide](../for-developers/ADD_NEW_MODALITY_SERVER.md)

---

## Course Integration Ideas

### Undergraduate Courses

**Bioinformatics 101:**
- Module 1: Introduction to genomic data formats (VCF, FASTA)
- Module 2: Differential expression analysis
- Module 3: Pathway enrichment
- **Use PatientOne:** As running example throughout course

**Precision Medicine:**
- Week 1-2: Clinical data standards (FHIR)
- Week 3-4: Genomic variant interpretation
- Week 5-6: Multi-omics integration
- Week 7-8: Spatial transcriptomics
- **Final project:** Complete PatientOne analysis with report

**Data Science for Biology:**
- Topic: Multi-modal data integration
- Dataset: PatientOne (5 modalities)
- Methods: PCA, clustering, meta-analysis
- **Lab:** Integrate PatientOne RNA + Protein + Spatial data

### Graduate Courses

**Computational Biology:**
- Advanced topic: AI orchestration in bioinformatics
- Assignment: Design and implement custom workflow
- **Capstone:** Extend platform with new server (metabolomics, single-cell, etc.)

**Translational Research:**
- Case study: Ovarian cancer precision medicine
- Data: PatientOne multi-modal dataset
- Outcome: Treatment recommendation report
- **Presentation:** Molecular tumor board simulation

**Cloud Computing for Bioinformatics:**
- Architecture: MCP protocol, serverless computing
- Deployment: GCP Cloud Run, Docker
- Cost optimization: DRY_RUN mode, caching
- **Project:** Deploy and scale bioinformatics pipeline

---

## Assessment Ideas

### Formative Assessments

**1. Quick Checks (5-10 minutes each)**
- "What is a VCF file? What information does it contain?"
- "Explain the difference between p-value and FDR-corrected p-value"
- "Why do we use batch correction in spatial transcriptomics?"

**2. Prompt Engineering Exercises (15-20 minutes)**
- "Write a prompt to identify upregulated genes in tumor vs. normal"
- "Critique this prompt: [bad example]. How would you improve it?"

**3. Error Debugging (20-30 minutes)**
- Provide error message, ask students to diagnose and fix
- Example: "FileNotFoundError: /data/patient-001/spatial/data.csv"

### Summative Assessments

**1. PatientOne Analysis Report (Individual, 2-3 hours)**

**Grading rubric (100 points):**
- Clinical summary (15 pts)
- Genomic analysis (20 pts)
- Multi-omics integration (20 pts)
- Spatial analysis (20 pts)
- Treatment recommendations (15 pts)
- Visualizations (10 pts)

**2. Literature Review + Replication (Group, 4-6 hours)**

**Assignment:**
- Choose paper using spatial transcriptomics
- Replicate key analysis using platform
- Compare results (synthetic vs. published data)
- Write methods section for reproducibility

**3. Custom Workflow Design (Group, 8-12 hours)**

**Assignment:**
- Define research question
- Design 5-step workflow
- Implement and test with PatientOne
- Document workflow (README, example prompts)
- Present to class (10-minute presentation)

---

## Example Syllabi

### Undergraduate: Introduction to Precision Medicine (8 weeks)

| Week | Topic | Activity | PatientOne Module |
|------|-------|----------|-------------------|
| 1 | Clinical data standards | Explore FHIR resources | Clinical summary |
| 2 | Genomic variants | VCF analysis | Identify TP53, BRCA1 |
| 3 | RNA-seq basics | Differential expression | Upregulated genes |
| 4 | Pathway analysis | Fisher's exact test | Enriched pathways |
| 5 | Multi-omics integration | Stouffer meta-analysis | RNA + Protein |
| 6 | Spatial transcriptomics | Moran's I, cell deconvolution | Spatial patterns |
| 7 | Imaging & AI | Cell segmentation | H&E analysis |
| 8 | Final project | Complete PatientOne report | All modules |

**Learning outcomes:**
- Interpret multi-modal cancer data
- Apply statistical methods correctly
- Generate treatment recommendations
- Communicate findings effectively

### Graduate: Computational Methods in Cancer Biology (12 weeks)

| Week | Topic | Reading | Assignment |
|------|-------|---------|------------|
| 1-2 | AI orchestration in bioinformatics | MCP protocol spec | Setup environment |
| 3-4 | Statistical methods | Mann-Whitney, FDR, Fisher's | PatientOne differential expression |
| 5-6 | Multi-omics integration | HAllA paper | Integrate PatientOne modalities |
| 7-8 | Spatial transcriptomics | Visium tutorial | PatientOne spatial analysis |
| 9-10 | Cloud deployment | GCP Cloud Run docs | Deploy custom server |
| 11-12 | Final project | Literature review | Extend platform with new feature |

**Learning outcomes:**
- Design and implement bioinformatics workflows
- Apply advanced statistical methods
- Deploy scalable cloud infrastructure
- Contribute to open-source bioinformatics

---

## Teaching Resources

### Instructor Materials
- **[PatientOne Guide](../reference/testing/patient-one/README.md)** - Complete walkthrough
- **[Statistical Methods](../for-researchers/README.md)** - Detailed method explanations
- **[Cost Analysis](../reference/shared/cost-analysis.md)** - Budgeting for classroom use

### Student Resources
- **[Installation Guide](../getting-started/installation.md)** - Setup instructions
- **[Quick Start Demo](../for-funders/DEMO_AND_PITCH.md)** - 90-second overview
- **[Architecture Overview](../for-developers/ARCHITECTURE.md)** - System design

---

## Instructor Support

### Contributing Educational Materials
We welcome contributions!
- Lecture slides
- Problem sets
- Video tutorials
- Assessment rubrics
- Course syllabi

**How to contribute:** See [CONTRIBUTING.md](../for-developers/CONTRIBUTING.md)

### Pilot Program
Interested in piloting this platform in your course?



---

## Frequently Asked Questions

### "Is this approved for classroom use?"
**A:** Yes! PatientOne data is 100% synthetic with no patient identifiers. No IRB approval needed for educational use.

### "How much does it cost for a class of 20 students?"
**A:** DRY_RUN mode (synthetic data): ~$6.40 per class session (20 students × $0.32)
Production mode (real data): Requires institutional GCP account and varies by usage.

### "Can students work on their own computers?"
**A:** Yes! Four options: (1) Claude Code CLI for terminal-based exploration, (2) Claude Desktop GUI for visual analysis, (3) Gemini in VSCode for teams with Gemini licenses, or (4) cloud-based Streamlit UI (no local install needed).

### "What if students find bugs or have questions?"
**A:** Students can:
1. Check documentation first
2. Ask in GitHub Discussions
3. Email instructor
4. Open GitHub Issue for bugs

### "Can I modify the PatientOne case study?"
**A:** Yes! Synthetic data is fully customizable. Contact the maintainers for guidance on creating custom cases.

### "Is this suitable for high school students?"
**A:** Yes for advanced high school (AP Biology, AP Computer Science). Requires basic biology knowledge and comfort with technology. Instructor guidance recommended.

### "What if my institution blocks Claude Desktop?"
**A:** Use Claude Code (CLI-based, runs in terminal), the cloud-based Streamlit UI (browser-accessible, deployed on GCP), or switch to Gemini — see the [Gemini Setup Guide](../getting-started/gemini-setup.md). All MCP servers work with both Claude and Gemini.

### "My institution only has Gemini licenses, not Claude. Can we still use this?"
**A:** Yes! All MCP servers work with Gemini. Follow the [Gemini Setup Guide](../getting-started/gemini-setup.md). The key difference: enable **Agent Mode** in VSCode so Gemini actually calls tools instead of describing them. The student Streamlit app (`ui/streamlit-app-students/`) is also Gemini-native.

---


**Related Resources:**
- 🔬 [Researcher Guide](../for-researchers/README.md) - For bioinformatics details
- 💻 [Developer Guide](../for-developers/README.md) - For extending the platform
- 💰 [Funding Information](../for-funders/README.md) - For grant applications
- 🏠 [Back to Main Documentation](../INDEX.md)

---

**Last Updated:** 2026-02-16
