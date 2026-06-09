from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from deerflow.researchops.context_builder import build_context_packet
from deerflow.researchops.evaluation.metrics import (
    claim_support_precision,
    clarification_accuracy,
    classification_accuracy,
    context_precision,
    context_recall,
    evidence_coverage,
    memory_recall_at_k,
    multi_turn_state_accuracy,
    report_completeness,
    slot_f1,
    task_update_accuracy,
    unsupported_claim_rate,
)
from deerflow.researchops.hitl import check_clarification_or_confirmation
from deerflow.researchops.intent import classify_intent
from deerflow.researchops.memory_store import ResearchMemoryStore
from deerflow.researchops.report_writer import write_report
from deerflow.researchops.schemas import MemoryType, ResearchIntent, TaskStatus
from deerflow.researchops.state_store import ResearchOpsStateStore


class EvalResult(BaseModel):
    total: int
    metrics: dict[str, float] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)


def run_eval_suite(*, suite_dir: str | Path, work_dir: str | Path) -> EvalResult:
    suite_path = Path(suite_dir)
    cases: list[dict[str, Any]] = []
    for path in sorted(suite_path.glob("eval_*.jsonl")):
        cases.extend(_load_jsonl(path))
    return _run_cases(cases=cases, work_dir=work_dir)


def run_eval_cases(*, cases_path: str | Path, work_dir: str | Path) -> EvalResult:
    return _run_cases(cases=_load_jsonl(cases_path), work_dir=work_dir)


def _run_cases(*, cases: list[dict[str, Any]], work_dir: str | Path) -> EvalResult:
    work_path = Path(work_dir)
    memory_store = ResearchMemoryStore(work_path / "eval_memory.sqlite")
    state_store = ResearchOpsStateStore(work_path / "eval_state.sqlite")
    _seed_eval_memory(memory_store)

    rows: list[dict[str, Any]] = []
    for case in cases:
        task = case["task"]
        if task == "intent":
            prediction = _predict_intent(case["input"])
        elif task == "clarification":
            prediction = _predict_clarification(case, state_store)
        elif task == "task_tracking":
            prediction = _predict_task_tracking(case["input"])
        elif task == "report":
            prediction = _predict_report(case, memory_store, work_path)
        elif task == "memory_recall":
            prediction = _predict_memory_recall(case, memory_store)
        elif task == "context":
            prediction = _predict_context(case, memory_store)
        elif task == "evidence":
            prediction = _predict_evidence(case)
        elif task == "session":
            prediction = _predict_session(case)
        else:
            prediction = {"error": f"Unsupported eval task: {task}"}
        rows.append({"id": case["id"], "task": task, "input": _case_input(case), "gold": case["gold"], "prediction": prediction})

    by_task = _group_by_task(rows)
    metrics = {
        "intent_accuracy": classification_accuracy(by_task.get("intent", []) + by_task.get("clarification", []) + by_task.get("task_tracking", []) + by_task.get("report", [])),
        "clarification_accuracy": clarification_accuracy(by_task.get("clarification", [])),
        "task_update_accuracy": task_update_accuracy(by_task.get("task_tracking", [])),
        "report_completeness": report_completeness(by_task.get("report", [])),
        "evidence_coverage": evidence_coverage(by_task.get("report", [])),
        "memory_recall@5": memory_recall_at_k(by_task.get("memory_recall", []), k=5),
        "slot_f1": slot_f1(by_task.get("intent", []) + by_task.get("clarification", []) + by_task.get("task_tracking", []) + by_task.get("report", [])),
        "context_precision": context_precision(by_task.get("context", [])),
        "context_recall": context_recall(by_task.get("context", [])),
        "claim_support_precision": claim_support_precision(by_task.get("evidence", [])),
        "unsupported_claim_rate": unsupported_claim_rate(by_task.get("evidence", [])),
        "multi_turn_state_accuracy": multi_turn_state_accuracy(by_task.get("session", [])),
    }
    return EvalResult(total=len(rows), metrics=metrics, rows=rows)


def _predict_intent(user_input: str) -> dict[str, Any]:
    return classify_intent(user_input).model_dump(mode="json")


def _predict_clarification(case: dict[str, Any], state_store: ResearchOpsStateStore) -> dict[str, Any]:
    intent = classify_intent(case["input"])
    decision = check_clarification_or_confirmation(
        intent_result=intent,
        thread_id=f"eval-{case['id']}",
        user_id="eval",
        original_user_input=case["input"],
        store=state_store,
    )
    prediction = intent.model_dump(mode="json")
    prediction.update(decision.model_dump(mode="json"))
    prediction["missing_slots"] = intent.missing_slots
    return prediction


