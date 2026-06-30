import re
import pdfplumber
from typing import Dict, Any, List
from .base import BaseExtractor
from src.normalizers.date import normalize_date

# Known degree keywords for classifying education lines
DEGREE_KEYWORDS = ["b.tech", "m.tech", "bsc", "msc", "ba", "ma", "mba", "phd", "b.e", "m.e",
                    "bachelor", "master", "associate", "diploma"]

def _normalize_link(url: str) -> str:
    """Ensure links start with https://"""
    url = url.strip()
    if url and not url.startswith("http"):
        url = "https://" + url
    return url

def _parse_education_line(line: str) -> Dict[str, Any]:
    """
    Parses a single education line like:
    'B.Tech, Computer Science, ABC University, 2021'
    Returns a dict with degree, field, institution, end_year.
    """
    parts = [p.strip() for p in line.split(",")]
    edu = {"institution": None, "degree": None, "field": None, "end_year": None}
    
    for part in parts:
        # Check if it's a year
        year_match = re.match(r"^(19|20)\d{2}$", part)
        if year_match:
            edu["end_year"] = int(part)
            continue
        # Check if it's a degree keyword
        if any(kw in part.lower() for kw in DEGREE_KEYWORDS):
            edu["degree"] = part
            continue
        # Check if it could be a field of study (shorter text, no digits)
        if edu["degree"] and not edu["field"] and not re.search(r"\d", part):
            edu["field"] = part
            continue
        # Otherwise treat as institution
        if not edu["institution"]:
            edu["institution"] = part
    
    return edu

class PDFExtractor(BaseExtractor):
    """
    Extracts candidate data from an unstructured Resume PDF.
    Uses section-based heuristic parsing and regex extraction.
    """
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # 1. Regex extractions
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        
        # 2. Heuristics for name: first non-empty line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        name = lines[0] if lines else None
        
        # 3. Section-based block extraction
        skills = []
        education = []
        experience = []
        links = {}
        location = {}
        
        current_section = None
        section_headers = {"skills", "education", "experience", "links", "location"}
        
        for line in lines:
            lower = line.lower().strip()
            if lower in section_headers:
                current_section = lower
                continue
                
            if current_section == "skills":
                skills.append({"name": line})
                
            elif current_section == "education":
                edu = _parse_education_line(line)
                education.append(edu)
                
            elif current_section == "experience":
                # Heuristic: title -> company -> date range
                if len(experience) == 0 or experience[-1]["start"] is not None:
                    experience.append({
                        "title": line, "company": None,
                        "start": None, "end": None, "summary": None
                    })
                elif experience[-1]["company"] is None:
                    experience[-1]["company"] = line
                elif experience[-1]["start"] is None:
                    parts = line.split('-')
                    raw_start = parts[0].strip()
                    raw_end = parts[1].strip() if len(parts) > 1 else None
                    # Normalize dates to YYYY-MM
                    experience[-1]["start"] = normalize_date(raw_start)
                    if raw_end and raw_end.lower() == "present":
                        experience[-1]["end"] = None  # null means "current"
                    else:
                        experience[-1]["end"] = normalize_date(raw_end)
                        
            elif current_section == "links":
                if "linkedin" in line.lower():
                    links["linkedin"] = _normalize_link(line.split(":", 1)[-1].strip())
                elif "github" in line.lower():
                    links["github"] = _normalize_link(line.split(":", 1)[-1].strip())
                    
            elif current_section == "location":
                # Parse "City, Region, Country" or individual lines
                loc_parts = [p.strip() for p in line.split(",")]
                if len(loc_parts) >= 3:
                    location = {"city": loc_parts[0], "region": loc_parts[1], "country": loc_parts[2]}
                elif len(loc_parts) == 2:
                    location = {"city": loc_parts[0], "country": loc_parts[1]}
                elif len(loc_parts) == 1:
                    location = {"city": loc_parts[0]}
        
        # 4. Derive headline from first experience entry
        headline = None
        if experience:
            title = experience[0].get("title")
            company = experience[0].get("company")
            if title and company:
                headline = f"{title} at {company}"
            elif title:
                headline = title
        
        candidate_data = {
            "name": name,
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0) if phone_match else None,
            "skills": skills,
            "education": education,
            "experience": experience,
            "links": links,
            "location": location,
            "headline": headline,
            "raw_text": text 
        }
        
        return [candidate_data]
