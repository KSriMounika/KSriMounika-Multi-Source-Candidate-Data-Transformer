import jsonschema
from typing import Dict, Any

def validate_output(output_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validates the generated JSON projection against a predefined JSON schema.
    Returns True if valid. Raises jsonschema.exceptions.ValidationError if invalid.
    """
    try:
        jsonschema.validate(instance=output_data, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"Validation Error: {e.message}")
        raise
