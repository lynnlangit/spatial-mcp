# MCP Cost & Performance Observatory Dashboard

**Real-time observability for MCP server token usage, latency, and costs**

Monitor and optimize your precision medicine MCP server architecture for production deployment. Track "cost per insight" and identify optimization opportunities across all MCP servers plus 3 Streamlit client apps. Toggle **Live Mode** to poll real Cloud Run health status, query GCP Cloud Logging for live traffic metrics, and view actual token usage and costs from the audit log.

> **Related:** [Cost Analysis](../../docs/reference/shared/cost-analysis.md) | [Platform Overview](../../docs/reference/shared/README.md) | [Deployment Templates](../../docs/reference/shared/deployment-templates.md)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run dashboard (from `cd ui/dashboard`)
streamlit run streamlit_app.py

# 3. Open browser
# Dashboard automatically opens at http://localhost:8501
```

---

## What This Dashboard Does

### For Platform Builders
- **Cost Visibility**: See exactly how much each tool call costs in real-time
- **Performance Monitoring**: Track latency across all MCP servers
- **Resource Planning**: Project monthly/annual costs based on usage patterns
- **Optimization Guidance**: Get specific recommendations to reduce costs

### For Workflow Architects
- **Cost Per Insight**: Understand the ROI of each analytical step
- **Server Comparison**: Identify bottlenecks and expensive operations
- **Model Selection**: Compare costs across Claude Sonnet/Opus/Haiku
- **Scaling Analysis**: Estimate costs as you scale from demo to production

---

## Dashboard Views

### 📈 Overview
- High-level metrics (total cost, tool calls, duration)
- Cost breakdown by server
- Token distribution (input vs output)
- Workflow execution summary
- **Live Mode:** live traffic summary — total requests, error count, avg latency, and per-server request chart from Cloud Logging
- **Live Mode:** live token usage & costs — actual LLM token consumption and costs from audit log

![Overview](../../data/images/dash-1.png)

### 💰 Cost Analysis
- Detailed cost breakdown by server and tool
- Top 10 most expensive tool calls
- Model cost comparison (Claude Sonnet/Opus/Haiku + Gemini 3 Flash/Pro)
- Monthly/annual cost projections
- **Live Mode:** live token costs — actual usage from Streamlit client audit logs

![Cost Analysis](../../data/images/dash-2.png)

### ⚡ Performance
- Latency analysis by server
- Execution timeline (cost/tokens over time)
- Token processing efficiency
- Bottleneck identification
- **Live Mode:** real Avg vs P95 latency bar chart pulled directly from Cloud Run request logs

### 🔧 Optimization
- Automated cost-reduction recommendations
- Potential savings calculator
- Strategy comparison (caching, batching, model switching)
- Export reports for planning
- **Live Mode:** live error-signal warnings per server (error count, rate) from Cloud Logging
- **Live Mode:** high-cost server detection — flags servers exceeding $0.50/24h with per-query breakdown

![Optimization](../../data/images/dash-4.png)

---

## Sample Data

The dashboard includes sample metrics from **PatientOne Complete Workflow**:
- **Patient**: PAT001-OVC-2025 (Stage IV HGSOC)
- **Analysis**: End-to-end precision medicine workflow
- **Servers**: All MCP servers (mcp-epic, mcp-spatialtools, mcp-multiomics, etc.)
- **Tool Calls**: 27 tool invocations
- **Total Cost**: $1.45 (Claude Sonnet 4.5)
- **Duration**: 127 seconds

See [sample_data/patientone_workflow.yaml](sample_data/patientone_workflow.yaml) for full metrics.

---

## Architecture

```
ui/dashboard/
├── streamlit_app.py              # Main Streamlit dashboard (Sample + Live modes)
├── live_server_monitor.py        # Health polling + Cloud Logging queries
├── cost_calculator.py            # Anthropic API pricing calculations
├── metrics_aggregator.py         # Load and process workflow metrics (YAML)
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Cloud Run container image
├── deploy.sh                     # Cloud Run deploy script (provisions SA, grants IAM)
├── sample_data/
│   └── patientone_workflow.yaml  # Sample PatientOne metrics
└── README.md                     # This file
```

### Data Flow

```
┌─ Sample Mode ──────────────────┐   ┌─ Live Mode ────────────────────────┐
│ Workflow Metrics (YAML)        │   │ Cloud Run / endpoints (health)     │
│         ↓                      │   │         ↓                          │
│ metrics_aggregator.py          │   │ live_server_monitor.py             │
│         ↓                      │   │   (async httpx health poll)        │
│ cost_calculator.py             │   │         +                          │
│         ↓                      │   │ GCP Cloud Logging                  │
└─────────┬──────────────────────┘   │   (request counts, latency, errs)  │
          │                          │         +                          │
          │                          │ mcp-audit-log                      │
          │                          │   (token usage, costs from clients)│
          │                          └────────────┬───────────────────────┘
          ↓                                       ↓
          └───────────────┬───────────────────────┘
                          ↓
              streamlit_app.py
                          ↓
              Interactive Dashboard
