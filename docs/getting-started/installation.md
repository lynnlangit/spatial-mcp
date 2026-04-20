# Getting Started & Installation

## Which Setup Should I Use?

| You Are... | Use This | Time |
|------------|----------|------|
| Student (Claude) | [Claude Code (CLI)](#quick-start-claude-code) | 5 min |
| Student (Gemini) | [Gemini Setup Guide](gemini-setup.md) | 10 min |
| Developer | [Claude Code (CLI)](#quick-start-claude-code) | 5 min |
| Clinician | [Claude Desktop (GUI)](#quick-start-claude-desktop) | 10 min |
| Instructor | [Educator Guide](../for-educators/README.md) | 30 min |

**Prerequisites:** Python 3.11+, git, [uv](https://docs.astral.sh/uv/). Claude Code also needs Node.js 18+.

**Other setup options:** [Gemini Setup Guide](gemini-setup.md) | [Desktop Config Files](desktop-configs/README.md)

---

Choose your preferred interface:

- **[Claude Code (CLI)](#quick-start-claude-code)** -- Best for developers, students, and study groups
- **[Claude Desktop (GUI)](#quick-start-claude-desktop)** -- Best for clinicians and non-technical users

## Table of Contents

- [Quick Start: Claude Code (5 Minutes)](#quick-start-claude-code)
- [Quick Start: Claude Desktop (10 Minutes)](#quick-start-claude-desktop)
- [Complete Setup](#complete-setup)
- [Verification](#verification)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Quick Start: Claude Code

Use Claude Code (the CLI) to explore the codebase, run tests, and interact with servers from your terminal.

### 1. Prerequisites

```bash
python3 --version   # Should be 3.11 or higher
git --version
uv --version        # Python package manager (see below if not installed)
```

**Install `uv`** (if not already installed):
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv
```

**Install Claude Code** (requires Node.js 18+):
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Clone and Explore

```bash
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp

# Launch Claude Code
claude
```

Claude Code reads the `CLAUDE.md` file at the repo root and understands the project structure automatically.

### 3. Try These in Claude Code

```
What MCP servers are in this repo and what do they do?
```

```
Run the tests for mcp-multiomics
```

```
Show me the PatientOne synthetic data files
```

```
Explain how the mcp-spatialtools server works
```

### 4. Run a Server Locally (optional)

```bash
cd servers/mcp-fgbio
uv run python -m mcp_fgbio
# Server starts on stdio — press Ctrl+C to stop
```

---

## Quick Start: Claude Desktop

If you already have Claude Desktop installed and want to get started quickly:

### 1. Verify Prerequisites

```bash
python3 --version   # Should be 3.11 or higher
git --version
uv --version        # See Claude Code section above for install instructions
```

### 2. Clone Repository

```bash
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp
```

### 3. Configure Claude Desktop

```bash
# macOS — copy the pre-built config
cp docs/getting-started/desktop-configs/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json

# IMPORTANT: Edit the config file to replace paths with YOUR installation path
# The default config uses /Users/lynnlangit/Documents/GitHub/spatial-mcp/
```

See [desktop-configs/README.md](desktop-configs/README.md) for the template and path details.

### 4. Restart Claude Desktop

Quit Claude Desktop completely (Cmd+Q on macOS), then relaunch it.

### 5. Test It

Open Claude Desktop and try:

```
What MCP servers are available?
```

You should see all servers listed.

**Done! Jump to [Usage Examples](#usage-examples) to start analyzing spatial transcriptomics data.**

### Optional: External MCP Connectors

The custom servers above handle core analysis. For real-world literature, trials, and genomics data, you can also connect external MCP servers:

- **Anthropic connectors** (ClinicalTrials.gov, PubMed, bioRxiv, Seqera): Toggle on in Claude Desktop > Settings > Connectors — no install needed
- **Community servers** (cBioPortal, Hugging Face): Self-hosted, requires `git clone` + `uv sync`

See [Connect External MCP Servers](../for-researchers/CONNECT_EXTERNAL_MCP.md) for setup instructions.

---

## Complete Setup

For first-time installation or if you need detailed instructions:

### System Requirements

- **Operating System:** Ubuntu 24.04 LTS, macOS 13+, or Windows 11 with WSL2
- **Python:** 3.11 or higher
- **Memory:** 16GB RAM minimum (32GB recommended for production)
- **Disk Space:** 50GB free space
- **Network:** Internet connection for downloading reference data

### 1. Install Claude Desktop

Download and install from [claude.ai/download](https://claude.ai/download).

### 2. Clone Repository

```bash
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp
```

### 3. Install `uv` (Python Package Manager)

This project uses [`uv`](https://docs.astral.sh/uv/) to manage dependencies — it replaces pip/venv with a single fast tool:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Verify
uv --version
```

### 4. Install and Test a Server

Each server is a standalone Python project with a `pyproject.toml`. Use `uv` to install and run:

```bash
# Example: Install and test mcp-multiomics
cd servers/mcp-multiomics
uv run pytest -v    # uv automatically creates venv and installs deps

# Example: Install and test mcp-spatialtools
cd ../mcp-spatialtools
uv run pytest -v
```

Repeat for other servers you want to use. `uv run` handles virtual environments automatically — no manual `venv` or `pip install` needed.

### 5. Configure Environment Variables

Each server can use a `.env` file for configuration:

**Example: servers/mcp-spatialtools/.env**

```bash
# Data directories
SPATIAL_DATA_DIR=/absolute/path/to/spatial-mcp/data
SPATIAL_CACHE_DIR=/absolute/path/to/spatial-mcp/data/cache

# Mode
SPATIAL_DRY_RUN=false  # Set to true for testing

# Performance
SPATIAL_TIMEOUT_SECONDS=300
```

### 6. Configure Claude Desktop

**Configuration File Location:**

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:** Use the pre-built config or the template:

```bash
# Option A: Copy pre-built config (paths set for /Users/lynnlangit/...)
cp docs/getting-started/desktop-configs/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Option B: Copy template and customize paths
cp docs/getting-started/desktop-configs/claude_desktop_config.template.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
# Then edit the file to replace /ABSOLUTE/PATH/TO/ with your actual path
```

The config uses `uv run --directory` to launch each server — no manual venv setup needed. See [desktop-configs/README.md](desktop-configs/README.md) for details.

**⚠️ Important:**
- Replace all path placeholders with your actual installation path
- Use absolute paths, not relative paths
- Verify JSON syntax: `python3 -m json.tool < ~/Library/Application\ Support/Claude/claude_desktop_config.json`

### 7. Restart Claude Desktop

After editing configuration:
1. Quit Claude Desktop completely (not just close window)
2. Relaunch Claude Desktop
3. Servers will load automatically

---

## Verification

### 1. Check Server Installation

```bash
cd servers/mcp-spatialtools
uv run python -c "import mcp_spatialtools; print('✓ mcp-spatialtools installed')"
```

### 2. Run Tests

```bash
cd servers/mcp-spatialtools
uv run pytest -v

# Expected output:
# test_server.py::test_differential_expression PASSED
# test_server.py::test_spatial_autocorrelation PASSED
# ... (more tests)
```

### 3. Test with Claude Desktop

Open Claude Desktop and try:

**Check Available Servers:**
```
What MCP servers are available?
```

Expected: Should list all configured servers (spatialtools, epic, fgbio, etc.)

**List Server Tools:**
```
What tools does the spatialtools server provide?
```

Expected: Should list 14 tools including perform_differential_expression, calculate_spatial_autocorrelation, etc.

**Test a Tool:**
```
Using the spatialtools server, list the available test data files.
```

Expected: Should return information about available patient data.

---

## Usage Examples

### Available MCP Servers

After installation, you have access to the following **MCP servers**:

📋 **[Complete Server Status](../reference/shared/server-registry.md)** - Detailed capabilities matrix

See [Server Registry](../reference/shared/server-registry.md) for all servers, tool counts, and production status.

### Example 1: Analyze Patient-001 (Complete Workflow)

```
I want to analyze Patient-001 (PAT001-OVC-2025) ovarian cancer spatial data.

Please run the complete analysis:
1. Load the data from /path/to/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial/
2. Perform differential expression (tumor_core vs stroma)
3. Calculate spatial autocorrelation for all genes
4. Do cell type deconvolution
5. Summarize findings and clinical implications
```

### Example 2: Identify Drug Resistance Markers

```
Using the spatialtools server, analyze Patient-001 to identify drug resistance markers:

1. Run differential expression comparing tumor_core vs stroma regions
2. Filter for genes with log2FC > 2
3. Check if ABCB1, PIK3CA, or AKT1 are upregulated
4. Calculate spatial autocorrelation for resistance genes
5. Tell me if resistance markers are spatially clustered
```

### Example 3: Access FHIR Clinical Data

```
Using the epic MCP server, retrieve Patient-001 data from the GCP Healthcare API:

1. Get patient demographics
2. List all conditions
3. Show CA-125 observations
4. What medications has the patient received?
```

### Example 4: Batch Correction (Multi-Site Study)

```
I have spatial data from 3 different hospitals. Run batch correction:

Files:
- /path/to/hospital1_visium.csv
- /path/to/hospital2_visium.csv
- /path/to/hospital3_visium.csv

Use ComBat to harmonize the data and tell me:
- What % of variance was due to batch effects?
- How much did batch correction reduce variance?
- Is the biological signal preserved?
```

### Tips for Best Results

**1. Be Specific About Inputs**

❌ Bad:
```
Analyze some spatial data
```

✅ Good:
```
Analyze Patient-001 spatial data located at /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial/
Compare tumor_core vs stroma regions
```

**2. Request Interpretation**

```
What do these differential expression results mean for treatment?
```

```
Are there any actionable drug targets based on this pathway enrichment?
```

**3. Iterate and Refine**

```
1. First: "What are the top differentially expressed genes?"
2. Then: "Tell me more about the PI3K/AKT pathway genes"
3. Finally: "Are these genes spatially clustered? What does that mean?"
```

---

## Troubleshooting

### Issue: "No MCP servers found"

**Solution:** Restart Claude Desktop

```bash
# macOS: Cmd+Q, then relaunch
# Verify config file exists
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Issue: "Tool execution failed"

**Check:**
1. File paths are correct (use absolute paths)
2. Data files exist and are readable
3. Server logs (Claude Desktop → Settings → MCP Logs)

**Enable Debug Mode:**

```json
"env": {
  "SPATIAL_LOG_LEVEL": "DEBUG"
}
```

### Issue: "Server not responding"

**Test server manually:**

```bash
cd /path/to/spatial-mcp/servers/mcp-spatialtools
uv run python -m mcp_spatialtools

# Expected output: "Server running on stdio..."
```

### Issue: "Permission denied" for GCP

**Fix:** Ensure service account key exists:

```bash
ls -la /path/to/spatial-mcp/infrastructure/deployment/mcp-server-key.json
```

### Issue: "ModuleNotFoundError"

**Solutions:**

1. **Reinstall with uv:**
   ```bash
   cd servers/mcp-spatialtools
   uv sync
   uv run python -c "import mcp_spatialtools; print('OK')"
   ```

2. **If using Claude Desktop, verify the config uses `uv run --directory`** (not raw `python`). See [desktop-configs/README.md](desktop-configs/README.md).

### Issue: Performance/Timeouts

**Solutions:**

1. **Increase timeout:**
   ```json
   "env": {
     "SPATIAL_TIMEOUT_SECONDS": "600"
   }
   ```

2. **Check disk space:**
   ```bash
   df -h /path/to/spatial-mcp/data/
   ```

3. **Use local cache on SSD**

### Issue: Validate JSON Configuration

**Check syntax:**

```bash
python -m json.tool < ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

---

## Next Steps

**Now that you're set up:**

1. ✅ Try the [Example Prompts](#usage-examples) above
2. ✅ Explore [PatientOne Testing Scenario](../reference/testing/patient-one/README.md)
3. ✅ Read [Test Prompts](../reference/testing/patient-one/test-prompts) for comprehensive workflows
4. ✅ Review [Architecture Documentation](../reference/architecture/README.md)

**For Development:**
- See [Developer Guide](../for-developers/README.md) - Architecture, contributing, building servers
- Add new tools following existing patterns
- Run tests before submitting changes

---

## Related Documentation

- **[Architecture Overview](../reference/architecture/README.md)** - System design
- **[Server Status](../reference/shared/server-registry.md)** - Implementation status and capabilities
- **[Documentation Index](../INDEX.md)** - Role-specific guides and documentation
- **[Test Documentation](../reference/testing/README.md)** - Testing strategies and prompts

---

**Last Updated:** 2026-02-16

**Support:**
- Documentation: `/docs` directory
- Issues: GitHub Issues
- MCP Specification: https://modelcontextprotocol.io/
