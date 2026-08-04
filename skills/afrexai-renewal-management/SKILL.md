# Contract & Subscription Renewal Management

Systematic framework for managing contract renewals, reducing involuntary churn, and maximizing renewal revenue. Covers SaaS subscriptions, service agreements, vendor contracts, and client retainers.

## When to Use

- Quarterly renewal pipeline review
- Building a renewal management process from scratch
- Reducing churn from missed or mishandled renewals
- Negotiating vendor contract renewals
- Forecasting renewal revenue

## Renewal Pipeline Framework

### 120-Day Renewal Cadence

| Days Out | Action | Owner | Deliverable |
|----------|--------|-------|-------------|
| 120 | Flag renewal in pipeline | Ops/CS | Renewal record created |
| 90 | Health check + usage review | CSM | Account health score |
| 60 | Renewal proposal drafted | Sales/CS | Pricing + terms doc |
| 45 | First outreach to customer | CSM | Meeting scheduled |
| 30 | Negotiation / upsell conversation | AE/CSM | Updated proposal |
| 14 | Final terms agreed | Legal/Sales | Contract ready |
| 7 | Signature reminder | Ops | DocuSign/PandaDoc sent |
| 0 | Renewal executed | Finance | Invoice generated |
| +7 | Post-renewal check-in | CSM | Confirmation + next QBR |

### Account Health Score (Pre-Renewal)

Rate each dimension 1-5:

| Dimension | Weight | Indicators |
|-----------|--------|------------|
| Product Usage | 25% | DAU/MAU ratio, feature adoption, login frequency |
| Support Health | 20% | Ticket volume trend, CSAT, escalations |
| Relationship | 20% | Exec sponsor access, NPS, referral willingness |
| Business Impact | 20% | ROI documented, expansion potential, strategic fit |
| Payment History | 15% | On-time payments, disputes, credit terms |

**Score interpretation:**
- 4.0-5.0: Auto-renew candidate, push multi-year
- 3.0-3.9: Standard renewal, address gaps before proposal
- 2.0-2.9: At-risk — executive intervention needed
- Below 2.0: Churn likely — prepare save offer or graceful exit

### Renewal Pricing Strategy

**Price increase guidelines by segment:**

| Segment | Safe Increase | Max Without Justification | Requires Business Case |
|---------|--------------|--------------------------|----------------------|
| Enterprise ($100K+) | 3-5% | 7% | 10%+ |
| Mid-Market ($25-100K) | 5-8% | 10% | 15%+ |
| SMB ($5-25K) | 8-12% | 15% | 20%+ |
| Self-Serve (<$5K) | 10-15% | 20% | 25%+ |

**Uplift justification framework:**
1. New features shipped since last renewal (list top 5)
2. Usage growth (% increase in seats/API calls/storage)
3. Market rate comparison (competitor pricing delta)
4. Cost-of-switching calculation for customer
5. ROI documentation (dollars saved or generated)

### Vendor Renewal Negotiation (Buy-Side)

When YOUR contracts are up for renewal:

**Pre-negotiation checklist:**
- [ ] Pull actual usage data (are you using what you're paying for?)
- [ ] Get 2-3 competitive quotes (even if you plan to stay)
- [ ] Calculate cost per unit vs. market benchmarks
- [ ] Identify contract terms to improve (payment terms, SLA, data portability)
- [ ] Know your BATNA (best alternative to negotiated agreement)

**Negotiation levers:**
| Lever | Typical Discount | When to Use |
|-------|-----------------|-------------|
| Multi-year commit | 15-25% | When vendor is strategic and stable |
| Upfront annual payment | 10-15% | When cash flow allows |
| Case study / reference | 5-10% | When your brand has marketing value |
| Competitive threat | 10-20% | When credible alternatives exist |
| Volume commitment | 10-30% | When usage is growing predictably |
| Off-cycle renewal | 5-10% | When renewing outside vendor's fiscal year-end |
| Bundle consolidation | 15-25% | When vendor has multiple products you could adopt |

### Renewal Revenue Forecasting

**Forecast categories:**
```
Committed Revenue = Signed renewals + auto-renewals with no churn signal
Probable Revenue = Health score 3.5+ with active engagement (weight: 85%)
At-Risk Revenue = Health score 2.0-3.4 or unresponsive (weight: 50%)
Churning Revenue = Health score <2.0 or explicit cancellation intent (weight: 10%)

Forecast = Committed + (Probable × 0.85) + (At-Risk × 0.50) + (Churning × 0.10)
```

**Monthly renewal dashboard metrics:**
- Gross Renewal Rate (GRR): Target >90%
- Net Revenue Retention (NRR): Target >110%
- Renewal pipeline coverage: 3x minimum
- Average days to close renewal: Target <30 from first outreach
- Price increase realization: % of proposed increases accepted

### Involuntary Churn Prevention

Payment failures cause 20-40% of SaaS churn. Prevention framework:

| Trigger | Action | Timeline |
|---------|--------|----------|
| Card expiring in 30 days | Email + in-app notification | Day -30 |
| First payment failure | Retry + email notification | Day 0 |
| Second failure | SMS + email + in-app banner | Day 3 |
| Third failure | Phone call from CS | Day 7 |
| Grace period warning | Final notice with deadline | Day 10 |
| Account suspension | Suspend with easy reactivation | Day 14 |
| Final cancellation | Data export + win-back offer | Day 30 |

### Save Offers (Last Resort)

When a customer explicitly wants to cancel:

| Customer Reason | Save Offer | Success Rate |
|----------------|------------|-------------|
| Too expensive | 20-30% discount for 3 months | 35-45% |
| Not using enough | Free onboarding session + usage plan | 25-35% |
| Switching to competitor | Feature roadmap preview + price match | 15-25% |
| Budget cuts | Downgrade to lower tier | 40-50% |
| Missing features | Beta access + feedback loop | 20-30% |
| Poor support experience | Dedicated CSM + SLA upgrade | 30-40% |

### Renewal Automation Checklist

- [ ] Auto-renewal clause in all contracts (with opt-out notice period)
- [ ] CRM renewal pipeline with automated stage progression
- [ ] Email sequences triggered at 90/60/30/14/7 days
- [ ] Dunning flow for failed payments (3-4 retries over 14 days)
- [ ] Usage reports auto-generated and sent to stakeholders monthly
- [ ] Health score calculated weekly from product analytics
- [ ] Renewal forecast updated in real-time from pipeline data
- [ ] Post-renewal survey sent within 48 hours of signing

### Annual Renewal Calendar Template

| Month | Renewals Due | ARR at Risk | Priority Accounts | Notes |
|-------|-------------|-------------|-------------------|-------|
| Jan | [count] | $[amount] | [list top 3] | Post-holiday — start outreach early Dec |
| Feb | [count] | $[amount] | [list top 3] | Fiscal year-end for some — budget conversations |
| Mar | [count] | $[amount] | [list top 3] | Q1 close — decision-makers available |
| ... | ... | ... | ... | Fill per your renewal schedule |

---

## Resources

- **Full industry context packs** with renewal playbooks for 10 verticals: [AfrexAI Context Packs](https://afrexai-cto.github.io/context-packs/) — $47 per industry
- **Calculate your AI automation ROI**: [Revenue Leak Calculator](https://afrexai-cto.github.io/ai-revenue-calculator/)
- **Set up your agent stack**: [Agent Setup Wizard](https://afrexai-cto.github.io/agent-setup/)
- **Bundle deals**: Pick 3 for $97 | All 10 for $197 | Everything Bundle $247
