## Description: <br>
Queries and summarizes legal and business risk records for Mainland China companies using 88cha search and company-risk APIs. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[1688aiinfra](https://clawhub.ai/user/1688aiinfra) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and agents use this skill to look up company risk records for Mainland China businesses by company name, unified social credit code, or companyId, then receive a structured risk overview and follow-up analysis. <br>

### Deployment Geography for Use: <br>
Global; the queried company-risk domain is limited to Mainland China companies. <br>

## Known Risks and Mitigations: <br>
Risk: The access key is sensitive and the security evidence reports under-scoped credential setup that may store or reuse it under a different skill namespace. <br>
Mitigation: Use a limited-scope key, avoid pasting shared production credentials into chat, rotate the key if exposed, and verify that writing under the cha88-base config entry is acceptable before installation. <br>
Risk: The skill contacts the 88cha skills gateway for company-risk lookup and usage reporting. <br>
Mitigation: Review the gateway dependency and telemetry behavior before deployment, especially in environments with restricted outbound network or usage-reporting requirements. <br>


## Reference(s): <br>
- [ClawHub release page](https://clawhub.ai/1688aiinfra/1688-common-cha88-company-risk) <br>
- [Company risk capability guide](references/capabilities/companyRisk.md) <br>
- [Company search capability guide](references/capabilities/cha88_search.md) <br>
- [Access key configuration guide](references/capabilities/configure.md) <br>
- [Skill usage telemetry notes](references/skill_description.md) <br>
- [88cha skills gateway](https://skills-gateway.1688.com) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, JSON, shell commands, configuration, guidance] <br>
**Output Format:** [JSON CLI responses containing Markdown, followed by agent-authored Markdown risk summaries and guidance.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Queries require a configured access key and may include paginated risk data.] <br>

## Skill Version(s): <br>
0.1.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
