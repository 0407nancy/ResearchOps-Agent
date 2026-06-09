from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from deerflow.config.paths import get_paths
from deerflow.researchops.schemas import HitlCheckpointStatus, PendingCheckpoint


def default_state_db_path(*, user_id: str = "default", agent_name: str = "researchops-agent") -> Path:
    return get_paths().user_agent_dir(user_id, agent_name) / "researchops_state.sqlite"


class ResearchOpsStateStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else default_state_db_path()
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
                CREATE TABLE IF NOT EXISTS hitl_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    original_intent TEXT NOT NULL,
                    original_user_input TEXT NOT NULL,
                    intent_result_json TEXT NOT NULL,
                    pending_state_json TEXT NOT NULL,
                    missing_slots_json TEXT NOT NULL,
                    pending_reason TEXT NOT NULL,
                    question TEXT NOT NULL,
                    options_json TEXT,
                    resume_node TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_hitl_pending_thread
                ON hitl_checkpoints(thread_id, user_id, status, updated_at)
                """
            )

    def save_checkpoint(self, checkpoint: PendingCheckpoint) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO hitl_checkpoints (
                    checkpoint_id, thread_id, user_id, original_intent,
                    original_user_input, intent_result_json, pending_state_json,
                    missing_slots_json, pending_reason, question, options_json,
                    resume_node, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.thread_id,
                    checkpoint.user_id,
                    checkpoint.original_intent.value,
                    checkpoint.original_user_input,
                    json.dumps(checkpoint.intent_result, ensure_ascii=False),
                    json.dumps(checkpoint.pending_state, ensure_ascii=False),
                    json.dumps(checkpoint.missing_slots, ensure_ascii=False),
                    checkpoint.pending_reason,
                    checkpoint.question,
                    json.dumps(checkpoint.options, ensure_ascii=False) if checkpoint.options is not None else None,
                    checkpoint.resume_node,
                    checkpoint.status.value,
                    checkpoint.created_at,
                    checkpoint.updated_at,
                ),
            )

    def get_pending_checkpoint(self, *, thread_id: str, user_id: str) -> PendingCheckpoint | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM hitl_checkpoints
                WHERE thread_id = ? AND user_id = ? AND status = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (thread_id, user_id, HitlCheckpointStatus.PENDING.value),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_checkpoint(row)

    def mark_resolved(self, checkpoint_id: str, *, updated_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE hitl_checkpoints
                SET status = ?, updated_at = ?
                WHERE checkpoint_id = ?
                """,
                (HitlCheckpointStatus.RESOLVED.value, updated_at, checkpoint_id),
            )

    @staticmethod
    def _row_to_checkpoint(row: sqlite3.Row) -> PendingCheckpoint:
        return PendingCheckpoint(
            checkpoint_id=row["checkpoint_id"],
            thread_id=row["thread_id"],
            user_id=row["user_id"],
            original_user_input=row["original_user_input"],
            original_intent=row["original_intent"],
            intent_result=json.loads(row["intent_result_json"]),
            missing_slots=json.loads(row["missing_slots_json"]),
            pending_reason=row["pending_reason"],
            question=row["question"],
            options=json.loads(row["options_json"]) if row["options_json"] else None,
            resume_node=row["resume_node"],
            pending_state=json.loads(row["pending_state_json"]),
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

