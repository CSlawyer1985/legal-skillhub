# HTML 框架参考

Legal Test Builder（法律测试生成器）HTML 输出的完整实现指南。在为法律测试工件编写任何 HTML 之前，先阅读本文件。

---

## 设计系统

### 设计理念

深色、近似单色系调色板，配单一强调色。衬线展示字体用于题目文本（传达庄重感和法律感）。所有元数据、标签、计时器和代码使用等宽字体。正文散文使用无衬线字体。整体美感应像严肃的专业工具，而非消费类应用。

### CSS 变量。粘贴到每个测试中

```css
:root {
  --bg: #08090d;
  --surface: #111218;
  --surface2: #181920;
  --border: #24252e;
  --border2: #2e3040;
  --text: #e8e9f0;
  --text-muted: #6b6d80;
  --text-dim: #44465a;
  --accent: #c8b4ff;       /* 主要高亮。紫色 */
  --accent2: #7b6fbf;      /* 淡化强调色 */
  --red: #ff6b6b;          /* 关键问题 */
  --red-dim: #3d1a1a;
  --amber: #ffb347;        /* 高严重度问题 / 警告 */
  --amber-dim: #3d2a0a;
  --green: #5ddfb0;        /* 参考答案 / 修正 */
  --green-dim: #0d2e23;
  --blue: #60a5fa;         /* 中严重度问题 / 信息 */
  --blue-dim: #0d1f3d;
  --mono: 'DM Mono', monospace;
  --serif: 'Fraunces', serif;
  --sans: 'DM Sans', sans-serif;
}
```

### Google Fonts 引入（始终包含）

```html
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Fraunces:ital,opsz,wght@0,9.144,300;0,9.144,400;0,9.144,600;1,9.144,300&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
```

---

## 组件

### 1. 带计时器的粘性页头

```html
<header class="header">
  <div class="header-left">
    <div class="header-label">组织 · 角色</div>
    <div class="header-title">测试标题</div>
  </div>
  <nav class="section-nav">
    <a href="#s1" class="nav-pill">§1 合同</a>
    <a href="#s2" class="nav-pill">§2 备忘录</a>
    <!-- 按需添加 -->
  </nav>
  <div class="timer-block">
    <div>
      <div class="header-label" style="text-align:center;margin-bottom:2px;">剩余时间</div>
      <div class="timer-display" id="timer">3:00:00</div>
      <div class="progress-bar"><div class="progress-fill" id="timer-bar" style="width:100%"></div></div>
    </div>
    <div class="timer-controls">
      <button class="btn primary" id="start-btn" onclick="startTimer()">开始</button>
      <button class="btn" onclick="resetTimer()">重置</button>
    </div>
  </div>
</header>
```

**计时器 CSS：**
```css
.header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(8,9,13,0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 12px 32px;
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
}
.timer-display {
  font-family: var(--mono); font-size: 28px; color: var(--accent);
  letter-spacing: 0.05em; min-width: 120px; text-align: center;
  transition: color 0.3s;
}
.timer-display.warn { color: var(--amber); }
.timer-display.danger { color: var(--red); animation: pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
.progress-bar { height: 2px; background: var(--border); border-radius: 1px; margin-top: 8px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent2), var(--accent)); transition: width 1s linear; }
```

**计时器 JS（放在 body 底部的 `<script>` 中）：**
```js
const TOTAL = 3 * 60 * 60; // 调整为测试时长（秒）
let remaining = TOTAL;
let interval = null;
let running = false;

function startTimer() {
  if (running) {
    clearInterval(interval); running = false;
    document.getElementById('start-btn').textContent = 'Resume'; return;
  }
  running = true;
  document.getElementById('start-btn').textContent = 'Pause';
  interval = setInterval(() => {
    if (remaining <= 0) { clearInterval(interval); return; }
    remaining--;
    const h = Math.floor(remaining/3600);
    const m = Math.floor((remaining%3600)/60);
    const s = remaining%60;
    const el = document.getElementById('timer');
    el.textContent = `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    el.className = 'timer-display';
    if (remaining < 1800) el.classList.add('warn');
    if (remaining < 600) { el.classList.remove('warn'); el.classList.add('danger'); }
    document.getElementById('timer-bar').style.width = (remaining/TOTAL*100)+'%';
  }, 1000);
}
function resetTimer() {
  clearInterval(interval); running = false; remaining = TOTAL;
  document.getElementById('start-btn').textContent = 'Start';
  document.getElementById('timer').textContent = '3:00:00'; // 与 TOTAL 一致
  document.getElementById('timer-bar').style.width = '100%';
}
```

---

### 2. 带注释问题的合同正文

问题用 `<span class="problem">` 标记，并带 `data-title` / `data-body` 属性。悬停时通过 JS 渲染浮动提示框。问题注释**在悬停前不可见**：条款读起来像正常合同文本——这正是本设计的用意。

```html
<!-- 合同包装 -->
<div class="contract-wrapper">
  <div class="contract-toolbar">
    <div class="toolbar-label">草稿。协议名称 v1（当事方批注）。日期</div>
    <span style="font-family:var(--mono);font-size:9px;color:var(--red);">● N 个内嵌问题</span>
  </div>
  <div class="contract-body">

    <span class="cl">
      <span class="cl-title">1. 条款标题</span>
      此处为正常合同文本。 <span class="problem" 
        data-id="P1" 
        data-title="问题简短标题" 
        data-body="完整说明为什么这是问题以及其在商业上的含义。要具体。说明商业后果，而不仅是法律缺陷。">有问题的措辞放在这里，并在条款内自然通读。</span> 更多正常文本。
    </span>

  </div>
