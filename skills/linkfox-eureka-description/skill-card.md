## Description: <br>
Retrieves patent description and specification data from the Eureka patent data platform by patent ID or publication number. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and patent research workflows use this skill to retrieve full patent description text for one or more known patent IDs or publication numbers. It is useful when the user already has identifiers and needs faithful patent specification content rather than keyword search, legal-status analysis, or infringement guidance. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: LinkFox receives patent query data, API-key authenticated requests, and session metadata headers. <br>
Mitigation: Verify the gateway configuration before use and avoid submitting confidential patent identifiers unless sharing them with LinkFox is intended. <br>
Risk: The skill reports feedback through a separate LinkFox feedback API. <br>
Mitigation: Review or disable workflows that report feedback without asking the user first. <br>
Risk: Patent responses and cache entries are persisted locally under LinkFox session storage. <br>
Mitigation: Review the generated response files and cache retention practices before using the skill with sensitive patent data. <br>
Risk: Authentication or credit failures can lead to guidance for installing a separate onboarding skill. <br>
Mitigation: Review and approve any separate onboarding skill installation before following that workflow. <br>


## Reference(s): <br>
- [Eureka patent description API reference](artifact/references/api.md) <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-eureka-description) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, configuration, guidance, JSON] <br>
**Output Format:** [Markdown guidance with JSON API responses and local JSON response files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires LinkFox API credentials; queries consume credits; full responses are saved to local LinkFox session data and repeated parameter sets may use a 24-hour cache.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
