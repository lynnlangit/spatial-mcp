"""A failed extraction must never present as a completed de-identification.

`_call_haiku` used to return [] on every failure path: anthropic missing,
malformed JSON, any exception, retries exhausted. An empty entity list is a
*finding* -- "this text contains no PII" -- and `replace_entities` acts on it by
returning the text unchanged. So a failed Haiku call handed back the ORIGINAL
document under a key named `deidentified_text`.

That is the same silent-failure shape as the half-stubbed validator: the caller
cannot distinguish "found nothing" from "could not look". These tests pin the
replacement contract:

  - every failure path raises ExtractionFailure
  - extraction is all-or-nothing per document
  - the tool boundary converts it to status="extraction_failed" carrying NO
    de-identified content of any kind
"""

import json

import pytest

from mcp_deidentify import config, engine
from mcp_deidentify.engine import ExtractionFailure

# Text carrying obvious identifiers. If any test finds this verbatim in a tool
# result, the tool leaked the source under a name implying it was redacted.
PHI = "Patient Marion T. Halloway, MRN 40881236, seen by Dr. Priya Raghunathan."


@pytest.fixture(autouse=True)
def _live_mode(monkeypatch):
    """These tests are about the live path; DRY_RUN short-circuits before Haiku."""
    monkeypatch.delenv("DEIDENTIFY_DRY_RUN", raising=False)
    config.reload()
    assert config.DRY_RUN is False
    yield
    config.reload()


async def _boom(*_a, **_k):
    """Async on purpose.

    A synchronous raiser would fire while `extract_entities` is *building* its
    task list, short-circuiting before `asyncio.gather` is ever called -- so a
    test using one would pass even if gather were changed to swallow failures.
    """
    raise ExtractionFailure("simulated extraction failure")


# ---------------------------------------------------------------------------
# The engine contract
# ---------------------------------------------------------------------------


class TestCallHaikuRaises:
    """Each failure path raises rather than returning an empty list."""

    def _fake_anthropic(self, monkeypatch, *, raises=None, returns=None):
        """Install a stand-in `anthropic` module.

        Behaviour lives in a mutable dict so a test can install the module once
        and then reference `mod.RateLimitError` when choosing what to raise --
        building the module twice would create two distinct exception classes,
        and `_call_haiku` would not catch the one it was not compiled against.
        """
        import sys
        import types

        mod = types.ModuleType("anthropic")
        behaviour = {"raises": raises, "returns": returns}

        class RateLimitError(Exception):
            pass

        class _Messages:
            def create(self, **_kw):
                if behaviour["raises"] is not None:
                    raise behaviour["raises"]
                return types.SimpleNamespace(
                    content=[types.SimpleNamespace(text=behaviour["returns"])]
                )

        class Anthropic:
            def __init__(self, *_a, **_k):
                self.messages = _Messages()

        mod.RateLimitError = RateLimitError
        mod.Anthropic = Anthropic
        mod.behaviour = behaviour
        monkeypatch.setitem(sys.modules, "anthropic", mod)
        return mod

    @pytest.mark.asyncio
    async def test_malformed_json_raises(self, monkeypatch):
        """Previously logged 'Skipping chunk', silently dropping that chunk's PII."""
        self._fake_anthropic(monkeypatch, returns="this is not json")
        with pytest.raises(ExtractionFailure, match="malformed JSON"):
            await engine._call_haiku("prompt", PHI)

    @pytest.mark.asyncio
    async def test_api_error_raises(self, monkeypatch):
        self._fake_anthropic(monkeypatch, raises=RuntimeError("connection reset"))
        with pytest.raises(ExtractionFailure, match="connection reset"):
            await engine._call_haiku("prompt", PHI)

    @pytest.mark.asyncio
    async def test_retries_exhausted_raises(self, monkeypatch):
        """Rate limits retry, but exhausting them is a failure, not an empty result."""
        mod = self._fake_anthropic(monkeypatch)
        mod.behaviour["raises"] = mod.RateLimitError()
        monkeypatch.setattr(engine.asyncio, "sleep", lambda _s: _noop())
        with pytest.raises(ExtractionFailure, match="after .* attempts"):
            await engine._call_haiku("prompt", PHI)

    @pytest.mark.asyncio
    async def test_success_still_returns_entities(self, monkeypatch):
        """The happy path is unchanged: a parsed entity list comes back."""
        payload = json.dumps(
            {"entities": [{"text": "Marion", "entity_type": "PERSON_NAME_PATIENT"}]}
        )
        self._fake_anthropic(monkeypatch, returns=payload)
        out = await engine._call_haiku("prompt", PHI)
        assert out == [{"text": "Marion", "entity_type": "PERSON_NAME_PATIENT"}]

    @pytest.mark.asyncio
    async def test_empty_entity_list_is_still_a_valid_finding(self, monkeypatch):
        """'No PII here' must remain expressible -- it is not an error."""
        self._fake_anthropic(monkeypatch, returns=json.dumps({"entities": []}))
        assert await engine._call_haiku("prompt", "the sky is blue") == []


async def _noop():
    return None


