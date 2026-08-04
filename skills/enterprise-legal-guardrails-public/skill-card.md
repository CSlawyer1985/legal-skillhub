## Description: <br>
Legal/compliance guardrails for outbound OpenClaw actions, including anti-spam, defamation, privacy, and financial-claim checks. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[lawyered0](https://clawhub.ai/user/lawyered0) <br>

### License/Terms of Use: <br>


## Use Case: <br>
Developers and operators use this skill to preflight outbound bot content before posting, messaging, publishing, or running outbound commands that may create legal or compliance risk. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The outbound wrapper can run commands after a guardrail check, and review-worthy content may proceed unless strict mode is enabled. <br>
Mitigation: Use --strict for real sending, posting, trading, or publishing workflows, keep --allowed-command narrow, enable --sanitize-env, and configure audit logs deliberately. <br>
Risk: --allow-any-command bypasses command allow-list enforcement. <br>
Mitigation: Avoid --allow-any-command except for explicitly approved emergency use, and require an approval reason, approval token, and audit trail when it is used. <br>


## Reference(s): <br>
- [Guardrail Policy Map](references/guardrail-policy-map.md) <br>
- [ClawHub Release Page](https://clawhub.ai/lawyered0/enterprise-legal-guardrails-public) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Shell commands, Configuration, Guidance] <br>
**Output Format:** [Plain text decisions, optional JSON, and Markdown with shell command examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Guardrail decisions include PASS, WATCH, REVIEW, and BLOCK; the outbound wrapper can run approved commands after checks.] <br>

## Skill Version(s): <br>
1.0.13 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
