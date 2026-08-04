# ISO 42001 ↔ ISO 27001 Alignment Map

## Purpose
For organizations already certified to ISO 27001, this map shows which ISO 42001 controls extend existing 27001 controls vs. which are net new. Avoid duplication; maximize shared evidence.

## Shared Controls (Leverage Existing 27001 Evidence)

| ISO 42001 Control | ISO 27001 Equivalent | Notes |
|---|---|---|
| Clause 4.1 Context of organization | Clause 4.1 | Same intent — extend to cover AI context |
| Clause 5.2 AI Policy | A.5.1 Policies for information security | Extend existing IS policy to cover AI, or create separate AI policy |
| Clause 5.3 Roles & responsibilities | A.5.2 IS roles and responsibilities | Add AI-specific roles (AI system owner, AI risk officer) |
| Clause 6.1 Risk assessment | Clause 6.1 / A.8.2 | Extend risk assessment to include AI-specific risks |
| Clause 7.1 Resources | A.6.3 Information security awareness | Extend to include AI competency |
| Clause 7.2 Competence | A.6.3 | Add AI training requirements |
| Clause 7.5 Documented information | A.5.33 Protection of records | Same controls apply |
| Clause 8.1 Operational planning | A.5.37 Documented operating procedures | Extend to AI operations |
| Clause 9.1 Monitoring | A.8.16 Monitoring activities | Extend monitoring to AI systems |
| Clause 9.2 Internal audit | Clause 9.2 | Same audit process — add AI scope |
| Clause 9.3 Management review | Clause 9.3 | Add AI performance to management review agenda |
| Clause 10.2 Nonconformity | Clause 10.2 | Same corrective action process |
| A.4.2 Acquiring AI systems | A.5.21 ICT supply chain security | Extend vendor assessment to AI-specific questions |
| A.7.6 AI system documentation | A.8.8 Management of technical vulnerabilities | Extend to AI system technical docs |
| A.8.1 Data collection and preparation | A.8.10 Information deletion | Add AI training data controls |
| A.8.2 Data acquisition controls | A.5.19 IS in supplier relationships | Extend to AI data suppliers |
| A.10.2 Monitoring AI systems | A.8.16 Monitoring activities | Same monitoring infrastructure |

## Net New ISO 42001 Requirements (No 27001 Equivalent)

| ISO 42001 Control | Description | What to Build |
|---|---|---|
| Clause 4.6 AI roles in org | Defining whether org is AI provider, deployer, or both | New: document role classification |
| Clause 6.1.4 AI impact assessment | Assessing impact of AI on individuals and society | New: impact assessment process |
| A.2.2 Human oversight of AI | Ensuring humans can oversee/override AI systems | New: oversight controls per AI system |
| A.2.3 Responsible AI policy | Ethics and responsible use policy | New: AI ethics/responsible use policy |
| A.5.1 AI system risk classification | Classifying AI systems by risk level | New: risk classification scheme |
| A.5.2 Impact on individuals | Assessing societal/individual impact | New: impact assessment template |
| A.6.1 Conducting AI impact assessments | Formal AIIA process | New: AIIA procedure |
| A.7.1 Intended purpose documentation | Documenting AI system intended use | New: intended purpose register |
| A.7.3 Data for AI (quality/provenance) | Documenting training data quality | New: data provenance documentation |
| A.9.1 Transparency and explainability | Informing users about AI systems | New: transparency disclosures |

## Certification Strategy

**For ISO 27001 certified organizations pursuing ISO 42001:**

1. **Scope alignment:** Determine if AI systems fall within existing 27001 ISMS scope or require expanded scope
2. **Gap assessment:** Use the net-new controls above as your gap list
3. **Evidence reuse:** For shared controls, update existing procedures to reference AI — don't create duplicate documents
4. **Integrated audits:** Schedule combined 27001/42001 audits to reduce burden
5. **Timeline:** Expect 6–12 months to close net-new gaps; 3–6 months for organizations with mature 27001 programs

## Quick Win Checklist (For 27001 orgs adding 42001)
- [ ] Extend IS policy to cover AI (or add standalone AI policy)
- [ ] Add AI roles to existing RACI/responsibility matrix
- [ ] Extend risk assessment methodology to include AI risk taxonomy
- [ ] Create AI impact assessment template and process
- [ ] Add AI systems to asset inventory
- [ ] Build training data provenance documentation
- [ ] Define human oversight controls per AI system
- [ ] Add AI transparency disclosures to user-facing systems
- [ ] Extend internal audit scope to include AI systems
- [ ] Add AI performance metrics to management review
