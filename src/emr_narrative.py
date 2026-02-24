"""
Narrative generation backends for Synthetic EMR Generation.

Provides LLM-based narrative generation:
- MedGemmaBackend: Uses the MedGemma model for clinical narrative generation

The backend can:
1. Generate diagnosis-specific clinical data (labs, vitals, meds, conditions)
2. Generate narrative sections (HPI, PE, A&P, nursing notes, office visit notes)
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Optional


class NarrativeBackend(ABC):
    """Abstract base class for narrative text generation."""

    @abstractmethod
    def generate_clinical_data(self, scenario_context: dict) -> dict:
        """
        Ask the LLM to generate diagnosis-appropriate clinical data.

        Args:
            scenario_context: Dict with diagnosis, demographics, history, indication

        Returns:
            Dict with keys: labs, vitals, medications, conditions, acuity,
                           physical_exam_findings, family_history, social_history
        """
        ...

    @abstractmethod
    def generate_hpi(self, context: dict) -> str:
        """Generate History of Present Illness narrative."""
        ...

    @abstractmethod
    def generate_physical_exam(self, context: dict) -> str:
        """Generate Physical Examination narrative."""
        ...

    @abstractmethod
    def generate_assessment_plan(self, context: dict) -> str:
        """Generate Assessment & Plan narrative."""
        ...

    @abstractmethod
    def generate_radiology_report(self, context: dict) -> str:
        """Generate radiology report narrative (findings + impression)."""
        ...

    @abstractmethod
    def generate_nursing_notes(self, context: dict) -> list[str]:
        """Generate nursing progress notes."""
        ...

    @abstractmethod
    def generate_discharge_summary(self, context: dict) -> str:
        """Generate discharge summary narrative."""
        ...

    @abstractmethod
    def generate_vignette_extraction(self, vignette_text: str) -> dict:
        """Extract structured clinical data from a free-text vignette."""
        ...

    @abstractmethod
    def generate_office_visit_note(self, context: dict) -> str:
        """Generate a brief outpatient office visit note."""
        ...

    @abstractmethod
    def generate_consultation_note(self, context: dict) -> str:
        """Generate a specialist consultation note."""
        ...


# =============================================================================
# PROMPTS
# =============================================================================

CLINICAL_DATA_PROMPT = """You are a clinical data generation system for creating realistic synthetic electronic medical records. Given a clinical scenario, generate diagnosis-appropriate structured clinical data.

SCENARIO:
- Diagnosis: {diagnosis}
- Patient: {age}-year-old {sex}
- History: {history_summary}
- Clinical Indication: {protocol_indication}

Generate realistic clinical data as a JSON object. All lab values must be specific numbers (not ranges). Values should be clinically consistent with the diagnosis.

{{
    "acuity": "<stable|mild|febrile|septic|shock>",
    "vitals": {{
        "temperature_f": <float>,
        "heart_rate": <int>,
        "blood_pressure_systolic": <int>,
        "blood_pressure_diastolic": <int>,
        "respiratory_rate": <int>,
        "oxygen_saturation": <float>,
        "pain_scale": <int 0-10>
    }},
    "labs": {{
        "wbc": <float>,
        "hemoglobin": <float>,
        "hematocrit": <float>,
        "platelets": <float>,
        "sodium": <float>,
        "potassium": <float>,
        "chloride": <float>,
        "co2": <float>,
        "bun": <float>,
        "creatinine": <float>,
        "glucose": <float>,
        "calcium": <float>,
        "ast": <float>,
        "alt": <float>,
        "alp": <float>,
        "bilirubin_total": <float>,
        "bilirubin_direct": <float>,
        "lipase": <float>,
        "albumin": <float>,
        "inr": <float>,
        "lactate": <float or null if not indicated>
    }},
    "inpatient_medications": [
        {{"name": "<drug>", "dose": "<dose>", "route": "<PO|IV|IM|SubQ>", "frequency": "<frequency>", "indication": "<reason>"}}
    ],
    "additional_conditions": [
        {{"condition": "<condition name>", "icd10": "<code>"}}
    ],
    "allergies": [
        {{"allergen": "<allergen>", "allergy_type": "<Drug|Food|Environmental>", "reaction": "<reaction>", "severity": "<Mild|Moderate|Severe>"}}
    ],
    "physical_exam_findings": "<key physical exam findings relevant to the diagnosis>",
    "family_history": ["<relevant family history items>"],
    "social_history": {{
        "smoking_status": "<Never|Former|Current>",
        "alcohol_use": "<None|Social|Daily|Heavy>",
        "occupation": "<occupation>",
        "living_situation": "<living situation>"
    }}
}}

