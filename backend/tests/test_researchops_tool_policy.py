from deerflow.researchops.schemas import RiskLevel
from deerflow.researchops.tool_policy import assess_tool_call
from deerflow.researchops.tools.tool_policy_tools import tool_policy_check_tool


def test_tool_policy_marks_read_tools_low_risk():
    decision = assess_tool_call(tool_name="memory_search", args={"query": "context"})

    assert decision.risk_level == RiskLevel.LOW
    assert decision.requires_approval is False


def test_tool_policy_requires_approval_for_high_risk_writes():
    decision = assess_tool_call(
        tool_name="memory_writer",
        args={"memory_type": "DecisionMemory", "title": "覆盖项目方向", "overwrite": True},
    )

    assert decision.risk_level == RiskLevel.HIGH
    assert decision.requires_approval is True
    assert decision.reason == "high_risk_memory_write"


def test_tool_policy_tool_returns_json():
    payload = tool_policy_check_tool.invoke(
        {
            "tool_name": "task_writer",
            "args_json": '{"status":"done","title":"实现 memory store"}',
        }
    )

    assert '"risk_level": "medium"' in payload
    assert '"requires_approval": false' in payload
