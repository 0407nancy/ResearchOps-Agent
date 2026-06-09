from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def classification_accuracy(rows: Sequence[dict[str, Any]], *, key: str = "intent") -> float:
    if not rows:
        return 0.0
    correct = sum(1 for row in rows if row.get("prediction", {}).get(key) == row.get("gold", {}).get(key))
    return correct / len(rows)


def clarification_accuracy(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    correct = 0
    for row in rows:
        gold = row.get("gold", {})
        pred = row.get("prediction", {})
        if pred.get("need_user_input") != gold.get("need_user_input"):
            continue
        gold_missing = set(gold.get("missing_slots", []))
        pred_missing = set(pred.get("missing_slots", []))
        if gold_missing.issubset(pred_missing):
            correct += 1
    return correct / len(rows)


def task_update_accuracy(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    scores = []
    for row in rows:
        gold_updates = {(item["title"], item["status"]) for item in row.get("gold", {}).get("task_updates", [])}
        pred_updates = {(item["title"], item["status"]) for item in row.get("prediction", {}).get("task_updates", [])}
        if not gold_updates:
            scores.append(1.0)
        else:
            scores.append(len(gold_updates & pred_updates) / len(gold_updates))
    return sum(scores) / len(scores)


def report_completeness(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    scores = []
    for row in rows:
        required = set(row.get("gold", {}).get("required_sections", []))
        sections = set(row.get("prediction", {}).get("sections", []))
        scores.append(1.0 if not required else len(required & sections) / len(required))
    return sum(scores) / len(scores)


def evidence_coverage(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    correct = 0
    for row in rows:
        min_evidence = row.get("gold", {}).get("min_evidence", 0)
        evidence_count = row.get("prediction", {}).get("evidence_count", 0)
        if evidence_count >= min_evidence:
            correct += 1
    return correct / len(rows)


def memory_recall_at_k(rows: Sequence[dict[str, Any]], *, k: int = 5) -> float:
    if not rows:
        return 0.0
    scores = []
    for row in rows:
        expected_ids = set(row.get("gold", {}).get("memory_ids", []))
        retrieved_ids = row.get("prediction", {}).get("memory_ids", [])[:k]
        if not expected_ids:
            scores.append(1.0)
        else:
            scores.append(len(expected_ids & set(retrieved_ids)) / len(expected_ids))
    return sum(scores) / len(scores)
