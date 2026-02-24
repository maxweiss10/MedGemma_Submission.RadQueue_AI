# Synthetic EMR Generation: Comprehensive Comparison Table

## Methods & Approaches

| **Method Category** | **Type** | **Key Approach** | **Best For** | **Key Limitation** |
|---|---|---|---|---|
| **Synthea** | Rule-based simulator | State machines encoding 120+ disease modules from CDC/NIH guidelines | Complete longitudinal patient histories, structured data (FHIR, C-CDA, CSV) | No native clinical note generation; covers ~160 phecodes |
| **LLM-based Text Generation** | Autoregressive transformer | Fine-tuned or prompted LLMs to generate clinical narratives from codes or brief scenarios | Discharge summaries, SOAP notes, HPI narratives, radiology reports | Hallucination risk; requires careful prompting or fine-tuning |
| **GANs (Generative Adversarial Networks)** | Adversarial deep learning | Generator learns to fool discriminator; handles mixed-type data | Single-timepoint or short sequences; computationally efficient generation | Training instability; limited temporal coherence in early models |
| **Diffusion Models** | Denoising probabilistic models | Iterative noise removal (DDPM, DDIM); sequential sampling | High-fidelity time-series EHR; rare condition generation; strong privacy guarantees | 2.5–8× slower than GANs; higher computational cost |
| **Variational Autoencoders (VAEs)** | Encoder-decoder with latent space | Maps data to learned distribution; conditional generation possible | Patient trajectories as graphs; ensuring novelty and preventing memorization | Posterior collapse; lower fidelity than diffusion models |
| **Knowledge-Graph-Guided Prompting** | Hybrid LLM + structured knowledge | LLM generates narratives conditioned on disease-symptom-drug graphs from medical ontologies | Converting brief clinical scenarios to realistic clinical notes; controlling hallucination | Requires curated knowledge graphs; higher manual setup |

---

## Major Tools & Platforms

