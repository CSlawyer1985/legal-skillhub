## Description: <br>
Searches Zhihuiya for visually similar utility model patents from an image URL and returns ranked patent matches for review. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and agents use this skill to compare a product image against utility model patent images, prioritize visually similar patents, and prepare non-legal review summaries for potential patent risk or prior-art research. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent-search images and query parameters are sent to LinkFox/Zhihuiya services. <br>
Mitigation: Use only images and parameters approved for that external service before running searches. <br>
Risk: Local image inputs may be uploaded as public-read URLs. <br>
Mitigation: Avoid confidential local product images unless the user accepts public URL exposure for the upload lifetime. <br>
Risk: Full responses and cache files are stored locally under linkfox output directories. <br>
Mitigation: Review or delete local linkfox data and cache files after use when results include sensitive patent-search context. <br>
Risk: The skill includes a separate feedback reporting flow that can send user comments or task context. <br>
Mitigation: Avoid feedback reporting when comments or task context may contain sensitive information. <br>
Risk: Search calls consume paid LinkFox credits. <br>
Mitigation: Confirm user intent before repeated searches, pagination, or parameter changes that would create additional cost. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-utility-patent-image-search) <br>
- [Zhihuiya patent image search API reference](references/api.md) <br>


## Skill Output: <br>
**Output Type(s):** [Guidance, Shell commands, JSON, Files] <br>
**Output Format:** [Markdown guidance with Python command examples and JSON API results printed to stdout or saved as local files.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires a LinkFox API key; local image inputs may be uploaded to a public URL; search responses and cache files are written under a local linkfox directory.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
