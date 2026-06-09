from __future__ import annotations

from collections.abc import Mapping, Sequence

from deerflow.researchops.memory_store import ResearchMemoryStore
from deerflow.researchops.schemas import (
    ContextPacket,
    EvidenceRef,
    MemoryType,
    ResearchIntent,
    ResearchMemoryRecord,
    SourceChunk,
)


INTENT_MEMORY_TYPES: dict[ResearchIntent, list[MemoryType]] = {
    ResearchIntent.PROGRESS_SUMMARY: [MemoryType.PROJECT, MemoryType.EXPERIMENT, MemoryType.DECISION],
    ResearchIntent.EXPERIMENT_REVIEW: [MemoryType.EXPERIMENT, MemoryType.PROJECT, MemoryType.DECISION],
    ResearchIntent.PROJECT_PLANNING: [MemoryType.PROJECT, MemoryType.TASK, MemoryType.DECISION, MemoryType.RESOURCE],
    ResearchIntent.KNOWLEDGE_QA: [MemoryType.PAPER, MemoryType.RESOURCE, MemoryType.PROJECT, MemoryType.DECISION],
    ResearchIntent.TASK_TRACKING: [MemoryType.TASK, MemoryType.PROJECT, MemoryType.DECISION],
}


def build_context_packet(
    *,
    intent: ResearchIntent | str,
    project: str | None,
    time_range: str | None,
    query: str = "",
    memory_store: ResearchMemoryStore | None = None,
    source_chunks: Sequence[SourceChunk | Mapping] | None = None,
    memory_limit: int = 8,
    task_limit: int = 20,
) -> ContextPacket:
    normalized_intent = ResearchIntent(intent)
    store = memory_store or ResearchMemoryStore()
    chunks = [_to_source_chunk(chunk) for chunk in source_chunks or []]

    memories: list[ResearchMemoryRecord] = []
    seen_ids: set[str] = set()
    for memory_type in INTENT_MEMORY_TYPES[normalized_intent]:
        if memory_type == MemoryType.TASK:
            continue
        records = store.search_memory(
            query=query,
            memory_type=memory_type,
            project_id=project,
            limit=memory_limit,
        )
        if query.strip() and not records:
            records = store.search_memory(
                query="",
                memory_type=memory_type,
                project_id=project,
                limit=memory_limit,
            )
        for record in records:
            if record.id not in seen_ids:
                memories.append(record)
                seen_ids.add(record.id)

    tasks = store.list_tasks(project_id=project, limit=task_limit)
    evidence_table = _build_evidence_table(memories=memories, tasks=tasks, chunks=chunks)

    return ContextPacket(
        intent=normalized_intent,
        project=project,
        time_range=time_range,
        memories=memories[:memory_limit],
        source_chunks=chunks,
        tasks=tasks,
        evidence_table=evidence_table,
    )


def _to_source_chunk(chunk: SourceChunk | Mapping) -> SourceChunk:
    if isinstance(chunk, SourceChunk):
        return chunk
    return SourceChunk.model_validate(dict(chunk))


def _build_evidence_table(
    *,
    memories: Sequence[ResearchMemoryRecord],
    tasks: Sequence[ResearchMemoryRecord],
    chunks: Sequence[SourceChunk],
) -> list[EvidenceRef]:
    evidence: dict[str, EvidenceRef] = {}

    for chunk in chunks:
        evidence[chunk.source_ref] = EvidenceRef(
            source_ref=chunk.source_ref,
            kind="source",
            snippet=chunk.text[:240],
        )

    for record in memories:
        for source_ref in record.evidence_refs:
            evidence.setdefault(
                source_ref,
                EvidenceRef(
                    source_ref=source_ref,
                    kind="memory",
                    title=record.title,
                    snippet=record.summary[:240],
                ),
            )

    for task in tasks:
        for source_ref in task.evidence_refs:
            evidence.setdefault(
                source_ref,
                EvidenceRef(
                    source_ref=source_ref,
                    kind="task",
                    title=task.title,
                    snippet=task.summary[:240],
                ),
            )

    return list(evidence.values())
