# Synthetic Data for Spatial MCP Testing

Realistic synthetic datasets for testing the Spatial MCP POC without requiring real biological data.

## 📁 Directory Structure

```
synthetic_data/
├── fastq/              # Paired-end FASTQ files with spatial barcodes
├── spatial/            # Spatial coordinates and expression matrices
├── clinical/           # Patient metadata and clinical outcomes
├── images/             # Histology image metadata
├── workflows/          # Example workflow scripts
├── generate_data.py    # Data generation script
└── README.md           # This file
```

## 🧬 Generated Datasets

### 1. FASTQ Files (`fastq/`)

**Files:**
- `sample_001_R1.fastq.gz` - Read 1: Spatial barcodes (16bp) + UMIs (12bp) + polyT
- `sample_001_R2.fastq.gz` - Read 2: cDNA sequences (75bp)

**Characteristics:**
- 10,000 read pairs
- Realistic Phred quality scores (mean Q35-36)
- GC content: ~50-52%
- Proper FASTQ format (4 lines per read)
- Gzip compressed

**Read Structure:**
```
R1: [Spatial Barcode 16bp][UMI 12bp][polyT 47bp]
R2: [cDNA sequence 75bp]
```

**Usage:**
```bash
# Validate FASTQ
mcp-fgbio validate_fastq fastq/sample_001_R1.fastq.gz

# Extract UMIs
mcp-fgbio extract_umis fastq/sample_001_R1.fastq.gz output/
```

---

### 2. Spatial Coordinates (`spatial/`)

**File:** `spatial_coordinates.json`

**Contents:**
- 5,000 spatial spots
- X,Y coordinates (100×100 grid)
- Unique barcodes for each spot
- Spot IDs

**Format:**
```json
[
  {
    "barcode": "ACGTACGTACGTACGT",
    "x": 45.23,
    "y": 67.89,
    "spot_id": "SPOT000001"
  },
  ...
]
```

**Usage:**
```bash
# Split by spatial region
mcp-spatialtools split_by_region \
  spatial/spatial_coordinates.json \
  output/ \
  --regions tumor,stroma,immune
```

---

### 3. Expression Matrix (`spatial/`)

**File:** `expression_matrix.json`

**Contents:**
- 5,000 spots × 50 genes
- Realistic count distributions (negative binomial)
- Regional expression patterns:
  - **Tumor regions:** High EPCAM, KRT19 (epithelial markers)
  - **Stroma regions:** High VIM, COL1A1 (stromal markers)
  - **Immune regions:** High CD3D, CD8A (immune markers)
  - **Housekeeping genes:** GAPDH, ACTB, B2M (high everywhere)

**Gene Categories:**
- Epithelial markers: EPCAM, KRT19, KRT7, KRT8, CDH1, etc.
- Stromal markers: VIM, FN1, COL1A1, COL3A1, ACTA2, etc.
- Immune markers: PTPRC, CD3D, CD8A, CD4, CD19, CD68, etc.
- Tumor markers: MKI67, PCNA, TP53, KRAS, PIK3CA, etc.
- Angiogenesis: VEGFA, PECAM1, CD34, etc.

**Format:**
```json
[
  {
    "spot_id": "SPOT000001",
    "barcode": "ACGTACGTACGTACGT",
    "region": "tumor",
    "EPCAM": 523,
    "KRT19": 412,
    "VIM": 45,
    ...
  },
  ...
]
```

**Usage:**
```bash
# Differential expression analysis
mcp-spatialtools perform_differential_expression \
  spatial/expression_matrix.json \
  --group1 tumor \
  --group2 normal

# Spatial autocorrelation
mcp-spatialtools calculate_spatial_autocorrelation \
  spatial/expression_matrix.json \
  --genes EPCAM,VIM,CD3D
```

---

### 4. Clinical Metadata (`clinical/`)

**File:** `clinical_data.json`

**Contents:**
- 10 patient records
- Demographics (age, sex, ethnicity)
- Diagnosis (ICD-10 codes, stage)
- Treatment information
- Survival data
- Treatment response

**Cancer Types:**
- Breast cancer (C50.9)
- Lung cancer (C34.9)
- Colon cancer (C18.9)
- Prostate cancer (C61)
- Gastric cancer (C16.9)

**Format:**
```json
[
  {
    "patient_id": "PT00001",
    "age": 64,
    "sex": "F",
    "ethnicity": "Caucasian",
    "diagnosis": {
      "icd10": "C50.9",
      "description": "Breast cancer, unspecified",
      "stage": "II"
    },
    "treatment": "Combined",
    "survival_months": 28,
    "response": "Partial Response",
    "sample_id": "SAMPLE00001"
  },
  ...
]
```

