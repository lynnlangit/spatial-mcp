# Bias Audit Environment Setup

Automated bias auditing for the Precision Medicine MCP platform, supporting FDA, AMA, and NIH ethical AI standards.

**What it provides:**
- Automated bias detection for AI/ML workflows
- Data representation analysis across diverse ancestries
- Fairness metrics calculation (demographic parity, equalized odds, calibration)
- Proxy feature detection
- Ancestry-aware confidence scoring
- HTML/JSON audit report generation

**Related Documentation:**
- [Ethics & Bias Framework](../../docs/for-hospitals/ethics/ETHICS_AND_BIAS.md) - Comprehensive methodology and audit guide

## Prerequisites

- GCP project and VPC set up (via `setup-project.sh` and `setup-vpc.sh`)
- Cloud Storage bucket for audit reports
- Python 3.11+ environment
- Service account with Storage permissions

## Step 1: Create Audit Workstation

**Option A: Cloud Compute Instance (Recommended)**

```bash
# Create dedicated audit workstation
gcloud compute instances create mcp-audit-workstation \
  --project=$PROJECT_ID \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --subnet=mcp-subnet \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --service-account=mcp-audit-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --scopes=cloud-platform \
  --tags=mcp-audit,internal-only

# Allow SSH access (from hospital VPN only)
gcloud compute firewall-rules create allow-ssh-audit \
  --project=$PROJECT_ID \
  --network=hospital-vpc \
  --allow=tcp:22 \
  --source-ranges=10.0.0.0/8 \
  --target-tags=mcp-audit

# SSH to workstation
gcloud compute ssh mcp-audit-workstation --zone=us-central1-a
```

**Option B: Local Workstation**

```bash
# For testing/development, you can run audits locally
# Just ensure you have gcloud SDK configured
gcloud auth application-default login
```

## Step 2: Install Python Environment

```bash
# SSH to audit workstation
gcloud compute ssh mcp-audit-workstation --zone=us-central1-a

# Install Python 3.11
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip git

# Create dedicated audit directory
sudo mkdir -p /opt/bias-audits
sudo chown $USER:$USER /opt/bias-audits
cd /opt/bias-audits

# Clone repository (or copy relevant files)
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp

# Create Python virtual environment
python3.11 -m venv /opt/bias-audits/venv
source /opt/bias-audits/venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install numpy pandas pytest

# Test bias detection module
python3 -c "from shared.utils.bias_detection import check_data_representation; print('Bias detection module loaded successfully')"

# Test audit script
python3 infrastructure/audit/audit_bias.py --help
```

## Step 3: Create Cloud Storage Bucket for Reports

```bash
# Create bucket for audit reports (10-year retention)
gsutil mb -p $PROJECT_ID -l us-central1 gs://$PROJECT_ID-audit-reports

# Create subdirectory structure
gsutil -m cp /dev/null gs://$PROJECT_ID-audit-reports/bias/.keep

# Set lifecycle policy for 10-year retention
cat > retention-10years.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 3650}
      }
    ]
  }
}
EOF

gsutil lifecycle set retention-10years.json gs://$PROJECT_ID-audit-reports

# Grant service account access
gsutil iam ch serviceAccount:mcp-audit-sa@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectAdmin \
  gs://$PROJECT_ID-audit-reports

# Verify permissions
gsutil ls -lh gs://$PROJECT_ID-audit-reports/bias/
```

## Step 4: Set Up Service Account

```bash
# Create service account for bias audits
gcloud iam service-accounts create mcp-audit-sa \
  --project=$PROJECT_ID \
  --display-name="Bias Audit Service Account" \
  --description="Service account for running quarterly bias audits"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:mcp-audit-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"  # For audit reports

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:mcp-audit-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.viewer"  # For viewing logs

# Grant access to analysis data buckets
gsutil iam ch serviceAccount:mcp-audit-sa@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectViewer \
  gs://$PROJECT_ID-analysis-results

gsutil iam ch serviceAccount:mcp-audit-sa@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectViewer \
  gs://$PROJECT_ID-fhir-exports
```

## Step 5: Test Audit Workflow

