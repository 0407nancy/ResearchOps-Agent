from pathlib import Path

from deerflow.researchops.memory_store import ResearchMemoryStore
from deerflow.researchops.schemas import MemoryType, TaskStatus
from deerflow.researchops.tools.memory_tools import memory_search_tool, memory_writer_tool


def test_insert_and_search_project_memory(tmp_path: Path):
    store = ResearchMemoryStore(tmp_path / "research_memory.sqlite")
    record = store.upsert_memory(
        memory_type=MemoryType.PROJECT,
        project_id="researchops_agent",
        title="ResearchOps-Agent MVP",
        summary="Implement intent classifier and HITL checkpoint state.",
        content={"goal": "Build DeerFlow-native ResearchOps-Agent"},
        tags=["mvp", "agent"],
        evidence_refs=["note:20260609#L3-L8"],
    )

    results = store.search_memory(query="intent HITL", memory_type=MemoryType.PROJECT, project_id="researchops_agent")

    assert len(results) == 1
    assert results[0].id == record.id
    assert results[0].type == MemoryType.PROJECT
    assert results[0].evidence_refs == ["note:20260609#L3-L8"]


def test_upsert_deduplicates_by_type_project_and_title(tmp_path: Path):
    store = ResearchMemoryStore(tmp_path / "research_memory.sqlite")
    first = store.upsert_memory(
        memory_type=MemoryType.PROJECT,
        project_id="researchops_agent",
        title="ResearchOps-Agent MVP",
        summary="Initial summary",
    )
    second = store.upsert_memory(
        memory_type=MemoryType.PROJECT,
        project_id="researchops_agent",
        title="ResearchOps-Agent MVP",
        summary="Updated summary",
    )

    assert first.id == second.id
    assert store.get_memory(first.id).summary == "Updated summary"


def test_update_task_memory_status(tmp_path: Path):
    store = ResearchMemoryStore(tmp_path / "research_memory.sqlite")
    task = store.upsert_task(
        project_id="researchops_agent",
        title="实现 intent classifier",
        status=TaskStatus.TODO,
        priority="high",
        next_action="实现 HITL checkpoint",
    )

    updated = store.update_task_status(task.id, status=TaskStatus.DONE, next_action="开始 memory store")

    assert updated.content["status"] == "done"
    assert updated.content["next_action"] == "开始 memory store"


def test_memory_tools_return_json(tmp_path: Path):
    db_path = str(tmp_path / "research_memory.sqlite")
    write_payload = memory_writer_tool.invoke(
        {
            "memory_type": "TaskMemory",
            "project_id": "researchops_agent",
            "title": "实现 memory store",
            "summary": "实现 SQLite typed research memory store",
            "content_json": '{"status":"todo","priority":"high","next_action":"写检索测试"}',
            "tags": ["memory", "mvp"],
            "evidence_refs": ["note:20260609#L10-L12"],
            "db_path": db_path,
        }
    )
    assert '"type": "TaskMemory"' in write_payload

    search_payload = memory_search_tool.invoke(
        {
            "query": "SQLite memory",
            "memory_type": "TaskMemory",
            "project_id": "researchops_agent",
            "db_path": db_path,
        }
    )

    assert "实现 memory store" in search_payload
