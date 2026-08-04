# 生成工作流（共享核心）

由 `direct.md` 和 `guided.md` 共享的图表生成核心。两条通道仅在信息引导和确认上不同；生成 = 完全相同，只存在于此一处。

**调用方契约。** 输入：丰富化的 `ExtractionResult`、`intent` 字符串（或固定的 Mermaid 类型）、`mode`（`direct` | `guided`）、输出偏好（HTML 标志、路径覆盖）。

## 第 1 步——选择类型

调用方传入固定 Mermaid 类型 → 若类型为 `mindmap`，在尊重它之前按 `shared/diagram-type-map.md` 的“思维导图范围规则”一节应用精确性防护。否则直接进行。使用意图运行 `python scripts/diagram_selector.py --extraction-json <enriched JSON>`。保留 `recommended_type`、`rationale`、`alternatives`、`confidence`、`density`（在第 3.4 步消费的包含目标）和 `geometry`（同样在第 3.4 步消费的布局可读性判定）。

置信度门控，**仅直接模式**（硬上限 1）：< 0.50 → 呈现前 2 个并询问一次；≥ 0.50 → 继续。引导模式绝不在此阻塞；已显示摘要并在交付时提供备选方案。

## 第 2 步——防护

加载 `shared/parser-guards.md`；按类型应用防护。对于 `erDiagram`/`flowchart`，按“实体名称规范化”一节规范化实体名称（记录每次替换）。

## 第 3 步——生成

以原生方式输出围栏 Mermaid 块。将节点标签宽度限制在约 40 字符（宽度限制，而非内容限制）：将长内容拆分为更多节点，绝不为了适配而丢弃或合并实体。自检：每个被引用的节点都已声明；无未闭合的括号或引号；每个包含元字符（`( ) [ ] { } | : ; # & < > " ,`）的节点和边缘标签都按 `shared/parser-guards.md` 的“节点和边缘标签”一节加双引号；保留字 ID（`end`、`state` 等）已规范化；无尾随 `%%` 注释。

**分组与嵌套（当 `grouping_suggested: true` 或 `extraction_result.hierarchy` 已填充时）。** 构建包含关系，`flowchart TB`：
- `hierarchy` 已填充 → 按节点深度嵌套：深度 0 = 最外层子图，深度 1 嵌套在其 `parent` 内，深度 2 嵌套在更内层。深度硬上限 2；更深的层级折叠为一个摘要节点（详情 → 图形描述）。
- 无 `hierarchy` → 按 `grouping_axis` 键控的单一包含层。`axis: "era"` → 按时期分组事件；在每个时期组内按时间顺序串联。
- 每个子图：唯一字母数字 ID（复用 `hierarchy` 节点 `id`）、人类可读标签、`direction TB`。一个子图中兄弟节点过多 → 先按子轴拆分；仅作为最后手段折叠为摘要节点。“绝不缩小”约束的是字体/间距/画布，而非节点数。

**可读性优先于适配。** 绝不缩小字体、间距或画布来适配，也绝不过度截断；这些约束的是呈现方式，而非节点数。按内容设定尺寸；HTML 导出支持平移和缩放，因此大而清晰胜过小而拥挤。约 40 字符上限仅限制标签宽度：将内容拆分为更多节点，而非丢弃或合并；完整的逐字文本也存在于图形描述中，绝不作为节点的替代品。

## 第 3.4 步——节点密度（在图表中承载细节）

细节应存在于图表中，而非仅存在于图形描述中。按调用方的 `intent` 设定节点数，以**显著实体**（已填充的 `ExtractionResult` 列表字段：当事方、事件、义务、期限、决策点、付款、风险事项、条件、文件）为基准：

| 意图 | 呈现为节点的比例 |
|---|---|
| comprehensive（全面）/ exhaustive（详尽）/ “everything”（全部） | 显著实体的 85-95% |
| detailed（详细）/ thorough（深入） | 60-75% |
| overview（概览）/ “at a glance”（一览）/ 高层 | 30-45% |

意图模糊时，或用户同时要求“详细”和“一览”时（平移/缩放使大图可一览），默认 **comprehensive（全面）**。实例：100 项义务 + 全面意图 → 约 85-95 个节点。

**先拆分后折叠。** 当一组兄弟节点过多时，按子轴（日期、当事方、类型）拆分。仅作为最后手段折叠为摘要节点（达到深度上限或确实不可读）；然后将每个被省略的实体逐字连同其来源引用倒入图形描述。绝不静默丢弃实体。

若 `diagram_selector` 发出了 `density` 块，将其包含区间作为目标：达到它，或说明偏离原因。

