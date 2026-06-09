---
name: researchops-knowledge-qa
description: "Use for ResearchOps KNOWLEDGE_QA intent: paper, technical concept, project background, code architecture, and resource questions."
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
  - web_search
  - web_fetch
  - present_files
---

# ResearchOps Knowledge QA

## Trigger Intent

Use when `classify_research_intent` returns `KNOWLEDGE_QA`.

## Required Slots

- question

Ask clarification only when the question has multiple plausible interpretations.

## Recommended Memory Types

- PaperMemory
- ResourceMemory
- ProjectMemory
- DecisionMemory

## Recommended Tools

1. `researchops_resume_pending`
2. `classify_research_intent`
3. `read_file`, `grep`, `web_search`, `web_fetch`
4. `memory_search`, `memory_writer`
5. Future phases: `paper_parser`

## Output Structure

- Short answer
- Explanation
- Evidence or citations
- Relation to active project if relevant

## Evidence Requirements

Use local memory or source citations for claims. If using web results, include links.

## Memory Update Rules

Only durable paper/resource insights should be saved in later phases.
