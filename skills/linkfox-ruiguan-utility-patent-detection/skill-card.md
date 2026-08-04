## Description: <br>
基于产品信息检测和搜索相似的实用新型/发明专利，帮助跨境电商卖家在上架前识别潜在专利侵权和 TRO 风险。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External sellers and agents use this skill to query LinkFox/Ruiguan patent data with product titles, product descriptions, and a target US selling region, then review similar utility or invention patents, similarity scores, validity, and TRO indicators. It supports preliminary patent-risk screening and does not replace advice from a patent attorney. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Product titles and descriptions are sent to LinkFox/Ruiguan external services for patent lookup. <br>
Mitigation: Use the skill only when external transmission is authorized, and avoid submitting confidential unreleased product details unless the user accepts that exposure. <br>
Risk: Full patent-search responses can be stored locally, including result and cache files. <br>
Mitigation: Review and delete LinkFox result or cache files when they are no longer needed, especially after searches involving sensitive business context. <br>
Risk: The tool gateway can be overridden by LINKFOX_TOOL_GATEWAY. <br>
Mitigation: Check that LINKFOX_TOOL_GATEWAY is unset or points to an expected LinkFox/Ruiguan host before running searches. <br>
Risk: Feedback reporting is an external data transmission path. <br>
Mitigation: Do not include secrets, personal data, or confidential business context in feedback reports. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-ruiguan-utility-patent-detection) <br>
- [睿观-发明专利检测 API 参考](references/api.md) <br>
- [LinkFox tool gateway](https://tool-gateway.linkfox.com/ruiguan/utilityPatentDetection) <br>
- [LinkFox feedback API](https://skill-api.linkfox.com/api/v1/public/feedback) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, JSON, guidance] <br>
**Output Format:** [Markdown guidance with patent-result tables and JSON response files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Calls require a LinkFox API key, consume credits, support only US patent searches, return up to 200 results, and may save full API responses locally.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
