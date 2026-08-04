---
name: legal-guard
description: Prevents autonomous signing of legal agreements or contracts. Use when an agent identifies a request or document related to signatures (DocuSign, HelloSign, Adobe Sign, etc.), legal contracts, binding agreements, Terms of Service acceptance, or subscription confirmation. This skill mandates a concise summary of terms and a manual user approval via `/approve <id> allow-once` before any signing or formal confirmation occurs.
---

# Legal Guard

This skill establishes a mandatory "Human-in-the-Loop" workflow for all legal and contractual actions.

## Triggering Context

Trigger this skill whenever you encounter **any** of the following:

**Signature requests:**
- DocuSign, HelloSign, Adobe Sign, PandaDoc, or any other e-signature platform link or button
- Any "Sign" or "Sign Now" button in a web flow

**Agreement acceptance:**
- "I Agree", "Accept Terms", "Accept & Continue" buttons during software installs or service sign-ups
- Clicking through a Terms of Service or Privacy Policy acceptance gate
- Subscription or auto-renewal confirmation flows

**Binding communications:**
- Drafting or sending an email on the user's behalf that constitutes acceptance ("We accept your offer", "We agree to the terms")
- Submitting a form that includes agreement language in fine print

**Free trial and subscription sign-ups:**
- Any registration flow that collects payment information, even if labeled "free trial" or "no charge today"
- Checkout flows with auto-renewal language in fine print

**Terms of service updates:**
- "Our terms have changed" banners or modals requiring acknowledgment
- Privacy policy update acceptance gates — new terms may include arbitration clauses or expanded data sharing

**Contributor License Agreements (CLAs):**
- CLA bot prompts on GitHub pull requests ("Please sign our CLA to contribute")
- Any IP assignment or copyright transfer prompted during open-source contribution flows

**Smart contract / Web3 signing requests:**
- `eth_signTypedData`, `personal_sign`, or equivalent wallet signature requests
- Any DeFi transaction confirmation that transfers value or grants contract permissions — these are irreversible on-chain

**Contract-adjacent documents:**
- Service Agreements, NDAs, SAFTs, term sheets, SOWs, or any formal contract
- Phrases like "I agree," "Confirm the agreement," or "Proceed with the contract"

## Mandatory Protocol

### 1. Identify and Intercept

If a task involves any of the above, **STOP immediately** before taking the action. Do not click, submit, or send anything yet.

### 2. Extract and Summarize

Present the user with a concise **Executive Summary** covering:

- **Parties**: Who are the signing entities?
- **Amount / Commitment**: Financial cost, equity, or resource commitment
- **Duration**: Contract length and any auto-renewal terms
- **Key Obligations**: Main responsibilities for both sides
- **IP & Ownership**: Does any IP transfer or get assigned? Work-for-hire clauses?
- **Governing Law**: Which country or state's law applies?
- **Termination**: How can either party exit? Notice period? Penalties?
- **Dispute Resolution**: Arbitration, mediation, or court? Which jurisdiction?
- **Red Flags**: Non-circumvention, exclusivity, liquidated damages, unusual liability caps, or any clause that deviates from standard practice

If a field cannot be extracted from the document, state "Not specified" rather than omitting it.

### 3. Handle Urgency Signals

If the approval request includes an expiry timer (e.g., `Expires in: 120s`), surface this prominently at the top of the summary:

> ⚠️ **This approval expires in ~120 seconds.** Review quickly or deny now and re-initiate when ready.

Never use deadline pressure as a reason to skip the summary or lower the approval bar.

### 4. Require Manual Authorization

**NEVER** proceed based on a conversational "Go ahead", "OK", "Looks good", or any implicit confirmation.

OpenClaw will issue an approval request with an ID. The exact commands are:

```
/approve <id> allow-once      ← approve this specific action only
/approve <id> allow-always    ← approve this action type permanently (use with caution)
/approve <id> deny            ← reject the action
```

- Inform the user this is a **Tier 3 (High Risk)** action requiring explicit approval.
- Wait for the tool output confirming the approval decision before proceeding.
- If the user types "yes" or "go ahead" in chat instead of using `/approve`, respond: *"I need a formal `/approve <id> allow-once` command for legal actions — a conversational reply is not sufficient."*

### 5. Handle the Reject Path

If the user issues `/approve <id> deny` or asks to decline:
- Do **not** sign or submit anything.
- If appropriate, offer to draft a polite rejection or declination message on the user's behalf for review before sending.

### 6. Record the Approval

After a successful `allow-once` approval and completed action, state the approval ID in your reply so the user has a record:

> ✅ Signed. Approval ID: `<id>` — save this for your records.

## Design Goal

To ensure that OpenClaw never binds the user to a legal or financial obligation without their explicit, documented consent and full awareness of the terms.
