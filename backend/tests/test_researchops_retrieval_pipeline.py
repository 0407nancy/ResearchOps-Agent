from deerflow.researchops.compression import compress_source_chunk
from deerflow.researchops.rerank import RetrievalCandidate, rerank_candidates
from deerflow.researchops.schemas import SourceChunk


def test_rerank_prefers_project_match_query_overlap_and_evidence_density():
    candidates = [
        RetrievalCandidate(
            ref="mem:other",
            text="unrelated project memory",
            kind="memory",
            project_id="other",
            evidence_refs=[],
        ),
        RetrievalCandidate(
            ref="mem:researchops",
            text="ResearchOps-Agent context builder evidence table report writer",
            kind="memory",
            project_id="researchops_agent",
            evidence_refs=["note:weekly.md#L1-L4"],
        ),
        RetrievalCandidate(
            ref="note:noise",
            text="context words but no project evidence",
            kind="source",
            project_id=None,
            evidence_refs=[],
        ),
    ]

    ranked = rerank_candidates(
        query="ResearchOps-Agent context evidence",
        candidates=candidates,
        project_id="researchops_agent",
        limit=2,
    )

    assert [candidate.ref for candidate in ranked] == ["mem:researchops", "note:noise"]
    assert ranked[0].score > ranked[1].score


def test_compress_source_chunk_keeps_query_relevant_sentences_and_line_ref():
    chunk = SourceChunk(
        source_ref="note:long.md#L1-L8",
        text=(
            "今天整理了无关背景。\n"
            "Context builder 已经可以构建 evidence table。\n"
            "这里还有很多普通笔记。\n"
            "Report writer 会使用 evidence ref 输出周报。\n"
            "最后是无关记录。"
        ),
        metadata={"path": "long.md"},
    )

    compressed = compress_source_chunk(chunk, query="context evidence report", max_sentences=2)

    assert compressed.source_ref == "note:long.md#L1-L8"
    assert "Context builder" in compressed.text
    assert "Report writer" in compressed.text
    assert "无关背景" not in compressed.text
    assert compressed.metadata["compressed"] is True
