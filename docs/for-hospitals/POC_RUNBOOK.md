# 90-Day Proof of Concept Runbook

## Days 1-30: Infrastructure Setup

### IT prerequisites checklist
- [ ] Python 3.11+ installed on server
- [ ] uv 0.4+ installed (`pip install uv`)
- [ ] Network ports open: 443 (TLS), 8000-8018 (MCP servers)
- [ ] Claude API key procured from console.anthropic.com
- [ ] 16 GB RAM minimum per server node
- [ ] De-identification layer deployed and tested with synthetic data

### Setup steps
1. `git clone https://github.com/lynnlangit/precision-medicine-mcp`
2. `cd precision-medicine-mcp && uv sync`
3. `python -m pytest tests/ -x --tb=short`
4. Verify PAT001 canonical values match the "Validated Results" table in README.md
5. Connect Claude Desktop and confirm all 19 MCP servers appear

### People to identify before Day 10
- 3 oncologist champions willing to review AI-generated hypotheses
- 1 bioinformatician to manage server configuration and data flow
- 1 HIPAA Security Officer contact for gap remediation (see HIPAA_CHECKLIST.md)

## Days 31-60: Pilot with De-identified Retrospective Cases

1. Select 10 retrospective HGSOC cases from the tumor board archive (recommend 2020-2024).
2. De-identify each case using the de-identification layer; assign study IDs.
3. Run each case through the full pipeline: genomic-results -> neoantigen -> spatial-tools -> cell-classify -> patient-report.
4. Conduct blinded review: each oncologist champion receives the AI hypothesis without knowing the actual treatment decision.
5. Record concordance (AI hypothesis aligns with actual treatment) and discordance.
6. Document all discordances in GitHub issues with the `hospital-poc` label.

## Days 61-90: Evaluation and Go/No-Go Decision

### Quantitative metrics

| Metric | Go target | Actual (fill in) |
|--------|-----------|------------------|
| Concordance with oncologist judgment | >= 70% across 10 cases | {{FILL}} |
| Processing time per case | < 5 minutes | {{FILL}} |
| Tool error rate | < 5% | {{FILL}} |
| HIGH-severity HIPAA gaps closed | 100% | {{FILL}} |

### Go criteria (all must be met)
- Concordance >= 70%
- Error rate < 5%
- All HIGH-severity gaps from HIPAA_CHECKLIST.md resolved

### No-go criteria and remediation path
- Concordance < 70%: expand retrospective pilot to 25 cases before re-evaluation
- Error rate > 5%: triage by server; open GitHub issues tagged `hospital-poc`
- HIPAA gaps remain open: do not proceed to any live patient data

### Stakeholder presentation
Prepare using docs/for-hospitals/STAKEHOLDER_ONE_PAGER.md as the base document.
