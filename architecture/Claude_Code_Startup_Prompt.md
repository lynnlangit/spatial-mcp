# Claude Code Prompt: Spatial MCP POC Implementation

## Project Overview

I need you to help me build a Proof of Concept (POC) for a Spatial Transcriptomics Bioinformatics Pipeline using the Model Context Protocol (MCP). This system will use 8 specialized MCP servers to process spatial genomics data through a 5-stage pipeline, with Claude Desktop acting as the AI orchestrator.

## Context Documents

I have three key documents that define this project:

1. **Architecture Document** (`Spatial_MCP_POC_Architecture.md`) - Complete technical architecture with 60+ pages of specifications
2. **Visual Diagram** (`Spatial_MCP_Architecture_Diagram.html`) - One-page visual overview 
3. **Example Prompts** (`MCP_POC_Example_Prompts.md`) - 18 example prompts showing how bioinformaticians will use the system

Please read all three documents to understand the full scope before we begin.

## Project Structure

Create the following directory structure:

```
spatial-mcp-poc/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── setup_guide.md
│   └── developer_guide.md
├── servers/
│   ├── mcp-fgbio/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   ├── mcp-tcga/
│   ├── mcp-spatialtools/
│   ├── mcp-huggingface/
│   ├── mcp-mockepic/
│   ├── mcp-openimagedata/
│   ├── mcp-seqera/
│   └── mcp-deepcell/
├── shared/
│   ├── common/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── validation.py
│   └── models/
├── tests/
│   ├── integration/
│   └── e2e/
├── data/
│   ├── reference/
│   ├── test_data/
│   └── cache/
├── configs/
│   ├── claude_desktop_config.json
│   └── docker-compose.yml
├── scripts/
│   ├── setup_environment.sh
│   └── run_tests.sh
└── .github/
    └── workflows/
```

## Implementation Priority

Start with **Phase 1: Foundation (Weeks 1-2)** from the architecture document:

### Step 1: Environment Setup
1. Create Python virtual environment with Python 3.11+
2. Install core dependencies:
   - FastMCP
   - Required bioinformatics tools (list from architecture doc)
3. Create base configuration files
4. Set up logging and error handling infrastructure

### Step 2: Build First MCP Server (mcp-FGbio)

Create a working MCP server for genomic reference data with:

**Required Tools:**
- `fetch_reference_genome` - Download reference genome sequences
- `validate_fastq` - Quality validation of FASTQ files
- `query_gene_annotations` - Retrieve gene annotation data
- `extract_umis` - UMI extraction and processing

**Required Resources:**
- `reference://hg38` - Human genome reference (GRCh38)
- `reference://mm10` - Mouse genome reference
- `annotations://gencode` - GENCODE gene annotations

