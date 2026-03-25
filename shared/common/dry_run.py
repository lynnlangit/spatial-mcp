"""Shared DRY_RUN warning utility for all MCP servers."""

from typing import Any


_DRY_RUN_WARNING_TEXT = "SYNTHETIC DATA - NOT FOR RESEARCH USE"

_WARNING_TEMPLATE = (
    "=== SYNTHETIC DATA WARNING ===\n"
    "This result was generated in DRY_RUN mode and does NOT represent real analysis.\n"
    "Do NOT use this data for clinical or research decisions.\n"
    "Set {env_var}=false for production use.\n"
    "==============================\n"
)


def add_dry_run_warning(result: Any, *, dry_run: bool, env_var: str = "DRY_RUN") -> Any:
    """Add warning banner to results when in DRY_RUN mode.

    Args:
        result: The tool result (dict or str).
        dry_run: Whether DRY_RUN mode is active.
        env_var: Name of the env var that controls DRY_RUN for this server
                 (e.g. "FGBIO_DRY_RUN").

    Returns:
        The result with warning metadata injected (if dry_run is True).
    """
    if not dry_run:
        return result

    warning = _WARNING_TEMPLATE.format(env_var=env_var)

    if isinstance(result, dict):
        result["_DRY_RUN_WARNING"] = _DRY_RUN_WARNING_TEXT
        result["_message"] = warning.strip()
    elif isinstance(result, str):
        result = warning + "\n" + result

    return result
