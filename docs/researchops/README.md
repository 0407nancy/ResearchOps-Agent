# ResearchOps-Agent

ResearchOps-Agent is a DeerFlow-native long-horizon research operations agent. It reuses DeerFlow's lead agent runtime, LangGraph graph, custom agent config, skill loader, tool registry, sandbox/file tools, and built-in clarification tool. ResearchOps adds only domain-specific intent, HITL state, typed memory, context engineering, reports, session trace, and evaluation.

## DeerFlow Entry Points

- Lead agent graph: `backend/langgraph.json` -> `deerflow.agents:make_lead_agent`
- Custom agent: `.deer-flow/users/default/agents/researchops-agent/`
- Public skills: `skills/public/researchops/**/SKILL.md`
- ResearchOps tools: `backend/packages/harness/deerflow/researchops/tools/`
- Typed memory and HITL state: `.deer-flow/users/default/agents/researchops-agent/*.sqlite`

## Implemented Phases

- Phase 0: DeerFlow extension-point research in `docs/researchops/phase0.md`
- Phase 1: `researchops-agent` custom agent config and 5 ResearchOps skills
- Phase 2: five-intent classifier and Claude-style HITL checkpoint state
- Phase 3: SQLite typed memory store and memory tools
- Phase 4: note loader, log parser, task tools, context packet and evidence table
- Phase 5: markdown report writer for progress, experiment review, planning, QA, and tasks
- Phase 6: local evaluation runner, metrics, and 20 eval cases
- Phase 7: session trace store/tool and demo docs

## Local Verification

From `backend/`:

```bash
uv run pytest tests/test_researchops_intent.py tests/test_researchops_hitl.py tests/test_researchops_memory.py tests/test_researchops_context_tools.py tests/test_researchops_report_writer.py tests/test_researchops_evaluation.py tests/test_researchops_session_trace.py tests/test_researchops_skills.py tests/test_researchops_tool_registration.py -q
```

Run the sample evaluation:

```bash
uv run python -c 'import json, tempfile; from pathlib import Path; from deerflow.researchops.evaluation.runner import run_eval_cases; result=run_eval_cases(cases_path="../data/examples/researchops/eval_queries.jsonl", work_dir=Path(tempfile.mkdtemp())); print(json.dumps({"total": result.total, "metrics": result.metrics}, ensure_ascii=False, indent=2))'
```

## Yishuo Router

Do not commit API keys. Enable the local Yishuo Router model in ignored `config.yaml` only after setting:

```bash
export YISHUO_API_KEY='your-api-key'
```

Then uncomment the `yishuo-router` model block in `config.yaml` and set the ResearchOps custom agent model to `yishuo-router`.

## Resume Pitch

Built a DeerFlow-native long-horizon ResearchOps agent for research interns and independent developers, adding typed research memory, Claude-style HITL checkpoint state, evidence-grounded context construction, markdown report generation, session tracing, and a local evaluation harness over DeerFlow's existing lead agent runtime, LangGraph graph, skills, tool registry, sandbox, and clarification tool. Evaluated intent classification, clarification behavior, task updates, report completeness, evidence coverage, and memory recall on a 20-case benchmark.
