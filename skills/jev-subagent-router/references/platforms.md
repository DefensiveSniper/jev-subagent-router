# 平台模型与 effort

模型 ID 复核：2026-09-21；effort 研究快照：2026-09-20；定价与定位复核：2026-09-22。Codex 数据同时由当前工具 schema 和本机 `models_cache.json` 核实；Claude Code 本机版本为 2.1.272。使用时以当前宿主允许的集合为准。

## Codex

| 用户名称 | 精确模型 ID | Codex effort | 默认 |
| --- | --- | --- | --- |
| 5.6-sol | `gpt-5.6-sol` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | `medium` |
| terra | `gpt-5.6-terra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | `medium` |
| luna | `gpt-5.6-luna` | `low`, `medium`, `high`, `xhigh`, `max` | `medium` |
| 6-astra | `gpt-6-astra` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | `low` |

模型目录是宿主能力记录，默认值不是 Jev 的选型策略。

官方列表价（美元 / 百万 token）与定位，`route.py` 的 `CATALOG` 把同样的事实写进每个候选的 `list_price` 与 `profile`：

| 模型 | 输入 | 缓存输入 | 输出 | 相对 Luna | 官方定位 |
| --- | --- | --- | --- | --- | --- |
| `gpt-5.6-luna` | $0.2 | $0.02 | $1.2 | 1× | nano 档；成本敏感、高吞吐、窄范围可重复的工作 |
| `gpt-5.6-terra` | $2 | $0.2 | $12 | 10× | mini 档；平衡智能与成本，探索、读多写少的扫描、大文件审查 |
| `gpt-5.6-sol` | $4 | $0.4 | $20 | 20× | GPT-5.6 旗舰（`gpt-5.6` 别名指向它）；需要规划、工具使用、验证与跟进的模糊多步工作 |
| `gpt-6-astra` | $10 | $1 | $50 | 50× | 最强模型；最难的端到端工作、新颖问题、长程自主 |

Sol 的价格为促销价，官方注明至少持续到 2026-11-21。Codex 子代理文档对 effort 的说明：`low` 用于直接且看重速度的任务；`medium` 是多数代理的平衡默认；`high` 用于追踪复杂逻辑、检查假设、处理边界；`xhigh` 与 `max` 用于特别苛刻的推理；`ultra` 是最深档并带自动委派。未指定时子代理继承父设置或模型默认值。

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

来源：[Codex 子代理与配置](https://learn.chatgpt.com/docs/agent-configuration/subagents)（模型与 effort 选择指引）、[Sol API](https://developers.openai.com/api/docs/models/gpt-5.6-sol)、[Terra API](https://developers.openai.com/api/docs/models/gpt-5.6-terra)、[Luna API](https://developers.openai.com/api/docs/models/gpt-5.6-luna)、[Astra API](https://developers.openai.com/api/docs/models/gpt-6-astra)。当前运行时工具 schema 是模型覆盖和 fork 参数的直接依据。

## Claude Code

| 用户名称 | 精确模型 ID | Claude Code effort | 默认 |
| --- | --- | --- | --- |
| opus-5 | `claude-opus-5` | `low`, `medium`, `high`, `xhigh`, `max` | `high` |
| opus-4.6 | `claude-opus-4-6` | `low`, `medium`, `high`, `max` | `high` |
| sonnet-5 | `claude-sonnet-5` | `low`, `medium`, `high`, `xhigh`, `max` | `high` |
| fable-5.1 | `claude-fable-5-1` | `low`, `medium`, `high`, `xhigh`, `max` | `high` |

精确 ID 避免 `opus`、`sonnet`、`fable` 家族别名随版本变动。Opus 4.6 保留在指定候选集合中，不能误配 `xhigh`。`adaptive` 是 thinking 模式；`ultracode` 是 Claude Code 编排设置；二者均不是这里的 effort 值。

官方列表价（美元 / 百万 token）与定位，`CATALOG` 把同样的事实写进每个候选：

| 模型 | 输入 | 输出 | 相对 Sonnet | 定位与区分点 |
| --- | --- | --- | --- | --- |
| `claude-sonnet-5` | $2 | $10 | 1× | 当代高效通用模型，1M 上下文；规格清楚的实现、有测试覆盖的重构、文档、有复现的单模块调试 |
| `claude-opus-5` | $5 | $25 | 2.5× | 复杂代理式编码的默认选择；跨模块改动、并发与状态类 bug 定位、大 diff 正确性审查、带兼容约束的设计 |
| `claude-opus-4-6` | $5 | $25 | 2.5× | 上一代 Opus，与 Opus 5 同价且无 `xhigh`；只在本项目证据表明它更合适时选 |
| `claude-fable-5-1` | $10 | $50 | 5× | 最强模型；相对 Opus 5 的差异化优势是长程自主、新颖或欠定义问题、竞争假设的裁决、错误代价高且难验证的任务。推理常开，Fable 的低档 effort 常相当于 Opus 的 high/xhigh。订阅计划对 Fable 单独计量周额度 |

Claude 侧 effort：`high` 是 API 默认；`xhigh` 是这一代模型（Sonnet 5、Opus 5、Fable 5.1）上多数编码与代理任务的推荐档；`max` 只在 xhigh 可测量地留有余量时使用；`medium` 是质量守得住时的降本档；`low` 给简单明确的子任务。同名 effort 在不同模型上不等价。Opus 4.6 不能配 `xhigh`；不能凭版本号给它虚构成本优势或强制分配固定档位。

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
name: jev-claude-opus-5-high
description: 核对取消请求与写入完成之间的状态所有权
model: claude-opus-5
effort: high
---
分析主模型交付的子任务，返回有证据的结论和验证结果。
```

本 skill 通过代理定义固定完整模型 ID 和 effort，调用 `Agent` 时只指定 `subagent_type` 与任务内容。逐次 `model` 参数会覆盖定义，因此派发时省略该参数。完整模型 ID 在 frontmatter 中受支持，与工具逐次 `model` 参数的别名枚举分别判断。存在 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`、组织模型限制或 effort cap 时，核对最终生效值。

来源：[定价](https://platform.claude.com/docs/en/about-claude/pricing)、[模型 ID 与版本](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions)、[当前模型目录](https://platform.claude.com/docs/en/models/overview)、[模型配置和 effort 表](https://code.claude.com/docs/en/model-config)、[原生子代理定义与优先级](https://code.claude.com/docs/en/sub-agents)、[API effort](https://platform.claude.com/docs/en/build-with-claude/effort)。
