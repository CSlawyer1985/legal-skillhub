# Regulatory Compliance Audit

Run a full regulatory compliance audit for any business. Covers US, UK, and EU frameworks across 8 compliance domains with gap analysis, risk scoring, and remediation timelines.

## When to Use
- Annual or quarterly compliance reviews
- Pre-audit preparation (SOC 2, ISO 27001, GDPR, HIPAA, PCI DSS)
- New market entry requiring regulatory assessment
- Board or investor due diligence on compliance posture
- Post-incident compliance gap analysis

## How It Works

### Step 1: Identify Applicable Frameworks
Based on the business profile (industry, geography, data types, revenue), determine which frameworks apply:

| Framework | Triggers |
|-----------|----------|
| SOC 2 Type II | B2B SaaS, handles customer data |
| GDPR | Any EU customer data, EU employees |
| HIPAA | Any PHI (healthcare, benefits, wellness) |
| PCI DSS | Processes, stores, or transmits card data |
| ISO 27001 | Enterprise clients requesting certification |
| SOX | Public company or preparing for IPO |
| CCPA/CPRA | >$25M revenue OR >50K CA consumers |
| NIST AI RMF | Deploying AI/ML in production |
| UK DPA 2018 | UK operations or UK customer data |
| FCA/PRA | UK financial services |

### Step 2: 8-Domain Compliance Assessment

Score each domain 1-5 (1=non-existent, 5=mature):

**Domain 1: Data Governance**
- [ ] Data classification policy (public/internal/confidential/restricted)
- [ ] Data retention schedule with legal hold procedures
- [ ] Data processing agreements with all vendors
- [ ] Cross-border transfer mechanisms (SCCs, adequacy decisions)
- [ ] Data subject rights workflow (access, deletion, portability)
- [ ] Data breach notification procedure (<72hr GDPR, state-specific US)

**Domain 2: Access Control & Identity**
- [ ] Role-based access control (RBAC) implemented
- [ ] Multi-factor authentication on all critical systems
- [ ] Privileged access management (PAM) for admin accounts
- [ ] Quarterly access reviews with evidence retention
- [ ] Automated provisioning/deprovisioning tied to HR
- [ ] Service account inventory with rotation schedule

**Domain 3: Security Operations**
- [ ] Vulnerability management program (scan frequency, SLA by severity)
- [ ] Penetration testing (annual minimum, after major changes)
- [ ] Security incident response plan (tested within 12 months)
- [ ] Log retention meeting regulatory minimums (1yr SOC 2, 6yr SOX)
- [ ] Endpoint detection and response (EDR) on all endpoints
- [ ] Network segmentation between environments

**Domain 4: Business Continuity**
- [ ] Business impact analysis (BIA) current within 12 months
- [ ] Disaster recovery plan with defined RTO/RPO by system tier
- [ ] Backup testing (restore verified quarterly minimum)
- [ ] Pandemic/remote work continuity procedures
- [ ] Third-party dependency mapping for critical services
- [ ] Communication plan (internal + external + regulatory)

**Domain 5: Vendor & Third-Party Risk**
- [ ] Vendor risk assessment questionnaire (SIG Lite or equivalent)
- [ ] Tiered vendor classification (critical/high/medium/low)
- [ ] Annual vendor reviews for critical and high-tier vendors
- [ ] Right-to-audit clauses in critical vendor contracts
- [ ] Fourth-party risk assessment for critical vendors
- [ ] Vendor offboarding procedure with data return/destruction

**Domain 6: HR & Personnel Security**
- [ ] Background check policy (scope appropriate to role)
- [ ] Security awareness training (annual + phishing simulations)
- [ ] Acceptable use policy signed by all employees
- [ ] Code of conduct with reporting mechanisms
- [ ] Termination checklist (access removal, device collection, NDA reminder)
- [ ] Contractor/temp worker security requirements

**Domain 7: AI & Automation Governance**
- [ ] AI model inventory with risk classification
- [ ] Bias testing and fairness metrics for decision-making models
- [ ] Human-in-the-loop requirements defined per use case
- [ ] AI incident response procedures
- [ ] Transparency documentation (model cards, impact assessments)
- [ ] Training data governance and lineage tracking

**Domain 8: Financial & Reporting Controls**
- [ ] Segregation of duties in financial processes
- [ ] Change management procedures for financial systems
- [ ] Audit trail for all financial transactions
- [ ] Revenue recognition controls (ASC 606 / IFRS 15)
- [ ] Tax compliance calendar (federal, state, international)
- [ ] Internal audit schedule and findings tracking

### Step 3: Risk Scoring Matrix

For each gap identified:

| Likelihood | Impact | Risk Score | Action Timeline |
|-----------|--------|------------|-----------------|
| High | High | Critical | Fix within 30 days |
| High | Medium | High | Fix within 60 days |
| Medium | High | High | Fix within 60 days |
| Medium | Medium | Medium | Fix within 90 days |
| Low | High | Medium | Fix within 90 days |
| Low | Medium | Low | Next quarterly review |
| Low | Low | Informational | Annual review |

