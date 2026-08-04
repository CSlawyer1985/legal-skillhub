/* 精选案例数据与渲染（外链化：兼容 CSP script-src 'self'，不执行内联脚本） */
(function () {
  const el = document.getElementById("cases");
  if (!el) return;
  const prefix = (document.body.getAttribute("data-prefix") || "./") + "skill.html";
  const cases = [
    { f: "ad-compliance-consumer-rights-review-plus", t: "广告合规审查 Plus（知识库增强型·中国）",
      d: "78 个附属文件承载法答网问答、标签合规锚点——渐进式披露的完整教案。" },
    { f: "legal-research", t: "中国法律研究助手（流程 SOP 型·中国）",
      d: "八阶段工作流 + 元典/Tavily 双检索 + 强制验证闭环，工程化标杆。" },
    { f: "construction-contract-review", t: "施工合同审查（审查清单型·中国）",
      d: "13 维度专业级风险排查，五套标准对照，任务自由度的黄金分割。" },
    { f: "complaint-drafter", t: "要素式起诉状生成（文书模板型·中国）",
      d: "最高法 67 类官方模板上'填空而非重写'，模板保真优先于生成自由。" },
    { f: "30b6-deposition", t: "30(b)(6) 公司代表取证（流程 SOP 型·美国）",
      d: "Part A/B 双线工作流，美国程序法 Skill 的典型结构。" },
    { f: "demand-letter", t: "诉前催告函（文书起草型·美国）",
      d: "element-driven narrative，把诉求要素驱动写入流程。" },
    { f: "analyse-dpa-fournisseur-hugo-salard", t: "DPA 数据处理协议审查（审查清单型·欧盟/法国）",
      d: "RGPD 第 28 条逐条款 18 项诊断 + 可插入救济条款，欧盟合规 Skill 范本。" },
    { f: "ai-governance-reviewer-carl-ditzler", t: "AI 治理审查（知识库增强型·通用）",
      d: "25 文件的审查矩阵，AI 用例/产品/工作流/供应商全覆盖。" },
    { f: "civil-litigation-thinking", t: "民事诉讼思维（角色方法论型·中国）",
      d: "高自由度典范：只给诉讼思维框架，不给僵硬步骤。" },
    { f: "billable-time-stephane-boghossian", t: "计时审计包（工具/合规型·通用）",
      d: "SHA-256 证据链 + 五条硬性拒绝，AI 计费合规防御的开荒设计。" },
  ];
  el.innerHTML = cases.map((c, i) => `
    <a class="learn-item" href="${prefix}?f=${c.f}">
      <span class="num">${String(i + 1).padStart(2, "0")}</span>
      <div><div class="lt">${c.t}</div><div class="ld">${c.d}</div></div>
    </a>`).join("");
})();
