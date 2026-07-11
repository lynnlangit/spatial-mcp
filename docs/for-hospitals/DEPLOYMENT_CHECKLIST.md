# Hospital Deployment Checklist

Step-by-step checklist for deploying the Precision Medicine MCP Platform at your institution.

---

## Pre-Deployment (4-6 weeks)

### Institutional Approvals
- [ ] **IRB Approval** (if using for research) - 4-8 weeks
- [ ] **IT Security Review** - Security officer sign-off
- [ ] **HIPAA Compliance Review** - Legal/compliance team approval
- [ ] **Budget Approval** - See [Cost Analysis](../reference/shared/cost-analysis.md) for estimated initial and annual costs
- [ ] **Epic Integration Request** - Submit to Epic team (6-8 week lead time)

### Technical Prerequisites
- [ ] **GCP Organization** - Existing HIPAA-compliant GCP setup
- [ ] **Azure AD** - User directory for SSO
- [ ] **Epic FHIR API Access** - R4 API credentials (sandbox + production)
- [ ] **Bioinformatics Infrastructure** - VCF/FASTQ data pipeline
- [ ] **PACS Integration** (optional) - H&E and MxIF image access

---

## Month 1: Infrastructure Setup

### GCP Project Setup
- [ ] Create new GCP project: `precision-medicine-[institution]-prod`
- [ ] Enable required APIs:
  - [ ] Cloud Run API
  - [ ] Cloud Storage API
  - [ ] Healthcare API (FHIR)
  - [ ] Secret Manager API
  - [ ] Cloud Logging API
  - [ ] IAM API
- [ ] Configure billing alerts (80%, 90%, 100% thresholds)
- [ ] Set up budget (see [Cost Analysis](../reference/shared/cost-analysis.md) for estimates)

### Networking
- [ ] Create VPC: `precision-medicine-vpc`
- [ ] Create subnet: `precision-medicine-subnet` (10.0.0.0/24)
- [ ] Configure Cloud NAT for outbound traffic
- [ ] Set up firewall rules (ingress: IAP only, egress: Epic FHIR + external APIs)
- [ ] Test connectivity to Epic FHIR sandbox API

### Storage & Data
- [ ] Create Cloud Storage bucket: `[project]-patient-data` (encrypted)
- [ ] Create Healthcare dataset: `precision-medicine-dataset`
- [ ] Create FHIR store: `identified-fhir-store` (for Epic data)
- [ ] Create FHIR store: `deidentified-fhir-store` (for analysis)
- [ ] Configure backup policy: daily snapshots, 30-day retention

### Authentication
- [ ] Configure Azure AD as OIDC provider in GCP
- [ ] Create IAP OAuth consent screen
- [ ] Configure IAP for Cloud Run services
- [ ] Test SSO login with 2 pilot users

---

## Month 2: Core Servers Deployment

### Deploy mcp-deidentify (Stage 0 — De-identification)
> Deploy this **before all other servers** — Stage 0 preprocessing is required by every downstream pipeline stage.
- [ ] Deploy to Cloud Run: `mcp-deidentify`
- [ ] Configure environment variables: `DEIDENTIFY_DRY_RUN=false`, `DEIDENTIFY_KEY_DIR=/gcs/bucket/keys`, `DEIDENTIFY_OUTPUT_DIR=/gcs/bucket/deidentified`
- [ ] Confirm `ANTHROPIC_API_KEY` available via ambient Cloud Run SA auth
- [ ] Test: "De-identify this synthetic patient JSON record"
- [ ] Verify anonymization key written to `DEIDENTIFY_KEY_DIR`
- [ ] Run `validate_deidentification` on a de-identified record and confirm `passed: true`

### Deploy mcp-fgbio (Reference Genomes)
- [ ] Deploy to Cloud Run: `mcp-fgbio`
- [ ] Configure environment variables: `FGBIO_DRY_RUN=false`
- [ ] Load reference genomes (GRCh38, transcripts)
- [ ] Test: "List available reference genomes"

### Deploy mcp-multiomics (Multi-omics Integration)
- [ ] Deploy to Cloud Run: `mcp-multiomics`
- [ ] Configure environment variables: `MULTIOMICS_DRY_RUN=false`
- [ ] Upload synthetic test data (PatientOne RNA/Protein/Phospho)
- [ ] Test: "Run Stouffer meta-analysis on PatientOne data"

### Deploy mcp-spatialtools (Spatial Transcriptomics)
- [ ] Deploy to Cloud Run: `mcp-spatialtools`
- [ ] Configure environment variables: `SPATIAL_DRY_RUN=false`
- [ ] Upload synthetic Visium data (PatientOne tumor regions)
- [ ] Test: "Perform pathway enrichment on PatientOne spatial data"

### Monitoring & Logging
- [ ] Create Cloud Monitoring dashboard: "MCP Platform Health"
- [ ] Configure uptime checks for all 4 deployed servers
- [ ] Set up log-based metrics: error rate, latency p95
- [ ] Create alert policies: server down, error spike, high cost
- [ ] Test alert routing to on-call email/Slack

---

## Month 3: Epic FHIR Integration

### Epic Sandbox Testing
- [ ] Configure mcp-epic server with sandbox credentials
- [ ] Deploy to Cloud Run: `mcp-epic` (internal only, no public IP)
- [ ] Test FHIR queries:
  - [ ] Patient demographics (de-identified)
  - [ ] Conditions (ICD-10 codes)
  - [ ] Medications (RxNorm codes)
  - [ ] Observations (labs: CA-125, tumor markers)
- [ ] Validate de-identification (Safe Harbor method)
- [ ] Review audit logs for all FHIR API calls

