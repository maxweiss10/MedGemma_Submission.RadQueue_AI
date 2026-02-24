"""
Longitudinal EMR Generator.

Generates complete multi-year patient charts from clinical vignettes.
Produces 3-7 years of encounter history with trending labs, evolving
medications, and temporal disease progression.
"""

import random
import re
from dataclasses import fields
from datetime import datetime, timedelta
from typing import Optional

from .emr_models import (
    Allergy,
    ClinicalNote,
    ClinicalScenario,
    ClinicalVignette,
    Encounter,
    EncounterRecord,
    GenerationMetadata,
    ImagingOrder,
    ImagingReport,
    LabPanel,
    LabResult,
    LongitudinalEMR,
    Medication,
    MedicationChange,
    MedicationList,
    NursingNote,
    ParsedVignette,
    PatientDemographics,
    ProblemListEntry,
    SocialHistory,
    SurgicalProcedure,
    VitalSignSet,
)
from .clinical_knowledge import (
    ANNUAL_PHYSICAL_VARIANTS,
    CONDITION_EXPANSIONS,
    CONDITION_PROGRESSIONS,
    CONDITION_PROGRESSION_MAP,
    ENCOUNTER_TYPE_PROFILES,
    LAB_PANELS,
    LAB_PANELS_BY_ENCOUNTER_TYPE,
    NORMAL_LAB_RANGES,
    VITAL_RANGES,
    calculate_gfr,
    evolve_lab_value,
    flag_lab_value,
    generate_normal_value,
    get_random_demographics,
    get_random_hospital,
    get_random_nurse,
    get_random_provider,
    lookup_rxnorm,
)
from .emr_narrative import NarrativeBackend
from .vignette_parser import VignetteParser


def _default_family_history(rng: random.Random) -> list[str]:
    """Generate randomized default family history."""
    pool = [
        "Father with hypertension",
        "Mother with type 2 diabetes",
        "Father with coronary artery disease",
        "Mother with breast cancer",
        "Sibling with hypertension",
        "No family history of gallbladder disease",
        "Father with hyperlipidemia",
        "Mother with osteoporosis",
        "Maternal grandmother with stroke",
    ]
    return rng.sample(pool, min(rng.randint(2, 4), len(pool)))


def _merge_exam_findings(vignette_pe: Optional[str], llm_pe: str) -> str:
    """Merge vignette-sourced exam findings with LLM-generated findings.

    Vignette findings (e.g., "+Murphy's sign, no rebound") are placed first
    so the PE prompt sees them explicitly.
    """
    vignette_pe = (vignette_pe or "").strip()
    llm_pe = (llm_pe or "").strip()
    if vignette_pe and llm_pe:
        return f"{vignette_pe}. {llm_pe}"
    return vignette_pe or llm_pe


