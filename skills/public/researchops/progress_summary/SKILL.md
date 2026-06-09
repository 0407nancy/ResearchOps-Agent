---
name: researchops-progress-summary
description: "Use for ResearchOps PROGRESS_SUMMARY intent: daily summaries, weekly reports, meeting preparation, and project progress summaries."
allowed-tools:
  - classify_research_intent
  - researchops_check_hitl
  - researchops_resume_pending
  - memory_search
  - memory_writer
  - ask_clarification
  - read_file
  - write_file
  - ls
  - grep
  - present_files
---

# ResearchOps Progress Summary

## Trigger Intent

Use when `classify_research_intent` returns `PROGRESS_SUMMARY`.

## Required Slots

- `project`
- `time_range`
- `output_format`

If `time_range` is missing, call `researchops_check_hitl` and then `ask_clarification`. Do not treat clarification as a separate intent.

## Recommended Memory Types

- ProjectMemory
- ExperimentMemory
- DecisionMemory
- TaskMemory

## Recommended Tools

1. `researchops_resume_pending`
2. `classify_research_intent`
3. `researchops_check_hitl`
4. `read_file`, `grep`, `ls`
5. `memory_search`, `memory_writer`
6. Future phases: `note_loader`, `report_writer`

## Output Structure

- Scope
- Progress
- Evidence
- Issues and blockers
- Next actions

## Evidence Requirements

Every key progress claim should cite a note, task, experiment, or memory id. If evidence is insufficient, state uncertainty.

## Memory Update Rules

Persist durable project progress, blockers, decisions, and next actions through ResearchOps memory tools in later phases.
