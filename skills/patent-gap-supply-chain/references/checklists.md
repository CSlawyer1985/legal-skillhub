# Checklists and Confidence Rules

## Alternative-Hypothesis Checklist

For each inference, check each item and explicitly exclude alternative explanations. List unexcluded ones in the report's "Alternative hypotheses" section.

### Alternative explanations for the patent gap
- [ ] Does A's patent gap stem from a cross-licensing agreement? (check announcements / news)
- [ ] Did A inherit T usage rights via an acquisition? (check M&A history)
- [ ] Does T belong to a patent pool? (e.g., Avanci, MPEG-LA, Via Licensing)
- [ ] Is there an open-source implementation of T? (check open-source projects)
- [ ] Does A hold T patents via a subsidiary / affiliate? (check related-entity patents)

### Alternative explanations for "B entered the supply chain"
- [ ] Is B an NPE (non-practicing entity)? If so, B licenses only and is not in the supply chain
- [ ] Does A use B's patent indirectly via a third-party module? The third party is the supplier; B is its upstream
- [ ] Is B only a patent licensor with no physical transaction with A?
- [ ] Is the A-B tie purely financial investment, not business cooperation?

## Counter-Intelligence Checklist

If the subject has counter-intelligence awareness, it may use these means to hide the real supply chain. Check each:

### Patent-ownership side
- [ ] Is B's patent ownership abnormally dispersed? (multiple shell companies / affiliates holding separately)
- [ ] Is there a shell company set up specifically to hold patents? (low registered capital, no real operations, abnormal address)
- [ ] Are patent transfers frequent? (possibly to obscure true ownership)

### A's patent-strategy side
- [ ] Does A deliberately not file patents to hide its tech roadmap? (the "gap" may be an active choice, not passive dependency)
- [ ] Do A's patent filings mismatch its actual product technology? (decoy filings)

### Anomaly signals
- [ ] Is A's supplier-disclosure abnormally terse or deliberately vague?
- [ ] Are key technical staff employed via labor dispatch / outsourcing rather than directly? (hiding talent flow)
- [ ] Are there related entities with frequent changes of company name / legal representative / shareholders?

If any anomaly exists → flag "counter-intelligence risk" in the report, raise vigilance, and recommend field research or primary-source verification.

## Confidence Scoring Rules

### Per-lead confidence

| Lead | High | Medium | Low |
|------|------|--------|-----|
| Patent ownership | B holds T's core patents with valid timeline | B holds T-related patents but timeline is questionable | T patents found but owner unclear |
| Corporate affiliation | JV / mutual investment | Executive overlap | Same address / same legal rep (weak) |
| Talent flow | Multiple B technical staff joined A | Single key person joined | Job postings only mention B background |
| Procurement | B directly named as supplier | B's category mentioned | Category-related but no clear pointer |
| Product teardown | Physically confirmed B component | Teardown report mentions but unconfirmed | No teardown report |

### Overall confidence

- **High**: ≥2 high-confidence leads corroborating
- **Medium**: 1 high + 1 medium corroborating, or multiple medium leads partially corroborating
- **Low**: only 1 lead hit, or leads contradict each other
- **Cannot infer**: 0 leads hit
