# Implementation Plan: Four New MCP Servers for Precision Medicine MCP Platform

> **Status:** ALL 4 SERVERS COMPLETE
> **New tools:** 23 (bringing platform from 74 to 97 tools)
> **Build order:** ~~C~~ → ~~A~~ → ~~B~~ → ~~D~~ (all done)
>
> ### Build Progress
> | Server | Status | Tools | Tests |
> |--------|--------|-------|-------|
> | C: mcp-opentargets | COMPLETE | 6/6 | 24/24 passing |
> | A: mcp-geodownload | COMPLETE | 6/6 | 22/22 passing |
> | B: mcp-cibersortx | COMPLETE | 5/5 | 19/19 passing |
> | D: mcp-neoantigen | COMPLETE | 6/6 | 30/30 passing |

---

## Server A: mcp-geodownload (GEO Download MCP)

### 1. Summary

The mcp-geodownload server provides programmatic access to NCBI GEO and SRA databases for downloading gene expression datasets. It enables searching, metadata retrieval, and downloading of expression matrices, SOFT files, and raw FASTQ files. This server is the critical data ingestion gateway: it feeds bulk RNA-seq expression matrices into the CIBERSORTx deconvolution pipeline and provides reference cohort data (GSE32062, GSE26712) for HGSOC comparison studies.

### 2. Recommended Implementation

FastMCP Python, consistent with all 13 existing servers in the repository. This server follows the same pattern as `mcp-genomic-results` (lightweight, no config.py, uses `os.getenv` directly) since it primarily wraps external REST APIs without complex internal state. The boilerplate template at `servers/mcp-server-boilerplate/` provides the exact scaffolding. All tools are async functions decorated with `@mcp.tool()`, returning `Dict[str, Any]` with the established `status`/`data`/`metadata` structure.

### 3. File and Directory Structure

```
servers/mcp-geodownload/
    README.md
    pyproject.toml
    Dockerfile
    src/
        mcp_geodownload/
            __init__.py          # __version__ = "0.1.0"
            __main__.py          # from .server import main; main()
            server.py            # 6 @mcp.tool() functions + main()
            geo_client.py        # GEO/Entrez API client (aiohttp)
            sra_client.py        # SRA toolkit wrapper (subprocess)
            parsers.py           # SOFT/Series Matrix file parsers
    tests/
        test_server.py           # DRY_RUN smoke tests per tool
        fixtures/
            sample_soft.txt      # Minimal SOFT fixture
            sample_series_matrix.txt  # Minimal Series Matrix fixture
```

### 4. Tool Definitions Table

| Tool Name | Input Parameters | Return Value | Notes |
|-----------|-----------------|--------------|-------|
| `search_geo_datasets` | `query: str`, `organism: str = "Homo sapiens"`, `study_type: str = "Expression profiling by high throughput sequencing"`, `max_results: int = 20` | `{"status": "success", "datasets": [{"gse_id": "GSE32062", "title": "...", "summary": "...", "organism": "...", "n_samples": 260, "platform": "GPL570"}], "total_count": 145}` | Uses Entrez E-utilities `esearch` + `esummary`. URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term={query}` |
| `get_geo_metadata` | `gse_id: str` | `{"status": "success", "gse_id": "GSE32062", "title": "...", "abstract": "...", "samples": [...], "platform": "GPL570", "supplementary_files": [...], "pubmed_ids": [...]}` | Uses GEOparse library or Entrez `esummary` for db=gds. Falls back to raw SOFT parsing. |
| `download_geo_expression_matrix` | `gse_id: str`, `output_dir: str = "/data/cache/geodownload"`, `normalize: bool = False` | `{"status": "success", "output_path": "/data/cache/geodownload/GSE32062_series_matrix.csv", "shape": [20000, 260], "genes": 20000, "samples": 260}` | Downloads Series Matrix from `https://ftp.ncbi.nlm.nih.gov/geo/series/GSEnnn/GSEnnnnnn/matrix/`. Parses with pandas. |
| `list_geo_samples` | `gse_id: str`, `include_metadata: bool = True` | `{"status": "success", "gse_id": "GSE32062", "samples": [{"gsm_id": "GSM793463", "title": "...", "source": "...", "characteristics": {...}}], "sample_count": 260}` | Extracts from SOFT metadata. Each GSM has source, characteristics, platform. |
| `download_sra_fastq` | `srr_id: str`, `output_dir: str = "/data/cache/geodownload"`, `split_files: bool = True` | `{"status": "success", "srr_id": "SRR12345678", "output_files": [...], "total_size_gb": 12.5, "warning": "Large download"}` | Wraps `prefetch` + `fasterq-dump` via subprocess. Must emit size warning for files >5GB. Production-only (mock returns immediately). |
| `get_geo_soft_file` | `gse_id: str`, `output_dir: str = "/data/cache/geodownload"` | `{"status": "success", "output_path": "/data/cache/geodownload/GSE32062_family.soft.gz", "file_size_mb": 45.2}` | Downloads raw SOFT from `https://ftp.ncbi.nlm.nih.gov/geo/series/GSEnnn/GSEnnnnnn/soft/`. |

### 5. Authentication and Configuration

