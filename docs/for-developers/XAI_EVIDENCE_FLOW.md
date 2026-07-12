# XAI & Evidence Flow

← Back to [Architecture Overview](ARCHITECTURE.md)

---

Every tool returns `xai_metadata` alongside its results, enabling end-to-end evidence traceability from individual tool calls through to the patient report.

```
┌────────────────────────────────────────────────────────────────┐
│  Stage 1: Per-Tool XAI Metadata                                │
│                                                                │
│  mcp-fgbio         mcp-multiomics      mcp-spatialtools       │
│  ┌──────────────┐  ┌──────────────┐    ┌──────────────┐       │
│  │ xai_metadata  │  │ xai_metadata  │    │ xai_metadata  │     │
│  │ confidence: H │  │ confidence: H │    │ confidence: M │     │
│  │ grade: Tier_I │  │ grade: strong │    │ grade: mod.   │     │
│  │ drivers: [..] │  │ drivers: [..] │    │ drivers: [..] │     │
│  └──────┬───────┘  └──────┬───────┘    └──────┬───────┘      │
│         │                 │                    │               │
└─────────┼─────────────────┼────────────────────┼───────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌────────────────────────────────────────────────────────────────┐
│  Stage 2: Claude Cross-Tool Synthesis                          │
│                                                                │
│  • Collects xai_metadata from each tool call                   │
│  • Identifies the weakest evidence link                        │
│  • Counts high / medium / low confidence results               │
│  • Flags disagreements between modalities                      │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│  Stage 3: Report Evidence Summary                              │
│                                                                │
│  evidence_strength_summary:                                    │
│    high_confidence_count: 3                                    │
│    medium_confidence_count: 1                                  │
│    weakest_link: "Spatial enrichment (medium)"                 │
│    overall_assessment: "Strong multi-modal evidence"           │
│                                                                │
│  → Clinician: APPROVE / REVISE / REJECT                        │
└────────────────────────────────────────────────────────────────┘
```

**Three stages explained:**

1. **Per-tool metadata** -- Each MCP server includes `xai_metadata` in every tool response via a standardized `_build_xai_metadata()` helper. This captures confidence level, key drivers, evidence grade, guideline version, and an optional counterfactual.

2. **Cross-tool synthesis** -- Claude aggregates the `xai_metadata` from all tool calls in a workflow. It identifies the weakest evidence link and flags any confidence disagreements between modalities (e.g., genomic evidence is high but spatial evidence is only moderate).

3. **Report aggregation** -- The final patient report includes an `evidence_strength_summary` that gives clinicians a single view of evidence quality, supporting the APPROVE / REVISE / REJECT decision in the clinician-in-the-loop workflow.

**Schema reference:** [XAI Metadata Schema](../reference/shared/xai-metadata-schema.md)
