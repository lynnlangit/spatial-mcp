"""Central configuration for mcp-deidentify.

Every module reads DRY_RUN, DATE_POLICY and KEY_DIR from here instead of calling
os.getenv() on its own. Two reasons:

1. A module-level ``os.getenv()`` in each file snapshots the value at *import*
   time. Seven modules doing that independently could disagree with each other
   if the environment changed between imports, which is how a "half-stubbed"
   server becomes possible in the first place.
2. Call sites reference ``config.DRY_RUN`` (attribute lookup at call time), so a
   test can flip one value and have the whole server agree.

DEIDENTIFY_DRY_RUN defaults to **"false"**. This deliberately diverges from the
repo-wide convention of defaulting DRY_RUN on. For a de-identification server,
emitting fabricated entities is a safety failure rather than a safe default: a
caller who forgets the env var must get a loud error, never synthetic output
that reads like a successful de-identification.

DEIDENTIFY_DATE_POLICY selects the HIPAA regime:

    SAFE_HARBOR       (default) No date elements except year. 45 CFR 164.514(b)(2).
    LIMITED_DATA_SET  Full dates retained. 45 CFR 164.514(e). Requires a data use
                      agreement; the caller is responsible for having one.

The policy is applied consistently by the deidentify_* tools and by
validate_deidentification, so the validator can no longer flag as residual PII a
date that the de-identifier was configured to keep.
"""

import os

SAFE_HARBOR = "SAFE_HARBOR"
LIMITED_DATA_SET = "LIMITED_DATA_SET"
VALID_DATE_POLICIES = (SAFE_HARBOR, LIMITED_DATA_SET)


def _read_dry_run() -> bool:
    return os.getenv("DEIDENTIFY_DRY_RUN", "false").strip().lower() == "true"


def _read_date_policy() -> str:
    raw = os.getenv("DEIDENTIFY_DATE_POLICY", SAFE_HARBOR).strip().upper()
    if raw not in VALID_DATE_POLICIES:
        raise ValueError(
            f"DEIDENTIFY_DATE_POLICY={raw!r} is not a valid policy. "
            f"Expected one of {VALID_DATE_POLICIES}."
        )
    return raw


def _read_key_dir() -> str:
    """Empty string means 'use the repo-anchored default' (see key_manager)."""
    return os.getenv("DEIDENTIFY_KEY_DIR", "").strip()


DRY_RUN: bool = _read_dry_run()
DATE_POLICY: str = _read_date_policy()
KEY_DIR: str = _read_key_dir()


def reload() -> None:
    """Re-read every setting from the environment.

    Intended for tests, which need to exercise both modes in one process.
    Production code should never call this.
    """
    global DRY_RUN, DATE_POLICY, KEY_DIR
    DRY_RUN = _read_dry_run()
    DATE_POLICY = _read_date_policy()
    KEY_DIR = _read_key_dir()