```python
# Environment variables (simple os.getenv, no Pydantic BaseSettings needed)
GEO_DRY_RUN = os.getenv("GEO_DRY_RUN", "true").lower() == "true"
GEO_DATA_DIR = os.getenv("GEO_DATA_DIR", "/data/geodownload")
GEO_CACHE_DIR = os.getenv("GEO_CACHE_DIR", "/data/cache/geodownload")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")  # Optional, raises rate limit from 3 to 10 req/sec
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")  # Required by NCBI policy for Entrez usage
```

No Pydantic BaseSettings needed — use simple `os.getenv` pattern matching `mcp-genomic-results`. NCBI API key is optional but recommended.

### 6. External Dependencies

**pip packages:**
- `fastmcp>=0.2.0`
- `pydantic>=2.0.0`
- `aiohttp>=3.9.0` (async HTTP client for Entrez E-utilities)
- `GEOparse>=2.0.0` (GEO metadata parsing)
- `pandas>=2.0.0` (Series Matrix parsing)
- `numpy>=1.24.0`

**System tools (production mode only):**
- `sra-tools` (provides `prefetch`, `fasterq-dump`) — only for `download_sra_fastq`

**Specific API endpoints:**
- `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term={query}&retmax={max_results}&api_key={key}`
- `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gds&id={uid}&api_key={key}`
- `https://ftp.ncbi.nlm.nih.gov/geo/series/GSEnnn/GSEnnnnnn/matrix/` (Series Matrix FTP)
- `https://ftp.ncbi.nlm.nih.gov/geo/series/GSEnnn/GSEnnnnnn/soft/` (SOFT FTP)

### 7. Mock / Fallback Strategy

In DRY_RUN mode (default), every tool returns clinically relevant HGSOC synthetic data:
- `search_geo_datasets` returns 3 known HGSOC datasets: GSE32062 (Tothill 2008, 260 samples), GSE26712 (Bonome 2008, 185 samples), GSE9899 (AOCS, 285 samples)
- `download_geo_expression_matrix` returns synthetic CSV path, shape `[20000, 260]`, and mock gene list
- `download_sra_fastq` returns immediately with file paths and size estimate (never runs SRA toolkit)
- All mock responses include the standard `add_dry_run_warning()` wrapper

### 8. Key Risk / Mitigation

**Risk:** NCBI rate limits (3 requests/second without key, 10 with) will cause `429 Too Many Requests` during batch operations.
**Mitigation:** Use the existing `shared/utils/api_retry.py` `retry_with_backoff` decorator with `base_delay=0.35` and `max_retries=5`. Implement token-bucket rate limiter in `geo_client.py` using `asyncio.Semaphore`. Accept `NCBI_API_KEY` env var to raise limits.

**Risk:** FASTQ downloads can be 10-50GB, filling disk.
**Mitigation:** `download_sra_fastq` must check available disk space before download, emit size warnings, and support `max_size_gb` parameter with default of 50GB.

### 9. Estimated Implementation Effort

**Medium (M)** — 3-5 days. The Entrez APIs are well-documented REST endpoints. GEOparse handles the complex SOFT parsing. The SRA toolkit integration is subprocess calls with error handling.

---

## Server B: mcp-cibersortx (CIBERSORTx MCP)

### 1. Summary

The mcp-cibersortx server provides cell-type deconvolution capabilities via the Stanford CIBERSORTx web API. Given a bulk RNA-seq expression matrix (such as one downloaded via mcp-geodownload), it infers the fractional abundances of immune and stromal cell types present in each sample. For the HGSOC use case, this reveals the tumor microenvironment composition — CD8+ T cells, tumor-associated macrophages (TAMs), regulatory T cells (Tregs), NK cells, and cancer-associated fibroblasts (CAFs) — which directly informs immunotherapy responsiveness scoring.

### 2. Recommended Implementation

FastMCP Python with Pydantic BaseSettings for config, matching the `mcp-multiomics` pattern (since this server has complex auth + long-running async job management). The server needs a polling loop for CIBERSORTx job status, which maps naturally to the async patterns already used throughout the codebase. The `scipy.optimize.nnls` local fallback provides an essential offline mode.

### 3. File and Directory Structure

```
servers/mcp-cibersortx/
    README.md
    pyproject.toml
    Dockerfile
    src/
        mcp_cibersortx/
            __init__.py          # __version__ = "0.1.0"
            __main__.py          # from .server import main; main()
            server.py            # 5 @mcp.tool() functions + main()
            config.py            # CIBERSORTxConfig(BaseSettings)
            api_client.py        # CIBERSORTx REST API client
            nnls_fallback.py     # scipy.optimize.nnls local deconvolution
            signature_matrices.py # Built-in LM22 and custom HGSOC matrix definitions
    tests/
        test_server.py
        test_nnls_fallback.py
        fixtures/
            sample_mixture.csv
            sample_signature.csv
```

### 4. Tool Definitions Table

