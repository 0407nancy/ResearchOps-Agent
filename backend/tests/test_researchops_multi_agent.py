import json
from pathlib import Path

import yaml

from deerflow.config.agents_config import AgentConfig
from deerflow.researchops.multi_agent import plan_specialist_agents
from deerflow.researchops.schemas import IntentResult, ResearchIntent
from deerflow.researchops.tools.multi_agent_tools import multi_agent_plan_tool


TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "researchops" / "multi_agent" / "agents"


def test_specialist_agent_templates_parse_as_deerflow_agent_configs():
    expected = {
        "researchops-memory-agent",
        "researchops-evidence-agent",
        "researchops-report-agent",
    }

    parsed = {}
    for agent_dir in TEMPLATE_ROOT.iterdir():
        if not agent_dir.is_dir():
            continue
        config = AgentConfig(**yaml.safe_load((agent_dir / "config.yaml").read_text(encoding="utf-8")))
        soul = (agent_dir / "SOUL.md").read_text(encoding="utf-8")
        parsed[config.name] = config
        assert soul.strip()

    assert set(parsed) == expected
    assert "memory_writer" not in (parsed["researchops-memory-agent"].tool_groups or [])
    assert "memory_writer" not in (parsed["researchops-evidence-agent"].tool_groups or [])
    assert parsed["researchops-report-agent"].skills == ["researchops-progress-summary", "researchops-experiment-review"]


def test_multi_agent_plan_delegates_only_for_complex_formal_outputs():
    intent = IntentResult(
        intent=ResearchIntent.PROGRESS_SUMMARY,
        confidence=0.88,
        project="ResearchOps-Agent",
        time_range="this_week",
        output_format="weekly_report",
    )

    plan = plan_specialist_agents(
        intent_result=intent,
        source_chunk_count=8,
        memory_count=5,
        require_formal_report=True,
        require_evidence_verification=True,
    )

    assert [agent.name for agent in plan.agents] == [
        "researchops-memory-agent",
        "researchops-report-agent",
        "researchops-evidence-agent",
    ]
    assert plan.use_multi_agent is True


def test_multi_agent_plan_keeps_simple_task_tracking_single_agent():
    intent = IntentResult(
        intent=ResearchIntent.TASK_TRACKING,
        confidence=0.9,
        task_operation="update",
        output_format="task_update",
    )

    plan = plan_specialist_agents(
        intent_result=intent,
        source_chunk_count=0,
        memory_count=1,
        require_formal_report=False,
        require_evidence_verification=False,
    )

    assert plan.use_multi_agent is False
    assert plan.agents == []


def test_multi_agent_plan_tool_returns_json():
    payload = multi_agent_plan_tool.invoke(
        {
            "intent_json": json.dumps(
                {
                    "intent": "PROGRESS_SUMMARY",
                    "confidence": 0.88,
                    "project": "ResearchOps-Agent",
                    "time_range": "this_week",
                    "output_format": "meeting_prep",
                }
            ),
            "source_chunk_count": 6,
            "memory_count": 4,
            "require_formal_report": True,
            "require_evidence_verification": True,
        }
    )

    data = json.loads(payload)
    assert data["use_multi_agent"] is True
    assert data["agents"][-1]["name"] == "researchops-evidence-agent"
