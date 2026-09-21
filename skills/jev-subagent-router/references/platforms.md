# 平台模型与 effort

研究快照：2026-09-20。Codex 数据同时由当前工具 schema 和本机 `models_cache.json` 核实；Claude Code 本机版本为 2.1.272。使用时以当前宿主允许的集合为准。

## Codex

| 用户名称 | 精确模型 ID | Codex effort | 默认 |
| --- | --- | --- | --- |
| 5.6-sol | `gpt-5.6-sol` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | `medium` |
| terra | `gpt-5.6-terra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | `medium` |
| luna | `gpt-5.6-luna` | `low`, `medium`, `high`, `xhigh`, `max` | `medium` |
| 6-astra | `gpt-6-astra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | `low` |

模型目录是宿主能力记录，默认值不是 Jev 的选型策略。Luna 适合明确、窄范围任务；Terra 适合常规实现与检索；Sol 适合较复杂的多步工作；Astra 面向最具挑战性的问题。该描述用于判断任务适配，不是本 skill 测出的排名。

参数入口：

| 入口 | 模型字段 | effort 字段 |
| --- | --- | --- |
| 当前 `collaboration.spawn_agent` | `model` | `reasoning_effort` |
| Codex 自定义 agent TOML | `model` | `model_reasoning_effort` |
| Codex CLI 配置 | `model` / `--model` | `model_reasoning_effort` |
| OpenAI Responses API | `model` | `reasoning.effort` |

当前 spawn 工具只有 `fork_turns: "none"` 或有限轮数历史支持显式模型覆盖；本 skill 使用 `"none"`。自定义 TOML 示例：

```toml
name = "jev-worker"
description = "完成主模型分配的有界子任务"
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
```

OpenAI API 与 Codex 不是同一参数面。例如 Sol API 文档列出 `none`、`low`、`medium`、`high`、`xhigh`、`max`，而本机 Codex 列出上表集合。不得把 API 的 `none` 或宽泛类型里的 `minimal` 自动加入 Codex 子代理候选。`ultra` 在本机描述中包含自动委派语义，必须满足嵌套委派限制。

来源：[Codex 子代理与配置](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Sol API](https://developers.openai.com/api/docs/models/gpt-5.6-sol)、[Astra API](https://developers.openai.com/api/docs/models/gpt-6-astra)。当前运行时工具 schema 是模型覆盖和 fork 参数的直接依据。

## Claude Code

| 用户名称 | 精确模型 ID | Claude Code effort | 默认 |
| --- | --- | --- | --- |
| opus-5 | `claude-opus-5` | `low`, `medium`, `high`, `xhigh`, `max` | `high` |
| opus-4.6 | `claude-opus-4-6` | `low`, `medium`, `high`, `max` | `high` |
| sonnet-5 | `claude-sonnet-5` | `low`, `medium`, `high`, `xhigh`, `max` | `high` |
| fable-5.1 | `claude-fable-5-1` | `low`, `medium`, `high`, `xhigh`, `max` | `high` |

精确 ID 避免 `opus`、`sonnet`、`fable` 家族别名随版本变动。Opus 4.6 保留在指定候选集合中，不能误配 `xhigh`。`adaptive` 是 thinking 模式；`ultracode` 是 Claude Code 编排设置；二者均不是这里的 effort 值。

Sonnet 5 用于常规任务；Opus 5 用于复杂代理工作；Fable 5.1 用于高难度推理。Opus 4.6 是较早的 Opus 代际，按当前任务适配证据选择；不能凭版本号给它虚构成本优势或强制分配固定档位。

配置入口：

| 入口 | 模型字段 | effort 字段 |
| --- | --- | --- |
| 原生子代理 Markdown frontmatter | `model` | `effort` |
| `claude --agents` 的代理定义对象 | `model` | `effort` |
| Claude Code CLI 会话 | `--model` | `--effort` |
| Claude Code 会话设置 | `model` | `effortLevel` |
| Claude Messages API | `model` | `output_config.effort` |

原生子代理定义示例（具体值必须来自当前 Jev 结果）：

```markdown
---
name: jev-cancellation-review
description: 核对取消请求与写入完成之间的状态所有权
model: claude-opus-5
effort: high
---
分析主模型交付的子任务，返回有证据的结论和验证结果。
```

模型逐次调用参数可覆盖定义中的模型；effort 可在定义中覆盖会话。`Agent` 工具逐次参数是否包含 effort，须读当次 schema，不能由 CLI 支持推断。存在 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`、组织模型限制或 effort cap 时，核对最终生效值。

来源：[模型 ID 与版本](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions)、[当前模型目录](https://platform.claude.com/docs/en/models/overview)、[模型配置和 effort 表](https://code.claude.com/docs/en/model-config)、[原生子代理定义与优先级](https://code.claude.com/docs/en/sub-agents)、[API effort](https://platform.claude.com/docs/en/build-with-claude/effort)。
