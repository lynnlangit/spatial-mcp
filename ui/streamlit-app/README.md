# MCP Chat - Streamlit UI for Precision Medicine MCP Servers

A visual chat interface for testing deployed MCP servers on GCP Cloud Run. Provides a Claude Desktop-like experience for bioinformatics workflows.

<img src="../../data/images/streamlit-ui-preview.png" width="800" alt="Streamlit Chat UI Preview">

## Features

- **Chat Interface** — Natural language interaction with MCP servers
- **Multi-Provider** — Choose between Claude (Anthropic) or Gemini (Google) LLMs
- **Server Selection** — Choose which MCP servers to enable (default: fgbio)
- **14 Example Prompts** — Built-in prompts with GCS data paths for PatientOne
- **Token Usage & Caching** — Per-message token tracking with cache metrics (Claude automatic caching, Gemini implicit caching)
- **Token Benchmark** — 3-phase benchmark (Cold/Warm/Repeat) comparing providers across all prompts
- **Orchestration Trace** — See which servers were called and in what order (4 view styles)
- **File Upload** — Secure upload for 21+ bioinformatics file formats (FASTQ, VCF, BAM, H5AD, etc.)
- **GCS Integration** — Direct access to files in Google Cloud Storage buckets
- **Audit Logging** — Per-prompt logging to GCP Cloud Logging
- **IAM Authentication** — Cloud Run IAM-based access control (no public access)

---

## Quick Start

### Prerequisites

