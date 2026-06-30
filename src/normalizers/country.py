from typing import Optional

# A small dictionary for demonstration. 
# In a real system, you would use the `pycountry` library for comprehensive mapping.
COUNTRY_MAPPING = {
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "india": "IN",
    "canada": "CA",
    "germany": "DE"
}

def normalize_country(raw_country: str) -> Optional[str]:
    """
    Normalizes a country name to its ISO-3166 Alpha-2 code.
    """
    if not raw_country or not isinstance(raw_country, str):
        return None
        
    cleaned = raw_country.strip().lower()
    
    # Exact match on alpha-2
    if len(cleaned) == 2 and cleaned.upper() in COUNTRY_MAPPING.values():
        return cleaned.upper()
        
    # Match using our mapping dictionary
    if cleaned in COUNTRY_MAPPING:
        return COUNTRY_MAPPING[cleaned]
        
    return None
