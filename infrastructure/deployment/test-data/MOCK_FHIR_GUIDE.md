# Mock FHIR Store Usage Guide

## Overview

Your GCP Healthcare API FHIR store is now populated with synthetic test data for a Stage IV ovarian cancer patient. This allows you to develop and test the mcp-epic server without waiting for Epic sandbox approval.

---

## FHIR Store Details

**Project:** `precision-medicine-poc`
**Location:** `us-central1`
**Dataset:** `precision-medicine-dataset`
**FHIR Store:** `identified-fhir-store`
**FHIR Version:** R4

**Base URL:**
```
https://healthcare.googleapis.com/v1/projects/precision-medicine-poc/locations/us-central1/datasets/precision-medicine-dataset/fhirStores/identified-fhir-store/fhir
```

---

## Test Patient Data

### Patient Demographics
- **ID:** `patient-001`
- **Name:** Jane Marie TestPatient
- **Gender:** Female
- **Birth Date:** 1968-03-15 (Age: 56)
- **Identifier:** P001

### Clinical Diagnosis
- **Condition:** Stage IV High-Grade Serous Ovarian Carcinoma (HGSOC)
- **Status:** Platinum-resistant
- **FIGO Stage:** IV
- **Onset:** June 2022

### Laboratory Results
1. **CA-125:** 487 U/mL (Critical high, normal: 0-35)
   - Trending upward from 312 U/mL (Sept 2024)
2. **BRCA1/2:** Negative (no pathogenic variants)
   - Somatic TP53 mutation detected: c.524G>A (p.Arg175His)

### Medications
1. **Carboplatin** (Completed)
   - First-line treatment
   - AUC 5 IV every 21 days
   - 6 cycles (Aug-Nov 2022)

2. **Paclitaxel** (Completed)
   - First-line treatment (with Carboplatin)
   - 175 mg/m² IV every 21 days
   - 6 cycles (Aug-Nov 2022)

3. **Bevacizumab** (Active)
   - Second-line treatment for platinum-resistant disease
   - 15 mg/kg IV every 21 days
   - Started March 2023, ongoing

---

## Querying the FHIR Store

### Using curl (REST API)

**Get Patient:**
```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://healthcare.googleapis.com/v1/projects/precision-medicine-poc/locations/us-central1/datasets/precision-medicine-dataset/fhirStores/identified-fhir-store/fhir/Patient/patient-001"
```

**Search Conditions:**
```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://healthcare.googleapis.com/v1/projects/precision-medicine-poc/locations/us-central1/datasets/precision-medicine-dataset/fhirStores/identified-fhir-store/fhir/Condition?patient=patient-001"
```

**Search Observations:**
```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://healthcare.googleapis.com/v1/projects/precision-medicine-poc/locations/us-central1/datasets/precision-medicine-dataset/fhirStores/identified-fhir-store/fhir/Observation?patient=patient-001"
```

**Search Medications:**
```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://healthcare.googleapis.com/v1/projects/precision-medicine-poc/locations/us-central1/datasets/precision-medicine-dataset/fhirStores/identified-fhir-store/fhir/MedicationStatement?patient=patient-001"
```

### Using Python (Google Cloud Healthcare API)

```python
from google.cloud import healthcare_v1
from google.oauth2 import service_account

# Setup
PROJECT_ID = "precision-medicine-poc"
LOCATION = "us-central1"
DATASET_ID = "precision-medicine-dataset"
FHIR_STORE_ID = "identified-fhir-store"

credentials = service_account.Credentials.from_service_account_file(
    os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "path/to/your-service-account-key.json")
)

client = healthcare_v1.FhirStoresServiceClient(credentials=credentials)

# Get patient
fhir_store_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/datasets/{DATASET_ID}/fhirStores/{FHIR_STORE_ID}"
resource_path = f"{fhir_store_name}/fhir/Patient/patient-001"

response = client.execute_fhir_bundle(
    parent=fhir_store_name,
    body={
        "resourceType": "Bundle",
        "type": "batch",
        "entry": [{
            "request": {
                "method": "GET",
                "url": "Patient/patient-001"
            }
        }]
    }
)

print(response)
```

---

## Using with mcp-epic Development

When developing the mcp-epic server, you can now:

1. **Test FHIR client implementation** - Query real FHIR R4 resources
2. **Test de-identification** - Apply HIPAA Safe Harbor to these resources
3. **Test tool responses** - Verify output format and content
4. **Develop without Epic sandbox** - No need to wait for Epic approval

### Example mcp-epic Tool Test

```python
# In your mcp-epic server development
async def get_patient_demographics(patient_id: str = "patient-001"):
    """Test with mock FHIR store"""
    # This will work with your GCP FHIR store
    response = await fhir_client.get(f"Patient/{patient_id}")
    deidentified = deidentify_patient_data(response)
    return deidentified
```

---

## Adding More Test Data

To add additional test patients or resources:

1. **Create JSON file** in `data/patient-data/PAT001-OVC-2025/clinical/fhir_raw/`
2. **Follow FHIR R4 format** (examples provided)
3. **Upload using:**
   ```bash
   curl -X PUT \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/fhir+json" \
     -d @your-resource.json \
     "https://healthcare.googleapis.com/v1/projects/precision-medicine-poc/locations/us-central1/datasets/precision-medicine-dataset/fhirStores/identified-fhir-store/fhir/ResourceType/resource-id"
   ```

---

## Security Notes

- This is the **identified** FHIR store containing PII (for testing)
- Use the **deidentified** FHIR store for de-identified data
- Never commit real patient data to this repository
- Service account key is in `.gitignore`

---

## Costs

FHIR store usage is minimal for testing:
- Storage: ~$0.10/GB/month (you have <1MB)
- Operations: $0.01 per 1000 operations
- **Estimated cost:** <$1/month for testing

---

## Next Steps

1. **Develop mcp-epic server** using this mock FHIR store
2. **Test de-identification** with these resources
3. **Validate HIPAA compliance** of de-identified output
4. **Once working:** Switch to Epic sandbox for real integration

---

## Resources

- [FHIR R4 Specification](https://www.hl7.org/fhir/R4/)
- [GCP Healthcare API Docs](https://cloud.google.com/healthcare-api/docs)
- [HIPAA Safe Harbor Method](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)
