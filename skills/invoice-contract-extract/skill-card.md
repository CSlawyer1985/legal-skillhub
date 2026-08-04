## Description: <br>
Extracts key fields from invoice, receipt, and contract PDFs or images, validates amounts and dates, and returns structured JSON plus a readable report. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[sh2601393743-png](https://clawhub.ai/user/sh2601393743-png) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Finance, legal, and operations teams use this skill to extract key data from invoices, receipts, and contracts for review or automation workflows. It supports single-document and batch extraction with validation warnings for fields that need manual review. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Invoices, receipts, and contracts may contain private financial, legal, or business information. <br>
Mitigation: Use the skill only on files or folders intentionally provided for extraction, and handle extracted data according to the user's data-retention and access-control requirements. <br>
Risk: OCR, field extraction, or contract interpretation can be incomplete or uncertain. <br>
Mitigation: Manually review extracted contract interpretations, uncertain fields, validation warnings, and high-value financial amounts before acting on the output. <br>
Risk: The skill is not a substitute for accounting, legal advice, invoice authenticity checks, or encrypted-document handling. <br>
Mitigation: Route accounting decisions, legal conclusions, authenticity checks, and password-protected documents to the appropriate human review or source system. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/sh2601393743-png/skills/invoice-contract-extract) <br>
- [Publisher profile](https://clawhub.ai/user/sh2601393743-png) <br>
- [SKILL.md](artifact/SKILL.md) <br>


## Skill Output: <br>
**Output Type(s):** [JSON, Markdown, Text] <br>
**Output Format:** [Structured JSON plus human-readable Markdown report] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Supports single-file and batch summaries; flags uncertain or failed validations for manual review.] <br>

## Skill Version(s): <br>
1.0.0 (source: release evidence and skill frontmatter) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
