#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法条原文检索脚本（law_text_lookup.py）。

功能：从法条全文库检索条文原文，供引用前核对。确定性检索，不依赖模型判断。

数据源（双包架构，大纲 8.8）：法条原文已整体剥离至独立数据包 cdiw-law-pack，
单一事实源为包内 registry.json。本脚本按三级路径解析数据目录，首个命中即用：
  ① 环境变量 CDIW_LAW_PACK_DIR（指向法条包根，脚本自动补 assets/data/law_texts/）
  ② 同级目录 <主包父目录>/cdiw-law-pack/assets/data/law_texts/（默认部署形态）
  ③ 旧版相对路径 <主包>/assets/data/law_texts/（兼容历史部署）
三级均未命中时返回 ERR_LAW_PACK_MISSING 结构化信封，退出码 2，禁止裸抛异常。
脱包降级：效力校验、期限计算、文书生成、罪名辨析（非敏感条目）不受影响；
仅条文原文核对降级「待核实」（主包 SKILL.md 7.2 第 5 条）。

新增法规只须在 registry.json 登记一次即自动进入本检索与 self_check 自检链。

调用方式：
  python scripts/law_text_lookup.py --law 刑法 --article 第266条
  python scripts/law_text_lookup.py --law 刑诉法 --article 91
  python scripts/law_text_lookup.py --law 解释 --article 第81条
  python scripts/law_text_lookup.py --law 程序规定 --article 第160条
  python scripts/law_text_lookup.py --law 复议复核 --search 不予立案
  python scripts/law_text_lookup.py --law 查封冻结 --article 第35条
  python scripts/law_text_lookup.py --law 经济犯罪规定 --article 第28条
  python scripts/law_text_lookup.py --law 量刑指导意见 --search 认罪认罚
  python scripts/law_text_lookup.py --law 量刑指导意见二 --article 一（六）
  python scripts/law_text_lookup.py --law 刑诉法 --search 认罪认罚 --max 5
  python scripts/law_text_lookup.py --pack-info        # 输出当前挂载路径与解析层级

统一接口规范：
  - 仅依赖Python标准库；支持--help；全部本地执行、零网络请求；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或法条包未挂载 / 3检索失败；
  - 错误码：ERR_ARGS_MISSING / ERR_LAW_NOT_FOUND / ERR_ARTICLE_NOT_FOUND
            / ERR_LAW_PACK_MISSING / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_NAME = "law_text_lookup"
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_ERR_PACK_MSG = (
    "法条数据包（cdiw-law-pack）未挂载，条文原文核对不可用。挂载指引三条："
    "①设置环境变量 CDIW_LAW_PACK_DIR 指向法条数据包根目录；"
    "②将 cdiw-law-pack 与 cdiw-core 同级放置（默认部署形态，自动识别）；"
    "③旧版部署可将数据置于 <主包>/assets/data/law_texts/。"
    "当前降级口径：法条引用的效力校验不受影响（效力库随主包），"
    "条文原文核对一律标注「待核实」，禁止凭记忆补全条文内容或静默省略校验环节。"
)


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def _emit_pack_missing(trace_id=None):
    """三级路径均未命中：返回结构化信封，退出码 2，禁止裸抛异常（8.8.4）。"""
    print(json.dumps({"status": "error", "error_code": "ERR_LAW_PACK_MISSING",
                      "message": _ERR_PACK_MSG,
                      "data": {"trace_id": trace_id or make_trace_id(),
                               "degraded": True, "fallback": "待核实",
                               "unaffected": ["效力校验", "期限计算", "文书生成", "罪名辨析（非敏感条目）"]}},
                     ensure_ascii=False, indent=2))
    sys.exit(2)


def resolve_law_texts_dir():
    """法条全文库目录三级解析（首个命中即用，8.8.4）。

    ① 环境变量 CDIW_LAW_PACK_DIR（指向法条包根，脚本自动补 assets/data/law_texts/）
    ② 同级目录 <主包父目录>/cdiw-law-pack/assets/data/law_texts/
    ③ 旧版相对路径 <主包>/assets/data/law_texts/
    """
    cands = []
    env = os.environ.get("CDIW_LAW_PACK_DIR")
    if env:
        p = env if env.rstrip("/").endswith("law_texts") else os.path.join(env, "assets", "data", "law_texts")
        cands.append(("env:CDIW_LAW_PACK_DIR", p))
    cands.append(("sibling:cdiw-law-pack", os.path.join(
        os.path.dirname(SKILL_ROOT), "cdiw-law-pack", "assets", "data", "law_texts")))
    cands.append(("legacy:<主包>/assets/data/law_texts",
                  os.path.join(SKILL_ROOT, "assets", "data", "law_texts")))
    for level, path in cands:
        if os.path.isfile(os.path.join(path, "registry.json")):
            return path, level
    return None, None


