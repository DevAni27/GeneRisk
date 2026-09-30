# GeneRisk

**AI-assisted HBB variant triage using NVIDIA Evo2**

> **Runner-Up — MITAOE Project Expo 2026, National-Level Engineering Competition**

GeneRisk is a research prototype for **rapid first-pass triage of HBB gene variants** associated with sickle-cell disease and beta-thalassemia. It combines long-context genomic sequence scoring with clinical database evidence to help prioritize variants for expert review.

The system accepts multiple real-world variant identifiers, normalizes them to a common genomic representation, constructs reference and mutant DNA contexts, scores both with **NVIDIA Evo2 7B**, and presents the result alongside evidence from sources such as **ClinVar/NCBI** and **Ensembl**.

---

## Highlights

- **0.971 AUROC** on preliminary HBB validation
- **92.1% sensitivity**
- **100% specificity**
- Calibrated on **47 clinically labelled HBB SNVs**
- Uses **8,192-bp reference and mutant sequence contexts**
- Supports common variant input formats including **HGVS, genomic coordinates, rsIDs, and aliases**
- Full-stack implementation with **FastAPI + Next.js**
- Built as a **triage/research aid**, not a diagnostic system

---

## Why GeneRisk?

Genomic screening can identify variants that are rare, poorly characterized, or absent from common clinical databases. These variants can require significant manual interpretation before they can be meaningfully prioritized.

GeneRisk explores whether a genomic foundation model can provide a useful **first-pass signal** for HBB variants by comparing how strongly a model scores:

1. the normal genomic sequence, and
2. the same sequence after introducing the candidate mutation.

The goal is not to replace clinical interpretation. The goal is to help surface variants that may deserve closer review.

---

## How It Works

```text
Variant input
(HGVS / coordinate / rsID / alias)
                │
                ▼
        Variant normalization
                │
                ▼
        GRCh38 coordinate mapping
                │
                ▼
      UCSC reference sequence fetch
                │
        8,192-bp context window
                │
          ┌─────┴─────┐
          ▼           ▼
   Reference DNA   Mutant DNA
          │           │
          ▼           ▼
       Evo2 score   Evo2 score
          │           │
          └─────┬─────┘
                ▼
          Delta score
                │
                ▼
       HBB-calibrated decision
                │
        ┌───────┴────────┐
        ▼                ▼
  Model prediction   Clinical evidence
                     ClinVar / NCBI /
                     Ensembl
        │                │
        └───────┬────────┘
                ▼
         GeneRisk result
```

---

## Model Methodology

GeneRisk uses **NVIDIA Evo2 7B** in a zero-shot sequence-scoring setup.

For a candidate HBB variant:

1. Fetch an **8,192-bp reference sequence** surrounding the variant.
2. Construct a matching mutant sequence by introducing the alternate allele.
3. Score both sequences with Evo2.
4. Compare their sequence likelihoods.
5. Use the difference between the reference and mutant scores as a variant-impact signal.
6. Apply an HBB-specific calibration threshold derived from clinically labelled variants.

Conceptually:

```text
delta = score(mutant sequence) - score(reference sequence)
```

A larger disruption to the learned genomic sequence distribution can provide evidence that a variant may be functionally important.

> GeneRisk treats this score as a **triage signal**, not as independent proof of pathogenicity.

---

## Preliminary HBB Validation

The HBB-specific calibration was evaluated on **47 clinically labelled single-nucleotide variants**.

| Metric | Result |
|---|---:|
| AUROC | **0.971** |
| Sensitivity | **92.1%** |
| Specificity | **100%** |

These results are preliminary and should be interpreted as prototype validation rather than clinical performance.

### Why these metrics?

- **AUROC** measures how well the score separates labelled pathogenic and benign variants across thresholds.
- **Sensitivity** measures how many labelled pathogenic variants were correctly identified.
- **Specificity** measures how many labelled benign variants were correctly identified.

---

## Supported Variant Inputs

GeneRisk is designed to accept multiple forms of variant notation and normalize them to a consistent GRCh38 representation.

Examples include:

```text
HGVS notation
Genomic coordinates
rsIDs
Common variant aliases
```

This makes the system easier to use with heterogeneous inputs from reports, databases, and research datasets.

---

## Clinical Evidence Layer

The model score is shown alongside external evidence where available.

GeneRisk integrates or references:

- **ClinVar / NCBI**
- **Ensembl**
- **UCSC Genome Browser API**

This separation is intentional:

```text
AI-derived sequence signal
            +
Independent clinical/database evidence
            =
More interpretable triage output
```

A known ClinVar classification is not replaced by the AI prediction.

---

## Architecture

```text
┌───────────────────────────────┐
│        Next.js Frontend       │
│ Variant input + result view   │
└───────────────┬───────────────┘
                │
                │ HTTP
                ▼
┌───────────────────────────────┐
│        FastAPI Backend        │
│                               │
│ • Input normalization         │
│ • Reference validation        │
│ • Sequence construction       │
│ • Evo2 inference orchestration│
│ • Calibration                 │
│ • Clinical evidence lookup    │
└───────┬───────────┬───────────┘
        │           │
        ▼           ▼
   NVIDIA Evo2   Genomic APIs
                 UCSC / NCBI /
                 Ensembl
```

