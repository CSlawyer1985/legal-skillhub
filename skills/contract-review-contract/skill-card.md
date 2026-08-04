## Description: <br>
AI合同智能审查助手 reviews pasted, uploaded, or linked contract text; scores risk across nine dimensions; suggests clause revisions and negotiation strategy; cites legal references; and produces an interactive HTML review report for common Chinese contract types. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[bettermen](https://clawhub.ai/user/bettermen) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Legal, procurement, HR, operations, and business users can use this skill for AI-assisted first-pass review of contracts, including risk triage, clause improvement suggestions, legal-reference lookup, and negotiation preparation. The output is advisory and should be reviewed by qualified counsel for important contracts. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill processes sensitive contract text and local contract files. <br>
Mitigation: Use it only with documents appropriate for the agent environment, avoid privileged or highly confidential contracts unless network access is disabled, and delete or secure generated reports after review. <br>
Risk: The generated HTML report may contact external resources. <br>
Mitigation: Open reports in a restricted or offline environment when reviewing confidential contracts, or replace external assets with vetted local copies before sharing. <br>
Risk: AI-generated legal review can be incomplete or incorrect. <br>
Mitigation: Treat findings as first-pass triage and have qualified counsel verify important legal conclusions, statutory references, and proposed clause changes. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/bettermen/contract-ai-review) <br>
- [Publisher Profile](https://clawhub.ai/user/bettermen) <br>
- [Project Homepage](https://github.com/bettermen/contract-review) <br>
- [通用合同审查清单](references/checklist_general.md) <br>
- [买卖合同审查清单](references/checklist_sales.md) <br>
- [劳动用工合同审查清单](references/checklist_labor.md) <br>
- [租赁合同审查清单](references/checklist_lease.md) <br>
- [服务合同审查清单](references/checklist_service.md) <br>
- [保密协议审查清单](references/checklist_nda.md) <br>
- [投资协议审查清单](references/checklist_investment.md) <br>
- [建设工程合同审查清单](references/checklist_construction.md) <br>
- [技术开发合同审查清单](references/checklist_tech_dev.md) <br>
- [法律条款引用库](references/law_reference.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown summary plus generated HTML report file] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May extract text from txt, docx, or pdf files and write contract-review-report.html in the workspace.] <br>

## Skill Version(s): <br>
1.0.0 (source: release evidence and SKILL.md frontmatter) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
