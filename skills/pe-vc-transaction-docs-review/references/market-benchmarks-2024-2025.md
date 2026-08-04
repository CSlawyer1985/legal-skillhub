# Market Benchmarks 2024-2025

The filename matches the two principal annual datasets used for this benchmark.
Verification date: 2026-07-10. Independently verify historical figures before
high-stakes reliance or updates.

Use this as negotiation context, not legal authority. User-facing outputs must refer to the source only as "historical statistics for comparable VC/PE projects" or similar. Do not name the underlying report source.

Default rule: use the 2025 current-year statistic as the primary anchor. Where this file gives exact comparable 2024 and 2025 figures, use the 2024/2025 two-year average. Where 2024 is unavailable or not comparable, use 2025 only and mark that internally.

## Data Completeness Gate

The structured companion contains exactly 23 unique benchmark topics. It is a
complete JSON object, not a clipped preview: every topic must have a non-empty
`id`, `aliases`, `benchmark`, and `review_use`. Before release or delivery,
`scripts/validate_skill_consistency.py` parses the entire file, rejects missing
or duplicate topics, and confirms all 23 expected IDs. A visible preview being
shortened by a platform must not be treated as source-data truncation.

## Structure Baseline

| Metric | 2024 | 2025 | Benchmark |
|---|---:|---:|---:|
| RMB/onshore structure | 73.58% | 66.51% | 70.05% |
| Offshore/USD structure | 26.42% | 33.49% | 29.96% |
| RMB currency | 67.88% | 64.62% | 66.25% |
| USD currency | 30.05% | 34.43% | 32.24% |
| Offshore VIE | 33.33% | 40.85% | 37.09% |
| Offshore direct holding/non-VIE | 66.67% | 59.15% | 62.91% |
| Onshore pure domestic structure | 64.79% | 73.05% | 68.92% |
| Onshore foreign-invested structure | 35.21% | 26.95% | 31.08% |
| Early stage rounds (seed/angel/Pre-A) | 44.04% | 40.56% | 42.30% |

2025-only structure notes:

- In onshore structures, 87.20% of financing subjects were limited liability companies and 10.40% were joint stock companies.
- In 24.76% of 2025 projects, the current-round investors held less than 5% post-closing.
- Nearly 40% of all 2025 projects involved state-owned or government-backed investors; in onshore projects, the proportion exceeded 50%.
- 11.71% of 2025 projects involved listed-company investors or their SPVs; among them, Hong Kong-listed companies were 45.83% and PRC A-share listed companies were 37.50%.
- 2025 project operating locations remained concentrated in Beijing/Shanghai/Shenzhen, but Suzhou and Hangzhou continued rising.

## Clause Benchmarks

