---
name: researchops-task-tracking
description: "Use for ResearchOps TASK_TRACKING intent: task list management, TODO updates, blocker tracking, and next-action maintenance."
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

# ResearchOps Task Tracking

## Trigger Intent

Use when `classify_research_intent` returns `TASK_TRACKING`.

## Required Slots

- `task_operation`
- task title or identifiable task reference when updating an existing task

If the user says "I completed A", mark A as `done`. If the user says "B is blocked", mark B as `blocked` and ask for `blocked_by` or `next_action` when missing.

## Recommended Memory Types

- TaskMemory
- ProjectMemory
- DecisionMemory

## Recommended Tools

1. `researchops_resume_pending`
2. `classify_research_intent`
3. `researchops_check_hitl`
4. `note_loader`, `task_reader`
5. `memory_search`, `memory_writer`, `task_writer`
6. `context_builder`
7. `report_writer`

## Output Structure

- Parsed task updates
- Updated statuses
- Blockers
- Next actions

## Evidence Requirements

Task updates should cite the user statement or a source note.

## Memory Update Rules

All task changes must be persisted through TaskMemory tools and recorded in session trace.
