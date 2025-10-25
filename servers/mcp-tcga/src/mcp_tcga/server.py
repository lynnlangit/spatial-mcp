"""MCP TCGA server - The Cancer Genome Atlas data integration."""

import json
import os
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
import pandas as pd
import numpy as np

mcp = FastMCP("tcga")

DRY_RUN = os.getenv("TCGA_DRY_RUN", "true").lower() == "true"


@mcp.tool()
async def query_tcga_cohorts(
    cancer_type: Optional[str] = None,
    tissue_type: Optional[str] = None,
    min_samples: int = 10
) -> Dict[str, Any]:
    """Search TCGA datasets by cancer type and tissue.

    Args:
        cancer_type: TCGA cancer type code (e.g., BRCA, LUAD, COAD)
        tissue_type: Tissue type filter (primary_tumor, metastatic, normal)
        min_samples: Minimum number of samples required

    Returns:
        Dictionary with matching TCGA cohorts and sample counts
    """
    if DRY_RUN:
        mock_cohorts = {
            "BRCA": {
                "full_name": "Breast Invasive Carcinoma",
                "primary_tumor_samples": 1097,
                "normal_samples": 113,
                "metastatic_samples": 7,
                "data_types": ["RNA-Seq", "DNA-Seq", "Methylation", "Clinical"],
                "url": "https://portal.gdc.cancer.gov/projects/TCGA-BRCA"
            },
            "LUAD": {
                "full_name": "Lung Adenocarcinoma",
                "primary_tumor_samples": 515,
                "normal_samples": 59,
                "metastatic_samples": 1,
                "data_types": ["RNA-Seq", "DNA-Seq", "Methylation", "Clinical"],
                "url": "https://portal.gdc.cancer.gov/projects/TCGA-LUAD"
            },
            "COAD": {
                "full_name": "Colon Adenocarcinoma",
                "primary_tumor_samples": 459,
                "normal_samples": 41,
                "metastatic_samples": 0,
                "data_types": ["RNA-Seq", "DNA-Seq", "Methylation", "Clinical"],
                "url": "https://portal.gdc.cancer.gov/projects/TCGA-COAD"
            }
        }

        if cancer_type:
            results = {cancer_type: mock_cohorts.get(cancer_type, {})}
        else:
            results = mock_cohorts

        # Filter by tissue type and min samples
        filtered = {}
        for code, data in results.items():
            if not data:
                continue
            sample_count = 0
            if tissue_type == "primary_tumor":
                sample_count = data.get("primary_tumor_samples", 0)
            elif tissue_type == "normal":
                sample_count = data.get("normal_samples", 0)
            elif tissue_type == "metastatic":
                sample_count = data.get("metastatic_samples", 0)
            else:
                sample_count = data.get("primary_tumor_samples", 0)

            if sample_count >= min_samples:
                filtered[code] = data

        return {
            "query": {
                "cancer_type": cancer_type,
                "tissue_type": tissue_type,
                "min_samples": min_samples
            },
            "cohorts_found": len(filtered),
            "cohorts": filtered,
            "mode": "dry_run"
        }

    return {"cohorts_found": 0, "cohorts": {}}


@mcp.tool()
async def fetch_expression_data(
    cohort: str,
    genes: List[str],
    tissue_type: str = "primary_tumor",
    normalization: str = "TPM"
) -> Dict[str, Any]:
    """Download gene expression data from TCGA.

    Args:
        cohort: TCGA cohort code (e.g., BRCA, LUAD)
        genes: List of gene symbols to retrieve
        tissue_type: Sample type (primary_tumor, normal, metastatic)
        normalization: Expression normalization (TPM, FPKM, counts)

    Returns:
        Dictionary with expression matrix and sample metadata
    """
    if DRY_RUN:
        # Generate mock expression data
        num_samples = 100 if tissue_type == "primary_tumor" else 20
        expression_data = {}

        for gene in genes:
            # Simulate realistic expression distributions
            if gene in ["EPCAM", "KRT19", "CDH1"]:  # Epithelial markers
                mean_expr = 1000 if tissue_type == "primary_tumor" else 100
            elif gene in ["VIM", "FN1", "COL1A1"]:  # Stromal markers
                mean_expr = 500 if tissue_type == "primary_tumor" else 50
            elif gene in ["CD3D", "CD8A", "PTPRC"]:  # Immune markers
                mean_expr = 300 if tissue_type == "primary_tumor" else 30
            else:
                mean_expr = 200

            expression_data[gene] = list(np.random.lognormal(
                mean=np.log(mean_expr),
                sigma=1.0,
                size=num_samples
            ).round(2))

        return {
            "cohort": cohort,
            "genes": genes,
            "tissue_type": tissue_type,
            "normalization": normalization,
            "num_samples": num_samples,
            "expression_data": expression_data,
            "sample_ids": [f"TCGA-{cohort}-{i:04d}" for i in range(num_samples)],
            "mode": "dry_run"
        }

    return {"expression_data": {}}


