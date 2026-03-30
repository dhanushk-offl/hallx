# hallx（中文）

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)

`hallx` 是一个面向 LLM 输出的轻量级风险评分护栏库。  
它帮助团队在生产环境中回答一个关键问题：

`这条模型输出到底有多高风险？`

## 为什么需要 Hallx

LLM 在生产中的问题通常很隐蔽：

- 回答很流畅，但没有证据支撑
- JSON 看起来正确，但在严格消费端失败
- 同一提示词多次生成差异过大，难以自动化

Hallx 提供可落地的决策层：

- 给输出打分
- 明确风险问题
- 做出 `proceed` / `retry` 决策
- 用反馈持续校准阈值

## Hallx 提供什么

| 能力 | 输出 |
|---|---|
| 风险评分 | `confidence`（`0.0` 到 `1.0`） |
| 风险分级 | `risk_level`（`high` / `medium` / `low`） |
| 诊断信息 | `issues` |
| 运行建议 | `recommendation` |
| 运营闭环 | 反馈存储 + 校准报告 |

## 适合哪些团队

- 构建 RAG / 对话产品的团队
- 输出机器可消费 JSON 的后端系统
- LLM 输出会触发下游动作的自动化流程
- 负责重试/拦截策略的 Ops/QA 团队

说明：在医疗、法律、金融等高风险场景，应将 Hallx 与领域校验和人工审核结合使用。

## 评分模型

Hallx 基于 3 个启发式信号进行评分：

- `schema`: 结构有效性
- `consistency`: 多次生成稳定性
- `grounding`: 结论与上下文证据一致性

```text
confidence = clamp(
  schema_score * w_schema +
  consistency_score * w_consistency +
  grounding_score * w_grounding,
  0.0, 1.0
)
```

默认（`balanced`）权重：
- `w_schema = 0.34`
- `w_consistency = 0.33`
- `w_grounding = 0.33`

风险分级：
- `< 0.40` -> `high`
- `< 0.75` -> `medium`
- `>= 0.75` -> `low`

如果某些检查被跳过，系统会默认施加惩罚，避免对不完整分析产生过度信任。

## 端到端流程

![Hallx workflow](images/hallx-working-flow.svg)

1. 接收 Prompt，以及可选的 context/schema
2. 通过 Adapter/Callable 生成响应
3. 执行 `schema` / `consistency` / `grounding`
4. 计算 `confidence` 与 `risk_level`
5. 根据 `recommendation` 执行 `proceed` 或 `retry`
6. 保存人工复核结果并持续校准阈值

## Quick Start

```python
from hallx import Hallx

checker = Hallx(profile="balanced")
result = checker.check(
    prompt="Summarize refund policy",
    response={"summary": "Refunds are allowed within 30 days."},
    context=["Refunds are allowed within 30 days of purchase."],
)

print(result.confidence, result.risk_level)
print(result.issues)
print(result.recommendation)
```

## Safety Profiles

| Profile | 目标 | 默认 `consistency_runs` | Skip penalty |
|---|---|---:|---:|
| `fast` | 更低延迟 | 2 | 0.15 |
| `balanced` | 通用平衡 | 3 | 0.25 |
| `strict` | 更严格控制 | 4 | 0.40 |

## 继续阅读

- English: [README.en.md](README.en.md)
- தமிழ்: [README.ta.md](README.ta.md)
- മലയാളം: [README.ml.md](README.ml.md)
- Usage: [USAGE.md](USAGE.md)
- Production: [PRODUCTION.md](PRODUCTION.md)
