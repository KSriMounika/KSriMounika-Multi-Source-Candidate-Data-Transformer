from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseExtractor(ABC):
    """
    Abstract base class for all data extractors.
    """
    @abstractmethod
    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts raw data from a given file.
        Returns a list of dictionaries, where each dictionary represents one candidate's raw data.
        """
        pass
