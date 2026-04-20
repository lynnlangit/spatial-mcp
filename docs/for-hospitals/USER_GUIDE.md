# User Guide - Precision Medicine MCP System
## For Clinicians and Bioinformaticians

**Version:** 1.0
**Last Updated:** 2026-02-25
**Target Users:** Ovarian Cancer Research Team (5 users)

---

## Table of Contents

- [Getting Started](#getting-started)
- [Logging In](#logging-in)
- [Streamlit Chat UI](#streamlit-chat-ui)
- [Jupyter Notebooks](#jupyter-notebooks)
- [Common Workflows](#common-workflows)
- [Understanding Results](#understanding-results)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)
- [Getting Help](#getting-help)

---

## Getting Started

### What is the Precision Medicine MCP System?

The MCP system uses Claude AI to help you analyze spatial transcriptomics and multi-omics data for ovarian cancer patients. It connects to:

- **Epic FHIR** - Clinical data (demographics, diagnoses, labs, medications)
- **Spatial Transcriptomics** - Gene expression with spatial location
- **Multi-Omics** - RNA-seq, proteomics, phosphoproteomics
- **Bioinformatics Tools** - STAR alignment, pathway enrichment, etc.

### Who Can Use It?

- **Clinicians:** Query patient data, understand spatial analyses, interpret results
- **Bioinformaticians:** Run complex analyses, customize workflows, export data

### Requirements

- Hospital email address (@hospital.org)
- Access to hospital VPN (required for remote access)
- Modern web browser (Chrome, Firefox, Edge)
- For Jupyter: Basic Python knowledge helpful but not required

---

## Logging In

### Step 1: Connect to VPN

**If working remotely:**
1. Launch hospital VPN client
2. Enter your hospital credentials
3. Connect to VPN
4. Wait for "Connected" status

**If on hospital network:**
- No VPN needed, skip to Step 2

### Step 2: Access the System

**Option A: Streamlit Chat UI (For Everyone)**
1. Open browser and go to: `https://oauth2-proxy-streamlit-{hash}.run.app`
2. You'll be redirected to Azure AD login
3. Enter your hospital email and password
4. Complete multi-factor authentication if prompted
5. You'll be redirected to the MCP chat interface

**Option B: Jupyter Notebooks (For Bioinformaticians)**
1. Open browser and go to: `https://oauth2-proxy-jupyter-{hash}.run.app`
2. Azure AD login (same as above)
3. You'll see the JupyterLab interface

### Troubleshooting Login

**Problem: "Authentication Required" error**
- Solution: Clear browser cookies and try again
- Solution: Check you're connected to VPN
- Solution: Contact IT if issue persists

**Problem: "Access Denied" after login**
- Solution: Verify you're in the `precision-medicine-users` Azure AD group
- Solution: Contact Hospital IT to request access

**Problem: "Connection Timeout"**
- Solution: Check VPN connection is active
- Solution: Try a different browser
- Solution: Check with IT if servers are down

---

## Streamlit Chat UI

### Interface Overview

```
┌─────────────────────────────────────────────────────┐
│  Precision Medicine MCP Chat          👤 Your Name  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Sidebar:                      Main Chat:           │
│  ┌──────────────┐             ┌─────────────────┐  │
│  │ MCP Servers  │             │ Chat History    │  │
│  │ □ fgbio      │             │                 │  │
│  │ ☑ multiomics │             │ User: ...       │  │
│  │ ☑ spatialtools│             │ Assistant: ... │  │
│  │ ☑ epic       │             │                 │  │
│  │              │             └─────────────────┘  │
│  │ Model        │             ┌─────────────────┐  │
│  │ sonnet-4-6 ▼ │             │ Type message... │  │
│  │              │             └─────────────────┘  │
│  │ Max Tokens   │                                  │
│  │ [=====] 4096 │                                  │
│  └──────────────┘                                  │
└─────────────────────────────────────────────────────┘
```

### Using the Chat Interface

**1. Select MCP Servers (Sidebar)**

Choose which analysis tools to use:

- **fgbio:** Reference genomes, FASTQ validation
- **multiomics:** Multi-omics integration (RNA + protein + phospho)
- **spatialtools:** Spatial transcriptomics analysis
- **epic:** Clinical data from Epic FHIR

**Tip for Clinicians:** Start with `epic + spatialtools` for basic patient queries
**Tip for Bioinformaticians:** Enable all servers for comprehensive analysis

**2. Choose Model (Sidebar)**

- **claude-sonnet-4-6** (Recommended) - Best balance of speed and quality
- **claude-opus-4-6** - Highest quality, slower, more expensive
- **claude-haiku-4-5** - Fastest, most cost-effective

**3. Adjust Max Tokens (Sidebar)**

- Lower (1024): Quick queries, simple answers
- Medium (4096): Standard analyses (recommended)
- Higher (8192): Comprehensive reports, detailed explanations

**4. Type Your Query (Main Area)**

Examples:
```
For patient RESEARCH-PAT001:
1. Get clinical demographics and diagnosis
2. Analyze spatial transcriptomics data
3. Identify platinum resistance markers
```

**5. Review Results**

- Results appear in chat history
- Token usage shown below each response
- Can copy/paste results for reports

### Example Queries

**For Clinicians:**

```
Simple Patient Summary:
"What clinical data do we have for patient RESEARCH-PAT001?"

Spatial Analysis Overview:
"For RESEARCH-PAT001, what are the main cell populations in the tumor?"

Treatment Markers:
"Based on spatial analysis of RESEARCH-PAT001, what markers suggest platinum resistance?"
```

**For Bioinformaticians:**

```
Detailed Analysis:
"For RESEARCH-PAT001, perform cell type deconvolution and differential expression
between tumor core and margin. Report top 20 differentially expressed genes."

Multi-Omics Integration:
"Integrate RNA-seq, proteomics, and phosphoproteomics for RESEARCH-PAT001.
Run HAllA association analysis and identify significant correlations."

Pathway Enrichment:
"For these upregulated genes in RESEARCH-PAT001: [TP53, BRCA1, MYC, KRAS, PTEN],
perform GO_BP pathway enrichment. Filter for p < 0.05."
```

### Tips & Best Practices

**Do:**
- ✅ Be specific about patient IDs
- ✅ Ask follow-up questions to refine results
- ✅ Use "Example Prompts" button for templates
- ✅ Copy important results immediately (chat history is session-based)

**Don't:**
- ❌ Include patient names or identifiable information (use research IDs only)
- ❌ Ask about non-research patients (system only has 100 test patients)
- ❌ Expect real-time results (analyses take 15-45 seconds typically)
- ❌ Run the same query repeatedly (costs add up)

---

## Jupyter Notebooks

### JupyterLab Interface

After logging in, you'll see:

- **File Browser (left):** Your notebooks and files
- **Main Area:** Notebook editing
- **Kernel Status (top right):** Shows if Python is ready

### Using the MCP Client

**1. Open the Example Notebook:**

Click: `mcp_client.ipynb` in file browser

**2. Import Libraries:**

```python
from utils.mcp_client import MCPClient
import pandas as pd
import matplotlib.pyplot as plt
```

**3. Initialize Client:**

```python
client = MCPClient()
# Your API key is automatically loaded from environment
```

**4. Run a Query:**

```python
result = client.call_servers(
    prompt="For patient RESEARCH-PAT001, get clinical demographics from Epic.",
    servers=["epic"],
    model="claude-sonnet-4-6",
    max_tokens=2048
)

print(result["response"])
print(f"Tokens used: {result['usage']['total_tokens']}")
print(f"Cost: ${result['usage']['estimated_cost_usd']:.4f}")
```

**5. Parse and Visualize Results:**

```python
# Example: Parse spatial data (you'll need to adapt based on actual response)
import json

# Extract data from response
# data = json.loads(result["response"])

# Create visualization
plt.figure(figsize=(10, 6))
# ... your plotting code ...
plt.title("Spatial Gene Expression for RESEARCH-PAT001")
plt.show()
```

### Example Workflows

**Workflow 1: Patient Clinical Summary**

```python
# Get clinical data
clinical_result = client.call_servers(
    prompt="""
    For patient RESEARCH-PAT001:
    1. Get demographics (age, gender)
    2. Get primary diagnosis
    3. Get recent CA-125 lab values
    4. Get current medications
    """,
    servers=["epic"]
)

print(clinical_result["response"])
```

**Workflow 2: Spatial Transcriptomics Analysis**

```python
# Run spatial analysis
spatial_result = client.call_servers(
    prompt="""
    For patient RESEARCH-PAT001:
    1. Load spatial transcriptomics data
    2. Perform cell type deconvolution
    3. Identify tumor vs. stroma regions
    4. Report top cell populations
    """,
    servers=["spatialtools"]
)

print(spatial_result["response"])
```

**Workflow 3: Multi-Omics Integration**

```python
# Integrate omics data
multiomics_result = client.call_servers(
    prompt="""
    For patient RESEARCH-PAT001:
    1. Load RNA-seq, proteomics, phosphoproteomics
    2. Run HAllA association analysis
    3. Identify significant multi-omics correlations
    4. Report top 10 associations
    """,
    servers=["multiomics"]
)

print(multiomics_result["response"])
```

**Workflow 4: Complete Patient Analysis**

```python
# Full analysis pipeline
patients = ["RESEARCH-PAT001", "RESEARCH-PAT002", "RESEARCH-PAT003"]
results = []

for patient_id in patients:
    print(f"Analyzing {patient_id}...")

    result = client.call_servers(
        prompt=f"""
        For patient {patient_id}:
        1. Get clinical data (Epic)
        2. Analyze spatial transcriptomics
        3. Run pathway enrichment on DEGs
        4. Identify treatment-relevant markers
        """,
        servers=["epic", "spatialtools", "multiomics"]
    )

    results.append({
        "patient_id": patient_id,
        "response": result["response"],
        "tokens": result["usage"]["total_tokens"],
        "cost": result["usage"]["estimated_cost_usd"]
    })

# Save results
import json
with open("patient_analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Analyzed {len(patients)} patients")
print(f"Total cost: ${sum(r['cost'] for r in results):.2f}")
```

### Saving Your Work

**Save Notebook:**
- Click File → Save Notebook (or Ctrl+S / Cmd+S)
- Notebooks are saved in your JupyterHub user directory

**Export Results:**
```python
# Export to CSV
df = pd.DataFrame(results)
df.to_csv("analysis_results.csv", index=False)

# Export to Excel
df.to_excel("analysis_results.xlsx", index=False)

# Export plots
plt.savefig("spatial_heatmap.png", dpi=300, bbox_inches="tight")
```

**Download to Your Computer:**
- Right-click file in file browser → Download

---

## Common Workflows

### Workflow 1: Patient Clinical Overview

**Goal:** Get basic clinical information for a patient

**Streamlit:**
```
For patient RESEARCH-PAT001, provide:
- Demographics (age, gender)
- Primary diagnosis
- Stage and grade
- Current medications
- Recent CA-125 values
```

**Expected Output:**
- Patient demographics (de-identified)
- Ovarian cancer diagnosis details
- List of current medications
- Lab value trends

**Use Case:** Clinicians preparing for tumor board, reviewing patient status

---

### Workflow 2: Spatial Cell Type Analysis

**Goal:** Understand cell populations in tumor

**Streamlit:**
```
For patient RESEARCH-PAT001:
1. Load spatial transcriptomics data
2. Perform cell type deconvolution
3. Identify major cell populations
4. Report percentages of each cell type
5. Highlight any unusual patterns
```

**Expected Output:**
- Cell type composition (e.g., 40% tumor cells, 30% immune cells, 20% stroma, 10% other)
- Spatial distribution patterns
- Notable findings

**Use Case:** Understanding tumor microenvironment composition

---

### Workflow 3: Differential Expression Analysis

**Goal:** Find genes differentially expressed between tumor regions

**Streamlit:**
```
For patient RESEARCH-PAT001:
1. Identify tumor core vs. margin regions
2. Run differential expression analysis
3. Report top 20 upregulated genes in core vs. margin
4. Highlight any treatment-relevant markers
```

**Expected Output:**
- List of differentially expressed genes
- Fold changes and p-values
- Biological interpretation
- Treatment implications

**Use Case:** Identifying regional heterogeneity, resistance markers

---

### Workflow 4: Multi-Omics Integration

**Goal:** Integrate RNA, protein, phospho data

**Jupyter:**
```python
result = client.call_servers(
    prompt="""
    For patient RESEARCH-PAT001:
    1. Load RNA-seq, proteomics, phosphoproteomics
    2. Normalize each dataset
    3. Run HAllA multi-omics association analysis
    4. Identify significant correlations between datasets
    5. Report top 10 multi-omics associations
    6. Highlight any pathway-level patterns
    """,
    servers=["multiomics"],
    max_tokens=4096
)
```

**Expected Output:**
- RNA-protein correlations
- Protein-phospho relationships
- Multi-omics pathway associations
- Potential drug targets

**Use Case:** Comprehensive molecular profiling

---

### Workflow 5: Pathway Enrichment

**Goal:** Understand biological pathways affected

**Streamlit:**
```
I have these upregulated genes from RESEARCH-PAT001:
TP53, BRCA1, MYC, KRAS, PTEN, AKT1, PIK3CA, EGFR, ERBB2, VEGFA

Please:
1. Perform GO_BP pathway enrichment
2. Filter for p-value < 0.05
3. Report top 10 pathways
4. Explain clinical relevance for ovarian cancer
```

**Expected Output:**
- Enriched Gene Ontology pathways
- P-values and gene counts
- Clinical interpretation
- Potential therapeutic targets

**Use Case:** Understanding molecular mechanisms, identifying drug targets

---

### Workflow 6: Batch Patient Analysis

**Goal:** Analyze multiple patients systematically

**Jupyter:**
```python
# Batch analysis
patient_ids = [
    "RESEARCH-PAT001", "RESEARCH-PAT002", "RESEARCH-PAT003",
    "RESEARCH-PAT004", "RESEARCH-PAT005"
]

summary_df = []

for patient_id in patient_ids:
    result = client.call_servers(
        prompt=f"""
        For {patient_id}:
        1. Get clinical stage and grade
        2. Get primary treatment received
        3. Analyze spatial transcriptomics
        4. Report tumor purity estimate
        5. Identify top 3 overexpressed genes
        """,
        servers=["epic", "spatialtools"]
    )

    # Parse result and add to summary
    # (You'll need to parse the actual text response)
    summary_df.append({
        "patient_id": patient_id,
        "response": result["response"]
    })

# Create comparison table
import pandas as pd
df = pd.DataFrame(summary_df)
df.to_excel("patient_comparison.xlsx", index=False)
```

**Use Case:** Cohort analysis, finding patterns across patients

---

## Understanding Results

### Reading Token Usage

Each query shows token usage:

```
Input tokens: 523
Output tokens: 1,247
Total tokens: 1,770
Estimated cost: $0.0283
```

**What this means:**
- **Input tokens:** Your prompt + server context (~500 typical)
- **Output tokens:** Claude's response (~1000-2000 typical)
- **Cost:** Based on model pricing
  - Sonnet: ~$3/million input, ~$15/million output
  - Typical query: $0.02-0.08

**Estimated budget implications:**
- Costs vary by model and query complexity — see [Cost Analysis](../reference/shared/cost-analysis.md)
- A soft daily query limit per user is recommended to manage costs

### Interpreting Spatial Analysis Results

**Example output:**
```
Cell Type Composition:
- High-grade serous tumor cells: 45%
- Cancer-associated fibroblasts: 20%
- T cells (CD8+): 15%
- T cells (CD4+): 8%
- Macrophages: 7%
- B cells: 3%
- Other: 2%

Spatial Patterns:
- Dense immune infiltration at tumor margins
- Immunosuppressive M2 macrophages in tumor core
- Sparse T cell presence in central tumor regions

Clinical Implications:
- Immune-excluded phenotype suggests potential
  resistance to checkpoint inhibitors
- Consider combination immunotherapy strategies
```

**Key points:**
- **Cell percentages:** Tumor purity and microenvironment composition
- **Spatial patterns:** Where different cells are located
- **Clinical implications:** What this means for treatment

### Interpreting Pathway Results

**Example output:**
```
Top Enriched Pathways (p < 0.05):

1. DNA repair (GO:0006281)
   - p-value: 1.2e-8
   - Genes: TP53, BRCA1, BRCA2, PARP1 (15 total)
   - Clinical: PARP inhibitor sensitivity likely

2. PI3K-AKT signaling (GO:0014065)
   - p-value: 3.4e-6
   - Genes: PIK3CA, AKT1, PTEN, mTOR (12 total)
   - Clinical: Consider PI3K inhibitors

3. Apoptosis regulation (GO:0042981)
   - p-value: 8.7e-5
   - Genes: BCL2, BAX, CASP3, CASP9 (9 total)
   - Clinical: May affect chemotherapy response
```

**Key points:**
- **p-value:** Statistical significance (lower = more significant)
- **Genes:** Which genes contribute to pathway
- **Clinical:** Treatment implications

---

## FAQ

### General Questions

**Q: How many patients can I analyze?**
A: The system has 100 ovarian cancer research patients loaded. You can analyze any of them (IDs: RESEARCH-PAT001 through RESEARCH-PAT100).

**Q: Can I analyze patients not in the research cohort?**
A: No, only the 100 pre-loaded research patients. Contact the PI if you need additional patients added.

**Q: Is patient data de-identified?**
A: Yes, all data from Epic FHIR is automatically de-identified using HIPAA Safe Harbor method. Names, addresses, dates (beyond year), and other identifiers are removed.

**Q: How long do analyses take?**
A: Typically 15-45 seconds depending on complexity. Batch analyses of multiple patients may take several minutes.

**Q: What if I get an error?**
A: See [Troubleshooting](#troubleshooting) section. If unresolved, contact support (see [Getting Help](#getting-help)).

### Cost & Usage Questions

**Q: How much does each query cost?**
A: Typically $0.02-0.08 per query with Sonnet model. You can see exact cost in token usage display.

**Q: Is there a usage limit?**
A: Soft daily limit per user — see [Cost Analysis](../reference/shared/cost-analysis.md) for budget details. If you need more, contact the PI.

**Q: Which model should I use?**
A:
- **Sonnet (recommended):** Best balance for most analyses
- **Haiku:** Use for simple queries to save costs
- **Opus:** Only for critical analyses needing highest quality

### Technical Questions

**Q: Can I download results?**
A: Streamlit: Copy/paste text. Jupyter: Save notebooks, export to CSV/Excel, download files.

**Q: Does chat history persist?**
A: Streamlit: Only within session (disappears on logout). Jupyter: Notebooks are saved.

**Q: Can I use my own Python packages in Jupyter?**
A: Yes, but they must be installed by admin. Request via IT ticket.

**Q: What Python version is available?**
A: Python 3.11 with standard data science packages (pandas, numpy, matplotlib, seaborn, plotly).

---

## Troubleshooting

### Login Issues

**Problem:** "Cannot connect" error
- ✅ Check VPN connection is active
- ✅ Try https:// (not http://)
- ✅ Clear browser cache and cookies
- ✅ Try different browser

**Problem:** "Access Denied" after login
- ✅ Verify you're in `precision-medicine-users` AD group
- ✅ Contact Hospital IT to request access
- ✅ Check email is @hospital.org domain

**Problem:** Stuck at Azure AD login page
- ✅ Complete multi-factor authentication
- ✅ Check password hasn't expired
- ✅ Contact Hospital IT for AD issues

### Query Issues

**Problem:** "Server timeout" error
- ✅ Query may be too complex, try breaking into smaller parts
- ✅ Reduce max_tokens setting
- ✅ Check if specific server is down (see status page)
- ✅ Wait 30 seconds and retry

**Problem:** "No data found for patient"
- ✅ Verify patient ID is correct (RESEARCH-PAT001 format)
- ✅ Check patient is in the 100-patient research cohort
- ✅ Try a different patient to verify system is working

**Problem:** "Rate limit exceeded"
- ✅ You've hit Anthropic API rate limit
- ✅ Wait 60 seconds before retrying
- ✅ Consider using Haiku model for simple queries

**Problem:** Results don't make sense
- ✅ Check which servers you selected
- ✅ Rephrase query to be more specific
- ✅ Ask follow-up clarifying questions
- ✅ Verify patient ID is correct

### Performance Issues

**Problem:** Very slow responses (>60 seconds)
- ✅ Reduce max_tokens
- ✅ Disable unused servers
- ✅ Switch to Haiku model
- ✅ Check if running during peak hours

**Problem:** Jupyter kernel crashes
- ✅ Restart kernel: Kernel → Restart
- ✅ Clear output: Cell → All Output → Clear
- ✅ Check if running too many queries in parallel

---

## Getting Help

### Self-Service Resources

1. **This User Guide:** Read relevant sections
2. **Example Prompts:** Click button in Streamlit sidebar
3. **Jupyter Example Notebook:** `mcp_client.ipynb`
4. **FAQ Section:** Common questions answered above

### Support Tiers

**Tier 1: Hospital IT Help Desk**
- Email: help@hospital.org
- Phone: (555) 123-4567
- Hours: 24/7
- For: Login issues, VPN problems, Azure AD access

**Tier 2: Development Team**
- Email: mcp-support@devteam.com
- Hours: Mon-Fri 9 AM - 5 PM PT
- Response: Within 4 hours
- For: Server errors, query issues, bugs

**Tier 3: On-Call Engineer**
- Email: oncall-mcp@devteam.com
- Hours: 24/7 (emergencies only)
- Response: Within 1 hour for P0/P1
- For: System down, critical issues only

### Requesting Help

**Include in your request:**
1. Your name and email
2. Patient ID (if relevant)
3. Query you were trying (copy/paste)
4. Error message (screenshot or copy/paste)
5. Browser and OS version
6. Time the error occurred
7. Steps to reproduce

**Example:**
```
Subject: Error querying patient RESEARCH-PAT001

Name: Dr. Sarah Johnson (sarah.johnson@hospital.org)
Patient: RESEARCH-PAT001
Query: "Get clinical demographics"
Error: "Server timeout after 60 seconds"
Browser: Chrome 120.0 on macOS 14.1
Time: 2025-12-30 10:30 AM PT
Steps: Selected epic server, typed query, clicked send, waited 60s, got error

I've tried:
- Different browser (same error)
- Different patient (same error)
- Waited 5 minutes and retried (same error)
```

### Feature Requests

Have an idea to improve the system?

**Submit via:**
- Email: mcp-support@devteam.com
- Subject: "Feature Request: [brief description]"

**Include:**
- What you want to do
- Why it would be useful
- How often you'd use it
- Any examples

**Example requests from users:**
- "Add export to PDF button" - Implemented!
- "Show total cost for session" - On roadmap
- "Support batch patient upload" - Under review

---

**Document History:**
- v1.0 (2025-12-30): Initial user guide for production deployment
- Next Review: 2026-01-30 (monthly based on user feedback)

**Quick Links:**
- [Security Overview](SECURITY_OVERVIEW.md) - For IT staff
- [HIPAA Compliance](compliance/hipaa.md) - For administrators
