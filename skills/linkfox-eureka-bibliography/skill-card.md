## Description: <br>
Queries Eureka patent bibliography records for patent titles, abstracts, applicants, inventors, classifications, priority claims, cited references, related documents, and estimated expiry data. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users, developers, and patent-analysis workflows use this skill to retrieve structured bibliographic metadata for one or more patent identifiers or publication numbers from the Eureka patent platform. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill sends LinkFox API credentials, patent identifiers, and session metadata to LinkFox services. <br>
Mitigation: Use only trusted LinkFox endpoints, avoid overriding LINKFOX_TOOL_GATEWAY unless the host is trusted, and scope or rotate API keys according to your credential policy. <br>
Risk: Full query responses may be cached or saved locally, which can retain patent query history and returned metadata. <br>
Mitigation: Review the local linkfox output and cache directories, avoid running the skill in sensitive workspaces, and delete retained response files when they are no longer needed. <br>
Risk: The skill includes automatic feedback reporting behavior to a separate LinkFox endpoint. <br>
Mitigation: Review or disable feedback submission where possible before use in confidential workflows. <br>
Risk: The onboarding path may ask the user to download and install another LinkFox skill. <br>
Mitigation: Require explicit user approval and verify the download source before installing any additional skill. <br>


## Reference(s): <br>
- [Eureka Bibliography API Reference](references/api.md) <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-eureka-bibliography) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance, files] <br>
**Output Format:** [Markdown guidance with shell examples, JSON API responses, stdout summaries, and saved JSON response files.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Queries require a LinkFox API key, accept patentId or patentNumber values, support up to 100 patents per request, and may cache or save full responses locally.] <br>

## Skill Version(s): <br>
1.0.5 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
