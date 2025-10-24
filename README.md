# Spatial MCP Demonstration POC

AI-Orchestrated Spatial Transcriptomics Bioinformatics Pipeline using Model Context Protocol

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-2025--06--18-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## Overview

This project demonstrates the power of **Model Context Protocol (MCP)** in orchestrating complex bioinformatics workflows for spatial transcriptomics. Using Claude Desktop as the AI orchestrator, the system coordinates 8 specialized MCP servers to process spatial genomics data through a 5-stage pipeline.

### Key Features

- 🤖 **AI-Driven Orchestration** - Claude coordinates multi-server workflows
- 🧬 **Modular Architecture** - 8 specialized servers, each with single responsibility
- 🔒 **Production-Ready** - Comprehensive testing, logging, and security
- 🚀 **Scalable Design** - Containerized, cloud-ready deployment
- 📊 **Industry Tools** - FGbio, TCGA, Hugging Face, Seqera Platform integration

## Architecture

![Spatial MCP Architecture](https://github.com/lynnlangit/spatial-mcp/blob/main/spatial-mcp-arch.png)

### Pipeline Flow

```
┌─────────────┐    ┌──────────────┐    ┌───────────┐    ┌────────────────┐    ┌──────────┐
│ 1. Ingest   │───▶│ 2. Segment   │───▶│ 3. Align  │───▶│ 4. Quantify    │───▶│ 5. Analyze│
│   & QC      │    │   Spatial    │    │   Reads   │    │   Expression   │    │  Results  │
└─────────────┘    └──────────────┘    └───────────┘    └────────────────┘    └──────────┘
```

### MCP Servers

| Server | Status | Purpose |
|--------|--------|---------|
| **mcp-FGbio** | ✅ Phase 1 | Genomic reference data & FASTQ processing |
| **mcp-spatialtools** | ✅ Phase 2 | Core spatial transcriptomics processing (QC, alignment, segmentation) |
| **mcp-openImageData** | ✅ Phase 2 | Histology image processing & spatial registration |
| **mcp-seqera** | ✅ Phase 3 | Nextflow workflow orchestration via Seqera Platform |
| **mcp-huggingFace** | ✅ Phase 3 | ML models for genomics (DNABERT, Geneformer, scGPT) |
| **mcp-deepcell** | ✅ Phase 3 | Deep learning cell segmentation and phenotyping |
| **mcp-mockEpic** | ✅ Phase 3 | Mock Epic EHR integration with synthetic patient data |
| **mcp-tcga** | 📋 Future | TCGA cancer genomics data (optional enhancement) |

## Quick Start

### Prerequisites

- Python 3.11+
- Claude Desktop
- 16GB+ RAM
- 50GB free disk space

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/spatial-mcp.git
cd spatial-mcp

# Run setup script
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh

# Install mcp-fgbio (Phase 1)
cd servers/mcp-fgbio
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest
```

### Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fgbio": {
      "command": "python",
      "args": ["-m", "mcp_fgbio"],
      "cwd": "/absolute/path/to/spatial-mcp/servers/mcp-fgbio",
      "env": {
        "PYTHONPATH": "/absolute/path/to/spatial-mcp/servers/mcp-fgbio/src",
        "FGBIO_REFERENCE_DATA_DIR": "/absolute/path/to/spatial-mcp/data/reference",
        "FGBIO_CACHE_DIR": "/absolute/path/to/spatial-mcp/data/cache",
        "FGBIO_DRY_RUN": "true"
      }
    }
  }
}
```

Restart Claude Desktop and try:

```
What MCP servers are available?
Can you fetch information about the hg38 reference genome?
```

## Documentation

- 📖 **[Setup Guide](docs/setup_guide.md)** - Complete installation and configuration
- 🏗️ **[Architecture Document](Spatial_MCP_POC_Architecture.md)** - Full technical architecture
- 🎨 **[Visual Diagram](Spatial_MCP_Architecture_Diagram.html)** - One-page architecture overview
- 🔧 **[mcp-FGbio README](servers/mcp-fgbio/README.md)** - FGbio server documentation

## Project Status

### ✅ Phase 1: Foundation (Complete)

- [x] Project structure and shared utilities
- [x] mcp-FGbio server with 4 tools and 3 resources
- [x] Comprehensive unit tests (>80% coverage)
- [x] Integration test framework
- [x] Claude Desktop configuration
- [x] Documentation and README files

### ✅ Phase 2: Core Processing (Complete)

- [x] mcp-spatialtools server with 4 processing tools
- [x] mcp-openImageData server with 3 image tools
- [x] End-to-end pipeline orchestration capability
- [x] Quality control → Segmentation → Alignment workflow
- [x] Updated Claude Desktop config for all 3 servers

### ✅ Phase 3: Advanced Analysis (Complete)

- [x] mcp-seqera with Nextflow workflow orchestration (3 tools, 1 resource)
- [x] mcp-huggingFace with ML genomics models (3 tools, 2 resources)
- [x] mcp-deepcell for cell segmentation (2 tools, 1 resource)
- [x] mcp-mockEpic with synthetic clinical data (3 tools, 1 resource)
- [x] Complete POC with all 7 servers integrated
- [x] Full demonstration workflow capability

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run integration tests
pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Example Usage

Once configured with Claude Desktop, you can use natural language to orchestrate bioinformatics workflows:

**Example 1: Fetch Reference Genome**
```
Claude, please download the hg38 reference genome and tell me about its characteristics.
```

**Example 2: Validate FASTQ Data**
```
I have a FASTQ file at /data/sample.fastq.gz. Can you validate it and check if the quality is good enough for analysis?
```

**Example 3: Complete Workflow**
```
I need to process spatial transcriptomics data:
1. Fetch the hg38 reference
2. Validate my FASTQ files at /data/sample_R1.fastq.gz and /data/sample_R2.fastq.gz
3. Extract the 12bp UMIs from read 1
4. Look up the genomic coordinates for TP53 gene
```

## Technology Stack

- **MCP Framework:** FastMCP (Python)
- **AI Orchestrator:** Claude Desktop
- **Bioinformatics Tools:** FGbio, STAR, samtools, bedtools
- **ML Frameworks:** Hugging Face Transformers, PyTorch
- **Workflow Engine:** Nextflow (via Seqera Platform)
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Deployment:** Docker, Kubernetes (future)

## Contributing

We welcome contributions! Please see our development guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure tests pass (`pytest`)
5. Format code (`black`, `ruff`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Model Context Protocol** - Anthropic's open standard for AI-data integration
- **BioinfoMCP** - Inspiration for bioinformatics tool integration
- **FGbio** - Fulcrum Genomics bioinformatics toolkit
- **TCGA** - The Cancer Genome Atlas program
- **Seqera Platform** - Nextflow workflow orchestration

## References

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [BioinfoMCP Paper](https://arxiv.org/html/2510.02139v1)
- [Spatial Transcriptomics Review](https://academic.oup.com/nar/article/53/12/gkaf536/8174767)

## Contact

- **Issues:** [GitHub Issues](https://github.com/your-org/spatial-mcp/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/spatial-mcp/discussions)

---

**Built with ❤️ for the bioinformatics community**
