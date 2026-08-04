# 自动化指标

使用本文件跟踪工作流效率和瓶颈。

## 目的

该技能应有助于减少人工工作和合同周期时间。跟踪指标，使反复出现的摩擦变得可见。

## 推荐指标

- 合同开启时间
- 受理完成时间
- 审查开始时间
- 红线稿准备时间
- 批准包准备时间
- 达到可签署状态时间
- 结案时间
- 缺失文件数量
- 阻碍项数量
- 关键问题数量
- 所需批准数量
- 外部依赖数量

## 指标文件

使用以下内容保存 `metrics.yaml`：

```yaml
metrics:
  contract_opened_at: ""
  intake_completed_at: ""
  review_started_at: ""
  redline_prepared_at: ""
  approval_packet_prepared_at: ""
  signature_ready_at: ""
  closed_at: ""
  missing_document_count: 0
  blocker_count: 0
  critical_issue_count: 0
  required_approval_count: 0
  external_dependency_count: 0
  notes: []
```

## 使用

- 在每个主要工作流阶段更新指标。
- 如瓶颈对时间或执行产生实质影响，在最终摘要中提及主要瓶颈。
