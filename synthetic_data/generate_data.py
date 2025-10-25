#!/usr/bin/env python3
"""Generate realistic synthetic data for testing Spatial MCP POC.

This script creates:
- FASTQ files with spatial barcodes and UMIs
- Spatial coordinate files
- Expression matrices
- Clinical metadata
- Histology image metadata
"""

import argparse
import gzip
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


# Seed for reproducibility
random.seed(42)
np.random.seed(42)


class SyntheticDataGenerator:
    """Generate synthetic spatial transcriptomics data."""

    # Realistic gene names for human tissue
    GENES = [
        # Epithelial markers
        "EPCAM", "KRT19", "KRT7", "KRT8", "KRT18", "CDH1", "CLDN4", "MUC1",
        # Stromal markers
        "VIM", "FN1", "COL1A1", "COL1A2", "COL3A1", "ACTA2", "PDGFRA", "FAP",
        # Immune markers
        "PTPRC", "CD3D", "CD3E", "CD4", "CD8A", "CD19", "CD68", "CD163",
        # Tumor markers
        "MKI67", "PCNA", "TOP2A", "CCND1", "MYC", "TP53", "KRAS", "PIK3CA",
        # Angiogenesis
        "VEGFA", "PECAM1", "CD34", "FLT1", "KDR",
        # Other common
        "GAPDH", "ACTB", "B2M", "MALAT1", "NEAT1"
    ] + [f"GENE{i:04d}" for i in range(100)]  # Additional synthetic genes

    # Nucleotide bases with realistic distribution
    BASES = ["A", "C", "G", "T"]
    BASE_WEIGHTS = [0.3, 0.2, 0.2, 0.3]  # Slight AT bias

    # Phred quality scores (ASCII offset 33)
    QUALITY_CHARS = "".join([chr(33 + q) for q in range(42)])  # Q0-Q41

    def __init__(self, output_dir: Path):
        """Initialize generator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_sequence(self, length: int, gc_content: float = 0.5) -> str:
        """Generate a random DNA sequence.

        Args:
            length: Sequence length
            gc_content: GC content (0-1)

        Returns:
            DNA sequence string
        """
        at_prob = (1 - gc_content) / 2
        gc_prob = gc_content / 2
        weights = [at_prob, gc_prob, gc_prob, at_prob]  # A, C, G, T

        return "".join(random.choices(self.BASES, weights=weights, k=length))

    def generate_quality_scores(self, length: int, mean_quality: int = 35) -> str:
        """Generate Phred quality scores.

        Args:
            length: Number of quality scores
            mean_quality: Mean Phred quality (typically 30-40)

        Returns:
            Quality string (ASCII Phred+33)
        """
        # Generate quality scores with normal distribution
        qualities = np.random.normal(mean_quality, 5, length)
        qualities = np.clip(qualities, 2, 41).astype(int)

        return "".join([chr(33 + q) for q in qualities])

    def generate_spatial_barcode(self) -> str:
        """Generate a spatial barcode (16bp)."""
        return self.generate_sequence(16)

    def generate_umi(self) -> str:
        """Generate a UMI (12bp)."""
        return self.generate_sequence(12)

    def generate_fastq_reads(
        self,
        num_reads: int,
        output_prefix: str,
        read_length: int = 75,
        paired: bool = True
    ) -> Dict[str, Path]:
        """Generate paired-end FASTQ files.

        Args:
            num_reads: Number of read pairs to generate
            output_prefix: Output file prefix
            read_length: Length of each read
            paired: Generate paired-end reads

        Returns:
            Dictionary with paths to generated files
        """
        r1_path = self.output_dir / "fastq" / f"{output_prefix}_R1.fastq.gz"
        r2_path = self.output_dir / "fastq" / f"{output_prefix}_R2.fastq.gz"

        r1_path.parent.mkdir(parents=True, exist_ok=True)

        with gzip.open(r1_path, "wt") as r1_file:
            r2_file = gzip.open(r2_path, "wt") if paired else None

            for i in range(num_reads):
                # R1: Spatial barcode (16bp) + UMI (12bp) + polyT (47bp)
                barcode = self.generate_spatial_barcode()
                umi = self.generate_umi()
                polyt = "T" * 47
                r1_seq = barcode + umi + polyt
                r1_qual = self.generate_quality_scores(len(r1_seq))

                # Write R1
                r1_file.write(f"@READ{i:08d}/1\n")
                r1_file.write(f"{r1_seq}\n")
                r1_file.write("+\n")
                r1_file.write(f"{r1_qual}\n")

                if paired:
                    # R2: cDNA sequence (transcript)
                    # Simulate gene expression by sampling from gene list
                    gene = random.choice(self.GENES)
                    r2_seq = self.generate_sequence(read_length, gc_content=0.52)
                    r2_qual = self.generate_quality_scores(read_length, mean_quality=36)

                    r2_file.write(f"@READ{i:08d}/2 GENE:{gene}\n")
                    r2_file.write(f"{r2_seq}\n")
                    r2_file.write("+\n")
                    r2_file.write(f"{r2_qual}\n")

            if r2_file:
                r2_file.close()

        result = {"R1": r1_path}
        if paired:
            result["R2"] = r2_path

        return result

    def generate_spatial_coordinates(
        self,
        num_spots: int,
        output_file: str,
        grid_size: Tuple[int, int] = (100, 100)
    ) -> Path:
        """Generate spatial coordinates for spots.

        Args:
            num_spots: Number of spatial spots
            output_file: Output filename
            grid_size: (width, height) of spatial grid

        Returns:
            Path to generated file
        """
        output_path = self.output_dir / "spatial" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        coords = []
        for i in range(num_spots):
            x = np.random.uniform(0, grid_size[0])
            y = np.random.uniform(0, grid_size[1])
            barcode = self.generate_spatial_barcode()

            coords.append({
                "barcode": barcode,
                "x": round(x, 2),
                "y": round(y, 2),
                "spot_id": f"SPOT{i:06d}"
            })

        with open(output_path, "w") as f:
            json.dump(coords, f, indent=2)

        return output_path

    def generate_expression_matrix(
        self,
        num_genes: int,
        num_spots: int,
        output_file: str,
        regions: List[str] = None
    ) -> Path:
        """Generate gene expression matrix.

        Args:
            num_genes: Number of genes
            num_spots: Number of spatial spots
            output_file: Output filename
            regions: Optional region labels for spots

        Returns:
            Path to generated file
        """
        output_path = self.output_dir / "spatial" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        genes = self.GENES[:num_genes]

        # Create expression data with regional patterns
        expression_data = []

        for spot_idx in range(num_spots):
            spot_data = {
                "spot_id": f"SPOT{spot_idx:06d}",
                "barcode": self.generate_spatial_barcode(),
                "region": random.choice(regions) if regions else "tissue"
            }

            # Generate expression values (UMI counts)
            # Different genes have different expression patterns
            for gene_idx, gene in enumerate(genes):
                # Simulate realistic count distribution
                if gene in ["GAPDH", "ACTB", "B2M"]:
                    # Housekeeping genes - high expression
                    count = int(np.random.negative_binomial(100, 0.1))
                elif gene in ["EPCAM", "KRT19"] and spot_data["region"] == "tumor":
                    # Epithelial markers - high in tumor
                    count = int(np.random.negative_binomial(50, 0.2))
                elif gene in ["VIM", "COL1A1"] and spot_data["region"] == "stroma":
                    # Stromal markers - high in stroma
                    count = int(np.random.negative_binomial(40, 0.2))
                elif gene in ["CD3D", "CD8A"] and spot_data["region"] == "immune":
                    # Immune markers - high in immune regions
                    count = int(np.random.negative_binomial(30, 0.3))
                else:
                    # Other genes - sparse expression
                    count = int(np.random.negative_binomial(5, 0.5))

                spot_data[gene] = max(0, count)

            expression_data.append(spot_data)

        with open(output_path, "w") as f:
            json.dump(expression_data, f, indent=2)

        return output_path

    def generate_clinical_metadata(
        self,
        num_patients: int,
        output_file: str
    ) -> Path:
        """Generate synthetic clinical metadata.

        Args:
            num_patients: Number of patients
            output_file: Output filename

        Returns:
            Path to generated file
        """
        output_path = self.output_dir / "clinical" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        diagnoses = [
            ("C50.9", "Breast cancer, unspecified"),
            ("C34.9", "Lung cancer, unspecified"),
            ("C18.9", "Colon cancer, unspecified"),
            ("C61", "Prostate cancer"),
            ("C16.9", "Gastric cancer, unspecified")
        ]

        patients = []
        for i in range(num_patients):
            diagnosis = random.choice(diagnoses)
            age = int(np.random.normal(62, 12))
            age = max(18, min(95, age))

            patient = {
                "patient_id": f"PT{i:05d}",
                "age": age,
                "sex": random.choice(["M", "F"]),
                "ethnicity": random.choice(["Caucasian", "African American", "Hispanic", "Asian", "Other"]),
                "diagnosis": {
                    "icd10": diagnosis[0],
                    "description": diagnosis[1],
                    "stage": random.choice(["I", "II", "III", "IV"])
                },
                "treatment": random.choice(["Surgery", "Chemotherapy", "Radiation", "Immunotherapy", "Combined"]),
                "survival_months": int(np.random.exponential(24)) if random.random() > 0.3 else None,
                "response": random.choice(["Complete Response", "Partial Response", "Stable Disease", "Progressive Disease"]),
                "sample_id": f"SAMPLE{i:05d}"
            }

            patients.append(patient)

        with open(output_path, "w") as f:
            json.dump(patients, f, indent=2)

        return output_path

    def generate_image_metadata(
        self,
        num_images: int,
        output_file: str
    ) -> Path:
        """Generate histology image metadata.

        Args:
            num_images: Number of images
            output_file: Output filename

        Returns:
            Path to generated file
        """
        output_path = self.output_dir / "images" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        images = []
        for i in range(num_images):
            image = {
                "image_id": f"IMG{i:05d}",
                "sample_id": f"SAMPLE{i:05d}",
                "stain_type": random.choice(["H&E", "IF", "IHC"]),
                "magnification": random.choice(["10x", "20x", "40x"]),
                "resolution": random.choice(["low", "medium", "high"]),
                "dimensions": {
                    "width": random.choice([2048, 4096, 8192]),
                    "height": random.choice([2048, 4096, 8192])
                },
                "file_format": "tiff",
                "file_size_mb": round(random.uniform(10, 500), 2),
                "regions_annotated": random.choice([True, False]),
                "quality_score": round(random.uniform(0.7, 1.0), 2)
            }

            images.append(image)

        with open(output_path, "w") as f:
            json.dump(images, f, indent=2)

        return output_path


def main():
    """Generate all synthetic datasets."""
    parser = argparse.ArgumentParser(description="Generate synthetic spatial transcriptomics data")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument("--num-reads", type=int, default=10000, help="Number of FASTQ reads")
    parser.add_argument("--num-spots", type=int, default=5000, help="Number of spatial spots")
    parser.add_argument("--num-genes", type=int, default=50, help="Number of genes")
    parser.add_argument("--num-patients", type=int, default=10, help="Number of patients")
    parser.add_argument("--num-images", type=int, default=10, help="Number of images")

    args = parser.parse_args()

    generator = SyntheticDataGenerator(Path(args.output_dir))

    print("🧬 Generating Synthetic Spatial Transcriptomics Data...")
    print(f"Output directory: {args.output_dir}\n")

    # Generate FASTQ files
    print(f"1. Generating FASTQ files ({args.num_reads:,} reads)...")
    fastq_files = generator.generate_fastq_reads(
        num_reads=args.num_reads,
        output_prefix="sample_001"
    )
    for read_type, path in fastq_files.items():
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"   ✅ {read_type}: {path.name} ({size_mb:.2f} MB)")

    # Generate spatial coordinates
    print(f"\n2. Generating spatial coordinates ({args.num_spots:,} spots)...")
    coords_file = generator.generate_spatial_coordinates(
        num_spots=args.num_spots,
        output_file="spatial_coordinates.json"
    )
    print(f"   ✅ {coords_file.name}")

    # Generate expression matrix with regions
    print(f"\n3. Generating expression matrix ({args.num_genes} genes × {args.num_spots} spots)...")
    regions = ["tumor", "stroma", "immune", "normal"]
    expr_file = generator.generate_expression_matrix(
        num_genes=args.num_genes,
        num_spots=args.num_spots,
        output_file="expression_matrix.json",
        regions=regions
    )
    size_mb = expr_file.stat().st_size / (1024 * 1024)
    print(f"   ✅ {expr_file.name} ({size_mb:.2f} MB)")
    print(f"   📊 Regions: {', '.join(regions)}")

    # Generate clinical metadata
    print(f"\n4. Generating clinical metadata ({args.num_patients} patients)...")
    clinical_file = generator.generate_clinical_metadata(
        num_patients=args.num_patients,
        output_file="clinical_data.json"
    )
    print(f"   ✅ {clinical_file.name}")

    # Generate image metadata
    print(f"\n5. Generating image metadata ({args.num_images} images)...")
    image_file = generator.generate_image_metadata(
        num_images=args.num_images,
        output_file="image_metadata.json"
    )
    print(f"   ✅ {image_file.name}")

    print("\n✨ Synthetic data generation complete!")
    print(f"\n📁 Files generated in: {args.output_dir}/")
    print("   ├── fastq/")
    print("   ├── spatial/")
    print("   ├── clinical/")
    print("   └── images/")


if __name__ == "__main__":
    main()
