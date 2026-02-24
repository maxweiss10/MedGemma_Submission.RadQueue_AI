"""
Clinical Knowledge Base for Synthetic EMR Generation.

Provides deterministic clinical reference data:
- Normal lab reference ranges with LOINC codes
- Lab panel definitions
- Normal vital sign ranges by acuity
- Common condition expansion maps with medications
- Medication formulary
- Synthetic demographic data pools
- GFR calculation
- Lab flag logic
"""

import random
from typing import Optional


# =============================================================================
# LAB REFERENCE RANGES
# =============================================================================

NORMAL_LAB_RANGES = {
    # Complete Blood Count (CBC)
    "wbc": {
        "low": 4.5, "high": 11.0, "unit": "x10^3/uL",
        "loinc": "6690-2", "critical_low": 2.0, "critical_high": 30.0,
    },
    "hemoglobin_male": {
        "low": 13.5, "high": 17.5, "unit": "g/dL",
        "loinc": "718-7", "critical_low": 7.0, "critical_high": 20.0,
    },
    "hemoglobin_female": {
        "low": 12.0, "high": 16.0, "unit": "g/dL",
        "loinc": "718-7", "critical_low": 7.0, "critical_high": 20.0,
    },
    "hematocrit_male": {
        "low": 38.0, "high": 50.0, "unit": "%",
        "loinc": "4544-3", "critical_low": 20.0, "critical_high": 60.0,
    },
    "hematocrit_female": {
        "low": 36.0, "high": 46.0, "unit": "%",
        "loinc": "4544-3", "critical_low": 20.0, "critical_high": 60.0,
    },
    "platelets": {
        "low": 150.0, "high": 400.0, "unit": "x10^3/uL",
        "loinc": "777-3", "critical_low": 50.0, "critical_high": 1000.0,
    },
    "mcv": {
        "low": 80.0, "high": 100.0, "unit": "fL",
        "loinc": "787-2",
    },
    "rdw": {
        "low": 11.5, "high": 14.5, "unit": "%",
        "loinc": "788-0",
    },
    # Comprehensive Metabolic Panel (CMP)
    "sodium": {
        "low": 136.0, "high": 145.0, "unit": "mEq/L",
        "loinc": "2951-2", "critical_low": 120.0, "critical_high": 160.0,
    },
    "potassium": {
        "low": 3.5, "high": 5.1, "unit": "mEq/L",
        "loinc": "2823-3", "critical_low": 2.5, "critical_high": 6.5,
    },
    "chloride": {
        "low": 98.0, "high": 106.0, "unit": "mEq/L",
        "loinc": "2075-0",
    },
    "co2": {
        "low": 23.0, "high": 29.0, "unit": "mEq/L",
        "loinc": "2028-9",
    },
    "bun": {
        "low": 7.0, "high": 20.0, "unit": "mg/dL",
        "loinc": "3094-0",
    },
    "creatinine_male": {
        "low": 0.7, "high": 1.3, "unit": "mg/dL",
        "loinc": "2160-0", "critical_high": 10.0,
    },
    "creatinine_female": {
        "low": 0.6, "high": 1.1, "unit": "mg/dL",
        "loinc": "2160-0", "critical_high": 10.0,
    },
    "glucose": {
        "low": 70.0, "high": 100.0, "unit": "mg/dL",
        "loinc": "2345-7", "critical_low": 40.0, "critical_high": 500.0,
    },
    "calcium": {
        "low": 8.5, "high": 10.5, "unit": "mg/dL",
        "loinc": "17861-6", "critical_low": 6.0, "critical_high": 13.0,
    },
    "albumin": {
        "low": 3.5, "high": 5.0, "unit": "g/dL",
        "loinc": "1751-7",
    },
    "total_protein": {
        "low": 6.0, "high": 8.3, "unit": "g/dL",
        "loinc": "2885-2",
    },
    # Liver Function Tests (LFT)
    "ast": {
        "low": 10.0, "high": 40.0, "unit": "U/L",
        "loinc": "1920-8",
    },
    "alt": {
        "low": 7.0, "high": 56.0, "unit": "U/L",
        "loinc": "1742-6",
    },
    "alp": {
        "low": 44.0, "high": 147.0, "unit": "U/L",
        "loinc": "6768-6",
    },
    "ggt": {
        "low": 9.0, "high": 48.0, "unit": "U/L",
        "loinc": "2324-2",
    },
    "bilirubin_total": {
        "low": 0.1, "high": 1.2, "unit": "mg/dL",
        "loinc": "1975-2",
    },
    "bilirubin_direct": {
        "low": 0.0, "high": 0.3, "unit": "mg/dL",
        "loinc": "1968-7",
    },
    # Pancreatic
    "lipase": {
        "low": 0.0, "high": 60.0, "unit": "U/L",
        "loinc": "3040-3",
    },
    "amylase": {
        "low": 28.0, "high": 100.0, "unit": "U/L",
        "loinc": "1798-8",
    },
    # Coagulation
    "inr": {
        "low": 0.8, "high": 1.1, "unit": "",
        "loinc": "6301-6", "critical_high": 5.0,
    },
    "pt": {
        "low": 11.0, "high": 13.5, "unit": "seconds",
        "loinc": "5902-2",
    },
    "ptt": {
        "low": 25.0, "high": 35.0, "unit": "seconds",
        "loinc": "3173-2", "critical_high": 100.0,
    },
    # Inflammatory markers
    "crp": {
        "low": 0.0, "high": 1.0, "unit": "mg/dL",
        "loinc": "1988-5",
    },
    "esr": {
        "low": 0.0, "high": 20.0, "unit": "mm/hr",
        "loinc": "4537-7",
    },
    "procalcitonin": {
        "low": 0.0, "high": 0.1, "unit": "ng/mL",
        "loinc": "75241-0",
    },
    "lactate": {
        "low": 0.5, "high": 2.0, "unit": "mmol/L",
        "loinc": "2524-7", "critical_high": 4.0,
    },
    # Cardiac
    "troponin_i": {
        "low": 0.0, "high": 0.04, "unit": "ng/mL",
        "loinc": "10839-9",
    },
    "bnp": {
        "low": 0.0, "high": 100.0, "unit": "pg/mL",
        "loinc": "30934-4",
    },
    # D-dimer
    "d_dimer": {
        "low": 0.0, "high": 500.0, "unit": "ng/mL",
        "loinc": "48065-7",
    },
    # Urinalysis
    "ua_wbc": {
        "low": 0.0, "high": 5.0, "unit": "/HPF",
        "loinc": "5821-4",
    },
    # Thyroid
    "tsh": {
        "low": 0.4, "high": 4.0, "unit": "mIU/L",
        "loinc": "3016-3",
    },
    # HbA1c
    "hba1c": {
        "low": 4.0, "high": 5.6, "unit": "%",
        "loinc": "4548-4",
    },
    # Magnesium
    "magnesium": {
        "low": 1.7, "high": 2.2, "unit": "mg/dL",
        "loinc": "19123-9",
    },
    # Phosphorus
    "phosphorus": {
        "low": 2.5, "high": 4.5, "unit": "mg/dL",
        "loinc": "2777-1",
    },
    # Iron Studies
    "iron": {
        "low": 60.0, "high": 170.0, "unit": "mcg/dL",
        "loinc": "2498-4",
    },
    "ferritin_male": {
        "low": 20.0, "high": 250.0, "unit": "ng/mL",
        "loinc": "2276-4",
    },
    "ferritin_female": {
        "low": 10.0, "high": 120.0, "unit": "ng/mL",
        "loinc": "2276-4",
    },
    "tibc": {
        "low": 250.0, "high": 370.0, "unit": "mcg/dL",
        "loinc": "2500-7",
    },
    # Vitamins
    "vitamin_d": {
        "low": 30.0, "high": 100.0, "unit": "ng/mL",
        "loinc": "1989-3",
    },
    "vitamin_b12": {
        "low": 200.0, "high": 900.0, "unit": "pg/mL",
        "loinc": "2132-9",
    },
    # Thyroid extended
    "free_t4": {
        "low": 0.8, "high": 1.8, "unit": "ng/dL",
        "loinc": "3024-7",
    },
    # Uric Acid
    "uric_acid": {
        "low": 3.0, "high": 7.0, "unit": "mg/dL",
        "loinc": "3084-1",
    },
}


# =============================================================================
# RXNORM CODES
# =============================================================================

RXNORM_CODES: dict[str, str] = {
    # Cardiovascular
    "Lisinopril": "29046",
    "Amlodipine": "17767",
    "Metoprolol Succinate": "866924",
    "Metoprolol Tartrate": "866508",
    "Losartan": "52175",
    "Hydrochlorothiazide": "5487",
    "Aspirin": "1191",
    "Clopidogrel": "32968",
    "Atorvastatin": "83367",
    "Rosuvastatin": "301542",
    "Simvastatin": "36567",
    # Endocrine
    "Metformin": "6809",
    "Glipizide": "4815",
    "Insulin Glargine": "274783",
    "Levothyroxine": "10582",
    # GI
    "Omeprazole": "7646",
    "Pantoprazole": "40790",
    "Esomeprazole": "283742",
    "Ondansetron": "26225",
    "Metoclopramide": "6915",
    "Famotidine": "4278",
    # Pain / Anti-inflammatory
    "Acetaminophen": "161",
    "Ibuprofen": "5640",
    "Ketorolac": "6095",
    "Toradol": "6095",
    "Morphine": "7052",
    "Hydromorphone": "3423",
    "Tramadol": "10689",
    "Naproxen": "7258",
    # Antibiotics
    "Ceftriaxone": "2193",
    "Piperacillin-Tazobactam": "684240",
    "Metronidazole": "6922",
    "Ciprofloxacin": "2551",
    "Amoxicillin": "723",
    "Azithromycin": "18631",
    "Cephalexin": "2231",
    "Cefepime": "25037",
    "Vancomycin": "11124",
    # Neurologic
    "Sumatriptan": "37418",
    "Topiramate": "38404",
    "Gabapentin": "25480",
    "Pregabalin": "187832",
    # Anticoagulants
    "Heparin": "5224",
    "Enoxaparin": "67108",
    "Warfarin": "11289",
    # Other common
    "Albuterol": "435",
    "Prednisone": "8640",
    "Furosemide": "4603",
    "Spironolactone": "9997",
    "Potassium Chloride": "8591",
}


def lookup_rxnorm(medication_name: str) -> Optional[str]:
    """Look up RxNorm code for a medication name (case-insensitive)."""
    if medication_name in RXNORM_CODES:
        return RXNORM_CODES[medication_name]
    name_lower = medication_name.lower()
    for key, code in RXNORM_CODES.items():
        if key.lower() == name_lower:
            return code
    return None


# =============================================================================
# LAB PANEL DEFINITIONS
# =============================================================================

LAB_PANELS = {
    "CBC": [
        "wbc", "hemoglobin", "hematocrit", "platelets", "mcv", "rdw",
    ],
    "BMP": [
        "sodium", "potassium", "chloride", "co2", "bun", "creatinine", "glucose", "calcium",
    ],
    "CMP": [
        "sodium", "potassium", "chloride", "co2", "bun", "creatinine", "glucose",
        "calcium", "albumin", "total_protein", "ast", "alt", "alp", "bilirubin_total",
    ],
    "LFT": [
        "ast", "alt", "alp", "ggt", "bilirubin_total", "bilirubin_direct",
        "albumin", "total_protein",
    ],
    "Hepatic Function Panel": [
        "ast", "alt", "alp", "bilirubin_total", "bilirubin_direct", "albumin",
    ],
    "Lipase": ["lipase"],
    "Amylase": ["amylase"],
    "Coagulation": ["inr", "pt", "ptt"],
    "Inflammatory Markers": ["crp", "esr", "procalcitonin"],
    "Lactate": ["lactate"],
    "Cardiac Markers": ["troponin_i", "bnp"],
    "D-dimer": ["d_dimer"],
    "Thyroid Panel": ["tsh"],
    "HbA1c": ["hba1c"],
    "Iron Studies": ["iron", "ferritin", "tibc"],
    "Uric Acid": ["uric_acid"],
}


