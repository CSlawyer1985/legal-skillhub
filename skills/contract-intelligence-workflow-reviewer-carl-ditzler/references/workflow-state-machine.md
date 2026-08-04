# 工作流状态机

使用本文件跟踪合同在生命周期中的位置以及适当的状态转换。

## 状态

- `setup`（设置）
- `intake`（接入）
- `triage`（分诊）
- `review`（审查）
- `redline`（红线）
- `negotiation`（谈判）
- `internal_approvals`（内部审批）
- `signature_ready`（可签署）
- `closed`（已关闭）

## 状态含义

- `setup`：全局工作区配置仍缺失或不完整
- `intake`：正在收集文件（document）和业务语境
- `triage`：正在进行有限的首次筛查
- `review`：实质性条款分析进行中
- `redline`：正在准备起草修订或退路措辞
- `negotiation`：正在管理未决问题和退路立场
- `internal_approvals`：合同在等待法律或业务审批
- `signature_ready`：障碍已清除，文件包已可执行
- `closed`：审查工作流已完成

## 允许的转换

- `setup -> intake`
- `intake -> triage`
- `intake -> review`
- `triage -> intake`
- `triage -> review`
- `review -> redline`
- `review -> internal_approvals`
- `redline -> negotiation`
- `redline -> internal_approvals`
- `negotiation -> redline`
- `negotiation -> internal_approvals`
- `internal_approvals -> redline`
- `internal_approvals -> signature_ready`
- `signature_ready -> closed`

## 状态更新规则

- 在接入最低要求满足前，不要移至 `review`。
- 在优先级模型应用前，不要移至 `redline`。
- 在审批表构建前，不要移至 `internal_approvals`。
- 如有未解决的阻塞审批或重大未解决问题，不要移至 `signature_ready`。
- 如用户仅想要对不完整输入的摘要，保持在 `triage`。

## 必需的工作流状态文件

用以下内容保存 `workflow-state.yaml`：

```yaml
workflow_state:
  current_state: ""
  previous_state: ""
  recommended_next_state: ""
  blockers: []
  rationale: []
  last_updated_stage: ""
```
