"""MCP server for multi-omics PDX data analysis.

Provides tools for:
- Multi-omics data integration (RNA, Protein, Phosphorylation)
- Data quality validation and preprocessing
- HAllA association testing
- Stouffer's meta-analysis for p-value combination
- Multi-omics visualizations
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .config import config

# Import cost tracking utilities
# In container: /app/shared/utils is in PYTHONPATH
# In development: Try to add shared/utils to path
try:
    from cost_tracking import CostTracker, CostEstimator
except ImportError:
    # Development mode - add shared/utils to path
    _shared_utils_path = Path(__file__).resolve().parents[4] / "shared" / "utils"
    if str(_shared_utils_path) not in sys.path:
        sys.path.insert(0, str(_shared_utils_path))
    from cost_tracking import CostTracker, CostEstimator

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
from common.transport import run_server as _run_server
from .tools.integration import integrate_omics_data_impl
from .tools.stouffer import calculate_stouffer_meta_impl
from .tools.preprocessing import (
    validate_multiomics_data_impl,
    preprocess_multiomics_data_impl,
    visualize_data_quality_impl,
)
from .tools.halla import run_halla_analysis_impl
from .tools.upstream_regulators import predict_upstream_regulators_impl
from .tools.visualization import create_multiomics_heatmap_impl, run_multiomics_pca_impl

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("multiomics")


# DRY_RUN warning wrapper
def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=config.dry_run, env_var="MULTIOMICS_DRY_RUN")


# Research Use Only disclaimer
def add_research_disclaimer(result: Any, analysis_type: str = "analysis") -> Any:
    """Add research use disclaimer to results."""
    disclaimer = f"""
⚠️  RESEARCH USE ONLY - NOT FOR CLINICAL DECISION-MAKING ⚠️

This {analysis_type} is provided for RESEARCH PURPOSES ONLY and has not been
clinically validated. Results should NOT be used for:
  • Patient diagnosis
  • Treatment selection
  • Clinical decision-making

All findings must be:
  1. Reviewed by qualified bioinformatics personnel
  2. Validated with orthogonal methods (e.g., qPCR, Western blot)
  3. Interpreted by board-certified oncologist before any clinical consideration

