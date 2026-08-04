# Security & Privacy Requirements

## Storage Rules

### Local-Only by Default

```
✅ REQUIRED
├── All contracts in ~/contracts/ (user-controlled)
├── Metadata in local files only
├── No cloud sync unless user explicitly enables
└── No network transmission of contract content

❌ PROHIBITED
├── Uploading to any cloud service
├── Sending contract text via messages
├── Including contract content in logs
├── Using external OCR services
```

### File Permissions

- Contracts folder: `chmod 700` (owner-only access)
- Individual files: inherit from folder
- Backups: warn if unencrypted backup detected

---

## Data Sensitivity

### What Contracts Contain

| Data Type | Sensitivity | Handling |
|-----------|-------------|----------|
| Names | Medium | Extract, don't expose in logs |
| Addresses | High | Extract, minimize storage |
| SSN / Tax IDs | **Critical** | Flag, don't extract |
| Bank accounts | **Critical** | Flag, don't extract |
| Salaries | High | Extract with caution |
| Signatures | High | Don't process |

### GDPR Considerations (EU)

- **Data minimization** — Only extract necessary metadata
- **Right to erasure** — Support full deletion on request
- **No automated decisions** — Don't auto-interpret legal meaning
- **Retention awareness** — Don't delete without user consent

---

## Legal Boundaries

### The Skill MUST NEVER:

1. **Interpret legal clauses** — Cannot say if something is "fair" or "standard"
2. **Provide legal advice** — Cannot recommend signing or not signing
3. **Assess legal risk** — Cannot score contracts as "safe" or "risky"
4. **Compare to standards** — Cannot say "this is unusual for the industry"
5. **Predict outcomes** — Cannot speculate on disputes
6. **Modify contracts** — Cannot suggest edits to legal language

### The Skill CAN:

1. ✅ Extract factual data (dates, amounts, parties)
2. ✅ Track deadlines and send reminders
3. ✅ Organize and search contracts
4. ✅ Show specific clauses when asked
5. ✅ Flag items for review ("this has an arbitration clause")
6. ✅ Aggregate costs across contracts

### Mandatory Disclaimers

When user asks legal questions:

> "I can show you the relevant clause, but for interpretation or advice, please consult a qualified attorney."

When flagging unusual terms:

> "This clause may be worth reviewing with a lawyer before signing."

---

## Confidentiality

### NDA-Aware Handling

- Treat ALL contracts as potentially confidential
- Never expose counterparty names in messages unless user requests
- Never share contract snippets outside the skill context
- If contract references NDA, flag as extra-sensitive

### Attorney-Client Privilege

- If contract folder contains legal correspondence, treat as privileged
- Don't analyze or summarize legal advice documents
- Safest approach: treat lawyer emails as opaque files

---

## Incident Response

### If Contract Exposed Accidentally

1. Don't panic — assess what was exposed
2. Identify affected parties
3. Consider notification obligations
4. Document the incident
5. Review and tighten access controls

### If User Requests Cloud Sync

- Warn about risks explicitly
- Recommend encryption before sync
- Don't enable by default
- Log that user acknowledged risks
