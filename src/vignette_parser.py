"""
Clinical Vignette Parser.

Parses free-text clinical vignettes into structured ParsedVignette objects.
Uses MedGemma for LLM-based extraction.
"""

import re
from typing import Optional

from .emr_models import ClinicalVignette, ParsedVignette
from .emr_narrative import NarrativeBackend


class VignetteParser:
    """
    Parses clinical text vignettes into structured ParsedVignette objects.

    Uses a MedGemma LLM backend for extraction.

    Example:
        parser = VignetteParser(backend=medgemma_backend)
        vignette = ClinicalVignette(vignette_text="A 52-year-old woman...")
        parsed = parser.parse(vignette)
        print(parsed.age, parsed.diagnosis, parsed.ordered_study)
    """

    def __init__(self, narrative_backend: Optional[NarrativeBackend] = None):
        if narrative_backend is None:
            raise ValueError("A narrative backend (e.g., MedGemmaBackend) is required.")
        self.backend = narrative_backend

    def parse(self, vignette: ClinicalVignette) -> ParsedVignette:
        """
        Parse a clinical vignette into structured data.

        Args:
            vignette: ClinicalVignette with vignette_text

        Returns:
            ParsedVignette with extracted structured data
        """
        # Step 1: Extract structured data via LLM or regex
        raw = self.backend.generate_vignette_extraction(vignette.vignette_text)

        # Step 2: Build ParsedVignette from raw extraction
        parsed = ParsedVignette()

        # Demographics
        parsed.age = raw.get("age")
        parsed.sex = raw.get("sex")

        # Clinical presentation
        parsed.diagnosis = raw.get("diagnosis", "")
        parsed.differential_diagnoses = raw.get("differential_diagnoses", [])
        parsed.chief_complaint = raw.get("chief_complaint", "")
        parsed.symptom_onset = raw.get("symptom_onset")
        parsed.symptom_character = raw.get("symptom_character")

        # History
        parsed.history_conditions = raw.get("history_conditions", [])
        parsed.surgical_history = raw.get("surgical_history", [])

        # Symptoms
        parsed.presenting_symptoms = raw.get("presenting_symptoms", [])
        parsed.pertinent_negatives = raw.get("pertinent_negatives", [])

        # Vitals mentioned
        vitals = raw.get("vitals", {})
        if isinstance(vitals, dict):
            parsed.vitals_mentioned = _normalize_vitals(vitals)

        # Labs mentioned
        labs = raw.get("labs", {})
        if isinstance(labs, dict):
            parsed.labs_mentioned = _normalize_labs(labs)

        # Imaging ordered
        parsed.ordered_study = raw.get("ordered_study", "")
        if parsed.ordered_study:
            parsed.imaging_modality = _extract_modality(parsed.ordered_study)
            parsed.imaging_body_region = _extract_body_region(parsed.ordered_study)
            parsed.imaging_contrast = _extract_contrast(parsed.ordered_study)

        # Clinical setting and acuity
        parsed.clinical_setting = raw.get("clinical_setting", "ED")
        parsed.acuity = raw.get("acuity")

        # Special populations and safety flags
        parsed.special_populations = raw.get("special_populations", [])
        parsed.safety_flags_mentioned = raw.get("safety_flags", [])

        # Step 3: Apply overrides from the vignette metadata
        if vignette.seed is not None:
            pass  # seed handled by generator

        # Step 4: Confidence
        filled_fields = sum([
            parsed.age is not None,
            parsed.sex is not None,
            bool(parsed.diagnosis),
            bool(parsed.ordered_study),
            bool(parsed.chief_complaint),
            len(parsed.vitals_mentioned) > 0,
            len(parsed.labs_mentioned) > 0,
        ])
        parsed.extraction_confidence = min(1.0, filled_fields / 7.0)

        return parsed


# =============================================================================
# HELPERS
# =============================================================================

def _normalize_vitals(vitals: dict) -> dict:
    """Normalize vital sign keys and values."""
    normalized = {}
    key_map = {
        "temperature_f": "temperature_f", "temp": "temperature_f",
        "temperature": "temperature_f", "t": "temperature_f",
        "heart_rate": "heart_rate", "hr": "heart_rate", "pulse": "heart_rate",
        "blood_pressure_systolic": "blood_pressure_systolic",
        "bp_systolic": "blood_pressure_systolic", "sbp": "blood_pressure_systolic",
        "blood_pressure_diastolic": "blood_pressure_diastolic",
        "bp_diastolic": "blood_pressure_diastolic", "dbp": "blood_pressure_diastolic",
        "respiratory_rate": "respiratory_rate", "rr": "respiratory_rate",
        "oxygen_saturation": "oxygen_saturation", "spo2": "oxygen_saturation",
        "o2_sat": "oxygen_saturation",
        "pain_scale": "pain_scale", "pain": "pain_scale",
    }
    for key, value in vitals.items():
        normalized_key = key_map.get(key.lower(), key.lower())
        try:
            normalized[normalized_key] = float(value) if value is not None else None
        except (ValueError, TypeError):
            pass
    return normalized


