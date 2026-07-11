"""Confidence-based routing: auto-approve, fast review, or detailed review."""
from __future__ import annotations

from src.validation.rules import ValidationReport


def route_document(overall_confidence: float, report: ValidationReport,
                    high_conf: float = 0.9, medium_conf: float = 0.6) -> str:
    """Returns: 'auto_approve' | 'fast_review' | 'detailed_review'."""
    if report.has_critical:
        return "detailed_review"
    if overall_confidence >= high_conf and report.is_clean:
        return "auto_approve"
    if overall_confidence >= medium_conf:
        return "fast_review"
    return "detailed_review"
