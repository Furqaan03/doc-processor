"""Human correction feedback loop: every edit is logged and classified."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

CORRECTIONS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "corrections.jsonl"


class Correction(BaseModel):
    id: str
    document_id: str
    field: str
    original_value: str
    corrected_value: str
    corrected_by: str
    correction_type: str   # "extraction_error" | "validation_false_positive"
    created_at: str


def log_correction(document_id: str, field: str, original: str, corrected: str, corrected_by: str, correction_type: str, path: Path = CORRECTIONS_PATH) -> Correction:
    c = Correction(
        id=str(uuid.uuid4()), document_id=document_id, field=field,
        original_value=original, corrected_value=corrected, corrected_by=corrected_by,
        correction_type=correction_type, created_at=datetime.now(timezone.utc).isoformat(),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(c.model_dump_json() + "\n")
    return c


def load_corrections(path: Path = CORRECTIONS_PATH) -> list[Correction]:
    if not path.exists():
        return []
    return [Correction(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def analytics(path: Path = CORRECTIONS_PATH) -> dict:
    corrections = load_corrections(path)
    if not corrections:
        return {"total": 0, "extraction_errors": 0, "validation_false_positives": 0, "by_field": {}}
    by_field: dict[str, int] = {}
    for c in corrections:
        by_field[c.field] = by_field.get(c.field, 0) + 1
    return {
        "total": len(corrections),
        "extraction_errors": sum(1 for c in corrections if c.correction_type == "extraction_error"),
        "validation_false_positives": sum(1 for c in corrections if c.correction_type == "validation_false_positive"),
        "by_field": by_field,
    }
