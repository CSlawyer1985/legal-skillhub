/* Data-driven explorer for the anonymized 2026 collection. */
(() => {
  const PAGE_SIZE = 36;
  const state = { group: "all", query: "", limit: PAGE_SIZE };
  const grid = document.getElementById("yl-grid");
  const filters = document.getElementById("yl-filters");
  const search = document.getElementById("yl-search-input");
  const count = document.getElementById("yl-result-count");
  const empty = document.getElementById("yl-empty");
  const more = document.getElementById("yl-load-more");
  const featuredGrid = document.getElementById("yl-featured-grid");

  const normalize = value => String(value || "").toLocaleLowerCase("zh-CN").replace(/\s+/g, " ").trim();
  const first = (value, fallback = "") => Array.isArray(value) && value.length ? value[0] : fallback;

  function featuredCard(entry, byId) {
    const number = String(entry.order || "").padStart(2, "0");
    const linked = entry.availability === "indexed" && entry.skill_id && byId.has(entry.skill_id);
    const body = `<span class="yl-feature-number" aria-hidden="true">${escHtml(number)}</span>
      <div class="yl-feature-main">
        <div class="yl-feature-meta"><span>${escHtml(entry.session)}</span><span>${escHtml(entry.track)}</span></div>
        <h3>${escHtml(entry.title)}</h3>
        <p class="yl-feature-author"><span>展示团队</span>${escHtml(entry.presenters)}</p>
        <div class="yl-feature-foot">
          <span class="yl-feature-status">${linked ? "● 已收录" : "○ 现场展示记录"}</span>
          <span>${linked ? "查看 Skill ↗" : "技能包待补充"}</span>
        </div>
      </div>`;
    if (linked) {
      return `<a class="yl-feature-card" data-availability="indexed" href="${skillHref(entry.skill_id)}">${body}</a>`;
    }
    return `<article class="yl-feature-card" data-availability="showcase-only">${body}</article>`;
  }

  function card(record, item) {
    const tags = [
      lbl("jur", first(record.jur)),
      lbl("dom", first(record.dom)),
      lbl("task", first(record.task)),
    ].filter(Boolean).slice(0, 3);
    const title = item.title || record.name || item.id;
    const author = item.author || record.author || "原作者未署名";
    const summary = record.summary || "已收录的 Agent Skill，点击查看完整说明与技能包文件。";
    return `<a class="yl-card" href="${skillHref(item.id)}">
      <div class="yl-card-meta"><code>${escHtml(item.id)}</code><span>${escHtml(item.eyebrow)} ↗</span></div>
      <h3>${escHtml(title)}</h3>
      <p>${escHtml(summary)}</p>
      <div class="yl-card-author"><span>作者 / 团队</span><b>${escHtml(author)}</b></div>
      <div class="yl-card-tags">${tags.map(tag => `<span>${escHtml(tag)}</span>`).join("")}</div>
      <div class="yl-card-foot"><span>${record.files || 1} FILE${record.files === 1 ? "" : "S"}</span><span>VIEW SKILL</span></div>
    </a>`;
  }

  function render(items) {
    const query = normalize(state.query);
    const filtered = items.filter(item => {
      if (state.group !== "all" && item.group !== state.group) return false;
      if (!query) return true;
      return item.search.includes(query);
    });
    count.textContent = String(filtered.length);
    const visible = filtered.slice(0, state.limit);
    grid.innerHTML = visible.map(item => card(item.record, item)).join("");
    grid.setAttribute("aria-busy", "false");
    empty.hidden = filtered.length !== 0;
    more.hidden = visible.length >= filtered.length;
    more.textContent = visible.length < filtered.length
      ? `继续加载 ${Math.min(PAGE_SIZE, filtered.length - visible.length)} 项 ↓`
      : "";
  }

  async function init() {
    try {
      const [manifest, skills] = await Promise.all([
        fetch("./events/young-lawyers-ai-skills-2026.json?v=95-priority2").then(response => {
          if (!response.ok) throw new Error(`manifest HTTP ${response.status}`);
          return response.json();
        }),
        fetch("./data/skills.json").then(response => {
          if (!response.ok) throw new Error(`skills HTTP ${response.status}`);
          return response.json();
        }),
      ]);
      const byId = new Map(skills.map(record => [record.id, record]));
      const featured = Array.isArray(manifest.featured) ? manifest.featured : [];
      featuredGrid.innerHTML = featured.map(entry => featuredCard(entry, byId)).join("");
      featuredGrid.setAttribute("aria-busy", "false");
      const featuredRank = new Map(
        featured.filter(entry => entry.skill_id).map((entry, index) => [entry.skill_id, index])
      );
      const priorityAuthors = Array.isArray(manifest.priority_authors) ? manifest.priority_authors : [];
      const authorRank = author => {
        const rank = priorityAuthors.findIndex(name => String(author || "").includes(name));
        return rank === -1 ? Number.MAX_SAFE_INTEGER : rank;
      };
      const items = manifest.groups.flatMap(group => group.skills.map(id => {
        const record = byId.get(id) || { id, name: id, summary: "", jur: [], dom: [], task: [], files: 1 };
        const title = manifest.titles[id] || record.name || id;
        return {
          id,
          group: group.id,
          eyebrow: group.eyebrow,
          title,
          author: manifest.authors[id] || record.author || "原作者未署名",
          record,
          search: normalize([id, title, manifest.authors[id], record.author, record.name, record.summary, ...(record.jur || []), ...(record.dom || []), ...(record.task || [])].join(" ")),
        };
      })).sort((left, right) => {
        const featuredDelta = (featuredRank.get(left.id) ?? Number.MAX_SAFE_INTEGER)
          - (featuredRank.get(right.id) ?? Number.MAX_SAFE_INTEGER);
        if (featuredDelta) return featuredDelta;
        return authorRank(left.author) - authorRank(right.author);
      });

      const buttons = [
        { id: "all", label: "全部", count: items.length },
        ...manifest.groups.map(group => ({ id: group.id, label: group.label, count: group.skills.length })),
      ];
      filters.innerHTML = buttons.map((button, index) =>
        `<button class="yl-filter" type="button" data-group="${escHtml(button.id)}" aria-pressed="${index === 0}">${escHtml(button.label)} · ${button.count}</button>`
      ).join("");
      filters.addEventListener("click", event => {
        const button = event.target.closest("[data-group]");
        if (!button) return;
        state.group = button.dataset.group;
        state.limit = PAGE_SIZE;
        filters.querySelectorAll("[data-group]").forEach(node => node.setAttribute("aria-pressed", String(node === button)));
        render(items);
      });
      search.addEventListener("input", () => {
        state.query = search.value;
        state.limit = PAGE_SIZE;
        render(items);
      });
      more.addEventListener("click", () => {
        state.limit += PAGE_SIZE;
        render(items);
      });
      render(items);
    } catch (error) {
      featuredGrid.setAttribute("aria-busy", "false");
      featuredGrid.innerHTML = `<div class="yl-empty">现场展示数据加载失败：${escHtml(error.message)}</div>`;
      grid.setAttribute("aria-busy", "false");
      grid.innerHTML = `<div class="yl-empty">专题数据加载失败：${escHtml(error.message)}</div>`;
    }
  }

  init();
})();
