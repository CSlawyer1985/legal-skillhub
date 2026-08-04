## Description: <br>
Global compliance checker and data localization audit tool for Chinese products expanding overseas, with checklists, a CLI/API-backed regulations lookup, and structured GDPR, CCPA, AI Act, App Store, and China outbound data transfer assessment guidance. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[lm203688](https://clawhub.ai/user/lm203688) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External teams, product leaders, compliance reviewers, and developers use this skill to structure pre-launch compliance checks for Chinese apps, SaaS products, and digital services entering overseas markets. It helps identify likely privacy, payment, content moderation, app store, AI, and cross-border data transfer requirements before launch. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill provides high-level legal and compliance guidance whose claims are broader than the bundled implementation can independently verify. <br>
Mitigation: Treat outputs as a checklist and planning aid, verify current requirements for each jurisdiction, and consult qualified legal counsel before launch decisions. <br>
Risk: The bundled regulations helper script contacts an external API endpoint. <br>
Mitigation: Avoid sending sensitive product details to the endpoint unless the service is trusted and approved for the data being shared. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/lm203688/cn-global-compliance) <br>
- [Compliance checklist](references/compliance-checklist.md) <br>
- [Regulations API endpoint](https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, JSON, shell commands, guidance] <br>
**Output Format:** [Markdown reports and checklist guidance, with optional JSON output from the bundled compliance check script and shell commands for regulations lookup.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May call an external API endpoint for regulations lookup through the bundled shell script.] <br>

## Skill Version(s): <br>
2.3.0 (source: release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
