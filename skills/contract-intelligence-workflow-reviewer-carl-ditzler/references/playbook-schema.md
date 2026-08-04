# 剧本模式

在进行最终审查之前，将每个指导来源规范化为单一的、基于条款的剧本。

如果剧本是上传的或从云来源获取的，从保存的 `source.md` 提取进行规范化，并保留回源元数据的链接。

指导来源可包括：

- 正式的法律剧本
- 标准合同模板
- 先前已谈判的协议
- 经批准的底线条款库
- 法律顾问或业务团队的电子邮件指示
- 采购要求
- DPA 或安全立场

## 规范化规则

- 将所有指导合并为一个权威剧本表。
- 如两个来源冲突，注明冲突并识别哪个来源起控制作用。
- 如无正式剧本，从用户的明确目标加上底线最佳实践标准创建临时剧本。
- 区分法律要求、商业偏好和纯起草偏好。
- 不要发明未提供的内部立场。有疑问时，将该条款标记为需要确认。

## 条款记录模式

使用以下模式为每个条款族创建一条记录：

```yaml
playbook_clause:
  clause_family: ""
  clause_variants: []
  priority_level: "critical|high|medium|low"
  business_owner: ""
  legal_owner: ""
  preferred_position: ""
  acceptable_fallback: ""
  last_resort_position: ""
  prohibited_terms: []
  rationale:
    legal: ""
    commercial: ""
    operational: ""
  approval_trigger: []
  specialist_review_trigger: []
  negotiation_notes: []
  sample_redline: ""
  counterparty_explanation: ""
  jurisdiction_notes: []
  dependencies: []
  comparison_basis: "playbook|template|prior_deal|fallback_best_practice"
```

## 强制条款族

适用时涵盖以下条款族：

- 当事人、关联公司、定义和优先顺序
- 范围、服务、交付物、验收、变更单
- 费用、付款条款、税费、信用额、费用控制
- 期限、续约、中止、终止、过渡
- 保密、残留、公开、名称使用
- 数据使用、DPA、安全、事件通知、次级处理者、AI 或模型训练、数据位置
- 知识产权所有权、许可授予、反馈、定制工作成果、开源
- 陈述、保证、免责声明、SLA、支持、服务水平
- 赔偿与抗辩控制
- 责任限制与损害除外
- 保险
- 审计权、记录、基准、最惠国、最优惠定价
- 合规、制裁、反贿赂、可访问性、行业特定要求
- 转让、控制权变更、分包
- 准据法、审判地、争议解决、禁令救济
- 完整协议、修订、弃权、通知、不可抗力

## 比较输出

对每个条款族，使用以下之一将合同对照剧本分类：

- `aligned`（一致）
- `acceptable fallback`（可接受的底线）
- `needs revision`（需要修订）
- `deal blocker`（交易障碍）
- `missing from contract`（合同缺失）
- `missing from playbook`（剧本缺失）

当合同是返回的草稿或交易对手的标记版本时，还运行偏差评分工作流，并将结果映射到剧本偏差评分参考中更严格的操作状态值。

## 升级逻辑

如果以下任一情况为真，条款需要升级：

- 合同超出剧本的最后可接受底线。
- 条款影响法律部门以外的部门。
- 指导来源冲突。
- 审查者缺乏足够背景可靠地评估该条款。
- 条款缺失且缺失造成重大风险。

## 临时剧本

如无剧本存在，使用以下内容创建临时剧本：

1. 用户的必须有条款
2. 用户的禁止条款
3. 优先级矩阵中的角色和合同类型优先级
4. 法律审查最佳实践参考中的最佳实践指导

将所得剧本标记为临时，并相应降低置信度。