| **Tool** | **Approach** | **Data Type** | **Output Format** | **License** | **Maturity** | **GitHub/Link** | **Key Citation** |
|---|---|---|---|---|---|---|---|
| **Synthea** | Rule-based state machines | Structured: encounters, conditions, medications, labs, procedures, immunizations, claims | FHIR R4, C-CDA, CSV, bulk FHIR (ndjson), OMOP CDM | Apache 2.0 (open-source) | Production-ready (2800+ stars) | `github.com/synthetichealth/synthea` | *JAMIA* 2018 |
| **chatty-notes** | GPT-3.5/4 prompting on Synthea FHIR bundles | Unstructured: clinical narratives, discharge summaries, notes | Markdown/text; integrable with Synthea output | Apache 2.0 (open-source) | Active (updated June 2025) | `github.com/synthetichealth/chatty-notes` | — |
| **GatorTronGPT** | Fine-tuned autoregressive 20B model on 82B clinical words + 195B general English | Unstructured: clinical text (notes, summaries, reports) | Raw text | Research license (UF Health) | Research-grade; not openly available for commercial use | University of Florida | *npj Digital Medicine* 2023 |
| **Asclepius** | Fine-tuned Llama & Mistral variants on 157k synthetic discharge summaries from PMC-Patients | Unstructured: discharge summaries, clinical narratives | Raw text; HuggingFace models | Weights: Apache 2.0 compatible; code: MIT | Research release (Dec 2024) | `github.com/starmpcc/Asclepius` HuggingFace weights | *ACL 2024 Findings* |
| **MedSyn** | GPT-4/LLaMA-7b + Medical Knowledge Graph sampling | Unstructured: clinical notes for 219 ICD-10 codes | Raw text; 41,000+ synthetic clinical notes included | Research code available (Springer) | Academic (ECML PKDD 2024) | `github.com/[unclear—check SpringerLink]` | *ECML PKDD* 2024 |
| **CEHR-GPT** | GPT architecture applied directly to EHR time-series | Both: structured coded sequences + temporal patterns | Time-series sequences; convertible to OMOP | Open-source (arXiv) | Recent (2024) | arXiv:2402.04400 | *arXiv* 2024 |
| **HALO (HierarchicAL LongitudInAl Observation)** | Hierarchical autoregressive transformer (visit-level, code-level) | Structured: sequences of 10,000+ unique ICD codes; longitudinal | Time-series; OMOP format | Open-source | *Nature Communications* 2023; production-validated | — (check Nature Comms supplementary) | *Nature Communications* 2023 |
| **HiSGT** | Hierarchical ICD + SNOMED ontology + ClinicalBERT embeddings | Structured: coded diagnosis/procedure sequences | Longitudinal sequences | Open-source (2025) | Very recent | `github.com/jameszhou-gl/HiSGT` | *preprint* 2025 |
| **PromptEHR** | Text-to-text prompting with LLMs; formulates EHR generation as NLG | Both: coded data + conditional narratives from demographics | Structured + text | Open-source (MIT) | *EMNLP* 2022 | `github.com/RyanWangZf/PromptEHR` | *EMNLP* 2022 |
| **medGAN** | GAN for multi-label discrete patient records | Structured: diagnosis/medication codes; single timepoint | Tabular; one record per patient | Open-source (MIT) | Foundational (2017); has limitations for longitudinal data | `github.com/mp2893/medgan` | *ICML* 2017 |
| **EHR-M-GAN** | Dual-VAE + coupled recurrent generator for mixed-type longitudinal data | Structured: mixed-type (categorical codes, continuous labs, counts); longitudinal | Tabular time-series | Open-source | *npj Digital Medicine* 2023; validated on 141K+ patients across 3 ICU datasets | `github.com/jli0117/ehrMGAN` | *npj Digital Medicine* 2023 |
| **CTGAN (Conditional Tabular GAN)** | Conditional GAN for tabular data with mixed types | Structured: mixed-type tabular; single or multiple snapshots | Tabular (CSV, Parquet) | Open-source (Apache 2.0) | Production-ready; part of SDV ecosystem | `github.com/sdv-dev/CTGAN` | *ICLR* 2021 |
| **EHR-Safe (Google Research)** | Encoder-decoder + WGAN-GP; privacy-preserving | Structured: patient records; mixed types | Tabular; FHIR JSON optional | Code unavailable (research) | High-fidelity; code requests unmet as of 2025 | Google Research blog | *JAMIA* 2023 |
| **TimeDiff** | Mixed-sequence DDPM (diffusion model) for time-series EHR | Structured: high-dimensional longitudinal EHR; time-series | Time-series sequences | Open-source | State-of-the-art on MIMIC-III/IV, eICU; includes 9 baselines | `github.com/MuhangTian/TimeDiff` | *JAMIA* 2024 |
| **EHR-D3PM (Discrete Denoising Diffusion Probabilistic Models)** | Discrete diffusion with energy-guided Langevin dynamics | Structured: categorical codes; conditional generation for rare conditions | Sequences with condition control | Open-source (arXiv) | Recent; specialized for rare disease oversampling | arXiv:2404.12314 | *arXiv* 2024 |
| **FLEXGEN-EHR** | Latent-space diffusion with LSTM encoders + optimal transport alignment | Structured: missing-modality EHR (heterogeneous data types) | Tabular time-series with missing values handled | Open-source | Recent (2024) | arXiv details | *arXiv* 2024 |
| **Variational Graph Autoencoders (VGAE)** | Graph VAE where nodes = encounters/conditions/medications | Structured: encounters and associated clinical events as graphs | Graph format or adjacency matrices | Open-source (PyTorch Geometric) | *npj Digital Medicine* 2023; research-grade | — | *npj Digital Medicine* 2023 |
| **CodeAR (VQ-VAE + Autoregressive)** | VQ-VAE tokenization of medical time series → autoregressive generation | Structured: coded medical time-series | Tokenized sequences; decodable to original format | Open-source | *AI in Medicine* 2024 | — | *AI in Medicine* 2024 |
| **SynthEHRella** | Benchmarking package; evaluation harness (not generation) | Meta: evaluation framework for 7+ generation methods | Metrics (MMD, Pearson, JSD, Hellinger) + TSTR/TSRTR utilities | Open-source (MIT) | JAMIA benchmark (2025); active | `github.com/chenxran/synthEHRella` | *JAMIA* 2025 |
| **Synthetic Data Vault (SDV)** | Modular Python library for tabular/time-series synthesis | Structured: tabular or sequential; mixed types | Tabular or time-series (Pandas, etc.) | Open-source (Apache 2.0) | Production-ready; 3000+ stars | `github.com/sdv-dev/SDV` | Various papers; see docs.sdv.dev |
| **SmartNoise SDK** | Differential privacy toolkit; DP-SGD for DP synthesizers (DPGAN, PATE-GAN, DP-CTGAN) | Both: enables DP training of any synthesizer | Depends on base synthesizer; adds DP guarantees | Open-source (MIT; OpenDP project) | Production-ready | `github.com/opendp/smartnoise-sdk` | *Proceedings on Privacy Enhancing Technologies* (various) |
| **MOSTLY AI** | Self-contained tabular/time-series synthesizer with DP option | Structured: tabular, time-series, sequences | CSV, Parquet, JSON lines; time-series compatible | Open-source (Apache 2.0); also commercial SaaS | Production-ready; NVIDIA early investor | `github.com/mostly-ai/mostlyai` | MOSTLY AI white papers |
| **MDClone** | Integrates with Epic, Cerner, Meditech; creates digital twins from real EHR | Both: structured + narratives; "digital twins" | Integrates with EHR systems; outputs in native formats | Commercial (closed-source) | Production (enterprise); 70% reduction in research proposal time reported | mdclone.com | — |
| **Syntegra** | FHIR USCDI-formatted synthetic EHR from real US hospital distributions | Structured: USCDI-compliant EHR; condition-specific cohorts | FHIR, OMOP CDM | Commercial (closed-source) | Production; purchasing model | syntegra.com / Datarade | — |
| **Gretel.ai** | Generative AI platform for tabular + time-series; differential privacy native | Both: tabular, sequences, time-series; mixed types | Multiple formats (CSV, JSON, etc.); FHIR plugins in development | Commercial with free tier (code open for inspection) | Production-ready; acquired by NVIDIA March 2025 | gretel.ai | Various Gretel research; blog posts |