**几何门控（形状，而非覆盖率）。** 密度决定多少实体成为节点；几何判断这些节点的布局是否清晰。驱动挤压的是广度（最宽层级中的节点数），而非总数：深窄图没问题，浅宽图不可读。若 `diagram_selector` 发出了 `geometry` 块，按其 `band` 行动：

- `green` → 作为一张图交付。
- `warn` → 交付一张，将局限（宽层级、深扇出）写入图形描述；若容易，则重新平衡 `direction` 或修剪交叉边。
- `split` → 在导出前沿 `geometry.split_axis_suggestion`（日期、当事方、类型）拆分为多张聚焦图。保持每个子图在 green 区间内（每个层级 ≤ 约 6-7 个节点）；超出区间的子图再次拆分。每个子图按 `workflows/html-export.md` 的“多张图表”一节导出为独立文件。这是子图子轴拆分与折叠为摘要之间的升级阶梯；它将同一批实体重新分配到更多图表中，绝不丢弃任何一个。

缩放不是替代品：平移/缩放能挽救深窄图，但宽层级会使适配框架的字体低于可读性，因此广度驱动的 `split` 判定需要真正的拆分。

**导出前预览（尽力而为）。** 在提供 HTML 报告之前，确认围栏 Mermaid 块在您的预览界面（网页应用工件或本地 Mermaid 预览）中渲染时无“Syntax error”。在 CLI 上，预览和导出引擎是同一个固定的 Mermaid 11；在网页应用上，预览引擎由平台控制，可能不同于导出引擎，因此干净的预览是强信号，而非保证。无可用预览 → 跳过此步，依赖导出时的渲染检查。

## 第 3.5 步——构建语义映射

围栏 Mermaid 块组装完成后，为 HTML 导出着色层分类所有节点 ID。加载 `shared/node-styles.md`。

1. **活动调色板** = 基础 5 类 + 与 `extraction_result.matter_type` 匹配的领域扩展行。
2. **确定性遍历**：对 `extraction_result` 中的每个已提升实体，在“ExtractionResult 字段 → 类别映射表”一节中查找字段。将节点 ID（Mermaid 源码中使用的标签）映射到对应的 `sem-*` 类。为任何 `risk_level == "high"` 的义务/期限节点添加 `sem-risk-high`。
3. **剩余遍历**：对任何尚未分类的节点 ID（子图标签、连接文本、合成节点），仅使用 `shared/node-styles.md` 的“剩余分类”一节中的剩余分类提示，从活动调色板分类。仅返回 JSON。
4. **容器（仅分组图）**：当图表使用子图时，将每个子图 ID 映射到其嵌套深度，最外层为 `0`，向内一层为 `1`，依此类推。未分组图 → 省略或留空。
5. **发出语义映射**：
   ```json
   {
     "meta": { "matter_type": "...", "diagram_type": "...", "active_palette": [...] },
     "nodes": { "NODE_ID": "sem-class", ... },
     "containers": { "SUBGRAPH_ID": 0, ... }
   }
   ```
   存储为 `semantic_map_json` 并传给 `workflows/html-export.md`。若 HTML 导出被拒绝则丢弃。

**⛔ 类名约束。** 仅使用 `shared/node-styles.md` 的“通用基础调色板”和“领域扩展调色板”一节中定义的类。有效类为：`sem-party`、`sem-authority`、`sem-risk`、`sem-outcome`、`sem-process`、`sem-evidence`、`sem-claim`、`sem-ownership`、`sem-financial`、`sem-control`、`sem-gap`、`sem-dataflow`、`sem-finding`、`sem-ip-asset`，以及修饰类 `sem-risk-high`。绝不发明新的 `sem-*` 类名——未列出的类不会产生颜色。

**classDef 注入（自动）。** `render_html.py` 从 `semantic_map.nodes` 推导 Mermaid `classDef` + `class` 语句，并在渲染时将它们追加到图表块。这是 `flowchart` 和 `stateDiagram` 类型的主要节点着色机制。**不要**在 Mermaid 块中手动发出 `classDef` 或 `class` 语句——`render_html.py` 拥有此步骤。

**容器着色（自动）。** `render_html.py` 从 `semantic_map.containers` 推导 Mermaid `style <subgraph-id> fill:...` 语句，按深度层级为每个子图着色（浅到深、灰度、仅限 flowchart/graph；超过层级 2 的深度钳制）。**不要**手动发出容器 `style` 语句。层级色调：`shared/node-styles.md` 的“容器层级调色板”一节。

## 第 3.6 步——构建摘要表（始终，除非被拒绝）

从 `ExtractionResult` 为 HTML 导出中的源文档选项卡构建 `digest_rows`。**默认 = 始终发出。** 仅当用户在本会话中明确说过“不要源表”“不要验证表”或类似表述时才跳过。

