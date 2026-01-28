import unittest
from src.modules.parsers.text import TextParser

class TestTextParser(unittest.TestCase):
    def setUp(self):
        self.parser = TextParser()

    def test_clean_text(self):
        text = "Hello, world!  №123\nNew line."
        cleaned = self.parser.clean_text(text)
        # clean_text removes punctuation including '.'
        self.assertEqual(cleaned, "Hello world 123 New line ")
        
        # Test consecutive duplicates
        text_dupes = "test test test test word word"
        cleaned_dupes = self.parser.clean_text(text_dupes)
        self.assertIn("test", cleaned_dupes)
        self.assertIn("word", cleaned_dupes)

    def test_parse_inn(self):
        # 10 digits INN (Juridical)
        # Valid 10 digit INN from a known region (e.g., Moscow 77)
        valid_inn10 = "ИНН 7701000000"
        self.assertEqual(self.parser.parse_inn(valid_inn10), "7701000000")
        
        # 12 digits INN (Individual)
        valid_inn12 = "ИНН 770100000000"
        self.assertEqual(self.parser.parse_inn(valid_inn12), "770100000000")
        
        # INN with noise - note: yargy parser might be sensitive to format
        noise_inn = "инн 7701000000 " 
        self.assertEqual(self.parser.parse_inn(noise_inn), "7701000000")

    def test_parse_bik(self):
        # Valid BIK
        bik = "БИК 044525225"
        self.assertEqual(self.parser.parse_bik(bik), "044525225")
        
        # BIK with O instead of 0
        bik_o = "БИК О44525225"
        self.assertEqual(self.parser.parse_bik(bik_o), "044525225")

    def test_parse_r_account(self):
        # Valid settlement account
        acc = "р/с 40702810123456789012"
        self.assertEqual(self.parser.parse_r_account(acc), "40702810123456789012")
        
        # Account in long string
        acc_long = "Settlement account 40702810123456789012 in bank"
        self.assertEqual(self.parser.parse_r_account(acc_long), "40702810123456789012")

    def test_parse_tel(self):
        # Various phone formats
        self.assertEqual(self.parser.parse_tel("тел 8 900 123 45 67"), "89001234567")
        self.assertEqual(self.parser.parse_tel("моб тел 79001234567"), "79001234567")
        self.assertEqual(self.parser.parse_tel("No phone here"), "")

if __name__ == '__main__':
    unittest.main()
