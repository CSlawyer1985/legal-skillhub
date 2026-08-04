## Description: <br>
Chinese contract risk intelligence that scans, annotates, and explains clauses in labor, rental, service, NDA, and more than 15 other contract types under PRC law. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[harrylabsj](https://clawhub.ai/user/harrylabsj) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users use this skill to review Chinese contracts before signing or negotiation by identifying risk levels, explanations, suggested revisions, and negotiation priorities. It supports contracts such as labor agreements, leases, service agreements, NDAs, loans, procurement, construction, insurance, and technology contracts under PRC law. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Contract inputs may contain sensitive personal, financial, signature, address, or trade secret information. <br>
Mitigation: Redact IDs, bank details, signatures, addresses, trade secrets, and unrelated personal data before sharing contract text with the assistant environment. <br>
Risk: Contract review output may be incomplete or unsuitable as final legal advice. <br>
Mitigation: Treat the output as review support and have qualified legal counsel verify important findings before signing, negotiating, or taking legal action. <br>
Risk: PRC-law contract analysis can depend on current law, local practice, contract context, and facts not present in the input. <br>
Mitigation: Check high-impact findings against current applicable law and the full transaction context before relying on recommendations. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/harrylabsj/contract-review-ai) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, guidance] <br>
**Output Format:** [Markdown contract review report with clause annotations, risk inventory, explanations, modification suggestions, and negotiation priorities] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May summarize parties, amounts, terms, key dates, and special conditions when provided in the contract text.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
