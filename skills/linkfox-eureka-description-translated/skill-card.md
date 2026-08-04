## Description: <br>
Retrieves translated patent description or specification text from the Eureka patent data platform in Chinese, English, or Japanese using a patent ID or publication number. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users, patent professionals, and developers use this skill to retrieve translated patent specification text for known patent IDs or publication numbers. It is suited to single or batch patent-description translation requests, including optional family-member substitution when the requested description is unavailable. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent queries and returned descriptions are sent to LinkFox and may be saved locally and cached. <br>
Mitigation: Use only in workspaces appropriate for the data, avoid confidential patent work unless LinkFox handling is acceptable, and review saved output paths before sharing the workspace. <br>
Risk: The skill includes automatic feedback reporting behavior and external onboarding guidance. <br>
Mitigation: Review or disable feedback reporting and separately review any onboarding skill before installing or running it. <br>
Risk: The service consumes credits dynamically and batch requests can create higher costs. <br>
Mitigation: Confirm expected cost with the user before calls, keep batches within the documented limit, and avoid repeated retries after failures or empty results. <br>


## Reference(s): <br>
- [Eureka API reference](references/api.md) <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-eureka-description-translated) <br>
- [LinkFox skill guide](https://skill.linkfox.com/linkfoxskills/guide.htm) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, JSON, shell commands, guidance] <br>
**Output Format:** [Markdown guidance with JSON API responses and locally saved JSON files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Returns translated patent-description records, token cost fields, optional family-member substitution indicators, and summaries for large responses.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
