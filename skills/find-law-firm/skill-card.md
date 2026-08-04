## Description: <br>
Find Law Firm helps agents search, shortlist, and enrich US B2B law firms for corporate legal needs such as IP, M&A, securities, employment, litigation, compliance, privacy, real estate, and tax. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[nostrband](https://clawhub.ai/user/nostrband) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and business teams use this skill to find, compare, and enrich US business-to-business law firms for outside-counsel procurement. It is intended for corporate practice areas and not for consumer legal matters, DIY legal advice, non-US firms, or in-house hiring. <br>

### Deployment Geography for Use: <br>
United States <br>

## Known Risks and Mitigations: <br>
Risk: The skill requires a ServiceGraph API key and may expose credentials if secrets are pasted into chat or committed to files. <br>
Mitigation: Store SERVICEGRAPH_API_KEY locally, do not paste it into chat, and pass it through the shell environment or configured MCP server. <br>
Risk: Detail enrichment consumes ServiceGraph credits. <br>
Mitigation: Use free validation, search, and brief reads first; confirm selected firms and expected credit cost before running unlocks. <br>
Risk: The catalog is limited to US B2B law firms and is not intended for consumer legal matters or DIY legal advice. <br>
Mitigation: Decline out-of-scope consumer, non-US, and legal-advice requests and direct users to appropriate referral or legal-advice channels. <br>


## Reference(s): <br>
- [Find Law Firm on ClawHub](https://clawhub.ai/nostrband/find-law-firm) <br>
- [Publisher profile: nostrband](https://clawhub.ai/user/nostrband) <br>
- [ServiceGraph API](https://api.servicegraph.co) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown with API request examples and concise recommendations] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May include ServiceGraph filters, curl examples, shortlist summaries, and credential setup guidance.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
