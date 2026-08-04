# 受理表

在审查合同之前完成本表。不要跳过可能实质性改变审查的字段。

如果用户尚未提供合同，停下并索取。请用户上传文件或分享 Dropbox、Google Drive、OneDrive、SharePoint、Box 或其他可访问云盘等链接。

## 文件请求

预先索取以下材料：

- 待审查的合同
- 清洁版、红线版或两者
- 所有附件、附表、附录、订购表、工作说明书、政策和以引用方式并入的 URL
- 公司手册、条款库、底线立场或标准文本
- 可比较的先前协议或先前已谈判的格式
- 相关 DPA、安全附录、安全措施、支持政策、SLA、AI 条款或 AI 附录、订购表、定价表或保险要求
- 相关邮件指引、工单说明或业务指示

## 必答问题

提出并将答案规范化：

1. 应审查哪份合同，哪份文档版本当前控制该交易？
2. 提出审查请求的用户是谁，其角色或职能是什么？
3. 你代表哪一方？
4. 这是本方文本还是对方文本？
5. 这是什么类型的合同？
6. 业务目标或交易目的是什么？
7. 商业事实是什么：合同价值、付款模式、期限、续约、终止时点、排他性和关键交付物？
8. 合同在哪个业务区域履行：AMER、APAC、EMEA 还是多区域？
9. 合同是否涉及个人数据、安全承诺、AI 使用、保密信息、受监管数据或跨境转移？
10. 哪些司法辖区对准据法、审判地、数据转移或合规具有重要性？
10A. 交易是否通过当事方、客户、受监管运营、服务、托管或范围内关联公司具有欧盟或欧洲经济区联系？
11. 如果被代表方是客户，客户属于哪个部门或行业？
12. 另一方属于哪个行业？
13. 服务或产品是云产品还是云赋能服务？
14. 如果客户是美国的医疗保健提供者或医疗保健服务组织，是否传输、处理或存储 PHI（受保护健康信息）？
15. 签署的时间表是什么，哪些问题是真正的障碍？
16. 用户的风险承受度：激进、平衡还是促成交易？
17. 是否有必须审查或批准的内部利益相关方？示例：财务、安全、隐私、采购、产品、销售、保险、合规、高管发起人。如已知，提供具体批准人姓名和联系途径，或确认应使用保存的默认批准人映射。
18. 是否有必须有的立场、禁止条款或先前已谈判的妥协应主导本次审查？

## 先读规则

如果用户已提供合同供审查，先读合同，再问可避免的受理问题。

在可能的情况下，先从合同本身推断这些答案：

- 问题 1：审查的是哪份合同，哪个版本似乎起控制作用
- 问题 5：这是什么类型的合同

如果读完合同后任一答案仍不清楚，向用户提出简短有针对性的追问，而不是猜测。

## 受理规范化模式

使用以下模式以结构化块记录答案：

```yaml
intake:
  document_set:
    contract: ""
    version_status: "clean|redline|both|unknown"
    exhibits_received: []
    referenced_external_docs: []
    comparison_docs: []
  user:
    user_identity: ""
    represented_party: ""
    user_role: ""
    internal_business_owner: ""
    counterparty: ""
    paper_owner: "first_party|third_party|mixed|unknown"
  contract_profile:
    contract_type: ""
    subtype: ""
    business_region: "AMER|APAC|EMEA|multi|unknown"
    jurisdictions: []
    term: ""
    renewal_model: ""
    signature_deadline: ""
    customer_industry: ""
    other_party_industry: ""
    cloud_service: "yes|no|mixed|unknown"
  commercial_context:
    deal_value: ""
    pricing_model: ""
    deliverables_or_scope: ""
    critical_deadlines: []
    business_goal: ""
  data_and_regulatory:
    personal_data: "yes|no|unknown"
    security_sensitive: "yes|no|unknown"
    ai_or_model_use: "yes|no|unknown"
    regulated_industry: []
    cross_border_data: "yes|no|unknown"
    eu_or_eea_nexus: "yes|no|unknown"
    us_healthcare_customer: "yes|no|unknown"
    phi_in_scope: "yes|no|unknown"
    baa_required: "yes|no|unknown"
    emea_financial_cloud_addendum_required: "yes|no|unknown"
    dora_review_required: "yes|no|unknown"
  negotiation_posture:
    risk_tolerance: "aggressive|balanced|close-the-deal|unknown"
    must_have_terms: []
    prohibited_terms: []
    priority_concerns: []
  approval_map:
    finance: "required|optional|no"
    security: "required|optional|no"
    privacy: "required|optional|no"
    procurement: "required|optional|no"
    product: "required|optional|no"
    compliance: "required|optional|no"
    insurance: "required|optional|no"
    exec: "required|optional|no"
    named_approvers: []
  constraints_and_gaps:
    missing_documents: []
    unanswered_questions: []
    assumptions_allowed: []
```

## 自动监管与附属文件检查

明确设定这些规则：

- 如果客户是美国的医疗保健提供者或医疗保健服务组织，且传输、处理或存储 PHI，则要求签订 BAA（业务伙伴协议）。
- 如果交易具有欧盟或欧洲经济区联系，进行 DORA 适用性筛查。如果交易涉及为欧盟或欧洲经济区金融部门或保险客户提供的 ICT 或云服务，或以其他方式似乎支持受监管金融实体的关键或重要职能，则进行 DORA 审查并检查是否符合 DORA 的合同条款。
- 如果客户在 EMEA，客户行业为保险或金融服务，营业地为欧洲，且产品为云服务，则要求包含审计、安全和退出条款的增强型金融云合同附表或附录。
- 始终检查是否包含或以引用方式并入 SLA、安全措施或安全附表以及 AI 条款。

## 受理最低要求

除非已知以下最低要求，否则不发布最终完整审查：

- 合同文本或可靠文件
- 被代表方
- 用户角色或等效职能
- 合同类型

如果其中一项最低要求缺失，在分析前索取。

## 回退规则

如果非关键字段缺失：

- 提问。
- 如用户无法回答，以最不激进的假设继续。
- 清晰标注该假设。
- 在风险评分、建议和批准路由中反映该不确定性。

如果关键比较文件缺失：

- 以回退审查模式继续。
- 识别一旦提供缺失文件后哪些发现可能变化。

## 受理完成检查

在进入手册规范化之前，确认：

- 已识别起控制作用的协议版本。
- 已列出缺失材料。
- 用户的角色和被代表方已明确。
- 已选择审查模式。
- 批准映射要么指定合同特定批准人，要么确认保存的默认值适用。
