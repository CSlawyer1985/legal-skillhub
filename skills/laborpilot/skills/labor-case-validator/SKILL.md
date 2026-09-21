---
name: labor-case-validator
description: 劳动争议案件状态、分析底稿和文书初稿的独立验证器。当需要在阶段转换或交付前专门查找事实矛盾、证据缺口、引用错误、金额不一致、时效遗漏、主体管辖或程序路由错误时使用。不用于代替起草者继续完善原文。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议独立验证

以“尽力推翻当前方案”为目标，不继续执行作者的起草任务。

1. 读取 `.casework/case_state.json`、待验证产物和 [验证规则](../../references/validation.md)。
2. 运行 `python3 scripts/validate_case.py --state <case-root>/.casework/case_state.json --output <case-root>/.casework/validation/deterministic.json`，检查状态、材料、事实冲突、要件覆盖、证据、法源、金额、程序、产物和工作图的一致性。
3. 运行 `python3 scripts/adversarial_validation.py --state <case-root>/.casework/case_state.json --output <case-root>/.casework/validation/adversarial.json`。该报告形成六项可重算检查：对方最强论证、失败边界、事实分层、事实冲突、引用一致性和程序完整性；同时输出事实冲突矩阵、程序矩阵及逐争点挑战矩阵。
4. 对抗报告必须由执行器生成，不得手工拼装为 `pass`。未解决事实冲突必须退回核实；缺少时效、管辖、一裁终局、临时救济或后续救济，存在待确认程序项，或者程序摘要被篡改时不得通过。报告绑定当前事实与程序业务状态；任一状态变化后必须重新运行，不能沿用旧报告。
5. 在 `.casework/validation/` 保存 JSON 内部报告。可选 Markdown 只作人读附件，不得作为 `--report` 入参；不在案件根目录增加用户交付报告。
6. 使用 `python3 scripts/workflow_graph.py record-validation` 登记报告，并提供案件状态、验证类型、验证器、报告和正式产物 ID。对抗报告的 `--validator` 必须为 `laborpilot-adversarial-validator`；工作流会保存被验证文件与报告的 SHA-256，并重新计算业务结果，报告过期、被修改、未绑定实际文件或挑战矩阵不完整时拒绝登记或通过节点。
7. 验证者不得修改待验证产物后自行标记通过。确定性或对抗结果为 `return`／`blocked` 时返回相应上游修复；需要律师判断的剩余风险按工作图升级。
8. 律师审批仍是最终交付门禁；批准时必须同时绑定正式产物 ID 和本次使用的全部验证记录 ID，阶段结案前使用 `trace-artifact` 复算整条来源链。

完成后运行：

```bash
python3 scripts/workflow_graph.py record-validation \
  --state <case-root>/.casework/case_state.json \
  --kind adversarial \
  --validator laborpilot-adversarial-validator \
  --report <case-root>/.casework/validation/adversarial.json \
  --artifact-id <正式产物ID>
```

该命令将验证者、类型、结论、问题、报告路径和哈希就地写入单一案件状态。结论为 `pass` 或 `escalate` 时报告不可省略；仅传命令行状态会被机器门禁拒绝。
