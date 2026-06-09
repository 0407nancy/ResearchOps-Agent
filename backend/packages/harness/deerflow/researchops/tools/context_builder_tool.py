from __future__ import annotations

import json

from langchain.tools import tool

from deerflow.researchops.context_builder import build_context_packet
from deerflow.researchops.memory_store import ResearchMemoryStore
from deerflow.researchops.schemas import ResearchIntent


@tool("context_builder", parse_docstring=True)
def context_builder_tool(
    intent: str,
    project: str | None = None,
    time_range: str | None = None,
    query: str = "",
    source_chunks_json: str = "[]",
    memory_limit: int = 8,
    task_limit: int = 20,
    db_path: str | None = None,
) -> str:
    """Build a compact ResearchOps context packet with evidence references.

    Args:
        intent: One of the ResearchOps intent names.
        project: Optional project filter.
        time_range: Optional time range slot.
        query: Retrieval query.
        source_chunks_json: JSON array of source chunks from note_loader or log summaries.
        memory_limit: Maximum memory count.
        task_limit: Maximum task count.
        db_path: Optional SQLite path for tests or local demos.
    """
    source_chunks = json.loads(source_chunks_json or "[]")
    packet = build_context_packet(
        intent=ResearchIntent(intent),
        project=project,
        time_range=time_range,
        query=query,
        memory_store=ResearchMemoryStore(db_path) if db_path else ResearchMemoryStore(),
        source_chunks=source_chunks,
        memory_limit=memory_limit,
        task_limit=task_limit,
    )
    return packet.model_dump_json(indent=2)
