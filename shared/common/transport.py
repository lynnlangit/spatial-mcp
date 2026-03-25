"""Shared MCP server transport/entrypoint boilerplate."""

import logging
import os


logger = logging.getLogger(__name__)


def run_server(
    mcp,
    *,
    server_name: str,
    dry_run: bool = True,
    env_var: str = "DRY_RUN",
    default_port: int = 8000,
) -> None:
    """Standard entrypoint for an MCP server with transport detection.

    Handles stdio vs SSE/streamable-http transport selection from environment
    variables, and logs the DRY_RUN status on startup.

    Args:
        mcp: The FastMCP server instance.
        server_name: Human-readable server name for log messages.
        dry_run: Whether DRY_RUN mode is active.
        env_var: The env var name that controls DRY_RUN (for log messages).
        default_port: Default port for SSE/HTTP transport.
    """
    logger.info("Starting %s server...", server_name)

    if dry_run:
        logger.warning("=" * 80)
        logger.warning("DRY_RUN MODE ENABLED - RETURNING SYNTHETIC DATA")
        logger.warning("Results are MOCKED and do NOT represent real analysis")
        logger.warning("Set %s=false for production use", env_var)
        logger.warning("=" * 80)
    else:
        logger.info("Real data processing mode enabled (%s=false)", env_var)

    transport = os.getenv("MCP_TRANSPORT", "stdio")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", str(default_port))))

    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport, port=port, host="0.0.0.0")
    else:
        mcp.run(transport=transport)
