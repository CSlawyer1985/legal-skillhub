## Description: <br>
企业法律风险智能检测专家，通过对话式体检帮助企业发现隐藏法律风险并给出整改建议。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[lswjp1234-lgtm](https://clawhub.ai/user/lswjp1234-lgtm) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External business users use this skill to run a Chinese enterprise legal-risk screening conversation, score common compliance risks, and receive informational remediation guidance. It also routes users toward paid module reviews or lawyer consultation when the skill's documented flow calls for deeper review. <br>

### Deployment Geography for Use: <br>
China <br>

## Known Risks and Mitigations: <br>
Risk: The skill asks for sensitive business or legal details without an included privacy notice. <br>
Mitigation: Use anonymized or non-confidential facts unless the user trusts the publisher and understands how the information will be handled. <br>
Risk: The skill includes a paid consultation funnel and asks for payment screenshots. <br>
Mitigation: Verify the lawyer identity and payment destination before sending money, payment screenshots, or contact details. <br>
Risk: Broad legal-risk trigger terms can activate the skill outside an intentional screening session. <br>
Mitigation: Use it only when the user intentionally wants a Chinese enterprise legal-risk screening and confirm scope before collecting sensitive details. <br>


## Reference(s): <br>
- [13模块97+检测项完整题库](references/modules.md) <br>
- [ClawHub release page](https://clawhub.ai/lswjp1234-lgtm/enterprise-law-risk-checker) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, guidance] <br>
**Output Format:** [Markdown-style legal-risk screening questions, score summaries, risk explanations, and remediation guidance] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Outputs are informational and not formal legal advice; the skill may ask for business/legal facts and payment screenshots during the documented paid-service flow.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
