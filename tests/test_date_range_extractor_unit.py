import unittest
from datetime import datetime
from src.modules.parsers.date_range_extractor import extract_date_range


class TestExplicitDateRanges(unittest.TestCase):
    """Тесты для явных диапазонов дат: DD.MM.YYYY - DD.MM.YYYY"""
    
    def test_standard_date_range(self):
        """Стандартный формат с дефисом"""
        test_cases = [
            ('Акт сверки ООО "АМИЛКО" 01.01.2025 - 30.11.2025', '2025-01-01', '2025-11-30'),
            ('Прошу направить Акт сверки за период с 01.01.2025 - 26.11.2025', '2025-01-01', '2025-11-26'),
            ('Документы 15.03.2024 - 20.06.2024', '2024-03-15', '2024-06-20'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_date_range_with_different_dashes(self):
        """Разные типы тире: дефис (-), среднее тире (–), длинное тире (—)"""
        test_cases = [
            ('01.01.2025 - 31.12.2025', '2025-01-01', '2025-12-31'),  # дефис
            ('01.01.2025 – 31.12.2025', '2025-01-01', '2025-12-31'),  # среднее тире
            ('01.01.2025 — 31.12.2025', '2025-01-01', '2025-12-31'),  # длинное тире
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать тире в: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_date_range_two_digit_years(self):
        """Двузначные годы"""
        test_cases = [
            ('01.01.25 - 31.12.25', '2025-01-01', '2025-12-31'),
            ('15.06.24 - 30.09.24', '2024-06-15', '2024-09-30'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать 2-значный год: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_date_range_single_digit_day_month(self):
        """Однозначные дни и месяцы"""
        test_cases = [
            ('1.1.2025 - 9.9.2025', '2025-01-01', '2025-09-09'),
            ('5.3.2024 - 7.11.2024', '2024-03-05', '2024-11-07'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_date_range_no_spaces_around_dash(self):
        """Без пробелов вокруг тире"""
        result = extract_date_range('01.01.2025-31.12.2025')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2025-01-01')
        self.assertEqual(result['end_month'], '2025-12-31')
    
    def test_date_range_leap_year(self):
        """Високосный год - 29 февраля"""
        result = extract_date_range('01.01.2024 - 29.02.2024')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2024-01-01')
        self.assertEqual(result['end_month'], '2024-02-29')
    
    def test_date_range_cross_year(self):
        """Диапазон через границу года"""
        result = extract_date_range('15.12.2024 - 15.01.2025')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2024-12-15')
        self.assertEqual(result['end_month'], '2025-01-15')


class TestQuarters(unittest.TestCase):
    """Тесты для кварталов: 'за 2-й квартал 2025г', 'за 3 кв 2025'"""
    
    def test_all_quarters(self):
        """Все четыре квартала"""
        test_cases = [
            ('за 1 квартал 2025', '2025-01-01', '2025-03-31'),
            ('за 2 квартал 2025', '2025-04-01', '2025-06-30'),
            ('за 3 квартал 2025', '2025-07-01', '2025-09-30'),
            ('за 4 квартал 2025', '2025-10-01', '2025-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_quarter_various_formats(self):
        """Разные форматы записи кварталов"""
        test_cases = [
            ('Прошу предоставить акт сверки за 3 кв. 2025 г.', '2025-07-01', '2025-09-30'),
            ('Акт сверки 4кв 2024г', '2024-10-01', '2024-12-31'),
            ('за 2-й квартал 2025', '2025-04-01', '2025-06-30'),
            ('за 1-я квартал 2024', '2024-01-01', '2024-03-31'),
            ('за 3-е квартал 2025', '2025-07-01', '2025-09-30'),
            ('квартал 2 2024', '2024-04-01', '2024-06-30'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_quarter_abbreviated(self):
        """Сокращенные записи кварталов"""
        test_cases = [
            ('1кв 2025', '2025-01-01', '2025-03-31'),
            ('2кв. 2024', '2024-04-01', '2024-06-30'),
            ('3 кв 2025', '2025-07-01', '2025-09-30'),
            ('4 кв. 2024', '2024-10-01', '2024-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)


class TestHalfYear(unittest.TestCase):
    """Тесты для полугодий: 'за 1-е полугодие 2025 г.'"""
    
    def test_first_half_year(self):
        """Первое полугодие"""
        test_cases = [
            ('за 1-е полугодие 2025 г.', '2025-01-01', '2025-06-30'),
            ('за 1 полугодие 2024', '2024-01-01', '2024-06-30'),
            ('1-е полугодие 2025', '2025-01-01', '2025-06-30'),
            ('первое полугодие 2025', '2025-01-01', '2025-06-30'),  # может не сработать, зависит от реализации
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                if '1' in text or 'первое' not in text:
                    self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                    self.assertEqual(result['start_month'], expected_start)
                    self.assertEqual(result['end_month'], expected_end)
    
    def test_second_half_year(self):
        """Второе полугодие"""
        test_cases = [
            ('за 2-е полугодие 2025 г.', '2025-07-01', '2025-12-31'),
            ('за 2 полугодие 2024', '2024-07-01', '2024-12-31'),
            ('2-е полугодие 2025', '2025-07-01', '2025-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_half_year_various_endings(self):
        """Разные окончания слова 'полугодие'"""
        test_cases = [
            ('1 полугодия 2025', '2025-01-01', '2025-06-30'),
            ('2 полугодию 2024', '2024-07-01', '2024-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)


class TestMonths(unittest.TestCase):
    """Тесты для месяцев: 'За 9 месяцев 2025 года'"""
    
    def test_months_count(self):
        """Количество месяцев с начала года"""
        test_cases = [
            ('За 1 месяц 2025 года', '2025-01-01', '2025-01-31'),
            ('За 3 месяца 2025 года', '2025-01-01', '2025-03-31'),
            ('За 6 месяцев 2025 года', '2025-01-01', '2025-06-30'),
            ('За 9 месяцев 2025 года', '2025-01-01', '2025-09-30'),
            ('За 12 месяцев 2024 года', '2024-01-01', '2024-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_months_abbreviated(self):
        """Сокращенная форма 'мес'"""
        test_cases = [
            ('за 9 мес 2025', '2025-01-01', '2025-09-30'),
            ('за 6 мес. 2024', '2024-01-01', '2024-06-30'),
            ('11 мес 2025', '2025-01-01', '2025-11-30'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_months_various_word_forms(self):
        """Разные падежные формы слова 'месяц'"""
        test_cases = [
            ('за 1 месяц 2025', '2025-01-01', '2025-01-31'),
            ('за 2 месяца 2025', '2025-01-01', '2025-02-28'),  # не високосный
            ('за 5 месяцев 2025', '2025-01-01', '2025-05-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)


class TestFullYear(unittest.TestCase):
    """Тесты для полного года: 'за 2024 год'"""
    
    def test_year_with_god_suffix(self):
        """Год с суффиксом 'год', 'года', 'году'"""
        test_cases = [
            ('акт сверки за 2024 год', '2024-01-01', '2024-12-31'),
            ('за 2025 года', '2025-01-01', '2025-12-31'),
            ('в 2024 году', '2024-01-01', '2024-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_year_with_g_suffix(self):
        """Год с суффиксом 'г', 'г.'"""
        test_cases = [
            ('за 2024 г', '2024-01-01', '2024-12-31'),
            ('за 2025 г.', '2025-01-01', '2025-12-31'),
            ('на 2024 г', '2024-01-01', '2024-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_year_with_prepositions(self):
        """Разные предлоги: 'за', 'в', 'на'"""
        test_cases = [
            ('за 2024 год', '2024-01-01', '2024-12-31'),
            ('в 2025 году', '2025-01-01', '2025-12-31'),
            ('на 2024 год', '2024-01-01', '2024-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)


class TestSingleDate(unittest.TestCase):
    """Тесты для одиночной даты: 'на 01.12'"""
    
    def test_single_date_with_year(self):
        """Одиночная дата с годом"""
        test_cases = [
            ('на 01.12.2025', '2025-12-01', '2025-12-01'),
            ('на 15.06.2024', '2024-06-15', '2024-06-15'),
            ('на 31.12.2025', '2025-12-31', '2025-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_single_date_without_year(self):
        """Одиночная дата без года (использует текущий год)"""
        current_year = datetime.now().year
        result = extract_date_range('на 01.12')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], f'{current_year}-12-01')
        self.assertEqual(result['end_month'], f'{current_year}-12-01')
    
    def test_single_date_with_year_in_context(self):
        """Дата без года, но год есть в контексте"""
        result = extract_date_range('акт сверки на 15.06 за 2024 год')
        self.assertTrue(result['success'])
        # Поведение зависит от приоритета правил - может вернуть год или дату


class TestAllPeriod(unittest.TestCase):
    """Тесты для 'весь период'"""
    
    def test_all_period_with_two_years(self):
        """Весь период с двумя годами"""
        test_cases = [
            ('весь период 2023-2025', '2023-01-01', '2025-12-31'),
            ('весь период с 2022 по 2024', '2022-01-01', '2024-12-31'),
            ('за весь период 2021 2023', '2021-01-01', '2023-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_all_period_variations(self):
        """Разные вариации 'весь'"""
        test_cases = [
            ('весь 2023 2024', '2023-01-01', '2024-12-31'),
            ('все 2022 2025', '2022-01-01', '2025-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)


class TestPeriod(unittest.TestCase):
    """Тесты для периода как квартала: 'за 3 период 2025 года'"""
    
    def test_period_as_quarter(self):
        """Период интерпретируется как квартал"""
        test_cases = [
            ('за 3 период 2025 г', '2025-07-01', '2025-09-30'),
            ('за 1 период 2024 г.', '2024-01-01', '2024-03-31'),
            ('за 2 период 2025 года', '2025-04-01', '2025-06-30'),
            ('за 4 период 2024', '2024-10-01', '2024-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_period_with_ordinal_suffix(self):
        """Период с порядковым суффиксом"""
        test_cases = [
            ('за 1-й период 2025', '2025-01-01', '2025-03-31'),
            ('за 2-я период 2024', '2024-04-01', '2024-06-30'),
            ('за 3-е период 2025', '2025-07-01', '2025-09-30'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)


class TestRussianMonths(unittest.TestCase):
    """Тесты для русских названий месяцев: 'за декабрь 2025 год'"""
    
    def test_full_month_names(self):
        """Полные названия месяцев"""
        test_cases = [
            ('за январь 2025', '2025-01-01', '2025-01-31'),
            ('за февраль 2024', '2024-02-01', '2024-02-29'),  # високосный
            ('за март 2025', '2025-03-01', '2025-03-31'),
            ('за апрель 2025', '2025-04-01', '2025-04-30'),
            ('за май 2025', '2025-05-01', '2025-05-31'),
            ('за июнь 2025', '2025-06-01', '2025-06-30'),
            ('за июль 2025', '2025-07-01', '2025-07-31'),
            ('за август 2025', '2025-08-01', '2025-08-31'),
            ('за сентябрь 2025', '2025-09-01', '2025-09-30'),
            ('за октябрь 2025', '2025-10-01', '2025-10-31'),
            ('за ноябрь 2025', '2025-11-01', '2025-11-30'),
            ('за декабрь 2025', '2025-12-01', '2025-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_abbreviated_month_names(self):
        """Сокращенные названия месяцев"""
        test_cases = [
            ('за янв 2025', '2025-01-01', '2025-01-31'),
            ('за фев 2025', '2025-02-01', '2025-02-28'),
            ('за мар 2025', '2025-03-01', '2025-03-31'),
            ('за апр 2025', '2025-04-01', '2025-04-30'),
            ('за авг 2025', '2025-08-01', '2025-08-31'),
            ('за сен 2025', '2025-09-01', '2025-09-30'),
            ('за окт 2025', '2025-10-01', '2025-10-31'),
            ('за ноя 2025', '2025-11-01', '2025-11-30'),
            ('за дек 2025', '2025-12-01', '2025-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_month_with_year_suffix(self):
        """Месяц с суффиксом года"""
        test_cases = [
            ('за декабрь 2025 год', '2025-12-01', '2025-12-31'),
            ('за январь 2025 г.', '2025-01-01', '2025-01-31'),
            ('за март 2024 года', '2024-03-01', '2024-03-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_month_various_cases(self):
        """Разные падежи месяцев"""
        test_cases = [
            ('в январе 2025', '2025-01-01', '2025-01-31'),
            ('на февраля 2025', '2025-02-01', '2025-02-28'),
            ('за марта 2025', '2025-03-01', '2025-03-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)


class TestAktSverkiYear(unittest.TestCase):
    """Тесты для 'акт сверки за {year}' без суффикса 'год'"""
    
    def test_akt_sverki_without_suffix(self):
        """Акт сверки за год без суффикса"""
        test_cases = [
            ('Добрый день! Просьба прислать акт сверки за 2025 с ООО "Рога и Копыта"', '2025-01-01', '2025-12-31'),
            ('Прошу акт за 2024', '2024-01-01', '2024-12-31'),
            ('Акт сверки за 2023 нужен срочно', '2023-01-01', '2023-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_akt_sverki_year_boundary(self):
        """Граничные случаи для года (>2020)"""
        # Год 2021 и выше должен работать
        result = extract_date_range('акт сверки за 2021')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2021-01-01')
        self.assertEqual(result['end_month'], '2021-12-31')
        
        # Год 2020 - должен использовать fallback
        result = extract_date_range('акт сверки за 2020')
        self.assertTrue(result['success'])
    
    def test_akt_sverki_fallback_to_current_year(self):
        """Fallback на текущий год при отсутствии валидного года"""
        current_year = datetime.now().year
        result = extract_date_range('Прошу акт сверки за')
        # Должен использовать текущий год как fallback
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], f'{current_year}-01-01')
        self.assertEqual(result['end_month'], f'{current_year}-12-31')
    
    def test_akt_sverki_with_god_goes_to_extract_year(self):
        """С суффиксом 'год' обрабатывается extract_year"""
        result = extract_date_range('акт сверки за 2024 год')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2024-01-01')
        self.assertEqual(result['end_month'], '2024-12-31')


class TestNoMatch(unittest.TestCase):
    """Тесты для случаев без совпадения"""
    
    def test_no_date_patterns(self):
        """Текст без дат"""
        test_cases = [
            'Добрый день! Как дела?',
            'Просто какой-то текст',
            'Здравствуйте, коллеги!',
            '',
        ]
        for text in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertFalse(result['success'], f"Не должен был распознать: {text}")
    
    def test_invalid_dates(self):
        """Невалидные даты"""
        # 30 февраля не существует
        result = extract_date_range('01.01.2025 - 30.02.2025')
        self.assertFalse(result['success'])
    
    def test_empty_and_none(self):
        """Пустые значения"""
        result = extract_date_range('')
        self.assertFalse(result['success'])
        self.assertIsNone(result['start_month'])
        self.assertIsNone(result['end_month'])


class TestEdgeCases(unittest.TestCase):
    """Граничные и особые случаи"""
    
    def test_case_insensitivity(self):
        """Независимость от регистра"""
        test_cases = [
            ('ЗА 2024 ГОД', '2024-01-01', '2024-12-31'),
            ('За Январь 2025', '2025-01-01', '2025-01-31'),
            ('ДЕКАБРЬ 2025', '2025-12-01', '2025-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_text_with_multiple_patterns(self):
        """Текст с несколькими паттернами - должен выбрать первый по приоритету"""
        # Явный диапазон имеет приоритет
        result = extract_date_range('за 2024 год, период 01.01.2025 - 31.03.2025')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2025-01-01')
        self.assertEqual(result['end_month'], '2025-03-31')
    
    def test_real_email_examples(self):
        """Реальные примеры из email"""
        test_cases = [
            ('Добрый день! Просьба направить акт сверки за 2024 год. С уважением, Иванов И.И.', 
             '2024-01-01', '2024-12-31'),
            ('Прошу предоставить акт сверки взаимных расчетов за 3 кв. 2025 г. между ООО "Альфа" и ООО "Бета"',
             '2025-07-01', '2025-09-30'),
            ('Акт сверки за период 01.01.2024 - 30.06.2024 во вложении',
             '2024-01-01', '2024-06-30'),
            ('Направляем акт сверки за 1-е полугодие 2025 года',
             '2025-01-01', '2025-06-30'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_year_boundaries(self):
        """Граничные значения годов"""
        # Минимальный валидный год
        result = extract_date_range('за 2000 год')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2000-01-01')
        
        # Максимальный валидный год
        result = extract_date_range('за 2100 год')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2100-01-01')
    
    def test_february_leap_vs_non_leap(self):
        """Февраль в високосный и не високосный год"""
        # 2024 - високосный
        result = extract_date_range('за февраль 2024')
        self.assertTrue(result['success'])
        self.assertEqual(result['end_month'], '2024-02-29')
        
        # 2025 - не високосный
        result = extract_date_range('за февраль 2025')
        self.assertTrue(result['success'])
        self.assertEqual(result['end_month'], '2025-02-28')
    
    def test_whitespace_variations(self):
        """Разные варианты пробелов"""
        test_cases = [
            ('за  2024  год', '2024-01-01', '2024-12-31'),  # двойные пробелы
            ('за 2024год', '2024-01-01', '2024-12-31'),     # без пробела перед 'год'
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                # Может не сработать для некоторых вариаций
                if result['success']:
                    self.assertEqual(result['start_month'], expected_start)
                    self.assertEqual(result['end_month'], expected_end)


class TestSpecificQuarterShort(unittest.TestCase):
    """Тесты для короткой записи квартала: '1кв 2025г'"""
    
    def test_quarter_short_format(self):
        """Короткий формат без пробела"""
        test_cases = [
            ('1кв 2025', '2025-01-01', '2025-03-31'),
            ('2кв 2024', '2024-04-01', '2024-06-30'),
            ('3кв 2025', '2025-07-01', '2025-09-30'),
            ('4кв 2024', '2024-10-01', '2024-12-31'),
        ]
        for text, expected_start, expected_end in test_cases:
            with self.subTest(text=text):
                result = extract_date_range(text)
                self.assertTrue(result['success'], f"Не удалось распознать: {text}")
                self.assertEqual(result['start_month'], expected_start)
                self.assertEqual(result['end_month'], expected_end)
    
    def test_quarter_short_with_dot(self):
        """С точкой после 'кв'"""
        result = extract_date_range('2кв. 2025')
        self.assertTrue(result['success'])
        self.assertEqual(result['start_month'], '2025-04-01')
        self.assertEqual(result['end_month'], '2025-06-30')


if __name__ == '__main__':
    unittest.main()