| Tool Name | Input Parameters | Return Value | Notes |
|-----------|-----------------|--------------|-------|
| `run_cibersortx_deconvolution` | `mixture_path: str`, `signature_matrix: str = "LM22"`, `custom_signature_path: Optional[str] = None`, `permutations: int = 100`, `quantile_normalize: bool = True` | `{"status": "success", "job_id": "cb-12345", "fractions": {"Sample_01": {"CD8_T_cells": 0.12, "TAMs_M2": 0.35, ...}}, "p_values": {...}, "rmse": {...}}` | Main tool. In production, submits to CIBERSORTx API, polls every 30s, returns when complete. In DRY_RUN, returns HGSOC-relevant synthetic fractions. |
| `upload_signature_matrix` | `matrix_path: str`, `matrix_name: str`, `description: str = ""` | `{"status": "success", "matrix_id": "sig-custom-001", "genes": 547, "cell_types": 12, "upload_size_kb": 245}` | Uploads custom scRNA-seq-derived signature matrix to CIBERSORTx. Validates format (genes x cell_types CSV) before upload. |
| `get_job_status` | `job_id: str` | `{"status": "success", "job_id": "cb-12345", "state": "RUNNING", "progress_pct": 65, "estimated_remaining_seconds": 180, "submitted_at": "..."}` | Polls CIBERSORTx job status API. States: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`. |
| `download_results` | `job_id: str`, `output_dir: str = "/data/cache/cibersortx"` | `{"status": "success", "output_path": "/data/cache/cibersortx/cb-12345_results.csv", "fractions": {...}, "summary": {"n_samples": 260, "n_cell_types": 22}}` | Downloads completed job results. Returns fractions matrix as dict + saves CSV. |
| `run_mock_deconvolution` | `mixture_path: str`, `signature_path: str`, `output_dir: Optional[str] = None` | `{"status": "success", "method": "scipy_nnls", "fractions": {...}, "rmse": {...}, "warning": "Approximate method, not CIBERSORTx-grade"}` | Always runs locally using scipy NNLS. Does not require token. Used for testing and when CIBERSORTx API is unavailable. |

### 5. Authentication and Configuration

```python
class CIBERSORTxConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CIBERSORTX_", env_file=".env")

    token: str = Field(default="", description="CIBERSORTx API token from Stanford")
    email: str = Field(default="", description="Email registered with CIBERSORTx")
    api_url: str = Field(
        default="https://cibersortx.stanford.edu/api",
        description="CIBERSORTx API base URL",
    )
    dry_run: bool = Field(default=True)
    data_dir: Path = Field(default=Path("/data/cibersortx"))
    cache_dir: Path = Field(default=Path("/data/cache/cibersortx"))
    poll_interval_seconds: int = Field(default=30, ge=10, le=120)
    max_wait_seconds: int = Field(default=1800, ge=300, le=7200)  # 30 min default
```

**Env vars:** `CIBERSORTX_TOKEN`, `CIBERSORTX_EMAIL`, `CIBERSORTX_DRY_RUN`, `CIBERSORTX_API_URL`.
Token is required for production mode; the server raises `ValueError` at startup if `DRY_RUN=false` and no token is set.

**CIBERSORTx API endpoint patterns:**
- `POST https://cibersortx.stanford.edu/api/submit` — submit job (multipart form: mixture file + signature matrix + params)
- `GET https://cibersortx.stanford.edu/api/status/{job_id}` — poll job status
- `GET https://cibersortx.stanford.edu/api/results/{job_id}` — download results
- `POST https://cibersortx.stanford.edu/api/signature/upload` — upload custom signature matrix

### 6. External Dependencies

**pip packages:**
- `fastmcp>=0.2.0`, `pydantic>=2.0.0`, `pydantic-settings>=2.0.0`
- `aiohttp>=3.9.0` (async HTTP for CIBERSORTx API)
- `pandas>=2.0.0`, `numpy>=1.24.0`
- `scipy>=1.11.0` (for `scipy.optimize.nnls` fallback)

**No system tools required.** CIBERSORTx is a web service.

### 7. Mock / Fallback Strategy

**DRY_RUN mode:** Returns biologically realistic HGSOC immune fractions: high TAM-M2 (30-40%), low CD8+ T cells (5-15%), moderate Tregs (3-8%), low NK cells (2-5%), elevated CAFs (10-20%). These match published deconvolution results from HGSOC cohorts (TCGA-OV, GSE32062).

**Local fallback (`run_mock_deconvolution`):** Always available regardless of DRY_RUN setting. Uses `scipy.optimize.nnls(signature_matrix, mixture_sample)` per sample. This provides approximate deconvolution without Stanford API access. Return values include explicit warning that results are approximate.

### 8. Key Risk / Mitigation

**Risk:** CIBERSORTx jobs take 5-30 minutes, and the MCP tool call must return within a reasonable time.
**Mitigation:** Implement two patterns: (1) `run_cibersortx_deconvolution` does submit + poll loop with configurable `max_wait_seconds`, and (2) split workflow using `get_job_status` for explicit polling. The tool returns early with `job_id` if polling times out, and `download_results` retrieves completed results later.

**Risk:** Token authentication may expire or get rate-limited.
**Mitigation:** Use `shared/utils/api_retry.py` `CircuitBreaker` pattern with `failure_threshold=3`, `recovery_timeout=300` to prevent hammering a failing API. Validate token format at startup.

### 9. Estimated Implementation Effort

**Large (L)** — 5-8 days. The async polling loop, token auth, multipart file upload, and local NNLS fallback each require careful implementation and testing. The CIBERSORTx API documentation is not publicly detailed, requiring some reverse-engineering.

