#!/usr/bin/env python3
"""
合并 L1（微信读书）+ L2（元宝补充）候选 → candidates_merged.jsonl

规则：
  - 以 L1 为主，L2 补充 L1 缺失本号原文的条目（元宝反查命中 mp 直链时覆盖）
  - 去重按 URL；冲突以 L1 结果为准（微信读书更稳定）
  - 输出 5 字段：title/url/publish_time/digest/_source，无空值

用法：
  python3 scripts/merge_candidates.py
  python3 scripts/merge_candidates.py --check   # 只校验字段完整性，不写文件
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
L1_PATH = BASE / "mp_articles_weread.json"
L2_PATH = BASE / "yuanbao_links.json"
OUT_PATH = BASE / "candidates_merged.jsonl"

FIELDS = ["title", "url", "publish_time", "digest", "_source"]


def l2_to_l1(entry: dict, l1_by_key: dict) -> dict:
    """L2 条目转 5 字段（元宝反查命中 → 用元宝直链替换 L1 转载链接）。
    发布时间/摘要继承 L1 同标题条目（同一篇文章的属性与链接来源无关）。"""
    url = entry.get("mp_urls", [None])[0] if entry.get("mp_urls") else None
    if not url:
        url = entry.get("l1_url", "")  # 转载版：保留 L1 链接
    l1_src = l1_by_key.get((entry.get("title", ""), entry.get("account", "")))
    return {
        "title": entry.get("title", ""),
        "url": url,
        "publish_time": (l1_src or {}).get("publish_time", ""),
        "digest": (l1_src or {}).get("digest", "") or f"[元宝反查] {entry.get('query', '')}",
        "_source": entry.get("account", ""),
    }


def merge() -> list:
    l1 = json.loads(L1_PATH.read_text())
    l2 = json.loads(L2_PATH.read_text()) if L2_PATH.exists() else []

    merged = {}
    l1_by_key = {(a["title"], a["_source"]): a for a in l1}
    # L1 优先写入（冲突以 L1 为准）
    for a in l1:
        merged[a["url"]] = dict(a)

    # L2 仅在 URL 未出现过时补充；元宝命中直链且与 L1 转载链接不同 → 覆盖
    for e in l2:
        if e.get("status") == "元宝不可用":
            continue
        new_url = e.get("mp_urls", [None])[0] if e.get("mp_urls") else None
        l1_url = e.get("l1_url", "")
        if new_url and new_url not in merged:
            merged[new_url] = l2_to_l1(e, l1_by_key)
        elif not new_url and l1_url:
            # 转载版：L1 链接已在 merged 中，仅标记 digest 提示（不覆盖 L1 的 digest）
            if l1_url in merged and merged[l1_url].get("digest", "").startswith("[元宝"):
                pass  # 保持 L1 原文
        # new_url 与某 L1 相同 → 以 L1 为准（无需处理）

    return list(merged.values())


def validate(rows: list) -> list:
    """校验 5 字段无空值，返回问题列表"""
    problems = []
    for i, r in enumerate(rows):
        for f in FIELDS:
            v = r.get(f)
            if v is None or (isinstance(v, str) and not v.strip()):
                problems.append(f"line {i}: 字段 {f} 为空 -> {r}")
    return problems


def main():
    parser = argparse.ArgumentParser(description="合并 L1+L2 候选")
    parser.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = parser.parse_args()

    rows = merge()
    problems = validate(rows)
    if problems:
        print(f"❌ 字段完整性校验失败: {len(problems)} 处", file=sys.stderr)
        for p in problems[:10]:
            print(f"  {p}", file=sys.stderr)
        sys.exit(1)

    if args.check:
        print(f"✅ 校验通过: {len(rows)} 条候选，5 字段全部非空")
        return

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"✅ 合并完成: L1 {len(json.loads(L1_PATH.read_text()))} + L2 补充 → 候选 {len(rows)} 条，已写入 {OUT_PATH}")


if __name__ == "__main__":
    main()
