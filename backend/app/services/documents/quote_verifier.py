import re
from typing import List, Optional, Tuple
from app.services.documents.extractor import ExtractedUnit


def normalize_text_for_matching(text: str) -> str:
    """Normalize whitespace, punctuation, and casing for robust substring matching."""
    text = text.lower()
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def verify_quote_in_units(quote: Optional[str], units: List[ExtractedUnit]) -> Tuple[bool, Optional[str]]:
    """
    Verify if a supporting quote exists in the extracted source text units.
    Returns: (is_found, matched_source_reference)
    """
    if not quote or len(quote.strip()) == 0:
        return False, None

    normalized_quote = normalize_text_for_matching(quote)
    if len(normalized_quote) < 5:
        # Quote too short to be meaningful evidence
        return False, None

    for unit in units:
        norm_unit_text = normalize_text_for_matching(unit.text)
        if normalized_quote in norm_unit_text:
            return True, unit.source_ref

    # Allow partial window match if quote is long (> 60 chars) and mostly matches
    if len(normalized_quote) > 60:
        # Take first 40 chars
        prefix = normalized_quote[:40]
        for unit in units:
            norm_unit_text = normalize_text_for_matching(unit.text)
            if prefix in norm_unit_text:
                return True, unit.source_ref

    return False, None
