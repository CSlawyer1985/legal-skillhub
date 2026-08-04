# Legal Authority Protocol

Use this protocol whenever an issue depends on legal validity, enforceability,
corporate authority, capital maintenance, contribution liability, arbitration,
limitations, or another legal rule. Do not use market statistics as a substitute
for legal authority.

## Authority Ladder

Prefer sources in this order and identify the level in the work product:

1. Effective law in an official legislation database or legislature website.
2. Effective administrative regulation or departmental rule from an official source.
3. Effective judicial interpretation or formal Supreme People's Court approval/reply.
4. Judicial policy document, official case database entry, guiding case, or court publication.
5. Secondary commentary, including law-firm articles and local digests.

Use secondary commentary to find issues and arguments, then verify the operative
rule against an official primary source wherever feasible.

Historical transaction documents and version chains are drafting evidence only.
They may reveal recurring negotiation controls, but they cannot establish current
law, current enforceability or current market frequency. Re-check the operative
authority and any transition rule as of the current review date.

## Status Gate

Assign one status to every authority relied on:

- `effective`: currently in force.
- `not yet effective`: promulgated but the effective date has not arrived.
- `draft - nonbinding`: consultation or draft text only.
- `superseded/repealed`: historical context only.
- `effective guidance`: current judicial policy or guidance, but not legislation
  or a judicial interpretation.
- `status unverified`: do not state a definitive legal conclusion.

Never present a draft, consultation paper, article, meeting minute, or FAQ as an
effective law or judicial interpretation. If status cannot be verified, write
`[pending legal research]` and state the question that must be checked.

## Authority Card

For each material legal proposition, record internally:

- Authority title and issuing body.
- Authority level and status.
- Promulgation and effective dates.
- Article/section or other pinpoint.
- Official URL or verified database citation.
- Date checked.
- Proposition supported.
- Temporal, entity-type, structure, or factual limitation.

Use `scripts/legal_authority_lookup.py <terms>` to retrieve the bundled authority
cards. Run it with `--check-freshness` before relying on the registry for a
high-stakes conclusion. A lookup result is a research starting point, not proof
that the cited rule governs the facts.

Run `scripts/refresh_legal_authorities.py --check-urls` for a machine-readable
schema, temporal-status, topic-coverage and official-URL health report. A 404 or
410 is a broken-source signal; TLS, anti-bot, redirect, rate-limit and server
failures are inconclusive and require manual official-source review. The script
never advances `last_verified` automatically. The registry's coverage matrix
must link every declared topic to at least one currently effective authority.

## Current Mandatory Checks

As last verified on 2026-07-13:

- The 2023 revised PRC Company Law is effective from 2024-07-01.
- The State Council registered-capital transition regulation is effective from
  2024-07-01 and must be checked for companies formed before that date.
- The Supreme People's Court temporal-effect interpretation and the later reply
  on non-retroactivity of Company Law Article 88(1) must be checked for historic
  equity transfers and contribution facts.
- The 2025 revised PRC Arbitration Law is effective from 2026-03-01. Review
  institution, scope, seat for foreign-related arbitration, interim measures,
  service, and the applicable arbitration rules under the current law.
- The general Company Law judicial interpretation published on 2025-09-30 is a
  consultation draft in the bundled registry. Do not treat it as binding unless
  a fresh official check confirms a final version.
- The Ninth Minutes can inform the validity/performance distinction for valuation
  adjustment and company redemption, but identify it as a judicial policy
  document and re-check the current Company Law and judicial authorities.
- The 2024 Supreme People's Court Fada reference answer on redemption exercise
  periods is official reference guidance, not legislation or a judicial
  interpretation. Use it to stress-test drafting; do not state that six months is
  a statutory hard limit.
- Foreign-investment matters require checks under the Foreign Investment Law,
  its implementation regulation, the current negative list, and security-review
  rules; offshore/SPV structures may also require SAFE Circular 37 analysis.
- Competition-sensitive transactions require a current merger-filing threshold
  check and fact-specific control/turnover analysis under the Anti-Monopoly Law.
- PRC outbound investment from 2026-07-01 requires the State Council outbound-
  investment regulation plus the applicable NDRC, MOFCOM, SAFE, security-review,
  export-control, data, tax, state-asset and sector rules.
- Apply the SAFE cross-border investment/financing reform effective from
  2025-09-15 to current funds-flow and registration steps, while retaining
  Circular 37 and other fact-specific foreign-exchange checks.
- For an in-scope public state-owned asset transfer or capital increase, check
  the 2025 transaction operation rules. Determine scope before applying the
  buyback, compensation, nominee-holding, disguised-debt or price-adjustment restrictions.
- For insurance capital that obtains control or joint control, check the 2025
  major-equity-investment rule, including approval, own funds, permitted industry,
  prohibited support, control layers and look-through treatment.
- Data-heavy or cross-border matters require current PIPL, Data Security Law,
  Cybersecurity Law, network-data regulation, and cross-border-data rule checks.

## Output Discipline

- Name official legal authorities and give a pinpoint when the user requests or
  needs a legal basis. The rule against naming the benchmark source does not
  apply to statutes, regulations, or judicial authorities.
- Separate three propositions: agreement text/fact, market context, and legal rule.
- State whether a conclusion is verified, pending research, draft-based, or
  fact-dependent.
- Do not claim that a clause is enforceable merely because it is common, or that
  it is uncommon merely because it may be difficult to enforce.
- Use this notice for legal matters: `涉及中国法律相关事项，请咨询执业中国律师；涉及非中国法管辖事项，请咨询相应法域的执业律师。`

## Freshness Trigger

Refresh official sources when any of the following applies:

- The registry is older than 90 days.
- The matter refers to a newer amendment, interpretation, regulatory notice, or case.
- The result depends on a transition date or historical legal fact.
- A draft authority may have become final.
- The client will rely on the conclusion for signing, enforcement, litigation,
  arbitration, capital reduction, or registration.
