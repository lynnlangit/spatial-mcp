"""Tests for report generator."""

import json
from pathlib import Path
import pytest

from mcp_patient_report.models import PatientReportData
from mcp_patient_report.report.report_generator import ReportGenerator


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def pat001_data() -> PatientReportData:
    """Load PAT001 fixture data."""
    fixture_path = FIXTURES_DIR / "pat001_report_data.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return PatientReportData(**data)


@pytest.fixture
def pat001_clinical_data() -> PatientReportData:
    """Load PAT001 clinical report fixture data (includes TMB/HRD/neoantigen/etc.)."""
    fixture_path = FIXTURES_DIR / "pat001_clinical_report_data.json"
    with open(fixture_path) as f:
        data = json.load(f)
    return PatientReportData(**data)


@pytest.fixture
def report_generator() -> ReportGenerator:
    """Create report generator with templates."""
    # Templates are bundled with the package
    templates_dir = Path(__file__).parent.parent / "src" / "mcp_patient_report" / "templates"
    if not templates_dir.exists():
        pytest.skip(f"Templates directory not found: {templates_dir}")
    return ReportGenerator(templates_dir)


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_validate_templates(self, report_generator):
        """Test template validation."""
        result = report_generator.validate_templates()

        assert result["all_valid"] is True
        assert "_base.html.j2" in result["templates_found"]
        assert "patient_report_full.html.j2" in result["templates_found"]
        assert "patient_report_onepage.html.j2" in result["templates_found"]

    def test_render_full_report(self, report_generator, pat001_data):
        """Test rendering full report."""
        html = report_generator.render_full_report(pat001_data)

        # Check key content is present
        assert "Sarah Anderson" in html
        assert "Stage IV" in html
        assert "BRCA1" in html
        assert "Olaparib" in html
        assert "DRAFT" in html  # Should have draft watermark

    def test_render_onepage_summary(self, report_generator, pat001_data):
        """Test rendering one-page summary."""
        html = report_generator.render_onepage_summary(pat001_data)

        assert "Sarah Anderson" in html
        assert "Ovarian Cancer" in html
        assert "Key Findings" in html

    def test_render_with_type(self, report_generator, pat001_data):
        """Test render method with type parameter."""
        full_html = report_generator.render(pat001_data, "full")
        onepage_html = report_generator.render(pat001_data, "onepage")

        # Full report should be longer
        assert len(full_html) > len(onepage_html)

    def test_render_invalid_type(self, report_generator, pat001_data):
        """Test render with invalid type raises error."""
        with pytest.raises(ValueError, match="Unknown report type"):
            report_generator.render(pat001_data, "invalid_type")

    def test_html_escaping(self, report_generator):
        """Test that HTML content is properly escaped."""
        from mcp_patient_report.models import (
            PatientInfo,
            DiagnosisSummary,
            MonitoringPlan,
        )

        # Create data with potential XSS
        data = PatientReportData(
            patient_info=PatientInfo(
                name="<script>alert('xss')</script>",
                age=50,
                sex="Female",
                patient_id="TEST",
                diagnosis="Test"
            ),
            diagnosis_summary=DiagnosisSummary(
                cancer_type="Test",
                stage="I",
                plain_language_description="Test"
            ),
            monitoring_plan=MonitoringPlan(
                warning_signs=["Test"]
            )
        )

        html = report_generator.render_full_report(data)

        # XSS payload should be escaped, not rendered as raw HTML
        assert "<script>alert('xss')</script>" not in html
        assert "&lt;script&gt;" in html