---

## Server C: mcp-opentargets (Open Targets MCP) — COMPLETE

> Built: 10 files, 6 tools, 24 tests passing. Location: `servers/mcp-opentargets/`

### 1. Summary

The mcp-opentargets server queries the Open Targets Platform GraphQL API to retrieve target validation evidence, drug associations, safety data, and clinical evidence for gene targets. For the HGSOC use case, it takes the 30+ immunotherapy and targeted therapy gene targets identified by Stouffer's meta-analysis (from mcp-multiomics) and retrieves their drug development status, clinical trial evidence, safety profiles, and association scores with ovarian carcinoma (EFO:0001071). This is the "drug-to-target" bridge that transforms bioinformatics findings into actionable therapeutic recommendations.

### 2. Recommended Implementation

FastMCP Python with simple `os.getenv` config (matching `mcp-genomic-results` pattern), since the Open Targets GraphQL API is public with no authentication. The server is stateless and each tool makes independent GraphQL queries. Use `aiohttp` for async HTTP requests. The server should include a `graphql_client.py` module containing all query templates as Python string constants.

### 3. File and Directory Structure

```
servers/mcp-opentargets/
    README.md
    pyproject.toml
    Dockerfile
    src/
        mcp_opentargets/
            __init__.py          # __version__ = "0.1.0"
            __main__.py          # from .server import main; main()
            server.py            # 6 @mcp.tool() functions + main()
            graphql_client.py    # GraphQL query templates + async executor
            disease_ontology.py  # EFO ID mappings for common diseases
    tests/
        test_server.py
        test_graphql_client.py
        fixtures/
            sample_target_response.json
            sample_association_response.json
```

### 4. Tool Definitions Table

| Tool Name | Input Parameters | Return Value | Notes |
|-----------|-----------------|--------------|-------|
| `get_target_info` | `gene_symbol: str = ""`, `ensembl_id: str = ""` | `{"status": "success", "target": {"id": "ENSG00000141510", "symbol": "TP53", "name": "Tumor protein p53", "description": "...", "biotype": "protein_coding", "tractability": {"smallMolecule": 0.7, "antibody": 0.3}}}` | Accepts either gene symbol or Ensembl ID. GraphQL `target` query. |
| `get_target_disease_associations` | `gene_symbol: str`, `disease_id: str = "EFO_0001071"`, `top_n: int = 10` | `{"status": "success", "target": "TP53", "disease": "ovarian carcinoma", "overall_score": 0.87, "evidence_scores": {"literature": 0.92, "rna_expression": 0.85, "genetic_association": 0.78, "somatic_mutation": 0.95, "known_drug": 0.45, "animal_model": 0.60, "affected_pathway": 0.88}}` | Uses `associatedDiseases` query with EFO ID. Default disease is ovarian carcinoma. |
| `get_target_drugs` | `gene_symbol: str`, `phase_min: int = 0` | `{"status": "success", "target": "PIK3CA", "drugs": [{"name": "Alpelisib", "phase": 4, "status": "Approved", "mechanism": "PI3K alpha inhibitor", "indications": ["breast cancer"], "clinical_trial_count": 45}]}` | Uses `knownDrugs` query. `phase_min` filters by minimum clinical phase (0-4). |
| `search_targets_by_disease` | `disease_id: str = "EFO_0001071"`, `top_n: int = 25`, `evidence_type: Optional[str] = None` | `{"status": "success", "disease": "ovarian carcinoma", "targets": [{"symbol": "TP53", "score": 0.87, "top_evidence": "somatic_mutation"}, ...]}` | Uses `disease` query with `associatedTargets`. Evidence types: `literature`, `rna_expression`, `genetic_association`, `somatic_mutation`, `known_drug`. |
| `get_target_safety` | `gene_symbol: str` | `{"status": "success", "target": "VEGFA", "safety_liabilities": [{"event": "Hypertension", "biosamples": ["cardiovascular"], "effects": [...]}], "adverse_events": [...], "risk_level": "moderate"}` | Uses `targetSafety` query. Returns adverse event profiles and organ-specific risks. |
| `batch_score_targets` | `gene_symbols: List[str]`, `disease_id: str = "EFO_0001071"` | `{"status": "success", "disease": "ovarian carcinoma", "scores": {"TP53": 0.87, "PIK3CA": 0.72, "PTEN": 0.68, ...}, "druggable_targets": ["PIK3CA", "VEGFA"], "novel_targets": ["CDK12"]}` | Batches multiple gene lookups. Chunks into groups of 10 to avoid query complexity limits. |

### 5. Authentication and Configuration

```python
# Environment variables (simple os.getenv, no Pydantic BaseSettings needed)
OPENTARGETS_DRY_RUN = os.getenv("OPENTARGETS_DRY_RUN", "true").lower() == "true"
OPENTARGETS_API_URL = os.getenv(
    "OPENTARGETS_API_URL",
    "https://api.platform.opentargets.org/api/v4/graphql",
)
OPENTARGETS_CACHE_DIR = os.getenv("OPENTARGETS_CACHE_DIR", "/data/cache/opentargets")
```

**No authentication required.** The Open Targets Platform API is public and free. Rate limiting is handled by the API itself (generous limits for normal usage).

**Specific GraphQL query structures:**

