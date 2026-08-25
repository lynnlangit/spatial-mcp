# Developer Quick Reference

Cheat sheet for common development tasks in the precision-medicine-mcp platform.

---

## Project Structure

```
precision-medicine-mcp/
├── servers/                      # 19 MCP servers (127 tools) + boilerplate template
│   ├── mcp-fgbio/               # Reference genomes, VCF/FASTQ (4 tools)
│   ├── mcp-genomic-results/     # Somatic variant/CNV parsing + allelic-imbalance CNV suite (12 tools)
│   ├── mcp-multiomics/          # RNA/Protein/Phospho (10 tools, best reference)
│   ├── mcp-spatialtools/        # Spatial transcriptomics (16 tools)
│   ├── mcp-cibersortx/          # Immune deconvolution (5 tools)
│   ├── mcp-neoantigen/          # Neoantigen prediction & HLA binding (6 tools)
│   ├── mcp-opentargets/         # Drug-target associations (6 tools)
│   ├── mcp-perturbation/        # GEARS perturbation prediction (8 tools)
│   ├── mcp-quantum-celltype-fidelity/ # Quantum cell type fidelity (6 tools)
│   ├── mcp-openimagedata/       # Histology image processing (5 tools)
│   ├── mcp-deepcell/            # Cell segmentation (3 tools)
│   ├── mcp-cell-classify/       # Cell phenotype classification (3 tools)
│   ├── mcp-geodownload/         # GEO/SRA dataset download (6 tools)
│   ├── mcp-cardiometabolic/     # CVD risk scoring & preventive health (14 tools)
│   ├── mcp-deidentify/          # HIPAA Safe Harbor de-identification (6 tools)
│   ├── mcp-epic/                # Real Epic FHIR (local-only, 4 tools)
│   ├── mcp-mockepic/            # Synthetic FHIR for demos (3 tools)
│   ├── mcp-mocktcga/            # Mock TCGA cohort comparison (5 tools)
│   ├── mcp-patient-report/      # PDF report generation (5 tools)
│   └── mcp-server-boilerplate/  # Template for new servers
├── tests/
│   ├── unit/                    # Unit tests by server
│   ├── integration/             # Multi-server tests
│   ├── fixtures/                # Canonical values (pat001, pat002, pat003)
│   ├── manual_testing/          # Manual test scripts
│   └── verification/            # Verification checks
├── docs/
│   ├── INDEX.md                 # Central navigation
│   ├── for-developers/          # Developer guides (this section)
│   ├── for-educators/           # Teaching materials, walkthrough notebook
│   ├── for-funders/             # ROI, grants
│   ├── for-hospitals/           # Deployment, security, HIPAA
│   ├── for-patients/            # Patient-facing overviews
│   ├── for-researchers/         # Research guides, paper v19, open questions
│   ├── getting-started/         # Installation, desktop configs
│   └── reference/               # Architecture, testing, shared canonical docs
├── data/                        # Patient data and reference files
│   ├── patient-data/PAT001-OVC-2025/  # Synthetic HGSOC data
│   ├── pat002/                        # Synthetic ER+ breast cancer data
│   └── pat003/                        # Synthetic preventive CVD data
├── ui/                          # User interfaces
│   ├── streamlit-app/           # Main Streamlit web app
│   ├── streamlit-app-students/  # Simplified student version
│   ├── dashboard/               # Monitoring dashboard
│   └── jupyter-notebook/        # Jupyter integration
└── infrastructure/              # GCP deployment configs (Docker, Cloud Run)
```

---

## Common Commands

### Setup & Installation

```bash
# Clone repository
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install server for development
cd servers/mcp-{server}
uv sync --dev

# Verify installation
uv run python -m mcp_{server} --help
```

### Running Servers

```bash
# Run server locally (STDIO mode)
export SERVER_DRY_RUN=true
python -m mcp_{server}

# Run with real data
export SERVER_DRY_RUN=false
export SERVER_DATA_DIR=/path/to/data
python -m mcp_{server}

# Run server with SSE transport (for cloud)
export MCP_TRANSPORT=sse
export PORT=8080
python -m mcp_{server}
```

### Testing

```bash
# Run all tests for a server
cd tests/unit/mcp-{server}
pytest -v

# Run with coverage
pytest -v --cov=../../../servers/mcp-{server}/src/mcp_{server}

# Show missing coverage
pytest --cov-report=term-missing

# Run specific test
pytest test_server.py::test_function_name -v

# Run with real data (not DRY_RUN)
SERVER_DRY_RUN=false pytest -v

# Run fast (skip slow tests)
pytest -v -m "not slow"
```

### Deployment

```bash
# Deploy to GCP Cloud Run (development)
./infrastructure/deployment/deploy_to_gcp.sh --development --server mcp-{server}

# Deploy to production
./infrastructure/deployment/deploy_to_gcp.sh --production --server mcp-{server}

# Check deployment
curl https://mcp-{server}-{hash}.run.app/health

# View logs
gcloud run logs read mcp-{server} --region=us-central1
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Stage changes
git add .

# Commit with conventional format
git commit -m "feat(server): Add new tool for X"

# Push to fork
git push origin feature/your-feature-name

# Update from upstream
git fetch upstream
git merge upstream/main
```

