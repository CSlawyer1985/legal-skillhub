/* Legal SkillHub 详情页：10 段信息架构 + 文件树浏览器 + 安装命令 */
(function () {
  const $ = s => document.querySelector(s);
  document.getElementById("header").innerHTML = renderHeader("home");
  document.getElementById("footer").innerHTML = renderFooter();

  const params = new URLSearchParams(location.search);
  const id = params.get("f");
  const RISK_LBL = { open: ["宽松许可", "lic-open"], copyleft: ["传染性许可", "lic-copyleft"], "restrictive-nc": ["非商业限制", "lic-restrictive-nc"], undeclared: ["未声明授权", "lic-undeclared"] };

  let DATA = null, FILES = null, rec = null, files = [];

  async function load() {
    if (!id) { $("#detail").innerHTML = "<p>缺少参数 ?f=<skill-id></p>"; return; }
    DATA = await fetch("data/skills.json").then(r => r.json());
    rec = DATA.find(d => d.id === id);
    if (!rec) { $("#detail").innerHTML = `<p>未找到技能：${escHtml(id)}</p>`; return; }
    FILES = await fetch("data/files.json").then(r => r.json());
    files = FILES[id] || [];
    document.title = `${rec.name} · Legal SkillHub`;
    render();
    openFile(defaultFile());
  }

  function defaultFile() {
    return files.find(f => /skill\.md$/i.test(f)) || files[0];
  }

  /* ═══ 页面骨架 ═══ */
  function render() {
    const d = rec;
    const [riskLbl, riskCls] = RISK_LBL[d.lrisk] || RISK_LBL.undeclared;
    const badges = [];
    (d.jur || []).forEach(j => badges.push(`<span class="badge jur">${lbl("jur", j)}</span>`));
    (d.dom || []).slice(0, 2).forEach(x => badges.push(`<span class="badge dom">${lbl("dom", x)}</span>`));
    (d.task || []).slice(0, 2).forEach(x => badges.push(`<span class="badge task">${lbl("task", x)}</span>`));
    badges.push(`<span class="badge">${d.lang === "zh-CN" ? "中文" : "EN"}</span>`);
    badges.push(`<span class="badge verif">${lbl("verif", d.verif)}</span>`);
    badges.push(`<span class="badge ${riskCls}">${riskLbl} · ${lbl("lic", d.lic)}</span>`);
    if (d.fresh) badges.push(`<span class="badge verif">含新法</span>`);
    if (d.cur) badges.push(`<span class="badge verif">★精选</span>`);

    $("#detail").innerHTML = `
      <a class="back-link" href="./index.html">← 返回技能库</a>
      <div class="detail-head">
        <h1>${escHtml(d.name)}</h1>
        <p class="detail-summary">${escHtml(d.summary || "（暂无简介）")}</p>
        <div class="badge-row">${badges.join("")}</div>
      </div>

      <section class="section" id="sec-what">
        <h2>它能完成什么</h2>
        <dl class="kv-grid">
          <dt>工作任务</dt><dd>${(d.task || []).map(x => lbl("task", x)).join(" / ") || "—"}</dd>
          <dt>输入</dt><dd>${(d.in || []).map(x => lbl("in", x)).join("、") || "—"}</dd>
          <dt>输出</dt><dd>${(d.out || []).map(x => lbl("out", x)).join("、") || "—"}</dd>
          <dt>适用角色</dt><dd>${(d.roles || []).map(x => lbl("role", x)).join("、") || "—"}</dd>
          <dt>行业</dt><dd>${(d.ind || []).map(x => lbl("ind", x)).join("、") || "—"}</dd>
        </dl>
      </section>

      <section class="section" id="sec-how">
        <h2>它如何工作</h2>
        ${d.logic ? `<p style="font-size:.9rem;line-height:1.8">${escHtml(d.logic)}</p>` : `<p style="color:var(--text-dim)">工作逻辑整理中。可直接查看下方 SKILL.md 原文了解完整工作流程。</p>`}
        <dl class="kv-grid" style="margin-top:12px">
          <dt>技能类型</dt><dd>${lbl("type", d.type)}</dd>
          <dt>自动化等级</dt><dd>${d.auto ? lbl("auto", d.auto) : "—"}</dd>
          <dt>复杂度</dt><dd>${d.cplx}（${d.files} 个文件）</dd>
        </dl>
      </section>

      <section class="section" id="sec-jur">
        <h2>法域与适用</h2>
        <dl class="kv-grid">
          <dt>适用法域</dt><dd>${(d.jur || []).map(x => lbl("jur", x)).join("、")}</dd>
          <dt>法律领域</dt><dd>${(d.dom || []).map(x => lbl("dom", x)).join("、")}</dd>
        </dl>
        <p style="color:var(--text-dim);font-size:.8rem;margin-top:10px">// 法域标签由内容信号自动判定，使用前请核实与你的案件/业务所在法域是否匹配。</p>
      </section>

      <section class="section" id="sec-files">
        <h2>技能包文件（${files.length}）</h2>
        <div class="file-browser">
          <div class="file-tree" id="file-tree"></div>
          <div class="file-content" id="file-content">
            <div class="loading">选择左侧文件查看内容</div>
          </div>
        </div>
      </section>

      <section class="section" id="sec-install">
        <h2>安装与部署</h2>
        <div class="mirror-toggle">下载源：<a id="m-raw">GitHub Raw</a> · <a id="m-js">jsDelivr 镜像（国内推荐）</a></div>
        <div id="cmd-area"></div>
        <dl class="kv-grid" style="margin-top:14px">
          <dt>依赖条件</dt><dd>${d.deps && d.deps.length ? d.deps.map(escHtml).join("；") : "无特殊依赖（纯 Markdown Skill）"}</dd>
          <dt>数据权限</dt><dd>${(d.has.scripts ? "含脚本，可能涉及文件读写/网络访问，安装前请审阅 scripts/" : "无脚本，不执行代码")}</dd>
        </dl>
      </section>

      <section class="section" id="sec-risk">
        <h2>风险与限制</h2>
        <dl class="kv-grid">
          <dt>风险等级</dt><dd>${d.risk ? lbl("risk", d.risk) : "待评估"}</dd>
          <dt>人工复核</dt><dd>法律类 Skill 输出均需人工复核后方可用于正式用途</dd>
          <dt>授权</dt><dd>${riskLbl}（${lbl("lic", d.lic)}）</dd>
        </dl>
        ${d.lrisk === "undeclared" ? `<p style="color:var(--red);font-size:.82rem;margin-top:10px">⚠ 该 Skill 原作者未声明授权条款。本站已标注来源；商业使用前请自行评估或联系原作者。权利人可通过<a href="./about.html#takedown">下架通道</a>联系我们。</p>` : ""}
        ${d.lrisk === "restrictive-nc" ? `<p style="color:var(--orange);font-size:.82rem;margin-top:10px">⚠ 该 Skill 采用非商业限制许可（${lbl("lic", d.lic)}），禁止商业用途。</p>` : ""}
      </section>

      <section class="section" id="sec-src">
        <h2>来源与许可</h2>
        <dl class="kv-grid">
          <dt>来源平台</dt><dd>${lbl("src", d.src)}</dd>
          <dt>验证状态</dt><dd>${lbl("verif", d.verif)}</dd>
        </dl>
      </section>

      <section class="section" id="sec-rel" style="border-bottom:none">
        <h2>相关 Skill</h2>
        <div class="rel-grid" id="rel-grid"></div>
      </section>
    `;
    renderTree();
    renderCmds();
    renderRelated();
    bindCopy(document);
    bindMirror();
  }

  /* ═══ 文件树 ═══ */
  function renderTree() {
    const tree = {};
    files.forEach(f => {
      const parts = f.split("/");
      let node = tree;
      parts.forEach((p, i) => {
        if (i === parts.length - 1) (node.__files = node.__files || []).push(f);
        else node = node[p] = node[p] || {};
      });
    });
    let html = `<div class="file-tree-header">WHAT'S INCLUDED · ${files.length} FILES</div>`;
    function walk(node, prefix, depth) {
      const dirs = Object.keys(node).filter(k => k !== "__files").sort();
      dirs.forEach(d => {
        html += `<div class="tree-item dir" style="padding-left:${14 + depth * 14}px">▸ ${d}/</div>`;
        walk(node[d], prefix + d + "/", depth + 1);
      });
      (node.__files || []).sort().forEach(f => {
        const base = f.split("/").pop();
        html += `<div class="tree-item" data-file="${escHtml(f)}" style="padding-left:${14 + depth * 14}px"><span>${escHtml(base)}</span></div>`;
      });
    }
    walk(tree, "", 0);
    $("#file-tree").innerHTML = html;
    $("#file-tree").querySelectorAll(".tree-item[data-file]").forEach(el =>
      el.addEventListener("click", () => {
        $("#file-tree").querySelectorAll(".tree-item").forEach(x => x.classList.remove("active"));
        el.classList.add("active");
        openFile(el.dataset.file);
      }));
  }

  async function openFile(path) {
    if (!path) return;
    const box = $("#file-content");
    box.innerHTML = `<div class="path-bar">${escHtml(rec.id)}/${escHtml(path)}</div><div class="loading">加载中…</div>`;
    try {
      const text = await fetchSkillFile(`skills/${rec.id}/${path}`);
      const ext = path.split(".").pop().toLowerCase();
      let body;
      if (ext === "md" || ext === "markdown") {
        body = `<div class="md">${renderMd(text)}</div>`;
      } else {
        body = `<pre>${escHtml(text)}</pre>`;
      }
      box.innerHTML = `<div class="path-bar">${escHtml(rec.id)}/${escHtml(path)}</div>` + body;
    } catch (e) {
      box.innerHTML = `<div class="path-bar">${escHtml(rec.id)}/${escHtml(path)}</div>
        <div class="error">文件加载失败：${escHtml(e.message)}<br><br>
        <a href="https://github.com/${(await siteConfig()).owner}/${(await siteConfig()).repo}/blob/main/skills/${rec.id}/${path}" target="_blank" rel="noopener">在 GitHub 上查看 →</a></div>`;
    }
  }

  /* ═══ 安装命令 ═══ */
  function cmdBlock(title, cmd) {
    return `<div class="cmd-block">
      <div class="cmd-head"><span>${title}</span><button class="copy-btn">复制</button></div>
      <pre>${escHtml(cmd)}</pre>
    </div>`;
  }
  async function buildCurlCmd() {
    const c = await siteConfig();
    const base = MIRRORS[getMirror()](c, `skills/${rec.id}`);
    const lines = [`mkdir -p ~/.claude/skills/${rec.id} && cd ~/.claude/skills/${rec.id} \\`];
    files.forEach((f, i) => {
      const dir = f.includes("/") ? ` --create-dirs` : "";
      const last = i === files.length - 1 ? "" : " \\";
      lines.push(`  && curl -fsSL${dir} -o "${f}" "${base}/${f}"${last}`);
    });
    return lines.join("\n");
  }
  async function buildGitCmd() {
    const c = await siteConfig();
    return `git clone --depth 1 --filter=blob:none --sparse https://github.com/${c.owner}/${c.repo}.git\ncd ${c.repo}\ngit sparse-checkout set skills/${rec.id}\ncp -r skills/${rec.id} ~/.claude/skills/`;
  }
  function buildPromptCmd() {
    return `请从 GitHub 仓库下载并安装一个 Skill 到我的工作环境：\n1. 逐个读取 https://github.com/${"${owner}/${repo}"}/tree/main/skills/${rec.id} 下的全部文件（共 ${files.length} 个）\n2. 按相同目录结构保存到 ~/.claude/skills/${rec.id}/\n3. 完成后告诉我这个 Skill 的触发方式`;
  }
  async function renderCmds() {
    const [curlCmd, gitCmd] = await Promise.all([buildCurlCmd(), buildGitCmd()]);
    $("#cmd-area").innerHTML =
      cmdBlock("方式一：curl 逐文件下载（推荐）", curlCmd) +
      cmdBlock("方式二：git sparse-checkout（适合批量）", gitCmd) +
      cmdBlock("方式三：让 AI 助手帮你安装（复制给它）", buildPromptCmd().replace("${owner}/${repo}", (await siteConfig()).owner + "/" + (await siteConfig()).repo));
    bindCopy($("#cmd-area"));
  }
  function bindMirror() {
    const upd = () => {
      $("#m-raw").style.color = getMirror() === "raw" ? "var(--accent)" : "";
      $("#m-js").style.color = getMirror() === "jsdelivr" ? "var(--accent)" : "";
    };
    $("#m-raw").addEventListener("click", () => { setMirror("raw"); upd(); renderCmds(); });
    $("#m-js").addEventListener("click", () => { setMirror("jsdelivr"); upd(); renderCmds(); });
    upd();
  }

  /* ═══ 相关推荐 ═══ */
  function renderRelated() {
    const rel = [];
    const sameTaskDiffJur = DATA.filter(d => d.id !== rec.id && d.task && rec.task && d.task[0] === rec.task[0] && !(d.jur || []).some(j => (rec.jur || []).includes(j)));
    const sameJurDom = DATA.filter(d => d.id !== rec.id && d.dom && rec.dom && d.dom[0] === rec.dom[0] && (d.jur || []).some(j => (rec.jur || []).includes(j)));
    rel.push(...sameTaskDiffJur.slice(0, 3), ...sameJurDom.slice(0, 3));
    const seen = new Set();
    const uniq = rel.filter(d => !seen.has(d.id) && seen.add(d.id)).slice(0, 6);
    $("#rel-grid").innerHTML = uniq.map(d => `
      <a class="rel-card" href="./skill.html?f=${encodeURIComponent(d.id)}">
        <div class="rel-title">${escHtml(d.name)}</div>
        <div class="rel-desc">${escHtml(d.summary || "")}</div>
        <div style="margin-top:6px">${(d.jur || []).slice(0, 2).map(j => `<span class="tag jur">${lbl("jur", j)}</span>`).join("")}</div>
      </a>`).join("") || `<span style="color:var(--text-dim)">暂无相关推荐</span>`;
  }

  load().catch(e => { $("#detail").innerHTML = `<p>加载失败：${escHtml(e.message)}</p>`; });
})();
