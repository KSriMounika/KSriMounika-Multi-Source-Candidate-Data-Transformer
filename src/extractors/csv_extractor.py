import pandas as pd
from typing import Dict, Any, List
from .base import BaseExtractor

class CSVExtractor(BaseExtractor):
    """
    Extracts candidate data from a Recruiter CSV.
    Assumes columns like: name, email, phone, current_company, title.
    """
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Replace pandas NaN values with Python's None for easier handling later
        df = df.where(pd.notnull(df), None)
        
        # Convert the DataFrame to a list of dictionaries
        # e.g., [{"name": "Alice", "email": "alice@test.com", ...}, ...]
        return df.to_dict(orient='records')