---

## Comparison Matrix: Technology Stack

| **Dimension** | **Synthea** | **LLM-based (GPT-4/Asclepius)** | **Diffusion (TimeDiff)** | **GAN (EHR-M-GAN/CTGAN)** | **VAE-based** | **Knowledge-Graph LLM (MedSyn)** |
|---|---|---|---|---|---|---|
| **Primary Strength** | Complete longitudinal histories; rule-based consistency | Realistic clinical narratives; pass physician Turing test | Highest fidelity; best TSTR scores; privacy-stable | Fast inference; efficient training; low compute | Theoretical rigor; graph-structured logic; novelty guarantees | Control over hallucination; domain-aligned generation |
| **Primary Weakness** | No native narratives; limited disease coverage (~160 phecodes) | Hallucination risk; requires careful prompting/fine-tuning; unstructured only | 2.5–8× slower than GANs | Training instability (GANs); lower fidelity than diffusion | Posterior collapse issues; lower fidelity; limited longitudinal support | Requires curated knowledge graphs; higher setup cost |
| **Data Types Handled** | Structured only (encounters, diagnoses, procedures, medications, labs, claims) | Unstructured only (text narratives) | Structured time-series | Structured (tabular or short sequences) | Structured (can encode as graphs) | Unstructured (narratives from codes) |
| **Temporal Modeling** | Excellent (full lifespan; state machines encode disease progression) | N/A (single-document generation) | Excellent (autoregressive time-series) | Limited (early GANs); good in EHR-M-GAN with LSTM | Good (trajectories as graph evolution) | N/A (document-level) |
| **Conditional Generation** | Yes (define disease modules; constrain scenarios) | Yes (prompt engineering; chain-of-thought) | Yes (energy-guided diffusion for rare conditions) | Conditional variants available (CTGAN) | Yes (conditional VAE) | Yes (graph-conditioned sampling) |
| **Rare Condition Support** | Configurable (set disease prevalence; risk factors) | Prompt-engineered scenarios | Excellent (EHR-D3PM energy guidance) | Imbalanced class handling needed | Oversampling possible | Knowledge-graph pruning by prevalence |
| **Privacy Guarantees** | Intrinsic (never trains on real data; rule-based) | None (depends on training data; LLMs memorize) | Can add differential privacy via SmartNoise | Can add DP via SmartNoise | Can add DP via SmartNoise | Depends on LLM & knowledge graph source |
| **Training Complexity** | Low (rules + random sampling) | High (fine-tuning 7B–20B models; compute expensive) | Medium-high (requires GPU; sequential denoising) | Medium (adversarial training; hyperparameter tuning) | Medium (VAE training; hyperparameter-sensitive) | Medium-high (LLM fine-tuning; knowledge-graph curation) |
| **Inference Speed** | Fast (rule-based; CPU capable) | Medium (LLM inference; 1–5 sec per sample; depends on model size) | Slow (100 denoising steps; 0.65 sec per 100 samples) | Fast (0.08 sec per 100 samples) | Medium | Medium (LLM + graph lookup) |
| **Scalability** | Excellent (pre-computed up to 2.8M patients; AWS OMOP available) | Good (can generate in batches; but high compute) | Good (batch denoising; GPU scalable) | Excellent (batch generation; highly efficient) | Good | Good (depends on LLM inference infra) |
| **Output Format Flexibility** | High (FHIR R4, C-CDA, CSV, OMOP CDM, bulk FHIR) | Low (raw text; post-processing needed for structure) | Medium (time-series; post-process to OMOP or FHIR) | Medium (tabular; FHIR conversion post-hoc) | Medium | Low (text; structure requires extraction) |
| **Clinical Consistency** | High (rules encode medical logic; state transitions validated) | Medium-High (depends on prompting; can hallucinate) | High (learns from real EHR distributions) | Medium (less aware of clinical sequencing) | High (graph encodes relationships) | High (knowledge graph constrains generation) |
| **Validation Ease** | High (fidelity vs. real distributions; TSTR straightforward) | Medium (requires domain expert review; TSTR possible) | High (TSTR, privacy metrics, temporal validation all supported) | High (TSTR, Wasserstein metrics available) | High (graph-based validation) | Medium-High (requires expert evaluation + TSTR) |
| **Community & Support** | Excellent (2800+ GitHub stars; MITRE/Synthea Health active; documentation extensive) | Growing (Asclepius on HuggingFace; MedSyn on arXiv; varying support) | Growing (TimeDiff actively maintained; reproduces 9 baselines) | Good (medGAN/CTGAN mature; SDV well-documented) | Research-focused (less active maintenance) | Academic (MedSyn paper authors; limited production deployments) |
| **Total Cost** | Free (open-source; rules are pre-defined) | $$-$$$$$ (LLM API costs or compute for fine-tuning; 10k notes: $50–500 via GPT-4) | $-$$ (GPU compute for training; inference cheaper) | $-$$ (lower compute for training) | $$ (moderate GPU cost) | $$$-$$$$ (LLM + knowledge graph curation labor) |
| **Best Use Case** | "I need realistic longitudinal patient histories with structured data." | "I need realistic clinical narratives that accompany structured data." | "I need synthetic EHR with highest statistical fidelity for ML validation." | "I need fast, efficient structured data synthesis for tabular benchmarking." | "I need patient trajectories as graphs; guarantee no memorization." | "I need brief scenarios converted to realistic full clinical narratives." |

