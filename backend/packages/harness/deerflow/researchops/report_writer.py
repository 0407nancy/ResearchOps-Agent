from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from deerflow.researchops.evidence.verifier import extract_claims, verify_claims
from deerflow.researchops.schemas import ContextPacket, ResearchIntent, ResearchMemoryRecord


class ReportResult(BaseModel):
    path: Path
    intent: ResearchIntent
    output_format: str
    evidence_count: int
    required_sections_present: bool
    claim_count: int = 0
    unsupported_claim_count: int = 0


REQUIRED_SECTIONS: dict[ResearchIntent, list[str]] = {
    ResearchIntent.PROGRESS_SUMMARY: ["进展", "问题与阻塞", "下一步", "Evidence"],
    ResearchIntent.EXPERIMENT_REVIEW: ["实验目标", "实验现象", "失败假设", "下一步排查", "Evidence"],
    ResearchIntent.PROJECT_PLANNING: ["当前状态", "优先级判断", "阶段计划", "下一步", "Evidence"],
    ResearchIntent.KNOWLEDGE_QA: ["问题", "回答", "Evidence"],
    ResearchIntent.TASK_TRACKING: ["任务更新", "阻塞", "下一步", "Evidence"],
}


def write_report(
    *,
    context_packet: ContextPacket,
    output_format: str,
    output_dir: str | Path = "outputs/reports",
    log_summary: dict[str, Any] | None = None,
) -> ReportResult:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    markdown = render_report(context_packet=context_packet, output_format=output_format, log_summary=log_summary)
    verified_claims = verify_claims(claims=extract_claims(markdown), evidence_table=context_packet.evidence_table)
    filename = _build_filename(context_packet=context_packet, output_format=output_format)
    path = output_path / filename
    path.write_text(markdown, encoding="utf-8")

    sections = REQUIRED_SECTIONS[context_packet.intent]
    return ReportResult(
        path=path,
        intent=context_packet.intent,
        output_format=output_format,
        evidence_count=len(context_packet.evidence_table),
        required_sections_present=all(f"## {section}" in markdown for section in sections),
        claim_count=len(verified_claims),
        unsupported_claim_count=sum(1 for claim in verified_claims if claim.support_status == "unsupported"),
    )


def render_report(
    *,
    context_packet: ContextPacket,
    output_format: str,
    log_summary: dict[str, Any] | None = None,
) -> str:
    if context_packet.intent == ResearchIntent.EXPERIMENT_REVIEW:
        return _render_experiment_review(context_packet, output_format, log_summary or {})
    if context_packet.intent == ResearchIntent.PROJECT_PLANNING:
        return _render_project_planning(context_packet, output_format)
    if context_packet.intent == ResearchIntent.TASK_TRACKING:
        return _render_task_tracking(context_packet, output_format)
    if context_packet.intent == ResearchIntent.KNOWLEDGE_QA:
        return _render_knowledge_qa(context_packet, output_format)
    return _render_progress_summary(context_packet, output_format)


def _render_progress_summary(packet: ContextPacket, output_format: str) -> str:
    title = _title(packet, output_format)
    progress = _memory_bullets(packet.memories) or ["- 暂未检索到可引用的进展记忆。"]
    blockers = _blocked_task_bullets(packet.tasks) or ["- 暂未发现明确阻塞。"]
    next_actions = _task_bullets(packet.tasks) or ["- 需要补充下一步任务记录。"]
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- Intent: `{packet.intent.value}`",
            f"- Time Range: `{packet.time_range or 'unspecified'}`",
            "",
            "## 进展",
            *progress,
            "",
            "## 问题与阻塞",
            *blockers,
            "",
            "## 下一步",
            *next_actions,
            "",
            *_evidence_section(packet),
        ]
    )


