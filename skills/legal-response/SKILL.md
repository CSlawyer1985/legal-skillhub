---
name: legal-response
description: Generate a response to a common legal inquiry using configured templates, with built-in escalation checks for situations that shouldn't use a templated reply. Use when responding to data subject requests, litigation hold notices, vendor legal questions, NDA requests from business teams, or subpoenas.
argument-hint: "[inquiry-type]"
---

# /legal-response -- Generate Response from Templates

Generate a response to a common legal inquiry using configured templates. Customizes the response with specific details and includes escalation triggers for situations that should not use a templated response.

**Important**: This command assists with legal workflows but does not provide legal advice. Generated responses should be reviewed by qualified legal professionals before being sent.

## Invocation

```
/legal-response [inquiry-type]
```

Common inquiry types:
- `dsr` -- Data subject access/deletion/correction requests
- `hold` -- Litigation hold notices
- `vendor` -- Vendor legal questions
- `nda` -- NDA requests from business teams
- `privacy` -- Privacy-related questions
- `subpoena` -- Subpoena or legal process responses
- `insurance` -- Insurance claim notifications

## Workflow

### Step 1: Identify Inquiry Type
Accept the inquiry type. If ambiguous, show available categories.

### Step 2: Load Template
Look for templates in local settings. If none configured, offer to help create one or use reasonable defaults.

### Step 3: Check Escalation Triggers

Before generating any response, evaluate escalation criteria:

#### Universal Triggers (All Categories)
- Potential litigation or regulatory investigation
- Inquiry from regulator, government, or law enforcement
- Response could create binding commitment or waiver
- Potential criminal liability
- Media attention involved
- Multiple jurisdictions with conflicting requirements

#### Category-Specific Triggers
- **DSR**: Minor's data, litigation hold conflict, special category data
- **Discovery Hold**: Criminal liability, unclear scope, conflicting regulatory requirements
- **Vendor**: Dispute or threatened litigation, regulatory compliance issues
- **NDA**: Competitor counterparty, M&A context, government classified information
- **Subpoena**: ALWAYS requires counsel review

**When trigger detected**: Stop, alert user, explain which trigger, recommend escalation path, offer draft marked "FOR COUNSEL REVIEW ONLY".

### Step 4: Gather Details

**DSR**: Requester info, request type, applicable regulation, response deadline
**Discovery Hold**: Matter name, custodians, scope, outside counsel contact
**Vendor**: Vendor name, reference agreement, specific question
**NDA**: Requesting team, counterparty, purpose, mutual/unilateral

### Step 5: Generate Response

Customize template with gathered details. Ensure:
- Appropriate professional tone
- All required legal elements included
- Specific dates, deadlines, obligations referenced
- Clear next steps for recipient
- Appropriate disclaimers

Present draft for user review before sending.

## Response Categories

### 1. Data Subject Requests (DSRs)
Sub-types: Acknowledgment, identity verification, fulfillment, partial/full denial, extension notification.

### 2. Discovery Holds
Sub-types: Initial hold notice, reminder, scope modification, hold release.

### 3. Privacy Inquiries
Sub-types: Cookie/tracking, privacy policy, data sharing, cross-border transfer questions.

### 4. Vendor Legal Questions
Sub-types: Contract status, amendment request, compliance certification, audit request.

### 5. NDA Requests
Sub-types: Sending standard form, accepting with markup, declining, renewal.

### 6. Subpoena / Legal Process
Sub-types: Acknowledgment, objection letter, extension request, compliance cover letter.
**Critical**: Almost always requires individualized counsel review.

### 7. Insurance Notifications
Sub-types: Initial claim notification, supplemental information, reservation of rights response.

## Notes

- Always present draft response for user review before sending
- Track response deadlines and offer calendar reminders
- For regulated responses (DSRs, subpoenas), note applicable deadline and regulatory requirements
- Templates should be living documents; suggest updates when modified during use
