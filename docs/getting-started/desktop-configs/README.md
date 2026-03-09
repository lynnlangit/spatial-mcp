# Claude Desktop Configuration Files

This folder contains configuration files for connecting Claude Desktop to the Precision Medicine MCP servers.

---

## 📁 Files

### `claude_desktop_config.json` ✅ USE THIS FILE

**Status:** ✅ **Ready to use** - Pre-configured for this system

**Purpose:** Production-ready configuration with full absolute paths to all MCP servers.

**Contains:**
- All MCP servers ([Server Registry](../../../docs/reference/shared/server-registry.md))
- Uses `uv run --directory` syntax (no manual venv setup needed)
- All required environment variables
- DRY_RUN mode enabled by default for quick & safe testing

**How to use:**
```bash
# Copy to Claude Desktop config location
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop
# All servers should now be available
```

---

### `claude_desktop_config.template.json` 📝 TEMPLATE

**Purpose:** Template for other users or different installations.

**Contains:**
- Same structure as the main config (all servers)
- Uses `uv run --directory` syntax (same as main config)
- Placeholder paths: `/ABSOLUTE/PATH/TO/spatial-mcp/...`

**How to use:**
1. Copy template to a new file
2. Replace all `/ABSOLUTE/PATH/TO/` placeholders with your actual installation path
3. Copy to Claude Desktop config location

**Example replacements:**
```
Before: "/ABSOLUTE/PATH/TO/spatial-mcp/servers/mcp-fgbio"
After:  "/Users/yourname/projects/spatial-mcp/servers/mcp-fgbio"
```

---


## 🔧 Configuration Details

### Why `uv run --directory`?

Claude Desktop runs in a sandboxed environment and cannot resolve `python` or `python3` commands. Using `uv run --directory` lets `uv` handle the virtual environment and dependencies automatically.

**❌ This will NOT work:**
```json
"command": "python"
```

**✅ This WILL work:**
```json
"command": "uv",
"args": ["run", "--directory", "/Users/lynnlangit/Documents/GitHub/spatial-mcp/servers/mcp-fgbio", "python", "-m", "mcp_fgbio"]
```

### Environment Variables

