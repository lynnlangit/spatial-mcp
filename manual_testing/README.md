# Manual Testing Resources

This folder contains scripts and documentation for manually testing the Spatial MCP POC.

## 📁 Contents

### Scripts (Executable)

| File | Purpose | Usage |
|------|---------|-------|
| `install_dependencies.sh` | Install all dependencies for 8 MCP servers | `./install_dependencies.sh` |
| `verify_servers.sh` | Verify all servers can be imported | `./verify_servers.sh` |
| `setup_and_test_servers.sh` | Combined setup and verification | `./setup_and_test_servers.sh --install` |
| `test_all_servers.py` | Python-based server verification | `python3 test_all_servers.py` |

### Documentation

| File | Purpose |
|------|---------|
| `MANUAL_TESTING_GUIDE.md` | **Comprehensive step-by-step testing guide** |
| `TESTING_SUMMARY.md` | Quick reference summary |
| `CLAUDE_DESKTOP_TEST_PROMPTS.md` | **8 ready-to-paste test prompts with absolute paths for Claude Desktop** |

---

## 🚀 Quick Start

### 1. Install All Server Dependencies

```bash
cd manual_testing
./install_dependencies.sh
```

This will:
- Create Python 3.11 virtual environments for each server
- Install FastMCP and all dependencies
- Set up 8 servers in development mode

**Time:** ~5-10 minutes

### 2. Verify All Servers

```bash
./verify_servers.sh
```

Expected output:
```
Servers working: 8/8
Total tools: 31
🎉 All MCP servers are operational!
```

**Time:** ~10-30 seconds

---

## 📖 Full Testing Guide

For complete testing instructions, see:
- **`MANUAL_TESTING_GUIDE.md`** - Detailed step-by-step guide
- **`TESTING_SUMMARY.md`** - Quick reference

---

## ⚠️ Important Notes

### Claude Code vs Claude Desktop

**These scripts run in Claude Code** (VSCode extension):
- ✅ Can install dependencies
- ✅ Can verify server code
- ❌ Cannot orchestrate MCP protocol

**To test MCP workflows:**
- ✅ Use Claude Desktop (standalone app)
- ✅ Configure with `../configs/claude_desktop_config.json`
- ✅ Test with prompts from `CLAUDE_DESKTOP_TEST_PROMPTS.md`

### Python Version Requirement

All servers require **Python 3.11+**. The install script automatically uses `python3.11`.

Check your version:
```bash
python3.11 --version
# Should show: Python 3.11.x
```

---

## 🔧 Troubleshooting

### Issue: Scripts won't execute

**Solution:** Make them executable
```bash
chmod +x *.sh
```

### Issue: Dependencies fail to install

**Solution:** Check Python version
```bash
which python3.11
python3.11 --version
```

If Python 3.11 not found, install it:
```bash
brew install python@3.11  # macOS with Homebrew
```

### Issue: Servers won't import

**Solution:** Reinstall in specific server
```bash
cd ../servers/mcp-fgbio
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

---

## 📊 What Gets Tested

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
| **TOTAL** | **31** | **✅** |

---

## 🎯 Next Steps After Installation

1. ✅ Run installation scripts (this folder)
2. ✅ Verify all servers working
3. 📋 Configure Claude Desktop (`../configs/`)
4. 📋 Test with example prompts (`../docs/MCP_POC_Example_Prompts.md`)
5. 📋 Test with synthetic data (`../synthetic_data/`)

---

## 📚 Related Documentation

- `../docs/MCP_POC_Example_Prompts.md` - 18 test prompts
- `../synthetic_data/README.md` - Synthetic test data
- `../architecture/Spatial_MCP_POC_Architecture.md` - Full architecture
- `../README.md` - Main project README

---

**Last Updated:** October 25, 2025
**Status:** ✅ Ready for Testing
