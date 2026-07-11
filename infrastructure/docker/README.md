# Docker Infrastructure

Base images for local bioinformatics and ML workflows. **Local use only — do not push to remote registries.**

## Base Images

See **[base-images/README.md](base-images/README.md)** for full details, package lists, and security scanning.

| Image | Purpose | Size |
|-------|---------|------|
| `python-base` | Python 3.12 + bioinformatics libs | ~500MB |
| `r-base` | R 4.3.2 + Bioconductor | ~2-3GB |
| `tensorflow-base` | TensorFlow 2.15 (GPU/CPU) | ~8-10GB / ~4-5GB |

## Quick Start

```bash
cd infrastructure/docker/base-images
docker build -t precision-medicine/python-base:latest ./python-base
docker build -t precision-medicine/r-base:latest ./r-base
docker build -t precision-medicine/tensorflow-base:latest ./tensorflow-base
```

## Requirements

- Docker Desktop or Docker Engine
- 15GB+ free disk (30GB+ recommended for all images)
- 8GB+ RAM (16GB+ for TensorFlow)

---

**Last Updated:** 2026-02-19
