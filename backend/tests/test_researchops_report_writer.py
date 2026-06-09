import json
from pathlib import Path

from deerflow.researchops.context_builder import build_context_packet
from deerflow.researchops.memory_store import ResearchMemoryStore
from deerflow.researchops.report_writer import write_report
from deerflow.researchops.schemas import MemoryType, ResearchIntent, TaskStatus
from deerflow.researchops.tools.report_writer import report_writer_tool


def _seed_context(tmp_path: Path):
    store = ResearchMemoryStore(tmp_path / "research_memory.sqlite")
    store.upsert_memory(
        memory_type=MemoryType.PROJECT,
        project_id="researchops_agent",
        title="ResearchOps-Agent MVP",
        summary="完成 intent、HITL、typed memory 和 context tools。",
        evidence_refs=["note:weekly.md#L1-L4"],
    )
    store.upsert_memory(
        memory_type=MemoryType.EXPERIMENT,
        project_id="researchops_agent",
        title="Context recall smoke test",
        summary="ContextPacket 可以召回项目记忆和任务。",
        evidence_refs=["note:weekly.md#L5-L7"],
    )
    store.upsert_task(
        project_id="researchops_agent",
        title="实现 report writer",
        status=TaskStatus.IN_PROGRESS,
        next_action="补 evaluation runner",
        evidence_refs=["note:weekly.md#L8-L9"],
    )
    return build_context_packet(
        intent=ResearchIntent.PROGRESS_SUMMARY,
        project="researchops_agent",
        time_range="this_week",
        query="ResearchOps context report",
        memory_store=store,
    )


def test_write_progress_summary_report_with_required_sections_and_evidence(tmp_path: Path):
    packet = _seed_context(tmp_path)

    result = write_report(
        context_packet=packet,
        output_format="weekly_report",
        output_dir=tmp_path / "reports",
    )

    assert result.path.exists()
    markdown = result.path.read_text(encoding="utf-8")
    assert "# researchops_agent Weekly Report" in markdown
    assert "## 进展" in markdown
    assert "## 问题与阻塞" in markdown
    assert "## 下一步" in markdown
    assert "## Evidence" in markdown
    assert "note:weekly.md#L1-L4" in markdown
    assert result.evidence_count >= 3
    assert result.claim_count >= 1
    assert result.unsupported_claim_count >= 0


def test_report_writer_tool_writes_markdown_file(tmp_path: Path):
    packet = _seed_context(tmp_path)

    payload = report_writer_tool.invoke(
        {
            "context_packet_json": packet.model_dump_json(),
            "output_format": "weekly_report",
            "output_dir": str(tmp_path / "reports"),
        }
    )
    result = json.loads(payload)

    assert result["intent"] == "PROGRESS_SUMMARY"
    assert result["path"].endswith(".md")
    assert Path(result["path"]).exists()
    assert result["required_sections_present"] is True


def test_write_experiment_review_includes_log_summary(tmp_path: Path):
    packet = build_context_packet(
        intent=ResearchIntent.EXPERIMENT_REVIEW,
        project="researchops_agent",
        time_range=None,
        source_chunks=[
            {
                "source_ref": "log:train.log",
                "text": "loss=0.42 accuracy=0.73; ERROR CUDA out of memory",
                "metadata": {},
            }
        ],
        memory_store=ResearchMemoryStore(tmp_path / "memory.sqlite"),
    )

    result = write_report(
        context_packet=packet,
        output_format="experiment_review",
        output_dir=tmp_path / "reports",
        log_summary={"metrics": {"loss": 0.42, "accuracy": 0.73}, "errors": ["ERROR CUDA out of memory"]},
    )

    markdown = result.path.read_text(encoding="utf-8")
    assert "## 实验现象" in markdown
    assert "loss: 0.42" in markdown
    assert "ERROR CUDA out of memory" in markdown
    assert "log:train.log" in markdown