---

## Hybrid Pipelines (Recommended)

| **Use Case** | **Recommended Stack** | **Rationale** | **Validation Method** |
|---|---|---|---|
| **Full EMR for model validation (TSTR)** | Synthea (structured) + TimeDiff (augmentation) + SynthEHRella (evaluation) | Synthea provides complete longitudinal histories; TimeDiff refines fidelity; SynthEHRella benchmarks against baselines | TSTR (train on synthetic, test on real hold-out); TSRTR (augmentation utility); MMD, Pearson, JSD, Hellinger distance |
| **Complete chart with realistic narratives** | Synthea (structured) + chatty-notes (narratives) | Synthea outputs FHIR bundles; chatty-notes generates clinically realistic notes from them; maintains consistency | TSTR for structured; physician Turing test for narratives (survey review); temporal coherence check |
| **Conditional generation for rare disease cohorts** | Synthea module for rare disease + EHR-D3PM (diffusion with energy guidance) | Synthea constructs disease modules; diffusion refines fidelity while maintaining rare condition oversampling | Prevalence preservation; TSTR on rare subpopulation; Energy-guided validation metrics |
| **High-fidelity time-series (ICU data)** | TimeDiff (primary generation) + SmartNoise (differential privacy) + MOSTLY AI (tabular augmentation) | TimeDiff outperforms on MIMIC benchmarks; SmartNoise adds formal privacy; MOSTLY AI augments sparse variables | TSTR; privacy attack resistance (MIA, AIA); autocorrelation function for temporal patterns |
| **Large-scale privacy-safe data (research/industry)** | MOSTLY AI or Gretel.ai (DP-enabled) + SDV validation toolkit | Commercial tools offer DP guarantees; SDV provides flexible validation; avoids HIPAA/GDPR risk | TSTR; DP budget documentation (ε values); utility-privacy trade-off curves |
| **Narrative generation from brief scenarios** | Knowledge-graph-guided MedSyn or GPT-4 + chain-of-thought prompting + MOSTLY AI (structured components) | LLM generates narratives constrained by disease graphs; structured data ensures consistency; MOSTLY AI handles codes | Expert clinical review; semantic similarity (BERTScore) vs. reference notes; TSTR on downstream tasks |
| **Rapid prototyping (exploratory validation)** | Synthea (quick generation) + basic TSTR + manual review | Fastest path to realistic data; does not require training; validation can be informal in prototyping phase | TSTR on any one downstream task; domain expert review of 50–100 samples |

