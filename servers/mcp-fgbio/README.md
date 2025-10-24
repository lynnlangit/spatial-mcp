# mcp-FGbio

MCP server for genomic reference data using the FGbio toolkit.

## Overview

`mcp-fgbio` provides access to genomic reference databases, gene annotations, and FASTQ quality validation through the Model Context Protocol (MCP). This server integrates the FGbio Java toolkit to enable AI-driven orchestration of genomic data processing workflows.

### Key Features

- 🧬 **Reference Genome Access** - Download and manage reference genomes (hg38, mm10, hg19)
- ✅ **FASTQ Validation** - Quality control and validation of sequencing data
- 🔖 **UMI Extraction** - Extract Unique Molecular Identifiers for deduplication
- 📊 **Gene Annotations** - Query GENCODE, Ensembl, and RefSeq annotations

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) FGbio JAR file for full functionality

### Setup

1. **Create a virtual environment:**

```bash
cd servers/mcp-fgbio
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -e ".[dev]"
```

3. **Set up environment variables:**

Create a `.env` file in the server directory:

```bash
# Required directories
FGBIO_REFERENCE_DATA_DIR=/workspace/data/reference
FGBIO_CACHE_DIR=/workspace/cache

# Optional: FGbio JAR path (for real tool execution)
FGBIO_JAR_PATH=/opt/fgbio/fgbio.jar

# Optional: Performance tuning
FGBIO_TIMEOUT_SECONDS=300
FGBIO_MAX_DOWNLOAD_SIZE_GB=10

# Development mode (uses mocks instead of real tools)
FGBIO_DRY_RUN=true
```

## Usage

### Running the Server

**Standalone mode (stdio):**

```bash
python -m mcp_fgbio
```

**With Claude Desktop:**

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "fgbio": {
      "command": "python",
      "args": ["-m", "mcp_fgbio"],
      "cwd": "/path/to/spatial-mcp/servers/mcp-fgbio",
      "env": {
        "PYTHONPATH": "/path/to/spatial-mcp/servers/mcp-fgbio/src",
        "FGBIO_REFERENCE_DATA_DIR": "/path/to/data/reference",
        "FGBIO_CACHE_DIR": "/path/to/data/cache",
        "FGBIO_DRY_RUN": "true"
      }
    }
  }
}
```

## Available Tools

### 1. fetch_reference_genome

Download reference genome sequences from NCBI.

**Parameters:**
- `genome` (string): Genome identifier - `hg38`, `mm10`, or `hg19`
- `output_dir` (string): Directory for output files

**Returns:**
```json
{
  "path": "/workspace/data/reference/hg38.fna.gz",
  "size_mb": 938.2,
  "md5sum": "abc123...",
  "metadata": {
    "genome_id": "hg38",
    "name": "Human GRCh38",
    "status": "downloaded"
  }
}
```

**Example usage with Claude:**
```
Can you fetch the hg38 reference genome and save it to /workspace/data/reference?
```

### 2. validate_fastq

Validate FASTQ file format and calculate quality statistics.

**Parameters:**
- `fastq_path` (string): Path to FASTQ file (can be gzipped)
- `min_quality_score` (integer, optional): Minimum average quality score threshold (default: 20)

**Returns:**
```json
{
  "valid": true,
  "total_reads": 1000000,
  "avg_quality": 32.5,
  "avg_read_length": 150,
  "warnings": []
}
```

**Example usage with Claude:**
```
Please validate the FASTQ file at /data/sample.fastq.gz and check if the average quality is above 25.
```

### 3. extract_umis

Extract Unique Molecular Identifiers (UMIs) from FASTQ reads.

**Parameters:**
- `fastq_path` (string): Path to input FASTQ file
- `output_dir` (string): Directory for output files
- `umi_length` (integer, optional): Length of UMI sequence in bases (default: 12)
- `read_structure` (string, optional): FGbio read structure string (default: "12M+T")

**Returns:**
```json
{
  "output_fastq": "/data/processed/sample_with_umis.fastq.gz",
  "umi_count": 45000,
  "reads_processed": 1000000,
  "stats": {
    "umi_length": 12,
    "read_structure": "12M+T",
    "unique_umi_ratio": 0.045
  }
}
```

**Example usage with Claude:**
```
Extract UMIs from /data/sample_R1.fastq.gz using a 10bp UMI at the start of each read.
```

### 4. query_gene_annotations

Retrieve gene annotation data from GENCODE, Ensembl, or RefSeq.

**Parameters:**
- `genome` (string): Genome identifier (hg38, mm10, etc.)
- `gene_name` (string, optional): Gene name/symbol to search for
- `chromosome` (string, optional): Chromosome to filter (e.g., "chr1", "chrX")
- `annotation_source` (string, optional): Annotation database - `gencode`, `ensembl`, or `refseq` (default: "gencode")

**Returns:**
```json
{
  "annotations": [
    {
      "gene_name": "TP53",
      "gene_id": "ENSG00000141510",
      "chromosome": "chr17",
      "start": 7661779,
      "end": 7687550,
      "strand": "-",
      "gene_type": "protein_coding"
    }
  ],
  "total_genes": 1,
  "source": "gencode",
  "genome": "hg38"
}
```

**Example usage with Claude:**
```
What are the genomic coordinates for the BRCA1 gene in hg38?
```

## Available Resources

### reference://hg38

Metadata for the Human GRCh38 reference genome.

**Example:**
```
Claude: What information do you have about the hg38 reference genome?
```

### reference://mm10

Metadata for the Mouse GRCm38/mm10 reference genome.

### annotations://gencode

Information about the GENCODE gene annotation database.

## Development

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=src/mcp_fgbio --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_server.py -v
```