def _reg_updated_at():
    """取注册表的库内数据时点——引用法条时须一并展示（7.2 第 5 条）。"""
    try:
        reg = json.load(open(os.path.join(DATA_DIR, "registry.json"), encoding="utf-8"))
        return reg.get("_updated_at")
    except (OSError, ValueError):
        return None


DATA_DIR, DATA_DIR_LEVEL = resolve_law_texts_dir()
if DATA_DIR is None:
    _emit_pack_missing()

# 法律名别名 → 数据文件：单一事实源为法条数据包内 registry.json（随包迁移，仍为法条库单一事实源）。
# 新增法规只须在 registry.json 登记一次即自动进入本检索与 self_check 自检链。
# 文件名规范：<主题全拼>_<年份>.json。


def load_law_aliases():
    """从注册表构建别名映射；别名按长度降序排列（长名优先，防短名抢先命中变体）。"""
    reg_path = os.path.join(DATA_DIR, "registry.json")
    try:
        with open(reg_path, "r", encoding="utf-8") as f:
            reg = json.load(f)
        pairs = []
        for law in reg.get("laws", []):
            fn = law.get("file")
            if not fn:
                continue
            for alias in law.get("aliases", []):
                pairs.append((alias, fn))
        pairs.sort(key=lambda x: -len(x[0]))
        return dict(pairs)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error_code": "ERR_IO",
                          "message": "法条全文库注册表缺失或损坏：%s（%s）——请维护者检查 assets/data/law_texts/registry.json"
                          % (reg_path, exc), "data": None}, ensure_ascii=False, indent=2))
        sys.exit(2)


LAW_ALIASES = load_law_aliases()


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def load_law(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(json.dumps(envelope("error", "ERR_IO", "法条全文库缺失：%s" % path, None),
                         ensure_ascii=False, indent=2))
        sys.exit(2)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        print(json.dumps(envelope("error", "ERR_IO", "法条全文库读取失败：%s（%s）" % (path, exc), None),
                         ensure_ascii=False, indent=2))
        sys.exit(2)


def resolve_law(name):
    if not name:
        return None
    if name in LAW_ALIASES:
        return LAW_ALIASES[name]
    # 模糊匹配仅限长查询词（≥4字）作容错；短词（如"解释"2字）子串命中系歧义，直接拒绝
    if len(name) < 4:
        return None
    for alias, fn in LAW_ALIASES.items():
        if alias in name or name in alias:
            return fn
    return None


def normalize_article(article):
    """“17”“第17条”“第17条第3款”→ 条级键候选列表（含数字与中文序号匹配）。"""
    s = article.strip().replace(" ", "")
    m = re.match(r"^第?(\d+)条?", s)
    if m:
        return int(m.group(1))
    m = re.match(r"^第?([一二三四五六七八九十百千零〇]+)条?", s)
    if m:
        return cn_to_int(m.group(1))
    return None


def cn_to_int(s):
    units = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
             "十": 10, "百": 100, "千": 1000, "万": 10000}
    result, current = 0, 0
    for ch in s:
        if ch not in units:
            return None
        v = units[ch]
        if v >= 10:
            if current == 0:
                current = 1
            if v == 10000:
                result = (result + current) * v
            else:
                result += current * v
            current = 0
        else:
            current = current * 10 + v
    return result + current


