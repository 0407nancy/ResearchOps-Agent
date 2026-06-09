from __future__ import annotations

from langchain.tools import tool

from deerflow.researchops.evaluation.runner import run_eval_cases


@tool("eval_runner", parse_docstring=True)
def eval_runner_tool(cases_path: str, work_dir: str = "outputs/evaluation") -> str:
    """Run ResearchOps local evaluation cases and return metrics JSON.

    Args:
        cases_path: Path to eval_queries.jsonl.
        work_dir: Directory for temporary eval memory, state, and reports.
    """
    return run_eval_cases(cases_path=cases_path, work_dir=work_dir).model_dump_json(indent=2)
