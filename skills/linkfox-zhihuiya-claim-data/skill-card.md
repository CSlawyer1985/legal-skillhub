## Description: <br>
Retrieves patent claim data from Zhihuiya (PatSnap) by patent ID or publication number and helps agents present claim text, counts, and related-family substitutions. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
IP professionals, patent analysts, R&D teams, and developer agents use this skill to retrieve and format patent claim data for specific patents. It is suited to claim lookup, claim counts, batch retrieval, and family-member substitution when claims are unavailable. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent lookup requests and feedback content may be sent to LinkFox services. <br>
Mitigation: Use the skill only for patent identifiers and feedback content appropriate to share with LinkFox, and review the feedback workflow before enabling automated reports. <br>
Risk: Full claim responses are saved locally by the script. <br>
Mitigation: Run the skill in an approved workspace, review saved response files for sensitivity, and remove local outputs when retention is not needed. <br>
Risk: The onboarding flow may install or invoke a separate LinkFox onboarding package. <br>
Mitigation: Install the onboarding package only after reviewing and trusting that package separately. <br>


## Reference(s): <br>
- [ClawHub listing](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-claim-data) <br>
- [API reference](artifact/references/api.md) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, JSON, Shell commands, Guidance] <br>
**Output Format:** [Markdown guidance with JSON API parameters and optional saved JSON response files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [The script writes full API responses locally and prints either the full JSON response or a summary depending on response size.] <br>

## Skill Version(s): <br>
1.0.4 (source: server evidence release.version) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
