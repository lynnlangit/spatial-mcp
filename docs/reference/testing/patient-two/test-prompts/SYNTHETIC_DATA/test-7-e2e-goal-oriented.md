# PAT002 End-to-End Goal-Oriented Test (SYNTHETIC_DATA)

**Purpose:** Validate model routing across all pipeline stages for PAT002.
Claude selects tools and sequencing autonomously — do not prescribe tool order.

**Setup:** All `*_DRY_RUN` vars = false except EPIC_DRY_RUN=true.

**Patient data root:**
`/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/`

---

### Prompt to paste into Claude Desktop:

```
You are a precision oncology analysis platform. Run a full end-to-end analysis
for PAT002-BC-2026 (Michelle Thompson, 42F, Stage IIA ER+/PR+/HER2- Invasive
Ductal Carcinoma, BRCA2 germline c.5946delT, PIK3CA H1047R, on tamoxifen).

Patient data is at:
/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/

Your goal is to produce a precision oncology report that:
1. Confirms FDA-approved treatment options supported by genomic and spatial evidence
2. Identifies any investigational hypotheses NOT reachable by standard clinical
   workup (germline BRCA testing + tumour NGS panel + standard imaging)
3. Predicts immunotherapy responsiveness with mechanistic justification
4. Matches relevant clinical trials to PAT002's molecular profile

Use whatever MCP servers and tools are available to best achieve these goals.
You decide the order and selection of tool calls. Prioritise depth of insight
over breadth of tool coverage.

At the end, structure your response as:
A) Standard treatment paths confirmed (with evidence source for each)
B) Investigational hypotheses beyond standard workup (ranked by actionability)
C) Immunotherapy prediction and mechanistic basis
D) Clinical trial matches
E) Confidence gaps — what additional data would change your conclusions

Flag the response: SYNTHETIC DATA — not for clinical use.
```

---

**Pass criteria:**
- Claude calls at least 8 tools across >= 3 stages without being told which to call
- Standard treatment paths match test-1 through test-3 results
- At least one beyond-standard-workup hypothesis surfaces without being prompted
- Response includes a confidence gap section (demonstrates calibrated uncertainty)