class TestXAIContext:
    """Tests for XAI evidence strength summary in rendered reports."""

    def test_full_report_with_xai_context(self, report_generator, pat001_data):
        """XAI section renders when extra context is provided."""
        xai_collection = {
            "somatic_variants": {
                "confidence_level": "high",
                "confidence_note": "Validated somatic calls",
                "evidence_grade": "ACMG Tier I",
                "key_drivers": ["FoundationOne CDx"],
            },
            "spatial_autocorrelation": {
                "confidence_level": "moderate",
                "confidence_note": "Computational prediction",
                "evidence_grade": "Algorithm-predicted",
                "key_drivers": ["Moran's I"],
            },
            "cell_type_fidelity": {
                "confidence_level": "low",
                "confidence_note": "SYNTHETIC simulation only",
                "evidence_grade": "Research-only",
                "key_drivers": ["Quantum sim"],
            },
        }
        evidence_strength_summary = {
            "confidence_counts": {"high": 1, "moderate": 1, "low": 1},
            "lowest_confidence_items": ["Quantum Cell-Type Fidelity"],
            "synthetic_data_items": ["Quantum Cell-Type Fidelity"],
            "action_required": True,
            "table_text": "",
        }
        xai_tool_labels = {
            "somatic_variants": "Somatic Variant Calls",
            "spatial_autocorrelation": "Spatial Autocorrelation (Moran's I)",
            "cell_type_fidelity": "Quantum Cell-Type Fidelity",
        }

        html = report_generator.render_full_report(
            pat001_data,
            evidence_strength_summary=evidence_strength_summary,
            xai_collection=xai_collection,
            xai_tool_labels=xai_tool_labels,
        )

        assert "Evidence Strength Summary" in html
        assert "HIGH" in html
        assert "MODERATE" in html
        assert "LOW" in html
        assert "Somatic Variant Calls" in html
        assert "Quantum Cell-Type Fidelity" in html
        assert "Synthetic Data Warning" in html
        assert "Action Required" in html

    def test_full_report_without_xai_context(self, report_generator, pat001_data):
        """XAI section does NOT render when no extra context is provided."""
        html = report_generator.render_full_report(pat001_data)

        # The <h2> heading and rendered table should be absent.
        # (CSS class names like xai-chip--high appear in the inlined
        # stylesheet, so only check for rendered section content.)
        assert "<h2>Evidence Strength Summary</h2>" not in html
        assert "Synthetic Data Warning" not in html
        assert "Action Required" not in html


class TestHealthLiteracy:
    """Tests for health literacy compliance."""

    def test_reading_level_indicator(self, report_generator, pat001_data):
        """Test that reading level is indicated in metadata."""
        assert pat001_data.metadata.reading_level_target == "6th-8th grade"

    def test_plain_language_fields_present(self, pat001_data):
        """Test that plain language fields are filled."""
        # Diagnosis summary
        assert len(pat001_data.diagnosis_summary.plain_language_description) > 50

        # All genomic findings should have plain language
        for finding in pat001_data.genomic_findings:
            assert len(finding.plain_language) > 20

        # All treatment options should have plain language
        for treatment in pat001_data.treatment_options:
            assert len(treatment.plain_language_description) > 20

    def test_disclaimer_present(self, report_generator, pat001_data):
        """Test that disclaimer is prominent in report."""
        html = report_generator.render_full_report(pat001_data)

        assert "must be reviewed" in html.lower()
        assert "healthcare team" in html.lower()


