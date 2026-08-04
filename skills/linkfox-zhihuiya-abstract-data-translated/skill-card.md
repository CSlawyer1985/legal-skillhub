## Description: <br>
Retrieves translated patent titles and abstracts from Zhihuiya (PatSnap) by patent ID or publication number, supporting Chinese, English, and Japanese. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and agent operators use this skill to retrieve translated patent titles and abstracts for known patent IDs or publication numbers. It supports batch lookup and optional family-patent abstract fallback, but it is not a keyword patent search or full-text patent retrieval tool. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers and request context are sent to LinkFox/PatSnap using a LinkFox API key. <br>
Mitigation: Use only with patent identifiers and task context approved for that external service, and protect LinkFox API keys as secrets. <br>
Risk: Full API responses are retained in local LinkFox cache and session data folders. <br>
Mitigation: Review local retention expectations, restrict workspace access, and delete cache or session outputs when they are no longer needed. <br>
Risk: The skill includes automatic feedback reporting behavior to a separate LinkFox Feedback API. <br>
Mitigation: Review or disable feedback behavior before using the skill in sensitive or controlled environments. <br>
Risk: Authentication remediation may direct the agent to download and install a LinkFox onboarding skill. <br>
Mitigation: Require explicit user approval for downloads and review any downloaded skill before installation or use. <br>
Risk: Batch patent lookups can consume LinkFox credits proportional to returned records. <br>
Mitigation: Confirm batch size and expected credit use with the user before making additional or repeated requests. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-abstract-data-translated) <br>
- [API reference](artifact/references/api.md) <br>
- [LinkFox API key guide](https://skill.linkfox.com/linkfoxskills/guide.htm) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, JSON, Shell commands, Configuration, Guidance] <br>
**Output Format:** [Markdown guidance with JSON API responses and saved JSON response files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Uses a LinkFox API key, may consume LinkFox credits, caches matching requests for 24 hours, and persists full API responses in local LinkFox session data folders.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
