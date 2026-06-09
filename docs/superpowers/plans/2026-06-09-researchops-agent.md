# ResearchOps Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a DeerFlow-native ResearchOps-Agent that reuses DeerFlow's lead agent, graph, skills, tools, sandbox, memory middleware, and clarification middleware while adding ResearchOps-specific intent and HITL state management.

**Architecture:** ResearchOps is implemented as a custom agent plus skills and tools. The existing `lead_agent` graph remains the runtime entry point; ResearchOps domain behavior is added through `SOUL.md`, `skills/public/researchops/*`, and `deerflow.researchops` tool modules.

**Tech Stack:** Python 3.12, LangChain tools, Pydantic, SQLite, DeerFlow custom agents, DeerFlow skills, pytest.

---

### Task 1: Phase 0 Documentation

**Files:**
- Create: `docs/researchops/phase0.md`

- [ ] Add a concise Phase 0 record listing DeerFlow-native reuse points, ResearchOps additions, and things not to reimplement.
- [ ] Verify the document references the actual lead graph, custom agent, skill, tool, memory, sandbox, and clarification entry points.

### Task 2: ResearchOps Intent Tool

**Files:**
- Create: `backend/packages/harness/deerflow/researchops/__init__.py`
- Create: `backend/packages/harness/deerflow/researchops/schemas.py`
- Create: `backend/packages/harness/deerflow/researchops/intent.py`
- Create: `backend/packages/harness/deerflow/researchops/tools/__init__.py`
- Create: `backend/packages/harness/deerflow/researchops/tools/intent_tool.py`
- Test: `backend/tests/test_researchops_intent.py`

- [ ] Write tests for five intents and missing-slot behavior.
- [ ] Implement deterministic keyword-based classification for the MVP.
- [ ] Expose `classify_research_intent` as a LangChain tool returning JSON.

### Task 3: Claude-Style HITL State

**Files:**
- Create: `backend/packages/harness/deerflow/researchops/hitl.py`
- Create: `backend/packages/harness/deerflow/researchops/state_store.py`
- Create: `backend/packages/harness/deerflow/researchops/tools/hitl_tools.py`
- Test: `backend/tests/test_researchops_hitl.py`

- [ ] Write tests proving slot gaps create pending checkpoints without changing the original intent.
- [ ] Implement SQLite-backed pending checkpoint storage under the ResearchOps agent directory.
- [ ] Expose `researchops_check_hitl` and `researchops_resume_pending` tools.
- [ ] Ensure resume fills missing slots and returns the original intent state.

### Task 4: ResearchOps Custom Agent and Skills

**Files:**
- Create: `.deer-flow/users/default/agents/researchops-agent/config.yaml`
- Create: `.deer-flow/users/default/agents/researchops-agent/SOUL.md`
- Create: `skills/public/researchops/progress_summary/SKILL.md`
- Create: `skills/public/researchops/experiment_review/SKILL.md`
- Create: `skills/public/researchops/project_planning/SKILL.md`
- Create: `skills/public/researchops/knowledge_qa/SKILL.md`
- Create: `skills/public/researchops/task_tracking/SKILL.md`
- Test: `backend/tests/test_researchops_skills.py`

- [ ] Add custom agent config scoped to ResearchOps tool groups and skills.
- [ ] Add SOUL policy requiring resume-pending check before new classification.
- [ ] Add five skills with trigger intent, required slots, recommended tools, evidence rules, memory update rules, and clarification conditions.
- [ ] Add tests that skill frontmatter parses and declares expected allowed tools.

### Task 5: Config Registration and Demo

**Files:**
- Modify: `config.yaml`
- Test: `backend/tests/test_researchops_tool_registration.py`

- [ ] Register `researchops` tool group and Phase 1 tools in `config.yaml`.
- [ ] Add tests that `get_available_tools(groups=["researchops"])` includes the ResearchOps tools.
- [ ] Run focused pytest tests.
- [ ] Provide demo commands and expected output.

