## Description: <br>
Organizes legal intake materials into facts, dispute points, known evidence, missing materials, follow-up questions, and risk notes without providing legal conclusions. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[52YuanChangXing](https://clawhub.ai/user/52YuanChangXing) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Legal operations teams, intake coordinators, and legal reviewers use this skill to turn case intake notes, timelines, and existing documents into a structured, reviewable Markdown brief. It is intended for organizing materials and identifying missing information, not for legal advice or replacing attorney review. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The bundled script can inspect local files or directories and produce reports beyond simple legal intake summarization. <br>
Mitigation: Run it only on a narrow copied test folder or specific intake file, and avoid pointing it at full case repositories, home directories, or broad document stores. <br>
Risk: Generated reports may include privileged, confidential, personal, or secret material from the supplied input. <br>
Mitigation: Review and redact outputs before sharing them, and avoid using sensitive source material unless the deployment environment is approved for that data. <br>
Risk: The skill organizes legal matter information but may be mistaken for legal advice. <br>
Mitigation: Use the output as a review draft and checklist only, and require qualified legal review before relying on conclusions or taking action. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/52YuanChangXing/legal-matter-intake-summarizer) <br>
- [Publisher profile](https://clawhub.ai/user/52YuanChangXing) <br>
- [README](artifact/README.md) <br>
- [Output specification](artifact/resources/spec.json) <br>
- [Output template](artifact/resources/template.md) <br>


## Skill Output: <br>
**Output Type(s):** [analysis, markdown, json, shell commands, files, guidance] <br>
**Output Format:** [Structured Markdown by default, with optional JSON report output when the local script is run with --format json.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [The local script can write an output file, run in dry-run mode, and limit sampled findings for supported audit-style modes.] <br>

## Skill Version(s): <br>
1.0.0 (source: frontmatter and server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
