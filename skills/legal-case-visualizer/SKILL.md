---
name: legal-case-visualizer
description: 法律案件分析报告可视化工具，将案件分析报告中的主体关系、债权链条、时间轴、风险矩阵等核心内容转换为专业SVG图表，供律师直观阅读。本技能应在用户需要将法律案件分析报告（如iterative-analysis技能输出的报告）中的文字描述转化为可视化图表时使用。不要用于：生成非法律类图表、通用数据可视化、代码结构分析。
license: CC BY-NC-SA 4.0 - 详见 LICENSE.txt
---

# legal-case-visualizer（优化版）

目标：把法律案件报告转成**可直接交付的 HTML 可视化报告**，图表使用内嵌 SVG，支持浏览器内**一键导出 PDF**（打印为 PDF）。

---

## 1. 适用边界

仅用于法律案件报告可视化，特别是执行、追偿、担保、债权转让、关联主体分析场景。  
不用于通用 BI 图表、财务分析仪表盘、代码架构图。

---

## 2. 强制原则（本技能核心）

### 2.1 事实分层（必须执行）

先把信息分成两层，再画图：

- **A层：核心确认法律事实**（可入主图实线）
  - 生效判决/裁定/调解书
  - 已签署合同、担保文件、登记信息
  - 已发生执行措施（查封、拍卖、以物抵债、终本等）
- **B层：待核实线索**（仅可用虚线或“待核实”标签）
  - “疑似”“可能”“待查询”事项
  - 外部平台关系圈线索但无文书支撑事项

### 2.2 可视化逻辑

- 主图先展示 A 层事实关系，再附 B 层补充线索。
- 不得把 B 层线索画成既定结论。
- 文档顺序优先，图表顺序与原报告模块一致。

### 2.3 技术极简

仅用：

- `HTML + CSS + SVG + 少量原生JS`
- PDF 导出仅用浏览器打印：`window.print()`

禁止引入复杂前端框架。

---

## 3. 输出物标准（默认）

默认输出一个文件：`案件可视化报告.html`

该文件应包含：

1. 顶部工具栏（标题、导出按钮）
2. 按报告顺序排列的章节
3. 每章一个或多个 SVG 图
4. 页脚“事实依据说明/版本信息”

---

## 4. 标准章节顺序（按文档逻辑）

按原报告顺序排版：

1. `案件摘要`（文字卡片）
2. `图V1 主体关系网络图`
3. `图V2 债权转让与担保链条图`
4. `图V3 案件时间轴图`
5. `图V4 资产状况与追偿路径图`
6. `图V5 风险矩阵图`
7. `图V6 行动优先级图`
8. `事实依据与核验说明`

若源报告缺少某类数据，可省略对应图，但须写“未生成原因”。

---

## 5. 图表规则（简化且可执行）

### 5.1 V1 主体关系网络图

目的：展示控制关系、债权关系、担保关系、执行主体关系。  
要求：

- 主体类型分形状（自然人圆、公司圆角矩形）
- A层事实连线为实线；B层线索连线为虚线并标“待核实”
- 被执行人边框红色，申请执行人边框绿色

### 5.2 V2 债权链条图

目的：展示“原始债权人→受让链→现债权人”，并并列展示借款/担保结构。  
要求：

- 左侧债权转让纵向链
- 右侧借款与担保关系
- 金额统一单位（万元/亿元）并标注口径

### 5.3 V3 时间轴图

目的：展示关键法律事件的先后关系。  
要求：

- 节点必须有日期
- 事件分色：借款、违约、转让、执行、裁判
- 异常事项必须有“待核实/异常”标记

### 5.4 V4 资产与追偿图

目的：展示已处置资产、可执行资产、潜在追偿路径。  
要求：

- 三列布局：已处置 / 可执行 / 追偿路径
- 每项标注状态（已处置/轮候查封/待核实）

### 5.5 V5 风险矩阵

目的：展示风险等级与紧迫程度。  
要求：

- 风险点必须来自报告文本，不凭空新增
- 每个风险点附简要法律后果

### 5.6 V6 行动优先级图

目的：展示执行动作与时间安排。  
要求：

- 维度至少包含：任务、责任主体、时限、优先级
- 与报告行动计划逐项对应

