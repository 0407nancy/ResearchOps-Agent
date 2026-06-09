# Phase 0: DeerFlow-Native ResearchOps 接入确认

## 目标

ResearchOps-Agent 作为 DeerFlow-native custom agent 实现，不创建平行 Agent runtime，不复制 lead agent，不新增独立 skill loader 或 tool registry。

## 直接复用的 DeerFlow 能力

- LangGraph graph：`backend/langgraph.json` 中的 `lead_agent`
- Lead agent factory：`deerflow.agents:make_lead_agent`
- Custom agent：`.deer-flow/users/{user_id}/agents/{agent_name}/config.yaml` 与 `SOUL.md`
- Skill system：`skills/public/**/SKILL.md`
- Tool system：`config.yaml` 的 `tool_groups` 与 `tools`
- Built-in HITL display：`ask_clarification` + `ClarificationMiddleware`
- Sandbox 与文件工具：`read_file`、`write_file`、`ls`、`grep`、`bash`
- Thread workspace：`/mnt/user-data/workspace`、`/mnt/user-data/uploads`、`/mnt/user-data/outputs`
- DeerFlow memory middleware：保留为通用用户画像和偏好注入

## 需要轻量封装的 DeerFlow 能力

- HITL：ResearchOps 负责 pending checkpoint 状态，DeerFlow 负责中断展示问题。
- Session trace：ResearchOps 记录领域 trace，同时可以引用 DeerFlow run events。
- Report output：ResearchOps 写入 `/mnt/user-data/outputs/reports`，复用 DeerFlow artifacts/present_files 能力。

## 新增 ResearchOps 领域能力

- 5 个 intent：`PROGRESS_SUMMARY`、`EXPERIMENT_REVIEW`、`PROJECT_PLANNING`、`KNOWLEDGE_QA`、`TASK_TRACKING`
- Claude-style HITL pending checkpoint store
- Typed research memory store：Project、Experiment、Paper、Decision、Preference、Resource、Task
- ResearchOps skills：progress summary、experiment review、project planning、knowledge QA、task tracking
- ResearchOps tools：intent classifier、HITL checker/resumer、typed memory、note/log/task/report/eval tools
- Evaluation harness：intent、clarification、memory recall、task update、report completeness、evidence coverage

## 不重复实现

- 不重写 DeerFlow lead agent
- 不新增第二套 LangGraph graph
- 不新增独立 tool registry
- 不新增独立 skill loader
- 不重复实现文件读写、sandbox、web search、Todo middleware
- 不把 slot 缺失编码为 `NEED_CLARIFICATION` intent
- 不把 typed research memory 强塞进 DeerFlow 通用 facts memory

## 最终接入形态

```text
DeerFlow existing runtime
  -> graph: lead_agent
    -> custom agent: researchops-agent
      -> SOUL.md / config.yaml
      -> skills/public/researchops/*/SKILL.md
      -> tool group: researchops
      -> deerflow.researchops.tools.*
      -> typed memory + HITL checkpoint SQLite
      -> evaluation runner
```

## Phase 1 Demo 目标

输入：

```text
帮我整理 OpenClaw RL 的进展
```

期望 intent：

```json
{
  "intent": "PROGRESS_SUMMARY",
  "project": "OpenClaw RL",
  "time_range": null,
  "missing_slots": ["time_range"]
}
```

ResearchOps HITL 应保存 pending checkpoint，然后调用 DeerFlow 原生 `ask_clarification` 追问时间范围。用户回复后，ResearchOps 从 pending checkpoint 恢复原始 `PROGRESS_SUMMARY`，而不是重新分类为新 intent。
