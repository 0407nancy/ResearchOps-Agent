from __future__ import annotations

import re

from deerflow.researchops.schemas import IntentResult, ResearchIntent, RiskLevel


_KNOWN_PROJECTS = (
    "OpenClaw RL",
    "ResearchOps-Agent",
    "ResearchOps Agent",
    "DeerFlow",
    "LangGraph",
)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in text.lower() for keyword in keywords)


def _extract_project(text: str) -> str | None:
    for project in _KNOWN_PROJECTS:
        if project.lower() in text.lower():
            return "ResearchOps-Agent" if project == "ResearchOps Agent" else project

    match = re.search(r"([\w.-]+(?:\s+[\w.-]+){0,2})\s*(?:项目|工程)", text)
    if match:
        candidate = match.group(1).strip(" ，,。")
        return candidate or None
    return None


def _extract_time_range(text: str) -> str | None:
    lowered = text.lower()
    if _contains_any(lowered, ("这周", "本周", "weekly", "week")):
        return "this_week"
    if _contains_any(lowered, ("今天", "今日", "daily", "today")):
        return "today"
    if _contains_any(lowered, ("下周", "next week")):
        return "next_week"
    if _contains_any(lowered, ("最近", "近期", "recent")):
        return "recent"
    if _contains_any(lowered, ("自上次", "since last")):
        return "since_last_report"
    return None


def _progress_output_format(text: str) -> str:
    if _contains_any(text, ("组会", "meeting")):
        return "meeting_prep"
    if _contains_any(text, ("周报", "weekly")):
        return "weekly_report"
    if _contains_any(text, ("日报", "daily")):
        return "daily_report"
    return "progress_summary"


def _is_progress_summary_request(text: str) -> bool:
    return _contains_any(text, ("进展", "总结", "汇报", "日报", "周报", "组会", "summary", "report"))


def _is_task_tracking_request(text: str) -> bool:
    return _contains_any(text, ("完成了", "还没做", "todo", "待办", "任务列表", "标记", "卡住", "阻塞", "blocked", "done"))


def _is_project_planning_request(text: str) -> bool:
    return _contains_any(text, ("规划", "计划", "路线", "优先级", "下一步", "简历", "roadmap"))


def _is_experiment_review_request(text: str) -> bool:
    return _contains_any(text, ("失败", "复盘", "日志", "error", "报错", "排查", "实验复盘", "failure"))


def _extract_task_operation(text: str) -> str | None:
    if _contains_any(text, ("查看", "列表", "还有哪些", "todo", "待办")):
        return "read"
    if _contains_any(text, ("创建", "新增", "添加")):
        return "create"
    if _contains_any(text, ("完成了", "还没做", "卡住", "阻塞", "blocked", "done")):
        return "update"
    return None


def _missing_slots(intent: ResearchIntent, project: str | None, time_range: str | None, task_operation: str | None) -> list[str]:
    missing: list[str] = []
    if intent in {
        ResearchIntent.PROGRESS_SUMMARY,
        ResearchIntent.EXPERIMENT_REVIEW,
        ResearchIntent.PROJECT_PLANNING,
    } and project is None:
        missing.append("project")
    if intent == ResearchIntent.PROGRESS_SUMMARY and time_range is None:
        missing.append("time_range")
    if intent == ResearchIntent.TASK_TRACKING and task_operation is None:
        missing.append("task_operation")
    return missing


def classify_intent(user_input: str) -> IntentResult:
    """Classify a ResearchOps request into one of the five MVP intents."""
    text = user_input.strip()
    project = _extract_project(text)
    time_range = _extract_time_range(text)

    if _is_task_tracking_request(text):
        intent = ResearchIntent.TASK_TRACKING
        output_format = "task_update"
        task_operation = _extract_task_operation(text)
        confidence = 0.86
        risk = RiskLevel.MEDIUM
    elif _is_experiment_review_request(text):
        intent = ResearchIntent.EXPERIMENT_REVIEW
        output_format = "experiment_review"
        task_operation = None
        confidence = 0.84
        risk = RiskLevel.LOW
    elif _is_project_planning_request(text):
        intent = ResearchIntent.PROJECT_PLANNING
        output_format = "project_plan"
        task_operation = None
        confidence = 0.82
        risk = RiskLevel.LOW
    elif _is_progress_summary_request(text):
        intent = ResearchIntent.PROGRESS_SUMMARY
        output_format = _progress_output_format(text)
        task_operation = None
        confidence = 0.86
        risk = RiskLevel.LOW
    elif _contains_any(text, ("解释", "是什么", "为什么", "架构", "论文", "技术", "concept", "qa")):
        intent = ResearchIntent.KNOWLEDGE_QA
        output_format = "answer"
        task_operation = None
        confidence = 0.78
        risk = RiskLevel.LOW
    else:
        intent = ResearchIntent.PROGRESS_SUMMARY
        output_format = _progress_output_format(text)
        task_operation = None
        confidence = 0.86
        risk = RiskLevel.LOW

    missing = _missing_slots(intent, project, time_range, task_operation)
    if intent == ResearchIntent.KNOWLEDGE_QA:
        missing = []

    return IntentResult(
        intent=intent,
        confidence=confidence,
        project=project,
        time_range=time_range,
        output_format=output_format,
        task_operation=task_operation,
        missing_slots=missing,
        risk_level=risk,
    )
