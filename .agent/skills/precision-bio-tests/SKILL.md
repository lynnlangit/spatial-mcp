---
name: precision-bio-tests
description: >
  Expert guide for testing bioinformatics MCP servers.
  Covers pytest, DRY_RUN modes, and PatientOne simulation scenarios.
---

# Precision Bio-Testing

This skill provides guidelines for validating the complex biological and clinical logic in this repository.

## 🧪 Automated Testing Strategy

### 1. Unit Testing (`pytest`)
- Located in `/tests/unit/mcp-[server]/`.
- **FastMCP Pattern**: Never call decorated functions directly. Always use the `.fn` attribute (e.g., `server.perturbation_predict.fn`).
- **DRY_RUN Mode**: Always test both `DRY_RUN=True` (synthetic) and `DRY_RUN=False` (real logic/monkeypatched).

### 2. Bioinformatics Fixtures
- Small biological datasets should live in `/tests/unit/mcp-[server]/fixtures/`.
- Large datasets should be mocked or referenced from `data/patient-data/`.

## 🏥 The PatientOne Scenario

The gold standard for integration testing is the **PatientOne** workflow (`/docs/reference/testing/patient-one/`).
- **Phase 1**: Clinical (Epic).
- **Phase 2**: Multi-omics.
- **Phase 3**: Spatial.
- **Phase 4**: Imaging.
- **Phase 5**: Final integrated recommendation.

Use the `CITL Quick Test` script to verify changes across the entire platform.

## 📝 Manual Testing (Prompts)

For browser-based or chat-based testing:
- Use the templates in `docs/reference/testing/quick-test-prompts.md`.
- Always verify the "Clinical Interpretation" matches the expected biological signal (e.g., GZMB/IFNG upregulation in immunotherapy).

## ✅ Testing Checklist
- [ ] Tool discovery via MCP protocol works.
- [ ] SSE transport validation complete.
- [ ] Memory usage remains within 4Gi during heavy bioinformatics processing.
- [ ] Error messages are informative for clinicians, not just developers.

---

**Use this skill when:**
- Adding new tools to an MCP server.
- Running regression tests on patient data pipelines.
- Validating a new server's "production-ready" status.
