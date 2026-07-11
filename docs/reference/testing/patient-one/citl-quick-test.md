# CitL Workflow Quick Test Guide

**Goal:** Test the complete Clinician-in-the-Loop validation workflow with PatientOne data

**Time Required:** 10-15 minutes
**Prerequisites:** PatientOne spatial data available, Python environment with dependencies

---

## Test Steps

### Step 1: Generate Draft Report (~30 seconds)

```bash
cd /Users/lynnlangit/Documents/GitHub/spatial-mcp

# Use spatialtools venv (has all dependencies)
/Users/lynnlangit/Documents/GitHub/spatial-mcp/servers/mcp-spatialtools/venv/bin/python3 \
  servers/mcp-patient-report/scripts/generate_patient_report.py \
  --patient-id PAT001-OVC-2025 \
  --output-dir ./results \
  --generate-draft
```

**Expected Output:**
```
✅ DRAFT REPORT COMPLETE! Ready for CitL review.
   Draft report: results/PAT001-OVC-2025/draft_report.json
   Quality checks: results/PAT001-OVC-2025/quality_checks.json
   Clinical summary: results/PAT001-OVC-2025/clinical_summary.txt
```

**Verify Files Created:**
```bash
ls -lh results/PAT001-OVC-2025/
# Should see: draft_report.json, quality_checks.json, clinical_summary.txt
```

---

### Step 2: Review Quality Checks (~2 minutes)

```bash
# View quality check results
cat results/PAT001-OVC-2025/quality_checks.json | python3 -m json.tool
```

**What to Check:**
- `all_checks_passed`: true or false
- `flags`: [] (empty if all passed) or list of warnings/critical issues
- 4 checks should be present: sample_size_adequate, fdr_thresholds_met, data_completeness, consistency_cross_modal

**Expected for PatientOne:** All checks should PASS (no flags)

---

### Step 3: Review Draft Report (~3 minutes)

```bash
# View draft report structure
cat results/PAT001-OVC-2025/draft_report.json | python3 -m json.tool | head -50

# View clinical summary (human-readable)
cat results/PAT001-OVC-2025/clinical_summary.txt
```

**What to Check:**
- `report_metadata.status`: should be "pending_review"
- `key_molecular_findings`: should have 10 findings (DEG_1 through DEG_10)
- `treatment_recommendations`: should have recommendations based on molecular profile
- `flags_for_review`: should match quality_checks.json flags

---

### Step 4: Create Mock Review (~3 minutes)

For quick testing, create a simplified review JSON (normally clinician would complete full template):

```bash
cat > results/PAT001-OVC-2025/citl_review_completed.json <<'EOF'
{
  "patient_id": "PAT001-OVC-2025",
  "report_date": "2026-01-13T14:00:00Z",
  "reviewer": {
    "name": "Dr. Test Reviewer",
    "email": "test.reviewer@hospital.org",
    "credentials": "MD, Medical Oncology",
    "role": "oncologist"
  },
  "review_date": "2026-01-13T15:00:00Z",
  "decision": {
    "status": "APPROVE",
    "rationale": "All findings consistent with clinical presentation. Quality checks passed. Molecular results align with platinum-resistant HGSOC. Treatment recommendations follow NCCN guidelines."
  },
  "per_finding_validation": [
    {
      "finding_id": "DEG_1",
      "gene": "TP53",
      "validation_status": "CONFIRMED",
      "comments": "Expected finding for HGSOC"
    }
  ],
  "guideline_compliance": {
    "nccn_aligned": "ALIGNED",
    "institutional_aligned": "ALIGNED"
  },
  "quality_flags_assessment": [],
  "treatment_recommendations_review": [],
  "attestation": {
    "reviewed_all_findings": true,
    "assessed_compliance": true,
    "clinical_judgment": true,
    "medical_record_acknowledgment": true
  },
  "revision_count": 0
}
EOF
```

**Note:** In production, clinicians would complete the full `docs/for-hospitals/citl-workflows/CITL_REVIEW_TEMPLATE.md`

---

### Step 5: Submit Review (~5 seconds)

```bash
# Submit review with signature and audit logging
/Users/lynnlangit/Documents/GitHub/spatial-mcp/servers/mcp-spatialtools/venv/bin/python3 \
  servers/mcp-patient-report/scripts/citl_submit_review.py \
  --patient-id PAT001-OVC-2025 \
  --review-file results/PAT001-OVC-2025/citl_review_completed.json \
  --skip-cloud-logging
```

**Expected Output:**
```
📋 CitL Review Submission
======================================================================
✅ Schema validation passed
🔐 Generating digital signature...
✅ Logged locally to: citl_review_audit_trail.jsonl
💾 Saving signed review...
======================================================================
Review Submission Summary
======================================================================
Patient ID:       PAT001-OVC-2025
Decision:         APPROVE
Reviewer:         Dr. Test Reviewer (MD, Medical Oncology)
Signature Hash:   abc123...
Signed Review:    results/PAT001-OVC-2025/citl_review_completed_signed.json
```