# =============================================================================
# VITAL SIGN RANGES BY ACUITY
# =============================================================================

VITAL_RANGES = {
    "stable": {
        "temperature_f": (97.0, 99.5),
        "heart_rate": (60, 90),
        "blood_pressure_systolic": (110, 140),
        "blood_pressure_diastolic": (65, 90),
        "respiratory_rate": (14, 18),
        "oxygen_saturation": (97.0, 100.0),
        "pain_scale": (0, 3),
    },
    "mild": {
        "temperature_f": (98.0, 100.3),
        "heart_rate": (70, 100),
        "blood_pressure_systolic": (110, 150),
        "blood_pressure_diastolic": (65, 95),
        "respiratory_rate": (16, 20),
        "oxygen_saturation": (96.0, 100.0),
        "pain_scale": (3, 6),
    },
    "febrile": {
        "temperature_f": (100.4, 102.5),
        "heart_rate": (85, 110),
        "blood_pressure_systolic": (100, 145),
        "blood_pressure_diastolic": (60, 90),
        "respiratory_rate": (16, 22),
        "oxygen_saturation": (95.0, 99.0),
        "pain_scale": (5, 8),
    },
    "septic": {
        "temperature_f": (101.0, 104.0),
        "heart_rate": (100, 130),
        "blood_pressure_systolic": (80, 110),
        "blood_pressure_diastolic": (45, 65),
        "respiratory_rate": (20, 28),
        "oxygen_saturation": (90.0, 96.0),
        "pain_scale": (6, 10),
    },
    "shock": {
        "temperature_f": (96.0, 104.0),
        "heart_rate": (110, 150),
        "blood_pressure_systolic": (60, 95),
        "blood_pressure_diastolic": (30, 55),
        "respiratory_rate": (22, 34),
        "oxygen_saturation": (85.0, 95.0),
        "pain_scale": (7, 10),
    },
}


# =============================================================================
# CONDITION EXPANSION MAPS
# =============================================================================

CONDITION_EXPANSIONS = {
    "metabolic syndrome": {
        "conditions": [
            {"condition": "Type 2 Diabetes Mellitus", "icd10": "E11.9"},
            {"condition": "Essential Hypertension", "icd10": "I10"},
            {"condition": "Hyperlipidemia", "icd10": "E78.5"},
            {"condition": "Obesity", "icd10": "E66.01"},
        ],
        "medications": [
            {"name": "Metformin", "dose": "1000mg", "route": "PO", "frequency": "BID", "indication": "Type 2 DM"},
            {"name": "Lisinopril", "dose": "20mg", "route": "PO", "frequency": "daily", "indication": "Hypertension"},
            {"name": "Atorvastatin", "dose": "40mg", "route": "PO", "frequency": "daily", "indication": "Hyperlipidemia"},
        ],
    },
    "cardiovascular disease": {
        "conditions": [
            {"condition": "Coronary Artery Disease", "icd10": "I25.10"},
            {"condition": "Essential Hypertension", "icd10": "I10"},
            {"condition": "Hyperlipidemia", "icd10": "E78.5"},
        ],
        "medications": [
            {"name": "Aspirin", "dose": "81mg", "route": "PO", "frequency": "daily", "indication": "CAD"},
            {"name": "Metoprolol Succinate", "dose": "50mg", "route": "PO", "frequency": "daily", "indication": "CAD/HTN"},
            {"name": "Atorvastatin", "dose": "80mg", "route": "PO", "frequency": "daily", "indication": "Hyperlipidemia"},
            {"name": "Lisinopril", "dose": "10mg", "route": "PO", "frequency": "daily", "indication": "Hypertension"},
        ],
    },
    "hypertension": {
        "conditions": [
            {"condition": "Essential Hypertension", "icd10": "I10"},
        ],
        "medications": [
            {"name": "Amlodipine", "dose": "5mg", "route": "PO", "frequency": "daily", "indication": "Hypertension"},
        ],
    },
    "diabetes": {
        "conditions": [
            {"condition": "Type 2 Diabetes Mellitus", "icd10": "E11.9"},
        ],
        "medications": [
            {"name": "Metformin", "dose": "1000mg", "route": "PO", "frequency": "BID", "indication": "Type 2 DM"},
        ],
    },
    "obesity": {
        "conditions": [
            {"condition": "Obesity", "icd10": "E66.01"},
        ],
        "medications": [],
    },
    "copd": {
        "conditions": [
            {"condition": "Chronic Obstructive Pulmonary Disease", "icd10": "J44.1"},
        ],
        "medications": [
            {"name": "Tiotropium", "dose": "18mcg", "route": "INH", "frequency": "daily", "indication": "COPD"},
            {"name": "Albuterol", "dose": "90mcg", "route": "INH", "frequency": "PRN", "indication": "COPD"},
        ],
    },
    "chf": {
        "conditions": [
            {"condition": "Heart Failure with Reduced Ejection Fraction", "icd10": "I50.20"},
            {"condition": "Essential Hypertension", "icd10": "I10"},
        ],
        "medications": [
            {"name": "Carvedilol", "dose": "12.5mg", "route": "PO", "frequency": "BID", "indication": "HFrEF"},
            {"name": "Sacubitril-Valsartan", "dose": "49/51mg", "route": "PO", "frequency": "BID", "indication": "HFrEF"},
            {"name": "Spironolactone", "dose": "25mg", "route": "PO", "frequency": "daily", "indication": "HFrEF"},
            {"name": "Furosemide", "dose": "40mg", "route": "PO", "frequency": "daily", "indication": "Fluid overload"},
        ],
    },
    "ckd": {
        "conditions": [
            {"condition": "Chronic Kidney Disease, Stage 3", "icd10": "N18.3"},
        ],
        "medications": [
            {"name": "Sodium Bicarbonate", "dose": "650mg", "route": "PO", "frequency": "TID", "indication": "Metabolic acidosis"},
        ],
    },
    "atrial fibrillation": {
        "conditions": [
            {"condition": "Atrial Fibrillation", "icd10": "I48.91"},
        ],
        "medications": [
            {"name": "Apixaban", "dose": "5mg", "route": "PO", "frequency": "BID", "indication": "Atrial fibrillation"},
            {"name": "Metoprolol Succinate", "dose": "50mg", "route": "PO", "frequency": "daily", "indication": "Rate control"},
        ],
    },
    "gerd": {
        "conditions": [
            {"condition": "Gastroesophageal Reflux Disease", "icd10": "K21.0"},
        ],
        "medications": [
            {"name": "Omeprazole", "dose": "20mg", "route": "PO", "frequency": "daily", "indication": "GERD"},
        ],
    },
    "hypothyroidism": {
        "conditions": [
            {"condition": "Hypothyroidism", "icd10": "E03.9"},
        ],
        "medications": [
            {"name": "Levothyroxine", "dose": "75mcg", "route": "PO", "frequency": "daily", "indication": "Hypothyroidism"},
        ],
    },
    "depression": {
        "conditions": [
            {"condition": "Major Depressive Disorder", "icd10": "F32.9"},
        ],
        "medications": [
            {"name": "Sertraline", "dose": "100mg", "route": "PO", "frequency": "daily", "indication": "Depression"},
        ],
    },
    "anxiety": {
        "conditions": [
            {"condition": "Generalized Anxiety Disorder", "icd10": "F41.1"},
        ],
        "medications": [
            {"name": "Escitalopram", "dose": "10mg", "route": "PO", "frequency": "daily", "indication": "Anxiety"},
        ],
    },
    "asthma": {
        "conditions": [
            {"condition": "Asthma", "icd10": "J45.20"},
        ],
        "medications": [
            {"name": "Fluticasone-Salmeterol", "dose": "250/50mcg", "route": "INH", "frequency": "BID", "indication": "Asthma"},
            {"name": "Albuterol", "dose": "90mcg", "route": "INH", "frequency": "PRN", "indication": "Asthma rescue"},
        ],
    },
    "osteoarthritis": {
        "conditions": [
            {"condition": "Osteoarthritis", "icd10": "M19.90"},
        ],
        "medications": [
            {"name": "Acetaminophen", "dose": "500mg", "route": "PO", "frequency": "Q6H PRN", "indication": "Pain"},
        ],
    },
    "osa": {
        "conditions": [
            {"condition": "Obstructive Sleep Apnea", "icd10": "G47.33"},
        ],
        "medications": [],
    },
    "migraine": {
        "conditions": [
            {"condition": "Migraine", "icd10": "G43.909"},
        ],
        "medications": [
            {"name": "Sumatriptan", "dose": "50mg", "route": "PO", "frequency": "PRN", "indication": "Migraine"},
        ],
    },
    "ibs": {
        "conditions": [
            {"condition": "Irritable Bowel Syndrome", "icd10": "K58.9"},
        ],
        "medications": [
            {"name": "Dicyclomine", "dose": "20mg", "route": "PO", "frequency": "QID PRN", "indication": "IBS"},
        ],
    },
    "bph": {
        "conditions": [
            {"condition": "Benign Prostatic Hyperplasia", "icd10": "N40.0"},
        ],
        "medications": [
            {"name": "Tamsulosin", "dose": "0.4mg", "route": "PO", "frequency": "daily", "indication": "BPH"},
        ],
    },
    "nafld": {
        "conditions": [
            {"condition": "Non-Alcoholic Fatty Liver Disease", "icd10": "K76.0"},
        ],
        "medications": [],
    },
    "dvt": {
        "conditions": [
            {"condition": "Deep Vein Thrombosis", "icd10": "I82.40"},
        ],
        "medications": [
            {"name": "Rivaroxaban", "dose": "20mg", "route": "PO", "frequency": "daily", "indication": "Anticoagulation"},
        ],
    },
    "lupus": {
        "conditions": [
            {"condition": "Systemic Lupus Erythematosus", "icd10": "M32.9"},
        ],
        "medications": [
            {"name": "Hydroxychloroquine", "dose": "400mg", "route": "PO", "frequency": "daily", "indication": "SLE"},
        ],
    },
    "gout": {
        "conditions": [
            {"condition": "Gout", "icd10": "M10.9"},
        ],
        "medications": [
            {"name": "Allopurinol", "dose": "300mg", "route": "PO", "frequency": "daily", "indication": "Gout"},
        ],
    },
    "osteoporosis": {
        "conditions": [
            {"condition": "Osteoporosis", "icd10": "M81.0"},
        ],
        "medications": [
            {"name": "Alendronate", "dose": "70mg", "route": "PO", "frequency": "weekly", "indication": "Osteoporosis"},
            {"name": "Calcium + Vitamin D", "dose": "600mg/800IU", "route": "PO", "frequency": "daily", "indication": "Bone health"},
        ],
    },
    "peripheral arterial disease": {
        "conditions": [
            {"condition": "Peripheral Arterial Disease", "icd10": "I73.9"},
        ],
        "medications": [
            {"name": "Cilostazol", "dose": "100mg", "route": "PO", "frequency": "BID", "indication": "PAD"},
        ],
    },
    "fibromyalgia": {
        "conditions": [
            {"condition": "Fibromyalgia", "icd10": "M79.7"},
        ],
        "medications": [
            {"name": "Duloxetine", "dose": "60mg", "route": "PO", "frequency": "daily", "indication": "Fibromyalgia"},
        ],
    },
    "iron deficiency anemia": {
        "conditions": [
            {"condition": "Iron Deficiency Anemia", "icd10": "D50.9"},
        ],
        "medications": [
            {"name": "Ferrous Sulfate", "dose": "325mg", "route": "PO", "frequency": "daily", "indication": "Iron deficiency anemia"},
        ],
    },
    "diverticulosis": {
        "conditions": [
            {"condition": "Diverticulosis", "icd10": "K57.30"},
        ],
        "medications": [],
    },
    "kidney stones": {
        "conditions": [
            {"condition": "Nephrolithiasis", "icd10": "N20.0"},
        ],
        "medications": [],
    },
    "vitamin d deficiency": {
        "conditions": [
            {"condition": "Vitamin D Deficiency", "icd10": "E55.9"},
        ],
        "medications": [
            {"name": "Cholecalciferol", "dose": "2000 IU", "route": "PO", "frequency": "daily", "indication": "Vitamin D deficiency"},
        ],
    },
    "chronic pain": {
        "conditions": [
            {"condition": "Chronic Pain Syndrome", "icd10": "G89.29"},
        ],
        "medications": [
            {"name": "Gabapentin", "dose": "300mg", "route": "PO", "frequency": "TID", "indication": "Chronic pain"},
        ],
    },
    "dementia": {
        "conditions": [
            {"condition": "Dementia, Unspecified", "icd10": "F03.90"},
        ],
        "medications": [
            {"name": "Donepezil", "dose": "10mg", "route": "PO", "frequency": "daily", "indication": "Dementia"},
        ],
    },
    "neuropathy": {
        "conditions": [
            {"condition": "Peripheral Neuropathy", "icd10": "G62.9"},
        ],
        "medications": [
            {"name": "Gabapentin", "dose": "300mg", "route": "PO", "frequency": "TID", "indication": "Neuropathy"},
        ],
    },
}