**Run only fast tests (skip integration):**
```bash
pytest -m "not integration"
```

### Code Quality

**Format code:**
```bash
black src/ tests/
```

**Lint code:**
```bash
ruff check src/ tests/
```

**Type checking:**
```bash
mypy src/
```

## Architecture

### Design Principles

1. **Single Responsibility** - Focused solely on reference data and FASTQ processing
2. **Idempotent Operations** - Tools can be safely retried
3. **Mocked Development** - Dry-run mode for testing without real data
4. **Comprehensive Validation** - All inputs validated before processing

### Directory Structure

```
mcp-fgbio/
├── src/
│   └── mcp_fgbio/
│       ├── __init__.py
│       ├── __main__.py
│       └── server.py          # Main server implementation
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_server.py         # Tool tests
│   └── test_resources.py      # Resource tests
├── pyproject.toml             # Project configuration
└── README.md
```

### Error Handling

All tools implement comprehensive error handling:

- **Input Validation** - Invalid parameters raise `ValueError`
- **File Errors** - Missing or corrupt files raise `IOError`
- **Timeout Handling** - Long operations respect timeout limits
- **Graceful Degradation** - Failures return helpful error messages

## Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `FGBIO_REFERENCE_DATA_DIR` | `/workspace/data/reference` | Directory for reference genomes |
| `FGBIO_CACHE_DIR` | `/workspace/cache` | Directory for cached files |
| `FGBIO_JAR_PATH` | `/opt/fgbio/fgbio.jar` | Path to FGbio JAR file |
| `FGBIO_JAVA_EXECUTABLE` | `java` | Java executable path |
| `FGBIO_DRY_RUN` | `false` | Enable mock mode (no real tool calls) |
| `FGBIO_LOG_LEVEL` | `INFO` | Logging level |
| `FGBIO_TIMEOUT_SECONDS` | `300` | Default operation timeout |
| `FGBIO_MAX_DOWNLOAD_SIZE_GB` | `10` | Maximum download size |

## Troubleshooting

### Server won't start

- **Check Python version:** Must be 3.11+
- **Verify dependencies:** Run `pip install -e .`
- **Check environment variables:** Ensure directories exist

### Tools return errors

- **Enable dry-run mode:** Set `FGBIO_DRY_RUN=true` for testing
- **Check file paths:** Ensure absolute paths are used
- **Review logs:** Check stderr output for details

### Performance issues

- **Increase timeout:** Set higher `FGBIO_TIMEOUT_SECONDS`
- **Allocate more memory:** Increase `FGBIO_JAVA_MEMORY_GB`
- **Use local cache:** Ensure `FGBIO_CACHE_DIR` is on fast storage

## Contributing

### Adding New Tools

1. Add tool function in `server.py` with `@mcp.tool()` decorator
2. Add comprehensive docstring with parameters and examples
3. Implement input validation
4. Add error handling
5. Create unit tests in `tests/test_server.py`
6. Update this README

### Testing Guidelines

- Aim for >80% code coverage
- Mock external dependencies (subprocess, network)
- Test both success and failure scenarios
- Use fixtures for common test data

## License

See the main repository LICENSE file.

## Support

- **Issues:** https://github.com/spatial-mcp/spatial-mcp/issues
- **Documentation:** See main repository docs/
- **MCP Specification:** https://modelcontextprotocol.io/

## Related Servers

Part of the Spatial MCP POC demonstration:

- **mcp-tcga** - TCGA cancer genomics data
- **mcp-spatialtools** - Spatial transcriptomics processing
- **mcp-huggingface** - ML models for genomics
- **mcp-seqera** - Nextflow workflow orchestration
