from __future__ import annotations

from deerflow.researchops.intent_rules import IntentRuleCandidate
from deerflow.researchops.schemas import IntentCandidate


def confidence_from_score(score: float, *, top_score: float) -> float:
    if score <= 0.5:
        return 0.52
    if score >= 4.0:
        return 0.9
    confidence = 0.55 + min(score, 4.0) / 4.0 * 0.35
    if score < top_score:
        confidence = min(confidence, 0.82)
    return round(confidence, 2)


def build_alternatives(candidates: list[IntentRuleCandidate]) -> list[IntentCandidate]:
    if not candidates:
        return []
    top_score = candidates[0].score
    alternatives = []
    for candidate in candidates[1:]:
        alternatives.append(
            IntentCandidate(
                intent=candidate.intent,
                confidence=confidence_from_score(candidate.score, top_score=top_score),
                rationale=f"matched: {', '.join(candidate.matched)}",
            )
        )
    return alternatives


def rationale_for(candidate: IntentRuleCandidate) -> str:
    if candidate.score <= 0.75:
        return "low evidence fallback; no strong ResearchOps intent signal matched"
    return f"matched {candidate.intent.value}: {', '.join(candidate.matched)}"
