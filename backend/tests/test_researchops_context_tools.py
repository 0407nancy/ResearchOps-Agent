import json
from pathlib import Path

from deerflow.researchops.context_builder import build_context_packet
from deerflow.researchops.memory_store import ResearchMemoryStore
from deerflow.researchops.schemas import MemoryType, ResearchIntent, TaskStatus
from deerflow.researchops.tools.log_parser import log_parser_tool
from deerflow.researchops.tools.note_loader import note_loader_tool
from deerflow.researchops.tools.task_tools import task_reader_tool, task_writer_tool


def test_note_loader_reads_markdown_with_line_grounded_chunks(tmp_path: Path):
    note_path = tmp_path / "daily.md"
    note_path.write_text(
        "# Daily\n"
        "今天完成 intent classifier。\n"
        "下一步实现 ContextPacket。\n"
        "实验日志显示 loss=0.42。\n",
        encoding="utf-8",
    )

    payload = note_loader_tool.invoke({"paths": [str(note_path)], "max_lines_per_chunk": 2})
    chunks = json.loads(payload)

    assert len(chunks) == 2
    assert chunks[0]["source_ref"].endswith("daily.md#L1-L2")
    assert "intent classifier" in chunks[0]["text"]
    assert chunks[1]["source_ref"].endswith("daily.md#L3-L4")


def test_log_parser_extracts_errors_metrics_and_observations(tmp_path: Path):
    log_path = tmp_path / "train.log"
    log_path.write_text(
        "step=10 loss=0.89 acc=0.51\n"
        "WARN dataloader is slow\n"
        "step=20 loss=0.42 accuracy=0.73\n"
        "ERROR CUDA out of memory at batch 64\n",
        encoding="utf-8",
    )

    payload = log_parser_tool.invoke({"path": str(log_path)})
    parsed = json.loads(payload)

    assert parsed["source_ref"].endswith("train.log")
    assert parsed["metrics"]["loss"] == 0.42
    assert parsed["metrics"]["accuracy"] == 0.73
    assert parsed["errors"] == ["ERROR CUDA out of memory at batch 64"]
    assert parsed["observations"] == ["WARN dataloader is slow"]


def test_task_tools_create_update_and_read_task_memory(tmp_path: Path):
    db_path = str(tmp_path / "research_memory.sqlite")

    created_payload = task_writer_tool.invoke(
        {
            "project_id": "researchops_agent",
            "title": "实现 ContextPacket",
            "status": "todo",
            "priority": "high",
            "next_action": "先写 context builder 测试",
            "evidence_refs": ["note:daily.md#L2-L3"],
            "db_path": db_path,
        }
    )
    created = json.loads(created_payload)

    assert created["type"] == "TaskMemory"
    assert created["content"]["status"] == "todo"

    updated_payload = task_writer_tool.invoke(
        {
            "project_id": "researchops_agent",
            "title": "实现 ContextPacket",
            "status": "in_progress",
            "next_action": "实现最小 context builder",
            "db_path": db_path,
        }
    )
    updated = json.loads(updated_payload)

    assert updated["id"] == created["id"]
    assert updated["content"]["status"] == "in_progress"

    read_payload = task_reader_tool.invoke(
        {
            "project_id": "researchops_agent",
            "status": "in_progress",
            "db_path": db_path,
        }
    )
    tasks = json.loads(read_payload)

    assert [task["title"] for task in tasks] == ["实现 ContextPacket"]


def test_context_packet_filters_memory_tasks_and_evidence(tmp_path: Path):
    store = ResearchMemoryStore(tmp_path / "research_memory.sqlite")
    store.upsert_memory(
        memory_type=MemoryType.PROJECT,
        project_id="researchops_agent",
        title="ResearchOps-Agent MVP",
        summary="Phase 4 需要 context builder 和 evidence table。",
        evidence_refs=["note:daily.md#L1-L2"],
    )
    store.upsert_memory(
        memory_type=MemoryType.EXPERIMENT,
        project_id="other_project",
        title="Unrelated experiment",
        summary="不应该被当前项目召回。",
    )
    store.upsert_task(
        project_id="researchops_agent",
        title="实现 ContextPacket",
        status=TaskStatus.IN_PROGRESS,
        evidence_refs=["note:daily.md#L2-L3"],
    )

    packet = build_context_packet(
        intent=ResearchIntent.PROGRESS_SUMMARY,
        project="researchops_agent",
        time_range="this_week",
        query="context evidence",
        memory_store=store,
        source_chunks=[
            {
                "source_ref": "note:daily.md#L1-L2",
                "text": "Phase 4 需要 context builder 和 evidence table。",
                "metadata": {"path": "daily.md"},
            }
        ],
    )

    assert packet.intent == ResearchIntent.PROGRESS_SUMMARY
    assert packet.project == "researchops_agent"
    assert [memory.title for memory in packet.memories] == ["ResearchOps-Agent MVP"]
    assert [task.title for task in packet.tasks] == ["实现 ContextPacket"]
    assert packet.source_chunks[0].source_ref == "note:daily.md#L1-L2"
    assert {evidence.source_ref for evidence in packet.evidence_table} == {
        "note:daily.md#L1-L2",
        "note:daily.md#L2-L3",
    }


def test_context_packet_reranks_and_compresses_source_chunks(tmp_path: Path):
    store = ResearchMemoryStore(tmp_path / "research_memory.sqlite")
    store.upsert_memory(
        memory_type=MemoryType.PROJECT,
        project_id="researchops_agent",
        title="Context memory",
        summary="Context builder should prefer evidence grounded context.",
        evidence_refs=["note:context.md#L2-L3"],
    )

    packet = build_context_packet(
        intent=ResearchIntent.PROGRESS_SUMMARY,
        project="researchops_agent",
        time_range="this_week",
        query="context evidence",
        memory_store=store,
        source_chunks=[
            {
                "source_ref": "note:noise.md#L1-L5",
                "text": "无关背景。\n普通记录。\n更多普通记录。",
                "metadata": {"path": "noise.md"},
            },
            {
                "source_ref": "note:context.md#L1-L5",
                "text": "无关开头。\nContext builder 生成 evidence table。\nReport writer 使用 evidence refs。\n无关结尾。",
                "metadata": {"path": "context.md"},
            },
        ],
    )

    assert packet.source_chunks[0].source_ref == "note:context.md#L1-L5"
    assert packet.source_chunks[0].metadata["compressed"] is True
    assert "Context builder" in packet.source_chunks[0].text
    assert "无关开头" not in packet.source_chunks[0].text
