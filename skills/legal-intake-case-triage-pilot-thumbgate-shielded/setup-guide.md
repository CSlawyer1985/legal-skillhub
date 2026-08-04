# Setup Guide: Legal Intake Pilot (20 Minutes)

## 1. CRM Connection (5 Mins)
- **Clio/MyCase:** Use the `MyCase` webhook connector in OpenClaw.
- **Clio API:** Add `CLIO_API_KEY` to your `.env`.

## 2. ThumbGate Configuration (5 Mins)
- Run `thumbgate import thumbgate-rules.md`.
- Ensure your `clients.json` (for conflict checks) is mapped to the `active_clients` namespace.

## 3. Disclaimers (2 Mins)
- Edit the `UPL Disclaimer` in `SKILL.md` to match your state bar requirements.

## 4. Deploy (8 Mins)
- Say: "Load skill: Legal Intake Pilot."
- Test with a mock lead: "I got hit by a truck in Chicago yesterday, can I sue?"
