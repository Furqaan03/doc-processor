import src.review.feedback as fb


def test_log_and_analytics(tmp_path, monkeypatch):
    path = tmp_path / "corrections.jsonl"
    fb.log_correction("doc-1", "vendor_name", "Acme", "Acme Corp", "reviewer1", "extraction_error", path=path)
    fb.log_correction("doc-2", "total_amount", "100", "150", "reviewer1", "validation_false_positive", path=path)

    stats = fb.analytics(path)
    assert stats["total"] == 2
    assert stats["extraction_errors"] == 1
    assert stats["validation_false_positives"] == 1
    assert stats["by_field"]["vendor_name"] == 1


def test_analytics_empty(tmp_path):
    stats = fb.analytics(tmp_path / "nonexistent.jsonl")
    assert stats["total"] == 0
