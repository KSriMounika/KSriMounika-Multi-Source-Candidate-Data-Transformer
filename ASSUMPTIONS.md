# Assumptions

1. **One candidate per run.** All input files (CSV row, Resume PDF) are assumed to belong to the same person. Cross-candidate entity resolution is out of scope.

2. **CSV is more reliable for contact details.** Structured sources like recruiter CSV exports are assigned a higher base confidence (0.90) than unstructured sources (0.80) for fields like name, email, and phone.

3. **Resume is preferred for skills and experience.** These fields are typically richer and more detailed in a resume than in a recruiter CSV export.

4. **Resume follows common section headings.** The PDF extractor relies on detecting headers like "Skills", "Education", "Experience", and "Links" to parse blocks. Non-standard headings will not be recognized.

5. **Missing values are returned as `null`, never invented.** If a field cannot be extracted from any source, it appears as `null` in the output. The pipeline never guesses or fabricates data.

6. **`"Present"` in experience dates is stored as `null`.** This is a deliberate design choice: `null` for `end` means "current role", distinguishing it from a truly missing date. This is documented in the output.

7. **Candidate IDs are generated deterministically.** We use `uuid5(email)` to produce the same ID for the same candidate across runs. If no email exists, we fall back to `uuid4()`.

8. **Country is normalized to ISO-3166 alpha-2.** `"India"` becomes `"IN"`, `"United States"` becomes `"US"`. Unrecognized country strings are returned as `null`.

9. **Skill canonicalization uses a two-tier approach.** First, an explicit mapping handles known abbreviations (`ml` → `Machine Learning`). Then, fuzzy matching via `rapidfuzz` catches variations above an 80% similarity threshold. Unmatched skills are title-cased and kept.

10. **Phone normalization defaults to India (+91).** The `phonenumbers` library uses `"IN"` as the default region when no country code is provided. Numbers with explicit country codes (e.g., `+1`) are parsed correctly regardless.
