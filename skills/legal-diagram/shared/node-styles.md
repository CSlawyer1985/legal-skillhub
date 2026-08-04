# 节点样式——语义颜色系统

在 `workflows/generation.md` 第 3.5 步（语义映射构建）和 `workflows/html-export.md` 第 2 步加载。

## 通用基础调色板（始终激活，所有图表类型）

|类别|CSS 类|填充|描边|无障碍图案|
|---|---|---|---|---|
|当事方 / 利益相关方|`sem-party`|`#C9D6E3`|`#8FA8BE`|无|
|法律依据 / 规则|`sem-authority`|`#CAD2C5`|`#8A9E84`|斜向阴影线|
|风险 / 关注点|`sem-risk`|`#D6B8B8`|`#A87878`|交叉阴影线|
|结果 / 立场|`sem-outcome`|`#CFCFCF`|`#909090`|圆点|
|流程步骤|`sem-process`|`#F5F3EE`|`#B0A898`|无（默认中性）|

风险修饰类（可叠加，与任何类别堆叠）：`sem-risk-high`——应用于任何来自 `risk_level: "high"` 的义务或期限节点；将描边加深为 `#8B4444`，描边宽度 2.5。

## 领域扩展调色板（按 `matter_type` 键控）

当 `extraction_result.matter_type` 匹配时加载对应行。未知或缺失 `matter_type` → 仅使用基础调色板。

|matter_type|类别|CSS 类|填充|描边|图案|
|---|---|---|---|---|---|
|litigation|证据 / 记录|`sem-evidence`|`#D8D3E8`|`#9888B8`|圆点|
|litigation|主张要件|`sem-claim`|`#DDD2C2`|`#A89878`|斜向阴影线|
|corporate|股权链|`sem-ownership`|`#D3DDE8`|`#7898B8`|斜向阴影线|
|corporate|财务节点|`sem-financial`|`#E6D3A3`|`#B89840`|圆点|
|compliance|控制措施|`sem-control`|`#D4E8D3`|`#78A878`|斜向阴影线|
|compliance|差距|`sem-gap`|`#E8D6B8`|`#B89860`|交叉阴影线|
|privacy|数据流|`sem-dataflow`|`#D8E8E3`|`#78A898`|圆点|
|employment|调查发现|`sem-finding`|`#E3D8E8`|`#9878A8`|圆点|
|ip|知识产权资产|`sem-ip-asset`|`#D8E3D8`|`#789878`|斜向阴影线|
|tax, bankruptcy|财务节点|`sem-financial`|`#E6D3A3`|`#B89840`|圆点|

## ExtractionResult 字段 → 类别映射（确定性查找）

在任何 LLM 分类之前应用。匹配已知字段中已提升实体的节点 ID 被确定性分配——无需推断。

|ExtractionResult 字段|基础类别|事项类型覆盖|
|---|---|---|
|`parties`|`sem-party`|—|
|`entities`|`sem-party`|—|
|`legal_authorities`|`sem-authority`|—|
|`controls`|`sem-authority`|compliance → `sem-control`|
|`risk_items`|`sem-risk`|—|
|`claim_classes`|`sem-risk`|litigation → `sem-claim`|
|`decision_points`|`sem-risk`|—|
|`events`、`process_steps`、`phases`、`tasks`、`investigation_steps`|`sem-process`|—|
|`obligations`、`deadlines`、`conditions`|`sem-process`|+ 若 `risk_level: "high"` 则 `sem-risk-high`|
|`documents`、`witnesses`|`sem-process`|litigation → `sem-evidence`|
|`ownership_links`、`transfers`|`sem-process`|corporate/tax → `sem-ownership` 或 `sem-financial`|
|`data_flows`、`communications`|`sem-process`|privacy → `sem-dataflow`|
|`states`、`transitions`|`sem-process`|—|
|`concepts`、`negotiation_issues`|`sem-risk`|—|
|`ip_assets`|`sem-process`|ip → `sem-ip-asset`|
|推断结论 / 结果节点|`sem-outcome`|—|

## 剩余分类（LLM 遍历）

未被上述字段查找匹配的节点（子图标签、连接桥接文本、合成节点、结果摘要节点）→ 由 LLM 分类。将 LLM 约束为**仅活动类别集**（基础 5 类 + 当前 `matter_type` 的领域扩展）。将活动集限制为 ≤10 个类别；保持跨会话分类一致。

要在第 3.5 步中包含的提示片段：
> 仅使用下方活动类别对每个未列出节点 ID 分类。仅返回 JSON——无叙述文字。
> 活动类别：[列出活动调色板中的 `sem-*` 类名]
> 格式：`{"NODE_ID": "sem-class", "NODE_ID": "sem-class sem-risk-high"}`
> 规则：(1) 使用确切类名；(2) 类以空格分隔且可叠加；(3) 确实模棱两可时，分配 `sem-process`。

## 语义映射 JSON 模式

生成步骤将此对象作为 `semantic_map_json` 发出，并传给 HTML 导出步骤：

```json
{
  "meta": {
    "matter_type": "litigation",
    "diagram_type": "flowchart",
    "active_palette": ["sem-party", "sem-authority", "sem-risk", "sem-outcome", "sem-process", "sem-evidence", "sem-claim"]
  },
  "nodes": {
    "CLAIM": "sem-claim",
    "ISSUE1": "sem-claim",
    "NWR1": "sem-authority",
    "NWR2": "sem-authority",
    "SEC": "sem-outcome",
    "RELIEF": "sem-outcome",
    "NWRC": "sem-outcome sem-risk-high"
  }
}
```

`meta.active_palette` 驱动图例；列出 `nodes` 中使用的所有类，去重，基础类别在前。

## CSS 类命名契约

- 前缀：始终为 `sem-`
- 类可叠加：节点可携带 `sem-process sem-risk-high`
- 主类（第一个）决定填充颜色和图案；修饰类仅调整描边
- 绝不在此参考之外发明新类名——若需要新类别，请添加到此文件

## 容器层级调色板

子图容器（分组或嵌套）按嵌套深度着色，而非按语义类别。灰度，因此绝不与彩色节点 `sem-*` 填充冲突。`render_html.py` 从 `semantic_map.containers` 发出 `style <subgraph-id> fill:...`（仅限 flowchart/graph）；超过层级 2 的深度钳制到层级 2。

|层级|深度|填充|描边|
|---|---|---|---|
|0|最外层|`#F7F7F5`|`#D8D8D2`|
|1|向内一层|`#ECECE6`|`#C8C8C0`|
|2|向内两层|`#E0E0D8`|`#B8B8AE`|

契约：层级色调仅限灰度；绝不复用节点 `sem-*` 填充。容器编码深度，而非类别。
