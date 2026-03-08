"""IEDB (Immune Epitope Database) REST API client for MHC binding prediction."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

IEDB_BASE_URL = "http://tools-cluster-interface.iedb.org/tools_api"

# IEDB rate limiting — conservative semaphore
_rate_semaphore = asyncio.Semaphore(2)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=120)


async def predict_mhc_class_i(
    peptides: List[str],
    alleles: List[str],
    method: str = "netmhcpan_ba",
    length: int = 9,
    api_url: str = IEDB_BASE_URL,
) -> List[Dict[str, Any]]:
    """Predict MHC class I binding affinity via the IEDB API.

    Args:
        peptides: List of peptide sequences (amino acid strings).
        alleles: List of HLA class I alleles (e.g., ["HLA-A*02:01"]).
        method: Prediction method. Options: netmhcpan_ba, netmhcpan_el,
            ann, smm, comblib_sidney2008.
        length: Peptide length for prediction (8-14, default 9).
        api_url: Base URL for the IEDB API.

    Returns:
        List of prediction dicts with allele, peptide, ic50, rank, etc.
    """
    sequence_text = "\n".join(peptides)
    allele_text = ",".join(alleles)

    payload = {
        "method": method,
        "sequence_text": sequence_text,
        "allele": allele_text,
        "length": str(length),
    }

    async with _rate_semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/mhci/",
                data=payload,
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(
                        f"IEDB MHC-I API returned status {resp.status}: {text[:500]}"
                    )
                text = await resp.text()
                return _parse_iedb_response(text)


async def predict_mhc_class_ii(
    peptides: List[str],
    alleles: List[str],
    method: str = "netmhciipan",
    length: int = 15,
    api_url: str = IEDB_BASE_URL,
) -> List[Dict[str, Any]]:
    """Predict MHC class II binding affinity via the IEDB API.

    Args:
        peptides: List of peptide sequences.
        alleles: List of HLA class II alleles (e.g., ["HLA-DRB1*01:01"]).
        method: Prediction method. Options: netmhciipan, nn_align, smm_align.
        length: Peptide length (default 15).
        api_url: Base URL for the IEDB API.

    Returns:
        List of prediction dicts.
    """
    sequence_text = "\n".join(peptides)
    allele_text = ",".join(alleles)

    payload = {
        "method": method,
        "sequence_text": sequence_text,
        "allele": allele_text,
        "length": str(length),
    }

    async with _rate_semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/mhcii/",
                data=payload,
                timeout=DEFAULT_TIMEOUT,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(
                        f"IEDB MHC-II API returned status {resp.status}: {text[:500]}"
                    )
                text = await resp.text()
                return _parse_iedb_response(text)


def _parse_iedb_response(text: str) -> List[Dict[str, Any]]:
    """Parse tab-delimited IEDB API response into list of dicts.

    The IEDB API returns tab-separated values with a header row.

    Args:
        text: Raw response text from the IEDB API.

    Returns:
        List of prediction result dicts.
    """
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return []

    headers = [h.strip().lower() for h in lines[0].split("\t")]
    results = []
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) != len(headers):
            continue
        row = {}
        for header, value in zip(headers, fields):
            value = value.strip()
            # Try numeric conversion
            try:
                if "." in value:
                    row[header] = float(value)
                else:
                    row[header] = int(value)
            except (ValueError, TypeError):
                row[header] = value
        results.append(row)

    return results


async def predict_mhc_batch(
    peptides: List[str],
    alleles: List[str],
    method: str = "netmhcpan_ba",
    length: int = 9,
    batch_size: int = 100,
    api_url: str = IEDB_BASE_URL,
) -> List[Dict[str, Any]]:
    """Predict MHC class I binding in batches to respect IEDB rate limits.

    Args:
        peptides: Full list of peptide sequences.
        alleles: HLA alleles for prediction.
        method: Prediction method.
        length: Peptide length.
        batch_size: Number of peptides per API call (default 100).
        api_url: IEDB API base URL.

    Returns:
        Aggregated list of all prediction results.
    """
    all_results = []
    for i in range(0, len(peptides), batch_size):
        batch = peptides[i : i + batch_size]
        results = await predict_mhc_class_i(
            peptides=batch,
            alleles=alleles,
            method=method,
            length=length,
            api_url=api_url,
        )
        all_results.extend(results)

    return all_results
