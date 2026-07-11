# STAR Aligner Installation Guide

**Purpose:** Install STAR aligner and prepare genome index for `align_spatial_data` function

**Time Required:** 1-2 hours (mostly downloading genome files)

**Disk Space:** ~35GB for human genome (hg38) + index

---

## Prerequisites

- **Operating System:** Linux or macOS (Windows requires WSL2)
- **RAM:** ≥32GB recommended for indexing (8GB minimum for alignment)
- **Disk Space:** 35GB for human genome + index
- **Python:** ≥3.11 (already required for mcp-spatialtools)

---

## Installation Methods

### Method 1: Conda (Recommended) ✅

**Best for:** Most users, all platforms

```bash
# Install STAR via conda
conda install -c bioconda star

# Verify installation
STAR --version
# Expected output: 2.7.11a (or later)

# Check STAR path (needed for mcp-spatialtools)
which STAR
# /opt/homebrew/Caskroom/miniconda/base/bin/STAR
```

**Pros:**
- Easy installation
- Automatic dependency management
- Cross-platform

**Cons:**
- Requires conda/mamba

---

### Method 2: Homebrew (macOS only)

**Best for:** macOS users without conda

```bash
# Install STAR via Homebrew
brew install brewsci/bio/star

# Verify installation
STAR --version
# 2.7.11a

# Check STAR path
which STAR
# /opt/homebrew/bin/STAR
```

**Pros:**
- Native macOS integration
- Fast installation

**Cons:**
- macOS only
- May have version lags

---

### Method 3: Pre-compiled Binary (Linux)

**Best for:** Linux servers, HPC clusters

```bash
# Download latest release
cd /usr/local/bin  # Or any directory in your PATH
wget https://github.com/alexdobin/STAR/releases/download/2.7.11a/STAR_2.7.11a.tar.gz

# Extract
tar -xzf STAR_2.7.11a.tar.gz
cd STAR_2.7.11a/bin/Linux_x86_64

# Add to PATH (add to ~/.bashrc for persistence)
export PATH=$PATH:/usr/local/bin/STAR_2.7.11a/bin/Linux_x86_64

# Verify
STAR --version
```

**Pros:**
- No package manager required
- Full control over version

**Cons:**
- Manual PATH management
- Requires root for /usr/local/bin

---

### Method 4: Compile from Source (Advanced)

**Best for:** HPC optimization, custom configurations

```bash
# Clone repository
git clone https://github.com/alexdobin/STAR.git
cd STAR/source

# Compile
make STAR

# Copy binary to PATH
sudo cp STAR /usr/local/bin/

# Verify
STAR --version
```

**Pros:**
- Latest development version
- Compiler optimizations for specific CPU

**Cons:**
- Requires C++ compiler (g++ or clang)
- More complex

---

## Genome Index Preparation

### Overview

STAR requires a **genome index** - a preprocessed version of the reference genome optimized for fast alignment. This is a one-time setup per genome.

**Options:**
1. Download pre-built index (fastest, easiest)
2. Build from FASTA + GTF (more flexible)

---

### Option 1: Download Pre-Built Index (Recommended)

#### Human (hg38/GRCh38)

**10x Genomics Reference (Recommended for Visium):**

```bash
# Create directory for genome index
mkdir -p ~/genome_indices/human_hg38_10x
cd ~/genome_indices/human_hg38_10x

# Download 10x Genomics reference (3.1GB compressed, ~30GB uncompressed)
wget https://cf.10xgenomics.com/supp/cell-exp/refdata-gex-GRCh38-2020-A.tar.gz

# Extract
tar -xzf refdata-gex-GRCh38-2020-A.tar.gz

# STAR index location
STAR_INDEX_DIR=~/genome_indices/human_hg38_10x/refdata-gex-GRCh38-2020-A/star
```

**Features:**
- Optimized for 10x Visium and Chromium
- Includes GENCODE v32 annotations
- Pre-filtered for protein-coding genes

**GENCODE Reference (Alternative):**

```bash
# Create directory
mkdir -p ~/genome_indices/human_hg38_gencode
cd ~/genome_indices/human_hg38_gencode

# Download GENCODE genome (850MB compressed)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/GRCh38.primary_assembly.genome.fa.gz

# Download GENCODE annotations (53MB compressed)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/gencode.v44.primary_assembly.annotation.gtf.gz

# Decompress
gunzip GRCh38.primary_assembly.genome.fa.gz
gunzip gencode.v44.primary_assembly.annotation.gtf.gz
```

