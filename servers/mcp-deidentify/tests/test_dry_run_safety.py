"""Regression tests for the DRY_RUN safety defects found on 2026-08-11.

Three defects motivated these tests:

1. DEIDENTIFY_DRY_RUN defaulted to "true" with no config anywhere setting it
   otherwise, so the server always returned fabricated data.
2. validate_deidentification stubbed only its Haiku layer, letting text full of
   names return passed=True at confidence 1.0.
3. deidentify_pdf returned a fixture unrelated to the input file -- the fixture
   even reported a different page count than the PDF it was handed.

Each test below fails against the pre-fix code.
"""

import io
import pathlib

import pytest

# NB: deliberately do NOT set DEIDENTIFY_DRY_RUN at import. These tests control
# it explicitly per-case, because the whole point is the *default*.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reload_config(monkeypatch, dry_run=None, date_policy=None):
    """Set env and re-read config, restoring afterwards via monkeypatch."""
    from mcp_deidentify import config

    if dry_run is None:
        monkeypatch.delenv("DEIDENTIFY_DRY_RUN", raising=False)
    else:
        monkeypatch.setenv("DEIDENTIFY_DRY_RUN", dry_run)
    if date_policy is not None:
        monkeypatch.setenv("DEIDENTIFY_DATE_POLICY", date_policy)
    config.reload()
    return config


@pytest.fixture(autouse=True)
def _restore_config():
    """Restore process-wide config after each test so module order can't matter."""
    from mcp_deidentify import config

    saved = (config.DRY_RUN, config.DATE_POLICY, config.KEY_DIR)
    yield
    config.DRY_RUN, config.DATE_POLICY, config.KEY_DIR = saved


def _make_text_pdf(path: pathlib.Path, lines) -> None:
    """Write a minimal single-page PDF with a real text layer (no deps)."""
    text_ops = "BT /F1 12 Tf 72 720 Td 14 TL\n"
    for line in lines:
        text_ops += f"({line}) Tj T*\n"
    text_ops += "ET\n"
    content = text_ops.encode("latin-1")

    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
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


def _make_image_only_pdf(path: pathlib.Path, pages: int = 2) -> None:
    """Write a PDF with drawing operators but no text layer (mimics a scan)."""
    content = b"0 0 0 rg 100 600 300 100 re f\n"
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(pages))
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [" + kids.encode() + b"] /Count %d >>" % pages,
    ]
    for i in range(pages):
        objs.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents %d 0 R >>"
            % (4 + 2 * i)
        )
        objs.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream")
    out = io.BytesIO()
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


# ---------------------------------------------------------------------------
# Tier 3 #9 -- no tool may report dry_run under the production config
# ---------------------------------------------------------------------------


def test_dry_run_defaults_to_false_when_unset(monkeypatch):
    """The production default must be live mode, not fixtures.

    This is the original defect: os.getenv(..., "true") in seven modules, with
    nothing in the repo ever setting the variable to false.
    """
    config = _reload_config(monkeypatch, dry_run=None)
    assert config.DRY_RUN is False


@pytest.mark.asyncio
async def test_no_tool_reports_dry_run_under_production_config(monkeypatch, tmp_path):
    """With DEIDENTIFY_DRY_RUN unset, no tool may return dry_run=True."""
    monkeypatch.setenv("DEIDENTIFY_KEY_DIR", str(tmp_path))
    config = _reload_config(monkeypatch, dry_run=None)
    assert config.DRY_RUN is False

    from mcp_deidentify.server import generate_anonymization_key

    result = await generate_anonymization_key(patient_id="PATTEST")
    assert result["dry_run"] is False
    assert result.get("status") != "SYNTHETIC_DRY_RUN"
    assert "_DRY_RUN_WARNING" not in result


@pytest.mark.asyncio
async def test_dry_run_payload_is_impossible_to_miss(monkeypatch):
    """In DRY_RUN every string is prefixed and status flags the payload."""
    config = _reload_config(monkeypatch, dry_run="true")
    assert config.DRY_RUN is True

    from mcp_deidentify.server import generate_anonymization_key

    result = await generate_anonymization_key(patient_id="PATTEST")
    assert result["status"] == "SYNTHETIC_DRY_RUN"
    assert result["dry_run"] is True
    # Server-generated values are prefixed...
    assert result["key_path"].startswith("SYNTHETIC:")
    # ...but caller-supplied echo fields are left intact, so downstream dispatch
    # on file_type / patient_id keeps working.
    assert result["patient_id"] == "PATTEST"


# ---------------------------------------------------------------------------
# Tier 3 #10 -- never a passing verdict when a layer was skipped
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_never_passes_when_a_layer_is_skipped(monkeypatch):
    """The core defect: PII-laden text scored passed=True at confidence 1.0.

    Names, a physician, a facility and a city trip none of the regex patterns and
    are absent from an empty key, so layers 2 and 3 pass. Before the fix the
    stubbed Haiku layer supplied the third pass.
    """
    _reload_config(monkeypatch, dry_run="true")
    from mcp_deidentify.validator import validate

    pii = (
        "Patient Jane Marie Smith was seen by Dr. Robert Chen at Mercy General "
        "Hospital in Springfield. Her mother is Susan Smith."
    )
    result = await validate(pii, {})

    assert result["passed"] is not True
    assert result["passed"] is None
    assert result["confidence"] is None
    assert result["status"] == "unavailable_in_dry_run"
    assert "haiku_red_team" in result["layers_skipped"]
    assert "_VALIDATION_WARNING" in result


