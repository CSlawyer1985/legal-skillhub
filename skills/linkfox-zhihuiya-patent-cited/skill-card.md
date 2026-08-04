## Description: <br>
Queries Zhihuiya (PatSnap) patent forward-citation data, including citation counts and citing-patent details, from patent IDs or publication numbers. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Patent analysts, IP teams, and developers use this skill to retrieve forward-citation counts and citing-patent details for one or more patent IDs or publication numbers. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers and related research context may be sent to LinkFox/PatSnap. <br>
Mitigation: Use the skill only when sharing that patent research context with the service is acceptable. <br>
Risk: Full API responses are saved locally by default. <br>
Mitigation: Run the skill from an approved writable location and manage retention or cleanup for saved response files. <br>
Risk: The artifact instructs feedback reporting to LinkFox without a clear consent step. <br>
Mitigation: Review feedback behavior before deployment and avoid sending confidential or sensitive user context. <br>


## Reference(s): <br>
- [智慧芽-专利被引用 API 参考](references/api.md) <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-patent-cited) <br>
- [Publisher Profile](https://clawhub.ai/user/linkfox-ai) <br>


## Skill Output: <br>
**Output Type(s):** [API Calls, JSON, Markdown, Files, Shell commands, Guidance] <br>
**Output Format:** [Markdown guidance and tables, shell commands, and JSON API responses saved to local files or printed to stdout] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Full API responses are saved locally; large responses are summarized unless inline output is requested.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
