---
name: legal-diagram
version: '1.2.0'
description: '当用户需要根据文档、粘贴文本、事项描述、流程、时间线、当事方关系图、义务关系图、公司结构、资金流向或合规工作流生成法律或涉法 Mermaid 图表时使用。触发词：“diagram this contract”（为这份合同绘制图表）、“visualise this deal/matter”（可视化这笔交易/这个事项）、“map the parties”（绘制当事方关系图）、“create a timeline of events”（创建事件时间线）、“make an org chart”（制作组织结构图）、“obligation checklist”（义务清单）、“export as HTML diagram”（导出为 HTML 图表）。不适用于通用非法律图表、纯平面设计、图像生成或法律咨询。'
argument-hint: '[文件路径 | "粘贴文本" | 事项描述] [图表类型] [--guided] [--direct] [--html] [--tutorial]'
---

# /legal-diagram

独立技能：将法律材料转化为适合上下文场景的 Mermaid 图表，并可选择导出可下载的 HTML 图形。保留结构的 Python 引擎提取带类型的真实信息；指令驱动的 LLM 丰富化填补缺口；选择器选择图表类型；图表以原生方式生成。

## 路由门控

每个真实的图表请求都按此固定顺序运行：首次运行检查、摄取、构建模式门控、生成、报告门控。非图表意图在第 0 步短路退出。

三个人工门控 = 强制硬停点：门控 0（教程提示）、门控 A（构建模式）、门控 B（HTML 报告）。门控纪律，无例外：

- 每项均以结构化选择呈现（使用问题工具）。无此类工具 → 带编号的纯文本列表。无论哪种方式，STOP，等待回复。
- 绝不跳过门控。绝不从措辞推断其答案。绝不在未回答的门控之后继续生成。详细、具体或点名图表类型的请求 = 仍然是请求，不是门控答案。
- 只有字面量标志可以预先作答：`--direct`/`--guided`（门控 A）、`--html`（门控 B）、`--tutorial`（教程）。其他任何内容都不算数。

### 第 0 步——意图与首次运行

首先检查显式短路信号：

1. **教程**信号：“tutorial”（教程）、“show me how”（演示给我看）、“first time”（第一次）、“demo”（演示）、“walk me through”（带我走一遍）、`--tutorial`。→ 加载 `workflows/tutorial.md`。在此停止。
2. **设置**信号：“check setup”（检查设置）、“install deps”（安装依赖）、“is setup ready”（设置是否就绪）。→ 加载 `shared/setup-check.md`，运行 `check_setup.py`，报告结果。在此停止。

否则，这是真实的图表请求（文件、粘贴文本或事项描述）。检测首次运行：

运行 `python scripts/first_run.py`。解析 `{state}`：`returning`（回访）、`first_run`（首次）或 `unknown`（未知）。脚本缺失、非零退出或没有 JSON → 视为 `unknown`。

- `returning`（已确认）→ 不提供教程；用户以前运行过该技能。继续到第 1 步。
- `first_run`、`unknown` 或任何非已确认 `returning` 的状态 → **门控 0**（硬停点）：“首次使用。想要快速教程，还是直接开始生成图表？”选项：**开始教程**（推荐，列在最前）/ **跳过，直接生成我的图表**。以结构化选择呈现，若宿主无选择工具则以带编号的纯文本列表呈现，然后 STOP，等待回复。回答后，运行 `python scripts/first_run.py --mark` 记录提示（尽力而为；在 `unknown` 状态且无可写磁盘时，标记可能无法持久化，没关系）。然后：教程 → 加载 `workflows/tutorial.md`，停止；跳过 → 继续到第 1 步。

`unknown` 默认为提供而非抑制：呈现选择，不替用户决定。仅在已确认的 `returning` 状态下抑制。教程可随时通过关键词触达。

### 第 1 步——在选择通道前先摄取

检测输入：文件路径、粘贴文本或对话/事项描述。加载 `shared/setup-check.md`（会话缓存）。

**多文件范围门控**（2 个及以上文件）⛔：除非用户已明确说明范围，否则强制硬停点。以结构化选择呈现，若宿主无选择工具则以带编号的纯文本列表呈现，然后 STOP，等待回复。选项：**一张合并图表** / **每份文档一张图**。绝不从措辞推断范围。存储 `diagram_scope`。单文件，或用户已明确说明范围 → 跳过。

仅运行第 1 遍（确定性清单，无 LLM）：`workflows/extract.md` 第 0-2 步。将结果存储为 `manifest_cache` 并传递给所选通道，确保第 1 遍绝不重复运行。仅事项描述输入（无文档）没有第 1 遍计数；没有计数也照常进行。

### 第 2 步——门控 A：构建模式（摄取之后）⛔ 阻塞

门控 A = 强制硬停点。除非用户输入了字面量 `--direct` 或 `--guided` 标志，否则始终触发。在门控 A 得到回答之前，不加载任何通道，不生成任何图表。

**只有字面量标志能预先作答。** 唯一的答案载体 = 用户消息中确切的 `--direct` 或 `--guided` 标记。存在 → 用一行说明已确定的模式（“构建模式：直接（标志）”）并加载相应通道。这是用户自己记录的选择，而非模型决策。