**Then build index (see Option 2 below).**

---

#### Human (hg19/GRCh37) - Legacy

```bash
mkdir -p ~/genome_indices/human_hg19
cd ~/genome_indices/human_hg19

# Download UCSC hg19
wget http://hgdownload.cse.ucsc.edu/goldenPath/hg19/bigZips/hg19.fa.gz
gunzip hg19.fa.gz

# Download GENCODE v19 (hg19-compatible)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gtf.gz
gunzip gencode.v19.annotation.gtf.gz
```

**Then build index (see Option 2).**

---

#### Mouse (mm10/GRCm38)

```bash
mkdir -p ~/genome_indices/mouse_mm10
cd ~/genome_indices/mouse_mm10

# Download 10x Genomics mouse reference
wget https://cf.10xgenomics.com/supp/cell-exp/refdata-gex-mm10-2020-A.tar.gz
tar -xzf refdata-gex-mm10-2020-A.tar.gz

STAR_INDEX_DIR=~/genome_indices/mouse_mm10/refdata-gex-mm10-2020-A/star
```

---

### Option 2: Build Custom Index from FASTA + GTF

**When to use:**
- Need specific genome version
- Custom annotations (e.g., lncRNA, viral sequences)
- Non-standard organism

**Time:** 1-2 hours (human genome)
**RAM:** ≥32GB recommended

```bash
# Set paths
GENOME_FASTA=~/genome_indices/human_hg38_gencode/GRCh38.primary_assembly.genome.fa
GENOME_GTF=~/genome_indices/human_hg38_gencode/gencode.v44.primary_assembly.annotation.gtf
INDEX_DIR=~/genome_indices/human_hg38_custom

# Create index directory
mkdir -p $INDEX_DIR

# Build STAR index
STAR --runMode genomeGenerate \
     --runThreadN 8 \
     --genomeDir $INDEX_DIR \
     --genomeFastaFiles $GENOME_FASTA \
     --sjdbGTFfile $GENOME_GTF \
     --sjdbOverhang 99  # Read length - 1 (100bp reads → 99)

# Expected time: 60-90 minutes
# Expected output: ~30GB index files
```

**Parameters:**
- `--runThreadN 8` - Use 8 CPU cores (adjust based on your system)
- `--sjdbOverhang 99` - For 100bp reads; use 149 for 150bp reads
- `--genomeSAindexNbases` - Optional, auto-calculated

**Output Files:**
```
$INDEX_DIR/
├── Genome                    # Binary genome sequence
├── SA                        # Suffix array
├── SAindex                   # Suffix array index
├── chrName.txt               # Chromosome names
├── chrNameLength.txt         # Chromosome lengths
├── chrStart.txt              # Chromosome start positions
└── genomeParameters.txt      # Index metadata
```

---

### Verifying Genome Index

```bash
# Check index directory
ls -lh $INDEX_DIR

# Expected files (7-8 files, ~30GB total):
# Genome (27GB), SA (14GB), SAindex (1.5GB), etc.

# Check index parameters
cat $INDEX_DIR/genomeParameters.txt
# Should show:
#   versionGenome: 2.7.11a
#   genomeFastaFiles: [your FASTA path]
#   sjdbGTFfile: [your GTF path]
```

---

## Testing STAR Installation

### Test 1: Create Synthetic FASTQ

```python
# Use mcp-spatialtools synthetic FASTQ generator
from mcp_spatialtools.server import _create_synthetic_fastq
from pathlib import Path

_create_synthetic_fastq(
    output_r1=Path("test_R1.fastq.gz"),
    output_r2=Path("test_R2.fastq.gz"),
    num_reads=10000,
    read_length=100
)
```

### Test 2: Run Test Alignment

```bash
# Set paths
STAR_INDEX=~/genome_indices/human_hg38_10x/refdata-gex-GRCh38-2020-A/star
R1_FASTQ=test_R1.fastq.gz
R2_FASTQ=test_R2.fastq.gz
OUTPUT_DIR=test_alignment

# Run STAR alignment
STAR --runThreadN 4 \
     --genomeDir $STAR_INDEX \
     --readFilesIn $R2_FASTQ $R1_FASTQ \
     --readFilesCommand zcat \
     --outFileNamePrefix $OUTPUT_DIR/ \
     --outSAMtype BAM SortedByCoordinate

# Check output
ls -lh $OUTPUT_DIR/
# Expected:
#   Aligned.sortedByCoord.out.bam (~10KB for 10K reads)
#   Log.final.out (alignment statistics)
#   Log.out (processing log)
```

