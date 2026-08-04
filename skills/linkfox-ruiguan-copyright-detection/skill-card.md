## Description: <br>
Helps agents check image copyright infringement risk with Ruiguan by submitting public image URLs and summarizing similarity, rights-owner, TRO, and radar-detection results. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External e-commerce sellers, designers, and agents use this skill to assess whether product or design images resemble registered copyrighted works before publication. It presents factual risk indicators and recommends legal counsel for definitive copyright assessments. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Image URLs and local images uploaded for checking may be sent to LinkFox/Ruiguan services, and uploaded local images may become public temporary URLs. <br>
Mitigation: Use the skill only with images whose sharing is acceptable, and avoid confidential product or customer images unless that data flow is approved. <br>
Risk: API results may be saved locally and cached. <br>
Mitigation: Review the local linkfox data directory after use and remove sensitive result files when they are no longer needed. <br>
Risk: The skill may forward environment metadata and report feedback to a separate LinkFox endpoint. <br>
Mitigation: Review the data-sharing behavior before commercial use and avoid including sensitive user or project details in feedback content. <br>


## Reference(s): <br>
- [睿观-版权检测 API Reference](references/api.md) <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-ruiguan-copyright-detection) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, JSON, guidance] <br>
**Output Format:** [Markdown summaries with optional shell commands and saved JSON API responses] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Can cache responses for 24 hours and save full API responses under a local linkfox session data directory.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
