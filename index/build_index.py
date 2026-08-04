#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index.py — Legal SkillHub 打标管线（T1：程序化 + 信号词；合并 overrides；幂等）

用法：
    python3 index/build_index.py            # 全量构建（Pass1+2 + overrides 合并 + emit）
    python3 index/build_index.py --stats    # 仅打印分布统计

输入：skills/、scratch/master-index.md（来源归因）、index/overrides.json（可选）
输出：index/skills-index.json、index/files.json、index/review-queue.json、
      index/master-index.md、index/stats.md、docs/data/{skills,files,site-config}.json
"""
import json, os, re, sys, hashlib, unicodedata
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
INDEX = os.path.join(ROOT, "index")
DOCS_DATA = os.path.join(ROOT, "docs", "data")
MASTER = os.path.join(ROOT, "scratch", "master-index.md")
OVERRIDES_PATH = os.path.join(INDEX, "overrides.json")

SCHEMA_VERSION = "0.1"

# ═══════════════════════════ 1. frontmatter 容错解析 ═══════════════════════════

def parse_frontmatter(text):
    """容错解析 YAML frontmatter。返回 dict（name/description/license/language/tags/version/author/metadata）。
    兼容：单行、`>`/`>-`/`|`/`|` 多行、内联数组、块列表、两层嵌套 metadata、
    前置标题（frontmatter 不在文件开头但在前 600 字符内）。"""
    m = re.match(r"^﻿?---\s*\n(.*?)\n---", text, re.S)
    if not m:
        # 兼容前置标题：在前 600 字符内找 --- 块
        m = re.search(r"\n---\s*\n(.*?)\n---", text[:600], re.S)
    if not m:
        return {}
    block = m.group(1)
    lines = block.split("\n")
    out, meta = {}, {}
    i = 0
    while i < len(lines):
        line = lines[i]
        km = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if not km:
            i += 1
            continue
        key, val = km.group(1), km.group(2)
        if key == "metadata":
            # 两层嵌套：读取缩进子键
            i += 1
            while i < len(lines) and re.match(r"^\s+\S", lines[i]):
                sm = re.match(r"^\s+([A-Za-z_-]+):\s*(.*)$", lines[i])
                if sm:
                    meta[sm.group(1)] = _clean_scalar(sm.group(2))
                i += 1
            continue
        if val in (">", ">-", ">+", "|", "|-", "|+"):
            # 多行块：收集缩进行
            buf = []
            i += 1
            while i < len(lines) and (lines[i].startswith(" ") or lines[i].startswith("\t") or lines[i].strip() == ""):
                if re.match(r"^\S", lines[i]):
                    break
                buf.append(lines[i])
                i += 1
            sep = "\n" if val.startswith("|") else " "
            out[key] = _unquote(sep.join(x.strip() for x in buf).strip())
            continue
        if val == "" and i + 1 < len(lines) and re.match(r"^\s+-\s+", lines[i + 1]):
            # 块列表
            items = []
            i += 1
            while i < len(lines) and re.match(r"^\s+-\s+(.*)$", lines[i]):
                items.append(_unquote(re.match(r"^\s+-\s+(.*)$", lines[i]).group(1).strip()))
                i += 1
            out[key] = items
            continue
        out[key] = _clean_scalar(val)
        i += 1
    if meta:
        out["metadata"] = meta
    return out

def _clean_scalar(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_unquote(x.strip()) for x in inner.split(",") if x.strip()]
    return _unquote(v)

def _unquote(v):
    v = v.strip().strip("\\").strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v.strip()

# ═══════════════════════════ 2. 来源归因 ═══════════════════════════

def load_source_map():
    """从 scratch/master-index.md 解析 folder → 来源。表格行：| # | `folder` | name | desc | files | source |"""
    src = {}
    if not os.path.exists(MASTER):
        return src
    for line in open(MASTER, encoding="utf-8"):
        m = re.match(r"\|\s*\d+\s*\|\s*`([^`]+)`\s*\|.*\|.*\|.*\|\s*([^|]+?)\s*\|$", line)
        if m:
            folder, source = m.group(1), m.group(2).strip()
            src[folder] = source
    return src

SOURCE_MAP = {
    "腾讯SkillHub": "tencent", "元力法律": "yuanli",
    "AgentSkills.Legal": "casemark", "AwesomeLegalSkills(zh)": "awesome-zh",
}
SOURCE_DEFAULT_LICENSE = {"casemark": "apache-2.0", "awesome-zh": "cc-by-nc-nd-4.0"}

# ═══════════════════════════ 3. 语言检测 ═══════════════════════════

def detect_language(text):
    head = text[:4000]
    cjk = sum(1 for ch in head if "一" <= ch <= "鿿")
    return "zh-CN" if cjk > 40 else "en"

# ═══════════════════════════ 4. license 检测 ═══════════════════════════

LICENSE_SNIFF = [
    (r"Apache License", "apache-2.0"),
    (r"MIT License", "mit"),
    (r"GNU AFFERO GENERAL PUBLIC LICENSE", "agpl-3.0"),
    (r"GNU GENERAL PUBLIC LICENSE", "gpl-3.0"),
    (r"Attribution-NonCommercial-NoDerivatives", "cc-by-nc-nd-4.0"),
    (r"Attribution-NonCommercial-ShareAlike", "cc-by-nc-sa-4.0"),
    (r"Attribution-NonCommercial", "cc-by-nc"),
    (r"Attribution 4\.0 International", "cc-by-4.0"),
]

