---
name: researchops-project-planning
description: "Use for ResearchOps PROJECT_PLANNING intent: project roadmaps, priority decisions, milestones, and next development plans."
allowed-tools:
  - classify_research_intent
  - researchops_check_hitl
  - researchops_resume_pending
  - memory_search
  - memory_writer
  - note_loader
  - task_reader
  - task_writer
  - context_builder
  - report_writer
  - eval_runner
  - ask_clarification
  - read_file
  - write_file
  - ls
  - grep
  - present_files
---

# ResearchOps Project Planning

## Trigger Intent

Use when `classify_research_intent` returns `PROJECT_PLANNING`.

## Required Slots

- `project`
- planning horizon when user asks for a time-bound plan

If multiple projects match, ask clarification and preserve the original intent.

## Recommended Memory Types

- ProjectMemory
- DecisionMemory
- TaskMemory
- ResourceMemory

## Recommended Tools

1. `researchops_resume_pending`
2. `classify_research_intent`
3. `researchops_check_hitl`
4. `note_loader`, `task_reader`
5. `memory_search`, `memory_writer`, `task_writer`
6. `context_builder`
7. `report_writer`

## Output Structure

- Current state
- Constraints
- Priority rationale
- Milestones
- Next actions

## Evidence Requirements

Planning recommendations must cite project state, prior decisions, blockers, or task evidence.

## Memory Update Rules

Important planning decisions should become DecisionMemory. New action items should become TaskMemory.
