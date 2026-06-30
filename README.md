# Multi-Source Candidate Data Transformer
*Eightfold AI Engineering Intern Assignment*

## Overview
A production-grade data pipeline that ingests candidate information from multiple disparate sources (Structured CSV + Unstructured PDF Resume), normalizes fields, deterministically merges them with conflict resolution, computes confidence scores, and projects the result into a strictly validated JSON schema — all configurable at runtime without code changes.

## Architecture Pipeline
```
CSV Parser ──┐
             ├──► Normalizer ──► Merge Engine ──► Confidence Calculator ──► Projection Layer ──► Schema Validator ──► Output JSON
Resume Parser┘
```

1. **Extraction**: `CSVExtractor` (pandas) and `PDFExtractor` (pdfplumber + section-based heuristics) pull raw data from structured and unstructured sources.
2. **Normalization**: Pure functional modules sanitize inputs:
   - **Phones**: E.164 formatting via `phonenumbers` (default region: IN). `9876543210` → `+919876543210`
   - **Dates**: YYYY-MM via `dateparser`. `Jan 2022` → `2022-01`
   - **Skills**: Canonicalized via explicit mapping + `rapidfuzz` fuzzy matching. `ml` → `Machine Learning`
   - **Links**: Normalized to `https://` prefix
3. **Merging**: Deterministic rules resolve conflicts across sources (see Merge Strategy below).
4. **Confidence**: Dynamic scoring based on source reliability, agreement, and conflicts (see Confidence Calculation below).
5. **Projection**: Translates the internal `CandidateProfile` to a user-defined JSON shape using JSON-path queries (e.g., `emails[0]`).
6. **Validation**: Enforces strict `jsonschema` compliance before outputting.

## Folder Structure
```
candidate-transformer/
├── data/
│   ├── input/              # recruiter.csv and resume.pdf
│   └── output/             # Generated JSON profiles
├── schemas/
│   ├── output_schema.json  # Default canonical schema
│   ├── custom_schema.json  # Schema for custom projections
│   └── projection_config.json  # Runtime config example
├── src/
│   ├── extractors/         # CSV and PDF extraction logic
│   ├── merger/             # Deterministic merge rules + confidence scoring
│   ├── models/             # CandidateProfile, TrackedField, Provenance dataclasses
│   ├── normalizers/        # Phone, Date, Country, Skill normalization
│   ├── output/             # Projection layer + JSON schema validation
│   └── utils/              # Custom exceptions
├── tests/                  # Unit tests (phone, skills, merge, projection)
├── main.py                 # Argparse CLI entry point
├── generate_pdf.py         # Helper to create sample resume PDF
└── requirements.txt        # Dependencies
```

## Installation
Requires Python 3.10+.
```bash
pip install -r requirements.txt
```

## How to Run (CLI)

**Default schema** (all fields, provenance + confidence ON):
```bash
python main.py
```

**With custom file paths:**
```bash
python main.py --csv data/input/recruiter.csv --resume data/input/resume.pdf
```

**With custom projection config** (reshapes output without code changes):
```bash
python main.py --config schemas/projection_config.json
```

## Tests
```bash
python -m unittest discover tests -v
```
Covers: phone normalization (E.164), skill canonicalization (explicit map + fuzzy), merge rules (names, dedup, skills), and projection (JSON-path extraction).

---

## Sample Output

Example of a custom JSON projection (`schemas/projection_config.json`):
```json
{
  "full_name": "John Doe",
  "primary_email": "john.doe@example.com",
  "phone": "+919876543210",
  "skills": [
    "Machine Learning",
    "Python",
    "SQL"
  ]
}
```

---

## Merge Strategy

| Field | Strategy | Rationale |
|---|---|---|
| `full_name` | Prefer longest non-empty string | CSV may have "John", Resume has "John Doe" |
| `emails` | Unique aggregation (insertion order) | Both sources may have valid, different emails |
| `phones` | Unique aggregation after E.164 normalization | Additive — all valid phones are kept |
| `skills` | Deduplicate by name after canonicalization, sort alphabetically | Deterministic output across runs |
| `experience` | Deduplicate by `(company, title)` key | Prevents duplicating the same role |
| `education` | Deduplicate by `(institution, degree)` key | Prevents duplicating the same degree |
| `headline` | Derived from first experience entry: `"{title} at {company}"` | Auto-generated when missing |
| `links` | First non-null per field (linkedin, github) | Typically from Resume only |
| `location` | From Resume section parsing | CSV rarely contains location |
| `candidate_id` | `uuid5(email)` for determinism, `uuid4()` fallback | Same email → same ID across runs |
| `years_experience` | Computed from YYYY-MM normalized experience dates | Derived, not extracted |

## Confidence Calculation

| Scenario | Score | Explanation |
|---|---|---|
| Single source (CSV) | **0.90** | CSV is structured, high base reliability |
| Single source (Resume) | **0.80** | Resume parsing uses heuristics, slightly lower |
| Both sources agree | **0.95** | Agreement bonus: `+0.05` (capped at 1.0) |
| Both sources conflict | **0.75** | Conflict penalty: base `0.95 - 0.20 = 0.75` |
| Pipeline-computed field | Inherits source confidence | e.g., `years_experience` inherits from experience |
| **Overall confidence** | **Weighted average** of all non-null field confidences | Holistic profile quality score |

*Note: Resume-derived skills receive a base confidence of 0.8 to reflect heuristic parsing uncertainty.*

## Phone Normalization
- Uses `phonenumbers` library with default region `IN` (India)
- `9876543210` → `+919876543210`
- `+14155552671` → `+14155552671` (US number with country code preserved)
- Invalid/malformed → `null` (never invented)

## Projection Layer
The runtime config supports:
- **`path`**: Output key name
- **`from`**: JSON-path extraction (e.g., `emails[0]`, `skills[].name`)
- **`on_missing`**: `"null"` | `"omit"` | `"error"`
- **`include_confidence`** / **`include_provenance`**: Toggle metadata on/off

## Schema Validation
Output is validated against `jsonschema` before returning. Invalid output raises `ValidationError` with the exact schema violation, never silently passes bad data.

## Assumptions & Descoped Features
- **Single candidate per run**: Input files are assumed to belong to the same person.
- **Cross-candidate deduplication**: Not in scope. Real systems need entity resolution to determine *if* two rows are the same person.
- **Advanced NLP**: The `PDFExtractor` uses section-based heuristics. In production, spaCy NER or an LLM would improve accuracy.
- **Present = null**: In experience dates, `"Present"` is stored as `null` (intentional design choice — `null` means "current role").
