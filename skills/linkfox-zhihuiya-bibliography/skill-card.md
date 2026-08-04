## Description: <br>
Queries Zhihuiya patent bibliography records by patent ID or publication number and returns structured metadata such as titles, applicants, inventors, classifications, citations, abstracts, and dates. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users, patent researchers, and developers use this skill to retrieve factual bibliographic metadata for known patents when they already have a patent ID or publication number. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers, API credentials, and session or app metadata may be sent to LinkFox or Zhihuiya services. <br>
Mitigation: Use approved credentials, avoid confidential patent identifiers unless sharing is permitted, and confirm the service is appropriate for the user's data. <br>
Risk: Full lookup responses are saved locally and may include detailed patent records beyond the immediate answer. <br>
Mitigation: Run the skill in an appropriate workspace, review saved response files, and remove cached or session data when retention is not needed. <br>
Risk: The skill includes feedback reporting and guidance to install a separate onboarding skill when authentication or credits fail. <br>
Mitigation: Review feedback content before reporting, and only install or follow onboarding materials from LinkFox if that source is trusted. <br>
Risk: Lookups consume LinkFox/Zhihuiya credits and batch requests can consume credits quickly. <br>
Mitigation: Confirm the expected cost with the user before additional or batch lookups, and avoid repeated automatic retries with changed inputs. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-bibliography) <br>
- [API reference](references/api.md) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, JSON, Shell commands, Files, Guidance] <br>
**Output Format:** [Markdown guidance with optional shell commands and JSON API responses saved to local files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Results may be summarized when large; full API responses are saved locally by the helper script.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
