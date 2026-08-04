# 图表类型映射（共享）

30 个法律类别映射到 Mermaid 类型。来源分类法：legal-diagram 发现文档。由 `direct.md` 第 2 步和 `extract.md` 第 5 步使用。

**如何阅读。** 用户点名法律类别时 → 映射到其**主**类型。若行标记为**歧义** → 不直接映射；使用丰富化提取调用 `diagram_selector.py`，让实体计数打破平局。**驱动字段** = 主导选择的 `ExtractionResult` 字段。

|#|类别|主类型|备选|驱动字段|歧义|怪癖|
|---|---|---|---|---|---|---|
|1|法律流程地图|flowchart|state diagram|process_steps, decision_points|否|flowchart|
|2|法律决策树|flowchart||decision_points|否|flowchart|
|3|争点 / 主张—抗辩地图|flowchart|erDiagram|concepts, relationships|是|flowchart|
|4|时间脉络 / 时间线|timeline|gantt|events|是|timeline|
|5|诉讼期限规划|gantt|timeline|tasks, deadlines, phases|否|gantt|
|6|当事方 / 实体关系|erDiagram|flowchart, classDiagram|ownership_links, relationships, entities|是|erDiagram|
|7|合同架构|flowchart|mindmap, requirementDiagram|relationships, concepts, documents|是|flowchart|
|8|谈判 / 立场地图|quadrantChart|flowchart, mindmap|negotiation_issues, risk_items|否|quadrantChart|
|9|合规义务地图|requirementDiagram|flowchart, state diagram|obligations, controls|否|requirementDiagram|
|10|数据隐私 / 数据流|flowchart|sequenceDiagram, erDiagram|data_flows|是|flowchart|
|11|电子证据开示工作流|state diagram|flowchart, gantt|states, transitions, process_steps|是|state diagram|
|12|特权 / 保密|state diagram|flowchart|decision_points, states, transitions|是|state diagram|
|13|监管调查|sequenceDiagram|flowchart, timeline, gantt|communications, events|是|sequenceDiagram|
|14|交易 / 交易执行|gantt|flowchart, sequenceDiagram, erDiagram|phases, tasks, conditions|是|gantt|
|15|资金流向 / 资金变动|sequenceDiagram|flowchart|transfers, communications|是|sequenceDiagram|
|16|公司治理 / 审批|state diagram|flowchart, sequenceDiagram|process_steps, conditions|是|state diagram|
|17|法律接案 / 分诊|state diagram|flowchart|states, transitions|是|state diagram|
|18|法务运营 / 知识管理|quadrantChart|flowchart, mindmap|risk_items|是|quadrantChart|
|19|客户咨询 / 解释|journey|flowchart, timeline|process_steps|是|journey|
|20|法律研究地图|mindmap|flowchart, classDiagram|concepts, legal_authorities|是|mindmap|
|21|法规 / 监管结构|requirementDiagram|flowchart, mindmap|obligations, concepts|是|requirementDiagram|
|22|诉讼策略 / 案件理论|quadrantChart|mindmap, flowchart, timeline|risk_items, concepts|是|quadrantChart|
|23|取证 / 证人准备|mindmap|flowchart, timeline|witnesses|是|mindmap|
|24|仲裁 / 争议解决|timeline|gantt, flowchart, sequenceDiagram|events, phases, transitions|是|timeline|
|25|知识产权策略 / 申请程序|state diagram|flowchart, timeline, mindmap|states, transitions, ip_assets|是|state diagram|
|26|雇佣 / 人力资源工作流|timeline|flowchart, state diagram|events, investigation_steps, transitions|是|timeline|
|27|不动产 / 建设工程|gantt|timeline, flowchart, erDiagram|phases, tasks|是|gantt|
|28|破产 / 重组|timeline|flowchart, erDiagram|claim_classes, transfers|是|timeline|
|29|税务规划 / 税务争议|erDiagram|flowchart, timeline|entities, relationships, transfers|是|erDiagram|
|30|AI / 网络 / 科技法|requirementDiagram|flowchart, sequenceDiagram, state diagram|obligations, controls, data_flows|是|requirementDiagram|

**渲染器说明。** `Sankey`、`architecture`、`kanban`、`classDiagram` 渲染不均匀。选择器绝不返回它们；替换为所列主类型（例如 Sankey 资金流向用 flowchart、classDiagram 实体模型用 erDiagram）。怪癖列 → `shared/parser-guards.md` 中的对应行。

## 思维导图范围规则

思维导图 = **仅用于头脑风暴和方向梳理。** 树状结构：每个节点恰好一个父节点；边不带标签；无法交叉链接。仅在层级关系是全部要点且不需要关系精确性时使用。

**当事项涉及以下任何内容时禁止使用思维导图：**

- 论点、主张或抗辩（节点之间的定向支持/矛盾）
- 证据链（一项事实支持多个主张，或削弱某项抗辩）
- 义务、合规或监管要求
- 定向因果（X 导致 Y 导致 Z）
- 需要带标签边或基数的当事方、实体或关系
- 任何措辞为“映射论点”“展示 X 如何支持 Y”“追踪推理”的意图

对于以上所有情况，使用 **flowchart**（带标签边的有向图）。流程图能表达思维导图能表达的一切，外加定向逻辑、多父节点和边缘标签。只要提取中填充了任何精确性字段，选择器就必须优先 flowchart 而非 mindmap。

**精确性防护（从 `workflows/generation.md` 第 1 步调用）。** 当固定类型为 `mindmap` 时，检查丰富化提取中是否有任何非空精确性字段：`obligations`、`parties`、`ownership_links`、`relationships`、`risk_level`、`decision_points`、`process_steps`、`communications`、`transfers`、`risk_items`、`legal_authorities`。若任何字段已填充，在继续前标记一次不匹配：

> “思维导图是树：无边标签、无定向逻辑、无交叉链接。您的事项有 [已填充字段]，需要定向关系。**流程图**能保留这种精确性。按思维导图继续、切换到流程图，还是选择备选方案？”

等待用户回答。这计为允许的一次中断。用户确认后，尊重其选择，不再提出质疑。

## 通俗名称（面向用户）

在用户阅读的所有文本中，用这些通俗词语命名图表，绝不用 Mermaid 类型。技术名称保持内部使用（脚本、工作流）。接受用户的通俗词语请求并以相同方式映射回类型。FR 提示双向使用 FR 列（接受和表达）。

|Mermaid 类型|对用户说|法语|
|---|---|---|
|`timeline`|timeline（时间线）|chronologie|
|`gantt`|schedule（带持续时间的时间线）|échéancier|
|`flowchart`|flowchart（流程图），或走 yes/no 检验时用“decision tree”（决策树）|schéma, ou « arbre de décision »|
|`state diagram`|status flow（事物如何在阶段间流转）|flux de statuts|
|`erDiagram`|org chart（组织结构图），或 relationship map（关系图）|organigramme|
|`requirementDiagram`|obligation checklist（义务清单/合规地图）|liste d'obligations|
|`sequenceDiagram`|who-does-what-when（谁在何时做什么，往复图）|qui-fait-quoi-quand|
|`mindmap`|mind map（思维导图）|carte mentale|
|`quadrantChart`|priority grid（优先级网格，2x2）|grille de priorités|
|`journey`|experience map（体验图）|carte d'expérience|

示例交付：“我绘制了一张 **时间线**。此事项也可作为 **组织结构图** 或 **义务清单** 呈现——需要其中一种吗？”而非：“recommended_type: timeline, alternatives: erDiagram, requirementDiagram.”
