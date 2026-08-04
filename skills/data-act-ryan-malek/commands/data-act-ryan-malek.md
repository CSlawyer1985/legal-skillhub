---
description: EU 数据法案技能——根据 (EU) 2023/2854 号条例进行分类、起草、查询、分析或审计。生成律师风格 Word 输出。
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# /data-act-ryan-malek — EU 数据法案律师技能

调用安装在 `~/.claude/skills/data-act-ryan-malek/` 的 EU 数据法案技能。

用户输入：$ARGUMENTS

## 要做什么

1. 阅读 `~/.claude/skills/data-act-ryan-malek/SKILL.md` 并严格遵循其工作流。编排器处理逐字引用、陷阱、行文风格、模板填写和 Word 渲染。

2. 如果 `$ARGUMENTS` 非空，将其视为律师的请求。常见模式：
   - `/data-act-ryan-malek classify [描述]` → 分类模式
   - `/data-act-ryan-malek draft [要起草的内容]` → 起草模式
   - `/data-act-ryan-malek lookup [条款]` → 查询模式
   - `/data-act-ryan-malek analyze [情景]` → 分析模式
   - `/data-act-ryan-malek audit [产品]` → 审计模式
   - `/data-act-ryan-malek save-here` → 设置 `config.output_dir = cwd`（始终将 Word 保存到当前文件夹，不询问）
   - `/data-act-ryan-malek save-to-desktop` → 设置 `config.output_dir = desktop`
   - `/data-act-ryan-malek ask-where-to-save` → 重置 `config.output_dir = ""`（下次导出时提示）

3. 如果 `$ARGUMENTS` 为空，询问律师想要哪个数据法案任务：

   ```
   **哪种模式？**

     A) **classify（分类）** — 该产品是互联产品 / 相关服务 / DPS / 重叠吗？*（开始新事项时推荐）*
     B) draft（起草）— 合同前通知 / 第 25 条条款 / 拒绝函
     C) lookup（查询）— 按引用逐字查询条例 / FAQ 文本
     D) analyze（分析）— 将条例应用于具体事实

   （audit（审计）模式也可用——说 "audit" 或描述。）

   回复 A / B / C / D，或描述。
   ```

4. 绝不从训练数据复现条例、序言或 FAQ 文本。始终从 `~/.claude/skills/data-act-ryan-malek/assets/source/` 逐字阅读。

5. 默认输出是聊天本身。聊天回答后，询问律师是否导出到 Word。如果是，通过 `python3 ~/.claude/skills/data-act-ryan-malek/scripts/render_docx.py --template <md> --deliverable-type <type>` 渲染。渲染器：
   - 默认写入律师当前工作目录下的 `Data Act outputs/{date}_{type}.docx`。
   - 如果 cwd 不可写或解析到技能文件夹内，回退到 `~/Desktop/Data Act outputs/`。
   - 如果设置了 `config.output_dir`（`cwd`、`desktop` 或绝对路径），则遵循它。
   - 使用 pandoc + `assets/styles/lawyer-reference.docx` 实现正确的 Calibri / 藏青色标题 / 页码 / 表格网格 / 引用块样式。
   - 附加带 FAQ 版本 + 核验日期的简短免责声明。
   - 打印绝对路径和 `file://` URI，使律师可以点击打开。
   - 绝不在技能文件夹内写入交付物。

## 快速参考路径（技能内部）

- 知识层：`~/.claude/skills/data-act-ryan-malek/references/`
- 逐字来源：`~/.claude/skills/data-act-ryan-malek/assets/source/`
- 起草模板：`~/.claude/skills/data-act-ryan-malek/assets/templates/`
- 脚本：`~/.claude/skills/data-act-ryan-malek/scripts/`

## 免责声明

本命令调用一个仅生成起点草稿的技能。它不是法律意见。完整免责声明见 `~/.claude/skills/data-act-ryan-malek/LICENSE`。
