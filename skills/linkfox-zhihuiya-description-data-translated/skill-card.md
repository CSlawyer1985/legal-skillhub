## Description: <br>
Retrieves translated patent description or specification text from the Zhihuiya data service for Chinese, English, or Japanese outputs using a patent ID or publication number. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and patent-focused agent workflows use this skill to retrieve translated patent description text by patent ID or publication number. It supports single or batch lookups, target languages of English, Chinese, and Japanese, and optional family-member substitution when the original description is unavailable. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers and translated description content are sent to the LinkFox service. <br>
Mitigation: Use the skill only when sharing those patent details with LinkFox is acceptable for the user's task and data-handling requirements. <br>
Risk: Gateway environment variables can redirect requests to an untrusted host. <br>
Mitigation: Review gateway configuration before use and keep LinkFox API credentials scoped to trusted environments. <br>
Risk: Response files and feedback reports may persist task content beyond the immediate chat context. <br>
Mitigation: Check where saved response files and feedback reports are stored or sent, and remove sensitive artifacts when retention is not desired. <br>
Risk: Each returned patent description consumes service credits, and batch requests can multiply cost. <br>
Mitigation: Confirm the intended query set and cost impact before running large batches or repeating failed lookups. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-description-data-translated) <br>
- [API reference](references/api.md) <br>
- [LinkFox tool endpoint](https://tool-gateway.linkfox.com/zhihuiya/descriptionDataTranslated) <br>


## Skill Output: <br>
**Output Type(s):** [Text, JSON, Markdown, Shell commands, Configuration, Guidance] <br>
**Output Format:** [Markdown guidance with JSON API responses and saved JSON response files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Large responses may be summarized in stdout while the full response is saved under a LinkFox session data directory.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
