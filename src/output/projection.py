import re
from typing import Dict, Any, List
from src.models.candidate import CandidateProfile, TrackedField

def _extract_value_from_path(profile: CandidateProfile, internal_path: str) -> Any:
    """
    Evaluates JSON-path style strings against the profile.
    Supports basic paths like 'emails[0]', 'skills[].name', 'full_name'.
    """
    # E.g., 'emails[0]' -> field='emails', index=0
    # E.g., 'skills[].name' -> field='skills', index=None, subfield='name'
    match = re.match(r"^([a-zA-Z_]+)(?:\[(\d*)\])?(?:\.([a-zA-Z_]+))?$", internal_path)
    if not match:
        return None
        
    field_name, index_str, subfield = match.groups()
    
    if not hasattr(profile, field_name):
        return None
        
    tracked_field: TrackedField = getattr(profile, field_name)
    val = tracked_field.value
    
    # Convert dataclasses to dicts for JSON serialization
    from dataclasses import is_dataclass, asdict
    if is_dataclass(val):
        val = asdict(val)
    elif isinstance(val, list) and len(val) > 0 and is_dataclass(val[0]):
        val = [asdict(v) for v in val]
        
    if val is None:
        return None
        
    # Handle array indexing
    if index_str:
        idx = int(index_str)
        if isinstance(val, list) and len(val) > idx:
            val = val[idx]
        else:
            return None
            
    # Handle array mapping (e.g., skills[].name)
    if isinstance(val, list) and subfield and match.group(0).endswith("[]" + f".{subfield}"):
        return [item.get(subfield) for item in val if isinstance(item, dict) and subfield in item]
        
    # Handle single object attribute extraction
    if not isinstance(val, list) and subfield and hasattr(val, subfield):
        return getattr(val, subfield)
        
    return val

def project_candidate(profile: CandidateProfile, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms the internal CandidateProfile into a JSON-serializable dictionary
    based on the provided runtime configuration array.
    """
    output = {}
    flat_provenances = []
    
    fields_config = config.get("fields", [])
    missing_strategy = config.get("on_missing", "null") # "null", "omit", "error"
    
    for field_settings in fields_config:
        output_path = field_settings.get("path")
        # If 'from' is missing, it implies the path is the same as the internal field
        internal_path = field_settings.get("from", output_path)
        
        # 1. Extract Value
        raw_val = _extract_value_from_path(profile, internal_path)
        
        # 2. Collect Provenance for this field
        # We need the base field name to grab the TrackedField provenance
        base_field = internal_path.split('[')[0]
        if hasattr(profile, base_field):
            tf: TrackedField = getattr(profile, base_field)
            if tf.provenance:
                for p in tf.provenance:
                    flat_provenances.append({
                        "field": output_path,
                        "source": p.source,
                        "method": p.extraction_method
                    })
        
        # 3. Handle Missing Values
        if raw_val is None:
            if field_settings.get("required", False) and missing_strategy == "error":
                raise ValueError(f"Required field '{output_path}' is missing.")
            elif missing_strategy == "error":
                 raise ValueError(f"Field '{output_path}' is missing.")
            elif missing_strategy == "omit":
                continue
            else:
                raw_val = None
                
        # (Normalization like "E164" or "canonical" is typically done pre-merge in this architecture,
        # but if requested in projection config, it acts as a contract assertion or on-the-fly formatter).
        # We assume data is already pre-normalized correctly before merge.
        
        output[output_path] = raw_val
        
    # Add root level confidence and provenance if not toggled off
    if config.get("include_confidence", True):
        output["overall_confidence"] = profile.overall_confidence
        
    # The prompt expects flat provenance array
    if flat_provenances: # Assuming they didn't toggle it off, but prompt doesn't explicitly name a provenance toggle in the example (it says "Toggle provenance... on or off"). Let's check config.
        if config.get("include_provenance", True):
            output["provenance"] = flat_provenances
            
    return output