RULES:
- Lab values must be specific numbers appropriate for the diagnosis
- Vitals must reflect the clinical acuity of the diagnosis
- Include only medications appropriate for acute management of this diagnosis
- Allergies should be realistic (most patients have NKDA - return empty list for no allergies)
- Physical exam findings should be specific to the diagnosis
- Output ONLY the JSON object"""

HPI_PROMPT = """You are a physician writing a History of Present Illness (HPI) for a clinical note. Write a realistic, detailed HPI based on the following structured data.

Patient: {age}-year-old {sex}
Chief Complaint: {chief_complaint}
Working Diagnosis: {diagnosis}
Clinical Indication: {protocol_indication}
Medical History: {medical_history}
Current Medications: {medications}
Vitals: Temp {temperature}F, HR {heart_rate}, BP {bp}, RR {respiratory_rate}, SpO2 {spo2}%
Key Labs: {labs_summary}

Write 2-3 paragraphs in standard clinical documentation style. Include:
- Onset, duration, character, location, radiation, severity of symptoms
- Associated symptoms (nausea, vomiting, fever, etc.)
- Pertinent negatives
- What prompted the visit today
- Relevant review of systems

Use the Working Diagnosis as provided — do not substitute a more specific diagnosis. Use clinical language. Be specific with timeframes. Do not include information not derivable from the data above. Do not include a header/title."""

PHYSICAL_EXAM_PROMPT = """You are a physician writing a Physical Examination section for a clinical note. Write a realistic, detailed physical exam based on the following data.

Patient: {age}-year-old {sex}
Working Diagnosis: {diagnosis}
Vitals: Temp {temperature}F, HR {heart_rate}, BP {bp}, RR {respiratory_rate}, SpO2 {spo2}%
Key Exam Findings: {physical_exam_findings}
Medical History: {medical_history}
Current Medications: {medications}

Write a standard physical exam note with these sections:
- GENERAL
- HEENT
- CARDIOVASCULAR
- PULMONARY
- ABDOMEN
- EXTREMITIES
- NEUROLOGICAL

Make findings consistent with the clinical presentation. Include pertinent positives and negatives. Use standard abbreviations. Do not include a header/title - start directly with GENERAL.

IMPORTANT: The physical exam must be consistent with the provided vitals and medical history.
- If temperature is >100.4F, do NOT describe the patient as "afebrile"
- Reference the patient's documented medical history and medications accurately
- Do NOT state "no significant medical history" or "no medications" unless that is true per the data above"""

ASSESSMENT_PLAN_PROMPT = """You are a physician writing the Assessment and Plan section for a clinical note.

Patient: {age}-year-old {sex}
Working Diagnosis: {diagnosis}
Medical History: {medical_history}
Key Labs: {labs_summary}
Key Vitals: Temp {temperature}F, HR {heart_rate}
Imaging Ordered: {imaging_ordered}
Clinical Indication: {protocol_indication}

Write a structured Assessment and Plan. Format as:

ASSESSMENT:
Brief clinical assessment summarizing the presentation and key findings.

PLAN:
1. [Working diagnosis / chief complaint] - workup and management steps
2. [Secondary issues] - management
3. Disposition plan

IMPORTANT: Use the Working Diagnosis exactly as provided above. Do NOT substitute a more specific diagnosis. If the working diagnosis is symptom-based (e.g., "RUQ pain, etiology under evaluation"), present the case as an active workup — list broad differentials without committing to a single etiology. The imaging study has been ordered as part of the diagnostic workup.

Use clinical language. Be specific about medications, doses, and monitoring. Do not include a header/title - start directly with ASSESSMENT."""

RADIOLOGY_REPORT_PROMPT = """You are a radiologist writing a report for an imaging study.

Study: {modality} {body_region} {contrast}
Patient: {age}-year-old {sex}
Clinical Indication: {indication}
Diagnosis: {diagnosis}

Write a radiology report with:

TECHNIQUE:
Brief description of the technique used.

FINDINGS:
Detailed findings organized by organ system. Include measurements where appropriate. Findings should be consistent with the diagnosis.

IMPRESSION:
Numbered impression items summarizing key findings.

Use standard radiology reporting language. Do not include a title - start directly with TECHNIQUE."""

NURSING_NOTE_PROMPT = """You are a nurse writing a brief progress note for a patient.

Patient: {age}-year-old {sex}
Working Diagnosis: {diagnosis}
Current Vitals: Temp {temperature}F, HR {heart_rate}, BP {bp}, RR {respiratory_rate}, SpO2 {spo2}%, Pain {pain}/10
Time: {time_description}

Write a brief (3-5 sentences) nursing assessment note. Include:
- Patient status and comfort level
- Vital signs trend
- Interventions performed
- Any concerns or changes

Use the Working Diagnosis as provided — do not substitute a more specific diagnosis. Use nursing documentation style. Be concise. Do not include a header."""

DISCHARGE_SUMMARY_PROMPT = """You are a physician writing a discharge summary.

