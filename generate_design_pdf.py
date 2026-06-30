from fpdf import FPDF

class DesignPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "Multi-Source Candidate Data Transformer - Technical Design", ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "Author: Mounika  |  Assignment: Eightfold Engineering Intern (Jul-Dec 2026)", ln=True, align="C")
        self.line(10, self.get_y()+2, 200, self.get_y()+2)
        self.ln(4)

pdf = DesignPDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=10)
pdf.add_page()
pdf.set_font("Helvetica", "", 8.5)

# --- Pipeline Architecture ---
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 5, "Pipeline Architecture", ln=True)
pdf.set_font("Courier", "", 7.5)
pdf.cell(0, 4, "CSV (Structured) -----+", ln=True)
pdf.cell(0, 4, "                      +--> Normalize --> Merge Engine --> Confidence --> Projection --> Validate --> Output JSON", ln=True)
pdf.cell(0, 4, "Resume PDF (Unstructured) --+", ln=True)
pdf.ln(2)

pdf.set_font("Helvetica", "", 8)
pdf.multi_cell(0, 3.8, "Stage 1 - Extract: CSVExtractor reads structured rows via pandas. PDFExtractor parses resume PDF via pdfplumber using section-heading detection (Skills, Education, Experience, Links, Location) and regex patterns for emails, phones, and URLs.")
pdf.ln(1)
pdf.multi_cell(0, 3.8, "Stage 2 - Normalize: Pure functions transform raw values into canonical formats before merging.")

# Normalization table
pdf.set_font("Helvetica", "B", 8)
col_w = [25, 45, 120]
headers = ["Field", "Format", "Method"]
for i, h in enumerate(headers):
    pdf.cell(col_w[i], 4.5, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 7.5)
rows = [
    ["Phones", "E.164 (+919876543210)", "phonenumbers library, default region IN"],
    ["Dates", "YYYY-MM (2022-01)", "dateparser with explicit format coercion"],
    ["Country", "ISO-3166 alpha-2 (IN)", "Dictionary lookup from common country names"],
    ["Skills", "Canonical (Machine Learning)", "Explicit alias map -> rapidfuzz fuzzy match (>=80%) -> title-case fallback"],
]
for row in rows:
    for i, val in enumerate(row):
        pdf.cell(col_w[i], 4, val, border=1)
    pdf.ln()
pdf.ln(1)

pdf.set_font("Helvetica", "", 8)
pdf.multi_cell(0, 3.8, "Stage 3 - Merge: Deterministic conflict resolution per field. Stage 4 - Confidence: Dynamic scoring. Stage 5 - Projection: Reshapes internal record to requested JSON shape. Stage 6 - Validate: jsonschema enforcement.")
pdf.ln(1)

# --- Merge Strategy ---
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 5, "Merge / Conflict-Resolution Policy", ln=True)
pdf.set_font("Helvetica", "B", 8)
merge_col = [30, 55, 105]
for i, h in enumerate(["Field", "Strategy", "Rationale"]):
    pdf.cell(merge_col[i], 4.5, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 7.5)
merge_rows = [
    ["full_name", "Longest non-empty string", "Resume often has full name; CSV may truncate"],
    ["emails, phones", "Union (deduplicated, insertion-order)", "Both sources contribute valid, distinct values"],
    ["skills", "Deduplicate by canonical name, sort A-Z", "Ensures deterministic output across runs"],
    ["experience", "Deduplicate by (company, title) key", "Prevents duplicating the same role"],
    ["education", "Deduplicate by (institution, degree) key", "Prevents duplicating the same degree"],
    ["candidate_id", "uuid5(email), fallback uuid4()", "Same email always produces the same ID"],
]
for row in merge_rows:
    for i, val in enumerate(row):
        pdf.cell(merge_col[i], 4, val, border=1)
    pdf.ln()
pdf.ln(1)

# --- Confidence ---
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 5, "Confidence Scoring", ln=True)
pdf.set_font("Helvetica", "B", 8)
conf_col = [45, 20, 125]
for i, h in enumerate(["Scenario", "Score", "Logic"]):
    pdf.cell(conf_col[i], 4.5, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 7.5)
conf_rows = [
    ["CSV + Resume agree", "0.95", "Cross-source agreement bonus"],
    ["CSV only", "0.90", "Structured source, high base reliability"],
    ["Resume only", "0.80", "Heuristic parsing, slightly lower trust"],
    ["Conflict detected", "0.75", "Penalty applied (0.95 - 0.20)"],
    ["overall_confidence", "Avg", "Weighted average of all non-null field scores"],
]
for row in conf_rows:
    for i, val in enumerate(row):
        pdf.cell(conf_col[i], 4, val, border=1)
    pdf.ln()
pdf.ln(1)

# --- Runtime Config ---
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 5, "Runtime Configuration (Projection Layer)", ln=True)
pdf.set_font("Helvetica", "", 8)
pdf.multi_cell(0, 3.8, 'The internal CandidateProfile holds all fields with TrackedField wrappers (value, provenance[], confidence). A Projection Layer reshapes this into the requested output using a JSON config - no code changes required. Supports: field selection & remapping ("from": "emails[0]"), array mapping ("from": "skills[].name"), toggles for confidence/provenance, and missing-value policy ("on_missing": "null" | "omit" | "error"). Output is validated against jsonschema before returning.')
pdf.ln(1)

# --- Edge Cases ---
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 5, "Edge Cases Handled", ln=True)
pdf.set_font("Helvetica", "", 8)
edges = [
    "1. Missing/garbage source: Pipeline continues with available data; confidence adjusts downward. Never crashes.",
    "2. Conflicting names: CSV says \"John\", Resume says \"John Doe\" - picks longest string, records both in provenance.",
    "3. Malformed phones: Invalid strings return null. Wrong-but-confident is worse than honestly-empty.",
    "4. Duplicate skills: \"ml\" (CSV) and \"Machine Learning\" (Resume) canonicalize to same skill, confidence 0.95.",
    "5. \"Present\" in dates: Stored as null for end (not the string), meaning \"current role\".",
]
for e in edges:
    pdf.multi_cell(0, 3.8, e)
    pdf.ln(0.5)
pdf.ln(1)

# --- Descoped ---
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 5, "Deliberately Descoped", ln=True)
pdf.set_font("Helvetica", "", 8)
descoped = [
    "- Cross-candidate entity resolution (determining if two rows are the same person).",
    "- Advanced NLP / LLM extraction (spaCy NER would improve Resume parsing accuracy).",
    "- DOCX / GitHub / LinkedIn sources (architecture supports adding new extractors without modifying the pipeline).",
]
for d in descoped:
    pdf.cell(0, 3.8, d, ln=True)

pdf.output("C:/Users/keert/Downloads/Mounika_Eightfold.pdf")
print("PDF generated: C:/Users/keert/Downloads/Mounika_Eightfold.pdf")
