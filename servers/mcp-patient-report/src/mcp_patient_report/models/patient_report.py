"""
Pydantic models for patient-facing report data.

This module defines the data contract between the analysis workflow
and the report generator. The LLM constructs PatientReportData JSON
from analysis results, which the report generator validates and renders.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


from .graded_placement import (
    ALLOWED_SECTIONS,
    PlacedGradedResult,
    ReportActionability,
    ReportDetectability,
    ReportEvidenceGrade,
    ReportSection,
)


class EvidenceLevel(str, Enum):
    """Evidence levels for treatment options (oncology + preventive cardiology)."""
    # Oncology: ESMO ESCAT
    ESCAT_I = "ESCAT I"      # FDA approved for this indication
    ESCAT_II = "ESCAT II"    # Standard of care based on strong evidence
    ESCAT_III = "ESCAT III"  # Clinical benefit in other tumor types
    ESCAT_IV = "ESCAT IV"    # Preclinical evidence
    ESCAT_V = "ESCAT V"      # No evidence
    FDA_APPROVED = "FDA Approved"
    NCCN_1 = "NCCN Category 1"
    NCCN_2A = "NCCN Category 2A"
    NCCN_2B = "NCCN Category 2B"
    CLINICAL_TRIAL = "Clinical Trial Only"
    # Preventive cardiology: ACC/AHA and ESC guideline classifications
    ACC_AHA_CLASS_A = "ACC/AHA Class A"
    ACC_AHA_CLASS_B = "ACC/AHA Class B"
    ACC_AHA_CLASS_C = "ACC/AHA Class C"
    ESC_CLASS_I = "ESC Class I"
    ESC_CLASS_IIA = "ESC Class IIa"
    ESC_CLASS_IIB = "ESC Class IIb"
    GUIDELINE_RECOMMENDED = "Guideline Recommended"
    EVIDENCE_LEVEL_A = "Evidence Level A"
    EVIDENCE_LEVEL_B = "Evidence Level B"
    EVIDENCE_LEVEL_C = "Evidence Level C"


class ImmuneStatus(str, Enum):
    """Tumor immune microenvironment classification."""
    HOT = "hot"              # High immune infiltration
    COLD = "cold"            # Low immune infiltration
    MIXED = "mixed"          # Heterogeneous
    UNKNOWN = "unknown"


class ResourceType(str, Enum):
    """Types of support resources."""
    GENETIC_COUNSELING = "genetic_counseling"
    FINANCIAL_ASSISTANCE = "financial_assistance"
    SUPPORT_GROUP = "support_group"
    PATIENT_ADVOCACY = "patient_advocacy"
    CLINICAL_NAVIGATION = "clinical_navigation"
    MENTAL_HEALTH = "mental_health"


class PatientInfo(BaseModel):
    """Patient demographic information."""
    name: str = Field(..., description="Patient full name")
    age: int = Field(..., ge=0, le=150, description="Patient age in years")
    sex: str = Field(..., description="Patient sex (Male/Female/Other)")
    patient_id: str = Field(..., description="Patient identifier")
    diagnosis: str = Field(..., description="Plain-language disease name")


class DiagnosisSummary(BaseModel):
    """Summary of the diagnosis or health profile.

    For oncology reports, cancer_type and stage are expected.
    For preventive health reports (e.g., PAT003), these fields are optional.
    """
    cancer_type: Optional[str] = Field(None, description="Cancer type (e.g., 'Ovarian Cancer'). Optional for non-oncology reports.")
    subtype: Optional[str] = Field(None, description="Histological subtype (e.g., 'High-Grade Serous')")
    stage: Optional[str] = Field(None, description="Cancer stage (e.g., 'Stage IV'). Optional for non-oncology reports.")
    grade: Optional[str] = Field(None, description="Tumor grade if applicable")
    plain_language_description: str = Field(
        ...,
        description="1-2 sentence explanation of what the diagnosis means"
    )
    key_positive_factors: list[str] = Field(
        default_factory=list,
        description="List of positive factors (e.g., 'BRCA1 mutation opens targeted therapy options')"
    )
    key_challenges: list[str] = Field(
        default_factory=list,
        description="List of challenges (e.g., 'Platinum-resistant disease limits some treatment options')"
    )


class GenomicFinding(BaseModel):
    """Individual genomic finding with plain-language explanation."""
    gene: str = Field(..., description="Gene name (e.g., 'TP53')")
    variant: str = Field(..., description="Variant description (e.g., 'R175H missense mutation')")
    significance: str = Field(..., description="Clinical significance (Pathogenic/Likely Pathogenic/VUS)")
    variant_allele_frequency: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="VAF as decimal (0-1)"
    )
    plain_language: str = Field(
        ...,
        description="What this means for the patient in simple terms"
    )
    actionability: Optional[str] = Field(
        None,
        description="FDA-approved therapy or clinical trial opportunity"
    )
    icon: Optional[str] = Field(
        None,
        description="Icon indicator: 'positive' (green), 'caution' (amber), 'attention' (red)"
    )


class SpatialFindings(BaseModel):
    """Spatial transcriptomics analysis findings."""
    tumor_microenvironment_summary: str = Field(
        ...,
        description="Overview of tumor microenvironment composition"
    )
    immune_infiltration: ImmuneStatus = Field(
        ...,
        description="Immune status classification"
    )
    key_spatial_patterns: list[str] = Field(
        default_factory=list,
        description="Notable spatial patterns observed"
    )
    plain_language: str = Field(
        ...,
        description="What the spatial analysis means for treatment in simple terms"
    )


class HistologyFindings(BaseModel):
    """Histopathology findings from imaging analysis."""
    key_observations: list[str] = Field(
        default_factory=list,
        description="Key histological observations"
    )
    cell_counts: Optional[dict[str, int]] = Field(
        None,
        description="Cell type counts from segmentation"
    )
    plain_language: str = Field(
        ...,
        description="What the microscopy shows in simple terms"
    )


class TreatmentOption(BaseModel):
    """Individual treatment option with evidence."""
    name: str = Field(..., description="Treatment name (e.g., 'Olaparib')")
    type: str = Field(..., description="Treatment type (targeted/chemotherapy/immunotherapy/trial)")
    evidence_level: EvidenceLevel = Field(..., description="ESMO ESCAT or FDA status")
    expected_response_rate: Optional[str] = Field(
        None,
        description="Expected response rate if available (e.g., '60-70%')"
    )
    plain_language_description: str = Field(
        ...,
        description="How this treatment works in simple terms"
    )
    common_side_effects: list[str] = Field(
        default_factory=list,
        description="Common side effects to expect"
    )
    why_recommended: str = Field(
        ...,
        description="Why this treatment is relevant for this patient"
    )


class ClinicalTrial(BaseModel):
    """Matched clinical trial information."""
    nct_id: str = Field(..., description="ClinicalTrials.gov NCT number")
    title: str = Field(..., description="Trial title")
    phase: str = Field(..., description="Trial phase (1/2/3)")
    status: str = Field(..., description="Recruitment status")
    location: Optional[str] = Field(None, description="Nearest trial site")
    plain_language_why_relevant: str = Field(
        ...,
        description="Why this trial might be good for this patient"
    )
    contact_info: Optional[str] = Field(None, description="Contact information for enrollment")


class MonitoringScheduleItem(BaseModel):
    """Individual monitoring schedule item."""
    test_name: str = Field(..., description="Name of test or scan")
    frequency: str = Field(..., description="How often (e.g., 'Every 3 months')")
    purpose: str = Field(..., description="Why this test is important")


class MonitoringPlan(BaseModel):
    """Follow-up monitoring plan."""
    schedule: list[MonitoringScheduleItem] = Field(
        default_factory=list,
        description="List of scheduled tests and their timing"
    )
    warning_signs: list[str] = Field(
        default_factory=list,
        description="Symptoms that should prompt immediate contact with care team"
    )
    who_to_contact: Optional[str] = Field(
        None,
        description="Contact information for questions or concerns"
    )


class FamilyImplications(BaseModel):
    """Genetic implications for family members."""
    has_germline_findings: bool = Field(..., description="Whether germline findings exist")
    germline_findings_plain_language: Optional[str] = Field(
        None,
        description="What the germline findings mean for family members"
    )
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Recommended actions for family (e.g., 'Siblings should consider genetic testing')"
    )
    genetic_counseling_recommended: bool = Field(
        default=False,
        description="Whether genetic counseling is recommended"
    )


class SupportResource(BaseModel):
    """Support resource for patients."""
    name: str = Field(..., description="Resource name")
    type: ResourceType = Field(..., description="Type of resource")
    phone: Optional[str] = Field(None, description="Phone number")
    url: Optional[str] = Field(None, description="Website URL")
    description: str = Field(..., description="What this resource provides")


# ---------------------------------------------------------------------------
# Clinical-report-only models (dense, clinician-facing)
# ---------------------------------------------------------------------------


class TMBData(BaseModel):
    """Tumor Mutational Burden summary."""
    mutations_per_mb: float = Field(..., ge=0, description="TMB in mutations per megabase")
    total_mutations: Optional[int] = Field(None, ge=0, description="Total somatic mutations counted")
    percentile: Optional[str] = Field(None, description="TMB percentile within tumor type")
    category: Optional[str] = Field(
        None, description="TMB category (e.g., Low, Intermediate, High, Hypermutator)"
    )


class HRDData(BaseModel):
    """Homologous Recombination Deficiency score."""
    hrd_score: int = Field(..., ge=0, description="Combined HRD score")
    hrd_positive: bool = Field(..., description="Whether HRD-positive (score >= 42 typical)")
    loh: Optional[int] = Field(None, ge=0, description="Loss of heterozygosity component")
    tai: Optional[int] = Field(None, ge=0, description="Telomeric allelic imbalance component")
    lst: Optional[int] = Field(None, ge=0, description="Large-scale state transitions component")
    brca_status: Optional[dict] = Field(
        None, description="BRCA1/2 status detail (e.g., {'gene': 'BRCA1', 'status': 'mutated'})"
    )


class MHCBindingResult(BaseModel):
    """Individual MHC binding prediction for a neoantigen candidate."""
    peptide: str = Field(..., description="Peptide sequence")
    allele: str = Field(..., description="HLA allele (e.g., HLA-A*02:01)")
    ic50_nm: float = Field(..., ge=0, description="Predicted IC50 in nanomolar")
    percentile_rank: float = Field(..., ge=0, le=100, description="Percentile rank (lower = stronger)")
    binder_level: str = Field(
        ..., description="Binding strength: strong_binder, weak_binder, or non_binder"
    )
    source_gene: str = Field(..., description="Gene harboring the source mutation")
    source_mutation: str = Field(..., description="Mutation generating this neoantigen")


class NeoantigenData(BaseModel):
    """Neoantigen burden and top binding results."""
    estimated_neoantigens: int = Field(..., ge=0, description="Total predicted neoantigens")
    strong_binders: int = Field(..., ge=0, description="Count of strong MHC binders (IC50 < 50 nM)")
    weak_binders: int = Field(default=0, ge=0, description="Count of weak MHC binders (50-500 nM)")
    top_binding_results: list[MHCBindingResult] = Field(
        default_factory=list, description="Top MHC binding predictions"
    )


class PerturbationEffect(BaseModel):
    """Single gene-level effect from a perturbation prediction."""
    gene: str = Field(..., description="Affected gene symbol")
    direction: str = Field(..., description="up or down")
    magnitude: Optional[float] = Field(None, description="Log2 fold-change magnitude")


class PerturbationResult(BaseModel):
    """GEARS perturbation prediction result for one treatment context."""
    treatment: str = Field(..., description="Treatment or perturbation applied (e.g., 'NNMT+STAT3')")
    cell_type: str = Field(..., description="Cell type context (e.g., 'tumor_core')")
    top_effects: list[PerturbationEffect] = Field(
        default_factory=list, description="Top predicted gene-level effects"
    )
    interpretation: Optional[str] = Field(
        None, description="Clinical interpretation of the perturbation result"
    )


class OpenTargetsHit(BaseModel):
    """Open Targets drug-target association hit."""
    gene_symbol: str = Field(..., description="Gene symbol (e.g., PIK3CA)")
    overall_score: float = Field(..., ge=0, le=1, description="Overall association score (0-1)")
    disease_name: Optional[str] = Field(None, description="Disease name from Open Targets")
    evidence_count: Optional[int] = Field(None, ge=0, description="Number of evidence items")
    tractability: Optional[str] = Field(
        None, description="Tractability assessment (e.g., 'Small molecule', 'Antibody')"
    )
    known_drugs: list[str] = Field(
        default_factory=list, description="Known drugs targeting this gene"
    )


class ReportMetadata(BaseModel):
    """Report metadata and provenance."""
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Report generation timestamp"
    )
    report_version: str = Field(default="1.0", description="Report version")
    report_status: str = Field(
        default="preliminary",
        description="Status: preliminary (draft) or current (approved)"
    )
    disclaimer: str = Field(
        default="This AI-generated summary must be reviewed by your healthcare team before any treatment decisions. It is not a substitute for professional medical advice.",
        description="Required disclaimer text"
    )
    data_sources: list[str] = Field(
        default_factory=list,
        description="Which MCP servers/data sources contributed to this report"
    )
    reading_level_target: str = Field(
        default="6th-8th grade",
        description="Target reading level for plain language text"
    )
    clinician_reviewer: Optional[str] = Field(
        None,
        description="Name of clinician who reviewed/approved the report"
    )
    review_date: Optional[datetime] = Field(
        None,
        description="Date of clinician review"
    )


class PatientReportData(BaseModel):
    """
    Complete patient report data model.

    This is the contract between the analysis workflow and the report generator.
    The LLM constructs this JSON from conversation context, validates it,
    and passes it to the generate_patient_report tool.
    """

    # Report classification
    report_category: str = Field(
        default="oncology",
        description="Report category: 'oncology', 'preventive_health', or 'general'"
    )

    # Required sections
    patient_info: PatientInfo = Field(..., description="Patient demographics")
    diagnosis_summary: DiagnosisSummary = Field(..., description="Diagnosis overview")
    genomic_findings: list[GenomicFinding] = Field(
        default_factory=list,
        description="List of genomic findings"
    )
    treatment_options: list[TreatmentOption] = Field(
        default_factory=list,
        description="Recommended treatment options"
    )
    monitoring_plan: MonitoringPlan = Field(..., description="Follow-up monitoring plan")
    metadata: ReportMetadata = Field(
        default_factory=ReportMetadata,
        description="Report metadata and provenance"
    )

    # Optional sections
    spatial_findings: Optional[SpatialFindings] = Field(
        None,
        description="Spatial transcriptomics findings (if available)"
    )
    histology_findings: Optional[HistologyFindings] = Field(
        None,
        description="Histopathology findings (if available)"
    )
    clinical_trials: list[ClinicalTrial] = Field(
        default_factory=list,
        description="Matched clinical trials"
    )
    family_implications: Optional[FamilyImplications] = Field(
        None,
        description="Genetic implications for family members"
    )
    support_resources: list[SupportResource] = Field(
        default_factory=list,
        description="Patient support resources"
    )

    # Branding (white-label support)
    hospital_name: Optional[str] = Field(
        None,
        description="Hospital/institution name for branding"
    )
    hospital_logo_path: Optional[str] = Field(
        None,
        description="Path to hospital logo image"
    )

    # Clinical-report-only fields (optional, no effect on patient-facing reports)
    tmb_data: Optional[TMBData] = Field(
        None, description="Tumor Mutational Burden data (clinical report only)"
    )
    hrd_data: Optional[HRDData] = Field(
        None, description="Homologous Recombination Deficiency data (clinical report only)"
    )
    neoantigen_data: Optional[NeoantigenData] = Field(
        None, description="Neoantigen burden and binding predictions (clinical report only)"
    )
    perturbation_results: list[PerturbationResult] = Field(
        default_factory=list,
        description="GEARS perturbation predictions (clinical report only)"
    )
    graded_results: list[PlacedGradedResult] = Field(
        default_factory=list,
        description=(
            "GradedResult envelopes from analytic tools, each declaring the report "
            "section it appears in. Placement is validated: a PROGNOSTIC_ONLY result "
            "cannot appear in treatment hypotheses, and a result with no stated "
            "assumptions is rejected."
        ),
    )
    open_targets_hits: list[OpenTargetsHit] = Field(
        default_factory=list,
        description="Open Targets drug-target associations (clinical report only)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "patient_info": {
                    "name": "Sarah Anderson",
                    "age": 58,
                    "sex": "Female",
                    "patient_id": "PAT001-OVC-2025",
                    "diagnosis": "Stage IV High-Grade Serous Ovarian Cancer"
                },
                "diagnosis_summary": {
                    "cancer_type": "Ovarian Cancer",
                    "subtype": "High-Grade Serous Carcinoma",
                    "stage": "Stage IV",
                    "grade": "High Grade",
                    "plain_language_description": "You have an advanced form of ovarian cancer that has spread beyond the ovaries. While this is serious, there are effective treatments available.",
                    "key_positive_factors": [
                        "Your BRCA1 mutation makes you eligible for PARP inhibitor therapy",
                        "Your tumor shows good immune cell infiltration"
                    ],
                    "key_challenges": [
                        "The cancer is platinum-resistant, which limits some chemotherapy options"
                    ]
                },
                "genomic_findings": [
                    {
                        "gene": "BRCA1",
                        "variant": "Pathogenic germline mutation",
                        "significance": "Pathogenic",
                        "plain_language": "You carry a change in the BRCA1 gene that increases cancer risk but also makes your cancer more responsive to certain targeted therapies.",
                        "actionability": "PARP inhibitors (olaparib, niraparib) are FDA-approved",
                        "icon": "positive"
                    }
                ],
                "treatment_options": [],
                "monitoring_plan": {
                    "schedule": [],
                    "warning_signs": ["Severe abdominal pain", "Difficulty breathing"],
                    "who_to_contact": "Your oncology nurse navigator"
                },
                "metadata": {
                    "report_version": "1.0",
                    "report_status": "preliminary",
                    "data_sources": ["mcp-epic", "mcp-fgbio", "mcp-spatialtools"]
                }
            }
        }