# =============================================================================
# SYNTHETIC DEMOGRAPHIC DATA POOLS
# =============================================================================

FIRST_NAMES_FEMALE = [
    "Maria", "Jennifer", "Linda", "Patricia", "Elizabeth", "Barbara", "Susan",
    "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra",
    "Ashley", "Dorothy", "Kimberly", "Emily", "Donna", "Michelle", "Carol",
    "Amanda", "Melissa", "Deborah", "Stephanie", "Rebecca", "Sharon", "Laura",
    "Cynthia", "Kathleen", "Amy", "Angela", "Shirley", "Anna", "Brenda",
    "Pamela", "Emma", "Nicole", "Helen", "Samantha", "Katherine", "Christine",
    "Debra", "Rachel", "Carolyn", "Janet", "Catherine", "Maria", "Heather",
    "Diane", "Ruth", "Julie", "Olivia", "Joyce", "Virginia", "Victoria",
    "Kelly", "Lauren", "Christina", "Joan", "Evelyn", "Judith", "Megan",
    "Andrea", "Cheryl", "Hannah", "Jacqueline", "Martha", "Gloria", "Teresa",
    "Ann", "Sara", "Madison", "Frances", "Kathryn", "Janice", "Jean",
    "Abigail", "Alice", "Judy", "Sophia", "Grace", "Denise", "Amber",
    "Doris", "Marilyn", "Danielle", "Beverly", "Isabella", "Theresa", "Diana",
    "Natalie", "Brittany", "Charlotte", "Marie", "Kayla", "Alexis", "Lori",
    "Aisha", "Priya", "Wei", "Yuki", "Fatima", "Ingrid", "Olga", "Svetlana",
    "Guadalupe", "Carmen", "Rosa", "Lucia", "Ana", "Elena", "Sofia", "Valentina",
    "Mei", "Hana", "Suki", "Amara", "Zara", "Nadia", "Leila", "Yasmin",
]

FIRST_NAMES_MALE = [
    "James", "Robert", "John", "Michael", "David", "William", "Richard",
    "Joseph", "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony",
    "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth",
    "Kevin", "Brian", "George", "Timothy", "Ronald", "Edward", "Jason",
    "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan",
    "Stephen", "Larry", "Justin", "Scott", "Brandon", "Benjamin", "Samuel",
    "Raymond", "Gregory", "Frank", "Alexander", "Patrick", "Jack", "Dennis",
    "Jerry", "Tyler", "Aaron", "Jose", "Adam", "Nathan", "Henry", "Peter",
    "Zachary", "Douglas", "Harold", "Kyle", "Noah", "Gerald", "Keith",
    "Roger", "Arthur", "Terry", "Sean", "Christian", "Austin", "Jesse",
    "Dylan", "Bryan", "Joe", "Jordan", "Billy", "Bruce", "Albert",
    "Willie", "Gabriel", "Logan", "Alan", "Juan", "Wayne", "Elijah",
    "Randy", "Roy", "Vincent", "Ralph", "Eugene", "Russell", "Bobby",
    "Mason", "Philip", "Louis", "Carlos", "Miguel", "Antonio", "Alejandro",
    "Ahmed", "Raj", "Wei", "Hiroshi", "Omar", "Viktor", "Andrei", "Sergei",
    "Diego", "Ricardo", "Fernando", "Pablo", "Jorge", "Marco", "Liam",
    "Kwame", "Tariq", "Jamal", "Darius", "Kofi", "Abdul", "Hassan", "Ravi",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris",
    "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan",
    "Cooper", "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos",
    "Kim", "Cox", "Ward", "Richardson", "Watson", "Brooks", "Chavez",
    "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long",
    "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell",
    "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes", "Gonzales",
    "Chen", "Liu", "Wang", "Zhang", "Li", "Yang", "Wu", "Singh", "Kumar",
    "Sharma", "Tanaka", "Nakamura", "Sato", "Yamamoto", "Ivanov", "Petrov",
    "Kowalski", "Mueller", "Schmidt", "Fischer", "Weber", "O'Brien", "O'Connor",
    "McCarthy", "Sullivan", "MacDonald", "Ibrahim", "Ali", "Hassan", "Mohammed",
]

HOSPITAL_NAMES = [
    "Memorial General Hospital",
    "St. Mary's Medical Center",
    "University Hospital",
    "Mercy Regional Medical Center",
    "Community General Hospital",
    "Valley Medical Center",
    "Providence Health Center",
    "Lakeside Hospital",
    "Cedar Creek Medical Center",
    "Riverside Community Hospital",
    "Northside Regional Medical Center",
    "Oakwood General Hospital",
]

PROVIDER_NAMES = {
    "Emergency Medicine": [
        "Dr. Sarah Chen", "Dr. Michael Torres", "Dr. Amanda Patel",
        "Dr. Robert Kim", "Dr. Jennifer Walsh", "Dr. David Nakamura",
    ],
    "Internal Medicine": [
        "Dr. James Wilson", "Dr. Emily Rodriguez", "Dr. Thomas Park",
        "Dr. Lisa Hernandez", "Dr. Andrew Mitchell", "Dr. Rachel Green",
    ],
    "Surgery": [
        "Dr. Christopher Lee", "Dr. Maria Santos", "Dr. Brian O'Connor",
        "Dr. Patricia Nguyen", "Dr. William Chang", "Dr. Katherine Moore",
    ],
    "Radiology": [
        "Dr. Daniel Foster", "Dr. Susan Miller", "Dr. Kevin Shah",
        "Dr. Laura Thompson", "Dr. Mark Johnson", "Dr. Diane Williams",
    ],
    "Family Medicine": [
        "Dr. Steven Brown", "Dr. Nancy Davis", "Dr. Jeffrey Martin",
        "Dr. Karen Taylor", "Dr. Paul Anderson", "Dr. Michelle Clark",
    ],
    "Nursing": [
        "RN Jessica Adams", "RN David Lee", "RN Sarah Martinez",
        "RN Michael Johnson", "RN Emily Chen", "RN Amanda Wilson",
        "RN Robert Taylor", "RN Lisa Garcia", "RN James Brown",
        "RN Patricia Davis", "RN Christopher Moore", "RN Jennifer White",
    ],
    "Critical Care": [
        "Dr. Alexander Petrov", "Dr. Nicole Wang", "Dr. Benjamin Harris",
        "Dr. Stephanie Rivera", "Dr. Jonathan Kim", "Dr. Rebecca Chen",
    ],
    "Gastroenterology": [
        "Dr. Robert Chen", "Dr. Maria Hernandez", "Dr. James Liu",
        "Dr. Patricia Wong", "Dr. David Rivera", "Dr. Laura Kim",
    ],
    "Cardiology": [
        "Dr. Michael Park", "Dr. Sarah Thompson", "Dr. Andrew Chen",
        "Dr. Jennifer Lee", "Dr. Thomas Wilson", "Dr. Emily Patel",
    ],
    "Pulmonology": [
        "Dr. Richard Davis", "Dr. Nancy Kim", "Dr. Christopher Martinez",
        "Dr. Angela Foster", "Dr. Raymond Lee", "Dr. Deborah Chen",
    ],
    "Rheumatology": [
        "Dr. Stefan Mueller", "Dr. Priya Sharma", "Dr. Catherine Brooks",
        "Dr. Ryan Nakamura", "Dr. Diane Foster", "Dr. Kenneth Park",
    ],
    "Hematology": [
        "Dr. Marcus Johnson", "Dr. Linda Nguyen", "Dr. Gregory Adams",
        "Dr. Michelle Santos", "Dr. Brian O'Malley", "Dr. Sofia Rodriguez",
    ],
    "Urology": [
        "Dr. William Torres", "Dr. Helen Chang", "Dr. Anthony Petrov",
        "Dr. Rebecca Foster", "Dr. Daniel Kim", "Dr. Susan Miller",
    ],
    "OB/GYN": [
        "Dr. Patricia Santos", "Dr. Brian Mitchell", "Dr. Sofia Rodriguez",
        "Dr. Karen Lee", "Dr. David Foster", "Dr. Angela Chen",
    ],
    "Neurology": [
        "Dr. Daniel Park", "Dr. Rebecca Foster", "Dr. Jonathan Kim",
        "Dr. Lisa Hernandez", "Dr. Christopher Lee", "Dr. Amanda Chen",
    ],
}

INSURANCE_PLANS = [
    "Blue Cross Blue Shield PPO",
    "Aetna HMO",
    "UnitedHealthcare PPO",
    "Cigna Select",
    "Medicare Part A & B",
    "Medicaid",
    "Humana Gold Plus",
    "Kaiser Permanente",
    "Anthem Blue Cross",
    "Self-Pay",
]

RACES = [
    "White", "Black or African American", "Asian", "Hispanic or Latino",
    "American Indian or Alaska Native", "Native Hawaiian or Other Pacific Islander",
    "Two or More Races",
]

ETHNICITIES = ["Hispanic or Latino", "Not Hispanic or Latino"]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_lab_reference(test_name: str, sex: str = "Male") -> dict:
    """
    Get the reference range for a lab test, accounting for sex-specific ranges.

    Args:
        test_name: Lab test name (case-insensitive, matches keys in NORMAL_LAB_RANGES)
        sex: Patient sex ("Male" or "Female")

    Returns:
        Dict with low, high, unit, loinc, and optional critical values
    """
    key = test_name.lower().replace(" ", "_").replace(".", "_")

    # Check for sex-specific keys
    sex_key = f"{key}_{sex.lower()}"
    if sex_key in NORMAL_LAB_RANGES:
        return NORMAL_LAB_RANGES[sex_key]
    if key in NORMAL_LAB_RANGES:
        return NORMAL_LAB_RANGES[key]

    return None


