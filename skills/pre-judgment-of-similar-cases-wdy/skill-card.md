## Description: <br>
Retrieves legal provisions and similar cases through the Wendaoyun API to help users assess disputes and possible next steps. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[rose-develop](https://clawhub.ai/user/rose-develop) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and agents use this skill to search for relevant legal provisions and similar case examples from a user's dispute description. It supports legal research and triage, not a substitute for review by a qualified legal professional. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: User dispute descriptions may contain personal identifiers, amounts, or confidential legal facts that are sent to a third-party API. <br>
Mitigation: Avoid entering personal identifiers or confidential facts unless necessary, and confirm before sending sensitive details externally. <br>
Risk: Legal provisions, case matches, and suggested next steps may be incomplete or inappropriate for a user's jurisdiction or situation. <br>
Mitigation: Review outputs against authoritative legal sources and seek qualified legal advice before relying on them. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/rose-develop/skills/pre-judgment-of-similar-cases-wdy) <br>
- [rose-develop publisher profile](https://clawhub.ai/user/rose-develop) <br>
- [Wendaoyun Open Platform](https://open.wintaocloud.com/home) <br>
- [Wendaoyun legal provisions API endpoint](https://h5.wintaocloud.com/prod-api/api/invoke/get-laws) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, configuration, guidance] <br>
**Output Format:** [Markdown legal provisions, similar case summaries, configuration guidance, and optional analysis] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Uses WENDAOYUN_API_KEY when configured; top_k defaults to 3 and is capped at 5.] <br>

## Skill Version(s): <br>
1.0.6 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