@pytest.mark.asyncio
async def test_validate_reports_skipped_layer_status(monkeypatch):
    """Every layer carries an explicit ran/skipped status."""
    _reload_config(monkeypatch, dry_run="true")
    from mcp_deidentify.validator import validate

    result = await validate("Nothing identifying here.", {})
    assert result["layers"]["haiku_red_team"]["status"] == "skipped_dry_run"
    assert result["layers"]["haiku_red_team"]["passed"] is None
    assert result["layers"]["regex_sweep"]["status"] == "ran"
    assert result["layers"]["key_reverse_lookup"]["status"] == "ran"


@pytest.mark.asyncio
async def test_validate_haiku_failure_does_not_yield_a_verdict(monkeypatch):
    """A failed Haiku call must degrade to 'incomplete', not to a pass."""
    _reload_config(monkeypatch, dry_run=None)  # live mode

    import mcp_deidentify.engine as engine

    async def _boom(*a, **k):
        raise RuntimeError("simulated API outage")

    monkeypatch.setattr(engine, "extract_entities", _boom)

    from mcp_deidentify.validator import validate

    result = await validate("Perfectly clean text.", {})
    assert result["passed"] is None
    assert result["status"] == "incomplete"
    assert "haiku_red_team" in result["layers_skipped"]


# ---------------------------------------------------------------------------
# Tier 2 #8 -- date policy applied consistently
# ---------------------------------------------------------------------------


def test_safe_harbor_flags_dates(monkeypatch):
    _reload_config(monkeypatch, dry_run="true", date_policy="SAFE_HARBOR")
    from mcp_deidentify.validator import _run_regex_layer

    passed, hits = _run_regex_layer("Collected 7/21/2026 and 1980-01-01.")
    assert passed is False
    assert {h["pattern"] for h in hits} >= {"DATE_SLASHED", "DATE_ISO"}


def test_limited_data_set_permits_dates(monkeypatch):
    """Under LDS the validator must not contradict the de-identifier."""
    _reload_config(monkeypatch, dry_run="true", date_policy="LIMITED_DATA_SET")
    from mcp_deidentify.validator import _run_regex_layer

    passed, hits = _run_regex_layer("Collected 7/21/2026 and 1980-01-01.")
    assert passed is True
    assert hits == []


def test_limited_data_set_still_flags_real_pii(monkeypatch):
    """Relaxing dates must not relax anything else."""
    _reload_config(monkeypatch, dry_run="true", date_policy="LIMITED_DATA_SET")
    from mcp_deidentify.validator import _run_regex_layer

    passed, hits = _run_regex_layer("SSN 123-45-6789 on 7/21/2026")
    assert passed is False
    assert {h["pattern"] for h in hits} == {"SSN"}


def test_invalid_date_policy_is_rejected(monkeypatch):
    from mcp_deidentify import config

    monkeypatch.setenv("DEIDENTIFY_DATE_POLICY", "WHATEVER")
    with pytest.raises(ValueError, match="not a valid policy"):
        config.reload()
    monkeypatch.delenv("DEIDENTIFY_DATE_POLICY")
    config.reload()


# ---------------------------------------------------------------------------
# Tier 3 #11 -- PDF output must be derived from the PDF input
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pdf_extraction_is_derived_from_the_input_file(monkeypatch, tmp_path):
    """A known non-PII string from the source must survive into extracted text.

    The pre-fix DRY_RUN fixture fails this immediately: it returned canned text
    about "Jane Doe Smith" with page_count 3 regardless of the file supplied.
    """
    _reload_config(monkeypatch, dry_run=None)

    marker = "SPECIMEN INTEGRITY ACCEPTABLE"
    pdf = tmp_path / "realistic_lab_report.pdf"
    _make_text_pdf(
        pdf,
        [
            "REGIONAL REFERENCE LABORATORY",
            "Patient: Marion T. Halloway    MRN: 40881236",
            "DOB: 03/14/1958    Accession: RL24A889134",
            "Ordering physician: Dr. Priya Raghunathan",
            marker,
            "HLA-A*02:01 HLA-B*07:02 HLA-DRB1*15:01",
        ],
    )

    # Stub the Haiku call: this test exercises extraction, not entity detection.
    import mcp_deidentify.format_handlers.pdf_handler as ph

    async def _no_entities(text, red_team=False):
        return []

    monkeypatch.setattr(ph, "extract_entities", _no_entities)

    result = await ph.deidentify_pdf_file(str(pdf), "PATTEST", {"entity_map": {}})

    assert result["status"] == "ok"
    assert result["page_count"] == 1, "page_count must reflect the real file"
    assert marker in result["raw_text"], "extracted text must come from the input PDF"
    assert "Jane Doe Smith" not in result["raw_text"], "must not be the old fixture"
    assert result["pages_without_text"] == []


@pytest.mark.asyncio
async def test_scanned_pdf_reports_no_text_layer(monkeypatch, tmp_path):
    """An image-only PDF must not read as 'no PII found'."""
    _reload_config(monkeypatch, dry_run=None)

    pdf = tmp_path / "scanned.pdf"
    _make_image_only_pdf(pdf, pages=2)

    import mcp_deidentify.format_handlers.pdf_handler as ph

    result = await ph.deidentify_pdf_file(str(pdf), "PATTEST", {"entity_map": {}})

    assert result["status"] == "no_text_layer"
    assert result["page_count"] == 2
    assert result["pages_without_text"] == [1, 2]
    assert "OCR" in result["error"]
