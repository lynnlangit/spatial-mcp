"""Regression test for Phase 8a.6 Fix 2 (mcp-perturbation dry_run path).

Covers the one-step ``perturbation_predict_response`` dry-run path that
returns a canonical PAT001 payload without requiring GEARS/torch training.
"""
import os

import pytest

# Force DRY_RUN env var before import so the server module picks it up.
os.environ["PERTURBATION_DRY_RUN"] = "true"

from mcp_perturbation.server import (  # noqa: E402
    DRY_RUN,
    _PAT001_PREDICT_DRY_RUN,
    _datasets,
    _models,
    _predict_response_impl,
)


def test_dry_run_flag_defaults_true_in_test_env():
    assert DRY_RUN is True


def test_predict_response_dry_run_explicit_returns_canonical_payload():
    """Explicit dry_run=True returns the canonical PAT001 payload."""
    result = _predict_response_impl(dry_run=True)
    assert result["status"] == "success"
    assert result["mode"] == "dry_run"
    assert result["treatment"] == _PAT001_PREDICT_DRY_RUN["treatment"]
    assert result["cell_type"] == _PAT001_PREDICT_DRY_RUN["cell_type"]
    assert result["top_upregulated"] == _PAT001_PREDICT_DRY_RUN["top_upregulated"]
    assert result["top_downregulated"] == _PAT001_PREDICT_DRY_RUN["top_downregulated"]
    # Dry-run warning injected by add_dry_run_warning
    assert "_DRY_RUN_WARNING" in result


def test_predict_response_no_model_env_dry_run_returns_canonical_payload():
    """When env DRY_RUN is on and no trained model exists, return canonical payload."""
    _models.clear()
    result = _predict_response_impl(model_name="missing_model")
    assert result["status"] == "success"
    assert result["mode"] == "dry_run"
    assert result["treatment"] == "NNMT+STAT3"


def test_predict_response_dataset_id_fallback_includes_hint():
    """When dataset_id is loaded but no trained model, return payload with setup hint."""
    _models.clear()
    _datasets["test_ds"] = object()  # sentinel; not touched by dry-run path
    try:
        result = _predict_response_impl(dataset_id="test_ds")
        assert result["status"] == "success"
        # Either env-dry-run path (with dataset_id_hint) or dataset_id fallback
        # path (with 'hint' field) — both are valid.
        assert "dataset_id_hint" in result or "hint" in result
        # canonical payload fields still present
        assert result["treatment"] == "NNMT+STAT3"
    finally:
        _datasets.pop("test_ds", None)


def test_predict_response_missing_patient_data_returns_helpful_error(monkeypatch):
    """With DRY_RUN disabled and a trained model, missing patient path returns a clear error."""
    import mcp_perturbation.server as server_mod
    monkeypatch.setattr(server_mod, "DRY_RUN", False)

    # Fake a trained model entry so the dry-run branches are skipped
    sentinel_wrapper = object()
    _models["fake_model"] = sentinel_wrapper
    try:
        result = _predict_response_impl(
            model_name="fake_model",
            dry_run=False,
        )
        assert result["status"] == "error"
        assert "patient_data_path" in result["message"]
    finally:
        _models.pop("fake_model", None)
