import json

from deerflow.researchops.intent import classify_intent
from deerflow.researchops.schemas import ResearchIntent, RiskLevel
from deerflow.researchops.tools.intent_tool import classify_research_intent_tool


def test_classifies_progress_summary_with_missing_time_range():
    result = classify_intent("帮我整理 OpenClaw RL 的进展")

    assert result.intent == ResearchIntent.PROGRESS_SUMMARY
    assert result.project == "OpenClaw RL"
    assert result.time_range is None
    assert result.output_format == "progress_summary"
    assert result.missing_slots == ["time_range"]
    assert result.risk_level == RiskLevel.LOW


def test_classifies_experiment_review_from_failure_language():
    result = classify_intent("GRPO 实验失败了，帮我分析日志和下一步排查建议")

    assert result.intent == ResearchIntent.EXPERIMENT_REVIEW
    assert result.project is None
    assert result.output_format == "experiment_review"
    assert "project" in result.missing_slots


def test_classifies_project_planning():
    result = classify_intent("根据 ResearchOps-Agent 当前进展规划下周开发路线")

    assert result.intent == ResearchIntent.PROJECT_PLANNING
    assert result.project == "ResearchOps-Agent"
    assert result.time_range == "next_week"
    assert result.output_format == "project_plan"
    assert result.missing_slots == []


def test_classifies_knowledge_qa():
    result = classify_intent("解释一下 LangGraph 的 checkpoint 在 agent 里有什么用")

    assert result.intent == ResearchIntent.KNOWLEDGE_QA
    assert result.output_format == "answer"
    assert result.missing_slots == []


def test_classifies_task_tracking_update():
    result = classify_intent("我今天完成了 intent 分类，但 memory store 还没做")

    assert result.intent == ResearchIntent.TASK_TRACKING
    assert result.task_operation == "update"
    assert result.output_format == "task_update"
    assert result.missing_slots == []
    assert result.risk_level == RiskLevel.MEDIUM


def test_intent_tool_returns_json():
    payload = classify_research_intent_tool.invoke({"user_input": "根据这周记录生成组会汇报"})
    data = json.loads(payload)

    assert data["intent"] == "PROGRESS_SUMMARY"
    assert data["time_range"] == "this_week"
    assert data["output_format"] == "meeting_prep"
