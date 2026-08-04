## Description: <br>
Extract & classify key clauses from contract PDFs into a structured risk summary -- with bilingual (CN/EN) support. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[harrylabsj](https://clawhub.ai/user/harrylabsj) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users, legal operations teams, and developers can use this skill to extract contract clauses, classify them into standard categories, compare agreements, and produce bilingual risk summaries for human review. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill presents mock contract-analysis output as real legal risk extraction. <br>
Mitigation: Treat it as a scaffold or demo unless the publisher replaces canned outputs with document-derived parsing and clearly labels confidence and limitations. <br>
Risk: Contract summaries, translations, risk scores, and negotiation suggestions may be mistaken for legal advice. <br>
Mitigation: Require qualified legal review before contractual decisions and keep the automated-extraction disclaimer visible in generated reports. <br>


## Reference(s): <br>
- [Contract Clause Risk Categories](references/risk-categories.json) <br>
- [Input Schema](schemas/input.schema.json) <br>
- [Output Schema](schemas/output.schema.json) <br>
- [ClawHub Skill Page](https://clawhub.ai/harrylabsj/contract-clause-extractor) <br>
- [OpenClaw Input Schema](https://openclaw.dev/skills/contract-clause-extractor/input.schema.json) <br>
- [OpenClaw Output Schema](https://openclaw.dev/skills/contract-clause-extractor/output.schema.json) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, JSON, Shell commands, Guidance] <br>
**Output Format:** [Markdown reports, structured JSON-compatible summaries, bilingual tables, and shell command output] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Outputs should include a legal-advice disclaimer and should be reviewed before use on real agreements.] <br>

## Skill Version(s): <br>
1.0.0 (source: frontmatter, skill.json, release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
