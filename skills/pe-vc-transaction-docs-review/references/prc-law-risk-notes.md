# PRC Law and Enforcement Risk Notes

Use this file for legal/enforcement issues. Legal basis is not mandatory for purely commercial comments, but is mandatory for issues under this file.

Before relying on a proposition below, apply `references/legal-authority-protocol.md`
and retrieve the current authority card with `scripts/legal_authority_lookup.py`.
Record the article/section, authority status, and verification date in the issue
log. The bullets below are issue-spotting prompts, not self-proving legal advice.

## Company Law Issues

Capital increase and preemptive rights:

- For PRC limited liability companies, statutory preemptive subscription and transfer rules may apply unless all shareholders agree otherwise.
- Check whether agreement provisions conflict with articles, shareholder resolutions, capital contribution records, or registration mechanics.

Capital reduction / redemption:

- Company redemption in RMB deals often requires capital reduction, share transfer, or other implementable route.
- Check shareholder approval, creditor notice, registration, solvency/capital maintenance, and whether performance is practically possible.
- If company redemption may fail, flag founder liability, second-ranking obligation, or alternative compensation path.

Articles vs shareholders agreement:

- Contractual rights may bind parties but not always work as corporate governance mechanics unless mirrored in articles/resolutions.
- Reserved matters, transfer restrictions, information rights, board rights, and liquidation mechanics should be checked against articles.

Contribution defects:

- Review founder and predecessor shareholder contribution obligations, acceleration, unpaid contribution transfer liability, and director/officer responsibility where relevant.
- Under the amended PRC Company Law, LLC shareholders generally must fully pay subscribed registered capital within the statutory period. Review whether the company must issue a written contribution demand, whether a grace period is specified, and whether shareholder forfeiture is available after default.
- For current-law pinpoints, check Company Law Articles 47, 51, 52 and 54 and,
  for pre-2024 companies, the State Council registered-capital transition
  regulation. Article 52's statutory grace period may not be shorter than sixty
  days; do not draft a shorter contractual process as if it were the statutory
  forfeiture process.
- If forfeited equity is not transferred or cancelled within the statutory period, check whether other shareholders may need to contribute proportionately; flag this risk when articles and transaction documents are silent.
- For transfers of unpaid subscribed equity, check whether the transferee assumes the unpaid contribution obligation and whether the transferor bears supplementary or joint liability depending on whether the contribution deadline has arrived and whether the transferee knew or should have known about the defect.
- Check Company Law Article 88 together with the temporal-effect interpretation
  and the Supreme People's Court reply on non-retroactivity of Article 88(1).
  Record the equity-transfer date before selecting the liability rule.
- For founder secondary sales in RMB LLCs, require proof that the transferred registered capital has been fully paid or allocate statutory contribution liability expressly.

## Civil Code / Contract Issues

- Conditions precedent and termination rights should be objective and administrable.
- Penalty/liquidated damages, default interest, indemnity, and liability caps should be reviewed for proportionality and enforceability.
- Material breach triggers need definition and cure periods where company/founder side.

## Redemption / Valuation Adjustment

Review:

- Trigger certainty.
- Obligor identity and legal capacity.
- Whether performance requires corporate action or third-party approval.
- Whether the remedy resembles debt or creates "fixed return" concerns in context.
- Whether taxes and payment mechanics are addressed.
- Whether an exercise window is stated, when it opens, how notice must be served,
  and what happens after expiry. The Supreme People's Court's 2024 Fada reference
  answer supports heightened drafting attention but is expressly nonbinding;
  do not state that six months is a statutory limitation period.
- Whether the price formula separately defines principal, contractual return,
  compounding, post-due interest/liquidated damages, tax and payment allocation.
  Check Civil Code Article 585 and the actual loss/adjustment risk before claiming
  cumulative recovery is enforceable.
- Whether a transfer, resignation or founder exit purports to shift or release
  the obligation. Check assignment/assumption, obligee consent, novation, release,
  security and continuing-liability language.
- Whether a side agreement with only some investors conflicts with corporate
  authority, amendment/waiver thresholds, MFN, equal treatment or other investors' rights.

## Founder Personal Liability

Founder-side concerns:

- Avoid unlimited joint/several liability for company breaches not caused by founders.
- Use misconduct-based liability, second-ranking obligation, equity/equity-value caps, and cure periods.

Investor-side concerns:

- Company-only obligation may be weak if company cannot reduce capital or lacks funds.
- Preserve founder liability for fraud, misrepresentation, contribution defects, misconduct, or obstruction.
- Where spouse consent, guarantee or marital-property recourse is requested,
  identify the exact undertaking and signatory capacity; do not infer liability
  from marriage alone.

## Dispute Resolution

Check:

- Arbitration clause validity and consistency across documents.
- Interim measures and preservation.
- Service addresses and deemed service.
- Consolidation or related proceedings where SPA/SHA/articles/side letters are all involved.
- For offshore documents, identify the governing-law and enforcement issues, then state: `涉及中国法律相关事项，请咨询执业中国律师；涉及非中国法管辖事项，请咨询相应法域的执业律师。`
- For PRC-law arbitration, use the 2025 revised Arbitration Law effective from
  2026-03-01. Check Articles 27 and 29 for the institution/scope elements,
  Articles 39 and 58 for interim measures, Article 72 for the current setting-
  aside period, and Article 81 for the seat of foreign-related arbitration.
- Do not treat the 2025 general Company Law judicial-interpretation consultation
  draft as binding. Re-check the official Supreme People's Court source before
  using any draft proposition.

## Regulated Investor and Cross-Border Issues

State-owned asset transactions:

- First determine whether the transaction is a public property-exchange transfer
  or capital increase within the 2025 operation rules. For an in-scope transaction,
  check approval, appraisal, announcement, selection, agreement content, real
  payment, governance and the applicable prohibitions on buyback, benefit
  compensation, nominee holding, disguised debt and price adjustment.
- Do not generalize those public-process restrictions to every investment by a
  state-owned entity. Record ownership chain, transaction type and approval route.

Insurance capital:

- Determine whether the investor and affiliates obtain control or joint control
  directly or on a look-through/aggregated basis. If the 2025 major-equity rule
  applies, check regulatory approval, own-funds and industry requirements,
  lending/guarantee and cross-holding prohibitions, control layers and anti-avoidance.

Outbound investment and foreign exchange:

- For PRC outbound investment after 2026-07-01, use the State Council regulation
  as the framework and separately map NDRC/MOFCOM/SAFE, security review, export
  control, data, tax, merger-control, state-asset and sector procedures.
- Use the 2025 SAFE reform notice for current direct-investment and reinvestment
  mechanics, but keep authenticity, account, use-of-proceeds and bank-practice
  checks. It does not eliminate Circular 37 analysis for relevant resident/SPV facts.
