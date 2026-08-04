## Description: <br>
Guides agents through Ruiguan/Linkfox design patent risk checks for product images, including similarity search, TRO history signals, and radar analysis across 25+ supported countries and regions. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External sellers, IP professionals, and agent developers use this skill to check whether a product image may resemble existing design patents before listing or reviewing products. It helps prepare patent-risk summaries while preserving the skill's instruction to avoid legal conclusions beyond the returned data. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Product images, descriptions, and sales context are sent to an external Ruiguan/Linkfox service for analysis. <br>
Mitigation: Use the skill only for data that may be shared with that provider, and avoid confidential unreleased products unless the provider's data handling is acceptable. <br>
Risk: Detailed API responses are saved locally and may contain product, patent, and sales-context data. <br>
Mitigation: Review saved response files after use and remove them when they are no longer needed. <br>
Risk: The artifact includes feedback-reporting behavior separate from the patent-analysis API. <br>
Mitigation: Review or disable feedback reporting before installation when user comments or operational details should not be sent externally. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-ruiguan-detection-patent-design) <br>
- [API reference](artifact/references/api.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, JSON, shell commands, guidance] <br>
**Output Format:** [Markdown guidance with JSON request examples, shell commands, and saved JSON response files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires a public image URL or uploads a local image to obtain one; full API responses are saved locally and smaller responses may also print as JSON.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
