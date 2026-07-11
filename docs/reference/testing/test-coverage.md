# 🧪 Test Coverage - Precision Medicine MCP Servers

**Automated tests** covering tools across all MCP servers.

---

## 📊 Quick Stats

| Metric | Value | Status |
|--------|-------|--------|
| **Overall Coverage** | 56.9% | ⬆️ +27.5 points from baseline |
| **Automated Tests** | 167+ | ✅ All servers tested |
| **Production Ready** | See [Server Registry](../shared/server-registry.md) | Most servers production-ready |
| **GCP Deployed** | See [Server Registry](../shared/server-registry.md) | All validated on Cloud Run (mcp-epic local only) |

---

## 📋 Coverage by Server

📋 **[See Server Status →](../../../servers/README.md#-server-status)** - Complete server status and implementation details

| Server | Coverage | Tests | Status |
|--------|----------|-------|--------|
| 🧬 **mcp-fgbio** | 77% | 29 | ✅ Complete |
| 🔬 **mcp-multiomics** | 68% | 91 | ✅ Complete |
| 🖼️ **mcp-deepcell** | 62% | 9 | ✅ Smoke |
| 🏥 **mcp-epic** | 58% | 12 | ✅ Complete |
| 🖼️ **mcp-openimagedata** | 55% | 30 | ✅ Full |
| 🧪 **mcp-mocktcga** | 35% | 5 | ✅ Smoke |
| 📍 **mcp-spatialtools** | 23% | 5 | ✅ Smoke |
| 🔬 **mcp-cell-classify** | — | — | ✅ Smoke |
| 🧬 **mcp-genomic-results** | — | 20 | ✅ Smoke |

For production readiness status, see [Server Registry](../shared/server-registry.md).

**Note:** Low test coverage ≠ low production readiness. mcp-spatialtools has 23% coverage but is 95% production-ready with real implementations.

---

## 📂 Test Organization

```
/tests/
├── unit/                  # Unit tests for all servers (pytest)
│   ├── mcp-fgbio/        # 29 tests (77% coverage)
│   ├── mcp-multiomics/   # 91 tests (68% coverage) ⭐ Most comprehensive
│   ├── mcp-spatialtools/ # 5 tests (production-ready)
│   └── mcp-epic/         # 12 tests (real Epic FHIR)
├── integration/          # GCP deployment validation
├── manual_testing/       # End-to-end test suites
│   ├── PatientOne-OvarianCancer/  # Full workflow (TESTS 1-5)
│   └── Solution-Testing/          # Server verification
└── verification/         # Server utilities
```

---

## 🚀 Running Tests

### Run All Tests for a Server

**Production servers:**
```bash
# From repository root
MULTIOMICS_DRY_RUN="true" servers/mcp-multiomics/venv/bin/python -m pytest tests/unit/mcp-multiomics/ -v
FGBIO_DRY_RUN="true" servers/mcp-fgbio/venv/bin/python -m pytest tests/unit/mcp-fgbio/ -v
SPATIAL_DRY_RUN="true" servers/mcp-spatialtools/venv/bin/python -m pytest tests/unit/mcp-spatialtools/ -v
DEEPCELL_DRY_RUN="true" servers/mcp-deepcell/venv/bin/python -m pytest tests/unit/mcp-deepcell/ -v
```

**Mocked servers:**
```bash
MOCKTCGA_DRY_RUN="true" servers/mcp-mocktcga/venv/bin/python -m pytest tests/unit/mcp-mocktcga/ -v
```

### With Coverage Report

```bash
MULTIOMICS_DRY_RUN="true" servers/mcp-multiomics/venv/bin/python -m pytest tests/unit/mcp-multiomics/ \
  --cov=servers/mcp-multiomics/src/mcp_multiomics --cov-report=term-missing -v
```

### Run Specific Test

```bash
# Specific file
MULTIOMICS_DRY_RUN="true" servers/mcp-multiomics/venv/bin/python -m pytest tests/unit/mcp-multiomics/test_preprocessing.py -v

# Specific test function
MULTIOMICS_DRY_RUN="true" servers/mcp-multiomics/venv/bin/python -m pytest \
  tests/unit/mcp-multiomics/test_preprocessing.py::TestValidateWithRealData::test_validate_with_real_rna_data -v
```

---

## 🧩 Test Types

### ✅ Smoke Tests (All Servers)
- Module imports and DRY_RUN configuration
- Tool registration and server initialization
- Location: `/tests/unit/mcp-{server}/test_server.py`

### 🔬 Functional Tests (Production Servers)
- Real data processing and statistical calculations
- Batch correction, normalization, edge cases
- Best example: `mcp-multiomics` - 91 tests with 580KB+ fixture data
- Location: `/tests/unit/mcp-{server}/` (e.g., `test_preprocessing.py`, `test_integration.py`)

### 🔗 Integration Tests
- Multi-server workflows (PatientOne)
- GCP Cloud Run deployment validation
- SSE transport and Claude API integration
- Location: `/tests/integration/`

---

## ☁️ GCP Cloud Run Testing

**Validation:** ✅ All servers passing functional tests via Claude API

```bash
cd tests/integration
python test_all_gcp_servers.py
```

**Coverage:**
- SSE transport validation
- Tool discovery via MCP protocol
- Response time < 5 seconds (excluding cold starts)

---

## 🏥 PatientOne Test Suite

**Location:** `/docs/reference/testing/patient-one/`

Complete end-to-end precision medicine workflow for Stage IV ovarian cancer:

- 🧬 **TEST_1** - Clinical data (Epic FHIR)
- 🔬 **TEST_2** - Multi-omics resistance (RNA/Protein/Phospho)
- 📍 **TEST_3** - Spatial transcriptomics (900 spots × 31 genes)
- 🖼️ **TEST_4** - Histology & imaging (H&E, MxIF)
- 🎯 **TEST_5** - Integration & treatment recommendations

**Modes:**
- **DRY_RUN** (default): Synthetic data demo (~$0.32, 25-35 min)
- **Real Data**: Your own patient data ([Configuration Guide](patient-one/data-modes-guide.md))

📖 **[PatientOne Quick Start →](patient-one/README.md)**

---

## 📚 Development Guidelines

### Adding Tests

**For new servers (smoke tests):**
1. Create `/tests/unit/mcp-{server}/test_server.py`
2. Test imports, configuration, tool registration
3. Target: 35-60% coverage with 5-12 tests

**For production servers (functional tests):**
1. Create fixtures in `/tests/unit/mcp-{server}/fixtures/` with realistic data
2. Test with `DRY_RUN=False` using monkeypatch
3. Validate actual calculations and outputs
4. Target: 70%+ coverage on critical modules

### Best Practices

**✅ DO:**
- Use pytest fixtures for test data
- Test both DRY_RUN modes (True/False)
- Validate actual outputs (files, calculations)
- Use descriptive test names

**❌ DON'T:**
- Call FastMCP-decorated functions directly (use `.fn` attribute to access the underlying async function)
- Skip assertions on key results
- Hard-code file paths (use fixtures, tmp_path)
- Ignore test failures

---

## 🎯 Next Steps to 60% Coverage

1. **mcp-spatialtools:** Add functional tests for spatial algorithms (+5.4 point impact)
2. **mcp-mocktcga:** Add TCGA API integration tests (+1.6 point impact)

**Estimated effort:** ~20-25 functional tests across 2 servers

---

## 🔗 Resources

- 📖 [pytest Documentation](https://docs.pytest.org/)
- 📊 [pytest-cov Plugin](https://pytest-cov.readthedocs.io/)
- 🔌 [MCP Protocol](https://modelcontextprotocol.io/)
- ✅ [Server Implementation Status](../shared/server-registry.md)

---

**Status:** 200+ tests | All servers deployed ✅
