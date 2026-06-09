import json
from pathlib import Path

from deerflow.researchops.session_trace import ResearchOpsSessionTraceStore
from deerflow.researchops.tools.session_trace_tools import session_trace_writer_tool


def test_session_trace_store_appends_and_lists_thread_events(tmp_path: Path):
    store = ResearchOpsSessionTraceStore(tmp_path / "trace.sqlite")

    first = store.append_event(
        thread_id="thread-1",
        user_id="user-1",
        event_type="classify_intent",
        payload={"intent": "PROGRESS_SUMMARY"},
    )
    second = store.append_event(
        thread_id="thread-1",
        user_id="user-1",
        event_type="build_context_packet",
        payload={"evidence_count": 2},
    )
    store.append_event(
        thread_id="thread-2",
        user_id="user-1",
        event_type="classify_intent",
        payload={"intent": "TASK_TRACKING"},
    )

    events = store.list_events(thread_id="thread-1", user_id="user-1")

    assert [event.event_id for event in events] == [first.event_id, second.event_id]
    assert events[0].payload["intent"] == "PROGRESS_SUMMARY"
    assert events[1].payload["evidence_count"] == 2


def test_session_trace_writer_tool_returns_event_json(tmp_path: Path):
    payload = session_trace_writer_tool.invoke(
        {
            "thread_id": "thread-1",
            "user_id": "user-1",
            "event_type": "execute_tools",
            "payload_json": '{"tool":"memory_search","result_count":3}',
            "db_path": str(tmp_path / "trace.sqlite"),
        }
    )
    event = json.loads(payload)

    assert event["event_type"] == "execute_tools"
    assert event["payload"]["tool"] == "memory_search"
