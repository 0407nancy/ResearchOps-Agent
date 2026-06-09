from __future__ import annotations

import json

from langchain.tools import tool

from deerflow.researchops.memory_store import ResearchMemoryStore
from deerflow.researchops.schemas import MemoryType


def _store_from_path(db_path: str | None) -> ResearchMemoryStore:
    return ResearchMemoryStore(db_path) if db_path else ResearchMemoryStore()


@tool("memory_writer", parse_docstring=True)
def memory_writer_tool(
    memory_type: str,
    project_id: str | None,
    title: str,
    summary: str = "",
    content_json: str = "{}",
    tags: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    db_path: str | None = None,
) -> str:
    """Write or update typed ResearchOps memory.

    Args:
        memory_type: One of ProjectMemory, ExperimentMemory, PaperMemory, DecisionMemory, PreferenceMemory, ResourceMemory, TaskMemory.
        project_id: Project identifier, or null for global memory.
        title: Stable memory title used for deduplication.
        summary: Short memory summary.
        content_json: JSON object containing type-specific structured content.
        tags: Optional tags.
        evidence_refs: Evidence references such as note ids or line ranges.
        db_path: Optional SQLite path for tests or local demos.
    """
    content = json.loads(content_json or "{}")
    record = _store_from_path(db_path).upsert_memory(
        memory_type=MemoryType(memory_type),
        project_id=project_id,
        title=title,
        summary=summary,
        content=content,
        tags=tags or [],
        evidence_refs=evidence_refs or [],
    )
    return json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False)


@tool("memory_search", parse_docstring=True)
def memory_search_tool(
    query: str = "",
    memory_type: str | None = None,
    project_id: str | None = None,
    limit: int = 10,
    db_path: str | None = None,
) -> str:
    """Search typed ResearchOps memory.

    Args:
        query: Search query.
        memory_type: Optional memory type filter.
        project_id: Optional project filter.
        limit: Maximum result count.
        db_path: Optional SQLite path for tests or local demos.
    """
    results = _store_from_path(db_path).search_memory(
        query=query,
        memory_type=MemoryType(memory_type) if memory_type else None,
        project_id=project_id,
        limit=limit,
    )
    return json.dumps([record.model_dump(mode="json") for record in results], indent=2, ensure_ascii=False)