**Verify Files Created:**
```bash
ls -lh results/PAT001-OVC-2025/*_signed.json
cat citl_review_audit_trail.jsonl | tail -1 | python3 -m json.tool
```

---

### Step 6: Finalize Approved Report (~10 seconds)

```bash
# Generate final approved report
/Users/lynnlangit/Documents/GitHub/spatial-mcp/servers/mcp-spatialtools/venv/bin/python3 \
  servers/mcp-patient-report/scripts/finalize_patient_report.py \
  --patient-id PAT001-OVC-2025 \
  --output-dir ./results
```

**Expected Output:**
```
📋 Report Finalization
======================================================================
✅ Review status: APPROVED
   Reviewer: Dr. Test Reviewer
📝 Generating final approved report...
💾 Saving final report...
======================================================================
Final Report Summary
======================================================================
Patient ID:           PAT001-OVC-2025
Status:               clinically_approved
Reviewer:             Dr. Test Reviewer (MD, Medical Oncology)
Review Decision:      APPROVE
======================================================================
✅ Report finalization complete!
```

**Verify Final Report:**
```bash
ls -lh results/PAT001-OVC-2025/final_report_approved.json

# Check status
cat results/PAT001-OVC-2025/final_report_approved.json | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Status: {data['report_metadata']['status']}\")"
```

**Expected:** Status should be "clinically_approved"

---

## Test Scenarios

### Scenario A: Test REVISE Decision

Modify mock review:
```bash
# Change decision status to REVISE
sed -i '' 's/"status": "APPROVE"/"status": "REVISE"/' results/PAT001-OVC-2025/citl_review_completed.json

# Add revision instructions
cat >> results/PAT001-OVC-2025/citl_review_completed.json <<'EOF'
,
  "revision_instructions": {
    "issues_to_address": [
      "Test issue: Exclude tumor_necrotic region due to sample size"
    ],
    "reanalysis_parameters": {
      "regions_to_exclude": ["tumor_necrotic"],
      "min_spots_per_region": 50
    },
    "resubmission_date": "2026-01-20"
  }
}
EOF
```

**Then submit and try to finalize:**
```bash
# Submit REVISE review
python3 servers/mcp-patient-report/scripts/citl_submit_review.py --patient-id PAT001-OVC-2025 --review-file results/PAT001-OVC-2025/citl_review_completed.json --skip-cloud-logging

# Try to finalize - should FAIL
python3 servers/mcp-patient-report/scripts/finalize_patient_report.py --patient-id PAT001-OVC-2025
```

**Expected:** Finalization should fail with message about addressing revision instructions

---

### Scenario B: Test REJECT Decision

```bash
# Change to REJECT
# (follow same pattern as REVISE scenario)
```

---

## Validation Checklist

After running all steps, verify:

- [ ] Draft report generated with quality checks
- [ ] Quality checks JSON contains 4 automated checks
- [ ] Review form submitted successfully
- [ ] Digital signature (SHA-256) generated and added to review
- [ ] Audit trail logged (local file: citl_review_audit_trail.jsonl)
- [ ] Signed review file created (*_signed.json)
- [ ] Final report generated with status "clinically_approved"
- [ ] Final report contains clinical_attestation section
- [ ] REVISE decision prevents finalization (if tested)

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pandas'"

**Fix:** Use spatialtools venv:
```bash
/Users/lynnlangit/Documents/GitHub/spatial-mcp/servers/mcp-spatialtools/venv/bin/python3 scripts/...
```

### Error: "Could not find spatial data for PAT001-OVC-2025"

**Fix:** Check data directory exists:
```bash
ls -la /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT001-OVC-2025/spatial/
```

### Error: "Schema validation failed"

**Fix:** Ensure JSON is valid:
```bash
cat results/PAT001-OVC-2025/citl_review_completed.json | python3 -m json.tool
```

### Warning: "google-cloud-logging not available"

**Expected:** This is normal. Use `--skip-cloud-logging` flag for local testing.

---

## Success Criteria

✅ **Test passes if:**
1. Draft report generates with quality checks
2. Review submission succeeds with digital signature
3. Audit trail entry created
4. Final report has status "clinically_approved"
5. REVISE decision blocks finalization

**Total test time:** ~10-15 minutes (5 minutes if skipping scenarios)

---

## Next Steps After Testing

1. **Review outputs:** Check all JSON files for correct structure
2. **Verify audit trail:** Inspect `citl_review_audit_trail.jsonl`
3. **Test with real data:** Replace mock review with complete template
4. **Integration testing:** Run full TEST_1-6 workflow in Claude Desktop
5. **Production readiness:** Configure Cloud Logging, test with oncologist

---

**Document Version:** 1.0
**Part of:** Precision Medicine MCP - CitL Validation Workflow Testing
