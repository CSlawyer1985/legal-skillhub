/* 顾问单位工作记录 - 前端逻辑
 * 视图职责：
 *  - 总表（currentUnit === ""）：仅列示各单位的服务对象名称与服务期限（依据律师服务合同），
 *    不含任何工作明细；工作明细全部在各单位独立分表中记录与展示。
 *  - 分表（currentUnit 为某单位）：展示该单位的法律服务工作明细。
 */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  let editingId = null;
  let currentUnits = [];
  let currentUnitMeta = {};   // { 单位名: {start_date, end_date} }
  let currentUnit = "";       // "" = 全部单位（总表）；否则为某家单位独立分表
  let currentUncCount = 0;    // 未分类单位记录数（unit 不在 units 列表中）
  const UNC = "__uncategorized__";  // 未分类单位 sentinel（与后端 server.py 保持一致）

  // ---------------- 通用 ---------------- //
  function toast(msg, isErr) {
    const t = $("toast");
    t.textContent = msg;
    t.className = "toast show" + (isErr ? " err" : "");
    setTimeout(() => { t.className = "toast" + (isErr ? " err" : ""); }, 2600);
  }

  async function api(path, opts) {
    const res = await fetch(path, Object.assign({ headers: { "Content-Type": "application/json" } }, opts));
    let data = {};
    try { data = await res.json(); } catch (e) { /* empty */ }
    if (!res.ok) throw new Error(data.error || ("请求失败 " + res.status));
    return data;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function todayStr() {
    const d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  function monthRange() {
    const d = new Date();
    const y = d.getFullYear(), m = d.getMonth();
    const from = y + "-" + String(m + 1).padStart(2, "0") + "-01";
    const last = new Date(y, m + 1, 0).getDate();
    const to = y + "-" + String(m + 1).padStart(2, "0") + "-" + String(last).padStart(2, "0");
    return { from, to };
  }

  function quarterRange() {
    const d = new Date();
    const q = Math.floor(d.getMonth() / 3);
    const from = new Date(d.getFullYear(), q * 3, 1);
    const to = new Date(d.getFullYear(), q * 3 + 3, 0);
    const f = (dt) => dt.getFullYear() + "-" + String(dt.getMonth() + 1).padStart(2, "0") + "-" + String(dt.getDate()).padStart(2, "0");
    return { from: f(from), to: f(to) };
  }

  // ---------------- 模式切换 ---------------- //
  function applyMode() {
    const overview = currentUnit === "";
    document.body.classList.toggle("is-overview", overview);
    if (overview) {
      $("panelHeadTitle").textContent = "顾问单位一览（总表）· 服务对象名称与服务期限";
    } else if (currentUnit === UNC) {
      $("panelHeadTitle").textContent = "工作记录明细 · 未分类单位";
    } else {
      $("panelHeadTitle").textContent = "工作记录明细 · " + currentUnit;
    }
  }

  // ---------------- 单位分表 Tab ---------------- //
  async function loadUnits() {
    const data = await api("/api/units");
    currentUnits = data.units || [];
    currentUnitMeta = data.unit_meta || {};
    currentUncCount = data.uncategorized_count || 0;
    renderUnitTabs();
    $("unitList").innerHTML = currentUnits.map(u => `<option value="${esc(u)}"></option>`).join("");
  }

  function renderUnitTabs() {
    const wrap = $("unitTabs");
    const uncBadge = currentUncCount > 0 ? ` <span class="badge">${currentUncCount}</span>` : "";
    wrap.innerHTML =
      `<button class="tab${currentUnit === "" ? " active" : ""}" data-unit="">全部单位（总表）</button>` +
      currentUnits.map(u => `<button class="tab${currentUnit === u ? " active" : ""}" data-unit="${esc(u)}" title="${esc(u)}">${esc(u)}</button>`).join("") +
      `<button class="tab tab-uncategorized${currentUnit === UNC ? " active" : ""}" data-unit="${UNC}" title="未分类单位：删除单位后保留、或新增时未指定归属的记录，可在此查看、编辑并重新指定单位">未分类单位${uncBadge}</button>` +
      `<button class="tab tab-manage" id="btnManageUnits">＋ 单位管理</button>`;
    wrap.querySelectorAll(".tab[data-unit]").forEach(b => b.onclick = () => {
      currentUnit = b.getAttribute("data-unit");
      renderUnitTabs();
      loadRecords();
    });
    $("btnManageUnits").onclick = openManage;
  }

  // ---------------- 列表（总表 / 分表 双视图） ---------------- //
  async function loadRecords() {
    applyMode();
    if (currentUnit === "") {
      // 总表视图：仅展示单位一览（服务对象名称 + 服务期限），无工作明细
      renderOverview();
      $("listCount").textContent = currentUnits.length + " 家单位";
      buildOverviewSummary();
      return;
    }
    const from = $("fFrom").value;
    const to = $("fTo").value;
    const qs = new URLSearchParams();
    qs.set("unit", currentUnit === UNC ? UNC : currentUnit);
    if (from) qs.set("from", from);
    if (to) qs.set("to", to);
    const data = await api("/api/records?" + qs.toString());
    const recs = data.records || [];
    $("pillCount").textContent = recs.length;
    $("pillHours").textContent = (data.total_hours != null ? data.total_hours : 0);
    $("listCount").textContent = "共 " + recs.length + " 项 · 工时 " + (data.total_hours != null ? data.total_hours : 0) + " 小时";
    buildSummary(recs);
    renderDetail(recs);
  }

  function renderOverview() {
    const thead = $("thead");
    thead.innerHTML = `
      <tr>
        <th class="seq">序号</th>
        <th>服务对象名称</th>
        <th>服务开始日期（合同约定）</th>
        <th>服务结束日期（合同约定）</th>
        <th>操作</th>
      </tr>`;
    const tb = $("tbody");
    if (!currentUnits.length) {
      tb.innerHTML = `<tr><td colspan="5"><div class="empty"><div class="big">🏢</div>暂无顾问单位。点击右上角「＋ 单位管理」新建单位并设置服务期限；各单位的具体工作明细请在对应分表中记录。</div></td></tr>`;
      return;
    }
    tb.innerHTML = currentUnits.map((u, i) => {
      const m = currentUnitMeta[u] || {};
      const sd = (m.start_date || "").trim() || '<span style="color:#aaa">—</span>';
      const ed = (m.end_date || "").trim() || '<span style="color:#aaa">—</span>';
      return `<tr>
        <td class="seq">${i + 1}</td>
        <td><span class="unit-tag">${esc(u)}</span></td>
        <td class="date">${sd}</td>
        <td class="date">${ed}</td>
        <td>
          <div class="row-actions">
            <button class="btn btn-ghost btn-sm" data-view="${esc(u)}">查看分表</button>
            <button class="btn btn-blue btn-sm" data-period="${esc(u)}">编辑期限</button>
          </div>
        </td>
      </tr>`;
    }).join("");
    tb.querySelectorAll("[data-view]").forEach(b => b.onclick = () => {
      currentUnit = b.getAttribute("data-view");
      renderUnitTabs();
      loadRecords();
    });
    tb.querySelectorAll("[data-period]").forEach(b => b.onclick = () => openPeriod(b.getAttribute("data-period")));
  }

  function renderDetail(recs) {
    const thead = $("thead");
    thead.innerHTML = `
      <tr>
        <th class="seq">序号</th>
        <th>日期</th>
        <th>律师工作内容</th>
        <th style="text-align:right">工作时间(小时)</th>
        <th>后续工作</th>
        <th>备注</th>
        <th>经办律师</th>
        <th>操作</th>
      </tr>`;
    const tb = $("tbody");
    if (!recs.length) {
      tb.innerHTML = `<tr><td colspan="8"><div class="empty"><div class="big">📋</div>当前单位分表「${esc(currentUnit)}」暂无记录。点击右上角「+ 新增记录」开始记录。</div></td></tr>`;
      return;
    }
    tb.innerHTML = recs.map(r => `
      <tr>
        <td class="seq">${r.seq}</td>
        <td class="date">${esc(r.date)}</td>
        <td>${esc(r.content)}</td>
        <td class="hours">${esc(r.hours)}</td>
        <td>${esc(r.followup) || '<span style="color:#aaa">—</span>'}</td>
        <td>${esc(r.remark) || '<span style="color:#aaa">—</span>'}</td>
        <td class="lawyer">${esc(r.lawyer) || '<span style="color:#aaa">—</span>'}</td>
        <td>
          <div class="row-actions">
            <button class="btn btn-ghost btn-sm" data-edit="${esc(r.id)}">编辑</button>
            <button class="btn btn-danger btn-sm" data-del="${esc(r.id)}">删除</button>
          </div>
        </td>
      </tr>`).join("");
    tb.querySelectorAll("[data-edit]").forEach(b => b.onclick = () => openModal(b.getAttribute("data-edit")));
    tb.querySelectorAll("[data-del]").forEach(b => b.onclick = () => delRecord(b.getAttribute("data-del")));
  }

  function buildSummary(records) {
    const wrap = $("summaryBar");
    const units = new Set(records.map(r => r.unit).filter(Boolean));
    const hours = records.reduce((s, r) => s + (parseFloat(r.hours) || 0), 0);
    const follow = records.filter(r => r.followup && r.followup.trim()).length;
    wrap.innerHTML = `
      <div class="chip"><div class="k">记录事项</div><div class="v">${records.length} <small>项</small></div></div>
      <div class="chip"><div class="k">累计工时</div><div class="v">${hours.toFixed(2)} <small>小时</small></div></div>
      <div class="chip"><div class="k">涉及单位</div><div class="v">${units.size} <small>家</small></div></div>
      <div class="chip"><div class="k">含后续工作</div><div class="v">${follow} <small>项</small></div></div>`;
  }

  function buildOverviewSummary() {
    const wrap = $("summaryBar");
    const withPeriod = currentUnits.filter(u => {
      const m = currentUnitMeta[u] || {};
      return (m.start_date || "").trim() && (m.end_date || "").trim();
    }).length;
    wrap.innerHTML = `
      <div class="chip"><div class="k">顾问单位</div><div class="v">${currentUnits.length} <small>家</small></div></div>
      <div class="chip"><div class="k">已设服务期限</div><div class="v">${withPeriod} <small>家</small></div></div>
      <div class="chip"><div class="k">待补服务期限</div><div class="v">${currentUnits.length - withPeriod} <small>家</small></div></div>`;
  }

  // ---------------- 记录弹窗 ---------------- //
  function openModal(id) {
    editingId = id || null;
    $("modalTitle").textContent = id ? "编辑工作记录" : "新增工作记录";
    if (id) {
      api("/api/records/" + id).then(d => {
        if (d.record) fillForm(d.record);
      }).catch(() => toast("加载记录失败", true));
    } else {
      fillForm({ date: todayStr(), hours: 0, unit: currentUnit === UNC ? "" : (currentUnit || "") });
    }
    $("modal").classList.add("show");
  }

  function fillForm(r) {
    $("mUnit").value = r.unit || "";
    $("mDate").value = r.date || todayStr();
    $("mContent").value = r.content || "";
    $("mHours").value = (r.hours != null ? r.hours : 0);
    $("mLawyer").value = r.lawyer || "";
    $("mFollowup").value = r.followup || "";
    $("mRemark").value = r.remark || "";
  }

  function closeModal() {
    $("modal").classList.remove("show");
    editingId = null;
  }

  async function saveRecord() {
    let unitVal = $("mUnit").value.trim();
    if (!unitVal) {
      if (currentUnit === UNC) {
        // 未分类单位视图下允许不指定单位，保持为未分类（提交 sentinel，后端归一化为空单位）
        unitVal = UNC;
      } else {
        toast("请填写顾问单位", true);
        return;
      }
    }
    const payload = {
      unit: unitVal,
      date: $("mDate").value,
      content: $("mContent").value.trim(),
      hours: $("mHours").value,
      lawyer: $("mLawyer").value.trim(),
      followup: $("mFollowup").value.trim(),
      remark: $("mRemark").value.trim(),
    };
    if (!payload.date) { toast("请选择日期", true); return; }
    if (!payload.content) { toast("请填写律师工作内容", true); return; }
    try {
      if (editingId) {
        await api("/api/records/" + editingId, { method: "PUT", body: JSON.stringify(payload) });
        toast("已保存修改");
      } else {
        await api("/api/records", { method: "POST", body: JSON.stringify(payload) });
        toast("记录已添加");
      }
      closeModal();
      await loadUnits();
      await loadRecords();
    } catch (e) {
      toast(e.message, true);
    }
  }

  async function delRecord(id) {
    if (!confirm("确认删除该条工作记录？")) return;
    try {
      await api("/api/records/" + id, { method: "DELETE" });
      toast("已删除");
      await loadRecords();
    } catch (e) {
      toast(e.message, true);
    }
  }

  // ---------------- 服务期限弹窗 ---------------- //
  function openPeriod(unit) {
    $("periodUnit").textContent = unit;
    const m = currentUnitMeta[unit] || {};
    $("pStart").value = (m.start_date || "").trim();
    $("pEnd").value = (m.end_date || "").trim();
    $("periodModal").dataset.unit = unit;
    $("periodModal").classList.add("show");
  }

  function closePeriod() {
    $("periodModal").classList.remove("show");
  }

  async function savePeriod() {
    const unit = $("periodModal").dataset.unit;
    const start_date = $("pStart").value.trim();
    const end_date = $("pEnd").value.trim();
    if (start_date && end_date && start_date > end_date) {
      toast("服务结束日期不得早于开始日期", true);
      return;
    }
    try {
      const r = await api("/api/units/meta", { method: "PUT", body: JSON.stringify({ name: unit, start_date, end_date }) });
      currentUnitMeta = r.unit_meta || currentUnitMeta;
      toast("已保存服务期限");
      closePeriod();
      if (currentUnit === "") { renderOverview(); buildOverviewSummary(); }
      else { await loadUnits(); }
    } catch (e) { toast(e.message, true); }
  }

  // ---------------- 单位管理弹窗 ---------------- //
  function openManage() {
    $("newUnitName").value = "";
    $("newUnitStart").value = "";
    $("newUnitEnd").value = "";
    renderManageList();
    $("manageModal").classList.add("show");
  }

  function closeManage() {
    $("manageModal").classList.remove("show");
  }

  async function createUnit() {
    const name = $("newUnitName").value.trim();
    if (!name) { toast("请输入单位名称", true); return; }
    const start_date = $("newUnitStart").value.trim();
    const end_date = $("newUnitEnd").value.trim();
    if (start_date && end_date && start_date > end_date) {
      toast("服务结束日期不得早于开始日期", true);
      return;
    }
    try {
      const r = await api("/api/units", { method: "POST", body: JSON.stringify({ name, start_date, end_date }) });
      currentUnits = r.units || currentUnits;
      currentUnitMeta = r.unit_meta || currentUnitMeta;
      $("newUnitName").value = "";
      $("newUnitStart").value = "";
      $("newUnitEnd").value = "";
      await loadUnits();
      await loadRecords();
      toast("已新建单位分表：" + name);
      renderManageList();
    } catch (e) { toast(e.message, true); }
  }

  function renderManageList() {
    const ul = $("unitListManage");
    if (!currentUnits.length) {
      ul.innerHTML = '<li class="empty">暂无单位分表，请在上方输入名称后点击「新建」。</li>';
      return;
    }
    ul.innerHTML = currentUnits.map(u => {
      const m = currentUnitMeta[u] || {};
      const period = (m.start_date || m.end_date)
        ? (esc(m.start_date || "—") + " ~ " + esc(m.end_date || "—"))
        : "未设服务期限";
      return `
      <li>
        <span class="u-name">${esc(u)}</span>
        <span class="u-period">${period}</span>
        <span class="u-actions">
          <button class="btn btn-ghost btn-sm" data-period="${esc(u)}">编辑期限</button>
          <button class="btn btn-ghost btn-sm" data-rename="${esc(u)}">重命名</button>
          <button class="btn btn-danger btn-sm" data-delunit="${esc(u)}">删除</button>
        </span>
      </li>`;
    }).join("");
    ul.querySelectorAll("[data-period]").forEach(b => b.onclick = () => { closeManage(); openPeriod(b.getAttribute("data-period")); });
    ul.querySelectorAll("[data-rename]").forEach(b => b.onclick = () => renameUnit(b.getAttribute("data-rename")));
    ul.querySelectorAll("[data-delunit]").forEach(b => b.onclick = () => deleteUnit(b.getAttribute("data-delunit")));
  }

  async function renameUnit(oldName) {
    const input = prompt("将单位分表重命名为：", oldName);
    if (input == null) return;
    const newName = input.trim();
    if (!newName) { toast("名称不能为空", true); return; }
    if (newName === oldName) return;
    try {
      const r = await api("/api/units", { method: "PUT", body: JSON.stringify({ old: oldName, new: newName }) });
      currentUnitMeta = r.unit_meta || currentUnitMeta;
      if (currentUnit === oldName) currentUnit = newName;
      await loadUnits();
      toast("已重命名为：" + newName);
      renderManageList();
    } catch (e) { toast(e.message, true); }
  }

  async function deleteUnit(name) {
    if (!confirm(`确认删除单位分表「${name}」？`)) return;
    const mode = confirm(
      "请选择删除方式：\n\n点【确定】= 仅移除单位标签，保留其全部工作记录（归入“未分类单位”）\n点【取消】= 连同该单位全部工作记录一起删除（不可恢复）"
    ) ? "keep_records" : "delete_records";
    try {
      const r = await api("/api/units", { method: "DELETE", body: JSON.stringify({ name, mode }) });
      currentUnitMeta = r.unit_meta || currentUnitMeta;
      if (currentUnit === name) currentUnit = "";
      await loadUnits();
      await loadRecords();
      toast(mode === "delete_records"
        ? `已删除单位「${name}」及其 ${r.removed_records} 条工作记录`
        : `已移除单位「${name}」标签，其记录归入未分类`);
      renderManageList();
    } catch (e) { toast(e.message, true); }
  }

  // ---------------- 报告 ---------------- //
  function reportUrl(fmt) {
    const from = $("fFrom").value;
    const to = $("fTo").value;
    const qs = new URLSearchParams();
    qs.set("format", fmt);
    if (currentUnit) qs.set("unit", currentUnit);           // 单单位分表（仅明细）
    if (from) qs.set("from", from);
    if (to) qs.set("to", to);
    if ($("chkSplit").checked && !currentUnit) qs.set("split", "1");  // 总表按单位拆多分表（总表概览 + 各单位明细）
    return "/api/report?" + qs.toString();
  }

  function downloadReport(fmt) {
    const w = window.open(reportUrl(fmt), "_blank");
    if (!w) toast("浏览器拦截了下载，请允许弹出窗口", true);
    else toast(fmt === "docx" ? "正在生成 DOCX 报告…" : "正在生成 Excel 报告…");
  }

  // ---------------- 事件绑定 ---------------- //
  function bind() {
    $("btnAdd").onclick = () => openModal(null);
    $("btnCancel").onclick = closeModal;
    $("btnSave").onclick = saveRecord;
    $("btnQuery").onclick = loadRecords;
    $("btnReset").onclick = () => { $("fFrom").value = ""; $("fTo").value = ""; loadRecords(); };
    $("btnDocx").onclick = () => downloadReport("docx");
    $("btnExcel").onclick = () => downloadReport("excel");
    $("btnThisMonth").onclick = () => {
      const r = monthRange(); $("fFrom").value = r.from; $("fTo").value = r.to; loadRecords();
      toast("已按本月范围筛选，可导出报告");
    };
    $("btnThisQuarter").onclick = () => {
      const r = quarterRange(); $("fFrom").value = r.from; $("fTo").value = r.to; loadRecords();
      toast("已按本季度范围筛选，可导出报告");
    };
    $("modal").onclick = (e) => { if (e.target === $("modal")) closeModal(); };
    // 单位管理
    $("btnManageClose").onclick = closeManage;
    $("btnCreateUnit").onclick = createUnit;
    $("manageModal").onclick = (e) => { if (e.target === $("manageModal")) closeManage(); };
    // 服务期限
    $("btnPeriodClose").onclick = closePeriod;
    $("btnPeriodSave").onclick = savePeriod;
    $("periodModal").onclick = (e) => { if (e.target === $("periodModal")) closePeriod(); };
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closeModal(); closeManage(); closePeriod(); } });
  }

  // ---------------- 启动 ---------------- //
  async function init() {
    bind();
    $("mDate").value = todayStr();
    try {
      await loadUnits();
      await loadRecords();
    } catch (e) {
      toast("初始化失败：" + e.message, true);
    }
  }

  init();
})();
