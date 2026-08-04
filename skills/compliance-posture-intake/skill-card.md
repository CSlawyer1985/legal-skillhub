## Description: <br>
Comprehensive HIPAA compliance posture assessment for agent and API contexts that guides intake, analyzes provided compliance documents, and produces a posture snapshot with maturity stage, blocker flags, gap priorities, and a 30/60/90 day roadmap. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[dangsllc](https://clawhub.ai/user/dangsllc) <br>

### License/Terms of Use: <br>
Apache-2.0 <br>


## Use Case: <br>
External users, compliance teams, and advisors use this skill to run a structured HIPAA posture intake, review supplied compliance documents, prioritize gaps, and prepare a shareable compliance roadmap. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Users may provide sensitive compliance materials or patient identifiers during intake or document analysis. <br>
Mitigation: Use redacted or summarized documents where possible, avoid patient identifiers unless necessary, and decide where generated reports will be stored and deleted before use. <br>
Risk: State-law and HIPAA interpretations may be incomplete or unsuitable for final legal reliance. <br>
Mitigation: Verify state-law output and compliance recommendations with qualified counsel before making operational or legal decisions. <br>
Risk: Report generation may depend on docx tooling that is not clearly declared in the skill metadata. <br>
Mitigation: Confirm docx generation support in the agent context, or produce a markdown report and convert it through an approved document workflow. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/dangsllc/skills/compliance-posture-intake) <br>
- [Rote Compliance](https://rotecompliance.com) <br>
- [Publisher profile](https://clawhub.ai/user/dangsllc) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, guidance, files] <br>
**Output Format:** [Conversational intake followed by a structured compliance posture report, with Word document output when docx tooling is available.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May analyze user-provided compliance documents and summarize sensitive findings; report storage and deletion should be decided before use.] <br>

## Skill Version(s): <br>
0.1.2 (source: ClawHub release metadata; SKILL.md frontmatter reports 1.1) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
