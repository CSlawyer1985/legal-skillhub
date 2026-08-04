---
name: vendor-check
description: Check the status of existing agreements with a vendor across all connected systems — CLM, CRM, email, and document storage — with gap analysis and upcoming deadlines. Use when onboarding or renewing a vendor, when you need a consolidated view of what's signed and what's missing (MSA, DPA, SOW), or when checking for approaching expirations and surviving obligations.
argument-hint: "[vendor name]"
---

# /vendor-check -- Vendor Agreement Status

Check the status of existing agreements with a vendor across all connected systems. Provides a consolidated view of the legal relationship.

**Important**: This command assists with legal workflows but does not provide legal advice. Agreement status reports should be verified against original documents by qualified legal professionals.

## Workflow

### Step 1: Identify the Vendor

Accept the vendor name. Handle variations:
- Full legal name vs. trade name
- Abbreviations
- Parent/subsidiary relationships

### Step 2: Search Connected Systems

Search in priority order:
- **CLM**: Active agreements, expired agreements, in-negotiation, amendments
- **CRM**: Account status, associated deals, contact information
- **Email**: Contract-related emails, NDA attachments, negotiation threads
- **Documents**: Executed agreements, redlines, due diligence materials
- **Chat**: Contract requests, legal questions, team discussions

### Step 3: Compile Agreement Status

For each agreement found:

| Field | Details |
|-------|---------|
| **Agreement Type** | NDA, MSA, SOW, DPA, SLA, License Agreement |
| **Status** | Active, Expired, In Negotiation, Pending Signature |
| **Effective Date** | When the agreement started |
| **Expiration Date** | When it expires or renews |
| **Auto-Renewal** | Yes/No, renewal term and notice period |
| **Key Terms** | Liability cap, governing law, termination provisions |
| **Amendments** | Any amendments or addenda on file |

### Step 4: Gap Analysis

```
## Agreement Coverage

[CHECK] NDA -- [status]
[CHECK/MISSING] MSA -- [status or "Not found"]
[CHECK/MISSING] DPA -- [status or "Not found"]
[CHECK/MISSING] SOW(s) -- [status or "Not found"]
[CHECK/MISSING] SLA -- [status or "Not found"]
[CHECK/MISSING] Insurance Certificate -- [status or "Not found"]
```

### Step 5: Generate Report

```
## Vendor Agreement Status: [Vendor Name]

**Search Date**: [today's date]
**Sources Checked**: [list of systems searched]

## Relationship Overview
**Vendor**: [full legal name]
**Relationship Type**: [vendor/partner/customer]

## Agreement Summary
### [Agreement Type] -- [Status]
- **Effective**: [date]
- **Expires**: [date]
- **Key Terms**: [summary]

## Gap Analysis
[What's in place vs. what may be needed]

## Upcoming Actions
- [Approaching expirations or renewal deadlines]
- [Required agreements not yet in place]
```

## Notes

- Flag agreements expired but with surviving obligations (confidentiality, indemnification)
- Highlight agreements approaching expiration within 90 days
- For vendor groups, ask whether to check specific entity or entire group
