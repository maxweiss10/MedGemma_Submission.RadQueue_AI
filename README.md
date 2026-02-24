# MedGemma Radiology Protocol Generator

Generate synthetic longitudinal EMRs and triage radiology imaging orders against ACR Appropriateness Criteria using Google's MedGemma 27B.

**This project is NOT for direct clinical use.** All outputs are synthetic and require verification by a qualified radiologist/physician.

## What This Project Does

1. **Generate synthetic EMRs** from a dataset of 92 RUQ (right upper quadrant) pain cases, producing realistic multi-year patient charts with labs, vitals, clinical notes, imaging orders, and medications
2. **Triage imaging protocols** against ACR Appropriateness Criteria, flagging inappropriate or suboptimal orders
3. **Visualize the triage queue** in an interactive web app (RadQueue AI) with priority flags and full EMR drill-down

## Quick Start

### Option A: View the pre-built app (no setup needed)

Open `radqueue_app.html` in any web browser. This standalone file contains all 92 triaged cases with full EMR data — no server, no installation, no internet required.

### Option B: Run the notebooks in Google Colab

#### Prerequisites

- Google Colab account (free GPU access required)
- HuggingFace account with MedGemma 27B access

#### Get MedGemma Access

1. Create account at [huggingface.co](https://huggingface.co)
2. Accept terms at [google/medgemma-27b-text-it](https://huggingface.co/google/medgemma-27b-text-it)
3. Generate token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. In Colab, add your token as a Secret named `HF_TOKEN` (key icon in left sidebar)

#### Run the Notebooks

Upload this project folder to Google Drive, then open each notebook in Colab:

| # | Notebook | Purpose | GPU Required |
|---|----------|---------|:---:|
| 04 | `04_emr_generator.ipynb` | Generate longitudinal EMRs from the RUQ pain dataset | Yes (T4+) |
| 03 | `03_ruq_triage.ipynb` | Triage generated EMRs against ACR criteria | Yes (T4+) |
| 05 | `05_radqueue_app.ipynb` | Build the RadQueue AI web app from triage results | No |

**Execution order:** Run 04 first (generates EMRs), then 03 (triages them), then 05 (builds the viewer). Pre-generated data is included, so you can skip to notebook 05 if you just want the app.

Set runtime to **T4 GPU**: Runtime > Change runtime type > T4 GPU.

## Project Structure

```
medgemma-protocol-generator/
├── notebooks/
│   ├── 03_ruq_triage.ipynb              # ACR triage evaluation (MedGemma 27B)
│   ├── 04_emr_generator.ipynb           # Longitudinal EMR generation (MedGemma 27B)
│   ├── 05_radqueue_app.ipynb            # RadQueue AI web app builder
│   └── synthetic_emr_comparison.md      # EMR quality analysis reference
├── src/
│   ├── __init__.py                      # Package exports
│   ├── clinical_knowledge.py            # Lab ranges, vitals, condition progressions, demographics
│   ├── emr_models.py                    # Data models (ParsedVignette, LongitudinalEMR, etc.)
│   ├── emr_narrative.py                 # MedGemma prompt templates for clinical narratives
│   ├── longitudinal_generator.py        # Multi-encounter EMR generation engine
│   └── vignette_parser.py              # Modality/region/contrast extraction helpers
├── data/
│   ├── ruq_pain_dataset_2.xlsx          # 92 RUQ pain cases (input dataset)
│   └── generated_emrs_27b/             # Generated EMR data (output)
│       ├── RUQ-001.json ... RUQ-092.json  # 92 longitudinal EMR files
│       ├── generation_summary.csv         # EMR generation log
│       ├── triage_results.csv             # ACR triage results
│       └── triage_safety_report.csv       # Safety concern flags
├── radqueue_app.html                    # Pre-built standalone web app
├── requirements.txt                     # Python dependencies
├── .env.example                         # HuggingFace token template
└── README.md
```

## Pipeline Overview

```
ruq_pain_dataset_2.xlsx (92 cases)
        │
        ▼
┌─────────────────────────┐
│  04_emr_generator.ipynb │  MedGemma 27B generates clinical narratives
│  + src/ package          │  for realistic multi-year patient charts
└──────────┬──────────────┘
           │ 92 JSON EMR files
           ▼
┌─────────────────────────┐
│  03_ruq_triage.ipynb    │  MedGemma 27B evaluates each case against
│  (inline ACR criteria)   │  ACR Appropriateness Criteria for RUQ pain
└──────────┬──────────────┘
           │ triage_results.csv
           ▼
┌─────────────────────────┐
│  05_radqueue_app.ipynb  │  Builds interactive radiology triage queue
│  → radqueue_app.html     │  with priority flags and EMR drill-down
└─────────────────────────┘
```

## ACR Clinical Variants for RUQ Pain

| Variant | Description | Usually Appropriate |
|---------|-------------|---------------------|
| 1 | Unknown etiology, initial | US (9), CT+contrast (8) |
| 2 | Suspected biliary, initial | US (9) only |
| 3 | Biliary, afebrile, negative US | MRI+MRCP (8), CT+contrast (7) |
| 4 | Biliary, febrile, negative US | MRI+MRCP (8), HIDA (7), CT+contrast (7) |
| 5 | Acalculous cholecystitis | HIDA (8) |

## Priority Flags (RadQueue AI)

| Flag | Priority | Meaning |
|------|----------|---------|
| RED | High | Protocol rated inappropriate or unsafe by ACR |
| YELLOW | Medium | Protocol rated suboptimal; consider alternatives |
| GREEN | Low | Protocol rated appropriate per ACR guidelines |
| PURPLE | Insufficient | Cannot assess appropriateness with available data |

## Model Information

- **Model**: [google/medgemma-27b-text-it](https://huggingface.co/google/medgemma-27b-text-it)
- **Parameters**: 27 billion
- **Quantization**: 4-bit (required for Colab T4 GPU)
- **Usage**: Clinical narrative generation (notebook 04) and ACR triage evaluation (notebook 03)

## Data Notes

- All patient data in this project is **entirely synthetic** — no real patient information is used
- The input dataset (`ruq_pain_dataset_2.xlsx`) contains 92 clinical vignettes with demographics, vitals, labs, and imaging orders
- Generated EMRs include realistic but fictional names, MRNs, dates, and clinical notes
- The `radqueue_app.html` strips sensitive fields (`actual_diagnosis`, `pattern_type`) from the display

## Limitations

- **Not for clinical use**: All outputs are synthetic and require physician verification
- **RUQ-specific**: Triage currently only supports RUQ pain (expandable to other ACR criteria)
- **Colab-dependent**: Notebooks 03 and 04 require Google Colab with a T4+ GPU for MedGemma

## Resources

- [ACR Appropriateness Criteria: RUQ Pain](https://acsearch.acr.org/docs/69474/Narrative/)
- [MedGemma Documentation](https://developers.google.com/health-ai-developer-foundations/medgemma)
- [MedGemma on HuggingFace](https://huggingface.co/google/medgemma-27b-text-it)

## License

This project code is provided under MIT License.

MedGemma model usage is subject to [Health AI Developer Foundations Terms](https://developers.google.com/health-ai-developer-foundations/terms).