```graphql
# get_target_info
query TargetInfo($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    approvedName
    biotype
    description
    tractability {
      label
      modality
      value
    }
  }
}

# get_target_disease_associations
query TargetDiseaseAssociation($ensemblId: String!, $efoId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    associatedDiseases(page: {size: 50}) {
      rows {
        disease { id name }
        score
        datasourceScores {
          id
          score
        }
      }
    }
  }
}

# get_target_drugs
query TargetDrugs($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    knownDrugs(size: 100) {
      rows {
        drug { id name }
        phase
        status
        mechanismOfAction
        disease { id name }
        urls { url name }
      }
    }
  }
}

# search_targets_by_disease
query DiseaseTargets($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    associatedTargets(page: {size: $size, index: 0}) {
      rows {
        target { id approvedSymbol }
        score
        datasourceScores { id score }
      }
    }
  }
}
```

**Gene symbol to Ensembl ID resolution:** The server needs a `_resolve_gene_symbol` helper that queries the Open Targets `search` endpoint: `query Search($query: String!) { search(queryString: $query, entityNames: ["target"]) { hits { id ... on Target { approvedSymbol } } } }`. Cache results in-memory for the session.

### 6. External Dependencies

**pip packages:**
- `fastmcp>=0.2.0`, `pydantic>=2.0.0`
- `aiohttp>=3.9.0` (async HTTP for GraphQL)

Intentionally minimal. No pandas/numpy needed since this server only processes JSON.

### 7. Mock / Fallback Strategy

**DRY_RUN mode** returns hardcoded data for the HGSOC gene panel from the existing `annotations.py` in `mcp-genomic-results`. The mock covers all genes in `OVC_GENE_PANEL`: TP53, PIK3CA, PTEN, BRCA1, BRCA2, MYC, CCNE1, AKT2, RB1, CDKN2A, BRAF, KRAS, ARID1A, VEGFA, CDK12. Mock association scores and drug lists reflect real Open Targets data (as of 2025) for ovarian carcinoma.

**EFO disease ontology mapping** is hardcoded in `disease_ontology.py`:
```python
DISEASE_IDS = {
    "ovarian carcinoma": "EFO_0001071",
    "high-grade serous ovarian carcinoma": "EFO_0001071",
    "breast carcinoma": "EFO_0000305",
    "lung adenocarcinoma": "EFO_0000571",
    # ... more mappings
}
```

### 8. Key Risk / Mitigation

**Risk:** GraphQL query complexity limits. Open Targets may reject queries requesting too many nested fields or too many targets in batch.
**Mitigation:** `batch_score_targets` chunks gene lists into groups of 10 and makes sequential requests. Each individual query is kept simple with explicit field selection (no open-ended wildcards).

**Risk:** Gene symbol to Ensembl ID resolution failures for aliases or non-standard symbols.
**Mitigation:** The `_resolve_gene_symbol` function first checks a local lookup table of common HGSOC genes, then falls back to the Open Targets search API. If resolution fails, return a clear error message listing the unresolved symbol.

### 9. Estimated Implementation Effort

**Small-Medium (S-M)** — 2-4 days. The Open Targets GraphQL API is well-documented, public, and requires no authentication. The main complexity is crafting correct GraphQL queries and handling the response shape variations across different query types.

---

## Server D: mcp-neoantigen (Neoantigen MCP)

### 1. Summary

The mcp-neoantigen server predicts neoantigen burden and HLA-peptide binding from somatic mutations. It takes VCF data (from mcp-genomic-results `parse_somatic_variants`) and HLA typing to predict which tumor-specific peptides are likely to be presented by MHC molecules, estimating the patient's neoantigen load. This is critical for scoring the antigen presentation pathway component of the PatientOne immunotherapy responsiveness analysis. The server integrates with IEDB, NetMHCpan, pVACtools, and OptiType, with graceful fallbacks at each layer.

### 2. Recommended Implementation

FastMCP Python with Pydantic BaseSettings for config (matching `mcp-multiomics`), since this server has complex multi-API integration, local tool execution paths, and needs careful configuration of external tool paths. The server architecture follows the `_impl` function pattern from `mcp-genomic-results` where thin MCP tool wrappers call implementation functions, enabling direct testing without the MCP decorator layer.

### 3. File and Directory Structure

```
servers/mcp-neoantigen/
    README.md
    pyproject.toml
    Dockerfile
    src/
        mcp_neoantigen/
            __init__.py          # __version__ = "0.1.0"
            __main__.py          # from .server import main; main()
            server.py            # 6 @mcp.tool() functions + main()
            config.py            # NeoantigenConfig(BaseSettings)
            iedb_client.py       # IEDB REST API client (async)
            pvactools_wrapper.py # pVACseq local execution wrapper
            optitype_wrapper.py  # OptiType HLA typing wrapper
            hla_utils.py         # HLA allele format conversion utilities
            peptide_generator.py # Extract mutant peptides from VCF
    tests/
        test_server.py
        test_iedb_client.py
        test_peptide_generator.py
        test_hla_utils.py
        fixtures/
            sample_vcf_peptides.csv
            sample_iedb_response.json
```

### 4. Tool Definitions Table

