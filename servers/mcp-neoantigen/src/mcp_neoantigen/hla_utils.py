"""HLA allele format conversion utilities.

Normalizes between the many HLA naming conventions used by different tools:
- IEDB:      "HLA-A*02:01"
- NetMHCpan: "HLA-A02:01"
- OptiType:  "A*02:01"
- Compact:   "A0201"
"""

import re
from typing import List

# Regex pattern for HLA alleles in various formats
_HLA_PATTERN = re.compile(
    r"^(HLA-)?"           # Optional "HLA-" prefix
    r"([A-C]|D[PQR][AB]\d?)"  # Gene: A, B, C, or DPA1/DPB1/DQA1/DQB1/DRB1
    r"\*?"                # Optional asterisk separator
    r"(\d{2,4})"          # First field (2 or 4 digits)
    r":?"                 # Optional colon separator
    r"(\d{2,4})?"         # Second field (optional, 2 or 4 digits)
    r"$",
    re.IGNORECASE,
)

# Valid HLA class I genes
HLA_CLASS_I_GENES = {"A", "B", "C"}

# Valid HLA class II genes
HLA_CLASS_II_GENES = {"DPA1", "DPB1", "DQA1", "DQB1", "DRB1"}


def normalize_hla_allele(allele: str) -> str:
    """Convert any HLA naming format to the canonical form: HLA-A*02:01.

    Handles these input formats:
        'HLA-A*02:01' -> 'HLA-A*02:01'  (already canonical)
        'A*02:01'     -> 'HLA-A*02:01'  (missing HLA prefix)
        'A0201'       -> 'HLA-A*02:01'  (compact 4-digit)
        'HLA-A02:01'  -> 'HLA-A*02:01'  (missing asterisk)
        'a*02:01'     -> 'HLA-A*02:01'  (lowercase)

    Args:
        allele: HLA allele string in any common format.

    Returns:
        Canonical HLA allele string (e.g., "HLA-A*02:01").

    Raises:
        ValueError: If the allele string cannot be parsed.
    """
    allele = allele.strip()
    match = _HLA_PATTERN.match(allele)

    if not match:
        raise ValueError(
            f"Cannot parse HLA allele: '{allele}'. "
            "Expected format like 'HLA-A*02:01', 'A*02:01', or 'A0201'."
        )

    gene = match.group(2).upper()
    field1 = match.group(3)
    field2 = match.group(4)

    # Handle compact 4-digit format: "0201" -> field1="02", field2="01"
    if field2 is None and len(field1) == 4:
        field2 = field1[2:]
        field1 = field1[:2]
    elif field2 is None and len(field1) == 2:
        # Only first field provided (e.g., "A*02"), use "01" as default
        field2 = "01"

    # Ensure 2-digit fields
    field1 = field1[:2].zfill(2)
    field2 = field2[:2].zfill(2)

    return f"HLA-{gene}*{field1}:{field2}"


def normalize_hla_list(alleles: List[str]) -> List[str]:
    """Normalize a list of HLA alleles to canonical format.

    Args:
        alleles: List of HLA allele strings.

    Returns:
        List of normalized allele strings.

    Raises:
        ValueError: If any allele cannot be parsed.
    """
    return [normalize_hla_allele(a) for a in alleles]


def is_class_i(allele: str) -> bool:
    """Check if an HLA allele is class I (A, B, or C).

    Args:
        allele: HLA allele string (any format).

    Returns:
        True if class I, False otherwise.
    """
    normalized = normalize_hla_allele(allele)
    gene = normalized.split("*")[0].replace("HLA-", "")
    return gene in HLA_CLASS_I_GENES


def is_class_ii(allele: str) -> bool:
    """Check if an HLA allele is class II (DR, DP, DQ).

    Args:
        allele: HLA allele string (any format).

    Returns:
        True if class II, False otherwise.
    """
    normalized = normalize_hla_allele(allele)
    gene = normalized.split("*")[0].replace("HLA-", "")
    return gene in HLA_CLASS_II_GENES


def format_for_iedb(allele: str) -> str:
    """Format an HLA allele for the IEDB API.

    IEDB expects: "HLA-A*02:01" for class I, "HLA-DRB1*01:01" for class II.

    Args:
        allele: HLA allele string (any format).

    Returns:
        IEDB-compatible allele string.
    """
    return normalize_hla_allele(allele)
