# AI Recruitment Risk Assessment

## Overview

AI systems used in recruitment are classified as **high-risk** under Annex III of the EU AI Act. This document provides specific guidance for assessing and managing these risks.

---

## EU AI Act Classification

### High-Risk Presumption

Under Annex III, Section 4(a), AI systems intended to be used for recruitment are **presumed high-risk**:

> "AI systems intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates."

This includes:

| System Type | Classification | Legal Basis |
|-------------|----------------|-------------|
| CV screening and parsing | High-risk | Annex III, 4(a)(i) |
| Candidate ranking or scoring | High-risk | Annex III, 4(a)(ii) |
| Interview scheduling affecting opportunities | High-risk | Annex III, 4(a) |
| Assessment tools for selection | High-risk | Annex III, 4(a)(ii) |
| Targeted job advertising | High-risk | Annex III, 4(a) |

---

## Recruitment AI Use Cases

### 1. CV Screening and Parsing

**What it does**: Extracts information from CVs and filters candidates based on criteria.

**Risk Assessment**:

| Risk Category | Level | Description |
|---------------|-------|-------------|
| Discrimination | **High** | May replicate historical biases in training data |
| Transparency | **High** | Candidates unaware of filtering criteria |
| Accuracy | **Medium** | May incorrectly parse or interpret CVs |
| Human oversight | **High** | Risk of automatic rejection without review |

**Mitigation Requirements**:

- Document selection criteria clearly
- Test for bias against protected characteristics
- Ensure human review before rejection
- Provide feedback to rejected candidates
- Log all screening decisions

**Regulatory Requirements**:

- EU AI Act: Articles 9-15 (high-risk system requirements)
- GDPR: Article 22 (automated decision-making)
- Irish Employment Equality Acts: Prohibition on discrimination

---

### 2. Candidate Ranking and Scoring

**What it does**: Scores or ranks candidates based on various criteria.

**Risk Assessment**:

| Risk Category | Level | Description |
|---------------|-------|-------------|
| Discrimination | **High** | Scoring may disadvantage protected groups |
| Transparency | **High** | Candidates unaware of scoring methodology |
| Accuracy | **High** | Scoring may not correlate with job performance |
| Human oversight | **High** | Ranking may be accepted without question |

**Mitigation Requirements**:

- Validate scoring criteria against job performance
- Test for adverse impact on protected groups
- Document scoring methodology
- Allow human review and override
- Explain scores to candidates on request

**Regulatory Requirements**:

- EU AI Act: Articles 9-15, Article 13 (transparency)
- GDPR: Article 22, Articles 13-14 (information rights)
- Employment Equality Acts: Objective justification requirement

---

### 3. Interview Scheduling

**What it does**: Automatically schedules interviews based on availability.

**Risk Assessment**:

| Risk Category | Level | Description |
|---------------|-------|-------------|
| Discrimination | **Low** | Generally neutral scheduling process |
| Transparency | **Low** | Process is straightforward |
| Accuracy | **Low** | Scheduling errors are easily corrected |
| Human oversight | **Medium** | May affect candidate experience |

**Mitigation Requirements**:

- Allow candidates to request alternative times
- Ensure accessibility for candidates with disabilities
- Provide clear confirmation and reminders

**Regulatory Requirements**:

- GDPR: Processing personal data for scheduling
- Reasonable accommodation obligations

---

### 4. Video Interview Analysis

**What it does**: Analyses video interviews for facial expressions, voice tone, or content.

**Risk Assessment**:

| Risk Category | Level | Description |
|---------------|-------|-------------|
| Discrimination | **Very High** | Facial analysis may discriminate |
| Transparency | **Very High** | Candidates unaware of analysis criteria |
| Accuracy | **Very High** | Scientific validity questionable |
| Human oversight | **High** | Risk of algorithmic bias |
| Privacy | **Very High** | Biometric data processing |

**Critical Concerns**:

- **Prohibited in some jurisdictions**: Emotional recognition in employment may be prohibited under Article 5
- **Biometric data**: Special category data under GDPR Article 9
- **Scientific validity**: Many claims lack empirical support

**Mitigation Requirements**:

- Obtain explicit consent for biometric processing
- Conduct thorough bias testing
- Ensure scientific validity of claims
- Provide opt-out for candidates
- Strong human oversight required

**Regulatory Requirements**:

- EU AI Act: Article 5 (potential prohibition of emotional recognition)
- GDPR: Article 9 (special category data)
- Employment Equality Acts: Prohibition on discrimination

---

### 5. Assessment and Psychometric Testing

**What it does**: Administers and scores assessments, personality tests, or cognitive tests.

**Risk Assessment**:

