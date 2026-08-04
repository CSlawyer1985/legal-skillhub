## Description: <br>
Checks Chinese marketing content for advertising-law, banned-word, platform-rule, and SEO issues using an external compliance API, then suggests safer wording and optimization fixes. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[lm203688](https://clawhub.ai/user/lm203688) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers, marketers, and content teams use this skill to scan Chinese-language campaign copy for platform-specific compliance issues and SEO gaps before publication. It helps revise flagged wording and verify that updated content passes the external compliance check. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Content submitted for scanning is sent to an external compliance-checking API. <br>
Mitigation: Avoid sending confidential drafts, customer data, legal strategy, or unreleased business material unless the API operator and its privacy and retention practices have been reviewed. <br>
Risk: Compliance scan results may not guarantee legal safety for high-risk campaigns. <br>
Mitigation: Use the scan as pre-publication support and have a qualified legal professional review high-risk content before release. <br>
Risk: Chinese advertising and platform rules can change over time. <br>
Mitigation: Re-scan content close to publication and document any remaining issues or manual legal review decisions. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/lm203688/chinese-seo-compliance) <br>
- [Compliance Web App](https://1341839497-jv04655vcs.ap-shanghai.tencentscf.com/) <br>
- [Compliance Check API](https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com/check) <br>
- [Suggestion API](https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com/suggestions?platform=xiaohongshu) <br>
- [API Health Check](https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com/health) <br>
- [Baidu Webmaster Tools](https://ziyuan.baidu.com) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, guidance] <br>
**Output Format:** [Markdown with API request examples and compliance recommendations] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May include platform-specific violation summaries, suggested replacement language, SEO recommendations, and follow-up scan commands.] <br>

## Skill Version(s): <br>
2.3.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
