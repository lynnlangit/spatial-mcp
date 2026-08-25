# mcp-mockepic

Synthetic EHR records for demos, teaching and CI. Stands in for
[`mcp-epic`](../mcp-epic/README.md) wherever real Epic credentials are unavailable.

> **Mock by design — not for research.** Every record this server returns is
> fabricated. It is not a DRY_RUN fallback that becomes real when configured
> correctly; there is no real mode. Results must never be used for clinical or
> research decisions.
>
> Automatically excluded from `DEPLOYMENT_MODE=production` deploys, where
> `mcp-epic` takes its place.

## Tools

| Tool | Purpose |
|---|---|
| `query_patient_records` | Synthetic demographics and clinical data; `include_labs` / `include_meds` toggle the sections returned |
| `link_spatial_to_clinical` | Associates a spatial sample id with a patient and tissue site, so a spatial workflow has clinical context to join against |
| `search_diagnoses` | Look up ICD-10 diagnosis codes by `icd10_code` or free-text `keyword` |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MOCKEPIC_DRY_RUN` | `true` | Retained for interface parity with the other servers. Output is synthetic either way. |

## Usage

```bash
cd servers/mcp-mockepic
uv run python -m mcp_mockepic
```

## Related

- **Real EHR integration:** [`mcp-epic`](../mcp-epic/README.md) (local deployment only)
- **Tool counts and status:** [Server Registry](../../docs/reference/shared/server-registry.md)
- **DRY_RUN conventions:** [DRY_RUN Mode](../../docs/reference/shared/dry-run-mode.md)
