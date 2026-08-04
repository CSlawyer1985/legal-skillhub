# 变更日志

对本技能的所有重要变更都将记录在本文件中。格式大致基于 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)；版本按 Agent Skills 编写惯例遵循 semver。

## [1.0.2] — 2026-05-12

### 变更

- **扁平布局与市场安装（现在两者同时实现）。** SKILL.md 直接位于仓库根目录。市场条目使用 `source: "./"`、`skills: ["./"]` 和 `strict: false`，三者共同告诉 Claude Code 将仓库根目录视为技能文件夹（依据 plugins-reference 文档："当技能路径指向一个直接包含 `SKILL.md` 的目录时，例如 `\"skills\": [\"./\"]` 指向插件根目录，`SKILL.md` 中 frontmatter 的 `name` 字段决定技能的调用名称"）。不再有 `skills/customs-trade-law/` 嵌套。

### 说明

1.0.1 的打包假设市场机制需要 `source: "./skills/<name>"`。这是错误的——通过上述模式字段支持扁平布局。安装命令不变：`/plugin marketplace add onurkafk/customs-trade-law` + `/plugin install customs-trade-law@onurkafk`。

## [1.0.1] — 2026-05-12

### 变更

- **安装路径。** 在仓库根目录添加了 `.claude-plugin/marketplace.json`，启用 Claude Code 的一级市场安装：`/plugin marketplace add onurkafk/customs-trade-law` 后接 `/plugin install customs-trade-law@onurkafk`。之前的 `git clone` 安装仍然可作为替代方案。
- **布局。** 将技能重新嵌套到 `skills/customs-trade-law/` 下，因为市场机制需要 `source: "./skills/<name>"`（依据 Claude Code 插件文档，扁平仓库根目录不是受支持的来源）。技能内容本身不变——只有其所在目录变化。

### 说明

这是打包变更。技能的行为、方法论、参考资料、模板和脚本与 1.0.0 完全相同。

## [1.0.0] — 2026-05-12 *（布局扁平化后重新打标签）*

作为 Agent Skill 的首次稳定发布。

### 仓库布局说明

初始发布（提交 `442e6a9`）将技能嵌套在 `skills/customs-trade-law/` 下。由于这是单技能仓库，嵌套是多余的。布局已扁平化：`SKILL.md` 及其支持目录现在位于仓库根目录，GitHub 仓库从 `onurkafk/trade-law` 更名为 `onurkafk/customs-trade-law`。GitHub 会自动重定向旧 URL。`v1.0.0` 标签已移至扁平化提交。

### 新增

- Agentic 研究协议：证据台账、来源标注纪律（Retrieved / Verified / Identified / Unverified）、权威层级执行。
- HTS 数据协议，含 Data.gov 批量 JSON 发现、现行修订版本选择和记录的事实来源块。
- 辅助脚本：
  - `scripts/resolve-latest-hts-json.py` — 通过 Data.gov 目录元数据解析最新 HTS JSON。
  - `scripts/cit-opinion-fetcher.py` — 按案卷编号获取并读取 CIT 简易判决意见书 PDF。
  - `scripts/hts-hierarchy-builder.py` — 将扁平的 HTS JSON 数组转换为用于 GRI 6 分析的缩进层级结构。
- 八工作流路由器：归类、CROSS 研究、CIT/CAFC 简报、关税汇编、第 99 章附加关税筛查、原产地分析、全面合规审查、来源/证据控制。
- 参考库：`references/` 中的 23 个法理和来源映射文件（GRI 分析、本质特征法理、美国附加规则、第 99 章附加关税、CROSS 研究方法论、CIT 判决分析、原产地分析、关税税率汇编、特殊项目解码器、归类置信度、解释框架、现行来源映射、HTS 数据来源、人工审查触发点、格式标准、免责声明、概念词汇表、范围路线图、检索策略、CIT 法院信息、FTA 项目代码、章节/目录映射、agentic 研究协议）。
- 五个输出模板：归类备忘录、CIT 判决简报、合规审查、关税税率摘要、裁决摘要。
- `examples/output.md` 中的完整端到端示例。

### 变更

- **打包。** 从 Claude Code *插件*（含 `plugins/trade-law/` + `.claude-plugin/marketplace.json` + `/trade-law` 斜杠命令）重构为 `skills/customs-trade-law/` 下的 *Agent Skill*，遵循 lq_ai frontmatter 约定。
- **权威性。** Frontmatter 重写为完整的 `lq_ai:` 模式（title、version、author、tags、jurisdiction、trigger_examples、inputs、output_format 等）。
- **触发。** 移除了 `/trade-law` 斜杠命令。技能现在在用户提及 HTS / customs / tariff / CROSS / CIT / CAFC / Section 301 / duty / origin / UFLPA / PGA 主题时从其描述自动触发。
- **许可证。** AGPL-3.0 在仓库级别和技能级别均适用。
- **文件夹语义。** `methodology/` 合并到 `references/`（lq_ai 约定是单一 `references/` 文件夹）。

### 移除

- `.claude-plugin/marketplace.json` 和 `plugins/trade-law/.claude-plugin/plugin.json`（技能格式下不再需要）。
- `plugins/trade-law/commands/trade-law.md`（`/trade-law` 斜杠命令）。
- `plugins/` 目录树（内容迁移到 `skills/customs-trade-law/`）。
