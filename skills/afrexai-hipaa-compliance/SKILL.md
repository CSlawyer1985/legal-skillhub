# HIPAA Compliance for AI Agents

Generate HIPAA compliance checklists, risk assessments, and audit frameworks for healthcare organizations deploying AI agents.

## What This Skill Does

When activated, produce any of these deliverables based on user request:

### 1. Pre-Deployment Compliance Gate
- BAA requirements checklist for AI vendors
- PHI data flow mapping template
- Minimum Necessary standard application guide
- Risk assessment framework (45 CFR 164.308(a)(1))

### 2. Technical Safeguards (45 CFR 164.312)
**Access Controls:**
- Unique service account IDs for AI agents
- Emergency access procedures for system failures
- 15-minute auto-logoff configuration
- Role-based minimum necessary permissions

**Audit Controls:**
- PHI access logging (timestamp, user, action, data)
- 6-year retention compliance
- Anomaly detection on access patterns
- AI decision audit trails

**Transmission Security:**
- TLS 1.3 enforcement
- E2E encryption for patient comms
- Certificate pinning for API connections
- No PHI in URLs, query strings, or logs

### 3. AI-Specific Risk Matrix

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt injection → PHI leak | Critical | Input sanitization, output filtering, sandboxing |
| Model training on PHI | High | BAA prohibition, single-tenant deployment |
| Hallucinated medical info | Critical | Human-in-loop, confidence thresholds |
| Shadow AI with PHI | High | Approved tool registry, DLP rules |

### 4. Breach Response Timeline
- 0-1 hrs: Contain (disable agent, preserve logs)
- 1-24 hrs: Assess scope of PHI exposure
- 24-48 hrs: Document root cause, affected individuals
- Within 60 days: Notify HHS + individuals + media (if 500+)
- 30-90 days: Remediate, patch, retrain

### 5. Compliance by Use Case
Rate each AI deployment:
- Patient scheduling → Medium risk
- Billing/coding → High risk
- Clinical decision support → Critical risk
- Patient communication → High risk
- Medical records summarization → Critical risk

### 6. Penalty Reference
| Tier | Per Violation | Annual Cap |
|------|-------------|------------|
| Unknowing | $141 - $71,162 | $2,134,831 |
| Reasonable cause | $1,424 - $71,162 | $2,134,831 |
| Willful neglect (corrected) | $14,232 - $71,162 | $2,134,831 |
| Willful neglect (not corrected) | $71,162 | $2,134,831 |

Average healthcare breach cost: $10.93M (IBM/Ponemon 2025).

## Output Format
- Markdown checklist with status columns
- Risk matrix with impact/likelihood scoring
- Timeline tables for breach response
- Department-specific compliance cards

## Resources
- [Healthcare AI Context Pack — $47](https://afrexai-cto.github.io/context-packs/) — Full patient journey automation, revenue cycle, EHR integration patterns
- [AI Revenue Leak Calculator](https://afrexai-cto.github.io/ai-revenue-calculator/) — Find where manual processes cost you money
- [AI Agent Setup Wizard](https://afrexai-cto.github.io/agent-setup/) — Configure compliant AI agents in 5 minutes
