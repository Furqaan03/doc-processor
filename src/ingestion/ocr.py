"""Dual-engine OCR ensemble: run two engines, reconcile via character-level
alignment, pick the higher-confidence reading per segment.

Engines are pluggable functions (page_bytes -> (text, confidence)) so the
ensemble/alignment logic is fully testable without Tesseract/EasyOCR installed."""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import Callable

OCREngine = Callable[[bytes], tuple[str, float]]


@dataclass
class OCRResult:
    text: str
    confidence: float
    engines_agreed: bool
    discrepancy_ratio: float


def _tesseract_engine(page_bytes: bytes) -> tuple[str, float]:
    import pytesseract
    from PIL import Image
    import io

    img = Image.open(io.BytesIO(page_bytes))
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    confs = [int(c) for c in data["conf"] if c not in ("-1", -1)]
    text = " ".join(w for w in data["text"] if w.strip())
    return text, (sum(confs) / len(confs) / 100.0) if confs else 0.0


def _easyocr_engine(page_bytes: bytes) -> tuple[str, float]:
    import easyocr
    import numpy as np
    from PIL import Image
    import io

    reader = easyocr.Reader(["en"], gpu=False)
    img = np.array(Image.open(io.BytesIO(page_bytes)))
    results = reader.readtext(img)
    if not results:
        return "", 0.0
    text = " ".join(r[1] for r in results)
    confidence = sum(r[2] for r in results) / len(results)
    return text, confidence


def reconcile(
    text_a: str, conf_a: float, text_b: str, conf_b: float
) -> OCRResult:
    """When engines agree, confidence is high. When they disagree, prefer the
    higher-confidence reading and record the discrepancy for downstream flagging."""
    matcher = difflib.SequenceMatcher(None, text_a, text_b)
    similarity = matcher.ratio()
    agreed = similarity > 0.95

    if agreed:
        combined_conf = (conf_a + conf_b) / 2
        return OCRResult(text=text_a if conf_a >= conf_b else text_b, confidence=combined_conf,
                          engines_agreed=True, discrepancy_ratio=1 - similarity)

    winner_text = text_a if conf_a >= conf_b else text_b
    winner_conf = max(conf_a, conf_b) * (0.5 + 0.5 * similarity)  # penalize for disagreement
    return OCRResult(text=winner_text, confidence=winner_conf, engines_agreed=False, discrepancy_ratio=1 - similarity)


def run_dual_ocr(page_bytes: bytes, engine_a: OCREngine, engine_b: OCREngine) -> OCRResult:
    text_a, conf_a = engine_a(page_bytes)
    text_b, conf_b = engine_b(page_bytes)
    return reconcile(text_a, conf_a, text_b, conf_b)
