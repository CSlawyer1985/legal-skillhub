# ESI Protocol Drafter

**Platforms:** Claude · Openclaw · Codex
**Domain:** E-Discovery / Litigation Support

## Purpose

A conversational drafting assistant for litigation-support attorneys, e-discovery counsel, and paralegals preparing for a Federal Rule of Civil Procedure 26(f) meet-and-confer. Guides intake of case posture, custodians, data sources, scope, preservation, collection, search terms / TAR, privilege, production format, and inaccessible ESI, and produces a meet-and-confer-ready ESI Protocol draft plus the Rule 26(f) joint discovery plan section.

## When to Use

- Preparing for the Rule 26(f) meet-and-confer conference (must occur at least 21 days before the Rule 16(b) scheduling conference)
- Drafting or revising a stand-alone ESI Protocol to be filed with or referenced by the court's scheduling order
- Negotiating an ESI Protocol with opposing counsel and need a structured term-by-term position
- Pre-existing protocol is silent on TAR validation, inaccessible ESI, FRE 502(d) clawback, or format of production and disputes are emerging
- Counsel needs a gap audit before signing a draft circulated by the other side

## What It Does

1. Captures case posture: court, civil docket number, parties, claims and defenses, relevant date range, client side (producing / requesting / both), and any prior preservation actions
2. Walks the custodian universe (named custodians, non-custodial repositories, departed-employee data, third-party-held data) and a data-source inventory (corporate email, file shares, collaboration platforms, mobile, ephemeral messaging, cloud apps, structured data, voicemail, legacy systems)
3. Confirms scope and Rule 26(b)(1) proportionality limits (custodian caps, date range, file-type exclusions, deduplication scope, threading, email-family handling)
4. Pins down preservation and legal-hold posture (hold issuance date, scope, custodian acknowledgments, suspension of auto-delete, mobile and ephemeral-messaging posture)
5. Walks collection and processing terms (forensic vs. targeted collection, hash verification, time-zone normalization, de-NIST, dedup, near-dup, email threading)
6. Negotiates search-term and TAR / CAL workflow with validation requirements (hit reports, sampling, recall / precision, elusion testing, control-set workflow)
7. Locks privilege workflow including FRE 502(d) clawback order, log format (metadata or categorical), and treatment of inadvertent production
8. Locks production format (TIFF + load file vs. native + metadata fields, fielded metadata list, OCR, bates, redaction format, audio/video, spreadsheet and presentation native rules, color-image rules)
9. Addresses Rule 26(b)(2)(B) inaccessible ESI and burden-shifting (backup tapes, legacy systems, structured-data extracts, foreign-data posture)
10. Runs a gap audit against the most common late-emerging Rule 26(f) failure points and emits a pre-conference Q&A worksheet plus a clean ESI Protocol draft

## Note

This skill drafts the ESI Protocol and the discovery-plan section. It does not give legal advice on case-specific proportionality, work-product, or privilege calls; the supervising attorney must review and sign. Cross-border data transfer (GDPR / cross-border discovery / Hague Convention), criminal-matter ESI, and ITAR / CUI / classified data require specialized counsel and are flagged but not resolved by the skill. Never paste actual privileged content, credentials, custodian PII beyond initials, or matter-protected material into examples.

## Feedback & Contributions

Found a gap or have a suggestion? [Open an issue or PR](https://github.com/archlab-space/Open-Skill-Hub/issues) — improvements are welcome.
