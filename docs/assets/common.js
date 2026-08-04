/* Legal SkillHub 公共模块：标签字典 + 工具函数 + 极简 Markdown 渲染 */

const LBL = {
  jur: {china:"中国大陆",us:"美国","us-de":"美国·特拉华","us-ca":"美国·加州","us-ny":"美国·纽约","us-tx":"美国·德州",
    eu:"欧盟",fr:"法国",uk:"英国",de:"德国",jp:"日本",kr:"韩国",sg:"新加坡",hk:"香港",
    br:"巴西",in:"印度",ca:"加拿大",au:"澳大利亚",international:"跨境国际",multi:"多法域",general:"法域中立"},
  dom: {"general-civil":"民商综合","contract-law":"合同法",corporate:"公司商事","investment-ma":"投融资并购",
    securities:"证券资本","banking-finance":"银行金融",insurance:"保险","real-estate":"房地产",construction:"建工基建",
    ip:"知识产权","data-privacy":"数据隐私","ai-tech-law":"AI与科技法",labor:"劳动社保",tax:"税法",antitrust:"反垄断",
    consumer:"消费者",advertising:"广告电商","intl-trade":"国际贸易",environmental:"环境气候","life-sciences":"食药生命",
    administrative:"行政监管",criminal:"刑事","civil-procedure":"民事诉讼","arbitration-adr":"仲裁ADR",bankruptcy:"破产重组",
    family:"家事继承","public-rights":"公益人权","intl-foreign":"涉外国际","legal-profession":"律所职业",
    litigation:"诉讼仲裁","estate-trust":"遗产信托","personal-injury":"人身损害",immigration:"移民",
    medical:"医疗纠纷","education-law":"法律教育",general:"综合"},
  task: {"legal-research":"法律检索","legal-analysis":"法律研究","doc-reading":"文件阅读","contract-work":"合同工作",
    litigation:"诉讼仲裁","due-diligence":"尽职调查",compliance:"合规管理","legal-writing":"法律写作",
    "knowledge-mgmt":"知识管理","client-project":"客户项目",calculation:"计算量化",education:"教学培训",
    translation:"翻译本地化","quality-control":"质量控制",automation:"自动化"},
  role: {lawyer:"律师",paralegal:"律师助理","in-house":"法务","compliance-officer":"合规人员",judiciary:"司法人员",
    "gov-legal":"政府法制",executive:"公司管理者",hr:"人力资源",investor:"投资人员",scholar:"研究人员",
    student:"法学师生",public:"普通公众"},
  ind: {finance:"金融",insurance:"保险","real-estate":"房地产",construction:"建筑",manufacturing:"制造",energy:"能源",
    internet:"互联网",ai:"人工智能",healthcare:"医疗医药",education:"教育",retail:"消费零售",ecommerce:"电商",
    government:"政府","professional-services":"专业服务",general:"综合"},
  src: {tencent:"腾讯SkillHub",yuanli:"元力法律",casemark:"CaseMark","awesome-zh":"AwesomeLegal",unknown:"其他"},
  type: {instruction:"指令型","prompt-template":"模板型",checklist:"清单型",workflow:"工作流型",
    "tool-wrapper":"工具封装","code-package":"代码包","knowledge-pack":"知识包",hybrid:"混合型"},
  auto: {L0:"L0 知识参考",L1:"L1 单次辅助",L2:"L2 结构化工作流",L3:"L3 工具调用",L4:"L4 有限自主"},
  risk: {low:"低风险",medium:"中风险",high:"高风险"},
  verif: {collected:"已收录","metadata-reviewed":"元数据已审","install-verified":"安装已验证",
    "sample-tested":"示例已运行","legal-reviewed":"法律已审核"},
  lic: {"apache-2.0":"Apache-2.0",mit:"MIT","mit-0":"MIT-0","cc-by-4.0":"CC-BY-4.0","cc-by-nc":"CC-BY-NC",
    "cc-by-nc-nd-4.0":"CC-BY-NC-ND-4.0","cc-by-nc-sa-4.0":"CC-BY-NC-SA-4.0","agpl-3.0":"AGPL-3.0",
    "gpl-3.0":"GPL-3.0",proprietary:"专有许可","declared-only":"仅声明",undeclared:"未声明"},
  in: {"nl-question":"自然语言",contract:"合同","litigation-doc":"诉讼文书",judgment:"判决书",statute:"法规",
    evidence:"证据材料","corporate-doc":"公司文件",spreadsheet:"表格",pdf:"PDF",docx:"Word",xlsx:"Excel",
    image:"图片",webpage:"网页",batch:"批量文件"},
  out: {"research-report":"研究报告",memo:"备忘录","legal-opinion":"法律意见书","contract-draft":"合同条款",
    "review-report":"审查意见",redline:"红线稿","risk-list":"风险清单","dd-report":"尽调报告",
    "litigation-doc":"诉讼文书","evidence-list":"证据目录",timeline:"时间线",issues:"争议焦点",
    "case-summary":"案例摘要","statute-list":"法规清单","compliance-report":"合规报告",checklist:"检查表",
    calculation:"计算结果","data-table":"数据表格",json:"JSON",slides:"演示文稿",letter:"函件",advice:"操作建议"},
};

function lbl(dim, slug) {
  if (slug == null) return "";
  return (LBL[dim] && LBL[dim][slug]) || slug;
}

