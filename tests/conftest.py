"""Root pytest configuration for the Precision Medicine MCP Platform.

DRY_RUN=True is the default for all unit tests.  Each MCP server reads its own
environment variable (e.g. FGBIO_DRY_RUN, MULTIOMICS_DRY_RUN) and defaults to
"true" when unset.  This means:

  - Tests run without external API keys, reference genomes, or network access.
  - Tool responses use synthetic/mock data that matches the expected schema.
  - The ``dry_run`` flag in returned dicts is set to ``true`` so assertions can
    distinguish synthetic from live results.

To run tests against real data, export the relevant env var::

    MYSERVER_DRY_RUN=false uv run pytest tests/unit/mcp-myserver -v

Canonical PAT001 reference values live in ``tests/fixtures/pat001_canonical.py``
and should be imported instead of hard-coding magic numbers in assertions.
"""
