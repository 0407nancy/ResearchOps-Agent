from __future__ import annotations

from langchain.tools import tool

from deerflow.researchops.multi_agent import plan_specialist_agents
from deerflow.researchops.schemas import IntentResult


@tool("multi_agent_plan", parse_docstring=True)
def multi_agent_plan_tool(
    intent_json: str,
    source_chunk_count: int = 0,
    memory_count: int = 0,
    require_formal_report: bool = False,
    require_evidence_verification: bool = False,
) -> str:
    """Decide whether ResearchOps should delegate to specialist agents.

    Args:
        intent_json: JSON IntentResult from classify_research_intent.
        source_chunk_count: Number of retrieved source chunks.
        memory_count: Number of retrieved memory records.
        require_formal_report: Whether the user asked for a formal report.
        require_evidence_verification: Whether claim-level evidence verification is required.
    """
    plan = plan_specialist_agents(
        intent_result=IntentResult.model_validate_json(intent_json),
        source_chunk_count=source_chunk_count,
        memory_count=memory_count,
        require_formal_report=require_formal_report,
        require_evidence_verification=require_evidence_verification,
    )
    return plan.model_dump_json(indent=2)
