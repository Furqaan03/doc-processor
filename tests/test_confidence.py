from src.extraction.confidence import is_valid_amount, is_valid_date, value_confidence


def test_exact_match_high_confidence():
    score = value_confidence("INV-4471", "Invoice number: INV-4471, dated...", format_valid=True)
    assert score > 0.9


def test_missing_value_lower_confidence():
    score = value_confidence("INV-9999", "Invoice number: INV-4471", format_valid=True)
    assert score < 0.9


def test_format_invalid_lowers_confidence():
    exact_bad_format = value_confidence("INV-4471", "Invoice INV-4471 here", format_valid=False)
    exact_good_format = value_confidence("INV-4471", "Invoice INV-4471 here", format_valid=True)
    assert exact_bad_format < exact_good_format


def test_date_validation():
    assert is_valid_date("2026-03-14") is True
    assert is_valid_date("March 14 2026") is False


def test_amount_validation():
    assert is_valid_amount("1,250.00") is True
    assert is_valid_amount("$99.50") is True
    assert is_valid_amount("not a number") is False
