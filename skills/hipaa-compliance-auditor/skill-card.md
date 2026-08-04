## Description: <br>
Automatically detect and de-identify PII (Personal Identifiable Information) and PHI (Protected Health Information) from clinical/medical text to ensure HIPAA compliance. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[AIPOCH-AI](https://clawhub.ai/user/AIPOCH-AI) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Healthcare developers, compliance teams, and data reviewers use this skill to identify and replace potential PII or PHI in clinical text before sharing or downstream processing. Outputs require manual review before they are used for HIPAA-related release decisions. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patient data may be exposed through console output, generated files, or audit logs. <br>
Mitigation: Use only in a controlled local environment, avoid shared terminals and CI logs, and protect any audit logs as PHI. <br>
Risk: The skill's compliance claims are stronger than the implementation can guarantee. <br>
Mitigation: Require manual review and documented QA before relying on outputs for HIPAA-related release decisions. <br>
Risk: Unpinned or optional NLP dependencies can change detection behavior across environments. <br>
Mitigation: Pin and review dependencies, including spaCy models and optional Presidio packages, before operational use. <br>


## Reference(s): <br>
- [ClawHub release page](https://clawhub.ai/AIPOCH-AI/hipaa-compliance-auditor) <br>
- [HIPAA Safe Harbor Guide](references/hipaa_safe_harbor_guide.md) <br>
- [PII Pattern Reference](references/pii_patterns.json) <br>
- [Python Dependencies](references/requirements.txt) <br>
- [HHS De-identification Guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html) <br>


## Skill Output: <br>
**Output Type(s):** [text, json, guidance] <br>
**Output Format:** [De-identified text, JSON audit logs, console statistics, and validation recommendations] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May write output files and audit logs when paths are provided; manual review is recommended before relying on results.] <br>

## Skill Version(s): <br>
0.1.0 (source: server release metadata; artifact frontmatter reports 1.0.0) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
