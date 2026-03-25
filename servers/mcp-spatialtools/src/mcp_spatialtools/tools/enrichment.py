"""Pathway enrichment analysis tools."""

import logging
from typing import Any, Dict, List, Optional

from scipy.stats import fisher_exact

logger = logging.getLogger(__name__)


# Ovarian cancer-relevant pathway databases
# Based on KEGG, Hallmark (MSigDB), and GO Biological Process

OVARIAN_CANCER_PATHWAYS = {
    "KEGG": {
        "hsa05200": {
            "name": "Pathways in cancer",
            "genes": ["TP53", "PIK3CA", "PTEN", "AKT1", "AKT2", "MTOR", "KRAS", "NRAS",
                     "EGFR", "ERBB2", "MYC", "CCND1", "CCNE1", "CDK4", "CDK6", "RB1",
                     "BRCA1", "BRCA2", "VEGFA", "VEGFR2", "BCL2", "BCL2L1", "BAX"]
        },
        "hsa04151": {
            "name": "PI3K-Akt signaling pathway",
            "genes": ["PIK3CA", "PIK3CB", "PIK3R1", "AKT1", "AKT2", "AKT3", "MTOR",
                     "RPS6KB1", "PTEN", "PDK1", "TSC1", "TSC2", "FOXO3", "BCL2L1",
                     "BAD", "GSK3B", "CCND1", "MYC"]
        },
        "hsa04110": {
            "name": "Cell cycle",
            "genes": ["CCND1", "CCNE1", "CCNA2", "CCNB1", "CDK1", "CDK2", "CDK4", "CDK6",
                     "TP53", "RB1", "E2F1", "E2F3", "MYC", "PCNA", "MCM2", "MCM5", "CDKN1A", "CDKN2A"]
        },
        "hsa03030": {
            "name": "DNA replication",
            "genes": ["PCNA", "MCM2", "MCM3", "MCM4", "MCM5", "MCM6", "MCM7", "RFC1",
                     "POLD1", "POLE", "DNA2", "FEN1", "LIG1"]
        },
        "hsa03430": {
            "name": "Mismatch repair",
            "genes": ["MSH2", "MSH6", "MLH1", "PMS2", "PCNA", "RFC1", "EXO1", "POLD1", "LIG1"]
        },
        "hsa03420": {
            "name": "Nucleotide excision repair",
            "genes": ["XPA", "XPC", "ERCC1", "ERCC2", "ERCC3", "ERCC4", "ERCC5", "DDB1",
                     "DDB2", "PCNA", "RFC1", "POLD1", "LIG1"]
        },
        "hsa03440": {
            "name": "Homologous recombination",
            "genes": ["BRCA1", "BRCA2", "RAD51", "RAD52", "RAD54L", "XRCC2", "XRCC3",
                     "MRE11A", "RAD50", "NBN", "ATM", "POLD1"]
        },
        "hsa04210": {
            "name": "Apoptosis",
            "genes": ["TP53", "BAX", "BCL2", "BCL2L1", "BID", "CASP3", "CASP8", "CASP9",
                     "FADD", "FAS", "APAF1", "CYCS", "PARP1", "BAD"]
        },
        "hsa04066": {
            "name": "HIF-1 signaling pathway",
            "genes": ["HIF1A", "VEGFA", "EGLN1", "EGLN3", "VHL", "LDHA", "PFKL", "ENO1",
                     "PDK1", "EPO", "HMOX1", "NOS2", "REDD1"]
        },
        "hsa04010": {
            "name": "MAPK signaling pathway",
            "genes": ["KRAS", "NRAS", "BRAF", "RAF1", "MAP2K1", "MAP2K2", "MAPK1", "MAPK3",
                     "JUN", "FOS", "MYC", "ELK1", "TP53"]
        },
        "hsa04370": {
            "name": "VEGF signaling pathway",
            "genes": ["VEGFA", "VEGFB", "VEGFC", "KDR", "FLT1", "PIK3CA", "AKT1", "MAPK1",
                     "MAPK3", "PLA2G4A", "PTGS2", "NOS3"]
        }
    },
    "Hallmark": {
        "HALLMARK_PI3K_AKT_MTOR_SIGNALING": {
            "name": "PI3K/AKT/mTOR signaling",
            "genes": ["PIK3CA", "PIK3CB", "PIK3R1", "AKT1", "AKT2", "AKT3", "MTOR", "RPS6KB1",
                     "RPS6", "EIF4EBP1", "PTEN", "TSC1", "TSC2", "RHEB", "RPTOR", "RICTOR"]
        },
        "HALLMARK_MYC_TARGETS_V1": {
            "name": "MYC targets",
            "genes": ["MYC", "MYCN", "MAX", "E2F1", "E2F3", "CDK4", "CCND1", "CCNE1",
                     "PCNA", "MCM2", "MCM5", "MCM7", "LDHA", "PKM"]
        },
        "HALLMARK_E2F_TARGETS": {
            "name": "E2F targets (cell cycle)",
            "genes": ["E2F1", "E2F2", "E2F3", "CCNE1", "CCNE2", "CDK1", "CDK2", "PCNA",
                     "MCM2", "MCM3", "MCM4", "MCM5", "MCM6", "MCM7", "RRM2"]
        },
        "HALLMARK_G2M_CHECKPOINT": {
            "name": "G2/M checkpoint",
            "genes": ["CDK1", "CCNB1", "CCNB2", "CCNA2", "PLK1", "AURKA", "AURKB", "BUB1",
                     "BUB1B", "MAD2L1", "CDC20", "PTTG1", "TOP2A"]
        },
        "HALLMARK_APOPTOSIS": {
            "name": "Apoptosis",
            "genes": ["TP53", "BAX", "BCL2", "BCL2L1", "BID", "BIK", "CASP3", "CASP7",
                     "CASP8", "CASP9", "FAS", "FADD", "APAF1", "CYCS"]
        },
        "HALLMARK_P53_PATHWAY": {
            "name": "p53 pathway",
            "genes": ["TP53", "MDM2", "CDKN1A", "CDKN2A", "BAX", "PUMA", "NOXA", "GADD45A",
                     "BTG2", "ZMAT3", "RRM2B", "TIGAR"]
        },
        "HALLMARK_DNA_REPAIR": {
            "name": "DNA repair",
            "genes": ["BRCA1", "BRCA2", "RAD51", "XRCC1", "XRCC2", "XRCC3", "PARP1", "PARP2",
                     "ERCC1", "ERCC2", "XPA", "MSH2", "MLH1", "ATM", "ATR"]
        },
        "HALLMARK_HYPOXIA": {
            "name": "Hypoxia",
            "genes": ["HIF1A", "VEGFA", "LDHA", "PDK1", "BNIP3", "BNIP3L", "SLC2A1", "ENO1",
                     "PFKL", "ALDOA", "PGK1", "EGLN1", "EGLN3", "VHL"]
        },
        "HALLMARK_ANGIOGENESIS": {
            "name": "Angiogenesis",
            "genes": ["VEGFA", "VEGFB", "VEGFC", "KDR", "FLT1", "ANGPT1", "ANGPT2", "TEK",
                     "PDGFA", "PDGFB", "FGF2", "HIF1A", "NRP1"]
        },
        "HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION": {
            "name": "Epithelial-mesenchymal transition (EMT)",
            "genes": ["VIM", "SNAI1", "SNAI2", "TWIST1", "TWIST2", "ZEB1", "ZEB2", "CDH1",
                     "CDH2", "FN1", "MMP2", "MMP9", "TGFB1"]
        },
        "HALLMARK_INFLAMMATORY_RESPONSE": {
            "name": "Inflammatory response",
            "genes": ["IL6", "IL1B", "TNF", "NFKB1", "RELA", "CXCL8", "CCL2", "PTGS2",
                     "ICAM1", "VCAM1", "SELE", "IRF1"]
        },
        "HALLMARK_INTERFERON_GAMMA_RESPONSE": {
            "name": "Interferon gamma response",
            "genes": ["IFNG", "STAT1", "IRF1", "TAP1", "TAP2", "HLA-A", "HLA-B", "HLA-C",
                     "B2M", "CXCL9", "CXCL10", "CXCL11", "IDO1"]
        }
    },
    "GO_BP": {
        "GO:0006281": {
            "name": "DNA repair",
            "genes": ["BRCA1", "BRCA2", "RAD51", "XRCC1", "XRCC2", "PARP1", "ERCC1", "XPA",
                     "MSH2", "MLH1", "ATM", "ATR", "CHEK1", "CHEK2", "TP53BP1"]
        },
        "GO:0008283": {
            "name": "Cell proliferation",
            "genes": ["TP53", "MYC", "CCND1", "CCNE1", "CDK4", "CDK6", "RB1", "E2F1",
                     "PCNA", "Ki67", "MKI67", "TOP2A", "AURKA"]
        },
        "GO:0006974": {
            "name": "Cellular response to DNA damage stimulus",
            "genes": ["TP53", "ATM", "ATR", "BRCA1", "BRCA2", "CHEK1", "CHEK2", "RAD51",
                     "H2AFX", "TP53BP1", "MDC1", "NBN", "MRE11A", "RAD50"]
        },
        "GO:0045787": {
            "name": "Positive regulation of cell cycle",
            "genes": ["CCND1", "CCNE1", "CDK4", "CDK6", "MYC", "E2F1", "SKP2", "CDC25A",
                     "WEE1", "PLK1", "AURKA"]
        },
        "GO:0042981": {
            "name": "Regulation of apoptosis",
            "genes": ["TP53", "BCL2", "BCL2L1", "BAX", "BID", "CASP3", "CASP8", "CASP9",
                     "APAF1", "FAS", "TNFRSF10A", "TNFRSF10B", "MCL1"]
        },
        "GO:0001525": {
            "name": "Angiogenesis",
            "genes": ["VEGFA", "VEGFB", "VEGFC", "KDR", "FLT1", "ANGPT1", "ANGPT2", "TEK",
                     "FGF2", "HIF1A", "NRP1", "PDGFB", "SPHK1"]
        },
        "GO:0006954": {
            "name": "Inflammatory response",
            "genes": ["IL6", "IL1B", "TNF", "NFKB1", "RELA", "PTGS2", "CCL2", "CXCL8",
                     "ICAM1", "VCAM1", "TLR4", "MYD88"]
        },
        "GO:0030198": {
            "name": "Extracellular matrix organization",
            "genes": ["COL1A1", "COL3A1", "COL4A1", "FN1", "LAMA5", "MMP2", "MMP9", "MMP14",
                     "TIMP1", "TIMP2", "SPARC", "TNC"]
        },
        "GO:0001837": {
            "name": "Epithelial to mesenchymal transition",
            "genes": ["VIM", "SNAI1", "SNAI2", "TWIST1", "ZEB1", "ZEB2", "CDH1", "CDH2",
                     "FN1", "TGFB1", "TGFBR1", "SMAD2", "SMAD3"]
        },
        "GO:0006096": {
            "name": "Glycolysis",
            "genes": ["HK1", "HK2", "GPI", "PFKL", "PFKM", "ALDOA", "GAPDH", "PGK1", "ENO1",
                     "PKM", "LDHA", "LDHB"]
        }
    },
    "Drug_Resistance": {
        "PLATINUM_RESISTANCE": {
            "name": "Platinum resistance mechanisms",
            "genes": ["ERCC1", "XPA", "XPD", "GSTP1", "ABCB1", "ABCC1", "ABCC2", "ABCG2",
                     "BCL2L1", "BCL2", "XIAP", "SURVIVIN", "PTEN", "PIK3CA", "AKT1"]
        },
        "ABC_TRANSPORTERS": {
            "name": "ABC transporter drug efflux",
            "genes": ["ABCB1", "ABCC1", "ABCC2", "ABCC3", "ABCC4", "ABCC5", "ABCG2"]
        },
        "ANTI_APOPTOTIC": {
            "name": "Anti-apoptotic signaling",
            "genes": ["BCL2", "BCL2L1", "BCLW", "MCL1", "XIAP", "BIRC2", "BIRC3", "SURVIVIN"]
        },
        "PARP_RESISTANCE": {
            "name": "PARP inhibitor resistance",
            "genes": ["BRCA1", "BRCA2", "RAD51", "XRCC1", "PARP1", "TP53BP1", "RIF1",
                     "REV7", "SHLD1", "SHLD2", "SHLD3", "PIK3CA", "AKT1"]
        }
    }
}


