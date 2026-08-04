#!/usr/bin/env python3
"""构建 candidates.jsonl：MP 45篇 + AI+法律 + 法律补充（2026-07-28 周二）"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

# ── 1. 读 MP 文章 ──
mp = json.loads((BASE / "mp_articles.json").read_text())

# ── 2. 特征映射函数 ──

def _detect_author_tier_from_digest(digest):
    """从 digest（通常含法官所属法院）推断 author_tier。
    1=最高法/高级法院法官或知名学者, 2=中级法院法官, 3=基层法院法官。

    中国应用法学接受各级法院法官投稿，不能按来源硬编码 tier。
    """
    if not digest:
        return None
    # 最高法/高院
    if any(k in digest for k in ["最高人民法院", "高级人民法院"]):
        return 1
    # 中院
    if "中级人民法院" in digest:
        return 2
    # 基层（县/区法院、人民法庭）
    if any(k in digest for k in ["基层人民法院", "县人民法院", "区人民法院", "人民法庭"]):
        return 3
    # 其他中院变体（如"铁路运输中级法院"）
    if "中级法院" in digest:
        return 2
    return None


def classify_legal(title, source, digest=""):
    """v3 七维分类器（2026-07-28）。

    返回 features dict 包含七维 + 老四维兼容键。
    """
    t = title
    d = digest or ""
    features = {}

    # ── 案例密度 case_density (1-3) ──
    case_kw_1 = ["入库案例", "裁判要旨", "多元解纷案例库"]
    case_kw_2 = ["案例", "诉", "被告人", "原告", "被告", "判了", "法院判", "判决"]
    if any(k in t for k in case_kw_1):
        features["case_density"] = 1
    elif any(k in t for k in case_kw_2):
        features["case_density"] = 2
    else:
        features["case_density"] = 3  # 无案例

    # ── 规范锚定 norm_anchoring (1-3) ──
    norm_kw_1 = ["入库案例", "司法解释", "法释", "民法典", "公司法", "刑法", "劳动法",
                 "合同编", "物权编", "侵权编", "婚姻家庭编", "继承编"]
    norm_kw_2 = ["法条", "条文", "规定", "条例", "法规", "法律", "解释", "修改", "决定"]
    # 来源优先：最高法/最高检的直接发布 = 最高规范锚定
    if "最高法" in source or "最高人民法" in source or "最高检" in source:
        features["norm_anchoring"] = 1
    # 官方发布体（"发布《关于...》"）→ 规范锚定
    elif "发布" in t and "关于" in t:
        features["norm_anchoring"] = 1
    elif any(k in t for k in norm_kw_1):
        features["norm_anchoring"] = 1
    elif any(k in t for k in norm_kw_2):
        features["norm_anchoring"] = 2
    else:
        features["norm_anchoring"] = 3

    # ── 可操作性 actionability (1-3) ──
    act_kw_1 = ["裁判规则", "审理思路", "审查路径", "认定与责任", "认定与处理",
                "认定与效力", "能否", "如何认定", "处理规则", "审查认定"]
    act_kw_2 = ["分析", "探析", "辨析", "研究", "解读", "指南"]
    if any(k in t for k in act_kw_1):
        features["actionability"] = 1
    elif any(k in t for k in act_kw_2):
        features["actionability"] = 2
    else:
        features["actionability"] = 3

    # ── 作者实证深度 author_empirical_depth (1-3) ──
    # 来源层
    if source in ("上海一中法院", "上海一中院") or source == "上海二中院":
        base_author = 2
    elif source == "中国应用法学":
        tier = _detect_author_tier_from_digest(d)
        base_author = tier if tier is not None else 2
    elif source == "山东高法":
        base_author = 2
    else:
        base_author = 3

    # 至正系列提升
    if "至正" in t:
        base_author = max(1, base_author - 1)
    # 入库案例作者权威
    if "入库案例" in t:
        base_author = 1

    features["author_empirical_depth"] = base_author

    # ── 框架定性 framework_quality (1-3) ──
    fw_kw_1 = ["审理思路", "审查路径", "认定与责任", "体系", "框架", "规则探析",
               "理解与适用", "裁判规则", "司法认定", "合同僵局", "司法终止"]
    fw_kw_2 = ["分析", "探析", "辨析", "研究"]
    if any(k in t for k in fw_kw_1):
        features["framework_quality"] = 1
    elif any(k in t for k in fw_kw_2):
        features["framework_quality"] = 2
    elif "法官办案心得" in t:
        features["framework_quality"] = 2  # 心得类通常有分析结构
    else:
        features["framework_quality"] = 3

    # ── 时效半衰期 relevance_halflife (1-3) ──
    # 1=基础方法永不过时, 2=中期价值, 3=前沿快过时
    halflife_1_kw = ["合同", "侵权", "婚姻", "继承", "物权", "债权", "担保",
                     "劳动", "工伤", "交通事故", "保险", "借贷", "赔偿",
                     "执行", "管辖", "时效", "定金", "违约", "留置",
                     "夫妻", "离婚", "抚养", "遗嘱", "赠与", "物业",
                     "股权", "股东", "公司", "工程", "施工"]
    halflife_3_kw = ["AI", "人工智能", "生成式", "数据", "算法", "平台",
                     "虚拟", "数字", "网络", "众筹", "电子", "区块链",
                     "加密货币", "元宇宙"]
    if any(k in t for k in halflife_1_kw):
        features["relevance_halflife"] = 1
    elif any(k in t for k in halflife_3_kw):
        features["relevance_halflife"] = 3
    else:
        features["relevance_halflife"] = 2

    # ── 地域管辖贴近度 jurisdictional_proximity (0/1) ──
    jp_kw = ["浙江", "金华", "永康", "义乌", "东阳", "兰溪", "武义", "浦江", "磐安",
             "浙江省", "浙中", "金华中院", "婺城", "金东"]
    if any(k in d for k in jp_kw) or any(k in t for k in jp_kw):
        features["jurisdictional_proximity"] = 1
    else:
        features["jurisdictional_proximity"] = 0

    # ── 老四维（保留兼容，权重已置 0）──
    features["author_tier"] = base_author
    if source in ("上海一中法院", "上海一中院") or source == "上海二中院":
        features["platform_tier"] = 3
    elif source == "中国应用法学":
        features["platform_tier"] = 3
    elif source == "山东高法":
        features["platform_tier"] = 4
    else:
        features["platform_tier"] = 4
    features["depth"] = features["framework_quality"]  # 近似映射
    features["relevance"] = 2 if features["relevance_halflife"] <= 2 else 3

    # ── 至正系列后处理：至正=上海二中院品牌栏目，质量锚定高 ──
    if "至正" in t:
        features["author_empirical_depth"] = 1       # 审级高+论证深
        features["norm_anchoring"] = min(features["norm_anchoring"], 2)  # 至少引法条
        features["actionability"] = min(features["actionability"], 2)    # 至少可提炼
        features["framework_quality"] = min(features["framework_quality"], 1)  # 框架清晰

    return features


# ── 3. 构建 MP 法律候选 ──
candidates = []
skip_keywords = ["暑期安全", "青训营", "破茧", "点赞", "开讲", "周末人物", "入选！全国法院文化建设"]

for a in mp:
    source = a["_source"]
    title = a["title"]
    url = a["url"]
    digest = a.get("digest", "")
    pub_time = a.get("publish_time", "")

    if any(k in title for k in skip_keywords):
        continue

    features = classify_legal(title, source, digest)

    abstract = digest if digest else f"{source} {pub_time}发布的实务文章"
    enriched_abstract = f"【{source}】{title}（{pub_time}）"
    if digest:
        enriched_abstract += f"\n{digest}"

    ref_map = {1: "直接对标永康实务", 2: "有一定参考价值", 3: "泛资讯"}
    depth_map = {1: "体系化深度分析", 2: "有具体案例与分析", 3: "资讯/新闻"}
    case_map = {1: "有入库案例/裁判要旨", 2: "有案例但无细节", 3: "无具体案例"}
    norm_map = {1: "锚定入库案例/司法解释", 2: "有法条引用", 3: "无规范锚定"}

    recommend_parts = []
    # v3 维度 → 推荐理由
    if features.get("case_density") == 1:
        recommend_parts.append(case_map[1])
    if features.get("norm_anchoring") == 1:
        recommend_parts.append(norm_map[1])
    if features.get("author_empirical_depth") == 1:
        recommend_parts.append("审级高+论证深")
    elif features.get("author_empirical_depth") == 2:
        recommend_parts.append("有实证论证")
    if features.get("jurisdictional_proximity") == 1:
        recommend_parts.append("浙江/金华法官·预判价值")
    if features.get("actionability") == 1:
        recommend_parts.append("可直用裁判规则")
    if features.get("relevance_halflife") == 1:
        recommend_parts.append("基础方法·永不过时")
    recommend = "·".join(recommend_parts) if recommend_parts else "一般参考"

    candidates.append({
        "title": title, "url": url, "category": "legal",
        "source": source, "publish_time": pub_time,
        "abstract": enriched_abstract, "recommend": recommend,
        "features": features,
    })

# ── 4. AI+法律候选 ──
ai_legal = [
    {
        "title": "2026 WAIC法律科技论坛: 智合AI 3.0全国首发·星火晓法超级智能体·法律大模型部署指引出台",
        "url": "https://new.qq.com/rain/a/20260720A08RFS00",
        "category": "ai-legal", "source": "WAIC/科大讯飞/智合",
        "publish_time": "2026-07-18",
        "abstract": "2026 WAIC法律科技论坛集中发布6大成果: ①智合AI 3.0(法律智能本体+Skill中心+数字法务); ②全国首部《法律服务领域大模型部署应用指引》; ③讯飞星火晓法超级智能体面世; ④AI+调解推广计划启动(上海五区试点满意率95%+); ⑤《世界人工智能法治蓝皮书(2026)》《上海法律科技应用年度观察报告》发布; ⑥法律科技信用融资'智法融'发布; ⑦'模法境'可信算力空间共建倡议。",
        "recommend": "格局级: WAIC年度法律科技风向标, 国家首部法律大模型指引+讯飞晓法+智合3.0同台, 上海六项成果定义行业方向",
        "features": {"signal_strength": 1, "depth": 1, "relevance": 1, "domestic_relevance": 1}
    },
    {
        "title": "慧多宝法律AI荣获WAIC法律科技产品大赛一等奖 + 入选法律科技先锋",
        "url": "https://ex.chinadaily.com.cn/exchange/partners/82/rss/channel/cn/columns/sz8srm/stories//WS6a605816a310d709c2fbefb3.html",
        "category": "ai-legal", "source": "慧多宝/中国日报",
        "publish_time": "2026-07-20",
        "abstract": "慧多宝法律AI在WAIC法律科技产品大赛斩获一等奖(综合赛道), 同期入选《2026年度法律科技先锋》。产品覆盖案件分析·长文写作·深度研究·PE/VC尽调等核心工作流, Pre-A轮获金沙江创投/浦东创投支持。朱啸虎表示'看好真正能把事情做完、把结果交付出来的AI产品'。",
        "recommend": "格局级: WAIC综合赛道一等奖, PE/VC尽调+案件分析全流程AI, 金沙江朱啸虎背书",
        "features": {"signal_strength": 1, "depth": 2, "relevance": 1, "domestic_relevance": 1}
    },
    {
        "title": "Norm AI $120M C轮达$1.2B估值: 以结果定价模式挑战按小时计费, Blackstone/Khosla领投",
        "url": "https://valueaddvc.com/blog/norm-ai-120m-series-c-1-2b-valuation-legal-ai-unicorn",
        "category": "ai-legal", "source": "Norm AI/ValueAddVC",
        "publish_time": "2026-07-12",
        "abstract": "Norm AI完成$120M C轮(Khosla领投, Blackstone/Bain/Coatue/Vanguard参投), 估值$1.2B。旗下Norm Law以结果定价替代按小时计费, 从Kirkland/Paul Weiss/Skadden等律所挖来资深合伙人。已服务$30T+ AUM客户。与Harvey($11B)·Legora($5.6B)三足鼎立, 但Norm选择直接挑战传统计费模式。",
        "recommend": "格局级: 法律AI独角兽三足鼎立, Norm以结果定价破局, 银弹级监管合规Agent+律所双重模式, 国内律所商业模式变革参考",
        "features": {"signal_strength": 1, "depth": 1, "relevance": 2, "domestic_relevance": 0}
    },
    {
        "title": "讯飞星火晓法超级智能体落地上海: 全栈自研+全国产算力, 已覆盖上海900个法庭",
        "url": "https://www.toutiao.com/article/7665185496402018859",
        "category": "ai-legal", "source": "科大讯飞/IT时报",
        "publish_time": "2026-07-22",
        "abstract": "科大讯飞发布星火晓法超级智能体。上海法律科技总部已落地, 产品覆盖上海全部900个法庭的语音笔录系统。面向行政复议案件提供智能化阅卷、案情分析、审查效率提升。采用三重可信体系守住法律AI容错率底线。规划: 全栈自研国产算力; 以上海为样板普惠下沉; 共建开放生态。",
        "recommend": "格局级: 科大讯飞法律科技全国总部上海落地, 900法庭全覆盖, 全栈国产化可信法律AI路线",
        "features": {"signal_strength": 1, "depth": 1, "relevance": 1, "domestic_relevance": 1}
    },
]

# ── 5. WebSearch 法律补充 ──
web_legal = [
    {
        "title": "两高修改内幕交易司法解释(法释〔2026〕13号) 7月27日起施行",
        "url": "https://www.court.gov.cn/fabu/xiangqing/506981.html",
        "category": "legal", "source": "最高人民法院/最高人民检察院",
        "publish_time": "2026-07-24",
        "abstract": "两高联合发布修改内幕交易司法解释决定: ①明确控股股东/实际控制人内幕信息敏感期(意向初始时间视为动议时间); ②完善内幕交易阻却事由(强化上市公司收购目的审查、预定交易真实性、公开披露标准); ③与新证券法/期货和衍生品法保持协调。自2026年7月27日起施行。",
        "recommend": "司法解释本身就是最高规范锚定·刑事领域非核心方向",
        "features": {"case_density": 3, "norm_anchoring": 1, "actionability": 1, "author_empirical_depth": 1,
                     "framework_quality": 2, "relevance_halflife": 2, "jurisdictional_proximity": 0,
                     "author_tier": 1, "platform_tier": 1, "depth": 1, "relevance": 2}
    },
    {
        "title": "最高法入库案例: 网络众筹商品纠纷中众筹支持者主张出卖人责任的处理规则",
        "url": "https://m.thepaper.cn/newsDetail_forward_32851368",
        "category": "legal", "source": "人民法院案例库",
        "publish_time": "2026-07-27",
        "abstract": "入库案例裁判要旨: ①网络众筹商品合同为非典型合同, 应根据众筹经营模式及宣传内容确定当事人真实目的(投资回报vs商品所有权), 参照最相类似典型合同处理; ②参照买卖合同规定时, 众筹发起者未履行从给付义务致合同目的不能实现, 支持解除合同并承担出卖人责任。入库编号:2026-07-2-088-002。",
        "recommend": "入库案例·有具体裁判要旨·可直用裁判规则",
        "features": {"case_density": 1, "norm_anchoring": 1, "actionability": 1, "author_empirical_depth": 1,
                     "framework_quality": 1, "relevance_halflife": 2, "jurisdictional_proximity": 0,
                     "author_tier": 1, "platform_tier": 1, "depth": 1, "relevance": 2}
    },
]

# ── 合并写入 ──
all_candidates = candidates + web_legal + ai_legal
out = BASE / "candidates.jsonl"

seen = set()
with open(out, "w") as f:
    for c in all_candidates:
        u = c["url"]
        if u in seen:
            continue
        seen.add(u)
        f.write(json.dumps(c, ensure_ascii=False) + "\n")

print(f"总候选写入: {len(seen)} 条 -> {out}")
categories = {}
for c in all_candidates:
    cat = c["category"]
    categories[cat] = categories.get(cat, 0) + 1
for k, v in categories.items():
    print(f"  {k}: {v} 条")