| Clause | Benchmark | Review use |
|---|---|---|
| Preemptive right | 2025: overall 93.40%, RMB 94.33%, offshore 91.55%; absolute-ratio allocation 73.23%; over-allotment 56.06%. 2024/2025 average: overall 93.08%, absolute allocation 74.33%, over-allotment 56.80%. | Missing preemptive rights are still unusual. Company side may accept absolute-ratio allocation and narrow over-allotment; investor side should preserve pro rata protection and over-allotment. |
| ROFR | 2025: overall 89.15%, RMB 91.49%, offshore 84.51%; ordinary-share transfer/investor ROFR 89.95%; any-shareholder transfer ROFR 9.52%; relative-ratio allocation 81.18%; over-purchase 54.12%. | Founder/common share transfer restrictions remain market-standard but 2025 frequency declined. Company side should add permitted transfers and competitor/investor-transfer carve-outs. |
| Co-sale | 2025: overall 88.21%, RMB 90.07%, offshore 84.51%; change-of-control special co-sale 22.46%. | Check sequencing with ROFR and formulas. Company/founder side should resist overbroad co-sale on small permitted transfers; investor side may still ask for change-of-control full tag. |
| Redemption right | 2025: overall 79.72%, RMB 86.52%, offshore 66.20%, a nine-year low; material breach trigger 94.08%; cure period for material breach 59.75%; QIPO trigger 83.43%; cross-trigger 33.73%. | Redemption remains a key exit clause, especially in RMB deals, but should not be described as near-universal. RMB deals need enforceability, capital-reduction, share-transfer, and founder-liability analysis. |
| Redemption obligors | 2025: only 16.57% of redemption clauses made the company the sole obligor; company-only was 9.84% in RMB deals and 34.04% in offshore deals. Founder involvement in redemption obligations increased. | Investor side should seek founder support where company redemption is uncertain. Founder side should request specified triggers, cure periods, second-ranking liability, and equity/equity-value caps. |
| Redemption price | 2025: investment amount plus simple/compound interest 86.98%; fixed-multiple-only average 100%; simple interest avg 8.03%; compound interest avg 8.33%. | Prices materially above these figures need negotiation and enforceability comments. Align redemption price with liquidation preference and avoid double high-return economics. |
| Anti-dilution | 2025: overall 85.85%, RMB 85.82%, offshore 85.92%; weighted-average formula 79.12% overall, RMB 74.38%, offshore 88.52%; full ratchet 20.88%. | Full ratchet is a strong investor position. Company side should request broad-based weighted average and carve-outs; RMB implementation must specify nominal issuance, founder transfer, or cash compensation. |
| Drag-along | 2025: overall 60.85%, RMB 58.16%, offshore 66.20%; investor-only drag approval 31.01%; founder/founder-director approval included 52.71%; trigger by time/valuation plus shareholder approval 41.86%, shareholder approval only 23.26%, time plus valuation 19.38%. | Offshore deals still use drag more often. Company side should request valuation/time/shareholder approval and founder consent; investor side should preserve a workable sale path. |
| Preferred dividends | 2025: no preferred dividend 62.26%; if a preferred dividend exists, 75.95% use priority ranking, 20.25% use a dividend rate, and 3.80% use both; rate bands: 5%-10% at 78.95%, 10%-15% at 15.79%. | Do not treat preferred dividend as required. High dividend rates need commercial-burden comments, especially if paired with redemption and liquidation return. |
| Protective provisions | 2025: overall 83.49%, RMB 81.56%, offshore 87.32%, a nine-year low; investor veto appears in 95.48% of protective-provision clauses; investor veto threshold 6.51%; founder veto 6.21% overall, RMB 3.48%, offshore 11.29%. | Protective provisions are common but threshold use fell in 2025. Company side should control reserved-matter list and deadlock risk; investor side should protect core matters without overreaching. |
| Investor board seat | 2024: investor director right 72.02%. 2025: report states a clear decline but does not give an extractable exact overall adoption percentage; among deals granting investor board seats, threshold use was 43.33%, with RMB 55.56% and offshore 25.00%; over 90% of entitled investors appointed directors at closing; director indemnity agreements appeared in 26.32%. | Do not assume every investor receives a seat. Thresholds are important, especially in multi-investor RMB deals. Check director indemnity, D&O insurance, observer rights, and Articles/SHA consistency. |
| ESOP | 2025: adopted plan 31.13%, reserved/planned plan 53.30%, no plan/reserve 15.57%; RMB adopted/reserved 85.11%, offshore adopted/reserved 83.10%; RMB plans used options 50% and restricted equity 48%; offshore plans used options 87.50%; 98% of RMB plans used holding platforms and all such platforms were limited partnerships. | Check pool size, pre/post-money treatment, approvals, leaver rules, grant form, holding-platform mechanics, and PRC tax/registration issues. RMB companies increasingly use restricted equity. |
| Liquidation preference | 2025: overall 88.68%, RMB 87.23%, offshore 91.55%; participating 80.85%, capped participating 3.29%; RMB participating 89.43%, offshore participating 64.62%; preference amount formula: investment plus interest 55.32%, multiple-only 24.47%, higher-of formula 18.62%; multiple avg 105.40%, simple interest avg 8.29%, compound interest avg 8.25%. | Participating preference is common but 2025 shows lower investor-friendly intensity, especially offshore. Company side may request non-participating or capped participating; investor side should align waterfall with Articles. |
| Founder transfer restrictions | 2025: transfer restriction 88.68%, RMB 92.91%, offshore 80.28%; 98.92% prohibit founder transfer during the specified period without investor consent; exceptions: limited percentage transfer 23.50% (avg about 4%), internal/family/trust transfer 49.18%, both exceptions 2.73%, no exception 24.59%. | Investor side should protect founder stability. Founder side should request permitted transfers, estate/planning carve-outs, and reasonable percentage caps. |
| Founder restricted equity | 2025: restricted founder equity 46.70%; 52.53% of restricted-equity cases appeared in seed/angel/Pre-A rounds and 23.23% in A rounds; vesting/release period 3-5 years in 90.91%. | Check good/bad leaver definitions, vested/unvested equity, purchase price, buyer, trigger events, and registration path. |
| Founder secondary sale | 2025: 11.32% of projects involved founder secondary sale, mostly in RMB structures; tax allocation in those deals: seller 66.67%, buyer/seller shared 8.33%, company 12.50%, unclear 12.50%; for onshore LLC founder secondary sales, 100% of transferred registered capital was fully paid. | Not mainstream but common enough to review. Check disclosure, tax allocation, old-share price, primary/secondary split, control implications, and unpaid capital transfer liability. |
| Information and inspection rights | 2025: information rights still around the long-term c.90% market level; information-right thresholds: offshore 28%, RMB 4.88%, average threshold 4.59%. Inspection right 66.82%; inspection thresholds: offshore 36.73%, RMB 9.78%, average threshold 4.26%. | Investor side should review reporting package and frequency. Company side should add confidentiality, thresholds, information firewall for strategic investors, and non-disruption limits. |
| R&W survival | 2025: 94.81% did not set express survival periods; RMB no-survival 96.45%, offshore no-survival 91.55%; where a survival period was set, 63.64% were 1-3 years. | Survival limits are company-friendly. Investor side should resist broad limitation, or accept only for non-fundamental warranties with fraud/fundamental carve-outs. |
| Indemnity | 2025: express indemnity 77.83%; indemnity cap 18.18%; basket/deductible 18.18%; neither cap nor basket 63.64%; company + founders joint/several arrangements 96.97%; founder personal cap by equity/equity value 72.67%, RMB 66.36%, offshore 88.46%. | Founder side should seek caps and carve-outs; investor side should protect fraud/fundamental warranties and collection path. Distinguish general company breaches from founder-caused breaches. |
| Investor transfer restrictions | 2025: 58.96% restrict investor transfers, RMB 60.99%, offshore 54.93%; absolute prohibition on transfer to company competitors rose to 25.45% in affected deals; investor investment/cooperation restrictions appeared in 5.19%. | Company side should review competitor and strategic-investor risks carefully. Financial investors need liquidity and affiliate/fund transfer carve-outs; strategic investors may need information firewalls. |
| MFN | 2025: existing/same-round MFN 25.59%; future-financing MFN 17.06%, both materially down from 2024. | Separate same-round/side-letter MFN from future-financing MFN. Future MFN should usually exclude senior economic rights from later rounds and can be tied to valuation/down-round triggers. |
| Registered capital contribution | 2025 onshore LLCs: founders fully paid registered capital pre-closing in 37.61%; not fully paid in 62.39%, of which 98.53% were not yet due. For unpaid founders, more than half of deals required payment within the Company Law transition/statutory period, 14.71% required a shorter period, 25% were silent, and most documents/articles did not expressly address shareholder forfeiture. | RMB reviews must check subscription status, contribution deadlines, acceleration, transfer liability for unpaid capital, forfeiture mechanism, articles consistency, and closing/post-closing covenants. |
| Governing law and dispute resolution | 2025: RMB deal documents used PRC law in 99.29%; offshore deal documents used Hong Kong law in over 70% and Delaware law in 16.90%; arbitration was selected in 93.87%. | For PRC disputes, review arbitration body, seat, interim measures/preservation, service, consolidation, and enforceability. 涉及中国法律相关事项，请咨询执业中国律师；涉及非中国法管辖事项，请咨询相应法域的执业律师。 |

## Clause Weighting

High-priority clauses for most reviews:

- Redemption, liquidation preference, anti-dilution, protective provisions, board seat, founder restrictions, ROFR/co-sale, preemptive right, registered capital contribution, information/inspection, indemnity, governing law/dispute resolution.

Medium-priority clauses:

- Preferred dividends, ESOP pool mechanics, investor transfer restrictions, MFN, founder secondary sales, valuation adjustment, strategic cooperation restrictions.

Always adjust priority by client side, round, structure, investor type, and whether the clause was newly changed.