---

## FastMCP Patterns

### Basic Tool

```python
from fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
async def my_tool(param1: str, param2: int = 10) -> dict:
    """
    Clear description for Claude.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)

    Returns:
        Dictionary with results
    """
    if DRY_RUN:
        return {"status": "DRY_RUN", "data": "simulated"}

    # Real implementation
    result = do_work(param1, param2)
    return {"status": "success", "result": result}
```

### Tool with File I/O

```python
@mcp.tool()
async def process_file(input_file: str, output_dir: str) -> dict:
    """Process data file and save results."""

    # Validate inputs
    if not os.path.exists(input_file):
        return {
            "status": "error",
            "error": "FileNotFoundError",
            "message": f"File not found: {input_file}"
        }

    # Process
    data = pd.read_csv(input_file)
    results = analyze(data)

    # Save output
    output_file = os.path.join(output_dir, "results.csv")
    results.to_csv(output_file, index=False)

    return {
        "status": "success",
        "output_file": output_file,
        "num_results": len(results)
    }
```

### Tool with Error Handling

```python
@mcp.tool()
async def risky_operation(param: str) -> dict:
    """Operation that might fail."""

    try:
        result = do_something_risky(param)
        return {"status": "success", "result": result}

    except ValueError as e:
        return {
            "status": "error",
            "error": "ValueError",
            "message": f"Invalid parameter: {param}",
            "suggestion": "Try values in range [0, 100]"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": type(e).__name__,
            "message": str(e)
        }
```

---

## Configuration

### Environment Variables

```bash
# Common across all servers
export {SERVER}_DRY_RUN=true         # Enable synthetic data mode
export {SERVER}_DATA_DIR=/path       # Data directory
export {SERVER}_CACHE_DIR=/path     # Cache directory

# MCP transport
export MCP_TRANSPORT=stdio           # For local (Claude Desktop)
export MCP_TRANSPORT=sse             # For cloud (GCP Cloud Run)
export PORT=8080                     # SSE port

# Example for mcp-multiomics
export MULTIOMICS_DRY_RUN=false
export MULTIOMICS_DATA_DIR=/data/multiomics
export MULTIOMICS_CACHE_DIR=/data/cache/multiomics
```

### Claude Desktop Config

```json
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

**Config location:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

---

## Testing Patterns

### Basic Test Structure

```python
# tests/unit/mcp-{server}/test_server.py

import pytest
import os

def test_server_imports():
    """Test server imports successfully."""
    from mcp_{server} import server
    assert server.mcp is not None

def test_dry_run_enabled():
    """Test DRY_RUN defaults to true."""
    from mcp_{server}.server import DRY_RUN
    assert DRY_RUN is True

@pytest.mark.asyncio
async def test_tool_dry_run():
    """Test tool in DRY_RUN mode."""
    from mcp_{server}.server import my_tool

    result = await my_tool._impl(param="test")

    assert result["status"] == "DRY_RUN"
    assert "data" in result
```

### Test with Fixtures

```python
import pytest
import pandas as pd

@pytest.fixture
def sample_data():
    """Create sample test data."""
    return pd.DataFrame({
        "gene": ["BRCA1", "TP53", "EGFR"],
        "expression": [5.2, 8.1, 3.7]
    })

@pytest.mark.asyncio
async def test_with_fixture(sample_data):
    """Test using fixture data."""
    from mcp_{server}.server import analyze_expression

    result = await analyze_expression._impl(data=sample_data)

    assert result["status"] == "success"
    assert result["num_genes"] == 3
```

### Test with Mock

```python
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
@patch('mcp_{server}.server.external_api_call')
async def test_with_mock(mock_api):
    """Test with mocked external API."""
    mock_api.return_value = {"data": "mocked"}

    from mcp_{server}.server import tool_using_api

    result = await tool_using_api._impl()

    assert result["status"] == "success"
    mock_api.assert_called_once()
