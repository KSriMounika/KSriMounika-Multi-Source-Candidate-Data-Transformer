from typing import List, Optional
from src.models.candidate import Skill

def merge_names(names: List[Optional[str]]) -> Optional[str]:
    """
    Rule: Prefer longer non-empty names.
    e.g., ["John", "John Doe", None] -> "John Doe"
    """
    valid_names = [n.strip() for n in names if n and isinstance(n, str) and n.strip()]
    if not valid_names:
        return None
    # Sort by length descending, and take the first one
    return sorted(valid_names, key=len, reverse=True)[0]

def merge_unique_strings(values: List[Optional[str]]) -> List[str]:
    """
    Rule: Merge unique strings (used for emails and phone numbers).
    e.g., ["a@b.com", "a@b.com", "c@d.com"] -> ["a@b.com", "c@d.com"]
    """
    valid_values = [v.strip() for v in values if v and isinstance(v, str) and v.strip()]
    
    # Use a dictionary to maintain insertion order while removing duplicates
    # This is a Python 3.7+ trick for ordered sets
    return list(dict.fromkeys(valid_values))

def merge_skills(skills_lists: List[List[Skill]]) -> List[Skill]:
    """
    Rule: Merge duplicate skills after normalization.
    Assuming the skills have already been normalized before being passed here.
    """
    unique_skill_names = {}
    for skill_list in skills_lists:
        if not skill_list: continue
        for skill in skill_list:
            if skill.name not in unique_skill_names:
                unique_skill_names[skill.name] = skill
    
    return list(unique_skill_names.values())

def merge_experiences(exp_lists: List[List[Any]]) -> List[Any]:
    unique = {}
    for exp_list in exp_lists:
        if not exp_list: continue
        for exp in exp_list:
            key = f"{exp.company}_{exp.title}"
            if key not in unique:
                unique[key] = exp
    return list(unique.values())

def merge_educations(edu_lists: List[List[Any]]) -> List[Any]:
    unique = {}
    for edu_list in edu_lists:
        if not edu_list: continue
        for edu in edu_list:
            key = f"{edu.institution}_{edu.degree}"
            if key not in unique:
                unique[key] = edu
    return list(unique.values())

def merge_links(links_list: List[Any]) -> Any:
    # We'll just grab the first non-empty links object since they usually come from one source,
    # or we merge the dictionaries.
    from src.models.candidate import Links
    merged = Links()
    for links in links_list:
        if not links: continue
        if links.linkedin and not merged.linkedin: merged.linkedin = links.linkedin
        if links.github and not merged.github: merged.github = links.github
        if links.portfolio and not merged.portfolio: merged.portfolio = links.portfolio
        if links.other: merged.other.extend(links.other)
    # Deduplicate other
    merged.other = list(dict.fromkeys(merged.other))
    return merged
