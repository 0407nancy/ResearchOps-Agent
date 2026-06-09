from pathlib import Path

from deerflow.researchops.evaluation.metrics import (
    classification_accuracy,
    evidence_coverage,
    report_completeness,
)
from deerflow.researchops.evaluation.runner import run_eval_cases


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
