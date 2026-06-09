---
name: researchops-experiment-review
description: "Use for ResearchOps EXPERIMENT_REVIEW intent: experiment retrospectives, log analysis, failure analysis, and next debugging actions."
allowed-tools:
  - classify_research_intent
  - researchops_check_hitl
  - researchops_resume_pending
  - memory_search
  - memory_writer
  - note_loader
  - log_parser
  - task_reader
  - task_writer
  - context_builder
  - ask_clarification
  - read_file
  - write_file
  - ls
  - grep
  - present_files
---

# ResearchOps Experiment Review

## Trigger Intent

Use when `classify_research_intent` returns `EXPERIMENT_REVIEW`.

## Required Slots

- `project`
- experiment or log source when available

If the project or experiment target is ambiguous, ask clarification through the ResearchOps HITL flow.

## Recommended Memory Types

- ExperimentMemory
- ProjectMemory
- DecisionMemory
- ResourceMemory

## Recommended Tools

1. `researchops_resume_pending`
2. `classify_research_intent`
3. `researchops_check_hitl`
4. `read_file`, `grep`, `ls`
5. `note_loader`, `log_parser`
6. `memory_search`, `memory_writer`, `task_writer`
7. `context_builder`

## Output Structure

- Experiment goal
- Setup and evidence
- Observed result
- Failure hypotheses
- Next debugging actions

## Evidence Requirements

Claims about metrics, errors, and failed steps must cite logs or experiment memory.

## Memory Update Rules

Save durable failure reasons, metrics, and follow-up actions as ExperimentMemory and TaskMemory.
