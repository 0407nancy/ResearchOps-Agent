from __future__ import annotations

import uuid
from datetime import UTC, datetime

from deerflow.researchops.schemas import HitlDecision, IntentResult, PendingCheckpoint, ResearchIntent, ResumeResult
from deerflow.researchops.state_store import ResearchOpsStateStore


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _question_for_missing_slot(slot: str, intent: ResearchIntent) -> tuple[str, list[str] | None]:
    if slot == "time_range" and intent == ResearchIntent.PROGRESS_SUMMARY:
        return "请问你希望整理哪段时间的进展？今天、本周，还是自上次汇报以来？", ["今天", "本周", "自上次汇报以来"]
    if slot == "project":
        return "请问这次任务对应哪个项目？", None
    if slot == "task_operation":
        return "请问你希望创建任务、更新任务状态，还是查看当前任务列表？", ["创建任务", "更新状态", "查看任务"]
    return f"请补充 {slot}。", None


def check_clarification_or_confirmation(
    *,
    intent_result: IntentResult,
    thread_id: str,
    user_id: str,
    original_user_input: str,
    store: ResearchOpsStateStore | None = None,
) -> HitlDecision:
    store = store or ResearchOpsStateStore()
    if intent_result.confidence < 0.65:
        reason = "low_confidence"
        question = "我不确定你想执行哪类 ResearchOps 任务。你是想做进展总结、实验复盘、项目规划、知识问答，还是任务追踪？"
        options = ["进展总结", "实验复盘", "项目规划", "知识问答", "任务追踪"]
    elif intent_result.missing_slots:
        first_missing = intent_result.missing_slots[0]
        reason = f"missing_{first_missing}"
        question, options = _question_for_missing_slot(first_missing, intent_result.intent)
    else:
        return HitlDecision(need_user_input=False)

    now = _now_iso()
    checkpoint = PendingCheckpoint(
        checkpoint_id=f"hitl_{uuid.uuid4().hex[:12]}",
        thread_id=thread_id,
        user_id=user_id,
        original_user_input=original_user_input,
        original_intent=intent_result.intent,
        intent_result=intent_result.model_dump(mode="json"),
        missing_slots=list(intent_result.missing_slots),
        pending_reason=reason,
        question=question,
        options=options,
        resume_node="retrieve_memory",
        pending_state={
            "intent": intent_result.intent.value,
            "project": intent_result.project,
            "time_range": intent_result.time_range,
            "output_format": intent_result.output_format,
            "task_operation": intent_result.task_operation,
        },
        created_at=now,
        updated_at=now,
    )
    store.save_checkpoint(checkpoint)

    return HitlDecision(
        need_user_input=True,
        reason=reason,
        question=question,
        options=options,
        original_intent=intent_result.intent,
        checkpoint_id=checkpoint.checkpoint_id,
        pending_state=checkpoint.pending_state,
        resume_node=checkpoint.resume_node,
    )


def _parse_time_range(user_response: str) -> str | None:
    text = user_response.strip().lower()
    if any(keyword in text for keyword in ("本周", "这周", "week")):
        return "this_week"
    if any(keyword in text for keyword in ("今天", "今日", "today")):
        return "today"
    if any(keyword in text for keyword in ("自上次", "上次汇报", "since")):
        return "since_last_report"
    if any(keyword in text for keyword in ("最近", "近期", "recent")):
        return "recent"
    return None


def resume_pending_checkpoint(
    *,
    thread_id: str,
    user_id: str,
    user_response: str,
    store: ResearchOpsStateStore | None = None,
) -> ResumeResult:
    store = store or ResearchOpsStateStore()
    checkpoint = store.get_pending_checkpoint(thread_id=thread_id, user_id=user_id)
    if checkpoint is None:
        return ResumeResult(has_pending=False, resolved=False, reason="no_pending_checkpoint")

    filled_slots: dict[str, str] = {}
    resume_state = dict(checkpoint.pending_state)
    if "time_range" in checkpoint.missing_slots:
        parsed = _parse_time_range(user_response)
        if parsed is not None:
            filled_slots["time_range"] = parsed
            resume_state["time_range"] = parsed

    resolved = set(checkpoint.missing_slots).issubset(filled_slots.keys())
    if resolved:
        store.mark_resolved(checkpoint.checkpoint_id, updated_at=_now_iso())

    return ResumeResult(
        has_pending=True,
        resolved=resolved,
        checkpoint_id=checkpoint.checkpoint_id,
        original_intent=checkpoint.original_intent,
        filled_slots=filled_slots,
        resume_state=resume_state,
        reason=None if resolved else "could_not_fill_missing_slots",
    )
