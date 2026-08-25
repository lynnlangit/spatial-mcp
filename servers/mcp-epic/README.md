# mcp-epic

Epic FHIR R4 integration for real EHR data, with HIPAA Safe Harbor de-identification
applied to everything it returns.

> **Local deployment only.** This server talks to a hospital's Epic FHIR endpoint and
> needs credentials that exist only in the hospital's environment. It is excluded from
> `DEPLOYMENT_MODE=development` deploys; `mcp-mockepic` stands in for it there. See the
> profile filter in `infrastructure/deployment/deploy_to_gcp.sh`.

## Tools

| Tool | Purpose |
|---|---|
| `get_patient_demographics` | Patient demographics for one FHIR patient id |
| `get_patient_conditions` | Conditions / diagnoses, optionally filtered by `category` |
| `get_patient_observations` | Labs, vitals and other observations, filtered by `category` or LOINC `code` |
| `get_patient_medications` | Medication orders, optionally filtered by `status` |

Every response passes through HIPAA Safe Harbor de-identification before it is
returned. Nothing carries a direct identifier out of this server.

## Environment Variables

| Variable | Description |
|---|---|
| `EPIC_FHIR_ENDPOINT` | Epic FHIR R4 base URL, e.g. `https://hospital.epic.com/api/FHIR/R4/` |
| `EPIC_CLIENT_ID` | OAuth client id issued by the hospital's Epic administrator |
| `EPIC_CLIENT_SECRET` | OAuth client secret |
| `EPIC_DRY_RUN` | When `true`, returns synthetic responses without contacting Epic |

## Usage

```bash
cd servers/mcp-epic
uv run python -m mcp_epic
```

For demos, education and CI, use [`mcp-mockepic`](../mcp-mockepic/README.md) instead —
it exposes a comparable surface backed by synthetic records and needs no credentials.

## Related

- **Stage 0 de-identification:** [`mcp-deidentify`](../mcp-deidentify/README.md)
- **Tool counts and status:** [Server Registry](../../docs/reference/shared/server-registry.md)
- **Hospital deployment:** [Hospital Guide](../../docs/for-hospitals/README.md)
