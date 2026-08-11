"""Shared test configuration for mcp-deidentify.

DEIDENTIFY_DRY_RUN now defaults to "false", so tests that want fixture mode must
say so. Setting the env var at module import is not enough on its own: pytest
imports every test module during collection, before any test runs, so the last
module imported would decide the config for all of them.

This fixture makes the default explicit and re-reads config before each test, so
test order cannot change behaviour. Tests that need production mode (see
test_dry_run_safety.py) call config.reload() themselves inside the test body,
which runs after this fixture.
"""

import pytest


@pytest.fixture(autouse=True)
def _dry_run_by_default(monkeypatch):
    from mcp_deidentify import config

    monkeypatch.setenv("DEIDENTIFY_DRY_RUN", "true")
    monkeypatch.delenv("DEIDENTIFY_DATE_POLICY", raising=False)
    config.reload()
    yield
