# Gemini Setup Guide

*For students and teams using Google Gemini instead of Claude*

---

## When to Use This Guide

Use this guide if your organization has **Google Gemini licenses but not Claude access**. All MCP servers in this repo work with both Claude and Gemini — the servers don't care which AI model calls them.

**Three setup paths** (pick one):

| Path | Best For | Requirements |
|------|----------|-------------|
| **A. VSCode + Gemini Code Assist** | Corporate laptops with Gemini licenses | VSCode, Gemini Code Assist extension |
| **B. Gemini CLI (terminal)** | Developers who prefer the terminal | Node.js 18+, `@google/gemini-cli` |
| **C. Streamlit Student App** | Browser-based, no local MCP config | GCP project for Cloud Run deployment |

---

## Prerequisites (All Paths)

```bash
# 1. Python 3.11+ and git
python3 --version   # must be 3.11+
git --version

# 2. Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Clone the repo
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp

# 4. Install at least one MCP server to test with
cd servers/mcp-mockepic && uv sync && cd ../..
```

---

## Path A: VSCode + Gemini Code Assist

This is the most common setup for corporate environments with existing Gemini licenses.

### Step 1: Install Extensions

In VSCode, install:
- **Google Cloud Code** extension
- **Gemini Code Assist** extension

Sign in with your corporate Google account when prompted.

### Step 2: Configure MCP Servers

Create or edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "mockepic": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/precision-medicine-mcp/servers/mcp-mockepic",
        "python",
        "-m",
        "mcp_mockepic"
      ],
      "env": {
        "EPIC_DRY_RUN": "true"
      }
    }
  }
}
```

**Replace** `/ABSOLUTE/PATH/TO/` with your actual path (e.g., `/Users/yourname/Documents/GitHub/`).

> **Corporate Mac tip**: Use absolute paths for the `uv` command too if it's not on your system PATH. Find it with `which uv` and use the full path (e.g., `/Users/yourname/.local/bin/uv`).

### Step 3: Enable Agent Mode

This is the critical step. Without Agent Mode, Gemini will **describe** tools instead of **calling** them.

1. Open the Gemini side panel in VSCode
2. Look for the **Agent** or **Spark** toggle — it must be **active** (highlighted)
3. If you don't see the toggle, check **VSCode Settings** > search for `gemini` > look for agent-related settings

> **Note**: The exact setting name may vary by extension version. Check the Gemini Code Assist extension settings UI rather than editing JSON directly.

### Step 4: Verify

1. Type `/mcp` in the Gemini chat panel — your server should show **CONNECTED**
2. Test with an explicit prompt:

```
Use the mockepic tool to get patient demographics for patient-001. Execute now.
```

**Expected**: Gemini calls the MCP tool and returns Sarah Anderson's demographics (58yo, Stage IV HGSOC).

**If Gemini describes the tool instead of calling it**: You're still in Chat Mode, not Agent Mode. Go back to Step 3.

### Adding More Servers

Once mockepic works, add servers to `~/.gemini/settings.json` one at a time. Start with these for the PatientOne workflow:

```json
{
  "mcpServers": {
    "mockepic": {
      "command": "uv",
      "args": ["run", "--directory", "/ABSOLUTE/PATH/TO/precision-medicine-mcp/servers/mcp-mockepic", "python", "-m", "mcp_mockepic"],
      "env": { "EPIC_DRY_RUN": "true" }
    },
    "spatialtools": {
      "command": "uv",
      "args": ["run", "--directory", "/ABSOLUTE/PATH/TO/precision-medicine-mcp/servers/mcp-spatialtools", "python", "-m", "mcp_spatialtools"],
      "env": { "SPATIAL_DATA_DIR": "/ABSOLUTE/PATH/TO/precision-medicine-mcp/data", "SPATIAL_DRY_RUN": "true" }
    },
    "multiomics": {
      "command": "uv",
      "args": ["run", "--directory", "/ABSOLUTE/PATH/TO/precision-medicine-mcp/servers/mcp-multiomics", "python", "-m", "mcp_multiomics"],
      "env": { "MULTIOMICS_DATA_DIR": "/ABSOLUTE/PATH/TO/precision-medicine-mcp/data/multiomics", "MULTIOMICS_DRY_RUN": "true" }
    },
    "fgbio": {
      "command": "uv",
      "args": ["run", "--directory", "/ABSOLUTE/PATH/TO/precision-medicine-mcp/servers/mcp-fgbio", "python", "-m", "mcp_fgbio"],
      "env": { "FGBIO_DRY_RUN": "true" }
    }
  }
}
```

For the full list of all servers and their environment variables, see the [Claude Desktop config template](desktop-configs/claude_desktop_config.template.json) — the server names, args, and env vars are identical for Gemini.

---

## Path B: Gemini CLI (Terminal)

The Gemini CLI is a terminal-based alternative, similar to Claude Code. FastMCP has built-in support for installing servers into it.

### Step 1: Install Gemini CLI

```bash
npm install -g @google/gemini-cli
gemini --version   # verify installation
```

### Step 2: Install MCP Servers

FastMCP can register servers directly:

```bash
cd servers/mcp-mockepic
uv run fastmcp install gemini-cli src/mcp_mockepic/server.py \
  --name mockepic \
  --env EPIC_DRY_RUN=true
