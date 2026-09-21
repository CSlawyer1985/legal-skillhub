<!-- 本文件为「大成 Agent」通用版 v1 内容(2026-06,Claude 起草、供律所增量校订)。SKILL.md 只依赖文件存在与章节结构;律所可在保留各级标题的前提下增删条目。 -->

# HTML 可视化风格

本文件规定法规解读页的视觉与技术规范。目标是产出一份「打印得出、转发得动、离线打得开」的单文件 HTML:纸面质感、严肃克制、信息密度高于装饰密度。生成时遵循默认方向与自包含要求,并优先复用文末骨架。

## 默认方向

视觉基调:律所文书的纸面观感,不做营销页式的视觉堆叠。

- **背景与底色**:页面背景用暖白纸色 `#FBFAF6`;卡片底色用纯白 `#FFFFFF` 或更浅的 `#FFFEFB`,靠极浅边框与微弱阴影与背景拉开层次,不要大面积色块。
- **正文字体**:优先思源宋体,并以系统衬线兜底。统一字体栈:`"Source Han Serif SC", "Songti SC", "SimSun", "Noto Serif CJK SC", Georgia, serif`。**不外链任何 webfont**(见自包含要求),思源宋体仅在本机已安装时生效,否则自动落到系统衬线,排版不破。
- **正文字号与行距**:正文不小于 14px(推荐 15–16px),行高 1.7–1.8;长段落限制单行宽度(主内容区 `max-width` 约 800–880px),便于阅读与打印。
- **标题层级**:用字号、字重、字色区分层级,而非靠颜色块。H1 约 26–30px,H2 约 20–22px,H3 约 16–18px;标题可用深炭灰 `#1F2328`,正文用 `#2B2B2B`,辅助说明用 `#6B6B6B`。
- **强调色——大成紫**:主强调色 `#6B2D8B`,**克制使用**。只用于:H1/H2 的左侧细色条或下边线、关键标签底色、表格表头、重点条款的引用竖线。一屏内紫色面积建议不超过 10%。需要轻底色时用淡紫 `#F3ECF7`,需要分色时用一档辅助色即可(如义务用紫、责任/处罚用暗红 `#9B2C2C`、提示用琥珀 `#8A6D1F`),不要彩虹化。
- **卡片化与留白**:信息按语义分块成卡片,卡片圆角 8–10px、内边距 18–24px、卡片间距 16–20px。宁可多留白,不要把元素挤在一起。
- **不堆按钮**:这是阅读型文档,不是应用界面。**不放交互按钮、导航栏、折叠控件、悬浮操作条**。需要"标签"时用静态色块文字(如 `义务` `禁止` `罚则`),不是可点击按钮。全文应能在无 JavaScript 环境下完整阅读。
- **打印 / 转发 / 离线友好**:
  - 提供 `@media print` 规则:去掉多余阴影、保证背景色可打印(`-webkit-print-color-adjust: exact; print-color-adjust: exact;`)、避免卡片被分页截断(`break-inside: avoid;`)。
  - 不依赖网络、不依赖脚本即可完整呈现;双击本地文件应正常展示。
  - 颜色对比满足可读性(正文与背景对比度建议 ≥ 7:1),弱视与黑白打印都能读。
- **页脚来源与免责**:页面底部固定一块来源与免责区,标注解读所依据的文件名,并声明"本页为法律视角解读,仅供参考,不构成正式法律意见"。

必含与可选的可视化形式(均用纯 CSS 或内联 SVG 实现,**不引图表库**,不外链 webfont/CDN):

