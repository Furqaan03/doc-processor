"""Per-field extraction confidence: OCR text match + format validation + chunk agreement."""
from __future__ import annotations

import re
from difflib import SequenceMatcher


def value_confidence(extracted_value: str, source_text: str, format_valid: bool = True, multi_chunk_agreement: bool = True) -> float:
    """Combines: (1) how cleanly the value appears in source text — exact vs. fuzzy,
    (2) whether it passes format validation, (3) whether multiple chunks agreed."""
    if extracted_value in source_text:
        text_match_score = 1.0
    else:
        # Fuzzy fallback: best-window similarity against the source.
        best = 0.0
        window = len(extracted_value) + 10
        for i in range(0, max(1, len(source_text) - window), max(1, window // 2)):
            best = max(best, SequenceMatcher(None, extracted_value, source_text[i:i + window]).ratio())
        text_match_score = best

    signals = [text_match_score, 1.0 if format_valid else 0.0, 1.0 if multi_chunk_agreement else 0.5]
    return round(sum(signals) / len(signals), 3)


def is_valid_date(value: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", value))


def is_valid_amount(value: str) -> bool:
    try:
        return float(value.replace(",", "").replace("$", "")) >= 0
    except ValueError:
        return False
