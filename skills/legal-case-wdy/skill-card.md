## Description: <br>
Helps agents retrieve legal provisions and similar cases from WintaoCloud for user-described disputes, then format legal consequences and practical next-step guidance. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[rose-develop](https://clawhub.ai/user/rose-develop) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and agents use this skill to retrieve relevant laws and similar case summaries for disputes such as fraud, unpaid debts, contract breaches, injuries, and litigation questions. The skill can also provide follow-up analysis about legal risk factors, evidence collection, negotiation, or filing suit. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Dispute descriptions may include private names, IDs, phone numbers, addresses, financial amounts, or other sensitive details that are sent to WENDAOYUN's third-party API. <br>
Mitigation: Summarize facts minimally before lookup and remove private details where possible. <br>
Risk: The skill requires a WENDAOYUN_API_KEY for authenticated API calls. <br>
Mitigation: Store the API key only in the environment, avoid sharing it in prompts or logs, and revoke it from the WintaoCloud platform if exposure is suspected. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/rose-develop/skills/legal-case-wdy) <br>
- [Publisher profile](https://clawhub.ai/user/rose-develop) <br>
- [WintaoCloud Open Platform](https://open.wintaocloud.com/home) <br>
- [WintaoCloud legal lookup API endpoint](https://h5.wintaocloud.com/prod-api/api/invoke/get-laws) <br>


## Skill Output: <br>
**Output Type(s):** [Markdown, Guidance, Shell commands, Configuration instructions] <br>
**Output Format:** [Markdown with formatted legal provisions, similar case summaries, optional analysis, and inline shell commands for API key setup] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires WENDAOYUN_API_KEY; legal and case lookup requests default to top_k 3 and cap top_k at 5.] <br>

## Skill Version(s): <br>
1.0.3 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
