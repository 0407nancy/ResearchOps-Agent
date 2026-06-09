from __future__ import annotations

import json

from langchain.tools import tool

from deerflow.researchops.hitl import check_clarification_or_confirmation, resume_pending_checkpoint
from deerflow.researchops.schemas import IntentResult
from deerflow.researchops.state_store import ResearchOpsStateStore


def _store_from_path(db_path: str | None) -> ResearchOpsStateStore:
    return ResearchOpsStateStore(db_path) if db_path else ResearchOpsStateStore()


@tool("researchops_check_hitl", parse_docstring=True)
def researchops_check_hitl_tool(
    intent_result_json: str,
    thread_id: str,
    user_id: str,
    original_user_input: str,
    db_path: str | None = None,
) -> str:
    """Check whether a ResearchOps request needs HITL clarification or confirmation.

    Args:
        intent_result_json: JSON string returned by classify_research_intent.
        thread_id: Current DeerFlow thread id.
        user_id: Current DeerFlow user id.
        original_user_input: Original user request before clarification.
        db_path: Optional SQLite path for tests or local demos.
    """
    intent_result = IntentResult.model_validate_json(intent_result_json)
    decision = check_clarification_or_confirmation(
        intent_result=intent_result,
        thread_id=thread_id,
        user_id=user_id,
        original_user_input=original_user_input,
        store=_store_from_path(db_path),
    )
    return json.dumps(decision.model_dump(mode="json"), indent=2, ensure_ascii=False)


@tool("researchops_resume_pending", parse_docstring=True)
def researchops_resume_pending_tool(
    thread_id: str,
    user_id: str,
    user_response: str,
    db_path: str | None = None,
) -> str:
    """Resume a pending ResearchOps HITL checkpoint with the user's latest answer.

    Args:
        thread_id: Current DeerFlow thread id.
        user_id: Current DeerFlow user id.
        user_response: User answer to the previous clarification question.
        db_path: Optional SQLite path for tests or local demos.
    """
    result = resume_pending_checkpoint(
        thread_id=thread_id,
        user_id=user_id,
        user_response=user_response,
        store=_store_from_path(db_path),
    )
    return json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False)
