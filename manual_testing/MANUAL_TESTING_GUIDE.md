# Manual Testing Guide - Spatial MCP POC

This guide walks you through manually testing all 8 MCP servers in the Spatial MCP POC.

## Prerequisites

- Python 3.11+
- Claude Desktop (for full integration testing)
- 16GB+ RAM
- 50GB free disk space

---

## Quick Start: Test All Servers

### Step 1: Install Dependencies

Run the installation script to set up all server dependencies:

```bash
cd /Users/lynnlangit/Documents/GitHub/spatial-mcp
./install_dependencies.sh
```

This will:
- Create virtual environments for each server
- Install FastMCP and all dependencies
- Set up each server in development mode

### Step 2: Verify All Servers

Run the verification script:

```bash
./verify_servers.sh
```

Expected output:
```
Servers working: 8/8
Total tools: 31
🎉 All MCP servers are operational!
```

---

## Manual Server Testing (One at a Time)

If you want to test each server individually:

### 1. mcp-fgbio (4 tools)

```bash
cd servers/mcp-fgbio
source venv/bin/activate

# Set environment variables
export FGBIO_DRY_RUN=true
export FGBIO_REFERENCE_DATA_DIR=/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/reference

# Test import
python -c "from mcp_fgbio.server import mcp; print('✅ mcp-fgbio loaded')"

# List tools
python << EOF
from mcp_fgbio.server import mcp
print(f"Tools: {len(mcp._tools)}")
for tool in sorted(mcp._tools.keys()):
    print(f"  - {tool}")
EOF

deactivate
cd ../..
```

**Expected output:**
```
✅ mcp-fgbio loaded
Tools: 4
  - extract_umis
  - fetch_reference_genome
  - query_gene_annotations
  - validate_fastq
```

### 2. mcp-spatialtools (8 tools)

```bash
cd servers/mcp-spatialtools
source venv/bin/activate

# Set environment variables
export SPATIAL_DRY_RUN=true

# Test import
python -c "from mcp_spatialtools.server import mcp; print('✅ mcp-spatialtools loaded')"

# List tools (should show 8 tools including advanced analysis)
python << EOF
from mcp_spatialtools.server import mcp
print(f"Tools: {len(mcp._tools)}")
for tool in sorted(mcp._tools.keys()):
    print(f"  - {tool}")
EOF

deactivate
cd ../..
```

**Expected tools:**
- align_spatial_data
- calculate_spatial_autocorrelation
- filter_quality
- merge_tiles
- perform_batch_correction
- perform_differential_expression
- perform_pathway_enrichment
- split_by_region

### 3. mcp-tcga (5 tools)

```bash
cd servers/mcp-tcga
source venv/bin/activate

# Set environment variables
export TCGA_DRY_RUN=true

# Test import
python -c "from mcp_tcga.server import mcp; print('✅ mcp-tcga loaded')"

# List tools
python << EOF
from mcp_tcga.server import mcp
print(f"Tools: {len(mcp._tools)}")
for tool in sorted(mcp._tools.keys()):
    print(f"  - {tool}")
EOF

deactivate
cd ../..
```

**Expected tools:**
- compare_to_cohort
- fetch_expression_data
- get_mutation_data
- get_survival_data
- query_tcga_cohorts

### 4-8. Other Servers

Follow the same pattern for:
- mcp-openimagedata (3 tools)
- mcp-seqera (3 tools)
- mcp-huggingface (3 tools)
- mcp-deepcell (2 tools)
- mcp-mockepic (3 tools)

---

## Testing with Claude Desktop

### Step 1: Prepare Configuration

1. Copy the complete config:
```bash
cp configs/claude_desktop_config_complete.json ~/Desktop/claude_config_temp.json
```

2. Edit `~/Desktop/claude_config_temp.json` and update ALL paths to absolute paths:
   - Change `/absolute/path/to` → `/Users/lynnlangit/Documents/GitHub`
   - Update all server `cwd` paths
   - Update all `PYTHONPATH` env variables

