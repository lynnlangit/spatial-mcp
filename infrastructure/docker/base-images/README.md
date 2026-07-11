# Base Docker Images for Precision Medicine

Three base images for bioinformatics tools.

**IMPORTANT: These images are for LOCAL USE ONLY. Do not push to Docker Hub or any remote registry.**

## Images

| Image | Purpose | Base | Size |
|-------|---------|------|------|
| `python-base` | Python bioinformatics tools | python:3.12-slim | ~500MB |
| `r-base` | R/Bioconductor analysis | rocker/r-ver:4.3.2 | ~2-3GB |
| `tensorflow-base` | ML/DL tools (GPU) | tensorflow:2.15.0 | ~8-10GB |
| `tensorflow-base` | ML/DL tools (CPU) | tensorflow:2.15.0-cpu | ~4-5GB |

## Build

**Build all images:**
```bash
docker build -t precision-medicine/python-base:latest ./python-base
docker build -t precision-medicine/r-base:latest ./r-base
docker build -t precision-medicine/tensorflow-base:latest ./tensorflow-base
```

**Verify images exist:**
```bash
docker images | grep precision-medicine
```

**Remove images:**
```bash
docker rmi precision-medicine/python-base:latest
docker rmi precision-medicine/r-base:latest
docker rmi precision-medicine/tensorflow-base:latest
```

## Security Scanning

Use your preferred vulnerability scanner to check images for security issues:

```bash
# Example with Trivy
trivy image precision-medicine/python-base:latest

# Example with Grype
grype precision-medicine/python-base:latest

# Example with Docker Scout
docker scout cves precision-medicine/python-base:latest
```

### Best Practices

1. **Run scans regularly** - Re-scan images periodically as new vulnerabilities are discovered
2. **Update base images** - Rebuild with latest base images to get security patches
3. **Focus on CRITICAL/HIGH** - Most scanners can filter by severity level

## Important Notes

- These images are designed for **local development and testing only**
- **Do not push** these images to Docker Hub, GitHub Container Registry, or any other remote registry
- Images contain standard bioinformatics tools and should be rebuilt locally as needed
- The `precision-medicine/` prefix is just for local organization, not a registry path

## Packages Included

### Python Base
- numpy, scipy, pandas, scikit-learn, statsmodels
- biopython, pysam, pyvcf3, h5py
- matplotlib, seaborn

### R Base
- tidyverse, data.table, Matrix
- DESeq2, edgeR, limma, clusterProfiler
- GenomicRanges, SummarizedExperiment

### TensorFlow Base
**Optimized for size** (reduced from ~18GB to ~8-10GB for GPU, ~4-5GB for CPU)

**Included:**
- tensorflow, keras, tensorflow-hub
- numpy, scipy, pandas, scikit-learn, scikit-image
- opencv-python-headless, Pillow, tifffile, imageio
- matplotlib, seaborn

**Removed to reduce size** (can be added back if needed):
- transformers, datasets (Hugging Face - adds ~3GB)
- cellpose (specialized imaging - adds ~500MB-1GB)

**GPU vs CPU:**
- Edit the Dockerfile to switch between GPU and CPU versions
- GPU: Full CUDA support (~8-10GB)
- CPU: Smaller, CPU-only (~4-5GB)
- Simply comment/uncomment the appropriate FROM line
