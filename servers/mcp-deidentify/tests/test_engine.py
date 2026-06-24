"""Tests for Haiku-based PII extraction engine.

All tests run with DEIDENTIFY_DRY_RUN=true by default (no Haiku calls, no API key).
Tests marked @pytest.mark.live require ANTHROPIC_API_KEY and make real API calls.
"""

import os

import pytest

# Force DRY_RUN for unit tests
os.environ["DEIDENTIFY_DRY_RUN"] = "true"

from mcp_deidentify.engine import (
    SYNTHETIC_ENTITIES,
    SYNTHETIC_TEXT,
    _chunk_text,
    extract_entities,
    replace_entities,
)


@pytest.mark.asyncio
async def test_dry_run_returns_synthetic_entities():
    """DRY_RUN mode must return the synthetic fixture without calling Haiku."""
    entities = await extract_entities("any text")
    assert entities == SYNTHETIC_ENTITIES


@pytest.mark.asyncio
async def test_dry_run_entities_have_required_fields():
    """Every entity must have text, entity_type, start, end."""
    entities = await extract_entities("any text")
    for ent in entities:
        assert "text" in ent
        assert "entity_type" in ent
        assert "start" in ent
        assert "end" in ent


def test_chunk_text_short_string_no_split():
    """Strings shorter than chunk_size should not be split."""
    chunks = _chunk_text("short text", chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0]["offset"] == 0


def test_chunk_text_long_string_splits():
    """Long strings should be split into multiple overlapping chunks."""
    text = "x" * 200
    chunks = _chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    # Each chunk after the first should start before the end of the previous
    for i in range(1, len(chunks)):
        assert chunks[i]["offset"] < chunks[i - 1]["offset"] + 100


def test_chunk_text_covers_full_content():
    """All characters of the original text must appear in at least one chunk."""
    text = "abcdefghij" * 100
    chunks = _chunk_text(text, chunk_size=300, overlap=50)
    reconstructable = set()
    for chunk in chunks:
        offset = chunk["offset"]
        for i, ch in enumerate(chunk["text"]):
            reconstructable.add(offset + i)
    for i in range(len(text)):
        assert i in reconstructable


@pytest.mark.asyncio
async def test_replace_entities_dry_run():
    """replace_entities should substitute all synthetic entities in SYNTHETIC_TEXT."""
    session_key = {"entity_map": {}, "_counters": {}}
    entities = await extract_entities(SYNTHETIC_TEXT)
    result = replace_entities(SYNTHETIC_TEXT, entities, session_key, "PAT-SYNTHETIC-001")
    # None of the original entity texts should remain verbatim
    for ent in SYNTHETIC_ENTITIES:
        assert ent["text"] not in result, f"'{ent['text']}' still present after de-id"


@pytest.mark.asyncio
async def test_replace_entities_populates_session_key():
    """After replace_entities, session_key should contain all replaced entities."""
    session_key = {"entity_map": {}, "_counters": {}}
    entities = await extract_entities(SYNTHETIC_TEXT)
    replace_entities(SYNTHETIC_TEXT, entities, session_key, "PAT-SYNTHETIC-001")
    assert len(session_key["entity_map"]) > 0


# ---------------------------------------------------------------------------
# Live tests (require ANTHROPIC_API_KEY; skipped in CI)
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_haiku_returns_entities(tmp_path):
    """Live: Haiku should detect at least one entity in the synthetic note fixture."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    # Temporarily disable DRY_RUN for this test
    import mcp_deidentify.engine as eng

    orig = eng.DRY_RUN
    eng.DRY_RUN = False
    try:
        text = open("tests/fixtures/synthetic_note.txt").read()
        entities = await extract_entities(text)
        assert len(entities) > 0, "Haiku should detect at least one entity in the synthetic note"
    finally:
        eng.DRY_RUN = orig
