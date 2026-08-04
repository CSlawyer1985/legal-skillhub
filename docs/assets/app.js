/* Legal SkillHub 首页 — 参照 terminalskills.io 的列表式 + 顶部分类 pill 架构 */
(function () {
  const $ = s => document.querySelector(s);
  document.getElementById("header").innerHTML = renderHeader("home");
  document.getElementById("footer").innerHTML = renderFooter();

  /* 维度定义：顶部分类 pill 按维度切换 */
  const DIMS = [
    { key: "jur", label: "法域", field: "jur", single: true },
    { key: "dom", label: "领域", field: "dom" },
    { key: "task", label: "任务", field: "task" },
    { key: "roles", label: "角色", field: "roles", lbl: "role" },
  ];
  const ADV = [   // 高级筛选抽屉
    { key: "lang", label: "语言", field: "lang", single: true },
    { key: "lic", label: "授权", field: "lrisk", single: true },
    { key: "verif", label: "验证", field: "verif", single: true },
    { key: "type", label: "类型", field: "type", single: true },
    { key: "auto", label: "自动化", field: "auto", single: true },
    { key: "in", label: "输入", field: "in" },
    { key: "out", label: "输出", field: "out" },
    { key: "ind", label: "行业", field: "ind" },
    { key: "cplx", label: "复杂度", field: "cplx", single: true },
  ];
  const RISK_LBL = { open: "宽松许可", copyleft: "传染性", "restrictive-nc": "非商业", undeclared: "未声明" };
  const SORTS = [
    { key: "q", label: "质量分" },
    { key: "files", label: "文件数" },
    { key: "name", label: "A-Z" },
    { key: "fresh", label: "含新法" },
    { key: "cur", label: "★精选" },
  ];

  let DATA = [];
  const state = {
    q: "", dim: "jur", pills: new Set(), adv: {}, sort: "q", page: 1, perPage: 24,
  };
  DIMS.forEach(d => {}); ADV.forEach(d => state.adv[d.key] = new Set());

  /* ── hash 同步 ── */
  function stateToHash() {
    const p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    if (state.dim !== "jur") p.set("dim", state.dim);
    if (state.pills.size) p.set("p", [...state.pills].join(","));
    Object.keys(state.adv).forEach(k => { if (state.adv[k].size) p.set("a_" + k, [...state.adv[k]].join(",")); });
    if (state.sort !== "q") p.set("sort", state.sort);
    if (state.page !== 1) p.set("pg", state.page);
    const h = p.toString();
    history.replaceState(null, "", h ? "#" + h : location.pathname);
  }
  function hashToState() {
    const p = new URLSearchParams(location.hash.slice(1));
    state.q = p.get("q") || "";
    state.dim = p.get("dim") || "jur";
    state.pills = new Set((p.get("p") || "").split(",").filter(Boolean));
    ADV.forEach(d => state.adv[d.key] = new Set((p.get("a_" + d.key) || "").split(",").filter(Boolean)));
    state.sort = p.get("sort") || "q";
    state.page = parseInt(p.get("pg")) || 1;
    document.getElementById("q").value = state.q;
  }

  async function load() {
    DATA = await fetch("data/skills.json").then(r => r.json());
    DATA.forEach(d => {
      const text = (d.id + " " + d.name + " " + (d.summary || "")).toLowerCase();
      const tokens = new Set();
      text.replace(/[a-z0-9][a-z0-9\-_.]*/g, m => { tokens.add(m); return m; });
      const cjk = text.replace(/[a-z0-9\s\-_.]/g, "");
      for (let i = 0; i < cjk.length - 1; i++) tokens.add(cjk.slice(i, i + 2));
      if (cjk.length === 1) tokens.add(cjk);
      d._tokens = tokens; d._text = text;
    });
    hashToState();
    renderHero();
    renderDimTabs();
    renderPills();
    renderSort();
    refresh();
  }

  /* ── Hero 开机动画（首次访问播一次）── */
  function renderHero() {
    if (sessionStorage.getItem("lsh-hero")) { document.getElementById("hero").style.display = "none"; return; }
    const lines = [
      "> initializing legal_skillhub...",
      "> mounting /skills ............ [████████████] 2049/2049",
      "> indexing jurisdictions ...... china·us·eu·fr·uk·intl",
      "> ready.",
    ];
    const el = document.getElementById("hero");
    let li = 0, ci = 0, buf = "";
    (function step() {
      if (li >= lines.length) {
        el.querySelector(".hero-out").innerHTML = lines.join("\n");
        setTimeout(() => { el.style.opacity = "0"; setTimeout(() => el.style.display = "none", 400); }, 700);
        sessionStorage.setItem("lsh-hero", "1");
        return;
      }
      const line = lines[li];
      if (ci <= line.length) {
        buf = lines.slice(0, li).join("\n") + (li > 0 ? "\n" : "") + line.slice(0, ci);
        el.querySelector(".hero-out").textContent = buf;
        ci += Math.max(1, Math.floor(line.length / 28));
        setTimeout(step, 18);
      } else { li++; ci = 0; setTimeout(step, 90); }
    })();
  }

  /* ── 维度 tab ── */
  function renderDimTabs() {
    $("#dim-tabs").innerHTML = DIMS.map(d =>
      `<button class="dim-tab ${state.dim === d.key ? "on" : ""}" data-dim="${d.key}">${d.label}</button>`).join("") +
      `<button class="dim-tab adv" id="adv-btn">⊞ 高级筛选${advCount() ? `(${advCount()})` : ""}</button>`;
    $("#dim-tabs").querySelectorAll(".dim-tab[data-dim]").forEach(b =>
      b.addEventListener("click", () => { state.dim = b.dataset.dim; state.pills.clear(); state.page = 1; renderDimTabs(); renderPills(); refresh(); }));
    $("#adv-btn").addEventListener("click", renderAdvanced);
  }
  function advCount() { return Object.values(state.adv).reduce((s, set) => s + set.size, 0); }

  /* ── 分类 pills（按当前维度）── */
  function facetCounts(field) {
    const c = {};
    filtered(false, true).forEach(d => {
      const v = d[field];
      (Array.isArray(v) ? v : [v]).forEach(x => { if (x) c[x] = (c[x] || 0) + 1; });
    });
    return c;
  }
  function renderPills() {
    const d = DIMS.find(x => x.key === state.dim);
    const cnt = facetCounts(d.field);
    const entries = Object.entries(cnt).sort((a, b) => b[1] - a[1]).slice(0, 16);
    const lblFn = v => d.key === "lic" ? (RISK_LBL[v] || v) : lbl(d.lbl || d.key, v);
    let html = `<button class="pill ${state.pills.size === 0 ? "on" : ""}" data-val="">全部 ${d.label}</button>`;
    html += entries.map(([v, n]) =>
      `<button class="pill ${state.pills.has(v) ? "on" : ""}" data-val="${v}">${lblFn(v)} <span class="pcnt">${n}</span></button>`).join("");
    $("#pills").innerHTML = html;
    $("#pills").querySelectorAll(".pill").forEach(b =>
      b.addEventListener("click", () => {
        const v = b.dataset.val;
        if (v === "") state.pills.clear();
        else { state.pills.clear(); state.pills.add(v); }
        state.page = 1; renderPills(); refresh();
      }));
  }

  /* ── 高级筛选抽屉 ── */
  function renderAdvanced() {
    const overlay = document.createElement("div");
    overlay.id = "adv-overlay";
    overlay.innerHTML = `<div class="adv-panel">
      <div class="adv-head"><b>高级筛选</b><button id="adv-close">✕</button></div>
      <div class="adv-body">${ADV.map(d => dimAdvHtml(d)).join("")}</div>
      <div class="adv-foot"><button id="adv-clear">清空全部</button><button id="adv-apply" class="primary">应用</button></div>
    </div>`;
    document.body.appendChild(overlay);
    overlay.querySelectorAll(".filter-opt").forEach(el =>
      el.addEventListener("click", () => {
        const { dim, val } = el.dataset; const set = state.adv[dim];
        if (set.has(val)) set.delete(val); else { if (ADV.find(x => x.key === dim).single) set.clear(); set.add(val); }
        el.classList.toggle("on");
      }));
    $("#adv-close").addEventListener("click", () => overlay.remove());
    $("#adv-clear").addEventListener("click", () => { ADV.forEach(d => state.adv[d.key].clear()); overlay.remove(); renderDimTabs(); refresh(); });
    $("#adv-apply").addEventListener("click", () => { overlay.remove(); state.page = 1; renderDimTabs(); refresh(); });
    overlay.addEventListener("click", e => { if (e.target === overlay) overlay.remove(); });
  }
  function dimAdvHtml(d) {
    const cnt = facetCounts(d.field);
    const entries = Object.entries(cnt).sort((a, b) => b[1] - a[1]).slice(0, 12);
    if (!entries.length) return "";
    const lblFn = v => d.key === "lic" ? (RISK_LBL[v] || v) : lbl(d.lbl || d.key, v);
    return `<div class="filter-group"><h4>${d.label}</h4>` +
      entries.map(([v, n]) => `<span class="filter-opt ${state.adv[d.key].has(v) ? "on" : ""}" data-dim="${d.key}" data-val="${v}">${lblFn(v)}<span class="cnt">${n}</span></span>`).join("") + `</div>`;
  }

  /* ── 排序 ── */
  function renderSort() {
    $("#sortrow").innerHTML = `<span class="sort-lbl">Sort:</span>` +
      SORTS.map(s => `<button class="sort-opt ${state.sort === s.key ? "on" : ""}" data-sort="${s.key}">${s.label}</button>`).join("");
    $("#sortrow").querySelectorAll(".sort-opt").forEach(b =>
      b.addEventListener("click", () => { state.sort = b.dataset.sort; state.page = 1; renderSort(); refresh(); }));
  }

  /* ── 过滤 ── */
  function filtered(usePills, ignoreAdv) {
    return DATA.filter(d => {
      if (state.pills.size) {
        const d0 = DIMS.find(x => x.key === state.dim);
        const v = d[d0.field]; const arr = Array.isArray(v) ? v : [v];
        if (!arr.some(x => state.pills.has(x))) return false;
      }
      if (!ignoreAdv) {
        for (const ad of ADV) {
          if (state.adv[ad.key].size) {
            const v = d[ad.field]; const arr = Array.isArray(v) ? v : [v];
            if (!arr.some(x => state.adv[ad.key].has(x))) return false;
          }
        }
      }
      if (state.q) {
        const qs = state.q.toLowerCase().trim();
        if (qs && !qs.split(/\s+/).every(w => d._text.includes(w) || [...d._tokens].some(t => t.startsWith(w)))) return false;
      }
      return true;
    });
  }
  function sorted(list) {
    const by = {
      q: (a, b) => b.q - a.q || b.files - a.files,
      files: (a, b) => b.files - a.files,
      name: (a, b) => a.id.localeCompare(b.id),
      fresh: (a, b) => (b.fresh - a.fresh) || (b.q - a.q),
      cur: (a, b) => (b.cur - a.cur) || (b.q - a.q),
    }[state.sort];
    return [...list].sort(by);
  }

  /* ── 卡片（单列列表式，参考 terminalskills）── */
  function cardHtml(d) {
    const tags = [];
    (d.jur || []).slice(0, 1).forEach(j => tags.push(`<span class="hash">#${lbl("jur", j)}</span>`));
    if (d.dom && d.dom[0]) tags.push(`<span class="hash">#${lbl("dom", d.dom[0])}</span>`);
    if (d.task && d.task[0]) tags.push(`<span class="hash">#${lbl("task", d.task[0])}</span>`);
    const [riskLbl, riskWord] = d.lrisk === "open" ? ["SAFE", "SAFE"]
      : d.lrisk === "copyleft" ? ["COPYLEFT", "COPYLEFT"]
      : d.lrisk === "restrictive-nc" ? ["NC-ONLY", "NC-ONLY"] : ["UNDECLARED", "CHECK"];
    const riskCls = d.lrisk;
    return `<a class="skill-row" href="./skill.html?f=${encodeURIComponent(d.id)}">
      <div class="row-main">
        <div class="row-title"><span class="prompt">&gt;</span> <span class="sname">${escHtml(d.name)}</span> <span class="score">${d.q * 20}</span></div>
        <div class="row-desc">${escHtml(d.summary || "（暂无简介）")}</div>
        <div class="row-meta">
          <span class="badge-st ${riskCls}">${riskWord}</span>
          <span class="impact">${d.files} files · ${d.cplx}</span>
          ${tags.join("")}
          ${d.cur ? `<span class="hash star">#精选</span>` : ""}
          ${d.fresh ? `<span class="hash">#新法</span>` : ""}
        </div>
      </div>
      <div class="row-side">
        <span class="lic-dot lic-${d.lrisk}" title="${lbl('lic',d.lic)}"></span>
        <span class="lang-tag">${d.lang === "zh-CN" ? "中" : "EN"}</span>
        <span class="view-btn">View →</span>
      </div>
    </a>`;
  }

  /* ── 渲染 ── */
  function refresh() {
    stateToHash();
    renderPills();
    const all = sorted(filtered(true, false));
    const top = all.filter(d => d.cur || d.q >= 4).slice(0, 4);
    const totalPages = Math.max(1, Math.ceil(all.length / state.perPage));
    if (state.page > totalPages) state.page = 1;
    const slice = all.slice((state.page - 1) * state.perPage, state.page * state.perPage);

    $("#count").innerHTML = `<b>${all.length}</b> skills found`;
    // Top 精选区（仅首页且无搜索/筛选时显示）
    const showTop = !state.q && !state.pills.size && advCount() === 0 && state.page === 1;
    $("#top-zone").style.display = showTop ? "block" : "none";
    if (showTop) $("#top-zone").innerHTML = `<div class="top-label">▍ 编辑精选 · TOP PERFORMING</div><div class="top-grid">${
      (DATA.filter(d => d.cur).length ? DATA.filter(d => d.cur) : DATA.slice().sort((a,b)=>b.q-a.q).slice(0,8)).slice(0,4)
      .map(d => `<a class="top-card" href="./skill.html?f=${encodeURIComponent(d.id)}">
        <div class="tc-score">${d.q * 20}</div><div class="tc-name">&gt; ${escHtml(d.name)}</div>
        <div class="tc-desc">${escHtml((d.summary||"").slice(0,70))}</div></a>`).join("")}</div>`;

    $("#list").innerHTML = slice.map(cardHtml).join("");
    renderPager(all.length, totalPages);
    renderDir();
  }

  function renderPager(total, totalPages) {
    if (totalPages <= 1) { $("#pager").innerHTML = ""; return; }
    let html = `<button class="pg" data-pg="${state.page - 1}" ${state.page === 1 ? "disabled" : ""}>← 上一页</button> `;
    html += `<span class="pg-info">Page ${state.page} of ${totalPages}</span> `;
    html += `<button class="pg" data-pg="${state.page + 1}" ${state.page === totalPages ? "disabled" : ""}>下一页 →</button>`;
    $("#pager").innerHTML = html;
    $("#pager").querySelectorAll(".pg").forEach(b =>
      b.addEventListener("click", () => { const p = +b.dataset.pg; if (p >= 1 && p <= totalPages) { state.page = p; refresh(); window.scrollTo(0, 0); } }));
  }

  /* ── 底部分类目录（按法域分栏）── */
  function renderDir() {
    const byJur = {};
    DATA.forEach(d => (d.jur || ["general"]).forEach(j => (byJur[j] = byJur[j] || []).push(d)));
    const order = ["china","us","eu","fr","uk","de","jp","kr","sg","hk","br","in","ca","au","international","multi","general"];
    const html = order.filter(j => byJur[j]).map(j => {
      const cnt = byJur[j].length;
      return `<div class="dir-col"><h4>${lbl("jur", j)} <span class="dir-cnt">${cnt}</span></h4>
        <div class="dir-links">${byJur[j].slice(0, 10).map(d => `<a href="./skill.html?f=${encodeURIComponent(d.id)}">${escHtml(d.name)}</a>`).join("")}
        ${cnt > 10 ? `<a class="dir-more" href="#dim=jur&p=${j}">+${cnt - 10} more →</a>` : ""}</div></div>`;
    }).join("");
    $("#directory").innerHTML = `<h2 class="dir-h">All ${DATA.length} Skills <span class="dir-sub">// 按法域浏览</span></h2><div class="dir-grid">${html}</div>`;
    $("#directory").querySelectorAll(".dir-more").forEach(a =>
      a.addEventListener("click", e => { e.preventDefault(); const m = a.getAttribute("href").match(/p=([^&]+)/); state.dim = "jur"; state.pills = new Set([m[1]]); state.page = 1; renderDimTabs(); refresh(); window.scrollTo(0, 300); }));
  }

  /* ── 事件 ── */
  let debounce;
  $("#q").addEventListener("input", e => { clearTimeout(debounce); debounce = setTimeout(() => { state.q = e.target.value; state.page = 1; refresh(); }, 180); });
  window.addEventListener("hashchange", () => { hashToState(); renderDimTabs(); renderSort(); refresh(); });

  load().catch(e => { document.getElementById("list").innerHTML = `<p style="color:var(--red)">数据加载失败：${escHtml(e.message)}</p>`; });
})();
