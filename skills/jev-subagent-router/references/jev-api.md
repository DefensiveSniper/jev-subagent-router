# TypeSafe Jev HTTP 契约

研究快照：2026-09-20。直接依据 TypeSafe 官方 [API reference](https://docs.typesafe.ai/api)、[模型目录](https://docs.typesafe.ai/models) 与 [文档索引](https://docs.typesafe.ai/llms.txt)。

## 地址与鉴权

- Base URL：`https://api.typesafe.ai`
- 评估：`POST /v1/systemone`
- 模型列表：`GET /v1/models`
- 请求头：`Authorization: Bearer <JEV_API_KEY 的值>`、`Content-Type: application/json`
- Jev 模型：`jev-latest`；研究时指向 `jev-1.13.0`。实际返回的版本记录在脚本输出的 `jev_model`。

`JEV_API_KEY` 是本 skill 指定的环境变量名；HTTP 协议只收到 Bearer token。脚本用 Python 3 标准库调用固定 HTTPS 地址，不需要安装 SDK。

## 请求 schema

顶层必填 `model: string`、`state: string | object | array`、`questions: map<string, Question>`。支持的三个 Question 分支为：

| type | instructions | criteria |
| --- | --- | --- |
| `choice` | 必填，字符串、对象或数组 | 必填，选项名到描述的映射；描述可为字符串、对象、数组或 null；最多 255 项 |
| `score` | 同上 | 必填，有序等级描述数组，2–10 级 |
| `noul` | 同上 | 可选，`true` / `false` 的含义描述 |

本 skill 采用 `choice`，每个选项代表完整的模型与 effort 组合。请求示意（仅展示两个候选）：

```json
{
  "model": "jev-latest",
  "state": {
    "platform": "codex",
    "task": {
      "objective": "Trace ownership of cancellation and write completion.",
      "acceptance": "Return an evidence-backed root cause."
    }
  },
  "questions": {
    "route": {
      "type": "choice",
      "instructions": "Select the model and effort pair adequate for this task's reasoning demands and acceptance criteria.",
      "criteria": {
        "gpt-6-luna@medium": "Low-cost model; narrowly scoped work.",
        "gpt-6-sol@high": "General coding model; deeper analysis of interacting logic."
      }
    }
  }
}
```

问题 key（此处 `route`）只用于匹配响应，不进入推理；问题语义写在 `instructions`，模型能力与 effort 含义写在 `criteria`。实际请求由脚本生成，Jev 顶层 `model` 始终是 Jev，目标子代理模型是 Choice 选项。

## 响应 schema

顶层为 `model`、`answers`、`usage`。Choice 答案包含 `type: "choice"`、`choice: string`、`probabilities: map<string, number>` 和 `confidence: number`。概率值范围 0–1，总和为 1，`choice` 为最高概率选项；confidence 与选项概率是不同字段。

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "route": {
      "type": "choice",
      "choice": "gpt-6-sol@high",
      "probabilities": {
        "gpt-6-luna@medium": 0.2,
        "gpt-6-sol@high": 0.8
      },
      "confidence": 0.6
    }
  },
  "usage": {"input_tokens": 500, "output_tokens": 30}
}
```

以上响应为说明结构的合成数据，不是在线调用结果。Score 答案另有 `score`、`legend`、`probabilities`、`confidence`；Noul 答案为 `type` 与 `noul`，不是布尔值。本路由只接受 Choice。

脚本检查类型、有限概率、候选集合、概率总和与最大项，随后按本地映射取出模型参数；不执行响应文本。

## 错误与边界

官方列出的状态包括 `401` 鉴权错误、`422` 请求验证失败、`429` 限流、`529` 服务过载。脚本单次请求超时 30 秒、失败返回非零退出码并只输出状态类别。主模型在修复原因后重试；429/529 按服务要求等待后重试，不紧密循环。

研究时 Jev 接受文本与结构化文本，非图像模型；总请求预算 64k tokens，state 加最长问题预算 32k tokens。脚本要求任务摘要不超过 12000 字符，以保持路由输入紧凑；字符限制不等于官方 token 计数。官方说明英语效果较好，其他语言应按实际任务验证。
