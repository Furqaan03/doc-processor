from src.extraction.merge import chunk_text, merge_extractions


def test_chunk_text_respects_max_chars():
    text = "\n\n".join(f"Paragraph {i} " + "x" * 100 for i in range(20))
    chunks = chunk_text(text, max_chars=500)
    assert len(chunks) > 1
    assert all(len(c) <= 600 for c in chunks)  # allows small overflow from single long paragraphs


def test_merge_agrees_when_values_match():
    result = merge_extractions([
        ("chunk-0", {"vendor_name": "Acme"}),
        ("chunk-1", {"vendor_name": "Acme"}),
    ])
    assert result.merged["vendor_name"] == "Acme"
    assert result.conflicts == []


def test_merge_flags_conflicting_values():
    result = merge_extractions([
        ("chunk-0", {"total_amount": "100.00"}),
        ("chunk-1", {"total_amount": "150.00"}),
    ])
    assert len(result.conflicts) == 1
    assert result.conflicts[0].field == "total_amount"
    assert {"100.00", "150.00"} == {v for v, _ in result.conflicts[0].values}


def test_merge_skips_empty_values():
    result = merge_extractions([("chunk-0", {"tax": ""}), ("chunk-1", {"tax": "5.00"})])
    assert result.merged["tax"] == "5.00"
