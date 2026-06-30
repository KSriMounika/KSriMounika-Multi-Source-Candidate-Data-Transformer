import unittest
from src.normalizers.phone import normalize_phone

class TestPhoneNormalization(unittest.TestCase):
    def test_us_phone(self):
        # Even with IN as default, it should parse US numbers if country code is given
        self.assertEqual(normalize_phone("+14155552671"), "+14155552671")

    def test_in_phone_default(self):
        # 10 digit number without country code should default to IN (+91)
        self.assertEqual(normalize_phone("9876543210"), "+919876543210")
        
    def test_malformed_phone(self):
        # Invalid phone should return None
        self.assertIsNone(normalize_phone("abc1234567"))
        self.assertIsNone(normalize_phone(""))
        self.assertIsNone(normalize_phone(None))

if __name__ == '__main__':
    unittest.main()