---

## Quick Selection Guide

**Choose Synthea if...**
- You need complete patient histories spanning entire lifespans
- You want rule-based consistency (medical logic encoded in state machines)
- You prioritize privacy (zero training on real data)
- You need FHIR/OMOP/C-CDA interoperability

**Choose LLM-based (Asclepius, MedSyn, GPT-4) if...**
- You need realistic clinical narratives (notes, summaries, reports)
- You have a structured dataset and need to add narratives
- You can tolerate hallucination risk and can mitigate via domain knowledge graphs
- You want to convert brief scenarios into full clinical text

**Choose Diffusion (TimeDiff, EHR-D3PM) if...**
- Statistical fidelity is your primary goal (TSTR performance matters most)
- You have GPUs available for training
- You need formal privacy guarantees (can integrate SmartNoise)
- You're generating ICU or high-dimensional time-series EHR

**Choose GANs (CTGAN, EHR-M-GAN) if...**
- Speed and efficiency matter (inference is fast; training is fast)
- Your validation tasks are primarily tabular (no temporal complexity)
- You have limited GPU resources but need good enough fidelity
- You're augmenting sparse variables or rare classes

**Choose VAEs if...**
- You model patient trajectories as graphs or networks
- Preventing memorization is critical
- You need interpretability through latent space structure

**Choose Hybrid (Synthea + chatty-notes or Synthea + TimeDiff) if...**
- You need both structured and unstructured data
- You want clinical realism across all dimensions
- You're comfortable integrating multiple tools

