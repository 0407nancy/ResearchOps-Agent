from __future__ import annotations

import json
from pathlib import Path

from langchain.tools import tool

from deerflow.researchops.schemas import SourceChunk


SUPPORTED_NOTE_SUFFIXES = {".md", ".markdown", ".txt"}


@tool("note_loader", parse_docstring=True)
def note_loader_tool(paths: list[str], max_lines_per_chunk: int = 40) -> str:
    """Load local markdown or text research notes into line-grounded chunks.

    Args:
        paths: Markdown or text file paths to load.
        max_lines_per_chunk: Maximum lines per returned chunk.
    """
    chunks: list[SourceChunk] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.suffix.lower() not in SUPPORTED_NOTE_SUFFIXES:
            continue
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(str(path))
        lines = path.read_text(encoding="utf-8").splitlines()
        for start in range(0, len(lines), max_lines_per_chunk):
            block = lines[start : start + max_lines_per_chunk]
            if not any(line.strip() for line in block):
                continue
            end = start + len(block)
            chunks.append(
                SourceChunk(
                    source_ref=f"note:{path.name}#L{start + 1}-L{end}",
                    text="\n".join(block),
                    metadata={"path": str(path), "start_line": start + 1, "end_line": end},
                )
            )
    return json.dumps([chunk.model_dump(mode="json") for chunk in chunks], indent=2, ensure_ascii=False)
