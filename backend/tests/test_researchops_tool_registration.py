from deerflow.config.app_config import AppConfig
from deerflow.config.sandbox_config import SandboxConfig
from deerflow.config.tool_config import ToolConfig, ToolGroupConfig
from deerflow.tools import get_available_tools


def test_researchops_tools_load_through_deerflow_registry():
    app_config = AppConfig(
        sandbox=SandboxConfig(use="test"),
        tool_groups=[ToolGroupConfig(name="researchops")],
        tools=[
            ToolConfig(
                name="classify_research_intent",
                group="researchops",
                use="deerflow.researchops.tools.intent_tool:classify_research_intent_tool",
            ),
            ToolConfig(
                name="researchops_check_hitl",
                group="researchops",
                use="deerflow.researchops.tools.hitl_tools:researchops_check_hitl_tool",
            ),
            ToolConfig(
                name="researchops_resume_pending",
                group="researchops",
                use="deerflow.researchops.tools.hitl_tools:researchops_resume_pending_tool",
            ),
            ToolConfig(
                name="memory_search",
                group="researchops",
                use="deerflow.researchops.tools.memory_tools:memory_search_tool",
            ),
            ToolConfig(
                name="memory_writer",
                group="researchops",
                use="deerflow.researchops.tools.memory_tools:memory_writer_tool",
            ),
        ],
    )

    tools = get_available_tools(groups=["researchops"], include_mcp=False, app_config=app_config)
    names = {tool.name for tool in tools}

    assert "classify_research_intent" in names
    assert "researchops_check_hitl" in names
    assert "researchops_resume_pending" in names
    assert "memory_search" in names
    assert "memory_writer" in names
    assert "ask_clarification" in names
