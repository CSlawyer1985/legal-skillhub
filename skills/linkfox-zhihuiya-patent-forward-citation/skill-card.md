## Description: <br>
从智慧芽专利数据库查询指定专利在申请过程中引用的专利和非专利文献，并帮助代理按结果生成引用详情摘要。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[linkfox-ai](https://clawhub.ai/user/linkfox-ai) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers, patent analysts, and external agents use this skill to look up cited patent documents and non-patent literature for one or more patent IDs or publication numbers. It is suited for citation review and prior-art reference gathering, not legal-status, family, landscape, or reverse-citation analysis. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Patent identifiers, API credentials, and session metadata are sent to the LinkFox/Zhihuiya gateway. <br>
Mitigation: Use only in environments where sharing those values with the gateway is approved, and avoid confidential patent strategy unless that data flow is acceptable. <br>
Risk: Full API responses are cached and written under local linkfox directories. <br>
Mitigation: Review local retention requirements before use, restrict access to saved result directories, and delete cached or saved outputs when they are no longer needed. <br>
Risk: The skill may report broad feedback to a separate LinkFox feedback service. <br>
Mitigation: Confirm feedback reporting is acceptable for the deployment context and avoid including sensitive patent strategy or private user details in feedback content. <br>
Risk: The evidence flags a potential terminology mismatch between references cited by a patent and true forward citations. <br>
Mitigation: Verify that the requested analysis needs cited references from the queried patent before presenting the result as forward-citation analysis. <br>


## Reference(s): <br>
- [智慧芽专利引用查询 API 参考](artifact/references/api.md) <br>
- [ClawHub skill page](https://clawhub.ai/linkfox-ai/skills/linkfox-zhihuiya-patent-forward-citation) <br>
- [ClawHub publisher profile](https://clawhub.ai/user/linkfox-ai) <br>
- [LinkFox API key guide](https://skill.linkfox.com/linkfoxskills/guide.htm) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, JSON, shell commands, files, guidance] <br>
**Output Format:** [Markdown guidance with optional shell commands, API response JSON, and locally saved JSON result files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Accepts patentId or patentNumber inputs, supports comma-separated batches up to 100 entries, uses a 24-hour cache, and may summarize large JSON responses while saving the full response locally.] <br>

## Skill Version(s): <br>
1.0.4 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