class LongitudinalEMRGenerator:
    """
    Generates complete longitudinal synthetic EMRs from clinical vignettes.

    Produces a multi-year patient chart with temporal disease progression,
    multiple encounters, trending labs, and evolving medication lists.

    Args:
        narrative_backend: LLM backend for narrative generation (required).
        vignette_parser: Parser for free-text vignettes.
    """

    def __init__(
        self,
        narrative_backend: NarrativeBackend,
        vignette_parser: Optional[VignetteParser] = None,
    ):
        self.backend = narrative_backend
        self.parser = vignette_parser or VignetteParser(self.backend)

    def generate(self, vignette: ClinicalVignette) -> LongitudinalEMR:
        """
        Generate a complete longitudinal EMR from a clinical vignette.

        Pipeline:
        1. Parse vignette into structured data
        2. Delegate to generate_from_parsed()
        """
        # Step 1: Parse vignette
        print("  Parsing clinical vignette...")
        parsed = self.parser.parse(vignette)

        return self.generate_from_parsed(
            parsed, vignette=vignette, seed=vignette.seed,
        )

    def generate_from_parsed(
        self,
        parsed: ParsedVignette,
        vignette: Optional[ClinicalVignette] = None,
        seed: Optional[int] = None,
        mask_diagnosis_in_narratives: bool = False,
    ) -> LongitudinalEMR:
        """
        Generate a complete longitudinal EMR from a pre-parsed ParsedVignette.

        Skips the VignetteParser step — useful when structured data is already
        available (e.g., from a spreadsheet dataset).

        Args:
            parsed: Pre-populated ParsedVignette with structured clinical data.
            vignette: Optional source vignette for metadata tracking.
            seed: Random seed for reproducibility.
            mask_diagnosis_in_narratives: If True, provider-facing notes use a
                symptom-based description instead of the actual diagnosis, so
                the EMR reflects diagnostic uncertainty.
        """
        rng = random.Random(seed)

        # Step 2: Generate demographics
        sex = parsed.sex
        age = parsed.age
        demo_data = get_random_demographics(sex=sex, age=age, rng=rng)
        patient = PatientDemographics(**demo_data)

        # Use parsed age/sex if demographics overrode them
        if parsed.age is None:
            parsed.age = patient.age
        if parsed.sex is None:
            parsed.sex = patient.sex

        # Step 3: Build timeline
        print("  Building longitudinal timeline...")
        timeline_events = self._build_timeline(parsed, patient, rng)

        # Step 4: Generate prior encounters
        encounter_history = []
        problem_list = []
        medication_history = []
        current_meds = []
        allergies = []
        surgical_history = []
        family_history = []
        social_history = SocialHistory()

        primary_hospital = get_random_hospital(rng)
        specialist_hospital = get_random_hospital(rng)
        # Ensure different hospitals for specialist vs primary care
        attempts = 0
        while specialist_hospital == primary_hospital and attempts < 5:
            specialist_hospital = get_random_hospital(rng)
            attempts += 1

        pcp = get_random_provider("Family Medicine", rng)
        # PCP rotation for long timelines (>4 years)
        secondary_pcp = None
        pcp_switch_date = None
        if timeline_events:
            span_days = (
                max(e["_date"] for e in timeline_events)
                - min(e["_date"] for e in timeline_events)
            ).days
            if span_days > 4 * 365:
                secondary_pcp = get_random_provider("Family Medicine", rng)
                attempts = 0
                while secondary_pcp == pcp and attempts < 5:
                    secondary_pcp = get_random_provider("Family Medicine", rng)
                    attempts += 1
                # Midpoint date for PCP switch
                pcp_switch_date = min(e["_date"] for e in timeline_events) + timedelta(
                    days=span_days // 2
                )

        inpatient_meds = []

        # Populate surgical history from parsed data
        if parsed.surgical_history:
            for proc_text in parsed.surgical_history:
                # Try to extract year from text like "cholecystectomy (2018)"
                year_match = re.search(r'\((\d{4})\)', proc_text)
                proc_year = int(year_match.group(1)) if year_match else (
                    datetime.now().year - rng.randint(2, 10)
                )
                # Clean procedure name
                proc_name = re.sub(r'\s*\(\d{4}\)', '', proc_text).strip()
                surgical_history.append(SurgicalProcedure(
                    procedure=proc_name,
                    year=proc_year,
                ))

        # Inject contrast/allergy flags from parsed data
        if parsed.safety_flags_mentioned:
            for flag in parsed.safety_flags_mentioned:
                flag_lower = flag.lower()
                if "contrast" in flag_lower or "iodinated" in flag_lower:
                    if not any(a.allergen == "Iodinated contrast" for a in allergies):
                        allergies.append(Allergy(
                            allergen="Iodinated contrast",
                            reaction="Anaphylaxis/urticaria",
                            severity="Severe",
                        ))
                elif "gadolinium" in flag_lower:
                    if not any(a.allergen == "Gadolinium" for a in allergies):
                        allergies.append(Allergy(
                            allergen="Gadolinium",
                            reaction="Nephrogenic systemic fibrosis risk",
                            severity="Severe",
                        ))
                elif "shellfish" in flag_lower:
                    if not any(a.allergen == "Shellfish" for a in allergies):
                        allergies.append(Allergy(
                            allergen="Shellfish",
                            reaction="Allergic reaction",
                            severity="Moderate",
                        ))

        # Build narrative diagnosis override for masking
        narrative_dx_override = None
        if mask_diagnosis_in_narratives:
            cc = parsed.chief_complaint or "Abdominal pain"
            narrative_dx_override = f"{cc}, etiology under evaluation"

        print(f"  Generating {len(timeline_events)} encounters...")
        for i, event in enumerate(timeline_events):
            is_current = (i == len(timeline_events) - 1)

            if is_current:
                # Step 5: Generate current encounter (full detail)
                print("  Generating current encounter (full detail)...")
                record, inpatient_meds, clinical_data = self._generate_current_encounter(
                    parsed, patient, problem_list, current_meds,
                    allergies, primary_hospital, rng,
                    narrative_diagnosis_override=narrative_dx_override,
                )
            else:
                # Choose hospital: specialists use specialist_hospital
                enc_type = event.get("encounter_type", "outpatient_pcp")
                if "specialist" in enc_type or enc_type.startswith("outpatient_") and enc_type != "outpatient_pcp":
                    event_hospital = specialist_hospital
                else:
                    event_hospital = primary_hospital

                # PCP rotation: use secondary PCP after switch date
                event_pcp = pcp
                if secondary_pcp and event["_date"] > pcp_switch_date:
                    event_pcp = secondary_pcp

                # Generate prior encounter (template-based by default)
                record = self._generate_prior_encounter(
                    event, patient, problem_list, current_meds,
                    medication_history, event_hospital, event_pcp, rng,
                )

            encounter_history.append(record)

            # Update running state from event
            if not is_current and "new_diagnoses" in event:
                for dx in event["new_diagnoses"]:
                    if not any(p.condition == dx["condition"] for p in problem_list):
                        problem_list.append(ProblemListEntry(
                            condition=dx["condition"],
                            icd10=dx.get("icd10"),
                            date_added=record.encounter.admission_datetime,
                            status="Active",
                            added_encounter_id=record.encounter.encounter_id,
                        ))

            if not is_current and "new_medications" in event:
                for med_data in event["new_medications"]:
                    med = Medication(**med_data)
                    if not med.rxnorm_code:
                        med.rxnorm_code = lookup_rxnorm(med.name)
                    if not any(m.name == med.name for m in current_meds):
                        current_meds.append(med)
                        medication_history.append(MedicationChange(
                            medication=med,
                            change_type="Started",
                            change_date=record.encounter.admission_datetime,
                            encounter_id=record.encounter.encounter_id,
                            reason=med.indication,
                        ))

            if not is_current and "medication_changes" in event:
                for change in event["medication_changes"]:
                    for med in current_meds:
                        if med.name == change["medication_name"]:
                            old_dose = med.dose
                            med.dose = change.get("new_dose", med.dose)
                            medication_history.append(MedicationChange(
                                medication=Medication(
                                    name=med.name, dose=med.dose,
                                    route=med.route, frequency=med.frequency,
                                    rxnorm_code=med.rxnorm_code or lookup_rxnorm(med.name),
                                ),
                                change_type=change["change_type"],
                                change_date=record.encounter.admission_datetime,
                                encounter_id=record.encounter.encounter_id,
                                reason=change.get("reason"),
                                previous_dose=old_dose,
                            ))

        # Build family history from LLM clinical data, or randomized defaults
        if not family_history:
            llm_fh = clinical_data.get("family_history", [])
            if isinstance(llm_fh, list) and llm_fh:
                family_history = llm_fh
            else:
                family_history = _default_family_history(rng)

        # Build social history from LLM clinical data
        sh_data = clinical_data.get("social_history", {})
        if isinstance(sh_data, dict) and sh_data:
            social_history = SocialHistory(
                smoking_status=sh_data.get("smoking_status", "Never"),
                alcohol_use=sh_data.get("alcohol_use", "Social"),
                occupation=sh_data.get("occupation"),
                living_situation=sh_data.get("living_situation"),
            )

        # Step 6: Assemble
        return LongitudinalEMR(
            patient=patient,
            encounter_history=encounter_history,
            problem_list=problem_list,
            medication_history=medication_history,
            current_medications=MedicationList(
                home_medications=list(current_meds),
                inpatient_medications=inpatient_meds,
            ),
            allergies=allergies,
            surgical_history=surgical_history,
            family_history=family_history,
            social_history=social_history,
            source_vignette=vignette,
            parsed_vignette=parsed,
            generation_metadata=GenerationMetadata(
                generator_version="2.0.0",
                generation_timestamp=datetime.now().isoformat(),
                narrative_backend=self.backend.name,
                seed=seed,
            ),
        )

    def generate_from_scenario(self, scenario: ClinicalScenario) -> LongitudinalEMR:
        """Backward-compatible entry point from a ClinicalScenario."""
        vignette_text = (
            f"A {scenario.age_hint or 55}-year-old "
            f"{'woman' if scenario.sex_hint == 'Female' else 'man' if scenario.sex_hint == 'Male' else 'patient'} "
            f"with a history of {scenario.history_summary or 'no significant PMH'} "
            f"presents with {scenario.protocol_indication or scenario.diagnosis}. "
            f"The provider orders {scenario.ordered_study or 'imaging'}."
        )
        vignette = ClinicalVignette(
            vignette_text=vignette_text,
            case_id=scenario.case_id,
            case_name=scenario.case_name,
            seed=scenario.seed,
        )
        return self.generate(vignette)

    # =========================================================================
    # TIMELINE CONSTRUCTION
    # =========================================================================

    def _build_timeline(
        self, parsed: ParsedVignette, patient: PatientDemographics,
        rng: random.Random,
    ) -> list[dict]:
        """
        Build a chronological timeline of encounter events.

        Uses condition progression templates to determine when encounters
        happen and what diagnoses/medications are introduced at each.
        """
        events = []
        now = datetime.now()
        used_progressions = set()

        # Find applicable condition progressions from patient history
        conditions_text = " ".join(parsed.history_conditions).lower()
        # Also check the diagnosis itself for progression context
        full_text = conditions_text + " " + parsed.diagnosis.lower()

        for keyword, prog_key in CONDITION_PROGRESSION_MAP.items():
            if keyword in full_text and prog_key not in used_progressions:
                progression = CONDITION_PROGRESSIONS.get(prog_key)
                if progression:
                    used_progressions.add(prog_key)
                    for stage in progression["stages"]:
                        year_offset = stage["year_offset"]
                        month_offset = stage.get("month_offset", 0)
                        event_date = now + timedelta(
                            days=year_offset * 365 + month_offset * 30
                            + rng.randint(-30, 30)
                        )
                        events.append({
                            **stage,
                            "_date": event_date,
                            "_source": prog_key,
                        })

        # Add annual physicals to fill gaps
        if events:
            earliest = min(e["_date"] for e in events)
            years_back = max(1, (now - earliest).days // 365)
        else:
            years_back = 3

        for y in range(years_back, 0, -1):
            annual_date = now - timedelta(days=y * 365 + rng.randint(-60, 60))
            # Don't add if there's already an encounter within 60 days
            if not any(abs((e["_date"] - annual_date).days) < 60 for e in events):
                variant = rng.choice(ANNUAL_PHYSICAL_VARIANTS)
                events.append({
                    "encounter_type": "outpatient_pcp",
                    "reason": variant["reason"],
                    "new_diagnoses": [],
                    "new_medications": [],
                    "note_template": variant["note_template"],
                    "_date": annual_date,
                    "_source": "annual",
                })

        # Add the current encounter as the last event
        # Map clinical setting to timeline encounter type
        setting = (parsed.clinical_setting or "ED").lower()
        if "icu" in setting or "sicu" in setting or "micu" in setting:
            current_enc_type = "icu"
        elif "inpatient" in setting:
            current_enc_type = "inpatient"
        elif "urgent" in setting:
            current_enc_type = "urgent_care"
        elif "ed" in setting or "emergency" in setting:
            current_enc_type = "ed"
        else:
            current_enc_type = "outpatient_pcp"

        current_date = now - timedelta(days=rng.randint(1, 14))
        if current_enc_type in ("ed", "urgent_care"):
            current_hour = rng.randint(0, 23)
        elif current_enc_type in ("inpatient", "icu"):
            current_hour = rng.randint(6, 18)
        else:
            current_hour = rng.randint(8, 16)  # Outpatient clinic hours
        current_date = current_date.replace(
            hour=current_hour, minute=rng.randint(0, 59),
            second=0, microsecond=0,
        )
        events.append({
            "encounter_type": current_enc_type,
            "reason": parsed.chief_complaint or parsed.diagnosis,
            "new_diagnoses": [],
            "new_medications": [],
            "_date": current_date,
            "_source": "current",
            "_is_current": True,
        })

        # Set clinically-appropriate hours on prior event dates
        for event in events:
            if event.get("_is_current"):
                continue  # current encounter already has its hour set above
            enc_type = event.get("encounter_type", "outpatient_pcp")
            if enc_type in ("ed", "urgent_care"):
                hour = rng.randint(0, 23)
            elif enc_type in ("inpatient", "icu"):
                hour = rng.randint(6, 18)
            else:
                hour = rng.randint(8, 16)  # Outpatient clinic hours
            event["_date"] = event["_date"].replace(
                hour=hour, minute=rng.randint(0, 59),
                second=0, microsecond=0,
            )

        # Sort chronologically
        events.sort(key=lambda e: e["_date"])

        return events

    # =========================================================================
    # PRIOR ENCOUNTER GENERATION
    # =========================================================================

    def _generate_prior_encounter(
        self, event: dict, patient: PatientDemographics,
        problem_list: list[ProblemListEntry], current_meds: list[Medication],
        medication_history: list[MedicationChange],
        hospital: str, pcp: str, rng: random.Random,
    ) -> EncounterRecord:
        """Generate a prior (historical) encounter from a timeline event."""
        event_date = event["_date"]
        enc_type = event.get("encounter_type", "outpatient_pcp")
        profile = ENCOUNTER_TYPE_PROFILES.get(enc_type, ENCOUNTER_TYPE_PROFILES["outpatient_pcp"])

        # Provider — use profile-specific specialty for all non-PCP encounters
        if enc_type == "outpatient_pcp":
            provider = pcp
        elif enc_type == "ed":
            provider = get_random_provider("Emergency Medicine", rng)
        else:
            provider = get_random_provider(profile.get("provider_specialty", "Internal Medicine"), rng)

        encounter_id = f"ENC-{event_date.strftime('%Y%m%d')}-{rng.randint(100, 999)}"
        duration = profile["duration_hours"]
        if isinstance(duration, tuple):
            duration = round(rng.uniform(*duration), 2)
        discharge_dt = event_date + timedelta(hours=duration)

        encounter = Encounter(
            encounter_id=encounter_id,
            encounter_type=profile["encounter_type"],
            facility=hospital,
            admission_datetime=event_date.isoformat(),
            discharge_datetime=discharge_dt.isoformat(),
            attending_provider=provider,
            department=profile["department"],
            chief_complaint=event.get("reason", "Follow-up"),
            disposition=profile["disposition"],
        )

        # Vitals (stable for outpatient, slightly elevated for ED)
        vital_signs = []
        acuity = "stable" if "outpatient" in enc_type else "mild"
        ranges = VITAL_RANGES.get(acuity, VITAL_RANGES["stable"])

        # Apply any BP overrides from event
        bp_systolic_range = ranges["blood_pressure_systolic"]
        if "vitals_bp_systolic" in event:
            bp_systolic_range = event["vitals_bp_systolic"]

        for v_idx in range(profile["vitals_count"]):
            v_time = event_date + timedelta(minutes=5 + v_idx * 240)
            vs = VitalSignSet(
                timestamp=v_time.isoformat(),
                encounter_id=encounter_id,
                temperature_f=round(rng.uniform(*ranges["temperature_f"]), 1),
                heart_rate=rng.randint(*ranges["heart_rate"]),
                blood_pressure_systolic=rng.randint(*bp_systolic_range),
                blood_pressure_diastolic=rng.randint(*ranges["blood_pressure_diastolic"]),
                respiratory_rate=rng.randint(*ranges["respiratory_rate"]),
                oxygen_saturation=round(rng.uniform(*ranges["oxygen_saturation"]), 1),
                pain_scale=rng.randint(*ranges["pain_scale"]),
                source="Triage" if v_idx == 0 else "Nursing",
            )
            vital_signs.append(vs)

        # Labs (based on encounter type and condition)
        lab_results = self._generate_prior_labs(
            event, encounter_id, event_date, patient, provider, rng,
        )

        # Imaging (if event calls for it)
        imaging_orders = []
        imaging_reports = []
        if event.get("generates_imaging") and "imaging" in event:
            img = event["imaging"]
            order_time = event_date + timedelta(hours=1)
            oid = f"IMG-{order_time.strftime('%Y%m%d')}-{rng.randint(100, 999)}"
            imaging_orders.append(ImagingOrder(
                order_id=oid,
                modality=img.get("modality", "Imaging"),
                body_region=img.get("body_region", "Abdomen"),
                contrast=img.get("contrast", ""),
                indication=event.get("reason", ""),
                ordering_provider=provider,
                order_datetime=order_time.isoformat(),
                urgency="Routine",
                status="Completed",
            ))
            report_time = order_time + timedelta(hours=2)
            imaging_reports.append(ImagingReport(
                order_id=oid,
                modality=f"{img.get('modality', '')} {img.get('body_region', '')}",
                report_datetime=report_time.isoformat(),
                radiologist=get_random_provider("Radiology", rng),
                technique=f"{img.get('modality', 'Imaging')} of the {img.get('body_region', 'abdomen')} was performed {img.get('contrast', '')}.",
                findings=img.get("findings_template", "No significant findings."),
                impression=img.get("impression_template", "No acute findings."),
            ))

        # Clinical note — always use LLM backend for richer notes
        med_list = ", ".join(f"{m.name} {m.dose}" for m in current_meds) or "None"
        pmh = ", ".join(p.condition for p in problem_list) or "No significant PMH"
        note_ctx = {
            "age": patient.age, "sex": patient.sex,
            "reason": event.get("reason", "follow-up"),
            "medical_history": pmh, "medications": med_list,
            "bp": f"{vital_signs[0].blood_pressure_systolic}/{vital_signs[0].blood_pressure_diastolic}" if vital_signs else "120/80",
            "heart_rate": vital_signs[0].heart_rate if vital_signs else 80,
            "labs_summary": self._summarize_labs(lab_results),
            "assessment": event.get("note_template", "Stable."),
        }
        is_specialist = (
            enc_type.startswith("outpatient_")
            and enc_type != "outpatient_pcp"
        )
        if is_specialist:
            note_text = self.backend.generate_consultation_note({
                **note_ctx,
                "referring_provider": pcp,
            })
            note_type = "Consultation Note"
        elif enc_type == "ed":
            note_text = self.backend.generate_office_visit_note(note_ctx)
            note_type = "ED Note"
        else:
            note_text = self.backend.generate_office_visit_note(note_ctx)
            note_type = "Office Visit"

        clinical_notes = [ClinicalNote(
            note_type=note_type,
            encounter_id=encounter_id,
            timestamp=event_date.isoformat(),
            author=provider,
            note_text=note_text,
        )]

        # Diagnoses for this encounter
        diagnoses = [dx["condition"] for dx in event.get("new_diagnoses", [])]
        if event.get("reason"):
            diagnoses.append(event["reason"])

        return EncounterRecord(
            encounter=encounter,
            vital_signs=vital_signs,
            lab_results=lab_results,
            imaging_orders=imaging_orders,
            imaging_reports=imaging_reports,
            clinical_notes=clinical_notes,
            diagnoses=diagnoses,
        )

    def _generate_prior_labs(
        self, event: dict, encounter_id: str, event_date: datetime,
        patient: PatientDemographics, provider: str, rng: random.Random,
    ) -> list[LabPanel]:
        """Generate lab panels for a prior encounter based on event type."""
        enc_type = event.get("encounter_type", "outpatient_pcp")
        lab_targets = event.get("lab_targets", {})

        # Determine which panels to run based on encounter source
        source = str(event.get("_source", "")).lower()
        reason = str(event.get("reason", "")).lower()
        panel_key = "annual_physical"
        if enc_type == "ed":
            panel_key = "ed_abdominal"
        elif "dm" in source or "diabetes" in reason or "metabolic" in source:
            panel_key = "dm_followup"
        elif "ckd" in source or "kidney" in reason:
            panel_key = "ckd_followup"
        elif "thyroid" in source:
            panel_key = "thyroid_followup"
        elif "hepat" in source or "liver" in source or "nafld" in source:
            panel_key = "hep_followup"
        elif "cad" in source or "chf" in source or "cardiac" in reason:
            panel_key = "cardiology_clinic"
        elif "dvt" in source or "pe_history" in source:
            panel_key = "ed_dvt_pe"
        elif "lupus" in source or "sle" in reason:
            panel_key = "rheumatology_clinic"
        elif "asthma" in source or "osa" in source or "copd" in source:
            panel_key = "pulmonology_clinic"
        elif "ibs" in source or "divertic" in source or "gi" in reason:
            panel_key = "gi_clinic"
        elif "iron_deficiency" in source or "anemia" in source:
            panel_key = "iron_studies"
        elif "gout" in source:
            panel_key = "urology_clinic"
        elif "migraine" in source or "neuro" in reason:
            panel_key = "neurology_clinic"

        panel_names = LAB_PANELS_BY_ENCOUNTER_TYPE.get(panel_key, ["CBC", "CMP"])
        draw_time = (event_date + timedelta(minutes=rng.randint(10, 30))).isoformat()
        panels = []

        for panel_name in panel_names:
            test_keys = LAB_PANELS.get(panel_name, [])
            results = []
            for test_key in test_keys:
                # Get sex-specific reference
                ref_key = f"{test_key}_{patient.sex.lower()}"
                ref = NORMAL_LAB_RANGES.get(ref_key) or NORMAL_LAB_RANGES.get(test_key)
                if not ref:
                    continue

                # Use target value if specified, otherwise normal
                if test_key in lab_targets:
                    target_range = lab_targets[test_key]
                    value = round(rng.uniform(*target_range), 1)
                else:
                    value = generate_normal_value(ref, rng)

                # Friendly name
                name_map = {
                    "wbc": "WBC", "hemoglobin": "Hemoglobin",
                    "hematocrit": "Hematocrit", "platelets": "Platelets",
                    "sodium": "Sodium", "potassium": "Potassium",
                    "chloride": "Chloride", "co2": "CO2", "bun": "BUN",
                    "creatinine": "Creatinine", "glucose": "Glucose",
                    "calcium": "Calcium", "albumin": "Albumin",
                    "total_protein": "Total Protein",
                    "ast": "AST", "alt": "ALT", "alp": "ALP", "ggt": "GGT",
                    "bilirubin_total": "Bilirubin, Total",
                    "bilirubin_direct": "Bilirubin, Direct",
                    "lipase": "Lipase", "amylase": "Amylase",
                    "inr": "INR", "pt": "PT", "ptt": "PTT",
                    "lactate": "Lactate", "hba1c": "HbA1c", "tsh": "TSH",
                    "troponin_i": "Troponin I", "bnp": "BNP",
                    "crp": "CRP", "esr": "ESR",
                    "procalcitonin": "Procalcitonin", "d_dimer": "D-dimer",
                    "mcv": "MCV", "rdw": "RDW",
                    "magnesium": "Magnesium", "phosphorus": "Phosphorus",
                    "iron": "Iron", "ferritin": "Ferritin", "tibc": "TIBC",
                    "vitamin_d": "Vitamin D", "vitamin_b12": "Vitamin B12",
                    "free_t4": "Free T4", "uric_acid": "Uric Acid",
                }
                test_name = name_map.get(test_key, test_key.upper())

                results.append(LabResult(
                    test_name=test_name,
                    value=value,
                    unit=ref["unit"],
                    reference_low=ref["low"],
                    reference_high=ref["high"],
                    flag=flag_lab_value(value, ref),
                    loinc_code=ref.get("loinc"),
                ))

            if results:
                panels.append(LabPanel(
                    panel_name=panel_name,
                    timestamp=draw_time,
                    encounter_id=encounter_id,
                    results=results,
                    ordering_provider=provider,
                ))

        # Add calculated GFR if creatinine is present
        for panel in panels:
            cr_val = next(
                (r.value for r in panel.results if r.test_name == "Creatinine"),
                None,
            )
            if cr_val:
                gfr = calculate_gfr(cr_val, patient.age, patient.sex)
                # Adjust GFR for target if specified
                gfr_target = event.get("gfr_target")
                if gfr_target:
                    gfr = round(rng.uniform(*gfr_target), 1)
                panel.results.append(LabResult(
                    test_name="eGFR",
                    value=gfr,
                    unit="mL/min/1.73m2",
                    reference_low=90.0,
                    reference_high=120.0,
                    flag="L" if gfr < 90 else None,
                    loinc_code="33914-3",
                ))

        return panels

    # =========================================================================
    # CURRENT ENCOUNTER GENERATION
    # =========================================================================

    def _generate_current_encounter(
        self, parsed: ParsedVignette, patient: PatientDemographics,
        problem_list: list[ProblemListEntry], current_meds: list[Medication],
        allergies: list[Allergy], hospital: str, rng: random.Random,
        narrative_diagnosis_override: Optional[str] = None,
    ) -> tuple[EncounterRecord, list[Medication], dict]:
        """
        Generate the current (presenting) encounter with full detail.

        This is the most detailed encounter, using the LLM for narrative
        generation (HPI, PE, A&P, radiology report, nursing, discharge).

        Args:
            narrative_diagnosis_override: If provided, use this instead of
                the actual diagnosis in provider-facing narratives (HPI, PE,
                A&P, nursing notes). The real diagnosis is still used for
                clinical data generation to ensure consistency.

        Returns:
            Tuple of (EncounterRecord, inpatient_medications, clinical_data)
        """
        now = datetime.now()
        base_dt = now - timedelta(days=rng.randint(1, 14))

        # Map clinical setting to encounter type, department, and specialty
        setting = (parsed.clinical_setting or "ED").lower()

        # Setting-aware encounter hours
        if "ed" in setting or "emergency" in setting or "urgent" in setting:
            enc_hour = rng.randint(0, 23)
        elif "icu" in setting or "inpatient" in setting:
            enc_hour = rng.randint(6, 18)
        else:
            enc_hour = rng.randint(8, 16)  # Outpatient clinic hours
        base_dt = base_dt.replace(
            hour=enc_hour, minute=rng.randint(0, 59),
            second=0, microsecond=0,
        )
        if "icu" in setting or "sicu" in setting or "micu" in setting:
            enc_type = "Inpatient"
            department = parsed.clinical_setting or "Intensive Care Unit"
            specialty = "Critical Care"
            disposition = "Admitted to ICU"
        elif "inpatient" in setting:
            enc_type = "Inpatient"
            department = "Medical Floor"
            specialty = "Internal Medicine"
            disposition = "Admitted to Medicine"
        elif "urgent" in setting:
            enc_type = "Urgent Care"
            department = "Urgent Care"
            specialty = "Emergency Medicine"
            disposition = "Discharged with follow-up"
        elif "ed" in setting or "emergency" in setting:
            enc_type = "ED"
            department = "Emergency Department"
            specialty = "Emergency Medicine"
            disposition = "Admitted to Medicine"
        else:
            # Outpatient / clinic settings
            enc_type = "Outpatient"
            department = parsed.clinical_setting or "Outpatient Clinic"
            specialty = "Internal Medicine"
            disposition = "Follow-up as needed"

        attending = get_random_provider(specialty, rng)
        encounter_id = f"ENC-{base_dt.strftime('%Y%m%d')}-{rng.randint(100, 999)}"

        encounter = Encounter(
            encounter_id=encounter_id,
            encounter_type=enc_type,
            facility=hospital,
            admission_datetime=base_dt.isoformat(),
            attending_provider=attending,
            department=department,
            chief_complaint=parsed.chief_complaint or parsed.diagnosis,
            disposition=disposition,
        )

        # Ask LLM for diagnosis-specific clinical data
        pmh = ", ".join(p.condition for p in problem_list) or "No significant PMH"
        med_list = ", ".join(f"{m.name} {m.dose}" for m in current_meds) or "None"

        # Use chief complaint as fallback when diagnosis is "(Not documented)"
        effective_dx = parsed.diagnosis if parsed.diagnosis != "(Not documented)" else (
            parsed.chief_complaint or "Abdominal pain, etiology unknown"
        )
        scenario_ctx = {
            "diagnosis": effective_dx,
            "age": patient.age,
            "sex": patient.sex,
            "history_summary": ", ".join(parsed.history_conditions) or pmh,
            "protocol_indication": parsed.chief_complaint or effective_dx,
        }
        print("    Generating diagnosis-specific clinical data...")
        clinical_data = self.backend.generate_clinical_data(scenario_ctx)

        # Vitals
        acuity = parsed.acuity or clinical_data.get("acuity", "mild")
        ranges = VITAL_RANGES.get(acuity, VITAL_RANGES["mild"])

        def _validated_vital(val, key):
            r = ranges[key]
            if val is not None:
                try:
                    v = float(val)
                    lo, hi = r
                    if lo - (hi - lo) * 0.5 <= v <= hi + (hi - lo) * 0.5:
                        return round(v, 1)
                except (ValueError, TypeError):
                    pass
            lo, hi = r
            return round(max(lo, min(hi, rng.gauss((lo + hi) / 2, (hi - lo) / 4))), 1)

        # Use vignette-mentioned vitals first, then LLM, then generate
        vd = {**clinical_data.get("vitals", {}), **parsed.vitals_mentioned}

        triage_time = base_dt + timedelta(minutes=rng.randint(3, 15))
        triage_vitals = VitalSignSet(
            timestamp=triage_time.isoformat(),
            encounter_id=encounter_id,
            temperature_f=_validated_vital(vd.get("temperature_f"), "temperature_f"),
            heart_rate=int(_validated_vital(vd.get("heart_rate"), "heart_rate")),
            blood_pressure_systolic=int(_validated_vital(
                vd.get("blood_pressure_systolic"), "blood_pressure_systolic")),
            blood_pressure_diastolic=int(_validated_vital(
                vd.get("blood_pressure_diastolic"), "blood_pressure_diastolic")),
            respiratory_rate=int(_validated_vital(
                vd.get("respiratory_rate"), "respiratory_rate")),
            oxygen_saturation=_validated_vital(
                vd.get("oxygen_saturation"), "oxygen_saturation"),
            pain_scale=int(_validated_vital(vd.get("pain_scale"), "pain_scale")),
            source="Triage",
        )

        # Reassessment vitals (trending toward stable)
        stable = VITAL_RANGES["stable"]
        def _blend(ar, sr, f=0.3):
            return (ar[0] + f * (sr[0] - ar[0]), ar[1] + f * (sr[1] - ar[1]))

        reassess_time = base_dt + timedelta(hours=4, minutes=rng.randint(0, 30))
        reassess_vitals = VitalSignSet(
            timestamp=reassess_time.isoformat(),
            encounter_id=encounter_id,
            temperature_f=_validated_vital(None, "temperature_f"),
            heart_rate=int(round(rng.uniform(*_blend(
                ranges["heart_rate"], stable["heart_rate"])), 0)),
            blood_pressure_systolic=int(round(rng.uniform(*_blend(
                ranges["blood_pressure_systolic"], stable["blood_pressure_systolic"])), 0)),
            blood_pressure_diastolic=int(round(rng.uniform(*_blend(
                ranges["blood_pressure_diastolic"], stable["blood_pressure_diastolic"])), 0)),
            respiratory_rate=int(round(rng.uniform(*_blend(
                ranges["respiratory_rate"], stable["respiratory_rate"])), 0)),
            oxygen_saturation=round(rng.uniform(*_blend(
                ranges["oxygen_saturation"], stable["oxygen_saturation"])), 1),
            pain_scale=max(0, (triage_vitals.pain_scale or 5) - rng.randint(1, 3)),
            source="Nursing",
        )

        vital_signs = [triage_vitals, reassess_vitals]

        # Labs
        ld = {**clinical_data.get("labs", {}), **parsed.labs_mentioned}
        lab_results = self._generate_current_labs(
            ld, encounter_id, base_dt, patient, attending, rng,
            acuity=acuity,
            diagnosis=parsed.diagnosis,
            setting=parsed.clinical_setting or "ED",
            history_conditions=parsed.history_conditions,
        )

        # Medications (inpatient from LLM)
        _med_fields = {f.name for f in fields(Medication)}
        inpatient_meds_for_encounter = [
            Medication(**{k: v for k, v in m.items() if k in _med_fields})
            for m in clinical_data.get("inpatient_medications", [])
            if isinstance(m, dict) and m.get("name")
        ]
        for med in inpatient_meds_for_encounter:
            if not med.rxnorm_code:
                med.rxnorm_code = lookup_rxnorm(med.name)

        # Allergies
        _allergy_fields = {f.name for f in fields(Allergy)}
        for a in clinical_data.get("allergies", []):
            if isinstance(a, dict) and a.get("allergen"):
                if not any(al.allergen == a["allergen"] for al in allergies):
                    # Remap common LLM key variants and filter to valid fields
                    if "type" in a and "allergy_type" not in a:
                        a["allergy_type"] = a.pop("type")
                    filtered = {k: v for k, v in a.items() if k in _allergy_fields}
                    allergies.append(Allergy(**filtered))

        # Imaging
        imaging_orders = []
        imaging_reports = []
        if parsed.ordered_study:
            # Determine urgency based on clinical setting
            if ("ed" in setting or "emergency" in setting or "icu" in setting
                    or "inpatient" in setting or "urgent" in setting):
                img_urgency = "Urgent"
            else:
                img_urgency = "Routine"

            order_time = base_dt + timedelta(hours=1, minutes=rng.randint(0, 30))
            oid = f"IMG-{order_time.strftime('%Y%m%d')}-{rng.randint(100, 999)}"
            imaging_orders.append(ImagingOrder(
                order_id=oid,
                modality=parsed.imaging_modality or "Imaging",
                body_region=parsed.imaging_body_region or "Abdomen",
                contrast=parsed.imaging_contrast or "",
                indication=parsed.chief_complaint or parsed.diagnosis,
                ordering_provider=attending,
                order_datetime=order_time.isoformat(),
                urgency=img_urgency,
                status="Ordered",
            ))

        # Build narrative context
        lv = triage_vitals
        labs_summary = self._summarize_labs(lab_results)
        prior_summary = self._build_prior_visit_summary(problem_list, current_meds)

        # Use override for provider-facing narratives if masking diagnosis
        narrative_dx = narrative_diagnosis_override or parsed.diagnosis
        narrative_indication = (
            parsed.chief_complaint or narrative_dx
        )

        n_ctx = {
            "age": patient.age, "sex": patient.sex,
            "diagnosis": narrative_dx,
            "chief_complaint": encounter.chief_complaint,
            "protocol_indication": narrative_indication,
            "medical_history": pmh,
            "medications": med_list,
            "temperature": lv.temperature_f or 98.6,
            "heart_rate": lv.heart_rate or 80,
            "bp": f"{lv.blood_pressure_systolic or 120}/{lv.blood_pressure_diastolic or 80}",
            "respiratory_rate": lv.respiratory_rate or 16,
            "spo2": lv.oxygen_saturation or 99,
            "pain": lv.pain_scale or 5,
            "labs_summary": labs_summary,
            "physical_exam_findings": _merge_exam_findings(
                parsed.exam_findings, clinical_data.get("physical_exam_findings", "")
            ),
            "imaging_ordered": parsed.ordered_study or "Imaging",
            "modality": parsed.imaging_modality or "Imaging",
            "body_region": parsed.imaging_body_region or "Abdomen",
            "contrast": parsed.imaging_contrast or "",
            "indication": narrative_indication,
            "time_description": "4 hours post-admission",
            "prior_visit_summary": prior_summary,
        }

        # Generate narratives
        clinical_notes = []

        print("    Generating HPI...")
        hpi = self.backend.generate_hpi(n_ctx)
        clinical_notes.append(ClinicalNote(
            note_type="HPI", encounter_id=encounter_id,
            timestamp=base_dt.isoformat(), author=attending, note_text=hpi,
        ))

        print("    Generating Physical Exam...")
        pe = self.backend.generate_physical_exam(n_ctx)
        clinical_notes.append(ClinicalNote(
            note_type="Physical Exam", encounter_id=encounter_id,
            timestamp=base_dt.isoformat(), author=attending, note_text=pe,
        ))

        print("    Generating Assessment & Plan...")
        ap = self.backend.generate_assessment_plan(n_ctx)
        clinical_notes.append(ClinicalNote(
            note_type="Assessment & Plan", encounter_id=encounter_id,
            timestamp=base_dt.isoformat(), author=attending, note_text=ap,
        ))

        print("    Generating Nursing Notes...")
        nursing_texts = self.backend.generate_nursing_notes(n_ctx)
        for nt in nursing_texts:
            clinical_notes.append(ClinicalNote(
                note_type="Nursing Note",
                encounter_id=encounter_id,
                timestamp=(base_dt + timedelta(hours=4)).isoformat(),
                author=get_random_nurse(rng),
                note_text=nt,
            ))

        # Add new diagnoses from current encounter
        # When masking, use the chief complaint as the working diagnosis
        diagnoses = [narrative_dx]

        record = EncounterRecord(
            encounter=encounter,
            vital_signs=vital_signs,
            lab_results=lab_results,
            imaging_orders=imaging_orders,
            imaging_reports=[],
            clinical_notes=clinical_notes,
            diagnoses=diagnoses,
        )
        return record, inpatient_meds_for_encounter, clinical_data

    def _generate_current_labs(
        self, lab_data: dict, encounter_id: str, base_dt: datetime,
        patient: PatientDemographics, attending: str, rng: random.Random,
        acuity: str = "mild", diagnosis: str = "",
        setting: str = "ED", history_conditions: list[str] = None,
    ) -> list[LabPanel]:
        """Generate lab panels for the current encounter.

        Always generates CBC and CMP+LFT. Adds extra panels based on:
        - lab_data keys present (lipase, lactate, troponin from LLM/dataset)
        - Clinical context (acuity, diagnosis, setting, PMHx)
        """
        draw_time = (base_dt + timedelta(minutes=rng.randint(20, 45))).isoformat()

        def _validated_lab(val, ref):
            if val is not None:
                try:
                    v = float(val)
                    lo = ref.get("critical_low", ref["low"] * 0.1)
                    hi = ref.get("critical_high", ref["high"] * 5.0)
                    if lo <= v <= hi:
                        return round(v, 1)
                except (ValueError, TypeError):
                    pass
            return generate_normal_value(ref, rng)

        def _make_result(name, key, sex_specific=False):
            rk = f"{key}_{patient.sex.lower()}" if sex_specific else key
            ref = NORMAL_LAB_RANGES.get(rk) or NORMAL_LAB_RANGES.get(key)
            if not ref:
                return None
            v = _validated_lab(lab_data.get(key), ref)
            return LabResult(
                test_name=name, value=v, unit=ref["unit"],
                reference_low=ref["low"], reference_high=ref["high"],
                flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
            )

        # CBC
        cbc = LabPanel(
            panel_name="CBC", timestamp=draw_time,
            encounter_id=encounter_id, ordering_provider=attending,
            results=[r for r in [
                _make_result("WBC", "wbc"),
                _make_result("Hemoglobin", "hemoglobin", True),
                _make_result("Hematocrit", "hematocrit", True),
                _make_result("Platelets", "platelets"),
            ] if r],
        )

        # CMP + LFT
        cmp_results = [r for r in [
            _make_result("Sodium", "sodium"),
            _make_result("Potassium", "potassium"),
            _make_result("Chloride", "chloride"),
            _make_result("CO2", "co2"),
            _make_result("BUN", "bun"),
            _make_result("Creatinine", "creatinine", True),
            _make_result("Glucose", "glucose"),
            _make_result("Calcium", "calcium"),
            _make_result("AST", "ast"),
            _make_result("ALT", "alt"),
            _make_result("ALP", "alp"),
            _make_result("Bilirubin, Total", "bilirubin_total"),
            _make_result("Bilirubin, Direct", "bilirubin_direct"),
            _make_result("Albumin", "albumin"),
        ] if r]

        # Add calculated GFR
        cr_val = next(
            (r.value for r in cmp_results if r.test_name == "Creatinine"), None,
        )
        if cr_val:
            gfr = calculate_gfr(cr_val, patient.age, patient.sex)
            cmp_results.append(LabResult(
                test_name="eGFR", value=gfr, unit="mL/min/1.73m2",
                reference_low=90.0, reference_high=120.0,
                flag="L" if gfr < 90 else None, loinc_code="33914-3",
            ))

        cmp = LabPanel(
            panel_name="CMP + LFT", timestamp=draw_time,
            encounter_id=encounter_id, ordering_provider=attending,
            results=cmp_results,
        )

        panels = [cbc, cmp]

        # Lipase if present
        lip = lab_data.get("lipase")
        if lip is not None:
            ref = NORMAL_LAB_RANGES["lipase"]
            v = _validated_lab(lip, ref)
            panels.append(LabPanel(
                panel_name="Lipase", timestamp=draw_time,
                encounter_id=encounter_id, ordering_provider=attending,
                results=[LabResult(
                    test_name="Lipase", value=v, unit=ref["unit"],
                    reference_low=ref["low"], reference_high=ref["high"],
                    flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                )],
            ))

        # Lactate if present
        lac = lab_data.get("lactate")
        if lac is not None:
            ref = NORMAL_LAB_RANGES["lactate"]
            v = _validated_lab(lac, ref)
            panels.append(LabPanel(
                panel_name="Lactate", timestamp=draw_time,
                encounter_id=encounter_id, ordering_provider=attending,
                results=[LabResult(
                    test_name="Lactate", value=v, unit=ref["unit"],
                    reference_low=ref["low"], reference_high=ref["high"],
                    flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                )],
            ))

        # Troponin if present
        trop = lab_data.get("troponin_i")
        if trop is not None:
            ref = NORMAL_LAB_RANGES["troponin_i"]
            v = _validated_lab(trop, ref)
            panels.append(LabPanel(
                panel_name="Cardiac Markers", timestamp=draw_time,
                encounter_id=encounter_id, ordering_provider=attending,
                results=[LabResult(
                    test_name="Troponin I", value=v, unit=ref["unit"],
                    reference_low=ref["low"], reference_high=ref["high"],
                    flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                )],
            ))

        # ── Context-driven extra panels ──────────────────────────────────
        # Add clinically relevant labs based on scenario (acuity, diagnosis,
        # setting, PMHx).  Only adds panels not already present.
        dx_lower = diagnosis.lower()
        setting_lower = setting.lower()
        pmhx_text = " ".join(history_conditions or []).lower()
        added_panels = {p.panel_name for p in panels}

        is_ed_or_inpatient = any(
            k in setting_lower for k in ("ed", "emergency", "icu", "inpatient", "sicu", "micu")
        )

        # --- Coagulation panel: ED/inpatient + liver/biliary/coag concerns ---
        needs_coags = (
            is_ed_or_inpatient
            and (
                any(k in dx_lower for k in ("cholangitis", "liver", "hepat", "cirrhosis",
                    "coagulopathy", "bleeding", "varices", "pancreatitis"))
                or lab_data.get("inr") is not None
                or acuity in ("septic", "shock")
            )
        )
        if needs_coags and "Coagulation" not in added_panels:
            coag_results = [r for r in [
                _make_result("INR", "inr"),
                _make_result("PT", "pt"),
                _make_result("PTT", "ptt"),
            ] if r]
            if coag_results:
                panels.append(LabPanel(
                    panel_name="Coagulation", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=coag_results,
                ))
                added_panels.add("Coagulation")

        # --- Inflammatory markers: febrile/septic/shock acuity ---
        needs_inflammatory = acuity in ("febrile", "septic", "shock")
        if needs_inflammatory and "Inflammatory Markers" not in added_panels:
            inf_results = []
            for name, key in [("CRP", "crp"), ("ESR", "esr"), ("Procalcitonin", "procalcitonin")]:
                ref = NORMAL_LAB_RANGES.get(key)
                if ref:
                    v = _validated_lab(lab_data.get(key), ref)
                    # For septic/shock, CRP and procalcitonin should be elevated
                    if acuity in ("septic", "shock") and lab_data.get(key) is None:
                        if key == "crp":
                            v = round(rng.uniform(8.0, 25.0), 1)
                        elif key == "procalcitonin":
                            v = round(rng.uniform(2.0, 15.0), 2)
                        elif key == "esr":
                            v = round(rng.uniform(40.0, 90.0), 0)
                    elif acuity == "febrile" and lab_data.get(key) is None:
                        if key == "crp":
                            v = round(rng.uniform(3.0, 12.0), 1)
                        elif key == "procalcitonin":
                            v = round(rng.uniform(0.5, 3.0), 2)
                    inf_results.append(LabResult(
                        test_name=name, value=v, unit=ref["unit"],
                        reference_low=ref["low"], reference_high=ref["high"],
                        flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                    ))
            if inf_results:
                panels.append(LabPanel(
                    panel_name="Inflammatory Markers", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=inf_results,
                ))
                added_panels.add("Inflammatory Markers")

        # --- Amylase: biliary/pancreatic workup if lipase present ---
        has_lipase = any(
            r.test_name == "Lipase"
            for p in panels for r in p.results
        )
        if has_lipase and "Amylase" not in added_panels:
            ref = NORMAL_LAB_RANGES.get("amylase")
            if ref:
                v = _validated_lab(lab_data.get("amylase"), ref)
                # If lipase is elevated but amylase not specified, elevate it
                lip_val = lab_data.get("lipase")
                if lip_val is not None and lab_data.get("amylase") is None:
                    try:
                        if float(lip_val) > 60:
                            v = round(rng.uniform(120, 350), 0)
                    except (ValueError, TypeError):
                        pass
                panels.append(LabPanel(
                    panel_name="Amylase", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=[LabResult(
                        test_name="Amylase", value=v, unit=ref["unit"],
                        reference_low=ref["low"], reference_high=ref["high"],
                        flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                    )],
                ))
                added_panels.add("Amylase")

        # --- Lactate: septic/shock without lactate already present ---
        has_lactate = any(
            r.test_name == "Lactate"
            for p in panels for r in p.results
        )
        if not has_lactate and acuity in ("septic", "shock") and is_ed_or_inpatient:
            ref = NORMAL_LAB_RANGES.get("lactate")
            if ref:
                if acuity == "shock":
                    v = round(rng.uniform(4.0, 8.0), 1)
                else:
                    v = round(rng.uniform(2.0, 4.5), 1)
                panels.append(LabPanel(
                    panel_name="Lactate", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=[LabResult(
                        test_name="Lactate", value=v, unit=ref["unit"],
                        reference_low=ref["low"], reference_high=ref["high"],
                        flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                    )],
                ))

        # --- D-dimer: if PE/DVT concern ---
        if any(k in dx_lower for k in ("embolism", "dvt", "thrombo")) and "D-dimer" not in added_panels:
            ref = NORMAL_LAB_RANGES.get("d_dimer")
            if ref:
                v = round(rng.uniform(1.0, 8.0), 2)
                panels.append(LabPanel(
                    panel_name="D-dimer", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=[LabResult(
                        test_name="D-dimer", value=v, unit=ref["unit"],
                        reference_low=ref["low"], reference_high=ref["high"],
                        flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                    )],
                ))

        # --- Magnesium: ED/inpatient (commonly ordered alongside CMP) ---
        if is_ed_or_inpatient and "Magnesium" not in added_panels:
            ref = NORMAL_LAB_RANGES.get("magnesium")
            if ref:
                v = _validated_lab(lab_data.get("magnesium"), ref)
                panels.append(LabPanel(
                    panel_name="Magnesium", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=[LabResult(
                        test_name="Magnesium", value=v, unit=ref["unit"],
                        reference_low=ref["low"], reference_high=ref["high"],
                        flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                    )],
                ))

        # --- HbA1c: if diabetic history (wouldn't be ordered every visit,
        #     but reasonable for an ED workup if diabetes in PMHx) ---
        has_dm = any(k in pmhx_text for k in ("diabetes", "dm", "a1c"))
        if has_dm and "HbA1c" not in added_panels and rng.random() < 0.6:
            ref = NORMAL_LAB_RANGES.get("hba1c")
            if ref:
                v = _validated_lab(lab_data.get("hba1c"), ref)
                # If no value provided and patient is diabetic, slightly elevated
                if lab_data.get("hba1c") is None:
                    v = round(rng.uniform(6.5, 9.0), 1)
                panels.append(LabPanel(
                    panel_name="HbA1c", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=[LabResult(
                        test_name="HbA1c", value=v, unit=ref["unit"],
                        reference_low=ref["low"], reference_high=ref["high"],
                        flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                    )],
                ))

        # --- BNP: if CHF history or cardiac concern ---
        has_cardiac = any(k in pmhx_text for k in ("heart failure", "chf", "cardiomyopathy"))
        if has_cardiac and "BNP" not in added_panels:
            ref = NORMAL_LAB_RANGES.get("bnp")
            if ref:
                v = round(rng.uniform(200, 800), 0)
                panels.append(LabPanel(
                    panel_name="BNP", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=[LabResult(
                        test_name="BNP", value=v, unit=ref["unit"],
                        reference_low=ref["low"], reference_high=ref["high"],
                        flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                    )],
                ))

        # --- TSH: if thyroid history ---
        has_thyroid = any(k in pmhx_text for k in ("thyroid", "hypothyroid", "hyperthyroid"))
        if has_thyroid and "TSH" not in added_panels:
            ref = NORMAL_LAB_RANGES.get("tsh")
            if ref:
                v = _validated_lab(lab_data.get("tsh"), ref)
                panels.append(LabPanel(
                    panel_name="TSH", timestamp=draw_time,
                    encounter_id=encounter_id, ordering_provider=attending,
                    results=[LabResult(
                        test_name="TSH", value=v, unit=ref["unit"],
                        reference_low=ref["low"], reference_high=ref["high"],
                        flag=flag_lab_value(v, ref), loinc_code=ref.get("loinc"),
                    )],
                ))

        return panels

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _summarize_labs(self, panels: list[LabPanel]) -> str:
        """Summarize lab results, highlighting abnormals."""
        if not panels:
            return "No labs available"
        abnormal = []
        for p in panels:
            for r in p.results:
                if r.flag:
                    abnormal.append(f"{r.test_name} {r.value} ({r.flag})")
        return "Abnormal: " + ", ".join(abnormal) if abnormal else "Labs within normal limits"

    def _build_prior_visit_summary(
        self, problem_list: list[ProblemListEntry],
        current_meds: list[Medication],
    ) -> str:
        """Build a summary of prior visits for the longitudinal HPI."""
        if not problem_list:
            return "No prior visits on record."

        lines = []
        for p in problem_list:
            if p.date_added:
                try:
                    dt = datetime.fromisoformat(p.date_added)
                    lines.append(f"- {p.condition} (diagnosed {dt.strftime('%B %Y')})")
                except ValueError:
                    lines.append(f"- {p.condition}")
            else:
                lines.append(f"- {p.condition}")

        if current_meds:
            med_str = ", ".join(f"{m.name} {m.dose}" for m in current_meds)
            lines.append(f"- Current medications: {med_str}")

        return "\n".join(lines)

    def _parse_radiology_report(self, text: str) -> dict:
        """Parse a radiology report into technique/findings/impression."""
        result = {"technique": "", "findings": "", "impression": ""}
        for key, pat in [
            ("technique", r"TECHNIQUE[:\s]*(.*?)(?=FINDINGS|IMPRESSION|$)"),
            ("findings", r"FINDINGS[:\s]*(.*?)(?=IMPRESSION|$)"),
            ("impression", r"IMPRESSION[:\s]*(.*?)$"),
        ]:
            m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
            if m:
                result[key] = m.group(1).strip()
        if not any(result.values()):
            result["findings"] = text.strip()
        return result