def flag_lab_value(value: float, reference: dict) -> Optional[str]:
    """
    Determine the flag for a lab value based on reference range.

    Returns:
        "H" for high, "L" for low, "Critical" for critical, None for normal
    """
    if reference is None:
        return None

    critical_low = reference.get("critical_low")
    critical_high = reference.get("critical_high")

    if critical_low is not None and value < critical_low:
        return "Critical"
    if critical_high is not None and value > critical_high:
        return "Critical"
    if value < reference["low"]:
        return "L"
    if value > reference["high"]:
        return "H"
    return None


def calculate_gfr(creatinine: float, age: int, sex: str, race: Optional[str] = None) -> float:
    """
    Calculate estimated GFR using the CKD-EPI 2021 equation (race-free).

    Args:
        creatinine: Serum creatinine in mg/dL
        age: Patient age in years
        sex: "Male" or "Female"
        race: Not used in CKD-EPI 2021 (race-free)

    Returns:
        Estimated GFR in mL/min/1.73m2
    """
    if sex.lower() == "female":
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0

    cr_ratio = creatinine / kappa
    min_ratio = min(cr_ratio, 1.0)
    max_ratio = max(cr_ratio, 1.0)

    gfr = 142 * (min_ratio ** alpha) * (max_ratio ** (-1.200)) * (0.9938 ** age) * sex_factor
    return round(gfr, 1)


def generate_normal_value(reference: dict, rng: random.Random = None) -> float:
    """Generate a random value within the normal range."""
    if rng is None:
        rng = random.Random()
    low = reference["low"]
    high = reference["high"]
    # Use a value roughly centered in normal range with some spread
    mid = (low + high) / 2
    spread = (high - low) / 4
    value = rng.gauss(mid, spread)
    # Clamp to stay within normal
    value = max(low, min(high, value))
    return round(value, 1)


def expand_conditions(history_summary: str) -> tuple[list[dict], list[dict]]:
    """
    Expand shorthand condition descriptions into specific conditions and medications.

    Args:
        history_summary: Brief history string, e.g. "female, metabolic syndrome, GERD"

    Returns:
        Tuple of (conditions_list, medications_list) where each is a list of dicts
    """
    conditions = []
    medications = []
    seen_conditions = set()
    seen_medications = set()

    summary_lower = history_summary.lower()

    for key, expansion in CONDITION_EXPANSIONS.items():
        if key in summary_lower:
            for cond in expansion["conditions"]:
                if cond["condition"] not in seen_conditions:
                    conditions.append(cond)
                    seen_conditions.add(cond["condition"])
            for med in expansion["medications"]:
                if med["name"] not in seen_medications:
                    medications.append(med)
                    seen_medications.add(med["name"])

    return conditions, medications


def get_random_demographics(
    sex: Optional[str] = None,
    age: Optional[int] = None,
    rng: random.Random = None,
) -> dict:
    """
    Generate random patient demographics.

    Args:
        sex: Optional sex override ("Male" or "Female")
        age: Optional age override
        rng: Random number generator for reproducibility

    Returns:
        Dict with first_name, last_name, sex, age, race, ethnicity, etc.
    """
    if rng is None:
        rng = random.Random()

    if sex is None:
        sex = rng.choice(["Male", "Female"])

    if sex == "Female":
        first_name = rng.choice(FIRST_NAMES_FEMALE)
    else:
        first_name = rng.choice(FIRST_NAMES_MALE)

    last_name = rng.choice(LAST_NAMES)

    if age is None:
        age = rng.randint(25, 85)

    # Generate DOB from age
    current_year = datetime.now().year
    birth_year = current_year - age
    birth_month = rng.randint(1, 12)
    birth_day = rng.randint(1, 28)
    dob = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"

    mrn = f"MRN-{rng.randint(100000, 999999)}"

    race = rng.choice(RACES)
    ethnicity = rng.choice(ETHNICITIES)
    insurance = rng.choice(INSURANCE_PLANS)

    # Generate phone
    phone = f"({rng.randint(200, 999)}) {rng.randint(200, 999)}-{rng.randint(1000, 9999)}"

    # Emergency contact
    contact_first = rng.choice(FIRST_NAMES_FEMALE if sex == "Male" else FIRST_NAMES_MALE)
    contact_last = last_name
    relation = rng.choice(["Spouse", "Sibling", "Parent", "Child", "Partner"])
    contact_phone = f"({rng.randint(200, 999)}) {rng.randint(200, 999)}-{rng.randint(1000, 9999)}"
    emergency_contact = f"{contact_first} {contact_last} ({relation}) - {contact_phone}"

    return {
        "first_name": first_name,
        "last_name": last_name,
        "mrn": mrn,
        "date_of_birth": dob,
        "age": age,
        "sex": sex,
        "race": race,
        "ethnicity": ethnicity,
        "insurance": insurance,
        "phone": phone,
        "emergency_contact": emergency_contact,
    }


def get_random_provider(specialty: str, rng: random.Random = None) -> str:
    """Get a random provider name for a given specialty."""
    if rng is None:
        rng = random.Random()
    providers = PROVIDER_NAMES.get(specialty, PROVIDER_NAMES["Internal Medicine"])
    return rng.choice(providers)


def get_random_hospital(rng: random.Random = None) -> str:
    """Get a random hospital name."""
    if rng is None:
        rng = random.Random()
    return rng.choice(HOSPITAL_NAMES)


def get_random_nurse(rng: random.Random = None) -> str:
    """Get a random nursing staff name."""
    if rng is None:
        rng = random.Random()
    return rng.choice(PROVIDER_NAMES["Nursing"])


from datetime import datetime


# =============================================================================
# CONDITION PROGRESSION TEMPLATES (for longitudinal EMR generation)
# =============================================================================

