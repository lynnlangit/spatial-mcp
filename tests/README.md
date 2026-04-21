# Tests

## Running Tests

Each server has its own test suite in `servers/mcp-*/tests/`. Run with `uv`:

```bash
cd servers/mcp-spatialtools && uv run pytest -v
cd servers/mcp-multiomics && uv run pytest -v
```

All tests run in **DRY_RUN mode** by default — no API keys or external services needed.

CI runs a subset automatically on every PR: see [ci.yml](../.github/workflows/ci.yml).

## Directory Contents

- **unit/** — Older unit tests (pre-server-local layout). Canonical tests now live in each server's `tests/` directory.
- **integration/** — End-to-end and GCP Cloud Run integration tests.
- **verification/** — Server import and health-check scripts.
- **manual_testing/** — Sample outputs and FASTQ fixtures from PatientOne testing.

## Test Documentation

Test prompts, data mode guides, and patient scenarios are in [docs/reference/testing/](../docs/reference/testing/).
