## Description: <br>
调取全球企业资料库查询股东信息以及实际受益所有人（Beneficial Owner），梳理企业股权架构、投资关联关系，协助销售、风控人员摸清企业真实管控背景。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[upkuajing](https://clawhub.ai/user/upkuajing) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External business users, investors, analysts, sales teams, and risk researchers use this skill to query a known company ID for shareholder records and beneficial ownership signals. It supports due diligence, investment research, competitor and group-relationship analysis, related-party checks, and control-structure review. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill calls a paid Upkuajing API and queries may incur charges. <br>
Mitigation: Tell the user that the action is charged, fetch current pricing when needed, and wait for explicit confirmation in a separate message before running charged queries or recharge steps. <br>
Risk: The API key may be stored locally in a plaintext ~/.upkuajing/.env file. <br>
Mitigation: Keep the key private, prefer environment-variable injection when possible, and tighten local file permissions when storing the key on disk. <br>
Risk: A shareholder lookup requires a valid company ID; using the wrong identifier can return irrelevant or failed results. <br>
Mitigation: Confirm the company ID before lookup and use a company-search skill first when the user provides only a company name. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/upkuajing/skills/global-company-shareholder-zh) <br>
- [Company shareholder list API reference](references/company-shareholder-list-api.md) <br>
- [Upkuajing homepage](https://www.upkuajing.com) <br>
- [Upkuajing developer platform](https://developer.upkuajing.com/) <br>
- [Upkuajing OpenAPI pricing](https://www.upkuajing.com/web/openapi/price.html) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with shell commands and JSON API results] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires a company ID and an UPKUAJING_API_KEY; successful shareholder lookups return shareholder data and fee information.] <br>

## Skill Version(s): <br>
1.0.2 (source: release evidence and SKILL.md metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