```

---

## Common Data Formats

### Patient Data Structure

```
/data/patient-data/
├── PAT001-OVC-2025/                  # Patient ID
│   ├── clinical/
│   │   └── fhir_bundle.json          # FHIR clinical data
│   ├── genomic/
│   │   ├── variants.vcf              # VCF variants
│   │   └── aligned_reads.bam         # BAM alignment
│   ├── multiomics/
│   │   ├── rna_counts.csv            # RNA-seq counts
│   │   ├── protein_abundance.csv     # Proteomics
│   │   └── phospho_abundance.csv     # Phosphoproteomics
│   ├── spatial/
│   │   ├── tissue_positions.csv      # Visium spots
│   │   ├── filtered_feature_matrix/  # Gene expression matrix
│   │   └── spatial/                  # Spatial images
│   └── imaging/
│       ├── H_and_E_slide_001.tif    # H&E histology
│       └── multiplex_IF_tumor.tif   # Multiplex IF
```

### Common File Formats

**CSV (Counts/Abundance):**
```csv
gene_id,sample_1,sample_2,sample_3
BRCA1,245.3,312.7,198.4
TP53,512.1,489.3,502.8
EGFR,123.5,145.2,132.7
```

**VCF (Variants):**
```
##fileformat=VCFv4.2
#CHROM  POS     ID      REF     ALT     QUAL    FILTER  INFO
chr17   7674220 .       C       A       100     PASS    DP=50
```

**FHIR JSON (Clinical):**
```json
{
  "resourceType": "Patient",
  "id": "patient-001",
  "gender": "female",
  "birthDate": "1965"
}
```

---

## Common Tool Patterns

### List Available Data

```python
@mcp.tool()
async def list_available_files(data_dir: str) -> dict:
    """List files available for analysis."""

    files = []
    for root, dirs, filenames in os.walk(data_dir):
        for f in filenames:
            if f.endswith((".csv", ".vcf", ".bam")):
                files.append(os.path.join(root, f))

    return {
        "status": "success",
        "num_files": len(files),
        "files": files[:20]  # First 20
    }
```

### Validate Input File

```python
@mcp.tool()
async def validate_vcf(vcf_file: str) -> dict:
    """Validate VCF file format."""

    if not os.path.exists(vcf_file):
        return {
            "status": "error",
            "error": "File not found",
            "message": f"VCF file not found: {vcf_file}"
        }

    # Check format
    try:
        with open(vcf_file) as f:
            first_line = f.readline()
            if not first_line.startswith("##fileformat=VCF"):
                return {
                    "status": "error",
                    "error": "Invalid format",
                    "message": "File is not valid VCF format"
                }
    except Exception as e:
        return {
            "status": "error",
            "error": type(e).__name__,
            "message": str(e)
        }

    return {
        "status": "success",
        "message": "Valid VCF file",
        "file_path": vcf_file
    }
```

### Return Visualization

```python
@mcp.tool()
async def create_plot(data_file: str, output_dir: str) -> dict:
    """Create visualization and return path."""

    data = pd.read_csv(data_file)

    # Create plot
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    plt.scatter(data["x"], data["y"])
    plt.xlabel("X")
    plt.ylabel("Y")

    # Save
    plot_file = os.path.join(output_dir, "plot.png")
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        "status": "success",
        "plot_file": plot_file,
        "message": f"Plot saved to {plot_file}"
    }
```

---

## Debugging Tips

### Enable Verbose Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@mcp.tool()
async def my_tool(param: str) -> dict:
    logger.debug(f"Tool called with param={param}")

    result = do_work(param)
    logger.debug(f"Result: {result}")

    return {"status": "success", "result": result}
```

### Check Claude Desktop Logs

**macOS:**
```bash
tail -f ~/Library/Logs/Claude/mcp-server-{server}.log
```

**Windows:**
```powershell
Get-Content -Path "$env:APPDATA\Claude\logs\mcp-server-{server}.log" -Wait
```

### Test Tool Directly

```python
# In Python REPL
import asyncio
from mcp_{server}.server import my_tool

result = asyncio.run(my_tool._impl(param="test"))
print(result)
```

### Common Issues

**Issue: "Server not found in Claude Desktop"**
- Check `claude_desktop_config.json` path
- Verify JSON syntax (no trailing commas)
- Restart Claude Desktop

**Issue: "Tool call times out"**
- Check if tool takes >30 seconds
- Add timeout handling
- Consider breaking into smaller tools

**Issue: "Import errors"**
- Verify virtual environment activated
- Check `pip install -e ".[dev]"` succeeded
- Verify Python version (≥3.11)

---

## Useful Links

### Documentation
- **FastMCP Docs:** https://gofastmcp.com
- **MCP Spec:** https://modelcontextprotocol.io/
- **Claude API:** https://docs.anthropic.com/

### Code Examples
- **Best reference:** `/servers/mcp-multiomics/` (91 tests, 68% coverage)
- **Server template:** `/servers/mcp-server-boilerplate/`
- **Test examples:** `/tests/unit/`

### Guides
- **Adding a server:** [ADD_NEW_MODALITY_SERVER.md](ADD_NEW_MODALITY_SERVER.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Quick Checklist: Adding a New Server

- [ ] Plan modality scope (5-8 tools, dependencies)
- [ ] Create server directory: `servers/mcp-{server}/`
- [ ] Write `pyproject.toml` with dependencies
- [ ] Implement server.py with FastMCP tools
- [ ] Add `__main__.py` entry point
- [ ] Write tests (≥50% coverage for production)
- [ ] Create fixtures: `tests/unit/mcp-{server}/fixtures/`
- [ ] Create server README with examples
- [ ] Create architecture doc with diagram
- [ ] Update `/servers/README.md#-server-status`
- [ ] Update `/architecture/README.md`
- [ ] Add to `claude_desktop_config.json`
- [ ] Test in Claude Desktop
- [ ] Create Dockerfile
- [ ] Deploy to GCP Cloud Run
- [ ] Test SSE endpoint
