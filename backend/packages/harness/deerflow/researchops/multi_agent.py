from __future__ import annotations

from pydantic import BaseModel, Field

from deerflow.researchops.schemas import IntentResult, ResearchIntent


class SpecialistAgentSpec(BaseModel):
    name: str
    role: str
    reason: str


class MultiAgentPlan(BaseModel):
    use_multi_agent: bool
    reason: str
    agents: list[SpecialistAgentSpec] = Field(default_factory=list)


def plan_specialist_agents(
    *,
    intent_result: IntentResult,
    source_chunk_count: int,
    memory_count: int,
    require_formal_report: bool,
    require_evidence_verification: bool,
) -> MultiAgentPlan:
    if intent_result.intent == ResearchIntent.TASK_TRACKING and not require_formal_report:
        return MultiAgentPlan(
            use_multi_agent=False,
            reason="simple_task_tracking_should_stay_single_agent",
        )

    complex_context = source_chunk_count >= 5 or memory_count >= 4
    formal_output = require_formal_report or intent_result.output_format in {"weekly_report", "meeting_prep", "experiment_review"}
    needs_evidence = require_evidence_verification or formal_output

    if not (complex_context or formal_output or needs_evidence):
        return MultiAgentPlan(use_multi_agent=False, reason="single_agent_sufficient")

    agents: list[SpecialistAgentSpec] = []
    if complex_context:
        agents.append(
            SpecialistAgentSpec(
                name="researchops-memory-agent",
                role="memory_retrieval_and_consolidation",
                reason="context contains enough memory/source material to benefit from isolated retrieval review",
            )
        )
    if formal_output:
        agents.append(
            SpecialistAgentSpec(
                name="researchops-report-agent",
                role="report_drafting",
                reason="formal ResearchOps output should be drafted separately from final lead-agent review",
            )
        )
    if needs_evidence:
        agents.append(
            SpecialistAgentSpec(
                name="researchops-evidence-agent",
                role="claim_evidence_verification",
                reason="formal or evidence-grounded output needs independent claim verification",
            )
        )

    return MultiAgentPlan(
        use_multi_agent=bool(agents),
        reason="specialist_agents_add_value_for_complex_or_formal_researchops_task",
        agents=agents,
    )
