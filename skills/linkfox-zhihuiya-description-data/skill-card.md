## Description: <br>
通过专利ID或公开号从智慧芽专利数据库获取专利说明书（描述）数据。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and patent-analysis users use this skill to retrieve full patent specification text from Zhihuiya by patent ID or publication number, including batch lookups and optional family-member substitution when a target description is unavailable. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers and related task metadata are sent to LinkFox/Zhihuiya services. <br>
Mitigation: Use the skill only for patent work that is approved for those services, and avoid confidential matters unless the data-sharing path is acceptable. <br>
Risk: Full patent responses are stored locally in the workspace session data directory. <br>
Mitigation: Run the skill only in controlled workspaces and manage the generated response files according to retention and access requirements. <br>
Risk: Queries consume service credits, and batch requests can increase cost quickly. <br>
Mitigation: Confirm the identifiers, batch size, and family-substitution behavior before making calls that may spend credits. <br>
Risk: Feedback may be sent to a separate LinkFox feedback service when the artifact behavior decides it applies. <br>
Mitigation: Disable or prevent automatic feedback reporting where confidential context or strict data-minimization requirements apply. <br>


## Reference(s): <br>
- [智慧芽专利说明书查询 API 参考](references/api.md) <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-description-data) <br>
- [linkfox-ai publisher profile](https://clawhub.ai/user/linkfox-ai) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, JSON, Shell commands, Guidance] <br>
**Output Format:** [Markdown guidance with JSON API responses and saved JSON files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Full API responses are written under a local linkfox session data directory; large responses are summarized unless inline output is requested.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
