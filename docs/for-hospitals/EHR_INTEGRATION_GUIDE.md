# EHR Integration Guide

## What the mock EPIC server simulates

The mock server is located at `servers/mcp-mockepic/src/mcp_mockepic/server.py`.

| Tool name | Real EPIC equivalent | What it returns |
|-----------|---------------------|-----------------|
| query_patient_records | FHIR Patient + Condition resources | Patient demographics and diagnosis list |
| search_diagnoses | FHIR Condition search | ICD-10 code lookup |
| link_spatial_to_clinical | Custom join | Links spatial biopsy data to clinical encounter |

## Replacing mock data with real EHR data

1. **Identify your EPIC FHIR R4 endpoint URL** -- typically `https://<hospital>.epic.com/api/FHIR/R4/`
2. **Obtain OAuth2 credentials** -- use SMART on FHIR app registration in your EPIC environment. Required scopes: `patient/Patient.read`, `patient/Condition.read`.
3. **Map EPIC patient fields to mock server schema** -- see mapping table below.
4. **Replace mock tool implementations** -- edit `servers/mcp-mockepic/src/mcp_mockepic/server.py`. Replace synthetic data returns with live FHIR API calls. Keep the same return schema so all downstream servers remain unaffected.
5. **Re-run PAT001 canonical test** -- `python -m pytest tests/ -k "pat001" -x` -- confirm schema compatibility before going live.

## HL7 FHIR resource mapping

| Mock field | FHIR R4 resource | FHIR path |
|------------|------------------|-----------|
| patient_id | Patient | `Patient.id` |
| diagnosis_code | Condition | `Condition.code.coding[0].code` |
| sample_date | Specimen | `Specimen.collection.collectedDateTime` |
| tumor_type | Condition | `Condition.code.text` |

## Known gaps between mock and production

- **Medication history**: not modeled in mock server
- **Radiology reports**: not available via MCP; requires separate DICOM integration
- **Clinical trial enrollment**: not modeled
- **Lab values** (CA-125, etc.): not returned by mock server
- **Prior treatment history**: not modeled