| Tool Name | Input Parameters | Return Value | Notes |
|-----------|-----------------|--------------|-------|
| `predict_mhc1_binding` | `peptides: List[str]`, `hla_alleles: List[str]`, `method: str = "netmhcpan_ba"`, `length: int = 9` | `{"status": "success", "predictions": [{"peptide": "RMPEAAPPV", "allele": "HLA-A*02:01", "ic50_nm": 45.2, "percentile_rank": 0.8, "binder": true}], "strong_binders": 3, "weak_binders": 7, "total_peptides": 25}` | Uses IEDB API: `POST http://tools-cluster-interface.iedb.org/tools_api/mhci/`. Method options: `netmhcpan_ba`, `netmhcpan_el`, `ann`, `smm`. Chunks peptides into batches of 100. |
| `predict_mhc2_binding` | `peptides: List[str]`, `hla_alleles: List[str]`, `method: str = "netmhciipan"`, `length: int = 15` | `{"status": "success", "predictions": [...], "strong_binders": 2, "weak_binders": 5}` | Uses IEDB API: `POST http://tools-cluster-interface.iedb.org/tools_api/mhcii/`. HLA-DRB1, HLA-DPA1/DPB1, HLA-DQA1/DQB1 alleles. |
| `run_pvacseq` | `vcf_path: str`, `hla_alleles: List[str]`, `output_dir: str = "/data/cache/neoantigen"`, `epitope_lengths: List[int] = [8, 9, 10, 11]`, `binding_threshold: float = 500.0` | `{"status": "success", "output_path": "...", "total_neoantigens": 45, "strong_binders": 12, "top_neoantigens": [{"gene": "TP53", "mutation": "R175H", "peptide": "...", "hla": "HLA-A*02:01", "binding_affinity": 35.2}]}` | Wraps local pVACtools via subprocess. Falls back to IEDB API if pVACtools not installed. |
| `estimate_neoantigen_burden` | `tmb_mutations_per_mb: float`, `hla_alleles: Optional[List[str]] = None`, `cancer_type: str = "HGSOC"` | `{"status": "success", "tmb": 3.5, "estimated_neoantigens": 42, "estimated_strong_binders": 8, "conversion_factor": 12.0, "cancer_type": "HGSOC", "interpretation": "Low-moderate neoantigen burden for HGSOC"}` | Uses published TMB-to-neoantigen conversion factors (Samstein et al. 2019). HGSOC factor: ~12 neoantigens per mutation/Mb. No API call needed. |
| `get_hla_typing_from_rna` | `bam_path: str`, `output_dir: str = "/data/cache/neoantigen"` | `{"status": "success", "hla_alleles": {"HLA-A": ["A*02:01", "A*03:01"], "HLA-B": ["B*07:02", "B*44:02"], "HLA-C": ["C*07:02", "C*05:01"]}, "method": "OptiType", "confidence": 0.95}` | Wraps OptiType via subprocess. Requires samtools + OptiType installation. Returns 6 HLA class I alleles. |
| `score_antigen_presentation_pathway` | `neoantigen_count: int`, `mhc1_expression: Optional[Dict[str, float]] = None`, `b2m_expression: Optional[float] = None`, `tap1_expression: Optional[float] = None`, `tap2_expression: Optional[float] = None`, `hla_loh: bool = False` | `{"status": "success", "pathway_score": 0.72, "components": {"neoantigen_score": 0.65, "mhc_expression_score": 0.80, "antigen_processing_score": 0.85, "hla_integrity_score": 1.0}, "interpretation": "Moderate antigen presentation capacity", "recommendation": "Checkpoint inhibitor may have moderate benefit"}` | Integrative scoring function. No external API — combines inputs from other tools into composite score. Uses weighted average with published weights. |

### 5. Authentication and Configuration

```python
class NeoantigenConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NEOANTIGEN_", env_file=".env")

    dry_run: bool = Field(default=True)
    data_dir: Path = Field(default=Path("/data/neoantigen"))
    cache_dir: Path = Field(default=Path("/data/cache/neoantigen"))

    # IEDB API (no auth needed)
    iedb_api_url: str = Field(
        default="http://tools-cluster-interface.iedb.org/tools_api"
    )
    iedb_batch_size: int = Field(default=100, ge=10, le=500)

    # pVACtools (local)
    pvactools_path: Optional[str] = Field(
        default=None, description="Path to pVACseq binary"
    )

    # OptiType (local)
    optitype_path: Optional[str] = Field(
        default=None, description="Path to OptiType"
    )
    samtools_path: str = Field(default="samtools", description="Path to samtools")

    # Binding thresholds
    strong_binder_threshold: float = Field(
        default=50.0, description="IC50 nM for strong binder"
    )
    weak_binder_threshold: float = Field(
        default=500.0, description="IC50 nM for weak binder"
    )

    log_level: str = Field(default="INFO")
```

**Env vars:** `NEOANTIGEN_DRY_RUN`, `NEOANTIGEN_PVACTOOLS_PATH`, `NEOANTIGEN_OPTITYPE_PATH`, `NEOANTIGEN_IEDB_API_URL`.

**Specific IEDB API endpoints:**
- `POST http://tools-cluster-interface.iedb.org/tools_api/mhci/` — MHC class I binding prediction
  - Body: `method=netmhcpan_ba&sequence_text={peptides}&allele={hla}&length={length}`