CONDITION_PROGRESSIONS = {
    "metabolic_syndrome": {
        "timeline_years": 5,
        "stages": [
            {
                "year_offset": -5,
                "encounter_type": "outpatient_pcp",
                "reason": "Annual physical exam",
                "new_diagnoses": [],
                "new_medications": [],
                "lab_targets": {"glucose": (100, 115), "hba1c": (5.7, 6.0)},
                "vitals_bp_systolic": (130, 140),
                "note_template": "Annual exam. BMI elevated. Fasting glucose borderline. Counseled on diet and exercise.",
            },
            {
                "year_offset": -4,
                "encounter_type": "outpatient_pcp",
                "reason": "Follow-up blood pressure",
                "new_diagnoses": [
                    {"condition": "Obesity", "icd10": "E66.01"},
                    {"condition": "Essential Hypertension", "icd10": "I10"},
                ],
                "new_medications": [
                    {"name": "Amlodipine", "dose": "5mg", "route": "PO", "frequency": "daily", "indication": "Hypertension"},
                ],
                "lab_targets": {"glucose": (105, 120), "hba1c": (6.0, 6.4)},
                "vitals_bp_systolic": (135, 145),
                "note_template": "Follow-up. BP remains elevated. BMI 30.2. Started amlodipine. Lifestyle modifications reinforced.",
            },
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "New onset fatigue, lab follow-up",
                "new_diagnoses": [
                    {"condition": "Type 2 Diabetes Mellitus", "icd10": "E11.9"},
                    {"condition": "Hyperlipidemia", "icd10": "E78.5"},
                ],
                "new_medications": [
                    {"name": "Metformin", "dose": "500mg", "route": "PO", "frequency": "BID", "indication": "Type 2 DM"},
                    {"name": "Atorvastatin", "dose": "20mg", "route": "PO", "frequency": "daily", "indication": "Hyperlipidemia"},
                ],
                "lab_targets": {"glucose": (140, 180), "hba1c": (6.5, 7.0), "bun": (12, 18), "creatinine_male": (0.9, 1.1), "creatinine_female": (0.7, 0.9)},
                "note_template": "A1c 6.8%. Diagnosed T2DM. LDL 162. Started metformin 500mg BID and atorvastatin 20mg. Diabetic education referral placed.",
            },
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Diabetes follow-up",
                "new_diagnoses": [],
                "new_medications": [],
                "medication_changes": [
                    {"medication_name": "Metformin", "change_type": "Increased", "new_dose": "1000mg", "reason": "A1c above target"},
                ],
                "lab_targets": {"glucose": (130, 170), "hba1c": (7.0, 7.5)},
                "note_template": "A1c 7.2%. Increased metformin to 1000mg BID. BP well controlled on amlodipine. LDL improved to 118.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_pcp",
                "reason": "Annual physical",
                "new_diagnoses": [],
                "new_medications": [],
                "lab_targets": {"glucose": (120, 160), "hba1c": (6.8, 7.3)},
                "note_template": "Annual exam. Diabetes stable. A1c 6.9%. Continue current medications. Discussed importance of dietary compliance.",
            },
        ],
    },
    "cholelithiasis_to_cholecystitis": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "RUQ discomfort after meals",
                "new_diagnoses": [
                    {"condition": "Cholelithiasis", "icd10": "K80.20"},
                ],
                "new_medications": [],
                "generates_imaging": True,
                "imaging": {
                    "modality": "Ultrasound",
                    "body_region": "Abdomen",
                    "contrast": "without contrast",
                    "findings_template": "Gallbladder contains multiple small echogenic foci with posterior acoustic shadowing, consistent with cholelithiasis. No gallbladder wall thickening or pericholecystic fluid. Common bile duct measures 4mm, within normal limits. Liver parenchyma is homogeneous without focal lesions.",
                    "impression_template": "1. Cholelithiasis without evidence of cholecystitis. 2. No biliary ductal dilation.",
                },
                "note_template": "Patient reports intermittent RUQ pain after fatty meals for past month. US shows cholelithiasis. Discussed dietary modifications. Surgical referral placed.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_gi",
                "reason": "Surgical consultation for cholecystectomy",
                "new_diagnoses": [],
                "new_medications": [],
                "note_template": "Surgical consultation for symptomatic cholelithiasis. Symptoms intermittent, manageable with dietary modifications. Patient prefers conservative management at this time. Will proceed with elective cholecystectomy if symptoms worsen. Return precautions discussed.",
            },
        ],
    },
    "chronic_liver_disease": {
        "timeline_years": 5,
        "stages": [
            {
                "year_offset": -5,
                "encounter_type": "outpatient_pcp",
                "reason": "Routine screening",
                "new_diagnoses": [
                    {"condition": "Hepatitis C", "icd10": "B18.2"},
                ],
                "new_medications": [],
                "lab_targets": {"ast": (45, 65), "alt": (50, 80), "albumin": (3.5, 4.0), "bilirubin_total": (0.8, 1.2), "platelets": (150, 200)},
                "note_template": "Hep C antibody positive. HCV RNA quantitative confirms viremia. Genotype 1a. Referred to hepatology.",
            },
            {
                "year_offset": -4,
                "encounter_type": "outpatient_gi",
                "reason": "Hepatology consultation",
                "new_diagnoses": [],
                "new_medications": [
                    {"name": "Sofosbuvir/Velpatasvir", "dose": "400/100mg", "route": "PO", "frequency": "daily", "indication": "Hepatitis C"},
                ],
                "lab_targets": {"ast": (50, 70), "alt": (55, 85), "albumin": (3.3, 3.8)},
                "generates_imaging": True,
                "imaging": {
                    "modality": "Ultrasound",
                    "body_region": "Abdomen",
                    "contrast": "without contrast",
                    "findings_template": "Liver is coarsened in echotexture with nodular surface contour. No focal hepatic lesions. Spleen is mildly enlarged at 13.5 cm. No ascites.",
                    "impression_template": "1. Hepatic parenchymal disease consistent with cirrhosis. 2. Mild splenomegaly.",
                },
                "note_template": "Hepatology consult. FibroScan shows F3-F4 fibrosis. Initiated DAA therapy. Liver US with coarsened echotexture. HCC surveillance recommended.",
            },
            {
                "year_offset": -3,
                "encounter_type": "outpatient_gi",
                "reason": "HCV treatment completion, HCC surveillance",
                "new_diagnoses": [
                    {"condition": "Hepatic Cirrhosis", "icd10": "K74.60"},
                ],
                "new_medications": [],
                "lab_targets": {"ast": (35, 50), "alt": (30, 45), "albumin": (3.2, 3.6), "platelets": (120, 160)},
                "note_template": "SVR achieved. HCV RNA undetectable at 12 weeks post-treatment. Cirrhosis confirmed. Continue HCC surveillance with US/AFP every 6 months.",
            },
        ],
    },
    "ckd_progression": {
        "timeline_years": 4,
        "stages": [
            {
                "year_offset": -4,
                "encounter_type": "outpatient_pcp",
                "reason": "Routine labs - incidental finding",
                "new_diagnoses": [
                    {"condition": "Chronic Kidney Disease, Stage 2", "icd10": "N18.2"},
                ],
                "new_medications": [],
                "lab_targets": {"creatinine_male": (1.2, 1.4), "creatinine_female": (1.0, 1.2), "bun": (18, 24)},
                "gfr_target": (65, 75),
                "note_template": "Incidental finding of mildly elevated creatinine. eGFR 72. Started monitoring. Avoid nephrotoxic medications.",
            },
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "CKD follow-up",
                "new_diagnoses": [
                    {"condition": "Chronic Kidney Disease, Stage 3a", "icd10": "N18.31"},
                ],
                "new_medications": [],
                "lab_targets": {"creatinine_male": (1.4, 1.7), "creatinine_female": (1.2, 1.4), "bun": (22, 30)},
                "gfr_target": (50, 60),
                "note_template": "CKD progressing. eGFR 55. Referred to nephrology. Renal diet counseling. Medication review for nephrotoxins.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_specialist",
                "reason": "Nephrology consultation",
                "new_diagnoses": [
                    {"condition": "Chronic Kidney Disease, Stage 3b", "icd10": "N18.32"},
                ],
                "new_medications": [
                    {"name": "Sodium Bicarbonate", "dose": "650mg", "route": "PO", "frequency": "TID", "indication": "Metabolic acidosis"},
                ],
                "lab_targets": {"creatinine_male": (1.7, 2.2), "creatinine_female": (1.4, 1.8), "bun": (28, 38), "potassium": (4.5, 5.3), "co2": (18, 22)},
                "gfr_target": (35, 45),
                "note_template": "Nephrology consult. CKD Stage 3b. eGFR declining. Started sodium bicarbonate for metabolic acidosis. Avoid iodinated contrast if possible.",
            },
        ],
    },
    "peptic_ulcer_disease": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Epigastric pain",
                "new_diagnoses": [
                    {"condition": "Peptic Ulcer Disease", "icd10": "K27.9"},
                ],
                "new_medications": [
                    {"name": "Omeprazole", "dose": "40mg", "route": "PO", "frequency": "daily", "indication": "PUD"},
                ],
                "note_template": "Epigastric pain worsened by NSAIDs. H. pylori positive. Started PPI and triple therapy. Advised to avoid NSAIDs.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_pcp",
                "reason": "Follow-up, recurrent symptoms",
                "new_diagnoses": [],
                "new_medications": [],
                "note_template": "Recurrent epigastric symptoms despite PPI. Patient admits to ongoing NSAID use for arthritis. Counseled strongly on NSAID avoidance. Discussed alternative pain management.",
            },
        ],
    },
    "copd_progression": {
        "timeline_years": 4,
        "stages": [
            {
                "year_offset": -4,
                "encounter_type": "outpatient_pcp",
                "reason": "Chronic cough, dyspnea on exertion",
                "new_diagnoses": [
                    {"condition": "Chronic Obstructive Pulmonary Disease", "icd10": "J44.1"},
                ],
                "new_medications": [
                    {"name": "Tiotropium", "dose": "18mcg", "route": "INH", "frequency": "daily", "indication": "COPD"},
                    {"name": "Albuterol", "dose": "90mcg", "route": "INH", "frequency": "PRN", "indication": "COPD rescue"},
                ],
                "note_template": "PFTs show FEV1/FVC 0.62, FEV1 68% predicted. Diagnosed COPD, GOLD stage 2. Started LAMA. Smoking cessation counseling.",
            },
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "COPD follow-up, increased dyspnea",
                "new_diagnoses": [],
                "new_medications": [
                    {"name": "Fluticasone-Vilanterol", "dose": "100/25mcg", "route": "INH", "frequency": "daily", "indication": "COPD"},
                ],
                "note_template": "Increasing dyspnea with exertion. PFTs show FEV1 58% predicted. Added ICS/LABA combination. Pneumonia and influenza vaccines up to date.",
            },
        ],
    },
    "chf_progression": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "ed",
                "reason": "Dyspnea, lower extremity edema",
                "new_diagnoses": [
                    {"condition": "Heart Failure with Reduced Ejection Fraction", "icd10": "I50.20"},
                ],
                "new_medications": [
                    {"name": "Furosemide", "dose": "40mg", "route": "PO", "frequency": "daily", "indication": "Fluid overload"},
                    {"name": "Carvedilol", "dose": "6.25mg", "route": "PO", "frequency": "BID", "indication": "HFrEF"},
                    {"name": "Lisinopril", "dose": "5mg", "route": "PO", "frequency": "daily", "indication": "HFrEF"},
                ],
                "lab_targets": {"bnp": (400, 800)},
                "note_template": "ED visit for acute dyspnea and bilateral LE edema. CXR with pulmonary edema. Echo EF 35%. Diagnosed new HFrEF. IV diuresis with good response. Started GDMT.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_cardiology",
                "reason": "Cardiology follow-up",
                "new_diagnoses": [],
                "new_medications": [],
                "medication_changes": [
                    {"medication_name": "Carvedilol", "change_type": "Increased", "new_dose": "12.5mg", "reason": "Up-titration per GDMT"},
                    {"medication_name": "Lisinopril", "change_type": "Increased", "new_dose": "10mg", "reason": "Up-titration per GDMT"},
                ],
                "lab_targets": {"bnp": (150, 300)},
                "note_template": "Cardiology follow-up. EF improved to 40%. Symptoms stable on current regimen. Up-titrating beta-blocker and ACE-I per guidelines.",
            },
        ],
    },
    "pregnancy": {
        "timeline_years": 1,
        "stages": [
            {
                "year_offset": 0,
                "month_offset": -6,
                "encounter_type": "outpatient_specialist",
                "reason": "Initial prenatal visit",
                "new_diagnoses": [
                    {"condition": "Pregnancy, first trimester", "icd10": "Z34.01"},
                ],
                "new_medications": [
                    {"name": "Prenatal Vitamins", "dose": "1 tab", "route": "PO", "frequency": "daily", "indication": "Pregnancy"},
                ],
                "note_template": "Initial OB visit. Confirmed intrauterine pregnancy. Dating US consistent with 10 weeks. Routine prenatal labs drawn.",
            },
            {
                "year_offset": 0,
                "month_offset": -3,
                "encounter_type": "outpatient_specialist",
                "reason": "Second trimester visit",
                "new_diagnoses": [
                    {"condition": "Pregnancy, second trimester", "icd10": "Z34.02"},
                ],
                "new_medications": [],
                "note_template": "20-week anatomy scan normal. Fundal height appropriate for gestational age. No complications.",
            },
        ],
    },
    "atrial_fibrillation": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "ed",
                "reason": "Palpitations, irregular heartbeat",
                "new_diagnoses": [
                    {"condition": "Atrial Fibrillation", "icd10": "I48.91"},
                ],
                "new_medications": [
                    {"name": "Metoprolol Succinate", "dose": "25mg", "route": "PO", "frequency": "daily", "indication": "Rate control"},
                    {"name": "Apixaban", "dose": "5mg", "route": "PO", "frequency": "BID", "indication": "Stroke prevention"},
                ],
                "note_template": "ED visit for palpitations. ECG shows atrial fibrillation with RVR. Rate controlled with IV metoprolol. Started oral metoprolol and apixaban. CHA2DS2-VASc calculated.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_cardiology",
                "reason": "Cardiology follow-up, rate control",
                "new_diagnoses": [],
                "new_medications": [],
                "medication_changes": [
                    {"medication_name": "Metoprolol Succinate", "change_type": "Increased", "new_dose": "50mg", "reason": "Improved rate control"},
                ],
                "note_template": "Cardiology follow-up. Rate controlled, HR 70s on Holter. Increased metoprolol for better rate control. Continuing anticoagulation.",
            },
        ],
    },
    "gerd_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Heartburn, acid reflux",
                "new_diagnoses": [
                    {"condition": "Gastroesophageal Reflux Disease", "icd10": "K21.0"},
                ],
                "new_medications": [
                    {"name": "Omeprazole", "dose": "20mg", "route": "PO", "frequency": "daily", "indication": "GERD"},
                ],
                "note_template": "Chronic heartburn worsened by spicy foods and lying flat. Started PPI trial. Lifestyle modifications discussed including elevation of head of bed.",
            },
        ],
    },
    "hypothyroidism_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Fatigue, weight gain",
                "new_diagnoses": [
                    {"condition": "Hypothyroidism", "icd10": "E03.9"},
                ],
                "new_medications": [
                    {"name": "Levothyroxine", "dose": "50mcg", "route": "PO", "frequency": "daily", "indication": "Hypothyroidism"},
                ],
                "lab_targets": {"tsh": (8.0, 15.0)},
                "note_template": "TSH elevated at 10.2. Fatigue and 10 lb weight gain over 3 months. Started levothyroxine. Recheck TSH in 6 weeks.",
            },
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Thyroid follow-up",
                "new_diagnoses": [],
                "new_medications": [],
                "medication_changes": [
                    {"medication_name": "Levothyroxine", "change_type": "Increased", "new_dose": "75mcg", "reason": "TSH still above target"},
                ],
                "lab_targets": {"tsh": (4.5, 7.0)},
                "note_template": "TSH 5.8, still above target. Increased levothyroxine to 75mcg. Energy improving. Weight stable.",
            },
        ],
    },
    "cad_progression": {
        "timeline_years": 5,
        "stages": [
            {
                "year_offset": -5,
                "encounter_type": "outpatient_pcp",
                "reason": "Chest pain on exertion, elevated cholesterol",
                "new_diagnoses": [
                    {"condition": "Coronary Artery Disease", "icd10": "I25.10"},
                ],
                "new_medications": [
                    {"name": "Aspirin", "dose": "81mg", "route": "PO", "frequency": "daily", "indication": "CAD"},
                    {"name": "Metoprolol Succinate", "dose": "25mg", "route": "PO", "frequency": "daily", "indication": "CAD"},
                    {"name": "Atorvastatin", "dose": "80mg", "route": "PO", "frequency": "daily", "indication": "CAD"},
                ],
                "note_template": "Exertional chest tightness. Stress test with borderline ischemic changes. Lipid panel: LDL 185. Started aspirin, beta-blocker, high-intensity statin. Cardiology referral placed.",
            },
            {
                "year_offset": -3,
                "encounter_type": "outpatient_cardiology",
                "reason": "Cardiology follow-up, stress echocardiogram",
                "new_diagnoses": [],
                "new_medications": [
                    {"name": "Lisinopril", "dose": "10mg", "route": "PO", "frequency": "daily", "indication": "Cardioprotection"},
                ],
                "medication_changes": [
                    {"medication_name": "Metoprolol Succinate", "change_type": "Increased", "new_dose": "50mg", "reason": "Rate control optimization"},
                ],
                "generates_imaging": True,
                "imaging": {
                    "modality": "Echocardiogram",
                    "body_region": "Chest",
                    "contrast": "without contrast",
                    "findings_template": "LV systolic function is normal with estimated ejection fraction of 55%. Mild concentric LVH. No regional wall motion abnormalities. No significant valvular disease. Normal RV size and function.",
                    "impression_template": "1. Normal LV systolic function, EF 55%. 2. Mild concentric LV hypertrophy. 3. No significant valvular disease.",
                },
                "lab_targets": {"troponin_i": (0.0, 0.02), "bnp": (20, 80)},
                "note_template": "Cardiology follow-up. Stress echo without ischemia. EF 55%. LDL improved to 72 on high-intensity statin. Added ACE-I for cardioprotection. Continue current regimen.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_cardiology",
                "reason": "Annual cardiology follow-up",
                "new_diagnoses": [],
                "new_medications": [],
                "note_template": "Stable CAD. No anginal symptoms. BP and HR well controlled. Lipids at goal. Continue current medications. Annual follow-up.",
            },
        ],
    },
    "asthma_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Wheezing, shortness of breath",
                "new_diagnoses": [
                    {"condition": "Asthma", "icd10": "J45.20"},
                ],
                "new_medications": [
                    {"name": "Albuterol", "dose": "90mcg", "route": "INH", "frequency": "PRN", "indication": "Asthma rescue"},
                    {"name": "Fluticasone", "dose": "110mcg", "route": "INH", "frequency": "BID", "indication": "Asthma controller"},
                ],
                "generates_imaging": True,
                "imaging": {
                    "modality": "X-ray",
                    "body_region": "Chest",
                    "contrast": "without contrast",
                    "findings_template": "Lungs are clear bilaterally. No infiltrate, effusion, or pneumothorax. Heart size is normal. Mediastinal contours are unremarkable.",
                    "impression_template": "1. No acute cardiopulmonary disease.",
                },
                "note_template": "Recurrent wheezing and dyspnea on exertion. CXR clear. PFTs show reversible obstruction. Diagnosed asthma. Started ICS + SABA. Asthma action plan provided.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_pulmonology",
                "reason": "Asthma follow-up, PFTs",
                "new_diagnoses": [],
                "new_medications": [],
                "note_template": "Asthma well controlled on current regimen. PFTs improved. Occasional SABA use. Continue ICS. Return in 6 months.",
            },
        ],
    },
    "osa_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Excessive daytime sleepiness, snoring",
                "new_diagnoses": [
                    {"condition": "Obstructive Sleep Apnea", "icd10": "G47.33"},
                ],
                "new_medications": [],
                "note_template": "Loud snoring per bed partner, witnessed apneas, Epworth score 14. BMI elevated. Sleep study referral placed. Diagnosed severe OSA, AHI 32. CPAP initiated.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_pcp",
                "reason": "OSA follow-up, CPAP compliance",
                "new_diagnoses": [],
                "new_medications": [],
                "note_template": "CPAP follow-up. Good compliance (avg 6.2 hrs/night). Epworth improved to 6. Daytime sleepiness resolved. Continue CPAP. Weight management counseling.",
            },
        ],
    },
    "anxiety_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Palpitations, insomnia, worry",
                "new_diagnoses": [
                    {"condition": "Generalized Anxiety Disorder", "icd10": "F41.1"},
                ],
                "new_medications": [
                    {"name": "Escitalopram", "dose": "10mg", "route": "PO", "frequency": "daily", "indication": "Anxiety"},
                ],
                "note_template": "Chronic worry, difficulty sleeping, palpitations. GAD-7 score 15. No cardiac etiology. Diagnosed GAD. Started SSRI. Counseling referral placed.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_pcp",
                "reason": "Anxiety follow-up",
                "new_diagnoses": [],
                "new_medications": [],
                "note_template": "GAD-7 improved to 8. Sleeping better. Continue escitalopram 10mg. Engaged in CBT. No dose adjustment needed at this time.",
            },
        ],
    },
    "depression_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Low mood, fatigue, poor concentration",
                "new_diagnoses": [
                    {"condition": "Major Depressive Disorder", "icd10": "F32.9"},
                ],
                "new_medications": [
                    {"name": "Sertraline", "dose": "50mg", "route": "PO", "frequency": "daily", "indication": "Depression"},
                ],
                "note_template": "PHQ-9 score 16. Low mood, anhedonia, poor sleep for 3 months. No SI/HI. Diagnosed MDD. Started sertraline 50mg. Safety plan discussed. Follow-up in 4 weeks.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_pcp",
                "reason": "Depression follow-up",
                "new_diagnoses": [],
                "new_medications": [],
                "medication_changes": [
                    {"medication_name": "Sertraline", "change_type": "Increased", "new_dose": "100mg", "reason": "Partial response, dose optimization"},
                ],
                "note_template": "PHQ-9 improved to 10. Partial response to sertraline. Increased to 100mg. Tolerating well. Continue counseling. No SI/HI.",
            },
        ],
    },
    "migraine_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Recurrent headaches",
                "new_diagnoses": [
                    {"condition": "Migraine without Aura", "icd10": "G43.909"},
                ],
                "new_medications": [
                    {"name": "Sumatriptan", "dose": "50mg", "route": "PO", "frequency": "PRN", "indication": "Migraine abortive"},
                ],
                "note_template": "Recurrent unilateral throbbing headaches with photophobia, nausea, 3-4x/month. Diagnosed migraine without aura. Started sumatriptan PRN. Headache diary initiated.",
            },
            {
                "year_offset": -2,
                "encounter_type": "outpatient_neurology",
                "reason": "Migraine follow-up, prophylaxis evaluation",
                "new_diagnoses": [],
                "new_medications": [
                    {"name": "Topiramate", "dose": "25mg", "route": "PO", "frequency": "BID", "indication": "Migraine prophylaxis"},
                ],
                "generates_imaging": True,
                "imaging": {
                    "modality": "MRI",
                    "body_region": "Head",
                    "contrast": "without contrast",
                    "findings_template": "Brain parenchyma demonstrates normal signal intensity. No intracranial mass, hemorrhage, or acute infarct. Ventricles and sulci are normal in size. No midline shift.",
                    "impression_template": "1. Normal MRI brain. No intracranial abnormality.",
                },
                "note_template": "Neurology consult. Migraine frequency 4/month despite abortive therapy. MRI brain normal. Started prophylactic topiramate. Migraine lifestyle modifications discussed.",
            },
        ],
    },
    "osteoarthritis_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Joint pain, stiffness",
                "new_diagnoses": [
                    {"condition": "Osteoarthritis", "icd10": "M19.90"},
                ],
                "new_medications": [
                    {"name": "Acetaminophen", "dose": "500mg", "route": "PO", "frequency": "Q6H PRN", "indication": "Pain"},
                ],
                "generates_imaging": True,
                "imaging": {
                    "modality": "X-ray",
                    "body_region": "Knee",
                    "contrast": "without contrast",
                    "findings_template": "Moderate joint space narrowing of the medial compartment. Marginal osteophyte formation. No fracture or dislocation. Soft tissues unremarkable.",
                    "impression_template": "1. Moderate degenerative changes consistent with osteoarthritis.",
                },
                "note_template": "Bilateral knee pain worse with stairs and prolonged standing. X-ray shows moderate OA. Started acetaminophen PRN. Physical therapy referral. Weight loss counseling.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_pcp",
                "reason": "OA follow-up, ongoing pain",
                "new_diagnoses": [],
                "new_medications": [
                    {"name": "Meloxicam", "dose": "7.5mg", "route": "PO", "frequency": "daily", "indication": "Osteoarthritis"},
                ],
                "note_template": "Persistent knee pain despite acetaminophen and PT. Added low-dose NSAID. Discussed knee injection options. Orthopedic referral if not improving.",
            },
        ],
    },
    "nafld_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Elevated liver enzymes on routine labs",
                "new_diagnoses": [
                    {"condition": "Non-Alcoholic Fatty Liver Disease", "icd10": "K76.0"},
                ],
                "new_medications": [],
                "generates_imaging": True,
                "imaging": {
                    "modality": "Ultrasound",
                    "body_region": "Abdomen",
                    "contrast": "without contrast",
                    "findings_template": "Liver demonstrates increased echogenicity consistent with hepatic steatosis. No focal hepatic lesions. Gallbladder is normal. No biliary ductal dilation.",
                    "impression_template": "1. Hepatic steatosis. 2. No focal hepatic lesion.",
                },
                "lab_targets": {"ast": (42, 58), "alt": (48, 72), "alp": (80, 130)},
                "note_template": "Incidentally elevated LFTs on routine labs. US shows hepatic steatosis. Viral hepatitis serologies negative. Diagnosed NAFLD. Weight loss and exercise counseling. Repeat LFTs in 3 months.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_gi",
                "reason": "NAFLD follow-up, trending LFTs",
                "new_diagnoses": [],
                "new_medications": [],
                "lab_targets": {"ast": (38, 52), "alt": (42, 65)},
                "note_template": "GI follow-up for NAFLD. LFTs trending down with lifestyle modifications. FIB-4 score low risk. Continue weight management. Repeat labs in 6 months.",
            },
        ],
    },
    "dvt_pe_history": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "ed",
                "reason": "Leg swelling, dyspnea",
                "new_diagnoses": [
                    {"condition": "Deep Vein Thrombosis", "icd10": "I82.40"},
                ],
                "new_medications": [
                    {"name": "Rivaroxaban", "dose": "15mg", "route": "PO", "frequency": "BID", "indication": "DVT treatment"},
                ],
                "generates_imaging": True,
                "imaging": {
                    "modality": "Ultrasound",
                    "body_region": "Lower Extremity",
                    "contrast": "without contrast",
                    "findings_template": "Non-compressible thrombus identified within the left common femoral and popliteal veins. Flow is absent in the affected segments. Right lower extremity veins are patent.",
                    "impression_template": "1. Acute deep vein thrombosis of the left common femoral and popliteal veins.",
                },
                "note_template": "ED visit for acute left leg swelling and dyspnea. D-dimer elevated. US confirms DVT. CTA negative for PE. Started rivaroxaban. Hypercoagulability workup ordered.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_hematology",
                "reason": "Hematology follow-up, anticoagulation management",
                "new_diagnoses": [],
                "new_medications": [],
                "medication_changes": [
                    {"medication_name": "Rivaroxaban", "change_type": "Changed", "new_dose": "20mg daily", "reason": "Transition to maintenance dosing"},
                ],
                "note_template": "Hematology follow-up. DVT resolved on repeat US. Hypercoagulability workup pending. Transitioned to maintenance anticoagulation. Plan for minimum 6 months total therapy.",
            },
        ],
    },
    "lupus_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Joint pain, facial rash, fatigue",
                "new_diagnoses": [],
                "new_medications": [],
                "lab_targets": {"esr": (35, 55), "crp": (1.5, 3.0)},
                "note_template": "Butterfly facial rash, polyarthralgia, fatigue. ANA positive 1:320. Referred to rheumatology for evaluation.",
            },
            {
                "year_offset": -2,
                "encounter_type": "outpatient_rheumatology",
                "reason": "Rheumatology evaluation for SLE",
                "new_diagnoses": [
                    {"condition": "Systemic Lupus Erythematosus", "icd10": "M32.9"},
                ],
                "new_medications": [
                    {"name": "Hydroxychloroquine", "dose": "400mg", "route": "PO", "frequency": "daily", "indication": "SLE"},
                ],
                "lab_targets": {"esr": (30, 45), "crp": (1.2, 2.5)},
                "note_template": "Rheumatology consult. Meets ACR criteria for SLE: malar rash, arthritis, positive ANA/anti-dsDNA. Started hydroxychloroquine. Baseline ophthalmology referral. Sun protection counseling.",
            },
        ],
    },
    "kidney_stones_history": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "ed",
                "reason": "Acute flank pain, hematuria",
                "new_diagnoses": [
                    {"condition": "Nephrolithiasis", "icd10": "N20.0"},
                ],
                "new_medications": [],
                "generates_imaging": True,
                "imaging": {
                    "modality": "CT",
                    "body_region": "Abdomen and Pelvis",
                    "contrast": "without contrast",
                    "findings_template": "A 6mm calculus is identified at the right ureterovesical junction with mild proximal hydroureteronephrosis. No other calculi identified. No free fluid.",
                    "impression_template": "1. 6mm right distal ureteral calculus with mild hydroureteronephrosis.",
                },
                "note_template": "ED visit for acute right flank pain with hematuria. CT shows 6mm distal ureteral stone. IV fluids and pain management. Stone likely to pass. Urology follow-up.",
            },
        ],
    },
    "pad_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Calf pain with walking, claudication",
                "new_diagnoses": [
                    {"condition": "Peripheral Arterial Disease", "icd10": "I73.9"},
                ],
                "new_medications": [
                    {"name": "Cilostazol", "dose": "100mg", "route": "PO", "frequency": "BID", "indication": "PAD/claudication"},
                ],
                "note_template": "Bilateral calf claudication, walking distance limited to 2 blocks. ABI 0.72 right, 0.68 left. Diagnosed PAD. Started cilostazol. Smoking cessation. Supervised exercise program referral.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_specialist",
                "reason": "Vascular surgery follow-up",
                "new_diagnoses": [],
                "new_medications": [],
                "note_template": "Vascular follow-up. Claudication improved with cilostazol and exercise. ABI stable. No rest pain or tissue loss. Continue medical management. Annual surveillance.",
            },
        ],
    },
    "bph_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Urinary frequency, nocturia",
                "new_diagnoses": [
                    {"condition": "Benign Prostatic Hyperplasia", "icd10": "N40.0"},
                ],
                "new_medications": [
                    {"name": "Tamsulosin", "dose": "0.4mg", "route": "PO", "frequency": "daily", "indication": "BPH"},
                ],
                "note_template": "Urinary frequency, nocturia x3, weak stream. IPSS score 18. DRE: enlarged prostate, no nodules. PSA 2.8. Started alpha-blocker. Urology referral if not improving.",
            },
        ],
    },
    "ibs_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Abdominal cramping, alternating bowel habits",
                "new_diagnoses": [
                    {"condition": "Irritable Bowel Syndrome", "icd10": "K58.9"},
                ],
                "new_medications": [
                    {"name": "Dicyclomine", "dose": "20mg", "route": "PO", "frequency": "QID PRN", "indication": "IBS"},
                ],
                "note_template": "Chronic abdominal cramping with alternating diarrhea and constipation. Alarm features absent. CBC, celiac panel, CRP all normal. Diagnosed IBS per Rome IV criteria. Started antispasmodic. Dietary counseling.",
            },
        ],
    },
    "gout_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Acute great toe swelling and pain",
                "new_diagnoses": [
                    {"condition": "Gout", "icd10": "M10.9"},
                ],
                "new_medications": [
                    {"name": "Allopurinol", "dose": "100mg", "route": "PO", "frequency": "daily", "indication": "Gout prophylaxis"},
                    {"name": "Colchicine", "dose": "0.6mg", "route": "PO", "frequency": "BID PRN", "indication": "Gout flare"},
                ],
                "lab_targets": {"uric_acid": (8.0, 10.5)},
                "note_template": "Acute 1st MTP joint inflammation. Uric acid 9.2. Diagnosed gout. Treated acute flare with colchicine. Started allopurinol for prophylaxis. Dietary counseling on purine-rich foods.",
            },
        ],
    },
    "diverticulosis_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_gi",
                "reason": "Screening colonoscopy",
                "new_diagnoses": [
                    {"condition": "Diverticulosis", "icd10": "K57.30"},
                ],
                "new_medications": [],
                "note_template": "Screening colonoscopy at age-appropriate interval. Multiple diverticula in sigmoid colon, non-inflamed. No polyps. Diagnosed diverticulosis. High-fiber diet recommended. Repeat colonoscopy in 10 years.",
            },
        ],
    },
    "fibromyalgia_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Widespread body pain, fatigue",
                "new_diagnoses": [
                    {"condition": "Fibromyalgia", "icd10": "M79.7"},
                ],
                "new_medications": [
                    {"name": "Duloxetine", "dose": "30mg", "route": "PO", "frequency": "daily", "indication": "Fibromyalgia"},
                ],
                "note_template": "Chronic widespread pain, multiple tender points, fatigue, sleep disturbance. Labs unremarkable (ESR, CRP, TSH, CBC all normal). Diagnosed fibromyalgia. Started duloxetine. Exercise program recommended.",
            },
        ],
    },
    "iron_deficiency_anemia": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Fatigue, pallor",
                "new_diagnoses": [
                    {"condition": "Iron Deficiency Anemia", "icd10": "D50.9"},
                ],
                "new_medications": [
                    {"name": "Ferrous Sulfate", "dose": "325mg", "route": "PO", "frequency": "daily", "indication": "Iron deficiency anemia"},
                ],
                "lab_targets": {"hemoglobin_female": (9.5, 11.0), "hemoglobin_male": (11.0, 12.5)},
                "note_template": "Fatigue and pallor. Hemoglobin 10.2. Iron studies: low ferritin, low iron, elevated TIBC. Diagnosed iron deficiency anemia. Started oral iron. GI evaluation for occult blood loss.",
            },
        ],
    },
    "osteoporosis_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "DEXA screening, bone health",
                "new_diagnoses": [
                    {"condition": "Osteoporosis", "icd10": "M81.0"},
                ],
                "new_medications": [
                    {"name": "Alendronate", "dose": "70mg", "route": "PO", "frequency": "weekly", "indication": "Osteoporosis"},
                    {"name": "Calcium + Vitamin D", "dose": "600mg/800IU", "route": "PO", "frequency": "daily", "indication": "Bone health"},
                ],
                "note_template": "DEXA screening. T-score -2.8 at lumbar spine. Diagnosed osteoporosis. Started bisphosphonate and calcium/vitamin D. Fall prevention counseling. Weight-bearing exercise encouraged.",
            },
        ],
    },
    "alcohol_use_disorder": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Alcohol screening, elevated GGT",
                "new_diagnoses": [
                    {"condition": "Alcohol Use Disorder", "icd10": "F10.20"},
                ],
                "new_medications": [],
                "lab_targets": {"ggt": (55, 120), "ast": (45, 65)},
                "note_template": "AUDIT-C score elevated. Patient acknowledges heavy drinking. CAGE 2/4. Elevated GGT. Counseled on alcohol cessation. Offered naltrexone, patient declined. AA referral provided.",
            },
        ],
    },
    "prediabetes_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_pcp",
                "reason": "Routine labs, elevated fasting glucose",
                "new_diagnoses": [
                    {"condition": "Prediabetes", "icd10": "R73.03"},
                ],
                "new_medications": [],
                "lab_targets": {"glucose": (105, 120), "hba1c": (5.7, 6.4)},
                "note_template": "Fasting glucose 112, A1c 6.1%. Diagnosed prediabetes. Intensive lifestyle counseling: weight loss 5-7%, 150 min/week moderate exercise. Repeat A1c in 6 months.",
            },
        ],
    },
    "pcos_standalone": {
        "timeline_years": 2,
        "stages": [
            {
                "year_offset": -2,
                "encounter_type": "outpatient_obgyn",
                "reason": "Irregular periods, hirsutism",
                "new_diagnoses": [
                    {"condition": "Polycystic Ovary Syndrome", "icd10": "E28.2"},
                ],
                "new_medications": [
                    {"name": "Oral Contraceptive", "dose": "1 tab", "route": "PO", "frequency": "daily", "indication": "PCOS/menstrual regulation"},
                ],
                "note_template": "Irregular menses, hirsutism, BMI elevated. Labs: elevated androgens, LH/FSH ratio >2. US: bilateral ovarian cysts. Diagnosed PCOS. Started OCP for menstrual regulation. Metformin discussed.",
            },
        ],
    },
    "dementia_standalone": {
        "timeline_years": 3,
        "stages": [
            {
                "year_offset": -3,
                "encounter_type": "outpatient_pcp",
                "reason": "Memory concerns, cognitive decline",
                "new_diagnoses": [
                    {"condition": "Dementia, Unspecified", "icd10": "F03.90"},
                ],
                "new_medications": [
                    {"name": "Donepezil", "dose": "5mg", "route": "PO", "frequency": "daily", "indication": "Dementia"},
                ],
                "note_template": "Family reports progressive memory loss over 12 months. MMSE 22/30. Difficulty with IADLs. Basic metabolic workup normal. TSH, B12 normal. Started cholinesterase inhibitor.",
            },
            {
                "year_offset": -1,
                "encounter_type": "outpatient_neurology",
                "reason": "Neurology follow-up, cognitive assessment",
                "new_diagnoses": [],
                "new_medications": [],
                "medication_changes": [
                    {"medication_name": "Donepezil", "change_type": "Increased", "new_dose": "10mg", "reason": "Tolerated well, dose optimization"},
                ],
                "note_template": "Neurology follow-up. MMSE stable at 21. Increased donepezil to 10mg. Caregiver support discussed. Advanced directives addressed.",
            },
        ],
    },
}


