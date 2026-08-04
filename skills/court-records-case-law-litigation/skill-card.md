## Description: <br>
Court Records, Case Law & Litigation helps AI agents search US court opinions and case law by keyword via CourtListener for lawsuits, precedent, due diligence, legal research, and risk checks. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[colinhughes2121](https://clawhub.ai/user/colinhughes2121) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External agents and developers use this skill to search US court opinions and case law by keyword, including litigation checks for companies, people, or topics during due diligence and legal research workflows. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The external provider receives search keywords submitted through the lookup endpoint. <br>
Mitigation: Confirm that keyword disclosure to the provider is acceptable before use, especially for sensitive legal or due diligence queries. <br>
Risk: The x402 wallet may make small USDC payments for each lookup. <br>
Mitigation: Review wallet configuration, spending limits, and expected per-call cost before enabling automated use. <br>
Risk: Returned court records and case law are legal research leads, not legal advice. <br>
Mitigation: Have qualified legal reviewers validate results before relying on them for legal conclusions or decisions. <br>


## Reference(s): <br>
- [ClawHub skill listing](https://clawhub.ai/colinhughes2121/court-records-case-law-litigation) <br>
- [GoCreative Agent Compliance & Data API](https://api.gocreativeai.com) <br>
- [Case law lookup endpoint](https://api.gocreativeai.com/v1/lookup/case-law/{keyword}) <br>


## Skill Output: <br>
**Output Type(s):** [API Calls, Guidance] <br>
**Output Format:** [Markdown guidance with HTTPS GET endpoint details and JSON service responses] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Uses an x402 pay-per-call flow in USDC; no API key or signup is described.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata and SKILL.md frontmatter) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