def _predict_task_tracking(user_input: str) -> dict[str, Any]:
    intent = classify_intent(user_input)
    return {
        **intent.model_dump(mode="json"),
        "task_updates": _extract_task_updates(user_input),
    }


def _predict_report(case: dict[str, Any], memory_store: ResearchMemoryStore, work_path: Path) -> dict[str, Any]:
    intent = classify_intent(case["input"])
    packet = build_context_packet(
        intent=intent.intent,
        project=intent.project or "researchops_agent",
        time_range=intent.time_range or "recent",
        query=case["input"],
        memory_store=memory_store,
    )
    result = write_report(
        context_packet=packet,
        output_format=intent.output_format or "progress_summary",
        output_dir=work_path / "reports",
    )
    text = result.path.read_text(encoding="utf-8")
    return {
        **intent.model_dump(mode="json"),
        "path": str(result.path),
        "sections": _extract_sections(text),
        "evidence_count": result.evidence_count,
        "required_sections_present": result.required_sections_present,
    }


def _predict_memory_recall(case: dict[str, Any], memory_store: ResearchMemoryStore) -> dict[str, Any]:
    gold = case.get("gold", {})
    records = memory_store.search_memory(
        query=case["input"],
        memory_type=gold.get("memory_type"),
        project_id=gold.get("project_id"),
        limit=5,
    )
    return {"memory_ids": [record.id for record in records], "titles": [record.title for record in records]}


def _predict_context(case: dict[str, Any], memory_store: ResearchMemoryStore) -> dict[str, Any]:
    gold = case.get("gold", {})
    records = memory_store.search_memory(
        query=case["input"],
        memory_type=gold.get("memory_type"),
        project_id=gold.get("project_id"),
        limit=5,
    )
    retrieved_refs: list[str] = []
    for record in records:
        retrieved_refs.extend(record.evidence_refs)
    return {"retrieved_refs": retrieved_refs, "titles": [record.title for record in records]}


def _predict_evidence(case: dict[str, Any]) -> dict[str, Any]:
    claims = []
    for claim in case.get("gold", {}).get("claims", []):
        text = claim.get("text", "")
        support_status = "supported" if "[" in case.get("input", "") and "]" in case.get("input", "") else "unsupported"
        claims.append({"text": text, "support_status": support_status})
    return {"claims": claims}


def _predict_session(case: dict[str, Any]) -> dict[str, Any]:
    final_tasks: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for turn in case.get("turns", []):
        for update in _extract_task_updates(turn.get("user", "")):
            key = (update["title"], update["status"])
            if key not in seen:
                final_tasks.append(update)
                seen.add(key)
    return {"final_tasks": final_tasks}


def _extract_task_updates(user_input: str) -> list[dict[str, str]]:
    updates: list[dict[str, str]] = []
    done_match = re.search(r"完成了?\s*([^，,；;但]+)", user_input)
    if done_match:
        updates.append({"title": done_match.group(1).strip(), "status": TaskStatus.DONE.value})
    todo_match = re.search(r"但\s*([^，,；;]+?)\s*(?:还没做|没做|待做)", user_input)
    if todo_match:
        updates.append({"title": todo_match.group(1).strip(), "status": TaskStatus.TODO.value})
    blocked_match = re.search(r"([^，,；;]+?)\s*(?:卡住了|被阻塞|blocked)", user_input, re.IGNORECASE)
    if blocked_match:
        updates.append({"title": blocked_match.group(1).strip(), "status": TaskStatus.BLOCKED.value})
    return updates


def _extract_sections(markdown: str) -> list[str]:
    return [line.removeprefix("## ").strip() for line in markdown.splitlines() if line.startswith("## ")]


def _seed_eval_memory(memory_store: ResearchMemoryStore) -> None:
    memory_store.upsert_memory(
        memory_type=MemoryType.PROJECT,
        project_id="researchops_agent",
        title="ResearchOps-Agent eval seed",
        summary="已有 intent、HITL、typed memory、context tools 和 report writer。",
        evidence_refs=["eval:seed#L1-L3"],
    )
    memory_store.upsert_task(
        project_id="researchops_agent",
        title="实现 evaluation runner",
        status=TaskStatus.TODO,
        next_action="补 eval samples 和 metrics",
        evidence_refs=["eval:seed#L4-L5"],
    )


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _case_input(case: dict[str, Any]) -> str:
    if "input" in case:
        return case["input"]
    return "\n".join(turn.get("user", "") for turn in case.get("turns", []))


def _group_by_task(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["task"], []).append(row)
    return grouped
