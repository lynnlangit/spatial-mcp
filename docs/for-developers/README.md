# For MCP Developers & Software Engineers

**This section is for:** MCP developers, software engineers, and platform builders who want to extend the precision-medicine-mcp platform with new servers or contribute to existing codebase.

---

## What You Can Accomplish Here

```mermaid
graph LR
    A["📐 Learn<br/>architecture"] --> B["🔨 Build<br/>new servers"] --> C["🧪 Test<br/>validate"] --> D["🚀 Deploy<br/>production"] --> E["🤝 Contribute<br/>upstream"]

    style A fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style B fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style C fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style D fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style E fill:#fce4ec,stroke:#e91e63,stroke-width:2px
```

> **Learn:** FastMCP patterns, Claude + Gemini orchestration ([Server Registry](../reference/shared/server-registry.md)) | **Build:** Custom MCP servers for new modalities (metabolomics, radiomics, single-cell) | **Test:** 91 tests in mcp-multiomics, 68% coverage target | **Deploy:** GCP Cloud Run, Docker, SSE transport | **Contribute:** Coding standards, PR guidelines

---

> **v17 update (April 2026):** Server #19 (`mcp-cardiometabolic`) added.
> Introduces non-oncology server pattern: no omics matrices, biomarker dict inputs,
> three CVD risk equations, ACC/AHA statin decision logic.
> Good reference implementation for preventive health use cases.

## Quick Start (3 Paths)

> **First step for all paths:** Before building anything new, check if an existing server (internal or external) already does what you need. Read [SEARCH_VS_BUILD.md](SEARCH_VS_BUILD.md) (10 min).

### 1. Building a New Modality Server (4-8 hours)
**Goal:** Add a new server for metabolomics/radiomics/other modalities

1. **Search first** → [SEARCH_VS_BUILD.md](SEARCH_VS_BUILD.md) — confirm no existing server covers your need (10 min)
2. **Read the guide** → [ADD_NEW_MODALITY_SERVER.md](ADD_NEW_MODALITY_SERVER.md) (20 min)
3. **Copy boilerplate template** → `/servers/mcp-server-boilerplate/` (5 min)
4. **Implement tools** → Use FastMCP patterns from mcp-multiomics (3-5 hours)
5. **Write tests** → 50%+ coverage for production servers (1-2 hours)
6. **Deploy** → GCP Cloud Run with `./infrastructure/deployment/deploy_to_gcp.sh` (30 min)

**Total Time:** 4-8 hours from template to deployed server

### 2. Understanding the Architecture (30-60 min)
**Goal:** Understand how the MCP servers orchestrate precision medicine workflows

1. **System overview** → [ARCHITECTURE.md](ARCHITECTURE.md) (15 min)
2. **Best reference implementation** → [mcp-multiomics README](../../servers/mcp-multiomics/README.md) (15 min)
3. **Architecture details** → [Architecture docs](../reference/architecture/README.md) (30 min)

**Total Time:** 30-60 minutes for full understanding

### 3. Contributing to Existing Servers (varies)
**Goal:** Fix bugs, add features, improve tests

