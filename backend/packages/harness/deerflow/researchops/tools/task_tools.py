from __future__ import annotations

import json

from langchain.tools import tool

from deerflow.researchops.memory_store import ResearchMemoryStore
from deerflow.researchops.schemas import TaskStatus


def _store_from_path(db_path: str | None) -> ResearchMemoryStore:
    return ResearchMemoryStore(db_path) if db_path else ResearchMemoryStore()


@tool("task_writer", parse_docstring=True)
def task_writer_tool(
    project_id: str,
    title: str,
    status: str,
    priority: str = "medium",
    blocked_by: list[str] | None = None,
    due_date: str | None = None,
    related_memories: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    next_action: str | None = None,
    db_path: str | None = None,
) -> str:
    """Create or update a ResearchOps task memory.

    Args:
        project_id: Project identifier for the task.
        title: Stable task title used for deduplication.
        status: One of todo, in_progress, blocked, done, dropped.
        priority: Task priority.
        blocked_by: Optional blockers.
        due_date: Optional due date.
        related_memories: Related memory ids.
        evidence_refs: Evidence references backing this task update.
        next_action: Next concrete action.
        db_path: Optional SQLite path for tests or local demos.
    """
    record = _store_from_path(db_path).upsert_task(
        project_id=project_id,
        title=title,
        status=TaskStatus(status),
        priority=priority,
        blocked_by=blocked_by or [],
        due_date=due_date,
        related_memories=related_memories or [],
        evidence_refs=evidence_refs or [],
        next_action=next_action,
    )
    return json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False)


@tool("task_reader", parse_docstring=True)
def task_reader_tool(
    project_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    db_path: str | None = None,
) -> str:
    """Read ResearchOps task memories by project and status.

    Args:
        project_id: Optional project filter.
        status: Optional status filter.
        limit: Maximum task count.
        db_path: Optional SQLite path for tests or local demos.
    """
    tasks = _store_from_path(db_path).list_tasks(
        project_id=project_id,
        status=TaskStatus(status) if status else None,
        limit=limit,
    )
    return json.dumps([task.model_dump(mode="json") for task in tasks], indent=2, ensure_ascii=False)
