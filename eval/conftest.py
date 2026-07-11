"""Pytest configuration for eval harness."""

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: MTBBench integration tests (DRY_RUN)")