- **必含:义务矩阵表**:核心义务必须用原生 `<table>` 呈现。行=义务/事项,列=义务主体、触发条件、履行期限、对应条款、责任后果。表头用淡紫底,斑马纹用极浅灰提升可读性。适合"谁、在什么情况下、要做什么、不做会怎样"的结构化呈现。
- **必含:合规清单(checklist)**:必须包含合规清单。每条一行,前置静态方框 `☐`(U+2610,**不是** `<input type="checkbox">`,因为要适合打印后手填),后接合规动作 + 对应条款锚点。
- **必含:关键日期/过渡期时间线**:必须包含关键日期或过渡期时间线。用于生效节点、过渡期、整改期限或原文明确的阶段安排。用 CSS 或内联 SVG 串联节点,每节点标日期 + 事项 + 条款;没有明确日期时标"原文未明确"。
- **可选:条款对比卡片**:左右两栏或上下两块对比"旧版 vs 新版"或"原文 vs 解读",顶部用静态标签区分,差异处用淡色底纹高亮。仅在用户提供了对比/旧版文件时使用,不虚构差异。

## 自包含要求

与 `write_html` 的自包含校验一致:产出必须是**单文件、零外部网络资源**,离线双击可正常打开,不向任何外部域名发请求。

- **内联 CSS**:所有样式写在文档 `<head>` 的 `<style>` 标签内或元素 `style` 属性中。**禁止** `<link rel="stylesheet">` 引外部样式表。
- **图表用内联 SVG**:时间线、矩阵装饰、checklist 方框、对比连线等图形一律用文档内的 `<svg>` 元素直接绘制。**禁止**引用任何图表库(ECharts、Chart.js、D3、Mermaid 等)。
- **字体走系统兜底,绝不外链 webfont**:**禁止** `@font-face` 加载远程字体、**禁止** `@import` 或 `<link>` 引 Google Fonts / 字体 CDN。只用上文字体栈靠本机字体逐级兜底。也不内嵌 base64 字体(体积大且无必要)。
- **绝不引用外部资源**:**禁止**任何指向外部 CDN、外部图片(`<img src="http...">`)、外部脚本(`<script src="...">`)、外部样式或字体的链接。需要图标/插图时用内联 SVG 自绘。
- **脚本**:阅读型文档默认**不写 JavaScript**;若确有必要也只能内联且不发网络请求,且全文在禁用脚本时仍可完整阅读。
- **离线与隐私**:不得有 `fetch`、`XMLHttpRequest`、`<iframe src="http...">`、外部 `<a>` 自动跳转或任何回传文件内容的行为。生成后应可在断网环境双击打开、内容完整。

## 骨架示例

