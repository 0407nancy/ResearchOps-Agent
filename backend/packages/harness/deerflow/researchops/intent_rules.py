from __future__ import annotations

import re
from dataclasses import dataclass

from deerflow.researchops.schemas import ResearchIntent


_KNOWN_PROJECTS = (
    "OpenClaw RL",
    "ResearchOps-Agent",
    "ResearchOps Agent",
    "DeerFlow",
    "LangGraph",
)


@dataclass(frozen=True)
class IntentRuleCandidate:
    intent: ResearchIntent
    score: float
    matched: list[str]


@dataclass(frozen=True)
class SlotExtraction:
    project: str | None
    time_range: str | None
    output_format: str | None
    task_operation: str | None
    evidence: dict[str, str]


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in text.lower() for keyword in keywords)


def extract_slots(text: str) -> SlotExtraction:
    evidence: dict[str, str] = {}
    project = _extract_project(text, evidence)
    time_range = _extract_time_range(text, evidence)
    output_format = _progress_output_format(text, evidence)
    task_operation = _extract_task_operation(text, evidence)
    return SlotExtraction(
        project=project,
        time_range=time_range,
        output_format=output_format,
        task_operation=task_operation,
        evidence=evidence,
    )


def score_intents(text: str) -> list[IntentRuleCandidate]:
    specs = {
        ResearchIntent.PROGRESS_SUMMARY: {
            "strong": ("进展", "总结", "汇报", "日报", "周报", "组会", "summary", "report"),
            "weak": ("整理", "最近", "本周", "今天", "结果"),
        },
        ResearchIntent.EXPERIMENT_REVIEW: {
            "strong": ("失败", "复盘", "日志", "error", "报错", "排查", "实验复盘", "failure"),
            "weak": ("实验", "metric", "loss", "accuracy", "结果"),
        },
        ResearchIntent.PROJECT_PLANNING: {
            "strong": ("规划", "计划", "路线", "优先级", "下一步", "简历", "roadmap"),
            "weak": ("阶段", "方向", "开发", "项目"),
        },
        ResearchIntent.KNOWLEDGE_QA: {
            "strong": ("解释", "是什么", "为什么", "架构", "论文", "技术", "concept", "qa"),
            "weak": ("看看", "了解", "资料", "方法"),
        },
        ResearchIntent.TASK_TRACKING: {
            "strong": ("完成了", "还没做", "todo", "待办", "任务列表", "标记", "卡住", "阻塞", "blocked", "done"),
            "weak": ("任务", "状态", "action"),
        },
    }
    candidates = []
    for intent, keywords in specs.items():
        matched_strong = _matched(text, keywords["strong"])
        matched_weak = _matched(text, keywords["weak"])
        score = len(matched_strong) * 2.0 + len(matched_weak) * 0.75
        if score > 0:
            candidates.append(IntentRuleCandidate(intent=intent, score=score, matched=matched_strong + matched_weak))
    if not candidates:
        candidates.append(IntentRuleCandidate(intent=ResearchIntent.KNOWLEDGE_QA, score=0.5, matched=["low evidence fallback"]))
    present = {candidate.intent for candidate in candidates}
    for intent in ResearchIntent:
        if intent not in present:
            candidates.append(IntentRuleCandidate(intent=intent, score=0.25, matched=["default alternative"]))
    return sorted(candidates, key=lambda item: item.score, reverse=True)


def _matched(text: str, keywords: tuple[str, ...]) -> list[str]:
    return [keyword for keyword in keywords if keyword.lower() in text.lower()]


def _extract_project(text: str, evidence: dict[str, str]) -> str | None:
    for project in _KNOWN_PROJECTS:
        if project.lower() in text.lower():
            normalized = "ResearchOps-Agent" if project == "ResearchOps Agent" else project
            evidence["project"] = normalized
            return normalized

    match = re.search(r"([\w.-]+(?:\s+[\w.-]+){0,2})\s*(?:项目|工程)", text)
    if match:
        candidate = match.group(1).strip(" ，,。")
        if candidate:
            evidence["project"] = candidate
            return candidate
    return None


def _extract_time_range(text: str, evidence: dict[str, str]) -> str | None:
    lowered = text.lower()
    options = (
        ("this_week", ("这周", "本周", "weekly", "week")),
        ("today", ("今天", "今日", "daily", "today")),
        ("next_week", ("下周", "next week")),
        ("recent", ("最近", "近期", "recent")),
        ("since_last_report", ("自上次", "since last")),
    )
    for value, keywords in options:
        for keyword in keywords:
            if keyword.lower() in lowered:
                evidence["time_range"] = keyword
                return value
    return None


def _progress_output_format(text: str, evidence: dict[str, str]) -> str:
    options = (
        ("meeting_prep", ("组会", "meeting")),
        ("weekly_report", ("周报", "weekly")),
        ("daily_report", ("日报", "daily")),
    )
    for value, keywords in options:
        for keyword in keywords:
            if keyword.lower() in text.lower():
                evidence["output_format"] = keyword
                return value
    return "progress_summary"


def _extract_task_operation(text: str, evidence: dict[str, str]) -> str | None:
    options = (
        ("read", ("查看", "列表", "还有哪些", "todo", "待办")),
        ("create", ("创建", "新增", "添加")),
        ("update", ("完成了", "还没做", "卡住", "阻塞", "blocked", "done")),
    )
    for value, keywords in options:
        for keyword in keywords:
            if keyword.lower() in text.lower():
                evidence["task_operation"] = value
                return value
    return None
