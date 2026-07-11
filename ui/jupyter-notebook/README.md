# Jupyter Notebook MCP Client - Precision Medicine

Interactive Jupyter notebooks for testing MCP servers via Claude API. Perfect for data scientists and researchers who want to analyze spatial transcriptomics, multi-omics, and genomics data.

> **Related:** [Deployment Templates](../../docs/reference/shared/deployment-templates.md) | [Cost Analysis](../../docs/reference/shared/cost-analysis.md) | [Platform Overview](../../docs/reference/shared/README.md)

<img src="../../data/images/jupyter-preview.png" width="800" alt="Jupyter Notebook Preview" style="display:none">

## Features

- **MCP Servers** — Access all deployed bioinformatics tools ([Server Registry](../../docs/reference/shared/server-registry.md))
- **Group-based notebooks** - Organized by domain (imaging, genomics, clinical, workflow/ML)
- **Shared MCPClient** - Single `mcp_utils.py` module used by all notebooks
- **Token usage tracking** - Monitor API costs per query
- **Built-in visualizations** - matplotlib, seaborn, plotly examples
- **Reproducible analysis** - Save and share workflows

## Notebooks

| Notebook | Servers | Description |
|---|---|---|
| `00-setup-and-test.ipynb` | all | Install deps, verify API key, test connectivity |
| `01-imaging.ipynb` | deepcell, cell-classify, openimagedata | Cell segmentation, phenotyping, MxIF images |
| `02-genomics-omics.ipynb` | fgbio, multiomics, spatialtools, mocktcga, perturbation | FASTQ QC, spatial analysis, multi-omics, GEARS |
| `03-clinical.ipynb` | mockepic, patient-report | EHR/FHIR data, patient-facing reports |
| `04-workflow-ml.ipynb` | quantum-celltype-fidelity | Quantum fidelity |
| `05-integration.ipynb` | cross-server | PatientOne end-to-end precision-medicine workflows |

The original `mcp_client.ipynb` is retained for backwards compatibility.

## Quick Start (2 minutes)

### Prerequisites

- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Local Installation

```bash
# 1. Navigate to notebook directory
cd ui/jupyter-notebook

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
export ANTHROPIC_API_KEY=your_key_here  # On Windows: set ANTHROPIC_API_KEY=your_key_here

# Or create a .env file:
cp .env.example .env
# Edit .env and add your API key

# 5. Start Jupyter
jupyter lab
```

The notebooks will open in your browser at http://localhost:8888

## Project Structure

```
ui/jupyter-notebook/
├── mcp_utils.py               # Shared MCPClient class + server config (used by all notebooks)
├── 00-setup-and-test.ipynb    # Setup and connectivity verification
├── 01-imaging.ipynb           # Imaging & cell analysis examples
├── 02-genomics-omics.ipynb    # Genomics & multi-omics examples
├── 03-clinical.ipynb          # Clinical data examples
├── 04-workflow-ml.ipynb       # Workflow & ML examples
├── 05-integration.ipynb       # Cross-server integration workflows
├── mcp_client.ipynb           # Original monolithic notebook (legacy)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── Dockerfile                 # Container for Cloud Run
├── .dockerignore              # Docker ignore rules
├── deploy.sh                  # Cloud Run deployment script
├── deploy_to_vertex_ai.sh     # Vertex AI Workbench deployment
├── jupyterhub_config.py       # JupyterHub configuration
└── README.md                  # This file
```

## Available MCP Servers

All servers are pre-configured in `mcp_utils.py`:

### Imaging (production)
- **deepcell** - DeepCell-TF cell segmentation and marker quantification for MxIF
- **cell-classify** - Cell phenotype classification and visualization
- **openimagedata** - H&E/MxIF image loading, registration, feature extraction, composites

### Genomics / Omics
- **fgbio** - Genomic reference data and FASTQ validation (production)
- **multiomics** - Multi-omics integration: RNA/Protein/Phospho (production)
- **spatialtools** - Spatial transcriptomics analysis (production)
- **mocktcga** - Mock TCGA cancer genomics data (mock)
- **perturbation** - GEARS perturbation prediction for treatment response (production)

### Clinical
- **mockepic** - Mock EHR/FHIR data (mock)
- **patient-report** - Patient-facing PDF reports with plain-language summaries (production)

### Workflow / ML
- **quantum-celltype-fidelity** - Quantum computing for cell type validation and immune evasion (production)

## MCPClient API Reference

All notebooks import from `mcp_utils.py`:

```python
from mcp_utils import MCPClient, MCP_SERVERS, SERVER_GROUPS, list_servers, print_result

mcp = MCPClient()
result = mcp.call_servers(
    prompt="Analyze spatial transcriptomics data for Patient-001.",
    servers=["spatialtools", "multiomics"],
    model="claude-sonnet-4-5",   # default
    max_tokens=4096,              # default
    clear_history=True,           # reset conversation
)
print_result(result)
```

Every call returns:

```python
{
    "response": "...",
    "usage": {
        "input_tokens": 5124,
        "output_tokens": 483,
        "total_tokens": 5607,
        "estimated_cost_usd": 0.0226
    },
    "model": "claude-sonnet-4-5",
    "servers_used": ["spatialtools", "multiomics"]
}
```

## Configuration

### API Key Security

| Environment | Storage Method | Security |
|---|---|---|
| **Local** | `.env` file (gitignored) | Not committed to git |
| **Cloud JupyterLab** | Environment variable (encrypted) | Managed by Google Cloud |
| **Browser** | Never exposed | Key stays server-side |

### Cost Estimates

- **Per query:** ~$0.02-0.08 (Sonnet)
- **Typical session (10 queries):** ~$0.20-0.80
- **Cloud JupyterLab:** ~$0.50-2.00/hr active use, scales to zero when idle

See [Cost Analysis](../../docs/reference/shared/cost-analysis.md) for detailed breakdowns.

## Deployment

### GCP Cloud Run (Current)

```bash
export ANTHROPIC_API_KEY=your_key_here
./deploy.sh
```

### GCP Vertex AI Workbench (Alternative)

```bash
export ANTHROPIC_API_KEY=your_key_here
./deploy_to_vertex_ai.sh
```

## Troubleshooting

### API Key Missing
```bash
export ANTHROPIC_API_KEY=your_key_here
# Or create .env:  cp .env.example .env
```

### MCP Servers Not Responding
1. Check server status in [GCP Cloud Run Console](https://console.cloud.google.com/run)
2. Verify URLs match deployed URLs
3. Test: `curl https://<your-streamlit-app-url>.a.run.app/sse`

### Module Import Errors
```bash
pip install -r requirements.txt
```

## Support

- **Issues:** [GitHub Issues](https://github.com/lynnlangit/precision-medicine-mcp/issues)
- **Documentation:** [Main README](../../README.md)
- **MCP Spec:** [Model Context Protocol](https://modelcontextprotocol.io/)
- **Anthropic Docs:** [Claude API](https://docs.anthropic.com/)

[GCP Cloud Run](https://cloud.google.com/run)

**Part of the Precision Medicine MCP suite** - Enabling AI-driven bioinformatics for cancer research.