下面是一段可直接复用的自包含骨架(暖白纸背景、宋体兜底、克制紫色、含一个义务矩阵表、一条合规清单、一个内联 SVG 时间线、打印规则)。生成时在此基础上填充真实内容,保持自包含。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>法规解读 · 文件名称</title>
<style>
  :root{
    --paper:#FBFAF6; --card:#FFFFFF; --ink:#2B2B2B; --ink-strong:#1F2328;
    --muted:#6B6B6B; --line:#E6E1DA; --purple:#6B2D8B; --purple-soft:#F3ECF7;
    --danger:#9B2C2C; --warn:#8A6D1F;
    --serif:"Source Han Serif SC","Songti SC","SimSun","Noto Serif CJK SC",Georgia,serif;
  }
  *{box-sizing:border-box;}
  body{margin:0;background:var(--paper);color:var(--ink);
    font-family:var(--serif);font-size:15px;line-height:1.75;}
  .wrap{max-width:860px;margin:0 auto;padding:32px 24px 56px;}
  h1{font-size:28px;color:var(--ink-strong);margin:0 0 4px;
    border-left:5px solid var(--purple);padding-left:14px;line-height:1.3;}
  .sub{color:var(--muted);font-size:14px;margin:0 0 28px;padding-left:19px;}
  h2{font-size:21px;color:var(--ink-strong);margin:34px 0 14px;
    padding-bottom:6px;border-bottom:2px solid var(--purple-soft);}
  .card{background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:20px 22px;margin:16px 0;box-shadow:0 1px 2px rgba(0,0,0,.04);}
  .meta{display:grid;grid-template-columns:repeat(2,1fr);gap:10px 24px;}
  .meta b{color:var(--muted);font-weight:normal;margin-right:8px;}
  table{width:100%;border-collapse:collapse;font-size:14px;}
  th{background:var(--purple-soft);color:var(--ink-strong);text-align:left;
    padding:10px 12px;border:1px solid var(--line);}
  td{padding:10px 12px;border:1px solid var(--line);vertical-align:top;}
  tr:nth-child(even) td{background:#FCFBF8;}
  .tag{display:inline-block;font-size:12px;padding:1px 8px;border-radius:4px;
    background:var(--purple-soft);color:var(--purple);}
  .tag.danger{background:#F7ECEC;color:var(--danger);}
  ul.check{list-style:none;padding:0;margin:0;}
  ul.check li{padding:8px 0;border-bottom:1px solid var(--line);}
  .box{color:var(--purple);font-weight:bold;margin-right:8px;}
  .clause{color:var(--muted);font-size:13px;}
  .foot{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);
    color:var(--muted);font-size:13px;}
  @media print{
    body{background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact;}
    .card{box-shadow:none;break-inside:avoid;}
    h2{break-after:avoid;}
  }
</style>
</head>
<body>
<div class="wrap">

  <h1>《示例规定》法律视角解读</h1>
  <p class="sub">发文机关 · 文号 · 生效日期</p>

  <h2>概览</h2>
  <div class="card meta">
    <div><b>名称</b>《示例规定》</div>
    <div><b>文号</b>××〔2026〕×号</div>
    <div><b>发文机关</b>××部</div>
    <div><b>生效日期</b>2026-××-××</div>
    <div style="grid-column:1/-1"><b>适用范围</b>……(锚原文条款)</div>
  </div>

  <h2>核心义务矩阵</h2>
  <div class="card">
    <table>
      <thead><tr><th>义务事项</th><th>义务主体</th><th>履行要求 / 期限</th><th>对应条款</th><th>不履行后果</th></tr></thead>
      <tbody>
        <tr>
          <td><span class="tag">义务</span> 示例义务</td>
          <td>经营者</td>
          <td>自生效之日起 30 日内完成</td>
          <td class="clause">第 X 条</td>
          <td><span class="tag danger">罚则</span> 责令改正、罚款</td>
        </tr>
      </tbody>
    </table>
  </div>

  <h2>合规清单</h2>
  <div class="card">
    <ul class="check">
      <li><span class="box">☐</span>完成示例合规动作。<span class="clause">第 X 条</span></li>
      <li><span class="box">☐</span>建立示例台账并留存。<span class="clause">第 Y 条</span></li>
    </ul>
  </div>

  <h2>关键时间线</h2>
  <div class="card">
    <svg viewBox="0 0 800 120" width="100%" role="img" aria-label="生效与过渡期时间线">
      <line x1="40" y1="60" x2="760" y2="60" stroke="#E6E1DA" stroke-width="2"/>
      <circle cx="160" cy="60" r="7" fill="#6B2D8B"/>
      <circle cx="500" cy="60" r="7" fill="#6B2D8B"/>
      <text x="160" y="40" text-anchor="middle" font-size="13" fill="#1F2328">2026-××-××</text>
      <text x="160" y="88" text-anchor="middle" font-size="12" fill="#6B6B6B">正式生效</text>
      <text x="500" y="40" text-anchor="middle" font-size="13" fill="#1F2328">2026-××-××</text>
      <text x="500" y="88" text-anchor="middle" font-size="12" fill="#6B6B6B">过渡期截止</text>
    </svg>
  </div>

  <div class="foot">
    本页基于文件《示例规定》整理,为法律视角解读,仅供内部参考,不构成正式法律意见。<br>
    具体适用请以正式发布原文及主管部门口径为准。
  </div>

</div>
</body>
</html>
```

骨架使用提示:

- 配色、字体栈、卡片与打印规则可整体沿用;律所可在保留章节结构与自包含约束的前提下,调整品牌色档位或新增可视化模块。
- 条款对比卡片可在上述基础上加一个两栏 `grid`(`grid-template-columns:1fr 1fr`),左旧右新,差异处加淡色底纹;仅在有对比文件时使用。
- 所有数字、期限、罚则、条款号必须锚定原文(见 SKILL.md 反幻觉约束);拿不准处标注"原文未明确",不要在可视化里凭样式"补齐"不存在的信息。
