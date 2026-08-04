# cpr-letter-drafter

起草您在英格兰与威尔士民事诉讼中起诉某人之前发出的正式信函——启动诉前时钟的《索赔前函》（Letter Before Claim）——并依据索赔适用*正确*的诉前协议。

适用哪个协议（债务、职业过失、房屋失修、人身伤害，或默认的《诉前行为实务指引》）会改变规则，通用信函会漏掉它们。面向诉讼初级律师、公司法务和没有先例库可复制的小型律所：它能抓住通用草稿遗漏的内容——30 天债务索赔答复窗口、职业过失的"先初步通知后索赔函"流程——并将时效日期标记为需律师确认，而非作为既成事实陈述。

## 安装

属于 [claude-for-uk-legal](https://github.com/b1rdmania/claude-for-uk-legal) 插件套件的一部分：

```bash
/plugin marketplace add https://github.com/b1rdmania/claude-for-uk-legal
/plugin install uk-litigation-legal@claude-for-uk-legal
```

或直接安装单个技能：

```bash
cp -r cpr-letter-drafter ~/.claude/skills/cpr-letter-drafter
```

## 用法

```
/cpr-letter-drafter
/cpr-letter-drafter --protocol=debt
/cpr-letter-drafter --protocol=prof-neg
```

对包含当事人、诉因、时间线、损失明细和待披露文件的事项运行它。它识别适用的协议（或默认为 PACC），核验时效门禁，并返回按该协议期望的结构起草的 LBC。

示例：

```
/cpr-letter-drafter --protocol=debt

原告：Acme Supplies Ltd。被告：J. Khan（个体工商户）。
未付发票总计 18,400 英镑加合同利息。
合同于 2025 年 1 月 12 日订立；最后一笔付款于 2025 年 3 月 3 日收到。
```

它返回一份《债务索赔协议》信函，含 30 天答复窗口、所要求的信息表和答复表引用、账户对账单，以及供律师确认的时效标记。

## 它做什么

- 识别是否有特定诉前协议适用，还是默认的《诉前行为与协议实务指引》（PACC）管辖。
- 应用该框架的时限、内容和披露要求——例如 30 天债务窗口，或职业过失的"先初步通知后索赔函"流程。
- 起草信函，含当事人、事实、按要件适用的索赔项、带利息的明细损失、文件、ADR 信号、答复要求和费用。
- 将表面时效日期作为 `[SOLICITOR: confirm limitation date]`（律师：确认时效日期）标记呈现，绝不作为既成事实，并标记起算假定和例外。
- 如案件继续推进，提示 CPR 第 36 部分和第 44 部分的费用后果。
- 行内标记不确定点——`[SOLICITOR: confirm X]`、`[PROTOCOL]`、`[SME VERIFY]`、`[CITE NEEDED]`——使任何内容都不显得已成定论。

## 它不做什么

- 不提起诉讼。LBC 属于诉前阶段。
- 不适用苏格兰或北爱尔兰程序。
- 不替代律师在时效紧迫时是否进行保护性起诉的判断。
- 不保证或认证合规。输出按遵循相关协议的样式制作；发送前核验其当前内容、时限和附件要求。
- 不解决时效问题。它使用的期限是一般默认值；起算日期和例外必须由律师核验。

这是供律师复核的草稿，而非法律意见。对事项负管理责任的律师对合规性以及以律所名义发出的内容负责。

## 要求

- Claude Code 或 Claude Cowork。无需 MCP 连接器。
- 一个可运行的事项——当事人、诉因、时间线、损失明细和待披露文件。

## 许可证

Apache-2.0。