Patient: {age}-year-old {sex}
Admission Diagnosis: {diagnosis}
Medical History: {medical_history}
Hospital Course Summary: Patient was admitted for {diagnosis}. {clinical_summary}
Discharge Medications: {discharge_meds}
Follow-up: {follow_up}

Write a concise discharge summary including:
- Brief hospital course
- Discharge condition
- Discharge instructions
- Follow-up appointments
- Medications at discharge
- Return precautions

Use clinical documentation style. Do not include a title - start directly with the content."""


VIGNETTE_EXTRACTION_PROMPT = """You are a clinical data extraction system. Given a clinical vignette, extract structured data as JSON.

VIGNETTE:
{vignette_text}

Extract the following as JSON:
{{
    "age": <int or null>,
    "sex": "<Male|Female|null>",
    "diagnosis": "<primary diagnosis or suspected diagnosis>",
    "differential_diagnoses": ["<list of differential diagnoses if mentioned>"],
    "chief_complaint": "<main presenting complaint>",
    "symptom_onset": "<duration string, e.g. '2 weeks', '24 hours'>",
    "history_conditions": ["<list of PMH conditions mentioned>"],
    "surgical_history": ["<list of prior surgeries if mentioned>"],
    "presenting_symptoms": ["<list of symptoms>"],
    "pertinent_negatives": ["<list of pertinent negatives if mentioned>"],
    "vitals": {{<key: value pairs for any vitals mentioned, use keys: temperature_f, heart_rate, blood_pressure_systolic, blood_pressure_diastolic, respiratory_rate, oxygen_saturation>}},
    "labs": {{<key: value pairs for any labs mentioned, use keys: wbc, ast, alt, alp, bilirubin_total, lipase, creatinine, glucose, troponin_i, d_dimer, etc.>}},
    "ordered_study": "<exact imaging study ordered, e.g. 'CT abdomen with IV contrast'>",
    "clinical_setting": "<ED|outpatient|inpatient|ICU>",
    "acuity": "<stable|mild|febrile|septic|shock>",
    "special_populations": ["<e.g. 'pregnant', 'pediatric', 'immunocompromised'>"],
    "safety_flags": ["<e.g. 'CKD with GFR < 30', 'elevated troponins', 'on metformin', 'contrast allergy'>"]
}}

RULES:
- Extract ONLY information explicitly stated in the vignette
- Do NOT infer or assume values not mentioned
- The ordered_study MUST be the imaging study the provider orders (look for 'orders', 'ordered', etc.)
- For safety_flags, flag: CKD/renal issues, pregnancy, contrast allergies, metformin use, elevated cardiac markers
- Output ONLY the JSON object"""

OFFICE_VISIT_NOTE_PROMPT = """Write a complete outpatient office visit note in standard SOAP format.

Patient: {age}-year-old {sex}
Visit Reason: {reason}
Medical History: {medical_history}
Current Medications: {medications}
Vitals: BP {bp}, HR {heart_rate}
Relevant Labs: {labs_summary}
Clinical Context: {assessment}

Write a full clinical note with these sections:
SUBJECTIVE: Chief complaint, history of present illness, review of systems (2-4 sentences).
OBJECTIVE: Vitals, physical exam findings relevant to the visit reason (2-3 sentences).
ASSESSMENT: Clinical assessment with diagnoses and clinical reasoning (2-3 sentences).
PLAN: Medication changes, follow-up instructions, referrals, patient education (2-4 sentences).

Use professional clinical documentation style with standard medical abbreviations. Include specific clinical details."""

CONSULTATION_NOTE_PROMPT = """Write a complete specialist consultation note.

Patient: {age}-year-old {sex}
Referring Provider: {referring_provider}
Reason for Consultation: {reason}
Medical History: {medical_history}
Current Medications: {medications}
Clinical Context: {assessment}

Write a full consultation note with these sections:
REASON FOR CONSULTATION: The clinical question from the referring provider (1-2 sentences).
HISTORY OF PRESENT ILLNESS: Relevant history pertaining to the consultation (2-4 sentences).
EXAMINATION: Focused physical exam findings relevant to the specialty (2-3 sentences).
ASSESSMENT: Clinical impression with differential diagnosis or confirmed diagnosis (2-3 sentences).
RECOMMENDATIONS: Specific management recommendations, medication changes, follow-up plan, and communication back to referring provider (2-4 sentences).

Use professional clinical documentation style with standard medical abbreviations. Include specific clinical details."""

PRIOR_IMAGING_REPORT_PROMPT = """Write a radiology report for a prior imaging study.

Study: {modality} {body_region} {contrast}
Patient: {age}-year-old {sex}
Clinical Indication: {indication}
Expected Findings: {expected_findings}

