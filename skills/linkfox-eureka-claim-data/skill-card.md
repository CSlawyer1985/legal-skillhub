## Description: <br>
Queries the Eureka patent database for patent claim text, claim counts, and related-patent fallback data for one or more patent identifiers. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Patent researchers, legal professionals, and agents use this skill to retrieve full patent claims, claim counts, and related-patent fallback data from Eureka when a user provides patent IDs or publication numbers. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers, API credentials, runtime metadata, and possible feedback content may be sent to LinkFox services. <br>
Mitigation: Install and use the skill only when this data sharing is acceptable, and review configured environment variables and feedback behavior before use. <br>
Risk: The skill can persist full API results and cache files locally. <br>
Mitigation: Run it only in workspaces where local LinkFox output paths are acceptable, and manage or remove stored result files according to the user's data retention requirements. <br>
Risk: Authentication or credit handling may direct the agent toward external onboarding resources or downloads. <br>
Mitigation: Require user approval before downloading or installing onboarding materials, and prefer already trusted account setup paths. <br>


## Reference(s): <br>
- [Eureka claim data API reference](references/api.md) <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-eureka-claim-data) <br>


## Skill Output: <br>
**Output Type(s):** [JSON, Markdown, Files, Guidance] <br>
**Output Format:** [JSON API responses and saved JSON files, with Markdown summaries or claim presentation guidance for users.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Large responses may be summarized while full results are persisted to a local LinkFox session data path.] <br>

## Skill Version(s): <br>
1.0.5 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
