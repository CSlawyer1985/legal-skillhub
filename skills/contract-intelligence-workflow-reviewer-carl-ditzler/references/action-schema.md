# 行动模式

每当 skill 需要建议或准备下一步工作流步骤时，使用本文件。

## 目的

审查不应只以分析结束。将合同的当前状态转化为人类或自动化层可以执行的明确下一步行动。

## 行动类型

使用一个主要行动类型：

- `request_missing_documents`（请求缺失文件）
- `route_for_internal_review`（路由内部审查）
- `revise_contract`（修订合同）
- `prepare_redline_packet`（准备红线稿包）
- `prepare_approval_packet`（准备审批包）
- `open_research_task`（开启研究任务）
- `draft_business_summary`（起草业务摘要）
- `draft_counterparty_message`（起草对方消息）
- `mark_signature_ready`（标记可签署）
- `close_matter`（结案）

## 必需的行动包

使用此模式编写 `action-packet.yaml`：

```yaml
action_packet:
  action_type: ""
  current_state: ""
  next_state: ""
  why_now: ""
  confidence: "high|medium|low"
  blocking: true
  required_approvals: []
  destination:
    tool_alias: ""
    location: ""
    mode: "allowed|approval-required|suggest-only|none"
  recipients:
    resolved: []
    unresolved: []
  notification:
    method: "slack|email|ticket|manual|none"
    approved: false
  prerequisites: []
  artifacts:
    required: []
    generated: []
  notes: []
```

## 决策规则

- 选择最小且有用的下一步行动，而非所有可能的行动。
- 如所需信息缺失，优先 `request_missing_documents`。
- 如须由专家先行审查，优先 `route_for_internal_review`。
- 如需法律变更，优先 `prepare_redline_packet` 或 `revise_contract`。
- 如合同就绪待签署，优先 `prepare_approval_packet` 或 `mark_signature_ready`。

## 输出规则

- 用散文陈述建议的行动。
- 将相同结果保存到机器可读的行动包中。
- 如不允许自动化行动，仍以 `suggest-only` 输出该行动。
