from __future__ import annotations

from deerflow.researchops.intent_calibrator import build_alternatives, confidence_from_score, rationale_for
from deerflow.researchops.intent_rules import extract_slots, score_intents
from deerflow.researchops.schemas import IntentResult, ResearchIntent, RiskLevel


def _missing_slots(intent: ResearchIntent, project: str | None, time_range: str | None, task_operation: str | None) -> list[str]:
    missing: list[str] = []
    if intent in {
        ResearchIntent.PROGRESS_SUMMARY,
        ResearchIntent.EXPERIMENT_REVIEW,
        ResearchIntent.PROJECT_PLANNING,
    } and project is None:
        missing.append("project")
    if intent == ResearchIntent.PROGRESS_SUMMARY and time_range is None:
        missing.append("time_range")
    if intent == ResearchIntent.TASK_TRACKING and task_operation is None:
        missing.append("task_operation")
    return missing


def classify_intent(user_input: str) -> IntentResult:
    """Classify a ResearchOps request with scored rule candidates and slot evidence."""
    text = user_input.strip()
    slots = extract_slots(text)
    candidates = score_intents(text)
    top = candidates[0]

    intent = top.intent
    output_format = _output_format_for_intent(intent, slots.output_format)
    risk = RiskLevel.MEDIUM if intent == ResearchIntent.TASK_TRACKING else RiskLevel.LOW
    missing = _missing_slots(intent, slots.project, slots.time_range, slots.task_operation)
    if intent == ResearchIntent.KNOWLEDGE_QA:
        missing = []

    return IntentResult(
        intent=intent,
        confidence=confidence_from_score(top.score, top_score=top.score),
        project=slots.project,
        time_range=slots.time_range,
        output_format=output_format,
        task_operation=slots.task_operation,
        missing_slots=missing,
        risk_level=risk,
        alternatives=build_alternatives(candidates),
        slot_evidence=slots.evidence,
        classification_rationale=rationale_for(top),
    )


def _output_format_for_intent(intent: ResearchIntent, progress_output_format: str | None) -> str:
    if intent == ResearchIntent.PROGRESS_SUMMARY:
        return progress_output_format or "progress_summary"
    if intent == ResearchIntent.EXPERIMENT_REVIEW:
        return "experiment_review"
    if intent == ResearchIntent.PROJECT_PLANNING:
        return "project_plan"
    if intent == ResearchIntent.TASK_TRACKING:
        return "task_update"
    return "answer"
