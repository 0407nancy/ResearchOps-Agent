from __future__ import annotations

import json

from langchain.tools import tool

from deerflow.researchops.session_trace import ResearchOpsSessionTraceStore


def _store_from_path(db_path: str | None) -> ResearchOpsSessionTraceStore:
    return ResearchOpsSessionTraceStore(db_path) if db_path else ResearchOpsSessionTraceStore()


@tool("session_trace_writer", parse_docstring=True)
def session_trace_writer_tool(
    thread_id: str,
    user_id: str,
    event_type: str,
    payload_json: str = "{}",
    db_path: str | None = None,
) -> str:
    """Append a ResearchOps session trace event.

    Args:
        thread_id: DeerFlow thread id.
        user_id: User id.
        event_type: Harness step or tool event type.
        payload_json: JSON payload for this trace event.
        db_path: Optional SQLite path for tests or demos.
    """
    event = _store_from_path(db_path).append_event(
        thread_id=thread_id,
        user_id=user_id,
        event_type=event_type,
        payload=json.loads(payload_json or "{}"),
    )
    return event.model_dump_json(indent=2)
