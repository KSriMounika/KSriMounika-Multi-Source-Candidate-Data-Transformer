import unittest
from src.merger.rules import merge_names, merge_unique_strings, merge_skills
from src.models.candidate import Skill

class TestMergerRules(unittest.TestCase):
    def test_merge_names(self):
        # Should prefer the longest non-empty string
        self.assertEqual(merge_names(["John", "John Doe", None]), "John Doe")
        self.assertEqual(merge_names([None, "Jane Smith"]), "Jane Smith")
        self.assertIsNone(merge_names([None, " "]))

    def test_merge_unique_strings(self):
        # Should remove duplicates while preserving order
        emails = ["a@b.com", "a@b.com", "c@d.com"]
        self.assertEqual(merge_unique_strings(emails), ["a@b.com", "c@d.com"])
        
    def test_merge_skills(self):
        # Should deduplicate skills by name
        csv_skills = [Skill(name="Python", confidence=0.9), Skill(name="SQL", confidence=0.9)]
        pdf_skills = [Skill(name="Python", confidence=0.8), Skill(name="Machine Learning", confidence=0.8)]
        
        merged = merge_skills([csv_skills, pdf_skills])
        self.assertEqual(len(merged), 3)
        self.assertEqual(merged[0].name, "Python")
        self.assertEqual(merged[0].confidence, 0.9) # Kept the first one encountered
        self.assertEqual(merged[1].name, "SQL")
        self.assertEqual(merged[2].name, "Machine Learning")

if __name__ == '__main__':
    unittest.main()