**Usage:**
```bash
# Query patient records
mcp-mockepic query_patient_records PT00001

# Link spatial to clinical
mcp-mockepic link_spatial_to_clinical \
  SAMPLE00001 PT00001 "breast_tumor_core"
```

---

### 5. Image Metadata (`images/`)

**File:** `image_metadata.json`

**Contents:**
- 10 histology image records
- Stain types (H&E, IF, IHC)
- Magnification levels
- Image dimensions and quality scores
- File size information

**Format:**
```json
[
  {
    "image_id": "IMG00001",
    "sample_id": "SAMPLE00001",
    "stain_type": "H&E",
    "magnification": "20x",
    "resolution": "high",
    "dimensions": {
      "width": 4096,
      "height": 4096
    },
    "file_format": "tiff",
    "file_size_mb": 245.67,
    "regions_annotated": true,
    "quality_score": 0.92
  },
  ...
]
```

**Usage:**
```bash
# Fetch histology image
mcp-openimagedata fetch_histology_image IMG00001 --stain-type he

# Register image to spatial coordinates
mcp-openimagedata register_image_to_spatial \
  images/IMG00001.tiff \
  spatial/spatial_coordinates.json \
  output/registered.tiff
```

---

## 🚀 Quick Start

### Generate New Synthetic Data

```bash
# Default parameters (10K reads, 5K spots)
python3 generate_data.py --output-dir .

# Custom parameters
python3 generate_data.py \
  --output-dir . \
  --num-reads 50000 \
  --num-spots 10000 \
  --num-genes 100 \
  --num-patients 50 \
  --num-images 20
```

### Script Options

```
--output-dir DIR         Output directory (default: current directory)
--num-reads N            Number of FASTQ read pairs (default: 10,000)
--num-spots N            Number of spatial spots (default: 5,000)
--num-genes N            Number of genes in expression matrix (default: 50)
--num-patients N         Number of patient records (default: 10)
--num-images N           Number of image metadata records (default: 10)
```

---

## 📊 Data Characteristics

### Realistic Biological Features

1. **Gene Expression Patterns**
   - Regional specificity (tumor vs. stroma vs. immune)
   - Negative binomial distribution (realistic count data)
   - Housekeeping genes: high expression everywhere
   - Marker genes: region-specific expression

2. **Spatial Organization**
   - Random but realistic spot distribution
   - 100×100 coordinate grid
   - Unique barcodes per spot

3. **Clinical Data**
   - Realistic age distribution (mean 62, σ=12)
   - Common cancer types with proper ICD-10 codes
   - Treatment response categories
   - Survival data (exponential distribution)

4. **Quality Scores**
   - FASTQ: Mean Phred Q35-36 (high quality)
   - Images: Quality scores 0.7-1.0
   - Realistic variation

---

## 🔬 Example Workflows

### Workflow 1: Complete QC Pipeline

```bash
# 1. Validate FASTQ
mcp-fgbio validate_fastq fastq/sample_001_R1.fastq.gz

# 2. Extract UMIs
mcp-fgbio extract_umis \
  fastq/sample_001_R1.fastq.gz \
  output/umis/

# 3. Quality filtering
mcp-spatialtools filter_quality \
  spatial/expression_matrix.json \
  output/filtered/ \
  --min-reads 1000 \
  --min-genes 200
```

### Workflow 2: Spatial Analysis

```bash
# 1. Calculate spatial autocorrelation
mcp-spatialtools calculate_spatial_autocorrelation \
  spatial/expression_matrix.json \
  --genes EPCAM,VIM,CD3D \
  --method morans_i

# 2. Split by region
mcp-spatialtools split_by_region \
  spatial/expression_matrix.json \
  output/regions/ \
  --regions tumor,stroma,immune,normal

# 3. Differential expression
mcp-spatialtools perform_differential_expression \
  spatial/expression_matrix.json \
  --group1-samples tumor \
  --group2-samples normal
```

### Workflow 3: Clinical Integration

```bash
# 1. Query patient data
mcp-mockepic query_patient_records PT00001

# 2. Link spatial to clinical
mcp-mockepic link_spatial_to_clinical \
  SAMPLE00001 PT00001 "breast_tumor_core"

# 3. Compare to TCGA
mcp-tcga compare_to_cohort \
  spatial/expression_matrix.json \
  --cohort BRCA \
  --genes EPCAM,KRT19,TP53
```

