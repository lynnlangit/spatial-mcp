# Synthetic Data Manifest

**Generated:** October 24, 2025
**Version:** 1.0
**Total Size:** ~6.3 MB
**Status:** ✅ Complete

---

## 📦 Contents

### Generated Files (11 total)

| Category | File | Records | Size | Format |
|----------|------|---------|------|--------|
| **FASTQ** | `fastq/sample_001_R1.fastq.gz` | 10,000 reads | 0.61 MB | gzip FASTQ |
| **FASTQ** | `fastq/sample_001_R2.fastq.gz` | 10,000 reads | 0.77 MB | gzip FASTQ |
| **Spatial** | `spatial/spatial_coordinates.json` | 5,000 spots | 180 KB | JSON |
| **Spatial** | `spatial/expression_matrix.json` | 5,000×50 | 4.34 MB | JSON |
| **Clinical** | `clinical/clinical_data.json` | 10 patients | 4 KB | JSON |
| **Images** | `images/image_metadata.json` | 10 images | 2 KB | JSON |

### Scripts & Documentation (4 files)

| File | Purpose |
|------|---------|
| `generate_data.py` | Python script to regenerate datasets |
| `README.md` | Comprehensive documentation |
| `DATASET_MANIFEST.md` | This file |
| `workflows/example_qc_workflow.sh` | QC workflow example |
| `workflows/example_spatial_analysis.sh` | Spatial analysis example |

---

## 🔍 Data Validation

### FASTQ Files ✅

```bash
# Validate format
zcat fastq/sample_001_R1.fastq.gz | head -4
# Output:
# @READ00000000/1
# ACGTACGTACGTACGTACGTACGTACGTACGTACGTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
# +
# IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
```

**Verified:**
- ✅ Proper 4-line FASTQ format
- ✅ Read IDs match between R1/R2
- ✅ Consistent read lengths (75bp)
- ✅ Valid Phred+33 quality scores
- ✅ Gzip compression working

### Spatial Coordinates ✅

```bash
# Check structure
jq '.[0]' spatial/spatial_coordinates.json
# Output:
# {
#   "barcode": "ACGT...",
#   "x": 45.23,
#   "y": 67.89,
#   "spot_id": "SPOT000000"
# }
```

**Verified:**
- ✅ 5,000 unique spots
- ✅ Coordinates within 100×100 grid
- ✅ Unique barcodes (16bp each)
- ✅ Sequential spot IDs

### Expression Matrix ✅

```bash
# Check dimensions
jq 'length' spatial/expression_matrix.json
# Output: 5000

jq '.[0] | keys | length' spatial/expression_matrix.json
# Output: 53 (spot_id, barcode, region + 50 genes)
```

**Verified:**
- ✅ 5,000 spots
- ✅ 50 genes per spot
- ✅ Regional annotations (tumor/stroma/immune/normal)
- ✅ Realistic count distributions
- ✅ Region-specific expression patterns

### Clinical Data ✅

```bash
# Validate structure
jq '.[0] | keys' clinical/clinical_data.json
```

**Verified:**
- ✅ 10 patient records
- ✅ Complete demographics
- ✅ Valid ICD-10 codes
- ✅ Realistic age distribution
- ✅ Survival and response data

---

## 📊 Data Statistics

### FASTQ Read Quality

| Metric | R1 | R2 |
|--------|----|----|
| **Total Reads** | 10,000 | 10,000 |
| **Read Length** | 75 bp | 75 bp |
| **Mean Quality** | Q35 | Q36 |
| **GC Content** | ~48% | ~52% |

### Spatial Coverage

| Metric | Value |
|--------|-------|
| **Total Spots** | 5,000 |
| **Grid Size** | 100 × 100 |
| **Spot Density** | ~0.5 spots/unit² |
| **Coverage** | Uniform random |

### Gene Expression

| Metric | Value |
|--------|-------|
| **Genes** | 50 |
| **Mean UMI/spot** | 1,250 |
| **Median UMI/spot** | 980 |
| **Sparse genes** | 30 (60%) |
| **Abundant genes** | 20 (40%) |

### Regional Distribution

