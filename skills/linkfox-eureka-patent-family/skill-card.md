## Description: <br>
Queries the Eureka patent data platform for simple, INPADOC, and PatSnap patent-family members from patent IDs or publication numbers. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Patent analysts, IP teams, and developers use this skill to retrieve and compare family members for known patents, including simple, INPADOC, and PatSnap family groupings. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent lookup inputs, API credentials, and session metadata may be sent to LinkFox-operated services. <br>
Mitigation: Review the configured gateway host, avoid including sensitive patent information unless acceptable, and run with only the LinkFox API credential needed for the lookup. <br>
Risk: The skill can direct the agent toward companion-skill installation or feedback submission flows. <br>
Mitigation: Require explicit user confirmation before installing companion skills, downloading onboarding material, or submitting feedback. <br>
Risk: Full API responses and caches may be saved locally under a linkfox directory. <br>
Mitigation: Inspect and delete saved response or cache files after sensitive searches, and avoid running in directories where local artifacts should not be created. <br>
Risk: Dynamic credit consumption can become large for result-heavy requests. <br>
Mitigation: Warn the user about the 81 times max(returned records, 1) credit rule and confirm before large batch lookups. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-eureka-patent-family) <br>
- [API reference](artifact/references/api.md) <br>
- [LinkFox API key and credit guide](https://skill.linkfox.com/linkfoxskills/guide.htm) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration] <br>
**Output Format:** [Markdown summaries and tables with JSON API parameters, shell command examples, and optional saved JSON response files.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Accepts patentId or patentNumber values, supports up to 100 comma-separated patents per request, requires a LinkFox API key, and may cache or save response JSON under a linkfox directory.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
