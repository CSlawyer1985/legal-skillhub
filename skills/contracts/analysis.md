# Contract Analysis Patterns

## Key Term Extraction

On every new contract, extract to meta.md:

```markdown
# Contract: {name}

## Parties
- **Party A:** {name, role}
- **Party B:** {name, role}

## Signature Status
- **Status:** draft | pending-them | pending-us | executed
- **Sent:** YYYY-MM-DD
- **Signed by them:** YYYY-MM-DD
- **Signed by us:** YYYY-MM-DD
- **Fully executed:** YYYY-MM-DD

## Dates
- **Effective:** YYYY-MM-DD
- **Term:** {duration}
- **Expires:** YYYY-MM-DD
- **Auto-renews:** Yes/No — {renewal term}
- **Notice period:** {days} before expiration

## Value
- **Amount:** {total or recurring}
- **Payment terms:** {net 30, milestone, etc.}
- **Late fees:** {if specified}

## Key Clauses
- **Termination:** {how to exit, penalties}
- **Renewal:** {automatic or manual, rate changes}
- **Liability:** {caps, exclusions}
- **IP:** {who owns what}
- **Confidentiality:** {NDA terms if any}

## Notes
{User observations, flags, context}
```

---

## Common Clause Lookups

**Cancellation:**
- Notice period required
- Method (written, certified mail, online)
- Penalties or early termination fees

**Auto-renewal:**
- Renewal term length
- Price adjustment provisions
- Opt-out window

**Liability:**
- Cap amount (if any)
- Indemnification scope
- Insurance requirements

**Confidentiality:**
- Duration (often survives termination)
- Scope of covered information
- Permitted disclosures

---

## Red Flags to Detect

When analyzing, flag these patterns:

| Red Flag | Example | Action |
|----------|---------|--------|
| Unlimited liability | "Party shall indemnify for all claims" | Flag for review |
| Auto-renewal no notice | Renews without reminder option | Set early alert |
| Unilateral changes | "Terms may change at any time" | Document current version |
| Asymmetric termination | They can exit anytime, you can't | Flag for negotiation |
| Broad non-compete | Restricts unrelated work | Check scope carefully |
| Arbitration mandate | No court option | Note limitation |
| Data retention unclear | What happens to your data? | Clarify before signing |

---

## Search Patterns

Natural language queries the skill should handle:

- "What's my notice period for [contract]?"
- "When does [contract] expire?"
- "Find all contracts expiring in [timeframe]"
- "Who owns the IP in my contract with [party]?"
- "What's my liability cap with [client]?"
- "Show all NDAs I've signed"
- "List recurring payments across all contracts"
- "What are my obligations under [contract]?"