**Implementation Requirements:**
1. Use FastMCP Python framework
2. Implement proper JSON schema validation for all inputs
3. Add comprehensive error handling
4. Include logging at INFO and DEBUG levels
5. Add docstrings for all functions
6. Create unit tests with >80% coverage
7. Mock external dependencies (don't download real genomes yet)

### Step 3: Create Claude Desktop Configuration

Generate a working `claude_desktop_config.json` that can connect to the mcp-FGbio server via stdio transport.

### Step 4: Write Integration Test

Create a test that:
1. Starts the mcp-FGbio server
2. Simulates Claude Desktop connecting to it
3. Calls each tool
4. Validates responses
5. Checks error handling

## Development Guidelines

### Code Quality Standards

**Python Style:**
- Use Python 3.11+ features (type hints, match statements)
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use dataclasses for structured data
- Prefer pathlib over os.path

**Error Handling:**
- Use custom exception classes (inherit from `MCPServerError`)
- Always include context in error messages
- Log errors before raising
- Validate all inputs before processing
- Use try-except blocks around external tool calls

**Testing:**
- Use pytest as testing framework
- Mock external dependencies (file I/O, network calls, subprocess calls)
- Create fixtures for common test data
- Test both success and failure scenarios
- Aim for >80% test coverage

**Logging:**
- Use Python's logging module
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Log levels:
  - DEBUG: Detailed tool execution
  - INFO: Key events (tool called, completed)
  - WARNING: Degraded performance, retries
  - ERROR: Tool failures
  - CRITICAL: Server failures

**Security:**
- Validate all file paths (prevent path traversal)
- Sanitize inputs before passing to subprocess
- Set resource limits (timeout, memory, disk)
- Don't log sensitive data
- Use environment variables for credentials

### MCP Server Best Practices

1. **Single Responsibility** - Each server handles one domain
2. **Idempotent Tools** - Same inputs → same outputs, safe to retry
3. **Clear Schemas** - JSON schema for all tool inputs/outputs
4. **Descriptive Errors** - Return helpful error messages
5. **Resource Management** - Clean up files, close connections
6. **Capability Declaration** - Declare supported features upfront

## Specific Technical Decisions

### For mcp-FGbio Server:

**Dependencies:**
```python
# pyproject.toml
[project]
name = "mcp-fgbio"
version = "0.1.0"
dependencies = [
    "fastmcp>=0.2.0",
    "pydantic>=2.0.0",
    "httpx>=0.27.0",  # For downloading references
    "aiofiles>=24.0.0",  # Async file operations
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=24.0.0",
    "ruff>=0.3.0",
]
```

**Configuration Management:**
```python
# Use pydantic for config validation
from pydantic import BaseSettings

class FGbioConfig(BaseSettings):
    reference_data_dir: Path
    cache_dir: Path
    max_download_size_gb: int = 10
    timeout_seconds: int = 300
    log_level: str = "INFO"
    
    class Config:
        env_prefix = "FGBIO_"
        env_file = ".env"
```

**Tool Implementation Pattern:**
```python
from fastmcp import FastMCP

mcp = FastMCP("fgbio")

@mcp.tool()
async def fetch_reference_genome(
    genome: str,  # "hg38" | "mm10" | "hg19"
    output_dir: str
) -> dict:
    """
    Download reference genome sequences.
    
    Args:
        genome: Genome identifier (hg38, mm10, hg19)
        output_dir: Directory for output files
        
    Returns:
        dict with keys: path, size_mb, md5sum, metadata
        
    Raises:
        ValueError: Invalid genome identifier
        IOError: Download failed
    """
    # Implementation with proper validation, logging, error handling
    pass
```

## What I Need From You

### Immediate Tasks (Start Here):

1. **Read all three context documents** I mentioned and confirm you understand:
   - The 8 MCP servers and their purposes
   - The 5-stage pipeline flow
   - The technology stack (FastMCP, STAR, etc.)
   - The security and testing requirements

2. **Set up the project structure** as specified above

3. **Implement the mcp-FGbio server** with:
   - All 4 required tools
   - All 3 required resources
   - Proper error handling and logging
   - Unit tests with mocked dependencies
   - README with usage examples

4. **Create the Claude Desktop config** that connects to mcp-FGbio

5. **Write an integration test** that proves the server works

### Questions to Answer:

Before you start coding, please tell me:

1. **Understanding Check**: Summarize the purpose of the mcp-FGbio server in 2-3 sentences
2. **Technical Approach**: How will you mock the FGbio Java toolkit calls? (We don't want to install the actual toolkit yet)
3. **Testing Strategy**: What are the 5 most important test cases for the fetch_reference_genome tool?
4. **Data Strategy**: How should we handle test data? (Create tiny mock FASTA files? Use fixtures?)

## Additional Context

### Key Constraints:
- **Development environment**: Linux (Ubuntu 24)
- **No real bioinformatics data yet**: Use mocks and fixtures
- **No external API calls**: Mock all network requests
- **Fast iteration**: Prioritize working code over perfect code
- **Documentation**: Every tool needs examples in the README

### Success Criteria for Step 1:

✅ Project structure created  
✅ mcp-FGbio server can start without errors  
✅ All 4 tools are implemented and testable  
✅ Claude Desktop config successfully connects to server  
✅ Integration test passes  
✅ Code coverage >80%  
✅ README has clear setup and usage instructions  

## Communication

As you work:
- **Ask questions** when requirements are unclear
- **Propose alternatives** if you see a better approach
- **Show progress** - commit code frequently
- **Document decisions** - add comments explaining "why" not just "what"
- **Run tests** - ensure everything passes before moving on

## After Step 1 is Complete

Once we have a working mcp-FGbio server, I'll ask you to:
1. Implement the second server (mcp-tcga)
2. Build the integration between servers
3. Add more sophisticated testing
4. Progress through the remaining phases

But let's start with just the foundation and get one solid MCP server working first.

## Resources

Reference these official sources:
- MCP Specification: https://modelcontextprotocol.io/specification/2025-06-18
- FastMCP Documentation: https://github.com/modelcontextprotocol/python-sdk
- BioinfoMCP Paper: https://arxiv.org/html/2510.02139v1

---

**Ready to begin?** Please confirm you've read the context documents and answer the 4 questions above, then we'll start building!
