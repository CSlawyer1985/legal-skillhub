## Description: <br>
Queries the Zhihuiya patent database for simple bibliographic patent metadata, including titles, abstracts, applicants, inventors, classifications, filing dates, priority claims, and citations. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and external users use this skill to retrieve structured front-page patent bibliography data when they already have patent IDs or publication numbers. It supports single and batch lookups and helps present selected fields such as applicants, inventors, dates, classifications, abstracts, and citations. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: API requests and patent identifiers are sent to LinkFox infrastructure. <br>
Mitigation: Install and use the skill only when users are comfortable with LinkFox receiving the request, and avoid submitting sensitive patent identifiers without approval. <br>
Risk: Full patent responses and session metadata are written to local LinkFox folders and may be committed accidentally. <br>
Mitigation: Run the skill in an appropriate workspace, inspect generated LinkFox folders, and exclude generated JSON outputs from version control. <br>
Risk: Troubleshooting guidance can lead to downloading or installing an onboarding skill. <br>
Mitigation: Require explicit user approval before downloading or installing any additional skill. <br>
Risk: The skill can send automatic feedback when it detects mismatches, dissatisfaction, praise, or improvement opportunities. <br>
Mitigation: Review feedback behavior before deployment and avoid including sensitive user or patent details in feedback content. <br>


## Reference(s): <br>
- [Zhihuiya Simple Bibliography API Reference](artifact/references/api.md) <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-simple-bibliography) <br>
- [Publisher Profile](https://clawhub.ai/user/linkfox-ai) <br>


## Skill Output: <br>
**Output Type(s):** [API Calls, JSON, Files, Markdown, Shell commands, Guidance] <br>
**Output Format:** [Markdown guidance with shell commands and JSON API responses saved to local files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Full responses are saved under a LinkFox session data folder; small responses may also be printed inline, while larger responses print a summary unless --inline is used.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
