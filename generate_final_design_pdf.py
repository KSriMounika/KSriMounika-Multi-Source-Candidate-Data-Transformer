from fpdf import FPDF
from fpdf.enums import XPos, YPos

class FinalDesignPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "Multi-Source Candidate Data Transformer", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 5, "Author: Keerthi Sri Mounika | Assignment: Eightfold Engineering Intern (Jul-Dec 2026)", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.line(10, self.get_y()+2, 200, self.get_y()+2)
        self.ln(4)

pdf = FinalDesignPDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=10)
pdf.add_page()

# --- Objective & Approach (From Mounika's text) ---
pdf.set_font("Helvetica", "B", 9)
pdf.cell(0, 5, "Objective & Approach", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Helvetica", "", 8)
pdf.multi_cell(0, 4, "Develop a configurable pipeline that transforms candidate data from multiple sources (Structured CSV & Unstructured PDF) into a single canonical profile. The system extracts information, normalizes data, merges conflicting values using deterministic rules, computes confidence scores, tracks provenance, and generates schema-valid JSON output. A runtime projection layer enables customization of the output schema without modifying the core engine.")
pdf.ln(2)

# --- Pipeline Architecture ---
pdf.set_font("Helvetica", "B", 9)
pdf.cell(0, 5, "Pipeline Architecture", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Courier", "", 8)
pdf.cell(0, 4, "CSV (Structured) -----+", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.cell(0, 4, "                      +--> Normalize --> Merge Engine --> Confidence --> Projection --> Validate --> Output JSON", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.cell(0, 4, "Resume PDF (Unstr.) --+", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(2)

# --- Normalization ---
pdf.set_font("Helvetica", "B", 9)
pdf.cell(0, 5, "Canonical Schema & Normalization", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Helvetica", "B", 8)
col_w = [25, 45, 120]
for i, h in enumerate(["Field", "Format", "Method"]):
    pdf.cell(col_w[i], 5, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 8)
rows = [
    ["Phones", "E.164 (+919876543210)", "phonenumbers library, default region IN"],
    ["Dates", "YYYY-MM (2022-01)", "dateparser with explicit format coercion"],
    ["Country", "ISO-3166 alpha-2 (IN)", "Dictionary lookup from common country names"],
    ["Skills", "Canonical (Machine Learning)", "Explicit alias map -> rapidfuzz fuzzy match (>=80%) -> fallback"],
]
for row in rows:
    for i, val in enumerate(row):
        pdf.cell(col_w[i], 4.5, val, border=1)
    pdf.ln()
pdf.ln(2)

# --- Merge Strategy ---
pdf.set_font("Helvetica", "B", 9)
pdf.cell(0, 5, "Merge & Conflict-Resolution Policy", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Helvetica", "B", 8)
merge_col = [30, 60, 100]
for i, h in enumerate(["Field", "Strategy", "Rationale"]):
    pdf.cell(merge_col[i], 5, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 8)
merge_rows = [
    ["full_name", "Longest non-empty string", "Resume often has full name; CSV may truncate"],
    ["emails, phones", "Union (deduplicated, insertion-order)", "Both sources contribute valid, distinct values"],
    ["skills", "Deduplicate canonical name, sort A-Z", "Ensures deterministic output across runs"],
    ["experience", "Deduplicate by (company, title) key", "Prevents duplicating the same role"],
    ["education", "Deduplicate by (institution, degree)", "Prevents duplicating the same degree"],
    ["candidate_id", "uuid5(email), fallback uuid4()", "Same email always produces the same ID"],
]
for row in merge_rows:
    for i, val in enumerate(row):
        pdf.cell(merge_col[i], 4.5, val, border=1)
    pdf.ln()
pdf.ln(2)

# --- Confidence ---
pdf.set_font("Helvetica", "B", 9)
pdf.cell(0, 5, "Confidence Scoring", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Helvetica", "B", 8)
conf_col = [45, 20, 125]
for i, h in enumerate(["Scenario", "Score", "Logic"]):
    pdf.cell(conf_col[i], 5, h, border=1)
pdf.ln()
pdf.set_font("Helvetica", "", 8)
conf_rows = [
    ["CSV + Resume agree", "0.95", "Cross-source agreement bonus"],
    ["CSV only", "0.90", "Structured source, high base reliability"],
    ["Resume only", "0.80", "Heuristic parsing, slightly lower trust"],
    ["Conflict detected", "0.75", "Penalty applied (0.95 - 0.20)"],
    ["overall_confidence", "Avg", "Weighted average of all non-null field scores"],
]
for row in conf_rows:
    for i, val in enumerate(row):
        pdf.cell(conf_col[i], 4.5, val, border=1)
    pdf.ln()
pdf.ln(2)

# --- Runtime Config ---
pdf.set_font("Helvetica", "B", 9)
pdf.cell(0, 5, "Runtime Configuration (Projection Layer & Validation)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Helvetica", "", 8)
pdf.multi_cell(0, 4, 'A Projection Layer reshapes the internal CandidateProfile (which stores value, provenance[], confidence) into the requested output using a JSON config without code changes. It supports: field selection & remapping ("from": "emails[0]"), array mapping ("from": "skills[].name"), toggles for confidence/provenance, and missing-value policies ("null" | "omit" | "error"). Output is strictly validated against jsonschema.')
pdf.ln(2)

# --- Edge Cases & Descoped ---
pdf.set_font("Helvetica", "B", 9)
pdf.cell(0, 5, "Edge Cases Handled & Limitations", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.set_font("Helvetica", "", 8)
edges = [
    "- Missing source / Malformed phones: Pipeline uses available data; invalid strings return null (wrong-but-confident is worse than empty).",
    "- Conflicting names / Duplicate skills: Picks longest string (names) or canonicalizes (skills), merges with high confidence, records both in provenance.",
    "- \"Present\" in dates: Stored as null for end_year, indicating a current role instead of a missing date.",
    "- Descoped (Scope Limitations): Cross-candidate entity resolution, advanced NLP/LLM extraction, and DOCX/API sources."
]
for e in edges:
    pdf.multi_cell(0, 4, e)
    pdf.ln(0.5)

pdf.output("C:/Users/keert/Downloads/Mounika_Eightfold.pdf")
