from pathlib import Path

from deerflow.researchops.hitl import check_clarification_or_confirmation, resume_pending_checkpoint
from deerflow.researchops.intent import classify_intent
from deerflow.researchops.schemas import ResearchIntent
from deerflow.researchops.state_store import ResearchOpsStateStore
from deerflow.researchops.tools.hitl_tools import researchops_check_hitl_tool, researchops_resume_pending_tool


def test_missing_time_range_creates_pending_checkpoint(tmp_path: Path):
    store = ResearchOpsStateStore(tmp_path / "researchops_state.sqlite")
    intent_result = classify_intent("帮我整理 OpenClaw RL 的进展")

    decision = check_clarification_or_confirmation(
        intent_result=intent_result,
        thread_id="thread_1",
        user_id="default",
        original_user_input="帮我整理 OpenClaw RL 的进展",
        store=store,
    )

    assert decision.need_user_input is True
    assert decision.reason == "missing_time_range"
    assert decision.original_intent == ResearchIntent.PROGRESS_SUMMARY
    assert "哪段时间" in decision.question

    pending = store.get_pending_checkpoint(thread_id="thread_1", user_id="default")
    assert pending is not None
    assert pending.original_intent == ResearchIntent.PROGRESS_SUMMARY
    assert pending.pending_state["project"] == "OpenClaw RL"
    assert pending.pending_state["time_range"] is None


def test_resume_pending_checkpoint_fills_slot_without_reclassifying(tmp_path: Path):
    store = ResearchOpsStateStore(tmp_path / "researchops_state.sqlite")
    intent_result = classify_intent("帮我整理 OpenClaw RL 的进展")
    check_clarification_or_confirmation(
        intent_result=intent_result,
        thread_id="thread_1",
        user_id="default",
        original_user_input="帮我整理 OpenClaw RL 的进展",
        store=store,
    )

    resumed = resume_pending_checkpoint(
        thread_id="thread_1",
        user_id="default",
        user_response="本周",
        store=store,
    )

    assert resumed.has_pending is True
    assert resumed.resolved is True
    assert resumed.original_intent == ResearchIntent.PROGRESS_SUMMARY
    assert resumed.filled_slots == {"time_range": "this_week"}
    assert resumed.resume_state["project"] == "OpenClaw RL"
    assert resumed.resume_state["time_range"] == "this_week"
    assert store.get_pending_checkpoint(thread_id="thread_1", user_id="default") is None


def test_resume_pending_checkpoint_reports_no_pending(tmp_path: Path):
    store = ResearchOpsStateStore(tmp_path / "researchops_state.sqlite")

    resumed = resume_pending_checkpoint(
        thread_id="thread_1",
        user_id="default",
        user_response="本周",
        store=store,
    )

    assert resumed.has_pending is False
    assert resumed.resolved is False
    assert resumed.original_intent is None


def test_hitl_tools_return_json(tmp_path: Path):
    db_path = str(tmp_path / "researchops_state.sqlite")
    check_payload = researchops_check_hitl_tool.invoke(
        {
            "intent_result_json": classify_intent("帮我整理 OpenClaw RL 的进展").model_dump_json(),
            "thread_id": "thread_1",
            "user_id": "default",
            "original_user_input": "帮我整理 OpenClaw RL 的进展",
            "db_path": db_path,
        }
    )

    assert '"need_user_input": true' in check_payload
    assert '"reason": "missing_time_range"' in check_payload

    resume_payload = researchops_resume_pending_tool.invoke(
        {
            "thread_id": "thread_1",
            "user_id": "default",
            "user_response": "本周",
            "db_path": db_path,
        }
    )

    assert '"resolved": true' in resume_payload
    assert '"time_range": "this_week"' in resume_payload
