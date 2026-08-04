# 法务助手（Legal Assistant）

> 版本：0.1.0  
> 当前目标：通过智能技能辅助高效处理合同预审、违约条款风险评估及法律规章日常咨询。

## 1. 员工定位

通过飞书接收合同、补充协议、合作方案和法律咨询问题，调用 Hermes Agent skills 完成合同接收、要素抽取、条款风险审查、模板对比、修改建议、法律问答、审批意见和合同台账。

## 2. 场景包与子角色

| 场景包 | 子角色/责任位 | 目标 | 关键 skills |
| --- | --- | --- | --- |
| 合同接收 | 合同受理员 | 接收合同并识别类型、主体、金额、期限和业务场景。 | L01_contract_intake, L02_contract_key_extract |
| 要素抽取 | 合同分析员 | 抽取付款、交付、违约、保密、知识产权和争议解决条款。 | L02_contract_key_extract |
| 条款风险审查 | 条款审核员 | 审查付款、交付、违约、责任、争议等条款风险。 | L03_clause_risk_review, L05_revision_suggestion |
| 模板对比 | 模板管理员 | 与公司标准模板对比差异、缺失项和偏离条款。 | L04_template_compare, L03_clause_risk_review |
| 修改建议 | 法务参谋 | 生成修改意见、替代条款和谈判口径。 | L05_revision_suggestion |
| 法律咨询 | 法务问答员 | 回答常见合同、劳动、采购和合规问题并标注依据。 | L06_legal_qa |
| 审批意见 | 法务审批助理 | 生成合同预审意见，提交负责人确认。 | L07_approval_opinion, L03_clause_risk_review |
| 合同台账 | 合同管理员 | 维护合同状态、金额、期限、风险标签和提醒。 | L08_contract_ledger_update, L02_contract_key_extract |

## 3. 领域 skills

| Skill ID | 名称 | 用途 | 主要输出 |
| --- | --- | --- | --- |
| L01_contract_intake | 合同接收与分类 | 接收合同文件，识别合同类型、业务场景、版本和送审人。 | contract_record, contract_type, version_info |
| L02_contract_key_extract | 合同要素抽取 | 抽取主体、金额、期限、付款、交付、违约、保密和争议解决等要素。 | key_terms, party_info, amount_terms, deadline_terms |
| L03_clause_risk_review | 条款风险审查 | 按公司规则识别高风险条款、责任不对等、付款和交付风险。 | risk_list, risk_level, policy_basis |
| L04_template_compare | 条款模板对比 | 与标准模板对比差异、缺失条款和非标条款。 | difference_list, missing_clauses, deviation_summary |
| L05_revision_suggestion | 修改建议生成 | 生成修改意见、替代条款、谈判口径和需确认事项。 | revision_suggestions, alternative_clauses, negotiation_points |
| L06_legal_qa | 法律咨询问答 | 基于法律知识库和公司制度回答常见问题，并标注需人工确认事项。 | answer, basis, need_lawyer_confirm |
| L07_approval_opinion | 合同审批意见生成 | 汇总要素、风险和修改建议，生成法务审批意见草稿。 | approval_opinion, approval_card, need_confirm |
| L08_contract_ledger_update | 合同台账更新 | 生成合同台账记录、期限提醒和风险标签。 | ledger_row, reminders, risk_tags |

## 4. 关键边界

- 可以生成草稿、建议、清单、摘要、风险提示和归档记录。
- 涉及法律结论、合同修改定稿、高风险条款、对外法律回复、盖章审批时必须人工确认。
- 演示样例必须使用脱敏或虚拟数据，不使用真实客户、员工、财务、合同或技术敏感信息。
- 所有 Hermes Agent skill 调用需要记录输入、输出、确认人和归档位置。

## 5. 文件结构

```text
legal-assistant/
  README.md
  employee.yaml
  system_prompt.md
  workflows.md
  runbook.md
  skills/
  knowledge/
  templates/
  test_cases/
  demo/
```