# =============================================================================
# LAB PANELS BY ENCOUNTER TYPE
# =============================================================================

LAB_PANELS_BY_ENCOUNTER_TYPE = {
    "annual_physical": ["CBC", "CMP"],
    "dm_followup": ["HbA1c", "CMP"],
    "ckd_followup": ["CMP", "CBC"],
    "htn_followup": ["BMP"],
    "thyroid_followup": ["Thyroid Panel"],
    "lipid_followup": ["CMP"],
    "hep_followup": ["LFT", "CBC"],
    "cardiology_followup": ["BMP", "Cardiac Markers"],
    "ed_abdominal": ["CBC", "CMP", "LFT", "Lipase"],
    "ed_abdominal_with_lactate": ["CBC", "CMP", "LFT", "Lipase", "Lactate"],
    "ed_cardiac": ["CBC", "CMP", "Cardiac Markers"],
    "ed_general": ["CBC", "CMP"],
    "preop": ["CBC", "CMP", "Coagulation"],
    "prenatal": ["CBC", "CMP"],
    "icu": ["CBC", "CMP", "LFT", "Lactate", "Coagulation"],
    "cardiology_clinic": ["CBC", "CMP", "Cardiac Markers"],
    "rheumatology_clinic": ["CBC", "CMP", "Inflammatory Markers"],
    "hematology_clinic": ["CBC", "CMP", "Coagulation"],
    "pulmonology_clinic": ["CBC", "BMP"],
    "gi_clinic": ["CBC", "CMP", "LFT"],
    "neurology_clinic": ["BMP"],
    "urology_clinic": ["BMP"],
    "ed_dvt_pe": ["CBC", "CMP", "D-dimer", "Coagulation"],
    "iron_studies": ["CBC", "CMP", "Iron Studies"],
}


