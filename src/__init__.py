"""
MedGemma Protocol Generator — Synthetic EMR Generation & Radiology Triage.

This package provides:
1. Longitudinal synthetic EMR generation from clinical vignettes
2. Clinical knowledge bases (lab ranges, vital ranges, condition progressions)
3. Narrative generation via MedGemma backend
"""

# EMR data models
from .emr_models import (
    ClinicalVignette,
    ParsedVignette,
    ClinicalNote,
    ProblemListEntry,
    MedicationChange,
    EncounterRecord,
    LongitudinalEMR,
    ClinicalScenario,
    SyntheticEMR,
    PatientDemographics,
    Encounter,
    VitalSignSet,
    LabPanel,
    LabResult,
    MedicationList,
    Medication,
    Allergy,
    MedicalCondition,
    SurgicalProcedure,
    SocialHistory,
    ImagingOrder,
    ImagingReport,
    NursingNote,
    GenerationMetadata,
)

# Narrative generation
from .emr_narrative import (
    NarrativeBackend,
    MedGemmaBackend,
)

# Vignette parsing
from .vignette_parser import VignetteParser

# Longitudinal EMR generator
from .longitudinal_generator import LongitudinalEMRGenerator

__all__ = [
    # EMR Models
    "ClinicalVignette",
    "ParsedVignette",
    "ClinicalNote",
    "ProblemListEntry",
    "MedicationChange",
    "EncounterRecord",
    "LongitudinalEMR",
    "ClinicalScenario",
    "SyntheticEMR",
    "PatientDemographics",
    "Encounter",
    "VitalSignSet",
    "LabPanel",
    "LabResult",
    "MedicationList",
    "Medication",
    "Allergy",
    "MedicalCondition",
    "SurgicalProcedure",
    "SocialHistory",
    "ImagingOrder",
    "ImagingReport",
    "NursingNote",
    "GenerationMetadata",
    # Narrative
    "NarrativeBackend",
    "MedGemmaBackend",
    # Parsing
    "VignetteParser",
    # Generator
    "LongitudinalEMRGenerator",
]