### Workflow 4: ML Integration

```bash
# 1. Load genomic model
mcp-huggingface load_genomic_model \
  --model Geneformer \
  --model-type rna

# 2. Predict cell types
mcp-huggingface predict_cell_type \
  spatial/expression_matrix.json \
  --model Geneformer

# 3. Pathway enrichment on predictions
mcp-spatialtools perform_pathway_enrichment \
  results/predicted_cell_types.json \
  --database GO_BP
```

---

## 📈 Dataset Statistics

### Current Generated Data

| Dataset | Records | Size | Format |
|---------|---------|------|--------|
| **FASTQ R1** | 10,000 reads | 0.61 MB | gzip FASTQ |
| **FASTQ R2** | 10,000 reads | 0.77 MB | gzip FASTQ |
| **Spatial Coords** | 5,000 spots | ~180 KB | JSON |
| **Expression Matrix** | 5,000×50 | 4.34 MB | JSON |
| **Clinical Data** | 10 patients | ~4 KB | JSON |
| **Image Metadata** | 10 images | ~2 KB | JSON |
| **Total** | - | **~6 MB** | - |

---

## 🔧 Advanced Usage

### Regenerate with Different Parameters

```bash
# Large dataset for stress testing
python3 generate_data.py \
  --num-reads 100000 \
  --num-spots 20000 \
  --num-genes 500 \
  --num-patients 100

# Small dataset for quick tests
python3 generate_data.py \
  --num-reads 1000 \
  --num-spots 500 \
  --num-genes 20 \
  --num-patients 5
```

### Use with pytest

```python
import json
from pathlib import Path

def test_spatial_analysis():
    # Load synthetic data
    with open("synthetic_data/spatial/expression_matrix.json") as f:
        data = json.load(f)

    # Test your analysis
    assert len(data) == 5000
    assert "EPCAM" in data[0]
```

---

## 📝 Data Dictionary

### FASTQ Read Structure

| Component | Position | Length | Description |
|-----------|----------|--------|-------------|
| Spatial Barcode | 1-16 | 16 bp | Unique spot identifier |
| UMI | 17-28 | 12 bp | Molecular identifier |
| PolyT | 29-75 | 47 bp | Reverse transcription primer |

### Expression Matrix Fields

| Field | Type | Description |
|-------|------|-------------|
| `spot_id` | string | Unique spot identifier |
| `barcode` | string | Spatial barcode sequence |
| `region` | string | Tissue region (tumor/stroma/immune/normal) |
| `{GENE}` | integer | UMI count for gene |

### Clinical Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `patient_id` | string | Unique patient identifier |
| `age` | integer | Patient age in years |
| `sex` | string | M/F |
| `ethnicity` | string | Patient ethnicity |
| `diagnosis.icd10` | string | ICD-10 diagnosis code |
| `diagnosis.stage` | string | Cancer stage (I-IV) |
| `treatment` | string | Treatment modality |
| `survival_months` | integer | Months since diagnosis |
| `response` | string | Treatment response |

---

## 🎯 Use Cases

### 1. Unit Testing
- Validate tool functionality
- Test error handling
- Performance benchmarking

### 2. Integration Testing
- End-to-end pipeline validation
- Multi-server workflows
- Data format compatibility

### 3. Development
- Rapid prototyping
- Algorithm development
- UI/visualization testing

### 4. Demonstration
- Example workflows
- User training
- Documentation screenshots

### 5. Performance Testing
- Scalability assessment
- Memory profiling
- Execution time benchmarking

---

## 🔒 Privacy & Ethics

**Note:** All data is **100% synthetic** and contains:
- ✅ No real patient information (PHI/PII)
- ✅ No actual biological sequences
- ✅ No protected health data
- ✅ Safe for public repositories
- ✅ No HIPAA/GDPR concerns

---

## 🤝 Contributing

To add new synthetic data types:

1. Add generation method to `SyntheticDataGenerator` class
2. Update `main()` function to call new method
3. Document in this README
4. Test with example workflows

---

## 📚 References

**Synthetic Data Generation:**
- Negative binomial distribution for count data
- Realistic GC content (~50%)
- Phred quality scores (Q33 encoding)
- FASTQ format specification

**Spatial Transcriptomics:**
- 10x Genomics Visium format
- Open-ST data structure
- Standard spatial barcoding schemes

---

**Generated with ❤️ for testing the Spatial MCP POC**
