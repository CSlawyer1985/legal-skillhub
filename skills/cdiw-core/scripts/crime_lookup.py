#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""罪名索引、立案标准与量刑档次查询脚本（crime_lookup.py）。

功能：按罪名或刑法条款号查询立案追诉标准与三档量刑档次；按章节浏览刑法分则
全量罪名。查询是确定性的——脚本直接读JSON数据，不依赖模型判断。数据源：
  assets/data/crime_index.json（罪名全量索引：现行有效483罪名，按分则十章分层）
  assets/data/case_filing_standards.json（立案追诉标准，275罪名）
  assets/data/crime_sentencing_table.json（量刑档次表，275罪名）

调用方式：
  python scripts/crime_lookup.py --crime 失火罪
  python scripts/crime_lookup.py --crime 失火罪 --field sentencing
  python scripts/crime_lookup.py --crime 失火罪 --field filing
  python scripts/crime_lookup.py --article 115
  python scripts/crime_lookup.py --chapter 第二章
  python scripts/crime_lookup.py --chapter 2
  python scripts/crime_lookup.py --list

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3查询失败；
  - 错误码：ERR_ARGS_MISSING / ERR_CRIME_NOT_FOUND / ERR_ARTICLE_NOT_FOUND /
    ERR_CHAPTER_NOT_FOUND / ERR_IO。
