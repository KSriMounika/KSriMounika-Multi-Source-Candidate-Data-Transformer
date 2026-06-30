# Multi-Source Candidate Data Transformer — Technical Design

**Author:** Mounika | **Assignment:** Eightfold Engineering Intern (Jul–Dec 2026)

---

## Pipeline Architecture

```
CSV (Structured) ──►┐                                                              
                     ├─► Normalize ──► Merge Engine ──► Confidence ──► Projection ──► Validate ──► Output JSON
Resume PDF (Unstructured) ──►┘                                                              
```

**Stage 1 — Extract:** `CSVExtractor` reads structured rows via pandas. `PDFExtractor` parses resume PDF via pdfplumber using section-heading detection (Skills, Education, Experience, Links, Location) and regex patterns for emails, phones, and URLs.

**Stage 2 — Normalize:** Pure functions transform raw values into canonical formats before merging:
| Field | Format | Method |
|-------|--------|--------|
| Phones | E.164 (`+919876543210`) | `phonenumbers` library, default region IN |
| Dates | `YYYY-MM` (`2022-01`) | `dateparser` with explicit format coercion |
| Country | ISO-3166 alpha-2 (`IN`) | Dictionary lookup from common names |
| Skills | Canonical names (`Machine Learning`) | Explicit alias map → `rapidfuzz` fuzzy match (≥80%) → title-case fallback |

**Stage 3 — Merge:** Deterministic conflict resolution per field:
| Field | Strategy | Rationale |
|-------|----------|-----------|
| `full_name` | Longest non-empty string | Resume often has full name; CSV may truncate |
| `emails`, `phones` | Union (deduplicated, insertion-order) | Both sources contribute valid, distinct values |
| `skills` | Deduplicate by canonical name, sort alphabetically | Ensures deterministic output across runs |
| `experience`, `education` | Deduplicate by composite key `(company, title)` / `(institution, degree)` | Prevents duplicating the same entry |
| `candidate_id` | `uuid5(email)`, fallback `uuid4()` | Same email always produces the same ID |

**Stage 4 — Confidence Scoring:**
| Scenario | Score | Logic |
|----------|-------|-------|
| CSV + Resume agree | **0.95** | Cross-source agreement bonus |
| CSV only | **0.90** | Structured source, high base reliability |
| Resume only | **0.80** | Heuristic parsing, slightly lower trust |
| Conflict detected | **0.75** | Penalty applied (`0.95 − 0.20`) |
| `overall_confidence` | Weighted average of all non-null field scores | Holistic profile quality metric |

## Canonical Schema & Runtime Configuration

The internal `CandidateProfile` dataclass holds all fields with `TrackedField` wrappers that carry `value`, `provenance[]`, and `confidence`. A **Projection Layer** then reshapes this internal record into the requested output using a JSON config — no code changes required. The config supports:
- **Field selection & remapping:** `"from": "emails[0]"` extracts the first email as `primary_email`.
- **Array mapping:** `"from": "skills[].name"` flattens skill objects into a string array.
- **Toggles:** `include_confidence`, `include_provenance` (on/off).
- **Missing-value policy:** `"on_missing": "null" | "omit" | "error"`.

Output is validated against a JSON Schema (`jsonschema`) before returning. Invalid output raises an error — bad data never passes silently.

## Edge Cases Handled

1. **Missing/garbage source:** If the PDF is missing or unreadable, the pipeline continues with CSV-only data and adjusts confidence downward. It never crashes.
2. **Conflicting names:** CSV says "John", Resume says "John Doe" — merge picks the longest non-empty string and records both sources in provenance.
3. **Malformed phone numbers:** Invalid strings return `null` instead of a corrupt value. Wrong-but-confident is worse than honestly-empty.
4. **Duplicate skills across sources:** `"ml"` from CSV and `"Machine Learning"` from Resume are canonicalized to the same skill, merged with confidence 0.95, and both sources tracked.
5. **"Present" in experience dates:** Stored as `null` for `end` (not the string "Present"), meaning "current role" — distinguishable from a truly missing date.

## Descoped Under Time Pressure

- **Cross-candidate entity resolution** (determining if two rows are the same person).
- **Advanced NLP / LLM extraction** (spaCy NER would improve Resume parsing accuracy).
- **DOCX / GitHub / LinkedIn source types** (architecture supports adding new extractors without modifying the pipeline).
