---
name: compliance-check
description: Run a compliance check on a proposed action, product feature, marketing campaign, or business initiative. Covers GDPR, CCPA/CPRA, LGPD, POPIA, PIPEDA, PDPA, PIPL, UK GDPR with DPA review checklist and data subject request handling procedures.
---

# /compliance-check -- Compliance Review

Run a compliance check on a proposed action, product feature, marketing campaign, or business initiative.

**Important**: This command assists with legal workflows but does not provide legal advice. Compliance assessments should be reviewed by qualified legal professionals. Regulatory requirements change frequently; always verify current requirements with authoritative sources.

## Usage

```
/compliance-check $ARGUMENTS
```

## What I Need From You

Describe what you're planning to do. Examples:
- "We want to launch a referral program with cash rewards"
- "We're adding biometric authentication to our mobile app"
- "We need to process EU customer data in our US data center"

## Output

```markdown
## Compliance Check: [Initiative]

### Summary
[Quick assessment: Proceed / Proceed with conditions / Requires further review]

### Applicable Regulations and Policies
| Regulation/Policy | Relevance | Key Requirements |
|-------------------|-----------|-----------------|
| [GDPR / CCPA / etc.] | [How it applies] | [What you need to do] |

### Requirements
| # | Requirement | Status | Action Needed |
|---|-------------|--------|---------------|
| 1 | [Requirement] | [Met / Not Met / Unknown] | [What to do] |

### Risk Areas
| Risk | Severity | Mitigation |
|------|----------|------------|
| [Risk] | [High/Med/Low] | [How to address] |

### Recommended Actions
1. [Most important action]
2. [Second priority]

### Approvals Needed
| Approver | Why | Status |
|----------|-----|--------|
| [Person/Team] | [Reason] | [Pending] |
```

## Privacy Regulation Overview

### GDPR (General Data Protection Regulation)

**Scope**: Processing of personal data of individuals in the EU/EEA.

**Key Obligations**:
- **Lawful basis**: Identify and document lawful basis for each processing activity
- **Data subject rights**: Respond to access, rectification, erasure, portability, restriction, and objection requests within 30 days
- **DPIAs**: Required for processing likely to result in high risk
- **Breach notification**: Notify supervisory authority within 72 hours
- **Records of processing**: Maintain Article 30 records
- **International transfers**: Ensure appropriate safeguards (SCCs, adequacy decisions, BCRs)

### CCPA / CPRA (California)

**Key Obligations**:
- **Right to know**: Consumers can request disclosure of PI collected, used, and shared
- **Right to delete**: Consumers can request deletion
- **Right to opt-out**: Consumers can opt out of sale/sharing of PI
- **Right to correct**: Consumers can request correction (CPRA)
- **Response timelines**: Acknowledge within 10 business days, respond within 45 calendar days

### Other Key Regulations

| Regulation | Jurisdiction | Key Differentiators |
|---|---|---|
| **LGPD** | Brazil | Similar to GDPR; requires DPO |
| **POPIA** | South Africa | Information Regulator oversight |
| **PIPEDA** | Canada (federal) | Consent-based framework |
| **PDPA** | Singapore | Do Not Call registry; mandatory breach notification |
| **PIPL** | China | Strict cross-border transfer rules; data localization |
| **UK GDPR** | United Kingdom | Post-Brexit UK version; ICO oversight |

## DPA Review Checklist

### Required Elements (GDPR Article 28)
- Subject matter and duration
- Nature and purpose of processing
- Type of personal data
- Categories of data subjects
- Controller obligations and rights

### Processor Obligations
- Process only on documented instructions
- Confidentiality commitments
- Appropriate security measures
- Sub-processor requirements (authorization, notification, liability)
- Data subject rights assistance
- Breach notification without undue delay
- Deletion or return on termination
- Audit rights

### International Transfers
- Transfer mechanism identified (SCCs, adequacy, BCRs)
- Current EU SCCs (June 2021 version)
- Transfer impact assessment completed
- UK addendum if UK data in scope

## Data Subject Request Handling

### Request Types
- Access, rectification, erasure, restriction, portability, objection, opt-out of sale/sharing

### Response Timelines

| Regulation | Acknowledgment | Response | Extension |
|---|---|---|---|
| GDPR | Promptly | 30 days | +60 days |
| CCPA/CPRA | 10 business days | 45 calendar days | +45 days |
| UK GDPR | Promptly | 30 days | +60 days |

### Common Exemptions
- Legal claims defense
- Legal obligations requiring retention
- Public interest
- Litigation hold
- Regulatory retention requirements

## Tips

1. **Be specific** — describe the actual planned activity
2. **Include the geography** — compliance requirements vary by jurisdiction
3. **Mention the data** — what personal data is involved drives most requirements