**其他所有情况 → 呈现门控并 STOP。** 详细、具体或点名图表类型的请求（“这个具体案件的全面图表”“制作组织结构图”）= 请求，不是门控答案。绝不从措辞推断构建模式。先以通俗语言说明第 1 遍的发现：“发现 [N 个当事方、M 个事件、……]。您希望如何构建？”（无文档输入省略计数）。以结构化选择呈现，若宿主无选择工具则以带编号的纯文本列表呈现，然后等待回复。选项，固定顺序：

- **引导式，逐步进行**
- **直接生成**

不重排选项，不按措辞暗示选择。顺序固定；选择权在用户。

选择后：加载 `workflows/direct.md` 或 `workflows/guided.md`，传入 `manifest_cache`、`input_source` 和 `diagram_scope`。两条通道共享 `workflows/generation.md` 进行构建；门控 B（HTML 报告）在那里触发。

**面向用户的语言（对普通用户友好）。** 绝不向用户显示 Mermaid 内部类型名称。使用 `shared/diagram-type-map.md` 中“通俗名称”一节的通俗名称——“timeline”（时间线）、“org chart”（组织结构图）、“flowchart”（流程图）、“obligation checklist”（义务清单）等。也接受通俗词语请求（“帮我做一张组织结构图”），并通过同一术语表映射。法律词汇没有问题；技术性图表词汇保持内部使用。

**输出语言（EN/FR）。** 门控、摘要、信息引导和理由说明以用户的提示语言呈现（EN 或 FR；FR 图表名称按术语表的 FR 列）。提取的证据和图表标签保持源语言逐字不变，绝不翻译。HTML 导出界面通过 `render_html.py --ui-lang en|fr` 跟随。

## 脚本

所有脚本命令均从技能根目录（包含本 `SKILL.md` 的文件夹）运行。解析一次技能根目录，然后以 `python scripts/<name>.py` 形式调用脚本。

| 脚本                        | 作用                                                                                    |
| ----------------------------- | --------------------------------------------------------------------------------------- |
| `scripts/check_setup.py`      | 依赖检查 → `{ok, missing[], installed[], optional{}}`                           |
| `scripts/first_run.py`        | 首次运行状态 → `{state}`（`returning`/`first_run`/`unknown`）；`--mark` 消费标志 |
| `scripts/extract_entities.py` | 编排器：规范化 → 检测 → 清单 JSON                                        |
| `scripts/diagram_selector.py` | 丰富化提取 + 意图 → 推荐类型                                         |
| `scripts/patch_gate.py`       | 第 2 遍补丁门控：验证并应用 LLM JSON Patch → `{ok, findings[], enriched_extraction_result}` |
| `scripts/eval_pass2.py`       | 第 2 遍评估评分器：根据标签期望评定 LLM 补丁 → `{ok, results[], score}` |
| `scripts/render_html.py`      | Mermaid + FigureDescription → 独立 HTML                                           |

`scripts/normalize/`（格式适配器）和 `scripts/extraction/`（候选实体采集器、解析器和实体化器）是编排器使用的库。一次性安装依赖：`pip install -r requirements.txt -c constraints.txt` 用于发布验证版本，或省略 `-c constraints.txt` 以进行广泛兼容性测试。

## 工作流加载映射

| 意图/需求                                                  | 文件                       |
| ------------------------------------------------------------ | -------------------------- |
| 首次运行演练 + 设置门控                           | `workflows/tutorial.md`    |
| 交互式默认通道（摘要/信息引导 → 菜单）              | `workflows/guided.md`      |
| 高级用户通道（读取所有信号，硬上限 1）               | `workflows/direct.md`      |
| 共享生成核心（选择 → 防护 → 生成 → 交付） | `workflows/generation.md`  |
| 两遍提取（两条通道均调用）                   | `workflows/extract.md`     |
| 第 2 遍质量评估（执行丰富化，根据标签评分） | `workflows/eval-pass2.md`  |
| 无文档摄取集 + 交付模式                       | `shared/elicitation.md`    |
| 独立 HTML 图形导出                                | `workflows/html-export.md` |

## 参考加载映射

| 意图/需求                                                       | 文件                                  |
| ----------------------------------------------------------------- | ------------------------------------- |
| 依赖检查流程                                        | `shared/setup-check.md`               |
| 按类型防护、实体规范化、解析器缺陷                | `shared/parser-guards.md`             |
| FigureDescription 字段、标题、图例、风险评分标准、注意事项 | `shared/figure-description-schema.md` |
| 30 个法律类别 → Mermaid 类型                                | `shared/diagram-type-map.md`          |
| 语义节点类别、调色板、CSS 类命名               | `shared/node-styles.md`               |
| 字段目录 + 检测层级 + 信号                       | `references/extraction-schema.md`     |

## 输出

输出仅为 CLI 显示：围栏 Mermaid 块在 Claude 网页应用中渲染为工件，在 CLI 中渲染为语法高亮代码。不写入笔记文件。该块之后，门控 B 以可选择项的形式提供 HTML 报告；导出会转义事项文本、以严格模式运行 Mermaid、在存在随附引擎时使用它，并且仅在显式启用时才加载固定的 CDN 回退。完整输出规则：`workflows/generation.md` 第 5 步。

## 边界

Mermaid 用于思考、规划、解释和生成结构。它不是法律建议、不是可提交法院的证据材料，也不是法律写作的替代品。每张图表都带有一行注意事项。机密材料仅保存在经批准用于该事项的工具中。
