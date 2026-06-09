from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from deerflow.config.paths import get_paths


def default_trace_db_path(*, user_id: str = "default", agent_name: str = "researchops-agent") -> Path:
    return get_paths().user_agent_dir(user_id, agent_name) / "session_trace.sqlite"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class SessionTraceEvent(BaseModel):
    event_id: str
    thread_id: str
    user_id: str
    event_type: str
    payload: dict = Field(default_factory=dict)
    created_at: str


class ResearchOpsSessionTraceStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else default_trace_db_path()
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
                CREATE TABLE IF NOT EXISTS researchops_session_trace (
                    event_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_researchops_session_trace_thread
                ON researchops_session_trace(thread_id, user_id, created_at)
                """
            )

    def append_event(
        self,
        *,
        thread_id: str,
        user_id: str,
        event_type: str,
        payload: dict | None = None,
    ) -> SessionTraceEvent:
        event = SessionTraceEvent(
            event_id=f"trace_{uuid.uuid4().hex[:12]}",
            thread_id=thread_id,
            user_id=user_id,
            event_type=event_type,
            payload=payload or {},
            created_at=_now_iso(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO researchops_session_trace (
                    event_id, thread_id, user_id, event_type, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.thread_id,
                    event.user_id,
                    event.event_type,
                    json.dumps(event.payload, ensure_ascii=False),
                    event.created_at,
                ),
            )
        return event

    def list_events(self, *, thread_id: str, user_id: str, limit: int = 100) -> list[SessionTraceEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM researchops_session_trace
                WHERE thread_id = ? AND user_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (thread_id, user_id, limit),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> SessionTraceEvent:
        return SessionTraceEvent(
            event_id=row["event_id"],
            thread_id=row["thread_id"],
            user_id=row["user_id"],
            event_type=row["event_type"],
            payload=json.loads(row["payload_json"]),
            created_at=row["created_at"],
        )
