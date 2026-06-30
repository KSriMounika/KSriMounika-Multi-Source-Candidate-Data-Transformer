import phonenumbers
from typing import Optional

def normalize_phone(raw_phone: str, default_region: str = "IN") -> Optional[str]:
    """
    Parses and formats a phone number to the E.164 standard (+1234567890).
    Returns None if the phone number is invalid or empty.
    """
    if not raw_phone or not isinstance(raw_phone, str):
        return None
        
    try:
        parsed_number = phonenumbers.parse(raw_phone, default_region)
        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        return None
    except phonenumbers.NumberParseException:
        # Gracefully handle malformed strings that phonenumbers can't parse
        return None
