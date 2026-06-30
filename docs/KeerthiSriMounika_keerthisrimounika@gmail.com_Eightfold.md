# Technical Design Document: Multi-Source Candidate Data Transformer

## 1. Architecture & Pipeline
```
┌─────────────┐     ┌──────────────┐
│  CSV Parser  │     │ Resume Parser │
│  (pandas)    │     │ (pdfplumber)  │
└──────┬──────┘     └──────┬───────┘
       │                    │
       └────────┬───────────┘
                ▼
        ┌───────────────┐
        │  Normalizer   │  Phone → E.164 | Dates → YYYY-MM | Skills → Canonical
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ Merge Engine  │  Deterministic conflict resolution per field
        └───────┬───────┘
                ▼
        ┌───────────────────┐
        │ Confidence Scorer │  Source reliability + agreement/conflict scoring
        └───────┬───────────┘
                ▼
        ┌───────────────────┐
        │ Projection Layer  │  Runtime JSON config → reshape output
        └───────┬───────────┘
                ▼
        ┌───────────────────┐
        │ Schema Validator  │  jsonschema enforcement before emit
        └───────┬───────────┘
                ▼
           Output JSON
```

## 2. Canonical Schema & Normalization
The internal `CandidateProfile` enforces strict types. Every field is wrapped in a `TrackedField` storing: value, provenance list, confidence score.

| Field | Normalization | Format |
|---|---|---|
| Phones | `phonenumbers` library | E.164 (`+919876543210`) |
| Dates | `dateparser` library | `YYYY-MM` (`2022-01`) |
| Country | ISO-3166 alpha-2 | `IN`, `US` |
| Skills | Explicit mapping + `rapidfuzz` | Canonical (`ml` → `Machine Learning`) |
| Links | URL prefix normalization | `https://linkedin.com/in/...` |
| Candidate ID | `uuid5(email)` or `uuid4()` | Deterministic UUID |

## 3. Merge Policy & Confidence
**Merge Rules**: Deterministic, reproducible conflict resolution.
- **Names**: Prefer longest non-empty string (`"John"` vs `"John Doe"` → `"John Doe"`).
- **Emails/Phones**: Unique aggregation (additive, never destructive).
- **Skills**: Deduplicate by canonical name, sort alphabetically for determinism.
- **Experience**: Deduplicate by `(company, title)` composite key.
- **Education**: Deduplicate by `(institution, degree)` composite key.

**Confidence Scoring**:
- CSV base: 0.90 | Resume base: 0.80
- Multi-source agreement: +0.05 (→ 0.95)
- Conflict detected: −0.20 (→ 0.75)
- Overall: weighted average of all non-null field scores

## 4. Runtime Configuration (Projection)
Clean separation between internal `CandidateProfile` and output. A JSON config controls:
- `path`: Output key name. `from`: JSON-path source (e.g., `emails[0]`, `skills[].name`).
- `on_missing`: `"null"` | `"omit"` | `"error"`. Toggle `include_confidence` / `include_provenance`.
- The projector parses array indexing and subfield extraction, then validates against the target schema.

## 5. Edge Cases & Scope
**Handled**:
1. **Missing source**: A missing PDF doesn't crash the pipeline — extraction logs a warning, processing continues with available data.
2. **Empty arrays**: Requesting `emails[0]` on an empty list returns `null` (or `omit`/`error` per config), never an IndexError.
3. **Conflicting names**: Deterministically resolved (longest wins), confidence penalized to signal uncertainty.
4. **"Present" in dates**: Stored as `null` — a deliberate choice meaning "current role", not a missing value.
5. **Skill variations**: `ml`, `machine-learning`, `Machine Learning` alldo collapse to a single canonical `"Machine Learning"`.

**Descoped**:
1. **Advanced NLP**: No spaCy/LLM for resume NER — heuristic section parsing is sufficient for this scope.
2. **Cross-candidate dedup**: This pipeline merges data for one known candidate. Entity resolution across candidates is a separate system.
