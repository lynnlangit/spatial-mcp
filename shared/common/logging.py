"""Logging configuration for MCP servers."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[Path] = None,
    server_name: str = "mcp-server"
) -> logging.Logger:
    """Set up logging configuration for an MCP server.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom format string for log messages
        log_file: Optional path to log file (logs to stderr if not provided)
        server_name: Name of the MCP server (used as logger name)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(level="DEBUG", server_name="mcp-fgbio")
        >>> logger.info("Server starting")
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logger = logging.getLogger(server_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    logger.debug(f"Logging initialized for {server_name} at {level} level")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing data")
    """
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logging wrapper for JSON-formatted logs.

    This class provides a wrapper around the standard Python logger
    to emit structured (JSON) log messages for better observability
    in production environments.
    """

    def __init__(self, logger: logging.Logger):
        """Initialize structured logger.

        Args:
            logger: Underlying Python logger instance
        """
        self.logger = logger

    def log_tool_call(
        self,
        tool_name: str,
        request_id: str,
        params: dict,
        level: str = "INFO"
    ) -> None:
        """Log an MCP tool invocation.

        Args:
            tool_name: Name of the tool being called
            request_id: Unique request identifier
            params: Tool parameters
            level: Log level
        """
        import json

        log_data = {
            "event": "tool_call",
            "tool": tool_name,
            "request_id": request_id,
            "params": params,
        }
        self.logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_data)
        )

    def log_tool_result(
        self,
        tool_name: str,
        request_id: str,
        duration_seconds: float,
        success: bool,
        level: str = "INFO"
    ) -> None:
        """Log an MCP tool result.

        Args:
            tool_name: Name of the tool
            request_id: Unique request identifier
            duration_seconds: Execution time in seconds
            success: Whether the tool succeeded
            level: Log level
        """
        import json

        log_data = {
            "event": "tool_result",
            "tool": tool_name,
            "request_id": request_id,
            "duration_seconds": duration_seconds,
            "success": success,
        }
        self.logger.log(
            getattr(logging, level.upper()),
            json.dumps(log_data)
        )
