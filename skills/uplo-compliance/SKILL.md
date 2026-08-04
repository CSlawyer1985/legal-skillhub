---
name: uplo-compliance
description: AI-powered compliance intelligence spanning legal, financial, and government regulatory requirements. Unified search across compliance obligations, audit findings, and regulatory filings.
---

# UPLO Compliance — Cross-Domain Regulatory Intelligence

Regulatory obligations do not respect department boundaries. A single product launch can trigger SEC disclosure requirements, GDPR data processing impact assessments, export control reviews, and state-level consumer protection filings simultaneously. UPLO Compliance unifies these fragmented compliance streams into one searchable knowledge layer, so your GRC team, outside counsel, and finance controllers are all working from the same ground truth.

## Session Start

Begin by loading your compliance identity. This determines which regulatory domains you can access (some filings are privileged or under litigation hold) and surfaces any active enforcement deadlines or consent decree obligations.

```
get_identity_context
```

Immediately review active directives — in compliance, a missed directive can mean a missed filing deadline:

```
get_directives
```

## When to Use

- Tracing which regulatory obligations attach to a new product line before go-to-market (e.g., does the product trigger CFPB oversight or only state AG jurisdiction?)
- Pulling the exact language from a prior consent decree to determine if a proposed business practice falls within its scope
- Preparing audit committee materials by gathering all open findings across SOX, HIPAA, and state privacy audits in one query
- Identifying which internal policies were updated after the last OCC examination and which remain unaddressed
- Checking whether a vendor's data processing agreement satisfies Article 28 GDPR processor requirements documented in your policy library
- Locating precedent from prior SEC comment letter responses when drafting a new 10-K disclosure
- Reviewing anti-money laundering (AML) suspicious activity report thresholds across different business units

## Example Workflows

### Regulatory Change Impact Assessment

A new state privacy law passes (e.g., Texas Data Privacy and Security Act). The compliance team needs to assess organizational readiness.

```
search_with_context query="data privacy consumer opt-out requirements current policies"
```

Compare the existing controls against the new requirements:

```
search_knowledge query="CCPA CPRA opt-out mechanisms implementation documentation"
```

Check if leadership has issued any directives about privacy program expansion timelines:

```
get_directives
```

Propose an update to the compliance obligation register:

```
propose_update target_table="entries" target_id="<obligation-register-entry-id>" changes='{"data":{"new_obligation":"Texas DPSA compliance deadline 2026-07-01"}}' rationale="New state privacy law enacted; obligation register needs updated deadline tracking"
```

### Multi-Jurisdiction Audit Preparation

External auditors are arriving for a combined SOX and data privacy audit. The compliance officer needs to assemble evidence across domains.

```
search_knowledge query="SOX Section 404 control testing results Q4 material weakness"
```

```
search_with_context query="data privacy audit findings remediation status open items"
```

Pull the organizational structure to identify control owners:

```
export_org_context
```

```
log_conversation summary="Assembled cross-domain audit prep materials covering SOX 404 controls and privacy audit remediation status" topics='["SOX","data-privacy","audit-prep"]' tools_used='["search_knowledge","search_with_context","export_org_context"]'
```

## Key Tools for Compliance

**search_with_context** — Compliance questions almost always require organizational context. "Who is responsible for this control?" or "Which department owns this filing obligation?" are answered by the graph traversal that enriches search results with entity relationships. Example: `search_with_context query="OFAC sanctions screening procedures responsible department"`

**get_directives** — The compliance team lives and dies by directives. Board resolutions, consent decrees, enforcement actions, and filing deadlines all surface here. Check at session start and before giving any compliance guidance.

**search_knowledge** — Targeted retrieval for known compliance artifacts: specific policy versions, audit finding numbers, regulatory filing drafts. Example: `search_knowledge query="Form ADV Part 2A brochure latest annual update"`

**flag_outdated** — Compliance documents have expiration dates. When you encounter a policy referencing a superseded regulation (e.g., a document still citing the EU-US Privacy Shield instead of the Data Privacy Framework), flag it immediately. Stale compliance documentation is a material risk.

**propose_update** — When you identify a gap between a regulatory requirement and the documented control, propose the fix. This enters the compliance review workflow with full audit trail.

## Tips

- Compliance queries often involve specific regulatory citations. Use precise references like "17 CFR 240.10b-5" or "GDPR Article 35" rather than paraphrasing — the extraction engine indexes these identifiers.
- Always check your clearance level at session start. Privileged legal communications, ongoing investigation materials, and draft regulatory responses are typically `restricted` and may not appear in results if your clearance is insufficient.
- When assembling audit evidence, use `export_org_context` to get the organizational snapshot that auditors will use as their map. Discrepancies between this snapshot and what auditors find on the ground create findings.
- Cross-domain compliance questions (e.g., "Does our AML program satisfy both FinCEN and EU 6AMLD requirements?") work best with `search_with_context` because the graph traversal connects financial regulation entries with legal analysis entries that may not share keywords.
