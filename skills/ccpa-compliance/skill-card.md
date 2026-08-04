## Description: <br>
Checks CCPA/CPRA compliance posture, consumer-rights handling, opt-out mechanisms, and generates local reports for businesses handling California consumer data. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[wwumit](https://clawhub.ai/user/wwumit) <br>

### License/Terms of Use: <br>
MIT <br>


## Use Case: <br>
Developers, privacy teams, and compliance staff use this skill to run local CCPA/CPRA self-checks, assess consumer-rights and opt-out workflows, and draft reports for internal review. <br>

### Deployment Geography for Use: <br>
United States, focused on California CCPA/CPRA obligations <br>

## Known Risks and Mitigations: <br>
Risk: The skill runs local Python code and reads or writes local report files. <br>
Mitigation: Run it only in directories where the skill artifact and sibling compliance_core module are trusted, and review generated files before relying on them. <br>
Risk: Compliance reports may be incomplete or unsuitable as legal advice. <br>
Mitigation: Treat output as an internal self-check aid and consult qualified counsel for material CCPA/CPRA decisions. <br>
Risk: Sensitive production data may be included in local checks or reports. <br>
Mitigation: Avoid sensitive production data unless local file reads and report writes are acceptable for the environment. <br>


## Reference(s): <br>
- [CCPA Compliance on ClawHub](https://clawhub.ai/wwumit/skills/ccpa-compliance) <br>
- [CCPA/CPRA law reference](references/ccpa-law.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [CLI guidance and locally generated text, JSON, Markdown, HTML, or CSV reports] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Runs local Python scripts; generated compliance output is a starting point for review, not legal advice.] <br>

## Skill Version(s): <br>
1.0.5 (source: server release metadata, README.md, package.json) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
