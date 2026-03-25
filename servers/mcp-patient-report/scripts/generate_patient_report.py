#!/usr/bin/env python3
"""
Automated Patient Report Generator

Generates a complete clinical analysis report for spatial transcriptomics patients.
Integrates FHIR clinical data with spatial molecular analysis.

Usage:
    python generate_patient_report.py --patient-id patient-001 --output-dir ./results

Author: Claude Code
Date: December 29, 2025
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Add servers to path
sys.path.insert(0, str(Path(__file__).parent / "servers" / "mcp-spatialtools" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "servers" / "mcp-epic" / "src"))

from mcp_spatialtools.server import _calculate_morans_i


class PatientReportGenerator:
    """Generate comprehensive patient analysis reports."""

    def __init__(self, patient_id: str, output_dir: str, generate_draft: bool = False):
        self.patient_id = patient_id
        self.output_dir = Path(output_dir)
        self.patient_output_dir = self.output_dir / patient_id
        self.patient_output_dir.mkdir(parents=True, exist_ok=True)
        self.generate_draft = generate_draft

        # Data paths
        self.data_dir = Path("/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data")
        self.patient_data_dir = None

        # Results storage
        self.fhir_data = {}
        self.spatial_data = {}
        self.analysis_results = {}

    def log(self, message: str):
        """Print timestamped log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def fetch_fhir_data(self):
        """Fetch patient clinical data from GCP Healthcare API."""
        self.log("Fetching FHIR data from GCP Healthcare API...")

        try:
            import subprocess

            project_id = "precision-medicine-poc"
            region = "us-central1"

            # Get access token
            token_result = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                capture_output=True,
                text=True
            )
            token = token_result.stdout.strip()

            base_url = f"https://healthcare.googleapis.com/v1/projects/{project_id}/locations/{region}/datasets/precision-medicine-dataset/fhirStores/identified-fhir-store/fhir"

            # Fetch patient demographics
            import requests

            patient_url = f"{base_url}/Patient/{self.patient_id}"
            response = requests.get(
                patient_url,
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                patient_data = response.json()
                self.fhir_data['patient'] = patient_data

                name = patient_data['name'][0]
                self.log(f"✅ Patient: {name['given'][0]} {name['family']}")
                self.log(f"   Gender: {patient_data['gender']}, DOB: {patient_data['birthDate']}")
            else:
                self.log(f"⚠️  Could not fetch patient data (using mock data)")
                self.fhir_data['patient'] = {
                    'name': [{'given': ['Patient'], 'family': self.patient_id}],
                    'gender': 'unknown',
                    'birthDate': 'unknown'
                }

            # Fetch conditions
            conditions_url = f"{base_url}/Condition?patient={self.patient_id}"
            response = requests.get(
                conditions_url,
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                conditions = response.json()
                self.fhir_data['conditions'] = conditions.get('entry', [])
                self.log(f"✅ Conditions: {conditions.get('total', 0)} found")
            else:
                self.fhir_data['conditions'] = []

            # Fetch observations
            observations_url = f"{base_url}/Observation?patient={self.patient_id}"
            response = requests.get(
                observations_url,
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                observations = response.json()
                self.fhir_data['observations'] = observations.get('entry', [])
                self.log(f"✅ Observations: {observations.get('total', 0)} found")
            else:
                self.fhir_data['observations'] = []

            # Fetch medications
            medications_url = f"{base_url}/MedicationStatement?patient={self.patient_id}"
            response = requests.get(
                medications_url,
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                medications = response.json()
                self.fhir_data['medications'] = medications.get('entry', [])
                self.log(f"✅ Medications: {medications.get('total', 0)} found")
            else:
                self.fhir_data['medications'] = []

        except Exception as e:
            self.log(f"⚠️  FHIR data fetch failed: {e}")
            self.log("   Continuing with spatial analysis only...")

    def load_spatial_data(self):
        """Load spatial transcriptomics data."""
        self.log("Loading spatial transcriptomics data...")

        # Find patient data directory (handle different naming conventions)
        possible_dirs = [
            self.data_dir / self.patient_id.upper() / "spatial",
            self.data_dir / self.patient_id / "spatial",
        ]

        for data_dir in possible_dirs:
            if data_dir.exists():
                self.patient_data_dir = data_dir
                break

        if not self.patient_data_dir:
            raise FileNotFoundError(f"Could not find spatial data for {self.patient_id}")

        self.log(f"   Data directory: {self.patient_data_dir}")

        # Load expression data
        expr_file = self.patient_data_dir / "visium_gene_expression.csv"
        expr_data = pd.read_csv(expr_file, index_col=0).T  # Transpose to genes × spots
        self.spatial_data['expression'] = expr_data
        self.log(f"✅ Expression: {expr_data.shape[0]} genes × {expr_data.shape[1]} spots")

        # Load region annotations
        region_file = self.patient_data_dir / "visium_region_annotations.csv"
        region_data = pd.read_csv(region_file).set_index('barcode')
        self.spatial_data['regions'] = region_data
        self.log(f"✅ Regions: {len(region_data['region'].unique())} tissue regions")

        # Load coordinates
        coord_file = self.patient_data_dir / "visium_spatial_coordinates.csv"
        coord_data = pd.read_csv(coord_file).set_index('barcode')
        self.spatial_data['coordinates'] = coord_data
        self.log(f"✅ Coordinates: {len(coord_data)} spots")

        # Align data
        common_barcodes = list(
            set(expr_data.columns) &
            set(region_data.index) &
            set(coord_data.index)
        )
        common_barcodes.sort()

        self.spatial_data['expression'] = expr_data[common_barcodes]
        self.spatial_data['regions'] = region_data.loc[common_barcodes]
        self.spatial_data['coordinates'] = coord_data.loc[common_barcodes]

        self.log(f"✅ Aligned: {len(common_barcodes)} common spots")

    def perform_differential_expression(self):
        """Run differential expression analysis."""
        self.log("Running differential expression analysis (tumor_core vs stroma)...")

        expr_data = self.spatial_data['expression']
        region_data = self.spatial_data['regions']

        # Get spots for each group
        tumor_spots = region_data[region_data['region'] == 'tumor_core'].index.tolist()
        stroma_spots = region_data[region_data['region'] == 'stroma'].index.tolist()

        if len(tumor_spots) == 0 or len(stroma_spots) == 0:
            self.log("⚠️  Insufficient samples for differential expression")
            return

        self.log(f"   Comparing: {len(tumor_spots)} tumor_core vs {len(stroma_spots)} stroma spots")

        # Extract expression data
        group1_data = expr_data[tumor_spots].values
        group2_data = expr_data[stroma_spots].values

        # Perform Mann-Whitney U tests
        results = []
        genes = expr_data.index.tolist()

        for gene_idx, gene in enumerate(genes):
            gene1 = group1_data[gene_idx, :]
            gene2 = group2_data[gene_idx, :]

            try:
                statistic, p_value = stats.mannwhitneyu(gene1, gene2, alternative='two-sided')

                mean1 = np.mean(gene1)
                mean2 = np.mean(gene2)

                if mean2 > 0:
                    fold_change = mean1 / mean2
                    log2fc = np.log2(fold_change) if fold_change > 0 else -10
                else:
                    log2fc = 10 if mean1 > 0 else 0

                results.append({
                    'gene': gene,
                    'mean_tumor': mean1,
                    'mean_stroma': mean2,
                    'log2_fold_change': log2fc,
                    'p_value': p_value,
                    'statistic': statistic
                })
            except:
                results.append({
                    'gene': gene,
                    'mean_tumor': 0,
                    'mean_stroma': 0,
                    'log2_fold_change': 0,
                    'p_value': 1.0,
                    'statistic': 0
                })

        deg_df = pd.DataFrame(results)

        # Calculate FDR
        from scipy.stats import false_discovery_control
        deg_df['fdr'] = false_discovery_control(deg_df['p_value'].values)

        # Filter significant DEGs
        sig_degs = deg_df[(deg_df['fdr'] < 0.05) & (np.abs(deg_df['log2_fold_change']) > 1.0)]

        self.analysis_results['differential_expression'] = deg_df
        self.analysis_results['significant_degs'] = sig_degs

        # Save results
        output_file = self.patient_output_dir / "differential_expression.csv"
        deg_df.to_csv(output_file, index=False)

        self.log(f"✅ DEGs: {len(sig_degs)} significant (FDR < 0.05, |log2FC| > 1)")
        self.log(f"   Saved to: {output_file}")

    def calculate_spatial_autocorrelation(self):
        """Calculate spatial autocorrelation for all genes."""
        self.log("Calculating spatial autocorrelation (Moran's I)...")

        expr_data = self.spatial_data['expression']
        coord_data = self.spatial_data['coordinates']

        coordinates = coord_data[['array_row', 'array_col']].values
        genes = expr_data.index.tolist()

        results = []
        for gene in genes:
            expression_values = expr_data.loc[gene].values

            try:
                morans_i, z_score, p_value = _calculate_morans_i(
                    expression_values,
                    coordinates,
                    distance_threshold=1.5
                )

                results.append({
                    'gene': gene,
                    'morans_i': morans_i,
                    'z_score': z_score,
                    'p_value': p_value
                })
            except:
                results.append({
                    'gene': gene,
                    'morans_i': 0,
                    'z_score': 0,
                    'p_value': 1.0
                })

        spatial_df = pd.DataFrame(results)
        spatial_df = spatial_df.sort_values('morans_i', ascending=False)

        # Identify significant SVGs
        svgs = spatial_df[spatial_df['p_value'] < 0.01]

        self.analysis_results['spatial_autocorrelation'] = spatial_df
        self.analysis_results['spatially_variable_genes'] = svgs

        # Save results
        output_file = self.patient_output_dir / "spatial_autocorrelation.csv"
        spatial_df.to_csv(output_file, index=False)

        self.log(f"✅ SVGs: {len(svgs)} spatially variable genes (p < 0.01)")
        self.log(f"   Top gene: {svgs.iloc[0]['gene']} (Moran's I = {svgs.iloc[0]['morans_i']:.4f})")
        self.log(f"   Saved to: {output_file}")

    def perform_cell_deconvolution(self):
        """Perform cell type deconvolution."""
        self.log("Performing cell type deconvolution...")

        expr_data = self.spatial_data['expression']
        region_data = self.spatial_data['regions']

        # Define signatures
        signatures = {
            'fibroblasts': ['COL1A1', 'COL3A1', 'ACTA2'],
            'immune_cells': ['CD3D', 'CD8A', 'PTPRC'],
            'hypoxic': ['HIF1A', 'CA9', 'VEGFA'],
            'resistant': ['ABCB1', 'PIK3CA', 'AKT1']
        }

        # Calculate signature scores
        signature_scores = {}
        for cell_type, sig_genes in signatures.items():
            available_genes = [g for g in sig_genes if g in expr_data.index]

            if len(available_genes) > 0:
                sig_expr = expr_data.loc[available_genes]
                scores = sig_expr.mean(axis=0)
                signature_scores[cell_type] = scores

        score_df = pd.DataFrame(signature_scores)
        score_df['region'] = region_data['region'].values

        # Calculate mean scores by region
        region_means = score_df.groupby('region').mean()

        self.analysis_results['cell_deconvolution'] = score_df
        self.analysis_results['region_cell_scores'] = region_means

        # Save results
        output_file = self.patient_output_dir / "cell_deconvolution.csv"
        region_means.to_csv(output_file)

        self.log(f"✅ Cell types: {len(signature_scores)} signatures analyzed")
        self.log(f"   Saved to: {output_file}")

    def create_visualizations(self):
        """Generate all visualizations for the report."""
        self.log("Creating visualizations...")

        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['font.size'] = 10

        # Create individual plots
        self.plot_volcano()
        self.plot_spatial_heatmap()
        self.plot_cell_composition()
        self.plot_spatial_autocorrelation()
        self.plot_summary_figure()

        self.log(f"✅ Visualizations saved to: {self.patient_output_dir}")

    def plot_volcano(self):
        """Create volcano plot for differential expression."""
        if 'differential_expression' not in self.analysis_results:
            return

        deg_df = self.analysis_results['differential_expression']

        fig, ax = plt.subplots(figsize=(10, 8))

        # Prepare data
        deg_df['neg_log10_fdr'] = -np.log10(deg_df['fdr'] + 1e-300)
        deg_df['significant'] = (deg_df['fdr'] < 0.05) & (np.abs(deg_df['log2_fold_change']) > 1.0)

        # Color scheme
        colors = ['lightgray' if not sig else 'red' if log2fc > 0 else 'blue'
                  for sig, log2fc in zip(deg_df['significant'], deg_df['log2_fold_change'])]

        # Scatter plot
        ax.scatter(deg_df['log2_fold_change'], deg_df['neg_log10_fdr'],
                  c=colors, alpha=0.6, s=50, edgecolors='none')

        # Threshold lines
        ax.axhline(-np.log10(0.05), color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(-1, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(1, color='gray', linestyle='--', linewidth=1, alpha=0.5)

        # Label top genes
        sig_degs = deg_df[deg_df['significant']].sort_values('neg_log10_fdr', ascending=False).head(10)
        for _, row in sig_degs.iterrows():
            ax.text(row['log2_fold_change'], row['neg_log10_fdr'],
                   row['gene'], fontsize=8, alpha=0.7)

        # Labels
        ax.set_xlabel('log2(Fold Change)', fontsize=12)
        ax.set_ylabel('-log10(FDR)', fontsize=12)
        ax.set_title(f'Differential Expression: Tumor Core vs Stroma\n({len(sig_degs)} significant DEGs)',
                    fontsize=14, fontweight='bold')

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', label='Upregulated (tumor)'),
            Patch(facecolor='blue', label='Downregulated (tumor)'),
            Patch(facecolor='lightgray', label='Not significant')
        ]
        ax.legend(handles=legend_elements, loc='upper right')

        plt.tight_layout()
        output_file = self.patient_output_dir / "volcano_plot.png"
        plt.savefig(output_file, bbox_inches='tight')
        plt.close()

    def plot_spatial_heatmap(self):
        """Create spatial gene expression heatmaps for top genes."""
        if 'spatially_variable_genes' not in self.analysis_results:
            return

        svgs = self.analysis_results['spatially_variable_genes'].head(6)
        expr_data = self.spatial_data['expression']
        coord_data = self.spatial_data['coordinates']

        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()

        for idx, (_, row) in enumerate(svgs.iterrows()):
            gene = row['gene']
            ax = axes[idx]

            # Get expression values and coordinates
            expression = expr_data.loc[gene].values
            x = coord_data['array_col'].values
            y = coord_data['array_row'].values

            # Create scatter plot with color representing expression
            scatter = ax.scatter(x, y, c=expression, cmap='viridis',
                               s=30, alpha=0.8, edgecolors='none')

            # Colorbar
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Expression', rotation=270, labelpad=15, fontsize=9)

            # Title with Moran's I
            ax.set_title(f"{gene}\nMoran's I = {row['morans_i']:.3f}",
                        fontsize=11, fontweight='bold')
            ax.set_xlabel('Array Column', fontsize=9)
            ax.set_ylabel('Array Row', fontsize=9)
            ax.invert_yaxis()  # Invert y-axis to match Visium orientation

        plt.suptitle('Spatial Expression Patterns: Top 6 Spatially Variable Genes',
                    fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        output_file = self.patient_output_dir / "spatial_heatmap.png"
        plt.savefig(output_file, bbox_inches='tight')
        plt.close()

    def plot_cell_composition(self):
        """Create cell type composition heatmap by region."""
        if 'region_cell_scores' not in self.analysis_results:
            return

        region_scores = self.analysis_results['region_cell_scores']

        fig, ax = plt.subplots(figsize=(10, 6))

        # Create heatmap
        sns.heatmap(region_scores.T, annot=True, fmt='.1f', cmap='YlOrRd',
                   cbar_kws={'label': 'Signature Score'}, ax=ax,
                   linewidths=0.5, linecolor='white')

        ax.set_title('Cell Type Enrichment by Tissue Region',
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Tissue Region', fontsize=12)
        ax.set_ylabel('Cell Type', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)

        plt.tight_layout()
        output_file = self.patient_output_dir / "cell_composition_heatmap.png"
        plt.savefig(output_file, bbox_inches='tight')
        plt.close()

    def plot_spatial_autocorrelation(self):
        """Create bar plot of Moran's I values."""
        if 'spatially_variable_genes' not in self.analysis_results:
            return

        svgs = self.analysis_results['spatially_variable_genes'].head(15)

        fig, ax = plt.subplots(figsize=(10, 6))

        # Create bar plot
        colors = ['red' if i < 0 else 'steelblue' for i in svgs['morans_i']]
        ax.barh(range(len(svgs)), svgs['morans_i'], color=colors, alpha=0.7)

        # Labels
        ax.set_yticks(range(len(svgs)))
        ax.set_yticklabels(svgs['gene'])
        ax.set_xlabel("Moran's I", fontsize=12)
        ax.set_title("Spatial Autocorrelation: Top 15 Genes",
                    fontsize=14, fontweight='bold')
        ax.axvline(0, color='black', linestyle='-', linewidth=0.5)
        ax.grid(axis='x', alpha=0.3)

        # Annotate values
        for i, (_, row) in enumerate(svgs.iterrows()):
            ax.text(row['morans_i'] + 0.002, i, f"{row['morans_i']:.3f}",
                   va='center', fontsize=8)

        plt.tight_layout()
        output_file = self.patient_output_dir / "spatial_autocorrelation_plot.png"
        plt.savefig(output_file, bbox_inches='tight')
        plt.close()

    def plot_summary_figure(self):
        """Create multi-panel summary figure."""
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Panel 1: Top DEGs (bar plot)
        ax1 = fig.add_subplot(gs[0, :2])
        if 'significant_degs' in self.analysis_results:
            degs = self.analysis_results['significant_degs'].sort_values('log2_fold_change', ascending=False).head(10)
            colors = ['red' if x > 0 else 'blue' for x in degs['log2_fold_change']]
            ax1.barh(range(len(degs)), degs['log2_fold_change'], color=colors, alpha=0.7)
            ax1.set_yticks(range(len(degs)))
            ax1.set_yticklabels(degs['gene'])
            ax1.set_xlabel('log2(Fold Change)', fontsize=10)
            ax1.set_title('Top 10 Differentially Expressed Genes', fontsize=11, fontweight='bold')
            ax1.axvline(0, color='black', linestyle='-', linewidth=0.5)
            ax1.grid(axis='x', alpha=0.3)

        # Panel 2: Cell composition (heatmap)
        ax2 = fig.add_subplot(gs[0, 2])
        if 'region_cell_scores' in self.analysis_results:
            region_scores = self.analysis_results['region_cell_scores']
            sns.heatmap(region_scores.T, annot=False, cmap='YlOrRd', ax=ax2,
                       cbar_kws={'label': 'Score'}, linewidths=0.5)
            ax2.set_title('Cell Type Enrichment', fontsize=11, fontweight='bold')
            ax2.set_xlabel('Region', fontsize=9)
            ax2.set_ylabel('Cell Type', fontsize=9)
            plt.setp(ax2.get_xticklabels(), rotation=45, ha='right', fontsize=8)
            plt.setp(ax2.get_yticklabels(), rotation=0, fontsize=8)

        # Panel 3: Spatial patterns (top 2 genes)
        if 'spatially_variable_genes' in self.analysis_results:
            svgs = self.analysis_results['spatially_variable_genes'].head(2)
            expr_data = self.spatial_data['expression']
            coord_data = self.spatial_data['coordinates']

            for idx, (_, row) in enumerate(svgs.iterrows()):
                ax = fig.add_subplot(gs[1, idx])
                gene = row['gene']

                expression = expr_data.loc[gene].values
                x = coord_data['array_col'].values
                y = coord_data['array_row'].values

                scatter = ax.scatter(x, y, c=expression, cmap='viridis',
                                   s=20, alpha=0.8, edgecolors='none')
                plt.colorbar(scatter, ax=ax, label='Expr', pad=0.02)
                ax.set_title(f"{gene} (I={row['morans_i']:.3f})", fontsize=10, fontweight='bold')
                ax.set_xlabel('Col', fontsize=8)
                ax.set_ylabel('Row', fontsize=8)
                ax.invert_yaxis()
                ax.tick_params(labelsize=7)

        # Panel 4: Spatial autocorrelation (bar plot)
        ax4 = fig.add_subplot(gs[1, 2])
        if 'spatially_variable_genes' in self.analysis_results:
            svgs = self.analysis_results['spatially_variable_genes'].head(8)
            ax4.barh(range(len(svgs)), svgs['morans_i'], color='steelblue', alpha=0.7)
            ax4.set_yticks(range(len(svgs)))
            ax4.set_yticklabels(svgs['gene'], fontsize=8)
            ax4.set_xlabel("Moran's I", fontsize=10)
            ax4.set_title('Top Spatial Genes', fontsize=11, fontweight='bold')
            ax4.grid(axis='x', alpha=0.3)

        # Panel 5: Region distribution (pie chart)
        ax5 = fig.add_subplot(gs[2, 0])
        region_data = self.spatial_data['regions']
        region_counts = region_data['region'].value_counts()
        ax5.pie(region_counts.values, labels=region_counts.index, autopct='%1.1f%%',
               startangle=90, textprops={'fontsize': 8})
        ax5.set_title('Tissue Region Distribution', fontsize=11, fontweight='bold')

        # Panel 6: Summary statistics (text)
        ax6 = fig.add_subplot(gs[2, 1:])
        ax6.axis('off')

        summary_text = f"""
ANALYSIS SUMMARY

Dataset:
  • {self.spatial_data['expression'].shape[0]} genes analyzed
  • {self.spatial_data['expression'].shape[1]} spots profiled
  • {len(self.spatial_data['regions']['region'].unique())} tissue regions

Key Findings:
"""

        if 'significant_degs' in self.analysis_results:
            degs = self.analysis_results['significant_degs']
            upregulated = degs[degs['log2_fold_change'] > 0]
            summary_text += f"  • {len(degs)} significant DEGs ({len(upregulated)} upregulated)\n"

        if 'spatially_variable_genes' in self.analysis_results:
            svgs = self.analysis_results['spatially_variable_genes']
            summary_text += f"  • {len(svgs)} spatially variable genes (p < 0.01)\n"

        # Check for resistance markers
        if 'significant_degs' in self.analysis_results:
            degs = self.analysis_results['significant_degs']
            resistance_markers = degs[degs['gene'].isin(['ABCB1', 'PIK3CA', 'AKT1', 'MTOR'])]
            if len(resistance_markers) > 0:
                summary_text += f"  • {len(resistance_markers)} drug resistance markers detected\n"

        summary_text += f"\nPatient ID: {self.patient_id}"
        summary_text += f"\nReport Date: {datetime.now().strftime('%Y-%m-%d')}"

        ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes,
                fontsize=10, verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        # Main title
        fig.suptitle(f'Spatial Transcriptomics Analysis Report: {self.patient_id}',
                    fontsize=16, fontweight='bold', y=0.98)

        plt.savefig(self.patient_output_dir / "summary_figure.png", bbox_inches='tight')
        plt.close()

    def generate_clinical_summary(self):
        """Generate clinical interpretation summary."""
        self.log("Generating clinical summary...")

        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("CLINICAL ANALYSIS REPORT")
        summary_lines.append("=" * 80)
        summary_lines.append("")

        # Patient information
        if self.fhir_data.get('patient'):
            patient = self.fhir_data['patient']
            name = patient['name'][0]
            summary_lines.append(f"Patient: {name['given'][0]} {name['family']}")
            summary_lines.append(f"Gender: {patient.get('gender', 'unknown')}")
            summary_lines.append(f"DOB: {patient.get('birthDate', 'unknown')}")
        else:
            summary_lines.append(f"Patient ID: {self.patient_id}")

        summary_lines.append(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")

        # Clinical diagnoses
        if self.fhir_data.get('conditions'):
            summary_lines.append("DIAGNOSES:")
            for entry in self.fhir_data['conditions']:
                condition = entry['resource']
                summary_lines.append(f"  - {condition['code']['text']}")
            summary_lines.append("")

        # Medications
        if self.fhir_data.get('medications'):
            summary_lines.append("CURRENT MEDICATIONS:")
            for entry in self.fhir_data['medications']:
                med = entry['resource']
                summary_lines.append(f"  - {med['medicationCodeableConcept']['text']} ({med['status']})")
            summary_lines.append("")

        # Spatial analysis summary
        summary_lines.append("MOLECULAR ANALYSIS SUMMARY:")
        summary_lines.append("-" * 80)
        summary_lines.append("")

        # Differential expression
        if 'significant_degs' in self.analysis_results:
            degs = self.analysis_results['significant_degs']
            upregulated = degs[degs['log2_fold_change'] > 0].sort_values('log2_fold_change', ascending=False)
            downregulated = degs[degs['log2_fold_change'] < 0].sort_values('log2_fold_change')

            summary_lines.append(f"1. DIFFERENTIAL EXPRESSION (tumor_core vs stroma):")
            summary_lines.append(f"   Total DEGs: {len(degs)}")
            summary_lines.append(f"   Upregulated: {len(upregulated)}")
            summary_lines.append(f"   Downregulated: {len(downregulated)}")
            summary_lines.append("")

            if len(upregulated) > 0:
                summary_lines.append("   Top 5 upregulated genes in tumor:")
                for _, row in upregulated.head(5).iterrows():
                    summary_lines.append(f"      {row['gene']}: log2FC = {row['log2_fold_change']:.3f}, FDR = {row['fdr']:.2e}")
                summary_lines.append("")

        # Spatial patterns
        if 'spatially_variable_genes' in self.analysis_results:
            svgs = self.analysis_results['spatially_variable_genes']

            summary_lines.append(f"2. SPATIAL ORGANIZATION:")
            summary_lines.append(f"   Spatially variable genes: {len(svgs)}")
            summary_lines.append("")

            if len(svgs) > 0:
                summary_lines.append("   Top 5 spatially clustered genes:")
                for _, row in svgs.head(5).iterrows():
                    summary_lines.append(f"      {row['gene']}: Moran's I = {row['morans_i']:.4f}, p = {row['p_value']:.2e}")
                summary_lines.append("")

        # Cell composition
        if 'region_cell_scores' in self.analysis_results:
            summary_lines.append("3. TUMOR MICROENVIRONMENT:")
            summary_lines.append("   Cell type enrichment by region:")
            summary_lines.append("")

            region_scores = self.analysis_results['region_cell_scores']
            for region in region_scores.index:
                summary_lines.append(f"   {region}:")
                for cell_type in region_scores.columns:
                    score = region_scores.loc[region, cell_type]
                    summary_lines.append(f"      {cell_type}: {score:.1f}")
            summary_lines.append("")

        # Clinical implications
        summary_lines.append("CLINICAL IMPLICATIONS:")
        summary_lines.append("-" * 80)
        summary_lines.append("")

        # Check for drug resistance markers
        if 'significant_degs' in self.analysis_results:
            degs = self.analysis_results['significant_degs']
            resistance_markers = ['ABCB1', 'PIK3CA', 'AKT1', 'MTOR']
            found_markers = degs[degs['gene'].isin(resistance_markers)]

            if len(found_markers) > 0:
                summary_lines.append("Drug Resistance Markers Detected:")
                for _, row in found_markers.iterrows():
                    summary_lines.append(f"  - {row['gene']}: {row['log2_fold_change']:.2f}× fold change")
                summary_lines.append("")
                summary_lines.append("  ⚠️  Consider:")
                summary_lines.append("     - PI3K/AKT pathway inhibitors (Alpelisib, Capivasertib)")
                summary_lines.append("     - MDR reversal agents")
                summary_lines.append("")

        # Check for hypoxia
        if 'spatially_variable_genes' in self.analysis_results:
            svgs = self.analysis_results['spatially_variable_genes']
            hypoxia_genes = svgs[svgs['gene'].isin(['HIF1A', 'CA9', 'VEGFA'])]

            if len(hypoxia_genes) > 0:
                summary_lines.append("Hypoxic Regions Identified:")
                for _, row in hypoxia_genes.iterrows():
                    summary_lines.append(f"  - {row['gene']}: Moran's I = {row['morans_i']:.4f} (spatially clustered)")
                summary_lines.append("")
                summary_lines.append("  ⚠️  Consider:")
                summary_lines.append("     - Hypoxia-targeting agents (Evofosfamide, TH-302)")
                summary_lines.append("     - VEGF inhibitors (Bevacizumab)")
                summary_lines.append("")

        # Disclaimers
        summary_lines.append("=" * 80)
        summary_lines.append("DISCLAIMER:")
        summary_lines.append("This analysis is for RESEARCH PURPOSES ONLY.")
        summary_lines.append("NOT validated for clinical decision-making.")
        summary_lines.append("All treatment decisions must be made by qualified oncologists.")
        summary_lines.append("=" * 80)

        # Save summary
        summary_text = "\n".join(summary_lines)
        output_file = self.patient_output_dir / "clinical_summary.txt"
        with open(output_file, 'w') as f:
            f.write(summary_text)

        self.log(f"✅ Clinical summary saved to: {output_file}")

        # Also print to console
        print("\n")
        print(summary_text)
        print("\n")

    def save_metadata(self):
        """Save analysis metadata."""
        metadata = {
            'patient_id': self.patient_id,
            'analysis_date': datetime.now().isoformat(),
            'data_directory': str(self.patient_data_dir),
            'output_directory': str(self.patient_output_dir),
            'spatial_data': {
                'num_genes': self.spatial_data['expression'].shape[0],
                'num_spots': self.spatial_data['expression'].shape[1],
                'num_regions': len(self.spatial_data['regions']['region'].unique())
            },
            'analysis_results': {
                'num_degs': len(self.analysis_results.get('significant_degs', [])),
                'num_svgs': len(self.analysis_results.get('spatially_variable_genes', []))
            }
        }

        output_file = self.patient_output_dir / "metadata.json"
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        self.log(f"✅ Metadata saved to: {output_file}")

    # ==================================================================================
    # QUALITY CHECK METHODS (for CitL workflow)
    # ==================================================================================

    def run_quality_checks(self):
        """
        Run automated quality gates before clinician review.

        Returns:
            Dict with quality check results and flags
        """
        self.log("Running quality checks...")

        checks = {
            'sample_size_adequate': self._check_sample_sizes(),
            'fdr_thresholds_met': self._check_statistical_thresholds(),
            'data_completeness': self._check_data_completeness(),
            'consistency_cross_modal': self._check_cross_modal_consistency(),
        }

        # Collect flags from failed checks
        flags = []
        for check_name, result in checks.items():
            if not result['passed']:
                flags.append({
                    'check': check_name,
                    'severity': result['severity'],
                    'message': result['message'],
                    'recommendation': result['recommendation']
                })

        all_passed = all(c['passed'] for c in checks.values())

        self.log(f"   Quality checks: {'✅ ALL PASSED' if all_passed else f'⚠️  {len(flags)} flag(s) raised'}")

        return {
            'all_checks_passed': all_passed,
            'flags': flags,
            'timestamp': datetime.now().isoformat(),
            'checks_detail': checks
        }

    def _check_sample_sizes(self):
        """Check that each region has adequate sample size (≥30 spots)."""
        region_data = self.spatial_data.get('regions')
        if region_data is None:
            return {'passed': True, 'severity': 'info', 'message': 'No region data', 'recommendation': 'N/A'}

        region_counts = region_data['region'].value_counts()
        min_threshold = 30
        ideal_threshold = 50

        # Find regions below threshold
        small_regions = region_counts[region_counts < min_threshold]
        marginal_regions = region_counts[(region_counts >= min_threshold) & (region_counts < ideal_threshold)]

        if len(small_regions) > 0:
            # Critical: regions below minimum threshold
            region_list = ', '.join([f"{r} (n={region_counts[r]})" for r in small_regions.index])
            return {
                'passed': False,
                'severity': 'critical',
                'message': f"Regions below minimum threshold ({min_threshold} spots): {region_list}",
                'recommendation': f"Exclude regions with <{min_threshold} spots or interpret with extreme caution. Consider increasing minimum spots per region to {ideal_threshold}."
            }
        elif len(marginal_regions) > 0:
            # Warning: regions below ideal threshold but above minimum
            region_list = ', '.join([f"{r} (n={region_counts[r]})" for r in marginal_regions.index])
            return {
                'passed': False,
                'severity': 'warning',
                'message': f"Regions below ideal threshold ({ideal_threshold} spots): {region_list}",
                'recommendation': f"Prefer ≥{ideal_threshold} spots for robust statistical power. Consider excluding small regions or interpreting results with caution. Verify that FDR values are very low (< 1e-10) to compensate for smaller sample size."
            }
        else:
            return {
                'passed': True,
                'severity': 'info',
                'message': f"All regions have adequate sample sizes (≥{ideal_threshold} spots)",
                'recommendation': 'N/A'
            }

    def _check_statistical_thresholds(self):
        """Check that FDR thresholds are appropriate."""
        deg_df = self.analysis_results.get('differential_expression')
        if deg_df is None or len(deg_df) == 0:
            return {'passed': True, 'severity': 'info', 'message': 'No DEG data', 'recommendation': 'N/A'}

        sig_degs = self.analysis_results.get('significant_degs', pd.DataFrame())

        if len(sig_degs) == 0:
            return {
                'passed': False,
                'severity': 'warning',
                'message': 'No significant DEGs found (FDR < 0.05, |log2FC| > 1.0)',
                'recommendation': 'Verify that analysis parameters are appropriate. Consider lowering log2FC threshold if biologically justified, or check if sample size is adequate.'
            }

        # Check FDR distribution of significant genes
        marginal_sig = sig_degs[(sig_degs['fdr'] >= 0.01) & (sig_degs['fdr'] < 0.05)]

        if len(marginal_sig) > len(sig_degs) * 0.5:
            # More than 50% of significant genes have marginal FDR (0.01-0.05)
            return {
                'passed': False,
                'severity': 'warning',
                'message': f"{len(marginal_sig)}/{len(sig_degs)} significant DEGs have marginal FDR values (0.01-0.05)",
                'recommendation': 'Consider using stricter FDR threshold (< 0.01) for high-confidence findings. Marginal FDR values may indicate borderline statistical power or high noise.'
            }
        else:
            return {
                'passed': True,
                'severity': 'info',
                'message': f"{len(sig_degs)} significant DEGs with appropriate FDR distribution",
                'recommendation': 'N/A'
            }

    def _check_data_completeness(self):
        """Check for missing data patterns."""
        expr_data = self.spatial_data.get('expression')
        if expr_data is None:
            return {'passed': True, 'severity': 'info', 'message': 'No expression data', 'recommendation': 'N/A'}

        # Count missing values (NaN or zero)
        total_values = expr_data.size
        missing_values = expr_data.isna().sum().sum()
        zero_values = (expr_data == 0).sum().sum()

        missing_pct = (missing_values / total_values) * 100
        zero_pct = (zero_values / total_values) * 100

        # Check missing data threshold
        if missing_pct > 10:
            return {
                'passed': False,
                'severity': 'critical',
                'message': f"High missing data rate: {missing_pct:.1f}% of values are NaN",
                'recommendation': 'Missing data rate >10% indicates poor data quality. Review data preprocessing and QC. Consider imputation or excluding problematic spots/genes.'
            }
        elif missing_pct > 5:
            return {
                'passed': False,
                'severity': 'warning',
                'message': f"Moderate missing data rate: {missing_pct:.1f}% of values are NaN",
                'recommendation': 'Missing data rate 5-10% is acceptable if values were imputed using appropriate method (k-NN, MAGIC). Document imputation method in report.'
            }
        else:
            completeness_pct = 100 - missing_pct
            return {
                'passed': True,
                'severity': 'info',
                'message': f"Data completeness: {completeness_pct:.1f}% (missing: {missing_pct:.2f}%, zero: {zero_pct:.1f}%)",
                'recommendation': 'N/A'
            }

    def _check_cross_modal_consistency(self):
        """Check consistency between spatial findings and clinical data."""
        # This is a placeholder for more sophisticated multi-modal consistency checks
        # In a full implementation, this would check:
        # - Genomic findings vs protein expression (IHC)
        # - Spatial patterns vs imaging features
        # - Clinical phenotype vs molecular profile

        deg_df = self.analysis_results.get('significant_degs')
        conditions = self.fhir_data.get('conditions', [])

        if deg_df is None or len(deg_df) == 0:
            return {'passed': True, 'severity': 'info', 'message': 'No molecular data for consistency check', 'recommendation': 'N/A'}

        if len(conditions) == 0:
            return {
                'passed': True,
                'severity': 'info',
                'message': 'No clinical data available for cross-modal consistency check',
                'recommendation': 'Consider integrating FHIR clinical data for comprehensive validation'
            }

        # Simple check: Look for expected markers based on condition
        # This is a simplified example - full implementation would be more sophisticated
        condition_text = ' '.join([c['resource']['code']['text'].lower() for c in conditions])

        # Check for ovarian cancer markers if condition mentions ovarian
        if 'ovarian' in condition_text:
            expected_markers = ['TP53', 'BRCA1', 'BRCA2', 'PIK3CA']
            found_markers = [g for g in expected_markers if g in deg_df['gene'].values]

            if len(found_markers) >= 2:
                return {
                    'passed': True,
                    'severity': 'info',
                    'message': f"Molecular findings consistent with clinical diagnosis (found {len(found_markers)} expected markers: {', '.join(found_markers)})",
                    'recommendation': 'N/A'
                }
            else:
                return {
                    'passed': False,
                    'severity': 'warning',
                    'message': f"Limited expected markers found for ovarian cancer ({len(found_markers)}/4: {', '.join(found_markers) if found_markers else 'none'})",
                    'recommendation': 'Review molecular findings for consistency with clinical diagnosis. Consider if tumor sample quality or subtype explains discrepancy.'
                }

        # Default: no specific consistency check available
        return {
            'passed': True,
            'severity': 'info',
            'message': 'Cross-modal consistency check not applicable for this condition',
            'recommendation': 'N/A'
        }

    # ==================================================================================
    # DRAFT REPORT JSON GENERATION (for CitL workflow)
    # ==================================================================================

    def generate_draft_report_json(self):
        """
        Generate structured draft report JSON for CitL review workflow.

        Returns:
            Dict containing draft report with quality checks and findings
        """
        self.log("Generating draft report JSON...")

        # Run quality checks
        quality_checks = self.run_quality_checks()

        # Build draft report structure
        draft_report = {
            'report_metadata': {
                'patient_id': self.patient_id,
                'report_date': datetime.now().isoformat(),
                'status': 'pending_review',
                'version': '1.0',
                'tests_included': ['TEST_3_SPATIAL'],  # Would include TEST_1, TEST_2, TEST_4, TEST_5 in full workflow
                'generated_by': 'generate_patient_report.py (automated)'
            },
            'quality_checks': quality_checks,
            'clinical_findings': {
                'test_1_clinical': self._extract_test1_findings(),
                'test_3_spatial': self._extract_test3_findings(),
            },
            'key_molecular_findings': self._extract_key_molecular_findings(),
            'treatment_recommendations': self._generate_treatment_recommendations(),
            'flags_for_review': quality_checks['flags']
        }

        # Save draft report
        output_file = self.patient_output_dir / "draft_report.json"
        with open(output_file, 'w') as f:
            json.dump(draft_report, f, indent=2)

        self.log(f"✅ Draft report saved: {output_file}")

        # Save quality checks separately for easy review
        qc_file = self.patient_output_dir / "quality_checks.json"
        with open(qc_file, 'w') as f:
            json.dump(quality_checks, f, indent=2)

        self.log(f"✅ Quality checks saved: {qc_file}")

        return draft_report

    def _extract_test1_findings(self):
        """Extract clinical findings from FHIR data (TEST_1)."""
        if not self.fhir_data.get('patient'):
            return {'status': 'not_available', 'reason': 'FHIR data not loaded'}

        findings = {
            'patient_demographics': {},
            'conditions': [],
            'medications': [],
            'observations': []
        }

        # Patient demographics
        if self.fhir_data.get('patient'):
            patient = self.fhir_data['patient']
            name = patient.get('name', [{}])[0]
            findings['patient_demographics'] = {
                'name': f"{name.get('given', [''])[0]} {name.get('family', '')}",
                'gender': patient.get('gender', 'unknown'),
                'birth_date': patient.get('birthDate', 'unknown')
            }

        # Conditions
        for entry in self.fhir_data.get('conditions', []):
            condition = entry.get('resource', {})
            findings['conditions'].append({
                'code': condition.get('code', {}).get('text', 'Unknown'),
                'onset': condition.get('onsetDateTime', 'Unknown')
            })

        # Medications
        for entry in self.fhir_data.get('medications', []):
            med = entry.get('resource', {})
            findings['medications'].append({
                'medication': med.get('medicationCodeableConcept', {}).get('text', 'Unknown'),
                'status': med.get('status', 'unknown')
            })

        # Observations (CA-125, etc.)
        for entry in self.fhir_data.get('observations', []):
            obs = entry.get('resource', {})
            findings['observations'].append({
                'code': obs.get('code', {}).get('text', 'Unknown'),
                'value': obs.get('valueQuantity', {}).get('value', 'N/A'),
                'unit': obs.get('valueQuantity', {}).get('unit', '')
            })

        return findings

    def _extract_test3_findings(self):
        """Extract spatial transcriptomics findings (TEST_3)."""
        findings = {
            'dataset_summary': {
                'num_genes': self.spatial_data['expression'].shape[0] if 'expression' in self.spatial_data else 0,
                'num_spots': self.spatial_data['expression'].shape[1] if 'expression' in self.spatial_data else 0,
                'num_regions': len(self.spatial_data['regions']['region'].unique()) if 'regions' in self.spatial_data else 0
            },
            'differential_expression': {
                'num_significant': len(self.analysis_results.get('significant_degs', [])),
                'num_upregulated': len(self.analysis_results.get('significant_degs', pd.DataFrame())[
                    self.analysis_results.get('significant_degs', pd.DataFrame()).get('log2_fold_change', pd.Series()) > 0
                ]) if 'significant_degs' in self.analysis_results else 0,
                'num_downregulated': len(self.analysis_results.get('significant_degs', pd.DataFrame())[
                    self.analysis_results.get('significant_degs', pd.DataFrame()).get('log2_fold_change', pd.Series()) < 0
                ]) if 'significant_degs' in self.analysis_results else 0
            },
            'spatial_patterns': {
                'num_svgs': len(self.analysis_results.get('spatially_variable_genes', []))
            }
        }

        return findings

    def _extract_key_molecular_findings(self):
        """Extract top 10 molecular findings for clinician validation."""
        sig_degs = self.analysis_results.get('significant_degs', pd.DataFrame())

        if len(sig_degs) == 0:
            return []

        # Sort by FDR (most significant first)
        top_findings = sig_degs.sort_values('fdr').head(10)

        findings = []
        for idx, (_, row) in enumerate(top_findings.iterrows(), 1):
            finding = {
                'finding_id': f'DEG_{idx}',
                'gene': row['gene'],
                'finding_type': 'Differential Expression',
                'log2_fold_change': float(row['log2_fold_change']),
                'fdr': float(row['fdr']),
                'confidence': 'high' if row['fdr'] < 0.01 else 'medium' if row['fdr'] < 0.05 else 'low',
                'clinical_significance': self._assess_clinical_significance(row['gene']),
                'requires_validation': row['fdr'] > 0.01  # Flag marginal findings for extra scrutiny
            }
            findings.append(finding)

        return findings

    def _assess_clinical_significance(self, gene):
        """Assess clinical significance of a gene finding."""
        # Database of gene functions and clinical relevance
        # This is a simplified example - full implementation would use comprehensive gene database
        gene_db = {
            'TP53': 'Tumor suppressor loss, TP53 pathway disrupted',
            'BRCA1': 'DNA repair deficiency, PARP inhibitor sensitivity',
            'BRCA2': 'DNA repair deficiency, PARP inhibitor sensitivity',
            'PIK3CA': 'PI3K pathway activation, PI3K inhibitor targetable',
            'ABCB1': 'Drug efflux pump overexpression, platinum resistance',
            'BCL2L1': 'Anti-apoptotic signaling, therapy resistance',
            'CD8A': 'T-cell marker, immune infiltration',
            'VEGFA': 'Angiogenesis, bevacizumab targetable',
            'MKI67': 'Proliferation marker, aggressive phenotype',
            'AKT1': 'PI3K/AKT pathway activation, AKT inhibitor targetable',
            'MTOR': 'mTOR signaling activation, mTOR inhibitor targetable',
            'HIF1A': 'Hypoxia response, poor prognosis',
            'CA9': 'Hypoxia marker, carbonic anhydrase inhibitor targetable',
            'ESR1': 'Estrogen receptor, endocrine therapy targetable',
            'ERBB2': 'HER2 receptor, trastuzumab/pertuzumab targetable',
            'EGFR': 'EGFR receptor, EGFR TKI targetable'
        }

        return gene_db.get(gene, 'Unknown clinical significance - requires literature review')

    def _generate_treatment_recommendations(self):
        """Generate preliminary treatment recommendations based on molecular findings."""
        sig_degs = self.analysis_results.get('significant_degs', pd.DataFrame())

        if len(sig_degs) == 0:
            return []

        recommendations = []
        gene_set = set(sig_degs['gene'].values)

        # Check for targetable alterations
        # PI3K pathway activation
        if 'PIK3CA' in gene_set or 'AKT1' in gene_set:
            recommendations.append({
                'recommendation_id': 'REC_1',
                'therapy_name': 'PI3K inhibitor (e.g., Alpelisib)',
                'molecular_target': 'PIK3CA activation or AKT1 upregulation',
                'expected_efficacy': '30-40% ORR in PIK3CA-mutant tumors',
                'evidence_level': 'NCCN Category 2B',
                'notes': 'Consider clinical trial enrollment if available'
            })

        # PARP inhibitor for HR deficiency
        if 'BRCA1' in gene_set or 'BRCA2' in gene_set:
            recommendations.append({
                'recommendation_id': 'REC_2',
                'therapy_name': 'PARP inhibitor (e.g., Olaparib, Niraparib)',
                'molecular_target': 'BRCA1/2 deficiency, homologous recombination deficiency',
                'expected_efficacy': '60-70% ORR in BRCA-mutant ovarian cancer',
                'evidence_level': 'NCCN Category 1',
                'notes': 'FDA approved for BRCA-mutant ovarian cancer'
            })

        # Anti-angiogenic therapy
        if 'VEGFA' in gene_set:
            recommendations.append({
                'recommendation_id': 'REC_3',
                'therapy_name': 'VEGF inhibitor (e.g., Bevacizumab)',
                'molecular_target': 'VEGFA overexpression, angiogenic phenotype',
                'expected_efficacy': '3-4 month PFS benefit in ovarian cancer',
                'evidence_level': 'NCCN Category 1',
                'notes': 'Approved for first-line and recurrent ovarian cancer'
            })

        # BCL2 inhibitor
        if 'BCL2L1' in gene_set:
            recommendations.append({
                'recommendation_id': 'REC_4',
                'therapy_name': 'BCL2 inhibitor (e.g., Venetoclax)',
                'molecular_target': 'BCL2L1 overexpression, anti-apoptotic signaling',
                'expected_efficacy': 'Investigational in solid tumors',
                'evidence_level': 'Clinical trial only',
                'notes': 'FDA approved for hematologic malignancies, investigational for solid tumors'
            })

        return recommendations

    def generate_report(self):
        """Run complete analysis pipeline."""
        self.log("=" * 80)
        self.log(f"GENERATING PATIENT REPORT: {self.patient_id}")
        self.log("=" * 80)
        self.log("")

        # Step 1: Fetch FHIR data
        self.fetch_fhir_data()
        self.log("")

        # Step 2: Load spatial data
        self.load_spatial_data()
        self.log("")

        # Step 3: Run analyses
        self.perform_differential_expression()
        self.log("")

        self.calculate_spatial_autocorrelation()
        self.log("")

        self.perform_cell_deconvolution()
        self.log("")

        # Step 4: Create visualizations
        self.create_visualizations()
        self.log("")

        # Step 5: Generate summary
        self.generate_clinical_summary()

        # Step 6: Save metadata
        self.save_metadata()

        # Step 7: Generate draft report JSON for CitL workflow (if requested)
        if self.generate_draft:
            self.log("")
            self.generate_draft_report_json()

        self.log("")
        self.log("=" * 80)
        if self.generate_draft:
            self.log(f"✅ DRAFT REPORT COMPLETE! Ready for CitL review.")
            self.log(f"   Draft report: {self.patient_output_dir / 'draft_report.json'}")
            self.log(f"   Quality checks: {self.patient_output_dir / 'quality_checks.json'}")
            self.log(f"   Clinical summary: {self.patient_output_dir / 'clinical_summary.txt'}")
            self.log("")
            self.log(f"📍 Next Steps:")
            self.log(f"   1. Review draft report and quality checks")
            self.log(f"   2. Complete CitL review form: docs/for-hospitals/citl-workflows/CITL_REVIEW_TEMPLATE.md")
            self.log(f"   3. Submit review: python servers/mcp-patient-report/scripts/citl_submit_review.py --patient-id {self.patient_id}")
        else:
            self.log(f"✅ REPORT COMPLETE!")
        self.log(f"   Output directory: {self.patient_output_dir}")
        self.log("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate automated patient analysis report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze Patient-001 (standard report)
  python generate_patient_report.py --patient-id patient-001 --output-dir ./results

  # Generate draft report for CitL review workflow
  python generate_patient_report.py --patient-id PAT001-OVC-2025 --output-dir ./results --generate-draft

  # Specify custom output directory
  python generate_patient_report.py --patient-id PAT002-OVC-2025 --output-dir /path/to/results
        """
    )

    parser.add_argument(
        '--patient-id',
        required=True,
        help='Patient ID (e.g., patient-001)'
    )

    parser.add_argument(
        '--output-dir',
        default='./results',
        help='Output directory for results (default: ./results)'
    )

    parser.add_argument(
        '--generate-draft',
        action='store_true',
        help='Generate draft report with quality checks for CitL review workflow (default: False)'
    )

    args = parser.parse_args()

    # Generate report
    generator = PatientReportGenerator(args.patient_id, args.output_dir, args.generate_draft)
    generator.generate_report()


if __name__ == "__main__":
    main()
