"""Visualization tools: heatmaps, charts, and spatial plots."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)


async def generate_spatial_heatmap_impl(
    expression_file: str,
    coordinates_file: str,
    genes: List[str],
    output_filename: Optional[str],
    colormap: str,
    *,
    dry_run: bool,
    add_dry_run_warning: callable,
    output_dir: Path,
) -> Dict[str, Any]:
    """Generate spatial heatmaps showing gene expression overlaid on tissue coordinates."""
    if dry_run:
        return add_dry_run_warning({
            "output_file": str(output_dir / "visualizations" / "spatial_heatmap_dryrun.png"),
            "genes_plotted": genes[:6],
            "genes_not_found": [],
            "description": "DRY_RUN: Would generate spatial heatmap for " + ", ".join(genes[:6]),
            "message": "Set SPATIAL_DRY_RUN=false to generate real visualizations"
        })

    try:
        expr_data = pd.read_csv(expression_file, index_col=0)
        coord_data = pd.read_csv(coordinates_file, index_col=0)

        col_lower = {c: c.lower() for c in coord_data.columns}
        pxl_cols = [c for c, cl in col_lower.items() if 'pxl' in cl or 'pixel' in cl]
        xy_cols = [c for c, cl in col_lower.items()
                   if cl in ('x', 'y', 'x_coord', 'y_coord', 'spot_x', 'spot_y')]
        array_cols = [c for c, cl in col_lower.items()
                      if cl in ('array_row', 'array_col', 'row', 'col')]
        if len(pxl_cols) >= 2:
            x_col, y_col = pxl_cols[1], pxl_cols[0]
        elif len(xy_cols) >= 2:
            x_col, y_col = xy_cols[0], xy_cols[1]
        elif len(array_cols) >= 2:
            x_col, y_col = array_cols[1], array_cols[0]
        else:
            numeric_cols = [c for c in coord_data.columns
                           if coord_data[c].dtype in ('int64', 'float64')]
            if len(numeric_cols) >= 2:
                x_col, y_col = numeric_cols[1], numeric_cols[0]
            else:
                return {
                    "status": "error",
                    "error": f"Could not find coordinate columns. Available: {list(coord_data.columns)}"
                }

        merged = coord_data.join(expr_data, how="inner")

        genes_plotted = [g for g in genes if g in expr_data.columns]
        genes_not_found = [g for g in genes if g not in expr_data.columns]

        if not genes_plotted:
            return {
                "status": "error",
                "error": "None of the requested genes found in expression data",
                "genes_requested": genes,
                "available_genes": list(expr_data.columns[:20])
            }

        genes_to_plot = genes_plotted[:6]

        n_genes = len(genes_to_plot)
        n_cols = 3 if n_genes > 3 else n_genes
        n_rows = (n_genes + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
        if n_genes == 1:
            axes = np.array([axes])
        axes = axes.flatten()

        for idx, gene in enumerate(genes_to_plot):
            ax = axes[idx]
            scatter = ax.scatter(
                merged[x_col],
                merged[y_col],
                c=merged[gene],
                cmap=colormap,
                s=50,
                alpha=0.8,
                edgecolors='none'
            )
            ax.set_title(f'{gene} Expression', fontsize=12, fontweight='bold')
            ax.set_xlabel('X Coordinate')
            ax.set_ylabel('Y Coordinate')
            ax.set_aspect('equal')
            plt.colorbar(scatter, ax=ax, label='Expression Level')

        for idx in range(n_genes, len(axes)):
            axes[idx].axis('off')

        plt.tight_layout()

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"spatial_heatmap_{timestamp}.png"

        output_path = output_dir / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        description = f"Spatial heatmap showing expression of {len(genes_to_plot)} genes across tissue coordinates. "
        description += f"Genes plotted: {', '.join(genes_to_plot)}. "
        if genes_not_found:
            description += f"Genes not found: {', '.join(genes_not_found)}."

        return {
            "status": "success",
            "output_file": str(output_path),
            "genes_plotted": genes_to_plot,
            "genes_not_found": genes_not_found,
            "num_spots": len(merged),
            "description": description,
            "visualization_type": "spatial_heatmap",
            "colormap": colormap
        }

    except Exception as e:
        logger.error(f"Error generating spatial heatmap: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate spatial heatmap. Check file paths and formats."
        }


async def generate_gene_expression_heatmap_impl(
    expression_file: str,
    regions_file: str,
    genes: List[str],
    output_filename: Optional[str],
    colormap: str,
    *,
    dry_run: bool,
    add_dry_run_warning: callable,
    output_dir: Path,
) -> Dict[str, Any]:
    """Generate gene x region expression heatmap matrix."""
    if dry_run:
        return add_dry_run_warning({
            "output_file": str(output_dir / "visualizations" / "gene_region_heatmap_dryrun.png"),
            "genes_plotted": genes,
            "regions": ["tumor_core", "stroma", "necrotic"],
            "description": "DRY_RUN: Would generate gene x region expression heatmap",
            "message": "Set SPATIAL_DRY_RUN=false to generate real visualizations"
        })

    try:
        expr_data = pd.read_csv(expression_file, index_col=0)
        region_data = pd.read_csv(regions_file, index_col=0)

        merged = expr_data.join(region_data, how="inner")

        genes_available = [g for g in genes if g in expr_data.columns]
        if not genes_available:
            return {
                "status": "error",
                "error": "None of the requested genes found in expression data",
                "genes_requested": genes
            }

        region_col = 'region' if 'region' in merged.columns else merged.columns[-1]

        mean_expr = merged.groupby(region_col)[genes_available].mean()

        fig, ax = plt.subplots(figsize=(max(8, len(mean_expr.columns) * 0.8),
                                        max(6, len(mean_expr) * 0.5)))

        sns.heatmap(
            mean_expr.T,
            annot=True,
            fmt='.2f',
            cmap=colormap,
            cbar_kws={'label': 'Mean Expression'},
            linewidths=0.5,
            linecolor='gray',
            ax=ax
        )

        ax.set_xlabel('Tissue Region', fontsize=12, fontweight='bold')
        ax.set_ylabel('Gene', fontsize=12, fontweight='bold')
        ax.set_title('Gene Expression by Tissue Region', fontsize=14, fontweight='bold')
        plt.tight_layout()

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"gene_region_heatmap_{timestamp}.png"

        output_path = output_dir / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        regions_list = list(mean_expr.index)
        description = f"Gene expression heatmap showing mean expression of {len(genes_available)} genes across {len(regions_list)} tissue regions. "
        description += f"Genes: {', '.join(genes_available)}. "
        description += f"Regions: {', '.join(regions_list)}."

        return {
            "status": "success",
            "output_file": str(output_path),
            "genes_plotted": genes_available,
            "regions": regions_list,
            "expression_matrix": mean_expr.T.to_dict(),
            "description": description,
            "visualization_type": "gene_region_heatmap",
            "colormap": colormap
        }

    except Exception as e:
        logger.error(f"Error generating gene expression heatmap: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate gene expression heatmap. Check file paths and formats."
        }


async def generate_region_composition_chart_impl(
    regions_file: str,
    output_filename: Optional[str],
    colormap: str,
    *,
    dry_run: bool,
    add_dry_run_warning: callable,
    output_dir: Path,
) -> Dict[str, Any]:
    """Generate bar chart showing number of spots per tissue region."""
    if dry_run:
        return add_dry_run_warning({
            "output_file": str(output_dir / "visualizations" / "region_composition_dryrun.png"),
            "region_counts": {"tumor_core": 150, "stroma": 300, "necrotic": 100},
            "total_spots": 550,
            "description": "DRY_RUN: Would generate region composition bar chart",
            "message": "Set SPATIAL_DRY_RUN=false to generate real visualizations"
        })

    try:
        region_data = pd.read_csv(regions_file, index_col=0)

        region_col = 'region' if 'region' in region_data.columns else region_data.columns[0]

        region_counts = region_data[region_col].value_counts().sort_index()

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = plt.cm.get_cmap(colormap)(np.linspace(0, 1, len(region_counts)))

        bars = ax.bar(
            range(len(region_counts)),
            region_counts.values,
            color=colors,
            edgecolor='black',
            linewidth=1.5
        )

        ax.set_xticks(range(len(region_counts)))
        ax.set_xticklabels(region_counts.index, rotation=45, ha='right')
        ax.set_xlabel('Tissue Region', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Spots', fontsize=12, fontweight='bold')
        ax.set_title('Tissue Region Composition', fontsize=14, fontweight='bold')

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{int(height)}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold'
            )

        ax.grid(axis='y', alpha=0.3, linestyle='--')
        plt.tight_layout()

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"region_composition_{timestamp}.png"

        output_path = output_dir / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        total_spots = int(region_counts.sum())
        description = f"Region composition bar chart showing distribution of {total_spots} spots across {len(region_counts)} tissue regions. "
        description += "Spot counts: " + ", ".join([f"{region}={count}" for region, count in region_counts.items()])

        return {
            "status": "success",
            "output_file": str(output_path),
            "region_counts": region_counts.to_dict(),
            "total_spots": total_spots,
            "num_regions": len(region_counts),
            "description": description,
            "visualization_type": "region_composition_bar_chart",
            "colormap": colormap
        }

    except Exception as e:
        logger.error(f"Error generating region composition chart: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate region composition chart. Check file path and format."
        }


async def visualize_spatial_autocorrelation_impl(
    autocorrelation_results: Dict[str, Any],
    output_filename: Optional[str],
    top_n: int,
    *,
    dry_run: bool,
    add_dry_run_warning: callable,
    output_dir: Path,
) -> Dict[str, Any]:
    """Generate bar chart of Moran's I spatial autocorrelation statistics."""
    if dry_run:
        return add_dry_run_warning({
            "output_file": str(output_dir / "visualizations" / "morans_i_plot_dryrun.png"),
            "genes_plotted": ["Ki67", "CD8A", "VEGFA"],
            "description": "DRY_RUN: Would generate Moran's I bar chart",
            "message": "Set SPATIAL_DRY_RUN=false to generate real visualizations"
        })

    try:
        if "results" not in autocorrelation_results:
            return {
                "status": "error",
                "error": "Invalid autocorrelation_results format. Expected 'results' key.",
                "message": "Provide output from calculate_spatial_autocorrelation tool"
            }

        results = autocorrelation_results["results"]

        df = pd.DataFrame(results)

        df = df[df.get("morans_i").notna()].copy()

        if len(df) == 0:
            return {
                "status": "error",
                "error": "No valid Moran's I results found",
                "message": "All genes may be missing from expression data"
            }

        df['abs_morans_i'] = df['morans_i'].abs()
        df = df.sort_values('abs_morans_i', ascending=False).head(top_n)

        fig, ax = plt.subplots(figsize=(10, max(6, len(df) * 0.4)))

        colors = ['#d62728' if x < 0 else '#2ca02c' for x in df['morans_i']]

        bars = ax.barh(range(len(df)), df['morans_i'], color=colors, edgecolor='black', linewidth=1.2)

        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df['gene'])
        ax.set_xlabel("Moran's I Statistic", fontsize=12, fontweight='bold')
        ax.set_ylabel('Gene', fontsize=12, fontweight='bold')
        ax.set_title("Spatial Autocorrelation (Moran's I)", fontsize=14, fontweight='bold')

        ax.axvline(x=0, color='black', linestyle='-', linewidth=1.5)

        for idx, (bar, value) in enumerate(zip(bars, df['morans_i'])):
            x_pos = value + (0.02 if value > 0 else -0.02)
            ha = 'left' if value > 0 else 'right'
            ax.text(
                x_pos,
                bar.get_y() + bar.get_height() / 2.,
                f'{value:.3f}',
                ha=ha,
                va='center',
                fontsize=9,
                fontweight='bold'
            )

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ca02c', edgecolor='black', label='Clustered (I > 0)'),
            Patch(facecolor='#d62728', edgecolor='black', label='Dispersed (I < 0)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        ax.grid(axis='x', alpha=0.3, linestyle='--')
        plt.tight_layout()

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        if output_filename is None:
            output_filename = f"morans_i_plot_{timestamp}.png"

        output_path = output_dir / "visualizations" / output_filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        genes_plotted = df['gene'].tolist()
        clustered_genes = df[df['morans_i'] > 0.3]['gene'].tolist()
        dispersed_genes = df[df['morans_i'] < -0.3]['gene'].tolist()

        description = f"Moran's I spatial autocorrelation plot showing top {len(genes_plotted)} genes. "
        if clustered_genes:
            description += f"Significantly clustered: {', '.join(clustered_genes)}. "
        if dispersed_genes:
            description += f"Significantly dispersed: {', '.join(dispersed_genes)}."

        return {
            "status": "success",
            "output_file": str(output_path),
            "genes_plotted": genes_plotted,
            "num_genes": len(genes_plotted),
            "description": description,
            "visualization_type": "morans_i_bar_chart"
        }

    except Exception as e:
        logger.error(f"Error visualizing spatial autocorrelation: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to visualize spatial autocorrelation. Check input format."
        }