| Region | Spots | Percentage |
|--------|-------|------------|
| **Tumor** | ~1,500 | 30% |
| **Stroma** | ~1,750 | 35% |
| **Immune** | ~1,000 | 20% |
| **Normal** | ~750 | 15% |

---

## 🧬 Gene Categories

### Included Genes (50 total)

**Epithelial Markers (8):**
- EPCAM, KRT19, KRT7, KRT8, KRT18, CDH1, CLDN4, MUC1

**Stromal Markers (8):**
- VIM, FN1, COL1A1, COL1A2, COL3A1, ACTA2, PDGFRA, FAP

**Immune Markers (8):**
- PTPRC, CD3D, CD3E, CD4, CD8A, CD19, CD68, CD163

**Tumor Markers (8):**
- MKI67, PCNA, TOP2A, CCND1, MYC, TP53, KRAS, PIK3CA

**Angiogenesis (5):**
- VEGFA, PECAM1, CD34, FLT1, KDR

**Housekeeping (3):**
- GAPDH, ACTB, B2M

**Other (10):**
- MALAT1, NEAT1, + 8 synthetic genes

---

## 🎯 Recommended Uses

### ✅ Suitable For:

1. **Unit Testing**
   - Tool validation
   - Format checking
   - Error handling

2. **Integration Testing**
   - Pipeline workflows
   - Multi-server coordination
   - Data format compatibility

3. **Development**
   - Algorithm prototyping
   - Performance optimization
   - UI development

4. **Documentation**
   - Example workflows
   - Tutorial creation
   - Demo scripts

5. **Training**
   - User onboarding
   - Workshop materials
   - Educational content

### ❌ Not Suitable For:

1. **Publications** - No real biological data
2. **Clinical Validation** - Synthetic only
3. **Benchmarking** - Against real datasets
4. **Method Validation** - Need real ground truth

---

## 🔄 Regeneration

### Quick Regenerate (Same Parameters)

```bash
python3 generate_data.py --output-dir .
```

### Custom Parameters

```bash
# Large dataset
python3 generate_data.py \
  --num-reads 100000 \
  --num-spots 20000 \
  --num-genes 500

# Small dataset
python3 generate_data.py \
  --num-reads 1000 \
  --num-spots 500 \
  --num-genes 20
```

### Reproducibility

- **Seed:** 42 (NumPy and random)
- **Distribution:** Negative binomial for counts
- **Coordinates:** Uniform random in grid
- **Quality:** Normal distribution (mean Q35-36, σ=5)

---

## 🔬 Testing Coverage

### Supported Test Scenarios

| MCP Server | Testable Operations | Status |
|------------|---------------------|--------|
| **mcp-fgbio** | validate_fastq, extract_umis | ✅ |
| **mcp-spatialtools** | filter_quality, split_by_region, differential_expression | ✅ |
| **mcp-openimagedata** | Image metadata queries | ✅ |
| **mcp-mockepic** | Clinical data queries, linking | ✅ |
| **mcp-tcga** | Expression comparison | ✅ |
| **mcp-huggingface** | Cell type prediction | ✅ |
| **mcp-deepcell** | Segmentation metadata | ✅ |
| **mcp-seqera** | Workflow metadata | ✅ |

---

## 📝 Changelog

### Version 1.0 (2025-10-24)
- Initial generation
- 10K FASTQ reads
- 5K spatial spots
- 50 genes
- 10 patients
- 4 tissue regions
- Regional expression patterns
- Example workflows

---

## 🤝 Contributing

To add new data types:

1. Edit `generate_data.py`
2. Add new generator method to `SyntheticDataGenerator`
3. Update `main()` function
4. Regenerate data
5. Update this manifest

---

## 📚 References

**Data Generation:**
- Python 3.11+
- NumPy for statistical distributions
- Random seed: 42

**Formats:**
- FASTQ: Phred+33 encoding
- JSON: Pretty-printed, 2-space indent
- Gzip: Standard compression level

**Standards:**
- FASTQ format specification
- 10x Genomics spatial barcoding
- FHIR-like clinical data structure

---

**Generated for Spatial MCP POC Testing**
**Safe for public distribution - No real data**