---

## Key Benchmarks (from SynthEHRella & TimeDiff papers, 2024–2025)

| **Method** | **Dataset** | **TSTR AUROC** | **MMD (Prevalence)** | **Inference Speed (per 100 samples)** | **Notes** |
|---|---|---|---|---|---|
| Real data (baseline) | MIMIC-III | 0.943 | 0.0 (reference) | N/A | Ground truth |
| TimeDiff (diffusion) | MIMIC-III | 0.937 | 0.018 | 0.65 sec | Best fidelity; slowest |
| HALO (hierarchical autoregressive) | MIMIC-III | 0.938 | 0.021 | 0.15 sec | Excellent speed-fidelity trade-off |
| EHR-M-GAN | ICU (3 databases, 141k patients) | ~0.92 | <0.03 | 0.08 sec | Fastest; handles mixed types well |
| CTGAN | Tabular benchmarks | ~0.85–0.91 | variable | 0.05 sec | Fast; good for sparse data |
| Synthea | Full EHR | ~0.90 (varies by condition) | ~0.05 | <0.01 sec (rule-based) | Excellent for complete histories; less useful for fidelity benchmarks |
| MedSyn (GPT-4 + knowledge graph) | Clinical narratives (41k notes) | N/A (text only) | N/A | 2–5 sec per note | Physician Turing test: hallucination rate ~18% (controlled via graph) |
| Asclepius (fine-tuned LLaMA) | Discharge summaries (157k) | N/A (text only) | N/A | 0.5–1 sec per summary | More efficient than GPT-4; comparable quality |

---

## Regulatory & Privacy Status

| **Framework** | **Status as of 2025** | **Key Implications** | **Recommended Approach** |
|---|---|---|---|
| **HIPAA (USA)** | Safe Harbor applies to rule-based synthetic data (Synthea); gray area for data-driven methods | Synthea-only workflows = zero HIPAA scope; GANs/diffusion trained on real data = Expert Determination recommended | Use Synthea; if training on real data, obtain Expert Determination certification or apply SmartNoise (DP-SGD) |
| **GDPR (EU)** | Even synthetic-looking data may be personal data if traits derive from real individuals | EU AI Act endorses synthetic data for debiasing (Article 59(1)(b)) | Prefer rule-based (Synthea) or add SmartNoise DP layer; document training data provenance |
| **EU Health Data Space (entered force March 2025)** | Synthetic data explicitly recognized as privacy-preserving mechanism | Regulatory momentum toward synthetic data adoption | Monitor guidance; use as compliance bridge for cross-border research |
| **FDA (USA)** | No specific guidance on synthetic EHR; REALYSM Program studies synthetic data for AI/ML device validation | No regulatory barrier; synthetic data not yet used in drug approvals | Document fidelity validation (TSTR, expert review); maintain decision audit trail |
| **Differential Privacy** | Standard privacy budget: ε = 1.0 for strict privacy; ε ≤ 5 for utility-privacy balance | DP-SGD integration available via SmartNoise for any synthesizer | Integrate SmartNoise if formal privacy guarantees required; specify ε budget in documentation |

---

## Implementation Checklist

- [ ] **Define use case**: Is your bottleneck structured data, narratives, or both?
- [ ] **Assess data availability**: Do you have real EHR to train on, or will you use rule-based approaches?
- [ ] **Choose generation method**: Use selection guide above; consider hybrid pipeline.
- [ ] **Set up validation framework**: Use SynthEHRella for structured; physician review for narratives; TSTR for ML validation.
- [ ] **Implement privacy controls**: If training on real data, add SmartNoise or obtain Expert Determination; prefer Synthea for maximum privacy.
- [ ] **Document compliance**: Record method selection, validation results, privacy guarantees (if applicable); maintain audit trail.
- [ ] **Iterate and refine**: Validate TSTR performance; adjust generation parameters; involve clinical experts.
