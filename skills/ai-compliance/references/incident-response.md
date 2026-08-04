# AI Incident Response Playbooks

## Playbook 1: Sensitive/Restricted Data Entered into AI Tool

**Trigger:** DLP alert, user report, or audit finding that restricted data (MNPI, PII, credentials, confidential IP) was entered into a third-party AI tool.

### Immediate (0–1 hour)
1. Identify the user, tool, timestamp, and nature of data entered
2. Pull raw prompt from webhook_events or DLP logs if available
3. Determine data classification: Restricted / Confidential / Internal / Public
4. If MNPI or financial data: **notify Legal and Compliance immediately** — do not delay
5. If credentials: initiate credential rotation immediately (treat as compromised)
6. If PII of EU residents: start GDPR 72-hour breach notification clock assessment

### Short-term (1–24 hours)
7. Contact AI vendor to request data deletion (document request + vendor response)
8. Assess whether vendor's data retention policies mean data was stored
9. Determine if data was used in model training (check vendor policy/DPA)
10. Assess blast radius: was this a one-time entry or pattern of behavior?
11. Check webhook_events for similar events from same user or data type
12. Brief ISAI lead and CISO

### Remediation
13. Restrict or suspend user's access to AI tools pending review
14. Conduct user awareness session
15. Update DLP rules if data type was not previously caught
16. Document incident in AI incident log
17. Update AI risk register

### Notification Assessment (GDPR)
- Personal data of EU residents? → notify DPA within 72 hours if high risk to individuals
- Volume and sensitivity determine notification requirement
- Document decision either way (notify or not + rationale)

---

## Playbook 2: Prompt Injection Attack

**Trigger:** AI agent or automated pipeline behaves unexpectedly; outputs contain instructions not authored by legitimate users; AI takes unexpected actions.

### Immediate
1. Isolate the affected AI system/agent
2. Preserve logs of all inputs and outputs around the incident
3. Identify the injection vector (user input, database content, email content, web content)
4. Determine what actions the AI took as a result (emails sent, commands executed, data accessed)
5. Revert any unauthorized actions where possible

### Investigation
6. Trace the full chain: what input → what AI action → what system impact
7. Identify whether this was targeted or opportunistic
8. Assess whether any data was exfiltrated or exposed
9. Review all AI agent actions in the window (audit log)

### Remediation
10. Implement input sanitization for the injection vector
11. Add output validation before AI actions are executed
12. Implement human approval gates for sensitive AI-driven actions
13. Update system prompts to include explicit injection resistance instructions
14. Document and publish lessons learned

---

## Playbook 3: AI-Generated Output Causes Harm

**Trigger:** AI tool produces harmful, discriminatory, incorrect, or legally problematic output that is acted upon.

### Examples
- AI-generated report contains factual errors acted upon by business
- AI recommendation discriminates against protected class
- AI legal/financial advice acted upon without verification
- AI-generated content published that violates law/policy

### Response
1. Identify and preserve the original AI output
2. Assess the downstream impact (who acted on it, what decisions were made)
3. Halt use of the AI system pending review
4. Notify affected parties if harm occurred
5. If discriminatory output: notify HR and Legal immediately
6. If financial harm: quantify and notify Finance/Legal

### Remediation
7. Implement mandatory human review for outputs in that category
8. Update acceptable use policy to require verification
9. Document AI system limitations formally
10. Retrain users on AI output verification

---

## Playbook 4: AI Vendor Security Breach

**Trigger:** AI tool vendor announces breach or incident affecting customer data.

### Immediate
1. Assess whether fi.com was a customer at time of breach
2. Identify what data may have been exposed (prompts, outputs, account info)
3. Notify CISO and Legal
4. Preserve vendor notification communications

### Investigation
5. Request vendor incident report and scope confirmation
6. Cross-reference with internal logs — what was sent to this vendor in the breach window?
7. Identify any MNPI, PII, or confidential data in the exposed window
8. Assess GDPR/regulatory notification requirements

### Remediation
9. Rotate any credentials or API keys used with the vendor
10. Review and potentially suspend the vendor relationship
11. Update vendor risk rating
12. Notify affected individuals if PII was exposed (GDPR requirement)
13. Document in AI incident log

---

## AI Incident Log Template
| Date | Tool | User | Data Type | Severity | Actions Taken | Status |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | Perplexity | user@fi.com | MNPI | HIGH | Legal notified, data deletion requested | Closed |
