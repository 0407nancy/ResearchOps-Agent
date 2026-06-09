from __future__ import annotations

from typing import Any

from deerflow.researchops.schemas import RiskLevel, ToolPolicyDecision


LOW_RISK_TOOLS = {
    "classify_research_intent",
    "researchops_resume_pending",
    "memory_search",
    "note_loader",
    "log_parser",
    "task_reader",
    "context_builder",
    "eval_runner",
}

MEDIUM_RISK_TOOLS = {
    "report_writer",
    "task_writer",
    "memory_writer",
    "session_trace_writer",
}


def assess_tool_call(*, tool_name: str, args: dict[str, Any] | None = None) -> ToolPolicyDecision:
    args = args or {}
    if tool_name in LOW_RISK_TOOLS:
        return _decision(tool_name, RiskLevel.LOW, False, "read_or_analysis_tool")

    if tool_name == "memory_writer":
        memory_type = str(args.get("memory_type", ""))
        if args.get("overwrite") or memory_type in {"DecisionMemory", "PreferenceMemory"}:
            return _decision(tool_name, RiskLevel.HIGH, True, "high_risk_memory_write")
        return _decision(tool_name, RiskLevel.MEDIUM, False, "typed_memory_write")

    if tool_name == "task_writer":
        status = str(args.get("status", ""))
        if status in {"dropped"}:
            return _decision(tool_name, RiskLevel.HIGH, True, "destructive_task_update")
        return _decision(tool_name, RiskLevel.MEDIUM, False, "task_status_update")

    if tool_name in MEDIUM_RISK_TOOLS:
        return _decision(tool_name, RiskLevel.MEDIUM, False, "write_or_trace_tool")

    return _decision(tool_name, RiskLevel.HIGH, True, "unknown_tool")


def _decision(tool_name: str, risk_level: RiskLevel, requires_approval: bool, reason: str) -> ToolPolicyDecision:
    return ToolPolicyDecision(
        tool_name=tool_name,
        risk_level=risk_level,
        requires_approval=requires_approval,
        reason=reason,
        allowed_without_approval=not requires_approval,
    )
