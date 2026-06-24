"""Tests for KeyManager -- key load, extend, save, and DRY_RUN behaviour."""

import os

import pytest

os.environ["DEIDENTIFY_DRY_RUN"] = "true"

from mcp_deidentify.key_manager import KeyManager


def test_dry_run_returns_synthetic_key():
    km = KeyManager("PAT-TEST-001")
    assert km.session_key["synthetic_data"] is True
    assert "entity_map" in km.session_key


def test_dry_run_patient_id_set_correctly():
    km = KeyManager("PAT-TEST-XYZ")
    assert km.session_key["patient_id"] == "PAT-TEST-XYZ"


def test_dry_run_save_is_noop(tmp_path):
    """save() in DRY_RUN must not write any file."""
    os.environ["DEIDENTIFY_KEY_DIR"] = str(tmp_path)
    km = KeyManager("PAT-TEST-001")
    km.save()
    # No file should have been written
    assert not any(tmp_path.rglob("*.json"))


def test_dry_run_path_property():
    km = KeyManager("PAT-TEST-001")
    # path must be a string and contain the patient id
    assert isinstance(km.path, str)
    assert "PAT-TEST-001" in km.path


def test_as_dict_omits_counters():
    km = KeyManager("PAT-TEST-001")
    d = km.as_dict()
    assert "_counters" not in d


def test_as_dict_contains_entity_map():
    km = KeyManager("PAT-TEST-001")
    d = km.as_dict()
    assert "entity_map" in d


# --- Live (disk) tests ---


@pytest.mark.live
def test_live_write_and_reload(tmp_path):
    """Live: key written to disk and reloaded should preserve entity_map."""
    import mcp_deidentify.key_manager as km_mod

    # Temporarily disable DRY_RUN
    orig_dry = km_mod.DRY_RUN
    orig_key_dir = km_mod.KEY_DIR
    km_mod.DRY_RUN = False
    km_mod.KEY_DIR = str(tmp_path)
    try:
        km = km_mod.KeyManager("PAT-LIVE-001")
        km.session_key["entity_map"]["Test Name"] = {
            "code": "Dr. ONC-001",
            "entity_type": "PERSON_NAME_PHYSICIAN",
        }
        km.save()
        # Reload
        km2 = km_mod.KeyManager("PAT-LIVE-001")
        assert "Test Name" in km2.session_key["entity_map"]
    finally:
        km_mod.DRY_RUN = orig_dry
        km_mod.KEY_DIR = orig_key_dir