---

## 6. 一键导出 PDF（强制支持）

HTML 内必须包含“导出PDF”按钮，调用：

```html
<button onclick="window.print()">导出PDF</button>
```

并配置打印样式：

```css
@media print {
  .toolbar { display: none; }
  .section { break-inside: avoid; page-break-inside: avoid; }
  @page { size: A4 portrait; margin: 12mm; }
}
```

说明：浏览器执行“打印为 PDF”即完成导出，属于最简、稳定方案。

---

## 7. HTML 最小模板（直接复用）

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>法律案件可视化报告</title>
  <style>
    :root{
      --bg:#f5f7fa; --card:#fff; --text:#1f2d3d; --line:#d9e1e8;
      --primary:#1a3a5c; --danger:#e05a47; --warn:#d4a017; --ok:#2e7d32;
    }
    body{margin:0;background:var(--bg);color:var(--text);font:14px/1.6 "PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;}
    .toolbar{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;padding:10px 16px;background:#fff;border-bottom:1px solid var(--line);}
    .main{max-width:1200px;margin:16px auto;padding:0 12px;}
    .section{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:12px;}
    h1,h2{margin:0 0 10px 0;color:var(--primary);}
    .note{font-size:12px;color:#5b6b7b}
    svg{width:100%;height:auto;border:1px solid #eef2f6;border-radius:8px;background:#fff}
    @media print{
      .toolbar{display:none}
      .section{break-inside:avoid;page-break-inside:avoid}
      @page{size:A4 portrait;margin:12mm}
      body{background:#fff}
    }
  </style>
</head>
<body>
  <div class="toolbar">
    <strong>法律案件可视化报告</strong>
    <button onclick="window.print()">导出PDF</button>
  </div>
  <main class="main">
    <section class="section"><h2>案件摘要</h2></section>
    <section class="section"><h2>图V1 主体关系网络图</h2><!-- svg --></section>
    <section class="section"><h2>图V2 债权转让与担保链条图</h2><!-- svg --></section>
    <section class="section"><h2>图V3 案件时间轴图</h2><!-- svg --></section>
    <section class="section"><h2>图V4 资产状况与追偿路径图</h2><!-- svg --></section>
    <section class="section"><h2>图V5 风险矩阵图</h2><!-- svg --></section>
    <section class="section"><h2>图V6 行动优先级图</h2><!-- svg --></section>
    <section class="section"><h2>事实依据与核验说明</h2></section>
  </main>
</body>
</html>
```

---

## 8. 工作流程（执行版）

### Step 1：读取报告并抽取事实

- 建立“事实清单表”：主体、关系、金额、时间、证据来源、事实层级（A/B）

### Step 2：先出结构再出图

- 确认章节顺序与图表范围
- 先排版 HTML 骨架，再填充 SVG

### Step 3：生成 SVG

- 一图一义，避免信息过载
- 每张图底部给出“事实口径说明”

### Step 4：嵌入导出能力

- 顶部固定导出按钮
- 打印样式确保 A4 可读

### Step 5：质检

- 事实准确性（A/B层是否混淆）
- 视觉可读性（字号、间距、色彩）
- 导出可用性（按钮可触发打印）

---

## 9. 输出格式要求

优先输出完整 HTML 文件内容或直接写入 `*.html` 文件。  
如用户仍要求 Markdown，则在 Markdown 中内嵌完整 HTML 代码块，并明确“可另存为 html 后一键导出 PDF”。

---

## 10. 质量检查清单（交付前必须通过）

- [ ] 图表顺序与原报告模块顺序一致
- [ ] 主图只使用 A 层核心确认事实
- [ ] B 层线索全部有“待核实”标注
- [ ] 所有金额、时间、案号与原文一致
- [ ] HTML 在浏览器可直接打开
- [ ] “导出PDF”按钮可用（触发打印）
- [ ] 打印后版面未明显错位

---

## 11. 与其他技能配合

- 上游：`iterative-analysis` / `legal-case-analysis`（提供案件事实与结构化文本）
- 下游：可直接交付 HTML；如需文档化可再交由其他技能转存

本技能已内置 HTML 与 PDF 导出能力，通常无需额外转换技能。
