## Description: <br>
Organize, track, and analyze contracts with renewal alerts, clause lookups, and multi-role support for individuals, landlords, freelancers, and legal teams. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[ivangdavila](https://clawhub.ai/user/ivangdavila) <br>

### License/Terms of Use: <br>


## Use Case: <br>
Individuals, landlords, freelancers, small businesses, and legal teams use this skill to organize local contract files, extract factual terms, track signatures, payments, and renewal deadlines, and look up clauses without providing legal advice. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill can persist sensitive contracts and extracted metadata in a local ~/contracts folder. <br>
Mitigation: Keep the folder private, use owner-only permissions, back it up securely, and avoid cloud sync unless the user explicitly accepts that risk. <br>
Risk: Contracts may include highly sensitive identifiers, banking details, signatures, or privileged legal advice. <br>
Mitigation: Avoid extracting or processing SSNs, tax IDs, bank details, signatures, and legal advice documents; store only necessary metadata. <br>
Risk: Contract summaries, risk flags, or liability notes could be mistaken for legal advice. <br>
Mitigation: Use the skill for factual extraction, organization, reminders, and clause lookup only, and consult a qualified attorney for interpretation or decisions. <br>


## Reference(s): <br>
- [Role-specific workflows](roles.md) <br>
- [Contract analysis patterns](analysis.md) <br>
- [Alert and deadline tracking](alerts.md) <br>
- [Security and boundaries](security.md) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Files, Guidance] <br>
**Output Format:** [Markdown files and concise text responses] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May create and update local files under ~/contracts/ when the user provides contracts.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
