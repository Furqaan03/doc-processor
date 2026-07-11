from src.ingestion.ocr import reconcile


def test_engines_agree_high_confidence():
    r = reconcile("invoice total 100.00", 0.9, "invoice total 100.00", 0.85)
    assert r.engines_agreed is True
    assert r.confidence > 0.8


def test_engines_disagree_prefers_higher_confidence():
    r = reconcile("total 100.00", 0.95, "totaI IOO.OO", 0.3)  # OCR garbling
    assert r.engines_agreed is False
    assert r.text == "total 100.00"  # higher-confidence engine wins


def test_disagreement_penalizes_confidence():
    agree = reconcile("same text here", 0.9, "same text here", 0.9)
    disagree = reconcile("some text here", 0.9, "totally different content entirely", 0.9)
    assert disagree.confidence < agree.confidence