```bash
# Create sample test data
mkdir -p /opt/bias-audits/test-data

# Create sample genomics data (CSV)
cat > /opt/bias-audits/test-data/sample_genomics.csv <<EOF
patient_id,variant_id,gene,ancestry,pathogenicity,confidence
patient_001,BRCA1:c.5266dupC,BRCA1,european,1,0.95
patient_002,BRCA2:c.123A>G,BRCA2,african,0,0.85
patient_003,TP53:c.456G>T,TP53,asian,1,0.90
patient_004,BRCA1:c.789C>A,BRCA1,latino,0,0.75
EOF

# Create sample clinical data (JSON)
cat > /opt/bias-audits/test-data/sample_clinical.json <<EOF
{
  "resourceType": "Bundle",
  "entry": [
    {"resource": {"resourceType": "Patient", "id": "patient_001", "gender": "female", "birthDate": "1963-01-01"}},
    {"resource": {"resourceType": "Patient", "id": "patient_002", "gender": "female", "birthDate": "1970-05-15"}},
    {"resource": {"resourceType": "Patient", "id": "patient_003", "gender": "male", "birthDate": "1955-12-20"}},
    {"resource": {"resourceType": "Patient", "id": "patient_004", "gender": "female", "birthDate": "1968-08-10"}}
  ]
}
EOF

# Run test audit
cd /opt/bias-audits/precision-medicine-mcp
source /opt/bias-audits/venv/bin/activate

python3 infrastructure/audit/audit_bias.py \
  --workflow patientone \
  --genomics-data /opt/bias-audits/test-data/sample_genomics.csv \
  --clinical-data /opt/bias-audits/test-data/sample_clinical.json \
  --output /opt/bias-audits/test-audit-report.html \
  --min-representation 0.10 \
  --max-disparity 0.10 \
  --reference-dataset gnomad

# Verify report generated
ls -lh /opt/bias-audits/test-audit-report.html

# Upload test report to Cloud Storage
gsutil cp /opt/bias-audits/test-audit-report.html \
  gs://$PROJECT_ID-audit-reports/bias/test/
```

## Step 6: Schedule Quarterly Audits

**Create cron job for quarterly reminders:**

```bash
# SSH to audit workstation
gcloud compute ssh mcp-audit-workstation --zone=us-central1-a

# Create cron job for audit reminders
crontab -e

# Add quarterly reminders (15th of Jan, Apr, Jul, Oct at 9 AM)
0 9 15 1,4,7,10 * echo "Quarterly bias audit due today!" | mail -s "Bias Audit Reminder" admin@hospital.org
```

**Or use Cloud Scheduler for automated reminders:**

```bash
# Create Cloud Scheduler job
gcloud scheduler jobs create pubsub quarterly-bias-audit-reminder \
  --project=$PROJECT_ID \
  --location=us-central1 \
  --schedule="0 9 15 1,4,7,10 *" \
  --topic=bias-audit-reminders \
  --message-body="Quarterly bias audit due today. See Admin Guide for procedure."

# Subscribe to topic for email notifications
gcloud pubsub topics create bias-audit-reminders --project=$PROJECT_ID
gcloud pubsub subscriptions create bias-audit-email \
  --topic=bias-audit-reminders \
  --project=$PROJECT_ID
```

## Verification Checklist

- [ ] Audit workstation created and accessible via SSH
- [ ] Python 3.11+ environment installed with required dependencies
- [ ] Bias detection module and audit script working
- [ ] Cloud Storage bucket created with 10-year retention policy
- [ ] Service account created with appropriate permissions
- [ ] Test audit completed successfully
- [ ] Test report uploaded to Cloud Storage
- [ ] Quarterly audit reminders configured
- [ ] Designated Bias Audit Lead has workstation access
- [ ] Documentation reviewed by admin team

## Troubleshooting

**Problem: Cannot SSH to audit workstation**
```bash
# Check firewall rules
gcloud compute firewall-rules list --filter="name:allow-ssh-audit"

# Verify workstation is running
gcloud compute instances describe mcp-audit-workstation --zone=us-central1-a

# Check IAM permissions for SSH
gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" \
  --format='table(bindings.role)' --filter="bindings.members:user@hospital.org"
```

**Problem: Bias detection module import fails**
```bash
# Verify Python version
python3 --version  # Should be 3.11+

# Check PYTHONPATH
echo $PYTHONPATH

# Reinstall dependencies
pip install --upgrade numpy pandas pytest

# Verify installation
python3 -c "import numpy, pandas; print('Dependencies OK')"
```

**Problem: Cannot access Cloud Storage bucket**
```bash
# Check bucket exists
gsutil ls gs://$PROJECT_ID-audit-reports/

# Verify service account permissions
gsutil iam get gs://$PROJECT_ID-audit-reports/

# Grant access if needed
gsutil iam ch serviceAccount:mcp-audit-sa@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectAdmin \
  gs://$PROJECT_ID-audit-reports/
```
