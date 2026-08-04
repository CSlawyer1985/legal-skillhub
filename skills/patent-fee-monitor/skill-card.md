## Description: <br>
Patent Fee Monitor helps users track patent annual-fee deadlines, query public patent status sources, manage patent, trademark, and software copyright asset ledgers, import and export CSV records, and generate reminder outputs. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[golngod](https://clawhub.ai/user/golngod) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users such as small-business IP managers, individual inventors, and startup teams use this skill to monitor IP asset deadlines, estimate renewal-fee status, and maintain lightweight patent, trademark, and software copyright records. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: IP asset records may contain sensitive patent, owner, inventor, deadline, or diligence information stored in local files inside the skill directory. <br>
Mitigation: Use controlled workspaces for confidential assets, restrict file access, and avoid entering highly confidential pre-publication strategy unless storage protections are acceptable. <br>
Risk: Patent identifiers may be sent to public patent lookup services during status queries. <br>
Mitigation: Disable or avoid network lookups for sensitive matters, rely on manually entered dates where needed, and review external lookup behavior before operational use. <br>
Risk: Fee and deadline calculations are lightweight estimates and may not reflect all jurisdiction-specific legal requirements or current fee schedules. <br>
Mitigation: Treat outputs as reminders and planning aids, and verify critical renewal decisions against official patent-office records or qualified counsel. <br>


## Reference(s): <br>
- [Patent Fee Monitor on ClawHub](https://clawhub.ai/golngod/skills/patent-fee-monitor) <br>
- [Publisher profile](https://clawhub.ai/user/golngod) <br>
- [Google Patents](https://patents.google.com) <br>
- [USPTO API](https://api.uspto.gov) <br>
- [EPO Open Patent Services](https://ops.epo.org) <br>
- [WIPO PATENTSCOPE](https://patentscope.wipo.int) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, files, configuration, guidance] <br>
**Output Format:** [Markdown-style reports, structured notification lists, CSV exports, and iCalendar reminder files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May read and write local IP asset JSON, CSV, and calendar files in the skill directory.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
