## Description: <br>
Security and compliance auditing tool for AI agents. Scans code for vulnerabilities, checks GDPR/CCPA compliance, generates risk reports with remediation guidance. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[agent-compliance-org](https://clawhub.ai/user/agent-compliance-org) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers, security reviewers, and compliance teams use this skill to scan AI agent or skill code for common security patterns and privacy/compliance issues before deployment. It produces risk-scored findings and remediation guidance for review. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Static, pattern-based scanning can miss issues or report false positives. <br>
Mitigation: Review findings with qualified security or compliance reviewers before using results for release decisions. <br>
Risk: The skill may need access to local code or project files to perform scans. <br>
Mitigation: Review requested permissions and scope scans to the intended files before installing or running the skill. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/agent-compliance-org/skills/compliance-audit-assistant) <br>


## Skill Output: <br>
**Output Type(s):** [Text, JSON, HTML, Guidance] <br>
**Output Format:** [Risk-scored audit report with findings and remediation guidance; output may be text, JSON, or HTML.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Static, pattern-based analysis with configurable language, strict_mode, exclude_patterns, and output_format options.] <br>

## Skill Version(s): <br>
1.0.0 (source: release evidence and artifact version history) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