class TestExtractEntitiesIsAllOrNothing:
    @pytest.mark.asyncio
    async def test_one_failed_chunk_fails_the_document(self, monkeypatch):
        """A partial result would redact some chunks and leave others intact.

        Uses a multi-chunk document with only the LAST chunk failing, so the
        successful chunks really are discarded rather than never attempted.
        """
        calls = {"n": 0}

        async def _fail_on_last(_prompt, _chunk):
            calls["n"] += 1
            if calls["n"] >= 3:
                raise ExtractionFailure("chunk 3 failed")
            return [{"text": "Marion", "entity_type": "PERSON_NAME_PATIENT"}]

        monkeypatch.setattr(engine, "_call_haiku", _fail_on_last)
        long_doc = (PHI + " ") * 2000  # forces several chunks
        assert len(engine._chunk_text(long_doc)) >= 3
        with pytest.raises(ExtractionFailure):
            await engine.extract_entities(long_doc)

    @pytest.mark.asyncio
    async def test_single_failed_chunk_propagates(self, monkeypatch):
        monkeypatch.setattr(engine, "_call_haiku", _boom)
        with pytest.raises(ExtractionFailure):
            await engine.extract_entities(PHI)

    @pytest.mark.asyncio
    async def test_dry_run_still_short_circuits(self, monkeypatch):
        monkeypatch.setenv("DEIDENTIFY_DRY_RUN", "true")
        config.reload()
        monkeypatch.setattr(engine, "_call_haiku", _boom)
        assert await engine.extract_entities(PHI) == engine.SYNTHETIC_ENTITIES


# ---------------------------------------------------------------------------
# The tool boundary -- no content may escape
# ---------------------------------------------------------------------------


CONTENT_KEYS = ("deidentified", "deidentified_text", "deidentified_content", "extracted_text")


def _assert_safe_failure(result, patient_id="PATTEST"):
    """Shared contract for every tool's extraction-failure envelope."""
    assert result["status"] == "extraction_failed"
    assert result["patient_id"] == patient_id
    assert "_SAFETY_NOTE" in result
    for key in CONTENT_KEYS:
        assert key not in result, f"{key} must be absent on failure, got {result.get(key)!r}"
    # The source text must not appear anywhere in the payload, under any key.
    assert PHI not in json.dumps(result, default=str)


class TestToolBoundary:
    @pytest.mark.asyncio
    async def test_deidentify_json(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DEIDENTIFY_KEY_DIR", str(tmp_path))
        config.reload()
        import mcp_deidentify.format_handlers.json_handler as jh

        monkeypatch.setattr(jh, "extract_entities", _boom)
        from mcp_deidentify.server import deidentify_json

        result = await deidentify_json(json_content=json.dumps({"note": PHI}), patient_id="PATTEST")
        _assert_safe_failure(result)

    @pytest.mark.asyncio
    async def test_deidentify_text(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DEIDENTIFY_KEY_DIR", str(tmp_path))
        config.reload()
        import mcp_deidentify.format_handlers.text_handler as th

        monkeypatch.setattr(th, "extract_entities", _boom)
        from mcp_deidentify.server import deidentify_text

        result = await deidentify_text(text=PHI, patient_id="PATTEST")
        _assert_safe_failure(result)
        assert result["source_format"] == "txt"

    @pytest.mark.asyncio
    async def test_deidentify_pdf_text(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DEIDENTIFY_KEY_DIR", str(tmp_path))
        config.reload()
        pdf = tmp_path / "note.pdf"
        _write_text_pdf(pdf, [PHI])

        import mcp_deidentify.format_handlers.pdf_handler as ph

        monkeypatch.setattr(ph, "extract_entities", _boom)
        from mcp_deidentify.server import deidentify_pdf_text

        result = await deidentify_pdf_text(pdf_path=str(pdf), patient_id="PATTEST")
        _assert_safe_failure(result)

    @pytest.mark.asyncio
    async def test_deidentify_genomics_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DEIDENTIFY_KEY_DIR", str(tmp_path))
        config.reload()
        vcf = tmp_path / "s.vcf"
        vcf.write_text(f"##fileDate=20260101\n##SAMPLE={PHI}\n#CHROM\tPOS\n")

        import mcp_deidentify.format_handlers.genomics_handler as gh

        monkeypatch.setattr(gh, "extract_entities", _boom)
        from mcp_deidentify.server import deidentify_genomics_file

        result = await deidentify_genomics_file(
            file_path=str(vcf), patient_id="PATTEST", file_type="vcf"
        )
        _assert_safe_failure(result)
        assert result["file_type"] == "vcf"


class TestValidatorReachesIncomplete:
    @pytest.mark.asyncio
    async def test_extraction_failure_degrades_to_incomplete(self, monkeypatch):
        """The validator's 'incomplete' branch is now actually reachable in live mode."""
        monkeypatch.setattr(engine, "extract_entities", _boom)
        from mcp_deidentify.validator import validate

        result = await validate("Some de-identified text.", {})
        assert result["status"] == "incomplete"
        assert result["passed"] is None
        assert "haiku_red_team" in result["layers_skipped"]


# ---------------------------------------------------------------------------


def _write_text_pdf(path, lines):
    """Minimal single-page PDF with a real text layer (no external deps)."""
    import io as _io

    ops = "BT /F1 12 Tf 72 720 Td 14 TL\n" + "".join(f"({ln}) Tj T*\n" for ln in lines) + "ET\n"
    content = ops.encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = _io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % i + obj + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    for off in offsets:
        out.write(b"%010d 00000 n \n" % off)
    out.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    )
    path.write_bytes(out.getvalue())