@mcp.tool()
async def compare_to_cohort(
    sample_expression: Dict[str, float],
    cohort: str,
    genes: List[str],
    statistical_test: str = "t_test"
) -> Dict[str, Any]:
    """Compare sample gene expression to TCGA cohort.

    Args:
        sample_expression: Dictionary of gene -> expression value for your sample
        cohort: TCGA cohort to compare against (e.g., BRCA)
        genes: Genes to compare
        statistical_test: Statistical method (t_test, wilcoxon, z_score)

    Returns:
        Dictionary with statistical comparison results
    """
    if DRY_RUN:
        comparison_results = []

        for gene in genes:
            sample_value = sample_expression.get(gene, 0)

            # Simulate cohort statistics
            cohort_mean = np.random.uniform(100, 2000)
            cohort_std = cohort_mean * 0.5

            # Calculate z-score
            z_score = (sample_value - cohort_mean) / cohort_std if cohort_std > 0 else 0

            # Determine if significantly different
            p_value = 2 * (1 - abs(z_score) / 3.0) if abs(z_score) < 3 else 0.001

            comparison_results.append({
                "gene": gene,
                "sample_expression": sample_value,
                "cohort_mean": round(cohort_mean, 2),
                "cohort_std": round(cohort_std, 2),
                "z_score": round(z_score, 3),
                "p_value": round(max(0.001, p_value), 4),
                "percentile": round(50 + z_score * 15, 1),  # Approximate percentile
                "interpretation": "higher" if z_score > 1.96 else "lower" if z_score < -1.96 else "similar"
            })

        return {
            "cohort": cohort,
            "statistical_test": statistical_test,
            "genes_compared": len(genes),
            "comparisons": comparison_results,
            "significantly_different": sum(1 for r in comparison_results if abs(r["z_score"]) > 1.96),
            "mode": "dry_run"
        }

    return {"comparisons": []}


@mcp.tool()
async def get_survival_data(
    cohort: str,
    gene: str,
    expression_threshold: Optional[float] = None,
    survival_type: str = "overall"
) -> Dict[str, Any]:
    """Retrieve survival data correlated with gene expression.

    Args:
        cohort: TCGA cohort code
        gene: Gene symbol for correlation
        expression_threshold: Split samples into high/low expression groups
        survival_type: Survival metric (overall, progression_free, disease_specific)

    Returns:
        Dictionary with survival curves and statistics
    """
    if DRY_RUN:
        # Simulate survival data
        num_samples = 100

        if expression_threshold:
            high_expr_samples = 50
            low_expr_samples = 50
        else:
            high_expr_samples = num_samples
            low_expr_samples = 0

        # Generate mock survival curves
        high_expr_survival = {
            "median_survival_months": 48.5,
            "5_year_survival_rate": 0.62,
            "num_samples": high_expr_samples,
            "num_events": int(high_expr_samples * 0.45)
        }

        low_expr_survival = {
            "median_survival_months": 32.1,
            "5_year_survival_rate": 0.38,
            "num_samples": low_expr_samples,
            "num_events": int(low_expr_samples * 0.68)
        } if expression_threshold else None

        return {
            "cohort": cohort,
            "gene": gene,
            "survival_type": survival_type,
            "expression_threshold": expression_threshold,
            "high_expression_group": high_expr_survival,
            "low_expression_group": low_expr_survival,
            "log_rank_p_value": 0.0043 if expression_threshold else None,
            "hazard_ratio": 1.82 if expression_threshold else None,
            "interpretation": f"High {gene} expression associated with better survival" if expression_threshold and high_expr_survival["median_survival_months"] > (low_expr_survival["median_survival_months"] if low_expr_survival else 0) else None,
            "mode": "dry_run"
        }

    return {"survival_data": {}}


