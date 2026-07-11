from src.ingestion.loader import load_page, needs_ocr


def test_dense_native_text_skips_ocr():
    text = "a" * 500
    result = load_page(text, ocr_fallback=lambda: "SHOULD NOT BE CALLED")
    assert result.used_ocr is False
    assert result.text == text


def test_sparse_text_triggers_ocr_fallback():
    result = load_page("", ocr_fallback=lambda: "ocr recovered text")
    assert result.used_ocr is True
    assert result.text == "ocr recovered text"


def test_needs_ocr_threshold():
    assert needs_ocr("") is True
    assert needs_ocr("x" * 1000) is False
