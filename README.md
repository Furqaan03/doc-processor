# Multi-Modal Document Processor: OCR + LLM Extraction + Validation

An end-to-end document pipeline: any format in (PDF, image, scan), dual-engine
OCR out, LLM structured extraction against a per-document-type schema,
validation against business rules and vendor history, and confidence-based
routing to auto-approve, fast human review, or detailed human review.

## Why this exists

Document processing is one of the largest categories of real enterprise AI
spend. It touches computer vision (OCR), NLU (extraction), and production
engineering (validation, error handling, routing at scale) — every layer of the
AI engineering stack, on a problem companies are actively paying to solve.

## Architecture

```
src/ingestion/loader.py       native-text-first, OCR fallback by text density
src/ingestion/ocr.py          dual-engine (Tesseract + EasyOCR) reconciliation via
                               character-level alignment; disagreement penalizes confidence
src/extraction/schemas.py     per-doc-type Pydantic schemas (invoice, contract) with
                               cross-field consistency checks (line items sum to total)
src/extraction/merge.py       chunk-and-merge for long docs; conflicting per-chunk
                               values are recorded, not silently overwritten
src/extraction/confidence.py  per-field confidence: text-match + format validity +
                               chunk agreement
src/extraction/extract.py     LLM extraction orchestration (classify -> extract -> merge)
src/validation/rules.py       business rules + statistical (z-score) anomaly detection
                               vs. vendor history
src/validation/routing.py     confidence + validation-severity -> auto_approve /
                               fast_review / detailed_review
src/review/feedback.py        human corrections logged and classified (extraction
                               error vs. validation false positive) for the flywheel
src/api/main.py               FastAPI: process, log correction, analytics
```

## Design decisions

- **OCR is an ensemble, not a single engine.** Tesseract and EasyOCR run
  independently; when they agree (>95% text similarity) confidence is high, when
  they disagree the higher-confidence reading wins but the *disagreement itself*
  further penalizes confidence — a single engine can't tell you it might be wrong.
- **Chunk conflicts are recorded, not silently resolved.** When two chunks of a
  long document extract different values for the same field, both are kept with
  their source chunk IDs rather than picking one arbitrarily — that's the honest
  signal for "this document has an internal inconsistency worth a human look."
- **Cross-field validation catches what per-field validation can't.** A perfectly
  well-formatted total that doesn't match line-items + tax is the single highest-
  value invoice check — most demos only validate types, not arithmetic consistency.
- **Anomaly detection is vendor-relative, not global.** A $12,000 invoice is
  normal for one vendor and a huge outlier for another; z-score against that
  specific vendor's history catches what a fixed threshold would miss.
- **Routing has three tiers, not two.** Auto-approve only fires when confidence
  is high AND validation is clean; any critical validation issue forces detailed
  review regardless of confidence — a confidently-wrong extraction is the worst
  outcome, so critical issues override the confidence score entirely.
- **OCR engines are lazy-imported.** `pytesseract`/`easyocr` need a system
  Tesseract binary and a heavy torch dependency respectively; the reconciliation
  *logic* (the actual engineering) is tested against injected fake engine outputs,
  so the full suite runs on `requirements-core.txt` with zero OCR install.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements-core.txt   # or requirements.txt for real OCR
cp .env.example .env                    # OPENAI_API_KEY
uvicorn src.api.main:app --reload
```

## Example

```bash
curl -X POST localhost:8000/v1/process -H "Content-Type: application/json" \
  -d '{"document_id": "doc-1", "text": "INVOICE #4471. Vendor: Acme Corp. Widget x10 @ $15.00 = $150.00. Tax: $0. Total: $150.00."}'
# -> {"doc_type": "invoice", "extracted": {...}, "validation_issues": [], "routing_decision": "fast_review"}

curl -X POST localhost:8000/v1/documents/doc-1/correct -H "Content-Type: application/json" \
  -d '{"field": "vendor_name", "original_value": "Acme", "corrected_value": "Acme Corp", "corrected_by": "reviewer1", "correction_type": "extraction_error"}'

curl localhost:8000/v1/analytics
```

## Tests

```bash
pytest tests/ -v
```

24 tests covering OCR reconciliation (agreement/disagreement/confidence
penalty), the native-vs-OCR loader decision, chunk-and-merge (chunking,
agreement, conflict flagging, empty-value skip), business rules (arithmetic
consistency, unknown vendor, negative quantity), vendor-relative anomaly
detection, three-tier routing, field-confidence scoring, and the correction
feedback loop — all offline, no OCR install or API key required.

## Docker

```bash
docker build -t doc-processor . && docker run -p 8000:8000 --env-file .env doc-processor
```

## Status

Phases 1-3 complete (OCR ensemble + native/scan loader, chunk-and-merge LLM
extraction with per-field confidence, business rules + anomaly detection +
three-tier routing) plus the correction feedback loop and analytics. Phase 4's
side-by-side review UI is not built — corrections are logged via API for now.
