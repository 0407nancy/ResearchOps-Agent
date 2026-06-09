# ResearchOps-Agent

ResearchOps-Agent is a DeerFlow-native long-horizon research operations agent for research interns, research assistants, and independent builders. It helps manage research and engineering projects across progress summaries, experiment retrospectives, project planning, knowledge QA, task tracking, reports, session trace, and evaluation.

This repository is based on ByteDance DeerFlow and intentionally reuses DeerFlow's existing runtime, lead agent, LangGraph graph, custom agent configuration, skill system, tool registry, sandbox/file tools, and built-in clarification tool. ResearchOps adds domain-specific agent capabilities without replacing DeerFlow's core runtime.

## What It Demonstrates

- Long-horizon agent state instead of a fixed workflow or simple chatbot
- Five-intent ResearchOps classifier
- Claude-style HITL checkpoint state for clarification and resume
- Typed research memory with SQLite and FTS-style retrieval
- Tool orchestration through DeerFlow tool groups
- Skill-guided behavior through DeerFlow public skills
- Evidence-grounded context packets and report generation
- Session trace for harness steps and tool results
- Local evaluation harness with measurable metrics

## MVP Intents

- `PROGRESS_SUMMARY`: daily summaries, weekly reports, meeting prep, progress reports
- `EXPERIMENT_REVIEW`: failed experiments, log analysis, retrospective reports
- `PROJECT_PLANNING`: roadmap, priority, milestones, next-step planning
- `KNOWLEDGE_QA`: paper, technical concept, project background, architecture QA
- `TASK_TRACKING`: TODO updates, blockers, task status maintenance

Clarification is not an intent. If slots are missing, ResearchOps stores a pending HITL checkpoint and resumes the original intent after user input.

## ResearchOps Modules

```text
backend/packages/harness/deerflow/researchops/
  intent.py
  hitl.py
  state_store.py
  memory_store.py
  context_builder.py
  report_writer.py
  session_trace.py
  evaluation/
  tools/

skills/public/researchops/
  progress_summary/SKILL.md
  experiment_review/SKILL.md
  project_planning/SKILL.md
  knowledge_qa/SKILL.md
  task_tracking/SKILL.md

data/examples/researchops/eval_queries.jsonl
docs/researchops/
```

## Core Tools

- `classify_research_intent`
- `researchops_check_hitl`
- `researchops_resume_pending`
- `memory_search`
- `memory_writer`
- `note_loader`
- `log_parser`
- `task_reader`
- `task_writer`
- `context_builder`
- `report_writer`
- `eval_runner`
- `session_trace_writer`
- `tool_policy_check`
- `multi_agent_plan`

## Optional Multi-Agent Layer

ResearchOps-Agent keeps the DeerFlow lead agent as the single owner of user interaction, HITL, final output, and memory writes. Multi-agent collaboration is optional and only used for complex or formal outputs.

Specialist agent templates live in:

```text
docs/researchops/multi_agent/agents/
  researchops-memory-agent/
  researchops-evidence-agent/
  researchops-report-agent/
```

To enable them in a local DeerFlow runtime, copy those directories into:

```text
.deer-flow/users/default/agents/
```

The `multi_agent_plan` tool decides whether a task should stay single-agent or delegate to specialists. Memory and Evidence specialists return structured proposals only; memory writes remain centralized through ResearchOps tools and HITL policy.

## Run Focused Tests

From `backend/`:

```bash
uv run pytest tests/test_researchops_intent.py tests/test_researchops_hitl.py tests/test_researchops_memory.py tests/test_researchops_context_tools.py tests/test_researchops_report_writer.py tests/test_researchops_evaluation.py tests/test_researchops_session_trace.py tests/test_researchops_skills.py tests/test_researchops_tool_registration.py -q
```

Expected current result:

```text
27 passed, 1 warning
```

## Run Evaluation

From `backend/`:

```bash
uv run python -c 'import json, tempfile; from pathlib import Path; from deerflow.researchops.evaluation.runner import run_eval_cases; result=run_eval_cases(cases_path="../data/examples/researchops/eval_queries.jsonl", work_dir=Path(tempfile.mkdtemp())); print(json.dumps({"total": result.total, "metrics": result.metrics}, ensure_ascii=False, indent=2))'
```

Run the expanded Eval 2.0 suite:

```bash
uv run python -c 'import json, tempfile; from pathlib import Path; from deerflow.researchops.evaluation.runner import run_eval_suite; result=run_eval_suite(suite_dir="../data/examples/researchops", work_dir=Path(tempfile.mkdtemp())); print(json.dumps({"total": result.total, "metrics": result.metrics}, ensure_ascii=False, indent=2))'
```

Current 20-case benchmark output:

```json
{
  "total": 20,
  "metrics": {
    "intent_accuracy": 1.0,
    "clarification_accuracy": 1.0,
    "task_update_accuracy": 1.0,
    "report_completeness": 1.0,
    "evidence_coverage": 0.75,
    "memory_recall@5": 1.0
  }
}
```

## Model Configuration

Do not commit API keys. Local runtime config is intentionally ignored by git.

For an OpenAI-compatible router, set an environment variable first:

```bash
export YISHUO_API_KEY='your-api-key'
```

Then enable the corresponding model block in local `config.yaml` and point `.deer-flow/users/default/agents/researchops-agent/config.yaml` to that model.

## Resume Project Summary

Built a DeerFlow-native long-horizon ResearchOps agent for research task management, experiment review, progress reporting, planning, and task tracking. Reused DeerFlow's lead agent runtime, LangGraph graph, skill system, tool registry, sandbox, and clarification tool; added typed SQLite research memory, Claude-style HITL checkpoint state, evidence-grounded context engineering, report generation, session tracing, and a local evaluation harness. Evaluated on a 20-case benchmark covering intent classification, clarification, task updates, report completeness, evidence coverage, and memory recall.

## Upstream

This project is built on ByteDance DeerFlow. See the original project at:

https://github.com/bytedance/deer-flow