| Risk Category | Level | Description |
|---------------|-------|-------------|
| Discrimination | **High** | Tests may disadvantage certain groups |
| Transparency | **High** | Candidates unaware of scoring criteria |
| Accuracy | **Medium** | Test validity varies |
| Human oversight | **Medium** | Scores may be accepted without review |

**Mitigation Requirements**:

- Validate tests for the specific job role
- Test for adverse impact on protected groups
- Provide practice tests and reasonable adjustments
- Document psychometric properties
- Allow human review of results

**Regulatory Requirements**:

- EU AI Act: Articles 9-15 (high-risk requirements)
- GDPR: Article 22 if automated decisions
- Employment Equality Acts: Objective justification

---

### 6. Reference Checking Automation

**What it does**: Automates collection and analysis of references.

**Risk Assessment**:

| Risk Category | Level | Description |
|---------------|-------|-------------|
| Discrimination | **Medium** | Analysis may introduce bias |
| Transparency | **Medium** | Candidates unaware of analysis |
| Accuracy | **Medium** | Automated analysis may misinterpret |
| Human oversight | **Medium** | Risk of accepting automated analysis |

**Mitigation Requirements**:

- Ensure references are reviewed by humans
- Document analysis criteria
- Allow candidates to provide context
- Verify automated analysis

**Regulatory Requirements**:

- GDPR: Processing of personal data in references
- Fair procedures requirements

---

## Risk Categories and Examples

### High-Risk Recruitment AI

| Example | Why High-Risk | Mitigation Priority |
|---------|---------------|-------------------|
| CV screening with auto-reject | Affects candidate rights without review | Critical |
| Candidate scoring algorithms | May discriminate against protected groups | Critical |
| Video interview analysis | Biometric data, questionable validity | Critical |
| Assessment scoring with automatic shortlisting | Affects candidate opportunities | High |

### Medium-Risk Recruitment AI

| Example | Why Medium-Risk | Mitigation Priority |
|---------|-----------------|-------------------|
| Interview scheduling with human review | Affects experience but not rights | Moderate |
| Reference collection automation | Human review of final decisions | Moderate |
| Job matching recommendations | Advisory, human final decision | Moderate |

### Lower-Risk Recruitment AI

| Example | Why Lower-Risk | Mitigation Priority |
|---------|----------------|-------------------|
| Job advertisement targeting | Targeting, but not decision-making | Low |
| Interview question generation | Advisory, human delivery | Low |
| Application tracking | Administrative, no decision impact | Low |

---

## Mitigation Requirements

### Technical Measures

1. **Bias testing and monitoring**
   - Test for adverse impact on protected groups
   - Monitor ongoing performance
   - Adjust for identified biases

2. **Explainability**
   - Document decision criteria
   - Provide explanations to candidates
   - Log all decisions

3. **Accuracy and robustness**
   - Validate AI predictions against outcomes
   - Test edge cases
   - Monitor for drift

### Organisational Measures

1. **Human oversight**
   - Human review before rejection
   - Ability to override AI recommendations
   - Appeal process for candidates

2. **Documentation**
   - Technical documentation (Article 11)
   - Use documentation (Article 13)
   - Training records for staff

3. **Governance**
   - Clear accountability
   - Regular audits
   - Incident response procedures

---

## Practical Checklist for HR Directors

### Before Deploying AI

- [ ] Conduct risk assessment for specific use case
- [ ] Identify if high-risk under Annex III
- [ ] Complete Data Protection Impact Assessment
- [ ] Review vendor documentation and claims
- [ ] Test for bias against protected characteristics
- [ ] Implement human oversight mechanisms
- [ ] Document decision criteria and methodology
- [ ] Update privacy notices
- [ ] Train staff on AI use and limitations
- [ ] Establish appeals process

### During AI Use

- [ ] Monitor for bias and accuracy
- [ ] Log all AI decisions
- [ ] Conduct regular human review
- [ ] Respond to candidate queries
- [ ] Update DPIA if processing changes

### After Deployment

- [ ] Review AI performance
- [ ] Address any incidents
- [ ] Update training for staff
- [ ] Document lessons learned

---

## Compliance Timeline

| Phase | Deadline | Actions |
|-------|----------|---------|
| **Assessment** | Now — August 2025 | Identify all AI systems, assess risks |
| **Preparation** | August 2025 — February 2026 | Implement requirements, train staff |
| **Compliance** | February 2026 onwards | Full compliance, ongoing monitoring |

---

## References

- **EU AI Act**: Regulation (EU) 2024/1689, Annex III, Section 4
- **GDPR**: Regulation (EU) 2016/679, Article 22
- **Employment Equality Acts**: 1998-2021 (Ireland)
- **Irish DPC**: Guidance on Automated Decision-Making
- **EDPB Guidelines**: WP251 on Automated Decision-Making

---

*Last updated: April 2026*  
*Author: Enda Rochford*  
*For informational purposes only — not legal advice*