### Test 3: Verify Alignment Statistics

```bash
# Parse log file
cat $OUTPUT_DIR/Log.final.out | grep "Uniquely mapped reads"
# Expected: ~85% for real data, varies for synthetic
```

---

## Integration with mcp-spatialtools

### Set STAR Path (if not in system PATH)

**Option 1: Environment Variable**

```bash
# Add to ~/.bashrc or ~/.zshrc
export STAR_PATH=/path/to/STAR

# Reload shell
source ~/.bashrc
```

**Option 2: Modify mcp-spatialtools server.py**

```python
# Edit servers/mcp-spatialtools/src/mcp_spatialtools/server.py
# Line ~395

# Change:
STAR_PATH = os.getenv("STAR_PATH", "STAR")  # Default assumes STAR in PATH

# To (if needed):
STAR_PATH = "/opt/homebrew/bin/STAR"  # Your specific path
```

### Test align_spatial_data Function

```python
# Example alignment using mcp-spatialtools
from mcp_spatialtools.server import align_spatial_data
import asyncio

async def test_alignment():
    result = await align_spatial_data.fn(
        r1_fastq="/path/to/sample_R1.fastq.gz",
        r2_fastq="/path/to/sample_R2.fastq.gz",
        genome_index="~/genome_indices/human_hg38_10x/refdata-gex-GRCh38-2020-A/star",
        output_dir="/path/to/output",
        threads=8
    )

    print(f"✅ Alignment complete!")
    print(f"  Total reads: {result['alignment_stats']['total_reads']:,}")
    print(f"  Uniquely mapped: {result['alignment_stats']['uniquely_mapped']:,}")
    print(f"  Alignment rate: {result['alignment_stats']['alignment_rate']:.1%}")

# Run test
asyncio.run(test_alignment())
```

---

## Resource Requirements

### Disk Space

| Component | Size (Human hg38) |
|-----------|-------------------|
| Reference FASTA | 3.1 GB |
| GTF annotations | 50 MB |
| STAR index | 27-30 GB |
| Alignment output (50M reads) | 20-100 GB |
| **Total** | **50-135 GB** |

**Recommendation:** 200GB free space for comfortable operation

### RAM Requirements

| Operation | Minimum RAM | Recommended RAM |
|-----------|-------------|-----------------|
| Index building | 32 GB | 64 GB |
| Alignment (human genome) | 32 GB | 32 GB |
| Alignment (small genomes) | 8 GB | 16 GB |

**Note:** STAR loads entire genome index into RAM for fast alignment.

### CPU Requirements

| Operation | Minimum Cores | Recommended Cores |
|-----------|---------------|-------------------|
| Index building | 4 cores | 8+ cores |
| Alignment | 4 cores | 8-16 cores |

**Scaling:** STAR scales nearly linearly with cores (8 cores → 8x faster)

---

## Cloud Deployment

### AWS EC2

**Recommended Instance:** `r5.2xlarge` (8 vCPU, 64GB RAM)

```bash
# Launch instance
aws ec2 run-instances \
    --instance-type r5.2xlarge \
    --image-id ami-0c55b159cbfafe1f0 \
    --key-name my-key \
    --security-group-ids sg-xxxxxxxx \
    --subnet-id subnet-xxxxxxxx

# SSH to instance
ssh -i my-key.pem ec2-user@<instance-public-ip>

# Install STAR (use conda method)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b
~/miniconda3/bin/conda install -c bioconda star

# Download genome index (see above)
```

**Cost:** ~$0.504/hour (~$30 for 60-hour alignment workflow)

### Google Cloud Platform

**Recommended Instance:** `n1-highmem-8` (8 vCPU, 52GB RAM)

```bash
# Create instance
gcloud compute instances create star-aligner \
    --machine-type=n1-highmem-8 \
    --zone=us-central1-a \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --boot-disk-size=200GB

# SSH to instance
gcloud compute ssh star-aligner --zone=us-central1-a

# Install STAR (same as AWS)
```

**Cost:** ~$0.474/hour

---

## Troubleshooting

### Issue 1: STAR Not Found

