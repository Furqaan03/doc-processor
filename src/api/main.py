"""FastAPI: classify -> extract (chunk+merge) -> validate -> route -> log correction."""
from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from src.extraction.extract import classify_document_type, extract_document
from src.extraction.schemas import InvoiceExtraction
from src.review.feedback import analytics, log_correction
from src.validation.rules import validate_invoice
from src.validation.routing import route_document

load_dotenv()

app = FastAPI(title="Multi-Modal Document Processor")


class ProcessRequest(BaseModel):
    document_id: str
    text: str


@app.post("/v1/process")
def process(req: ProcessRequest) -> dict:
    doc_type = classify_document_type(req.text)
    merge_result = extract_document(req.text, doc_type)

    validation = None
    confidence = 0.7 if not merge_result.conflicts else 0.5
    if doc_type == "invoice":
        try:
            invoice = InvoiceExtraction(**merge_result.merged)
            validation = validate_invoice(invoice)
        except Exception as exc:  # noqa: BLE001 — schema mismatch surfaces as a validation failure
            from src.validation.rules import ValidationIssue, ValidationReport
            validation = ValidationReport(issues=[ValidationIssue("critical", str(exc))])

    from src.validation.rules import ValidationReport
    report = validation or ValidationReport()
    decision = route_document(confidence, report)

    return {
        "document_id": req.document_id,
        "doc_type": doc_type,
        "extracted": merge_result.merged,
        "conflicts": [c.__dict__ for c in merge_result.conflicts],
        "validation_issues": [i.__dict__ for i in report.issues],
        "confidence": confidence,
        "routing_decision": decision,
    }


class CorrectionRequest(BaseModel):
    field: str
    original_value: str
    corrected_value: str
    corrected_by: str
    correction_type: str


@app.post("/v1/documents/{document_id}/correct")
def correct(document_id: str, req: CorrectionRequest) -> dict:
    c = log_correction(document_id, req.field, req.original_value, req.corrected_value, req.corrected_by, req.correction_type)
    return {"correction_id": c.id}


@app.get("/v1/analytics")
def get_analytics() -> dict:
    return analytics()
