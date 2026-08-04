## Description: <br>
从智慧芽（PatSnap）数据库查询专利法律状态信息，包括专利有效性、当前法律状态和转让、许可、质押、异议、诉讼、复审等法律事件。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Patent analysts, IP teams, and agents use this skill to look up current legal status and legal event history for one or more patents by publication number or patent ID. It is suited for validity checks, batch status review, and quick event history summaries. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Full patent lookup responses are saved locally by default and may include sensitive patent or task context. <br>
Mitigation: Run the skill only in an approved workspace, review the saved linkfox data directory after use, and clean cached or response files after sensitive lookups. <br>
Risk: Automatic feedback reporting can send user or task context to LinkFox. <br>
Mitigation: Ask for user consent before sending feedback and avoid including confidential patent details or client context in feedback content. <br>
Risk: Queries consume LinkFox credits based on returned data volume. <br>
Mitigation: Confirm scope before batch requests, reuse cached results for repeated queries, and avoid automatic retries or exploratory re-querying without user approval. <br>


## Reference(s): <br>
- [API Reference](references/api.md) <br>
- [ClawHub Skill Page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-legal-status) <br>
- [LinkFox API Key Guide](https://skill.linkfox.com/linkfoxskills/guide.htm) <br>
- [LinkFox Skills](https://skill.linkfox.com/) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with JSON API responses, saved JSON files, and shell command examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Queries require LINKFOX_AGENT_API_KEY or LINKFOXAGENT_API_KEY. Full responses are saved locally; small responses are also printed to stdout, while large responses are summarized unless --inline is used.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
