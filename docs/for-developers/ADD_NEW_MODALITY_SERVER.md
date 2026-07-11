# Adding a New Modality Server to the MCP Architecture

> **Prerequisite:** Before building a new server, confirm that no existing internal or external server covers your need. See [SEARCH_VS_BUILD.md](SEARCH_VS_BUILD.md) for the decision process.

**Last Updated:** 2026-01-12

**Purpose:** Step-by-step guide for platform builders adding new data modalities to the precision medicine MCP system

**Target Audience:** MCP developers, bioinformatics platform engineers, workflow architects

---

## Table of Contents

1. [Overview](#overview)
2. [When to Add a New Server](#when-to-add-a-new-server)
3. [Architecture Integration Points](#architecture-integration-points)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing Requirements](#testing-requirements)
6. [Documentation Requirements](#documentation-requirements)
7. [Deployment Guide](#deployment-guide)
8. [Example: Metabolomics Server](#example-metabolomics-server)
9. [Checklist](#integration-checklist)

---

## Overview

### What is a Modality?

A **modality** is a distinct category of biomedical data with unique:
- **Data format** (e.g., CSV expression matrices, VCF variants, TIFF images)
- **Analysis methods** (e.g., differential expression, mutation calling, image segmentation)
- **Tools/libraries** (e.g., scanpy, pysam, opencv)
- **Domain knowledge** (e.g., spatial statistics, genomics, radiology)

**Current modalities in this repo:**
1. 🧬 Clinical Data (EHR/FHIR)
2. 🧪 Genomic Cohorts (TCGA)
3. 🖼️ Imaging (H&E, multiplex IF)
4. 🔬 Multiomics (RNA/Protein/Phospho)
5. 📍 Spatial Transcriptomics
6. 🤖 AI/ML Inference (genomic foundation models)
7. ⚙️ Workflow Orchestration (Nextflow)

**Potential new modalities:**
- 🧪 **Metabolomics** - Small molecule abundance (LC-MS, GC-MS)
- 📊 **Radiomics** - Quantitative imaging features from CT/MRI
- 🧬 **Single-cell Omics** - scRNA-seq, scATAC-seq
- 🔬 **Proteomics** - Mass spec protein abundance
- 🧬 **Epigenomics** - DNA methylation, ChIP-seq
- 📈 **Wearable Data** - Continuous monitoring (heart rate, activity)

### What is an MCP Server?

An **MCP server** is a FastMCP-based Python module that:
- Exposes **tools** (functions) that Claude can call via MCP protocol
- Handles data I/O, computation, and analysis for a specific modality
- Runs as a stdio subprocess in Claude Desktop OR SSE endpoint on GCP Cloud Run
- Returns structured JSON responses with results/visualizations/errors

**Key characteristics:**
- **Stateless** - Each tool call is independent
- **Deterministic** - Same inputs → same outputs (in non-DRY_RUN mode)
- **Well-documented** - Clear docstrings for Claude to understand tool usage
- **Error-handling** - Graceful failures with actionable error messages
- **Testable** - Unit tests for all tools with DRY_RUN and real data modes

---

## When to Add a New Server

### Good Reasons to Add a Server ✅

1. **New data type with unique analysis needs**
   - Example: Metabolomics requires pathway mapping, compound identification

2. **Domain requires specialized tools/libraries**
   - Example: Radiomics needs pyradiomics for feature extraction

3. **Clear boundary from existing servers**
   - Example: Single-cell analysis is distinct from bulk spatial transcriptomics

4. **Will be used in multi-modality workflows**
   - Example: Metabolomics + transcriptomics integration for cancer metabolism

### Bad Reasons to Add a Server ❌

1. **Tool belongs in existing server**
   - Example: Adding ATAC-seq to mcp-multiomics instead of new server

2. **Creating artificial separation**
   - Example: Splitting mcp-spatialtools into mcp-spatial-de and mcp-spatial-viz

3. **Single-use tool with no modality**
   - Example: One-off data format converter → add to existing server

### Decision Framework

Ask these questions:
1. Does this data type have ≥5 distinct analysis tools?
2. Does it require ≥2 specialized Python libraries?
3. Will it integrate with ≥2 other modalities in workflows?
4. Is there a clear audience who needs just this modality?

**If 3+ are YES → Create new server**

---

## Architecture Integration Points

When adding a new server, you'll integrate with:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Desktop / Claude API                   │
│                  (MCP Client - Orchestrates Servers)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼─────┐      ┌─────▼──────┐      ┌────▼─────┐
    │ Existing │      │    NEW     │      │ Existing │
    │  Server  │      │   Server   │      │  Server  │
    │ (epic)   │      │(metabolomics)│    │(multiomics)│
    └──────────┘      └────────────┘      └──────────┘
```

### 1. Configuration Layer
- **Claude Desktop config** (`claude_desktop_config.json`)
- **Environment variables** (DATA_DIR, DRY_RUN, API keys)

### 2. Tool Discovery Layer
- **FastMCP registration** - Tools exposed via `@mcp.tool()` decorator
- **Input schemas** - Pydantic models for validation
- **Output schemas** - Structured JSON responses

### 3. Data Layer
- **Shared data directory** - `/data/patient-data/PAT001-OVC-2025/`
- **File naming conventions** - Consistent with other servers
- **Metadata standards** - Patient IDs, sample IDs, timestamps

### 4. Testing Layer
- **Unit tests** - `/tests/unit/mcp-{server}/`
- **Integration tests** - Multi-server workflows
- **Fixtures** - Synthetic test data in `/tests/unit/mcp-{server}/fixtures/`

### 5. Documentation Layer
- **Server README** - `/servers/mcp-{server}/README.md`
- **Architecture doc** - `/architecture/{modality}/README.md`
- **Main server table** - `/servers/README.md#-server-status`

### 6. Deployment Layer
- **GCP Cloud Run** - SSE transport for remote access
- **Docker container** - Isolated environment per server
- **Deployment script** - `/infrastructure/deployment/deploy_to_gcp.sh`

---

## Step-by-Step Implementation

### Phase 1: Planning (1-2 hours)

**1.1 Define the Modality Scope**

Create a planning document:
```markdown
# Metabolomics Server Plan

**Data Types:**
- LC-MS metabolite abundance tables (CSV)
- Compound annotations (HMDB IDs, KEGG IDs)
- Pathway databases (KEGG, Reactome)

**Key Tools (5-8):**
1. load_metabolomics_data - Parse LC-MS output
2. normalize_metabolite_abundance - Batch correction, normalization
3. identify_differential_metabolites - Statistical testing
4. map_metabolites_to_pathways - KEGG pathway enrichment
5. integrate_with_transcriptomics - Correlate metabolites with genes

**Dependencies:**
- pandas, numpy, scipy (standard)
- chempy (compound handling)
- requests (API calls to KEGG/HMDB)

**DRY_RUN Behavior:**
- Return synthetic metabolite data
- Mock API calls to external databases
```

**1.2 Review Existing Servers**

Study similar servers for patterns:
- Look at `mcp-multiomics` for data integration patterns
- Look at `mcp-fgbio` for reference data handling
- Look at `mcp-spatialtools` for statistical testing patterns

**1.3 Design Tool Signatures**

Draft function signatures with clear docstrings:
```python
@mcp.tool()
async def identify_differential_metabolites(
    data_file: str,
    group1_samples: list[str],
    group2_samples: list[str],
    test_method: str = "wilcoxon",
    fdr_threshold: float = 0.05
) -> dict:
    """
    Identify metabolites with significant abundance differences between groups.

    Args:
        data_file: Path to metabolomics data CSV (samples × metabolites)
        group1_samples: List of sample IDs for condition 1
        group2_samples: List of sample IDs for condition 2
        test_method: Statistical test - "wilcoxon", "t_test", "limma"
        fdr_threshold: FDR significance cutoff

    Returns:
        Dictionary with:
        - significant_metabolites: List of metabolites passing threshold
        - test_statistics: Per-metabolite p-values and fold-changes
        - pathway_hits: Enriched metabolic pathways

    Example:
        >>> result = await identify_differential_metabolites(
        ...     data_file="/data/patient-001/metabolomics/abundance.csv",
        ...     group1_samples=["tumor_1", "tumor_2"],
        ...     group2_samples=["normal_1", "normal_2"]
        ... )
    """
```

### Phase 2: Repository Setup (30 minutes)

**2.1 Create Server Directory**

```bash
cd /path/to/spatial-mcp
mkdir -p servers/mcp-metabolomics/src/mcp_metabolomics
mkdir -p servers/mcp-metabolomics/tests
```

**2.2 Initialize Python Project**

Create `servers/mcp-metabolomics/pyproject.toml`:
```toml
[project]
name = "mcp-metabolomics"
version = "0.1.0"
description = "MCP server for metabolomics data analysis"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.13.0",
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    "scipy>=1.11.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**2.3 Install Dependencies**

```bash
cd servers/mcp-metabolomics
uv sync --dev
```

### Phase 3: Core Implementation (3-5 hours)

**3.1 Create Server Skeleton**

`servers/mcp-metabolomics/src/mcp_metabolomics/server.py`:
```python
"""
MCP Server for Metabolomics Data Analysis

Provides tools for LC-MS/GC-MS metabolomics analysis including:
- Data loading and normalization
- Differential metabolite analysis
- Pathway enrichment
- Integration with transcriptomics
"""

import os
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
from scipy import stats
from fastmcp import FastMCP

# Initialize server
mcp = FastMCP("metabolomics")

# Configuration from environment
DRY_RUN = os.getenv("METABOLOMICS_DRY_RUN", "true").lower() == "true"
DATA_DIR = os.getenv("METABOLOMICS_DATA_DIR", "/data/metabolomics")

@mcp.tool()
async def load_metabolomics_data(
    data_file: str,
    metadata_file: Optional[str] = None
) -> dict:
    """
    Load metabolomics abundance data from LC-MS/GC-MS output.

    Args:
        data_file: Path to metabolite abundance CSV (samples × metabolites)
        metadata_file: Optional sample metadata CSV

    Returns:
        Dictionary with loaded data summary
    """
    if DRY_RUN:
        return {
            "status": "DRY_RUN",
            "samples": 24,
            "metabolites": 387,
            "message": "Simulated LC-MS data load"
        }

    # Real implementation
    data = pd.read_csv(data_file, index_col=0)

    result = {
        "status": "success",
        "data_file": str(data_file),
        "samples": data.shape[0],
        "metabolites": data.shape[1],
        "metabolite_ids": data.columns.tolist()[:10],  # First 10
    }

    if metadata_file:
        metadata = pd.read_csv(metadata_file)
        result["metadata_loaded"] = True
        result["sample_groups"] = metadata["group"].unique().tolist()

    return result

@mcp.tool()
async def identify_differential_metabolites(
    data_file: str,
    group1_samples: list[str],
    group2_samples: list[str],
    test_method: str = "wilcoxon",
    fdr_threshold: float = 0.05
) -> dict:
    """
    Identify metabolites with significant abundance differences.

    [Full docstring from planning phase]
    """
    if DRY_RUN:
        return {
            "status": "DRY_RUN",
            "significant_metabolites": 23,
            "top_upregulated": [
                {"metabolite": "Glucose-6-phosphate", "log2fc": 2.3, "fdr": 0.001},
                {"metabolite": "Lactate", "log2fc": 1.8, "fdr": 0.003},
            ],
            "message": "Simulated differential metabolite analysis"
        }

    # Real implementation
    data = pd.read_csv(data_file, index_col=0)

    group1_data = data.loc[group1_samples]
    group2_data = data.loc[group2_samples]

    results = []
    for metabolite in data.columns:
        g1_values = group1_data[metabolite].values
        g2_values = group2_data[metabolite].values

        # Statistical test
        if test_method == "wilcoxon":
            stat, pval = stats.mannwhitneyu(g1_values, g2_values, alternative='two-sided')
        else:
            stat, pval = stats.ttest_ind(g1_values, g2_values)

        # Effect size
        log2fc = np.log2(g1_values.mean() / g2_values.mean())

        results.append({
            "metabolite": metabolite,
            "log2fc": log2fc,
            "p_value": pval
        })

    # FDR correction
    results_df = pd.DataFrame(results)
    from scipy.stats import false_discovery_control
    results_df["fdr"] = false_discovery_control(results_df["p_value"])

    significant = results_df[results_df["fdr"] < fdr_threshold]

    return {
        "status": "success",
        "test_method": test_method,
        "significant_metabolites": len(significant),
        "top_upregulated": significant.nlargest(5, "log2fc").to_dict("records"),
        "top_downregulated": significant.nsmallest(5, "log2fc").to_dict("records"),
    }

# Add more tools here...

if __name__ == "__main__":
    mcp.run()
```

**3.2 Create __main__.py**

`servers/mcp-metabolomics/src/mcp_metabolomics/__main__.py`:
```python
"""Entry point for mcp-metabolomics server."""

from .server import mcp

if __name__ == "__main__":
    mcp.run()
```

**3.3 Test Locally**

```bash
# Set DRY_RUN mode
export METABOLOMICS_DRY_RUN=true

# Run server (will start MCP stdio server)
python -m mcp_metabolomics
```

### Phase 4: Testing (2-3 hours)

**4.1 Create Test Structure**

```bash
mkdir -p tests/unit/mcp-metabolomics/fixtures
```

**4.2 Write Unit Tests**

`tests/unit/mcp-metabolomics/test_server.py`:
```python
"""Tests for mcp-metabolomics server."""

import pytest
import os

def test_dry_run_enabled():
    """Test DRY_RUN mode is enabled by default."""
    from mcp_metabolomics.server import DRY_RUN
    # In test environment, should default to true
    assert DRY_RUN is True

@pytest.mark.asyncio
async def test_load_metabolomics_data_dry_run():
    """Test loading data in DRY_RUN mode."""
    from mcp_metabolomics.server import load_metabolomics_data

    result = await load_metabolomics_data._impl(
        data_file="/fake/path/data.csv"
    )

    assert result["status"] == "DRY_RUN"
    assert result["samples"] > 0
    assert result["metabolites"] > 0

@pytest.mark.asyncio
async def test_identify_differential_metabolites_dry_run():
    """Test differential analysis in DRY_RUN mode."""
    from mcp_metabolomics.server import identify_differential_metabolites

    result = await identify_differential_metabolites._impl(
        data_file="/fake/path/data.csv",
        group1_samples=["s1", "s2"],
        group2_samples=["s3", "s4"]
    )

    assert result["status"] == "DRY_RUN"
    assert "significant_metabolites" in result
    assert len(result["top_upregulated"]) > 0
```

**4.3 Create Test Fixtures**

Create synthetic test data in `tests/unit/mcp-metabolomics/fixtures/`:
- `abundance.csv` - Sample × metabolite matrix
- `metadata.csv` - Sample annotations

**4.4 Run Tests**

```bash
cd tests/unit/mcp-metabolomics
pytest -v --cov=../../../servers/mcp-metabolomics/src/mcp_metabolomics
```

### Phase 5: Documentation (1-2 hours)

**5.1 Create Server README**

`servers/mcp-metabolomics/README.md`:
```markdown
# mcp-metabolomics

MCP server for metabolomics data analysis (LC-MS, GC-MS)

## Tools

### 1. load_metabolomics_data
Load and validate metabolite abundance matrices

### 2. identify_differential_metabolites
Statistical testing for abundance differences between conditions

### 3. map_metabolites_to_pathways
KEGG/Reactome pathway enrichment

### 4. integrate_with_transcriptomics
Correlation analysis with mcp-multiomics data

## Installation

[Installation steps]

## Usage Examples

[Example prompts for Claude Desktop]

## Dependencies

[List of required packages]
```

**5.2 Create Architecture Doc**

`architecture/metabolomics/README.md`:
```markdown
# Metabolomics Analysis Architecture

[Workflow diagram with mermaid]

## Integration Points
- Clinical data (mcp-epic) → Sample metadata
- Multiomics (mcp-multiomics) → Transcriptomics correlation
- TCGA (mcp-mocktcga) → Population metabolite profiles
```

**5.3 Update Main Documentation**

Add to `/servers/README.md`:
```markdown
| 🧪 **mcp-metabolomics** | 5 | ✅ 80% real | [README →](mcp-metabolomics/README.md) |
```

Add to `/architecture/README.md`:
```markdown
| 🧪 **Metabolomics** | mcp-metabolomics | 5 | ✅ Partial (80%) | [metabolomics/README.md](metabolomics/README.md) |
```

### Phase 6: Claude Desktop Integration (30 minutes)

**6.1 Add to Configuration**

Edit `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "metabolomics": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/servers/mcp-metabolomics",
        "python",
        "-m",
        "mcp_metabolomics"
      ],
      "env": {
        "METABOLOMICS_DATA_DIR": "/path/to/data/metabolomics",
        "METABOLOMICS_CACHE_DIR": "/path/to/data/cache/metabolomics",
        "METABOLOMICS_DRY_RUN": "true"
      }
    }
  }
}
```

**6.2 Test in Claude Desktop**

1. Restart Claude Desktop
2. Ask: "What tools are available from the metabolomics server?"
3. Test a tool: "Use metabolomics server to identify differential metabolites..."

### Phase 7: GCP Deployment (1-2 hours)

**7.1 Create Dockerfile**

`servers/mcp-metabolomics/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities first
COPY shared/utils/ /app/shared/utils/

# Copy server code
COPY servers/mcp-metabolomics/ /app/servers/mcp-metabolomics/

# Install dependencies
WORKDIR /app/servers/mcp-metabolomics
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN uv sync --no-dev

# Set environment
ENV MCP_TRANSPORT=sse
ENV PORT=8080
ENV METABOLOMICS_DRY_RUN=true

# Run server
CMD ["python", "-m", "mcp_metabolomics"]
```

**7.2 Deploy to Cloud Run**

```bash
./infrastructure/deployment/deploy_to_gcp.sh --development --server mcp-metabolomics
```

**7.3 Test Deployment**

```bash
# Test via Claude API
python tests/integration/test_gcp_server.py --server metabolomics
```

---

## Testing Requirements

### Unit Tests (Required)

**Coverage target:** 50%+ for production servers, 35%+ for demo servers

**Test categories:**
1. **Smoke tests** - Server imports, DRY_RUN mode
2. **Tool registration** - All tools discovered by MCP
3. **Input validation** - Pydantic schemas catch invalid inputs
4. **DRY_RUN behavior** - Returns expected mock data
5. **Real data tests** (optional) - Process actual fixture data

**Test structure:**
```
tests/unit/mcp-metabolomics/
├── test_server.py           # Smoke tests
├── test_tools.py            # Individual tool tests
├── test_integration.py      # Multi-tool workflows
└── fixtures/
    ├── abundance.csv
    └── metadata.csv
```

### Integration Tests (Recommended)

Test multi-server workflows:
```python
# tests/integration/test_metabolomics_multiomics.py

async def test_metabolomics_transcriptomics_integration():
    """Test correlation between metabolites and gene expression."""

    # Step 1: Load metabolomics data
    metab_result = await metabolomics_server.load_data(...)

    # Step 2: Load transcriptomics from multiomics
    rna_result = await multiomics_server.get_rna_data(...)

    # Step 3: Correlate
    corr_result = await metabolomics_server.correlate_with_genes(...)

    assert len(corr_result["significant_correlations"]) > 0
```

---

## Documentation Requirements

### 1. Server README (Required)

**Location:** `/servers/mcp-{server}/README.md`

**Sections:**
- Overview & purpose
- Tool list with descriptions
- Installation instructions
- Usage examples (Claude Desktop prompts)
- Dependencies & requirements
- Testing guide
- Troubleshooting

### 2. Architecture Documentation (Required)

**Location:** `/architecture/{modality}/README.md`

**Sections:**
- Workflow diagram (mermaid)
- Integration points with other servers
- Data formats & standards
- Example use cases (PatientOne integration)

### 3. API Documentation (Auto-generated)

FastMCP automatically generates docstrings into MCP tool schemas. Ensure:
- Clear parameter descriptions
- Return value documentation
- Usage examples in docstrings

### 4. Update Central Docs (Required)

- Add row to `/servers/README.md#-server-status`
- Add section to `/architecture/README.md#-architecture-by-analysis-modality`
- Update PatientOne workflow if applicable

---

## Deployment Guide

### Local Development (Claude Desktop)

1. Install server: `cd servers/mcp-metabolomics && uv sync`
2. Add to `claude_desktop_config.json`
3. Set `DRY_RUN=true` initially
4. Restart Claude Desktop
5. Test with prompts

### GCP Cloud Run (Production)

**Prerequisites:**
- GCP project with billing enabled
- Cloud Run API enabled
- Docker configured

**Deployment steps:**
```bash
# 1. Build and deploy
./infrastructure/deployment/deploy_to_gcp.sh --development --server mcp-metabolomics

# 2. Test deployment
curl https://mcp-metabolomics-{hash}.run.app/health

# 3. Test via Claude API
python tests/integration/test_gcp_server.py --server metabolomics
```

**Environment variables for production:**
- `METABOLOMICS_DRY_RUN=false` (use real data)
- `METABOLOMICS_DATA_DIR=/gcs/bucket/data` (GCS mount)
- `METABOLOMICS_API_KEY=xxx` (if calling external APIs)

---

## Example: Metabolomics Server

See complete worked example in:
- `/docs/mcp-server-boilerplate/` - Reusable template
- `/docs/examples/metabolomics-server/` - Concrete implementation

---

## Integration Checklist

Use this checklist when adding your new server:

### Planning Phase
- [ ] Defined modality scope (data types, tools, dependencies)
- [ ] Reviewed existing servers for patterns
- [ ] Designed tool signatures with clear docstrings
- [ ] Identified integration points with other servers

### Implementation Phase
- [ ] Created server directory structure
- [ ] Wrote `pyproject.toml` with dependencies
- [ ] Implemented server.py with FastMCP
- [ ] Added `__main__.py` entry point
- [ ] Tested locally with DRY_RUN=true

### Testing Phase
- [ ] Created test directory structure
- [ ] Wrote unit tests (smoke + tool tests)
- [ ] Created test fixtures (synthetic data)
- [ ] Achieved >35% coverage
- [ ] Added integration tests (optional)

### Documentation Phase
- [ ] Created server README with examples
- [ ] Created architecture document with diagram
- [ ] Updated `/servers/README.md#-server-status`
- [ ] Updated `/architecture/README.md`
- [ ] Added to PatientOne workflow (if applicable)

### Integration Phase
- [ ] Added to `claude_desktop_config.json`
- [ ] Tested in Claude Desktop
- [ ] Verified multi-server workflows
- [ ] Created example prompts

### Deployment Phase
- [ ] Created Dockerfile
- [ ] Deployed to GCP Cloud Run
- [ ] Tested SSE endpoint
- [ ] Validated via Claude API
- [ ] Updated deployment documentation

### Validation Phase
- [ ] Runs successfully in DRY_RUN mode
- [ ] Processes real data correctly (if applicable)
- [ ] Integrates with ≥2 other servers
- [ ] Documented in all required locations
- [ ] Tests pass in CI/CD (if configured)

---

## Resources

### Documentation
- [FastMCP Documentation](https://gofastmcp.com)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Installation Guide](../getting-started/installation.md)

### Code Examples
- [Existing Servers](../../servers/) - Study patterns from mcp-multiomics, mcp-spatialtools
- [Server Template](../../servers/mcp-server-boilerplate/) - Reusable boilerplate

### Testing
- [Test Examples](../../tests/unit/) - Learn from existing test suites
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Testing async tools

### Deployment
- [GCP Integration Guide](../reference/testing/gcp-integration.md)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## Getting Help

**Questions about architecture?**
- Review existing servers: [servers/](../../servers/)
- Check architecture docs: [architecture/](../reference/architecture)

**Questions about MCP protocol?**
- MCP specification: https://modelcontextprotocol.io/
- FastMCP docs: https://gofastmcp.com

**Need code review?**
- Open GitHub issue with `[new-server]` tag
- Share server implementation for feedback

---

**Last Updated:** 2026-01-12
**Maintainer:** spatial-mcp contributors
**License:** Apache 2.0
