## Description: <br>
Detects graphic trademarks in product images and searches for visually similar registered marks across supported regions to help assess listing risk. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External e-commerce sellers, brand owners, and developers use this skill to submit product images, review similar graphic trademark matches, and understand potential listing risk before publication. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Local product images may be uploaded to public LinkFox-hosted URLs. <br>
Mitigation: Use non-confidential images, tell the user before uploading local files, and treat returned public URLs as externally accessible. <br>
Risk: Full API responses are saved locally and may contain product, trademark, or account-context data. <br>
Mitigation: Store outputs only in appropriate workspaces, avoid syncing saved response files to public locations, and delete them when no longer needed. <br>
Risk: Feedback may be sent to a separate LinkFox endpoint. <br>
Mitigation: Avoid including confidential user content in feedback and disclose feedback submission when it could affect user expectations. <br>
Risk: A custom LINKFOX_TOOL_GATEWAY setting can redirect API traffic. <br>
Mitigation: Use the default gateway unless a trusted operator has verified the custom endpoint. <br>
Risk: Remote onboarding dependencies may be installed when authentication or credit problems occur. <br>
Mitigation: Review remote onboarding packages before installation and obtain user approval when downloading is required. <br>


## Reference(s): <br>
- [睿观-图形商标检测 API reference](artifact/references/api.md) <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-ruiguan-trademark-graphic-detection) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with JSON API parameters, shell commands, saved JSON responses, and summarized result tables.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Full API responses are saved locally under LinkFox session data; large responses are summarized unless inline output is requested.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
