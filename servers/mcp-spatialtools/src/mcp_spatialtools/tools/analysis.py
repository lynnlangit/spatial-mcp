"""Analysis tools: spatial autocorrelation, differential expression, batch correction."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import norm, fisher_exact

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Moran's I helpers
# ---------------------------------------------------------------------------

def _calculate_morans_i(
    expression_values: np.ndarray,
    coordinates: np.ndarray,
    distance_threshold: float = 100.0
) -> tuple[float, float, float]:
    """Calculate Moran's I statistic for spatial autocorrelation.

    Args:
        expression_values: Gene expression values (1D array)
        coordinates: Spatial coordinates (Nx2 array)
        distance_threshold: Maximum distance for neighbors

    Returns:
        Tuple of (morans_i, z_score, p_value)
    """
    n = len(expression_values)

    if n == 0:
        return 0.0, 0.0, 1.0

    distances = cdist(coordinates, coordinates)
    weights = (distances < distance_threshold).astype(float)
    np.fill_diagonal(weights, 0)

    row_sums = weights.sum(axis=1)
    row_sums[row_sums == 0] = 1
    weights = weights / row_sums[:, np.newaxis]

    mean_expr = expression_values.mean()
    deviations = expression_values - mean_expr

    numerator = np.sum(weights * np.outer(deviations, deviations))
    denominator = np.sum(deviations ** 2)

    if denominator == 0:
        return 0.0, 0.0, 1.0

    morans_i = (n / weights.sum()) * (numerator / denominator)

    W = weights.sum()
    E_I = -1.0 / (n - 1)

    S1 = 0.5 * np.sum((weights + weights.T) ** 2)
    S2 = np.sum((weights.sum(axis=1) + weights.sum(axis=0)) ** 2)

    var_I = ((n * S1 - S2 + 3 * W ** 2) / (W ** 2 * (n ** 2 - 1))) - E_I ** 2

    if var_I <= 0:
        return float(morans_i), 0.0, 1.0

    z_score = (morans_i - E_I) / np.sqrt(var_I)
    p_value = 2 * (1 - norm.cdf(abs(z_score)))

    return float(morans_i), float(z_score), float(p_value)


async def calculate_spatial_autocorrelation_impl(
    expression_file: str,
    genes: List[str],
    coordinates_file: Optional[str],
    method: str,
    distance_threshold: float,
    *,
    dry_run: bool,
    add_dry_run_warning: callable,
) -> Dict[str, Any]:
    """Calculate spatial autocorrelation statistics for gene expression."""
    if dry_run:
        return add_dry_run_warning({
            "method": method,
            "genes_analyzed": 0,
            "results": [],
            "message": "DRY_RUN mode enabled. Set SPATIAL_DRY_RUN=false for real analysis."
        })

    try:
        expr_data = pd.read_csv(expression_file, index_col=0)

        if coordinates_file:
            coord_data = pd.read_csv(coordinates_file, index_col=0)
            col_lower = {c: c.lower() for c in coord_data.columns}
            pxl_cols = [c for c, cl in col_lower.items() if 'pxl' in cl or 'pixel' in cl]
            xy_cols = [c for c, cl in col_lower.items() if 'x' in cl or 'y' in cl]
            array_cols = [c for c, cl in col_lower.items() if cl in ('array_row', 'array_col', 'row', 'col')]
            if len(pxl_cols) >= 2:
                coord_cols = pxl_cols[:2]
            elif len(xy_cols) >= 2:
                coord_cols = xy_cols[:2]
            elif len(array_cols) >= 2:
                coord_cols = array_cols[:2]
            else:
                numeric_cols = [c for c in coord_data.columns if coord_data[c].dtype in ('int64', 'float64')]
                coord_cols = numeric_cols[:2] if len(numeric_cols) >= 2 else coord_data.columns[:2]
            coordinates = coord_data[coord_cols].values
            coord_range = coordinates.max() - coordinates.min()
            if distance_threshold == 100.0 and coord_range.max() > 500:
                distance_threshold = coord_range.max() * 0.15
                logger.info(f"Auto-adjusted distance_threshold to {distance_threshold:.0f} for pixel coordinates")
        elif 'x_coord' in expr_data.columns and 'y_coord' in expr_data.columns:
            coordinates = expr_data[['x_coord', 'y_coord']].values
            expr_data = expr_data.drop(['x_coord', 'y_coord'], axis=1)
        else:
            return {
                "status": "error",
                "error": "No spatial coordinates found",
                "message": "Provide coordinates_file or include x_coord/y_coord in expression file"
            }

        autocorr_results = []

        for gene in genes:
            if gene not in expr_data.columns:
                autocorr_results.append({
                    "gene": gene,
                    "status": "not_found",
                    "message": f"Gene {gene} not found in expression data"
                })
                continue

            expression_values = expr_data[gene].values

            morans_i, z_score, p_value = _calculate_morans_i(
                expression_values,
                coordinates,
                distance_threshold
            )

            if p_value < 0.05:
                if morans_i > 0.3:
                    interpretation = "significantly clustered"
                elif morans_i < -0.3:
                    interpretation = "significantly dispersed"
                else:
                    interpretation = "weakly patterned"
            else:
                interpretation = "random (not significant)"

            is_significant = float(p_value) < 0.05

            autocorr_results.append({
                "gene": str(gene),
                "morans_i": round(float(morans_i), 4),
                "z_score": round(float(z_score), 3),
                "p_value": round(float(p_value), 4),
                "significant": bool(is_significant),
                "interpretation": str(interpretation),
                "distance_threshold": float(distance_threshold)
            })

        significant_clustered = sum(
            1 for r in autocorr_results
            if r.get("significant") and r.get("morans_i", 0) > 0.3
        )
        significant_dispersed = sum(
            1 for r in autocorr_results
            if r.get("significant") and r.get("morans_i", 0) < -0.3
        )

        return {
            "status": "success",
            "method": method,
            "genes_analyzed": int(len([r for r in autocorr_results if "morans_i" in r])),
            "genes_not_found": int(len([r for r in autocorr_results if r.get("status") == "not_found"])),
            "distance_threshold": float(distance_threshold),
            "num_spots": int(len(coordinates)),
            "results": autocorr_results,
            "summary": {
                "significantly_clustered": int(significant_clustered),
                "significantly_dispersed": int(significant_dispersed),
                "random_pattern": int(len(autocorr_results) - significant_clustered - significant_dispersed)
            }
        }

    except Exception as e:
        logger.error(f"Error calculating spatial autocorrelation: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to calculate spatial autocorrelation. Check file paths and format."
        }


# ---------------------------------------------------------------------------
# Differential expression
# ---------------------------------------------------------------------------

async def perform_differential_expression_impl(
    expression_file: str,
    group1_samples: List[str],
    group2_samples: List[str],
    test_method: str,
    min_log_fc: float,
    *,
    dry_run: bool,
    add_dry_run_warning: callable,
) -> Dict[str, Any]:
    """Perform differential expression analysis between sample groups."""
    if dry_run:
        return add_dry_run_warning({
            "test_method": test_method,
            "results": [],
            "message": "DRY_RUN mode enabled. Set SPATIAL_DRY_RUN=false for real analysis."
        })

    try:
        from scipy.stats import mannwhitneyu, ttest_ind

        expr_data = pd.read_csv(expression_file, index_col=0)

        available_samples = set(expr_data.index)
        group1_valid = [s for s in group1_samples if s in available_samples]
        group2_valid = [s for s in group2_samples if s in available_samples]

        if not group1_valid:
            return {
                "status": "error",
                "error": "No valid samples found in group1",
                "available_samples": list(available_samples)[:10]
            }

        if not group2_valid:
            return {
                "status": "error",
                "error": "No valid samples found in group2",
                "available_samples": list(available_samples)[:10]
            }

        deg_results = []

        gene_cols = [col for col in expr_data.columns
                     if col not in ['x', 'y', 'in_tissue', 'region', 'n_reads', 'n_genes', 'mt_percent']]

        for gene in gene_cols:
            group1_expr = expr_data.loc[group1_valid, gene].values
            group2_expr = expr_data.loc[group2_valid, gene].values

            if group1_expr.sum() == 0 and group2_expr.sum() == 0:
                continue

            pseudocount = 1e-10
            mean1 = float(group1_expr.mean() + pseudocount)
            mean2 = float(group2_expr.mean() + pseudocount)
            log2_fc = float(np.log2(mean1 / mean2))
            base_mean = float((mean1 + mean2) / 2)

            try:
                if test_method == "wilcoxon":
                    stat, pval = mannwhitneyu(group1_expr, group2_expr, alternative='two-sided')
                else:
                    stat, pval = ttest_ind(group1_expr, group2_expr)

                pval = float(pval)
            except Exception:
                pval = 1.0

            deg_results.append({
                'gene': gene,
                'log2_fold_change': log2_fc,
                'base_mean': base_mean,
                'mean_group1': mean1,
                'mean_group2': mean2,
                'pvalue': pval
            })

        # FDR correction using Benjamini-Hochberg
        if deg_results:
            pvalues = np.array([r['pvalue'] for r in deg_results])

            n = len(pvalues)
            sorted_indices = np.argsort(pvalues)
            sorted_pvals = pvalues[sorted_indices]

            qvalues = np.zeros(n)
            for i in range(n):
                rank = i + 1
                qvalues[sorted_indices[i]] = min(sorted_pvals[i] * n / rank, 1.0)

            for i in range(n - 2, -1, -1):
                if qvalues[sorted_indices[i]] > qvalues[sorted_indices[i + 1]]:
                    qvalues[sorted_indices[i]] = qvalues[sorted_indices[i + 1]]

            for i, result in enumerate(deg_results):
                result['qvalue'] = float(qvalues[i])
                result['significant'] = bool(
                    qvalues[i] < 0.05 and abs(result['log2_fold_change']) >= min_log_fc
                )

        deg_results_sorted = sorted(deg_results, key=lambda x: x['pvalue'])

        significant = [r for r in deg_results_sorted if r.get('significant', False)]
        upregulated = [r for r in significant if r['log2_fold_change'] > 0]
        downregulated = [r for r in significant if r['log2_fold_change'] < 0]

        for r in deg_results_sorted:
            r['log2_fold_change'] = round(r['log2_fold_change'], 4)
            r['base_mean'] = round(r['base_mean'], 2)
            r['mean_group1'] = round(r['mean_group1'], 2)
            r['mean_group2'] = round(r['mean_group2'], 2)
            r['pvalue'] = round(r['pvalue'], 6)
            r['qvalue'] = round(r['qvalue'], 6)

        return {
            "status": "success",
            "test_method": test_method,
            "group1_size": int(len(group1_valid)),
            "group2_size": int(len(group2_valid)),
            "total_genes_tested": int(len(deg_results)),
            "significant_genes": int(len(significant)),
            "upregulated_genes": int(len(upregulated)),
            "downregulated_genes": int(len(downregulated)),
            "results": deg_results_sorted,
            "top_upregulated": sorted(upregulated, key=lambda x: x['log2_fold_change'], reverse=True)[:10],
            "top_downregulated": sorted(downregulated, key=lambda x: x['log2_fold_change'])[:10],
            "significant_results": significant,
            "mode": "real_analysis"
        }

    except Exception as e:
        logger.error(f"Error performing differential expression: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to perform differential expression analysis"
        }


# ---------------------------------------------------------------------------
# Batch correction helpers
# ---------------------------------------------------------------------------

def _calculate_batch_variance(data: np.ndarray, batch: np.ndarray) -> float:
    """Calculate variance explained by batch effects."""
    grand_mean = np.mean(data, axis=0)

    ss_total = np.sum((data - grand_mean) ** 2)

    if ss_total == 0:
        return 0.0

    ss_between = 0.0
    for b in np.unique(batch):
        batch_mask = (batch == b)
        batch_data = data[batch_mask]
        batch_mean = np.mean(batch_data, axis=0)
        n_batch = np.sum(batch_mask)
        ss_between += n_batch * np.sum((batch_mean - grand_mean) ** 2)

    variance_explained = ss_between / ss_total

    return float(variance_explained)


def _combat_batch_correction(
    data: pd.DataFrame,
    batch: np.ndarray,
    parametric: bool = True
) -> pd.DataFrame:
    """Apply ComBat batch correction algorithm."""
    dat = data.values
    n_genes, n_samples = dat.shape

    batches = np.unique(batch)
    n_batch = len(batches)

    if n_batch == 1:
        logger.warning("Only one batch detected, returning original data")
        return data

    batch_design = np.zeros((n_samples, n_batch))
    for i, b in enumerate(batches):
        batch_design[:, i] = (batch == b).astype(int)

    gene_mean = np.mean(dat, axis=1, keepdims=True)
    gene_var = np.var(dat, axis=1, keepdims=True)
    gene_var[gene_var == 0] = 1e-10

    s_data = (dat - gene_mean) / np.sqrt(gene_var)

    gamma_hat = np.zeros((n_genes, n_batch))
    delta_hat = np.zeros((n_genes, n_batch))

    for i, b in enumerate(batches):
        batch_samples = (batch == b)
        batch_data = s_data[:, batch_samples]

        gamma_hat[:, i] = np.mean(batch_data, axis=1)
        delta_hat[:, i] = np.var(batch_data, axis=1)

    if parametric:
        gamma_bar = np.mean(gamma_hat, axis=1, keepdims=True)
        tau_squared = np.var(gamma_hat, axis=1, keepdims=True)

        n_samples_per_batch = np.array([np.sum(batch == b) for b in batches])

        for i in range(n_batch):
            n_b = n_samples_per_batch[i]
            shrink_factor = tau_squared[:, 0] / (tau_squared[:, 0] + gene_var[:, 0] / n_b)
            gamma_star = shrink_factor * gamma_hat[:, i] + (1 - shrink_factor) * gamma_bar[:, 0]
            gamma_hat[:, i] = gamma_star

        pooled_var = np.mean(delta_hat, axis=1, keepdims=True)
        for i in range(n_batch):
            n_b = n_samples_per_batch[i]
            weight = n_b / (n_b + 10)
            delta_star = weight * delta_hat[:, i] + (1 - weight) * pooled_var[:, 0]
            delta_hat[:, i] = delta_star

    corrected = s_data.copy()

    for i, b in enumerate(batches):
        batch_samples = (batch == b)

        corrected[:, batch_samples] -= gamma_hat[:, i:i+1]

        scale_ratio = np.sqrt(gene_var[:, 0] / (delta_hat[:, i] + 1e-10))
        corrected[:, batch_samples] *= scale_ratio[:, np.newaxis]

    corrected = corrected * np.sqrt(gene_var) + gene_mean

    corrected_df = pd.DataFrame(
        corrected,
        index=data.index,
        columns=data.columns
    )

    return corrected_df


async def perform_batch_correction_impl(
    expression_files: List[str],
    batch_labels: List[str],
    output_file: str,
    method: str,
    *,
    dry_run: bool,
) -> Dict[str, Any]:
    """Perform batch correction across multiple samples."""
    if dry_run:
        return {
            "method": method,
            "num_batches": len(set(batch_labels)),
            "num_samples": len(expression_files),
            "output_file": output_file,
            "batch_metrics": {
                "variance_before": 0.45,
                "variance_after": 0.12,
                "variance_reduction": 0.73,
                "kbet_score_before": 0.35,
                "kbet_score_after": 0.82
            },
            "genes_corrected": 15000,
            "mode": "dry_run"
        }

    try:
        if len(expression_files) != len(batch_labels):
            return {
                "status": "error",
                "error": "Number of expression files must match number of batch labels"
            }

        if method not in ["combat"]:
            return {
                "status": "error",
                "error": f"Method '{method}' not supported. Currently only 'combat' is implemented."
            }

        expression_data = []
        sample_names = []

        for i, (file_path, batch_label) in enumerate(zip(expression_files, batch_labels)):
            try:
                expr_df = pd.read_csv(file_path, index_col=0)
                expr_df.columns = [f"{col}_{batch_label}_{i}" for col in expr_df.columns]

                expression_data.append(expr_df)
                sample_names.extend(expr_df.columns.tolist())

            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Failed to load file {file_path}: {str(e)}"
                }

        merged_data = pd.concat(expression_data, axis=1)
        merged_data = merged_data.fillna(0)

        logger.info(f"Merged data shape: {merged_data.shape} (genes x samples)")

        batch_array = []
        for i, (file_path, batch_label) in enumerate(zip(expression_files, batch_labels)):
            n_samples = expression_data[i].shape[1]
            batch_array.extend([batch_label] * n_samples)

        batch_array = np.array(batch_array)

        variance_before = _calculate_batch_variance(merged_data.T.values, batch_array)

        logger.info(f"Applying ComBat batch correction with {len(set(batch_labels))} batches...")
        corrected_data = _combat_batch_correction(merged_data, batch_array, parametric=True)

        variance_after = _calculate_batch_variance(corrected_data.T.values, batch_array)

        variance_reduction = (variance_before - variance_after) / variance_before if variance_before > 0 else 0

        corrected_data.to_csv(output_file)

        logger.info(f"Batch correction complete. Saved to: {output_file}")

        return {
            "status": "success",
            "method": method,
            "num_batches": len(set(batch_labels)),
            "num_samples": len(expression_files),
            "total_samples": len(sample_names),
            "genes_corrected": merged_data.shape[0],
            "output_file": output_file,
            "batch_metrics": {
                "variance_before": round(float(variance_before), 4),
                "variance_after": round(float(variance_after), 4),
                "variance_reduction": round(float(variance_reduction), 4)
            },
            "batches": {batch_label: batch_array.tolist().count(batch_label)
                       for batch_label in set(batch_labels)},
            "mode": "real_analysis"
        }

    except Exception as e:
        logger.error(f"Error performing batch correction: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to perform batch correction. Check file paths and formats."
        }