**Error:** `bash: STAR: command not found`

**Solution:**
```bash
# Verify STAR installation
which STAR

# If not found, reinstall or add to PATH
export PATH=$PATH:/path/to/STAR

# Make permanent (add to ~/.bashrc)
echo 'export PATH=$PATH:/path/to/STAR' >> ~/.bashrc
source ~/.bashrc
```

---

### Issue 2: Out of Memory (OOM) During Indexing

**Error:** `EXITING: FATAL INPUT ERROR: not enough memory for genome generation`

**Solution:**
```bash
# Reduce genomeSAindexNbases (less RAM, slower indexing)
STAR --runMode genomeGenerate \
     --genomeSAindexNbases 12 \  # Default: 14 (reduce to 12 or 10)
     --genomeDir $INDEX_DIR \
     --genomeFastaFiles $GENOME_FASTA \
     --sjdbGTFfile $GENOME_GTF

# Or use cloud instance with more RAM
```

---

### Issue 3: Out of Memory During Alignment

**Error:** `EXITING because of FATAL ERROR: not enough memory for BAM sorting`

**Solution:**
```bash
# Increase BAM sort RAM limit
STAR --limitBAMsortRAM 64000000000 \  # 64GB (default: 32GB)
     --genomeDir $INDEX_DIR \
     --readFilesIn $R2_FASTQ $R1_FASTQ

# Or reduce threads (less parallel processing)
STAR --runThreadN 4 \  # Instead of 8
     --limitBAMsortRAM 32000000000
```

---

### Issue 4: Slow Alignment

**Symptoms:** Alignment takes >2 hours for 50M reads

**Diagnosis:**
```bash
# Check if genome index is in RAM
top  # Look for STAR process using ~30GB RAM

# Check disk I/O (should be minimal during alignment)
iostat -x 1
```

**Solutions:**
1. **Increase threads:** `--runThreadN 16` (if available)
2. **Ensure index on fast disk:** SSD/NVMe (not network drive)
3. **Check for I/O bottlenecks:** Move index to local disk

---

### Issue 5: Genome Index Version Mismatch

**Error:** `EXITING because of FATAL ERROR: Genome version is incompatible with STAR version`

**Solution:**
```bash
# Rebuild index with current STAR version
STAR --runMode genomeGenerate \
     --genomeDir $INDEX_DIR \
     --genomeFastaFiles $GENOME_FASTA \
     --sjdbGTFfile $GENOME_GTF
```

---

## Alternative Aligners (Comparison)

| Aligner | Speed | RAM | Splice-Aware | Best For |
|---------|-------|-----|--------------|----------|
| **STAR** | Fast | High (32GB) | ✅ Yes | RNA-seq, spatial transcriptomics |
| HISAT2 | Moderate | Low (8GB) | ✅ Yes | RNA-seq with limited RAM |
| BWA | Fast | Moderate (16GB) | ❌ No | DNA-seq, not RNA |
| Bowtie2 | Fast | Low (4GB) | ❌ No | Short reads, not RNA |

**Recommendation:** STAR is the gold standard for spatial transcriptomics due to:
- Splice junction detection
- High sensitivity for lowly-expressed genes
- Optimized for 10x Visium/Chromium chemistry

---

## References

### Official Documentation

1. **STAR Manual:** https://github.com/alexdobin/STAR/blob/master/doc/STARmanual.pdf
2. **STAR GitHub:** https://github.com/alexdobin/STAR
3. **10x Genomics References:** https://support.10xgenomics.com/single-cell-gene-expression/software/downloads/latest

### Genome Sources

4. **GENCODE (Human):** https://www.gencodegenes.org/human/
5. **GENCODE (Mouse):** https://www.gencodegenes.org/mouse/
6. **Ensembl:** https://www.ensembl.org/info/data/ftp/index.html
7. **UCSC Genome Browser:** http://hgdownload.soe.ucsc.edu/downloads.html

### Publications

8. **STAR Paper:** Dobin et al., *Bioinformatics* 2013. [doi:10.1093/bioinformatics/bts635](https://doi.org/10.1093/bioinformatics/bts635)

---

## Support

**STAR Issues:** https://github.com/alexdobin/STAR/issues
**mcp-spatialtools Issues:** https://github.com/lynnlangit/precision-medicine-mcp/issues

---

**STAR Version Tested:** 2.7.11a
**Status:** Production-ready installation guide ✅
