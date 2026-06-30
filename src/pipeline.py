import logging
import uuid
import datetime
from typing import Dict, Any, List

from src.models import CandidateProfile, TrackedField, Provenance
from src.models.candidate import Skill, Experience, Education, Links, Location
from src.extractors import CSVExtractor, PDFExtractor
from src.normalizers import normalize_phone, normalize_date, normalize_country
from src.normalizers.skills import normalize_skill
from src.merger.rules import merge_names, merge_unique_strings, merge_skills, merge_experiences, merge_educations, merge_links
from src.merger.confidence import calculate_field_confidence, calculate_overall_confidence
from src.output import project_candidate, validate_output
from src.utils.exceptions import ExtractionError

logger = logging.getLogger(__name__)

def run_pipeline(csv_path: str, pdf_path: str, config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    The main orchestrator. 
    Reads from sources -> Normalizes -> Merges -> Calculates Confidence -> Projects -> Validates
    """
    csv_data = {}
    pdf_data = {}
    
    # ── 1. EXTRACTION (with Error Handling) ──
    try:
        csv_records = CSVExtractor().extract(csv_path)
        if csv_records:
            csv_data = csv_records[0]
    except Exception as e:
        logger.warning(f"Could not extract from CSV {csv_path}: {e}")
        
    try:
        pdf_records = PDFExtractor().extract(pdf_path)
        if pdf_records:
            pdf_data = pdf_records[0]
    except Exception as e:
        logger.warning(f"Could not extract from PDF {pdf_path}: {e}")
        
    if not csv_data and not pdf_data:
        raise ExtractionError("Failed to extract data from all provided sources.")

    # ── 2. NORMALIZATION ──
    csv_phone = normalize_phone(csv_data.get("phone")) if csv_data.get("phone") else None
    pdf_phone = normalize_phone(pdf_data.get("phone")) if pdf_data.get("phone") else None

    # ── 3. MERGING & PROVENANCE ──
    profile = CandidateProfile()
    field_confidences = []

    # --- Candidate ID (deterministic: hash of primary email, or UUID fallback) ---
    primary_email = csv_data.get("email") or pdf_data.get("email")
    if primary_email:
        # Deterministic ID from email ensures same inputs -> same output
        candidate_id = str(uuid.uuid5(uuid.NAMESPACE_URL, primary_email))
    else:
        candidate_id = str(uuid.uuid4())
    profile.candidate_id = TrackedField(
        value=candidate_id,
        provenance=[Provenance("Pipeline", "deterministic_hash")],
        confidence=1.0
    )

    # --- Full Name ---
    names = [csv_data.get("name"), pdf_data.get("name")]
    merged_name = merge_names(names)
    
    name_provs = []
    if csv_data.get("name"): name_provs.append(Provenance("CSV", "column_mapping"))
    if pdf_data.get("name"): name_provs.append(Provenance("Resume", "first_line_heuristic"))
    
    has_name_conflict = (csv_data.get("name") and pdf_data.get("name") and 
                         csv_data.get("name") != pdf_data.get("name"))
    name_conf = calculate_field_confidence(name_provs, has_name_conflict)
    
    profile.full_name = TrackedField(value=merged_name, provenance=name_provs, confidence=name_conf)
    if merged_name: field_confidences.append(name_conf)

    # --- Emails ---
    csv_email = csv_data.get("email")
    pdf_email = pdf_data.get("email")
    merged_emails = merge_unique_strings([csv_email, pdf_email])
    
    email_provs = []
    if csv_email: email_provs.append(Provenance("CSV", "column_mapping"))
    if pdf_email: email_provs.append(Provenance("Resume", "regex_extraction"))
    
    email_conf = calculate_field_confidence(email_provs, has_conflict=False)
    profile.emails = TrackedField(value=merged_emails, provenance=email_provs, confidence=email_conf)
    if merged_emails: field_confidences.append(email_conf)

    # --- Phones ---
    merged_phones = merge_unique_strings([csv_phone, pdf_phone])
    
    phone_provs = []
    if csv_phone: phone_provs.append(Provenance("CSV", "column_mapping"))
    if pdf_phone: phone_provs.append(Provenance("Resume", "regex_extraction"))
    
    phone_conf = calculate_field_confidence(phone_provs, has_conflict=False)
    profile.phones = TrackedField(value=merged_phones, provenance=phone_provs, confidence=phone_conf)
    if merged_phones: field_confidences.append(phone_conf)

    # --- Skills (normalized + sorted alphabetically for determinism) ---
    csv_skills_raw = csv_data.get("skills", [])
    pdf_skills_raw = pdf_data.get("skills", [])
    
    # Build per-skill provenance to compute confidence dynamically
    csv_skill_names = set()
    csv_skills = []
    for s in csv_skills_raw:
        name = normalize_skill(s) if isinstance(s, str) else normalize_skill(s.get("name"))
        csv_skill_names.add(name)
        csv_skills.append(Skill(name=name, sources=["CSV"]))
    
    pdf_skill_names = set()
    pdf_skills = []
    for s in pdf_skills_raw:
        if not s.get("name"): continue
        name = normalize_skill(s.get("name"))
        pdf_skill_names.add(name)
        pdf_skills.append(Skill(name=name, sources=["Resume"]))
    
    merged_skills = merge_skills([csv_skills, pdf_skills])
    
    # Compute per-skill confidence dynamically
    for skill in merged_skills:
        in_csv = skill.name in csv_skill_names
        in_pdf = skill.name in pdf_skill_names
        if in_csv and in_pdf:
            skill.confidence = 0.95  # Agreement across sources
            skill.sources = ["CSV", "Resume"]
        elif in_csv:
            skill.confidence = 0.90  # Structured source only
        elif in_pdf:
            skill.confidence = 0.80  # Unstructured source only
    
    # Sort alphabetically for deterministic output
    merged_skills.sort(key=lambda s: s.name)
    
    skills_provs = []
    if csv_skills: skills_provs.append(Provenance("CSV", "column_mapping"))
    if pdf_skills: skills_provs.append(Provenance("Resume", "section_parsing"))
    skills_conf = calculate_field_confidence(skills_provs, False)
    profile.skills = TrackedField(value=merged_skills, provenance=skills_provs, confidence=skills_conf)
    if merged_skills: field_confidences.append(skills_conf)
    
    # --- Education (smart parsing: degree != institution) ---
    csv_edu_raw = csv_data.get("education", [])
    pdf_edu_raw = pdf_data.get("education", [])
    
    csv_edus = [Education(institution=e.get("institution"), degree=e.get("degree"), 
                          field=e.get("field"), 
                          end_year=int(e.get("end_year")) if e.get("end_year") else None) 
                for e in csv_edu_raw]
    pdf_edus = [Education(institution=e.get("institution"), degree=e.get("degree"), 
                          field=e.get("field"), end_year=e.get("end_year")) for e in pdf_edu_raw]
    
    merged_edus = merge_educations([csv_edus, pdf_edus])
    edu_provs = []
    if csv_edus: edu_provs.append(Provenance("CSV", "column_mapping"))
    if pdf_edus: edu_provs.append(Provenance("Resume", "section_parsing"))
    edu_conf = calculate_field_confidence(edu_provs, False)
    profile.education = TrackedField(value=merged_edus, provenance=edu_provs, confidence=edu_conf)
    if merged_edus: field_confidences.append(edu_conf)
    
    # --- Experience (dates already normalized to YYYY-MM by extractor) ---
    csv_exp_raw = csv_data.get("experience", [])
    pdf_exp_raw = pdf_data.get("experience", [])
    
    csv_exps = [Experience(company=e.get("company"), title=e.get("title"), 
                           start=e.get("start"), end=e.get("end"), 
                           summary=e.get("summary")) for e in csv_exp_raw]
    pdf_exps = [Experience(company=e.get("company"), title=e.get("title"), 
                           start=e.get("start"), end=e.get("end"), 
                           summary=e.get("summary")) for e in pdf_exp_raw]
    
    merged_exps = merge_experiences([csv_exps, pdf_exps])
    exp_provs = []
    if csv_exps: exp_provs.append(Provenance("CSV", "column_mapping"))
    if pdf_exps: exp_provs.append(Provenance("Resume", "section_parsing"))
    exp_conf = calculate_field_confidence(exp_provs, False)
    profile.experience = TrackedField(value=merged_exps, provenance=exp_provs, confidence=exp_conf)
    if merged_exps: field_confidences.append(exp_conf)
    
    # --- Years of Experience (computed from normalized YYYY-MM dates) ---
    total_years = 0.0
    for exp in merged_exps:
        if exp.start:
            try:
                start_date = datetime.datetime.strptime(exp.start, "%Y-%m")
                if exp.end:
                    end_date = datetime.datetime.strptime(exp.end, "%Y-%m")
                else:
                    # null end means "Present"
                    end_date = datetime.datetime.now()
                days = (end_date - start_date).days
                if days > 0:
                    total_years += days / 365.25
            except ValueError:
                pass
    if total_years > 0:
        years_provs = [Provenance("Pipeline", "date_computation")]
        years_conf = exp_conf
        profile.years_experience = TrackedField(
            value=round(total_years, 1), provenance=years_provs, confidence=years_conf
        )
        field_confidences.append(years_conf)
        
    # --- Headline (derived from experience or resume) ---
    headline = pdf_data.get("headline") or csv_data.get("headline")
    if headline:
        headline_provs = []
        if pdf_data.get("headline"): headline_provs.append(Provenance("Resume", "section_parsing"))
        if csv_data.get("headline"): headline_provs.append(Provenance("CSV", "column_mapping"))
        headline_conf = calculate_field_confidence(headline_provs, False)
        profile.headline = TrackedField(value=headline, provenance=headline_provs, confidence=headline_conf)
        field_confidences.append(headline_conf)

    # --- Location (country normalized to ISO-3166 alpha-2) ---
    pdf_loc = pdf_data.get("location", {})
    if pdf_loc:
        raw_country = pdf_loc.get("country")
        iso_country = normalize_country(raw_country) if raw_country else None
        loc = Location(
            city=pdf_loc.get("city"),
            region=pdf_loc.get("region"),
            country=iso_country
        )
        loc_provs = [Provenance("Resume", "section_parsing")]
        loc_conf = calculate_field_confidence(loc_provs, False)
        profile.location = TrackedField(value=loc, provenance=loc_provs, confidence=loc_conf)
        field_confidences.append(loc_conf)

    # --- Links (URLs normalized to https://) ---
    pdf_links_raw = pdf_data.get("links", {})
    links_obj = Links(
        linkedin=pdf_links_raw.get("linkedin"),
        github=pdf_links_raw.get("github")
    )
    merged_links = merge_links([links_obj])
    links_provs = []
    if pdf_links_raw: links_provs.append(Provenance("Resume", "regex_extraction"))
    links_conf = calculate_field_confidence(links_provs, False)
    profile.links = TrackedField(value=merged_links, provenance=links_provs, confidence=links_conf)
    if pdf_links_raw: field_confidences.append(links_conf)

    # ── 4. OVERALL CONFIDENCE ──
    profile.overall_confidence = calculate_overall_confidence(field_confidences)

    # ── 5. OUTPUT PROJECTION ──
    final_output = project_candidate(profile, config)

    # ── 6. VALIDATION ──
    validate_output(final_output, schema)

    return final_output
