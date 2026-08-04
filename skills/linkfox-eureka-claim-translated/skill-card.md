## Description: <br>
Retrieves translated patent claim text from the Eureka patent data platform in Chinese, English, or Japanese using patent IDs or publication numbers. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Patent professionals, researchers, and agents use this skill to retrieve translated claim text for one or more known patents by ID or publication number. It is for claim retrieval and display, not patent search, legal status analysis, or claim interpretation. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers, API credentials, session metadata, and full API responses may be sent to LinkFox services or saved locally. <br>
Mitigation: Use only when this data handling is acceptable, protect API keys, keep LINKFOX_TOOL_GATEWAY pointed at a trusted host, and review saved response files before sharing. <br>
Risk: The server security summary reports automatic feedback reporting, remote onboarding-skill installation, and broad file persistence behavior that users should review. <br>
Mitigation: Review or disable feedback reporting where appropriate, and allow any remote onboarding-skill installation only after explicitly trusting that separate package. <br>
Risk: The server security verdict for this release is suspicious. <br>
Mitigation: Follow the server scan guidance before deployment and run the skill in a controlled workspace with least-privilege credentials. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-eureka-claim-translated) <br>
- [Eureka API Reference](references/api.md) <br>
- [LinkFox API Key Guide](https://skill.linkfox.com/linkfoxskills/guide.htm) <br>


## Skill Output: <br>
**Output Type(s):** [text, JSON, markdown, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with JSON API and script output, including saved JSON response files.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires a LinkFox API key; supports up to 100 patents per request; may consume credits and save full responses locally.] <br>

## Skill Version(s): <br>
1.0.5 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
