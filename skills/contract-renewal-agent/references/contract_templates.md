# Contract Renewal Proposal Templates

These templates are used by the `draft_renewal_proposal` tool as structural guidance. The AI adapts them to the specific contract context.

---

## SaaS / Software Subscription

**Use when:** contract_type is SaaS, Software, Subscription, Platform

```
Subject: Renewal Proposal — [Product Name] Agreement

Dear [Counterparty],

Thank you for being a valued [Product Name] customer. Our current agreement expires on [expiration_date], and we look forward to continuing our partnership.

**Proposed Renewal Terms**
- Term: [12/24/36] months from [new start date]
- Annual Value: $[value] ([X]% adjustment from current $[current_value])
- Tier/Seats: [same / updated]
- Auto-renew: [Yes/No]

**What's included in this renewal**
- [Feature highlight 1]
- [Feature highlight 2]
- Continued access to [support tier]

**Next Steps**
Please review and respond by [30 days before expiry]. We're happy to schedule a call to walk through any questions.

Warm regards,
[Sender]
```

---

## Professional Services / Consulting

**Use when:** contract_type is Services, Consulting, Professional Services, Statement of Work

```
Subject: Services Agreement Renewal — [Project/Program Name]

Dear [Counterparty],

Our current services agreement expires on [expiration_date]. Based on the strong results delivered during this engagement, we'd like to propose the following renewal.

**Proposed Renewal**
- Term: [start date] – [end date]
- Scope: [same scope / updated scope description]
- Rate: $[hourly or monthly rate] (updated from $[previous rate] to reflect [CPI / expanded scope / market rates])
- Estimated Annual Value: $[value]

**Highlights from this engagement**
- [Deliverable or outcome 1]
- [Deliverable or outcome 2]

We're committed to delivering the same quality of service and look forward to the continued partnership. Let's connect by [date] to finalize terms.

Best,
[Sender]
```

---

## Licensing Agreement

**Use when:** contract_type is Licensing, IP License, Technology License

```
Subject: License Renewal Proposal — [License Name/Product]

Dear [Counterparty],

The license agreement for [licensed property/technology] expires on [expiration_date]. We value this licensing relationship and propose the following renewal terms.

**Renewal Proposal**
- License Term: [X] years from [start date]
- Licensed Territory: [same / updated]
- Annual Royalty / License Fee: $[value]
- Usage Rights: [same / updated description]
- Exclusivity: [Exclusive / Non-exclusive]

**Rationale for Proposed Terms**
[Brief justification — market rates, usage volume, relationship length]

Please indicate your acceptance or proposed modifications by [30 days before expiry].

Regards,
[Sender]
```

---

## Maintenance & Support Agreement

**Use when:** contract_type is Maintenance, Support, MSA, Service Level Agreement

```
Subject: Maintenance Agreement Renewal — [System/Product Name]

Dear [Counterparty],

Your current maintenance and support agreement for [system/product] expires [expiration_date]. To ensure uninterrupted coverage, we propose the following renewal.

**Coverage Summary**
- System/Product: [name]
- Coverage Level: [Standard / Premium / 24x7]
- Response SLAs: [Critical: Xh / High: Yh / Normal: Zh]
- Renewal Term: 12 months from [date]

**Annual Fee**
$[value] ([same / X% increase from current $[current_value]])

**What's covered**
- [Coverage item 1]
- [Coverage item 2]
- [Coverage item 3]

Continuous support coverage ensures [key risk avoided]. Please confirm by [date] to avoid any gap in coverage.

Best regards,
[Sender]
```

---

## Non-Disclosure Agreement (NDA)

**Use when:** contract_type is NDA, Confidentiality, MNDA

```
Subject: NDA Renewal — [Parties / Project Name]

Dear [Counterparty],

Our Non-Disclosure Agreement expires on [expiration_date]. Given our ongoing collaboration on [project/relationship], we'd like to extend the agreement to maintain appropriate confidentiality protections.

**Proposed Renewal**
- Renewed Term: [X] years from [expiration_date]
- Covered Information: [same definition / updated]
- Mutual / One-way: [same as current]

A renewal amendment is attached (or can be prepared upon your confirmation). This is a straightforward extension with no changes to substantive terms.

Please confirm by [date] or let us know if you'd like to discuss any modifications.

Thank you,
[Sender]
```

---

## Vendor / Supplier Agreement

**Use when:** contract_type is Vendor, Supplier, Procurement, Supply

```
Subject: Vendor Agreement Renewal — [Vendor Name / Product]

Dear [Counterparty],

Our vendor agreement expires on [expiration_date]. We've been pleased with the quality and reliability of [product/service] and wish to continue the relationship.

**Proposed Terms**
- Term: [X] months from [start date]
- Products/Services: [same / updated]
- Pricing: [same / updated pricing schedule attached]
- Payment Terms: Net [30/45/60]
- Minimum Commitment: $[amount] (if applicable)

**Items to Discuss**
- [Any pricing adjustments]
- [Scope changes]
- [Service level updates]

We'd like to finalize terms by [date]. Please let us know your availability for a brief review call.

Best,
[Sender]
```

---

## Template Customization Notes

The `draft_renewal_proposal` tool uses these templates as structural guidance. Claude will:

1. Identify the contract type from the stored record
2. Select the closest matching template
3. Fill in all known fields from the database record
4. Adapt the tone based on contract value and relationship notes
5. Generate a complete, ready-to-send proposal

For contracts not matching any template type, Claude generates a professional renewal letter using the core elements (term, value, scope, deadline).
