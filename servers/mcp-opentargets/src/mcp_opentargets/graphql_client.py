"""GraphQL query templates and async executor for Open Targets Platform API."""

import logging
from typing import Any, Dict, Optional

import aiohttp

from .disease_ontology import HGSOC_GENE_SYMBOL_TO_ENSEMBL

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level cache for gene symbol -> Ensembl ID resolution
# ---------------------------------------------------------------------------

_symbol_cache: Dict[str, str] = {}

# ---------------------------------------------------------------------------
# GraphQL query templates
# ---------------------------------------------------------------------------

TARGET_INFO_QUERY = """
query TargetInfo($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    biotype
    functionDescriptions
    tractability {
      label
      modality
      value
    }
  }
}
"""

TARGET_DISEASE_ASSOCIATION_QUERY = """
query TargetDiseaseAssociation($ensemblId: String!, $size: Int!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    associatedDiseases(page: {size: $size}) {
      rows {
        disease {
          id
          name
        }
        score
        datasourceScores {
          id
          score
        }
      }
    }
  }
}
"""

TARGET_DRUGS_QUERY = """
query TargetDrugs($ensemblId: String!, $size: Int!) {
  target(ensemblId: $ensemblId) {
    knownDrugs(size: $size) {
      rows {
        drug {
          id
          name
        }
        phase
        status
        mechanismOfAction
        disease {
          id
          name
        }
        urls {
          url
          name
        }
      }
    }
  }
}
"""

DISEASE_TARGETS_QUERY = """
query DiseaseTargets($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    associatedTargets(page: {size: $size, index: 0}) {
      rows {
        target {
          id
          approvedSymbol
        }
        score
        datasourceScores {
          id
          score
        }
      }
    }
  }
}
"""

TARGET_SAFETY_QUERY = """
query TargetSafety($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    safetyLiabilities {
      event
      biosamples {
        tissueLabel
      }
      effects {
        direction
        dosing
      }
      datasource
    }
    adverseEvents(page: {size: 20}) {
      rows {
        name
        count
        logLR
        meddraCode
      }
    }
  }
}
"""

SEARCH_QUERY = """
query Search($query: String!) {
  search(queryString: $query, entityNames: ["target"], page: {size: 5}) {
    hits {
      id
      ... on Target {
        approvedSymbol
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Async GraphQL executor
# ---------------------------------------------------------------------------

async def execute_query(
    query: str,
    variables: Dict[str, Any],
    api_url: str,
) -> Dict[str, Any]:
    """Execute a GraphQL query against the Open Targets API.

    Args:
        query: GraphQL query string.
        variables: Query variables dict.
        api_url: Open Targets GraphQL endpoint URL.

    Returns:
        The parsed JSON response data.

    Raises:
        RuntimeError: If the API returns errors or a non-200 status.
    """
    payload = {"query": query, "variables": variables}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(
                    f"Open Targets API returned status {resp.status}: {text[:500]}"
                )

            result = await resp.json()

            if "errors" in result:
                errors = result["errors"]
                msg = "; ".join(e.get("message", str(e)) for e in errors)
                raise RuntimeError(f"Open Targets GraphQL errors: {msg}")

            return result.get("data", {})


# ---------------------------------------------------------------------------
# Gene symbol resolver
# ---------------------------------------------------------------------------

async def resolve_gene_symbol(
    symbol: str,
    api_url: str,
) -> Optional[str]:
    """Resolve a gene symbol to an Ensembl ID.

    Checks the local HGSOC lookup table first, then falls back to the
    Open Targets search API. Results are cached in-memory.

    Args:
        symbol: Gene symbol (e.g., "TP53").
        api_url: Open Targets GraphQL endpoint URL.

    Returns:
        Ensembl ID string, or None if resolution fails.
    """
    symbol_upper = symbol.upper()

    # Check in-memory cache
    if symbol_upper in _symbol_cache:
        return _symbol_cache[symbol_upper]

    # Check local lookup table
    if symbol_upper in HGSOC_GENE_SYMBOL_TO_ENSEMBL:
        ensembl_id = HGSOC_GENE_SYMBOL_TO_ENSEMBL[symbol_upper]
        _symbol_cache[symbol_upper] = ensembl_id
        return ensembl_id

    # Fall back to Open Targets search API
    try:
        data = await execute_query(
            SEARCH_QUERY,
            {"query": symbol_upper},
            api_url,
        )
        hits = data.get("search", {}).get("hits", [])
        for hit in hits:
            approved = hit.get("approvedSymbol", "")
            if approved.upper() == symbol_upper:
                ensembl_id = hit["id"]
                _symbol_cache[symbol_upper] = ensembl_id
                return ensembl_id

        # If no exact match, take the first hit
        if hits:
            ensembl_id = hits[0]["id"]
            _symbol_cache[symbol_upper] = ensembl_id
            logger.warning(
                "No exact match for '%s', using first hit: %s", symbol, ensembl_id
            )
            return ensembl_id

    except Exception:
        logger.exception("Failed to resolve gene symbol '%s' via API", symbol)

    return None
