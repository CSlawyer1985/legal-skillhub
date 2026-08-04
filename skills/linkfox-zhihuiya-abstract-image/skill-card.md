## Description: <br>
通过专利ID或公开号从智慧芽专利数据库获取专利摘要附图，并返回可展示的图片路径和相关元数据。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users, patent researchers, and agent operators use this skill to retrieve abstract drawings for one or more patents by patent ID or publication number. It helps present patent image results without adding patent analysis or legal interpretation. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers and the LinkFox API key are sent to the LinkFox service, and queries may consume paid credits. <br>
Mitigation: Use the skill only for research you are comfortable sending to the service, confirm cost-bearing batch queries with the user, and manage the API key through environment variables. <br>
Risk: Full API responses are persisted locally under a linkfox session directory. <br>
Mitigation: Run the skill only in a controlled workspace and review, retain, or delete generated linkfox files according to the sensitivity of the patent research. <br>
Risk: Feedback reports may be sent to a separate LinkFox feedback service without clear user control. <br>
Mitigation: Avoid including confidential patent details or credentials in feedback content, and review feedback behavior before enabling or invoking it. <br>
Risk: Authentication or balance failures can trigger onboarding that may install another LinkFox skill. <br>
Mitigation: Review onboarding steps and any additional skill before installation, especially in managed or restricted environments. <br>


## Reference(s): <br>
- [API Reference](references/api.md) <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-abstract-image) <br>
- [LinkFox Tool Gateway Endpoint](https://tool-gateway.linkfox.com/zhihuiya/abstractImage) <br>
- [Feedback API Endpoint](https://skill-api.linkfox.com/api/v1/public/feedback) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, configuration, guidance, files] <br>
**Output Format:** [Markdown responses with patent identifiers, inline image links when available, JSON summaries, and local JSON result file paths.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [The script writes full API responses to a local linkfox session directory, caches requests for 24 hours by default, and prints either full JSON or a compact summary depending on response size.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
