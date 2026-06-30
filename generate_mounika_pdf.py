from fpdf import FPDF
from fpdf.enums import XPos, YPos

class CustomPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 6, "Multi-Source Candidate Data Transformer - Technical Design", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, "Author: Keerthi Sri Mounika | Assignment: Eightfold Engineering Intern (Jul-Dec 2026)", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.line(10, self.get_y()+2, 200, self.get_y()+2)
        self.ln(4)

pdf = CustomPDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=10)
pdf.add_page()

# Ensure we use a small enough font to fit everything on one page if possible, though this is quite dense.
# We might need two pages for this much text, but the assignment asked for one page. We will use a compact font.
pdf.set_font("Helvetica", "", 7.5)

def add_section(title):
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 7.5)

# --- Pipeline Architecture ---
add_section("Pipeline Architecture")
diagram = """+-------------+   +-------------+   +-------------+   +-------------+   +-------------+
|  INGEST     |-->|  EXTRACT    |-->|  NORMALIZE  |-->|  MERGE      |-->|  PROJECT    |
|  (Parsers)  |   |  (Extractors)|  |  (Normalizers)|  |  (Merger)   |   |  (Config)   |
+-------------+   +-------------+   +-------------+   +-------------+   +-------------+
      |               |               |               |               |
      v               v               v               v               v
  CSV/PDF          Raw dicts      E.164 phones   Unified record   Custom schema
  -> raw text       per source     YYYY-MM dates  + provenance     + validation
                   + meta         Canonical skills + confidence    (JSON output)"""