Write a brief report with TECHNIQUE, FINDINGS, and IMPRESSION sections. The findings should be consistent with the expected findings. Start with TECHNIQUE."""

LONGITUDINAL_HPI_PROMPT = """You are a physician writing a History of Present Illness (HPI). This patient has a longitudinal history at this facility.

Patient: {age}-year-old {sex}
Chief Complaint: {chief_complaint}
Diagnosis: {diagnosis}
Clinical Indication: {protocol_indication}
Medical History: {medical_history}
Current Medications: {medications}
Vitals: Temp {temperature}F, HR {heart_rate}, BP {bp}, RR {respiratory_rate}, SpO2 {spo2}%
Key Labs: {labs_summary}

Prior Visit Summary:
{prior_visit_summary}

Write 2-3 paragraphs in standard clinical documentation style. Reference the patient's prior visits and history at this facility where relevant (e.g., "Patient with known cholelithiasis diagnosed on ultrasound 2 years ago..."). Include onset, duration, associated symptoms, pertinent negatives. Do not include a header."""


class MedGemmaBackend(NarrativeBackend):
    """
    Uses the existing MedGemma model for clinical narrative generation.

    Replicates the inference pattern from EMRExtractor in notebook 03.
    """

    def __init__(self, model, processor):
        self.model = model
        self.processor = processor
        self.name = "medgemma"

    def _run_inference(self, prompt: str, max_tokens: int = 800) -> str:
        """Run MedGemma inference using the standard pattern."""
        import torch

        messages = [
            {"role": "user", "content": prompt}
        ]

        inputs = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)

        input_len = inputs["input_ids"].shape[-1]

        with torch.inference_mode():
            generation = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
            )
            output_tokens = generation[0][input_len:]

        return self.processor.decode(output_tokens, skip_special_tokens=True)

    def generate_clinical_data(self, scenario_context: dict) -> dict:
        prompt = CLINICAL_DATA_PROMPT.format(**scenario_context)
        response = self._run_inference(prompt, max_tokens=1200)
        return _parse_json_response(response)

    def generate_hpi(self, context: dict) -> str:
        prompt = HPI_PROMPT.format(**context)
        return _trim_to_last_sentence(self._run_inference(prompt, max_tokens=600).strip())

    def generate_physical_exam(self, context: dict) -> str:
        prompt = PHYSICAL_EXAM_PROMPT.format(**context)
        return _trim_to_last_sentence(self._run_inference(prompt, max_tokens=600).strip())

    def generate_assessment_plan(self, context: dict) -> str:
        prompt = ASSESSMENT_PLAN_PROMPT.format(**context)
        return _trim_to_last_sentence(self._run_inference(prompt, max_tokens=600).strip())

    def generate_radiology_report(self, context: dict) -> str:
        prompt = RADIOLOGY_REPORT_PROMPT.format(**context)
        return self._run_inference(prompt, max_tokens=800).strip()

    def generate_nursing_notes(self, context: dict) -> list[str]:
        prompt = NURSING_NOTE_PROMPT.format(**context)
        note = self._run_inference(prompt, max_tokens=200).strip()
        return [note]

    def generate_discharge_summary(self, context: dict) -> str:
        prompt = DISCHARGE_SUMMARY_PROMPT.format(**context)
        return self._run_inference(prompt, max_tokens=800).strip()

    def generate_vignette_extraction(self, vignette_text: str) -> dict:
        prompt = VIGNETTE_EXTRACTION_PROMPT.format(vignette_text=vignette_text)
        response = self._run_inference(prompt, max_tokens=1200)
        return _parse_json_response(response)

    def generate_office_visit_note(self, context: dict) -> str:
        prompt = OFFICE_VISIT_NOTE_PROMPT.format(**context)
        return self._run_inference(prompt, max_tokens=600).strip()

    def generate_consultation_note(self, context: dict) -> str:
        prompt = CONSULTATION_NOTE_PROMPT.format(**context)
        return self._run_inference(prompt, max_tokens=600).strip()




# =============================================================================
# HELPERS
# =============================================================================


def _trim_to_last_sentence(text: str) -> str:
    """Trim text to the last complete sentence.

    When LLM output hits the max_new_tokens limit, it may be cut off
    mid-sentence. This trims to the last sentence-ending punctuation.
    """
    if not text:
        return text
    stripped = text.rstrip()
    if stripped and stripped[-1] in '.!?':
        return text
    last_period = text.rfind('.')
    last_excl = text.rfind('!')
    last_quest = text.rfind('?')
    last_boundary = max(last_period, last_excl, last_quest)
    if last_boundary > 0:
        return text[:last_boundary + 1]
    return text


def _parse_json_response(response: str) -> dict:
    """Parse JSON from an LLM response, handling common formatting issues."""
    if not response:
        return {}

    # Try direct parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code blocks
    code_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding the largest JSON object in the response
    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    print("WARNING: Could not parse JSON from LLM response. Using empty dict.")
    return {}