/* ── 数据源 ── */
let _cfg = null;
async function siteConfig() {
  if (_cfg) return _cfg;
  _cfg = await fetch("data/site-config.json").then(r => r.json());
  return _cfg;
}
const MIRRORS = {
  raw: (c, path) => `https://raw.githubusercontent.com/${c.owner}/${c.repo}/${c.branch}/${path}`,
  jsdelivr: (c, path) => `https://cdn.jsdelivr.net/gh/${c.owner}/${c.repo}@${c.branch}/${path}`,
};
let _mirror = localStorage.getItem("lsh-mirror") || "raw";
function getMirror() { return _mirror; }
function setMirror(m) { _mirror = m; localStorage.setItem("lsh-mirror", m); }
async function mirrorUrl(path) {
  const c = await siteConfig();
  return MIRRORS[_mirror](c, path);
}

async function fetchText(url, timeout = 15000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeout);
  try {
    const r = await fetch(url, {signal: ctrl.signal});
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.text();
  } finally { clearTimeout(t); }
}
/* 带镜像降级的文件抓取；本地开发时（从仓库根目录起服务）走相对路径 ../skills/ */
async function fetchSkillFile(path) {
  const host = location.hostname;
  if (host === "localhost" || host === "127.0.0.1") {
    const localPath = path.startsWith("skills/") ? "../" + path : path;
    return await fetchText(localPath);
  }
  const c = await siteConfig();
  try {
    return await fetchText(MIRRORS[_mirror](c, path));
  } catch (e) {
    const alt = _mirror === "raw" ? "jsdelivr" : "raw";
    return await fetchText(MIRRORS[alt](c, path));
  }
}

/* ── 极简 Markdown 渲染（覆盖本项目常见语法） ── */
function escHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function inlineMd(s) {
  s = escHtml(s);
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  return s;
}
function renderMd(src) {
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const out = [];
  let i = 0, inCode = false, codeBuf = [], inFrontmatter = false;
  // 跳过 frontmatter
  if (lines[0] && lines[0].trim() === "---") {
    i = 1;
    while (i < lines.length && lines[i].trim() !== "---") i++;
    i++;
  }
  let listType = null, tableBuf = [];
  const closeList = () => { if (listType) { out.push(`</${listType}>`); listType = null; } };
  const flushTable = () => {
    if (tableBuf.length < 2) { tableBuf.forEach(r => out.push(`<p>${inlineMd(r)}</p>`)); tableBuf = []; return; }
    const rows = tableBuf.filter(r => !/^\s*\|[\s:|-]+\|\s*$/.test(r));
    if (!rows.length) { tableBuf = []; return; }
    let html = "<table>";
    rows.forEach((r, idx) => {
      const cells = r.replace(/^\s*\|/, "").replace(/\|\s*$/, "").split("|").map(c => inlineMd(c.trim()));
      const tag = idx === 0 ? "th" : "td";
      html += `<tr>${cells.map(c => `<${tag}>${c}</${tag}>`).join("")}</tr>`;
    });
    out.push(html + "</table>");
    tableBuf = [];
  };
  for (; i < lines.length; i++) {
    const line = lines[i];
    if (/^```/.test(line.trim())) {
      if (inCode) {
        out.push(`<pre><code>${escHtml(codeBuf.join("\n"))}</code></pre>`);
        codeBuf = []; inCode = false;
      } else { closeList(); flushTable(); inCode = true; }
      continue;
    }
    if (inCode) { codeBuf.push(line); continue; }
    if (/^\s*\|.*\|\s*$/.test(line)) { closeList(); tableBuf.push(line); continue; }
    flushTable();
    const hm = line.match(/^(#{1,4})\s+(.*)$/);
    if (hm) { closeList(); const lv = hm[1].length; out.push(`<h${lv}>${inlineMd(hm[2])}</h${lv}>`); continue; }
    if (/^\s*>\s?/.test(line)) { closeList(); out.push(`<blockquote>${inlineMd(line.replace(/^\s*>\s?/, ""))}</blockquote>`); continue; }
    if (/^\s*[-*+]\s+/.test(line)) {
      if (listType !== "ul") { closeList(); out.push("<ul>"); listType = "ul"; }
      out.push(`<li>${inlineMd(line.replace(/^\s*[-*+]\s+/, ""))}</li>`); continue;
    }
    if (/^\s*\d+[.)]\s+/.test(line)) {
      if (listType !== "ol") { closeList(); out.push("<ol>"); listType = "ol"; }
      out.push(`<li>${inlineMd(line.replace(/^\s*\d+[.)]\s+/, ""))}</li>`); continue;
    }
    if (/^\s*$/.test(line)) { closeList(); continue; }
    closeList();
    out.push(`<p>${inlineMd(line)}</p>`);
  }
  closeList(); flushTable();
  return out.join("\n");
}

/* ── 复制按钮 ── */
function bindCopy(scope) {
  (scope || document).querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const pre = btn.closest(".cmd-block").querySelector("pre");
      navigator.clipboard.writeText(pre.innerText).then(() => {
        btn.textContent = "已复制 ✓"; btn.classList.add("done");
        setTimeout(() => { btn.textContent = "复制"; btn.classList.remove("done"); }, 1500);
      });
    });
  });
}

/* ── 页头页脚 ── */
function renderHeader(active) {
  return `<header class="site-header">
    <div class="logo">legal_skillhub<span class="cursor">▊</span></div>
    <nav class="site-nav">
      <a href="./index.html" ${active === "home" ? 'class="active"' : ""}>技能库</a>
      <a href="./learn/index.html" ${active === "learn" ? 'class="active"' : ""}>学习中心</a>
      <a href="./about.html" ${active === "about" ? 'class="active"' : ""}>关于</a>
    </nav>
    <div class="header-meta">2049 legal skills · v0.1</div>
  </header>`;
}
function renderFooter() {
  return `<footer class="site-footer">
    <span>© 2026 Legal SkillHub · 法律 Skill 目录、说明书与部署入口</span>
    <a href="./about.html">授权与免责</a>
    <a href="./about.html#takedown">权利人下架联系</a>
  </footer>`;
}
