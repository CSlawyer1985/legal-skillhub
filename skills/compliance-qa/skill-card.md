## Description: <br>
RAG-enhanced compliance Q&A with regulatory interpretation guardrails, source attribution, and escalation triggers. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[dangsllc](https://clawhub.ai/user/dangsllc) <br>

### License/Terms of Use: <br>
Apache-2.0 <br>


## Use Case: <br>
Employees, compliance teams, and developers use this skill to answer compliance questions from user-provided documents with citations, context gaps, confidence notes, and escalation triggers. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Users may treat compliance answers as legal advice or incident-response direction. <br>
Mitigation: Present answers as document-grounded summaries and escalate legal interpretation, critical non-compliance, active incidents, or contradictory evidence to privacy, compliance, or legal teams. <br>
Risk: Sensitive compliance documents or URLs may be shared with the agent without appropriate authorization. <br>
Mitigation: Use only documents and URLs the user is authorized to share, and keep answers limited to the supplied context. <br>
Risk: Incomplete or contradictory source context can produce incomplete compliance guidance. <br>
Mitigation: Require citations for claims, call out context gaps, and state when the provided documents do not determine an answer. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/dangsllc/skills/compliance-qa) <br>
- [ClawHub publisher profile](https://clawhub.ai/user/dangsllc) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, guidance] <br>
**Output Format:** [Markdown answer with cited analysis, context gaps, confidence, and escalation status] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Grounded in user-provided context; no install scripts, persistence, or mutation authority.] <br>

## Skill Version(s): <br>
0.1.2 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
