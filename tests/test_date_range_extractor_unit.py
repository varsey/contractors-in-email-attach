import unittest
from src.modules.parsers.date_range_extractor import extract_date_range

class TestDateRangeExtractor(unittest.TestCase):
    def test_explicit_date_ranges(self):
        test_cases = [
            {
                'text': 'Акт сверки ООО "АМИЛКО" 01.01.2025 - 30.11.2025',
                'expected': '2025-01-01 to 2025-11-30'
            },
            {
                'text': 'Прошу направить Акт сверки за период с 01.01.2025 - 26.11.2025',
                'expected': '2025-01-01 to 2025-11-26'
            }
        ]
        for case in test_cases:
            result = extract_date_range(case['text'])
            formatted = f"{result['start_month']} to {result['end_month']}"
            self.assertEqual(formatted, case['expected'], f"Failed for: {case['text']}")

    def test_quarters(self):
        test_cases = [
            {
                'text': 'Прошу предоставить акт сверки за 3 кв. 2025 г.',
                'expected': '2025-07-01 to 2025-09-30'
            },
            {
                'text': 'Акт сверки 4кв 2024г',
                'expected': '2024-10-01 to 2024-12-31'
            }
        ]
        for case in test_cases:
            result = extract_date_range(case['text'])
            formatted = f"{result['start_month']} to {result['end_month']}"
            self.assertEqual(formatted, case['expected'], f"Failed for: {case['text']}")

    def test_full_year(self):
        # The current implementation requires "год" or similar after the digits for full year extraction
        result = extract_date_range('акт сверки за 2024 год')
        formatted = f"{result['start_month']} to {result['end_month']}"
        self.assertEqual(formatted, '2024-01-01 to 2024-12-31')

    def test_no_match(self):
        result = extract_date_range('Добрый день! Как дела?')
        self.assertFalse(result['success'])

if __name__ == '__main__':
    unittest.main()