📋 **[See Complete Server Status →](../../../servers/README.md#-server-status)** - All servers with tools, status, and documentation

Each server requires specific environment variables:

| Server | Required Variables | Purpose |
|--------|-------------------|---------|
| **fgbio** | `FGBIO_REFERENCE_DATA_DIR`<br>`FGBIO_CACHE_DIR`<br>`FGBIO_DRY_RUN` | Reference genome paths<br>Cache location<br>Mock execution mode |
| **spatialtools** | `SPATIAL_DATA_DIR`<br>`SPATIAL_CACHE_DIR`<br>`SPATIAL_OUTPUT_DIR`<br>`SPATIAL_DRY_RUN` | Data directory<br>Cache location<br>Visualization output<br>Mock execution mode |
| **openimagedata** | `IMAGE_DATA_DIR`<br>`IMAGE_DRY_RUN` | Image storage<br>Mock execution mode |
| **mockepic** | `EPIC_DRY_RUN` | Mock execution mode |
| **mocktcga** | `MOCKTCGA_DRY_RUN` | Mock execution mode |
| **multiomics** | `MULTIOMICS_DATA_DIR`<br>`MULTIOMICS_CACHE_DIR`<br>`MULTIOMICS_DRY_RUN` | Multi-omics data directory<br>Cache location<br>Mock execution mode |
| **perturbation** | `PERTURBATION_DATA_DIR`<br>`PERTURBATION_MODEL_DIR`<br>`PERTURBATION_DRY_RUN` | Perturbation data<br>Model storage<br>Mock execution mode |
| **quantum-celltype-fidelity** | `QUANTUM_BACKEND`<br>`QUANTUM_DATA_DIR`<br>`QUANTUM_CACHE_DIR` | CPU/GPU backend<br>Data directory<br>Cache location |
| **patient-report** | `PATIENT_REPORT_OUTPUT_DIR`<br>`PATIENT_REPORT_TEMPLATES_DIR`<br>`PATIENT_REPORT_DRY_RUN` | Report output<br>Templates path<br>Mock execution mode |
| **deepcell** | `DEEPCELL_OUTPUT_DIR`<br>`DEEPCELL_DRY_RUN`<br>`DEEPCELL_USE_GPU` | Output directory<br>Mock execution mode<br>GPU acceleration |
| **cell-classify** | `CELL_CLASSIFY_OUTPUT_DIR`<br>`CELL_CLASSIFY_DRY_RUN` | Output directory<br>Mock execution mode |
| **genomic-results** | `GENOMIC_RESULTS_DRY_RUN` | Mock execution mode |
| **geodownload** | `GEO_DRY_RUN` | Mock execution mode |
| **opentargets** | `OPENTARGETS_DRY_RUN` | Mock execution mode |
| **cibersortx** | `CIBERSORTX_DRY_RUN` | Mock execution mode |
| **neoantigen** | `NEOANTIGEN_DRY_RUN` | Mock execution mode |
| **epic** | `EPIC_FHIR_ENDPOINT`<br>`EPIC_CLIENT_ID`<br>`EPIC_CLIENT_SECRET`<br>`DEIDENTIFY_ENABLED` | FHIR endpoint URL<br>OAuth client ID<br>OAuth client secret<br>PHI de-identification |

### DRY_RUN Mode

All servers are configured with `DRY_RUN=true` by default (synthetic data, no external dependencies). To disable, set the server-specific variable to `false` (e.g., `"FGBIO_DRY_RUN": "false"`).

> **Full details:** See [DRY_RUN Mode Guide](../../../docs/reference/shared/dry-run-mode.md) for per-server variables and requirements.

---

## 📍 Installation Path

The current configuration is set up for:
```
/Users/lynnlangit/Documents/GitHub/spatial-mcp/
```

If you cloned the repository to a different location, you'll need to:
1. Copy `claude_desktop_config.template.json` to a new file
2. Replace all placeholder paths with your installation path
3. Use that customized config file

---

## ✅ Verification

### Verify Config is Installed
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep "mcpServers"
```

Expected output: Should show the config JSON

### Verify All Server Paths Exist
```bash
for server in fgbio spatialtools openimagedata mockepic tcga multiomics perturbation quantum-celltype-fidelity patient-report geodownload opentargets cibersortx neoantigen; do
  echo "Checking mcp-$server..."
  ls /Users/lynnlangit/Documents/GitHub/spatial-mcp/servers/mcp-$server/
done
```

Expected: All server directories should be found

### Verify in Claude Desktop

After installing the config and restarting Claude Desktop:

```
What MCP servers are available?
```

Expected response: List of all servers with their tools

---

## 🚀 Quick Start

1. **Install server dependencies** (if not done):
   ```bash
   cd ../manual_testing
   ./install_dependencies.sh
   ```

2. **Install config**:
   ```bash
   cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. **Restart Claude Desktop**

4. **Verify servers loaded**:
   ```
   What MCP servers are available?
   ```

5. **Run first test**:
   - Open `../manual_testing/PatientOne-OvarianCancer/implementation/TEST_1_CLINICAL_GENOMIC.txt`
   - Copy and paste test into Claude Desktop

---

## 🔧 Troubleshooting

### Issue: "Could not connect to MCP server"

**Cause:** Config file not in correct location or invalid paths

**Solutions:**
1. Verify config location:
   ```bash
   ls -l ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Check JSON syntax is valid:
   ```bash
   python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. Verify all venv paths exist (see verification section above)

4. Restart Claude Desktop completely (Quit and relaunch)

### Issue: Some servers load, others don't

**Cause:** Individual server venv not properly installed

**Solution:** Reinstall specific server:
```bash
cd servers/mcp-fgbio  # Change to problematic server
uv sync
uv run python -c "import mcp_fgbio; print('OK')"
```

### Issue: Config file gets overwritten

**Cause:** Claude Desktop may reset config on updates

**Solution:** Keep a backup and re-apply:
```bash
# Create backup
cp claude_desktop_config.json ~/Desktop/claude_desktop_config_backup.json

# Restore if needed
cp ~/Desktop/claude_desktop_config_backup.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

---