def _render_experiment_review(packet: ContextPacket, output_format: str, log_summary: dict[str, Any]) -> str:
    metrics = log_summary.get("metrics") or {}
    errors = log_summary.get("errors") or []
    metric_lines = [f"- {key}: {value}" for key, value in metrics.items()] or ["- 暂未解析到关键指标。"]
    error_lines = [f"- {error}" for error in errors] or ["- 暂未解析到错误。"]
    return "\n".join(
        [
            f"# {_title(packet, output_format)}",
            "",
            "## 实验目标",
            *(_memory_bullets(packet.memories) or ["- 需要补充实验目标或配置记录。"]),
            "",
            "## 实验现象",
            *metric_lines,
            *error_lines,
            "",
            "## 失败假设",
            "- 基于当前证据，优先检查日志中错误对应的资源、配置或数据路径问题。",
            "",
            "## 下一步排查",
            *(_task_bullets(packet.tasks) or ["- 复现实验并补充关键配置、指标和错误上下文。"]),
            "",
            *_evidence_section(packet),
        ]
    )


def _render_project_planning(packet: ContextPacket, output_format: str) -> str:
    return "\n".join(
        [
            f"# {_title(packet, output_format)}",
            "",
            "## 当前状态",
            *(_memory_bullets(packet.memories) or ["- 当前项目状态证据不足。"]),
            "",
            "## 优先级判断",
            "- 优先推进会解除阻塞或产生可验证里程碑的任务。",
            "",
            "## 阶段计划",
            *(_task_bullets(packet.tasks) or ["- 需要创建阶段任务。"]),
            "",
            "## 下一步",
            "- 将计划拆成可追踪 TaskMemory，并在每次会话后更新状态。",
            "",
            *_evidence_section(packet),
        ]
    )


def _render_task_tracking(packet: ContextPacket, output_format: str) -> str:
    return "\n".join(
        [
            f"# {_title(packet, output_format)}",
            "",
            "## 任务更新",
            *(_task_bullets(packet.tasks) or ["- 暂无任务更新。"]),
            "",
            "## 阻塞",
            *(_blocked_task_bullets(packet.tasks) or ["- 暂未发现明确阻塞。"]),
            "",
            "## 下一步",
            "- 对状态不明确的任务触发 clarification，并将确认结果写回 TaskMemory。",
            "",
            *_evidence_section(packet),
        ]
    )


def _render_knowledge_qa(packet: ContextPacket, output_format: str) -> str:
    return "\n".join(
        [
            f"# {_title(packet, output_format)}",
            "",
            "## 问题",
            "- 见用户当前请求。",
            "",
            "## 回答",
            *(_memory_bullets(packet.memories) or ["- 当前本地记忆不足，需要补充论文、资源或项目记录。"]),
            "",
            *_evidence_section(packet),
        ]
    )


def _memory_bullets(memories: list[ResearchMemoryRecord]) -> list[str]:
    return [f"- {memory.title}: {memory.summary} {_refs(memory.evidence_refs)}".rstrip() for memory in memories]


def _task_bullets(tasks: list[ResearchMemoryRecord]) -> list[str]:
    bullets = []
    for task in tasks:
        status = task.content.get("status", "unknown")
        next_action = task.content.get("next_action")
        suffix = f"；next: {next_action}" if next_action else ""
        bullets.append(f"- [{status}] {task.title}{suffix} {_refs(task.evidence_refs)}".rstrip())
    return bullets


def _blocked_task_bullets(tasks: list[ResearchMemoryRecord]) -> list[str]:
    blocked = [task for task in tasks if task.content.get("status") == "blocked"]
    return _task_bullets(blocked)


def _evidence_section(packet: ContextPacket) -> list[str]:
    if not packet.evidence_table:
        return ["## Evidence", "- Evidence 不足，以上内容需要人工确认。"]
    lines = ["## Evidence"]
    for evidence in packet.evidence_table:
        title = f" - {evidence.title}" if evidence.title else ""
        snippet = f": {evidence.snippet}" if evidence.snippet else ""
        lines.append(f"- `{evidence.source_ref}` ({evidence.kind}){title}{snippet}")
    return lines


def _refs(refs: list[str]) -> str:
    if not refs:
        return ""
    return " ".join(f"[{ref}]" for ref in refs)


def _title(packet: ContextPacket, output_format: str) -> str:
    project = packet.project or "ResearchOps"
    label = output_format.replace("_", " ").title()
    return f"{project} {label}"


def _build_filename(*, context_packet: ContextPacket, output_format: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    project = _slug(context_packet.project or "researchops")
    fmt = _slug(output_format)
    return f"{timestamp}-{project}-{fmt}.md"


def _slug(value: str) -> str:
    value = value.strip().lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "report"
