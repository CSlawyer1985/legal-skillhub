# EU 数据法案技能

一个面向就欧盟数据法案（(EU) 2023/2854 号条例）提供咨询的律师的工作流导向技能。

该技能在五个工作流——分类、起草、查询、分析、审计——中生成律师风格 Word 输出，逐字引用捆绑的源文本（2023/2854 号条例和欧委会常见问题解答 v1.4），并指向欧委会的示范合同条款（2025 年 11 月 19 日建议）供直接查阅。

**作者：**Ryan Malek
**反馈 / 问题：**[LinkedIn](https://www.linkedin.com/in/theryanmalek/)
**分发渠道：**Github、Counselcoder.com、Lawvable
**项目网站：**[counselcoder.com](https://counselcoder.com)
**许可证：**AGPL-3.0（见 `LICENSE`）
**这不是法律意见。**完整免责声明见 `LICENSE`。

---

## 适用对象

就欧盟数据法案合规提供咨询的内部法律顾问和外部执业律师——包括工业物联网、汽车、医疗器械、SaaS、金融服务和云客户。

该技能假设用户是合格律师。它不解释 GDPR 基础、SaaS 的含义或律师已经知道的其他概念。

## 它的作用

五个工作流，每个都有自己的参考文件：

| 模式      | 触发                                                                         | 输出（Word）                                              |
|-----------|---------------------------------------------------------------------------------|------------------------------------------------------------|
| classify（分类）  | "这个产品是互联产品 / 相关服务 / DPS / 重叠吗？"      | 带推理的分类备忘录                         |
| draft（起草）     | "给我起草 [合同前披露 / 第 25 条条款 / 拒绝函 / 等]" | 可编辑 Word 文档，标记为起点           |
| lookup（查询）    | "第 X 条说了什么？"或"Y 的截止日期是什么？"                    | 逐字引用 + FAQ 关联 + 交叉引用                  |
| analyze（分析）   | "我的客户可以在此以商业秘密为由拒绝吗？"                            | 应用该框架的结构化法律分析           |
| audit（审计）     | "将这个产品与法规进行比较"                                  | 带严重性标志的差距分析检查清单                 |

该技能始终：

- 在起草前询问事项特定事实（所代理的一方、行业、成员国），而非依赖全局配置。
- 当事实触发汽车 / 医疗 / DORA / NIS2 / AI 法案 / CRA / 其他行业法时，提示**行业覆盖警告**。
- 从 `assets/source/*` **逐字**引用（不凭记忆转述）。
- 在每一个依赖它的输出中将**欧委会 FAQ 框架为非权威**。
- 在每个 Word 输出末尾附加简短的**免责声明**。

## 它不做什么

- **不提供法律意见。**技能产生由律师审查的草稿。
- **不涵盖行业特别法。**相邻制度（2018/858 号条例、MDR、DORA、NIS2、AI 法案、CRA 等）被标记，而非涵盖。
- **不涵盖成员国实施法律。**技能指向第 37 条主管机构；国家层面的叠加必须独立核实。
- **不提供多语言输出。**仅英文。使用您自己的 LLM 进行翻译。
- **不自动更新来源。**技能是带版本的静态快照。时效性通过"verified-as-of"（核验日期）印章和新的 Lawvable 版本检查。

## 安装

### Claude Code（一条命令）

```bash
git clone https://github.com/counselos/eu-data-act ~/data-act-skill
cd ~/data-act-skill
bash install.sh
```

该脚本将文件夹符号链接到 `~/.claude/skills/data-act-ryan-malek/`（按描述自动触发）并添加 `~/.claude/commands/data-act-ryan-malek.md`（显式 `/data-act-ryan-malek` 斜杠命令）。设置 `COPY=1` 以安装固定副本而非符号链接。

用 `bash install.sh --check` 验证。用 `bash install.sh --uninstall` 卸载。

### 其他平台

- **Claude Agent SDK**——相同的文件夹布局；通过 SDK 的技能目录注册。
- **Codex CLI**——无原生技能发现；要么在运行 `codex` 时 `cd` 进入文件夹，要么用 `Use the skill at /path/to/data-act-ryan-malek/SKILL.md ...` 打开提示。
- **完全不用代理**——直接打开模板和参考文件。Python 脚本独立运行。

### 依赖

**Pandoc**（用于 Word 导出）：

```bash
# macOS
brew install pandoc

# Linux
sudo apt-get install pandoc
```

Word 导出使用带参考模板（`assets/styles/lawyer-reference.docx`）的 pandoc，以实现正确的 Calibri / 藏青色标题 / 页码 / 表格网格样式。没有 pandoc，`/data-act-ryan-malek` 对聊天回答和查询仍可工作，但 Word 导出步骤会以清晰的安装消息失败。

**Python**（3.10+）和以下包（仅在脚本运行时）：

```bash
pip install python-docx pypdf
```

该技能可离线工作。任何最终用户功能都不需要网络访问。

## 如何使用

两种调用方式，均受支持：

### 斜杠命令（显式）

```
/data-act-ryan-malek                                      ← 显示模式菜单
/data-act-ryan-malek classify [产品描述]      ← 分类模式
/data-act-ryan-malek draft [要起草的内容]                ← 起草模式
/data-act-ryan-malek lookup [第 25(2)(a) 条]               ← 逐字查询
/data-act-ryan-malek analyze [情景]                   ← 将法律应用于事实
/data-act-ryan-malek audit [现有产品]            ← 差距分析
```

### 自动触发（隐式）

只需描述任务。技能的描述匹配类似短语：

> "我需要将客户的互联电表按数据法案分类。"
>
> "给我起草一套第 25 条合同条款。"
>
> "第 25(2)(g) 条说了什么？"
>
> "我的客户能以商业秘密为由拒绝这次访问请求吗？"

模型自动调用该技能。

无需设置。该技能开箱即零配置。

**交付物默认存在于聊天中。**聊天回答后，技能提供导出到 Word 的选项。Word 文件默认保存到律师当前工作目录下的 `./Data Act outputs/{date}_{type}.docx`——绝不保存在技能文件夹内。律师可以用以下命令持久化其他位置：

```
/data-act-ryan-malek save-here          # 始终保存到当前文件夹，不询问
/data-act-ryan-malek save-to-desktop    # 始终保存到 ~/Desktop/Data Act outputs/
/data-act-ryan-malek ask-where-to-save  # 每次都询问（默认）
```

## 更新模型

本技能是 (EU) 2023/2854 号条例、欧委会数据法案 FAQ 及相关来源的**带版本静态快照**。它不会在您的机器上自动更新。更新通过新的 Lawvable 版本流动。

**您如何保持最新：**

1. **发布新版本**发生在欧委会发布新 FAQ 版本、理事会通过修正案或行业指引变更影响捆绑材料时。每个版本都会更新 `CHANGELOG.md` 和 `_versions.json` 的核验日期。
2. **Lawvable 分发新版本。**更新通知会出现在您的 Lawvable 客户端中。要获取最新版本，请通过 Lawvable 重新下载。您的事项文件夹和 Word 输出不受影响。
3. **每个交付物都盖章"来源核验 [日期]"行。**这出现在每个聊天回答和 Word 备忘录的末尾，带实时 EUR-Lex 和欧委会 FAQ URL。如果您觉得盖章日期过旧（超过几个月），在依赖输出前重新下载技能。核验日期印章是您唯一需要的信号；您无需监控任何东西。

静态快照模型是深思熟虑的：它让安装保持简单，绝不让后台进程触碰您的工作，并将过时信号直接放入工作产物中，使您可以看到它。

## 每个下载者是其副本的维护者

原始创建者在分发后不维护、更新、监控或支持技能副本。每个下载者：

- 对其副本的时效性和准确性承担全部责任。
- 可以在 AGPL-3.0 许可证下自由修改、分叉和再分发。注意 AGPL-3.0 是强 Copyleft：衍生作品（包括作为网络服务运行的）必须在 AGPL-3.0 下发布并向用户提供源代码。
- 应在其为客户产生的输出中移除原始创建者的姓名（Word 页脚已经不含署名）。

这是有意为之——技能是您执业实践的起点，而非您订阅的服务。

## 文件夹布局

```
data-act/
├── SKILL.md                # 编排器（先读）
├── LICENSE                 # AGPL-3.0 + 法律意见免责声明
├── README.md               # 本文件
├── CHANGELOG.md            # 仅版本条目
├── install.sh              # Claude Code 一条命令安装
├── config.json             # output_dir 偏好（cwd / desktop / 自定义路径）
├── commands/
│   └── data-act-ryan-malek.md   # 斜杠命令定义 (/data-act-ryan-malek)
├── references/             # 知识层，按需读取
├── assets/
│   ├── source/             # 逐字条例、FAQ；SCC 指针
│   ├── templates/          # 起草起点（md → 通过 pandoc 生成 Word）
│   ├── styles/             # 用于 pandoc 样式的 lawyer-reference.docx
│   ├── decision-trees/     # 可走查的问答
│   └── examples/           # 工作示例
└── scripts/                # Python 辅助工具
```

## 捆绑的来源

- 2023 年 12 月 13 日的 (EU) 2023/2854 号条例（数据法案）——逐字文本
- 欧委会数据法案常见问题解答，v1.4，2026 年 1 月 22 日——逐字文本
- 欧委会"数据法案解读"页面——快照
- 欧委会关于标准合同条款 / 示范合同条款（附件）的建议，2025 年 11 月 19 日——**仅结构化指针**（`assets/source/model-contractual-terms.md`）；规范性 PDF 在欧委会网站上，条款文本应直接查阅

前三个在其各自的公共信息制度下再分发。建议被引用但不再分发。

## 版本控制

语义化版本控制。FAQ 实质性修订、法规修正案或范围变更时主版本号递增。新增模板、示例、参考时次版本号递增。错字和澄清时补丁版本号递增。

本版本：v1.0.0。见 `CHANGELOG.md`。