### Epic Production Connection
- [ ] Submit Epic production access request (requires Epic team)
- [ ] Configure read-only FHIR API credentials
- [ ] Test with 5-10 real patients (IRB-approved)
- [ ] Validate data quality and completeness
- [ ] Document any data mapping issues (custom Epic extensions)

---

## Month 4: Full Server Deployment

### Deploy Remaining Servers
- [ ] **mcp-mocktcga** - Mock TCGA cohort data (mocked for now, GDC API later)
- [ ] **mcp-openimagedata** - Imaging data retrieval
- [ ] **mcp-deepcell** - Cell segmentation (mocked, DeepCell API later)
- [ ] **mcp-mockepic** - Synthetic FHIR data for testing

### Integration Testing
- [ ] End-to-end workflow: PatientOne full analysis (25-35 min DRY_RUN)
- [ ] Multi-user test: 5 concurrent analyses
- [ ] Load test: 20 analyses in 1 hour
- [ ] Cost validation: verify per-analysis costs match [Cost Analysis](../reference/shared/cost-analysis.md) targets
- [ ] Error handling: graceful failures, retry logic

---

## Month 5: User Training & Validation

### Training Program
- [ ] **Week 1:** Clinician training (2 hours)
  - [ ] Streamlit UI walkthrough
  - [ ] Basic queries (clinical data, treatment recommendations)
  - [ ] Result interpretation
- [ ] **Week 2:** Bioinformatician training (4 hours)
  - [ ] Advanced queries (multi-omics, spatial analysis)
  - [ ] Data upload and validation
  - [ ] Quality control checks
- [ ] **Week 3:** Admin training (8 hours)
  - [ ] User management
  - [ ] Monitoring and alerting
  - [ ] Backup and recovery
  - [ ] Troubleshooting runbooks

### Pilot Testing (10-20 Patients)
- [ ] Select pilot patients (ovarian cancer, diverse stages)
- [ ] Perform analyses with both traditional and MCP approaches
- [ ] Compare results: accuracy, time, cost
- [ ] Collect user feedback (clinicians, bioinformaticians)
- [ ] Document edge cases and issues

### Security Audit
- [ ] External penetration testing (optional but recommended)
- [ ] HIPAA compliance validation
- [ ] Review audit logs (3 months of data)
- [ ] Verify de-identification (sample 10 random patients)
- [ ] Test incident response procedures

---

## Month 6: Production Launch

### Pre-Launch Checklist
- [ ] All servers deployed and tested
- [ ] Monitoring dashboard complete with alerts
- [ ] User training completed (5 pilot users)
- [ ] Documentation finalized (operations manual, runbooks)
- [ ] Backup and disaster recovery tested
- [ ] Security audit passed
- [ ] Stakeholder sign-off (IT, security, clinical leadership)

### Go-Live
- [ ] Announce production launch to pilot users
- [ ] Analyze first 50 patients (2-4 weeks)
- [ ] Daily monitoring for first week
- [ ] Weekly check-ins with pilot users
- [ ] Document issues and quick wins

### Scale-Up (Months 6-12)
- [ ] Expand to 20 trained users
- [ ] Analyze 100 patients (quarterly target)
- [ ] Integrate with clinical trial matching workflows
- [ ] Publish internal ROI analysis
- [ ] Plan expansion to other cancer types

---

## Ongoing Operations

### Daily
- [ ] Check monitoring dashboard (errors, uptime)
- [ ] Review cost usage vs. budget
- [ ] Respond to user support requests

### Weekly
- [ ] Review audit logs (unusual access patterns)
- [ ] Check backup success
- [ ] User feedback collection and triage

### Monthly
- [ ] Security log analysis
- [ ] Cost optimization review
- [ ] User access audit (add/remove users as needed)
- [ ] Update documentation

### Quarterly
- [ ] HIPAA compliance re-validation
- [ ] Disaster recovery drill
- [ ] User satisfaction survey
- [ ] Bias audit (production analyses)
- [ ] Roadmap planning (new features, integrations)

---

## Success Criteria

### Technical
- [ ] **Uptime:** >99.5% (excluding planned maintenance)
- [ ] **Response Time:** <30 seconds for 95th percentile queries
- [ ] **Error Rate:** <1% of total analyses
- [ ] **De-identification:** 100% compliance (no PHI leaks)

### Operational
- [ ] **User Satisfaction:** >4.0/5.0 average rating
- [ ] **Cost:** Within per-patient target ([Cost Analysis](../reference/shared/cost-analysis.md))
- [ ] **Time Savings:** Estimated >90% reduction vs. manual (40 hours → <4 hours, pending validation)

### Clinical
- [ ] **Analyses Completed:** 100 patients in first 6 months
- [ ] **Treatment Impact:** >70% of analyses inform clinical decisions
- [ ] **Turnaround Time:** <2 business days from request to results

---

## Troubleshooting Resources

- **[Security Overview](SECURITY_OVERVIEW.md)** - Security controls and troubleshooting
- **[HIPAA Compliance](compliance/hipaa.md)** - Compliance requirements

---

## Contact & Support

**Technical Support:** [Email placeholder]
**On-Call (Severity 1):** [Phone placeholder]
**Slack:** #precision-medicine-mcp (optional)

---

**Related Resources:**
- 🔒 [Security Overview](SECURITY_OVERVIEW.md)
- 📊 [Executive Summary](../for-funders/EXECUTIVE_SUMMARY.md)
- 📖 [HIPAA Compliance](compliance/hipaa.md)

---

**Last Updated:** 2026-02-19
