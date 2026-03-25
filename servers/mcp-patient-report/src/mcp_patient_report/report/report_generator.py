"""
Report Generator - Jinja2 template rendering engine.

Renders PatientReportData into HTML using Jinja2 templates.
"""

import logging
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..models import PatientReportData

logger = logging.getLogger(__name__)

# Template directory - bundled with the package
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class ReportGenerator:
    """Generate HTML reports from PatientReportData using Jinja2 templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the report generator.

        Args:
            templates_dir: Path to templates directory. Defaults to shared templates.
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR

        if not self.templates_dir.exists():
            raise FileNotFoundError(
                f"Templates directory not found: {self.templates_dir}\n"
                f"Expected location: {TEMPLATES_DIR}"
            )

        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml', 'html.j2']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(f"ReportGenerator initialized with templates from: {self.templates_dir}")

    def render_full_report(self, report_data: PatientReportData) -> str:
        """
        Render a comprehensive multi-page patient report.

        Args:
            report_data: Validated PatientReportData model

        Returns:
            Rendered HTML string
        """
        template = self.env.get_template("patient_report_full.html.j2")
        return template.render(report=report_data)

    def render_onepage_summary(self, report_data: PatientReportData) -> str:
        """
        Render a one-page quick reference summary.

        Args:
            report_data: Validated PatientReportData model

        Returns:
            Rendered HTML string
        """
        template = self.env.get_template("patient_report_onepage.html.j2")
        return template.render(report=report_data)

    def render(
        self,
        report_data: PatientReportData,
        report_type: str = "full"
    ) -> str:
        """
        Render a patient report of the specified type.

        Args:
            report_data: Validated PatientReportData model
            report_type: Type of report ("full" or "onepage")

        Returns:
            Rendered HTML string

        Raises:
            ValueError: If report_type is not recognized
        """
        if report_type == "full":
            return self.render_full_report(report_data)
        elif report_type == "onepage":
            return self.render_onepage_summary(report_data)
        else:
            raise ValueError(
                f"Unknown report type: {report_type}. "
                f"Supported types: full, onepage"
            )

    def validate_templates(self) -> dict:
        """
        Validate that all required templates exist and are parseable.

        Returns:
            Dictionary with validation results
        """
        required_templates = [
            "_base.html.j2",
            "patient_report_full.html.j2",
            "patient_report_onepage.html.j2",
        ]

        results = {
            "templates_dir": str(self.templates_dir),
            "templates_found": [],
            "templates_missing": [],
            "templates_valid": [],
            "templates_invalid": [],
        }

        for template_name in required_templates:
            template_path = self.templates_dir / template_name

            if template_path.exists():
                results["templates_found"].append(template_name)

                # Try to load and parse
                try:
                    self.env.get_template(template_name)
                    results["templates_valid"].append(template_name)
                except Exception as e:
                    results["templates_invalid"].append({
                        "template": template_name,
                        "error": str(e)
                    })
            else:
                results["templates_missing"].append(template_name)

        results["all_valid"] = (
            len(results["templates_missing"]) == 0 and
            len(results["templates_invalid"]) == 0
        )

        return results
