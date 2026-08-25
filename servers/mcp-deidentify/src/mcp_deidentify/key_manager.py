"""Disk-based anonymization key manager for mcp-deidentify.

Key file location:
  {DEIDENTIFY_KEY_DIR}/{patient_id}/{patient_id}_anonymization_key.json
  DEIDENTIFY_KEY_DIR defaults to <repo_root>/data/patients (absolute, not CWD-relative).

In DRY_RUN mode: no disk I/O. Returns in-memory synthetic key + a synthetic path.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from mcp_deidentify import config

logger = logging.getLogger(__name__)

# Anchor the default key directory to the repo root, not the process CWD.
# The anonymization key is the re-identification map for a patient -- the most
# sensitive artifact this server produces -- so where it lands must not depend
# on which directory the server happened to be launched from.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_KEY_DIR = _REPO_ROOT / "data" / "patients"


def _key_dir() -> Path:
    """Configured key directory, or the repo-anchored default."""
    return Path(config.KEY_DIR) if config.KEY_DIR else _DEFAULT_KEY_DIR


# Synthetic key returned in DRY_RUN mode -- no disk reads/writes
_SYNTHETIC_KEY: dict = {
    "patient_id": "PAT-SYNTHETIC-001",
    "generated_at": "2026-01-01T00:00:00+00:00",
    "synthetic_data": True,
    "entity_map": {
        "Jane Doe Smith": {"code": "PAT-NAME-001", "entity_type": "PERSON_NAME_PATIENT"},
        "Dr. Robert Sample": {"code": "Dr. ONC-001", "entity_type": "PERSON_NAME_PHYSICIAN"},
        "City General Hospital": {"code": "FAC-001", "entity_type": "FACILITY_NAME"},
        "12345678": {"code": "MRN-REDACTED-001", "entity_type": "MRN"},
        "22X-SAMPLE-00001": {"code": "ACCESSION-001", "entity_type": "ACCESSION_NUMBER"},
        "1980-01-01": {"code": "DOB-REDACTED", "entity_type": "DATE_OF_BIRTH"},
    },
    "_counters": {},
}


class KeyManager:
    """Load, extend, and persist the anonymization key for one patient."""

    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self._key: dict = {}
        self._path: Path = self._build_path(patient_id)

        if config.DRY_RUN:
            import copy

            self._key = copy.deepcopy(_SYNTHETIC_KEY)
            self._key["patient_id"] = patient_id
        else:
            self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def session_key(self) -> dict:
        """Return the mutable in-memory key dict.

        Pass this to code_generator.assign_code -- it will be modified in-place.
        After your operation, call save() to persist changes.
        """
        return self._key

    @property
    def path(self) -> str:
        """Absolute path to the key file (may not exist yet in DRY_RUN)."""
        return str(self._path.resolve())

    def save(self) -> str:
        """Write the current key to disk. No-op in DRY_RUN. Returns key path."""
        if config.DRY_RUN:
            logger.debug("DRY_RUN: skipping key write to disk")
            return self.path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._key["generated_at"] = datetime.now(UTC).isoformat()
        with open(self._path, "w") as f:
            json.dump(self._key, f, indent=2)
        logger.info(f"Anonymization key written: {self._path}")
        return self.path

    def as_dict(self) -> dict:
        """Return a clean copy of the key (without internal _counters)."""
        import copy

        clean = copy.deepcopy(self._key)
        clean.pop("_counters", None)
        return clean

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _build_path(patient_id: str) -> Path:
        return _key_dir() / patient_id / f"{patient_id}_anonymization_key.json"

    def _load(self) -> None:
        """Load key from disk if it exists, otherwise initialise empty key."""
        if self._path.exists():
            with open(self._path) as f:
                self._key = json.load(f)
            logger.info(f"Loaded existing anonymization key: {self._path}")
        else:
            self._key = {
                "patient_id": self.patient_id,
                "generated_at": datetime.now(UTC).isoformat(),
                "synthetic_data": False,
                "entity_map": {},
                "_counters": {},
            }
            logger.info(f"No existing key found for {self.patient_id}; starting fresh")
