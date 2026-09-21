/* One-Contract Rule Studio — 前端（原生 JS，无框架、无 CDN、无遥测）
 *
 * 安全约定：
 * - 规则文本一律用 textContent 渲染，**绝不使用 innerHTML**；
 * - 会话凭据只保存在内存（模块作用域），不进入 localStorage/sessionStorage/query；
 * - 所有规则语义来自 Core，前端不复制优先级。
 */
(function () {
  "use strict";

  // 会话凭据：仅内存
  var session = { token: null, csrf: null, origin: null };

  // ---------- 基础设施 ---------- //
  function bootstrap() {
    return fetch("/api/v1/session/bootstrap", {
      method: "GET",
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    })
      .then(function (r) { return r.json(); })
      .then(function (body) {
        if (!body.success) { throw new Error("会话初始化失败"); }
        session.token = body.result.token;
        session.csrf = body.result.csrf_token;
        session.origin = body.result.origin;
      });
  }

  function call(method, path, body) {
    var headers = { Accept: "application/json" };
    if (session.token) { headers.Authorization = "Bearer " + session.token; }
    var init = { method: method, headers: headers, credentials: "same-origin" };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      headers["X-CSRF-Token"] = session.csrf;
      init.body = JSON.stringify(body);
    }
    return fetch(path, init).then(function (r) {
      return r.json().then(function (payload) {
        return { status: r.status, body: payload };
      });
    }).catch(function () {
      // 本地服务已退出（默认空闲 120 秒）或不可达时，fetch 会 **reject**，
      // 而所有调用方只判 `res.body.success`、也没有 .catch——于是界面**完全静默**：
      // 点击没有任何反应、也无任何提示，用户会以为系统坏了。
      // 在此统一收口成结构化的失败结果，并挂出全局横幅。
      showServiceDown();
      return {
        status: 0,
        body: {
          success: false,
          error: {
            code: "LOCAL_SERVICE_UNAVAILABLE",
            message: "无法连接本地服务，面板可能已按空闲超时自动退出。",
            remediation: "请关闭本页，再双击启动文件重新打开；当前页面上的内容可能已过期。",
          },
        },
      };
    });
  }

  /** 服务不可达：挂出全局横幅（只挂一次），不静默。 */
  function showServiceDown() {
    var box = document.getElementById("service-status");
    if (!box || !box.hidden) { return; }
    box.textContent = "本地工具暂时无法连接，可能已自动休眠。请关闭本页，再双击启动文件重新打开；"
      + "当前页面上的内容可能已过期，不要据此下结论。";
    box.hidden = false;
  }

  function el(tag, text, className) {
    var node = document.createElement(tag);
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    if (className) { node.className = className; }
    return node;
  }

  function clear(node) {
    while (node.firstChild) { node.removeChild(node.firstChild); }
  }

  /**
   * 组装错误文案。
   *
   * 冻结错误码的 `message` 是**通用话术**，具体原因在 `error.details.detail`。
   * 只显示 message 会把三种不同失败显示成同一句「该事项需要人工判断，系统未自动决定」：
   * 主类型不存在、大类与主类型冲突、大类不存在——**用户无法据此知道该改什么**。
   * 后端已算出精确原因（RES-009 要求「明确失败」），呈现层不得把它丢掉。
   */
  function errorText(body, prefix) {
    var err = (body && body.error) || {};
    var text = prefix + (err.message || "请求失败");
    var detail = err.details && err.details.detail;
    if (detail) {
      text += "（" + detail + "）";
    } else if (err.remediation) {
      text += "（" + err.remediation + "）";
    }
    return text;
  }

  /**
   * 节点的适用范围文案（VIS-004 通过标准里的 `scope`）。
   *
   * 接口一直返回 `roles` / `scene_tags` / `type_ids` / `domain_codes` 四个字段，
   * 而界面从不渲染它们——用户看不到「这条规则适用于什么范围」，只能从关系图猜。
   * 列表可能很长（大类卡可派生上百个类型），故每个维度最多列 6 项并给出总数，
   * 避免详情面板被撑爆（VIS-010 首屏不传输全部正文的同一取向）。
   */
  var SCOPE_PREVIEW_LIMIT = 6;
  var ROLE_LABELS = { buyer: "买方／采购方", supplier: "卖方／供应方", transferor: "转让方", transferee: "受让方", employer: "用人单位", employee: "劳动者" };
  var SCENE_LABELS = { equipment_purchase: "设备采购", material_purchase: "原材料采购", delivery_logistics: "交付与物流", acceptance: "验收", breach_remedy: "违约救济", confidentiality: "保密", noncompete: "竞业限制", mutual_termination: "协商解除劳动关系", handover: "房屋或项目交接" };

  function friendlyScopeValues(kind, values) {
    if (kind === "角色") { return values.map(function (v) { return ROLE_LABELS[v] || "其他约定角色"; }); }
    if (kind === "场景") { return values.map(function (v) { return SCENE_LABELS[v] || "特定业务情形"; }); }
    if (kind === "类型") {
      return values.map(function (v) {
        return contractTypeChoices[v] ? contractTypeChoices[v].type_name : "特定合同类型";
      });
    }
    if (kind === "大类") {
      return values.map(function (v) {
        var found = Object.keys(contractTypeChoices).map(function (id) { return contractTypeChoices[id]; })
          .filter(function (item) { return item.domain_code === v; })[0];
        return found ? found.domain_name : "特定业务大类";
      });
    }
    return values;
  }

  function scopeText(node) {
    var groups = [
      ["大类", node.domain_codes],
      ["类型", node.type_ids],
      ["角色", node.roles],
      ["场景", node.scene_tags],
    ];
    var parts = [];
    groups.forEach(function (pair) {
      var values = pair[1] || [];
      if (!values.length) { return; }
      var shown = friendlyScopeValues(pair[0], values.slice(0, SCOPE_PREVIEW_LIMIT)).join("、");
      if (values.length > SCOPE_PREVIEW_LIMIT) {
        shown += " 等 " + values.length + " 项";
      }
      parts.push(pair[0] + " " + shown);
    });
    return parts.length ? parts.join("；") : "—";
  }

  // 数据模型里的英文枚举只用于机器交换；界面统一显示中文业务用语。
  var LABELS = {
    layer: { global: "通用审查要求", domain: "业务大类原则", type: "具体合同规则", client: "客户专属规则", case_instruction: "本案特别指示" },
    approval: { draft: "草稿", candidate: "待审核", lawyer_approved: "律师已确认", regression_passed: "测试已通过", active: "已启用", deprecated: "已停用" },
    activation: { active: "已启用", inactive: "未启用", deprecated: "已停用" },
    visibility: { full_active: "正文已启用", metadata_only_candidate: "待审核，仅显示摘要", document_node: "通用说明", private_client: "客户专属", unavailable: "暂不可用" },
    coverage: { strong: "较完整", limited: "有限覆盖", gap: "尚无规则", domain_and_type: "大类与具体类型均有规则", type_only: "仅有具体类型规则", domain_only: "仅有业务大类规则", global_only: "仅有通用规则", none: "尚无专门规则" },
    edge: { contains: "包含", inherits: "继承", deepens: "进一步细化", depends_on: "依赖", conflicts_with: "存在冲突", shared_by: "共同使用", sourced_from: "依据来源", client_overlays: "由客户规则补充" },
    decision: { included: "采用", excluded: "不采用", shadow_only: "仅显示摘要", blocked: "暂停处理" },
    proposal: { create: "新增规则", supersede: "修改现有规则", deprecate: "建议停用", candidate: "待审核", approved: "已确认", rejected: "不采纳" },
    event: { profile_created: "创建客户档案", draft_created: "新建规则草稿", draft_updated: "修改规则草稿", rule_submitted: "送交复核", lawyer_approved: "律师确认", regression_recorded: "记录测试结果", snapshot_published: "启用新版本", snapshot_rolled_back: "恢复上一版本", rule_deprecated: "停用规则", draft_deleted: "删除草稿", baseline_published: "建立回退点" },
    conflict: { HARD_BOUNDARY_CONFLICT: "触及法律边界，已暂停自动处理", CLIENT_SNAPSHOT_REQUIRED: "缺少客户规则版本，无法继续", CLIENT_SNAPSHOT_INCOMPATIBLE: "客户规则版本与公共规则不匹配" }
  };

  function label(group, value) {
    return (LABELS[group] && LABELS[group][value]) || value || "—";
  }

  function approvalStatusLabel(value) {
    return label("approval", value);
  }

  /**
   * 生命周期操作成功后给用户看的话。
   *
   * 此前这里直接 `JSON.stringify(result)`，于是律师看到的是
   * `已完成：submit（{"client_rule_id":"cr_…","revision":1,"approval_status":"candidate"}）`——
   * 内部动作名 + 原始 JSON。每个动作改说一句人话，并讲清**它改变了什么**
   * （推进到哪一步、是否已经生效、有没有动到历史数据）。
   * 缺字段时回落成通用中文，**不回落 JSON**——回落成 JSON 等于前功尽弃。
   */
  function lifecycleMessage(action, result) {
    var rule = (loadedDraft && loadedDraft.title) || "该规则";
    if (action === "submit") {
      return "已送交复核：" + rule + "。当前仍未启用。";
    }
    if (action === "approve") {
      return "已记录律师确认：" + rule + "。还需完成测试后才能启用。";
    }
    if (action === "regression") {
      return "已记录测试通过：" + rule + "。确认无误后即可启用。";
    }
    if (action === "deprecate") {
      return "已停用：" + rule + "（历史快照保留，规则未被删除）";
    }
    if (action === "delete") {
      return "已删除草稿：" + rule;
    }
    if (action === "baseline") {
      return "已建立回退点。今后可恢复到当前规则状态。";
    }
    return "操作已完成。";
  }

  function statusBadge(label, state) {
    var cls = "status status-" + state;
    return el("span", label, cls);
  }

  function activationState(node) {
    if (node.approval_status === "active" && node.activation_status === "active") {
      return "active";
    }
    return node.activation_status === "deprecated" ? "off" : "pending";
  }

  // ---------- 视图切换 ---------- //
  function showView(name) {
    ["map", "preview", "clients", "proposals"].forEach(function (key) {
      var section = document.getElementById("view-" + key);
      if (section) { section.hidden = key !== name; }
    });
    var tabs = document.querySelectorAll(".tab");
    Array.prototype.forEach.call(tabs, function (tab) {
      if (tab.getAttribute("data-view") === name) {
        tab.setAttribute("aria-current", "page");
      } else {
        tab.removeAttribute("aria-current");
      }
    });
  }

  // ---------- 知识地图 ---------- //
  var currentRuleId = null;

  function renderTree(result) {
    var nodes = result.nodes || [];
    var tree = document.getElementById("map-tree");
    clear(tree);
    if (!nodes.length) {
      tree.appendChild(el("li", "没有匹配的规则。", "hint"));
      return;
    }
    // 分页提示：不静默截断（VIS-010 要求按需加载）
    if (result.total !== undefined) {
      var shown = (result.offset || 0) + nodes.length;
      tree.appendChild(el("li",
        "显示 " + shown + " / 共 " + result.total + " 条"
        + (result.truncated ? "。请使用筛选或搜索缩小范围。" : "。"),
        "hint"));
    }
    nodes.forEach(function (node) {
      var li = document.createElement("li");
      var button = el("button", node.title, "node");
      button.type = "button";
      button.addEventListener("click", function () { selectNode(node.node_id); });
      li.appendChild(button);
      var meta = el("div", null, "tree-row-meta");
      var statusText = approvalStatusLabel(node.approval_status);
      if (node.activation_status === "inactive") { statusText += "，未启用"; }
      meta.appendChild(statusBadge(statusText, activationState(node)));
      meta.appendChild(el("span", label("layer", node.layer), "hint"));
      if (node.layer === "domain") { meta.appendChild(el("span", node.node_id, "technical-id")); }
      // 第二层（大类原则）额外显示覆盖等级：只有它的 summary 是「覆盖等级 X」。
      // 不渲染其它层的 summary——第三层的 summary 是任意长度的审查目标描述，
      // 渲染它会淹没状态信息（VIS-010 首屏不传输所有正文）。
      // VIS-002 要求「正确显示第二层 0 active、9 个实质 candidate 和 EC-10 gap」，
      // 覆盖等级此前只存在于接口载荷里、界面上从不呈现，用户无法区分
      // EC-10（gap）与其余 9 个实质候选。
      if (node.layer === "domain" && node.summary) {
        var level = String(node.summary).replace(/^覆盖等级\s*/, "");
        meta.appendChild(el("span", "覆盖程度：" + label("coverage", level), "hint"));
      }
      li.appendChild(meta);
      var technical = document.createElement("details");
      technical.className = "technical-details";
      technical.appendChild(el("summary", "查看规则编号"));
      technical.appendChild(el("code", node.node_id, "technical-id"));
      li.appendChild(technical);
      tree.appendChild(li);
    });
  }

  function renderDetail(node) {
    document.getElementById("d-id").textContent = node.node_id;
    document.getElementById("d-version").textContent = node.version;
    document.getElementById("d-layer").textContent = label("layer", node.layer);
    document.getElementById("d-approval").textContent = approvalStatusLabel(node.approval_status);
    document.getElementById("d-activation").textContent = label("activation", node.activation_status);
    document.getElementById("d-visibility").textContent = label("visibility", node.body_visibility);
    // 覆盖等级只对第二层（大类原则）有意义；其余层不显示该行（VIS-002）。
    var isDomain = node.layer === "domain";
    document.getElementById("d-coverage-label").hidden = !isDomain;
    var coverageValue = document.getElementById("d-coverage");
    coverageValue.hidden = !isDomain;
    // 详情面板已有「覆盖等级」标签，故去掉 summary 自带的同名前缀，避免重复。
    coverageValue.textContent = isDomain
      ? label("coverage", String(node.summary || "—").replace(/^覆盖等级\s*/, "") || "—")
      : "—";
    // 适用范围（VIS-004 的 `scope`）：接口一直返回 roles / scene_tags / type_ids /
    // domain_codes 四个字段，但界面从不渲染，用户看不到「这条规则适用于什么范围」。
    document.getElementById("d-scope").textContent = scopeText(node);
    document.getElementById("d-sources").textContent = (node.source_refs || []).join(", ") || "—";
    document.getElementById("d-updated").textContent = node.updated_at || "—";
    var note = document.getElementById("d-candidate-note");
    note.hidden = node.body_visibility !== "metadata_only_candidate";
  }

  function renderEdges(edges) {
    var list = document.getElementById("map-edges");
    clear(list);
    if (!edges.length) {
      list.appendChild(el("li", "这条规则没有需要展示的关联规则。", "hint"));
      return;
    }
    edges.forEach(function (edge) {
      var li = document.createElement("li");
      li.appendChild(el("strong", label("edge", edge.edge_kind)));
      li.appendChild(document.createTextNode("："));
      li.appendChild(el("span", edge.to_title || "另一条规则"));
      var details = document.createElement("details");
      details.className = "technical-details";
      details.appendChild(el("summary", "查看关联编号"));
      details.appendChild(el("div", edge.to_id, "technical-id"));
      li.appendChild(details);
      if (edge.status === "broken") {
        li.appendChild(el("span", "关联信息缺失，请维护人员检查。", "warning"));
      }
      list.appendChild(li);
    });
  }

  var DETAIL_FIELDS = ["d-id", "d-version", "d-layer", "d-approval", "d-activation",
                       "d-visibility", "d-scope", "d-sources", "d-updated"];

  function clearDetail() {
    DETAIL_FIELDS.forEach(function (id) {
      document.getElementById(id).textContent = "—";
    });
    document.getElementById("d-coverage-label").hidden = true;
    document.getElementById("d-coverage").hidden = true;
    document.getElementById("d-coverage").textContent = "—";
    document.getElementById("d-candidate-note").hidden = true;
  }

  function showDetailError(message) {
    var box = document.getElementById("map-detail-error");
    box.textContent = message;
    box.hidden = false;
  }

  function selectNode(ruleId) {
    currentRuleId = ruleId;
    // 先把三个面板清空再请求：请求失败时必须**空着**，不能把上一个节点的
    // 内容留在面板里——那会让提示行写着本节点 ID、详情却显示另一个节点，
    // 把 A 的数据标成 B 的详情。全局文档节点（node_id 含 `/`）曾因此 404。
    clearDetail();
    clear(document.getElementById("map-edges"));
    document.getElementById("map-detail-error").hidden = true;

    var hint = document.getElementById("map-graph-hint");
    hint.textContent = "正在读取所选规则的关联信息……";

    call("GET", "/api/v1/rules/" + encodeURIComponent(ruleId)).then(function (res) {
      if (res.body.success) {
        renderDetail(res.body.result);
      } else {
        var code = (res.body.error && res.body.error.code) || "请求失败";
        showDetailError("无法加载该节点详情（" + code + "）。面板已清空，未显示其它节点的内容。");
      }
    });
    call("GET", "/api/v1/rules/" + encodeURIComponent(ruleId) + "/neighbors")
      .then(function (res) {
        if (res.body.success) {
          renderEdges(res.body.result.edges);
        } else {
          var code = (res.body.error && res.body.error.code) || "请求失败";
          document.getElementById("map-graph-hint").textContent =
            "无法加载所选规则的关联信息（" + code + "）。";
        }
      });
  }

  function loadTree() {
    var layer = document.getElementById("map-layer").value;
    var params = [];
    if (layer) { params.push("layer=" + encodeURIComponent(layer)); }
    var query = params.length ? "?" + params.join("&") : "";
    call("GET", "/api/v1/rules/tree" + query + (query ? "&" : "?") + "limit=50").then(function (res) {
      if (res.body.success) { renderTree(res.body.result); }
    });
  }

  function doSearch() {
    var q = document.getElementById("map-search").value.trim();
    if (!q) { loadTree(); return; }
    call("GET", "/api/v1/rules/search?q=" + encodeURIComponent(q) + "&limit=50").then(function (res) {
      if (res.body.success) { renderTree(res.body.result); }
    });
  }

  // ---------- 运行预览 ---------- //
  var contractTypeChoices = {};
  var typeSceneDefaults = {
    "type-equity-transfer": "",
    "type-equipment-material-procurement": "equipment_purchase",
    "type-employee-confidentiality": "confidentiality",
    "type-noncompete": "noncompete",
    "type-employment-mutual-termination": "mutual_termination",
    "type-general-consulting-service": "",
    "type-property-venue-lease": "handover",
    "type-catalog-abe9bdc8c200506c93cd": "handover",
    "type-catalog-dfd7bd98afd650ff925c": "handover"
  };

  function syncPreviewContext() {
    var select = document.getElementById("p-type");
    var item = contractTypeChoices[select.value];
    if (!item) { return; }
    document.getElementById("p-domain").value = item.domain_code;
    document.getElementById("p-domain-name").textContent = item.domain_name;
    document.getElementById("p-scene").value = typeSceneDefaults[item.type_id] || "";
    document.getElementById("presale-permit-field").hidden = item.domain_code !== "EC-08";
  }

  function loadContractTypes() {
    return call("GET", "/api/v1/catalog/contract-types").then(function (res) {
      var select = document.getElementById("p-type");
      var ruleSelect = document.getElementById("r-type-friendly");
      clear(select);
      clear(ruleSelect);
      contractTypeChoices = {};
      if (!res.body.success) {
        select.appendChild(el("option", "读取合同类型失败"));
        ruleSelect.appendChild(el("option", "读取合同类型失败"));
        document.getElementById("preview-status").textContent = errorText(res.body, "读取合同类型失败：");
        return;
      }
      res.body.result.contract_types.forEach(function (item) {
        contractTypeChoices[item.type_id] = item;
        var option = document.createElement("option");
        option.value = item.type_id;
        option.textContent = item.type_name + "（" + item.domain_name + "）";
        select.appendChild(option);
        ruleSelect.appendChild(option.cloneNode(true));
      });
      if (contractTypeChoices["type-equipment-material-procurement"]) {
        select.value = "type-equipment-material-procurement";
        ruleSelect.value = "type-equipment-material-procurement";
      }
      syncPreviewContext();
      syncRuleFriendlyScope();
    });
  }

  function ruleDisplayName(rule) {
    var payload = rule.payload || rule.rule_payload || {};
    return payload.title || payload.review_objective || payload.name || "合同审查规则";
  }

  function appendRuleItem(list, rule, reason) {
    var li = document.createElement("li");
    li.appendChild(el("span", ruleDisplayName(rule), "rule-title"));
    if (reason) { li.appendChild(el("div", reason, "rule-reason")); }
    var details = document.createElement("details");
    details.className = "technical-details";
    details.appendChild(el("summary", "查看技术信息"));
    details.appendChild(el("div", "规则编号：" + (rule.rule_id || "—"), "technical-id"));
    if (rule.source_layer) {
      details.appendChild(el("div", "规则来源：" + label("layer", rule.source_layer), "technical-id"));
    }
    li.appendChild(details);
    list.appendChild(li);
  }

  function renderResolution(result) {
    var effective = document.getElementById("preview-effective");
    var excluded = document.getElementById("preview-excluded");
    var trace = document.getElementById("preview-trace");
    clear(effective); clear(excluded); clear(trace);

    (result.effective_rules || []).forEach(function (rule) {
      appendRuleItem(effective, rule, rule.inclusion_reason);
    });
    if (!(result.effective_rules || []).length) {
      effective.appendChild(el("li", "没有生效规则。", "hint"));
    }

    (result.excluded_rules || []).forEach(function (rule) {
      appendRuleItem(excluded, rule, rule.reason);
    });
    if (!(result.excluded_rules || []).length) {
      excluded.appendChild(el("li", "没有被排除的规则。", "hint"));
    }

    (result.rule_conflicts || []).forEach(function (conflict) {
      var li = document.createElement("li");
      li.appendChild(el("span", label("conflict", conflict.code || "CONFLICT"), "warning"));
      li.appendChild(el("div", conflict.detail || conflict.kind || "", "hint"));
      var details = document.createElement("details");
      details.className = "technical-details";
      details.appendChild(el("summary", "查看技术信息"));
      details.appendChild(el("div", "内部提示代码：" + (conflict.code || "CONFLICT"), "technical-id"));
      li.appendChild(details);
      trace.appendChild(li);
    });
    if (!(result.rule_conflicts || []).length) {
      trace.appendChild(el("li", "没有发现需要特别处理的规则冲突。", "hint"));
    }

    var status = document.getElementById("preview-status");
    status.textContent = "规则覆盖情况：" + label("coverage", result.coverage_level)
      + "。" + (result.coverage_notice || "");
    document.getElementById("preview-confirm").hidden = !result.human_confirmation_required;
  }

  // ---------- 客户规则：草稿编辑器与生命周期 ---------- //
  // 契约「律师 UAT」要求律师在浏览器里、不碰终端、不编辑 JSON 走完：
  // 新建尾款规则 → 保存并确认未生效 → 审批 / 回归 / 发布 → 比较 → 识别来源 →
  // 触发硬边界 → 回滚并确认恢复。此前面板只有「建档案 + 只读草稿列表」，
  // 第 3~5、8~9 步根本无法完成。
  var currentProfileId = null;
  var currentRuleId = null;
  var loadedDraft = null;
  var clientNames = {};

  function lcLine(text, isWarning) {
    var box = document.getElementById("lc-status");
    box.textContent = text || "";
    box.className = isWarning ? "warning" : "hint";
  }

  function splitList(value) {
    return String(value || "").split(",").map(function (s) { return s.trim(); })
      .filter(function (s) { return s.length > 0; });
  }

  function formValue(id) {
    return document.getElementById(id).value.trim();
  }

  function syncRuleValueHelp() {
    var target = document.getElementById("r-target").value;
    var input = document.getElementById("r-value");
    var help = document.getElementById("r-value-help");
    if (target === "output.draft_finalization") {
      help.textContent = "请填写“允许”或“不允许”。涉及法律边界时，系统仍会暂停并提示律师判断。";
      input.placeholder = "允许／不允许";
      if (/^[0-9.]+$/.test(input.value)) { input.value = "不允许"; }
    } else {
      help.textContent = "请直接填写尾款比例数字，例如 10。";
      input.placeholder = "例如：10";
      if (input.value === "允许" || input.value === "不允许") { input.value = "10"; }
    }
  }

  /**
   * 律师只选中文合同类型、我方身份和阶段；内部编号由界面自动填写。
   * 技术字段仍保留在折叠区，便于排查和处理少数多范围规则。
   */
  function syncRuleFriendlyScope() {
    var typeId = document.getElementById("r-type-friendly").value;
    var item = contractTypeChoices[typeId];
    if (item) {
      document.getElementById("r-types").value = item.type_id;
      document.getElementById("r-domains").value = item.domain_code;
      document.getElementById("r-scenes").value = typeSceneDefaults[item.type_id] || "";
    }
    document.getElementById("r-roles").value = document.getElementById("r-role-friendly").value;
    document.getElementById("r-stages").value = document.getElementById("r-stage-friendly").value;
  }

  function localId(prefix) {
    return prefix + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 10);
  }

  function evidenceId() {
    var input = document.getElementById("lc-evidence");
    var value = input.value.trim();
    if (!value) {
      value = localId("ev_local_");
      input.value = value;
    }
    return value;
  }

  function updateLifecycleProgress() {
    var order = ["draft", "candidate", "lawyer_approved", "regression_passed", "active"];
    var status = loadedDraft ? loadedDraft.approval_status : null;
    var current = status ? order.indexOf(status) : -1;
    ["draft", "submit", "approve", "regression", "publish"].forEach(function (name, index) {
      var step = document.getElementById("step-" + name);
      step.classList.remove("is-done", "is-current");
      if (current > index) { step.classList.add("is-done"); }
      else if (current === index) { step.classList.add("is-current"); }
    });
  }

  function updateLifecycleLabel() {
    var label = document.getElementById("lc-selected");
    if (!currentRuleId) {
      label.textContent = "请先在上方选择或新建一条规则。";
      updateLifecycleProgress();
      return;
    }
    var status = loadedDraft ? approvalStatusLabel(loadedDraft.approval_status) : "（未载入）";
    label.textContent = "当前规则：" + ((loadedDraft && loadedDraft.title) || "未命名规则")
      + " · " + status;
    updateLifecycleProgress();
  }

  function fillRuleForm(draft) {
    loadedDraft = draft;
    currentRuleId = draft.client_rule_id || null;
    document.getElementById("r-id").value = draft.client_rule_id || "";
    document.getElementById("r-title").value = draft.title || "";
    document.getElementById("r-version").value = draft.version || "1.0.0";
    document.getElementById("r-kind").value = draft.rule_kind || "requirement";
    document.getElementById("r-normative").value = draft.normative_level || "mandatory";
    var scope = draft.scope || {};
    document.getElementById("r-domains").value = (scope.domain_codes || []).join(",");
    document.getElementById("r-types").value = (scope.type_ids || []).join(",");
    document.getElementById("r-roles").value = (scope.roles || []).join(",");
    document.getElementById("r-scenes").value = (scope.scene_tags || []).join(",");
    document.getElementById("r-stages").value = (scope.contract_stages || []).join(",");
    document.getElementById("r-groups").value = (scope.clause_groups || []).join(",");
    var cond = draft.condition || {};
    document.getElementById("r-cond-mode").value = cond.mode || "all";
    var effect = draft.effect || {};
    document.getElementById("r-action").value = effect.action || "require";
    document.getElementById("r-target").value = effect.target_key || "";
    document.getElementById("r-value").value =
      effect.value === null || effect.value === undefined ? ""
        : (effect.value === true ? "允许" : (effect.value === false ? "不允许" : String(effect.value)));
    document.getElementById("r-sources").value = (draft.source_refs || []).join(",");
    var firstType = (scope.type_ids || [])[0];
    if (firstType && contractTypeChoices[firstType]) {
      document.getElementById("r-type-friendly").value = firstType;
    }
    var firstRole = (scope.roles || [])[0];
    if (firstRole && ROLE_LABELS[firstRole]) {
      document.getElementById("r-role-friendly").value = firstRole;
    }
    var firstStage = (scope.contract_stages || [])[0];
    if (["signing", "closing", "termination"].indexOf(firstStage) >= 0) {
      document.getElementById("r-stage-friendly").value = firstStage;
    }
    syncRuleValueHelp();
    document.getElementById("rule-status").textContent =
      "已载入“" + (draft.title || "未命名规则") + "”（第 " + draft.revision + " 次修改）";
    updateLifecycleLabel();
  }

  function clearRuleForm() {
    loadedDraft = null;
    currentRuleId = null;
    ["r-id", "r-title"].forEach(function (id) { document.getElementById(id).value = ""; });
    document.getElementById("r-version").value = "1.0.0";
    document.getElementById("r-kind").value = "requirement";
    document.getElementById("r-normative").value = "mandatory";
    document.getElementById("r-action").value = "require";
    document.getElementById("r-type-friendly").value = "type-equipment-material-procurement";
    document.getElementById("r-role-friendly").value = "buyer";
    document.getElementById("r-stage-friendly").value = "signing";
    document.getElementById("r-target").value = "output.reservation_ratio";
    document.getElementById("r-value").value = "10";
    document.getElementById("r-groups").value = "payment";
    document.getElementById("r-cond-mode").value = "all";
    document.getElementById("r-sources").value = "src-prc-civil-code-2020";
    syncRuleFriendlyScope();
    syncRuleValueHelp();
    document.getElementById("rule-status").textContent = "";
    updateLifecycleLabel();
  }

  /**
   * 由表单构造规则。**保留载入时未被表单编辑的字段**（审批状态、review、revision 等），
   * 否则编辑一条已批准的规则会把它的状态重置回 candidate。
   */
  function ruleFromForm() {
    var ruleId = formValue("r-id");
    if (!ruleId) {
      ruleId = localId("cr_local_");
      document.getElementById("r-id").value = ruleId;
    }
    var base;
    if (loadedDraft && loadedDraft.client_rule_id === ruleId) {
      base = JSON.parse(JSON.stringify(loadedDraft));
    } else {
      base = {
        schema_version: "1.0",
        approval_status: "candidate",
        activation_status: "inactive",
        review: {
          lawyer_approval_evidence_id: null, lawyer_approved_by: null,
          lawyer_approved_at: null, legal_check_status: "not_checked",
          legal_checked_at: null, regression_evidence_ids: [],
        },
      };
    }
    var rawValue = formValue("r-value");
    var value;
    if (rawValue === "") { value = null; }
    else if (rawValue === "true" || rawValue === "允许" || rawValue === "是") { value = true; }
    else if (rawValue === "false" || rawValue === "不允许" || rawValue === "否") { value = false; }
    else { value = isNaN(Number(rawValue)) ? rawValue : Number(rawValue); }
    base.client_rule_id = ruleId;
    base.version = formValue("r-version") || "1.0.0";
    base.client_profile_id = currentProfileId;
    base.title = formValue("r-title");
    base.rule_kind = formValue("r-kind");
    base.normative_level = formValue("r-normative");
    base.scope = {
      applies_to_all: false,
      domain_codes: splitList(formValue("r-domains")),
      type_ids: splitList(formValue("r-types")),
      roles: splitList(formValue("r-roles")),
      scene_tags: splitList(formValue("r-scenes")),
      contract_stages: splitList(formValue("r-stages")),
      clause_groups: splitList(formValue("r-groups")),
    };
    base.condition = {
      mode: formValue("r-cond-mode"), clauses: [],
      human_confirmation_required: false,
    };
    base.effect = { action: formValue("r-action"), target_key: formValue("r-target"), value: value };
    base.source_refs = splitList(formValue("r-sources"));
    return base;
  }

  function saveRuleDraft(event) {
    event.preventDefault();
    if (!currentProfileId) {
      document.getElementById("rule-status").textContent = "请先选择或创建一个客户档案。";
      return;
    }
    var rule = ruleFromForm();
    var isNew = !(loadedDraft && loadedDraft.client_rule_id === rule.client_rule_id);
    var base = "/api/v1/clients/" + encodeURIComponent(currentProfileId);
    var request = isNew
      ? call("POST", base + "/client-rules", { rule: rule })
      : call("POST", base + "/drafts",
             { draft: rule, expected_revision: loadedDraft.revision });
    request.then(function (res) {
      var box = document.getElementById("rule-status");
      if (res.body.success) {
        box.className = "hint";
        box.textContent = (isNew ? "已新建规则草稿。" : "已保存修改。")
          + "当前仍未启用。";
        loadClientDetail(currentProfileId);
      } else {
        box.className = "warning";
        box.textContent = errorText(res.body, isNew ? "新建失败：" : "保存失败：");
      }
    });
  }

  function lifecycleRequest(action) {
    if (!currentProfileId) { lcLine("请先选择客户档案。", true); return; }
    var base = "/api/v1/clients/" + encodeURIComponent(currentProfileId);
    var needsRule = action !== "baseline";
    if (needsRule && !currentRuleId) { lcLine("请先在草稿列表点选一条规则。", true); return; }
    var rulePath = base + "/client-rules/" + encodeURIComponent(currentRuleId || "");
    var guarded = action === "publish" || action === "rollback" || action === "delete";
    if (guarded && !document.getElementById("lc-confirm").checked) {
      lcLine("本操作需要二次确认：请勾选「我确认执行该操作」。", true);
      return;
    }
    var evidence = (action === "approve" || action === "regression") ? evidenceId() : "";
    var spec = {
      submit: { path: rulePath + "/submit", body: {} },
      approve: { path: rulePath + "/approval", body: { evidence_id: evidence } },
      regression: { path: rulePath + "/regression", body: { evidence_id: evidence, passed: true } },
      deprecate: { path: rulePath + "/deprecate", body: {} },
      baseline: { path: base + "/publish-baseline", body: { confirmation: true } },
      delete: { path: base + "/drafts/" + encodeURIComponent(currentRuleId || "") + "/delete",
                body: { confirmation: true } },
    }[action];
    if (!spec) { lcLine("未知操作：" + action, true); return; }

    call("POST", spec.path, spec.body).then(function (res) {
      if (res.body.success) {
        lcLine(lifecycleMessage(action, res.body.result || {}), false);
        loadClientDetail(currentProfileId);
        if (loadedDraft) { loadRuleIntoForm(loadedDraft.client_rule_id); }
      } else {
        lcLine(errorText(res.body, "操作失败（" + action + "）："), true);
      }
    });
  }

  /** 发布：必须携带**当前**生效快照做比较交换，故先读再发。 */
  function publishCurrent() {
    if (!currentProfileId) { lcLine("请先选择客户档案。", true); return; }
    if (!document.getElementById("lc-confirm").checked) {
      lcLine("发布需要二次确认：请勾选「我确认执行该操作」。", true);
      return;
    }
    var base = "/api/v1/clients/" + encodeURIComponent(currentProfileId);
    call("GET", base + "/snapshots").then(function (res) {
      var active = res.body.success ? res.body.result.active_snapshot_id : null;
      call("POST", base + "/publish",
           { confirmation: true, expected_active_snapshot: active })
        .then(function (out) {
          if (!out.body.success) {
            lcLine(errorText(out.body, "发布失败："), true);
            return;
          }
          var result = out.body.result || {};
          var message = "已启用新版客户规则。今后的合同审查将使用本次确认内容。";
          var skipped = result.skipped_drafts || [];
          if (skipped.length) {
            // 发布成功不等于「全都发布了」：未完成审批/回归的草稿没有被包含。
            // 必须点名，否则用户会以为它们也已生效。
            message += "　以下规则尚未完成确认，因此本次没有启用："
              + skipped.map(function (d) {
                  return d.title || "未命名规则";
                }).join("、");
          }
          lcLine(message, skipped.length > 0);
          loadClientDetail(currentProfileId);
        });
    });
  }

  /** 回滚到**上一快照**：目标取自接口返回的 previous_snapshot_id（权威链接），不靠位次。 */
  function rollbackPrevious() {
    if (!currentProfileId) { lcLine("请先选择客户档案。", true); return; }
    if (!document.getElementById("lc-confirm").checked) {
      lcLine("回滚需要二次确认：请勾选「我确认执行该操作」。", true);
      return;
    }
    var base = "/api/v1/clients/" + encodeURIComponent(currentProfileId);
    call("GET", base + "/snapshots").then(function (res) {
      var result = res.body.success ? res.body.result : {};
      if (!result.previous_snapshot_id) {
        lcLine("当前没有可恢复的上一版本。请先建立回退点。", true);
        return;
      }
      call("POST", base + "/rollback",
           { target_snapshot: result.previous_snapshot_id,
             expected_active_snapshot: result.active_snapshot_id })
        .then(function (out) {
          if (out.body.success) {
            lcLine("已恢复到上一版本；刚才启用的客户规则不再生效。", false);
            loadClientDetail(currentProfileId);
          } else {
            lcLine(errorText(out.body, "回滚失败："), true);
          }
        });
    });
  }

  function loadRuleIntoForm(ruleId) {
    call("GET", "/api/v1/clients/" + encodeURIComponent(currentProfileId)
         + "/drafts/" + encodeURIComponent(ruleId))
      .then(function (res) {
        if (res.body.success) {
          fillRuleForm(res.body.result.draft);
        } else {
          document.getElementById("rule-status").textContent =
            errorText(res.body, "载入草稿失败：");
        }
      });
  }

  function loadClients() {
    return call("GET", "/api/v1/clients").then(function (res) {
      if (!res.body.success) {
        // 失败不能静默：此前直接 return，列表保持旧内容且无任何提示。
        document.getElementById("client-status").textContent =
          errorText(res.body, "读取顾问单位失败：");
        return;
      }
      var list = document.getElementById("client-list");
      var select = document.getElementById("p-client");
      clear(list);
      clientNames = {};
      while (select.options.length > 1) { select.remove(1); }
      res.body.result.clients.forEach(function (client) {
        clientNames[client.client_profile_id] = client.display_name;
        var li = document.createElement("li");
        li.appendChild(el("strong", client.display_name));
        li.appendChild(document.createTextNode(" "));
        li.appendChild(statusBadge(client.status === "active" ? "正常使用" : "已停用", client.status === "active" ? "active" : "off"));
        var open = el("button", "管理规则", "node");
        open.type = "button";
        open.addEventListener("click", function () { loadClientDetail(client.client_profile_id); });
        li.appendChild(document.createTextNode(" "));
        li.appendChild(open);
        var details = document.createElement("details");
        details.className = "technical-details";
        details.appendChild(el("summary", "查看档案编号"));
        details.appendChild(el("div", client.client_profile_id, "technical-id"));
        li.appendChild(details);
        list.appendChild(li);

        var option = document.createElement("option");
        option.value = client.client_profile_id;
        option.textContent = client.display_name;
        select.appendChild(option);
      });
      if (!res.body.result.clients.length) {
        list.appendChild(el("li", "尚未创建顾问单位档案。", "hint"));
      }
      if (currentProfileId) {
        document.getElementById("drafts-empty").textContent =
          "正在管理：" + (clientNames[currentProfileId] || "已选客户");
      }
    });
  }

  function loadClientDetail(profileId) {
    currentProfileId = profileId;
    updateLifecycleLabel();
    call("GET", "/api/v1/clients/" + encodeURIComponent(profileId) + "/drafts")
      .then(function (res) {
        var list = document.getElementById("draft-list");
        clear(list);
        document.getElementById("drafts-empty").hidden = false;
        document.getElementById("drafts-empty").textContent =
          "正在管理：" + (clientNames[profileId] || "已选客户");
        if (res.body.success && res.body.result.drafts.length) {
          res.body.result.drafts.forEach(function (draft) {
            var li = document.createElement("li");
            var open = el("button", draft.title || "未命名规则", "node");
            open.type = "button";
            open.addEventListener("click", function () { loadRuleIntoForm(draft.client_rule_id); });
            li.appendChild(open);
            li.appendChild(document.createTextNode(" "));
            li.appendChild(statusBadge(approvalStatusLabel(draft.approval_status), activationState(draft)));
            var details = document.createElement("details");
            details.className = "technical-details";
            details.appendChild(el("summary", "查看技术信息"));
            details.appendChild(el("div", "规则编号：" + draft.client_rule_id, "technical-id"));
            details.appendChild(el("div", "版本：" + draft.version, "technical-id"));
            li.appendChild(details);
            list.appendChild(li);
          });
        } else {
          list.appendChild(el("li", "该客户暂无草稿。", "hint"));
        }
      });
    call("GET", "/api/v1/clients/" + encodeURIComponent(profileId) + "/snapshots")
      .then(function (res) {
        var list = document.getElementById("snapshot-list");
        clear(list);
        if (!res.body.success) { return; }
        if (res.body.result.active_snapshot_id) {
          list.appendChild(el("li", "当前已有一版客户规则正在使用。"));
        } else {
          list.appendChild(el("li", "该客户尚未启用任何专属规则。", "hint"));
        }
        res.body.result.snapshots.forEach(function (snap, index) {
          var li = el("li", "第 " + (index + 1) + " 版 · " + (snap.published_at || "时间未记录"));
          var details = document.createElement("details");
          details.className = "technical-details";
          details.appendChild(el("summary", "查看版本编号"));
          details.appendChild(el("div", snap.snapshot_id, "technical-id"));
          li.appendChild(details);
          list.appendChild(li);
        });
      });
    call("GET", "/api/v1/clients/" + encodeURIComponent(profileId) + "/audit")
      .then(function (res) {
        var list = document.getElementById("audit-list");
        clear(list);
        if (!res.body.success) { return; }
        res.body.result.events.slice(-20).forEach(function (event) {
          var li = document.createElement("li");
          li.appendChild(el("strong", label("event", event.event_kind)));
          li.appendChild(document.createTextNode(" · " + event.recorded_at));
          list.appendChild(li);
        });
        if (!res.body.result.events.length) {
          list.appendChild(el("li", "暂无操作记录。", "hint"));
        }
      });
  }

  // ---------- 公共提案（W5） ---------- //
  function renderProposals(list) {
    var ul = document.getElementById("proposal-list");
    clear(ul);
    if (!list.length) {
      ul.appendChild(el("li", "尚无提案。", "hint"));
      return;
    }
    list.forEach(function (item) {
      var li = document.createElement("li");
      li.appendChild(el("strong", item.title));
      li.appendChild(el("div", label("proposal", item.operation) + " · "
        + label("proposal", item.status) + " · 不会自动生效", "candidate-note"));
      var open = el("button", "查看影响", "node");
      open.type = "button";
      open.addEventListener("click", function () { loadProposalDetail(item.proposal_id); });
      li.appendChild(open);
      var details = document.createElement("details");
      details.className = "technical-details";
      details.appendChild(el("summary", "查看建议编号"));
      details.appendChild(el("div", item.proposal_id, "technical-id"));
      li.appendChild(details);
      ul.appendChild(li);
    });
  }

  function loadProposals() {
    return call("GET", "/api/v1/public-proposals").then(function (res) {
      if (res.body.success) { renderProposals(res.body.result.proposals); }
    });
  }

  function loadProposalDetail(proposalId) {
    document.getElementById("proposal-detail-hint").textContent = "正在读取所选建议……";
    call("GET", "/api/v1/public-proposals/" + encodeURIComponent(proposalId) + "/diff")
      .then(function (res) {
        var ul = document.getElementById("proposal-diff");
        clear(ul);
        if (!res.body.success) { return; }
        var d = res.body.result;
        var fieldLabels = { review_objective: "审查目标", scope: "适用范围", source_refs: "规则依据", version: "版本", approval_status: "审核状态", activation_status: "启用状态", modules: "条款内容" };
        var changed = (d.changed_fields || []).map(function (name) { return fieldLabels[name] || "规则内容"; });
        ul.appendChild(el("li", "预计修改内容：" + (changed.join("、") || "暂无可比较内容")));
        if (d.current) {
          ul.appendChild(el("li", "现行规则状态：" + approvalStatusLabel(d.current.approval_status)));
        }
        ul.appendChild(el("li", "是否移除现行规则：" + (d.removes_current ? "是" : "否")));
        ul.appendChild(el("li", "生效状态：未生效", "candidate-note"));
      });
    call("GET", "/api/v1/public-proposals/" + encodeURIComponent(proposalId))
      .then(function (res) {
        var ul = document.getElementById("proposal-audit");
        clear(ul);
        if (!res.body.success) { return; }
        var p = res.body.result;
        ul.appendChild(el("li", "预计影响现行规则：" + (((p.impact && p.impact.affected_rule_ids) || []).length) + " 项"));
        ul.appendChild(el("li", "需要重新测试：" + ((p.impact && p.impact.required_regression_ids) || []).length + " 项"));
        ul.appendChild(el("li", "人工复核要求：" + (p.impact && p.impact.human_review_required ? "是" : "否")));
      });
  }

  // ---------- 绑定 ---------- //
  function bind() {
    Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (tab) {
      tab.addEventListener("click", function () {
        var view = tab.getAttribute("data-view");
        showView(view);
        // 切页即刷新该页数据。除了取到最新值，更重要的是：**服务已退出时会被立刻发现**。
        // 否则用户切到一个在上次加载时就已缓存旧数据的页面，看到的是过期内容却毫无提示
        // （本地服务默认空闲 120 秒即退出，而浏览器不会主动察觉）。
        if (view === "clients") { loadClients(); }
        else if (view === "proposals") { loadProposals(); }
        else if (view === "map") { loadTree(); }
      });
    });

    document.getElementById("map-layer").addEventListener("change", loadTree);
    document.getElementById("p-type").addEventListener("change", syncPreviewContext);
    document.getElementById("r-type-friendly").addEventListener("change", syncRuleFriendlyScope);
    document.getElementById("r-role-friendly").addEventListener("change", syncRuleFriendlyScope);
    document.getElementById("r-stage-friendly").addEventListener("change", syncRuleFriendlyScope);
    document.getElementById("r-target").addEventListener("change", syncRuleValueHelp);
    document.getElementById("map-search-btn").addEventListener("click", doSearch);
    document.getElementById("map-search").addEventListener("keydown", function (event) {
      if (event.key === "Enter") { event.preventDefault(); doSearch(); }
    });

    document.getElementById("preview-form").addEventListener("submit", function (event) {
      event.preventDefault();
      var clientId = document.getElementById("p-client").value;
      var context = {
        primary_type_id: document.getElementById("p-type").value.trim(),
        secondary_type_ids: [],
        primary_domain_code: document.getElementById("p-domain").value.trim(),
        our_role: document.getElementById("p-role").value,
        scene_tags: document.getElementById("p-scene").value.split(",").map(function (s) {
          return s.trim();
        }).filter(Boolean),
        classification_status: "high",
        confirmed_domain_code: document.getElementById("p-domain").value.trim(),
        // 合同阶段是作用域的一个维度：规则若限定 contract_stages，此处不传就被判为
        // 「未命中」而排除。此前界面从不发送该字段，于是任何限定阶段的客户规则
        // 都不可能生效——用户会以为规则没保存成功。
        contract_stage: document.getElementById("p-stage").value.trim() || null,
        facts: document.getElementById("presale-permit-field").hidden ? {} : {
          "presale.permit.validity": document.getElementById("p-presale-permit").value || "unverified"
        },
        case_authorizations: [],
        client_profile_id: clientId || null,
        client_policy_snapshot_id: null,
      };
      call("POST", "/api/v1/resolutions/preview", { context: context }).then(function (res) {
        if (res.body.success) {
          renderResolution(res.body.result);
        } else {
          document.getElementById("preview-status").textContent =
            errorText(res.body, "解析失败：");
        }
      });
    });

    var proposalForm = document.getElementById("proposal-form");
    proposalForm.addEventListener("submit", function (event) {
      event.preventDefault();
      var target = document.getElementById("pp-target").value.trim();
      var payload = {
        operation: document.getElementById("pp-op").value,
        layer: "type",
        target_rule_id: target || null,
        title: document.getElementById("pp-title").value.trim(),
        rationale: document.getElementById("pp-rationale").value.trim(),
        source_refs: document.getElementById("pp-sources").value.split(",").map(function (s) {
          return s.trim();
        }).filter(Boolean),
        proposed_rule: { review_objective: "由提案页提交的修改建议" }
      };
      call("POST", "/api/v1/public-proposals", payload).then(function (res) {
        var status = document.getElementById("proposal-status");
        if (res.body.success) {
          status.textContent = "修改建议已保存，正在等待复核；不会自动影响合同审查。";
        } else {
          status.textContent = errorText(res.body, "提案创建失败：");
        }
        return loadProposals();
      });
    });

    document.getElementById("client-form").addEventListener("submit", function (event) {
      event.preventDefault();
      var profileId = document.getElementById("c-id").value.trim();
      if (!profileId) {
        profileId = localId("cp_local_");
        document.getElementById("c-id").value = profileId;
      }
      var displayName = document.getElementById("c-name").value.trim();
      call("POST", "/api/v1/clients",
        { client_profile_id: profileId, display_name: displayName })
        .then(function (res) {
          // 错误必须显示在**发起操作的那个页面**上。此前这里写的是
          // `#preview-status`（运行预览页的元素）——用户在顾问单位页提交失败时
          // 那条消息落在一个不可见的区块里，页面上什么都不显示，
          // 表现为「点了没反应」，且无从知道该改什么。
          var status = document.getElementById("client-status");
          status.textContent = res.body.success
            ? ""
            : errorText(res.body, "创建失败：");
          // 建完档案即选中它，否则「当前客户」仍为空，输了规则也存不进去
          // （编辑器会提示「请先选择或创建一个客户档案」）。
          if (res.body.success) { loadClientDetail(profileId); }
          return loadClients();
        });
    });

    // 规则编辑器与生命周期按钮
    document.getElementById("rule-form").addEventListener("submit", saveRuleDraft);
    document.getElementById("r-clear").addEventListener("click", clearRuleForm);
    ["submit", "approve", "regression", "baseline", "deprecate", "delete"].forEach(function (action) {
      var button = document.getElementById("lc-" + action);
      if (button) {
        button.addEventListener("click", function () { lifecycleRequest(action); });
      }
    });
    document.getElementById("lc-publish").addEventListener("click", publishCurrent);
    document.getElementById("lc-rollback").addEventListener("click", rollbackPrevious);
  }

  document.addEventListener("DOMContentLoaded", function () {
    bind();
    bootstrap()
      .then(function () {
        loadTree();
        loadClients();
        loadContractTypes();
        return loadProposals();
      })
      .catch(function () {
        document.getElementById("session-state").textContent =
          "本地工具连接失败，请关闭本页，再双击启动文件重新打开。";
      });
  });
})();
