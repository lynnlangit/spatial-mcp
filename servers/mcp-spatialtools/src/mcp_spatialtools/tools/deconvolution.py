"""Cell type deconvolution tools."""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# Ovarian cancer-specific cell type gene signatures
OVARIAN_CANCER_CELL_SIGNATURES = {
    "tumor_cells": {
        "markers": ["EPCAM", "KRT8", "KRT18", "PAX8", "TP53"],
        "description": "Epithelial tumor cells"
    },
    "cd8_tcells": {
        "markers": ["CD8A", "CD3D", "CD3E"],
        "description": "CD8+ cytotoxic T lymphocytes"
    },
    "cd4_tcells": {
        "markers": ["CD4", "CD3D", "CD3E"],
        "description": "CD4+ helper T lymphocytes"
    },
    "regulatory_tcells": {
        "markers": ["FOXP3", "CD4", "CD3D"],
        "description": "Regulatory T cells (Tregs)"
    },
    "macrophages": {
        "markers": ["CD68", "CD163"],
        "description": "Tumor-associated macrophages (TAMs)"
    },
    "endothelial_cells": {
        "markers": ["CD31", "VWF", "VEGFA", "KDR"],
        "description": "Endothelial cells (vasculature)"
    },
    "fibroblasts": {
        "markers": ["FAP", "COL1A1", "COL3A1", "ACTA2"],
        "description": "Cancer-associated fibroblasts (CAFs)"
    },
    "mesenchymal_cells": {
        "markers": ["VIM", "SNAI1", "TWIST1", "CDH2"],
        "description": "Mesenchymal/EMT cells"
    }
}


async def deconvolve_cell_types_impl(
    expression_file: str,
    signatures: Optional[Dict[str, List[str]]],
    normalize: bool,
    include_spot_scores: bool,
    *,
    dry_run: bool,
    add_dry_run_warning: callable,
) -> Dict[str, Any]:
    """Estimate cell type proportions from bulk spatial transcriptomics data."""
    if dry_run:
        return add_dry_run_warning({
            "cell_types": [],
            "message": "DRY_RUN mode enabled. Set SPATIAL_DRY_RUN=false for real analysis."
        })

    try:
        expr_data = pd.read_csv(expression_file, index_col=0)

        if signatures is None:
            signatures = {
                cell_type: sig_info["markers"]
                for cell_type, sig_info in OVARIAN_CANCER_CELL_SIGNATURES.items()
            }

        gene_cols = [col for col in expr_data.columns
                     if col not in ['x', 'y', 'in_tissue', 'region', 'n_reads', 'n_genes', 'mt_percent']]
        expr_data_genes = expr_data[gene_cols]

        cell_type_scores = {}
        signatures_used = {}

        for cell_type, marker_genes in signatures.items():
            available_genes = [g for g in marker_genes if g in expr_data_genes.columns]

            if not available_genes:
                cell_type_scores[cell_type] = np.zeros(len(expr_data_genes))
                signatures_used[cell_type] = {
                    "markers_requested": marker_genes,
                    "markers_available": [],
                    "markers_used": 0
                }
                continue

            signature_expr = expr_data_genes[available_genes].mean(axis=1)

            if normalize:
                mean_val = signature_expr.mean()
                std_val = signature_expr.std()
                if std_val > 0:
                    signature_expr = (signature_expr - mean_val) / std_val
                else:
                    signature_expr = signature_expr - mean_val

            cell_type_scores[cell_type] = signature_expr.values
            signatures_used[cell_type] = {
                "markers_requested": marker_genes,
                "markers_available": available_genes,
                "markers_used": len(available_genes)
            }

        scores_df = pd.DataFrame(cell_type_scores, index=expr_data_genes.index)

        summary_stats = {}
        for cell_type in scores_df.columns:
            scores = scores_df[cell_type].values
            summary_stats[cell_type] = {
                "mean": float(scores.mean()),
                "median": float(np.median(scores)),
                "std": float(scores.std()),
                "min": float(scores.min()),
                "max": float(scores.max()),
                "markers_used": signatures_used[cell_type]["markers_used"]
            }

        dominant_cell_types = scores_df.idxmax(axis=1).value_counts()

        response = {
            "status": "success",
            "spots_analyzed": int(len(expr_data_genes)),
            "cell_types": [str(ct) for ct in signatures.keys()],
            "num_cell_types": int(len(signatures)),
            "normalized": bool(normalize),
            "summary_statistics": summary_stats,
            "dominant_cell_type_distribution": {
                str(cell_type): int(count)
                for cell_type, count in dominant_cell_types.items()
            },
            "mode": "real_analysis"
        }

        if include_spot_scores:
            spot_scores = []
            for spot_id in scores_df.index:
                spot_dict = {"spot_id": str(spot_id)}
                for cell_type in scores_df.columns:
                    spot_dict[str(cell_type)] = round(float(scores_df.loc[spot_id, cell_type]), 4)
                spot_scores.append(spot_dict)
            response["spot_scores"] = spot_scores
            response["warning"] = f"Returning {len(spot_scores)} spot-level scores. For large datasets, consider using summary_statistics instead."
        else:
            response["note"] = "Spot-level scores excluded for token efficiency. Set include_spot_scores=True to include them."

        response["signatures_used"] = signatures_used

        return response

    except Exception as e:
        logger.error(f"Error performing cell type deconvolution: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to perform cell type deconvolution"
        }