- Python 3.11+
- At least one API key: Anthropic ([get one](https://console.anthropic.com/)) or Google AI ([get one](https://aistudio.google.com/apikey))

### Local Development

```bash
cd ui/streamlit-app

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API keys (option A: environment variables)
export ANTHROPIC_API_KEY=your_key_here
export GEMINI_API_KEY=your_key_here  # optional

# Set API keys (option B: .env file)
cp .env.example .env
# Edit .env and add your keys

# Run the app
streamlit run app.py
```

The app opens at http://localhost:8501.

**Mock mode** (no Cloud Run connections needed):
```bash
export USE_MOCK_MCP=true
streamlit run app.py
```

### Deploy to Cloud Run

```bash
cd ui/streamlit-app

# Set keys in .env file, then:
./deploy_now.sh
```

The service deploys with IAM authentication (no public access). Access via proxy:

```bash
gcloud run services proxy streamlit-mcp-chat \
  --region us-central1 \
  --project precision-medicine-poc

# Then open http://localhost:8080
```

---

## Usage

### 1. Select MCP Servers

Use the sidebar to select which servers to enable. Default: **fgbio** (keeps token costs low).

See [Server Registry](../../docs/reference/shared/server-registry.md) for the full list of servers and tools (production and mock).

### 2. Choose a Provider and Model

**Claude:** `claude-sonnet-4-6` (recommended), `claude-opus-4-6`, `claude-haiku-4-5`
**Gemini:** `gemini-3-flash-preview` (recommended), `gemini-2.5-flash`

### 3. Start Chatting

Type a question or select from the 14 built-in prompts in the sidebar. Start with "Warm Up Servers" to wake Cloud Run instances, then try analysis prompts.

### 4. View Results

- Chat history with full conversation
- Token usage per message (input, output, cache read/write, iterations)
- Orchestration trace showing which MCP servers were called

---

## LLM Providers

### Claude (Anthropic) — Native MCP

Claude uses Anthropic's native MCP integration. The API directly orchestrates MCP servers.

```
Streamlit UI -> Claude API (with MCP servers) -> Response
```

- Automatic prompt caching (system prompt + tool definitions cached at 0.1x cost)
- Cumulative token tracking across agentic loop iterations

### Gemini (Google) — SSE-Based MCP

Gemini uses a custom SSE client that connects to MCP servers and manually orchestrates tool calls.

```
Streamlit UI -> MCP SSE Client -> Cloud Run MCP Servers
            |                           |
        Gemini API <- Tool Results <- Tool Execution
```

- SSE connections to each Cloud Run server
- Schema cleaning converts MCP tool schemas to Gemini function declarations
- Agentic loop manages multi-turn tool calling
- Implicit caching (automatic but unreliable — hits ~19% of the time)

---

## Token Benchmark

The app includes a 3-phase token benchmark for comparing providers:

| Phase | What it does | Runs |
|-------|-------------|------|
| **Cold** | Fresh cache, baseline token usage | 14 prompts x 2 providers = 28 |
| **Warm** | Same session, measures cache hits | 14 prompts x 2 providers = 28 |
| **Repeat** | 3 multi-step prompts again, confirms cache stability | 3 prompts x 2 providers = 6 |

Each prompt has a 180-second timeout. Results are logged per-prompt to GCP Cloud Logging and can be exported as CSV.

**Key findings** (see `docs/for-developers/benchmark-findings-2026-02-19.md`):
- Claude caching reduces cost 69% on warm prompts (~14,600 tokens of system+tools cached)
- Gemini Flash is 8x cheaper and 2x faster on simple prompts
- Multi-step prompts can take 1-7 agentic loop iterations (unpredictable)

---

## Orchestration Trace

Toggle "Show trace for responses" in the sidebar. Four view styles:

- **Log View** — Text-based step-by-step log
- **Card View** — Visual cards for each server call
- **Timeline View** — Horizontal timeline showing flow
- **Sequence Diagram** — Mermaid diagram (copyable)

Each trace shows: server called, tool invoked, input parameters, result summary, timing metrics.

Export traces as JSON or Mermaid via download buttons.

---

## File Upload & GCS Access

### Local Upload

Drag-and-drop files in the sidebar. Supports 21+ formats: FASTA, FASTQ, VCF, GFF, GTF, BED, CSV, TSV, JSON, H5AD, HDF5, PNG, JPEG, TIFF, BAM, and more.

Security: extension whitelist, magic bytes verification, content validation, filename sanitization, 100MB limit.

Small files (< 50KB) are included inline for the LLM to analyze directly. Large files pass metadata only — MCP tools access the data.

### GCS Access

Enter a GCS URI (`gs://bucket/path/file`) in the sidebar. MCP servers on Cloud Run access GCS files directly via service account (cloud-to-cloud, no local bottleneck).

```bash
# Grant Cloud Run service account access to a GCS bucket
PROJECT_NUMBER=$(gcloud projects describe precision-medicine-poc --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:objectViewer gs://your-bucket-name
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes (for Claude) | Anthropic API key |
| `GEMINI_API_KEY` | No | Google AI API key (enables Gemini provider) |
| `USE_MOCK_MCP` | No | `true` for mock mode (no Cloud Run connections) |
| `DEFAULT_MODEL` | No | Default LLM model (default: `claude-sonnet-4-6`) |
| `DEFAULT_MAX_TOKENS` | No | Default max tokens (default: 4096) |
| `ENVIRONMENT` | No | `development` or `production` |

### MCP Server URLs

Server URLs are configured in `utils/mcp_config.py`. See [Server Registry](../../docs/reference/shared/server-registry.md) for the full list.

### Authentication

The app deploys with `--no-allow-unauthenticated` (Cloud Run IAM). To grant access:

```bash
gcloud run services add-iam-policy-binding streamlit-mcp-chat \
  --member=user:you@example.com \
  --role=roles/run.invoker \
  --region us-central1 \
  --project precision-medicine-poc
```

Access via authenticated proxy:
```bash
gcloud run services proxy streamlit-mcp-chat \
  --region us-central1 --project precision-medicine-poc
# Open http://localhost:8080
```

---

## Architecture

```
Streamlit UI (Browser)
    |
Provider Abstraction Layer
    |-- Claude Provider (Native MCP)
    |       |
    |   Anthropic Claude API
    |       |
    |   [Direct MCP orchestration, automatic caching]
    |
    +-- Gemini Provider (SSE-based MCP)
            |
        MCP SSE Client --> Cloud Run MCP Servers
            |                      |
        Google Gemini API <- Tool Results
            |
    [Manual agentic loop]
    |
GCP Cloud Run MCP Servers
    |
Bioinformatics Tools (STAR, ComBat, HAllA, GEARS, etc.)
```

### Project Structure

```
ui/streamlit-app/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image for Cloud Run
├── deploy.sh                       # Deployment script (parameterized)
├── deploy_now.sh                   # Quick deploy (reads .env)
├── validate.sh                     # Pre-deployment validation
├── .env.example                    # Environment variable template
├── providers/
│   ├── __init__.py                 # Provider factory
│   ├── base.py                     # Abstract base class + UsageInfo
│   ├── anthropic_provider.py       # Claude with native MCP + caching
│   └── gemini_provider.py          # Gemini with SSE-based MCP client
└── utils/
    ├── mcp_config.py               # Server configs + 14 example prompts
    ├── mcp_client.py               # SSE-based MCP client (for Gemini)
    ├── mcp_mock.py                 # Mock MCP client (USE_MOCK_MCP=true)
    ├── trace_utils.py              # Orchestration trace extraction
    ├── trace_display.py            # Trace visualization components
    ├── file_validator.py           # File upload security validation
    ├── gcs_handler.py              # Google Cloud Storage integration
    ├── audit_logger.py             # Audit logging (GCP Cloud Logging)
    └── auth.py                     # Authentication (SSO)
```

---

## Deployment Options

| Environment | Best For | Auth | Cost |
|-------------|----------|------|------|
| **Local** | Testing, debugging | None | Free |
| **Streamlit Cloud** | Public demos | None (public) | Free |
| **GCP Cloud Run** | Production | IAM | ~$5-20/month |

### Cloud Run Details

The deploy scripts use these settings:

| Setting | Value |
|---------|-------|
| Region | us-central1 |
| Memory | 2Gi |
| CPU | 1 |
| Min instances | 0 (scales to zero) |
| Max instances | 5 |
| Timeout | 300s |
| Auth | IAM (no public access) |
| Port | 8501 |

### Rollback

```bash
# List revisions
gcloud run revisions list --service streamlit-mcp-chat --region us-central1

# Rollback to a previous revision
gcloud run services update-traffic streamlit-mcp-chat \
  --to-revisions REVISION_NAME=100 --region us-central1
```

### Monitoring

```bash
# View logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=streamlit-mcp-chat" \
  --limit 50 --project precision-medicine-poc

# Errors only
gcloud logging read \
  "resource.labels.service_name=streamlit-mcp-chat AND severity>=ERROR" \
  --limit 20 --project precision-medicine-poc

# Health check
curl https://YOUR-SERVICE-URL/_stcore/health
```

---

## Troubleshooting

### API Keys

```bash
# "API Key Missing" — set the environment variable or .env file
export ANTHROPIC_API_KEY=your_key_here

# "Invalid API key" — check for extra spaces or quotes
echo $ANTHROPIC_API_KEY
```

### Server Connection

```bash
# Check server is responding
curl https://mcp-spatialtools-ondu7mwjpa-uc.a.run.app/sse

# Timeout errors are normal for long analyses (GEARS training: 5-10 min)
# Increase timeout: --timeout 600 in deploy script
```

### Provider Issues

- **Claude "Provider not available"** — check `ANTHROPIC_API_KEY` is set
- **Gemini "Connection to MCP server failed"** — check firewall allows HTTPS to `*.run.app`
- **Gemini "Maximum tool calling iterations reached"** — break query into smaller steps

### Deployment

```bash
# "Container failed to start" — check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# "Port already in use" locally
lsof -ti:8501 | xargs kill -9

# Validate before deploying (catches errors before 5-min Cloud Run build)
./validate.sh && ./deploy_now.sh
```

### Performance

- Use `claude-haiku-4-5` or `gemini-3-flash-preview` for faster responses
- Select fewer MCP servers (only enable what you need)
- Default is fgbio only to keep token costs low
- First request after idle has a cold start (10-30s)

---

## Cost

Claude's automatic caching provides estimated cost savings on warm prompts. Gemini Flash is cheaper for simple queries. See [Cost Analysis](../../docs/reference/shared/cost-analysis.md) for budget planning.
