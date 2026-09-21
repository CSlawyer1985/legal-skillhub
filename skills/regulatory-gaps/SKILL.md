---
name: regulatory-gaps
description: 未整改处理的内规差异台账 —— 已标记但未关闭的项。用户问"开放的内规差异有什么"、"内规差异台账"、"整改状态"，或想关闭（--close GAP-ID）/ 风险接受（--accept GAP-ID）某条已跟踪内规差异时使用。
metadata:
  displayName: 内规差异台账
  argument-hint: '[可选: --close GAP-ID | --accept GAP-ID]'
---

# /gaps

1. 读内规差异台账 `$LEGAL_AGENT_PROFILE_HOME/regulatory-legal/gap-tracker.yaml`
2. 如果 `--close`：标记内规差异为关闭，附解决方案说明
3. 如果 `--accept`：记录风险接受理由和接受人，状态 → risk-accepted
4. 否则：按年龄和重要性报告开放的内规差异

> 详细台账结构定义、状态报告格式、负责人通知逻辑（逐条预审确认、无例外）、提醒节奏、关闭 / 风险接受模式、重大动作确认环节 —— 全部在 **`regulatory-gap-surfacer`（内规差异呈现）** 参考技能中。做实质工作前先加载它。