### Step 2: Install Configuration

```bash
# Backup existing config
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup

# Install new config
cp ~/Desktop/claude_config_temp.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Step 3: Restart Claude Desktop

1. Quit Claude Desktop completely (Cmd+Q)
2. Relaunch Claude Desktop
3. Wait for all servers to initialize (~10-30 seconds)

### Step 4: Verify Servers in Claude Desktop

Open a new conversation and ask:

```
What MCP servers are available?
```

**Expected response:** Claude should list all 8 servers:
- fgbio
- spatialtools
- openimagedata
- seqera
- huggingface
- deepcell
- mockepic
- tcga

### Step 5: Test with Example Prompts

Try the test prompt from the README:

```
Claude, I have 10x Visium spatial transcriptomics data. Please:
1. Validate my FASTQ files (sample_R1.fastq.gz, sample_R2.fastq.gz)
2. Extract UMIs and spatial barcodes
3. Filter spots with <200 genes detected
4. Perform differential expression between tumor and normal regions
5. Run pathway enrichment on upregulated genes
6. Compare key marker genes to TCGA breast cancer cohorts
```

Since we're in DRY_RUN mode, this will execute with mock data and show you the complete workflow.

---

## Testing with Synthetic Data

The repository includes synthetic test data you can use:

```bash
cd synthetic_data

# View available data
ls -lh fastq/
ls -lh spatial/
ls -lh clinical/

# Test with synthetic FASTQ files
cd ..
```

Then in Claude Desktop:

```
Claude, I have synthetic Visium data in the synthetic_data folder.
Please validate the FASTQ files at:
- synthetic_data/fastq/sample_001_R1.fastq.gz
- synthetic_data/fastq/sample_001_R2.fastq.gz

Then load the expression matrix from:
- synthetic_data/spatial/expression_matrix.json

And perform spatial autocorrelation analysis on genes: EPCAM, VIM, CD3D
```

---

## Troubleshooting

### Server Won't Start

**Check dependencies:**
```bash
cd servers/<server-name>
source venv/bin/activate
python -c "import fastmcp; import numpy; import pandas; print('All deps OK')"
```

**Reinstall if needed:**
```bash
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastmcp httpx aiofiles pydantic numpy pandas
```

### Tools Not Showing

**Check tool count:**
```bash
cd servers/<server-name>
source venv/bin/activate
python -c "from mcp_<server_name>.server import mcp; print(len(mcp._tools), 'tools')"
```

### Claude Desktop Not Seeing Servers

1. Check config file location:
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq '.mcpServers | keys'
```

2. Check logs:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

3. Verify paths are absolute (not relative)

4. Restart Claude Desktop

---

## Next Steps

Once all servers are verified:

1. ✅ Test basic functionality (this guide)
2. ✅ Test with synthetic data
3. ✅ Try all 18 example prompts from `docs/MCP_POC_Example_Prompts.md`
4. 📋 Run unit tests: `cd servers/mcp-fgbio && pytest`
5. 📋 Test with real spatial transcriptomics data (if available)
6. 📋 Benchmark performance
7. 📋 Create demo video/presentation

---

## Summary of Expected Tool Counts

| Server | Tools | Status |
|--------|-------|--------|
| mcp-fgbio | 4 | ✅ |
| mcp-spatialtools | 8 | ✅ |
| mcp-openimagedata | 3 | ✅ |
| mcp-seqera | 3 | ✅ |
| mcp-huggingface | 3 | ✅ |
| mcp-deepcell | 2 | ✅ |
| mcp-mockepic | 3 | ✅ |
| mcp-tcga | 5 | ✅ |
| **TOTAL** | **31** | ✅ |

---

**Document Version:** 1.0
**Last Updated:** October 25, 2025
**Status:** Ready for Manual Testing
