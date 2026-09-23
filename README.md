# Jev Subagent Router

让 Codex 和 Claude Code 在委派子代理前，通过 [TypeSafe Jev](https://typesafe.ai/) 根据任务复杂度选择模型与 reasoning effort。

主模型提供任务事实与当前可用组合，Jev 联合选择模型和 effort，Python 脚本校验响应，主模型通过原生子代理入口执行。

## 一条命令安装

需要 Node.js / npm、Git，以及用于运行路由脚本的 Python 3.9+。

```sh
npx --yes skills add DefensiveSniper/jev-subagent-router --skill jev-subagent-router --agent codex claude-code --global --yes
```

命令使用 [Skills CLI](https://github.com/vercel-labs/skills)，同时安装到两个宿主的用户级技能目录。只使用一个宿主时，将 `--agent codex claude-code` 改为 `--agent codex` 或 `--agent claude-code`。

安装后重新打开宿主会话。在 Codex 中使用 `$jev-subagent-router`，在 Claude Code 中使用 `/jev-subagent-router`，例如：

> 使用 jev-subagent-router，为接下来需要委派的子任务选择模型和 effort，再启动子代理。

skill 在被加载时指导主模型执行路由。宿主是否自动加载 skill、允许委派哪些任务，取决于其配置与当前指令。

## 首次配置

用户在本机全局导入 `JEV_API_KEY`。例如，zsh 用户在 `~/.zshenv` 中加入：

```sh
export JEV_API_KEY='在本机填入实际密钥'
```

随后执行 `source ~/.zshenv`，并从已加载环境变量的终端重启宿主。macOS 桌面应用还需要在用户终端执行：

```sh
launchctl setenv JEV_API_KEY "$JEV_API_KEY"
```

再完全退出并重新打开应用。`launchctl` 设置作用于当前登录会话。其他 shell、Windows 和远程环境见 [首次配置说明](skills/jev-subagent-router/SKILL.md#首次配置)。

密钥只从进程环境读取。不要把真实密钥放进仓库、命令参数或对话。路由会向 TypeSafe 发送主模型整理的任务摘要和候选描述。

Claude Code 首次使用时，主模型根据 skill 指令，把随包安装的 19 个 [模型与 effort 子代理定义](skills/jev-subagent-router/assets/claude-agents) 放入 `~/.claude/agents/`。每个定义固定完整模型 ID 和 effort，每次调用使用 Jev 返回的 `subagent_type`；安装命令本身只安装 skill 文件。已有同名定义会先检查，保留用户定制。

## 支持范围

| 平台 | 模型 ID |
| --- | --- |
| Codex | `gpt-6-sol`、`gpt-6-luna`、`gpt-6-astra` |
| Claude Code | `claude-opus-5-5`、`claude-opus-4-6`、`claude-sonnet-5`、`claude-fable-5-1` |

每个候选带官方列表价、定位区分点和该平台的 effort 语义，让 Jev 能按"质量优先、够用里选最便宜"裁决。完整 effort 集合、定价、研究日期与官方来源见 [平台参考](skills/jev-subagent-router/references/platforms.md)。实际路由只接受宿主当前确认可用且符合用户约束的组合。Codex 的 `ultra` 还要求嵌套委派已获准。Claude Code 的 Opus 4.6 只参与带明确写作指令的写作任务；Opus 5.5 要求 Claude Code 2.1.280 或更新版本。

Jev 使用 `POST https://api.typesafe.ai/v1/systemone`，模型为 `jev-latest`。每个 Choice 选项代表一个完整的模型与 effort 组合。脚本只依赖 Python 标准库；鉴权失败、网络错误或无效响应会终止本次路由。见 [HTTP 契约](skills/jev-subagent-router/references/jev-api.md)。

## 本地验证

在仓库根目录运行：

```sh
python3 -B -m unittest discover -s tests -v
npx --yes skills add . --list
```

测试使用合成响应，覆盖合法组合、请求构造、响应校验、鉴权缺失及平台参数映射，不发送真实 Jev 请求。在线路由准确率与子代理执行效果需要在自己的任务上验证。

从源码安装：

```sh
npx --yes skills add . --skill jev-subagent-router --agent codex claude-code --global --yes
```

## 更新与移除

```sh
npx --yes skills update jev-subagent-router --global --yes
npx --yes skills remove jev-subagent-router --agent codex claude-code --global --yes
```

Claude Code 的 19 个组合定义独立保存在 `~/.claude/agents/jev-claude-*.md`。更新 skill 后，主模型应比较这些定义与随包模板；移除 skill 后，如已不再使用这些定义，可删除对应模板文件。

## 项目关系

这是面向 Codex 与 Claude Code 的社区集成，使用 TypeSafe Jev 服务。模型、产品名称与商标属于各自所有者。

## 许可证

[MIT](LICENSE)。
