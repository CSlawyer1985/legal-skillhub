## Description: <br>
Queries Zhihuiya (PatSnap) patent family data for supplied patent IDs or publication numbers, including Simple, INPADOC, and PatSnap family members. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Patent researchers, intellectual property teams, and agent users use this skill to retrieve family members and equivalent patents for known patent IDs or publication numbers. It supports comparison across Simple Family, INPADOC Family, and PatSnap Family definitions without providing legal advice. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers, API credentials, and session metadata are sent to LinkFox services during lookup. <br>
Mitigation: Use only approved LinkFox credentials, avoid submitting confidential patent research unless permitted, and confirm the destination service before running API calls. <br>
Risk: Full API responses and cached lookup data are saved locally under linkfox data/cache directories. <br>
Mitigation: Review generated files after use and remove saved responses or cache entries when they contain sensitive research data. <br>
Risk: The artifact includes feedback reporting and fallback onboarding instructions that may contact unrelated LinkFox endpoints or install another remote skill. <br>
Mitigation: Review or disable feedback reporting and require explicit user approval before downloading or installing any additional remote skill. <br>
Risk: Lookups consume LinkFox credits and can be costly for larger result sets. <br>
Mitigation: Warn users before running searches, respect the 100-patent batch limit, and avoid automatic retries or exploratory re-querying without confirmation. <br>


## Reference(s): <br>
- [智慧芽专利家族查询 API 参考](references/api.md) <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-patent-family) <br>


## Skill Output: <br>
**Output Type(s):** [API Calls, JSON, Files, Shell commands, Guidance] <br>
**Output Format:** [JSON responses saved to local files with stdout JSON or summaries; agent-facing guidance is Markdown.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires a LinkFox API key, uses a 24-hour local cache for repeated parameters, and may consume LinkFox credits per returned patent-family record.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
