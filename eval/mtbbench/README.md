# MTBBench Evaluation Harness

Paper-first validation harness for the Precision Medicine MCP Platform, validated
against the MTBBench longitudinal track (MSK-CHORD cohort).

**Paper contribution framing:** "The first open-source, MCP-federated,
governance-first platform independently validated on a public precision-oncology
benchmark, reporting safety and faithfulness metrics no existing system measures."

## What This Produces

| Table | Content | Source |
|-------|---------|--------|
| **A** | Accuracy (treatment match, biomarker F1, guideline citation) | `metrics/accuracy.py` |
| **B** | Governance metrics (tool-grounding, HITL catch rate, de-id integrity) — **the contribution** | `metrics/governance.py` |
| **C** | Ablations (no-HITL, no-XAI, no-de-id, base LLM) | `metrics/ablations.py` |

## MTBBench Longitudinal Track

- **Source:** MSK-CHORD via cBioPortal (Jain et al., NeurIPS 2024)
- **Protocol:** Doctor-agent multi-turn — patient context is revealed incrementally
- **Questions:** Binary (A/B) on recurrence, survival, and progression at specified time horizons
- **Cases:** 40 patients, ~100+ questions total
- **Cancer types:** Pancreatic (10), Lung (9), Colorectal (10), Prostate (2), Breast (1), Other (8)

## Key Design Decisions

1. **No ovarian/HGSOC cases** in MTBBench → paper anchors on pancreatic + colorectal
2. **PAT001 (HGSOC) and PAT002 (breast)** remain as cross-architecture validation,
   not MTBBench-scored
3. **All code runs DRY_RUN by default** — no real bioinformatics compute in CI
4. **No MSK-CHORD patient data committed** — only benchmark Q&A pairs in fixtures

## Running

```bash
# Smoke test (one case, DRY_RUN)
cd /path/to/repo
uv run pytest eval/test_milestone_1.py -v -m integration

# Full longitudinal track (Milestone 2+)
uv run python -m eval.mtbbench.eval_runner --all --dry-run
```

## Citation

```
Jain et al., "MTBBench: A Multimodal Sequential Clinical Decision-Making
Benchmark in Oncology," NeurIPS 2024. github.com/bunnelab/mtbbench
```

## Security Constraints

- DEIDENTIFY_DRY_RUN=true in all harness code paths
- CARDIOMETABOLIC_DRY_RUN respected
- Reports retain DRAFT watermark and NOT FOR CLINICAL USE banner
- No real PII in any file
- PAT003/PAT004 not referenced in harness code