```

Or manually edit `~/.gemini/settings.json` using the same JSON format from Path A above.

### Step 3: Verify

```bash
gemini   # launches the Gemini CLI
# Then type: "Use mockepic to get demographics for patient-001"
```

---

## Path C: Streamlit Student App (Browser)

The repo includes a pre-built student web app that uses Gemini and connects to MCP servers deployed on GCP Cloud Run. No local MCP configuration needed — students just open a browser.

**Requirements**: A GCP project with MCP servers deployed to Cloud Run (see the [deployment guide](../../infrastructure/deployment/)).

### Setup

```bash
cd ui/streamlit-app-students
cp .env.example .env
# Edit .env: add your GEMINI_API_KEY
# Set USE_MOCK_MCP=true for weeks 1-2

pip install -r requirements.txt
streamlit run app.py
```

**Safety guardrails** (built in):
- Max 4,096 tokens per request
- Max 50,000 tokens per session (~$1.50)
- Max 50 requests per session

See the [student app .env.example](../../ui/streamlit-app-students/.env.example) for all configuration options.

---

## Corporate Mac Troubleshooting

### Server won't connect

**Symptom**: `/mcp` shows server not connected, or no servers listed.

**Fixes** (try in order):
1. **Absolute paths**: Replace `uv` with output of `which uv` in your settings.json
2. **Restart VSCode**: MCP config changes require a restart
3. **Check Python**: Run `uv run --directory /path/to/server python -m mcp_mockepic` in terminal first — if it fails there, fix that before debugging VSCode

### Tools listed but not executed

**Symptom**: Gemini says "I can see the mockepic tool has these functions..." but doesn't call them.

**Fixes**:
1. **Agent Mode**: Toggle must be active (Step 3 above)
2. **Explicit prompts**: Use action-oriented language:
   - Instead of: "What data is available for PatientOne?"
   - Try: "Use the mockepic tool to get patient demographics for patient-001. Execute now."
3. **Model selection**: Use Gemini 2.5 Flash or newer — older models have weaker tool-calling

### Proxy blocks MCP server

**Symptom**: Server starts but can't reach external APIs, or connection times out.

**Fix**: MCP servers run as child processes of VSCode. If your corporate proxy requires configuration, set proxy env vars in your settings.json:

```json
{
  "mcpServers": {
    "mockepic": {
      "command": "uv",
      "args": ["..."],
      "env": {
        "EPIC_DRY_RUN": "true",
        "HTTPS_PROXY": "http://your-corporate-proxy:8080"
      }
    }
  }
}
```

### Complex JSON output causes errors

**Symptom**: Tool fires but Gemini shows "improper format" or gets stuck in a loop.

**Fix**: Set `DRY_RUN=true` for initial testing — DRY_RUN responses are simpler and less likely to trigger Gemini's JSON parsing issues. Once basic connectivity works, switch to `DRY_RUN=false` for real analysis.

---

## Study Group Quick Checklist

For instructors setting up a study group on corporate Macs:

- [ ] **Before session 1**: Create a standardized `settings.json` with absolute paths for your team's machines
- [ ] **Session 1 (30 min)**: Everyone installs extensions, copies config, verifies `/mcp` shows CONNECTED
- [ ] **Session 1 test**: Everyone runs `"Use mockepic to get demographics for patient-001. Execute now."` and gets a result
- [ ] **Weeks 1-2**: Use `DRY_RUN=true` (free practice, synthetic data)
- [ ] **Week 3+**: Switch to `DRY_RUN=false` for real analysis

---

## Gemini vs Claude: What's Different

| Feature | Claude (Code/Desktop) | Gemini (VSCode/CLI) |
|---------|----------------------|---------------------|
| MCP tool calling | Aggressive — calls tools automatically | Requires Agent Mode + explicit prompts |
| Config file | `claude_desktop_config.json` | `~/.gemini/settings.json` |
| Server format | Identical `uv run --directory` syntax | Identical `uv run --directory` syntax |
| Env vars | Identical per-server DRY_RUN vars | Identical per-server DRY_RUN vars |
| Best model for tools | Claude Sonnet 4.5 / Opus 4.6 | Gemini 2.5 Flash / 2.5 Pro |
| Streamlit app | Uses Claude provider | Uses Gemini provider (built in) |

**The MCP servers are identical** — only the AI client configuration differs.

---

## Related Documentation

- **[Server Registry](../reference/shared/server-registry.md)** — All servers with tool counts
- **[DRY_RUN Mode](../reference/shared/dry-run-mode.md)** — How mock mode works
- **[Claude Desktop Configs](desktop-configs/README.md)** — Server config template (same env vars work for Gemini)
- **[Installation Guide](installation.md)** — Claude-specific setup
- **[Educator Guide](../for-educators/README.md)** — Curriculum planning
- **[Student App](../../ui/streamlit-app-students/)** — Browser-based Gemini student interface
