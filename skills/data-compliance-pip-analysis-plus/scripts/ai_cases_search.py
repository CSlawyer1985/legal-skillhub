#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金杜中国 AI 司法实践案例图谱（80 例）本地检索工具。

用法示例：
  python search.py --keyword 声音
  python search.py --issue "AIGC可版权性" --year 2025
  python search.py --court 北京互联网法院
  python search.py --tech AI数字人 --province 浙江省
  python search.py --no 12                 # 查看单案详情
  python search.py --full "实质性相似"      # 检索原文正文（需 references/raw）
  python search.py --stats
  python search.py --all
"""
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "references")
RAW = os.path.join(BASE, "references", "ai_cases_raw")
META = "典型案例库_AI司法实践案例图谱_金杜81例.md"
CASES = json.load(open(os.path.join(DATA, "ai_cases.json"), encoding="utf-8"))


def match(c, args):
    if args.no and c["no"] != args.no.zfill(2):
        return False
    if args.level and c.get("level") != args.level.upper():
        return False
    if args.province and args.province not in c["province"]:
        return False
    if args.court and args.court not in c["city"]:
        return False
    if args.issue and args.issue != c.get("issue"):
        return False
    if args.tech and args.tech not in (c.get("tech") or []):
        return False
    if args.year and str(c.get("year")) != str(args.year):
        return False
    if args.status and args.status != c.get("procStatus"):
        return False
    if args.case_no and args.case_no not in (c.get("caseNumber") or ""):
        return False
    return True


def hit_kw(c, kw):
    blob = " ".join([c["title_zh"], c.get("title_en", ""), c["city"],
                     c.get("caseNumber", ""), c.get("issue", ""),
                     " ".join(c.get("tech") or []), c.get("procStatus", ""),
                     c.get("firstCourt_zh", ""), c.get("firstCaseNo_zh", "")])
    return all(k.lower() in blob.lower() for k in kw)


def fmt(c, verbose=False):
    s = "[%s][%s类] %s\n  法院：%s（%s）  案号：%s  年份：%s\n  焦点：%s  技术：%s  状态：%s" % (
        c["no"], c.get("level", "-"), c["title_zh"], c["city"], c["province"],
        c.get("caseNumber") or "案号未公开", c.get("year", ""),
        c.get("issue", ""), "、".join(c.get("tech") or []), c.get("procStatus", ""))
    if c.get("note_dc"):
        s += "\n  关联要点：%s" % c["note_dc"]
    if c.get("firstCourt_zh"):
        s += "\n  一审：%s %s" % (c["firstCourt_zh"], c.get("firstCaseNo_zh") or "")
    if c.get("kwInsight"):
        s += "\n  金杜解读：%s" % c["kwInsight"]
    s += "\n  原文：%s" % c["url"]
    if verbose:
        p = os.path.join(RAW, "%s.md" % c["no"])
        s += "\n  本地原文：%s" % (p if os.path.exists(p) else "（未抓取）")
    return s


def search_full(kws, limit=3):
    if not os.path.isdir(RAW):
        print("未找到原文目录 references/raw"); return
    for c in CASES:
        p = os.path.join(RAW, "%s.md" % c["no"])
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8", errors="ignore").read()
        low = t.lower()
        pos = [low.find(k.lower()) for k in kws]
        if all(x >= 0 for x in pos):
            print("[%s] %s" % (c["no"], c["title_zh"]))
            for k, x in zip(kws, pos):
                seg = t[max(0, x - 120): x + 200].replace("\n", " ")
                print("    …%s…" % seg)
            print("    原文：%s\n" % c["url"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", help="关联度分层 A/B/C/D（A=直接相关）")
    ap.add_argument("--keyword", "-k", nargs="*", help="关键词（匹配标题/法院/案号/焦点/技术）")
    ap.add_argument("--province", help="省份（模糊包含）")
    ap.add_argument("--court", help="审理法院（模糊包含）")
    ap.add_argument("--issue", help="争议焦点（精确，见 stats.md）")
    ap.add_argument("--tech", help="AI 技术类型（精确）")
    ap.add_argument("--year")
    ap.add_argument("--status", help="审理状态（精确）")
    ap.add_argument("--case-no", dest="case_no", help="案号片段")
    ap.add_argument("--no", help="案例编号，如 12")
    ap.add_argument("--full", nargs="+", help="检索原文正文并输出上下文")
    ap.add_argument("--all", action="store_true", help="列出全部 80 例")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    if a.stats:
        print(open(os.path.join(DATA, META), encoding="utf-8").read()[:6000]); return
    if a.full:
        search_full(a.full); return

    res = [c for c in CASES if match(c, a)]
    if a.keyword:
        res = [c for c in res if hit_kw(c, a.keyword)]
    if not any([a.keyword, a.province, a.court, a.issue, a.tech, a.year,
                a.status, a.case_no, a.no, a.all, a.level]):
        ap.print_help(); return

    print("命中 %d 例：\n" % len(res))
    for c in res:
        print(fmt(c, a.verbose)); print()


if __name__ == "__main__":
    sys.exit(main())
