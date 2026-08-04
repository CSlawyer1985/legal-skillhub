# 知识、规则与版本数据结构

## 目录

1. 文书节点
2. 法律规则节点
3. 推理节点
4. 风险节点
5. 版本与状态
6. 要素式诉辩节点
7. 逐诉请要件矩阵

## 1. 文书节点必备字段

每一种文书节点必须包含：

```json
{
  "document_id": "唯一稳定编号",
  "document_name": "文书名称",
  "canonical_name": "便于检索和生成的规范名称",
  "document_role": "party_filing",
  "document_function": "作用",
  "applicable_cases": ["适用案件"],
  "applicable_procedure": ["适用程序"],
  "start_conditions": ["启动条件"],
  "applicant_or_maker": ["申请主体或制作主体"],
  "counterparty_or_recipient": ["相对方或接收人"],
  "competent_court": ["法院"],
  "book_original_basis": ["本书原规定"],
  "current_legal_basis": ["现行法律依据"],
  "legal_update_note": "本书规定与现行规则的变化及影响",
  "judicial_interpretations": ["司法解释"],
  "case_authorities": ["指导性案例或入库案例"],
  "court_focus": ["法院关注重点"],
  "submission_or_making_time": ["提交或制作时间"],
  "burden_of_proof": ["举证责任"],
  "evidence_requirements": ["证据要求"],
  "risk_analysis": ["风险分析"],
  "logical_structure": ["逻辑结构"],
  "smart_template_fields": ["智能模板字段"],
  "court_review_logic": ["法院审查逻辑"],
  "lawyer_writing_tips": ["律师写作技巧"],
  "ai_generation_flow": ["AI生成流程"],
  "automatic_validation_rules": ["自动校验规则"],
  "common_errors": ["常见错误"],
  "excellent_example_policy": "优秀示范生成规则",
  "source_locator": {
    "source_edition": "第二版",
    "volume": "下册",
    "source_file_part": 0,
    "pdf_file_page": 0,
    "scan_global_page": 0,
    "printed_book_page": 0,
    "chapter": ""
  },
  "validation_status": "ocr_lead|book_verified|verified_current|superseded|needs_review",
  "version": "语义版本",
  "effective_from": "YYYY-MM-DD|null",
  "supersedes": "旧节点ID|null"
}
```

空数组不等于已核验。没有找到指导案例时写明“未检得／未核验”，不得编造案例号。

本项目只接收当事人可以制作、签署或提交的文书节点。法院判决书、裁定书、决定书、内部笔录、函件等法院制作样式不进入目录；当事人对法院文书的审查需求作为案件分析能力处理，不建立法院文书模板节点。

## 2. 法律规则节点

每条规则记录：规则编号、规范名称、条号、规则命题、触发事实、例外、法律后果、证明责任、程序期限、效力状态、公布／生效／失效日期、官方来源、核验日期、替代关系、影响的文书节点。

法条号必须与案件适用时点匹配。法律修正造成条号移动时，不得只替换条号而不检查规则内容。

## 3. 推理节点

```text
IF 触发事实全部成立
AND 不存在排除事实
AND 规则在案件时点有效
THEN 推荐／排除某文书
BECAUSE 法律规则与程序目的
ASK 缺失事实
CHECK 期限、法院、证据和替代路径
```

推理节点必须可解释，不用“综合判断”代替要件。

## 4. 风险节点

记录风险事件、触发条件、概率等级、影响等级、可发现证据、缓解动作、最晚行动时间和残余风险。风险提示必须能回指文书或规则节点。

## 5. 版本与状态

- `ocr_lead`：仅由教材 OCR 提取，用于定位，禁止直接作为最终法条引用。
- `book_verified`：已与教材页面人工核对，但未完成现行法核验。
- `verified_current`：已与官方现行来源核对，并记录核验日期。
- `superseded`：已被新规则替代，保留历史和替代指针。
- `needs_review`：存在 OCR、冲突、适用时点或官方来源问题。

版本号建议：知识结构重大变化升主版本；规则含义或模板逻辑变化升次版本；错字、链接和定位修正升补丁版本。

## 6. 要素式诉辩节点

`element-pleading-knowledge.json`中的每个`ELM`节点代表一种纠纷的双向诉辩系统，不是教材模板副本。必备字段包括：

```text
node_id、dispute_type、book_model_name、current_model_name
source_locator、book_model_status、current_norm、change_record
document_variants[plaintiff, defendant]
legal_basis、burden_of_proof
claim_elements、fact_questions、evidence_requirements
court_review_focus、calculation_rules、logic_structure
ai_generation_flow、automatic_checks
common_omissions、common_errors、lawyer_writing_tips
risk_analysis、excellent_example_rule、catalog_links
```

状态`superseded_methodology_retained`只表示教材的分析方法可保留；绝不表示2024年试行表格继续有效。每个节点必须路由`NORM-PLEADING-2025`，并与相应的4个`APPX`历史节点连接。

## 7. 逐诉请要件矩阵

`element-pleading-claim-matrix.json`把11类纠纷进一步拆成63个`claim_id`。每项必须包含：

```text
request_name、relief_type、branch
elements[]
fact_questions[question_id, prompt, blocking]
evidence_groups[evidence_id, group, required_or_explain_absence]
defense_paths[]
court_review_checks[]
calculation_rule
conflicts_with[]
legal_route_ids[]
source_guide_pages
article_verification_required
```

事实问题和证据组使用稳定ID，供案件信息收集、缺口审计和后续文书生成回溯。`article_verification_required=true`表示教材要件已蒸馏，但具体案件仍须核对现行条号、适用时点和例外。
