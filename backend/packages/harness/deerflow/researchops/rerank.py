from __future__ import annotations

import re

from pydantic import BaseModel, Field


class RetrievalCandidate(BaseModel):
    ref: str
    text: str
    kind: str
    project_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    score: float = 0.0


def rerank_candidates(
    *,
    query: str,
    candidates: list[RetrievalCandidate],
    project_id: str | None = None,
    limit: int = 8,
) -> list[RetrievalCandidate]:
    query_terms = _terms(query)
    scored = []
    for candidate in candidates:
        candidate_terms = _terms(candidate.text)
        overlap = len(query_terms & candidate_terms)
        project_boost = 1.5 if project_id and candidate.project_id == project_id else 0.0
        evidence_boost = min(len(candidate.evidence_refs), 3) * 0.4
        kind_boost = 0.2 if candidate.kind in {"memory", "task"} else 0.0
        score = overlap + project_boost + evidence_boost + kind_boost
        scored.append(candidate.model_copy(update={"score": round(score, 3)}))
    return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]


def _terms(text: str) -> set[str]:
    ascii_terms = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text.lower())
    cjk_terms = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    return set(ascii_terms + cjk_terms)
