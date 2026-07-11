"""Per-document-type extraction schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float


class InvoiceExtraction(BaseModel):
    vendor_name: str
    invoice_number: str
    line_items: list[LineItem] = Field(default_factory=list)
    tax: float = 0.0
    total_amount: float
    payment_terms: str = ""
    due_date: str = ""

    @field_validator("total_amount")
    @classmethod
    def positive_total(cls, v: float) -> float:
        if v < 0:
            raise ValueError("total_amount must be non-negative")
        return v


class ContractExtraction(BaseModel):
    parties: list[str] = Field(default_factory=list)
    effective_date: str = ""
    term: str = ""
    key_obligations: list[str] = Field(default_factory=list)
    termination_clauses: list[str] = Field(default_factory=list)


SCHEMAS = {"invoice": InvoiceExtraction, "contract": ContractExtraction}


def line_items_sum_matches_total(invoice: InvoiceExtraction, tolerance: float = 0.01) -> bool:
    """Cross-field consistency: line items + tax should reconcile with the total."""
    items_sum = sum(li.total for li in invoice.line_items)
    expected = items_sum + invoice.tax
    return abs(expected - invoice.total_amount) <= tolerance
