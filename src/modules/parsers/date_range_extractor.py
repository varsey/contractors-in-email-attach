import re
from datetime import datetime, date
from typing import Dict


def extract_date_range(message: str) -> Dict[str, any]:
    """
    Extract date range from email message text related to "акт сверки".
    
    Args:
        message: Email message text
        
    Returns:
        Dictionary with format:
        {
            'start_month': ISO date string or None,
            'end_month': ISO date string or None,
            'success': bool
        }
    """
    if not message:
        return {'start_month': None, 'end_month': None, 'success': False}

    text = message.lower()

    # 1. Explicit date range: DD.MM.YYYY - DD.MM.YYYY
    result = extract_explicit_date_range(text)
    if result['success']:
        return result
    
    # 2. Quarter: "за 2-й квартал 2025г", "за 3 кв 2025"
    result = extract_quarter(text)
    if result['success']:
        return result
    
    # 3. Half-year: "за 1-е полугодие 2025 г."
    result = extract_half_year(text)
    if result['success']:
        return result
    
    # 4. Months: "За 9 месяцев 2025 года"
    result = extract_months(text)
    if result['success']:
        return result
    
    # 5. Specific month: "за 1кв 2025г" (could be quarter or first quarter)
    result = extract_specific_quarter_short(text)
    if result['success']:
        return result
    
    # 6. Full year: "за 2024 год"
    result = extract_year(text)
    if result['success']:
        return result
    
    # 7. Single date: "на 01.12"
    result = extract_single_date(text)
    if result['success']:
        return result
    
    # 8. Try to find "весь период" (all period) with years
    result = extract_all_period(text)
    if result['success']:
        return result
    
    # 9. Period: "за 3 период 2025 года" (as quarter)
    result = extract_period(text)
    if result['success']:
        return result
    
    # 10. Russian month name: "за декабрь 2025 год", "за дек 2025"
    result = extract_russian_month(text)
    if result['success']:
        return result
    
    # 11. Low-priority: "акт сверки за {year}" or "акт за {year}" without "год" suffix
    result = extract_akt_sverki_year(text)
    if result['success']:
        return result
    
    # No pattern matched
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_explicit_date_range(text: str) -> Dict[str, any]:
    """Extract explicit date ranges like '01.01.2025 - 30.11.2025'"""
    # Pattern: DD.MM.YYYY - DD.MM.YYYY or DD.MM.YY - DD.MM.YY
    pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s*[-–—]\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})'
    match = re.search(pattern, text)
    
    if match:
        day1, month1, year1, day2, month2, year2 = match.groups()
        
        # Convert 2-digit years to 4-digit
        year1 = normalize_year(year1)
        year2 = normalize_year(year2)
        
        try:
            start_date = date(int(year1), int(month1), int(day1))
            end_date = date(int(year2), int(month2), int(day2))
            
            return {
                'start_month': start_date.isoformat(),
                'end_month': end_date.isoformat(),
                'success': True
            }
        except ValueError:
            pass
    
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_quarter(text: str) -> Dict[str, any]:
    """Extract quarter references like 'за 2-й квартал 2025г', 'за 3 кв 2025'"""
    # Patterns for quarters
    patterns = [
        r'(\d+)[-\s]*[йяе]*\s*(?:квартал|кв\.?)\s*(\d{4})',  # "2-й квартал 2025", "3 кв 2025"
        r'(?:квартал|кв\.?)\s*(\d+)\s*(?:за)?\s*(\d{4})',     # "квартал 2 2025"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            quarter = int(match.group(1))
            year = int(match.group(2))
            
            if 1 <= quarter <= 4:
                start_month = (quarter - 1) * 3 + 1
                end_month = quarter * 3
                
                start_date = date(year, start_month, 1)
                end_date = get_last_day_of_month(year, end_month)
                
                return {
                    'start_month': start_date.isoformat(),
                    'end_month': end_date.isoformat(),
                    'success': True
                }
    
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_specific_quarter_short(text: str) -> Dict[str, any]:
    """Extract patterns like 'за 1кв 2025г' where quarter is directly followed by 'кв'"""
    pattern = r'(\d+)кв\.?\s*(\d{4})'
    match = re.search(pattern, text)
    
    if match:
        quarter = int(match.group(1))
        year = int(match.group(2))
        
        if 1 <= quarter <= 4:
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            
            start_date = date(year, start_month, 1)
            end_date = get_last_day_of_month(year, end_month)
            
            return {
                'start_month': start_date.isoformat(),
                'end_month': end_date.isoformat(),
                'success': True
            }
    
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_half_year(text: str) -> Dict[str, any]:
    """Extract half-year references like 'за 1-е полугодие 2025 г.'"""
    pattern = r'(\d+)[-\s]*[еє]*\s*полугод[иіє]+\w*\s*(\d{4})'
    match = re.search(pattern, text)
    
    if match:
        half = int(match.group(1))
        year = int(match.group(2))
        
        if half == 1:
            start_date = date(year, 1, 1)
            end_date = date(year, 6, 30)
        elif half == 2:
            start_date = date(year, 7, 1)
            end_date = date(year, 12, 31)
        else:
            return {'start_month': None, 'end_month': None, 'success': False}
        
        return {
            'start_month': start_date.isoformat(),
            'end_month': end_date.isoformat(),
            'success': True
        }
    
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_months(text: str) -> Dict[str, any]:
    """Extract month count like 'За 9 месяцев 2025 года' or 'за 9 мес 2025'"""
    # Pattern to match both full "месяцев/месяца" and abbreviated "мес"
    pattern = r'(\d+)\s*(?:месяц[аеовів]*|мес\.?)\s*(\d{4})'
    match = re.search(pattern, text)
    
    if match:
        months = int(match.group(1))
        year = int(match.group(2))
        
        if 1 <= months <= 12:
            start_date = date(year, 1, 1)
            end_date = get_last_day_of_month(year, months)
            
            return {
                'start_month': start_date.isoformat(),
                'end_month': end_date.isoformat(),
                'success': True
            }
    
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_year(text: str) -> Dict[str, any]:
    """Extract full year like 'за 2024 год'"""
    pattern = r'(?:за|в|на)\s*(\d{4})\s*(?:год[ауе]*|г\.?)'
    match = re.search(pattern, text)
    
    if match:
        year = int(match.group(1))
        
        # Sanity check for reasonable years
        if 2000 <= year <= 2100:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            
            return {
                'start_month': start_date.isoformat(),
                'end_month': end_date.isoformat(),
                'success': True
            }
    
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_single_date(text: str) -> Dict[str, any]:
    """Extract single date like 'на 01.12' - assume current or specified year"""
    # Try to find a date with explicit year first
    pattern_with_year = r'на\s*(\d{1,2})\.(\d{1,2})\.?(\d{2,4})?'
    match = re.search(pattern_with_year, text)
    
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year_str = match.group(3)
        
        if year_str:
            year = normalize_year(year_str)
        else:
            # Try to find a year nearby in the text
            year_pattern = r'(\d{4})'
            year_matches = re.findall(year_pattern, text)
            if year_matches:
                year = int(year_matches[-1])  # Take the last year found
            else:
                year = datetime.now().year  # Default to current year
        
        try:
            target_date = date(int(year), month, day)
            
            return {
                'start_month': target_date.isoformat(),
                'end_month': target_date.isoformat(),
                'success': True
            }
        except ValueError:
            pass
    
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_all_period(text: str) -> Dict[str, any]:
    """Extract 'весь период' or 'все' with year mentions"""
    if 'весь период' in text or 'весь' in text or 'все' in text:
        # Try to find years in the context
        year_pattern = r'(\d{4})'
        years = [int(y) for y in re.findall(year_pattern, text) if 2000 <= int(y) <= 2100]
        
        if len(years) >= 2:
            start_year = min(years)
            end_year = max(years)
            
            start_date = date(start_year, 1, 1)
            end_date = date(end_year, 12, 31)
            
            return {
                'start_month': start_date.isoformat(),
                'end_month': end_date.isoformat(),
                'success': True
            }
    
    return {'start_month': None, 'end_month': None, 'success': False}


def normalize_year(year_str: str) -> int:
    """Convert 2-digit or 4-digit year string to 4-digit year"""
    year = int(year_str)
    if year < 100:
        # Assume 20xx for years < 100
        year = 2000 + year
    return year


def get_last_day_of_month(year: int, month: int) -> date:
    """Get the last day of a given month"""
    if month == 12:
        return date(year, 12, 31)
    else:
        next_month = date(year, month + 1, 1)
        from datetime import timedelta
        return next_month - timedelta(days=1)

def extract_period(text: str) -> Dict[str, any]:
    """Extract period references like 'за 3 период 2025 года' interpreted as quarter"""
    patterns = [
        r'(\d+)[-\s]*[йяе]*\s*период[а-яё]*\s*(\d{4})',
        r'период[а-яё]*\s*(\d+)\s*(\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            quarter = int(match.group(1))
            year = int(match.group(2))
            
            if 2000 <= year <= 2100 and 1 <= quarter <= 4:
                start_month = (quarter - 1) * 3 + 1
                end_month = quarter * 3
                
                start_date = date(year, start_month, 1)
                end_date = get_last_day_of_month(year, end_month)
                
                return {
                    'start_month': start_date.isoformat(),
                    'end_month': end_date.isoformat(),
                    'success': True
                }
    
    return {'start_month': None, 'end_month': None, 'success': False}


# Russian month names mapping (full and short forms)
RUSSIAN_MONTHS = {
    # Full form stems (without endings)
    'январ': 1, 'феврал': 2, 'март': 3, 'апрел': 4, 'июн': 6,
    'июл': 7, 'август': 8, 'сентябр': 9, 'октябр': 10, 'ноябр': 11, 'декабр': 12,
    # Short forms
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'ма': 5, 'авг': 8,
    'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12,
}


def extract_russian_month(text: str) -> Dict[str, any]:
    """
    Extract month from Russian month names like 'за декабрь 2025 год', 'за дек 2025'.
    Handles both full and short forms of Russian month names.
    """
    # Build pattern with all month name prefixes (sorted by length descending for proper matching)
    month_prefixes = '|'.join(sorted(RUSSIAN_MONTHS.keys(), key=len, reverse=True))
    
    # Pattern: optional preposition + month name + optional endings + year
    pattern = rf'(?:за|в|на)?\s*({month_prefixes})[а-яё]*\s*(\d{{4}})\s*(?:год[ауе]*|г\.?)?'
    
    match = re.search(pattern, text)
    
    if match:
        month_prefix = match.group(1)
        year = int(match.group(2))
        
        # Find the month number by matching the prefix
        month_num = None
        for prefix, num in RUSSIAN_MONTHS.items():
            if month_prefix.startswith(prefix) or prefix.startswith(month_prefix):
                month_num = num
                break
        
        if month_num and 2000 <= year <= 2100:
            start_date = date(year, month_num, 1)
            end_date = get_last_day_of_month(year, month_num)
            
            return {
                'start_month': start_date.isoformat(),
                'end_month': end_date.isoformat(),
                'success': True
            }
    
    return {'start_month': None, 'end_month': None, 'success': False}


def extract_akt_sverki_year(text: str) -> Dict[str, any]:
    """
    Low-priority extraction for patterns like 'акт сверки за 2025' or 'акт за 2025'.
    Handles cases without 'год', 'г', or 'гг' suffix.
    Year must be > 2020. If year is not found, defaults to current year.
    """
    # Patterns: "акт сверки за {year}" or "акт за {year}" 
    # Year can be followed by optional word boundary or end, but NOT by "год/г/гг"
    # We need to avoid matching cases already handled by extract_year
    patterns = [
        r'акт[а-яё]*\s+сверки\s+за\s+(\d{4})(?!\s*(?:год|г\.|г\b|гг))',
        r'акт[а-яё]*\s+за\s+(\d{4})(?!\s*(?:год|г\.|г\b|гг))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year = int(match.group(1))
            
            # Year must be > 2020 and reasonable
            if 2021 <= year <= 2100:
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
                
                return {
                    'start_month': start_date.isoformat(),
                    'end_month': end_date.isoformat(),
                    'success': True
                }
    
    # If pattern "акт сверки за" or "акт за" exists but no valid year, use current year
    fallback_patterns = [
        r'акт[а-яё]*\s+сверки\s+за\b',
        r'акт[а-яё]*\s+за\b',
    ]
    
    for pattern in fallback_patterns:
        if re.search(pattern, text):
            current_year = datetime.now().year
            start_date = date(current_year, 1, 1)
            end_date = date(current_year, 12, 31)
            
            return {
                'start_month': start_date.isoformat(),
                'end_month': end_date.isoformat(),
                'success': True
            }
    
    return {'start_month': None, 'end_month': None, 'success': False}