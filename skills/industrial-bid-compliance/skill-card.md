## Description: <br>
工业领域招投标技术方案智能审查，帮助用户对标国家和行业标准生成合规判定、整改建议和交互式报告。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[bettermen](https://clawhub.ai/user/bettermen) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Bid, procurement, compliance, and engineering teams use this skill to review industrial tender technical proposals against applicable legal, safety, environmental, energy-efficiency, quality, acceptance, qualification, and intellectual-property requirements. It is intended to surface compliance gaps and remediation suggestions before users rely on a bid package. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill reads tender documents and may process sensitive commercial or procurement information. <br>
Mitigation: Run it only on documents the user is authorized to share with the agent and keep generated JSON or HTML reports in approved local or organizational storage. <br>
Risk: Legal, standards, and bid-compliance conclusions are advisory and may be incomplete or outdated. <br>
Mitigation: Have qualified procurement, legal, or engineering professionals review critical findings before making bid decisions. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/bettermen/industrial-bid-compliance) <br>
- [bid_compliance_checklist.md](references/bid_compliance_checklist.md) <br>
- [bid_law_essentials.md](references/bid_law_essentials.md) <br>
- [compliance_framework.md](references/compliance_framework.md) <br>
- [industrial_standards_map.md](references/industrial_standards_map.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance plus local JSON and HTML compliance report artifacts] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces clause-level findings, 9-dimension compliance scores, remediation guidance, and interactive HTML reports from user-provided tender documents.] <br>

## Skill Version(s): <br>
1.0.0 (source: evidence.release.version and SKILL.md frontmatter) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
