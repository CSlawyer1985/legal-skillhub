# 文件系统工作流

本文件定义合同审查工作的可复用磁盘结构。

## 工作区结构

在活动工作区中使用此结构：

```text
.contract-review/
  config.yaml
  connectors.yaml
  workflow-tools.yaml
  approvals.yaml
  memory-policy.yaml
  playbooks/
    <剧本简称>/
      metadata.yaml
      source.md
      normalized.yaml
  contracts/
    <合同简称>/
      contract.yaml
      intake.yaml
      document-map.md
      playbook.normalized.yaml
      playbook-comparison.csv
      priority-profile.yaml
      workflow-state.yaml
      issues.csv
      redlines.md
      negotiation-plan.md
      approval-routing.md
      approval-routing.json
      action-packet.yaml
      review-summary.json
      research-notes.md
      drafting-output.md
      metrics.yaml
      qa-report.md
```

## 事实来源

- 全局可复用设置位于 `.contract-review/`。
- 可复用的剧本工件位于 `.contract-review/playbooks/` 下。
- 合同特定的事实仅存在于该合同文件夹中。
- `CLAUDE.md` 是简洁镜像，而非记录系统。

## 合同文件夹规则

在以下情形创建合同文件夹：

- 合同审查实际开始时
- 用户要求保存审查
- 审查需要跨会话可恢复

建议的简称格式：

`YYYY-MM-DD-对方-合同类型-短名称`

## 剧本文件夹规则

在以下情形创建剧本文件夹：

- 用户上传剧本文件
- 用户连接已批准的云剧本文件
- 需要将新的控制性剧本归一化以供复用

建议的简称格式：

`团队或公司-剧本-短名称`

## 必需的剧本文件

### `metadata.yaml`

来源溯源、提取方法、来源格式和提取置信度。

### `source.md`

剧本的可读 Markdown 提取，供模型使用和人工验证。

### `normalized.yaml`

用于比较和评分的规范结构化剧本。

## 必需的合同文件

### `contract.yaml`

高层级合同元数据：

- 合同名称
- 对方
- 所代表方
- 合同类型
- 审查模式
- 状态
- 文档位置

### `intake.yaml`

受理表的归一化受理记录。

### `document-map.md`

协议标题、当事方、附件、被引用的外部文档、缺失文档和关键结构说明。

### `playbook.normalized.yaml`

用于本合同合并后的条款剧本。

### `playbook-comparison.csv`

逐条款剧本比较，含状态、偏离评分、影响带、颜色标签、可能影响和置信度。

### `priority-profile.yaml`

最高优先事项、角色调整和所需内部审查人。

### `issues.csv`

结构化问题日志，每个问题一行。

### `redlines.md`

首选编辑和备用措辞。

### `negotiation-plan.md`

必赢问题、可交易项、谈判筹码说明和对方理由。

### `approval-routing.md`

哪些职能必须审查或批准及原因。

### `approval-routing.json`

供自动化使用的机器可读格式的同一审批路由，包括具名批准人、联系路径、通知方式和未解决收件人。

### `workflow-state.yaml`

当前生命周期状态、先前状态、允许的转换、阻塞器清单和下一状态建议。

### `action-packet.yaml`

供工作流自动化使用的机器可读下一步负载。

### `review-summary.json`

当前审查结果、阻塞器和下一步行动的结构化摘要。

### `research-notes.md`

使用研究模式时按条款的研究输出。

### `drafting-output.md`

使用起草模式时的合同起草、审批备忘录、邮件草稿或摘要交付物。

### `metrics.yaml`

合同的周期时间和工作流指标。

### `qa-report.md`

失败模式结果、QA 判定和基准摘要。

## 写入规则

- 全局配置新建或变更时在设置后保存。
- 剧本上传、获取或重新归一化时保存剧本工件。
- 启用合同跟踪时在受理后保存。
- 在审查后、谈判规划后和 QA 后再次保存。
- 不写入用户选择退出生成的文件。
- 除非用户允许本地副本，不将获取或上传的合同写入磁盘。
- 合同结案时，按照已保存的内存和保留策略审查合同特定工件应保留还是删除。

## 恢复规则

在后续会话中：

1. 加载 `.contract-review/config.yaml`
2. 如存在相关合同文件夹则加载
3. 仅询问缺失的更新
4. 从最近保存的阶段继续工作流

## `issues.csv` 的最小 CSV 列

使用以下列：

```text
clause_reference,status,risk,issue_summary,why_it_matters,recommended_position,suggested_redline,acceptable_fallback,approver_or_reviewer,confidence,notes
```

## `playbook-comparison.csv` 的最小 CSV 列

使用以下列：

```text
clause_reference,playbook_status,deviation_score,impact_band,color_label,likely_impact,why_it_matters,recommended_response,confidence,notes
```
