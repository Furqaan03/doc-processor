"""Chunk-and-merge for long documents: extract per-chunk, merge, flag conflicts."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FieldConflict:
    field: str
    values: list[tuple[str, str]]  # (value, source_chunk_id)


@dataclass
class MergeResult:
    merged: dict
    conflicts: list[FieldConflict] = field(default_factory=list)


def chunk_text(text: str, max_chars: int = 2000) -> list[str]:
    """Splits by paragraph boundaries, respecting max_chars per chunk."""
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) > max_chars and current:
            chunks.append(current.strip())
            current = p
        else:
            current += ("\n\n" if current else "") + p
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text]


def merge_extractions(per_chunk_results: list[tuple[str, dict]]) -> MergeResult:
    """Merges per-chunk extraction dicts. If two chunks disagree on the same field
    with different non-empty values, it's a conflict — include both with sources
    rather than silently picking one."""
    merged: dict = {}
    conflicts: list[FieldConflict] = []
    seen: dict[str, list[tuple[str, str]]] = {}

    for chunk_id, result in per_chunk_results:
        for key, value in result.items():
            if value in (None, "", [], {}):
                continue
            seen.setdefault(key, []).append((str(value), chunk_id))

    for key, values in seen.items():
        distinct = {v for v, _ in values}
        if len(distinct) == 1:
            merged[key] = values[0][0]
        else:
            conflicts.append(FieldConflict(field=key, values=values))
            merged[key] = values[0][0]  # keep first as a default; conflict is still recorded

    return MergeResult(merged=merged, conflicts=conflicts)
