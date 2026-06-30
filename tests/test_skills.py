import unittest
from src.normalizers.skills import normalize_skill

class TestSkillNormalization(unittest.TestCase):
    def test_explicit_mapping(self):
        # Should use SKILL_MAP
        self.assertEqual(normalize_skill("ml"), "Machine Learning")
        self.assertEqual(normalize_skill("machine-learning"), "Machine Learning")
        self.assertEqual(normalize_skill("python3"), "Python")

    def test_fuzzy_matching(self):
        # Should fuzzy match CANONICAL_SKILLS
        self.assertEqual(normalize_skill("Data Analysys"), "Data Analysis")
        self.assertEqual(normalize_skill("React.js"), "React")
        
    def test_fallback(self):
        # Should return title cased original if no match
        self.assertEqual(normalize_skill("Obscure Framework v9"), "Obscure Framework V9")
        
    def test_invalid_input(self):
        self.assertIsNone(normalize_skill(None))
        self.assertIsNone(normalize_skill(""))

if __name__ == '__main__':
    unittest.main()
