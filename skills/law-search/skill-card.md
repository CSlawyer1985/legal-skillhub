## Description: <br>
Korean law/case search via law.go.kr + data.go.kr APIs for legal questions, statute lookup, court cases, and everyday legal information. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[sw326](https://clawhub.ai/user/sw326) <br>

### License/Terms of Use: <br>


## Use Case: <br>
External users and developers use this skill to search Korean statutes, court cases, official interpretation examples, and everyday legal guidance, then produce practical Korean-language answers with cited legal sources. It is reference material only and is not a substitute for legal advice. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The release security summary says the scripts warrant review before installation because they expose users to local code-execution risk. <br>
Mitigation: Review or patch the scripts before installing, and pass user input to Python through argv or stdin instead of embedding it in python3 -c source. <br>
Risk: API credentials may be exposed when keys are placed in URLs or stored in broadly readable credential files. <br>
Mitigation: Use HTTPS where supported, avoid placing API keys in URLs, and lock credential files to the owner. <br>
Risk: Optional Notion, Telegram, and search integrations may expose sensitive legal queries beyond the core law-search workflow. <br>
Mitigation: Treat optional integrations as opt-in only and avoid using them for sensitive legal matters unless the user has accepted that exposure. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/sw326/law-search) <br>
- [Open Law API portal](https://open.law.go.kr) <br>
- [Data.go.kr public data portal](https://www.data.go.kr) <br>
- [Data.go.kr case search API](https://www.data.go.kr/data/15057123/openapi.do) <br>
- [Data.go.kr statute search API](https://www.data.go.kr/data/15000115/openapi.do) <br>
- [Data.go.kr everyday law API](https://www.data.go.kr/data/15000215/openapi.do) <br>


## Skill Output: <br>
**Output Type(s):** [Markdown, Shell commands, API Calls, Guidance] <br>
**Output Format:** [Markdown response with cited legal references and JSON returned by helper scripts] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Responses should identify relevant statutes or cases, explain practical next steps, and include a reference-only legal disclaimer.] <br>

## Skill Version(s): <br>
2.1.0 (source: frontmatter and server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
