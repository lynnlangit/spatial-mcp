"""MCP Open Targets server - query drug-target evidence and association scores."""

import logging
import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .disease_ontology import (
    DISEASE_IDS,
    HGSOC_GENE_SYMBOL_TO_ENSEMBL,
    MOCK_ASSOCIATION_SCORES,
    MOCK_DEFAULT_ASSOCIATION,
    MOCK_DEFAULT_SAFETY,
    MOCK_DEFAULT_TARGET_INFO,
    MOCK_DISEASE_TARGETS,
    MOCK_DRUGS,
    MOCK_SAFETY,
    MOCK_TARGET_INFO,
)
from .graphql_client import (
    DISEASE_TARGETS_QUERY,
    TARGET_DISEASE_ASSOCIATION_QUERY,
    TARGET_DRUGS_QUERY,
    TARGET_INFO_QUERY,
    TARGET_SAFETY_QUERY,
    execute_query,
    resolve_gene_symbol,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("opentargets")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DRY_RUN = os.getenv("OPENTARGETS_DRY_RUN", "true").lower() == "true"
OPENTARGETS_API_URL = os.getenv(
    "OPENTARGETS_API_URL",
    "https://api.platform.opentargets.org/api/v4/graphql",
)


def add_dry_run_warning(result: Any) -> Any:
    """Add warning banner to results when in DRY_RUN mode."""
    if not DRY_RUN:
        return result

    warning = (
        "=== SYNTHETIC DATA WARNING ===\n"
        "This result was generated in DRY_RUN mode and does NOT represent real analysis.\n"
        "Do NOT use this data for clinical decisions.\n"
        "Set OPENTARGETS_DRY_RUN=false for production use.\n"
        "==============================\n\n"
    )

    if isinstance(result, dict):
        result["_DRY_RUN_WARNING"] = "SYNTHETIC DATA - NOT FOR CLINICAL USE"
        result["_message"] = warning.strip()
    elif isinstance(result, str):
        result = warning + result

    return result


# ---------------------------------------------------------------------------
# Helper to resolve symbol or ensembl_id
# ---------------------------------------------------------------------------

async def _resolve_target(
    gene_symbol: str = "",
    ensembl_id: str = "",
) -> tuple[str, str]:
    """Resolve gene_symbol and ensembl_id, returning (symbol, ensembl_id).

    Raises ValueError if neither can be resolved.
    """
    if ensembl_id and gene_symbol:
        return gene_symbol.upper(), ensembl_id

    if ensembl_id and not gene_symbol:
        # Reverse lookup from our table
        for sym, eid in HGSOC_GENE_SYMBOL_TO_ENSEMBL.items():
            if eid == ensembl_id:
                return sym, ensembl_id
        return ensembl_id, ensembl_id  # Use ID as symbol fallback

    if gene_symbol:
        symbol = gene_symbol.upper()
        eid = await resolve_gene_symbol(symbol, OPENTARGETS_API_URL)
        if eid is None:
            raise ValueError(
                f"Could not resolve gene symbol '{gene_symbol}' to an Ensembl ID. "
                f"Known HGSOC genes: {', '.join(sorted(HGSOC_GENE_SYMBOL_TO_ENSEMBL.keys()))}"
            )
        return symbol, eid

    raise ValueError("Either gene_symbol or ensembl_id must be provided.")


# ---------------------------------------------------------------------------
# Tool implementation functions
# ---------------------------------------------------------------------------

async def _get_target_info_impl(
    gene_symbol: str = "",
    ensembl_id: str = "",
) -> Dict[str, Any]:
    """Implementation for get_target_info."""
    if DRY_RUN:
        symbol = (gene_symbol or ensembl_id).upper()
        # Check our mock data
        if symbol in MOCK_TARGET_INFO:
            info = MOCK_TARGET_INFO[symbol]
        else:
            eid = HGSOC_GENE_SYMBOL_TO_ENSEMBL.get(symbol, f"ENSG_UNKNOWN_{symbol}")
            info = {
                "id": eid,
                "symbol": symbol,
                "name": f"{symbol} gene",
                **MOCK_DEFAULT_TARGET_INFO,
            }
        return add_dry_run_warning({"status": "success", "target": info})

    symbol, eid = await _resolve_target(gene_symbol, ensembl_id)

    data = await execute_query(
        TARGET_INFO_QUERY,
        {"ensemblId": eid},
        OPENTARGETS_API_URL,
    )
    target = data.get("target")
    if not target:
        return {"status": "error", "message": f"Target not found: {symbol} ({eid})"}

    # Transform tractability
    tractability = {}
    for entry in target.get("tractability", []):
        modality = entry.get("modality", "unknown")
        tractability[modality] = entry.get("value", False)

    descriptions = target.get("functionDescriptions", [])
    description = descriptions[0] if descriptions else ""

    return {
        "status": "success",
        "target": {
            "id": target["id"],
            "symbol": target.get("approvedSymbol", symbol),
            "name": target.get("approvedName", ""),
            "description": description,
            "biotype": target.get("biotype", ""),
            "tractability": tractability,
        },
    }


async def _get_target_disease_associations_impl(
    gene_symbol: str,
    disease_id: str = "EFO_0001071",
    top_n: int = 10,
) -> Dict[str, Any]:
    """Implementation for get_target_disease_associations."""
    symbol = gene_symbol.upper()

    if DRY_RUN:
        scores = MOCK_ASSOCIATION_SCORES.get(symbol, MOCK_DEFAULT_ASSOCIATION)
        disease_name = "ovarian carcinoma"
        for name, eid in DISEASE_IDS.items():
            if eid == disease_id:
                disease_name = name
                break
        return add_dry_run_warning({
            "status": "success",
            "target": symbol,
            "disease": disease_name,
            "disease_id": disease_id,
            **scores,
        })

    _, eid = await _resolve_target(gene_symbol=gene_symbol)

    data = await execute_query(
        TARGET_DISEASE_ASSOCIATION_QUERY,
        {"ensemblId": eid, "size": max(top_n, 50)},
        OPENTARGETS_API_URL,
    )
    target = data.get("target")
    if not target:
        return {"status": "error", "message": f"Target not found: {symbol}"}

    rows = target.get("associatedDiseases", {}).get("rows", [])

    # Find the specific disease
    match = None
    for row in rows:
        if row.get("disease", {}).get("id") == disease_id:
            match = row
            break

    if not match:
        return {
            "status": "success",
            "target": symbol,
            "disease_id": disease_id,
            "overall_score": 0.0,
            "evidence_scores": {},
            "message": f"No association found between {symbol} and {disease_id}",
        }

    evidence_scores = {}
    for ds in match.get("datasourceScores", []):
        evidence_scores[ds["id"]] = ds["score"]

    return {
        "status": "success",
        "target": symbol,
        "disease": match["disease"]["name"],
        "disease_id": disease_id,
        "overall_score": match.get("score", 0.0),
        "evidence_scores": evidence_scores,
    }


async def _get_target_drugs_impl(
    gene_symbol: str,
    phase_min: int = 0,
) -> Dict[str, Any]:
    """Implementation for get_target_drugs."""
    symbol = gene_symbol.upper()

    if DRY_RUN:
        drugs = MOCK_DRUGS.get(symbol, [])
        filtered = [d for d in drugs if d.get("phase", 0) >= phase_min]
        return add_dry_run_warning({
            "status": "success",
            "target": symbol,
            "drugs": filtered,
            "total_drugs": len(filtered),
        })

    _, eid = await _resolve_target(gene_symbol=gene_symbol)

    data = await execute_query(
        TARGET_DRUGS_QUERY,
        {"ensemblId": eid, "size": 100},
        OPENTARGETS_API_URL,
    )
    target = data.get("target")
    if not target:
        return {"status": "error", "message": f"Target not found: {symbol}"}

    rows = target.get("knownDrugs", {}).get("rows", [])

    # Deduplicate drugs by name and collect indications
    drugs_by_name: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        phase = row.get("phase", 0)
        if phase < phase_min:
            continue

        drug_name = row.get("drug", {}).get("name", "Unknown")
        if drug_name not in drugs_by_name:
            drugs_by_name[drug_name] = {
                "name": drug_name,
                "phase": phase,
                "status": row.get("status", ""),
                "mechanism": row.get("mechanismOfAction", ""),
                "indications": [],
                "clinical_trial_count": 0,
            }

        disease_name = row.get("disease", {}).get("name", "")
        if disease_name and disease_name not in drugs_by_name[drug_name]["indications"]:
            drugs_by_name[drug_name]["indications"].append(disease_name)
        drugs_by_name[drug_name]["clinical_trial_count"] += 1

        # Keep highest phase
        if phase > drugs_by_name[drug_name]["phase"]:
            drugs_by_name[drug_name]["phase"] = phase

    drugs = sorted(drugs_by_name.values(), key=lambda d: d["phase"], reverse=True)

    return {
        "status": "success",
        "target": symbol,
        "drugs": drugs,
        "total_drugs": len(drugs),
    }


async def _search_targets_by_disease_impl(
    disease_id: str = "EFO_0001071",
    top_n: int = 25,
    evidence_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Implementation for search_targets_by_disease."""
    if DRY_RUN:
        disease_name = "ovarian carcinoma"
        for name, eid in DISEASE_IDS.items():
            if eid == disease_id:
                disease_name = name
                break

        targets = MOCK_DISEASE_TARGETS[:top_n]
        if evidence_type:
            targets = [t for t in targets if t["top_evidence"] == evidence_type][:top_n]

        return add_dry_run_warning({
            "status": "success",
            "disease": disease_name,
            "disease_id": disease_id,
            "targets": targets,
            "total_targets": len(targets),
        })

    data = await execute_query(
        DISEASE_TARGETS_QUERY,
        {"efoId": disease_id, "size": top_n},
        OPENTARGETS_API_URL,
    )
    disease = data.get("disease")
    if not disease:
        return {"status": "error", "message": f"Disease not found: {disease_id}"}

    rows = disease.get("associatedTargets", {}).get("rows", [])
    targets = []
    for row in rows:
        ds_scores = {ds["id"]: ds["score"] for ds in row.get("datasourceScores", [])}

        # Determine top evidence type
        top_evidence = max(ds_scores, key=ds_scores.get) if ds_scores else "unknown"

        if evidence_type and top_evidence != evidence_type:
            continue

        targets.append({
            "symbol": row.get("target", {}).get("approvedSymbol", ""),
            "ensembl_id": row.get("target", {}).get("id", ""),
            "score": row.get("score", 0.0),
            "top_evidence": top_evidence,
        })

    return {
        "status": "success",
        "disease": disease.get("name", ""),
        "disease_id": disease_id,
        "targets": targets[:top_n],
        "total_targets": len(targets),
    }


async def _get_target_safety_impl(
    gene_symbol: str,
) -> Dict[str, Any]:
    """Implementation for get_target_safety."""
    symbol = gene_symbol.upper()

    if DRY_RUN:
        safety = MOCK_SAFETY.get(symbol, MOCK_DEFAULT_SAFETY)
        return add_dry_run_warning({
            "status": "success",
            "target": symbol,
            **safety,
        })

    _, eid = await _resolve_target(gene_symbol=gene_symbol)

    data = await execute_query(
        TARGET_SAFETY_QUERY,
        {"ensemblId": eid},
        OPENTARGETS_API_URL,
    )
    target = data.get("target")
    if not target:
        return {"status": "error", "message": f"Target not found: {symbol}"}

    # Transform safety liabilities
    safety_liabilities = []
    for liability in target.get("safetyLiabilities", []):
        biosamples = [b.get("tissueLabel", "") for b in liability.get("biosamples", [])]
        effects = []
        for effect in liability.get("effects", []):
            direction = effect.get("direction", "")
            dosing = effect.get("dosing", "")
            if direction or dosing:
                effects.append(f"{direction} ({dosing})" if dosing else direction)

        safety_liabilities.append({
            "event": liability.get("event", ""),
            "biosamples": biosamples,
            "effects": effects,
            "datasource": liability.get("datasource", ""),
        })

    # Transform adverse events
    adverse_events = []
    for ae in target.get("adverseEvents", {}).get("rows", []):
        count = ae.get("count", 0)
        if count >= 1000:
            frequency = "very_common"
        elif count >= 100:
            frequency = "common"
        else:
            frequency = "uncommon"

        adverse_events.append({
            "event": ae.get("name", ""),
            "count": count,
            "frequency": frequency,
        })

    # Determine overall risk level
    if len(safety_liabilities) >= 3:
        risk_level = "high"
    elif len(safety_liabilities) >= 1:
        risk_level = "moderate"
    elif adverse_events:
        risk_level = "low"
    else:
        risk_level = "unknown"

    return {
        "status": "success",
        "target": symbol,
        "safety_liabilities": safety_liabilities,
        "adverse_events": adverse_events,
        "risk_level": risk_level,
    }


async def _batch_score_targets_impl(
    gene_symbols: List[str],
    disease_id: str = "EFO_0001071",
) -> Dict[str, Any]:
    """Implementation for batch_score_targets."""
    if DRY_RUN:
        disease_name = "ovarian carcinoma"
        for name, eid in DISEASE_IDS.items():
            if eid == disease_id:
                disease_name = name
                break

        scores = {}
        druggable_targets = []
        novel_targets = []

        for sym in gene_symbols:
            sym_upper = sym.upper()
            assoc = MOCK_ASSOCIATION_SCORES.get(sym_upper, MOCK_DEFAULT_ASSOCIATION)
            scores[sym_upper] = assoc["overall_score"]

            drugs = MOCK_DRUGS.get(sym_upper, [])
            if drugs:
                druggable_targets.append(sym_upper)
            elif assoc["overall_score"] > 0.4:
                novel_targets.append(sym_upper)

        return add_dry_run_warning({
            "status": "success",
            "disease": disease_name,
            "disease_id": disease_id,
            "scores": scores,
            "druggable_targets": druggable_targets,
            "novel_targets": novel_targets,
            "total_queried": len(gene_symbols),
        })

    # Chunk into groups of 10
    scores = {}
    druggable_targets = []
    novel_targets = []
    errors = []

    for i in range(0, len(gene_symbols), 10):
        chunk = gene_symbols[i : i + 10]
        for sym in chunk:
            try:
                result = await _get_target_disease_associations_impl(
                    gene_symbol=sym,
                    disease_id=disease_id,
                )
                if result.get("status") == "success":
                    score = result.get("overall_score", 0.0)
                    scores[sym.upper()] = score
                else:
                    errors.append(sym)
            except Exception as exc:
                logger.warning("Failed to score %s: %s", sym, exc)
                errors.append(sym)

        # Check drugability for this chunk
        for sym in chunk:
            sym_upper = sym.upper()
            if sym_upper in errors:
                continue
            try:
                drug_result = await _get_target_drugs_impl(
                    gene_symbol=sym, phase_min=1
                )
                if drug_result.get("total_drugs", 0) > 0:
                    druggable_targets.append(sym_upper)
                elif scores.get(sym_upper, 0) > 0.4:
                    novel_targets.append(sym_upper)
            except Exception:
                pass

    disease_name = disease_id
    result_data = {
        "status": "success",
        "disease": disease_name,
        "disease_id": disease_id,
        "scores": scores,
        "druggable_targets": druggable_targets,
        "novel_targets": novel_targets,
        "total_queried": len(gene_symbols),
    }
    if errors:
        result_data["errors"] = errors

    return result_data


# ============================================================================
# MCP Tool wrappers
# ============================================================================

@mcp.tool()
async def get_target_info(
    gene_symbol: str = "",
    ensembl_id: str = "",
) -> Dict[str, Any]:
    """Look up gene/target information and tractability from Open Targets.

    Retrieves basic target info including approved symbol, name, description,
    biotype, and tractability assessment (small molecule, antibody, other).

    Args:
        gene_symbol: Gene symbol (e.g., "TP53", "PIK3CA"). Case-insensitive.
        ensembl_id: Ensembl gene ID (e.g., "ENSG00000141510"). Alternative to symbol.

    Returns:
        Dictionary with target info including tractability scores.
    """
    return await _get_target_info_impl(gene_symbol, ensembl_id)


@mcp.tool()
async def get_target_disease_associations(
    gene_symbol: str,
    disease_id: str = "EFO_0001071",
    top_n: int = 10,
) -> Dict[str, Any]:
    """Get association evidence scores between a gene target and a disease.

    Queries the Open Targets Platform for the overall association score and
    per-datasource evidence scores (literature, RNA expression, genetic
    association, somatic mutation, known drug, animal model, affected pathway).

    Args:
        gene_symbol: Gene symbol (e.g., "TP53").
        disease_id: EFO disease ID. Default is ovarian carcinoma (EFO_0001071).
        top_n: Max disease associations to retrieve (used for API page size).

    Returns:
        Dictionary with overall_score and evidence_scores breakdown.
    """
    return await _get_target_disease_associations_impl(gene_symbol, disease_id, top_n)


@mcp.tool()
async def get_target_drugs(
    gene_symbol: str,
    phase_min: int = 0,
) -> Dict[str, Any]:
    """Get approved and in-trial drugs targeting a specific gene.

    Retrieves known drugs from Open Targets including drug name, clinical phase,
    approval status, mechanism of action, and indications.

    Args:
        gene_symbol: Gene symbol (e.g., "PIK3CA", "VEGFA").
        phase_min: Minimum clinical trial phase to include (0-4). 0 = all phases.

    Returns:
        Dictionary with list of drugs sorted by phase (highest first).
    """
    return await _get_target_drugs_impl(gene_symbol, phase_min)


@mcp.tool()
async def search_targets_by_disease(
    disease_id: str = "EFO_0001071",
    top_n: int = 25,
    evidence_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Find top gene targets associated with a disease.

    Queries Open Targets for genes most strongly associated with a disease,
    ranked by overall association score. Optionally filter by evidence type.

    Args:
        disease_id: EFO disease ID. Default is ovarian carcinoma (EFO_0001071).
        top_n: Number of top targets to return (max 100).
        evidence_type: Filter by top evidence type (e.g., "somatic_mutation",
            "known_drug", "genetic_association", "literature", "rna_expression").

    Returns:
        Dictionary with ranked list of targets and their scores.
    """
    return await _search_targets_by_disease_impl(disease_id, top_n, evidence_type)


@mcp.tool()
async def get_target_safety(
    gene_symbol: str,
) -> Dict[str, Any]:
    """Get safety and adverse event profiles for a gene target.

    Retrieves known safety liabilities, organ-specific risks, and adverse event
    frequencies from the Open Targets Platform.

    Args:
        gene_symbol: Gene symbol (e.g., "VEGFA").

    Returns:
        Dictionary with safety liabilities, adverse events, and risk level.
    """
    return await _get_target_safety_impl(gene_symbol)


@mcp.tool()
async def batch_score_targets(
    gene_symbols: List[str],
    disease_id: str = "EFO_0001071",
) -> Dict[str, Any]:
    """Score multiple gene targets against a disease in batch.

    Looks up association scores for a list of genes, identifies which have
    approved drugs (druggable targets) and which are high-scoring but lack
    drugs (novel targets). Queries are chunked in groups of 10 to avoid
    API complexity limits.

    Args:
        gene_symbols: List of gene symbols (e.g., ["TP53", "PIK3CA", "VEGFA"]).
        disease_id: EFO disease ID. Default is ovarian carcinoma (EFO_0001071).

    Returns:
        Dictionary with per-gene scores, druggable_targets, and novel_targets.
    """
    return await _batch_score_targets_impl(gene_symbols, disease_id)


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP opentargets server."""
    logger.info("Starting mcp-opentargets server...")

    if DRY_RUN:
        logger.warning("=" * 70)
        logger.warning("DRY_RUN MODE ENABLED - RETURNING SYNTHETIC DATA")
        logger.warning("Set OPENTARGETS_DRY_RUN=false for production use")
        logger.warning("=" * 70)
    else:
        logger.info("Production mode enabled (OPENTARGETS_DRY_RUN=false)")

    transport = os.getenv("MCP_TRANSPORT", "stdio")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))

    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport, port=port, host="0.0.0.0")
    else:
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()