The frontend and inference backend are separated by an API contract so model or calibration changes can be made without rewriting the user interface.

---

## Tech Stack

### AI / Genomics
- NVIDIA Evo2 7B
- UCSC Genome Browser API
- ClinVar / NCBI
- Ensembl
- HBB-specific calibration

### Backend
- Python
- FastAPI

### Frontend
- Next.js
- React
- TypeScript

### Deployment
- Render
- Vercel

---

## Example API Flow

A normalized request can conceptually look like:

```json
{
  "gene": "HBB",
  "chrom": "11",
  "position": 5227002,
  "ref": "A",
  "alt": "T"
}
```

An analysis response can include:

```json
{
  "delta_score": -4.2,
  "prediction": "likely_pathogenic",
  "confidence": 0.81,
  "clinvar_label": "Pathogenic",
  "explanation": "Model-derived triage signal combined with available clinical evidence."
}
```

The exact route and response shape may evolve as the project develops.

---

## Running the Project

Clone the repository:

```bash
git clone https://github.com/DevAni27/GeneRisk.git
cd GeneRisk
```

### Backend

Move into the backend directory and install the dependencies defined by the project:

```bash
cd backend
```

Create an environment file from the provided example, then configure the required genomic/model API credentials.

Start the FastAPI server using the command defined by the backend setup.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The Next.js development server will typically run at:

```text
http://localhost:3000
```

> Refer to the repository's `.env.example` files for the current environment-variable names. Never commit API keys or secrets.

---

## Suggested Environment Configuration

Depending on deployment, GeneRisk may require credentials or endpoints for services used by the inference and evidence pipeline.

Keep secrets only in local or deployment environment variables.

```env
# Example only — use the variable names expected by the codebase.
NVIDIA_API_KEY=your_key_here
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Do not commit `.env`, `.env.local`, API keys, access tokens, or private credentials.

---

## Design Decisions

### Why HBB?

HBB is directly associated with clinically important hemoglobin disorders including sickle-cell disease and beta-thalassemia.

It is also a useful test case for genomic foundation-model research because the system can be evaluated against known labelled variants while still addressing rare and uncertain variants.

### Why compare reference and mutant sequences?

Using matched sequence contexts isolates the candidate mutation as the primary difference between the two model inputs.

```text
Reference context ─┐
                   ├─ compare Evo2 scores → variant-impact signal
Mutant context ────┘
```

### Why keep clinical evidence separate?

Foundation-model output should not silently override established database evidence.

GeneRisk therefore treats the AI score as one signal and exposes available clinical annotations independently.

---

## Responsible Use

GeneRisk is intentionally positioned as a **variant-triage and research prototype**.

It is **not** intended to:

- diagnose sickle-cell disease or beta-thalassemia
- determine treatment
- replace genetic counsellors, clinicians, or laboratory interpretation
- independently establish variant pathogenicity

Any real-world medical use would require substantially larger validation, independent cohorts, expert review, regulatory consideration, and appropriate clinical workflow integration.

---

## Current Limitations

- Preliminary validation currently covers a relatively small HBB-labelled set.
- Performance may not generalize to unseen variant classes or populations.
- Zero-shot genomic model scores are not equivalent to clinical pathogenicity classifications.
- Sequence context alone does not capture every mechanism relevant to variant interpretation.
- Clinical databases can contain conflicting or evolving classifications.
- The system has not undergone prospective clinical validation.

---

## Future Work

- Expand HBB validation to substantially larger labelled datasets
- Perform patient- and cohort-independent evaluation
- Benchmark against established variant-effect predictors
- Add calibrated uncertainty estimates
- Improve evidence aggregation across clinical databases
- Add richer provenance for every prediction and evidence source
- Support additional hemoglobinopathy-related genes
- Explore G6PD and other high-impact genetic screening use cases
- Add batch variant analysis for public-health/research workflows

---

## Team

| Team Member | Role |
|---|---|
| **Aniket Dhingra** | Backend & AI Systems |
| **Aadit Pandit** | Frontend |
| **Alisha Savant** | Data & Validation |
| **Arya Sharma** | Data & Validation |

---

## Recognition

### Runner-Up — MITAOE Project Expo 2026

GeneRisk secured **Runner-Up (2nd Place)** at the **MITAOE Project Expo 2026**, a national-level engineering project competition hosted by MIT Academy of Engineering, Alandi, Pune.

The project was recognized for combining genomic foundation models, HBB-specific calibration, clinical evidence integration, and a usable full-stack workflow.

---

## Repository Hygiene

Before contributing or publishing changes:

- never commit `.env` files or API credentials
- do not commit sensitive patient/genomic records
- confirm redistribution rights before adding third-party datasets
- keep generated outputs and large model artifacts out of Git unless intentionally versioned
- document the provenance and licensing of external data sources

---

## License

Add a repository license that reflects how you want the source code to be reused.

Third-party datasets, model APIs, pretrained models, and external services remain subject to their own licenses and terms.

---

## Disclaimer

**GeneRisk is a research and educational prototype. It is not a medical device and does not provide medical diagnosis, treatment recommendations, or definitive clinical variant interpretation. Outputs must be reviewed by appropriately qualified professionals.**
