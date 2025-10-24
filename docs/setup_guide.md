# Spatial MCP POC - Setup Guide

Complete setup guide for the Spatial Transcriptomics MCP demonstration.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Setup](#environment-setup)
- [Installing MCP Servers](#installing-mcp-servers)
- [Configuring Claude Desktop](#configuring-claude-desktop)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System:** Ubuntu 24.04 LTS, macOS 13+, or Windows 11 with WSL2
- **Python:** 3.11 or higher
- **Memory:** 16GB RAM minimum (32GB recommended)
- **Disk Space:** 50GB free space for reference data
- **Network:** Internet connection for downloading reference genomes

### Required Software

```bash
# Check Python version
python --version  # Should be 3.11 or higher

# Check pip
pip --version

# Check git
git --version
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/spatial-mcp.git
cd spatial-mcp
```

### 2. Run Setup Script

```bash
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

This script will:
- Create necessary directories
- Set up Python virtual environments
- Install dependencies for all servers
- Configure environment variables

### 3. Install Claude Desktop

Download and install Claude Desktop from [claude.ai](https://claude.ai/download).

### 4. Configure Claude Desktop

```bash
# Copy the example configuration
cp configs/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Edit the configuration to match your paths
# Update all /path/to/spatial-mcp references
```

### 5. Start Claude Desktop

Launch Claude Desktop. It will automatically connect to the configured MCP servers.

## Environment Setup

### Directory Structure

The setup script creates the following structure:

```
spatial-mcp/
├── data/
│   ├── reference/          # Reference genomes (will be populated)
│   ├── test_data/          # Small test datasets
│   └── cache/              # Temporary files and caches
├── servers/
│   ├── mcp-fgbio/          # Genomic reference data server
│   ├── mcp-tcga/           # TCGA data server (future)
│   ├── mcp-spatialtools/   # Spatial processing server (future)
│   └── ... (other servers)
└── configs/
    └── claude_desktop_config.json
```

### Python Virtual Environment

Each MCP server has its own virtual environment:

```bash
# Activate mcp-fgbio environment
cd servers/mcp-fgbio
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Deactivate when done
deactivate
```

### Environment Variables

Create a `.env` file in each server directory:

**servers/mcp-fgbio/.env:**
```bash
# Data directories
FGBIO_REFERENCE_DATA_DIR=/absolute/path/to/spatial-mcp/data/reference
FGBIO_CACHE_DIR=/absolute/path/to/spatial-mcp/data/cache

# Development settings
FGBIO_DRY_RUN=true
FGBIO_LOG_LEVEL=DEBUG

# Performance
FGBIO_TIMEOUT_SECONDS=300
FGBIO_MAX_DOWNLOAD_SIZE_GB=10
```

## Installing MCP Servers

### Phase 1: mcp-FGbio (Current)

```bash
cd servers/mcp-fgbio

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests to verify installation
pytest

# Test the server manually
python -m mcp_fgbio
# Press Ctrl+C to exit
```

### Phase 2: Additional Servers (Future)

Follow similar steps for each server as they are implemented:

- mcp-tcga
- mcp-spatialtools
- mcp-huggingface
- mcp-mockepic
- mcp-openimagedata
- mcp-seqera
- mcp-deepcell

## Configuring Claude Desktop

### Location of Configuration File

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Configuration Template

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
        "FGBIO_DRY_RUN": "true",
        "FGBIO_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important:** Replace all `/absolute/path/to/spatial-mcp` with the actual path to your repository.

### Reloading Configuration

After editing the configuration:

1. Quit Claude Desktop completely
2. Relaunch Claude Desktop
3. The servers will be loaded automatically

## Verification

### 1. Check Server Installation

```bash
cd servers/mcp-fgbio
source venv/bin/activate
python -c "import mcp_fgbio; print('✓ mcp-fgbio installed')"
```

### 2. Run Tests

```bash
cd servers/mcp-fgbio
pytest -v

# Expected output:
# test_server.py::TestFetchReferenceGenome::test_fetch_valid_genome PASSED
# test_server.py::TestValidateFastq::test_validate_good_fastq PASSED
# ... (more tests)
# =========== X passed in Y.YYs ===========
```

### 3. Test with Claude Desktop

Open Claude Desktop and try these prompts:

```
What MCP servers are available?
```

Expected: Should list "fgbio" server

```
What tools does the fgbio server provide?
```

Expected: Should list fetch_reference_genome, validate_fastq, extract_umis, query_gene_annotations

```
Can you fetch information about the hg38 reference genome?
```

Expected: Should call the reference://hg38 resource and return genome metadata

### 4. Run Integration Tests

```bash
cd tests/integration
pytest test_fgbio_integration.py -v
```

## Troubleshooting

### Server Not Showing in Claude Desktop

**Symptoms:** Claude says "No MCP servers available"

**Solutions:**

1. **Check configuration file location:**
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Verify JSON syntax:**
   ```bash
   # Use a JSON validator
   python -m json.tool < claude_desktop_config.json
   ```

3. **Check file paths are absolute:**
   - All paths in the config must be absolute, not relative
   - Use `pwd` to get the absolute path

4. **Restart Claude Desktop:**
   - Quit completely (not just close window)
   - Relaunch

### Server Starts But Tools Fail

**Symptoms:** Tools return errors when called

**Solutions:**

1. **Enable dry-run mode:**
   ```bash
   export FGBIO_DRY_RUN=true
   ```

2. **Check environment variables:**
   ```bash
   # From within the server directory
   python -c "import os; print(os.getenv('FGBIO_REFERENCE_DATA_DIR'))"
   ```

3. **Verify directories exist:**
   ```bash
   ls -la data/reference
   ls -la data/cache
   ```

4. **Check logs:**
   - Claude Desktop logs (see Help → Developer → Logs)
   - Server stderr output

### Import Errors

**Symptoms:** `ModuleNotFoundError: No module named 'mcp_fgbio'`

**Solutions:**

1. **Verify PYTHONPATH in config:**
   ```json
   "env": {
     "PYTHONPATH": "/absolute/path/to/spatial-mcp/servers/mcp-fgbio/src"
   }
   ```

2. **Reinstall in development mode:**
   ```bash
   cd servers/mcp-fgbio
   source venv/bin/activate
   pip install -e .
   ```

### Performance Issues

**Symptoms:** Tools timeout or run slowly

**Solutions:**

1. **Increase timeout:**
   ```bash
   export FGBIO_TIMEOUT_SECONDS=600
   ```

2. **Check disk space:**
   ```bash
   df -h data/
   ```

3. **Use local cache:**
   - Ensure cache directory is on fast storage (SSD)

### Permission Errors

**Symptoms:** `Permission denied` when writing files

**Solutions:**

```bash
# Make directories writable
chmod -R u+w data/

# Check directory ownership
ls -la data/
```

## Next Steps

Once you have mcp-fgbio working:

1. **Try the example prompts** in `/MCP_POC_Example_Prompts.md`
2. **Implement additional servers** following Phase 2 of the architecture
3. **Test with real data** by disabling dry-run mode
4. **Integrate with your workflow** by creating custom prompts

## Getting Help

- **Documentation:** See `docs/` directory
- **Issues:** Create an issue on GitHub
- **MCP Specification:** https://modelcontextprotocol.io/
- **Claude Desktop:** https://claude.ai/help

## Development Workflow

For developers adding new features:

1. **Create a branch:**
   ```bash
   git checkout -b feature/new-tool
   ```

2. **Make changes:**
   - Add tool to `server.py`
   - Add tests to `tests/test_server.py`
   - Update README

3. **Run tests:**
   ```bash
   pytest
   black src/ tests/
   ruff check src/
   ```

4. **Submit PR:**
   ```bash
   git push origin feature/new-tool
   ```

## Security Notes

- **Never commit API keys** to the repository
- **Use environment variables** for sensitive data
- **Enable dry-run mode** for development
- **Validate all file paths** to prevent path traversal
- **Review logs** for sensitive information before sharing

---

**Last Updated:** October 24, 2025
**Version:** 1.0
**Status:** Phase 1 Complete
