import dateparser
from typing import Optional

def normalize_date(raw_date: str) -> Optional[str]:
    """
    Parses a date string (e.g., 'Jan 2020', '01/2020', '2020') 
    and normalizes it to YYYY-MM.
    Returns None if the date is invalid or empty.
    """
    if not raw_date or not isinstance(raw_date, str):
        return None
        
    # dateparser is very forgiving and can parse almost any human date format
    parsed_date = dateparser.parse(raw_date)
    
    if parsed_date:
        return parsed_date.strftime("%Y-%m")
    
    return None
