from __future__ import annotations

import re

from deerflow.researchops.schemas import SourceChunk


def compress_source_chunk(chunk: SourceChunk, *, query: str, max_sentences: int = 4) -> SourceChunk:
    sentences = _split_sentences(chunk.text)
    query_terms = _terms(query)
    ranked = sorted(
        enumerate(sentences),
        key=lambda item: len(_terms(item[1]) & query_terms),
        reverse=True,
    )
    selected_indexes = sorted(index for index, sentence in ranked[:max_sentences] if sentence.strip())
    compressed_text = "\n".join(sentences[index] for index in selected_indexes).strip()
    metadata = dict(chunk.metadata)
    metadata["compressed"] = True
    metadata["original_length"] = len(chunk.text)
    metadata["compressed_length"] = len(compressed_text)
    return SourceChunk(
        source_ref=chunk.source_ref,
        text=compressed_text or chunk.text[:800],
        metadata=metadata,
    )


def _split_sentences(text: str) -> list[str]:
    parts = []
    for line in text.splitlines():
        parts.extend(part.strip() for part in re.split(r"(?<=[。！？.!?])\s+", line) if part.strip())
    return parts or [text]


def _terms(text: str) -> set[str]:
    ascii_terms = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text.lower())
    cjk_terms = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    return set(ascii_terms + cjk_terms)
