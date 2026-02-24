"""
Data models for Synthetic EMR Generation.

Contains input/output structures:
- ClinicalScenario: Brief clinical case description (input)
- SyntheticEMR: Complete synthetic electronic medical record (output)
- Supporting dataclasses for demographics, encounters, labs, vitals, etc.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ClinicalScenario:
    """
    Input: A brief clinical case description to generate a full EMR from.

    Example:
        ClinicalScenario(
            diagnosis="Acute cholecystitis",
            history_summary="female, metabolic syndrome",
            ordered_study="CT abdomen w/ contrast",
            protocol_indication="Intermittent RUQ pain for 2 weeks...",
            acr_recommendation="US",
            protocol_suggestion="US",
        )
    """

    diagnosis: str
    history_summary: str = ""
    ordered_study: str = ""
    protocol_indication: str = ""
    acr_recommendation: Optional[str] = None
    protocol_suggestion: Optional[str] = None

    # Optional overrides for demographics
    age_hint: Optional[int] = None
    sex_hint: Optional[str] = None

    # Reproducibility
    seed: Optional[int] = None

    # Optional case metadata
    case_id: Optional[str] = None
    case_name: Optional[str] = None


@dataclass
class PatientDemographics:
    """Synthetic patient identity."""

    first_name: str = ""
    last_name: str = ""
    mrn: str = ""
    date_of_birth: str = ""  # ISO format YYYY-MM-DD
    age: int = 0
    sex: str = ""  # "Male", "Female"
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    insurance: Optional[str] = None
    emergency_contact: Optional[str] = None


@dataclass
class Encounter:
    """A clinical encounter (ED visit, inpatient admission, outpatient visit)."""

    encounter_id: str = ""
    encounter_type: str = ""  # "ED", "Inpatient", "Outpatient", "Urgent Care"
    facility: str = ""
    admission_datetime: str = ""  # ISO format
    discharge_datetime: Optional[str] = None
    attending_provider: str = ""
    department: str = ""
    chief_complaint: str = ""
    disposition: Optional[str] = None  # "Admitted", "Discharged", "Transferred"


@dataclass
class VitalSignSet:
    """A set of vital signs taken at a specific time."""

    timestamp: str = ""  # ISO format
    encounter_id: str = ""
    temperature_f: Optional[float] = None
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    pain_scale: Optional[int] = None
    source: str = ""  # "Triage", "Nursing", "Bedside"


@dataclass
class LabResult:
    """A single lab test result."""

    test_name: str = ""
    value: float = 0.0
    unit: str = ""
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    flag: Optional[str] = None  # "H", "L", "Critical"
    loinc_code: Optional[str] = None


@dataclass
class LabPanel:
    """A panel of lab results (e.g., CBC, CMP, LFT)."""

    panel_name: str = ""
    timestamp: str = ""  # ISO format
    encounter_id: str = ""
    results: list[LabResult] = field(default_factory=list)
    ordering_provider: str = ""


@dataclass
class Medication:
    """A medication entry."""

    name: str = ""
    dose: str = ""
    route: str = ""  # "PO", "IV", "IM", "SubQ", "Topical"
    frequency: str = ""  # "daily", "BID", "TID", "Q8H", "PRN"
    indication: Optional[str] = None
    rxnorm_code: Optional[str] = None


@dataclass
class MedicationList:
    """Home and inpatient medication lists."""

    home_medications: list[Medication] = field(default_factory=list)
    inpatient_medications: list[Medication] = field(default_factory=list)


@dataclass
class Allergy:
    """An allergy entry."""

    allergen: str = ""
    allergy_type: str = ""  # "Drug", "Food", "Environmental"
    reaction: str = ""
    severity: str = ""  # "Mild", "Moderate", "Severe"


@dataclass
class MedicalCondition:
    """A medical history entry."""

    condition: str = ""
    icd10: Optional[str] = None
    onset_year: Optional[int] = None
    status: str = "Active"  # "Active", "Resolved", "Chronic"


@dataclass
class SurgicalProcedure:
    """A surgical history entry."""

    procedure: str = ""
    year: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class SocialHistory:
    """Patient social history."""

    smoking_status: str = "Never"  # "Never", "Former", "Current"
    smoking_details: Optional[str] = None
    alcohol_use: str = "Social"  # "None", "Social", "Daily", "Heavy"
    alcohol_details: Optional[str] = None
    drug_use: str = "None"  # "None", "Former", "Current"
    drug_details: Optional[str] = None
    occupation: Optional[str] = None
    living_situation: Optional[str] = None


@dataclass
class ImagingOrder:
    """An imaging study order."""

    order_id: str = ""
    modality: str = ""  # e.g., "CT", "MRI", "US", "X-ray"
    body_region: str = ""
    contrast: str = ""  # "With IV contrast", "Without contrast", "Without and with contrast"
    indication: str = ""
    ordering_provider: str = ""
    order_datetime: str = ""  # ISO format
    urgency: str = ""  # "STAT", "Urgent", "Routine"
    status: str = "Ordered"  # "Ordered", "In Progress", "Completed"


@dataclass
class ImagingReport:
    """A radiology report."""

    order_id: str = ""
    modality: str = ""
    report_datetime: str = ""  # ISO format
    radiologist: str = ""
    technique: str = ""
    findings: str = ""
    impression: str = ""


@dataclass
class NursingNote:
    """A nursing progress note."""

    timestamp: str = ""  # ISO format
    author: str = ""
    note_text: str = ""


@dataclass
class GenerationMetadata:
    """Metadata about how the EMR was generated."""

    generator_version: str = "1.0.0"
    generation_timestamp: str = ""
    narrative_backend: str = ""  # "medgemma", "ollama", "template"
    seed: Optional[int] = None
    model_id: Optional[str] = None


@dataclass
class SyntheticEMR:
    """
    Complete synthetic electronic medical record.

    Generated from a ClinicalScenario, contains all sections of a realistic EMR.
    """

    # Patient identity
    patient: PatientDemographics = field(default_factory=PatientDemographics)

    # Encounters
    encounters: list[Encounter] = field(default_factory=list)

    # Vital signs (multiple sets across timeline)
    vital_signs: list[VitalSignSet] = field(default_factory=list)

    # Lab results (multiple panels)
    lab_results: list[LabPanel] = field(default_factory=list)

    # Medications
    medications: MedicationList = field(default_factory=MedicationList)

    # Allergies
    allergies: list[Allergy] = field(default_factory=list)

    # Medical history
    medical_history: list[MedicalCondition] = field(default_factory=list)
    surgical_history: list[SurgicalProcedure] = field(default_factory=list)
    family_history: list[str] = field(default_factory=list)
    social_history: SocialHistory = field(default_factory=SocialHistory)

    # Narrative clinical notes
    hpi: str = ""
    physical_exam: str = ""
    assessment_and_plan: str = ""
    nursing_notes: list[NursingNote] = field(default_factory=list)

    # Imaging
    imaging_orders: list[ImagingOrder] = field(default_factory=list)
    imaging_reports: list[ImagingReport] = field(default_factory=list)

    # Discharge
    discharge_summary: Optional[str] = None

    # Source scenario
    source_scenario: Optional[ClinicalScenario] = None

    # Generation metadata
    generation_metadata: GenerationMetadata = field(
        default_factory=GenerationMetadata
    )

    def to_dict(self) -> dict:
        """Convert entire EMR to a JSON-serializable dictionary."""
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_patient_context(self):
        """
        Convert to PatientContext for use with RUQProtocolReviewer.

        Returns a PatientContext object populated from the most recent
        labs, vitals, and clinical data in this EMR.
        """
        from .ruq_models import PatientContext

        ctx = PatientContext()
        ctx.patient_id = self.patient.mrn
        ctx.age = self.patient.age
        ctx.sex = self.patient.sex

        # Most recent vitals
        if self.vital_signs:
            latest_vitals = self.vital_signs[-1]
            ctx.temperature = latest_vitals.temperature_f
            if latest_vitals.temperature_f is not None:
                ctx.has_fever = latest_vitals.temperature_f > 100.4
            ctx.heart_rate = latest_vitals.heart_rate
            ctx.blood_pressure_systolic = latest_vitals.blood_pressure_systolic
            ctx.blood_pressure_diastolic = latest_vitals.blood_pressure_diastolic

        # Most recent labs -- search across all panels
        lab_map = {}
        for panel in self.lab_results:
            for result in panel.results:
                lab_map[result.test_name.lower()] = result.value

        ctx.wbc = lab_map.get("wbc")
        if ctx.wbc is not None:
            ctx.wbc_elevated = ctx.wbc > 11.0
        ctx.ast = lab_map.get("ast")
        ctx.alt = lab_map.get("alt")
        ctx.alp = lab_map.get("alp") or lab_map.get("alkaline phosphatase")
        ctx.bilirubin_total = (
            lab_map.get("bilirubin, total")
            or lab_map.get("total bilirubin")
            or lab_map.get("t.bili")
        )
        ctx.bilirubin_direct = (
            lab_map.get("bilirubin, direct")
            or lab_map.get("direct bilirubin")
            or lab_map.get("d.bili")
        )
        ctx.lipase = lab_map.get("lipase")
        ctx.creatinine = lab_map.get("creatinine") or lab_map.get("cr")
        ctx.gfr = lab_map.get("gfr") or lab_map.get("egfr")

        # Allergies
        for allergy in self.allergies:
            allergen_lower = allergy.allergen.lower()
            if "iodinated" in allergen_lower or "contrast" in allergen_lower:
                ctx.has_contrast_allergy = True
                if "iodinated" in allergen_lower:
                    ctx.iodinated_contrast_allergy = True
                if "gadolinium" in allergen_lower:
                    ctx.gadolinium_allergy = True

        if not any(
            [
                ctx.has_contrast_allergy,
                ctx.iodinated_contrast_allergy,
                ctx.gadolinium_allergy,
            ]
        ):
            ctx.has_contrast_allergy = False

        # Medical history
        ctx.medical_history = [c.condition for c in self.medical_history]
        ctx.surgical_history = [s.procedure for s in self.surgical_history]

        # Prior imaging
        for report in self.imaging_reports:
            modality_lower = report.modality.lower()
            if "us" in modality_lower or "ultrasound" in modality_lower:
                ctx.prior_us_performed = True
                impression_lower = report.impression.lower()
                if "negative" in impression_lower or "no evidence" in impression_lower:
                    ctx.prior_us_result = "negative"
                elif (
                    "equivocal" in impression_lower
                    or "inconclusive" in impression_lower
                ):
                    ctx.prior_us_result = "equivocal"
                else:
                    ctx.prior_us_result = "positive"
                ctx.prior_us_findings = report.findings

        # Clinical state (from encounter context)
        for encounter in self.encounters:
            dept_lower = encounter.department.lower()
            if "icu" in dept_lower:
                ctx.is_icu_patient = True
                ctx.is_critically_ill = True

        # Clinical notes
        if self.hpi:
            ctx.clinical_notes = self.hpi

        return ctx

    def to_clinical_data(self):
        """
        Convert to ClinicalData for use with ProtocolGenerator.

        Returns a ClinicalData object populated from this EMR.
        """
        from .data_preprocessing import ClinicalData

        data = ClinicalData()
        data.patient_id = self.patient.mrn
        data.age = f"{self.patient.age} years" if self.patient.age else None
        data.sex = self.patient.sex

        # Chief complaint from first encounter
        if self.encounters:
            data.chief_complaint = self.encounters[0].chief_complaint

        # Clinical history from medical conditions
        if self.medical_history:
            data.clinical_history = ", ".join(
                c.condition for c in self.medical_history
            )

        # Medications
        all_meds = (
            self.medications.home_medications
            + self.medications.inpatient_medications
        )
        if all_meds:
            data.current_medications = ", ".join(
                f"{m.name} {m.dose} {m.route} {m.frequency}" for m in all_meds
            )

        # Allergies
        if self.allergies:
            data.allergies = ", ".join(a.allergen for a in self.allergies)
        else:
            data.allergies = "NKDA"

        # Labs
        lab_parts = []
        for panel in self.lab_results:
            for result in panel.results:
                flag_str = f" ({result.flag})" if result.flag else ""
                lab_parts.append(
                    f"{result.test_name}: {result.value} {result.unit}{flag_str}"
                )
        if lab_parts:
            data.lab_results = ", ".join(lab_parts)

        # Vitals
        if self.vital_signs:
            v = self.vital_signs[-1]
            vitals_parts = []
            if v.temperature_f is not None:
                vitals_parts.append(f"Temp {v.temperature_f}F")
            if v.heart_rate is not None:
                vitals_parts.append(f"HR {v.heart_rate}")
            if v.blood_pressure_systolic is not None:
                vitals_parts.append(
                    f"BP {v.blood_pressure_systolic}/{v.blood_pressure_diastolic}"
                )
            if v.respiratory_rate is not None:
                vitals_parts.append(f"RR {v.respiratory_rate}")
            if v.oxygen_saturation is not None:
                vitals_parts.append(f"SpO2 {v.oxygen_saturation}%")
            if vitals_parts:
                data.vital_signs = ", ".join(vitals_parts)

        # Physical exam
        data.physical_exam = self.physical_exam

        # Clinical question from imaging orders
        if self.imaging_orders:
            data.clinical_question = self.imaging_orders[0].indication

        # Raw text fallback
        data.raw_text = self.hpi
        data.source_format = "synthetic_emr"

        return data


@dataclass
class ClinicalVignette:
    """
    Input: A clinical text vignette describing a patient presentation.

    The vignette is a narrative paragraph describing a clinical scenario,
    always ending with the provider ordering imaging. The system parses this
    to extract structured clinical data and generate a full longitudinal EMR.

    Example:
        ClinicalVignette(
            vignette_text="A 52-year-old woman with a history of obesity, "
            "type 2 diabetes on metformin, hypertension on lisinopril, and "
            "GERD presents to the ED with 2 weeks of intermittent RUQ pain "
            "that occurs 30 minutes after eating. Pain is now constant with "
            "nausea, vomiting, and fever for 24 hours. Vitals: T 101.2F, "
            "HR 98, BP 142/88. Labs: WBC 14.2, AST 85, ALT 92, ALP 165, "
            "T.Bili 1.8, lipase 45. Positive Murphy sign. The ED physician "
            "orders a CT abdomen with IV contrast.",
        )
    """

    vignette_text: str

    # Optional metadata
    case_id: Optional[str] = None
    case_name: Optional[str] = None
    source: Optional[str] = None  # "board_exam", "case_study", "generated"

    # Reproducibility
    seed: Optional[int] = None

    # Optional ground truth for evaluation
    ground_truth_diagnosis: Optional[str] = None
    ground_truth_appropriate_study: Optional[str] = None


@dataclass
class ParsedVignette:
    """Structured data extracted from a ClinicalVignette by the VignetteParser."""

    # Patient demographics
    age: Optional[int] = None
    sex: Optional[str] = None

    # Clinical presentation
    diagnosis: str = ""
    differential_diagnoses: list[str] = field(default_factory=list)
    chief_complaint: str = ""
    symptom_onset: Optional[str] = None
    symptom_character: Optional[str] = None

    # History
    history_conditions: list[str] = field(default_factory=list)
    surgical_history: list[str] = field(default_factory=list)

    # Presentation details
    presenting_symptoms: list[str] = field(default_factory=list)
    pertinent_negatives: list[str] = field(default_factory=list)

    # Physical exam findings from source vignette
    exam_findings: Optional[str] = None

    # Vitals mentioned in vignette
    vitals_mentioned: dict = field(default_factory=dict)

    # Labs mentioned in vignette
    labs_mentioned: dict = field(default_factory=dict)

    # Imaging ordered (extracted from the vignette text)
    ordered_study: str = ""
    imaging_modality: Optional[str] = None
    imaging_body_region: Optional[str] = None
    imaging_contrast: Optional[str] = None

    # Clinical setting and acuity
    clinical_setting: str = "ED"
    acuity: Optional[str] = None

    # Special populations and safety flags
    special_populations: list[str] = field(default_factory=list)
    safety_flags_mentioned: list[str] = field(default_factory=list)

    # Extraction confidence
    extraction_confidence: float = 0.0

    def to_clinical_scenario(self) -> ClinicalScenario:
        """Convert to legacy ClinicalScenario for backward compatibility."""
        history_parts = []
        if self.sex:
            history_parts.append(self.sex.lower())
        history_parts.extend(self.history_conditions)

        return ClinicalScenario(
            diagnosis=self.diagnosis,
            history_summary=", ".join(history_parts),
            ordered_study=self.ordered_study,
            protocol_indication=self.chief_complaint,
            age_hint=self.age,
            sex_hint=self.sex,
        )


@dataclass
class ClinicalNote:
    """A clinical note from any encounter type."""

    note_type: str = ""  # "Office Visit", "ED Note", "Discharge Summary",
    # "Progress Note", "Consultation", "Nursing Note"
    encounter_id: str = ""
    timestamp: str = ""
    author: str = ""
    note_text: str = ""


@dataclass
class ProblemListEntry:
    """An entry on the problem list with temporal tracking."""

    condition: str = ""
    icd10: Optional[str] = None
    date_added: str = ""  # ISO format
    date_resolved: Optional[str] = None
    status: str = "Active"  # "Active", "Resolved", "Chronic", "Inactive"
    added_encounter_id: str = ""


@dataclass
class MedicationChange:
    """Tracks a medication change event."""

    medication: Medication = field(default_factory=Medication)
    change_type: str = ""  # "Started", "Increased", "Decreased", "Discontinued"
    change_date: str = ""
    encounter_id: str = ""
    reason: Optional[str] = None
    previous_dose: Optional[str] = None


@dataclass
class EncounterRecord:
    """
    A complete encounter with all associated data.

    Bundles an encounter with its own vitals, labs, notes, orders, and reports,
    making each encounter self-contained within the longitudinal record.
    """

    encounter: Encounter = field(default_factory=Encounter)
    vital_signs: list[VitalSignSet] = field(default_factory=list)
    lab_results: list[LabPanel] = field(default_factory=list)
    imaging_orders: list[ImagingOrder] = field(default_factory=list)
    imaging_reports: list[ImagingReport] = field(default_factory=list)
    clinical_notes: list[ClinicalNote] = field(default_factory=list)
    diagnoses: list[str] = field(default_factory=list)


@dataclass
class LongitudinalEMR:
    """
    Complete synthetic electronic medical record with longitudinal history.

    Represents a full patient chart spanning multiple years of encounters,
    labs, medications, and notes. The last entry in encounter_history is
    the current/presenting encounter.
    """

    # Patient identity
    patient: PatientDemographics = field(default_factory=PatientDemographics)

    # Longitudinal timeline (chronological, last = current)
    encounter_history: list[EncounterRecord] = field(default_factory=list)

    # Problem list (evolves over time)
    problem_list: list[ProblemListEntry] = field(default_factory=list)

    # Medication timeline
    medication_history: list[MedicationChange] = field(default_factory=list)
    current_medications: MedicationList = field(default_factory=MedicationList)

    # Static patient data
    allergies: list[Allergy] = field(default_factory=list)
    surgical_history: list[SurgicalProcedure] = field(default_factory=list)
    family_history: list[str] = field(default_factory=list)
    social_history: SocialHistory = field(default_factory=SocialHistory)

    # Source and metadata
    source_vignette: Optional[ClinicalVignette] = None
    parsed_vignette: Optional[ParsedVignette] = None
    source_scenario: Optional[ClinicalScenario] = None
    generation_metadata: GenerationMetadata = field(
        default_factory=GenerationMetadata
    )

    @property
    def current_encounter(self) -> Optional[EncounterRecord]:
        """The presenting/current encounter (latest in timeline)."""
        return self.encounter_history[-1] if self.encounter_history else None

    @property
    def prior_encounters(self) -> list[EncounterRecord]:
        """All encounters before the current one."""
        return self.encounter_history[:-1] if len(self.encounter_history) > 1 else []

    def to_dict(self) -> dict:
        """Convert entire longitudinal EMR to a JSON-serializable dictionary."""
        return _dataclass_to_dict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_patient_context(self):
        """
        Convert to PatientContext for use with RUQProtocolReviewer.

        Uses the CURRENT encounter's labs/vitals but scans ALL prior
        encounters for prior imaging results, which is critical for
        ACR variant classification (Variant 1/2 vs 3/4/5).
        """
        from .ruq_models import PatientContext

        ctx = PatientContext()
        ctx.patient_id = self.patient.mrn
        ctx.age = self.patient.age
        ctx.sex = self.patient.sex

        current = self.current_encounter
        if not current:
            return ctx

        # Current encounter vitals
        if current.vital_signs:
            latest = current.vital_signs[-1]
            ctx.temperature = latest.temperature_f
            if latest.temperature_f is not None:
                ctx.has_fever = latest.temperature_f > 100.4
            ctx.heart_rate = latest.heart_rate
            ctx.blood_pressure_systolic = latest.blood_pressure_systolic
            ctx.blood_pressure_diastolic = latest.blood_pressure_diastolic

        # Current encounter labs
        lab_map = {}
        for panel in current.lab_results:
            for result in panel.results:
                lab_map[result.test_name.lower()] = result.value

        ctx.wbc = lab_map.get("wbc")
        if ctx.wbc is not None:
            ctx.wbc_elevated = ctx.wbc > 11.0
        ctx.ast = lab_map.get("ast")
        ctx.alt = lab_map.get("alt")
        ctx.alp = lab_map.get("alp") or lab_map.get("alkaline phosphatase")
        ctx.bilirubin_total = (
            lab_map.get("bilirubin, total")
            or lab_map.get("total bilirubin")
            or lab_map.get("t.bili")
        )
        ctx.bilirubin_direct = (
            lab_map.get("bilirubin, direct")
            or lab_map.get("direct bilirubin")
            or lab_map.get("d.bili")
        )
        ctx.lipase = lab_map.get("lipase")
        ctx.creatinine = lab_map.get("creatinine") or lab_map.get("cr")
        ctx.gfr = lab_map.get("gfr") or lab_map.get("egfr")

        # Allergies
        for allergy in self.allergies:
            allergen_lower = allergy.allergen.lower()
            if "iodinated" in allergen_lower or "contrast" in allergen_lower:
                ctx.has_contrast_allergy = True
                if "iodinated" in allergen_lower:
                    ctx.iodinated_contrast_allergy = True
                if "gadolinium" in allergen_lower:
                    ctx.gadolinium_allergy = True
        if not any(
            [ctx.has_contrast_allergy, ctx.iodinated_contrast_allergy,
             ctx.gadolinium_allergy]
        ):
            ctx.has_contrast_allergy = False

        # Medical history from problem list
        ctx.medical_history = [
            entry.condition for entry in self.problem_list
            if entry.status in ("Active", "Chronic")
        ]
        ctx.surgical_history = [s.procedure for s in self.surgical_history]

        # LONGITUDINAL: scan ALL encounters for prior imaging
        for prior_record in self.prior_encounters:
            for report in prior_record.imaging_reports:
                modality_lower = report.modality.lower()
                if "us" in modality_lower or "ultrasound" in modality_lower:
                    ctx.prior_us_performed = True
                    impression_lower = report.impression.lower()
                    if "negative" in impression_lower or "no evidence" in impression_lower:
                        ctx.prior_us_result = "negative"
                    elif "equivocal" in impression_lower or "inconclusive" in impression_lower:
                        ctx.prior_us_result = "equivocal"
                    else:
                        ctx.prior_us_result = "positive"
                    ctx.prior_us_findings = report.findings

        # Clinical state from current encounter
        dept_lower = current.encounter.department.lower()
        if "icu" in dept_lower:
            ctx.is_icu_patient = True
            ctx.is_critically_ill = True

        # Clinical notes from current encounter
        for note in current.clinical_notes:
            if note.note_type in ("ED Note", "HPI"):
                ctx.clinical_notes = note.note_text
                break

        return ctx

    def to_synthetic_emr(self) -> SyntheticEMR:
        """
        Flatten to legacy SyntheticEMR for backward compatibility.

        Combines all encounters into the flat SyntheticEMR format.
        """
        emr = SyntheticEMR()
        emr.patient = self.patient

        # Flatten encounters
        for record in self.encounter_history:
            emr.encounters.append(record.encounter)
            emr.vital_signs.extend(record.vital_signs)
            emr.lab_results.extend(record.lab_results)
            emr.imaging_orders.extend(record.imaging_orders)
            emr.imaging_reports.extend(record.imaging_reports)
            for note in record.clinical_notes:
                if note.note_type == "Nursing Note":
                    emr.nursing_notes.append(
                        NursingNote(
                            timestamp=note.timestamp,
                            author=note.author,
                            note_text=note.note_text,
                        )
                    )

        emr.medications = self.current_medications
        emr.allergies = self.allergies
        emr.medical_history = [
            MedicalCondition(
                condition=p.condition, icd10=p.icd10, status=p.status
            )
            for p in self.problem_list
        ]
        emr.surgical_history = self.surgical_history
        emr.family_history = self.family_history
        emr.social_history = self.social_history

        # Current encounter narratives
        current = self.current_encounter
        if current:
            for note in current.clinical_notes:
                if note.note_type == "HPI":
                    emr.hpi = note.note_text
                elif note.note_type == "Physical Exam":
                    emr.physical_exam = note.note_text
                elif note.note_type == "Assessment & Plan":
                    emr.assessment_and_plan = note.note_text
                elif note.note_type == "Discharge Summary":
                    emr.discharge_summary = note.note_text

        emr.source_scenario = self.source_scenario
        emr.generation_metadata = self.generation_metadata

        return emr


def _dataclass_to_dict(obj) -> dict | list | str | int | float | bool | None:
    """Recursively convert dataclasses to dicts."""
    if isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            result[field_name] = _dataclass_to_dict(value)
        return result
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
