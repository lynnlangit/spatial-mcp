# System Architecture Overview

High-level architecture for developers building or extending the precision-medicine-mcp platform.

---

## Detailed Guides

| Guide | Contents |
|---|---|
| **[Data Flow & Server Communication](DATA_FLOW.md)** | Query-to-results flow, server communication patterns, data passing conventions |
| **[Integration Patterns](INTEGRATION_PATTERNS.md)** | 4 integration patterns + PatientOne example workflow |
| **[XAI & Evidence Flow](XAI_EVIDENCE_FLOW.md)** | 3-stage explainability pipeline (per-tool → synthesis → report) |
| **[Technology Stack](TECHNOLOGY_STACK.md)** | Core technologies, Python libraries, performance, scalability |

---

## System Layers

The precision-medicine-mcp platform consists of 5 architectural layers:

```
┌──────────────────────────────────────────────────────────────┐
│                   USER INTERFACE LAYER                        │
│  Streamlit UI (web) | Jupyter Notebook (data science)        │
│  Claude Desktop (local) | Claude API (production)            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                  AI ORCHESTRATION LAYER                       │
│         Claude API (Anthropic Sonnet 4.6)                    │
│         • Natural language query parsing                      │
│         • Multi-server workflow orchestration                │
│         • Result synthesis and reporting                     │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                    MCP PROTOCOL LAYER                         │
│         Tool discovery | Input validation | Error handling   │
│         STDIO (local) or SSE (cloud) transport               │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                   SERVER EXECUTION LAYER                      │
│         MCP Servers (FastMCP-based)                           │
│         • Most production-ready (see Server Registry)        │
│         • Some mocked (tcga, mockepic)                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                      DATA LAYER                               │
│         • GCS buckets (patient data, analysis results)       │
│         • GCP Healthcare API (FHIR stores)                   │
│         • Reference data (genomes, pathways, ontologies)     │
│         • External APIs (TCGA, DeepCell, HuggingFace)        │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

### 1. Stateless Servers
Each tool call is independent. Servers don't maintain session state.

**Why:** Simplifies debugging, enables horizontal scaling, makes caching easier.

### 2. DRY_RUN Mode
All servers support synthetic data mode for demos without real data or API keys.

**Why:** Instant demos, education use cases, CI/CD testing without credentials.

### 3. Tool-Centric Design
Each tool does one thing well. Prefer many small tools over few large ones.

**Why:** Claude can compose complex workflows from simple building blocks.

### 4. Data-Last Philosophy
Tools return data and metadata. Claude interprets and presents to users.

**Why:** Separates computation from presentation, enables flexible UI layers.

### 5. Error Messages for Humans
Error messages explain what went wrong and suggest fixes.

**Why:** Claude needs actionable error messages to retry or adjust workflows.

**Example:**
```python
# ❌ BAD: Cryptic error
raise ValueError("Invalid input")

# ✅ GOOD: Actionable error
raise ValueError(
    "Invalid VCF file format. Expected columns: CHROM, POS, REF, ALT. "
    "Found: {actual_columns}. "
    "Try: mcp-fgbio.validate_vcf(file_path) to check format."
)
```

### 6. Observability & Traceability

Every tool call is logged with full context — no AI routing decision is invisible.

The platform captures traceability data at three layers:

1. **Structured tool logging** (`shared/common/logging.py`) — JSON-formatted logs emitted by each MCP server recording tool name, request ID, parameters, duration, and success/failure.
2. **HIPAA audit events** (`ui/streamlit-app/utils/audit_logger.py`) — 10 event types (login, query, response, error, server/model selection, session lifecycle, benchmarks) sent to Cloud Logging with 10-year retention.
3. **UI orchestration traces** (`ui/streamlit-app/utils/trace_utils.py` + `trace_display.py`) — per-call trace data extracted from AI responses, displayed in 4 visualization modes (log, cards, timeline, Mermaid sequence diagram), and exportable as JSON or Mermaid.

A live monitoring dashboard (`ui/dashboard/`) provides server health, cost analysis, performance metrics, and optimization recommendations.

**See also:** [Server Registry](../reference/shared/server-registry.md)

---

## Evaluation Architecture

The platform includes a reproducible evaluation harness under `eval/`
with two complementary evaluations designed around different questions:

### MTBBench Longitudinal (governance validation, n=40 patients)
- 40 cases from MSK-CHORD via cBioPortal; 180 binary questions across
  survival, progression, and recurrence tracks
- Measures governance properties independent of cancer type:
  HITL catch rate (7.5% [0%, 17.5%]), confidence calibration (82.1%
  moderate/low for MSS/low-TMB cohort), flagged items (5.60 per case)
- Tool-grounding and de-id integrity are architectural guarantees
  (enforced by pipeline, not model-dependent)
- Key methodological finding: MTBBench's standardized synthetic tool
  outputs are identical per case, preventing accuracy differentiation —
  MCP platforms require patient-specific data for accuracy evaluation

### Case Study (accuracy validation, n=12 questions)
- PAT001 (HGSOC) and PAT002 (HR+ breast cancer) — platform's target indications
- 12 clinically unambiguous binary questions with guideline-cited ground truth
- Tool outputs sourced from `tests/fixtures/pat001_canonical.py` and
  `pat002_canonical.py` — reproducible without running MCP servers
- Result: 100% accuracy with tool outputs vs. 33.3% without
  (p < 0.001, Fisher's exact test, Claude Sonnet 4.6)

### Reproducibility
- Case study: deterministic from canonical fixtures; runs in CI on every PR
- MTBBench: run manually before paper submission
- Model pinned: `claude-sonnet-4-6` across all evaluations
- See `eval/README.md` for full run instructions and result tables

---

## How we prove our results

The platform's claims rest on three layers of evidence: explainability
(each recommendation shows its work), traceability (every action is
recorded and auditable), and evaluation (results are independently validated).

**[View interactive summary →](https://lynnlangit.github.io/precision-medicine-mcp/proof-layers.html)**
*(click layer names to expand detail)*

| Layer | Mechanisms | Key evidence |
|---|---|---|
| **Explainability** | XAI Evidence Strength Summary, key_drivers, confidence_counts, evidence badges, counterfactual | Per-recommendation provenance in every report |
| **Traceability** | Tool-grounding, guideline attribution, HITL gate, de-id integrity, HIPAA audit log, canonical fixtures | 100% tool-grounding + de-id (architectural); HITL 7.5% catch rate (measured) |
| **Evaluation** | Case study accuracy, MTBBench governance, methodological finding, CI regression, scheduled doc-audit | 100% vs. 33.3% accuracy (p < 0.001); governance validated n=40 patients |

See [eval/README.md](../../eval/README.md) for full evaluation methodology and results.

---

## Next Steps for Developers

1. **Understand the architecture** (this doc + README.md) - 30 min
2. **Study a reference server** (mcp-multiomics recommended) - 30 min
3. **Build a new server** (follow ADD_NEW_MODALITY_SERVER.md) - 4-8 hours
4. **Write tests** (≥50% coverage for production) - 1-2 hours
5. **Deploy to GCP** (Cloud Run deployment) - 30 min
6. **Integrate with workflow** (test with PatientOne) - 30 min

**See:** [README.md](README.md) for quick start paths and resources.

---

**Related Resources:**
- **[ADD_NEW_MODALITY_SERVER.md](ADD_NEW_MODALITY_SERVER.md)** - Step-by-step guide for building new servers
- **[Server Registry](../reference/shared/server-registry.md)** - Canonical server/tool counts
- **[Server Implementations](../../servers/README.md)** - Code examples
