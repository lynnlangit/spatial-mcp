# Prompt Library

Reusable prompts for precision medicine analyses. Copy, paste, and customize for your use case.

---

## Browse by Audience

| Audience | File | Prompts | Time Range |
|----------|------|---------|------------|
| **Funders & Decision-Makers** | [funder-demo.md](funder-demo.md) | 7 prompts | 5-10 min each |
| **Clinicians & Researchers** | [clinical-workflow.md](clinical-workflow.md) | 15 prompts | 5-45 min each |
| **Developers & QA** | [developer-testing.md](developer-testing.md) | 11 prompts | 1-15 min each |
| **Students & Educators** | [educational.md](educational.md) | 10 prompts | 5-20 min each |

## Browse by Modality

| Modality | File | Prompts | Servers |
|----------|------|---------|---------|
| Clinical & Genomic | [clinical-genomic.md](clinical-genomic.md) | 17 | mcp-mockepic, mcp-fgbio, mcp-genomic-results |
| Multi-Omics | [multiomics.md](multiomics.md) | 17 | mcp-multiomics |
| Spatial Transcriptomics | [spatial.md](spatial.md) | 18 | mcp-spatialtools |
| Imaging | [imaging.md](imaging.md) | 8 | mcp-deepcell, mcp-cell-classify, mcp-openimagedata |
| External Data & Drug Targets | — | — | mcp-geodownload, mcp-opentargets |
| Immunology & Neoantigen | — | — | mcp-cibersortx, mcp-neoantigen |
| End-to-End Workflows | [workflows.md](workflows.md) | 10 | All servers (see [Registry](../shared/server-registry.md)) |

---

## PatientOne Quick Reference

> **Full profile:** [PatientOne Profile](../shared/patientone-profile.md) | **Cost details:** [Cost Analysis](../shared/cost-analysis.md)

- **Patient ID:** `PAT001-OVC-2025`
- **Diagnosis:** Stage IV HGSOC, platinum-resistant, BRCA1 germline mutation
- **Key mutations:** TP53 R175H (73% VAF), PIK3CA E545K (42%), PTEN LOH (85%)
- **GCS data:** `gs://sample-inputs-patientone/patient-data/PAT001-OVC-2025/`
- **Local data:** `data/patient-data/PAT001-OVC-2025/`

---

## Prompt Tips

Write prompts that are **specific**, include **parameters**, and specify **expected output**:

```
# Too vague
Analyze PatientOne data

# Better — specific, parameterized, output-directed
Perform spatial pathway enrichment on PatientOne (PAT001-OVC-2025) tumor regions.
Spatial data is in GCS at gs://sample-inputs-patientone/patient-data/PAT001-OVC-2025/spatial/.
Focus on cancer-related KEGG pathways with FDR < 0.05.
Return top 10 enriched pathways with p-values and gene counts.
```

For multi-step analyses, number each step and name the MCP server to use.

---

## Related Resources

- **[PatientOne Guide](../testing/patient-one/README.md)** - Complete walkthrough
- **[Test Prompts](../testing/patient-one/test-prompts/)** - 10 DRY_RUN + 4 SYNTHETIC_DATA test scenarios (canonical source for PatientOne Prompts 1-6)
- **[Immunotherapy Reference](../testing/patient-one/immunotherapy-reference.md)** - Cold tumor candidates
- **[Server Documentation](../../../servers/README.md)** - Tool reference
- **[Connect External MCP Servers](../../for-researchers/CONNECT_EXTERNAL_MCP.md)** - ClinicalTrials.gov, PubMed, bioRxiv, Hugging Face, cBioPortal, Seqera

---

**Last Updated:** 2026-03-09
