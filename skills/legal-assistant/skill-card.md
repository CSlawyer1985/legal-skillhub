## Description: <br>
法务助手（Legal Assistant）协助完成合同接收分类、合同要素抽取、条款风险审查、模板对比、修改建议生成、法律咨询问答、审批意见草拟与合同台账更新的完整合同与法务闭环。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[afeicn](https://clawhub.ai/user/afeicn) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Legal, sales, procurement, project, and management users use this skill to triage contracts and legal questions, extract key terms, identify clause risks, compare templates, draft revisions and approval notes, and maintain contract ledger records. It supports drafting and review workflows while keeping final legal decisions and external commitments with authorized human reviewers. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Legal conclusions, external commitments, contract finalization, and seal or approval workflows may be inappropriate without authorized review. <br>
Mitigation: Keep human approval for legal conclusions, external commitments, contract finalization, and seal or approval workflows. <br>
Risk: Contract, employee, customer, financial, or other sensitive information may be exposed if permissions are too broad. <br>
Mitigation: Before installing, limit Feishu bot, Hermes Agent, archive, knowledge base, and contract ledger permissions to authorized legal and business users. <br>
Risk: Drafting, extraction, and review support may be mistaken for final legal advice. <br>
Mitigation: Use the skill for drafting, extraction, and review support only, and require human confirmation for final legal judgments and high-risk contract actions. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/afeicn/legal-assistant) <br>
- [法务助手 README](README.md) <br>
- [法务助手 Workflows](workflows.md) <br>
- [法务助手 Runbook](runbook.md) <br>
- [Legal skills catalog](skills/legal_skills.yaml) <br>
- [Knowledge base README](knowledge/README.md) <br>
- [Output templates README](templates/README.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, configuration, guidance] <br>
**Output Format:** [Structured Markdown with tables, checklists, draft legal review text, and configuration records] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Outputs emphasize conclusions, key facts, risks or gaps, recommended actions, human-confirmation items, and archive records.] <br>

## Skill Version(s): <br>
0.1.0 (source: server release evidence and README) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
