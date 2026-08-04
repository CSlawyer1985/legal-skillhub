# ThumbGate Prevention Rules: Legal Intake Pilot

| Rule ID | Name | Description | Severity |
| :--- | :--- | :--- | :--- |
| LAW-001 | UPL_BLOCK | Block any response containing advice on "what to do" or "legal rights". | Critical |
| LAW-002 | GUARANTEE_LOCK | Reject responses that promise a specific outcome or settlement amount. | Critical |
| LAW-003 | CONFLICT_CHECK | Flag any lead where `opposing_party` matches an active client in `clients.json`. | High |
| LAW-004 | PHI_REDACTION | Redact Social Security Numbers, HIPAA diagnoses, and Driver's License IDs in logs. | Critical |
| LAW-005 | STATUTE_ALERT | If `incident_date` is > 1.5 years ago, MUST flag "Statute of Limitations Risk" for attorney review. | High |
| LAW-006 | UPL_DISCLAIMER | Require "Not legal advice" disclaimer in every first response and session close. | Critical |
| LAW-007 | CONTACT_CAPTURE | Ensure Name, Phone, and Email are verified against regex patterns before closing intake. | High |
| LAW-008 | JURISDICTION_CHECK | If lead is outside the firm's `licensed_states`, MUST provide referral disclaimer. | High |
| LAW-009 | CASE_TYPE_MATCH | Do not schedule a consult for "Criminal Law" if the firm only handles "Civil Litigation". | Medium |
| LAW-010 | NO_PII_LEAK | Ensure user-provided passwords or sensitive credentials are never stored in the intake sheet. | Critical |
