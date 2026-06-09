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


def slot_f1(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    scores = []
    slot_keys = ("project", "time_range", "output_format", "task_operation")
    for row in rows:
        gold = row.get("gold", {})
        pred = row.get("prediction", {})
        gold_pairs = {(key, gold[key]) for key in slot_keys if gold.get(key) is not None}
        pred_pairs = {(key, pred[key]) for key in slot_keys if gold.get(key) is not None and pred.get(key) is not None}
        if not gold_pairs and not pred_pairs:
            scores.append(1.0)
            continue
        if not gold_pairs or not pred_pairs:
            scores.append(0.0)
            continue
        true_positive = len(gold_pairs & pred_pairs)
        precision = true_positive / len(pred_pairs)
        recall = true_positive / len(gold_pairs)
        scores.append(0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall))
    return sum(scores) / len(scores)


def context_precision(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    scores = []
    for row in rows:
        relevant = set(row.get("gold", {}).get("relevant_refs", []))
        retrieved = row.get("prediction", {}).get("retrieved_refs", [])
        if not retrieved:
            scores.append(0.0 if relevant else 1.0)
        else:
            scores.append(len(relevant & set(retrieved)) / len(retrieved))
    return sum(scores) / len(scores)


def context_recall(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    scores = []
    for row in rows:
        relevant = set(row.get("gold", {}).get("relevant_refs", []))
        retrieved = set(row.get("prediction", {}).get("retrieved_refs", []))
        scores.append(1.0 if not relevant else len(relevant & retrieved) / len(relevant))
    return sum(scores) / len(scores)


def claim_support_precision(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    scores = []
    for row in rows:
        gold_claims = row.get("gold", {}).get("claims", [])
        pred_claims = row.get("prediction", {}).get("claims", [])
        if not gold_claims:
            scores.append(1.0)
            continue
        correct = 0
        for gold, pred in zip(gold_claims, pred_claims, strict=False):
            if gold.get("support_status") == pred.get("support_status"):
                correct += 1
        scores.append(correct / len(gold_claims))
    return sum(scores) / len(scores)


def unsupported_claim_rate(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    total = 0
    unsupported = 0
    for row in rows:
        for claim in row.get("prediction", {}).get("claims", []):
            total += 1
            if claim.get("support_status") == "unsupported":
                unsupported += 1
    return 0.0 if total == 0 else unsupported / total


def multi_turn_state_accuracy(rows: Sequence[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    scores = []
    for row in rows:
        gold_tasks = {(item["title"], item["status"]) for item in row.get("gold", {}).get("final_tasks", [])}
        pred_tasks = {(item["title"], item["status"]) for item in row.get("prediction", {}).get("final_tasks", [])}
        scores.append(1.0 if not gold_tasks else len(gold_tasks & pred_tasks) / len(gold_tasks))
    return sum(scores) / len(scores)
