## Description: <br>
Retrieves translated patent claim text from the Zhihuiya (PatSnap) patent database in Chinese, English, or Japanese by patent ID or publication number. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Patent researchers, patent attorneys, and agent users use this skill to retrieve translated claim text for one or more known patents. It supports claim lookup by patent ID or publication number, optional family-patent substitution, and presentation of returned claims in the requested supported language. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers, API request context, and possible feedback content may be sent to LinkFox services. <br>
Mitigation: Install only when that data sharing is acceptable, and avoid confidential patent research unless the workflow has been reviewed for the intended environment. <br>
Risk: The skill includes automatic feedback reporting and onboarding steps that can introduce another LinkFox skill dependency. <br>
Mitigation: Review or disable the feedback workflow and verify any onboarding dependency through a trusted manual installation path. <br>
Risk: Full API responses and cached results may be stored locally in LinkFox session directories. <br>
Mitigation: Run the skill in an appropriate workspace and manage saved patent data according to the user's confidentiality and retention requirements. <br>
Risk: Requests consume LinkFox credits, and batch or repeated lookups can increase cost. <br>
Mitigation: Confirm the expected cost before large requests and avoid exploratory retries unless the user approves the additional consumption. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-claim-data-translated) <br>
- [智慧芽-权利要求翻译 API 参考](references/api.md) <br>
- [Zhihuiya claim translation API endpoint](https://tool-gateway.linkfox.com/zhihuiya/claimDataTranslated) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, JSON, Files, Shell commands, Guidance] <br>
**Output Format:** [Markdown guidance with JSON API responses, summaries, and saved JSON response files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires a LinkFox API key; supports up to 100 patents per request, three output languages, 24-hour caching for repeated parameters, and local storage of full responses.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
