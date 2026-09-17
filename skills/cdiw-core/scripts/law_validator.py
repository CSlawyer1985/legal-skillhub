#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法条引用校验脚本（law_validator.py）。

功能：校验法条引用的现行有效性。校验是确定性的——脚本比对JSON数据，
不依赖模型判断。数据源：assets/data/law_effectiveness.json＋
assets/data/citation_blacklist.json。

调用方式：
  python scripts/law_validator.py --law 刑法 --article 第17条
  python scripts/law_validator.py --law 法发〔2020〕31号

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}，data含现行有效状态、
    所属修正版本、施行日期、修正前主要变化点、是否属于禁止引用范围、校验结论；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3计算或校验失败；
  - 错误码：ERR_ARGS_MISSING / ERR_LAW_NOT_FOUND / ERR_BLACKLIST_HIT / ERR_LAW_ABOLISHED / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_NAME = "law_validator"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "data")

LAW_GROUPS = ["刑法", "刑事诉讼法", "司法解释与指导意见", "公安机关办理刑事案件程序规定",
              "公安机关办理刑事复议复核案件程序规定", "查封冻结措施有关规定", "经济犯罪案件规定",
              "民法典", "律师法", "立案追诉标准"]


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


def normalize_article(article):
    """“17”“第17条”“第17条第3款”统一归一为条级键“第17条”。"""
    m = re.match(r"第?(\d+)条", article.strip())
    if m:
        return "第%s条" % m.group(1)
    return article.strip()


def _strip_parens(s):
    """去除全角/半角括号，供简称模糊匹配（“量刑指导意见二”可命中“量刑指导意见（二）”）。"""
    return re.sub(r"[（）()]", "", str(s))


def find_entry(law_db, law, article):
    """定位法条条目：支持（法律名, 条号）与（完整文号/名称）两种检索。"""
    if article:
        art = normalize_article(article)
        group = law_db.get(law)
        if isinstance(group, dict):
            if art in group:
                return law, art, group[art]
            # 模糊匹配：键含目标条号
            for k, v in group.items():
                if k.startswith(art) or art in k:
                    return law, k, v
        # 法律名可能是别名/简称：先按条目name定位组，再在组内匹配条号；
        # 名称命中但条号不在该组的，跳过继续找（防止简称误命中他组条文）
        for gname, group in law_db.items():
            if not isinstance(group, dict):
                continue
            name_hit = any(
                isinstance(v, dict) and (_strip_parens(law) in _strip_parens(v.get("name", "") + v.get("full_name", "")) or law in (v.get("name", "") + v.get("full_name", "")))
                for v in group.values() if isinstance(v, dict))
            if not name_hit:
                continue
            if art in group:
                return gname, art, group[art]
            for k, v in group.items():
                if k.startswith(art) or art in k:
                    return gname, k, v
        return None, None, None
    # 无条号：law本身可能是文号或名称键
    for gname in LAW_GROUPS:
        group = law_db.get(gname)
        if isinstance(group, dict) and law in group:
            return gname, law, group[law]
    for gname, group in law_db.items():
        if isinstance(group, dict):
            for k, v in group.items():
                if isinstance(v, dict) and (law in str(v.get("name", "")) + str(v.get("full_name", "")) or _strip_parens(law) in _strip_parens(str(v.get("name", "")) + str(v.get("full_name", "")))):
                    return gname, k, v
    return None, None, None


def check_blacklist(blacklist_db, law, article, entry):
    """检查是否命中禁止引用清单（已废止罪名/已失效司法解释/虚构案号特征/无法溯源内部口径）。"""
    hits = []
    for category, items in (blacklist_db or {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            keys = [str(item.get("name", "")), str(item.get("doc_no", "")),
                    str(item.get("keyword", ""))]
            target = law or ""
            if article:
                target = "%s%s" % (law, article)
            for key in keys:
                if key and key in target:
                    hits.append({"category": category, "hit": key,
                                 "reason": item.get("abolish_basis") or item.get("reason", "")})
    return hits


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="法条引用校验：核验现行有效性与禁止引用范围（确定性比对，不依赖模型判断）。")
    parser.add_argument("--law", required=True, help="法律名称（如：刑法、刑事诉讼法、法发〔2020〕31号）")
    parser.add_argument("--article", help="条号（如：第17条、第81条第1款）")
    args = parser.parse_args()
    trace_id = make_trace_id()

    law_db = load_json(os.path.join(DATA_DIR, "law_effectiveness.json"))
    if not law_db:
        print(json.dumps(envelope("error", "ERR_IO", "law_effectiveness.json缺失或为空", None),
                         ensure_ascii=False, indent=2))
        sys.exit(2)
    blacklist_db = load_json(os.path.join(DATA_DIR, "citation_blacklist.json")) or {}

    gname, key, entry = find_entry(law_db, args.law, args.article)
    blacklist_hits = check_blacklist(blacklist_db, args.law, args.article, entry)

    if blacklist_hits:
        print(json.dumps(envelope("error", "ERR_BLACKLIST_HIT",
                                  "命中禁止引用清单，禁止引用",
                                  {"trace_id": trace_id, "hits": blacklist_hits}),
                         ensure_ascii=False, indent=2))
        sys.exit(3)

    if entry is None:
        print(json.dumps(envelope("error", "ERR_LAW_NOT_FOUND",
                                  "法条不在数据文件中：触发人工核实流程（禁止由模型编造），请律师核实后更新law_effectiveness.json",
                                  {"trace_id": trace_id, "law": args.law,
                                   "article": args.article}),
                         ensure_ascii=False, indent=2))
        sys.exit(3)

    status = entry.get("status", "现行有效")
    # 废止/失效拦截（状态含"废止"或"失效"即禁止引用，输出替代依据）
    if ("废止" in status) or ("失效" in status):
        print(json.dumps(envelope("error", "ERR_LAW_ABOLISHED",
                                  "该法条/文件已废止或失效，禁止引用；替代依据见prior_changes",
                                  {"trace_id": trace_id, "law_group": gname, "key": key,
                                   "name": entry.get("name", ""),
                                   "status": status,
                                   "prior_changes": entry.get("prior_changes", ""),
                                   "verdict": "禁止引用：%s——按prior_changes所载现行替代依据引用" % status}),
                         ensure_ascii=False, indent=2))
        sys.exit(3)

    data = {
        "trace_id": trace_id,
        "law_group": gname,
        "key": key,
        "name": entry.get("name", ""),
        "current_effective": status,
        "version": entry.get("version", ""),
        "effective_date": entry.get("effective_date", ""),
        "prior_changes": entry.get("prior_changes", ""),
        "blacklist_hit": False,
        "verdict": "通过：现行有效，可引用；引用时标注%s（施行日期%s）" % (
            entry.get("version", "现行版本"), entry.get("effective_date", "见数据文件")),
    }
    # 非废止但非完全现行有效（如"部分废止或失效"）的警示
    if status != "现行有效":
        data["verdict"] = "有条件通过：状态为「%s」——须核对引用的具体条文/部分未被废止；%s" % (
            status, entry.get("prior_changes", "")[:120])
    print(json.dumps(envelope("ok", None, "校验通过", data), ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