def norm_license(v):
    if not v:
        return None
    v = str(v).strip().strip("\\").strip().strip('"').strip("'").lower()
    v = v.replace(" ", "-").replace("_", "-")
    table = {
        "mit": "mit", "mit-0": "mit-0", "apache-2.0": "apache-2.0", "apache": "apache-2.0",
        "apache-license-2.0": "apache-2.0", "agpl-3.0": "agpl-3.0", "gpl-3.0": "gpl-3.0",
        "gpl-3.0-only": "gpl-3.0", "cc-by-4.0": "cc-by-4.0", "cc-by": "cc-by-4.0",
        "cc-by-nc": "cc-by-nc", "cc-by-nc-4.0": "cc-by-nc",
        "cc-by-nc-nd": "cc-by-nc-nd-4.0", "cc-by-nc-nd-4.0": "cc-by-nc-nd-4.0",
        "cc-by-nc-sa": "cc-by-nc-sa-4.0", "cc-by-nc-sa-4.0": "cc-by-nc-sa-4.0",
        "proprietary": "proprietary", "commercial": "proprietary",
    }
    return table.get(v, "declared-only")

def detect_license(folder_path, fm, source):
    # 1. LICENSE 文件嗅探
    for name in ("LICENSE", "LICENSE.txt", "LICENSE.md", "license"):
        p = os.path.join(folder_path, name)
        if os.path.exists(p):
            head = open(p, encoding="utf-8", errors="replace").read(3000)
            for pat, lic in LICENSE_SNIFF:
                if re.search(pat, head):
                    return lic
            return "declared-only"
    # 2. frontmatter 顶层 license
    lic = norm_license(fm.get("license"))
    if lic:
        return lic
    # 3. metadata.license 嵌套
    lic = norm_license((fm.get("metadata") or {}).get("license"))
    if lic:
        return lic
    # 4. 集合默认
    if source in SOURCE_DEFAULT_LICENSE:
        return SOURCE_DEFAULT_LICENSE[source]
    return "undeclared"

def lbl_task(slug):
    m = {"legal-research":"法律检索","legal-analysis":"法律研究","doc-reading":"文件阅读","contract-work":"合同工作",
    "litigation":"诉讼仲裁","due-diligence":"尽职调查","compliance":"合规管理","legal-writing":"法律写作",
    "knowledge-mgmt":"知识管理","client-project":"客户项目","calculation":"计算量化","education":"教学培训",
    "translation":"翻译本地化","quality-control":"质量控制","automation":"自动化"}
    return m.get(slug, "法律")

def license_risk(lic):
    if lic in ("mit", "mit-0", "apache-2.0", "cc-by-4.0"):
        return "open"
    if lic in ("agpl-3.0", "gpl-3.0"):
        return "copyleft"
    if lic and lic.startswith("cc-by-nc"):
        return "restrictive-nc"
    if lic == "proprietary":
        return "restrictive-nc"
    return "undeclared"

# ═══════════════════════════ 5. 结构探测 ═══════════════════════════

