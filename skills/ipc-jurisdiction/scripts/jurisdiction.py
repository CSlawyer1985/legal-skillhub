#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""信息网络传播权纠纷 · 一审管辖判定引擎

确定性查表计算，不做任何推理。调用方（AI）负责从案件材料中抽取参数、
解释输出结果并起草文书；本脚本只负责保证「同样的输入永远得到同样的、
可追溯到法条和数据源的结论」。

用法：
    python jurisdiction.py --def-prov 浙江省 --def-city 杭州市 --def-district 西湖区 --amount 800000
    python jurisdiction.py --help
    python jurisdiction.py --selftest

输出：JSON（默认）或 --text 人类可读格式。
"""

import argparse
import json
import os
import re
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# 该省级别管辖标准未收录时的通用推定阈值（元）
GENERIC_BASIC = 1_000_000


def _load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


COURTS = _load("courts.json")
DIVISIONS = _load("divisions.json")
PROVINCES = _load("provinces.json")
SPECIAL = _load("special_courts.json")

BASIS_VENUE = "《最高人民法院关于审理侵害信息网络传播权民事纠纷案件适用法律若干问题的规定》（法释〔2020〕19号）第15条"


# ---------- 名称归一化 ----------

def norm_city(s):
    return re.sub(r"市$", "", (s or "").strip()).strip()


def norm_area(s):
    return re.sub(
        r"(经济技术开发区|高新技术产业开发区|经济开发区|开发区|新区|街道办事处|街道|镇|区|县|市|盟|地区)$",
        "", (s or "").strip()).strip()


def area_hit(a, q):
    """法院辖区名 a 是否命中查询地名 q。宽松匹配，容忍行政区划后缀差异。"""
    if not q:
        return False
    na, nq = norm_area(a), norm_area(q)
    if a == q or a.find(q) >= 0 or q.find(a) >= 0:
        return True
    if na and nq:
        if na == nq:
            return True
        if len(na) > 1 and nq.find(na) >= 0:
            return True
        if len(nq) > 1 and na.find(nq) >= 0:
            return True
    return False


def inter_name(x):
    """由地级市名推导中院名称。

    自治州、盟、地区的中院名不含「市」（延边朝鲜族自治州中级人民法院）；
    普通地级市则含「市」。注意不能按单字「州」判断——苏州、温州、常州、
    台州、湖州、广州、郑州、福州等均为普通地级市。
    """
    b = re.sub(r"市$", "", (x or "").strip())
    if re.search(r"自治州$|盟$|地区$", b):
        return b + "中级人民法院"
    return b + "市中级人民法院"


def norm_province(s):
    """省级行政区名归一化。接受「浙江」「内蒙古」这类口语简称，无法识别时返回 None。

    省级行政区是固定的 31 个，可以严格校验；错误的省名必须拒绝，
    不能像市县那样降级处理——否则会凭空编出「某某市有知产管辖权的基层人民法院」。
    """
    s = (s or "").strip()
    if not s:
        return None
    if s in PROVINCES:
        return s
    for suf in ("省", "市"):
        if s + suf in PROVINCES:
            return s + suf
    for p in PROVINCES:                      # 内蒙古/广西/西藏/宁夏/新疆等自治区简称
        if p.startswith(s) and ("自治区" in p or "特别行政区" in p):
            return p
    return None


def place_known(province, city, district):
    """城市/区县名是否出现在本省行政区划表中。

    用于区分「地名写错了」与「地名对但辖区表未收录」。直辖市在映射表中
    没有条目，一律视为已知，避免误判。
    """
    m = DIVISIONS.get(province)
    if not m:
        return True
    parents = set(m.values())
    for q in (city, district):
        if not q:
            continue
        if q in m or q in parents:
            return True
        nq = norm_area(q)
        if any(norm_area(k) == nq for k in m):
            return True
        if any(norm_city(p) == norm_city(q) for p in parents):
            return True
    return False


def lookup_div(province, name):
    """县级市/县/区 → 所属地级市。如 开原市 → 铁岭市。"""
    m = DIVISIONS.get(province)
    if not m or not name:
        return None
    n = name.strip()
    if n in m:
        return m[n]
    for suf in ("市", "县", "区", "旗"):
        if n + suf in m:
            return m[n + suf]
    nn = norm_area(n)
    if nn and nn != n:
        for k in m:
            if norm_area(k) == nn:
                return m[k]
    return None


# ---------- 级别管辖 ----------

def get_cap(province, city):
    """返回 (cap_info, status)。cap_info 为 None 表示该省未收录。"""
    e = PROVINCES.get(province)
    if not e:
        return None, "missing"
    cap, status = e.get("cap"), e.get("cap_status", "unknown")
    if cap == "noCap":
        return {"no_cap": True}, status
    if isinstance(cap, dict) and "cities9" in cap:
        c = norm_city(city)
        in9 = any(norm_city(m) == c for m in cap["cities9"])
        return {"max": cap["cap9"] if in9 else cap["capOther"], "tier": "重点城市" if in9 else "其他城市"}, status
    if isinstance(cap, (int, float)):
        return {"max": cap}, status
    return None, "missing"


def fmt_wan(y):
    w = y / 10000.0
    return ("%g万元" % w) if w == int(w) else ("%.2f万元" % w)


def decide_level(province, city, amount, is_foreign=False):
    """判定级别管辖。返回 dict: level / confidence / reason / warnings"""
    # 标的额是级别管辖的唯一决定因素。缺失时不得静默按 0 处理——那等于
    # 默认判成基层法院，会把本该由中院管辖的案件算错。
    # 门槛按法〔2025〕167号附件「不含本数」，故此处用严格小于。
    if amount is None or amount <= 0:
        return {
            "level": "基层",
            "confidence": "low",
            "reason": "未提供有效的诉讼请求标的额，级别管辖无法判定",
            "warnings": ["未提供标的额（或填了非正数），无法判断本案应由基层还是中级人民法院管辖。"
                         "下方法院仅为地域管辖的结果，补充标的额后必须重新判定。"],
        }

    cap, status = get_cap(province, city)
    warnings = []

    if not cap:
        lv = "基层" if amount < GENERIC_BASIC else "中级"
        return {
            "level": lv,
            "confidence": "low",
            "reason": "该省级别管辖标准未收录；按通用推定阈值 %s 判断为%s法院管辖" % (fmt_wan(GENERIC_BASIC), lv),
            "warnings": ["级别管辖结论为通用推定，未经核实，立案前必须向法院或按省高院文件确认"],
        }

    if cap.get("no_cap"):
        return {
            "level": "基层",
            "confidence": "medium" if status == "sourced" else "low",
            "reason": "该市各基层法院均有知产管辖权、无标的额上限，由基层法院管辖",
            "warnings": warnings,
        }

    mx = cap["max"]
    tier = ("（%s档）" % cap["tier"]) if cap.get("tier") else ""
    fw = "（涉外/涉港澳台，另需核实特别规定）" if is_foreign else ""

    if status == "presumed":
        note = (PROVINCES.get(province) or {}).get("note") or "本省标的额标准系推定值，使用前须核实"
        warnings.append(note)
    confidence = "low" if status == "presumed" else "medium"

    if is_foreign:
        warnings.append("涉外/涉港澳台案件的级别管辖可能另有规定，须单独核实")

    if amount < mx:
        return {"level": "基层", "confidence": confidence,
                "reason": "标的额 %s ＜ 本地基层受理上限 %s%s%s，由基层法院管辖" % (fmt_wan(amount), fmt_wan(mx), tier, fw),
                "warnings": warnings}
    return {"level": "中级", "confidence": confidence,
            "reason": "标的额 %s ≥ 本地基层受理上限 %s%s%s，由中级法院管辖" % (fmt_wan(amount), fmt_wan(mx), tier, fw),
            "warnings": warnings}


# ---------- 地域定位 ----------

def locate_court(province, city, district, parent):
    """在该省法院辖区表中定位具体基层法院。"""
    rd = COURTS.get(province)
    if not rd or not rd.get("courts"):
        return {"none": True}
    cN = norm_city(parent or city)

    def scan(q):
        if not q:
            return []
        return [ct for ct in rd["courts"] if any(area_hit(a, q) for a in ct.get("a", []))]

    # 匹配层级决定结论可信度：命中区县/本市最可靠；只能靠所属地级市名兜底的，
    # 命中的往往是该市市区的法院，对下辖县级市的被告而言是错的，必须降级处理。
    hits, via, level = scan(district), district, "district"
    if not hits:
        hits, via, level = scan(city), city, "city"
    if not hits and parent and norm_city(parent) != norm_city(city):
        hits, via, level = scan(parent), parent, "parent-fallback"
    if len(hits) > 1:
        by_city = [ct for ct in hits if cN and ct["c"].find(cN) >= 0]
        if by_city:
            hits = by_city
    if len(hits) == 1:
        matched = next((a for a in hits[0].get("a", []) if area_hit(a, via)), "")
        return {"court": hits[0]["c"], "matched": matched, "match_level": level, "via": via}
    if len(hits) > 1:
        return {"multi": [ct["c"] for ct in hits]}
    return {"none": True}


def court_for_place(province, city, district, amount, is_foreign=False):
    """给定一个连接点所在地，算出该走哪个法院。"""
    parent = lookup_div(province, city) or (lookup_div(province, district) if district else None)
    std_city = parent or city
    lv = decide_level(province, std_city, amount, is_foreign)
    warnings = list(lv["warnings"])
    extra = ""
    if parent and norm_city(parent) != norm_city(city):
        extra = "“%s”属%s，" % (city, parent)

    if lv["level"] == "中级":
        court = inter_name(std_city)
        warnings.append(
            "信息网络传播权侵权民事案件不属知识产权法院管辖范围，达到中院级别标准的应向普通中级人民法院起诉"
            "（计算机软件著作权案件除外）")
        return {"court": court, "level": "中级人民法院", "reason": lv["reason"],
                "confidence": lv["confidence"], "precise": False,
                "extra": extra + "中院为 %s" % court, "warnings": warnings}

    loc = locate_court(province, city, district, parent)
    if loc.get("court"):
        note = "已按“%s”定位" % (loc.get("via") or district or city)
        if loc.get("matched"):
            note += "（该院辖区含：%s）" % loc["matched"]
        if loc.get("match_level") == "parent-fallback":
            # 知产案件集中管辖：县级市通常无独立知产管辖法院，由所属地级市的集中管辖法院受理。
            # 这是制度设计的正常结果，不是数据缺失，不降置信度。
            note += "。知识产权案件实行集中管辖，“%s”无独立知产管辖法院，由所属%s的集中管辖法院受理" % (city, parent)
        return {"court": loc["court"], "level": "基层人民法院", "reason": lv["reason"],
                "confidence": lv["confidence"], "precise": True,
                "extra": extra + note, "warnings": warnings}
    if loc.get("multi"):
        return {"court": norm_city(city) + "市相应基层人民法院", "level": "基层人民法院",
                "reason": lv["reason"], "confidence": "low", "precise": False,
                "extra": "该市多个基层法院分片管辖（%s），需补充被告所在区/县/镇街" % "、".join(loc["multi"]),
                "warnings": warnings + ["未能定位到唯一法院，需补充更细的地址层级"]}
    # 定位失败有两种可能：地名真实但辖区表未收录，或地名本身写错了。
    # 两者的处置完全不同，必须区分开告知，不能都说成「未收录」。
    if not place_known(province, city, district):
        tip = ("未在%s的行政区划表中找到“%s”，请先核对地名是否有误。"
               % (province, district or city))
    else:
        tip = ("该地辖区名单未收录，无法锁定具体法院。可查最高人民法院知产案件管辖文件附件、"
               "拨打 12368，或通过『人民法院在线服务』网上立案由系统按被告地址自动路由")
    return {"court": (norm_city(city) + "市" if city else "被告所在地") + "有知产管辖权的基层人民法院",
            "level": "基层人民法院", "reason": lv["reason"], "confidence": "low", "precise": False,
            "extra": "", "warnings": warnings + [tip]}


# ---------- 管辖方案 ----------

def build_options(inp):
    """列出原告可选的全部管辖通道。"""
    opts = []
    amount = inp["amount"]
    fo = inp.get("is_foreign", False)

    if inp.get("def_prov"):
        r = court_for_place(inp["def_prov"], inp.get("def_city", ""), inp.get("def_district", ""), amount, fo)
        opts.append(_mk("被告住所地", r,
                        "被告住所地人民法院管辖（%s）。%s" % (BASIS_VENUE, r["reason"]),
                        "最稳妥通道，管辖异议风险最低。"))

    if inp.get("server_city"):
        r = court_for_place(inp.get("server_prov") or inp.get("def_prov"), inp["server_city"],
                            inp.get("server_district", ""), amount, fo)
        opts.append(_mk("侵权行为地（服务器/设备所在地）", r,
                        "以实施被诉侵权行为的网络服务器、计算机终端等设备所在地为侵权行为地（%s）。%s" % (BASIS_VENUE, r["reason"]),
                        "需举证服务器/设备确在该地；被告常以此为由提管辖异议，证据要提前固定。"))

    if inp.get("def_abroad") and inp.get("pl_city"):
        r = court_for_place(inp.get("pl_prov"), inp["pl_city"], inp.get("pl_district", ""), amount, fo)
        opts.append(_mk("原告发现地（兜底）", r,
                        "被告住所地与侵权行为地均难以确定或在境外的，原告发现侵权内容的计算机终端等设备所在地"
                        "可以视为侵权行为地（%s后段）。%s" % (BASIS_VENUE, r["reason"]),
                        "适用前提严格：须确实无法确定被告住所地和侵权行为地，否则极易被裁定移送。"))

    seen, uniq = set(), []
    for o in opts:
        k = (o["channel"], o["court"])
        if k not in seen:
            seen.add(k)
            uniq.append(o)
    return uniq


def _mk(channel, r, basis, strategy):
    return {"channel": channel, "court": r["court"], "level": r["level"],
            "confidence": r["confidence"], "precise": r["precise"],
            "reason": r["reason"], "basis": basis, "strategy": strategy,
            "note": r.get("extra", ""), "warnings": r.get("warnings", [])}


def analyze(inp):
    for key in ("def_prov", "server_prov", "pl_prov"):
        if inp.get(key):
            fixed = norm_province(inp[key])
            if fixed is None:
                return {"error": "无法识别省级行政区「%s」。请填写规范的省/直辖市/自治区名称，"
                                 "如「浙江省」「北京市」「内蒙古自治区」。" % inp[key],
                        "input": inp, "options": [], "overall_confidence": "low", "warnings": []}
            inp[key] = fixed

    opts = build_options(inp)
    all_w = []
    for o in opts:
        for w in o["warnings"]:
            if w not in all_w:
                all_w.append(w)
    conf = [o["confidence"] for o in opts]
    overall = "low" if (not opts or "low" in conf) else ("medium" if "medium" in conf else "high")
    return {"input": inp, "options": opts, "overall_confidence": overall,
            "warnings": all_w,
            "disclaimer": "本结论由查表计算得出。标的额门槛与辖区名单均据法〔2025〕167号附件"
                          "（2025-09-23 发布，2025-10-01 施行；同时废止法〔2022〕109号）。"
                          "各省数据的出处见 data/provinces.json。立案前应复核标的法院当期立案口径。"}


# ---------- 输出 ----------

def emit(text):
    """输出到 stdout，兼容 Windows GBK 控制台与管道两种场景。

    终端场景按终端编码输出（CMD 默认 GBK 代码页也能正常显示中文）；
    重定向或管道场景（AI 调用）强制 UTF-8，保证调用方按 UTF-8 解析不乱码。
    """
    if sys.stdout.isatty():
        enc = sys.stdout.encoding or "utf-8"
        try:
            text.encode(enc)
            print(text)
            return
        except (UnicodeEncodeError, LookupError):
            pass
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def to_text(res):
    if res.get("error"):
        return "输入有误：" + res["error"]
    L = []
    L.append("信息网络传播权纠纷 · 一审管辖分析")
    L.append("整体置信度：%s" % {"high": "高", "medium": "中", "low": "低"}[res["overall_confidence"]])
    L.append("")
    if not res["options"]:
        L.append("未能生成任何管辖方案：请至少提供被告住所地所在省、市。")
        return "\n".join(L)
    for i, o in enumerate(res["options"], 1):
        L.append("方案 %d · %s" % (i, o["channel"]))
        L.append("  法院：%s（%s）" % (o["court"], o["level"]))
        L.append("  依据：%s" % o["basis"])
        if o["note"]:
            L.append("  定位：%s" % o["note"])
        L.append("  策略：%s" % o["strategy"])
        L.append("  置信度：%s%s" % ({"high": "高", "medium": "中", "low": "低"}[o["confidence"]],
                                     "" if o["precise"] else "（未锁定到唯一法院）"))
        L.append("")
    if res["warnings"]:
        L.append("!! 风险提示")
        for w in res["warnings"]:
            L.append("  · %s" % w)
    L.append("")
    L.append(res["disclaimer"])
    return "\n".join(L)


# ---------- 自检 ----------

def selftest():
    cases = [
        # 法释〔2025〕14号（2025-11-01 施行）后，网络著作权案件不再由互联网法院管辖
        ("北京案件不得路由到互联网法院",
         {"def_prov": "北京市", "def_city": "北京市", "def_district": "朝阳区", "amount": 500_000},
         lambda r: "互联网法院" not in r["options"][0]["court"]),
        ("杭州案件不得路由到互联网法院",
         {"def_prov": "浙江省", "def_city": "杭州市", "def_district": "西湖区", "amount": 800_000},
         lambda r: "互联网法院" not in r["options"][0]["court"]),
        ("广州案件不得路由到互联网法院",
         {"def_prov": "广东省", "def_city": "广州市", "def_district": "天河区", "amount": 800_000},
         lambda r: "互联网法院" not in r["options"][0]["court"]),
        ("浙江超500万应升中院，且不得走知产法院",
         {"def_prov": "浙江省", "def_city": "杭州市", "def_district": "西湖区", "amount": 6_000_000},
         lambda r: r["options"][0]["level"] == "中级人民法院"
                   and "知识产权法院" not in r["options"][0]["court"]),
        ("京沪 noCap：标的额再大也留在基层",
         {"def_prov": "上海市", "def_city": "上海市", "def_district": "浦东新区", "amount": 20_000_000},
         lambda r: r["options"][0]["level"] == "基层人民法院"),
        ("宁夏标的额已据附件核实，不应再作推定值降级",
         {"def_prov": "宁夏回族自治区", "def_city": "银川市", "def_district": "兴庆区", "amount": 500_000},
         lambda r: r["options"][0]["confidence"] == "medium"
                   and not any("推定" in w for w in r["warnings"])),
        ("31 个省级行政区的标的额门槛均有明确出处，无推定值",
         {"def_prov": "浙江省", "def_city": "杭州市", "def_district": "西湖区", "amount": 800_000},
         lambda r: all(v.get("cap_status") == "sourced" for v in PROVINCES.values())),
        ("县级市按知产集中管辖归位到地级市法院，且结论精确",
         {"def_prov": "辽宁省", "def_city": "开原市", "amount": 500_000},
         lambda r: r["options"][0]["precise"] is True
                   and "集中管辖" in r["options"][0]["note"]),
        ("常规省份正常命中应为 medium 置信度",
         {"def_prov": "江苏省", "def_city": "苏州市", "def_district": "虎丘区", "amount": 500_000},
         lambda r: r["options"][0]["precise"] is True
                   and r["options"][0]["confidence"] == "medium"),
        ("广东分档：深圳按重点城市 1000 万档，600 万仍在基层",
         {"def_prov": "广东省", "def_city": "深圳市", "def_district": "南山区", "amount": 6_000_000},
         lambda r: r["options"][0]["level"] == "基层人民法院"),
        ("以「州」结尾的普通地级市，中院名须含「市」",
         {"def_prov": "江苏省", "def_city": "苏州市", "def_district": "虎丘区", "amount": 8_000_000},
         lambda r: r["options"][0]["court"] == "苏州市中级人民法院"),
        ("自治州中院名不含「市」",
         {"def_prov": "吉林省", "def_city": "延吉市", "amount": 5_000_000},
         lambda r: r["options"][0]["court"].endswith("自治州中级人民法院")),
        ("中山镇区细分：小榄归第二人民法院",
         {"def_prov": "广东省", "def_city": "中山市", "def_district": "小榄", "amount": 500_000},
         lambda r: r["options"][0]["court"] == "中山市第二人民法院"),
        ("省份简称「浙江」应能识别，不退化为未收录",
         {"def_prov": "浙江", "def_city": "杭州市", "def_district": "西湖区", "amount": 800_000},
         lambda r: r["options"][0]["court"] == "杭州市西湖区人民法院"
                   and r["options"][0]["confidence"] == "medium"),
        ("自治区简称「内蒙古」应能识别",
         {"def_prov": "内蒙古", "def_city": "呼和浩特市", "amount": 500_000},
         lambda r: not r.get("error")),
        ("无效省名必须报错，不得编造法院",
         {"def_prov": "火星省", "def_city": "火星市", "amount": 500_000},
         lambda r: bool(r.get("error")) and not r["options"]),
        ("未提供标的额时不得静默判为基层",
         {"def_prov": "浙江省", "def_city": "杭州市", "def_district": "西湖区", "amount": 0},
         lambda r: r["options"][0]["confidence"] == "low"
                   and any("无法判断" in x for x in r["warnings"])),
        ("地名写错时应提示核对地名，而非笼统说未收录",
         {"def_prov": "浙江省", "def_city": "不存在市", "amount": 500_000},
         lambda r: any("核对地名" in x for x in r["warnings"])),
        ("被告在境外时才出现原告发现地兜底方案",
         {"def_prov": "浙江省", "def_city": "杭州市", "amount": 500_000,
          "def_abroad": True, "pl_prov": "浙江省", "pl_city": "宁波市"},
         lambda r: any(o["channel"].startswith("原告发现地") for o in r["options"])),
    ]
    ok = 0
    for name, inp, check in cases:
        try:
            r = analyze(inp)
            passed = check(r)
        except Exception as e:                                  # noqa: BLE001
            passed, r = False, {"error": repr(e)}
        emit(("  PASS  " if passed else "  FAIL  ") + name)
        if not passed:
            emit("        -> " + json.dumps(r, ensure_ascii=False)[:400])
        ok += 1 if passed else 0
    emit("\n%d/%d passed" % (ok, len(cases)))
    return 0 if ok == len(cases) else 1


def main():
    p = argparse.ArgumentParser(description="信息网络传播权纠纷一审管辖判定")
    p.add_argument("--def-prov", dest="def_prov", help="被告住所地·省级")
    p.add_argument("--def-city", dest="def_city", default="", help="被告住所地·地级市")
    p.add_argument("--def-district", dest="def_district", default="", help="被告住所地·区/县")
    p.add_argument("--amount", type=float, default=0, help="诉讼请求标的额（元）")
    p.add_argument("--server-prov", dest="server_prov", default="", help="服务器所在地·省级")
    p.add_argument("--server-city", dest="server_city", default="", help="服务器所在地·地级市")
    p.add_argument("--server-district", dest="server_district", default="", help="服务器所在地·区/县")
    p.add_argument("--pl-prov", dest="pl_prov", default="", help="原告发现地·省级")
    p.add_argument("--pl-city", dest="pl_city", default="", help="原告发现地·地级市")
    p.add_argument("--pl-district", dest="pl_district", default="", help="原告发现地·区/县")
    p.add_argument("--def-abroad", dest="def_abroad", action="store_true", help="被告住所地/侵权行为地在境外或无法确定")
    p.add_argument("--foreign", dest="is_foreign", action="store_true", help="涉外或涉港澳台")
    p.add_argument("--text", action="store_true", help="输出人类可读文本而非 JSON")
    p.add_argument("--selftest", action="store_true", help="运行内置用例自检")
    a = p.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if not a.def_prov:
        p.error("至少需要 --def-prov（被告住所地所在省级行政区）")

    inp = {k: v for k, v in vars(a).items() if k not in ("text", "selftest") and v not in ("", None, False)}
    inp["amount"] = a.amount
    res = analyze(inp)
    out = to_text(res) if a.text else json.dumps(res, ensure_ascii=False, indent=1)
    emit(out)
    if res.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