```

---

## Using Your Own Data

### Option 1: YAML File (Recommended for Quick Win)

Create a YAML file with your workflow metrics:

```yaml
workflow_metadata:
  name: "My Analysis Workflow"
  patient_id: "patient-123"
  analysis_date: "2026-01-12T10:00:00Z"
  model: "claude-sonnet-4-5-20250929"

tool_calls:
  - server: "mcp-spatialtools"
    tool: "perform_differential_expression"
    timestamp: "2026-01-12T10:05:00Z"
    input_tokens: 8500
    output_tokens: 2100
    latency_ms: 3500
    status: "success"

  # ... more tool calls ...
```

Load in dashboard:
```python
from metrics_aggregator import MetricsAggregator

aggregator = MetricsAggregator("path/to/your/metrics.yaml")
```

### Option 2: Live Mode (built in)

Toggle **Live Mode** in the sidebar.  The dashboard automatically:

1. **Health-polls** all 15 Cloud Run services (12 MCP servers + 3 Streamlit clients — see [Server Registry](../../docs/reference/shared/server-registry.md)) via root `/` endpoint (10 s timeout, 2 retries) and displays status badges (healthy / degraded / unhealthy).
2. **Queries GCP Cloud Logging** for the selected time window (1 h – 7 d) and surfaces per-service request counts, avg/p95 latency, and error rates.
3. **Queries mcp-audit-log** for actual token usage and costs logged by Streamlit clients via `audit_logger.py`. Shows total tokens, costs, and per-MCP-server breakdown.

No manual log export or custom parser needed.  The deployed service account (`mcp-dashboard-sa`) has `roles/logging.viewer` — the minimum permission required.

**Monitored Services:**
- **MCP Servers (12 deployed):** fgbio, multiomics, spatialtools, perturbation, quantum-celltype-fidelity, deepcell, cell-classify, mocktcga, openimagedata, mockepic, patient-report, genomic-results (note: mcp-epic is local-only, not on Cloud Run)
- **Streamlit Clients (3):** mcp-dashboard, streamlit-mcp-chat, streamlit-mcp-chat-students

---

## Cost Calculator Usage

### Standalone Cost Calculations

```python
from cost_calculator import calculate_cost, estimate_monthly_cost, compare_model_costs

# Calculate cost for single tool call
cost = calculate_cost(input_tokens=8000, output_tokens=2000)
print(f"Total: ${cost['total_cost']:.4f}")
# Output: Total: $0.0540

# Compare models
comparison = compare_model_costs(10000, 2000)
for model, data in comparison.items():
    print(f"{model}: ${data['total_cost']:.4f}")
# Output:
# Claude Sonnet 4.5: $0.0600
# Claude Opus 4.5: $0.3000
# Claude Haiku 4.5: $0.0050

# Project monthly costs
monthly = estimate_monthly_cost(
    daily_tool_calls=50,
    avg_input_tokens=8000,
    avg_output_tokens=2000
)
print(f"Monthly: ${monthly['monthly_cost']:.2f}")
# Output: Monthly: $81.00
```

### LLM API Pricing (as of Feb 2026)

**Anthropic Claude Models:**

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude Sonnet 4.5 | $3.00 | $15.00 |
| Claude Opus 4.5 | $15.00 | $75.00 |
| Claude Haiku 4.5 | $0.25 | $1.25 |

**Google Gemini 3 Models:**

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Gemini 3 Flash | $0.50 | $3.00 |
| Gemini 3 Pro (≤200K context) | $2.00 | $12.00 |
| Gemini 3 Pro (>200K context) | $4.00 | $18.00 |

**Key Insight**: Haiku is ~92% cheaper than Sonnet; Gemini 3 Flash is 83% cheaper than Sonnet. Use for simple lookups!

---

## Optimization Strategies

### Strategy 1: Use Haiku for Simple Queries

**Savings**: 90%+ for low-complexity tools

**Good candidates**:
- `mcp-fgbio.get_reference_genome_info` (reference lookups)
- `mcp-mocktcga.query_mutation_frequency` (database queries)
- `mcp-epic.get_patient_demographics` (FHIR data retrieval)

**Implementation**:
```python
# In MCP server, add model parameter
@mcp.tool()
async def get_reference_genome_info(genome: str, model: str = "haiku"):
    # Use Haiku for simple reference lookups
    pass
