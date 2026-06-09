from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ResearchIntent(StrEnum):
    PROGRESS_SUMMARY = "PROGRESS_SUMMARY"
    EXPERIMENT_REVIEW = "EXPERIMENT_REVIEW"
    PROJECT_PLANNING = "PROJECT_PLANNING"
    KNOWLEDGE_QA = "KNOWLEDGE_QA"
    TASK_TRACKING = "TASK_TRACKING"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MemoryType(StrEnum):
    PROJECT = "ProjectMemory"
    EXPERIMENT = "ExperimentMemory"
    PAPER = "PaperMemory"
    DECISION = "DecisionMemory"
    PREFERENCE = "PreferenceMemory"
    RESOURCE = "ResourceMemory"
    TASK = "TaskMemory"


class IntentResult(BaseModel):
    intent: ResearchIntent
    confidence: float = Field(ge=0.0, le=1.0)
    project: str | None = None
    time_range: str | None = None
    output_format: str | None = None
    task_operation: str | None = None
    missing_slots: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    alternatives: list["IntentCandidate"] = Field(default_factory=list)
    slot_evidence: dict[str, str] = Field(default_factory=dict)
    classification_rationale: str = ""


class IntentCandidate(BaseModel):
    intent: ResearchIntent
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class HitlDecision(BaseModel):
    need_user_input: bool
    reason: str | None = None
    question: str | None = None
    options: list[str] | None = None
    original_intent: ResearchIntent | None = None
    checkpoint_id: str | None = None
    pending_state: dict = Field(default_factory=dict)
    resume_node: str | None = None


class ResumeResult(BaseModel):
    has_pending: bool
    resolved: bool
    checkpoint_id: str | None = None
    original_intent: ResearchIntent | None = None
    filled_slots: dict = Field(default_factory=dict)
    resume_state: dict = Field(default_factory=dict)
    reason: str | None = None


class HitlCheckpointStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class PendingCheckpoint(BaseModel):
    checkpoint_id: str
    thread_id: str
    user_id: str
    original_user_input: str
    original_intent: ResearchIntent
    intent_result: dict
    missing_slots: list[str]
    pending_reason: str
    question: str
    options: list[str] | None = None
    resume_node: str
    pending_state: dict
    status: HitlCheckpointStatus = HitlCheckpointStatus.PENDING
    created_at: str
    updated_at: str


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    DROPPED = "dropped"


class ResearchMemoryRecord(BaseModel):
    id: str
    type: MemoryType
    project_id: str | None = None
    title: str
    summary: str = ""
    content: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    importance: int = Field(default=3, ge=1, le=5)
    status: str = "active"
    created_at: str
    updated_at: str
    supersedes_id: str | None = None


class SourceChunk(BaseModel):
    source_ref: str
    text: str
    metadata: dict = Field(default_factory=dict)


class EvidenceRef(BaseModel):
    source_ref: str
    kind: Literal["memory", "source", "task", "log"] = "source"
    title: str | None = None
    snippet: str | None = None


class ContextPacket(BaseModel):
    intent: ResearchIntent
    project: str | None = None
    time_range: str | None = None
    memories: list[ResearchMemoryRecord] = Field(default_factory=list)
    source_chunks: list[SourceChunk] = Field(default_factory=list)
    tasks: list[ResearchMemoryRecord] = Field(default_factory=list)
    evidence_table: list[EvidenceRef] = Field(default_factory=list)


class Claim(BaseModel):
    text: str
    evidence_refs: list[str] = Field(default_factory=list)


class VerifiedClaim(Claim):
    support_status: Literal["supported", "weakly_supported", "unsupported"]
    matched_evidence_refs: list[str] = Field(default_factory=list)


class ToolPolicyDecision(BaseModel):
    tool_name: str
    risk_level: RiskLevel
    requires_approval: bool
    reason: str
    allowed_without_approval: bool
