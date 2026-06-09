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
            ToolConfig(
                name="note_loader",
                group="researchops",
                use="deerflow.researchops.tools.note_loader:note_loader_tool",
            ),
            ToolConfig(
                name="log_parser",
                group="researchops",
                use="deerflow.researchops.tools.log_parser:log_parser_tool",
            ),
            ToolConfig(
                name="task_reader",
                group="researchops",
                use="deerflow.researchops.tools.task_tools:task_reader_tool",
            ),
            ToolConfig(
                name="task_writer",
                group="researchops",
                use="deerflow.researchops.tools.task_tools:task_writer_tool",
            ),
            ToolConfig(
                name="context_builder",
                group="researchops",
                use="deerflow.researchops.tools.context_builder_tool:context_builder_tool",
            ),
            ToolConfig(
                name="report_writer",
                group="researchops",
                use="deerflow.researchops.tools.report_writer:report_writer_tool",
            ),
            ToolConfig(
                name="eval_runner",
                group="researchops",
                use="deerflow.researchops.tools.eval_runner:eval_runner_tool",
            ),
            ToolConfig(
                name="session_trace_writer",
                group="researchops",
                use="deerflow.researchops.tools.session_trace_tools:session_trace_writer_tool",
            ),
            ToolConfig(
                name="tool_policy_check",
                group="researchops",
                use="deerflow.researchops.tools.tool_policy_tools:tool_policy_check_tool",
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
    assert "note_loader" in names
    assert "log_parser" in names
    assert "task_reader" in names
    assert "task_writer" in names
    assert "context_builder" in names
    assert "report_writer" in names
    assert "eval_runner" in names
    assert "session_trace_writer" in names
    assert "tool_policy_check" in names
    assert "ask_clarification" in names
