## Description: <br>
Searches Zhihuiya design-patent records by image URL to find visually similar design patents and support appearance-risk review. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users, developers, and patent-review workflows use this skill to submit product or design images and retrieve ranked similar design-patent results for prior-art research or preliminary infringement-risk triage. It does not provide a legal determination and directs users to consult a patent attorney. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Local product or design images may be uploaded to publicly accessible LinkFox object storage before search. <br>
Mitigation: Use only images approved for external processing, avoid unreleased or confidential designs, and prefer already approved public image URLs when possible. <br>
Risk: Full patent-search responses are retained in local JSON files. <br>
Mitigation: Review the saved response location, apply workspace data-retention rules, and remove files containing sensitive query context when they are no longer needed. <br>
Risk: Feedback reports may be sent to a separate LinkFox endpoint. <br>
Mitigation: Ensure feedback content does not include confidential design details, credentials, or user-sensitive information. <br>
Risk: Similarity scores and search results can be mistaken for legal conclusions. <br>
Mitigation: Present results as preliminary similarity findings and direct users to qualified patent counsel for infringement or freedom-to-operate decisions. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-patent-image-search) <br>
- [Zhihuiya Patent Image Search API Reference](references/api.md) <br>


## Skill Output: <br>
**Output Type(s):** [API Calls, JSON, Files, Shell commands, Guidance] <br>
**Output Format:** [JSON responses saved to local files, with stdout JSON or summarized text depending on response size] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires LinkFox API credentials, consumes credits per search, caches identical requests for 24 hours, and supports an inline mode for full stdout output.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