async def perform_pathway_enrichment_impl(
    gene_list: List[str],
    background_genes: Optional[List[str]],
    database: str,
    p_value_cutoff: float,
    *,
    dry_run: bool,
) -> Dict[str, Any]:
    """Perform pathway enrichment analysis on gene lists."""
    if dry_run:
        pathways = [
            {
                "pathway_id": "GO:0008283",
                "pathway_name": "Cell proliferation",
                "genes_in_pathway": 450,
                "genes_overlapping": 12,
                "p_value": 0.00023,
                "p_adj": 0.0145,
                "fold_enrichment": 3.8,
                "genes": ["TP53", "BRCA1", "MYC", "CCND1"]
            },
            {
                "pathway_id": "GO:0006281",
                "pathway_name": "DNA repair",
                "genes_in_pathway": 280,
                "genes_overlapping": 8,
                "p_value": 0.00156,
                "p_adj": 0.0312,
                "fold_enrichment": 3.2,
                "genes": ["BRCA1", "BRCA2", "TP53", "ATM"]
            },
            {
                "pathway_id": "GO:0045787",
                "pathway_name": "Positive regulation of cell cycle",
                "genes_in_pathway": 195,
                "genes_overlapping": 6,
                "p_value": 0.0234,
                "p_adj": 0.0468,
                "fold_enrichment": 2.4,
                "genes": ["CCND1", "CDK4", "MYC"]
            }
        ]

        significant = [p for p in pathways if p["p_adj"] < p_value_cutoff]

        return {
            "database": database,
            "genes_analyzed": len(gene_list),
            "background_size": len(background_genes) if background_genes else 20000,
            "pathways_tested": 500,
            "pathways_enriched": len(significant),
            "p_value_cutoff": p_value_cutoff,
            "pathways": pathways,
            "top_pathway": pathways[0]["pathway_name"] if pathways else None,
            "mode": "dry_run"
        }

    # Real implementation: Fisher's exact test for pathway enrichment

    gene_list_upper = [gene.upper() for gene in gene_list]

    if background_genes is None:
        all_pathway_genes = set()
        if database in OVARIAN_CANCER_PATHWAYS:
            for pathway_info in OVARIAN_CANCER_PATHWAYS[database].values():
                all_pathway_genes.update([g.upper() for g in pathway_info["genes"]])
        background_genes_upper = list(all_pathway_genes)
    else:
        background_genes_upper = [gene.upper() for gene in background_genes]

    if database not in OVARIAN_CANCER_PATHWAYS:
        return {
            "status": "error",
            "error": f"Unknown database: {database}",
            "available_databases": list(OVARIAN_CANCER_PATHWAYS.keys())
        }

    pathways_db = OVARIAN_CANCER_PATHWAYS[database]

    enrichment_results = []

    for pathway_id, pathway_info in pathways_db.items():
        pathway_genes_upper = [g.upper() for g in pathway_info["genes"]]

        genes_in_list_and_pathway = set(gene_list_upper) & set(pathway_genes_upper)
        genes_in_list_not_pathway = set(gene_list_upper) - set(pathway_genes_upper)
        genes_in_pathway_not_list = set(pathway_genes_upper) - set(gene_list_upper)
        genes_not_in_either = set(background_genes_upper) - set(gene_list_upper) - set(pathway_genes_upper)

        a = len(genes_in_list_and_pathway)
        b = len(genes_in_pathway_not_list)
        c = len(genes_in_list_not_pathway)
        d = len(genes_not_in_either)

        if a == 0:
            continue

        contingency_table = [[a, b], [c, d]]
        try:
            _, p_value = fisher_exact(contingency_table, alternative='greater')
        except Exception as e:
            logger.warning(f"Fisher's exact test failed for {pathway_id}: {e}")
            continue

        if a + c > 0 and b + d > 0:
            fold_enrichment = (a / (a + c)) / ((a + b) / (a + b + c + d))
        else:
            fold_enrichment = 0.0

        enrichment_results.append({
            "pathway_id": pathway_id,
            "pathway_name": pathway_info["name"],
            "genes_in_pathway": len(pathway_genes_upper),
            "genes_overlapping": a,
            "overlapping_genes": sorted(list(genes_in_list_and_pathway)),
            "p_value": float(p_value),
            "fold_enrichment": round(float(fold_enrichment), 2)
        })

    enrichment_results.sort(key=lambda x: x["p_value"])

    num_tests = len(enrichment_results)
    for i, result in enumerate(enrichment_results):
        rank = i + 1
        p_adj = min(1.0, result["p_value"] * num_tests / rank)
        result["p_adj"] = round(float(p_adj), 6)

    significant_pathways = [p for p in enrichment_results if p["p_adj"] < p_value_cutoff]

    return {
        "database": database,
        "genes_analyzed": len(gene_list_upper),
        "background_size": len(background_genes_upper),
        "pathways_tested": len(pathways_db),
        "pathways_enriched": len(significant_pathways),
        "p_value_cutoff": p_value_cutoff,
        "pathways": significant_pathways[:20],
        "top_pathway": significant_pathways[0]["pathway_name"] if significant_pathways else None,
        "mode": "real_analysis"
    }