# =============================================================================
# ENCOUNTER TYPE PROFILES
# =============================================================================

ENCOUNTER_TYPE_PROFILES = {
    "outpatient_pcp": {
        "encounter_type": "Outpatient",
        "department": "Primary Care",
        "provider_specialty": "Family Medicine",
        "duration_hours": (0.33, 0.75),  # 20-45 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "outpatient_specialist": {
        "encounter_type": "Outpatient",
        "department": "Specialty Clinic",
        "provider_specialty": "Internal Medicine",
        "duration_hours": (0.33, 0.83),  # 20-50 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "ed": {
        "encounter_type": "ED",
        "department": "Emergency Department",
        "provider_specialty": "Emergency Medicine",
        "duration_hours": 6,
        "vitals_count": 2,
        "disposition": "Admitted to Medicine",
    },
    "inpatient": {
        "encounter_type": "Inpatient",
        "department": "Medical Floor",
        "provider_specialty": "Internal Medicine",
        "duration_hours": 72,
        "vitals_count": 4,
        "disposition": "Discharged",
    },
    "icu": {
        "encounter_type": "Inpatient",
        "department": "Intensive Care Unit",
        "provider_specialty": "Critical Care",
        "duration_hours": 120,
        "vitals_count": 6,
        "disposition": "Transferred to floor",
    },
    "outpatient_cardiology": {
        "encounter_type": "Outpatient",
        "department": "Cardiology Clinic",
        "provider_specialty": "Cardiology",
        "duration_hours": (0.33, 0.75),  # 20-45 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "outpatient_gi": {
        "encounter_type": "Outpatient",
        "department": "Gastroenterology Clinic",
        "provider_specialty": "Gastroenterology",
        "duration_hours": (0.33, 0.83),  # 20-50 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "outpatient_pulmonology": {
        "encounter_type": "Outpatient",
        "department": "Pulmonology Clinic",
        "provider_specialty": "Pulmonology",
        "duration_hours": (0.33, 0.75),  # 20-45 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "outpatient_rheumatology": {
        "encounter_type": "Outpatient",
        "department": "Rheumatology Clinic",
        "provider_specialty": "Rheumatology",
        "duration_hours": (0.33, 0.75),  # 20-45 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "outpatient_hematology": {
        "encounter_type": "Outpatient",
        "department": "Hematology Clinic",
        "provider_specialty": "Hematology",
        "duration_hours": (0.33, 0.75),  # 20-45 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "outpatient_obgyn": {
        "encounter_type": "Outpatient",
        "department": "OB/GYN Clinic",
        "provider_specialty": "OB/GYN",
        "duration_hours": (0.33, 0.75),  # 20-45 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "outpatient_neurology": {
        "encounter_type": "Outpatient",
        "department": "Neurology Clinic",
        "provider_specialty": "Neurology",
        "duration_hours": (0.33, 0.75),  # 20-45 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "outpatient_urology": {
        "encounter_type": "Outpatient",
        "department": "Urology Clinic",
        "provider_specialty": "Urology",
        "duration_hours": (0.33, 0.75),  # 20-45 min
        "vitals_count": 1,
        "disposition": "Discharged",
    },
    "urgent_care": {
        "encounter_type": "Urgent Care",
        "department": "Urgent Care",
        "provider_specialty": "Emergency Medicine",
        "duration_hours": (1.0, 3.0),  # 1-3 hours
        "vitals_count": 1,
        "disposition": "Discharged with follow-up",
    },
}


