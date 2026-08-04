# Contract Management by Role

## Consumer (Personal)

Focus: Subscriptions, services, insurance, memberships.

**Priority tasks:**
- Auto-renewal trap detection — Flag before annual renewals hit
- Free trial expiration tracking — Don't forget that "first month free"
- Cancellation procedure lookup — HOW to cancel, not just WHEN
- Price increase detection — Scan emails/updates for rate changes
- Plan comparison — When switching providers, compare against current terms

**Key extractions:**
- Monthly/annual cost
- Commitment period end date
- Auto-renewal date and notice period
- Cancellation method (online/phone/letter)
- Price lock guarantee expiration

---

## Landlord / Property Owner

Focus: Leases, service contracts, insurance per property.

**Priority tasks:**
- Unified calendar across all properties and tenants
- Rent increase eligibility tracking (when, how much, required notice)
- Tenant obligation comparison — Who handles what at each property?
- Service provider directory with contract terms
- Insurance coverage gap analysis across properties

**Organization:**
```
~/contracts/
├── properties/
│   ├── downtown-apt/
│   │   ├── lease-maria.pdf
│   │   ├── insurance.pdf
│   │   └── hoa.pdf
│   └── beach-condo/
└── vendors/
    ├── plumber-acme/
    └── property-mgmt/
```

**Key extractions:**
- Lease term and renewal options
- Security deposit amount and return conditions
- Maintenance responsibilities (landlord vs tenant)
- Notice periods for termination
- Rent amount and increase provisions

---

## Freelancer / Small Business

Focus: Client contracts, vendor agreements, business subscriptions.

**Priority tasks:**
- Payment milestone tracking — "Invoice when deliverable X is done"
- Deliverable deadline calendar — All commitments in one view
- IP ownership clarity — Who owns the work after delivery?
- Liability exposure summary — What's my max risk per client?
- Non-compete/exclusivity scan — Am I blocked from other work?

**Key extractions:**
- Payment terms (net 30, milestone-based, retainer)
- Deliverable descriptions and deadlines
- IP assignment or license-back clauses
- Indemnification scope
- Termination and kill fee provisions

**Alerts:**
- Payment due dates
- Deliverable deadlines
- Contract renewal windows
- Rate renegotiation opportunities

---

## Legal / Enterprise

Focus: High volume, multiple contract types, compliance requirements.

**Priority tasks:**
- Auto-classify by type (NDA, vendor, employment, etc.)
- Non-standard clause flagging vs templates
- Matter/client organization
- Deadline tracking (statute of limitations, filing dates)
- Version control with amendment linking

**Organization:**
```
~/contracts/
├── clients/
│   └── acme-corp/
│       ├── engagement-letter.pdf
│       └── matters/
│           ├── 2024-001/
│           └── 2024-002/
├── vendors/
├── employment/
└── templates/
```

**Advanced features:**
- Clause library lookup ("our standard arbitration language")
- Risk scoring (1-5 based on liability exposure)
- Compliance checklist (GDPR, insurance minimums)
- Executive summary generation
