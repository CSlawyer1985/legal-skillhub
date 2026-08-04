# Contract Alerts & Deadline Tracking

## Alert Schedule

Set reminders at multiple intervals before key dates:

| Event Type | Alerts At |
|------------|-----------|
| Pending signature | 7, 3, 1 days (since sent) |
| Contract expiration | 90, 60, 30, 14, 7 days |
| Auto-renewal deadline | 60, 30, 14 days (before notice cutoff) |
| Free trial ending | 7, 3, 1 days |
| Payment due | 7, 3, 1 days |
| Deliverable deadline | 14, 7, 3, 1 days |
| Insurance renewal | 60, 30 days |
| Lease renewal | 90, 60, 30 days |

---

## Priority Levels

| Priority | Criteria | Alert Style |
|----------|----------|-------------|
| **Critical** | Within 7 days, financial impact | Urgent notification |
| **High** | Within 30 days, action required | Daily reminder |
| **Normal** | 30-90 days out | Weekly summary |
| **Info** | >90 days | Monthly digest |

---

## Dashboard Views

### Pending Signatures
```markdown
## Awaiting Signature

| Contract | Status | Sent | Days Pending |
|----------|--------|------|--------------|
| NDA - Acme | pending-them | Feb 10 | 3 days |
| Lease renewal | pending-us | Feb 8 | 5 days |
```

### Expiring Soon (30 days)
```markdown
## Expiring This Month

| Contract | Expires | Action Needed | Notice Deadline |
|----------|---------|---------------|-----------------|
| Netflix | Mar 15 | Cancel or renew | Mar 1 |
| Office lease | Mar 31 | Negotiate renewal | Feb 28 |
```

### Upcoming Payments
```markdown
## Payments Due

| Contract | Amount | Due Date | Status |
|----------|--------|----------|--------|
| Adobe CC | €54.99 | Mar 1 | Auto-pay |
| Contractor | €2,500 | Mar 5 | Invoice sent |
```

### Action Items
```markdown
## Requires Attention

- [ ] Review Netflix price increase (effective Apr 1)
- [ ] Send termination notice for gym (deadline Mar 15)
- [ ] Collect signature on NDA amendment
```

---

## Auto-Renewal Trap Detection

When extracting contract terms, specifically flag:

1. **Silent renewals** — No notification, just charges
2. **Long renewal terms** — 1-year auto-renewal vs month-to-month
3. **Price escalation** — "May adjust rates upon renewal"
4. **Early cutoff** — Notice required 60+ days before

For each auto-renewal contract, create a separate alert for the *notice deadline*, not just expiration.

---

## Integration Points

Track dates for calendar sync:
- Export critical deadlines to calendar app
- Create recurring check-in reminders
- Link to contract file from calendar event

---

## Maintenance

Weekly: Review expiring contracts dashboard
Monthly: Check for any missed extractions (contracts without dates)
Quarterly: Audit alert settings, adjust lead times based on experience
