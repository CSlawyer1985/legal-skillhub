/* Legal SkillHub 首页：搜索 + 8 维筛选 + 卡片墙 + hash 同步 */
(function () {
  const $ = s => document.querySelector(s);
  document.getElementById("header").innerHTML = renderHeader("home");
  document.getElementById("footer").innerHTML = renderFooter();

  /* 筛选维度定义（首屏 8 + 高级 6） */
  const DIMS = [
    { key: "task", label: "工作任务", field: "task", primary: true },
    { key: "dom", label: "法律领域", field: "dom", primary: true },
    { key: "jur", label: "法域", field: "jur", primary: true },
    { key: "roles", label: "适用角色", field: "roles", primary: true },
    { key: "lang", label: "语言", field: "lang", primary: true, single: true },
    { key: "lic", label: "授权", field: "lrisk", primary: true, single: true },
    { key: "src", label: "来源", field: "src", primary: true, single: true },
    { key: "verif", label: "验证状态", field: "verif", primary: true, single: true },
    { key: "type", label: "技能类型", field: "type", primary: false, single: true },
    { key: "auto", label: "自动化等级", field: "auto", primary: false, single: true },
    { key: "in", label: "输入类型", field: "in", primary: false },
    { key: "out", label: "输出类型", field: "out", primary: false },
    { key: "ind", label: "行业", field: "ind", primary: false },
    { key: "cplx", label: "复杂度", field: "cplx", primary: false, single: true },
  ];
  const RISK_LBL = { open: "宽松许可", copyleft: "传染性", "restrictive-nc": "非商业限制", undeclared: "未声明" };

  let DATA = [];
  const state = { q: "", filters: {}, quick: {}, sort: "name", shown: 48 };
  DIMS.forEach(d => state.filters[d.key] = new Set());

  /* ── hash 同步 ── */
  function stateToHash() {
    const p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    DIMS.forEach(d => { if (state.filters[d.key].size) p.set(d.key, [...state.filters[d.key]].join(",")); });
    Object.keys(state.quick).forEach(k => { if (state.quick[k]) p.set("qk", k); });
    if (state.sort !== "name") p.set("sort", state.sort);
    const h = p.toString();
    history.replaceState(null, "", h ? "#" + h : location.pathname);
  }
  function hashToState() {
    const p = new URLSearchParams(location.hash.slice(1));
    state.q = p.get("q") || "";
    DIMS.forEach(d => (p.get(d.key) || "").split(",").filter(Boolean).forEach(v => state.filters[d.key].add(v)));
    (p.getAll("qk") || []).forEach(k => state.quick[k] = true);
    state.sort = p.get("sort") || "name";
    document.getElementById("q").value = state.q;
  }

  /* ── 数据加载 ── */
  async function load() {
    DATA = await fetch("data/skills.json").then(r => r.json());
    // 构建搜索索引：英文按词、中文 bigram
    DATA.forEach(d => {
      const text = (d.id + " " + d.name + " " + (d.summary || "")).toLowerCase();
      const tokens = new Set();
      text.replace(/[a-z0-9][a-z0-9\-_.]*/g, m => { tokens.add(m); return m; });
      const cjk = text.replace(/[a-z0-9\s\-_.]/g, "");
      for (let i = 0; i < cjk.length - 1; i++) tokens.add(cjk.slice(i, i + 2));
      if (cjk.length === 1) tokens.add(cjk);
      d._tokens = tokens;
      d._text = text;
    });
    renderStats();
    renderSidebar();
    hashToState();
    refresh();
  }

  /* ── 统计条 ── */
  function renderStats() {
    const srcCnt = {}, jurCnt = {};
    DATA.forEach(d => {
      srcCnt[d.src] = (srcCnt[d.src] || 0) + 1;
      (d.jur || []).forEach(j => jurCnt[j] = (jurCnt[j] || 0) + 1);
    });
    const topJur = Object.entries(jurCnt).sort((a, b) => b[1] - a[1]).slice(0, 5);
    $("#stats").innerHTML =
      `<div class="stat"><b>${DATA.length}</b>skills</div>` +
      Object.entries(srcCnt).sort((a, b) => b[1] - a[1])
        .map(([k, v]) => `<div class="stat"><b>${v}</b>${lbl("src", k)}</div>`).join("") +
      `<div class="stat" style="margin-left:auto">` +
      topJur.map(([k, v]) => `<span class="quick" data-jur="${k}">${lbl("jur", k)} ${v}</span>`).join(" · ") +
      `</div>`;
    $("#stats").querySelectorAll(".quick").forEach(el =>
      el.addEventListener("click", () => {
        state.filters.jur.clear(); state.filters.jur.add(el.dataset.jur); refresh();
      }));
  }

  /* ── 侧栏 ── */
  function facetCounts(field) {
    const c = {};
    const pool = filtered(true);
    pool.forEach(d => {
      const v = d[field];
      (Array.isArray(v) ? v : [v]).forEach(x => { if (x) c[x] = (c[x] || 0) + 1; });
    });
    return c;
  }
  function renderSidebar() {
    const sb = $("#sidebar");
    let html = "";
    DIMS.filter(d => d.primary).forEach(d => { html += dimHtml(d); });
    html += `<div class="advanced-toggle" id="adv-toggle">▸ 高级筛选（${DIMS.filter(d => !d.primary).length} 个维度）</div>`;
    html += `<div id="adv-dims" style="display:none">`;
    DIMS.filter(d => !d.primary).forEach(d => { html += dimHtml(d); });
    html += `</div>`;
    sb.innerHTML = html;
    sb.querySelectorAll(".filter-opt").forEach(el =>
      el.addEventListener("click", () => {
        const { dim, val } = el.dataset;
        const set = state.filters[dim];
        const d = DIMS.find(x => x.key === dim);
        if (set.has(val)) set.delete(val);
        else { if (d.single) set.clear(); set.add(val); }
        refresh();
      }));
    $("#adv-toggle").addEventListener("click", () => {
      const el = $("#adv-dims");
      const open = el.style.display !== "none";
      el.style.display = open ? "none" : "block";
      $("#adv-toggle").textContent = (open ? "▸" : "▾") + ` 高级筛选（${DIMS.filter(d => !d.primary).length} 个维度）`;
    });
  }
  function dimHtml(d) {
    const cnt = facetCounts(d.field);
    const entries = Object.entries(cnt).sort((a, b) => b[1] - a[1]).slice(0, 12);
    if (!entries.length) return "";
    const labelOf = v => d.key === "lic" ? (RISK_LBL[v] || v) : lbl(d.key === "roles" ? "role" : d.key, v);
    return `<div class="filter-group"><h4>${d.label}</h4>` +
      entries.map(([v, n]) =>
        `<span class="filter-opt ${state.filters[d.key].has(v) ? "on" : ""}" data-dim="${d.key}" data-val="${v}">${labelOf(v)}<span class="cnt">${n}</span></span>`
      ).join("") + `</div>`;
  }

  /* ── 过滤 ── */
  function filtered(ignoreSelfDim) {
    return DATA.filter(d => {
      for (const dim of DIMS) {
        const set = state.filters[dim.key];
        if (!set.size) continue;
        const v = d[dim.field];
        const arr = Array.isArray(v) ? v : [v];
        if (!arr.some(x => set.has(x))) return false;
      }
      for (const k of Object.keys(state.quick)) {
        if (!state.quick[k]) continue;
        if (k === "scripts" && !d.has.scripts) return false;
        if (k === "references" && !d.has.references) return false;
        if (k === "fresh" && !d.fresh) return false;
        if (k === "cur" && !d.cur) return false;
      }
      if (state.q) {
        const qs = state.q.toLowerCase().trim();
        if (!qs) return true;
        // 多词 AND；单词：子串或 token 前缀
        return qs.split(/\s+/).every(w => {
          if (d._text.includes(w)) return true;
          for (const t of d._tokens) if (t.startsWith(w)) return true;
          return false;
        });
      }
      return true;
    });
  }

  function sorted(list) {
    const by = {
      name: (a, b) => a.id.localeCompare(b.id),
      files: (a, b) => b.files - a.files,
      q: (a, b) => b.q - a.q || b.files - a.files,
    }[state.sort];
    return [...list].sort(by);
  }

  /* ── 渲染 ── */
  function cardHtml(d) {
    const tags = [];
    (d.jur || []).slice(0, 2).forEach(j => tags.push(`<span class="tag jur">${lbl("jur", j)}</span>`));
    if (d.dom && d.dom[0]) tags.push(`<span class="tag dom">${lbl("dom", d.dom[0])}</span>`);
    if (d.task && d.task[0]) tags.push(`<span class="tag task">${lbl("task", d.task[0])}</span>`);
    if (d.cur) tags.push(`<span class="tag star">★精选</span>`);
    tags.push(`<span class="tag src">${lbl("src", d.src)}</span>`);
    return `<div class="card">
      <div class="card-title"><a href="./skill.html?f=${encodeURIComponent(d.id)}">${escHtml(d.name)}</a></div>
      <div class="card-summary">${escHtml(d.summary || "（暂无简介）")}</div>
      <div class="card-tags">${tags.slice(0, 5).join("")}</div>
      <div class="card-foot">
        <span class="lic-dot lic-${d.lrisk}" title="授权：${lbl("lic", d.lic)}"></span>
        <span>${d.files} 文件</span>
        <span>·</span><span>${d.cplx}</span>
        <span class="q-dots" title="质量分 ${d.q}/5">${"●".repeat(d.q)}${"○".repeat(5 - d.q)}</span>
        <span style="margin-left:auto">${d.lang === "zh-CN" ? "中" : "EN"}</span>
      </div>
    </div>`;
  }

  function renderChips() {
    const chips = [];
    DIMS.forEach(d => state.filters[d.key].forEach(v => {
      const labelOf = d.key === "lic" ? (RISK_LBL[v] || v) : lbl(d.key === "roles" ? "role" : d.key, v);
      chips.push(`<span class="chip" data-dim="${d.key}" data-val="${v}">${d.label}: ${labelOf}</span>`);
    }));
    Object.keys(state.quick).forEach(k => {
      if (state.quick[k]) chips.push(`<span class="chip" data-quick="${k}">${{scripts:"有脚本",references:"有参考库",fresh:"含新法",cur:"★精选"}[k]}</span>`);
    });
    $("#chips").innerHTML = chips.join("");
    $("#chips").querySelectorAll(".chip").forEach(el =>
      el.addEventListener("click", () => {
        if (el.dataset.quick) state.quick[el.dataset.quick] = false;
        else state.filters[el.dataset.dim].delete(el.dataset.val);
        refresh();
      }));
  }

  function renderCards(reset) {
    const list = sorted(filtered());
    if (reset) state.shown = 48;
    const slice = list.slice(0, state.shown);
    $("#cards").innerHTML = slice.map(cardHtml).join("");
    $("#meta").innerHTML = `命中 <b>${list.length}</b> / ${DATA.length} 个技能${list.length > state.shown ? ` · 已显示 ${slice.length}` : ""}`;
    document.getElementById("sentinel").style.display = list.length > state.shown ? "block" : "none";
  }

  function refresh() {
    stateToHash();
    renderChips();
    renderSidebar();
    renderCards(true);
    document.querySelectorAll(".sort-opt").forEach(el => {
      const k = el.dataset.sort, qk = el.dataset.quick;
      el.classList.toggle("on", (k && k === state.sort) || (qk && !!state.quick[qk]));
    });
  }

  /* ── 事件 ── */
  let debounce;
  $("#q").addEventListener("input", e => {
    clearTimeout(debounce);
    debounce = setTimeout(() => { state.q = e.target.value; refresh(); }, 180);
  });
  document.querySelectorAll(".sort-opt[data-sort]").forEach(el =>
    el.addEventListener("click", () => { state.sort = el.dataset.sort; refresh(); }));
  document.querySelectorAll(".sort-opt[data-quick]").forEach(el =>
    el.addEventListener("click", () => {
      const k = el.dataset.quick; state.quick[k] = !state.quick[k]; refresh();
    }));
  new IntersectionObserver(es => {
    if (es[0].isIntersecting) { state.shown += 48; renderCards(false); }
  }, { rootMargin: "600px" }).observe(document.getElementById("sentinel"));
  window.addEventListener("hashchange", () => {
    DIMS.forEach(d => state.filters[d.key].clear());
    state.quick = {};
    hashToState(); refresh();
  });

  load().catch(e => {
    document.getElementById("meta").textContent = "数据加载失败：" + e.message;
  });
})();