对 `ExtractionResult` 中每个已填充的字段（义务、条件、期限、事件、当事方、决策点、风险事项），每个实体发一行：

| 字段 | `row.category` |
|---|---|
| `obligations` | `Obligation` |
| `conditions` | `Condition` |
| `deadlines` | `Deadline` |
| `events` | `Key Event` |
| `parties` | `Party` |
| `decision_points` | `Decision` |
| `risk_items` | `Risk` |
| `documents` | `Document` |
| 仅提示 / 未验证 | 相同类别 + `unverified: true` |

行字段：`row_num`（顺序号）、`category`、`finding`（简短标签）、`party`（或 null）、`verbatim`（文档中的精确文本——使用 `extraction_hints[].snippet` 或 `llm_enrichment.evidence_packets[].text`；绝不意译）、`anchor`（来自 `source_ref` 或 `anchor` 字段的段落/章节引用）、`source_doc`（输入文件的基本名称）。

对任何仅提示实体或无法从提取证据确认源文本的实体，标记 `unverified: true`。它们在表中以 ⚠ 渲染。

## 第 4 步——交付（理由 + 备选方案）

在用户阅读的所有内容中使用 `shared/diagram-type-map.md` 的“通俗名称”一节的通俗图表名称。绝不向用户打印 Mermaid 内部类型名称。

**若 `mode == "guided"`：** 仅显示围栏 Mermaid 块和清理说明。无理由、无备选方案；用户已在第 2.5 步看到两者。

**若 `mode == "direct"`：** 完整输出，无前言：
1. 内联围栏 Mermaid 块（块使用技术语法；预期且正常）。
2. 理由，一行通俗语言：“我绘制了一张 <通俗名称>，因为 <选择器理由，以通俗方式重述>。”
3. 备选方案，一行：“此事项也可作为 <通俗备选1>（<它展示什么>）或 <通俗备选2>（<它展示什么>）呈现——需要其中一种吗？”从 `shared/figure-description-schema.md` 的标题模式中提取“它展示什么”。仅提供有已填充驱动字段支持的类型；绝不列出无支撑数据的类型。
4. 任何清理事项的要点列表（规范化名称、转义冒号、截断标签）。

## 第 5 步——输出与门控 B（HTML 报告）⛔ 阻塞

不写入笔记文件。围栏 Mermaid 块（第 3-4 步）在 Claude 网页应用中渲染为工件，在 CLI 中渲染为语法高亮代码。

门控 B = 强制硬停点。除非用户输入了字面量 `--html` 标志（预先作答为 **HTML 报告**），否则始终触发。绝不从措辞推断答案；绝不跳过。以结构化选择（问题工具）呈现**门控 B**，若宿主无选择工具则以带编号的纯文本列表呈现，而非输入式 Y/n，然后 STOP，等待回复。以通俗方式开场：“想要将完整报告保存为可打开、可打印、可分享的文件吗？它会将图表与文档中每条发现的精确措辞表格配对。”选项：

- **HTML 报告**（推荐，列在最前）
- **不，只要图表**

**HTML 报告** → 设置 `html_export=true`，然后加载 `workflows/html-export.md`（设置标志时它会跳过自己的选择加入），传入 `semantic_map_json`（第 3.5 步）、`digest_rows`（第 3.6 步）和 `source_path`。完成后以通俗英语确认。**不，只要图表** → 继续到第 6 步。

两条通道的单一 HTML 决策点；不提前预选 HTML，也不问两次。

## 第 6 步——优化/分支

在优化提示之前，重新呈现图表内容的紧凑参考，使没有 Mermaid 知识的用户有具体抓手。格式取决于图表类型：

- **flowchart / stateDiagram / sequenceDiagram**：列出子图/组名称及其中主要节点标签，例如“**No Written Rule** — Commissioner's Message, Rationale shifted, Not broadcast on WITV · **Minor Court Void** — Ordered charge himself, Presided as judge, Conflict admitted …”
- **erDiagram / classDiagram**：列出实体名称及其关系。
- **timeline / gantt**：列出章节标题和关键事件/任务。
- **mindmap**：列出顶层分支。
- **其他类型**：列出主要带标签元素。

然后：“想改什么吗？用通俗英语描述，点明替代图表类型，或请求 HTML 报告。”若在门控 B 拒绝了 HTML 而用户现在要求，加载 `workflows/html-export.md`。

接受通俗英语变更描述（“移除 Arbour 点”“将 CM Pitts 重命名为 Correctional Manager Pitts”“为和解提议添加节点”）→ 在重新生成前将其转化为结构性编辑。对任何新块重新运行防护。点明替代类型 → 全新生成遍历。若已导出 HTML，完整重新调用 `workflows/html-export.md`（重建 FigureDescription；绝不复用过期的）。
