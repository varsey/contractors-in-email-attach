from email import policy
from email.parser import HeaderParser
from typing import Optional


def normalize_message_id(message_id: Optional[str]) -> str:
    """Normalize message-id for stable lookup/storage across all code paths."""
    if message_id is None:
        return ''

    normalized = str(message_id).strip()
    while normalized.startswith('<') and normalized.endswith('>') and len(normalized) > 1:
        normalized = normalized[1:-1].strip()

    return normalized


def extract_normalized_message_id(header_data: str) -> str:
    """Extract and normalize Message-ID from raw header text (supports folded headers)."""
    if not header_data:
        return ''

    parser = HeaderParser(policy=policy.default)
    parsed_headers = parser.parsestr(header_data)
    raw_message_id = parsed_headers.get('Message-ID', '')
    return normalize_message_id(raw_message_id)
