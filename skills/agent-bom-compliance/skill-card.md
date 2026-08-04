## Description: <br>
AI compliance and policy engine that evaluates scan results against OWASP, NIST, SOC 2, ISO 27001, CMMC, EU AI Act, AISVS v1.0, and related frameworks, then generates SBOMs and compliance reports. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[msaad00](https://clawhub.ai/user/msaad00) <br>

### License/Terms of Use: <br>
Apache-2.0 <br>


## Use Case: <br>
Developers, security engineers, and compliance teams use this skill to evaluate AI infrastructure scan results, enforce policy checks, generate SBOMs, and produce compliance reports for common security and regulatory frameworks. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Optional CIS benchmark checks can read cloud or Snowflake configuration data using locally configured credentials. <br>
Mitigation: Confirm the target account before running CIS checks and use only operator-configured credentials with read-only access where possible. <br>
Risk: Generated compliance reports or SBOMs may write local output files when requested. <br>
Mitigation: Choose output locations deliberately and review generated files before sharing them outside the working environment. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/msaad00/skills/agent-bom-compliance) <br>
- [Project homepage](https://github.com/msaad00/agent-bom) <br>
- [PyPI package](https://pypi.org/project/agent-bom/) <br>
- [OpenSSF Scorecard](https://securityscorecards.dev/viewer/?uri=github.com/msaad00/agent-bom) <br>


## Skill Output: <br>
**Output Type(s):** [guidance, markdown, code, shell commands, configuration] <br>
**Output Format:** [Markdown with inline commands and structured report or SBOM outputs when requested] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May produce local report or SBOM files when the operator explicitly requests generated outputs.] <br>

## Skill Version(s): <br>
0.97.2 (source: frontmatter and server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
