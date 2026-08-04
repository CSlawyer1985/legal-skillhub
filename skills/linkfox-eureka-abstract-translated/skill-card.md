## Description: <br>
Retrieves translated patent titles and abstracts from the Eureka patent data platform by patent ID or publication number, supporting Chinese, English, and Japanese. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and developers use this skill to retrieve translated patent titles and abstracts for specific patents, including batch lookup and optional family-patent fallback when an abstract is unavailable. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent lookup requests and API metadata are sent to LinkFox services. <br>
Mitigation: Use only a trusted LinkFox gateway and avoid submitting confidential patent identifiers unless that sharing is appropriate. <br>
Risk: The skill writes API responses and cache files locally by default. <br>
Mitigation: Run it in a workspace where local LinkFox output is expected and manage generated files according to data handling policy. <br>
Risk: Security evidence notes automatic feedback reporting and conditional remote onboarding installation behavior. <br>
Mitigation: Review or disable feedback behavior where possible, and require explicit user authorization before remote onboarding installation. <br>


## Reference(s): <br>
- [Eureka API reference](artifact/references/api.md) <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-eureka-abstract-translated) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration] <br>
**Output Format:** [Markdown guidance with table-style result presentation, plus JSON API responses and saved JSON files.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires a patent ID or publication number; supports up to 100 patents per request; writes full responses under a local linkfox session directory and may summarize large responses.] <br>

## Skill Version(s): <br>
1.0.5 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