### Step 4: Remediation Roadmap

Build a 90-day plan:

**Days 1-30: Critical Gaps**
- Address any gaps with Critical or High risk scores
- Implement quick wins (policy updates, access reviews)
- Engage external counsel for regulatory interpretation if needed

**Days 31-60: Systematic Improvements**
- Deploy technical controls (MFA, EDR, log aggregation)
- Complete vendor risk assessments for critical vendors
- Update employee training program

**Days 61-90: Evidence & Documentation**
- Build evidence collection system for ongoing compliance
- Conduct internal audit of remediated areas
- Prepare board-ready compliance dashboard

### Step 5: Compliance Cost Benchmarks (2026)

| Company Size | Annual Compliance Budget | Key Cost Drivers |
|-------------|------------------------|-----------------|
| 10-50 employees | $30K-$80K | SOC 2 audit ($15-30K), tools ($10-20K), training ($5-10K) |
| 50-200 employees | $80K-$250K | + DPO/compliance hire ($80-120K), pen testing ($15-40K) |
| 200-1000 employees | $250K-$800K | + GRC platform ($50-150K), multiple audits, legal counsel |
| 1000+ employees | $800K-$3M+ | + Dedicated compliance team, continuous monitoring, regulatory filings |

**Cost of non-compliance (real examples):**
- GDPR fines: up to 4% global annual revenue (Meta: €1.2B, 2023)
- HIPAA: $100-$50K per violation, $1.5M annual cap per category
- PCI DSS: $5K-$100K/month until compliant + liability for breaches
- SOX: Criminal penalties, officer personal liability
- Average data breach cost: $4.88M (IBM 2024)

### Step 6: Output Format

Generate a compliance report with:
1. **Executive Summary** — Overall maturity score (1-5), top 3 risks, recommended budget
2. **Framework Applicability Matrix** — Which frameworks apply and current certification status
3. **Domain Scores** — 8 domains with gap counts and risk distribution
4. **Critical Findings** — Top 10 gaps ranked by risk score with remediation steps
5. **90-Day Roadmap** — Week-by-week action plan with owners and milestones
6. **Budget Estimate** — Compliance cost projection for next 12 months
7. **Board Dashboard** — One-page visual for board/investor reporting

## Industry-Specific Requirements

| Industry | Primary Frameworks | Special Considerations |
|----------|-------------------|----------------------|
| **SaaS/Technology** | SOC 2, GDPR, CCPA | AI governance, open source licensing |
| **Healthcare** | HIPAA, HITRUST, FDA (if devices) | PHI everywhere, BAAs required |
| **Financial Services** | SOX, PCI DSS, GLBA, FCA/PRA | Transaction monitoring, AML/KYC |
| **Legal** | ABA ethics, GDPR, privilege rules | Client confidentiality, conflict checks |
| **Construction** | OSHA, environmental, bonding | Safety records, subcontractor compliance |
| **E-commerce** | PCI DSS, CCPA/GDPR, FTC | Payment data, consumer protection, returns |
| **Manufacturing** | ISO 9001, OSHA, EPA, export controls | Supply chain compliance, ITAR/EAR |
| **Real Estate** | Fair Housing, AML, state licensing | Property data, transaction compliance |
| **Recruitment** | EEOC, GDPR (candidate data), ban-the-box | AI hiring bias (NYC Local 144), background checks |
| **Professional Services** | Industry-specific licensing, SOC 2 | Client data handling, engagement letters |

## 7 Compliance Audit Mistakes That Cost Companies Millions

1. **Treating compliance as annual** — It's continuous. Point-in-time audits miss 60% of gaps that develop mid-year.
2. **Ignoring AI governance** — NIST AI RMF and EU AI Act are here. Every production model needs documentation.
3. **Vendor risk as checkbox** — Your vendor's breach is your breach. Fourth-party risk is real.
4. **No evidence retention system** — If you can't prove compliance, you're not compliant. Automate evidence collection.
5. **Security ≠ compliance** — You can be secure and non-compliant, or compliant and insecure. Address both.
6. **Underbudgeting remediation** — Plan for 2x the estimated remediation cost. Surprises are the norm.
7. **Board reporting as afterthought** — Boards that see compliance dashboards quarterly make better risk decisions.

---

Get the full compliance implementation toolkit for your industry:
- **Browse all 10 industry context packs** → https://afrexai-cto.github.io/context-packs/
- **Calculate your AI automation ROI** → https://afrexai-cto.github.io/ai-revenue-calculator/
- **Set up your AI agent stack** → https://afrexai-cto.github.io/agent-setup/

Bundles: Playbook $27 | Pick 3 $97 | All 10 $197 | Everything $247
