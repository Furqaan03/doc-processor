from src.extraction.schemas import InvoiceExtraction, LineItem
from src.validation.routing import route_document
from src.validation.rules import ValidationReport, detect_amount_anomaly, validate_invoice


def _invoice(total=150.0, tax=0.0, items=None):
    return InvoiceExtraction(
        vendor_name="Acme Corp", invoice_number="INV-1",
        line_items=items or [LineItem(description="Widget", quantity=10, unit_price=15.0, total=150.0)],
        tax=tax, total_amount=total,
    )


def test_valid_invoice_passes():
    report = validate_invoice(_invoice(total=150.0, tax=0.0))
    assert report.is_clean


def test_mismatched_total_is_critical():
    report = validate_invoice(_invoice(total=999.0, tax=0.0))
    assert report.has_critical


def test_unknown_vendor_is_warning_not_critical():
    report = validate_invoice(_invoice(), known_vendors={"Other Corp"})
    assert not report.has_critical
    assert any(i.severity == "warning" for i in report.issues)


def test_negative_quantity_is_critical():
    # total_amount itself must stay non-negative (enforced by the schema validator);
    # a negative line-item quantity with a valid overall total is the realistic bad case.
    bad_item = InvoiceExtraction(
        vendor_name="Acme", invoice_number="I1",
        line_items=[LineItem(description="x", quantity=-1, unit_price=10, total=-10)],
        total_amount=0,
    )
    report = validate_invoice(bad_item)
    assert report.has_critical


def test_amount_anomaly_detection():
    history = [100.0, 110.0, 105.0, 95.0, 108.0]
    assert detect_amount_anomaly(2000.0, history) is not None   # wild outlier
    assert detect_amount_anomaly(102.0, history) is None        # normal


def test_anomaly_needs_enough_history():
    assert detect_amount_anomaly(1000.0, [100.0]) is None  # too little history to judge


def test_routing_auto_approve():
    assert route_document(0.95, ValidationReport()) == "auto_approve"


def test_routing_critical_forces_detailed_review():
    from src.validation.rules import ValidationIssue

    report = ValidationReport(issues=[ValidationIssue("critical", "bad")])
    assert route_document(0.99, report) == "detailed_review"


def test_routing_medium_confidence_fast_review():
    assert route_document(0.7, ValidationReport()) == "fast_review"


def test_routing_low_confidence_detailed_review():
    assert route_document(0.3, ValidationReport()) == "detailed_review"
