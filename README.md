# Spatial MCP Demonstration POC

AI-Orchestrated Spatial Transcriptomics Bioinformatics Pipeline using Model Context Protocol

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-2025--06--18-green.svg)](https://modelcontextprotocol.io/)
[![Claude Desktop](https://img.shields.io/badge/Claude-Desktop-orange.svg)](https://claude.ai/download)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## What's In It For You?

**Are you tired of writing glue code to connect bioinformatics tools?** This POC demonstrates a fundamentally different approach to spatial transcriptomics analysis: instead of manually chaining together FASTQ validators, aligners, expression quantifiers, and statistical tools through brittle shell scripts, you **describe your analysis goals in natural language** and let Claude orchestrate the entire pipeline (example screenshot shown below).

**Why this matters for bioinformaticians:**
- ✅ **No more bash scripts from hell** - Replace complex pipeline code with conversational analysis requests
- ✅ **Instant access to 31 genomics tools** - From FASTQ QC to TCGA comparisons, all via natural language
- ✅ **Reproducible by default** - Every analysis is logged, versioned, and repeatable
- ✅ **Modular & extensible** - Add new tools as MCP servers without rewriting your pipeline
- ✅ **Tested with real workflows** - [18 complete example prompts](docs/MCP_POC_Example_Prompts.md) from QC to publication-ready analysis

**Try it yourself:**
```
Claude, I have 10x Visium spatial transcriptomics data. Please:
1. Validate my FASTQ files (sample_R1.fastq.gz, sample_R2.fastq.gz)
2. Extract UMIs and spatial barcodes
3. Filter spots with <200 genes detected
4. Perform differential expression between tumor and normal regions
5. Run pathway enrichment on upregulated genes
6. Compare key marker genes to TCGA breast cancer cohorts
```
<img src="https://github.com/lynnlangit/spatial-mcp/blob/main/data/images/Claude-client.png" width=800>

This single prompt orchestrates **6 different tools across 4 MCP servers**, generates statistical results, biological interpretations, and TCGA comparisons—all without writing a single line of pipeline code.

## Overview

This project demonstrates the power of **Model Context Protocol (MCP)** in orchestrating complex bioinformatics workflows for spatial transcriptomics. Using Claude Desktop as the AI orchestrator, the system coordinates **8 specialized MCP servers** with **31 tools** to process spatial genomics data through a 5-stage pipeline.

### Key Features

- 🤖 **AI-Driven Orchestration** - Claude coordinates multi-server workflows
- 🧬 **Modular Architecture** - 8 specialized servers, each with single responsibility
- 🔒 **Production-Ready** - Comprehensive testing, logging, and security
- 🚀 **Scalable Design** - Containerized, cloud-ready deployment
- 📊 **Industry Tools** - FGbio, TCGA, Hugging Face, Seqera Platform integration

## Architecture

![Spatial MCP Architecture](https://github.com/lynnlangit/spatial-mcp/blob/main/architecture/spatial-mcp-arch.png)

### Pipeline Flow

```
┌─────────────┐    ┌──────────────┐    ┌───────────┐    ┌────────────────┐    ┌──────────┐
│ 1. Ingest   │───▶│ 2. Segment   │───▶│ 3. Align  │───▶│ 4. Quantify    │───▶│ 5. Analyze│
│   & QC      │    │   Spatial    │    │   Reads   │    │   Expression   │    │  Results  │
└─────────────┘    └──────────────┘    └───────────┘    └────────────────┘    └──────────┘
```

### MCP Servers

| Server | Tools | Status | Purpose |
|--------|-------|--------|---------|
| **mcp-FGbio** | 4 | ✅ Phase 1 | Genomic reference data & FASTQ processing |
| **mcp-spatialtools** | 8 | ✅ Enhanced | Core spatial processing + advanced analysis |
| **mcp-openImageData** | 3 | ✅ Phase 2 | Histology image processing & spatial registration |
| **mcp-seqera** | 3 | ✅ Phase 3 | Nextflow workflow orchestration via Seqera Platform |
| **mcp-huggingFace** | 3 | ✅ Phase 3 | ML models for genomics (DNABERT, Geneformer, scGPT) |
| **mcp-deepcell** | 2 | ✅ Phase 3 | Deep learning cell segmentation and phenotyping |
| **mcp-mockEpic** | 3 | ✅ Phase 3 | Mock Epic EHR integration with synthetic patient data |
| **mcp-tcga** | 5 | ✅ Complete | TCGA cancer genomics data integration |
| **TOTAL** | **31** | ✅ | **All servers operational** |

## Quick Start

### Prerequisites

- Python 3.11+
- Claude Desktop (standalone app, not VSCode extension)
- 16GB+ RAM
- 50GB free disk space

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/spatial-mcp.git
cd spatial-mcp

# Install all 8 MCP servers (one command!)
cd manual_testing
./install_dependencies.sh

# Verify all servers are working
./verify_servers.sh
# Expected: "Servers working: 8/8"
```

For detailed testing instructions, see [Manual Testing Guide](manual_testing/README.md).

### Configure Claude Desktop

Copy the production config to Claude Desktop:

```bash
cp configs/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Or use the template and customize for your installation path:

```json
{
  "mcpServers": {
    "fgbio": {
      "command": "/absolute/path/to/spatial-mcp/servers/mcp-fgbio/venv/bin/python",
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

**Important:** Use the full path to the venv Python executable, not just `python`.

For complete configuration with all 8 servers, see [`configs/claude_desktop_config.json`](configs/claude_desktop_config.json).

Restart Claude Desktop and verify:

```
What MCP servers are available?
```

## Documentation

- 🧪 **[Manual Testing Guide](manual_testing/README.md)** - Scripts and guides for testing all servers
- 📋 **[Example Prompts](docs/MCP_POC_Example_Prompts.md)** - 18 test prompts from QC to analysis
- 📖 **[Setup Guide](docs/setup_guide.md)** - Complete installation and configuration
- 🏗️ **[Architecture Document](architecture/Spatial_MCP_POC_Architecture.md)** - Full technical architecture
- 🎨 **[Visual Diagram](architecture/Spatial_MCP_Architecture_Diagram.html)** - One-page architecture overview
- 🔧 **[Server Documentation](servers/mcp-fgbio/README.md)** - Individual server READMEs

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
- [x] mcp-tcga with TCGA cancer genomics data (5 tools, 2 resources)
- [x] Enhanced mcp-spatialtools with advanced analysis (+4 tools)
- [x] Complete POC with all 8 servers integrated
- [x] Full demonstration workflow capability
- [x] All 18 example prompts fully supported

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