class TestClinicalReport:
    """Tests for clinical report rendering."""

    def test_render_clinical_report(self, report_generator, pat001_clinical_data):
        """Basic render: patient ID, section headers, and DRAFT banner present."""
        html = report_generator.render_clinical_report(pat001_clinical_data)

        assert "PAT001-OVC-2025" in html
        assert "Clinical Genomic Report" in html
        assert "DRAFT -- NOT FOR CLINICAL USE" in html
        assert "1. Genomic Profile" in html
        assert "5. Treatment Hypotheses" in html

    def test_render_via_dispatch(self, report_generator, pat001_clinical_data):
        """render() dispatches to clinical correctly."""
        html = report_generator.render(pat001_clinical_data, "clinical")

        assert "Clinical Genomic Report" in html
        assert "PAT001-OVC-2025" in html

    def test_clinical_tmb_section(self, report_generator, pat001_clinical_data):
        """TMB value renders in clinical report."""
        html = report_generator.render_clinical_report(pat001_clinical_data)

        assert "3.5" in html
        assert "Mutations / Mb" in html
        assert "112" in html

    def test_clinical_hrd_section(self, report_generator, pat001_clinical_data):
        """HRD score renders in clinical report."""
        html = report_generator.render_clinical_report(pat001_clinical_data)

        assert "HRD Status" in html
        assert "44" in html
        assert "Positive" in html
        assert "LOH 18" in html

    def test_clinical_neoantigen_table(self, report_generator, pat001_clinical_data):
        """Neoantigen binding table renders peptide and HLA allele."""
        html = report_generator.render_clinical_report(pat001_clinical_data)

        assert "HMTEVVRHC" in html
        assert "HLA-A*02:01" in html
        assert "Strong" in html

    def test_clinical_perturbation_section(self, report_generator, pat001_clinical_data):
        """Perturbation section renders with NNMT and purple header."""
        html = report_generator.render_clinical_report(pat001_clinical_data)

        assert "GEARS Perturbation" in html
        assert "NNMT+STAT3" in html
        assert "VEGFA" in html
        assert "section-header-purple" in html

    def test_clinical_open_targets_section(self, report_generator, pat001_clinical_data):
        """Open Targets section renders PIK3CA and score."""
        html = report_generator.render_clinical_report(pat001_clinical_data)

        assert "Open Targets" in html
        assert "PIK3CA" in html
        assert "0.78" in html
        assert "Alpelisib" in html

    def test_clinical_without_optional_sections(self, report_generator, pat001_data):
        """Clinical report renders without crash when TMB/HRD/neoantigen/etc. absent."""
        html = report_generator.render_clinical_report(pat001_data)

        # Core sections still render
        assert "PAT001-OVC-2025" in html
        assert "1. Genomic Profile" in html
        assert "5. Treatment Hypotheses" in html

        # Optional sections should NOT appear
        assert "2. TMB" not in html
        assert "GEARS Perturbation" not in html
        assert "Open Targets" not in html

    def test_clinical_with_xai(self, report_generator, pat001_clinical_data):
        """XAI section renders when extra_context provided."""
        xai_collection = {
            "somatic_variants": {
                "confidence_level": "high",
                "confidence_note": "Validated somatic calls",
                "evidence_grade": "ACMG Tier I",
                "key_drivers": ["FoundationOne CDx"],
            },
        }
        evidence_strength_summary = {
            "confidence_counts": {"high": 1, "moderate": 0, "low": 0},
            "lowest_confidence_items": [],
            "synthetic_data_items": [],
            "action_required": False,
            "table_text": "",
        }
        xai_tool_labels = {
            "somatic_variants": "Somatic Variant Calls",
        }

        html = report_generator.render_clinical_report(
            pat001_clinical_data,
            evidence_strength_summary=evidence_strength_summary,
            xai_collection=xai_collection,
            xai_tool_labels=xai_tool_labels,
        )

        assert "XAI Evidence Strength Summary" in html
        assert "Somatic Variant Calls" in html
        assert "HIGH" in html

    def test_clinical_html_escaping(self, report_generator):
        """XSS payloads are escaped in clinical template."""
        from mcp_patient_report.models import (
            PatientInfo,
            DiagnosisSummary,
            MonitoringPlan,
            GenomicFinding,
            TreatmentOption,
        )

        data = PatientReportData(
            patient_info=PatientInfo(
                name="Test Patient",
                age=50,
                sex="Female",
                patient_id="<script>alert('xss')</script>",
                diagnosis="Test"
            ),
            diagnosis_summary=DiagnosisSummary(
                cancer_type="Test",
                stage="I",
                plain_language_description="Test"
            ),
            genomic_findings=[
                GenomicFinding(
                    gene="<img src=x onerror=alert(1)>",
                    variant="test",
                    significance="VUS",
                    plain_language="test",
                ),
            ],
            treatment_options=[
                TreatmentOption(
                    name="TestDrug",
                    type="test",
                    evidence_level="FDA Approved",
                    plain_language_description="test",
                    why_recommended="test",
                ),
            ],
            monitoring_plan=MonitoringPlan(
                warning_signs=["Test"]
            ),
        )

        html = report_generator.render_clinical_report(data)

        # Patient ID with script tag should be escaped
        assert "<script>alert('xss')</script>" not in html
        assert "&lt;script&gt;" in html
        # Gene name with img tag should be escaped
        assert "<img src=x onerror=alert(1)>" not in html
        assert "&lt;img src=x onerror=alert(1)&gt;" in html

    def test_validate_templates_includes_clinical(self, report_generator):
        """validate_templates() checks for clinical_report.html.j2."""
        result = report_generator.validate_templates()

        assert result["all_valid"] is True
        assert "clinical_report.html.j2" in result["templates_found"]
        assert "clinical_report.html.j2" in result["templates_valid"]
