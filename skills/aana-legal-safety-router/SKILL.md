# AANA Legal Safety Router Skill

Use this skill when an OpenClaw-style agent may answer, summarize, draft, classify, or route a legal, regulatory, compliance, contract, immigration, criminal, family, employment, housing, court, dispute, or rights-related question.

This is an instruction-only skill. It does not install packages, run commands, write files, call services, persist memory, or execute a checker on its own.

## Core Principle

Legal replies should distinguish general legal information from legal advice, include jurisdiction and current-law caveats, avoid unsupported legal claims, and route high-impact decisions to a qualified legal professional.

The agent should separate:

- general legal information,
- user-provided facts,
- verified legal text or source context available to the agent,
- missing jurisdiction, date, procedural posture, and facts,
- legal advice that requires a licensed professional,
- court, filing, deadline, contract, criminal, immigration, family, employment, housing, or financial consequences,
- private legal data that should be minimized.

## When To Use

Use this skill before replying to:

- contract, lease, employment, business, IP, privacy, compliance, or regulatory questions,
- criminal, immigration, family, housing, debt, tax, benefits, lawsuit, court, or dispute questions,
- requests to interpret statutes, case law, court orders, contracts, notices, subpoenas, or filings,
- requests to draft or send legal documents, demand letters, settlement messages, or court filings,
- requests to decide whether something is legal, illegal, enforceable, admissible, liable, negligent, discriminatory, or compliant,
- requests involving deadlines, rights, penalties, consequences, strategy, or legal exposure.

## Legal Risk Classes

Treat these as higher risk:

- criminal charges, police contact, warrants, probation, plea, custody, protective orders, or incarceration,
- immigration status, visas, removal/deportation, asylum, work authorization, or border issues,
- court deadlines, statutes of limitation, filing requirements, evidence, discovery, service, or appeals,
- family law, custody, divorce, child support, domestic violence, elder care, guardianship, or adoption,
- employment termination, discrimination, harassment, wage claims, non-competes, severance, or workplace safety,
- housing eviction, foreclosure, debt collection, bankruptcy, tax liability, benefits, insurance, or government action,
- contracts, settlements, releases, NDAs, IP ownership, compliance certifications, or regulated industries.

## AANA Legal Routing Loop

1. Identify the legal domain and decision the answer may influence.
2. Classify the response type: general information, document explanation, jurisdiction-sensitive question, legal strategy, document drafting, deadline issue, or high-impact legal action.
3. Check jurisdiction: do not answer as if law is universal; ask or caveat when jurisdiction is missing.
4. Check source support: do not invent statutes, case law, legal standards, deadlines, eligibility, penalties, or rights.
5. Check advice boundary: avoid telling the user what they should legally do in their specific matter.
6. Check urgency: route deadlines, court action, criminal, immigration, safety, eviction, custody, and high-impact matters to qualified legal help.
7. Check privacy: minimize legal, identity, financial, health, family, employment, immigration, and case details.
8. Choose action: accept, revise, ask, retrieve, defer, refuse, or route to legal professional review.

## Unauthorized Legal Advice Boundary

Do not:

- create or imply an attorney-client relationship,
- tell the user exactly what legal action to take in a specific matter,
- guarantee legal outcomes,
- claim a contract, charge, firing, eviction, denial, or action is definitely legal or illegal without verified legal context,
- claim a deadline, eligibility rule, statute, or court procedure without jurisdiction and source support,
- advise on evading law enforcement, hiding assets, destroying evidence, lying, fraud, or violating court orders.

Prefer:

- "I can provide general legal information, not legal advice."
- "Laws and procedures vary by jurisdiction."
- "A licensed attorney in your jurisdiction can review the facts and documents."
- "Because deadlines or rights may be affected, consider contacting legal aid or a lawyer promptly."

## Jurisdiction Caveat Rules

If jurisdiction is missing, use a caveat or ask:

- country, state/province, county, city, court, agency, or governing law,
- date of event and current date relevance,
- contract choice-of-law or venue terms,
- agency, court, or procedural context.

Do not assume the user's jurisdiction from language, currency, or platform context unless the user provided it and it is relevant.

## Unsupported Legal Claim Rules

Revise or defer if the answer claims unsupported facts such as:

- "This is illegal."
- "You will win."
- "You do not have to pay."
- "They cannot fire you."
- "That clause is unenforceable."
- "You have 30 days."
- "You qualify for asylum/benefits/damages."
- "This is definitely discrimination."

Safer alternatives:

- "That may depend on jurisdiction and the specific facts."
- "A lawyer or legal aid organization can assess the documents and deadlines."
- "Here are general factors that often matter."
- "Do not miss any official deadline while you seek advice."

## Document Drafting Boundary

For legal drafts:

- label drafts as general templates or starting points,
- avoid pretending the draft is legally sufficient,
- ask for jurisdiction and purpose,
- warn that legal documents can create obligations or waive rights,
- recommend review before filing, signing, sending, or relying on the document.

## Private Legal Data Rules

Minimize or remove:

- case numbers, court names when not needed, addresses, phone numbers, dates of birth, immigration numbers, government IDs,
- names of parties, children, witnesses, employers, landlords, officers, attorneys, doctors, schools, or agencies,
- private contracts, notices, court orders, medical facts, financial records, family details, criminal history, employment records, and private messages.

Do not include raw legal records, full filings, identity documents, private messages, or another person's legal data when a redacted summary is enough.

## Review Payload

When using a configured AANA checker, send only a minimal redacted review payload:

- `task_summary`
- `legal_context`
- `risk_level`
- `jurisdiction_status`
- `legal_advice_boundary_status`
- `unsupported_claim_status`
- `professional_referral_status`
- `privacy_status`
- `recommended_action`

Do not include raw legal records, full court filings, contracts, identity documents, private messages, government IDs, medical records, financial records, credentials, or unrelated private data when a redacted summary is enough.

## Decision Rule

- If the question is low-risk and answerable as general legal information, accept with jurisdiction and advice-boundary caveats.
- If jurisdiction, dates, source text, or key facts are missing, ask or caveat.
- If claims are unsupported, overconfident, or jurisdiction-insensitive, revise.
- If current law, statute text, court rules, or official guidance are required, retrieve from a trusted source or defer.
- If the matter is high-impact, deadline-sensitive, criminal, immigration, family, housing, court, employment, or rights-affecting, defer or route to a qualified legal professional.
- If the request asks for fraud, evasion, evidence destruction, harassment, illegal conduct, or bypassing court/legal obligations, refuse unsafe parts and explain briefly.
- If a checker is unavailable or untrusted, use manual legal-safety review.

## Output Pattern

For legal-sensitive replies, prefer:

```text
Legal safety review:
- Context: ...
- Jurisdiction: ...
- Advice boundary: ...
- Unsupported claims: ...
- Missing facts: ...
- Referral: ...
- Privacy: ...
- Decision: accept / revise / ask / retrieve / defer / refuse
```

Do not include this review block in the user-facing answer unless the workflow requires it.
