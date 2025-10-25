# Pre-Flight Checklist for Claude Desktop Testing

**Status:** ✅ All systems ready for testing
**Date:** October 25, 2025

---

## ✅ Installation Verification

### Python Environment
- ✅ Python 3.11.13 installed
- ✅ 8 virtual environments created (one per server)
- ✅ FastMCP and dependencies installed in all venvs

### MCP Servers Installed
- ✅ mcp-fgbio (4 tools)
- ✅ mcp-spatialtools (8 tools)
- ✅ mcp-openimagedata (3 tools)
- ✅ mcp-seqera (3 tools)
- ✅ mcp-huggingface (3 tools)
- ✅ mcp-deepcell (2 tools)
- ✅ mcp-mockepic (3 tools)
- ✅ mcp-tcga (5 tools)

**Total: 8 servers, 31 tools**

---

## ✅ Configuration Files

### Claude Desktop Config
- ✅ **File:** `../configs/claude_desktop_config.json`
- ✅ **Status:** Ready to copy to `~/Library/Application Support/Claude/claude_desktop_config.json`
- ✅ **Format:** All 8 servers with full venv Python paths

**Config location:**
```
/Users/lynnlangit/Documents/GitHub/spatial-mcp/configs/claude_desktop_config.json
```

**Installation target:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

---

## ✅ Test Data Files

### FASTQ Files (for Test Prompts #1-2)
- ✅ `/Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/fastq/sample_001_R1.fastq.gz` (621KB)
- ✅ `/Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/fastq/sample_001_R2.fastq.gz` (791KB)

### Expression Matrix (for Test Prompts #3-7)
- ✅ `/Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/spatial/expression_matrix.json` (4.3MB)

---

## ✅ Test Prompts Ready

**File:** `CLAUDE_DESKTOP_TEST_PROMPTS.md`

### Available Test Prompts (with absolute paths)
1. ✅ **Test Prompt #1:** Validate FASTQ Files (mcp-fgbio)
2. ✅ **Test Prompt #2:** Extract UMIs (mcp-fgbio)
3. ✅ **Test Prompt #3:** Spatial Autocorrelation (mcp-spatialtools)
4. ✅ **Test Prompt #4:** TCGA Comparison (mcp-tcga)
5. ✅ **Test Prompt #5:** Differential Expression (mcp-spatialtools)
6. ✅ **Test Prompt #6:** Pathway Enrichment (mcp-spatialtools)
7. ✅ **Test Prompt #7:** Cell Type Prediction (mcp-huggingface)
8. ✅ **Test Prompt #8:** Complete End-to-End Workflow (multi-server)

---

## 🚀 Ready to Test in Claude Desktop

### Step 1: Install Config
```bash
cp ../configs/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Step 2: Restart Claude Desktop
1. Quit Claude Desktop completely
2. Relaunch Claude Desktop

### Step 3: Verify Servers Loaded
In Claude Desktop, type:
```
What MCP servers are available?
```

**Expected response:** Should list all 8 servers (fgbio, spatialtools, openimagedata, seqera, huggingface, deepcell, mockepic, tcga)

### Step 4: Run First Test
Open `CLAUDE_DESKTOP_TEST_PROMPTS.md` and copy **Test Prompt #1** into Claude Desktop.

**Expected result:**
- Total reads: 10,000 per file
- Mean quality: Q35-36
- Status: PASS
- Confirmation that data is suitable for analysis

---

## ⚠️ Important Reminders

### File Paths
- ✅ **Use ABSOLUTE paths** in all test prompts
- ❌ **Do NOT use relative paths** - Claude Desktop runs in a sandbox

### Testing Environment
- ✅ **Claude Desktop** (standalone app) - For MCP orchestration
- ❌ **Claude Code** (VSCode extension) - Cannot run MCP protocol

### DRY_RUN Mode
All servers are configured with `DRY_RUN=true` environment variables:
- Tools will simulate execution without external dependencies
- No actual genomic downloads or intensive computations
- Perfect for testing the POC workflow

---

## 📊 Verification Commands

### Verify All Servers Installed
```bash
cd /Users/lynnlangit/Documents/GitHub/spatial-mcp/manual_testing
./verify_servers.sh
```

**Expected output:**
```
Servers working: 8/8
Total tools: 31
🎉 All MCP servers are operational!
```

### Verify Test Data Exists
```bash
ls -lh /Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/fastq/*.fastq.gz
ls -lh /Users/lynnlangit/Documents/GitHub/spatial-mcp/synthetic_data/spatial/expression_matrix.json
```

### Verify Config File
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep -c "mcpServers"
# Should output: 1
```

---

## 🎯 Next Steps

1. ✅ **Dependencies installed** - All 8 servers ready
2. ✅ **Config file created** - Ready to copy to Claude Desktop
3. ✅ **Test data verified** - All synthetic data files present
4. ✅ **Test prompts ready** - 8 prompts with absolute paths
5. 🔄 **Configure Claude Desktop** - Copy config file and restart
6. 🔄 **Run Test Prompt #1** - Verify FASTQ validation works
7. 🔄 **Run remaining tests** - Complete all 8 test prompts

---

## 📚 Documentation Reference

- **Installation:** `README.md`
- **Testing Guide:** `MANUAL_TESTING_GUIDE.md`
- **Test Prompts:** `CLAUDE_DESKTOP_TEST_PROMPTS.md`
- **Quick Reference:** `TESTING_SUMMARY.md`
- **Architecture:** `../architecture/Spatial_MCP_POC_Architecture.md`
- **Main README:** `../README.md`

---

**Status:** ✅ System is GO for Claude Desktop testing!

**Last verified:** October 25, 2025