- `POST http://tools-cluster-interface.iedb.org/tools_api/mhcii/` — MHC class II binding prediction
  - Body: `method=netmhciipan&sequence_text={peptides}&allele={hla}&length={length}`
- `POST http://tools-cluster-interface.iedb.org/tools_api/processing/` — proteasomal cleavage + TAP transport

**HLA allele format conversion** (critical utility):
```python
# hla_utils.py
def normalize_hla_allele(allele: str) -> str:
    """Convert between HLA naming formats.
    'HLA-A*02:01' -> 'HLA-A*02:01'  (already normalized)
    'A0201' -> 'HLA-A*02:01'
    'A*02:01' -> 'HLA-A*02:01'
    'HLA-A02:01' -> 'HLA-A*02:01'
    """
```

### 6. External Dependencies

**pip packages:**
- `fastmcp>=0.2.0`, `pydantic>=2.0.0`, `pydantic-settings>=2.0.0`
- `aiohttp>=3.9.0` (async HTTP for IEDB API)
- `pandas>=2.0.0`, `numpy>=1.24.0`
- `biopython>=1.83` (optional, for peptide sequence handling)

**System tools (production mode, all optional with fallbacks):**
- `pVACtools` >= 4.0 (provides `pvacseq`) — falls back to direct IEDB API calls
- `OptiType` (for HLA typing from RNA-seq) — falls back to user-provided HLA alleles
- `samtools` (required by OptiType) — only needed if OptiType is installed

### 7. Mock / Fallback Strategy

**DRY_RUN mode** returns PatientOne-specific mock data:
- HLA type: `HLA-A*02:01, HLA-A*03:01, HLA-B*07:02, HLA-B*44:02, HLA-C*07:02, HLA-C*05:01`
- Neoantigens from TP53 R175H, PIK3CA E545K mutations with realistic binding predictions
- Neoantigen burden estimate: ~42 neoantigens from TMB of 3.5 mut/Mb
- Pathway score: 0.72 (moderate) — reflecting HGSOC's typical partial antigen presentation

**Multi-layer fallback chain (production mode):**
1. `run_pvacseq` tries pVACtools locally -> falls back to IEDB API per-peptide
2. `get_hla_typing_from_rna` tries OptiType -> falls back to requiring user-provided HLA alleles
3. `predict_mhc1_binding` tries IEDB API -> returns error with suggestion to check network

**Peptide generation from VCF** (`peptide_generator.py`):
- Parse missense variants from VCF using the existing `_parse_vcf_file` pattern from `mcp-genomic-results`
- Generate 8-11mer peptide windows around each mutation
- Requires reference protein sequences (from `mcp-fgbio` reference data or Ensembl REST API)

### 8. Key Risk / Mitigation

**Risk:** IEDB API has per-peptide rate limits and can be slow for large peptide sets (>1000 peptides).
**Mitigation:** Chunk peptides into batches of 100 (configurable via `NEOANTIGEN_IEDB_BATCH_SIZE`). Use `asyncio.gather` with semaphore to parallelize batches while respecting rate limits. Use `shared/utils/api_retry.py` with `max_retries=3, base_delay=2.0`.

**Risk:** HLA allele format inconsistencies across tools (IEDB, NetMHCpan, OptiType, pVACtools all use slightly different formats).
**Mitigation:** Centralized `hla_utils.py` with `normalize_hla_allele()` function called at every API/tool boundary. Comprehensive test coverage for format conversion.

**Risk:** pVACtools and OptiType are complex to install with many dependencies.
**Mitigation:** These are optional. The Dockerfile installs them, but local development uses IEDB API fallback. Mock mode works without any external tools.

### 9. Estimated Implementation Effort

**Extra-Large (XL)** — 8-12 days. This server has the highest complexity: multiple external APIs (IEDB MHC-I, IEDB MHC-II), local tool wrappers (pVACtools, OptiType), a peptide generation pipeline requiring reference sequences, HLA format normalization, and a multi-component integrative scoring function. Each layer needs its own fallback path.

---

## 10. Recommended Build Order

**Build order: C -> A -> B -> D**

1. **~~Server C: mcp-opentargets~~ — COMPLETE**
   - 6 tools, 24 tests, all passing
   - `servers/mcp-opentargets/` — ready for integration

2. **~~Server A: mcp-geodownload~~ — COMPLETE**
   - 6 tools, 22 tests, all passing
   - `servers/mcp-geodownload/` — ready for integration

3. **~~Server B: mcp-cibersortx~~ — COMPLETE**
   - 5 tools, 19 tests, all passing
   - `servers/mcp-cibersortx/` — ready for integration

4. **~~Server D: mcp-neoantigen~~ — COMPLETE**
   - 6 tools, 30 tests, all passing
   - `servers/mcp-neoantigen/` — ready for integration

**Total estimated effort: 18-29 developer-days**

---

## Cross-Server Integration Notes

### Data Flow Pipelines

