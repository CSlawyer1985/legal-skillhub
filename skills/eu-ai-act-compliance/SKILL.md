# EU AI Act Compliance Skill

## Purpose

Classify AI systems used in HR and recruitment contexts according to EU AI Act risk categories and generate compliance gap reports with remediation recommendations.

## When to Use

Use this skill when:
- A user asks about whether their AI system is "high-risk"
- They need to assess compliance with EU AI Act requirements
- They're implementing AI in recruitment, HR management, or workforce planning
- They need documentation for regulatory compliance

## How It Works

### Step 1: Gather Information

Ask the following clarifying questions to understand the AI system:

1. **Use Case**: What specific HR or recruitment function does the AI perform?
   - CV screening or parsing
   - Candidate ranking or shortlisting
   - Interview scheduling
   - Employee performance assessment
   - Workforce planning or forecasting
   - Other (specify)

2. **Data Processed**: What types of data does the AI process?
   - Personal data (name, contact details)
   - Professional qualifications
   - Employment history
   - Performance data
   - Biometric data
   - Inferences or predictions about individuals

3. **Decision Impact**: What decisions are influenced or made by the AI?
   - Automatic decisions (no human review)
   - Recommendations that inform human decisions
   - Filtering that affects candidate pools
   - Scoring or ranking of individuals
   - Other outcomes

4. **Human Oversight**: What human oversight mechanisms exist?
   - Human review before final decisions
   - Ability to override AI recommendations
   - Appeal or review process for affected individuals
   - Documentation of human involvement

5. **Deployment Context**: Where will the AI be deployed?
   - Public sector (subject to SI 284/2016 procurement rules)
   - Private sector
   - Cross-border processing
   - Irish-specific regulatory requirements

### Step 2: Determine Risk Classification

Based on the information gathered, classify according to EU AI Act risk categories:

#### High-Risk Systems (Annex III, Article 6(2))

AI systems in HR are **presumed high-risk** if they:

1. **Recruitment or selection systems** (Annex III, 4.(a)):
   - CV screening and parsing
   - Candidate ranking or scoring
   - Interview scheduling that affects opportunities
   - Assessment tools for selection

2. **Employment, worker management, access to self-employment** (Annex III, 4.(b)):
   - Task allocation
   - Performance evaluation
   - Promotion or termination decisions
   - Access to employment opportunities

#### Medium-Risk Systems

Systems that:
- Assist human decisions but don't make autonomous decisions
- Process data without significantly affecting rights
- Have robust human oversight mechanisms

#### Minimal-Risk Systems

Systems that:
- Are purely informational
- Don't process personal data for decisions
- Don't affect individual rights or opportunities

### Step 3: Generate Compliance Gap Report

For high-risk systems, assess against:

| Requirement | Article | Status | Gap | Priority |
|-------------|---------|--------|-----|----------|
| Risk management system | Art. 9 | | | |
| Data governance | Art. 10 | | | |
| Technical documentation | Art. 11 | | | |
| Record-keeping | Art. 12 | | | |
| Transparency | Art. 13 | | | |
| Human oversight | Art. 14 | | | |
| Accuracy & robustness | Art. 15 | | | |
| Conformity assessment | Art. 43-48 | | | |

### Step 4: Provide Remediation Steps

Recommend specific actions based on gaps identified:

1. **Immediate actions** (0-30 days): Critical compliance gaps
2. **Short-term actions** (30-90 days): Documentation and process gaps
3. **Long-term actions** (90+ days): System improvements and monitoring

### Step 5: Reference Relevant Guidance

Always cite:
- EU AI Act articles (with specific sections)
- Annex III categorisation
- Irish DPC guidance where relevant
- GDPR Article 22 for automated decision-making
- SI 284/2016 for public sector procurement

## Reference Files

This skill includes detailed references:

- `references/article-14-checklist.md` — Human oversight requirements
- `references/gdpr-ai-intersection.md` — GDPR and AI intersection
- `references/recruitment-risk-assessment.md` — Recruitment-specific risks
- `references/irish-employment-context.md` — Irish regulatory context

## Output Format

Provide structured output:

```markdown
## AI System Risk Classification

**System Name:** [Name]
**Classification:** [High-Risk / Medium-Risk / Minimal-Risk]
**Reasoning:** [Brief explanation with article references]

## Compliance Gap Report

[Gap analysis table]

## Recommended Actions

### Immediate (0-30 days)
- [Action 1]
- [Action 2]

### Short-term (30-90 days)
- [Action 1]
- [Action 2]

### Long-term (90+ days)
- [Action 1]
- [Action 2]

## Relevant References

- [EU AI Act Article X]
- [Irish DPC Guidance Y]
- [GDPR Article 22]
```

## Important Notes

- **Presumption of high-risk**: HR AI systems listed in Annex III are presumed high-risk regardless of the specific risk they pose. This is a legal presumption, not a risk assessment.
- **Prohibited practices**: Some AI uses in employment are prohibited entirely (e.g., emotional recognition in workplace). Always check Article 5 prohibitions first.
- **Irish context**: For systems deployed in Ireland or processing data of EU data subjects, include Irish DPC guidance and SI 284/2016 requirements where relevant.

---

*This skill is for informational purposes only. It does not constitute legal advice. Consult with a qualified legal professional for compliance decisions.*