def probe_structure(folder_path):
    info = {"files": [], "has_scripts": False, "has_references": False,
            "has_assets": False, "has_license": False, "n_scripts": 0, "n_refs": 0}
    for root, dirs, fs in os.walk(folder_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in fs:
            if f.startswith("."):
                continue
            rel = os.path.relpath(os.path.join(root, f), folder_path)
            info["files"].append(rel)
    info["files"].sort()
    top = os.listdir(folder_path)
    info["has_scripts"] = "scripts" in top and os.path.isdir(os.path.join(folder_path, "scripts"))
    info["has_references"] = "references" in top and os.path.isdir(os.path.join(folder_path, "references"))
    info["has_assets"] = "assets" in top and os.path.isdir(os.path.join(folder_path, "assets"))
    info["has_license"] = any(f.startswith("LICENSE") or f == "license" for f in top if os.path.isfile(os.path.join(folder_path, f)))
    info["n_scripts"] = sum(1 for f in info["files"] if f.startswith("scripts/"))
    info["n_refs"] = sum(1 for f in info["files"] if f.startswith("references/"))
    return info

def skill_type_of(st):
    strong = 0
    t = "instruction"
    if st["n_scripts"] >= 1:
        strong += 1
        t = "code-package"
    if st["n_refs"] >= 3:
        strong += 1
        t = "knowledge-pack" if t == "instruction" else t
    if st["has_assets"]:
        strong += 1
        if t == "instruction":
            t = "prompt-template"
    if strong >= 2:
        return "hybrid"
    if st["n_scripts"] >= 1 and st["n_refs"] == 0:
        return "tool-wrapper"
    return t

def complexity_of(nfiles):
    if nfiles <= 1:
        return "S"
    if nfiles <= 10:
        return "M"
    if nfiles <= 30:
        return "L"
    return "XL"

def quality_of(st, desc):
    q = 0
    q += 1 if st["has_references"] else 0
    q += 1 if st["has_scripts"] else 0
    q += 1 if st["has_license"] else 0
    q += 1 if len(desc) >= 100 else 0
    q += 1 if len(st["files"]) >= 4 else 0
    return q

# ═══════════════════════════ 6. 信号词典 ═══════════════════════════

# 法域：w3 具名法律 / w2 机构专名 / w1 通用词
JUR_SIGNALS = {
    "china": {
        3: ["民法典", "劳动合同法", "个人信息保护法", "数据安全法", "网络安全法", "广告法", "法释〔", "刑事诉讼法", "民事诉讼法", "行政处罚法", "发明专利", "实用新型", "外观设计专利", "招标投标"],
        2: ["最高人民法院", "最高人民检察院", "国务院", "仲裁委员会", "劳动人事争议仲裁", "北大法宝", "威科先行", "指导案例", "法答网", "国家法律法规数据库", "国家知识产权局", "CNIPA", "市场监督管理局"],
        1: ["人民法院", "中国法院", "中国法律", "中国大陆", "检察院"]},
    "fr": {
        3: ["Code civil", "Code de commerce", "assignation en référé", "assignation en refere", "RGPD"],
        2: ["Judilibre", "Légifrance", "Conseil d'État", "Cour de cassation", "tribunal judiciaire", "tribunal de commerce", "-selim-brihi", "-amaury-fouret", "-christophe-quezel-ambrunaz"],
        1: ["tribunal", "法国"]},
    "eu": {
        3: ["GDPR", "AI Act", "MiCA", "NIS2", "DORA", "ePrivacy", "Data Act", "人工智能条例"],
        2: ["EDPB", "EMA", "European Commission", "Standard Contractual Clauses", "DPO", "CNIL"],
        1: ["欧盟", "European Union", "EU/EEA", "European"]},
    "us": {
        3: ["FRCP", "FRBP", "U.S.C.", "C.F.R.", "HIPAA", "CCPA", "CPRA", "Title VII", "OWBPA", "DTSA", "SOX", "Sarbanes-Oxley", "30(b)(6)", "Section 501(c)", "Reg D", "Form D", "ERISA", "FMLA", "NLRA", "FDCPA", "RESPA", "TILA", "DoD", "DD Form"],
        2: ["SEC", "EEOC", "FinCEN", "IRS", "FDA", "FTC", "OFAC", "Delaware", "Bluebook", "Restatement", "Federal Rules", "ALTA", "California"],
        1: ["U.S.", "United States", "federal court", "state law", "American"]},
    "uk": {2: ["England and Wales", "UK GDPR", "Companies Act"], 1: ["United Kingdom", "England", "Wales", "British", "UK"]},
    "de": {2: ["BGB", "Bundesgericht", "German Civil Code"], 1: ["Germany", "German", "德国"]},
    "jp": {2: ["Japanese law", "Japan"], 1: ["Japanese", "日本"]},
    "kr": {2: ["law.go.kr", "Korean law"], 1: ["韩国", "Korea"]},
    "sg": {2: ["Singapore law"], 1: ["Singapore", "新加坡"]},
    "br": {3: ["LGPD"], 1: ["Brazil", "巴西"]},
    "in": {3: ["DPDP"], 1: ["India", "印度"]},
    "ca": {1: ["Canada", "Canadian", "加拿大"]},
    "au": {1: ["Australia", "Australian", "澳大利亚"]},
    "hk": {2: ["Hong Kong law", "HKIAC"], 1: ["Hong Kong", "香港"]},
    "international": {
        3: ["UNCITRAL", "New York Convention", "CISG", "WTO"],
        2: ["跨境数据", "数据出境", "cross-border data", "international treaty"],
        1: ["cross-border", "跨境"]},
}
JUR_PRIORITY = ["china", "fr", "eu", "us", "uk", "de", "jp", "kr", "sg", "br", "in", "ca", "au", "hk", "international"]
# 全大写短词需大小写敏感+词边界匹配（防 EMA/ADA/UCC/IRC 等误中正常单词）
JUR_CASE_SENSITIVE = {"EMA", "ADA ", "UCC", "IRC", "SEC", "IRS", "FDA", "FTC", "ICC", "AAA", "DoD", "WTO", "DPO", "CNIL", "EDPB", "HKIAC", "BGB", "SOX", "FRCP", "FRBP", "DTSA", "FMLA", "NLRA", "FDCPA", "RESPA", "TILA", "ERISA", "LGPD", "DPDP", "MiCA", "NIS2", "DORA", "HIPAA", "CCPA", "CPRA", "OWBPA", "ALTA", "EAR", "ITAR", "OFAC", "CISG", "GDPR", "RGPD", "UNCITRAL", "CNIPA", "Reg D", "Form D", "AI Act", "UK GDPR", "Title VII", "U.S.C.", "C.F.R.", "30(b)(6)", "Section 501(c)", "DD Form", "Data Act", "ePrivacy", "Bluebook", "Restatement", "FinCEN", "EEOC", "law.go.kr"}

# 领域
DOMAIN_SIGNALS = {
    "contract-law": ["合同", "contract", "agreement", "NDA", "违约", "条款"],
    "litigation": ["诉讼", "litigation", "起诉", "诉状", "complaint", "pleading", "motion", "deposition", "discovery"],
    "arbitration-adr": ["仲裁", "arbitration", "调解", "mediation", "ICC", "AAA", "仲裁委"],
    "corporate": ["公司法", "股权", "股东", "治理", "corporate", "LLC", "incorporation", "bylaws", "并购", "merger", "M&A"],
    "investment-ma": ["PE/VC", "私募", "投资协议", "融资", "investment", "venture", "term sheet", "SPA"],
    "securities": ["证券", "securities", "SEC", "上市", "IPO", "Reg D", "Form D"],
    "banking-finance": ["银行", "信贷", "banking", "AML", "KYC", "FinCEN", "BSA", "金融"],
    "insurance": ["保险", "insurance", "理赔", "保单", "coverage"],
    "real-estate": ["房地产", "不动产", "房产", "real estate", "物业", "租赁", "lease"],
    "construction": ["建设工程", "施工", "建工", "construction", "EPC", "工程"],
    "ip": ["知识产权", "专利", "商标", "著作权", "版权", "patent", "trademark", "copyright", "IP "],
    "data-privacy": ["数据合规", "个人信息", "隐私", "GDPR", "PIPL", "个保法", "data privacy", "data protection", "CCPA", "数据安全"],
    "ai-tech-law": ["AI Act", "人工智能条例", "算法", "AIGC", "AI治理", "AI governance"],
    "labor": ["劳动", "工伤", "社保", "劳动合同", "employment", "labor", "EEOC", "workers comp", "裁员", "辞退"],
    "tax": ["税", "税务", "增值税", "个税", "tax", "IRS", "VAT", "纳税", "发票"],
    "antitrust": ["垄断", "antitrust", "competition", "反垄断"],
    "consumer": ["消费者", "消保", "consumer", "FTC", "虚假宣传"],
    "advertising": ["广告法", "广告合规", "绝对化用语", "advertising", "电商"],
    "intl-trade": ["出口管制", "制裁", "EAR", "ITAR", "OFAC", "海关", "sanctions", "export control"],
    "environmental": ["环境", "环保", "环评", "EPA", "NEPA", "EIR", "CEQA", "environmental"],
    "life-sciences": ["FDA", "药品", "医疗器械", "510(k)", "clinical", "pharma", "医药"],
    "administrative": ["行政处罚", "行政许可", "行政复议", "行政法", "administrative"],
    "criminal": ["刑事", "量刑", "辩护", "criminal", "取保候审", "会见"],
    "civil-procedure": ["民诉", "管辖", "执行", "FRCP", "保全", "civil procedure"],
    "bankruptcy": ["破产", "重整", "清算", "bankruptcy", "Chapter 7", "Chapter 11"],
    "family": ["婚姻", "离婚", "继承", "遗嘱", "抚养", "divorce", "custody", "family law", "estate"],
    "immigration": ["移民", "immigration", "visa", "asylum"],
    "estate-trust": ["信托", "trust", "estate planning", "probate", "遗嘱信托"],
    "personal-injury": ["人身损害", "personal injury", "negligence", "tort", "交通事故"],
    "medical": ["医疗纠纷", "medical malpractice", "病历"],
    "education-law": ["法考", "司法考试", "刷题", "quiz"],
    "legal-profession": ["律所", "律师管理", "计费", "billing", "law firm"],
}

# 任务
TASK_SIGNALS = {
    "legal-research": ["检索", "法条", "案例检索", "类案", "search", "法答网", "引证"],
    "legal-analysis": ["法律研究", "分析", "research", "analysis", "memo", "法律意见"],
    "doc-reading": ["摘要", "提取", "summary", "extract", "时间线", "阅卷", "chronology"],
    "contract-work": ["合同", "contract", "起草", "审查", "红线", "draft", "review"],
    "litigation": ["诉讼", "起诉", "答辩", "上诉", "litigation", "庭审", "证据"],
    "due-diligence": ["尽调", "due diligence", "背景调查"],
    "compliance": ["合规", "compliance", "监管"],
    "legal-writing": ["意见书", "律师函", "备忘录", "letter", "memo", "函件"],
    "calculation": ["计算", "calculator", "赔偿", "利息", "诉讼费"],
    "education": ["法考", "刷题", "quiz", "培训", "教学", "考试"],
    "translation": ["翻译", "translation", "术语"],
    "quality-control": ["核查", "verify", "校验", "审校"],
    "client-project": ["谈案", "报价", "计费", "billing", "客户管理"],
    "knowledge-mgmt": ["知识库", "模板库", "归档"],
}

# 角色
ROLE_SIGNALS = {
    "lawyer": ["律师", "lawyer", "attorney", "counsel", "律所"],
    "in-house": ["法务", "in-house", "legal department", "企业法务"],
    "compliance-officer": ["合规官", "合规人员", "compliance officer"],
    "judiciary": ["法官", "judge", "仲裁员", "arbitrator", "法院"],
    "hr": ["HR", "人力资源", "人事"],
    "investor": ["投资", "investor", "PE", "VC"],
    "student": ["法学生", "法考", "student"],
    "public": ["当事人", "公众", "consumer", "个人"],
    "executive": ["老板", "高管", "executive", "management"],
}

# 输入
INPUT_SIGNALS = {
    "contract": ["合同", "contract", "协议", "agreement"],
    "litigation-doc": ["起诉状", "答辩状", "上诉状", "诉状", "pleading"],
    "judgment": ["判决书", "裁判文书", "judgment", "裁决"],
    "pdf": ["PDF", "pdf"],
    "docx": ["Word", "docx", "DOCX", "word"],
    "xlsx": ["Excel", "xlsx", "表格"],
    "image": ["图片", "image", "截图", "扫描件"],
    "webpage": ["网页", "URL", "链接", "webpage"],
    "evidence": ["证据", "evidence", "材料"],
    "batch": ["批量", "batch", "文件夹", "多份"],
    "nl-question": ["提问", "咨询", "问答", "question"],
}

# 输出
OUTPUT_SIGNALS = {
    "research-report": ["研究报告", "research report"],
    "memo": ["备忘录", "memo"],
    "legal-opinion": ["法律意见书", "legal opinion", "意见书"],
    "review-report": ["审查报告", "审查意见", "review report", "风险报告"],
    "redline": ["红线", "redline", "修订稿", "批注"],
    "risk-list": ["风险清单", "risk list", "风险点"],
    "litigation-doc": ["起诉状", "答辩状", "上诉状", "代理词", "诉讼文书"],
    "checklist": ["清单", "checklist", "检查表"],
    "calculation": ["计算结果", "计算书", "赔偿金额"],
    "letter": ["函件", "letter", "律师函", "邮件"],
    "data-table": ["表格", "table", "Excel"],
    "json": ["JSON", "json", "结构化"],
    "slides": ["PPT", "演示", "slides"],
    "timeline": ["时间线", "timeline", "chronology"],
    "evidence-list": ["证据目录", "证据清单", "evidence list"],
    "case-summary": ["案例摘要", "case summary"],
    "advice": ["建议", "advice", "策略", "行动方案"],
    "contract-draft": ["合同文本", "合同草稿", "协议文本"],
}

# ═══════════════════════════ 7. 信号打分 ═══════════════════════════

def score_signals(text, signals, case_sensitive=False):
    """返回 {key: score}。text 已按 weight 分段加权由调用方处理——此处简单计数。"""
    flags = re.IGNORECASE if not case_sensitive else 0
    scores = {}
    for key, words in signals.items():
        if isinstance(words, dict):
            continue  # 法域单独处理
        s = 0
        for w in words:
            if re.search(re.escape(w), text, flags):
                s += 1
        if s:
            scores[key] = s
    return scores

def pick_top(scores, cap, min_score=2, dominance=0.5):
    """取得分 ≥min_score 且 ≥dominance×max 的，按分数排序，cap 上限。"""
    if not scores:
        return []
    mx = max(scores.values())
    cands = [(k, v) for k, v in scores.items() if v >= min_score and v >= dominance * mx]
    cands.sort(key=lambda x: -x[1])
    return [k for k, _ in cands[:cap]]

def _sig_hit(word, text):
    """信号匹配：全大写短词/专名大小写敏感+词边界；其余 IGNORECASE 子串。"""
    if word in JUR_CASE_SENSITIVE:
        return bool(re.search(r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])", text))
    return bool(re.search(re.escape(word), text, re.IGNORECASE))

def score_jurisdiction(text, lang):
    """法域加权打分 + 优先级链 + multi 判定 + 冲突检测。
    返回 (tags, confidence, conflict)；conflict=True 时进复核队列。"""
    scores = {}
    for jur, levels in JUR_SIGNALS.items():
        s = 0
        for w, words in levels.items():
            for word in words:
                if _sig_hit(word, text):
                    s += w
        if s:
            scores[jur] = s
    if not scores:
        # 无信号：中文回退 china（推定 medium），英文 general（low 但不排队）
        if lang == "zh-CN":
            return (["china"], "medium", False)
        return (["general"], "low", False)
    mx = max(scores.values())
    # 冲突检测：≥2 个国家组得分接近（差 ≤1）→ 进复核
    country_scores = {j: s for j, s in scores.items() if j != "international"}
    conflict = False
    if len(country_scores) >= 2:
        top2 = sorted(country_scores.values(), reverse=True)[:2]
        if top2[0] - top2[1] <= 1 and top2[1] >= 1:
            conflict = True
    # 优先级链：≥3 分入选
    picked = [j for j in JUR_PRIORITY if scores.get(j, 0) >= 3][:4]
    if not picked:
        picked = [max(scores, key=scores.get)]
    # multi：≥2 个国家组各 ≥4
    strong = [j for j, s in country_scores.items() if s >= 4]
    if len(strong) >= 2 and "multi" not in picked:
        picked.append("multi")
    conf = "high" if mx >= 5 else ("medium" if mx >= 2 else "low")
    return picked[:4], conf, conflict

# ═══════════════════════════ 8. 其他程序化判定 ═══════════════════════════

def detect_freshness(text):
    return bool(re.search(r"(202[4-6])\s*年", text) or re.search(r"\b(202[4-6])\b.{0,30}(Act|Regulation|修订|修正|施行|公告)", text[:6000]))

def detect_data_security(folder_path, st):
    perms = set()
    if st["n_scripts"]:
        for f in st["files"]:
            if f.startswith("scripts/") and f.endswith((".py", ".sh", ".js")):
                try:
                    code = open(os.path.join(folder_path, f), encoding="utf-8", errors="replace").read(8000)
                except Exception:
                    continue
                if re.search(r"requests\.|urllib|httpx|fetch\(|curl", code):
                    perms.add("network")
                if re.search(r"open\([^)]*['\"]w|\.write\(|fs\.write", code):
                    perms.add("file-write")
                if re.search(r"subprocess|os\.system|exec\(", code):
                    perms.add("shell")
                if re.search(r"api_key|API_KEY|apikey|token", code, re.I):
                    perms.add("api-call")
    perms.add("file-read")
    return {"processing": "local-external-model" if "network" in perms or "api-call" in perms else "local",
            "permissions": sorted(perms)}

# ═══════════════════════════ 9. 主流程 ═══════════════════════════

def load_overrides():
    if os.path.exists(OVERRIDES_PATH):
        try:
            return json.load(open(OVERRIDES_PATH, encoding="utf-8"))
        except Exception:
            return {}
    return {}

def build():
    src_map = load_source_map()
    overrides = load_overrides()
    folders = sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)) and not d.startswith("."))
    records, files_map, review_queue = [], {}, []
    parse_errors = []

    for folder in folders:
        fp = os.path.join(SKILLS, folder)
        st = probe_structure(fp)
        files_map[folder] = st["files"]

        md_path = None
        for fn in ("SKILL.md", "skill.md"):
            if os.path.exists(os.path.join(fp, fn)):
                md_path = os.path.join(fp, fn)
                break
        if not md_path:
            # 一层子目录兜底（元力个别 skill 嵌套一层中文目录）
            for sub in os.listdir(fp):
                cand = os.path.join(fp, sub, "SKILL.md")
                if os.path.isdir(os.path.join(fp, sub)) and os.path.exists(cand):
                    md_path = cand
                    break

        raw, fm = "", {}
        if md_path:
            try:
                raw = open(md_path, encoding="utf-8", errors="replace").read()
                fm = parse_frontmatter(raw)
            except Exception as e:
                parse_errors.append({"folder": folder, "error": str(e)[:100]})

        name = fm.get("name") or folder
        desc = fm.get("description") or ""
        if isinstance(desc, list):
            desc = " ".join(str(x) for x in desc)
        desc = re.sub(r"\s+", " ", str(desc)).strip()
        if not desc and raw:
            # 兜底：取正文首个有效段落（跳过标题/frontmatter/图片/分隔线）
            body = re.sub(r"^﻿?---\s*\n.*?\n---", "", raw, count=1, flags=re.S)
            for para in re.split(r"\n\s*\n", body):
                para = para.strip()
                if para and not para.startswith(("#", "!", "---", "<", "```")) and len(para) > 20:
                    desc = re.sub(r"\s+", " ", re.sub(r"[*`>\[\]#]", "", para)).strip()[:200]
                    break
        author = fm.get("author") or (fm.get("metadata") or {}).get("author") or None
        version = str(fm.get("version") or (fm.get("metadata") or {}).get("version") or "") or None
        src_tags = fm.get("tags") if isinstance(fm.get("tags"), list) else []

        source_label = src_map.get(folder, "未标注（待考）")
        source = SOURCE_MAP.get(source_label, "tencent" if source_label == "腾讯SkillHub" else "unknown")
        lic = detect_license(fp, fm, source)
        lang = detect_language(raw)
        text_sig = (name + " " + desc + " " + raw[:2000])

        # ── 法域 ──
        jur, jur_conf, jur_conflict = score_jurisdiction(text_sig, lang)
        # ── 领域 ──
        dom_scores = score_signals(text_sig, DOMAIN_SIGNALS)
        domains = pick_top(dom_scores, 3, min_score=2) or ["general"]
        dom_conf = "high" if dom_scores and max(dom_scores.values()) >= 4 else ("medium" if domains[0] != "general" else "low")
        # ── 任务 ──
        task_scores = score_signals(text_sig, TASK_SIGNALS)
        # CaseMark tags 折算
        TAGMAP = {"drafting": "contract-work", "litigation": "litigation", "agreement": "contract-work",
                  "transactional": "contract-work", "regulatory": "compliance", "analysis": "legal-analysis",
                  "summary": "doc-reading", "summarization": "doc-reading", "research": "legal-research",
                  "pleading": "litigation", "motion": "litigation", "brief": "litigation",
                  "letter": "legal-writing", "memo": "legal-writing", "checklist": "quality-control"}
        for t in src_tags:
            mapped = TAGMAP.get(str(t).lower())
            if mapped:
                task_scores[mapped] = task_scores.get(mapped, 0) + 1
        tasks = pick_top(task_scores, 3, min_score=2) or ["legal-analysis"]
        # ── 角色 ──
        roles = pick_top(score_signals(text_sig, ROLE_SIGNALS), 2, min_score=1) or ["lawyer"]
        # ── 输入/输出 ──
        inputs = pick_top(score_signals(text_sig, INPUT_SIGNALS), 3, min_score=1)
        if not inputs:
            inputs = ["nl-question"]
        outputs = pick_top(score_signals(text_sig, OUTPUT_SIGNALS), 3, min_score=1)
        if not outputs:
            outputs = ["advice"]
        # ── 行业 ──
        IND = {"finance": ["金融", "银行", "finance"], "insurance": ["保险", "insurance"],
               "real-estate": ["房地产", "房产", "real estate"], "construction": ["建筑", "施工", "建设"],
               "healthcare": ["医疗", "医药", "healthcare", "pharma"], "internet": ["互联网", "电商", "网店"],
               "ai": ["人工智能", "AI", "AIGC"], "government": ["政府", "政务", "公安", "交警"],
               "education": ["教育", "考试", "法考"], "professional-services": ["律所", "律师"]}
        industries = pick_top(score_signals(text_sig, IND), 2, min_score=1) or ["general"]

        lic_risk = license_risk(lic)
        ds = detect_data_security(fp, st)
        stype = skill_type_of(st)

        rec = {
            "schema_version": SCHEMA_VERSION,
            "id": folder,
            "folder": folder,
            "name": name,
            "summary": desc[:200] if desc else "",
            "classification": {
                "tasks": {"primary": tasks[0], "secondary": tasks[1:]},
                "areas_of_law": {"primary": domains[0], "secondary": domains[1:]},
                "jurisdictions": jur,
                "multi_jurisdictional": "multi" in jur or len(jur) > 1,
                "user_roles": roles[:2],
                "industries": industries,
            },
            "capabilities": {
                "inputs": inputs,
                "outputs": outputs,
                "automation_level": None,   # T2 LLM 填充
                "method_types": [],
            },
            "skill_type": stype,
            "complexity": complexity_of(len(st["files"])),
            "quality_score": quality_of(st, desc),
            "files_count": len(st["files"]),
            "has": {"scripts": st["has_scripts"], "references": st["has_references"],
                    "assets": st["has_assets"], "license": st["has_license"]},
            "compatibility": {"host_platforms": ["universal-markdown"], "dependencies": []},
            "data_security": ds,
            "risk": {"level": None, "human_review_required": True},   # T2
            "language": lang,
            "provenance": {"source": source, "source_label": source_label,
                           "author": author, "version": version,
                           "collected_at": "2026-08-04",
                           "content_hash": hashlib.sha256(raw.encode()).hexdigest()[:16] if raw else None},
            "license": {"spdx_id": lic, "risk": lic_risk},
            "verification": {"status": "collected"},
            "tags_src": [str(t) for t in src_tags][:10],
            "badges": {"freshness": detect_freshness(raw), "curated": False},
            "logic_summary": None,   # T2
            "use_cases": None,       # T2
            "dependencies": None,    # T2
            "relations": {"alternatives": [], "complements": []},
            "confidence": {"jurisdiction": jur_conf, "area_of_law": dom_conf},
        }

        # ── overrides 合并（优先级最高）──
        ov = overrides.get(folder)
        if ov:
            rec = deep_merge(rec, ov)

        # ── T2 启发式补全（overrides 未填时给默认值，保证全量可展示）──
        if rec["capabilities"].get("automation_level") is None:
            if st["has_scripts"]:
                rec["capabilities"]["automation_level"] = "L3"
            elif st["n_refs"] >= 3:
                rec["capabilities"]["automation_level"] = "L2"
            else:
                rec["capabilities"]["automation_level"] = "L1"
        if rec["risk"].get("level") is None:
            hi_domains = {"litigation", "criminal", "family", "bankruptcy"}
            doms = [rec["classification"]["areas_of_law"]["primary"]] + rec["classification"]["areas_of_law"]["secondary"]
            rec["risk"]["level"] = "high" if set(doms) & hi_domains else "medium"
        if rec.get("logic_summary") is None:
            rec["logic_summary"] = desc[:160] if desc else f"{lbl_task(rec['classification']['tasks']['primary'])}类 Skill。"
        if rec.get("dependencies") is None:
            rec["dependencies"] = ["python3 运行时（含脚本，安装前请审阅 scripts/）"] if st["has_scripts"] else []
        if rec["capabilities"].get("method_types") == []:
            mt = []
            if st["n_refs"] >= 3: mt.append("retrieval-augmented")
            if st["has_scripts"]: mt.append("tool-calling")
            if not mt: mt.append("rule-based")
            rec["capabilities"]["method_types"] = mt

        records.append(rec)

        # ── 复核队列 ──
        reasons = []
        if jur_conflict:
            reasons.append("jurisdiction-conflict")
        if not desc:
            reasons.append("empty-desc")
        if folder in [p["folder"] for p in parse_errors]:
            reasons.append("parse-error")
        if reasons and not ov:
            review_queue.append({"folder": folder, "name": name, "reasons": reasons,
                                 "jur_guess": jur, "dom_guess": domains,
                                 "desc_preview": desc[:120]})

    # ── 输出 ──
    os.makedirs(INDEX, exist_ok=True)
    os.makedirs(DOCS_DATA, exist_ok=True)
    json.dump(records, open(os.path.join(INDEX, "skills-index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(files_map, open(os.path.join(INDEX, "files.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    json.dump(review_queue, open(os.path.join(INDEX, "review-queue.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if parse_errors:
        json.dump(parse_errors, open(os.path.join(INDEX, "parse-errors.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    # 站点数据（裁剪）
    slim = [slim_record(r) for r in records]
    json.dump(slim, open(os.path.join(DOCS_DATA, "skills.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    json.dump(files_map, open(os.path.join(DOCS_DATA, "files.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    if not os.path.exists(os.path.join(DOCS_DATA, "site-config.json")):
        json.dump({"owner": "YOUR_GITHUB_USERNAME", "repo": "legal-skillhub", "branch": "main"},
                  open(os.path.join(DOCS_DATA, "site-config.json"), "w", encoding="utf-8"), indent=1)

    write_master_index(records)
    write_stats(records, review_queue)
    return records, review_queue

def deep_merge(base, ov):
    """overrides 深合并：dict 递归，其他类型直接覆盖。"""
    for k, v in ov.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            base[k] = deep_merge(base[k], v)
        else:
            base[k] = v
    return base

def slim_record(r):
    return {
        "id": r["id"], "name": r["name"], "summary": r["summary"][:200],
        "jur": r["classification"]["jurisdictions"],
        "dom": [r["classification"]["areas_of_law"]["primary"]] + r["classification"]["areas_of_law"]["secondary"],
        "task": [r["classification"]["tasks"]["primary"]] + r["classification"]["tasks"]["secondary"],
        "roles": r["classification"]["user_roles"],
        "ind": r["classification"]["industries"],
        "in": r["capabilities"]["inputs"], "out": r["capabilities"]["outputs"],
        "auto": r["capabilities"]["automation_level"],
        "type": r["skill_type"], "cplx": r["complexity"], "q": r["quality_score"],
        "files": r["files_count"], "has": r["has"], "lang": r["language"],
        "src": r["provenance"]["source"], "lic": r["license"]["spdx_id"], "lrisk": r["license"]["risk"],
        "verif": r["verification"]["status"], "fresh": r["badges"]["freshness"], "cur": r["badges"]["curated"],
        "logic": r.get("logic_summary"), "deps": r.get("dependencies"),
        "risk": r["risk"]["level"],
    }

def write_master_index(records):
    lines = ["# Legal SkillHub 主索引（机器生成，禁手改）", "",
             f"- 总数：**{len(records)} 个 Skill**", "- 标签体系：`index/taxonomy.md` v0.1",
             "- 数据权威：`index/skills-index.json`（本文件由其渲染）", "",
             "| # | 文件夹 | 简介 | 法域 | 领域 | 任务 | 语言 | 来源 | 授权 |",
             "|---|--------|------|------|------|------|------|------|------|"]
    for i, r in enumerate(records, 1):
        desc = (r["summary"][:60] + "…" if len(r["summary"]) > 60 else r["summary"]).replace("|", "\\|")
        jur = "/".join(r["classification"]["jurisdictions"])
        dom = r["classification"]["areas_of_law"]["primary"]
        task = r["classification"]["tasks"]["primary"]
        lines.append(f"| {i} | `{r['folder']}` | {desc} | {jur} | {dom} | {task} | {r['language']} | {r['provenance']['source']} | {r['license']['spdx_id']} |")
    open(os.path.join(INDEX, "master-index.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

def write_stats(records, review_queue):
    def dist(keyfn, top=40):
        c = Counter()
        for r in records:
            v = keyfn(r)
            if isinstance(v, list):
                for x in v:
                    c[x] += 1
            else:
                c[v] += 1
        return c.most_common(top)
    lines = ["# Legal SkillHub 统计报告（机器生成）", "",
             f"- 总数：{len(records)}",
             f"- 复核队列：{len(review_queue)} 条", "",
             "## 法域分布", ""]
    for k, v in dist(lambda r: r["classification"]["jurisdictions"]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## 领域分布（主领域）", ""]
    for k, v in dist(lambda r: r["classification"]["areas_of_law"]["primary"]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## 任务分布（主任务）", ""]
    for k, v in dist(lambda r: r["classification"]["tasks"]["primary"]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## 语言分布", ""]
    for k, v in dist(lambda r: r["language"]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## 来源分布", ""]
    for k, v in dist(lambda r: r["provenance"]["source"]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## 授权分布", ""]
    for k, v in dist(lambda r: r["license"]["spdx_id"]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## 技能类型分布", ""]
    for k, v in dist(lambda r: r["skill_type"]):
        lines.append(f"- {k}: {v}")
    lines += ["", "## 置信度（法域）", ""]
    for k, v in dist(lambda r: r["confidence"]["jurisdiction"]):
        lines.append(f"- {k}: {v}")
    open(os.path.join(INDEX, "stats.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

if __name__ == "__main__":
    records, rq = build()
    print(f"完成: {len(records)} 条, 复核队列 {len(rq)} 条")
    if "--stats" in sys.argv:
        print(open(os.path.join(INDEX, "stats.md"), encoding="utf-8").read())