def _normalize_labs(labs: dict) -> dict:
    """Normalize lab test keys and values."""
    normalized = {}
    key_map = {
        "wbc": "wbc", "white blood cell": "wbc", "white count": "wbc",
        "hemoglobin": "hemoglobin", "hgb": "hemoglobin", "hb": "hemoglobin",
        "hematocrit": "hematocrit", "hct": "hematocrit",
        "platelets": "platelets", "plt": "platelets",
        "sodium": "sodium", "na": "sodium",
        "potassium": "potassium", "k": "potassium",
        "chloride": "chloride", "cl": "chloride",
        "co2": "co2", "bicarb": "co2", "bicarbonate": "co2",
        "bun": "bun",
        "creatinine": "creatinine", "cr": "creatinine",
        "glucose": "glucose", "glu": "glucose",
        "calcium": "calcium", "ca": "calcium",
        "ast": "ast", "sgot": "ast",
        "alt": "alt", "sgpt": "alt",
        "alp": "alp", "alkaline_phosphatase": "alp", "alk_phos": "alp",
        "bilirubin_total": "bilirubin_total", "t_bili": "bilirubin_total",
        "total_bilirubin": "bilirubin_total", "tbili": "bilirubin_total",
        "bilirubin_direct": "bilirubin_direct", "d_bili": "bilirubin_direct",
        "direct_bilirubin": "bilirubin_direct",
        "lipase": "lipase",
        "albumin": "albumin", "alb": "albumin",
        "inr": "inr",
        "lactate": "lactate",
        "troponin_i": "troponin_i", "troponin": "troponin_i", "trop": "troponin_i",
        "bnp": "bnp",
        "d_dimer": "d_dimer", "d-dimer": "d_dimer",
        "hba1c": "hba1c", "a1c": "hba1c",
        "tsh": "tsh",
        "gfr": "gfr", "egfr": "gfr",
    }
    for key, value in labs.items():
        normalized_key = key_map.get(key.lower().replace(" ", "_"), key.lower())
        try:
            if value is not None:
                normalized[normalized_key] = float(value)
        except (ValueError, TypeError):
            pass
    return normalized


def _extract_modality(ordered_study: str) -> str:
    """Extract imaging modality from study description."""
    lower = ordered_study.lower()
    if "ercp" in lower:
        return "ERCP"
    if "pet" in lower:
        return "PET/CT"
    if "laparoscop" in lower:
        return "Diagnostic Laparoscopy"
    if "ct" in lower:
        return "CT"
    if "mri" in lower or "mr " in lower or "mrcp" in lower:
        return "MRI"
    if "eus" in lower or "endoscopic" in lower:
        return "EUS"
    if "us" in lower or "ultrasound" in lower or "sono" in lower:
        return "Ultrasound"
    if "x-ray" in lower or "xray" in lower or "cxr" in lower or "radiograph" in lower:
        return "X-ray"
    if "hida" in lower or "hepatobiliary" in lower:
        return "Nuclear Medicine (HIDA)"
    return ordered_study.split()[0] if ordered_study else "Imaging"


def _extract_body_region(ordered_study: str) -> str:
    """Extract body region from study description."""
    lower = ordered_study.lower()
    if "abdomen" in lower and "pelvis" in lower:
        return "Abdomen and Pelvis"
    if "abdomen" in lower:
        return "Abdomen"
    if "chest" in lower or "cxr" in lower:
        return "Chest"
    if "head" in lower or "brain" in lower:
        return "Head"
    if "spine" in lower:
        return "Spine"
    return "Abdomen"


def _extract_contrast(ordered_study: str) -> str:
    """Extract contrast type from study description."""
    lower = ordered_study.lower()
    if "without and with" in lower or "w/o and w/" in lower:
        return "without and with IV contrast"
    if "with contrast" in lower or "w/ contrast" in lower or "w/contrast" in lower:
        return "with IV contrast"
    if "without contrast" in lower or "w/o contrast" in lower:
        return "without contrast"
    if "pe protocol" in lower:
        return "with IV contrast"
    return ""