═══════════════════════════════════════════════════════════════════════════
"""

    if isinstance(result, dict):
        result["_DISCLAIMER"] = "RESEARCH USE ONLY - NOT FOR CLINICAL USE"
        result["_research_disclaimer"] = disclaimer.strip()
    elif isinstance(result, str):
        result = disclaimer + "\n" + result

    return result


# ============================================================================
# TOOLS
# ============================================================================


@mcp.tool()
def integrate_omics_data(
    rna_path: str,
    protein_path: Optional[str] = None,
    phospho_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
    normalize: bool = True,
    filter_missing: float = 0.5,
) -> Dict[str, Any]:
    """Integrate multi-omics data from RNA, protein, and phosphorylation datasets.

    Aligns samples across modalities, handles missing data, and performs normalization.

    Args:
        rna_path: Path to RNA expression data (CSV or TSV, genes x samples)
        protein_path: Path to protein abundance data (optional)
        phospho_path: Path to phosphorylation data (optional)
        metadata_path: Path to sample metadata (optional, must include 'Sample' column)
        normalize: Apply Z-score normalization within each modality
        filter_missing: Remove features with >X fraction missing (0.0-1.0)

    Returns:
        Dictionary with:
        - integrated_data: Aligned data matrices per modality
        - common_samples: List of samples present in all modalities
        - feature_counts: Number of features per modality
        - metadata: Sample metadata if provided
        - qc_metrics: Quality control statistics

    Example:
        ```
        result = integrate_omics_data(
            rna_path="/data/rna_fpkm.csv",
            protein_path="/data/protein_tmt.csv",
            phospho_path="/data/phospho.csv",
            metadata_path="/data/metadata.csv",
            normalize=True,
            filter_missing=0.5
        )
        # Returns aligned data for 15 samples across 3 modalities
        ```
    """
    logger.info(f"integrate_omics_data called with rna_path={rna_path}")

    if config.dry_run:
        # Mock response for testing
        return add_dry_run_warning({
            "integrated_data": {
                "rna": {"shape": [1000, 15], "path": rna_path},
                "protein": {"shape": [500, 15], "path": protein_path} if protein_path else None,
                "phospho": {"shape": [300, 15], "path": phospho_path} if phospho_path else None,
            },
            "common_samples": [f"Sample_{i:02d}" for i in range(1, 16)],
            "feature_counts": {
                "rna": 1000,
                "protein": 500 if protein_path else 0,
                "phospho": 300 if phospho_path else 0,
            },
            "metadata": {
                "samples": 15,
                "treatment_resistant": 7,
                "treatment_sensitive": 8,
            } if metadata_path else None,
            "qc_metrics": {
                "normalization": "z-score" if normalize else "none",
                "missing_threshold": filter_missing,
                "samples_filtered": 0,
                "features_filtered": {"rna": 50, "protein": 20, "phospho": 15},
            },
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = integrate_omics_data_impl(
        rna_path=rna_path,
        protein_path=protein_path,
        phospho_path=phospho_path,
        metadata_path=metadata_path,
        normalize=normalize,
        filter_missing=filter_missing,
    )
    return add_research_disclaimer(result, "multi-omics data integration")


@mcp.tool()
def validate_multiomics_data(
    rna_path: str,
    protein_path: Optional[str] = None,
    phospho_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate multi-omics data quality and consistency before integration.

    Performs comprehensive quality checks including sample name consistency,
    missing value patterns, batch effect detection, and outlier identification.
    Critical first step recommended by bioinformaticians before any analysis.

    Args:
        rna_path: Path to RNA expression data (CSV or TSV, genes x samples)
        protein_path: Path to protein abundance data (optional)
        phospho_path: Path to phosphorylation data (optional)
        metadata_path: Path to sample metadata (optional, must include 'Sample' and 'Batch' columns)

    Returns:
        Dictionary with:
        - validation_status: Overall pass/fail/warning status
        - sample_overlap: Sample name consistency across modalities
        - missing_patterns: Missing value analysis per modality
        - batch_effects: Batch effect detection results
        - outliers: Outlier samples identified
        - warnings: List of validation warnings
        - recommendations: Suggested preprocessing steps

    Example:
        ```
        result = validate_multiomics_data(
            rna_path="/data/rna.csv",
            protein_path="/data/protein.csv",
            phospho_path="/data/phospho.csv",
            metadata_path="/data/metadata.csv"
        )
        # Returns validation report with batch effect warnings for proteomics
        ```
    """
    logger.info(f"validate_multiomics_data called with rna_path={rna_path}")

    if config.dry_run:
        # Mock response for testing
        return add_dry_run_warning({
            "validation_status": "warning",
            "sample_overlap": {
                "rna_samples": 15,
                "protein_samples": 15 if protein_path else 0,
                "phospho_samples": 15 if phospho_path else 0,
                "common_samples": 15,
                "sample_name_issues": [
                    "Protein samples use '_' separator, RNA uses '-' separator"
                ],
            },
            "missing_patterns": {
                "rna": {"total_features": 20000, "features_with_missing": 500, "max_missing_fraction": 0.2},
                "protein": {"total_features": 7000, "features_with_missing": 2000, "max_missing_fraction": 0.4} if protein_path else None,
                "phospho": {"total_features": 5000, "features_with_missing": 1500, "max_missing_fraction": 0.35} if phospho_path else None,
            },
            "batch_effects": {
                "detected": True if metadata_path else False,
                "pc1_batch_correlation": 0.82 if metadata_path else None,
                "significance": "CRITICAL - PC1 strongly correlates with batch" if metadata_path else None,
                "batches_found": 2 if metadata_path else None,
            },
            "outliers": {
                "rna_outliers": ["Sample_07"],
                "protein_outliers": ["Sample_07", "Sample_12"] if protein_path else [],
                "method": "MAD (Median Absolute Deviation) > 3.0",
            },
            "warnings": [
                "CRITICAL: Batch effects detected in protein data (PC1 correlation: 0.82)",
                "WARNING: Sample naming inconsistency between modalities",
                "WARNING: High missing value fraction in protein data (40%)",
                "INFO: 2 outlier samples detected",
            ],
            "recommendations": [
                "1. Harmonize sample names before integration",
                "2. Apply batch correction to protein data (critical)",
                "3. Use KNN imputation for missing values",
                "4. Consider removing outlier samples: Sample_07, Sample_12",
            ],
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = validate_multiomics_data_impl(
        rna_path=rna_path,
        protein_path=protein_path,
        phospho_path=phospho_path,
        metadata_path=metadata_path,
    )

    return add_research_disclaimer(result, "analysis")


@mcp.tool()
def preprocess_multiomics_data(
    rna_path: str,
    protein_path: Optional[str] = None,
    phospho_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
    normalize_method: str = "quantile",
    batch_correction: bool = True,
    imputation_method: str = "knn",
    outlier_threshold: float = 3.0,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Preprocess multi-omics data with normalization, batch correction, and imputation.

    Comprehensive preprocessing pipeline addressing real-world proteomics challenges
    including batch effects, missing values, and sample name harmonization. Based on
    bioinformatician feedback from clinical PDX studies.

    Args:
        rna_path: Path to RNA expression data (CSV or TSV)
        protein_path: Path to protein abundance data (optional)
        phospho_path: Path to phosphorylation data (optional)
        metadata_path: Path to sample metadata with 'Batch' column (required for batch correction)
        normalize_method: Normalization method - "quantile", "median", "tmm", or "zscore" (default: quantile)
        batch_correction: Apply batch correction (ComBat method, default: True)
        imputation_method: Missing value imputation - "knn", "minimum", or "median" (default: knn)
        outlier_threshold: MAD threshold for outlier detection (default: 3.0)
        output_dir: Directory to save preprocessed data files

    Returns:
        Dictionary with:
        - preprocessed_paths: Paths to preprocessed data files per modality
        - preprocessing_report: Summary of transformations applied
        - qc_metrics: Before/after quality metrics
        - batch_correction_results: PCA variance explained by batch (before/after)
        - imputation_stats: Number of values imputed per modality
        - outliers_removed: List of outlier samples removed

    Example:
        ```
        result = preprocess_multiomics_data(
            rna_path="/data/rna.csv",
            protein_path="/data/protein.csv",
            metadata_path="/data/metadata.csv",
            normalize_method="quantile",
            batch_correction=True,
            imputation_method="knn",
            output_dir="/data/preprocessed"
        )
        # Returns preprocessed files with batch effects removed
        ```
    """
    logger.info(f"preprocess_multiomics_data called: normalize={normalize_method}, batch_correction={batch_correction}")

    if config.dry_run:
        # Mock response for testing
        return add_dry_run_warning({
            "preprocessed_paths": {
                "rna": f"{output_dir}/rna_preprocessed.csv" if output_dir else "/data/preprocessed/rna_preprocessed.csv",
                "protein": f"{output_dir}/protein_preprocessed.csv" if output_dir and protein_path else None,
                "phospho": f"{output_dir}/phospho_preprocessed.csv" if output_dir and phospho_path else None,
            },
            "preprocessing_report": {
                "steps_applied": [
                    "1. Sample name harmonization",
                    f"2. Missing value imputation ({imputation_method})",
                    "3. Batch correction (ComBat)" if batch_correction else "3. Batch correction (skipped)",
                    "4. Outlier removal (2 samples)",
                    f"5. Normalization ({normalize_method})",
                ],
                "total_runtime_seconds": 45.2,
            },
            "qc_metrics": {
                "before": {
                    "samples": 15,
                    "rna_features": 20000,
                    "protein_features": 7000 if protein_path else 0,
                    "missing_values": {"rna": 500, "protein": 2000},
                },
                "after": {
                    "samples": 13,  # 2 outliers removed
                    "rna_features": 20000,
                    "protein_features": 7000 if protein_path else 0,
                    "missing_values": {"rna": 0, "protein": 0},
                },
            },
            "batch_correction_results": {
                "pc1_batch_correlation_before": 0.82,
                "pc1_batch_correlation_after": 0.12,
                "improvement": "Batch effect successfully removed (0.82 → 0.12)",
                "method": "ComBat",
            } if batch_correction else None,
            "imputation_stats": {
                "rna_values_imputed": 500,
                "protein_values_imputed": 2000 if protein_path else 0,
                "phospho_values_imputed": 1500 if phospho_path else 0,
                "method": imputation_method,
            },
            "outliers_removed": ["Sample_07", "Sample_12"],
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = preprocess_multiomics_data_impl(
        rna_path=rna_path,
        protein_path=protein_path,
        phospho_path=phospho_path,
        metadata_path=metadata_path,
        normalize_method=normalize_method,
        batch_correction=batch_correction,
        imputation_method=imputation_method,
        outlier_threshold=outlier_threshold,
        output_dir=output_dir,
    )

    return add_research_disclaimer(result, "analysis")


@mcp.tool()
def visualize_data_quality(
    data_paths: Dict[str, str],
    metadata_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    compare_before_after: bool = False,
    before_data_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Generate quality control visualizations for multi-omics data.

    Creates comprehensive QC plots including PCA, correlation heatmaps, and
    missing value patterns. Essential for verifying preprocessing effectiveness,
    especially batch correction results.

    Args:
        data_paths: Dict of modality -> file path (e.g., {"rna": "/data/rna.csv", "protein": "/data/protein.csv"})
        metadata_path: Path to sample metadata (for coloring by batch, phenotype)
        output_dir: Directory to save visualization files (default: current directory)
        compare_before_after: Generate before/after comparison plots (default: False)
        before_data_paths: Dict of modality -> file path for before preprocessing (required if compare_before_after=True)

    Returns:
        Dictionary with:
        - plot_paths: Paths to generated visualization files
        - qc_summary: Quality metrics summary
        - batch_effect_assessment: PC1 correlation with batch variable
        - recommendations: Interpretation and next steps

    Example:
        ```
        result = visualize_data_quality(
            data_paths={
                "rna": "/data/rna_preprocessed.csv",
                "protein": "/data/protein_preprocessed.csv"
            },
            metadata_path="/data/metadata.csv",
            output_dir="/plots",
            compare_before_after=True,
            before_data_paths={
                "rna": "/data/rna_raw.csv",
                "protein": "/data/protein_raw.csv"
            }
        )
        # Generates PCA plots showing batch effect removal (0.82 → 0.12)
        ```
    """
    logger.info(f"visualize_data_quality called with {len(data_paths)} modalities")

    if config.dry_run:
        # Mock response for testing
        return add_dry_run_warning({
            "plot_paths": {
                "pca_plot": f"{output_dir}/pca_analysis.png" if output_dir else "/plots/pca_analysis.png",
                "correlation_heatmap": f"{output_dir}/sample_correlation.png" if output_dir else "/plots/sample_correlation.png",
                "missing_values": f"{output_dir}/missing_values.png" if output_dir else "/plots/missing_values.png",
                "before_after_comparison": f"{output_dir}/before_after_pca.png" if compare_before_after else None,
            },
            "qc_summary": {
                "total_samples": 13,
                "modalities_analyzed": list(data_paths.keys()),
                "pca_variance_pc1": 0.42,
                "pca_variance_pc2": 0.23,
                "sample_clustering": "Clear separation by treatment response",
            },
            "batch_effect_assessment": {
                "pc1_batch_correlation": 0.12,
                "status": "PASS - Batch effects minimal (r < 0.3)",
                "interpretation": "Batch correction successful. PC1 now reflects biological variation, not technical batch.",
            } if metadata_path else None,
            "recommendations": [
                "✓ Batch effects successfully removed (PC1 correlation: 0.12)",
                "✓ Sample clustering shows clear biological grouping",
                "→ Data is ready for downstream analysis (HAllA, Stouffer's)",
                "→ Proceed with integrate_omics_data tool",
            ],
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = visualize_data_quality_impl(
        data_paths=data_paths,
        metadata_path=metadata_path,
        output_dir=output_dir,
        compare_before_after=compare_before_after,
        before_data_paths=before_data_paths,
    )

    return add_research_disclaimer(result, "analysis")


@mcp.tool()
def run_halla_analysis(
    data_path: str,
    modality1: str,
    modality2: str,
    fdr_threshold: float = 0.05,
    method: str = "spearman",
    chunk_size: int = 1000,
    use_r_halla: bool = False,
) -> Dict[str, Any]:
    """Run HAllA hierarchical all-against-all association testing.

    Tests associations between features from two omics modalities using
    hierarchical clustering and statistical testing. Implements chunking
    strategy for large datasets based on bioinformatician feedback.

    **IMPORTANT**: Returns NOMINAL p-values (not FDR-corrected).
    Apply FDR correction AFTER Stouffer's meta-analysis, not before.

    Args:
        data_path: Path to integrated multi-omics data (from integrate_omics_data)
        modality1: First modality ("rna", "protein", or "phospho")
        modality2: Second modality ("rna", "protein", or "phospho")
        fdr_threshold: FDR threshold for reference only (p-values returned are NOMINAL)
        method: Correlation method - "spearman", "pearson", or "mi" (mutual information)
        chunk_size: Features per chunk (default: 1000, ~5 min/chunk vs days for full dataset)
        use_r_halla: Use R-based HAllA if available (default: False, use Python alternative)

    Returns:
        Dictionary with:
        - associations: List of feature pairs with NOMINAL p-values
        - chunks_processed: Chunking strategy information
        - clusters: Hierarchical cluster assignments
        - statistics: Summary statistics
        - nominal_p_values: Flag indicating p-values are NOMINAL
        - recommendation: "Apply FDR after Stouffer's"

    Example:
        ```
        result = run_halla_analysis(
            data_path="/workspace/cache/integrated_data.pkl",
            modality1="rna",
            modality2="protein",
            chunk_size=1000,
            method="spearman"
        )
        # Returns associations with NOMINAL p-values for Stouffer's meta-analysis
        # Full dataset: 20K RNA × 7K protein = 140M tests (would take days)
        # Chunked: 1000 features/chunk = ~5 min/chunk
        ```
    """
    logger.info(f"run_halla_analysis called: {modality1} vs {modality2}")
    logger.info(f"Chunk size: {chunk_size} features (~5 min/chunk)")
    logger.info(f"IMPORTANT: Returns NOMINAL p-values for Stouffer's meta-analysis")

    if config.dry_run:
        # Mock response
        return add_dry_run_warning({
            "associations": [
                {
                    "feature1": f"{modality1}_gene_{i}",
                    "feature2": f"{modality2}_protein_{i}",
                    "correlation": 0.75 + (i * 0.01),
                    "p_value_nominal": 0.001 / (i + 1),  # Explicitly labeled as NOMINAL
                    "chunk_id": i // chunk_size,
                }
                for i in range(1, 48)
            ],
            "chunks_processed": {
                "total_chunks": 3,
                "chunk_size": chunk_size,
                "strategy": "1000 features per chunk = ~5 min each (not days)",
            },
            "clusters": {
                "modality1_clusters": 5,
                "modality2_clusters": 4,
                "total_associations": 47,
            },
            "statistics": {
                "method": method,
                "total_associations_tested": 500000,
                "significant_associations": 47,
                "p_value_type": "NOMINAL (FDR should be applied AFTER Stouffer's)",
            },
            "nominal_p_values": True,
            "recommendation": "Apply FDR correction after Stouffer's meta-analysis, not before",
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = run_halla_analysis_impl(
        data_path=data_path,
        modality1=modality1,
        modality2=modality2,
        fdr_threshold=fdr_threshold,
        method=method,
        chunk_size=chunk_size,
        use_r_halla=use_r_halla,
    )

    return add_research_disclaimer(result, "analysis")


@mcp.tool()
def calculate_stouffer_meta(
    p_values_dict: Dict[str, List[float]],
    effect_sizes_dict: Optional[Dict[str, List[float]]] = None,
    weights: Optional[Dict[str, float]] = None,
    use_directionality: bool = True,
) -> Dict[str, Any]:
    """Combine p-values across omics modalities using Stouffer's Z-score method.

    **CRITICAL WORKFLOW** (per bioinformatician feedback):
    This tool implements the CORRECT FDR timing for multi-omics meta-analysis:

    Step 1: HAllA returns NOMINAL p-values (p_value_nominal)
    Step 2: THIS TOOL combines nominal p-values → meta_p_values
    Step 3: THIS TOOL applies FDR correction → q_values

    **USE q_values (not meta_p_values) for significance calls!**

    Stouffer's method:
    1. Convert NOMINAL p-values to Z-scores (with directionality from effect sizes)
    2. Combine Z-scores using weighted average
    3. Convert back to meta p-values (still nominal)
    4. Apply Benjamini-Hochberg FDR correction → q-values

    Args:
        p_values_dict: Dict of modality -> list of NOMINAL p-values
                       (e.g., from run_halla_analysis with p_value_nominal)
        effect_sizes_dict: Dict of modality -> list of effect sizes
                          (log2FC, correlation) for directionality
        weights: Dict of modality -> weight (default: equal weights)
        use_directionality: Incorporate effect size sign into Z-scores (default: True)

    Returns:
        Dictionary with:
        - meta_p_values: Combined p-values (NOMINAL, before FDR)
        - meta_z_scores: Combined Z-scores with directionality
        - q_values: FDR-corrected p-values (USE THESE for significance)
        - significant_features: Features passing FDR threshold with details
        - statistics: Summary including workflow_confirmation
        - p_value_types: Clarifies which values are nominal vs FDR-corrected
        - recommendation: "Use q_values for significance"

    Example:
        ```
        # After running HAllA analysis (which returns NOMINAL p-values)
        result = calculate_stouffer_meta(
            p_values_dict={
                "rna": [0.001, 0.05, 0.3],      # NOMINAL p-values from HAllA
                "protein": [0.002, 0.04, 0.25],  # NOMINAL p-values from HAllA
                "phospho": [0.01, 0.06, 0.28]    # NOMINAL p-values from HAllA
            },
            effect_sizes_dict={
                "rna": [2.5, 1.2, -0.3],
                "protein": [1.8, 1.5, -0.2],
                "phospho": [1.2, 0.8, -0.4]
            },
            use_directionality=True
        )
        # Returns: meta_p_values (nominal) and q_values (FDR-corrected)
        # Use: result['q_values'] for identifying significant features
        ```
    """
    logger.info(f"calculate_stouffer_meta called with {len(p_values_dict)} modalities")

    if config.dry_run:
        # Mock response
        n_features = len(next(iter(p_values_dict.values())))
        return add_dry_run_warning({
            "meta_p_values": [0.0001, 0.02, 0.35][:n_features],
            "meta_z_scores": [3.72, 2.33, 0.93][:n_features],
            "q_values": [0.0003, 0.04, 0.7][:n_features],
            "significant_features": [
                {
                    "feature_index": 0,
                    "meta_p": 0.0001,
                    "meta_z": 3.72,
                    "q_value": 0.0003,
                    "modality_contributions": {
                        mod: p_values_dict[mod][0] for mod in p_values_dict
                    },
                },
                {
                    "feature_index": 1,
                    "meta_p": 0.02,
                    "meta_z": 2.33,
                    "q_value": 0.04,
                    "modality_contributions": {
                        mod: p_values_dict[mod][1] for mod in p_values_dict
                    },
                },
            ],
            "statistics": {
                "total_features": n_features,
                "significant_features": 2,
                "fdr_threshold": config.fdr_threshold,
                "directionality_used": use_directionality,
                "weights_used": weights is not None,
                "modalities": list(p_values_dict.keys()),
                "workflow_confirmation": {
                    "step_1": "Input NOMINAL p-values (from HAllA)",
                    "step_2": "Combined p-values using Stouffer's method",
                    "step_3": "Applied FDR correction AFTER combination",
                    "fdr_method": "Benjamini-Hochberg",
                    "note": "This is the CORRECT workflow per bioinformatician feedback",
                },
            },
            "p_value_types": {
                "meta_p_values": "NOMINAL (combined, before FDR)",
                "q_values": "FDR-CORRECTED (use these for significance)",
            },
            "recommendation": "Use q_values (not meta_p_values) for identifying significant features",
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = calculate_stouffer_meta_impl(
        p_values_dict=p_values_dict,
        effect_sizes_dict=effect_sizes_dict,
        weights=weights,
        use_directionality=use_directionality,
        fdr_threshold=config.fdr_threshold,
    )

    return add_research_disclaimer(result, "analysis")


@mcp.tool()
def create_multiomics_heatmap(
    data_path: str,
    features: Optional[List[str]] = None,
    cluster_rows: bool = True,
    cluster_cols: bool = True,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create integrated heatmap visualization across multiple omics modalities.

    Generates publication-quality heatmap with hierarchical clustering and
    annotation tracks for treatment groups and data modalities.

    Args:
        data_path: Path to integrated multi-omics data
        features: List of feature names to include (default: top significant features)
        cluster_rows: Apply hierarchical clustering to rows (features)
        cluster_cols: Apply hierarchical clustering to columns (samples)
        output_path: Path to save plot (PNG or PDF)

    Returns:
        Dictionary with:
        - plot_path: Path to saved visualization
        - cluster_info: Cluster assignments
        - figure_data: Plotly JSON for interactive plot

    Example:
        ```
        result = create_multiomics_heatmap(
            data_path="/workspace/cache/integrated_data.pkl",
            features=["TP53", "MYC", "EGFR"],
            cluster_rows=True,
            cluster_cols=True,
            output_path="/workspace/plots/heatmap.png"
        )
        ```
    """
    logger.info(f"create_multiomics_heatmap called: data_path={data_path}")

    if config.dry_run:
        return add_dry_run_warning({
            "plot_path": output_path or "/workspace/plots/multiomics_heatmap.png",
            "cluster_info": {
                "row_clusters": 4,
                "col_clusters": 2,
                "row_linkage": "complete",
                "col_linkage": "complete",
            },
            "figure_data": {
                "type": "heatmap",
                "rows": len(features) if features else 50,
                "cols": 15,
                "format": "plotly_json",
            },
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = create_multiomics_heatmap_impl(
        data_path=data_path,
        features=features,
        cluster_rows=cluster_rows,
        cluster_cols=cluster_cols,
        output_path=output_path,
    )
    return add_research_disclaimer(result, "visualization")


@mcp.tool()
def run_multiomics_pca(
    data_path: str,
    modalities: Optional[List[str]] = None,
    n_components: int = 3,
    scale_features: bool = True,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run Principal Component Analysis on integrated multi-omics data.

    Performs PCA for dimensionality reduction and sample clustering visualization.
    Can analyze individual modalities or concatenated multi-omics data.

    Args:
        data_path: Path to integrated multi-omics data
        modalities: List of modalities to include (default: all available)
        n_components: Number of principal components to compute (default: 3)
        scale_features: Apply feature scaling before PCA
        output_path: Path to save 2D and 3D PCA plots

    Returns:
        Dictionary with:
        - variance_explained: Fraction of variance per component
        - loadings: Feature loadings on each PC
        - sample_coordinates: PC coordinates for each sample
        - plot_path: Path to saved visualization

    Example:
        ```
        result = run_multiomics_pca(
            data_path="/workspace/cache/integrated_data.pkl",
            modalities=["rna", "protein"],
            n_components=3,
            output_path="/workspace/plots/pca.png"
        )
        # PC1 explains 42% variance, separates Resistant vs Sensitive
        ```
    """
    logger.info(f"run_multiomics_pca called: n_components={n_components}")

    if config.dry_run:
        return add_dry_run_warning({
            "variance_explained": [0.42, 0.23, 0.15][:n_components],
            "loadings": {
                "PC1": {"top_features": ["TP53", "MYC", "EGFR"], "n_features": 1800},
                "PC2": {"top_features": ["BRCA1", "KRAS", "AKT1"], "n_features": 1800},
                "PC3": {"top_features": ["CDK4", "CCND1", "RB1"], "n_features": 1800},
            },
            "sample_coordinates": {
                "samples": 15,
                "dimensions": n_components,
                "clustering_observed": True,
            },
            "plot_path": output_path or "/workspace/plots/multiomics_pca.png",
            "statistics": {
                "total_variance": 0.80,
                "n_features": 1800,
                "modalities_used": modalities or ["rna", "protein", "phospho"],
            },
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = run_multiomics_pca_impl(
        data_path=data_path,
        modalities=modalities,
        n_components=n_components,
        scale_features=scale_features,
        output_path=output_path,
    )
    return add_research_disclaimer(result, "analysis")


@mcp.tool()
def predict_upstream_regulators(
    differential_genes: Dict[str, Dict[str, float]],
    regulator_types: Optional[List[str]] = None,
    fdr_threshold: float = 0.05,
    activation_zscore_threshold: float = 2.0,
) -> Dict[str, Any]:
    """Predict upstream regulators from differential expression data.

    Identifies kinases, transcription factors, and drugs that may regulate
    observed expression changes. Provides similar insights to IPA's Upstream
    Regulator Analysis using enrichment-based methods.

    **Key Insights** (per bioinformatician feedback):
    - **Kinases**: Identifies activated/inhibited protein kinases regulating phosphorylation
    - **Transcription Factors**: Finds TFs driving gene expression changes
    - **Drug Responses**: Predicts compounds that could modulate observed pathways

    Method:
    1. Enrichment test (Fisher's exact) - are regulator targets enriched in DEGs?
    2. Activation Z-score - based on target expression direction
    3. FDR correction across all regulators
    4. Rank by significance and activation strength

    Args:
        differential_genes: Dict of gene -> {"log2fc": float, "p_value": float}
                           Should be significantly differential genes (e.g., from Stouffer's)
        regulator_types: List of ["kinase", "transcription_factor", "drug"]
                        (default: all types)
        fdr_threshold: FDR threshold for significant regulators (default: 0.05)
        activation_zscore_threshold: |Z-score| threshold for activation/inhibition
                                     (default: 2.0, ~p < 0.05)

    Returns:
        Dictionary with:
        - kinases: List of predicted kinases with activation state
        - transcription_factors: List of predicted TFs with activation state
        - drugs: List of predicted drug responses
        - statistics: Summary statistics (counts, methods)
        - method: Enrichment method details
        - recommendation: Top therapeutic recommendation

    Example:
        ```
        # After Stouffer's meta-analysis identified significant genes
        result = predict_upstream_regulators(
            differential_genes={
                "AKT1": {"log2fc": 2.5, "p_value": 0.0001},
                "MTOR": {"log2fc": 1.8, "p_value": 0.001},
                "TP53": {"log2fc": -2.1, "p_value": 0.0005},
                "MYC": {"log2fc": 2.3, "p_value": 0.0002},
                # ... more significant genes
            },
            regulator_types=["kinase", "transcription_factor", "drug"]
        )
        # Returns:
        # - Kinases: AKT1 (Activated, Z=3.2), MTOR (Activated, Z=2.8)
        # - TFs: TP53 (Inhibited, Z=-3.5), MYC (Activated, Z=3.1)
        # - Drugs: Alpelisib (PI3K inhibitor, targets activated pathway)
        ```
    """
    logger.info(f"predict_upstream_regulators called with {len(differential_genes)} genes")

    if config.dry_run:
        # Mock response
        return add_dry_run_warning({
            "kinases": [
                {
                    "name": "AKT1",
                    "activation_state": "Activated",
                    "z_score": 3.2,
                    "p_value": 0.0001,
                    "q_value": 0.001,
                    "targets_in_dataset": 5,
                    "targets_consistent": 4,
                },
                {
                    "name": "MTOR",
                    "activation_state": "Activated",
                    "z_score": 2.8,
                    "p_value": 0.0005,
                    "q_value": 0.003,
                    "targets_in_dataset": 4,
                    "targets_consistent": 3,
                },
                {
                    "name": "GSK3B",
                    "activation_state": "Inhibited",
                    "z_score": -2.5,
                    "p_value": 0.001,
                    "q_value": 0.005,
                    "targets_in_dataset": 4,
                    "targets_consistent": 3,
                },
            ],
            "transcription_factors": [
                {
                    "name": "TP53",
                    "activation_state": "Inhibited",
                    "z_score": -3.5,
                    "p_value": 0.00005,
                    "q_value": 0.0005,
                    "targets_in_dataset": 6,
                    "targets_consistent": 5,
                },
                {
                    "name": "MYC",
                    "activation_state": "Activated",
                    "z_score": 3.1,
                    "p_value": 0.0002,
                    "q_value": 0.002,
                    "targets_in_dataset": 5,
                    "targets_consistent": 4,
                },
            ],
            "drugs": [
                {
                    "name": "Alpelisib",
                    "prediction": "Inhibits pathway",
                    "z_score": -2.9,
                    "p_value": 0.0003,
                    "q_value": 0.002,
                    "targets_in_dataset": 4,
                    "mechanism": "PI3K inhibitor",
                },
                {
                    "name": "Everolimus",
                    "prediction": "Inhibits pathway",
                    "z_score": -2.6,
                    "p_value": 0.0008,
                    "q_value": 0.004,
                    "targets_in_dataset": 3,
                    "mechanism": "mTOR inhibitor",
                },
            ],
            "statistics": {
                "total_genes_analyzed": len(differential_genes),
                "kinases_tested": 10,
                "tfs_tested": 10,
                "drugs_tested": 8,
                "significant_kinases": 3,
                "significant_tfs": 2,
                "significant_drugs": 2,
                "method": "Fisher's exact test + activation Z-score",
                "fdr_method": "Benjamini-Hochberg",
            },
            "method": {
                "enrichment_test": "Fisher's exact test (one-sided)",
                "activation_score": "Z-score based on target expression direction",
                "interpretation": "Positive Z-score = Activated, Negative = Inhibited",
            },
            "recommendation": "Focus on Alpelisib (PI3K inhibitor) - targets activated AKT/mTOR pathway",
            "status": "success (DRY_RUN mode)",
        })

    # Real implementation
    result = predict_upstream_regulators_impl(
        differential_genes=differential_genes,
        regulator_types=regulator_types,
        fdr_threshold=fdr_threshold,
        activation_zscore_threshold=activation_zscore_threshold,
    )

    return add_research_disclaimer(result, "analysis")


# ============================================================================
# COST TRACKING & ESTIMATION
# ============================================================================


@mcp.tool()
async def estimate_analysis_cost(
    num_samples: int,
    modalities: List[str],
    include_halla: bool = False,
    include_upstream: bool = False
) -> Dict[str, Any]:
    """Estimate cost for multi-omics analysis before execution.

    Helps researchers budget for computational costs before running analysis.

    Args:
        num_samples: Number of samples to analyze
        modalities: List of modalities (e.g., ["rna", "protein", "phospho"])
        include_halla: Include HAllA association testing
        include_upstream: Include upstream regulator prediction

    Returns:
        Dictionary with cost estimates and breakdown

    Example:
        >>> cost = await estimate_analysis_cost(
        ...     num_samples=10,
        ...     modalities=["rna", "protein", "phospho"],
        ...     include_halla=True
        ... )
        >>> print(f"Estimated cost: ${cost['total_usd']:.2f}")
    """
    estimator = CostEstimator()

    # Base integration cost
    integration_cost = estimator.multiomics_integration_cost(
        num_samples=num_samples,
        num_modalities=len(modalities)
    )

    costs = {
        "integration": integration_cost,
        "preprocessing": num_samples * 0.05,  # QC + normalization
        "validation": num_samples * 0.02,  # Input validation
    }

    # Optional analyses
    if include_halla:
        # HAllA is computationally expensive
        costs["halla_analysis"] = num_samples * 0.50 * len(modalities)

    if include_upstream:
        # Upstream regulator prediction
        costs["upstream_prediction"] = 0.30  # Fixed cost per analysis

    # Compute and storage
    estimated_duration_hours = (num_samples * len(modalities)) / 100.0  # Rough estimate
    costs["compute"] = estimator.compute_cost("aws_batch_medium", estimated_duration_hours)

    estimated_size_gb = num_samples * len(modalities) * 0.1  # ~100MB per sample-modality
    costs["storage_30days"] = estimator.storage_cost(estimated_size_gb, duration_days=30)

    # Total
    total = sum(costs.values())

    # Budget recommendations
    if total < 5:
        budget_tier = "low"
        recommendation = "Suitable for exploratory analysis"
    elif total < 20:
        budget_tier = "medium"
        recommendation = "Standard multi-omics analysis"
    else:
        budget_tier = "high"
        recommendation = "Large-scale comprehensive analysis"

    return {
        "estimated_cost_usd": total,
        "breakdown": costs,
        "parameters": {
            "num_samples": num_samples,
            "modalities": modalities,
            "include_halla": include_halla,
            "include_upstream": include_upstream,
        },
        "budget_tier": budget_tier,
        "recommendation": recommendation,
        "notes": [
            "Costs are estimates based on typical analysis patterns",
            "Actual costs may vary based on data complexity",
            "Includes 30-day data caching by default",
            "Use DRY_RUN mode for testing without charges"
        ],
        "status": "success"
    }


# ============================================================================
# RESOURCES
# ============================================================================


@mcp.resource("multiomics://config")
def get_config_resource() -> str:
    """Get current server configuration and analysis parameters.

    Returns:
        Formatted configuration settings
    """
    return f"""# Multi-Omics Server Configuration

## Data Paths
- Data Directory: {config.data_dir}
- Cache Directory: {config.cache_dir}

## Analysis Parameters
- Max Features: {config.max_features}
- Min Samples: {config.min_samples}
- FDR Threshold: {config.fdr_threshold}
- Stouffer Weights: {config.stouffer_weights}

## Mode
- DRY_RUN: {config.dry_run}
- R Home: {config.r_home or 'Auto-detect'}

## Performance
- N Jobs: {config.n_jobs}
- Timeout: {config.timeout_seconds}s
"""


@mcp.resource("multiomics://example-data")
def get_example_data_resource() -> str:
    """Get information about example datasets and data format requirements.

    Returns:
        Data format specifications and example file structures
    """
    return """# Multi-Omics Data Format Requirements

## RNA Expression Data (CSV/TSV)
```
Gene,Sample_01,Sample_02,Sample_03,...
TP53,1234.5,2341.2,987.3,...
MYC,5432.1,4321.9,3210.4,...
EGFR,876.4,1023.8,1156.2,...
```

## Protein Abundance (TMT)
```
Protein,Sample_01,Sample_02,Sample_03,...
TP53,45.2,67.8,34.1,...
MYC,123.4,145.6,98.7,...
```

## Phosphorylation Data
```
Phosphosite,Sample_01,Sample_02,Sample_03,...
TP53_S15,12.3,23.4,8.7,...
AKT1_S473,89.2,102.3,76.5,...
```

## Sample Metadata
```
Sample,Treatment,Response,Batch
Sample_01,Drug_A,Resistant,1
Sample_02,Drug_A,Sensitive,1
Sample_03,Drug_B,Resistant,2
```

## Example Dataset Locations
- `/workspace/data/multiomics/example_rna.csv` (1000 genes x 15 samples)
- `/workspace/data/multiomics/example_protein.csv` (500 proteins x 15 samples)
- `/workspace/data/multiomics/example_metadata.csv` (15 samples, 2 treatment groups)
"""


# Entry point for the server
def main():
    """Run the MCP multiomics server."""
    _run_server(mcp, server_name="mcp-multiomics", dry_run=config.dry_run, env_var="MULTIOMICS_DRY_RUN")


if __name__ == "__main__":
    main()