</div>

<!-- 提示框元素。放置一次，靠近 body 顶部 -->
<div id="tooltip">
  <div id="tooltip-title"></div>
  <div id="tooltip-body"></div>
</div>
```

**合同正文的 CSS：**
```css
.contract-wrapper { border: 1px solid var(--border2); border-radius: 8px; overflow: hidden; margin-bottom: 24px; }
.contract-toolbar { padding: 10px 16px; background: var(--surface2); border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 12px; }
.toolbar-label { font-family: var(--mono); font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-dim); flex: 1; }
.contract-body { padding: 32px; background: var(--surface); font-family: var(--mono); font-size: 12.5px; line-height: 1.9; color: #c8cad8; }
.cl { display: block; margin-bottom: 20px; }
.cl-title { font-weight: 500; color: var(--text); display: block; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
.problem { background: rgba(255,107,107,0.12); border-bottom: 1.5px solid var(--red); cursor: pointer; transition: background 0.15s; }
.problem:hover { background: rgba(255,107,107,0.22); }
#tooltip { position: fixed; z-index: 999; display: none; background: #1a0d0d; border: 1px solid var(--red); border-radius: 6px; padding: 10px 14px; font-family: var(--sans); font-size: 12px; color: var(--text); max-width: 320px; pointer-events: none; box-shadow: 0 8px 32px rgba(0,0,0,0.5); line-height: 1.5; }
#tooltip-title { font-family: var(--mono); font-size: 9px; letter-spacing: 0.1em; color: var(--red); margin-bottom: 5px; text-transform: uppercase; }
```

**提示框 JS：**
```js
const tooltip = document.getElementById('tooltip');
document.querySelectorAll('.problem').forEach(el => {
  el.addEventListener('mouseenter', (e) => {
    document.getElementById('tooltip-title').textContent = el.dataset.title || '';
    document.getElementById('tooltip-body').textContent = el.dataset.body || '';
    tooltip.style.display = 'block';
    posTooltip(e);
  });
  el.addEventListener('mousemove', posTooltip);
  el.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
});
function posTooltip(e) {
  const x = e.clientX + 16, y = e.clientY + 16;
  const tw = tooltip.offsetWidth || 320, th = tooltip.offsetHeight || 100;
  tooltip.style.left = Math.min(x, window.innerWidth-tw-20)+'px';
  tooltip.style.top = Math.min(y, window.innerHeight-th-20)+'px';
}
```

---

### 3. 问题行（合同下方）

每个问题一行。包含：ID 徽章、严重度徽章、标题、作答文本区、答案揭示块。

```html
<div class="problem-row">
  <div class="problem-row-header">
    <div class="problem-id">P1</div>
    <div class="problem-severity sev-critical">关键（CRITICAL）</div>  <!-- sev-critical | sev-high | sev-medium -->
    <div class="problem-title">条款问题的简短描述</div>
  </div>
  <div class="problem-detail">一句话说明考生应处理什么。</div>
  <textarea class="write-area" placeholder="你的分析 + 拟议红线修改措辞.."></textarea>
  
  <!-- 答案揭示块放在这里。见组件 4 -->
</div>
```

**CSS：**
```css
.problem-row { padding: 16px; border: 1px solid var(--border); border-radius: 6px; margin-bottom: 10px; background: var(--surface); transition: all 0.15s; }
.problem-row:hover { border-color: var(--red); }
.problem-row-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.problem-id { font-family: var(--mono); font-size: 9px; letter-spacing: 0.1em; color: var(--red); padding: 2px 8px; border: 1px solid var(--red); border-radius: 3px; }
.problem-severity { font-family: var(--mono); font-size: 9px; letter-spacing: 0.08em; padding: 2px 8px; border-radius: 3px; }
.sev-critical { background: var(--red-dim); color: var(--red); border: 1px solid var(--red); }
.sev-high { background: var(--amber-dim); color: var(--amber); border: 1px solid var(--amber); }
.sev-medium { background: var(--blue-dim); color: var(--blue); border: 1px solid var(--blue); }
.problem-title { font-size: 13px; font-weight: 500; color: var(--text); flex: 1; }
.problem-detail { font-size: 12px; color: var(--text-muted); line-height: 1.65; margin-bottom: 10px; }
.write-area { width: 100%; min-height: 160px; background: var(--surface2); border: 1px solid var(--border2); border-radius: 6px; padding: 14px; color: var(--text); font-family: var(--mono); font-size: 12px; line-height: 1.8; resize: vertical; outline: none; transition: border-color 0.15s; }
.write-area:focus { border-color: var(--accent2); }
.write-area::placeholder { color: var(--text-dim); }
```

---

### 4. 答案揭示块（隐藏的参考答案）

```html
<div class="reveal-block">
  <div class="reveal-header" onclick="toggle(this)">
    <span class="reveal-header-label model">▸ 参考答案。P1</span>
    <!-- 标签类选项：model（绿色）| analysis（紫色）| strategy（琥珀色） -->
    <span class="reveal-chevron">▼</span>
  </div>
  <div class="reveal-body">
    <div class="answer-content">
      <h4>章节标题</h4>
      <p>正文..</p>
      
      <!-- 红线替换文本 -->
      <p style="font-family:var(--mono);font-size:11px;color:var(--green);background:var(--green-dim);padding:12px;border-radius:4px;line-height:1.8;">
        <span style="text-decoration:line-through;color:var(--red);">此处为原文中的问题文本。</span>
        [插入] 此处为替换文本。
      </p>
      
      <!-- 钩子引语 -->
      <div class="hook-box">一句令人难忘的话，概括战略要点。</div>
      
      <!-- 陷阱警告 -->
      <div class="trap-box">直觉性但错误的回应是什么，以及它为什么失败。</div>
      
      <!-- 知识缺口 -->
      <div class="gap-box">法律真正不确定之处。对此要诚实。</div>
    </div>
  </div>
</div>
```

**CSS：**
```css
.reveal-block { margin-top: 12px; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.reveal-header { padding: 14px 20px; background: var(--surface2); cursor: pointer; display: flex; align-items: center; justify-content: space-between; transition: background 0.15s; user-select: none; }
.reveal-header:hover { background: var(--surface); }
.reveal-header-label { font-family: var(--mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; }
.reveal-header-label.model { color: var(--green); }
.reveal-header-label.analysis { color: var(--accent); }
.reveal-header-label.strategy { color: var(--amber); }
.reveal-chevron { font-family: var(--mono); font-size: 10px; color: var(--text-dim); transition: transform 0.2s; }
.reveal-header.open .reveal-chevron { transform: rotate(180deg); }
.reveal-body { display: none; padding: 24px; background: var(--surface); border-top: 1px solid var(--border); }
.reveal-body.open { display: block; }
.answer-content h4 { font-family: var(--mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); margin: 20px 0 8px; }
.answer-content h4:first-child { margin-top: 0; }
.answer-content p { font-size: 13px; color: var(--text-muted); margin-bottom: 12px; line-height: 1.75; }
.answer-content ul { list-style: none; margin-bottom: 16px; }
.answer-content ul li { font-size: 13px; color: var(--text-muted); padding: 6px 0 6px 20px; position: relative; border-bottom: 1px solid var(--border); line-height: 1.6; }
.answer-content ul li::before { content: '—'; position: absolute; left: 0; color: var(--text-dim); font-family: var(--mono); }
.hook-box { padding: 14px 18px; background: var(--green-dim); border-left: 3px solid var(--green); border-radius: 0 6px 6px 0; font-size: 13px; color: var(--green); font-style: italic; margin: 16px 0; }
.trap-box { padding: 14px 18px; background: var(--red-dim); border-left: 3px solid var(--red); border-radius: 0 6px 6px 0; font-size: 12px; color: var(--red); margin: 12px 0; }
.trap-box::before { content: '⚠ TRAP: '; font-family: var(--mono); font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 4px; opacity: 0.7; }
.gap-box { padding: 12px 16px; background: var(--amber-dim); border-left: 3px solid var(--amber); border-radius: 0 6px 6px 0; font-size: 12px; color: var(--amber); margin: 12px 0; }
.gap-box::before { content: '⚡ GAP: '; font-family: var(--mono); font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; display: block; margin-bottom: 4px; opacity: 0.7; }
```

**揭示 JS：**
```js
function toggle(el) {
  el.classList.toggle('open');
  const body = el.nextElementSibling;
  if (body) body.classList.toggle('open');
}
```

---

### 5. 章节结构

```html
<section class="section" id="s1">
  <div class="section-header">
    <div class="section-num">任务 01</div>
    <div class="section-meta">
      <h2 class="section-title">任务标题</h2>
      <div class="section-sub">副标题 / 文档名称</div>
    </div>
    <div class="section-time-badge">⏱ 目标：65 分钟</div>
  </div>
  <!-- 任务内容放在这里 -->
</section>
```

```css
.section { margin-bottom: 80px; scroll-margin-top: 80px; }
.section-header { display: flex; align-items: flex-start; gap: 20px; margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
.section-num { font-family: var(--mono); font-size: 11px; letter-spacing: 0.1em; color: var(--accent2); padding: 4px 10px; border: 1px solid var(--accent2); border-radius: 3px; white-space: nowrap; margin-top: 4px; }
.section-title { font-family: var(--serif); font-size: 22px; font-weight: 300; color: var(--text); margin-bottom: 4px; }
.section-sub { font-family: var(--mono); font-size: 10px; letter-spacing: 0.1em; color: var(--text-dim); }
.section-time-badge { font-family: var(--mono); font-size: 10px; padding: 4px 12px; border-radius: 20px; background: var(--surface2); border: 1px solid var(--border2); color: var(--text-muted); white-space: nowrap; }
```

---

### 6. 题目卡片

用于情景 / 备忘录题目。

```html
<div class="q-card">
  <div class="q-eyebrow">情景标签</div>
  <div class="q-text">"情景题目文本放在这里，用斜体。"</div>
  <div class="q-context">
    <strong>指示 / 限制条件：</strong> 考生需要的额外事实。
  </div>
  <textarea class="write-area" style="min-height:200px;" placeholder="你的分析.."></textarea>
  <!-- 答案揭示块放在这里 -->
</div>
```

```css
.q-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 24px; margin-bottom: 24px; }
.q-eyebrow { font-family: var(--mono); font-size: 9px; letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 10px; }
.q-text { font-family: var(--serif); font-size: 16px; font-weight: 300; color: var(--text); margin-bottom: 16px; line-height: 1.5; font-style: italic; }
.q-context { font-size: 13px; color: var(--text-muted); padding: 12px 16px; background: var(--surface2); border-radius: 6px; margin-bottom: 16px; border-left: 3px solid var(--border2); }
```

---

### 7. 检查清单

```html
<div onclick="toggleCheck(this)" class="checklist-item">
  <div class="check-box"><span class="check-mark">✓</span></div>
  <div class="checklist-text">描述考生应已完成事项的条目文本。</div>
</div>
```

```css
.checklist-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--border); cursor: pointer; }
.check-box { width: 16px; height: 16px; border: 1px solid var(--border2); border-radius: 3px; flex-shrink: 0; margin-top: 1px; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
.checklist-item.done .check-box { background: var(--green); border-color: var(--green); }
.check-mark { font-size: 9px; color: #000; display: none; }
.checklist-item.done .check-mark { display: block; }
.checklist-item.done .checklist-text { text-decoration: line-through; color: var(--text-dim); }
.checklist-text { font-size: 13px; color: var(--text-muted); line-height: 1.5; }
```

```js
function toggleCheck(item) { item.classList.toggle('done'); }
```

---

## 完整 HTML 脚手架

以此作为起点。填充内容并按需调整。

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[组织] : [角色] 模拟测试</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Fraunces:ital,opsz,wght@0,9.144,300;0,9.144,400;0,9.144,600;1,9.144,300&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
/* === 在此粘贴完整 CSS === */
/* 包含：CSS 变量、* 重置、body、header、timer、nav、main、intro、section、contract、problem、reveal、q-card、checklist */
</style>
</head>
<body>

<div id="tooltip"><div id="tooltip-title"></div><div id="tooltip-body"></div></div>

<header class="header">
  <!-- 计时器页头放在这里 -->
</header>

<main class="main">

  <!-- 引言块 -->
  
  <section class="section" id="s1">
    <!-- 任务 01：合同红线批注 -->
  </section>

  <hr class="divider">

  <section class="section" id="s2">
    <!-- 任务 02：法律备忘录 -->
  </section>

  <hr class="divider">

  <section class="section" id="s3">
    <!-- 任务 03：简短分析 -->
  </section>

  <hr class="divider">

  <section class="section" id="s4">
    <!-- 任务 04：策略 -->
  </section>

  <hr class="divider">

  <section class="section" id="s5">
    <!-- 检查清单 -->
  </section>

</main>

<script>
// 计时器函数：startTimer()、resetTimer()
// 揭示：toggle()
// 提示框：posTooltip() + 事件监听器
// 检查清单：toggleCheck()
// 导航标签的平滑滚动
</script>
</body>
</html>
```
