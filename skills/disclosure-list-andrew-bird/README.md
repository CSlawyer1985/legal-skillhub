# disclosure-list（披露清单）

确定在英格兰与威尔士的民事案件中必须向对方移交哪些文件，并构建正式清单——正确处理最容易让人出错的部分：适用哪种披露制度。

在商事与财产法院（Business and Property Courts），适用实践指引 57AD 下的披露试点方案（现为常设制度，含其 A–E 模式）；其他所有法院适用 CPR 第 31 部分下的标准披露。向通用工具索要“披露清单”，它通常会默认采用旧的 CPR 31，完全遗漏 PD 57AD。对诉讼初级律师、公司法律顾问以及没有先例库的小团队：本技能选择制度、按争点选择模式、构建披露审查文件（Disclosure Review Document），并起草由当事方亲自签署的证书草稿。

## 安装

属于 [claude-for-uk-legal](https://github.com/b1rdmania/claude-for-uk-legal) 插件套件的一部分：

```bash
/plugin marketplace add https://github.com/b1rdmania/claude-for-uk-legal
/plugin install uk-litigation-legal@claude-for-uk-legal
```

或直接安装单个技能：

```bash
cp -r disclosure-list ~/.claude/skills/disclosure-list
```

## 使用

```
/disclosure-list
/disclosure-list --regime=pd57ad --model=C
/disclosure-list --regime=cpr31
```

针对一个事务运行它，提供法院/审判庭、披露争点、保管人、数据来源、日期范围和特权范围。它识别制度、按争点选择扩展披露模式，并返回起草完成的清单。

示例：一个商事法院索赔案件，你提供披露争点、四名保管人、数据来源（Outlook、Teams、共享驱动器、WhatsApp）和日期范围。它返回一份逐争点选择模式的披露审查文件、一张保管人/来源/关键词表和一份标记为草稿的披露证书草稿。

## 它做什么

- 识别制度——商事与财产法院（商事、大法官、技术与建筑法院 TCC、巡回商事、知识产权、金融清单）适用 PD 57AD，其他所有法院适用 CPR 第 31 部分。
- 按争点选择 PD 57AD 扩展披露模式 A–E，以模式 C 为默认，模式 E 保留给例外案件。
- 将保管人、数据来源、日期范围和关键词映射为检索方法论，包括 TAR/预测性编码披露。
- 按类别标记特权候选——法律意见、诉讼、无偏见、共同利益。
- 构建输出：CPR 31 下的 N265 结构文件清单（三部分），或 PD 57AD 下的简化披露审查文件。
- 在行内标记每个不确定点——`[REGIME]`、`[PRIVILEGE]`、`[GDPR]`、`[SME VERIFY]`——使任何内容都不显得已定论。

## 它不做什么

- 运行检索。它界定范围和列清单；检索在模型之外进行，且在任何清单或声明被认证之前必须实际执行。
- 决定特权。它按描述标记候选；由律师审查每个被标记文件并作出判断。
- 产出已签署的证书。披露声明（CPR 31.10）和 PD 57AD 披露证书由当事方亲自签署——模型在 DRAFT（草稿）横幅后起草框架，不作认证。
- 虚构文件。每条记录都可追溯到你提供的真实输入。
- 覆盖苏格兰或北爱尔兰程序（Commission and Diligence；RCS 附表 1），或家事程序。
- 提供法律意见。它是起草辅助工具；在送达任何输出前，与律师核验范围、检索和特权判断。

## 要求

- Claude Code 或 Claude Cowork。无需 MCP 连接器。
- 一个可运行的事务——法院/审判庭、争点、保管人、来源、日期范围和特权范围。

## 许可

Apache-2.0。
