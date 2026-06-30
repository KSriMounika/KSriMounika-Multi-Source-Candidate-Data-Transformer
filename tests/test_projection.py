import unittest
from src.output.projection import project_candidate
from src.models.candidate import CandidateProfile, TrackedField

class TestProjection(unittest.TestCase):
    def test_project_candidate_mapping(self):
        # Create a mock profile
        profile = CandidateProfile()
        profile.full_name = TrackedField(value="Jane Doe")
        profile.emails = TrackedField(value=["jane@example.com"])
        
        # Test config mapping emails[0] to primary_email
        config = {
            "fields": [
                {"path": "full_name"},
                {"path": "primary_email", "from": "emails[0]"}
            ],
            "include_confidence": False,
            "on_missing": "omit"
        }
        
        result = project_candidate(profile, config)
        
        self.assertEqual(result["full_name"], "Jane Doe")
        self.assertEqual(result["primary_email"], "jane@example.com")
        self.assertNotIn("overall_confidence", result)

if __name__ == '__main__':
    unittest.main()
