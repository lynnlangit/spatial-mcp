# Testing Summary - How to Start and Verify All MCP Servers

## Quick Answer

To start and verify all 8 MCP servers in this work session:

### 1. Install All Dependencies (One-Time Setup)
```bash
cd /Users/lynnlangit/Documents/GitHub/spatial-mcp
./install_dependencies.sh
```

### 2. Verify All Servers Are Working
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

## What These Scripts Do

### `install_dependencies.sh`
- Creates a Python virtual environment for each of the 8 servers
- Installs FastMCP framework
- Installs all required dependencies (numpy, pandas, httpx, etc.)
- Sets up each server in development mode
- Takes ~5-10 minutes to complete

### `verify_servers.sh`
- Tests that each server can be imported
- Counts and lists all tools in each server
- Reports overall status (8/8 servers, 31 total tools)
- Takes ~10-30 seconds to run

---

## Server Status After Setup

| # | Server | Tools | Description |
|---|--------|-------|-------------|
| 1 | mcp-fgbio | 4 | FASTQ validation, UMI extraction, reference genome |
| 2 | mcp-spatialtools | 8 | Spatial processing + advanced analysis (DE, autocorrelation, etc.) |
| 3 | mcp-openimagedata | 3 | Histology image processing |
| 4 | mcp-seqera | 3 | Nextflow workflow orchestration |
| 5 | mcp-huggingface | 3 | ML models (Geneformer, DNABERT) |
| 6 | mcp-deepcell | 2 | Cell segmentation |
| 7 | mcp-mockepic | 3 | Clinical data integration |
| 8 | mcp-tcga | 5 | TCGA cancer genomics data |
| **TOTAL** | **8 servers** | **31 tools** | **All operational** |

---

## Testing in This Work Session (Claude Code)

Since you're in Claude Code (not Claude Desktop), the servers can't be directly orchestrated via MCP protocol. However, you CAN:

### ✅ Verify Server Code
```bash
# Test individual server
cd servers/mcp-fgbio
source venv/bin/activate
python -c "from mcp_fgbio.server import mcp; print(len(mcp._tools), 'tools loaded')"
deactivate
```

### ✅ Run Unit Tests
```bash
# Run tests for mcp-fgbio (the only server with tests so far)
cd servers/mcp-fgbio
source venv/bin/activate
pytest
# Expected: 29/29 tests passing, 77% coverage
deactivate
```

### ✅ Test with Synthetic Data
```bash
# Validate synthetic FASTQ files exist
ls -lh synthetic_data/fastq/
ls -lh synthetic_data/spatial/

# View synthetic data manifest
cat synthetic_data/DATASET_MANIFEST.md
```

---

## Full Integration Testing (Requires Claude Desktop)

For complete end-to-end testing where Claude orchestrates all servers:

### 1. Configure Claude Desktop

```bash
# Copy config template
cp configs/claude_desktop_config_complete.json ~/Desktop/claude_config.json

# Edit and update ALL paths from /absolute/path/to → /Users/lynnlangit/Documents/GitHub
# Then copy to Claude Desktop config location:
cp ~/Desktop/claude_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 2. Restart Claude Desktop

Quit (Cmd+Q) and relaunch Claude Desktop.

### 3. Verify in Claude Desktop

Ask Claude:
```
What MCP servers are available?
```

Should see all 8 servers listed.

### 4. Test with Example Prompt

Try the example from the README:
```
Claude, I have 10x Visium spatial transcriptomics data. Please:
1. Validate my FASTQ files (sample_R1.fastq.gz, sample_R2.fastq.gz)
2. Extract UMIs and spatial barcodes
3. Filter spots with <200 genes detected
4. Perform differential expression between tumor and normal regions
5. Run pathway enrichment on upregulated genes
6. Compare key marker genes to TCGA breast cancer cohorts
```

---

## Available Testing Resources

### Scripts Created
- ✅ `install_dependencies.sh` - Install all server dependencies
- ✅ `verify_servers.sh` - Verify all servers are working
- ✅ `MANUAL_TESTING_GUIDE.md` - Detailed step-by-step testing guide

### Documentation
- ✅ `docs/MCP_POC_Example_Prompts.md` - 18 structured example prompts
- ✅ `synthetic_data/README.md` - Synthetic data usage guide
- ✅ `synthetic_data/DATASET_MANIFEST.md` - Data specifications

### Test Data
- ✅ `synthetic_data/fastq/` - 10K synthetic FASTQ reads
- ✅ `synthetic_data/spatial/` - 5K spatial spots + expression matrix
- ✅ `synthetic_data/clinical/` - 10 patient records
- ✅ Total: ~6.3 MB of realistic test data

---

## Current Limitations

### ❌ Cannot Test in Claude Code
- MCP servers require Claude Desktop for full orchestration
- This work session (Claude Code) can verify code but not run MCP protocol

### ✅ Can Test in Claude Code
- Install dependencies
- Verify server imports
- Run unit tests
- Check synthetic data
- Validate code structure

### ✅ Can Test in Claude Desktop
- Full MCP server orchestration
- Natural language pipeline execution
- All 18 example prompts
- End-to-end workflows

---

## Next Steps

1. **In this session:**
   - ✅ Run `./install_dependencies.sh`
   - ✅ Run `./verify_servers.sh`
   - ✅ Verify output shows 8/8 servers working

2. **In Claude Desktop:**
   - Configure with `configs/claude_desktop_config_complete.json`
   - Restart and verify all 8 servers load
   - Test with example prompts

3. **For production:**
   - Add unit tests for remaining 7 servers
   - Test with real spatial transcriptomics data
   - Performance benchmarking
   - Create demo presentation

---

## Troubleshooting

### Issue: `verify_servers.sh` shows 0/8 servers working

**Solution:**
```bash
# Reinstall dependencies
./install_dependencies.sh

# Try manual test
cd servers/mcp-fgbio
source venv/bin/activate
python -c "import fastmcp; print('FastMCP version:', fastmcp.__version__)"
```

### Issue: Import errors for numpy/pandas

**Solution:**
```bash
cd servers/<server-name>
source venv/bin/activate
pip install numpy pandas httpx aiofiles pydantic
```

### Issue: Claude Desktop doesn't see servers

**Solution:**
1. Check config file exists and has correct paths
2. Verify paths are absolute (not relative)
3. Restart Claude Desktop
4. Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log`

---

**Ready to test?** Run `./install_dependencies.sh` to begin!
