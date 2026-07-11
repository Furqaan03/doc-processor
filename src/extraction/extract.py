"""LLM-driven extraction against a per-doc-type schema, with chunk-and-merge for long docs."""
from __future__ import annotations

import json

from openai import OpenAI

from src.extraction.merge import MergeResult, chunk_text, merge_extractions
from src.extraction.schemas import SCHEMAS


def classify_document_type(text: str, client: OpenAI | None = None) -> str:
    client = client or OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": (
            f"Classify this document as one word: invoice, contract, report, or correspondence.\n\n{text[:1000]}"
        )}],
        temperature=0,
    )
    label = (resp.choices[0].message.content or "").strip().lower()
    return label if label in ("invoice", "contract", "report", "correspondence") else "correspondence"


def _extract_chunk(chunk: str, doc_type: str, client: OpenAI) -> dict:
    schema_cls = SCHEMAS.get(doc_type)
    fields = list(schema_cls.model_fields.keys()) if schema_cls else []
    prompt = (
        f"Extract these fields as JSON from the text below. Only extract information "
        f"literally present in the text — no inference, no defaults. Fields: {fields}\n\n"
        f"Text:\n{chunk}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(resp.choices[0].message.content or "{}")


def extract_document(text: str, doc_type: str, client: OpenAI | None = None) -> MergeResult:
    """Chunks long documents, extracts per chunk, merges with conflict tracking."""
    client = client or OpenAI()
    chunks = chunk_text(text)
    per_chunk = [(f"chunk-{i}", _extract_chunk(c, doc_type, client)) for i, c in enumerate(chunks)]
    return merge_extractions(per_chunk)