@mcp.tool()
async def get_mutation_data(
    cohort: str,
    genes: List[str]
) -> Dict[str, Any]:
    """Retrieve mutation frequencies from TCGA cohort.

    Args:
        cohort: TCGA cohort code
        genes: List of genes to query

    Returns:
        Dictionary with mutation frequencies and types
    """
    if DRY_RUN:
        mutation_data = []

        for gene in genes:
            # Simulate realistic mutation frequencies
            if gene in ["TP53", "PIK3CA", "BRCA1", "BRCA2"]:
                mutation_freq = np.random.uniform(0.15, 0.35)
            elif gene in ["KRAS", "EGFR", "BRAF"]:
                mutation_freq = np.random.uniform(0.05, 0.20)
            else:
                mutation_freq = np.random.uniform(0.01, 0.10)

            mutation_data.append({
                "gene": gene,
                "mutation_frequency": round(mutation_freq, 3),
                "mutation_types": {
                    "missense": round(mutation_freq * 0.6, 3),
                    "nonsense": round(mutation_freq * 0.15, 3),
                    "frameshift": round(mutation_freq * 0.15, 3),
                    "splice_site": round(mutation_freq * 0.10, 3)
                },
                "num_mutated_samples": int(mutation_freq * 100),
                "total_samples": 100
            })

        return {
            "cohort": cohort,
            "genes_queried": len(genes),
            "mutation_data": mutation_data,
            "mode": "dry_run"
        }

    return {"mutation_data": []}


@mcp.resource("tcga://cohorts")
def get_tcga_cohorts_info() -> str:
    """TCGA cohort information."""
    return json.dumps({
        "resource": "tcga://cohorts",
        "description": "The Cancer Genome Atlas (TCGA) cohort catalog",
        "total_cohorts": 33,
        "total_samples": 11000,
        "data_types": [
            "RNA-Seq (gene expression)",
            "DNA-Seq (mutations, CNV)",
            "Methylation",
            "Clinical (survival, demographics)",
            "miRNA-Seq",
            "Protein expression (RPPA)"
        ],
        "major_cohorts": {
            "BRCA": "Breast Invasive Carcinoma (1097 samples)",
            "LUAD": "Lung Adenocarcinoma (515 samples)",
            "LUSC": "Lung Squamous Cell Carcinoma (501 samples)",
            "COAD": "Colon Adenocarcinoma (459 samples)",
            "PRAD": "Prostate Adenocarcinoma (498 samples)",
            "KIRC": "Kidney Renal Clear Cell Carcinoma (533 samples)"
        },
        "access": "Open access via GDC Data Portal",
        "url": "https://portal.gdc.cancer.gov/"
    }, indent=2)


@mcp.resource("tcga://brca")
def get_brca_cohort_info() -> str:
    """TCGA Breast Cancer cohort details."""
    return json.dumps({
        "resource": "tcga://brca",
        "cohort_code": "BRCA",
        "full_name": "Breast Invasive Carcinoma",
        "sample_counts": {
            "primary_tumor": 1097,
            "solid_normal": 113,
            "metastatic": 7
        },
        "subtypes": {
            "Luminal A": 231,
            "Luminal B": 127,
            "HER2-enriched": 58,
            "Basal-like": 98,
            "Normal-like": 26
        },
        "available_data": {
            "RNA-Seq": "Gene expression (TPM, FPKM, counts)",
            "DNA-Seq": "Somatic mutations, CNV",
            "Methylation": "450K array",
            "Clinical": "Survival, demographics, treatment",
            "Pathology": "Histology images, tumor grade"
        },
        "key_mutations": {
            "TP53": 0.36,
            "PIK3CA": 0.33,
            "MYC": 0.18,
            "GATA3": 0.13
        },
        "median_survival_months": 87.6,
        "5_year_survival_rate": 0.74
    }, indent=2)


def main() -> None:
    """Run the MCP TCGA server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
