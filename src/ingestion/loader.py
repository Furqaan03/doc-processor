"""Multi-format loader: native text extraction first, OCR fallback by text density."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PageLoadResult:
    text: str
    used_ocr: bool
    text_density: float   # chars per page-area proxy; low density -> likely scanned


def text_density(native_text: str, expected_min_chars: int = 200) -> float:
    """Cheap heuristic: ratio of extracted chars to what a real text page should have.
    Below 1.0 strongly suggests the page is a scan needing OCR."""
    return len(native_text.strip()) / expected_min_chars


def needs_ocr(native_text: str, threshold: float = 0.3) -> bool:
    return text_density(native_text) < threshold


def load_page(native_text: str, ocr_fallback) -> PageLoadResult:
    """`ocr_fallback` is a zero-arg callable returning OCR text, invoked only if needed."""
    density = text_density(native_text)
    if density >= 0.3:
        return PageLoadResult(text=native_text, used_ocr=False, text_density=density)
    ocr_text = ocr_fallback()
    return PageLoadResult(text=ocr_text, used_ocr=True, text_density=density)
