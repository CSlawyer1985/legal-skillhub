## Description: <br>
通过专利ID或公开号从智慧芽专利数据库下载专利PDF全文文档。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users, patent professionals, and developers use this skill to retrieve patent full-text PDF download links from Zhihuiya by patent ID or publication number. It supports batches of up to 100 patents and can optionally substitute a related family patent PDF when the original is unavailable. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers, session metadata, and an API key are sent to LinkFox/Zhihuiya. <br>
Mitigation: Use only with data that is appropriate to share with the service provider, and avoid confidential patent work unless the workspace and account controls are approved. <br>
Risk: The script saves full API responses locally and may cache responses for 24 hours. <br>
Mitigation: Run in a controlled workspace, review saved files under the LinkFox output directory, and delete cached or response files when retention is not desired. <br>
Risk: Requests consume paid tokens, with costs scaling by the number of patent PDF results. <br>
Mitigation: Confirm batch size and expected cost before running broad downloads, especially near the 100-patent request limit. <br>
Risk: Automatic feedback reporting can send user intent and result quality details to a separate LinkFox feedback endpoint. <br>
Mitigation: Review feedback content before submission and avoid including confidential patent context or sensitive user details. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-pdf-data) <br>
- [Zhihuiya PDF API reference](references/api.md) <br>
- [LinkFox tool gateway endpoint](https://tool-gateway.linkfox.com/zhihuiya/pdfData) <br>
- [LinkFox feedback API](https://skill-api.linkfox.com/api/v1/public/feedback) <br>


## Skill Output: <br>
**Output Type(s):** [Markdown, Shell commands, API Calls, Files, JSON, Guidance] <br>
**Output Format:** [Markdown guidance with shell commands and JSON API responses saved to local files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Uses patentId, patentNumber, and replaceByRelated parameters; responses include PDF links, patent identifiers, substitution details, and token cost information.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