```

### Strategy 2: Cache Expensive Computations

**Savings**: 30-50% for repeated analyses

**Target**: `mcp-multiomics.run_halla_analysis` (18K input, 6.8K output tokens)

**Implementation**:
```python
import hashlib
import json

def cache_key(data):
    return hashlib.md5(json.dumps(data).encode()).hexdigest()

@mcp.tool()
async def run_halla_analysis(data):
    key = cache_key(data)
    if key in cache:
        return cache[key]

    result = expensive_halla_computation(data)
    cache[key] = result
    return result
```

### Strategy 3: Batch Visualization Generation

**Savings**: 15-20% by reducing overhead

**Target**: `mcp-spatialtools` (6 separate visualization calls)

**Implementation**:
```python
@mcp.tool()
async def generate_all_visualizations(data):
    # Generate all 6 visualizations in one call
    # Reduces per-call overhead from 6× to 1×
    return {
        "spatial_heatmap": generate_spatial_heatmap(data),
        "gene_expression": generate_gene_expression(data),
        # ...
    }
```

### Strategy 4: Response Streaming

**Savings**: 10-15% by enabling early cancellation

**Implementation**: Use Claude API's streaming mode to stop generation when sufficient information is received.

---

## Cost Projections

### Example: Scaling PatientOne Workflow

**Current Demo Cost**: $1.45 per patient (Sonnet 4.5)

| Workload | Daily Cost | Monthly Cost | Annual Cost |
|----------|-----------|--------------|-------------|
| 10 patients/day | $14.50 | $319 (22 days) | $3,828 |
| 50 patients/day | $72.50 | $1,595 | $19,140 |
| 100 patients/day | $145.00 | $3,190 | $38,280 |

**With Optimizations** (Haiku for simple queries + caching):

| Workload | Daily Cost | Monthly Cost | Annual Cost | Savings |
|----------|-----------|--------------|-------------|---------|
| 10 patients/day | $8.70 | $191 | $2,293 | 40% |
| 50 patients/day | $43.50 | $957 | $11,466 | 40% |
| 100 patients/day | $87.00 | $1,914 | $22,932 | 40% |

---

## Integration with CI/CD

### Automated Cost Tracking

Add dashboard to your CI/CD pipeline:

```yaml
# .github/workflows/cost_check.yml
name: Cost Check

on: [pull_request]

jobs:
  cost-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run test workflow
        run: python run_test_workflow.py --metrics-output test_metrics.yaml

      - name: Analyze costs
        run: |
          pip install -r ui/dashboard/requirements.txt
          python -c "
          from metrics_aggregator import MetricsAggregator
          agg = MetricsAggregator('test_metrics.yaml')
          cost = agg.get_cost_breakdown()['total_cost']
          print(f'Workflow cost: ${cost:.4f}')
          if cost > 2.0:
              print('⚠️ Cost exceeds threshold!')
              exit(1)
          "

      - name: Comment on PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              body: '✅ Cost analysis passed: $1.45'
            })
```

---

## Troubleshooting

### Dashboard Won't Start

**Issue**: `ModuleNotFoundError: No module named 'streamlit'`

**Solution**:
```bash
pip install -r requirements.txt
```

### No Metrics Data

**Issue**: `FileNotFoundError: Sample metrics file not found`

**Solution**: Ensure you're running from the `ui/dashboard/` directory:
```bash
cd ui/dashboard
streamlit run streamlit_app.py
```

### Costs Don't Match Actual API Bills

**Issue**: Dashboard costs are estimates only

**Solution**: Pricing in `cost_calculator.py` reflects Anthropic's published rates (Feb 2026). Verify with:
```bash
python cost_calculator.py
```

Update pricing constants if rates change:
```python
# In cost_calculator.py
PRICING = {
    "claude-sonnet-4-5-20250929": ModelPricing(
        input_price=3.00,  # Update these values
        output_price=15.00,
        name="Claude Sonnet 4.5"
    ),
    # ...
}
```

---

## Deployment Options

### Option 1: Local Development

```bash
streamlit run streamlit_app.py
```

**Use for**: Testing, ad-hoc analysis, local demos

### Option 2: GCP Cloud Run

```bash
cd ui/dashboard
./deploy.sh                          # defaults: precision-medicine-poc, us-central1
./deploy.sh my-project us-east1      # custom project / region
```

`deploy.sh` handles everything:
- Creates `mcp-dashboard-sa` service account (idempotent)
- Grants `roles/logging.viewer` (least privilege for Cloud Logging reads)
- Builds from the included `Dockerfile` and deploys to Cloud Run
- Sets `GCP_PROJECT_ID` and `GCP_REGION` env vars so Live Mode works automatically

**Use for**: Team access, production monitoring, stakeholder demos

### Option 3: Embedded in Jupyter Notebook

```python
# In Jupyter notebook
from metrics_aggregator import load_sample_metrics
import plotly.express as px

