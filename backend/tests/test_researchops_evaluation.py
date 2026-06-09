from pathlib import Path

from deerflow.researchops.evaluation.metrics import (
    classification_accuracy,
    claim_support_precision,
    context_precision,
    context_recall,
    evidence_coverage,
    multi_turn_state_accuracy,
    report_completeness,
    slot_f1,
)
from deerflow.researchops.evaluation.runner import run_eval_cases, run_eval_suite


def test_metrics_compute_intent_report_and_evidence_scores():
    intent_rows = [
        {"gold": {"intent": "PROGRESS_SUMMARY"}, "prediction": {"intent": "PROGRESS_SUMMARY"}},
        {"gold": {"intent": "TASK_TRACKING"}, "prediction": {"intent": "PROJECT_PLANNING"}},
    ]
    report_rows = [
        {
            "gold": {"required_sections": ["进展", "问题", "下一步"]},
            "prediction": {"sections": ["进展", "下一步"]},
        }
    ]
    evidence_rows = [
        {"gold": {"min_evidence": 2}, "prediction": {"evidence_count": 3}},
        {"gold": {"min_evidence": 2}, "prediction": {"evidence_count": 1}},
    ]

    assert classification_accuracy(intent_rows) == 0.5
    assert report_completeness(report_rows) == 2 / 3
    assert evidence_coverage(evidence_rows) == 0.5


def test_eval_2_metrics_compute_slots_context_claims_and_sessions():
    slot_rows = [
        {
            "gold": {"project": "OpenClaw RL", "time_range": "this_week", "output_format": "weekly_report"},
            "prediction": {"project": "OpenClaw RL", "time_range": "this_week", "output_format": "meeting_prep"},
        }
    ]
    context_rows = [
        {
            "gold": {"relevant_refs": ["note:a#L1-L2", "mem:project"]},
            "prediction": {"retrieved_refs": ["note:a#L1-L2", "note:b#L1-L2"]},
        }
    ]
    claim_rows = [
        {
            "gold": {"claims": [{"text": "完成 intent", "support_status": "supported"}, {"text": "完成 eval", "support_status": "unsupported"}]},
            "prediction": {"claims": [{"text": "完成 intent", "support_status": "supported"}, {"text": "完成 eval", "support_status": "supported"}]},
        }
    ]
    session_rows = [
        {
            "gold": {"final_tasks": [{"title": "intent 分类", "status": "done"}]},
            "prediction": {"final_tasks": [{"title": "intent 分类", "status": "done"}]},
        }
    ]

    assert slot_f1(slot_rows) == 2 / 3
    assert context_precision(context_rows) == 0.5
    assert context_recall(context_rows) == 0.5
    assert claim_support_precision(claim_rows) == 0.5
    assert multi_turn_state_accuracy(session_rows) == 1.0


def test_run_eval_cases_covers_intent_clarification_task_and_report(tmp_path: Path):
    cases_path = tmp_path / "eval_queries.jsonl"
    cases_path.write_text(
        "\n".join(
            [
                '{"id":"intent_001","input":"根据这周记录生成组会汇报","task":"intent","gold":{"intent":"PROGRESS_SUMMARY","output_format":"meeting_prep"}}',
                '{"id":"clarify_001","input":"帮我整理 OpenClaw RL 的进展","task":"clarification","gold":{"intent":"PROGRESS_SUMMARY","need_user_input":true,"missing_slots":["time_range"]}}',
                '{"id":"task_001","input":"我今天完成了 intent 分类，但 memory store 还没做","task":"task_tracking","gold":{"intent":"TASK_TRACKING","task_updates":[{"title":"intent 分类","status":"done"},{"title":"memory store","status":"todo"}]}}',
                '{"id":"report_001","input":"把最近实验结果整理成周报","task":"report","gold":{"intent":"PROGRESS_SUMMARY","required_sections":["进展","问题与阻塞","下一步"],"min_evidence":1}}',
            ]
        ),
        encoding="utf-8",
    )

    result = run_eval_cases(cases_path=cases_path, work_dir=tmp_path)

    assert result.total == 4
    assert result.metrics["intent_accuracy"] == 1.0
    assert result.metrics["clarification_accuracy"] == 1.0
    assert result.metrics["task_update_accuracy"] == 1.0
    assert result.metrics["report_completeness"] == 1.0
    assert result.metrics["evidence_coverage"] == 1.0


def test_run_eval_suite_loads_multiple_eval_files_and_reports_new_metrics(tmp_path: Path):
    (tmp_path / "eval_intent.jsonl").write_text(
        '{"id":"intent_001","input":"把 OpenClaw RL 最近实验结果整理成周报","task":"intent","gold":{"intent":"PROGRESS_SUMMARY","project":"OpenClaw RL","time_range":"recent","output_format":"weekly_report"}}\n',
        encoding="utf-8",
    )
    (tmp_path / "eval_context.jsonl").write_text(
        '{"id":"context_001","input":"ResearchOps-Agent eval seed","task":"context","gold":{"project_id":"researchops_agent","relevant_refs":["eval:seed#L1-L3"],"memory_type":"ProjectMemory"}}\n',
        encoding="utf-8",
    )
    (tmp_path / "eval_evidence.jsonl").write_text(
        '{"id":"evidence_001","input":"完成 intent 分类 [eval:seed#L1-L3]","task":"evidence","gold":{"claims":[{"text":"完成 intent 分类","support_status":"supported"}]}}\n',
        encoding="utf-8",
    )
    (tmp_path / "eval_sessions.jsonl").write_text(
        '{"id":"session_001","task":"session","turns":[{"user":"我今天完成了 intent 分类，但 memory store 还没做"}],"gold":{"final_tasks":[{"title":"intent 分类","status":"done"},{"title":"memory store","status":"todo"}]}}\n',
        encoding="utf-8",
    )

    result = run_eval_suite(suite_dir=tmp_path, work_dir=tmp_path / "work")

    assert result.total == 4
    assert "slot_f1" in result.metrics
    assert "context_precision" in result.metrics
    assert "context_recall" in result.metrics
    assert "claim_support_precision" in result.metrics
    assert "multi_turn_state_accuracy" in result.metrics
