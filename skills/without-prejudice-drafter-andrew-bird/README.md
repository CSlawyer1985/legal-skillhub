# without-prejudice-drafter

在*正确的基础上*撰写和解函——并在标记“without prejudice”（不影响权利）实际上无法将其排除在法庭之外时警告你。

真正的和解函通常受保护，因此法官看不到它——但该标签只在实质是真正的和解尝试时才有效，且即便如此也有例外。本技能选择正确的基础（without prejudice、without prejudice save as to costs / Calderbank，或 open），起草完成的函件，并揭示导致 WP 材料尽管带标签仍被采纳的 Unilever v Procter & Gamble 例外——普通模板不会警告你的陷阱。面向需要第一次就把基础做对的初级律师和内部法律顾问。

## 安装

[claude-for-uk-legal](https://github.com/b1rdmania/claude-for-uk-legal) 插件套件的一部分：

```bash
/plugin marketplace add https://github.com/b1rdmania/claude-for-uk-legal
/plugin install uk-litigation-legal@claude-for-uk-legal
```

或直接安装单一技能：

```bash
cp -r without-prejudice-drafter ~/.claude/skills/without-prejudice-drafter
```

## 用法

```
/without-prejudice-drafter
/without-prejudice-drafter --type=wp
/without-prejudice-drafter --type=wpsatc
/without-prejudice-drafter --type=open
```

对照包含争议、提议条款以及谁向谁提出什么的条件运行它。它返回所选基础上的完成函件。

```
/without-prejudice-drafter --type=wpsatc
Draft a Calderbank offer in the Khan unfair-dismissal claim: our client
will pay £18,000 inclusive, open for 21 days, ET so no Part 36.
```

`--type` 标志固定基础——`wp` 为普通和解函，`wpsatc` 为 Calderbank / 费用保护提议，`open` 为记录在案的函件。省略时技能从请求中推断基础，仅在模糊时询问。

## 它做什么

- 识别正确的基础——open、WP 或 WPSATC——并为该情境提出正确选择。
- 应用匹配的页眉惯例并起草完成的函件，而非模板。
- 在关键点上区分三种基础：庭审中什么可采纳，什么仅费用上可采纳。
- 揭示 Unilever v Procter & Gamble 例外——WP 材料尽管带标签仍被采纳的情形——已达成协议、虚假陈述/欺诈、禁止反言、明确不当、延误、费用和费率。
- 将 open 和 WP 内容保存在不同文件中，并标记任何可能触发例外的内容（承认、威胁、禁止反言信号）。

## 它不做什么

- 不敲定基础。它提出一个基础；它不保证基础成立。无论哪种方式，误贴标签都有真实的披露后果。
- 不提供法律意见。输出是供律师审阅的草稿，而非客户可依赖的意见。发函前必须由出庭律师或经办律师确认基础。
- 不让一份实质不是真正和解尝试的带标签函件享有特权。标签跟随实质。
- 不在民事法院提供 Part 36 费用保护——为此单独起草 Part 36 提议。
- 不覆盖苏格兰 tender 或北爱尔兰对应机制。

## 要求

- Claude Code 或 Claude Cowork。无需 MCP 连接器。
- 要运行的条件——争议、提议条款和当事方。

## 许可

Apache-2.0。