# =============================================================================
# CONDITION TO PROGRESSION MAPPING
# =============================================================================

CONDITION_PROGRESSION_MAP = {
    "metabolic syndrome": "metabolic_syndrome",
    "type 2 diabetes": "metabolic_syndrome",
    "diabetes mellitus": "metabolic_syndrome",
    "diabetes": "metabolic_syndrome",
    "obesity": "metabolic_syndrome",
    "hypertension": "metabolic_syndrome",
    "gallstones": "cholelithiasis_to_cholecystitis",
    "cholelithiasis": "cholelithiasis_to_cholecystitis",
    "biliary colic": "cholelithiasis_to_cholecystitis",
    "hepatitis c": "chronic_liver_disease",
    "hepatitis": "chronic_liver_disease",
    "cirrhosis": "chronic_liver_disease",
    "chronic liver disease": "chronic_liver_disease",
    "chronic kidney disease": "ckd_progression",
    "ckd": "ckd_progression",
    "peptic ulcer": "peptic_ulcer_disease",
    "nsaid use": "peptic_ulcer_disease",
    "copd": "copd_progression",
    "emphysema": "copd_progression",
    "heart failure": "chf_progression",
    "chf": "chf_progression",
    "hfref": "chf_progression",
    "pregnant": "pregnancy",
    "pregnancy": "pregnancy",
    "second trimester": "pregnancy",
    "third trimester": "pregnancy",
    "atrial fibrillation": "atrial_fibrillation",
    "afib": "atrial_fibrillation",
    "gerd": "gerd_standalone",
    "acid reflux": "gerd_standalone",
    "hypothyroidism": "hypothyroidism_standalone",
    "hypothyroid": "hypothyroidism_standalone",
    # --- CAD / Cardiac ---
    "coronary artery disease": "cad_progression",
    "cad": "cad_progression",
    "prior mi": "cad_progression",
    "myocardial infarction": "cad_progression",
    "cabg": "cad_progression",
    "stent": "cad_progression",
    "s/p stent": "cad_progression",
    "dual antiplatelet": "cad_progression",
    # --- Pulmonary ---
    "asthma": "asthma_standalone",
    "reactive airway": "asthma_standalone",
    "osa": "osa_standalone",
    "sleep apnea": "osa_standalone",
    "obstructive sleep apnea": "osa_standalone",
    # --- Psychiatric ---
    "anxiety": "anxiety_standalone",
    "gad": "anxiety_standalone",
    "generalized anxiety": "anxiety_standalone",
    "depression": "depression_standalone",
    "mdd": "depression_standalone",
    "major depressive": "depression_standalone",
    # --- Neurologic ---
    "migraine": "migraine_standalone",
    "migraines": "migraine_standalone",
    "chronic headache": "migraine_standalone",
    "dementia": "dementia_standalone",
    "alzheimer": "dementia_standalone",
    "neuropathy": "depression_standalone",
    "peripheral neuropathy": "depression_standalone",
    # --- Musculoskeletal ---
    "osteoarthritis": "osteoarthritis_standalone",
    "chronic knee pain": "osteoarthritis_standalone",
    "chronic back pain": "osteoarthritis_standalone",
    "chronic pain": "osteoarthritis_standalone",
    "degenerative joint": "osteoarthritis_standalone",
    "gout": "gout_standalone",
    "fibromyalgia": "fibromyalgia_standalone",
    "osteoporosis": "osteoporosis_standalone",
    # --- GI ---
    "nafld": "nafld_standalone",
    "fatty liver": "nafld_standalone",
    "nonalcoholic fatty liver": "nafld_standalone",
    "ibs": "ibs_standalone",
    "irritable bowel": "ibs_standalone",
    "diverticulosis": "diverticulosis_standalone",
    "diverticular disease": "diverticulosis_standalone",
    # --- Vascular ---
    "dvt": "dvt_pe_history",
    "deep vein thrombosis": "dvt_pe_history",
    "pulmonary embolism": "dvt_pe_history",
    "factor v leiden": "dvt_pe_history",
    "peripheral arterial disease": "pad_standalone",
    "claudication": "pad_standalone",
    # --- Rheumatologic ---
    "lupus": "lupus_standalone",
    "sle": "lupus_standalone",
    # --- Urology / Renal ---
    "bph": "bph_standalone",
    "benign prostatic": "bph_standalone",
    "kidney stone": "kidney_stones_history",
    "nephrolithiasis": "kidney_stones_history",
    "renal calculi": "kidney_stones_history",
    # --- Hematologic ---
    "iron deficiency": "iron_deficiency_anemia",
    "anemia": "iron_deficiency_anemia",
    # --- Endocrine / Metabolic ---
    "prediabetes": "prediabetes_standalone",
    "pre-diabetes": "prediabetes_standalone",
    "pcos": "pcos_standalone",
    "polycystic ovary": "pcos_standalone",
    # --- Substance use ---
    "alcohol use disorder": "alcohol_use_disorder",
    "alcohol abuse": "alcohol_use_disorder",
    "alcohol dependence": "alcohol_use_disorder",
}


# =============================================================================
# ANNUAL PHYSICAL VARIANTS — randomize annual visit content
# =============================================================================

ANNUAL_PHYSICAL_VARIANTS = [
    {
        "reason": "Annual physical exam",
        "note_template": "Routine annual wellness visit. Reviewed medications, "
        "updated immunizations, ordered screening labs.",
    },
    {
        "reason": "Annual wellness visit",
        "note_template": "Comprehensive wellness exam. Blood pressure well controlled. "
        "Discussed diet and exercise. Age-appropriate cancer screenings up to date.",
    },
    {
        "reason": "Health maintenance visit",
        "note_template": "Health maintenance encounter. Flu vaccine administered. "
        "Reviewed preventive care schedule. Patient reports feeling well overall.",
    },
    {
        "reason": "Annual physical with chronic disease follow-up",
        "note_template": "Annual physical with chronic disease management review. "
        "Adjusted medications as noted. Reinforced lifestyle modifications. "
        "Follow-up labs ordered.",
    },
    {
        "reason": "Routine check-up",
        "note_template": "Routine office visit. Patient doing well. Reviewed lab trends, "
        "stable. Discussed smoking cessation resources. Return in 12 months.",
    },
]


# =============================================================================
# LAB EVOLUTION FUNCTION
# =============================================================================

def evolve_lab_value(
    base_value: float,
    target_value: float,
    step: int,
    total_steps: int,
    noise_factor: float = 0.05,
    rng: random.Random = None,
) -> float:
    """
    Generate a lab value that trends from base toward target over time.

    Used to show disease progression (e.g., A1c drifting from 5.9 to 7.2
    over several years, or creatinine slowly rising in CKD).

    Args:
        base_value: Starting value
        target_value: Ending value
        step: Current step (0-indexed)
        total_steps: Total number of steps
        noise_factor: How much random noise (fraction of range)
        rng: Random number generator

    Returns:
        Interpolated value with noise
    """
    if rng is None:
        rng = random.Random()

    if total_steps <= 1:
        return round(target_value, 1)

    progress = step / (total_steps - 1)
    value = base_value + (target_value - base_value) * progress
    spread = abs(target_value - base_value) * noise_factor
    if spread > 0:
        value += rng.gauss(0, spread)

    return round(value, 1)


def get_progression_for_condition(condition_text: str) -> Optional[dict]:
    """
    Look up a condition progression template for a given condition string.

    Args:
        condition_text: Free text condition description

    Returns:
        Progression template dict or None
    """
    condition_lower = condition_text.lower()
    for key, prog_key in CONDITION_PROGRESSION_MAP.items():
        if key in condition_lower:
            return CONDITION_PROGRESSIONS.get(prog_key)
    return None