"""

import argparse
import difflib
import hashlib
import json
import os
import sys
from datetime import datetime

SCRIPT_NAME = "crime_lookup"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "data")

INDEX_FILE = os.path.join(DATA_DIR, "crime_index.json")
FILING_FILE = os.path.join(DATA_DIR, "case_filing_standards.json")
SENTENCING_FILE = os.path.join(DATA_DIR, "crime_sentencing_table.json")


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        print(json.dumps(envelope("error", "ERR_IO", "数据文件读取失败：%s（%s）" % (path, exc), None),
                         ensure_ascii=False, indent=2))
        sys.exit(2)


def find_by_article(crimes_dict, article):
    """按条款号匹配（支持 '115'、'133之一'、'134-1'（之风格式化））。"""
    article = article.strip()
    # 精确匹配
    for name, entry in crimes_dict.items():
        if entry.get("article") == article:
            return name, entry
    # 归一化匹配：之X / -X 后缀
    def norm(a):
        return a.replace("之", "-").strip()
    for name, entry in crimes_dict.items():
        if norm(entry.get("article", "")) == norm(article):
            return name, entry
    # 纯数字前缀匹配（如 '115' 匹配 '115'，不匹配 '115-1'）
    for name, entry in crimes_dict.items():
        if entry.get("article", "").split("之")[0] == article and "之" not in entry.get("article", ""):
            return name, entry
    return None, None


def index_find_article(index_data, article):
    """在罪名全量索引中按条文号查找（article_ref如'第115条第2款'）。"""
    query = article.strip()
    num_m = query.split("之")[0].lstrip("第").rstrip("条")
    zh_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    hits = []
    for name, meta in index_data.get("index", {}).items():
        ref = meta.get("article", "")
        ref_num = ref.replace("第", "").split("条")[0]
        if ref_num == num_m or ref.startswith("第" + num_m + "条"):
            hits.append((name, meta))
    return hits


def province_hint(filing_entry, sentencing_entry):
    """省域口径提示（V1.0.1）：数额标准中“一类/二类”系地区分类口径（源表为广东省标准），
    各省份数额标准不同——命中即提示核对案件所在省份标准，防止跨省误用。"""
    numeric_texts = []
    if filing_entry:
        numeric_texts += [filing_entry.get("立案标准", ""), filing_entry.get("二档加重", ""),
                          filing_entry.get("三档加重", "")]
    if sentencing_entry:
        for tier_key in ("tier1", "tier2", "tier3"):
            tier = sentencing_entry.get(tier_key)
            if tier:
                numeric_texts.append(tier.get("trigger", ""))
    refs_text = json.dumps(
        (sentencing_entry or {}).get("references", []) + (filing_entry or {}).get("source_refs", []),
        ensure_ascii=False)
    if any(("一类" in t or "二类" in t) for t in numeric_texts) or "粤" in refs_text:
        return ("本条数额标准中的“一类/二类”地区分类系源表口径（广东省标准），"
                "各省份数额标准不同；正式引用前须核对案件所在省份的现行标准"
                "（如浙江省见浙江省高院、省检相关实施细则及数额标准文件）")
    return None


def build_output(name, filing_entry, sentencing_entry, index_meta=None):
    """合并罪名索引、立案标准与量刑档次为统一输出结构。"""
    result = {"罪名": name}
    if index_meta:
        result["章节"] = index_meta.get("chapter", "")
        if index_meta.get("section"):
            result["节"] = index_meta["section"]
        result["条文"] = index_meta.get("article", "")
        result["罪名规定来源"] = index_meta.get("source", "")
    if sentencing_entry:
        if not index_meta:
            result["刑法条款"] = sentencing_entry.get("article", "")
            result["章节"] = sentencing_entry.get("chapter", "")
        tiers = {}
        for tier_key in ["tier1", "tier2", "tier3"]:
            tier = sentencing_entry.get(tier_key)
            if tier:
                tiers[tier.get("label", tier_key)] = {
                    "触发事实": tier.get("trigger", ""),
                    "刑期": tier.get("sentence", ""),
                    "刑期类型": tier.get("sentence_type", ""),
                }
                if tier.get("notes"):
                    tiers[tier.get("label", tier_key)]["备注"] = tier["notes"]
        result["量刑档次"] = tiers
        result["量刑指导意见覆盖"] = sentencing_entry.get("guideline_covered", False)
        result["司法解释引用"] = [
            {"名称": r.get("name", ""), "文号": r.get("doc_no", ""), "时效状态": r.get("law_status", "")}
            for r in sentencing_entry.get("references", [])
        ]
        if sentencing_entry.get("name_note"):
            result["数据修正记录"] = sentencing_entry["name_note"]
    else:
        result["量刑档次"] = "未录入（本罪名现行有效，量刑档次数据待后续批次录入；可按刑法条文法定刑幅度先行分析并标注【幅度推演】）"
    if filing_entry:
        result["立案标准"] = filing_entry.get("立案标准", "")
        if filing_entry.get("二档加重"):
            result["二档加重标准"] = filing_entry["二档加重"]
        if filing_entry.get("三档加重"):
            result["三档加重标准"] = filing_entry["三档加重"]
        if filing_entry.get("notes"):
            result["立案标准备注"] = filing_entry["notes"]
    else:
        result["立案标准"] = "未录入（本罪名现行有效，立案追诉标准数据待后续批次录入；检索线按立案追诉标准（一）（二）及各罪司法解释补查）"
    if sentencing_entry:
        result["数据核验"] = {
            "核验方式": sentencing_entry.get("vetted_by", ""),
            "核验时间": sentencing_entry.get("vetted_at", ""),
            "来源页": sentencing_entry.get("source_page", ""),
        }
    # 省域口径提示（V1.0.1）
    hint = province_hint(filing_entry, sentencing_entry)
    if hint:
        result["省域提示"] = hint
    return result


def match_chapter(index_data, chapter_arg):
    """解析章参数：'第二章'/'2'/'危害公共安全'/'二' 均可。"""
    arg = chapter_arg.strip()
    zh_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    for ch in index_data.get("chapters", []):
        title = ch.get("title", "")
        no = ch.get("no")
        if arg == str(no) or arg in zh_map and zh_map[arg] == no:
            return ch
        # '第二章' / '第二章　危害公共安全罪' / '危害公共安全'
        title_name = title.split("　", 1)[1] if "　" in title else title
        if arg == title or arg == "第" + "一二三四五六七八九十"[no - 1] + "章" \
           or arg == title_name or arg in title_name:
            return ch
    return None


def main():
    parser = argparse.ArgumentParser(
        description="罪名索引、立案标准与量刑档次查询（数据源：crime_index.json + case_filing_standards.json + crime_sentencing_table.json）")
    parser.add_argument("--crime", help="罪名全称（如：失火罪）或含关键词名称")
    parser.add_argument("--article", help="刑法条款号（如：115、133之一）")
    parser.add_argument("--chapter", help="刑法分则章（如：第二章 / 2 / 危害公共安全），列出该章全部罪名")
    parser.add_argument("--field", choices=["all", "filing", "sentencing"], default="all",
                        help="输出字段：all=全部（默认） / filing=仅立案标准 / sentencing=仅量刑档次")
    parser.add_argument("--list", action="store_true", help="列出罪名全量索引（483罪名，按十章分层）")
    args = parser.parse_args()

    index_data = load_json(INDEX_FILE)
    filing_data = load_json(FILING_FILE)
    sentencing_data = load_json(SENTENCING_FILE)
    index_flat = index_data.get("index", {}) if index_data else {}

    # ---- 章节浏览 ----
    if args.chapter:
        ch = match_chapter(index_data, args.chapter)
        if not ch:
            print(json.dumps(envelope("error", "ERR_CHAPTER_NOT_FOUND",
                                      "未找到对应章：%s（可用形如'第二章'/'2'/'危害公共安全'，第一章至第十章）" % args.chapter,
                                      {"查询章": args.chapter}), ensure_ascii=False, indent=2))
            sys.exit(3)
        crimes_out = []
        for sec in ch.get("sections", []):
            for c in sec.get("crimes", []):
                crimes_out.append({
                    "罪名": c["name"], "条文": c["article_ref"], "节": sec.get("title"),
                    "罪名规定来源": c.get("source", ""),
                    "量刑数据": bool(index_flat.get(c["name"], {}).get("has_sentencing_data")),
                    "立案数据": bool(index_flat.get(c["name"], {}).get("has_filing_data")),
                })
        print(json.dumps(envelope("ok", None, "章节罪名清单", {
            "章": ch["title"],
            "罪名总数": ch["crime_count"],
            "量刑数据覆盖": sum(1 for c in crimes_out if c["量刑数据"]),
            "立案数据覆盖": sum(1 for c in crimes_out if c["立案数据"]),
            "罪名列表": crimes_out,
        }), ensure_ascii=False, indent=2))
        sys.exit(0)

    # ---- 全量清单 ----
    if args.list:
        chapters_out = []
        for ch in index_data.get("chapters", []):
            chapters_out.append({
                "章": ch["title"], "罪名数": ch["crime_count"],
                "节": [s["title"] for s in ch.get("sections", []) if s.get("title")],
            })
        print(json.dumps(envelope("ok", None, "罪名全量索引（按刑法分则十章分层）", {
            "罪名总数": index_data.get("statistics", {}).get("total"),
            "分章统计": chapters_out,
            "数据覆盖": {
                "量刑档次": index_data.get("statistics", {}).get("with_sentencing_data"),
                "立案标准": index_data.get("statistics", {}).get("with_filing_data"),
            },
            "数据版本": {
                "crime_index": index_data.get("_version", ""),
                "case_filing_standards": filing_data.get("_version", ""),
                "crime_sentencing_table": sentencing_data.get("_version", ""),
            },
            "索引查询提示": "按罪名名称逐个查询请用 --crime；按章浏览请用 --chapter",
        }), ensure_ascii=False, indent=2))
        sys.exit(0)

    if not args.crime and not args.article:
        print(json.dumps(envelope("error", "ERR_ARGS_MISSING",
                                  "缺少查询参数：须提供 --crime、--article 或 --chapter（或 --list 查看全量索引）", None),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    filing_crimes = filing_data.get("crimes", {})
    sentencing_crimes = sentencing_data.get("crimes", {})

    # ---- 按条款号查询 ----
    if args.article:
        name_f, entry_f = find_by_article(filing_crimes, args.article) if filing_crimes else (None, None)
        name_s, entry_s = find_by_article(sentencing_crimes, args.article) if sentencing_crimes else (None, None)
        if not name_f and not name_s:
            # 回退到罪名全量索引
            idx_hits = index_find_article(index_data, args.article) if index_data else []
            if idx_hits:
                names = [n for n, _ in idx_hits]
                data = [build_output(n, filing_crimes.get(n), sentencing_crimes.get(n), index_flat.get(n))
                        for n in names]
                print(json.dumps(envelope("ok", None, "查询成功（按条款·全量索引，量刑立案数据未录入）", data),
                                 ensure_ascii=False, indent=2))
                sys.exit(0)
            print(json.dumps(envelope("error", "ERR_ARTICLE_NOT_FOUND",
                                      "未找到条款号对应的罪名：刑法第%s条（罪名全量索引483罪名中亦无对应，请核对条文号）" % args.article,
                                      {"查询条款": args.article}),
                             ensure_ascii=False, indent=2))
            sys.exit(3)
        name = name_s or name_f
        out = build_output(name, filing_crimes.get(name), sentencing_crimes.get(name), index_flat.get(name))
        print(json.dumps(envelope("ok", None, "查询成功（按条款）", out), ensure_ascii=False, indent=2))
        sys.exit(0)

    # ---- 按罪名查询（支持模糊匹配） ----
    crime = args.crime.strip()
    if crime in filing_crimes or crime in sentencing_crimes:
        matched = crime
    else:
        matched = None
        for n in list(filing_crimes.keys()) + list(sentencing_crimes.keys()):
            if crime in n or n in crime:
                matched = n
                break
    if not matched and crime in index_flat:
        matched = crime  # 现行有效罪名但量刑立案数据未录入
    if not matched:
        # 全量索引中模糊匹配 + 近似建议
        for n in index_flat:
            if crime in n or n in crime:
                matched = n
                break
    if not matched:
        close = difflib.get_close_matches(crime, list(index_flat.keys()), n=5, cutoff=0.4)
        in_index = crime in index_flat
        msg = ("未找到罪名：%s。该罪名不在现行刑法483个法定罪名之列——非刑法罪名（如系治安违法或行政违法事项不构成犯罪），"
               "或系已取消罪名/俗称简称" % crime) if not in_index else "未找到罪名：%s" % crime
        if close:
            msg += "。近似罪名：" + "、".join(close)
        if not in_index and close:
            msg = ("未找到罪名：%s（该名称不在现行刑法483个法定罪名之列，可能系已取消罪名、数罪合并俗称或不构成犯罪；近似法定罪名：%s）"
                   % (crime, "、".join(close)))
        print(json.dumps(envelope("error", "ERR_CRIME_NOT_FOUND", msg,
                                  {"查询罪名": crime, "近似罪名": close,
                                   "提示": "可用 --list 查看全量索引、--chapter 按章浏览"}),
                         ensure_ascii=False, indent=2))
        sys.exit(3)

    entry_f = filing_crimes.get(matched)
    entry_s = sentencing_crimes.get(matched)

    # 按字段过滤
    if args.field == "filing" and entry_f:
        out = {"罪名": matched, "刑法条款": entry_f.get("article", ""),
               "立案标准": entry_f.get("立案标准", ""),
               "二档加重": entry_f.get("二档加重"),
               "三档加重": entry_f.get("三档加重")}
        hint = province_hint(entry_f, None)
        if hint:
            out["省域提示"] = hint
    elif args.field == "sentencing" and entry_s:
        out = {"罪名": matched, "刑法条款": entry_s.get("article", "")}
        for tier_key in ["tier1", "tier2", "tier3"]:
            tier = entry_s.get(tier_key)
            if tier:
                out[tier.get("label", tier_key)] = {
                    "触发事实": tier.get("trigger", ""),
                    "刑期": tier.get("sentence", ""),
                    "刑期类型": tier.get("sentence_type", ""),
                }
        hint = province_hint(None, entry_s)
        if hint:
            out["省域提示"] = hint
    else:
        out = build_output(matched, entry_f, entry_s, index_flat.get(matched))

    print(json.dumps(envelope("ok", None, "查询成功", out), ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