pdf.set_font("Courier", "", 6.5)
for line in diagram.split('\n'):
    pdf.cell(0, 3, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Helvetica", "", 7.5)
pdf.ln(1)
steps = [
    "Ingest - CSVParser (structured), ResumeParser (unstr., pdfplumber) read files; return raw text + warnings (never crash).",
    "Extract - ResumeExtractor uses deterministic regex/keyword matching to pull structured fields from resume text.",
    "Normalize - Pure functions: normalize_phone() (E.164), parse_date_to_ym() (YYYY-MM), canonicalize_skills() (rapidfuzz>=80).",
    "Merge - Deterministic field-level rules. Builds CanonicalProfile with ProvenanceEntry per field.",
    "Project - ProjectionEngine reads config, maps paths (supports []), applies per-field normalization, validates via JSON Schema."
]
for s in steps:
    pdf.multi_cell(0, 3.5, s)

# --- Canonical Schema & Normalized Formats ---
add_section("Canonical Schema & Normalized Formats")
pdf.set_font("Helvetica", "B", 7)
col_w1 = [30, 40, 115]
for i, h in enumerate(["Field", "Type", "Normalization"]):
    pdf.cell(col_w1[i], 4, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 7)
schema_rows = [
    ["candidate_id", "string", "Deterministic UUIDv5 (SHA-256 of email|name)"],
    ["full_name", "string", "Title-case, trimmed"],
    ["emails", "string[]", "Lowercase, RFC-5322 basic, deduped"],
    ["phones", "string[]", "E.164 via phonenumbers (default region: IN)"],
    ["location", "{city,region,country}", "Country = ISO-3166 alpha-2"],
    ["links", "{linkedin,github,portfolio...}", "Fully qualified URLs"],
    ["headline", "string|null", "First descriptive line >20 chars"],
    ["years_experience", "number|null", "Sum of (end-start) months across experience / 12"],
    ["skills", "{name,confidence,sources[]}[]", "Canonical names (ML -> Machine Learning)"],
    ["experience", "{company,title,start,end...}[]", "Dates = YYYY-MM; end=null for 'Present'"],
    ["education", "{institution,degree...}[]", "end_year = YYYY-MM"],
    ["provenance", "{field,source,method}[]", "One entry per output field"],
    ["overall_confidence", "number", "Weighted average"]
]
for row in schema_rows:
    for i, val in enumerate(row):
        pdf.cell(col_w1[i], 3.5, val, border=1)
    pdf.ln()

# --- Merge & Conflict-Resolution Policy ---
add_section("Merge & Conflict-Resolution Policy")
pdf.set_font("Helvetica", "B", 7)
col_w2 = [30, 50, 105]
for i, h in enumerate(["Field", "Strategy", "Tie-Break Rationale"]):
    pdf.cell(col_w2[i], 4, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 7)
merge_rows = [
    ["full_name", "Longest non-empty string", "Resume often has full name; CSV may truncate"],
    ["emails, phones", "Union (deduped, insertion-order)", "Both sources contribute valid, distinct values"],
    ["skills", "Union after canonicalization", "Ensures deterministic output across runs"],
    ["experience, education", "Concat all, dedupe by keys", "Prevents duplicating the same role/degree"],
    ["company, title", "Prefer structured source (CSV)", "CSV weight 0.90 > Resume 0.80"],
    ["location, headline", "Prefer resume (richer)", "-"]
]
for row in merge_rows:
    for i, val in enumerate(row):
        pdf.cell(col_w2[i], 3.5, val, border=1)
    pdf.ln()
pdf.multi_cell(0, 3.5, "Missing values -> null (never invented). Provenance: Every output field gets {field, source, method} where method in {Exact Match, Regex Extract, Canonical Map, Fuzzy Match>=80, Date Parse, Union Merge}.")

# --- Confidence Scoring ---
add_section("Confidence Scoring")
score_logic = [
    "field_confidence = max(source_weight)  // single source",
    "field_confidence = 1 - product(1 - w_i)  // multiple agree (union)",
    "field_confidence *= 0.7  // conflicting values",
    "overall_confidence = Sum(field_confidence x importance) / Sum(importance)"
]
pdf.set_font("Courier", "", 7)
for s in score_logic:
    pdf.cell(0, 3, s, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.set_font("Helvetica", "", 7)
pdf.ln(1)
pdf.multi_cell(0, 3.5, "Weights: Recruiter CSV (0.90), Resume PDF (0.80). Importance: emails, skills (1.0), phones, experience (0.8), education (0.7), name, years_exp (0.6), headline, location (0.5), links (0.4).")
pdf.multi_cell(0, 3.5, "Results: CSV + Resume agree -> 0.95 | CSV only -> 0.90 | Resume only -> 0.80 | Conflict detected -> 0.75")

# --- Runtime Configuration ---
add_section("Runtime Configuration (Projection Layer & Validation)")
pdf.multi_cell(0, 3.5, "A Projection Layer reshapes the internal CandidateProfile into the requested output using a JSON config without code changes. Capabilities include: Field selection & remapping ('from': 'emails[0]'), Array mapping ('from': 'skills[].name'), Per-field normalization, Toggles for include_confidence/include_provenance, and Missing-value policy ('null' | 'omit' | 'error'). Output is validated via jsonschema (Draft 2020-12).")

# --- Edge Cases Handled ---
add_section("Edge Cases Handled")
pdf.set_font("Helvetica", "B", 7)
col_w3 = [45, 140]
for i, h in enumerate(["Edge Case", "Handling"]):
    pdf.cell(col_w3[i], 4, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 7)
edge_rows = [
    ["Missing/empty source file", "Parser returns empty candidate list + warning; pipeline continues with other sources"],
    ["Corrupted/scanned PDF (no text)", "Extractor returns empty fields; confidence drops; provenance notes 'No text'"],
    ["Conflicting phone/email", "Union merge (both kept); confidence reduced by 30%; provenance lists both sources"],
    ["Unknown skill not in dictionary", "Kept as-is with confidence=0.5, method='Raw Extract'"],
    ["'Present' in dates", "Stored as end=null for current role (not missing)"]
]
for row in edge_rows:
    for i, val in enumerate(row):
        pdf.cell(col_w3[i], 3.5, val, border=1)
    pdf.ln()

# --- Assumptions & Scope Limitations ---
add_section("Assumptions & Scope Limitations (Time-Boxed)")
pdf.multi_cell(0, 3.5, "Assumptions: Single candidate per run. Phone region defaults to IN. Skills dictionary covers top tech skills; extensible via config.")
pdf.multi_cell(0, 3.5, "Deliberately Left Out: Cross-candidate entity resolution, advanced NLP/LLM extraction, API sources (LinkedIn, GitHub), OCR, database persistence, auth/UI.")

pdf.output("C:/Users/keert/Downloads/Mounika_Eightfold.pdf")
