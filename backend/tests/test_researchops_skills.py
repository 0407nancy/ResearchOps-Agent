from pathlib import Path

from deerflow.skills.parser import parse_skill_file
from deerflow.skills.types import SkillCategory


def test_researchops_skills_parse_with_allowed_tools():
    root = Path(__file__).resolve().parents[2] / "skills" / "public" / "researchops"
    expected = {
        "progress_summary": "researchops-progress-summary",
        "experiment_review": "researchops-experiment-review",
        "project_planning": "researchops-project-planning",
        "knowledge_qa": "researchops-knowledge-qa",
        "task_tracking": "researchops-task-tracking",
    }

    for directory, skill_name in expected.items():
        skill = parse_skill_file(root / directory / "SKILL.md", SkillCategory.PUBLIC, Path(f"researchops/{directory}"))
        assert skill is not None
        assert skill.name == skill_name
        assert skill.allowed_tools is not None
        assert "classify_research_intent" in skill.allowed_tools
        assert "researchops_check_hitl" in skill.allowed_tools
        assert "researchops_resume_pending" in skill.allowed_tools
        assert "ask_clarification" in skill.allowed_tools
