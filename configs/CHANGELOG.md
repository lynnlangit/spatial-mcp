# Configuration Files Changelog

## October 25, 2025 - Bug Fixes (Critical)

### 🐛 Fixed 3 Failing Servers

When testing in Claude Desktop, 3 out of 8 servers failed to start with errors like:
```
OSError: [Errno 30] Read-only file system: '/workspace'
```

**Root Causes:**

1. **Missing Cache Directory Environment Variables**
   - `spatialtools` expected `SPATIAL_CACHE_DIR` but it wasn't in config
   - `openimagedata` expected `IMAGE_CACHE_DIR` but it wasn't in config
   - Without these env vars, servers defaulted to `/workspace/cache` (read-only) and crashed

2. **Missing __main__.py for tcga**
   - The tcga module couldn't be executed as `python -m mcp_tcga`
   - Error: `No module named mcp_tcga.__main__`

**Fixes Applied:**

1. **Added missing environment variables** to `claude_desktop_config.json`:
   ```json
   // spatialtools
   "SPATIAL_CACHE_DIR": "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/cache"

   // openimagedata
   "IMAGE_CACHE_DIR": "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/cache/images"
   ```

2. **Created missing __main__.py** for tcga server:
   - File: `servers/mcp-tcga/src/mcp_tcga/__main__.py`
   ```python
   """Entry point for running mcp-tcga as a module."""
   from .server import main
   if __name__ == "__main__":
       main()
   ```

3. **Created required data directories:**
   - `data/cache/images/`
   - `data/images/he/` and `data/images/if/`
   - `data/raw/`, `data/filtered/`, `data/aligned/`

**Server Status:**

| Server | Before | After | Issue Fixed |
|--------|--------|-------|-------------|
| fgbio | ✅ | ✅ | N/A |
| spatialtools | ❌ | ✅ | Missing SPATIAL_CACHE_DIR |
| openimagedata | ❌ | ✅ | Missing IMAGE_CACHE_DIR |
| seqera | ✅ | ✅ | N/A |
| huggingface | ✅ | ✅ | N/A |
| deepcell | ✅ | ✅ | N/A |
| mockepic | ✅ | ✅ | N/A |
| tcga | ❌ | ✅ | Missing __main__.py |

**Result:** ✅ **All 8 servers now working (5/8 → 8/8 = 100%)**

**Verification:** All servers tested successfully in Claude Desktop. First test prompt (FASTQ validation) returned expected results.

---

## October 25, 2025 - Cleanup and Reorganization

### 🧹 Cleanup Actions

**Removed:**
- ❌ `claude_desktop_config_complete.json` - Incomplete config with broken `"command": "python"` paths

**Deleted:**
- ❌ `claude_desktop_config.json.OLD` - Old Phase 1 config (only 3 servers) - Removed during cleanup

**Renamed:**
- `claude_desktop_config_fixed.json` → `claude_desktop_config.json` (standard name)

**Added:**
- ✅ `claude_desktop_config.template.json` - Template for other users with placeholder paths
- ✅ `README.md` - Complete configuration documentation
- ✅ `CHANGELOG.md` - This file

---

## Current Files

### Production Config
**File:** `claude_desktop_config.json`

**Status:** ✅ Ready to use

**Contents:**
- All 8 MCP servers configured
- Full absolute paths to Python 3.11 venv executables
- All required environment variables
- DRY_RUN mode enabled
- Valid JSON syntax verified

**Installation:**
```bash
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

---

### Template Config
**File:** `claude_desktop_config.template.json`

**Status:** 📝 Template for other installations

**Purpose:**
- Same structure as production config
- Placeholder paths: `/ABSOLUTE/PATH/TO/spatial-mcp/...`
- For users who cloned repo to different location

**Usage:**
1. Copy template to new file
2. Replace all `/ABSOLUTE/PATH/TO/` with actual installation path
3. Use as config file

---


## Changes Made

### 1. Simplified Naming
**Before:**
- `claude_desktop_config.json` (incomplete, 3 servers)
- `claude_desktop_config_complete.json` (8 servers, broken paths)
- `claude_desktop_config_fixed.json` (8 servers, working paths)

**After:**
- `claude_desktop_config.json` (8 servers, working paths) ✅ USE THIS
- `claude_desktop_config.template.json` (template for other users)

### 2. Fixed All References
Updated references in documentation files:
- `manual_testing/README.md`
- `manual_testing/PRE_FLIGHT_CHECKLIST.md`
- `TESTING_STATUS.md`

**Before:** `claude_desktop_config_fixed.json`
**After:** `claude_desktop_config.json`

### 3. Added Documentation
Created comprehensive `README.md` in configs folder:
- File descriptions and purposes
- Configuration details and requirements
- Why full venv paths are needed
- Environment variable explanations
- DRY_RUN mode documentation
- Installation instructions
- Verification steps
- Troubleshooting guide

---

## Validation

### JSON Syntax
```bash
python3 -m json.tool claude_desktop_config.json
# ✅ Valid JSON
```

### Server Count
```bash
cat claude_desktop_config.json | grep -c "\"command\""
# Expected: 8 servers
```

### All Paths Exist
```bash
for server in fgbio spatialtools openimagedata seqera huggingface deepcell mockepic tcga; do
  path=$(cat claude_desktop_config.json | grep "mcp-$server/venv/bin/python" | cut -d'"' -f4)
  if [ -f "$path" ]; then
    echo "✅ $server: $path"
  else
    echo "❌ $server: Path not found"
  fi
done
```

---

## Migration Guide

If you previously used an old config file:

### Step 1: Backup Old Config (if already installed)
```bash
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json \
   ~/Desktop/claude_config_backup_$(date +%Y%m%d).json
```

### Step 2: Install New Config
```bash
cp configs/claude_desktop_config.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Step 3: Restart Claude Desktop
Quit and relaunch Claude Desktop

### Step 4: Verify All Servers Load
In Claude Desktop:
```
What MCP servers are available?
```

Expected: All 8 servers listed

---

## Troubleshooting

### Old References Still Showing Errors

If you see references to `claude_desktop_config_fixed.json` in error messages:

**Solution:** The file was renamed. Use `claude_desktop_config.json` instead.

### "Could not connect to MCP server"

**Causes:**
1. Config not in correct location
2. Invalid Python paths
3. Virtual environments not installed

**Solutions:**
1. Verify config location:
   ```bash
   ls -l ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Verify all venv paths exist:
   ```bash
   for server in fgbio spatialtools openimagedata seqera huggingface deepcell mockepic tcga; do
     ls /Users/lynnlangit/Documents/GitHub/spatial-mcp/servers/mcp-$server/venv/bin/python
   done
   ```

3. Reinstall dependencies:
   ```bash
   cd ../manual_testing
   ./install_dependencies.sh
   ```

---

## Summary

**Status:** ✅ Configuration files cleaned up and organized

**Active Config:** `claude_desktop_config.json` (ready to use)

**Documentation:** `README.md` (complete guide)

**Template:** `claude_desktop_config.template.json` (for other users)

**Next Step:** Copy config to Claude Desktop and test

---

**Last Updated:** October 25, 2025