aggregator = load_sample_metrics("patientone_workflow")
server_summary = aggregator.get_server_summary()

fig = px.bar(server_summary, x='server', y='total_cost')
fig.show()
```

**Use for**: Research notebooks, interactive analysis, reports

---

## Roadmap

### v1.0 (Current)
- ✅ Sample data from PatientOne workflow
- ✅ Cost calculator with Anthropic API pricing
- ✅ Streamlit dashboard with 4 views
- ✅ Optimization recommendations
- ✅ Export reports (TXT, CSV)
- ✅ Live Mode: health-polling all 15 Cloud Run services (12 MCP servers + 3 Streamlit clients; async, 10 s timeout, 2 retries)
- ✅ Live Mode: GCP Cloud Logging integration — per-server request counts, avg/p95 latency, error rates
- ✅ Live Mode: server-health badges, live traffic chart, Avg vs P95 latency chart, error-signal warnings
- ✅ Dedicated service account (`mcp-dashboard-sa`) with least-privilege `roles/logging.viewer`

### v1.1 (Current - Feb 2026)
- ✅ **Gemini 3 pricing** added to cost calculator (Flash: $0.50/$3.00, Pro: $2.00/$12.00)
- ✅ **Streamlit client monitoring** — dashboard, streamlit-mcp-chat, streamlit-mcp-chat-students
- ✅ **Live token usage & costs** — queries mcp-audit-log for actual LLM usage from Streamlit clients
- ✅ **15 services monitored** — 12 deployed MCP servers + 3 Streamlit clients
- ✅ **Improved health checks** — uses root `/` endpoint, treats any HTTP response as healthy
- ✅ **High-cost server detection** — flags servers >$0.50/24h in optimization view

### v1.2 (Planned)
- [ ] Multi-workflow comparison
- [ ] Historical trend analysis
- [ ] Alert thresholds (configurable error-rate / latency triggers)

### v2.0 (Future)
- [ ] Per-server `/metrics` endpoints for application-level telemetry (token usage at server layer)
- [ ] WebSocket real-time updates (push instead of poll)
- [ ] BigQuery data storage for long-term trend analysis
- [ ] Advanced ML-based optimization suggestions
- [ ] Cost anomaly detection

---

## API Reference

### MetricsAggregator

```python
class MetricsAggregator:
    """Aggregates and analyzes MCP server metrics."""

    def __init__(self, metrics_file: str):
        """Load metrics from YAML file."""

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get high-level summary statistics."""

    def get_server_summary(self) -> pd.DataFrame:
        """Get per-server metrics aggregation."""

    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get detailed cost breakdown."""

    def get_top_cost_tools(self, n: int = 10) -> pd.DataFrame:
        """Get top N most expensive tool calls."""

    def get_optimization_recommendations(self) -> List[str]:
        """Get cost optimization recommendations."""
```

### CostCalculator

```python
def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> Dict:
    """Calculate cost in USD for given token usage."""

def compare_model_costs(input_tokens: int, output_tokens: int) -> Dict:
    """Compare costs across all Claude models."""

def estimate_monthly_cost(daily_tool_calls: int, avg_input_tokens: int,
                         avg_output_tokens: int, model: str) -> Dict:
    """Estimate monthly costs based on usage patterns."""

def get_optimization_recommendations(server_metrics: Dict) -> List[str]:
    """Generate cost optimization recommendations."""
```

### LiveServerMonitor

```python
# Health polling (async, all services in parallel: MCP servers + Streamlit clients)
def get_live_health() -> Dict[str, Dict]:
    """Sync entry-point.  Returns {server_name: {status, latency_ms, checked_at, error, http_code}}."""

# Cloud Logging queries (Cloud Run request logs)
def query_server_logs(name: str, hours_back: int = 1) -> Dict:
    """Per-server: request_count, avg_latency_ms, p95_latency_ms, error_count, error_rate."""

def query_all_server_logs(hours_back: int = 1) -> Dict[str, Dict]:
    """Bulk query for all deployed services.  Reuses a single logging client."""

# Token Usage queries (mcp-audit-log from Streamlit clients)
def query_token_usage(hours_back: int = 24) -> Dict:
    """Aggregate token usage: total_input/output_tokens, total_cost_usd, query_count, by_server."""

def query_usage_by_user(hours_back: int = 24) -> List[Dict]:
    """Token usage grouped by user (email hash), sorted by cost descending."""

def get_combined_metrics(hours_back: int = 1) -> Dict:
    """Convenience: health + request_logs + token_usage in one call."""
```

---

**🎉 Monitor your MCP costs. Optimize your architecture. Scale with confidence.**
