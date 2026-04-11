"""
MCP Cost & Performance Observatory Dashboard

Real-time observability for MCP server token usage, latency, and costs.
Helps architects plan production deployments and optimize resource usage.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
from pathlib import Path

from metrics_aggregator import load_sample_metrics, MetricsAggregator
from cost_calculator import compare_model_costs, estimate_monthly_cost, PRICING


# Page configuration
st.set_page_config(
    page_title="MCP Cost Observatory",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .cost-high { color: #ff4b4b; font-weight: bold; }
    .cost-medium { color: #ffa500; font-weight: bold; }
    .cost-low { color: #00cc00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_metrics_data():
    """Load and cache metrics data."""
    return load_sample_metrics("patientone_workflow")


def format_currency(value: float) -> str:
    """Format value as currency with color coding."""
    if value >= 1.0:
        color_class = "cost-high"
    elif value >= 0.10:
        color_class = "cost-medium"
    else:
        color_class = "cost-low"

    return f'<span class="{color_class}">${value:.4f}</span>'


def main():
    """Main dashboard application."""

    # Header
    st.title("📊 MCP Cost & Performance Observatory")
    st.markdown("""
    **Real-time observability for precision medicine MCP server architecture**

    Monitor token usage, latency, and costs across all 21 deployed MCP servers.
    Optimize resource planning and identify cost-reduction opportunities.
    """)

    # Load data
    try:
        aggregator = load_metrics_data()
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        st.info("Make sure sample_data/patientone_workflow.yaml exists.")
        return

    # ── Sidebar ──────────────────────────────────────────────────────────
    st.sidebar.header("⚙️ Configuration")

    # Live / Sample toggle
    is_live = st.sidebar.toggle(
        "Live Mode",
        value=False,
        help="Poll deployed Cloud Run MCP servers and query GCP Cloud Logging in real time"
    )

    # Time window — only meaningful in Live mode
    time_window_hours = 1
    if is_live:
        time_window_hours = st.sidebar.selectbox(
            "Time Window",
            [1, 6, 24, 168],
            format_func=lambda x: {
                1: "Last 1 hour", 6: "Last 6 hours",
                24: "Last 24 hours", 168: "Last 7 days",
            }[x],
            help="Range of Cloud Run request logs to aggregate"
        )

    # View selector
    view_mode = st.sidebar.radio(
        "View Mode",
        ["📈 Overview", "💰 Cost Analysis", "⚡ Performance", "🔧 Optimization"],
        help="Select analysis view"
    )

    # Refresh controls (Live mode)
    st.sidebar.markdown("---")
    if is_live:
        if st.sidebar.button("🔄 Refresh"):
            st.rerun()
        st.sidebar.caption(f"Checked: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
    else:
        st.sidebar.markdown("### 📅 Filters")
        st.sidebar.info("Enable Live Mode to see real-time server traffic.")

    # ── Load workflow metrics (always — local YAML, cheap) ──────────────
    stats          = aggregator.get_summary_stats()
    server_summary = aggregator.get_server_summary()
    cost_breakdown = aggregator.get_cost_breakdown()
    tool_calls     = aggregator.get_tool_calls()

    # ── Load live data (health + Cloud Logging + Token Usage) when toggle is on ────────
    live_health = None  # type: dict or None
    live_logs   = None  # type: dict or None
    live_tokens = None  # type: dict or None

    if is_live:
        try:
            from live_server_monitor import get_live_health, query_all_server_logs, query_token_usage

            with st.status("Polling server health…", expanded=False) as _s1:
                live_health = get_live_health()
                _s1.update(label="Health check complete", state="complete")

            with st.status("Querying Cloud Logging…", expanded=False) as _s2:
                live_logs = query_all_server_logs(hours_back=time_window_hours)
                _s2.update(label="Cloud Logging data loaded", state="complete")

            with st.status("Querying token usage…", expanded=False) as _s3:
                # Query token usage over a longer window (24h minimum for meaningful data)
                token_hours = max(time_window_hours, 24)
                live_tokens = query_token_usage(hours_back=token_hours)
                _s3.update(label="Token usage data loaded", state="complete")
        except Exception as exc:
            st.warning(f"Live data unavailable: {exc}")
            is_live = False

    # ── Server health banner (Live mode, shown above every view) ─────────
    if is_live and live_health:
        render_server_health_badges(live_health)
        st.divider()

    # ── Route to view ────────────────────────────────────────────────────
    if view_mode == "📈 Overview":
        render_overview(stats, server_summary, cost_breakdown, aggregator, live_logs=live_logs, live_tokens=live_tokens)

    elif view_mode == "💰 Cost Analysis":
        render_cost_analysis(cost_breakdown, server_summary, aggregator, live_tokens=live_tokens)

    elif view_mode == "⚡ Performance":
        render_performance_analysis(server_summary, tool_calls, aggregator, live_logs=live_logs)

    elif view_mode == "🔧 Optimization":
        render_optimization_view(aggregator, server_summary, cost_breakdown, live_logs=live_logs, live_tokens=live_tokens)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Documentation")
    st.sidebar.markdown("[Cost Calculator](cost_calculator.py) | [Metrics Aggregator](metrics_aggregator.py)")
    st.sidebar.markdown("**Last Updated:** 2026-04-11")


def render_server_health_badges(health: dict):
    """Row of health-status metric cards for every polled MCP server."""
    STATUS_ICON = {"healthy": "🟢", "degraded": "🟡", "unhealthy": "🔴", "unknown": "⚪"}
    servers = sorted(health.items())
    cols = st.columns(min(len(servers), 4))
    for i, (name, info) in enumerate(servers):
        col = cols[i % len(cols)]
        icon    = STATUS_ICON.get(info["status"], "⚪")
        latency = f"{info['latency_ms']:.0f} ms" if info["latency_ms"] else "—"
        col.metric(
            label=f"{icon} {name}",
            value=info["status"].capitalize(),
            delta=latency,
            delta_color="off",
        )


def render_live_token_usage(live_tokens: dict):
    """Live token usage and cost summary from audit log."""
    if not live_tokens or live_tokens.get("query_count", 0) == 0:
        window = live_tokens.get("time_window_hours", 24) if live_tokens else 24
        st.info(
            f"No LLM queries recorded in the last {window} hours. "
            "Token usage is logged when users interact with Streamlit chat apps."
        )
        if live_tokens and live_tokens.get("error"):
            st.caption(f"Note: {live_tokens['error']}")
        return

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Queries", f"{live_tokens['query_count']:,}")
    c2.metric("Total Tokens", f"{live_tokens['total_tokens']:,}")
    c3.metric("Total Cost", f"${live_tokens['total_cost_usd']:.2f}")
    c4.metric("Avg Cost/Query", f"${live_tokens['avg_cost_per_query']:.4f}")

    # Token breakdown
    col1, col2 = st.columns(2)

    with col1:
        # Input vs Output tokens pie chart
        token_data = pd.DataFrame({
            'Type': ['Input Tokens', 'Output Tokens'],
            'Tokens': [live_tokens['total_input_tokens'], live_tokens['total_output_tokens']]
        })
        fig_tokens = px.pie(
            token_data,
            values='Tokens',
            names='Type',
            color_discrete_sequence=['#636EFA', '#EF553B'],
            title="Token Distribution"
        )
        fig_tokens.update_layout(height=300)
        st.plotly_chart(fig_tokens, use_container_width=True)

    with col2:
        # Usage by MCP server
        by_server = live_tokens.get("by_server", {})
        if by_server:
            server_data = pd.DataFrame([
                {"server": k, **v} for k, v in by_server.items()
            ]).sort_values("total_cost_usd", ascending=True)

            fig_servers = px.bar(
                server_data,
                y="server",
                x="total_cost_usd",
                orientation="h",
                color="query_count",
                color_continuous_scale="blues",
                labels={
                    "total_cost_usd": "Cost ($)",
                    "server": "MCP Server",
                    "query_count": "Queries"
                },
                title="Cost by MCP Server"
            )
            fig_servers.update_layout(height=300)
            st.plotly_chart(fig_servers, use_container_width=True)
        else:
            st.info("No per-server breakdown available yet.")


def render_live_traffic(live_logs: dict):
    """Live request-count / latency / error summary from Cloud Logging."""
    rows = list(live_logs.values())

    if not rows or all(r["request_count"] == 0 for r in rows):
        window = rows[0]["time_window_hours"] if rows else 1
        st.info(
            f"No requests recorded in the last {window} hour(s). "
            "Try a wider time window or wait for traffic to arrive."
        )
        return

    df = pd.DataFrame(rows)
    total_reqs   = int(df["request_count"].sum())
    total_errors = int(df["error_count"].sum())
    avg_latency  = df.loc[df["request_count"] > 0, "avg_latency_ms"].mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Requests", str(total_reqs))
    c2.metric(
        "Total Errors", str(total_errors),
        delta=f"{total_errors / total_reqs * 100:.1f}%" if total_reqs else "0%",
        delta_color="inverse",
    )
    c3.metric("Avg Latency", f"{avg_latency:.0f} ms" if avg_latency else "—")

    active = df[df["request_count"] > 0].sort_values("request_count", ascending=True)
    if not active.empty:
        fig = px.bar(
            active, y="server", x="request_count", orientation="h",
            color="avg_latency_ms", color_continuous_scale="blues",
            labels={
                "request_count":  "Requests",
                "server":         "Server",
                "avg_latency_ms": "Avg Latency (ms)",
            },
            title="Requests by Server",
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)


def render_overview(stats, server_summary, cost_breakdown, aggregator, live_logs=None, live_tokens=None):
    """Render overview dashboard."""
    st.header("📈 Workflow Overview")

    # Top-level metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total Cost",
            f"${stats['total_cost']:.4f}",
            help="Total cost for this workflow run"
        )

    with col2:
        st.metric(
            "Tool Calls",
            stats['total_tool_calls'],
            help="Total number of MCP tool invocations"
        )

    with col3:
        st.metric(
            "Servers Used",
            stats['servers_used'],
            help="Number of unique MCP servers called"
        )

    with col4:
        st.metric(
            "Duration",
            f"{stats['total_duration_seconds']}s",
            help="Total workflow execution time"
        )

    with col5:
        st.metric(
            "Cost/Insight",
            f"${stats['cost_per_insight']:.4f}",
            help="Average cost per analytical insight"
        )

    st.markdown("---")

    # Workflow metadata
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Workflow Details")
        st.write(f"**Name:** {stats['workflow_name']}")
        st.write(f"**Patient:** {stats['patient_id']}")
        st.write(f"**Date:** {stats['analysis_date']}")
        st.write(f"**Model:** {cost_breakdown['model']}")

    with col2:
        st.subheader("🎯 Results Summary")
        st.write(f"**Successful Calls:** {stats['successful_calls']}")
        st.write(f"**Dry Run Calls:** {stats['dry_run_calls']}")
        st.write(f"**Insights Generated:** {stats['insights_count']}")
        st.write(f"**Total Tokens:** {stats['total_tokens']:,}")

    st.markdown("---")

    # Server cost breakdown (horizontal bar chart)
    st.subheader("💰 Cost by Server")

    fig_server_cost = px.bar(
        server_summary.sort_values('total_cost', ascending=True),
        y='server',
        x='total_cost',
        orientation='h',
        color='status',
        color_discrete_map={
            'production': '#00cc00',
            'partial_production': '#ffa500',
            'mocked': '#ff4b4b'
        },
        labels={'total_cost': 'Total Cost ($)', 'server': 'MCP Server'},
        title="Cost Distribution Across MCP Servers"
    )
    fig_server_cost.update_layout(height=400)
    st.plotly_chart(fig_server_cost, use_container_width=True)

    # Token usage breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Token Distribution")

        # Create pie chart for input vs output tokens
        token_pie_data = pd.DataFrame({
            'Type': ['Input Tokens', 'Output Tokens'],
            'Tokens': [cost_breakdown['total_input_tokens'], cost_breakdown['total_output_tokens']]
        })

        fig_tokens = px.pie(
            token_pie_data,
            values='Tokens',
            names='Type',
            color_discrete_sequence=['#636EFA', '#EF553B'],
            title=f"Total: {cost_breakdown['total_tokens']:,} tokens"
        )
        st.plotly_chart(fig_tokens, use_container_width=True)

    with col2:
        st.subheader("💵 Cost Breakdown")

        # Create pie chart for input vs output cost
        cost_pie_data = pd.DataFrame({
            'Type': ['Input Cost', 'Output Cost'],
            'Cost': [cost_breakdown['input_cost'], cost_breakdown['output_cost']]
        })

        fig_cost = px.pie(
            cost_pie_data,
            values='Cost',
            names='Type',
            color_discrete_sequence=['#00CC96', '#AB63FA'],
            title=f"Total: ${cost_breakdown['total_cost']:.4f}"
        )
        st.plotly_chart(fig_cost, use_container_width=True)

    # ── Live traffic (when Live Mode is active) ──────────────────────────
    if live_logs:
        st.markdown("---")
        st.subheader("🌐 Live Traffic")
        render_live_traffic(live_logs)

    # ── Live token usage & costs (when Live Mode is active) ─────────────
    if live_tokens:
        st.markdown("---")
        st.subheader("💸 Live Token Usage & Costs")
        render_live_token_usage(live_tokens)


def render_cost_analysis(cost_breakdown, server_summary, aggregator, live_tokens=None):
    """Render detailed cost analysis."""
    st.header("💰 Cost Analysis")

    # Cost summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Cost", f"${cost_breakdown['total_cost']:.4f}")
        st.caption(f"Input: ${cost_breakdown['input_cost']:.4f} | Output: ${cost_breakdown['output_cost']:.4f}")

    with col2:
        st.metric("Cost per Tool Call", f"${cost_breakdown['cost_per_tool_call']:.4f}")
        st.caption(f"Based on {len(aggregator.get_tool_calls())} tool calls")

    with col3:
        st.metric("Cost per Insight", f"${cost_breakdown['cost_per_insight']:.4f}")
        st.caption(f"Based on {cost_breakdown['insights_count']} insights")

    st.markdown("---")

    # Top expensive tools
    st.subheader("🔥 Most Expensive Tool Calls")
    top_tools = aggregator.get_top_cost_tools(10)

    # Format for display
    display_tools = top_tools.copy()
    display_tools['tool_name'] = display_tools['server'] + '.' + display_tools['tool']
    display_tools['cost'] = display_tools['cost'].apply(lambda x: f"${x:.4f}")
    display_tools['input_tokens'] = display_tools['input_tokens'].apply(lambda x: f"{x:,}")
    display_tools['output_tokens'] = display_tools['output_tokens'].apply(lambda x: f"{x:,}")
    display_tools['latency_ms'] = display_tools['latency_ms'].apply(lambda x: f"{x:,}ms")

    st.dataframe(
        display_tools[['tool_name', 'input_tokens', 'output_tokens', 'cost', 'latency_ms']],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # Per-server cost details
    st.subheader("📊 Per-Server Cost Breakdown")

    # Create detailed table
    server_display = server_summary.copy()
    server_display['total_cost'] = server_display['total_cost'].apply(lambda x: f"${x:.4f}")
    server_display['input_tokens'] = server_display['input_tokens'].apply(lambda x: f"{x:,}")
    server_display['output_tokens'] = server_display['output_tokens'].apply(lambda x: f"{x:,}")
    server_display['avg_latency_ms'] = server_display['avg_latency_ms'].apply(lambda x: f"{x:.0f}ms")

    st.dataframe(
        server_display[[
            'server', 'tool_calls', 'input_tokens', 'output_tokens',
            'total_cost', 'avg_latency_ms', 'status'
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # Model comparison
    st.subheader("🔄 Model Cost Comparison")
    st.markdown("Compare costs if this workflow used different Claude models:")

    total_in = cost_breakdown['total_input_tokens']
    total_out = cost_breakdown['total_output_tokens']
    comparison = compare_model_costs(total_in, total_out)

    comparison_df = pd.DataFrame([
        {
            'Model': name,
            'Input Cost': f"${data['input_cost']:.4f}",
            'Output Cost': f"${data['output_cost']:.4f}",
            'Total Cost': f"${data['total_cost']:.4f}",
            'vs Current': f"{(data['total_cost'] / cost_breakdown['total_cost'] - 1) * 100:+.1f}%"
        }
        for name, data in comparison.items()
    ])

    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    # Highlight current model
    current_model = cost_breakdown['model']
    st.info(f"✅ Current model: **{current_model}** (${cost_breakdown['total_cost']:.4f})")

    # ── Live token costs (when available) ────────────────────────────────
    if live_tokens and live_tokens.get("query_count", 0) > 0:
        st.markdown("---")
        st.subheader("📡 Live Token Costs (Last 24h)")
        render_live_token_usage(live_tokens)

    st.markdown("---")

    # Monthly projection
    st.subheader("📅 Monthly Cost Projection")

    col1, col2 = st.columns(2)

    with col1:
        workflows_per_day = st.number_input(
            "Workflows per day",
            min_value=1,
            max_value=1000,
            value=10,
            help="Estimated number of patient analyses per day"
        )

    with col2:
        days_per_month = st.number_input(
            "Days per month",
            min_value=1,
            max_value=31,
            value=22,
            help="Working days per month"
        )

    # Calculate projections
    daily_cost = cost_breakdown['total_cost'] * workflows_per_day
    monthly_cost = daily_cost * days_per_month
    annual_cost = monthly_cost * 12

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Daily Cost", f"${daily_cost:.2f}")
    with col2:
        st.metric("Monthly Cost", f"${monthly_cost:.2f}")
    with col3:
        st.metric("Annual Cost", f"${annual_cost:,.2f}")


def render_performance_analysis(server_summary, tool_calls, aggregator, live_logs=None):
    """Render performance analysis."""
    st.header("⚡ Performance Analysis")

    # Latency metrics
    col1, col2, col3 = st.columns(3)

    avg_latency = tool_calls['latency_ms'].mean()
    max_latency = tool_calls['latency_ms'].max()
    total_latency = tool_calls['latency_ms'].sum()

    with col1:
        st.metric("Avg Latency", f"{avg_latency:.0f}ms")
    with col2:
        st.metric("Max Latency", f"{max_latency:.0f}ms")
    with col3:
        st.metric("Total Time", f"{total_latency/1000:.1f}s")

    st.markdown("---")

    # Latency by server
    st.subheader("📊 Latency by Server")

    fig_latency = px.bar(
        server_summary.sort_values('avg_latency_ms', ascending=False),
        x='server',
        y='avg_latency_ms',
        color='avg_latency_ms',
        color_continuous_scale='reds',
        labels={'avg_latency_ms': 'Avg Latency (ms)', 'server': 'MCP Server'},
        title="Average Latency per Server"
    )
    fig_latency.update_layout(height=400)
    st.plotly_chart(fig_latency, use_container_width=True)

    st.markdown("---")

    # Tool call timeline
    st.subheader("⏱️ Execution Timeline")

    timeline = aggregator.get_timeline_data()
    if not timeline.empty:
        # Create dual-axis chart: cumulative cost and tokens over time
        fig_timeline = go.Figure()

        # Add cumulative cost trace
        fig_timeline.add_trace(go.Scatter(
            x=timeline['timestamp'],
            y=timeline['cumulative_cost'],
            name='Cumulative Cost ($)',
            line=dict(color='#00CC96', width=3),
            yaxis='y1'
        ))

        # Add cumulative tokens trace
        fig_timeline.add_trace(go.Scatter(
            x=timeline['timestamp'],
            y=timeline['cumulative_tokens'],
            name='Cumulative Tokens',
            line=dict(color='#636EFA', width=3, dash='dash'),
            yaxis='y2'
        ))

        # Update layout with dual y-axes
        fig_timeline.update_layout(
            title="Cost and Token Accumulation Over Time",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Cumulative Cost ($)", side='left'),
            yaxis2=dict(title="Cumulative Tokens", side='right', overlaying='y'),
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("Timeline data not available (requires timestamp data)")

    st.markdown("---")

    # Token efficiency
    st.subheader("🎯 Token Efficiency")

    # Calculate tokens per millisecond for each server
    efficiency = server_summary.copy()
    efficiency['tokens_per_second'] = (
        (efficiency['input_tokens'] + efficiency['output_tokens']) /
        (efficiency['total_latency_ms'] / 1000)
    ).round(0).astype(int)

    fig_efficiency = px.bar(
        efficiency.sort_values('tokens_per_second', ascending=False),
        x='server',
        y='tokens_per_second',
        color='tokens_per_second',
        color_continuous_scale='greens',
        labels={'tokens_per_second': 'Tokens/Second', 'server': 'MCP Server'},
        title="Processing Speed (Higher is Better)"
    )
    fig_efficiency.update_layout(height=400)
    st.plotly_chart(fig_efficiency, use_container_width=True)

    # ── Live latency from Cloud Logging (real data overlay) ───────────────
    if live_logs:
        active = [v for v in live_logs.values() if v["request_count"] > 0]
        if active:
            live_df = pd.DataFrame(active)
            total_reqs = sum(r["request_count"] for r in active)
            window = active[0]["time_window_hours"]

            st.markdown("---")
            st.subheader("📡 Live Latency (Cloud Logging)")
            st.caption(f"Window: last {window}h  |  {total_reqs} requests observed")

            fig_live = px.bar(
                live_df.sort_values("avg_latency_ms", ascending=False),
                x="server",
                y=["avg_latency_ms", "p95_latency_ms"],
                barmode="group",
                labels={
                    "avg_latency_ms": "Avg (ms)",
                    "p95_latency_ms": "P95 (ms)",
                    "server":         "Server",
                },
                title="Live Latency: Avg vs P95",
            )
            fig_live.update_layout(height=400)
            st.plotly_chart(fig_live, use_container_width=True)
        else:
            st.markdown("---")
            st.info("No requests in the selected time window for latency comparison.")


def render_optimization_view(aggregator, server_summary, cost_breakdown, live_logs=None, live_tokens=None):
    """Render optimization recommendations."""
    st.header("🔧 Cost Optimization")

    # Get recommendations
    recommendations = aggregator.get_optimization_recommendations()

    st.subheader("💡 Recommendations")
    for rec in recommendations:
        # Determine icon based on content
        if "⚠️" in rec:
            st.warning(rec)
        elif "💡" in rec:
            st.info(rec)
        elif "📝" in rec:
            st.info(rec)
        else:
            st.success(rec)

    st.markdown("---")

    # Savings opportunities
    st.subheader("💰 Potential Savings")

    # Calculate savings from switching low-usage servers to Haiku
    low_usage_servers = server_summary[
        (server_summary['avg_output_tokens'] < 1000) &
        (server_summary['total_cost'] < 0.10)
    ]

    if not low_usage_servers.empty:
        # Calculate savings (Haiku is ~92% cheaper than Sonnet)
        potential_savings = low_usage_servers['total_cost'].sum() * 0.92

        st.metric(
            "Potential Monthly Savings (10 workflows/day)",
            f"${potential_savings * 10 * 22:.2f}",
            help="By switching low-usage servers to Haiku model"
        )

        st.markdown("**Candidate servers for Haiku:**")
        for _, row in low_usage_servers.iterrows():
            st.write(f"- `{row['server']}` (current cost: ${row['total_cost']:.4f}, potential savings: ${row['total_cost'] * 0.92:.4f} per run)")
    else:
        st.success("✅ All servers are using appropriate models for their workload.")

    st.markdown("---")

    # Cost reduction strategies
    st.subheader("📋 Cost Reduction Strategies")

    strategies = [
        {
            "strategy": "Cache Frequent Queries",
            "target": "mcp-multiomics (HAllA results)",
            "potential_saving": "30-50%",
            "complexity": "Medium"
        },
        {
            "strategy": "Batch Visualization Generation",
            "target": "mcp-spatialtools",
            "potential_saving": "15-20%",
            "complexity": "Low"
        },
        {
            "strategy": "Use Haiku for Simple Lookups",
            "target": "mcp-fgbio, mcp-mocktcga",
            "potential_saving": "90%+",
            "complexity": "Low"
        },
        {
            "strategy": "Implement Response Streaming",
            "target": "All servers",
            "potential_saving": "10-15%",
            "complexity": "High"
        },
    ]

    strategies_df = pd.DataFrame(strategies)
    st.dataframe(strategies_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Export options
    st.subheader("📤 Export Report")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Generate Text Report"):
            output_path = "cost_report.txt"
            aggregator.export_summary_report(output_path)
            st.success(f"✅ Report saved to {output_path}")

            # Show download button
            with open(output_path, 'r') as f:
                report_content = f.read()

            st.download_button(
                label="⬇️ Download Report",
                data=report_content,
                file_name="mcp_cost_report.txt",
                mime="text/plain"
            )

    with col2:
        if st.button("📊 Export to CSV"):
            server_summary_export = aggregator.get_server_summary()
            csv_data = server_summary_export.to_csv(index=False)

            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name="mcp_server_metrics.csv",
                mime="text/csv"
            )

    # ── Live error signals ─────────────────────────────────────────────────
    if live_logs:
        errored = {k: v for k, v in live_logs.items() if v["error_count"] > 0}
        st.markdown("---")
        st.subheader("⚠️ Live Error Signals")
        if errored:
            for name, info in sorted(errored.items()):
                st.warning(
                    f"`{name}` — {info['error_count']} errors / "
                    f"{info['request_count']} requests "
                    f"(error rate {info['error_rate'] * 100:.1f}%)"
                )
        else:
            st.success("No errors detected on any server in the selected time window.")

    # ── Live token cost insights ─────────────────────────────────────────
    if live_tokens and live_tokens.get("query_count", 0) > 0:
        st.markdown("---")
        st.subheader("📊 Live Token Cost Insights")

        by_server = live_tokens.get("by_server", {})
        if by_server:
            # Find high-cost servers
            high_cost_servers = [
                (name, data) for name, data in by_server.items()
                if data.get("total_cost_usd", 0) > 0.50
            ]

            if high_cost_servers:
                st.warning("**High-cost servers detected (>$0.50 in last 24h):**")
                for name, data in sorted(high_cost_servers, key=lambda x: x[1]["total_cost_usd"], reverse=True):
                    cost = data["total_cost_usd"]
                    queries = data["query_count"]
                    st.write(f"- `{name}`: ${cost:.2f} ({queries} queries, ${cost/queries:.4f}/query)")
            else:
                st.success("✅ All servers are within normal cost ranges.")

            # Show total live costs
            total = live_tokens["total_cost_usd"]
            queries = live_tokens["query_count"]
            st.info(
                f"**Total live usage (24h):** ${total:.2f} across {queries} queries "
                f"(avg ${live_tokens['avg_cost_per_query']:.4f}/query)"
            )


if __name__ == "__main__":
    main()