**Pipeline 1: Cohort Deconvolution (GEO -> CIBERSORTx -> Multi-Omics)**
```
mcp-geodownload                    mcp-cibersortx                     mcp-multiomics
  search_geo_datasets("HGSOC")       run_cibersortx_deconvolution       calculate_stouffer_meta
  -> GSE32062, GSE26712                (mixture=GSE32062_matrix.csv,      (p_values from HAllA
  download_geo_expression_matrix       signature=LM22)                     + deconvolution fractions)
  -> /data/cache/GSE32062.csv        -> immune cell fractions per sample  -> integrated significance
```
The expression matrix downloaded by `mcp-geodownload.download_geo_expression_matrix` is the direct input to `mcp-cibersortx.run_cibersortx_deconvolution`. The resulting cell-type fractions feed into `mcp-multiomics.calculate_stouffer_meta` as additional evidence layers for multi-omics meta-analysis.

**Pipeline 2: Variant to Neoantigen (Genomic-Results -> Neoantigen)**
```
mcp-genomic-results                mcp-neoantigen
  parse_somatic_variants             predict_mhc1_binding
  (vcf_path=PAT001 VCF)              (peptides from TP53_R175H, PIK3CA_E545K)
  -> somatic_mutations list          -> binding predictions
  -> provides GENE, EFFECT,          estimate_neoantigen_burden
     protein changes                  (tmb=3.5 mut/Mb)
                                    -> 42 estimated neoantigens
                                    score_antigen_presentation_pathway
                                    -> pathway score 0.72
```
The `parse_somatic_variants` output from `mcp-genomic-results` (specifically the `gene`, `effect`, and `id` fields like `TP53_R175H`) feeds directly into `mcp-neoantigen.peptide_generator` to extract mutant peptides for binding prediction. The PAT001 VCF at `data/patient-data/PAT001-OVC-2025/genomics/somatic_variants.vcf` is the reference input file.

**Pipeline 3: Target Validation (Multi-Omics -> Open Targets -> Patient Report)**
```
mcp-multiomics                     mcp-opentargets                    mcp-patient-report
  predict_upstream_regulators        batch_score_targets                generate_patient_report
  -> significant kinases, TFs         (gene_symbols=                    (findings from all servers)
  -> drug candidates                   [AKT1, MTOR, TP53, MYC, ...],
  calculate_stouffer_meta              disease_id="EFO_0001071")
  -> q_values for significant        -> association scores
     features                        -> approved drugs
                                     -> safety profiles
                                     get_target_drugs
                                     -> drug mechanism of action
```
The significant genes from `mcp-multiomics.calculate_stouffer_meta` (those with `q_value < 0.05`) and `predict_upstream_regulators` (kinases like AKT1, TFs like TP53) are the input gene list for `mcp-opentargets.batch_score_targets`. The Open Targets association scores, drug lists, and safety profiles then feed into `mcp-patient-report` for the final patient summary.

**Pipeline 4: Immunotherapy Responsiveness (Neoantigen + CIBERSORTx + Multi-Omics)**
```
mcp-neoantigen                     mcp-cibersortx                     Integrative Score
  score_antigen_presentation_pathway  run_cibersortx_deconvolution      (computed by Claude)
  -> pathway_score: 0.72              -> CD8_T_cells: 0.12
                                      -> TAMs_M2: 0.35
mcp-multiomics                       -> Tregs: 0.05
  predict_upstream_regulators
  -> PD-L1/PD-1 expression evidence

mcp-opentargets
  get_target_drugs("CD274")  # PD-L1
  -> pembrolizumab, nivolumab status
```
This is the ultimate integrative pipeline: neoantigen burden (Server D) + immune infiltrate composition (Server B) + target validation (Server C) + multi-omics pathway analysis (existing server) combine to predict immunotherapy responsiveness. The orchestration happens at the Claude conversation level, not within any single server.

### Shared Infrastructure

All four servers should:
1. Import `retry_with_backoff` from `shared/utils/api_retry.py` for API resilience (Servers A, B, C, D all make external API calls)
2. Import `CircuitBreaker` from `api_retry.py` for servers with authenticated APIs (Servers A, B)
3. Follow the Dockerfile pattern from `servers/mcp-genomic-results/Dockerfile` (copy `_shared_temp/utils/` into `/app/shared/utils/`, set `PYTHONPATH`)
4. Use the same MCP port allocation scheme (existing servers use ports 3001-3012; allocate 3013-3016 for the four new servers)
5. Update `docs/reference/shared/server-registry.md` to add the four new servers with tool counts (6+5+6+6 = 23 new tools, bringing platform total from 74 to 97)

### Port Allocation

| Server | Port |
|--------|------|
| mcp-geodownload | 3013 |
| mcp-cibersortx | 3014 |
| mcp-opentargets | 3015 |
| mcp-neoantigen | 3016 |

### Critical Files for Implementation

- `servers/mcp-server-boilerplate/` — Template directory to copy for each new server
- `servers/mcp-genomic-results/src/mcp_genomic_results/server.py` — Best pattern reference for API-wrapping servers (simple config, `_impl` functions, `add_dry_run_warning`)
- `servers/mcp-multiomics/src/mcp_multiomics/config.py` — Pattern for Pydantic BaseSettings config (used by Servers B and D)
- `shared/utils/api_retry.py` — Must be imported by all four servers for `retry_with_backoff` and `CircuitBreaker`
- `data/patient-data/PAT001-OVC-2025/genomics/somatic_variants.vcf` — Reference patient VCF that Server D's `peptide_generator` must parse
