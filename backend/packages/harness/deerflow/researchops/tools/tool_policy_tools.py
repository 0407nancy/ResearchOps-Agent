from __future__ import annotations

import json

from langchain.tools import tool

from deerflow.researchops.tool_policy import assess_tool_call


@tool("tool_policy_check", parse_docstring=True)
def tool_policy_check_tool(tool_name: str, args_json: str = "{}") -> str:
    """Assess ResearchOps tool-call risk and whether HITL approval is needed.

    Args:
        tool_name: Tool name that the agent plans to call.
        args_json: JSON object of planned tool arguments.
    """
    decision = assess_tool_call(tool_name=tool_name, args=json.loads(args_json or "{}"))
    return decision.model_dump_json(indent=2)