1. **Read CONTRIBUTING.md** → [CONTRIBUTING.md](CONTRIBUTING.md) (10 min)
2. **Pick a server** → See [Server Status](../../servers/README.md#-server-status) (5 min)
3. **Read codebase** → Study existing implementation patterns (30 min)
4. **Make changes** → Follow coding standards and testing requirements
5. **Submit PR** → Include tests and documentation

---

## Documents in This Section

### Getting Started
- **[README.md](README.md)** *(this file)* - Navigation hub for developers
- **[SEARCH_VS_BUILD.md](SEARCH_VS_BUILD.md)** - Should you search for an existing server or build a new one?
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview (data flow, integration)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Cheat sheet for common tasks

### Building New Servers
- **[ADD_NEW_MODALITY_SERVER.md](ADD_NEW_MODALITY_SERVER.md)** - Comprehensive guide (planning → deployment)

### Contributing
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - PR guidelines, coding standards, review process

---

## System Architecture ([Server Registry](../reference/shared/server-registry.md))

```mermaid
graph TB
    subgraph "User Interfaces"
        STREAMLIT["🌐 Streamlit Chat UI<br/>Web Interface"]
        JUPYTER["📓 Jupyter Notebook<br/>Data Science"]
        DESKTOP["💬 Claude Desktop<br/>Local STDIO"]
    end

    subgraph "AI Orchestration Layer"
        API["🤖 Claude API<br/>Anthropic Sonnet 4.6<br/>MCP Client"]
    end

    subgraph "20 Custom MCP Servers (114 tools)"
        STAGE0["🔒 Stage 0: De-identification (6 tools)<br/>mcp-deidentify"]
        CLINICAL["🏥 Clinical & Genomic (20 tools)<br/>mcp-epic · mcp-fgbio · mcp-genomic-results<br/>mcp-mockepic 🎭 · mcp-mocktcga 🔧"]
        OMICS["🧬 Multi-Omics & Spatial (37 tools)<br/>mcp-multiomics · mcp-spatialtools<br/>mcp-openimagedata · mcp-deepcell · mcp-cell-classify"]
        IMMUNO["💉 Immunology & Treatment (25 tools)<br/>mcp-cibersortx · mcp-neoantigen<br/>mcp-perturbation · mcp-quantum-celltype-fidelity"]
        EXTDATA["🌐 External Data (12 tools)<br/>mcp-geodownload · mcp-opentargets"]
        PREVENT["❤️ Preventive Health (5 tools)<br/>mcp-cardiometabolic"]
        REPORT["📋 Reporting (5 tools)<br/>mcp-patient-report"]
    end

    subgraph "Patient Analysis Workflows"
        PATIENT["🏥 Three Validated Patients<br/>PAT001 Stage IV HGSOC · PAT002 ER+ Breast<br/>PAT003 Preventive CVD"]
    end

    STREAMLIT ==> API
    JUPYTER ==> API
    DESKTOP --> API

    API ==> STAGE0
    API ==> CLINICAL
    API ==> OMICS
    API ==> IMMUNO
    API ==> EXTDATA
    API ==> PREVENT
    API ==> REPORT

    STAGE0 ==> CLINICAL
    CLINICAL ==> PATIENT
    OMICS ==> PATIENT
    IMMUNO ==> PATIENT
    EXTDATA ==> PATIENT
    PREVENT ==> PATIENT
    REPORT ==> PATIENT

    style STREAMLIT fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style JUPYTER fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style DESKTOP fill:#d1ecf1,stroke:#0c5460,stroke-width:2px
    style API fill:#cce5ff,stroke:#004085,stroke-width:3px
    style PATIENT fill:#e1f5ff,stroke:#0066cc,stroke-width:3px
    style STAGE0 fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    style CLINICAL fill:#d4edda,stroke:#28a745,stroke-width:2px
    style OMICS fill:#d4edda,stroke:#28a745,stroke-width:2px
    style IMMUNO fill:#d4edda,stroke:#28a745,stroke-width:2px
    style EXTDATA fill:#d4edda,stroke:#28a745,stroke-width:2px
    style PREVENT fill:#d4edda,stroke:#28a745,stroke-width:2px
    style REPORT fill:#d4edda,stroke:#28a745,stroke-width:2px
```

**Legend:**
- ✅ **Production**: Real data, comprehensive tests, deployed
- 🔧 **Framework**: API stubs ready for integration (tcga)
- 🎭 **Mock by Design**: Intentionally synthetic for demos (mockepic)

See [Server Registry](../reference/shared/server-registry.md) for current counts and status.

---

## Server Status Overview

**Production Status:** Most servers production-ready.

**Total:** See [Server Registry](../reference/shared/server-registry.md) for current server and tool counts.

📋 **[Complete Server Implementation Status →](../reference/architecture/README.md)** - Comprehensive documentation including:
- Detailed tool-by-tool implementation status
- Real vs. mocked capability breakdown
- Test coverage metrics and production readiness
- DRY_RUN mode behavior for each server
- GCP Cloud Run deployment status
- Production deployment checklists

---

## Why Two Epic Servers?

**mcp-epic (Real FHIR):** 100% production-ready Epic integration
- 🏥 Runs **locally only** (STDIO transport) for HIPAA compliance
- ✅ Real patient data with built-in de-identification
- 🔐 Requires hospital credentials (Epic FHIR API + GCP Healthcare API)
- 4 tools: `get_patient_demographics`, `get_patient_conditions`, `get_patient_observations`, `get_patient_medications`
- **Use for:** Production hospital deployment with real patient data

**mcp-mockepic (Mock FHIR):** Intentional mock for demonstration/education
- 🌐 Deployed to **GCP Cloud Run** (public SSE endpoint)
- 🎭 Synthetic patient data by design (no real PHI)
- 🚀 No credentials needed - instant demos
- 3 tools: `query_patient_records`, `link_spatial_to_clinical`, `search_diagnoses`
- **Use for:** Public demos, workflow development, education

---

## Key Technologies

### MCP Protocol
- **What:** Model Context Protocol - standard for AI-tool integration
- **Why:** Enables Claude to discover and call tools across multiple servers
- **Transport:** STDIO (local) or SSE (cloud)
- **Spec:** https://modelcontextprotocol.io/

### FastMCP Framework
- **What:** Python framework for building MCP servers
- **Why:** Simplifies tool registration, input validation, error handling
- **Docs:** https://gofastmcp.com
- **Pattern:** `@mcp.tool()` decorator for each tool

### GCP Cloud Run
- **What:** Serverless container platform
- **Why:** Auto-scales, pay-per-use, easy deployment
- **Transport:** SSE (Server-Sent Events) for MCP
- **Deployment:** `./infrastructure/deployment/deploy_to_gcp.sh`

### Claude API
- **What:** Anthropic's Sonnet 4.6 model with MCP client support
- **Why:** Orchestrates multi-server workflows via natural language
- **Integration:** Claude Desktop (local) or Claude API (production)

---

## Development Resources

### Best Reference Implementations
1. **mcp-multiomics** ([README](../../servers/mcp-multiomics/README.md)) - Production-ready, 91 tests, 68% coverage, HAllA integration
2. **mcp-spatialtools** ([README](../../servers/mcp-spatialtools/README.md)) - 95% real, comprehensive spatial analysis
3. **mcp-fgbio** ([README](../../servers/mcp-fgbio/README.md)) - Simple, focused, excellent for learning basics

### Architecture Documentation
- **System Design:** [Architecture Overview](../reference/architecture/README.md)
- **Data Flow:** [Clinical EHR Integration](../reference/architecture/clinical/ehr-integration.md)

### Testing Resources
- **Unit Tests:** [Test Examples](../../tests/unit/)
- **Integration Tests:** [GCP Testing](../../tests/integration/)

### Code Examples
- **Server Template:** [Boilerplate](../../servers/mcp-server-boilerplate/)

---

## Common Development Tasks

### 1. Add a New Tool to Existing Server

```python
# In servers/mcp-{server}/src/mcp_{server}/server.py

@mcp.tool()
async def my_new_tool(
    param1: str,
    param2: int = 10
) -> dict:
    """
    Clear description of what this tool does.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)

    Returns:
        Dictionary with:
        - result: The computed result
        - metadata: Additional context

    Example:
        >>> result = await my_new_tool(param1="test")
    """
    if DRY_RUN:
        return {"status": "DRY_RUN", "result": "simulated"}

    # Real implementation
    result = do_computation(param1, param2)
    return {"status": "success", "result": result}
```

### 2. Run Tests Locally

```bash
# Test single server
cd tests/unit/mcp-{server}
pytest -v --cov=../../../servers/mcp-{server}/src/mcp_{server}

# Test all servers
pytest tests/unit/ -v

# Test with real data (not DRY_RUN)
SERVER_DRY_RUN=false pytest tests/unit/mcp-{server}
```

### 3. Deploy to GCP Cloud Run

```bash
# Development deployment (DRY_RUN=true)
./infrastructure/deployment/deploy_to_gcp.sh --development --server mcp-{server}

# Production deployment (DRY_RUN=false)
./infrastructure/deployment/deploy_to_gcp.sh --production --server mcp-{server}

# Test deployment
curl https://mcp-{server}-{hash}.run.app/health
```

### 4. Debug with Claude Desktop

```json
// In claude_desktop_config.json
{
  "mcpServers": {
    "myserver": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/servers/mcp-myserver",
        "python",
        "-m",
        "mcp_myserver"
      ],
      "env": {
        "MYSERVER_DRY_RUN": "true",
        "MYSERVER_DATA_DIR": "/path/to/data"
      }
    }
  }
}
```

Restart Claude Desktop and test:
- "What tools are available from myserver?"
- "Use myserver to [do something]"

---

## Code Quality Standards

### Testing Requirements
- **Production servers:** ≥50% code coverage
- **Demo/mocked servers:** ≥35% code coverage
- **All servers:** 100% smoke tests (imports, tool registration, DRY_RUN)

### Documentation Requirements
- Clear docstrings for all tools (Claude reads these!)
- Server README with usage examples
- Architecture document showing integration points
- Update central documentation tables

### Code Style
- Python 3.11+
- Type hints for all function parameters
- Async/await for all MCP tools
- Error handling with actionable messages

---

## Frequently Asked Questions

### "Can I use a different Python framework (not FastMCP)?"
**A:** Yes, but FastMCP is strongly recommended. It handles MCP protocol details, input validation, and error handling. Raw MCP implementation requires 3-5x more boilerplate code.

### "Do all tools need to support DRY_RUN mode?"
**A:** Yes for public demos. No for hospital-only servers. DRY_RUN mode allows instant demos without real data or API keys.

### "Can I call external APIs (NCBI, KEGG, etc.)?"
**A:** Yes! Use `requests` or async libraries. Add retry logic and error handling. Cache responses when possible. Mock API calls in DRY_RUN mode.

### "How do I handle large data files (>1GB)?"
**A:**
- Store in GCS (Google Cloud Storage) or S3
- Pass file paths (not file contents) between tools
- Use streaming for analysis (don't load entire file into memory)
- Return summary results, not full datasets

### "Can servers call other servers?"
**A:** Not directly. Claude API orchestrates all inter-server communication. This prevents circular dependencies and makes debugging easier.

### "What if my tool takes >30 seconds?"
**A:**
- Break into smaller tools (e.g., "start_analysis" → "get_results")
- Use GCP Cloud Run timeout (max 60 minutes)
- Return partial results with status updates
- Consider background job pattern

---

## Example Workflow: Adding Metabolomics Server

**Goal:** Add a new server for LC-MS metabolomics data analysis

**Steps:**
1. **Plan** (1 hour) - Define 5-8 tools, dependencies, data formats
2. **Implement** (3-4 hours) - Use boilerplate template, add tools
3. **Test** (1-2 hours) - Write unit tests, achieve 50%+ coverage
4. **Document** (1 hour) - Server README + architecture doc
5. **Deploy** (30 min) - GCP Cloud Run deployment
6. **Integrate** (30 min) - Test with other servers (multiomics integration)

**Total Time:** 4-8 hours from start to deployed server

**See:** [ADD_NEW_MODALITY_SERVER.md](ADD_NEW_MODALITY_SERVER.md) for complete walkthrough

---

## See It In Action

<kbd><img src="https://github.com/lynnlangit/precision-medicine-mcp/blob/main/data/images/Claude-client.png" width=800></kbd>

*MCP servers orchestrating bioinformatics workflows through Claude Desktop*

---

**Related Resources:**
- 🏥 [Hospital Deployment Guide](../for-hospitals/README.md) - For IT teams deploying to production
- 🔬 [Researcher Guide](../for-researchers/README.md) - For bioinformaticians using the platform
- 📊 [Architecture Documentation](../reference/architecture/README.md) - Deep technical dive
- 🏠 [Back to Main Documentation](../INDEX.md)

---

**Last Updated:** 2026-02-01
