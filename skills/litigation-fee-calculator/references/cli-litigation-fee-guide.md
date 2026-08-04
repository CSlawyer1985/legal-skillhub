# 诉讼费用 CLI 场景指南

适用于 `litigation-fee-calculator` skill。目标是将用户提供的案件事实整理为 deli-cli 可执行的诉讼费用计算任务，并将返回结果映射为最终计算书。

使用本指南前，必须先执行 [cli-common.md](./cli-common.md) 中的前置检查和命令发现步骤。

## 一、CLI 命令使用原则

1. 先用 `npx @delilegal/deli-cli@latest cmds litigation-fee-calculator@1.0.0` 获取本次 `RUN id`、命令名和参数。
2. 后续调用必须采用当次返回的 `npx @delilegal/deli-cli@latest run_... <command> [options]` 形态。
3. 不在本指南中固化真实命令名；以下示例中的 `calculate`、`estimate`、`fee-calc` 仅表示可能的计算命令类型，实际以 `cmds` 输出为准。
4. 参数优先在 `cmds` 返回的 `usage` 和 `params` 中选择，不主动假设 `--query`、`--semantic`、`--long-text`、`--amount`、`--type` 或 `--json` 一定存在。
5. 不调用法规检索或案例检索命令；如果 `cmds` 只返回检索类命令，应停止并说明当前 skill scope 未提供可用计算命令。

示例 `cmds` 返回后，实际调用可能形如：

```bash
npx @delilegal/deli-cli@latest run_a1b2c3d4e5f6 calculate --long-text "财产案件，诉讼请求金额150万元，需要计算案件受理费并返回分段明细"
npx @delilegal/deli-cli@latest run_a1b2c3d4e5f6 estimate --long-text "离婚案件，涉及财产分割250万元，用户未提供当地基础费标准，需要按法定区间下限测算"
npx @delilegal/deli-cli@latest run_a1b2c3d4e5f6 fee-calc --long-text "申请财产保全，保全金额120万元，需要计算申请费并判断是否触发5000元上限"
```

以上仅为参数组织示例。正式执行时必须替换为当次 `cmds` 返回的 `run_...`、命令名和参数。

## 二、用户事实组织

每次 CLI 调用只聚焦一个费用类型。优先按以下字段整理事实摘要：

| 字段 | 写法 |
| --- | --- |
| 费用类型 | 财产案件、离婚、人格权、知识产权、劳动争议、行政、执行、保全、支付令、破产、海事申请等 |
| 金额口径 | 诉讼请求金额、争议金额、财产分割总额、赔偿金额、执行金额、保全金额、破产财产总额 |
| 二级分类 | 知识产权有无争议金额、行政案件类别、执行有无金额、海事申请类型 |
| 区间取值 | 用户是否提供当地标准或法院通知金额；未提供时说明按区间下限测算 |
| 计算目标 | 只算合计、展示分段、比较多方案、生成计算书 |

不得把用户没有确认的金额视为诉讼请求金额；例如本金、利息、违约金是否一并计入诉请金额，应先向用户确认。

## 三、CLI 结果映射

- `total`、`total_fee` 或等价字段：映射为合计金额。
- `segments`、`breakdown`、`items` 或等价字段：映射为分段计算明细。
- `cap`、`cap_applied` 或等价字段：映射为封顶说明。
- `range`、`selected_fee`、`local_standard_needed` 或等价字段：映射为区间费用取值说明。
- `basis`、`rule_refs`、`articles` 或等价字段：映射为依据来源；未返回时只能引用本地 `litigation-fee-rules.md` 中对应条款编号。
- `warnings`、`risks` 或等价字段：映射为风险提示。

CLI 未返回的地方标准、法院口径、减免缓缴决定、法条全文、案例裁判口径或额外金额不得自行补写。

## 四、后端计算服务边界

发布给 CLI 客户端的 skill 包只包含 `SKILL.md` 和 `references/`。计算逻辑由 CLI 命令调用后端 MCP 计算服务完成，不存在可供 agent 调用的本地计算入口。

调用后端计算服务时：

1. 只使用当次 `cmds` 返回的 `run_...`、命令名和参数形态。
2. 只采纳 CLI 返回的结构化计算字段，例如输入事实、分段、区间、上限、合计和风险提示。
3. 稳定规则说明以本地 `litigation-fee-rules.md` 或 CLI 返回依据字段为准。
4. CLI 未返回计算结果、分段或必要字段时，不得自行补算；应说明缺失字段并要求补充事实或等待后端计算服务支持。

## 五、无结果或参数不足

单次调用无结果、计算命令不可用或参数不足时：

1. 明确缺少的事实或命令能力。
2. 优先追问用户可提供的金额、案件类型或二级分类。
3. 可基于本地稳定规则说明计算口径和所需参数，但不得输出自行补算的确定金额。
4. 不连续换词调用检索命令，也不将检索结果替代计算结果。
