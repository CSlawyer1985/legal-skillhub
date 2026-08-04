## Description: <br>
Organizes audit evidence into catalogs, control mappings, missing-evidence lists, naming suggestions, priorities, and delivery recommendations for later review. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[52YuanChangXing](https://clawhub.ai/user/52YuanChangXing) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Compliance, audit, and governance practitioners use this skill to turn evidence folders, control lists, or scenario notes into reviewable evidence packages and gap lists. It supports audit preparation, evidence archiving, and control proof workflows without replacing formal audit conclusions. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Broad local audits can read files and report sensitive matches from the selected directory. <br>
Mitigation: Run the skill only on deliberately chosen directories, review outputs before sharing them, and avoid repositories or evidence folders that may contain secrets unless redaction is added and scan scope is clearly disclosed. <br>
Risk: The skill can organize gaps and recommendations but does not provide formal audit conclusions. <br>
Mitigation: Use outputs as review drafts and have qualified reviewers confirm evidence completeness, control mapping, and final audit conclusions. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/52YuanChangXing/compliance-evidence-assembler) <br>
- [Publisher profile](https://clawhub.ai/user/52YuanChangXing) <br>
- [Skill specification](artifact/resources/spec.json) <br>
- [Output template](artifact/resources/template.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown or JSON report] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Structured sections cover evidence overview, control mapping, missing evidence, naming suggestions, prioritization, delivery recommendations, and items needing confirmation.] <br>

## Skill Version(s): <br>
1.0.0 (source: release evidence and SKILL.md frontmatter) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