def int_to_cn(n):
    digits = "零一二三四五六七八九"
    if n < 10:
        return digits[n]
    if n < 20:
        return "十" + (digits[n % 10] if n % 10 else "")
    if n < 100:
        return digits[n // 10] + "十" + (digits[n % 10] if n % 10 else "")
    return str(n)


def arabic_to_cn(n):
    """1-99 阿拉伯数字→中文数字（层级键兼容，如 四(1)→四（一））。"""
    digits = "零一二三四五六七八九"
    if not (0 < n < 100):
        return None
    if n < 10:
        return digits[n]
    if n < 20:
        return "十" + (digits[n % 10] if n % 10 else "")
    return digits[n // 10] + "十" + (digits[n % 10] if n % 10 else "")


def find_articles(db, article):
    """按条号定位条文；返回条目列表（可能命中“之X”条文）。
    用户指定后缀（如“第133条之一”）时优先返回带后缀条目；未指定后缀时返回全部同号条目。
    量刑指导意见等非“第X条”结构法规：--article 传层级键（如“四（一）”“三（十四）”）直接命中。"""
    s0 = article.strip().replace(" ", "")
    # 层级键直查（兼容半角括号与半角数字，如“四(1)”→“四（一）”）
    full = s0.replace("(", "（").replace(")", "）")
    cands = [s0, full]
    m = re.match(r"^([一二三四五]{1,2})（(\d{1,2})）$", full)
    if m:
        cn = arabic_to_cn(int(m.group(2)))
        if cn:
            cands.append("%s（%s）" % (m.group(1), cn))
    for cand in cands:
        if cand in db["articles"]:
            return [(cand, db["articles"][cand])]
    # 含括号结构但未命中键的，不再回退条号数字匹配（防止误命中同号条目）
    if re.search(r"[（）()]", s0) and re.match(r"^[一二三四五六七八九十]", s0):
        return []
    no = normalize_article(article)
    if no is None:
        return []
    s = article.strip().replace(" ", "")
    has_suffix = bool(re.search(r"条之[一二三四五六七八九十]", s))
    hits = []
    for key, entry in db["articles"].items():
        if entry["no"] == no:
            hits.append((key, entry))
    hits.sort(key=lambda x: (0 if ("之" in x[0]) == has_suffix else 1, x[1]["no"]))
    if has_suffix:
        exact = [h for h in hits if h[0].endswith(s[s.index("条之"):])]
        if exact:
            return exact
    return hits


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="法条原文检索：从法条全文库检索条文原文（确定性检索，不依赖模型判断）。")
    parser.add_argument("--law",
                        help="法律名称（全部注册法规支持别名，文号亦可直接检索，如法释〔2026〕6号；"
                             "完整别名清单见法条数据包 registry.json，脱包状态见主包 "
                             "assets/data/registry_summary.json）")
    parser.add_argument("--article", help="条号（如：第266条、91、第133条之一；量刑指导意见传层级键如：四（一）、三（十四））")
    parser.add_argument("--search", help="关键词全文检索（与--article二选一）")
    parser.add_argument("--max", type=int, default=5, help="关键词检索最大返回条数，默认5")
    parser.add_argument("--pack-info", action="store_true",
                        help="输出当前法条包挂载路径、解析层级与法规统计，不做检索")
    args = parser.parse_args()
    trace_id = make_trace_id()

    if args.pack_info:
        try:
            reg = json.load(open(os.path.join(DATA_DIR, "registry.json"), encoding="utf-8"))
            n_laws = len(reg.get("laws", []))
            n_art = sum(l.get("article_entries", 0) for l in reg.get("laws", []))
        except (OSError, ValueError):
            n_laws = n_art = None
        print(json.dumps(envelope(
            "ok", None, "法条数据包已挂载（解析层级：%s）" % DATA_DIR_LEVEL,
            {"trace_id": trace_id, "data_dir": DATA_DIR, "resolved_by": DATA_DIR_LEVEL,
             "law_count": n_laws, "article_entries_total": n_art,
             "registry_updated_at": _reg_updated_at()}), ensure_ascii=False, indent=2))
        sys.exit(0)

    if not args.law:
        print(json.dumps(envelope("error", "ERR_ARGS_MISSING",
                                  "须指定--law（或--pack-info查看挂载状态）", {"trace_id": trace_id}),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    filename = resolve_law(args.law)
    if not filename:
        print(json.dumps(envelope("error", "ERR_LAW_NOT_FOUND",
                                  "未识别的法律名称：%s（全部注册法规支持别名，完整清单见 assets/data/law_texts/registry.json）" % args.law,
                                  {"trace_id": trace_id}), ensure_ascii=False, indent=2))
        sys.exit(1)

    db = load_law(filename)
    meta = db.get("legal_basis", {})

    if args.article:
        hits = find_articles(db, args.article)
        if not hits:
            print(json.dumps(envelope("error", "ERR_ARTICLE_NOT_FOUND",
                                      "条文不在全文库中：%s（请核对条号；本库范围：%s）" % (
                                          args.article, db.get("law_title", "")),
                                      {"trace_id": trace_id, "law": db.get("law_title", "")}),
                             ensure_ascii=False, indent=2))
            sys.exit(3)
        articles_out = []
        for key, entry in hits:
            item = {"article": key, "no": entry["no"], "text": entry["text"],
                    "context": entry.get("context", {})}
            if "title" in entry:
                item["title"] = entry["title"]
            articles_out.append(item)
        print(json.dumps(envelope("ok", None, "检索到%d个条目" % len(articles_out),
                                  {"trace_id": trace_id, "law": db.get("law_title", ""),
                                   "legal_basis": meta, "articles": articles_out}),
                         ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.search:
        kw = args.search.strip()
        matches = []
        for key in db.get("order", []):
            entry = db["articles"][key]
            blob = entry["text"] + (entry.get("title") or "")
            if kw in blob:
                item = {"article": key, "no": entry["no"],
                        "text": entry["text"][:400],
                        "context": entry.get("context", {})}
                if "title" in entry:
                    item["title"] = entry["title"]
                matches.append(item)
                if len(matches) >= args.max:
                    break
        print(json.dumps(envelope("ok", None, "关键词“%s”命中%d条（显示前%d条）" % (
            kw, len(matches), len(matches)),
            {"trace_id": trace_id, "law": db.get("law_title", ""),
             "legal_basis": meta, "matches": matches}),
            ensure_ascii=False, indent=2))
        sys.exit(0) if matches else sys.exit(3)

    print(json.dumps(envelope("error", "ERR_ARGS_MISSING",
                              "须指定--article或--search其一", {"trace_id": trace_id}),
                     ensure_ascii=False, indent=2))
    sys.exit(1)


if __name__ == "__main__":
    main()
