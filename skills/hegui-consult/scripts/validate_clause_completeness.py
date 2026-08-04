#!/usr/bin/env python3
"""确定性校验：拟发送答复是否完整、逐字引用了目标法规条文（从本条条号到下一条同级条号之前）。

只查格式与完整性，不判法规适用性（适用性由 Skill 的证据闸门处理）。

用法：
  python validate_clause_completeness.py \
    --source-text 正式附件提取出的全文.txt \
    --article 6.2.11 \
    --answer 待发送答复.txt

输出 JSON：
  {"article","source_found","next_article_found","complete_match","ellipsis_detected","missing_segments"}
退出码：0=complete_match 且无人工省略号；1=不完整/有省略号；2=未在源文中定位到该条。
"""
import argparse
import json
import re
import sys

# 条号形态：交易所层级编号 6.2.11 / 7.2.1；或 第六条 / 第六十三条 / 第六条之一
DOTTED = r"\d+(?:\.\d+)+"
CN_NUM = r"[一二三四五六七八九十百千零〇两]+"
CN_ART = rf"第{CN_NUM}条(?:之{CN_NUM})?"
ANY_ARTICLE = re.compile(rf"(?:{DOTTED}|{CN_ART})")
ELLIPSIS = re.compile(r"……|…|\.\.\.|（?略）?|以下省略|节选|部分略")


def norm(s: str) -> str:
    """仅做空白规范化，用于逐字包含比对。"""
    return re.sub(r"\s+", "", s or "")


def same_level_pattern(article: str) -> re.Pattern:
    """给定目标条号，返回匹配"下一条同级条号"的正则。"""
    if re.fullmatch(DOTTED, article):
        depth = article.count(".") + 1
        seg = r"\d+(?:\.\d+){%d}" % (depth - 1)
        return re.compile(seg)
    return re.compile(CN_ART)


def locate_clause(source: str, article: str):
    """在源全文中截取 [目标条号, 下一条同级条号) 之间的完整条文。"""
    esc = re.escape(article)
    m = re.search(esc, source)
    if not m:
        return None, False
    start = m.start()
    level = same_level_pattern(article)
    next_found = False
    end = len(source)
    for nm in level.finditer(source, m.end()):
        if nm.group(0) == article:
            continue
        end = nm.start()
        next_found = True
        break
    return source[start:end].strip(), next_found


def strip_leading_article(clause: str) -> str:
    """去掉条文开头的条号（其呈现方式在答复里常带不同标点/空格，逐字比对易误判）。"""
    m = ANY_ARTICLE.match(clause.lstrip())
    return clause.lstrip()[m.end():].lstrip() if m else clause


def split_segments(clause: str):
    """把条文正文（已去条号）粗分为段（自然段/款/项），用于逐段核验与报告缺失片段。"""
    parts = re.split(r"\n+|(?=（[一二三四五六七八九十]+）)|(?=[一二三四五六七八九十]+、)", clause)
    return [p.strip() for p in parts if len(norm(p)) >= 4]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-text", required=True, help="正式附件提取后的全文文件路径")
    ap.add_argument("--article", required=True, help="目标条号，如 6.2.11 或 第六条")
    ap.add_argument("--answer", required=True, help="待发送答复文件路径")
    args = ap.parse_args()

    source = open(args.source_text, encoding="utf-8", errors="ignore").read()
    answer = open(args.answer, encoding="utf-8", errors="ignore").read()

    clause, next_found = locate_clause(source, args.article)
    result = {
        "article": args.article,
        "source_found": clause is not None,
        "next_article_found": next_found,
        "complete_match": False,
        "ellipsis_detected": bool(ELLIPSIS.search(answer)),
        "missing_segments": [],
    }
    if clause is None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    # 逐段核验（对条号呈现差异更稳健）：正文每一段（款/项）都须逐字出现在答复里。
    na = norm(answer)
    segments = split_segments(strip_leading_article(clause))
    missing = [seg[:40] for seg in segments if norm(seg) not in na]
    result["complete_match"] = len(missing) == 0
    result["missing_segments"] = missing
    result["starts_with_article_number"] = norm(args.article) in na
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if (result["complete_match"] and not result["ellipsis_detected"]) else 1


if __name__ == "__main__":
    sys.exit(main())
