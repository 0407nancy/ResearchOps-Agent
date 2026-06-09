# ResearchOps Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade ResearchOps-Agent from MVP modules into a stronger DeerFlow-native long-horizon agent with better intent, retrieval/context, evidence verification, tool policy, eval, and optional multi-agent evolution.

**Architecture:** DeerFlow remains the runtime, lead agent, skill loader, tool registry, sandbox, and custom-agent layer. ResearchOps adds domain modules under `backend/packages/harness/deerflow/researchops/` and tools registered through DeerFlow's existing tool system. Claude-style ideas are used only for checkpoint state, tool policy, trace, and isolated specialist-agent evolution.

**Tech Stack:** Python, Pydantic, SQLite/FTS5, DeerFlow tools/skills/custom agents, pytest, local deterministic eval with optional LLM-backed extension points.

---

### Phase 8: Intent Classifier Upgrade

**Files:**
- Modify: `backend/packages/harness/deerflow/researchops/schemas.py`
- Replace: `backend/packages/harness/deerflow/researchops/intent.py`
- Create: `backend/packages/harness/deerflow/researchops/intent_rules.py`
- Create: `backend/packages/harness/deerflow/researchops/intent_calibrator.py`
- Modify: `backend/tests/test_researchops_intent.py`
- Modify: `backend/tests/test_researchops_evaluation.py`

**Behavior:**
- Keep deterministic behavior for offline tests.
- Add `alternatives`, `slot_evidence`, and `classification_rationale`.
- Use scored intent candidates instead of first-match keyword rules.
- Preserve HITL behavior: missing slots remain slots, not `NEED_CLARIFICATION`.

### Phase 9: Retrieval and Context Pipeline

**Files:**
- Create: `researchops/retrieval.py`
- Create: `researchops/rerank.py`
- Create: `researchops/compression.py`
- Create: `researchops/context_budget.py`
- Modify: `researchops/context_builder.py`
- Modify: `tests/test_researchops_context_tools.py`

**Behavior:**
- Candidate retrieval from memory/source/task.
- Lightweight rerank by lexical overlap, type priority, recency, and evidence density.
- Compress long chunks with extractive sentence selection.
- Track context budget and dropped candidates.

### Phase 10: Claim-Level Evidence Verification

**Files:**
- Create: `researchops/evidence/claim_extractor.py`
- Create: `researchops/evidence/verifier.py`
- Modify: `researchops/report_writer.py`
- Create: `tests/test_researchops_evidence.py`

**Behavior:**
- Extract report claims.
- Align claims to evidence refs.
- Mark claims `supported`, `weakly_supported`, or `unsupported`.
- Report unsupported claims instead of silently presenting them.

### Phase 11: Tool Policy

**Files:**
- Create: `researchops/tool_policy.py`
- Create: `researchops/tools/tool_policy_tools.py`
- Modify: task/memory/report tools to expose dry-run style payloads where useful.
- Create: `tests/test_researchops_tool_policy.py`

**Behavior:**
- Classify tool calls as low/medium/high risk.
- Trigger ResearchOps HITL for high-risk writes or overwrites.
- Persist pre/post tool events to session trace.

### Phase 12: Evaluation 2.0

**Files:**
- Modify: `researchops/evaluation/metrics.py`
- Modify: `researchops/evaluation/runner.py`
- Add: `data/examples/researchops/eval_sessions.jsonl`
- Create: `tests/test_researchops_evaluation_sessions.py`

**Behavior:**
- Add slot F1, context precision, context recall, claim support precision, unsupported claim rate, and multi-turn state accuracy.
- Keep current 20-case eval as smoke eval.

### Phase 13: Multi-Agent Evolution

**Files:**
- Add custom agent configs under `.deer-flow/users/default/agents/` for memory/evidence/report agents when runtime config is ready.
- Add ResearchOps skill docs for each specialist.
- Add tests that validate config/skill parsing, not live LLM behavior.

**Behavior:**
- Lead Agent stays in control.
- Specialist agents return structured outputs.
- Memory writes remain centralized through `memory_writer` and HITL policy.
