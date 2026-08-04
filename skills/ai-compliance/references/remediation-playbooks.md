# Remediation Playbooks

Quick-action guides for the most common AI compliance gaps.

---

## Playbook R-1: No Data Processing Agreement (DPA) with AI Vendor

**Frameworks:** GDPR Art.28, ISO A.4.2, NIST GOVERN 6
**Severity:** HIGH

**Steps:**
1. Identify the vendor's DPA offering — most major vendors have standard DPAs available online (OpenAI, Microsoft, Google, Grammarly all publish DPAs)
2. Download/request the vendor's standard DPA
3. Route to Legal for review — standard DPAs typically acceptable for non-regulated data
4. Execute DPA — usually via vendor portal or signed PDF
5. Document execution date and store in vendor contract management system
6. If vendor has no DPA available → escalate to block the tool until resolved
7. For EU operations: confirm Standard Contractual Clauses (SCCs) are included or available
8. Log in AI inventory under "DPA in Place: Yes"

**Timeline:** Target 5–10 business days
**Owner:** Legal / Procurement with ISAI support

---

## Playbook R-2: Credentials Found in AI Prompts

**Frameworks:** NIST MEASURE 2.7, ISO A.8.2
**Severity:** HIGH — treat as potential credential compromise

**Immediate (within 1 hour):**
1. Pull the specific event(s) from webhook_events — identify user, tool, timestamp, and what credential was entered
2. Rotate the credential immediately — assume compromised
3. Check vendor data retention policy — was the prompt stored?
4. If stored: contact vendor to request deletion; document request
5. Review access logs for the rotated credential — any unauthorized use?
6. Notify ISAI lead and security team

**Remediation:**
7. Update DLP rules to catch that credential pattern if not already covered
8. Conduct targeted awareness session with the user
9. Implement secrets management (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault)
10. Add to acceptable use policy: credentials are strictly prohibited in AI tools
11. Document in AI incident log

---

## Playbook R-3: No Human Oversight for Consequential AI Decisions

**Frameworks:** EU AI Act Art.14, ISO A.2.2, NIST GOVERN 1.2
**Severity:** MEDIUM–HIGH

**Steps:**
1. Define what constitutes a "consequential decision" for the AI system (financial recommendations, HR decisions, security alerts acted upon, etc.)
2. Map current workflow — where does AI output feed directly into action without human review?
3. Insert mandatory review checkpoints:
   - For reports: add "AI-generated — verify before acting" disclaimer
   - For automated actions: require human approval step before execution
   - For recommendations: require named reviewer sign-off
4. Document the oversight process formally (who reviews, what criteria, escalation path)
5. Train users on the review requirement
6. Implement technical controls where possible (approval workflows, dual sign-off)
7. Log oversight evidence for audit purposes

---

## Playbook R-4: Untrained Users with AI Access

**Frameworks:** ISO A.2.4, NIST GOVERN 2
**Severity:** HIGH (current fi.com gap: 89% untrained)

**Steps:**
1. Pull list of active AI users from webhook_events who lack training_completions records
2. Segment by usage volume — prioritize heaviest users
3. Assign training in LMS with a hard deadline (recommend 2 weeks)
4. Set technical enforcement date: after deadline, AI tool access is blocked until training complete
5. Communicate to users and their managers — frame as protection, not punishment
6. Coordinate with IAM to implement access block for non-completers on deadline date
7. Track completion weekly; report to CISO
8. For new hires: gate AI access at onboarding until training complete

**Quick wins:** Send targeted email to top 20 untrained heavy users immediately

---

## Playbook R-5: No AI System Inventory

**Frameworks:** ISO A.5.1, NIST MAP 1.6, EU AI Act Art.11
**Severity:** MEDIUM

**Steps:**
1. Use `references/ai-inventory.md` as the template
2. Run a discovery process:
   - Query webhook_events for all unique genai_app_name values
   - Survey department heads for AI tools in use
   - Check SaaS spend/procurement records for AI vendor payments
   - Review browser extension data for AI site categories
3. Populate inventory for each discovered tool
4. Assign ownership — each tool must have a named owner
5. Publish inventory to ISAI team
6. Establish intake process: no new AI tool without inventory registration
7. Review and update quarterly

---

## Playbook R-6: Secrets/Credentials in Cron Jobs or Config Files

**Frameworks:** NIST MEASURE 2.7, ISO A.8.2
**Severity:** HIGH

**Steps:**
1. Audit all config files, cron job payloads, and environment files for plaintext credentials
2. Move credentials to a secrets manager:
   - Linux: use environment variables sourced from a secured `.env` file (chmod 600)
   - Better: HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault
   - Quick option: store in `/etc/openclaw/secrets.env` with strict permissions, source at runtime
3. Rotate all credentials that were stored in plaintext — assume exposed
4. Implement secret scanning in CI/CD pipeline (e.g., GitGuardian, truffleHog)
5. Add pre-commit hook to catch secrets before they're committed
6. Document secret management approach in runbook

**Quick fix for OpenClaw specifically:**
```bash
# Create secured env file
sudo mkdir -p /etc/openclaw
sudo nano /etc/openclaw/secrets.env
# Add: DB_PASS=... SMTP_PASS=...
sudo chmod 600 /etc/openclaw/secrets.env
sudo chown bcaddy:bcaddy /etc/openclaw/secrets.env
```

---

## Playbook R-7: No Vendor Risk Assessment on File

**Frameworks:** ISO A.4.2, NIST GOVERN 6
**Severity:** MEDIUM

**Steps:**
1. Use `references/vendor-assessment.md` questionnaire
2. Prioritize by tool risk level — start with Perplexity, ChatGPT (highest usage + risk)
3. Gather publicly available information first (SOC 2 reports, privacy policies, security pages)
4. Send formal questionnaire to vendor security/compliance contact
5. Score responses using scoring guide
6. Document findings and risk rating
7. Store in vendor risk management system
8. Set annual review reminder
9. Update AI inventory with assessment date and outcome

---

## Playbook R-8: No Acceptable Use Policy

**Frameworks:** ISO A.2.3, NIST GOVERN 1.1
**Severity:** HIGH

**Steps:**
1. Use `references/aup-template.md` as starting point
2. Customize for firm: fill in [FIRM], [CONTACT], [LINK] placeholders
3. Review with Legal for regulatory accuracy (especially MNPI section for finserv)
4. Review with HR for enforcement/disciplinary language
5. CISO approval
6. Publish to intranet/policy portal
7. Require acknowledgment from all employees (LMS quiz or e-signature)
8. Communicate launch via all-hands or department briefings
9. Update onboarding to include AUP sign-off before AI access granted
