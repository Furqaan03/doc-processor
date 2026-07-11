"""Business rules + anomaly detection: does this extraction look right for THIS vendor?"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from src.extraction.schemas import InvoiceExtraction, line_items_sum_matches_total


@dataclass
class ValidationIssue:
    severity: str   # "warning" | "critical"
    message: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(i.severity == "critical" for i in self.issues)

    @property
    def is_clean(self) -> bool:
        return not self.issues


def validate_invoice(invoice: InvoiceExtraction, known_vendors: set[str] | None = None) -> ValidationReport:
    report = ValidationReport()

    if not line_items_sum_matches_total(invoice):
        report.issues.append(ValidationIssue("critical", "Line item totals + tax do not sum to the invoice total."))

    if known_vendors is not None and invoice.vendor_name not in known_vendors:
        report.issues.append(ValidationIssue("warning", f"Vendor '{invoice.vendor_name}' is not in the known vendor list."))

    if any(li.quantity <= 0 for li in invoice.line_items):
        report.issues.append(ValidationIssue("critical", "A line item has non-positive quantity."))

    return report


def detect_amount_anomaly(current_amount: float, historical_amounts: list[float], z_threshold: float = 2.5) -> ValidationIssue | None:
    """Flags an amount that is a statistical outlier vs. that vendor's history."""
    if len(historical_amounts) < 3:
        return None
    mean = statistics.mean(historical_amounts)
    stdev = statistics.pstdev(historical_amounts)
    if stdev == 0:
        return None
    z = abs(current_amount - mean) / stdev
    if z > z_threshold:
        return ValidationIssue("warning", f"Amount {current_amount} is {z:.1f} std devs from this vendor's historical mean ({mean:.2f}).")
    return None
