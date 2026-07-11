# Test Documentation

This directory contains all documentation related to testing the Precision Medicine MCP system.

**📍 Note:** Test **code** (`.py` files, test fixtures, scripts) remains in `/tests`. This directory contains test **documentation** only.

## Contents

### [Test Coverage](./test-coverage.md)
Overview of test coverage, test structure, and testing guidelines for the project.

### [GCP Integration Testing](./gcp-integration.md)
Testing deployed servers via Claude API.

### Manual Testing
- [Quick Test Prompts](./quick-test-prompts.md) - 14 copy-paste prompts for Claude Desktop
- [Claude Desktop Setup](./claude-desktop-setup.md) - File access configuration

### [PatientOne Scenario](./patient-one/)
Complete testing scenario using synthetic ovarian cancer patient data.

- [Overview](./patient-one/README.md) - PatientOne testing scenario (architecture, test descriptions, troubleshooting)
- [CITL Quick Test](./patient-one/citl-quick-test.md) - Clinician-in-the-Loop workflow test
- [Data Modes Guide](./patient-one/data-modes-guide.md) - DRY_RUN vs Actual Data configuration
- [Immunotherapy Reference](./patient-one/immunotherapy-reference.md) - Next-gen immunotherapy candidates

#### Test Prompts
Ready-to-use test prompts for the complete PatientOne workflow, organized by data mode:

**[DRY_RUN](./patient-one/test-prompts/DRY_RUN/)** — Hardcoded mock data, zero file I/O, instant responses:
1. [Test 1: Clinical Genomic](./patient-one/test-prompts/DRY_RUN/test-1-clinical-genomic.md)
2. [Test 2: Multiomics Enhanced](./patient-one/test-prompts/DRY_RUN/test-2-multiomics-enhanced.md)
3. [Test 3: Spatial](./patient-one/test-prompts/DRY_RUN/test-3-spatial.md)
4. [Test 4: Imaging](./patient-one/test-prompts/DRY_RUN/test-4-imaging.md)
5. [Test 5: Integration](./patient-one/test-prompts/DRY_RUN/test-5-integration.md)
6. [Test 6: CitL Review](./patient-one/test-prompts/DRY_RUN/test-6-citl-review.md)
7. [Test 7: E2E Claude Desktop](./patient-one/test-prompts/DRY_RUN/test-7-e2e-claude-desktop.md)
8. [Test 8: E2E + Connectors](./patient-one/test-prompts/DRY_RUN/test-8-e2e-claude-desktop-with-connectors.md)
9. [Test 9: E2E Seqera Connector](./patient-one/test-prompts/DRY_RUN/test-9-e2e-seqera-connector.md)
10. [Test 10: E2E Full Platform](./patient-one/test-prompts/DRY_RUN/test-10-e2e-full-platform.md)

**[SYNTHETIC_DATA](./patient-one/test-prompts/SYNTHETIC_DATA/)** — Real file parsing (`*_DRY_RUN=false`):
1. [Test 1: Clinical Genomic](./patient-one/test-prompts/SYNTHETIC_DATA/test-1-clinical-genomic.md)
2. [Test 2: Multiomics Enhanced](./patient-one/test-prompts/SYNTHETIC_DATA/test-2-multiomics-enhanced.md)
3. [Test 3: Spatial](./patient-one/test-prompts/SYNTHETIC_DATA/test-3-spatial.md)
7. [Test 7: E2E Claude Desktop](./patient-one/test-prompts/SYNTHETIC_DATA/test-7-e2e-claude-desktop.md)

See [test-prompts README](./patient-one/test-prompts/README.md) for details on both modes.

### [PatientTwo Scenario](./patient-two/)
Cross-cancer validation using synthetic ER+/HER2- breast cancer patient data. Demonstrates that the same platform handles a completely different cancer type with zero disease-specific code changes.

- [Overview](./patient-two/README.md) - PatientTwo workflow, key results, reference values
- [Test Prompts](./patient-two/test-prompts/README.md) - 10 DRY_RUN + 6 SYNTHETIC_DATA tests

### [PatientThree Scenario](./patient-three/) (PAT003 — Preventive Cardiovascular)
Preventive cardiovascular health workflow for a 67F post-menopausal patient. Validates the cardiometabolic server and surfaces evidence gaps (Lp(a), APOE, CAC score) missed by standard lipid panel.

- [Overview](./patient-three/README.md) - PatientThree workflow, key results, evidence gaps
- [Test 1: CVD Risk Assessment](./patient-three/test-prompts/DRY_RUN/test-1-cvd-risk-assessment.md) - DRY_RUN test prompt
- PAT003 data: `data/patient-data/PAT003-CVD-2026/`

### [Developer Testing Prompts](../prompts/developer-testing.md)
11 prompts for server validation, load testing, HIPAA audit, error handling, and cost monitoring. Complements the patient scenario tests above.

---

## Quick Start

**For automated testing:** See `/tests` directory for pytest unit and integration tests.

**For manual testing:**
1. Start with [Quick Test Prompts](./quick-test-prompts.md) for rapid verification
2. Run [PatientOne scenario](./patient-one/README.md) (HGSOC) or [PatientTwo scenario](./patient-two/README.md) (ER+ breast cancer) for end-to-end testing
3. Follow [CitL Quick Test](./patient-one/citl-quick-test.md) to validate clinical review workflow

---

## Manual Testing Setup

This section covers scripts and documentation for manually testing the Precision Medicine MCP servers.

### Scripts (Executable)

Located in `tests/manual_testing/Solution-Testing/`:

| File | Purpose | Usage |
|------|---------|-------|
| `install_dependencies.sh` | Install all dependencies for all MCP servers | `./install_dependencies.sh` |
| `verify_servers.sh` | Verify all servers can be imported | `./verify_servers.sh` |
| `setup_and_test_servers.sh` | Combined setup and verification | `./setup_and_test_servers.sh --install` |
| `test_all_servers.py` | Python-based server verification | `python3 test_all_servers.py` |

### Install All Server Dependencies

```bash
cd tests/manual_testing/Solution-Testing
./install_dependencies.sh
```

This will:
- Create Python 3.11 virtual environments for each server
- Install FastMCP and all dependencies
- Set up all servers in development mode

**Time:** ~5-10 minutes

### Verify All Servers

```bash
cd tests/manual_testing/Solution-Testing
./verify_servers.sh
```

Expected output:
```
All MCP servers are operational!
```

**Time:** ~10-30 seconds

### Claude Code vs Claude Desktop

**Scripts run in Claude Code** (VSCode extension):
- ✅ Can install dependencies
- ✅ Can verify server code
- ❌ Cannot orchestrate MCP protocol

**To test MCP workflows:**
- ✅ Use Claude Desktop (standalone app)
- ✅ Configure with [`docs/getting-started/desktop-configs/`](../../getting-started/desktop-configs/)

### Python Version Requirement

All servers require **Python 3.11+**. The install script automatically uses `python3.11`.

### Server Test Status

See [Server Registry](../shared/server-registry.md) for current server names, tool counts, and status.
