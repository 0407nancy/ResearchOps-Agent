from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from deerflow.config.paths import get_paths
from deerflow.researchops.schemas import MemoryType, ResearchMemoryRecord, TaskStatus


def default_memory_db_path(*, user_id: str = "default", agent_name: str = "researchops-agent") -> Path:
    return get_paths().user_agent_dir(user_id, agent_name) / "research_memory.sqlite"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ResearchMemoryStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else default_memory_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_memory (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    project_id TEXT,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    importance INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    supersedes_id TEXT,
                    UNIQUE(type, project_id, title)
                )
                """
            )
            try:
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS research_memory_fts
                    USING fts5(id UNINDEXED, title, summary, content_text, tags_text)
                    """
                )
            except sqlite3.OperationalError:
                pass

    def upsert_memory(
        self,
        *,
        memory_type: MemoryType | str,
        project_id: str | None,
        title: str,
        summary: str = "",
        content: dict | None = None,
        tags: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        confidence: float = 1.0,
        importance: int = 3,
        status: str = "active",
        supersedes_id: str | None = None,
    ) -> ResearchMemoryRecord:
        normalized_type = MemoryType(memory_type)
        content = content or {}
        tags = tags or []
        evidence_refs = evidence_refs or []
        now = _now_iso()

        existing = self._find_existing(normalized_type, project_id, title)
        record_id = existing["id"] if existing is not None else f"mem_{uuid.uuid4().hex[:12]}"
        created_at = existing["created_at"] if existing is not None else now

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO research_memory (
                    id, type, project_id, title, summary, content_json, tags_json,
                    evidence_refs_json, confidence, importance, status, created_at,
                    updated_at, supersedes_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    normalized_type.value,
                    project_id,
                    title,
                    summary,
                    json.dumps(content, ensure_ascii=False),
                    json.dumps(tags, ensure_ascii=False),
                    json.dumps(evidence_refs, ensure_ascii=False),
                    confidence,
                    importance,
                    status,
                    created_at,
                    now,
                    supersedes_id,
                ),
            )
            self._sync_fts(conn, record_id, title, summary, content, tags)

        return self.get_memory(record_id)

    def upsert_task(
        self,
        *,
        project_id: str,
        title: str,
        status: TaskStatus,
        priority: str = "medium",
        blocked_by: list[str] | None = None,
        due_date: str | None = None,
        related_memories: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        next_action: str | None = None,
    ) -> ResearchMemoryRecord:
        content = {
            "status": status.value,
            "priority": priority,
            "blocked_by": blocked_by or [],
            "due_date": due_date,
            "related_memories": related_memories or [],
            "next_action": next_action,
        }
        return self.upsert_memory(
            memory_type=MemoryType.TASK,
            project_id=project_id,
            title=title,
            summary=next_action or title,
            content=content,
            tags=["task", status.value, priority],
            evidence_refs=evidence_refs or [],
        )

    def update_task_status(self, memory_id: str, *, status: TaskStatus, next_action: str | None = None) -> ResearchMemoryRecord:
        record = self.get_memory(memory_id)
        if record.type != MemoryType.TASK:
            raise ValueError(f"Memory {memory_id} is not TaskMemory")
        content = dict(record.content)
        content["status"] = status.value
        if next_action is not None:
            content["next_action"] = next_action
        return self.upsert_memory(
            memory_type=record.type,
            project_id=record.project_id,
            title=record.title,
            summary=next_action or record.summary,
            content=content,
            tags=list({*record.tags, status.value}),
            evidence_refs=record.evidence_refs,
            confidence=record.confidence,
            importance=record.importance,
            status=record.status,
            supersedes_id=record.supersedes_id,
        )

    def get_memory(self, memory_id: str) -> ResearchMemoryRecord:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM research_memory WHERE id = ?", (memory_id,)).fetchone()
        if row is None:
            raise KeyError(memory_id)
        return self._row_to_record(row)

    def search_memory(
        self,
        *,
        query: str = "",
        memory_type: MemoryType | str | None = None,
        project_id: str | None = None,
        limit: int = 10,
    ) -> list[ResearchMemoryRecord]:
        normalized_type = MemoryType(memory_type).value if memory_type else None
        params: list[object] = []
        clauses = ["status = 'active'"]
        if normalized_type:
            clauses.append("type = ?")
            params.append(normalized_type)
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)

        ids = self._search_ids_with_fts(query, limit=limit) if query.strip() else []
        if ids:
            placeholders = ",".join("?" for _ in ids)
            clauses.append(f"id IN ({placeholders})")
            params.extend(ids)
        elif query.strip():
            like = f"%{query}%"
            clauses.append("(title LIKE ? OR summary LIKE ? OR content_json LIKE ? OR tags_json LIKE ?)")
            params.extend([like, like, like, like])

        sql = f"SELECT * FROM research_memory WHERE {' AND '.join(clauses)} ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _find_existing(self, memory_type: MemoryType, project_id: str | None, title: str) -> sqlite3.Row | None:
        if project_id is None:
            sql = "SELECT * FROM research_memory WHERE type = ? AND project_id IS NULL AND title = ?"
            params = (memory_type.value, title)
        else:
            sql = "SELECT * FROM research_memory WHERE type = ? AND project_id = ? AND title = ?"
            params = (memory_type.value, project_id, title)
        with self._connect() as conn:
            return conn.execute(sql, params).fetchone()

    def _sync_fts(self, conn: sqlite3.Connection, memory_id: str, title: str, summary: str, content: dict, tags: list[str]) -> None:
        try:
            conn.execute("DELETE FROM research_memory_fts WHERE id = ?", (memory_id,))
            conn.execute(
                "INSERT INTO research_memory_fts(id, title, summary, content_text, tags_text) VALUES (?, ?, ?, ?, ?)",
                (memory_id, title, summary, json.dumps(content, ensure_ascii=False), " ".join(tags)),
            )
        except sqlite3.OperationalError:
            pass

    def _search_ids_with_fts(self, query: str, *, limit: int) -> list[str]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT id FROM research_memory_fts WHERE research_memory_fts MATCH ? LIMIT ?",
                    (query, limit),
                ).fetchall()
            return [row["id"] for row in rows]
        except sqlite3.OperationalError:
            return []

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ResearchMemoryRecord:
        return ResearchMemoryRecord(
            id=row["id"],
            type=row["type"],
            project_id=row["project_id"],
            title=row["title"],
            summary=row["summary"],
            content=json.loads(row["content_json"]),
            tags=json.loads(row["tags_json"]),
            evidence_refs=json.loads(row["evidence_refs_json"]),
            confidence=row["confidence"],
            importance=row["importance"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            supersedes_id=row["supersedes_id"],
        )

