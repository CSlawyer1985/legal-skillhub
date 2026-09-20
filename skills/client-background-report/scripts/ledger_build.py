#!/usr/bin/env python3
"""证据账本自动构建器：把 MCP 采集原始 JSON 汇总为账本草稿，AI 只做判断题。
用法: python3 scripts/ledger_build.py <output/XX背调目录>
读取 采集原始数据/*.json，逐文件提取"摘要/搜索结果"与关键数字，
生成 证据账本_机器草稿.md（status 一律"待AI判断"，由 AI 确认后并入正式证据账本）。
"""
import glob
import json
import os
import re
import sys


def find_keys(obj, keys=("摘要", "搜索结果", "提示")):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.strip() in keys and isinstance(v, str):
                return v
            r = find_keys(v, keys)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_keys(v, keys)
            if r:
                return r
    return None


def extract(f):
    d = json.load(open(f, encoding="utf-8"))
    if isinstance(d, dict) and "error" in d:
        return None, f"调用报错: {str(d['error'])[:120]}"
    try:
        text = "\n".join(x.get("text", "") for x in d["result"]["content"]
                         if isinstance(x, dict))
    except Exception:
        return None, json.dumps(d, ensure_ascii=False)[:200]
    try:
        inner = json.loads(text)
        found = find_keys(inner)
        if found:
            return found, None
        if isinstance(inner, dict):
            kv = [f"{k}:{v}" for k, v in inner.items()
                  if isinstance(v, (str, int, float)) and len(str(v)) < 60]
            if kv:
                return "；".join(kv[:12]), None
    except Exception:
        pass
    return text[:200], None


def main(outdir):
    raw = os.path.join(outdir, "采集原始数据")
    files = sorted(glob.glob(os.path.join(raw, "*.json")))
    if not files:
        print("未找到采集原始数据，先运行 mcp_collect.py")
        sys.exit(1)
    rows = []
    for i, f in enumerate(files, 1):
        base = os.path.basename(f)[:-5]
        parts = base.split("_")
        dim = "_".join(parts[1:3]) if len(parts) > 3 else base
        tool = "_".join(parts[3:]) if len(parts) > 3 else parts[-1]
        summary, err = extract(f)
        note = err or summary
        rows.append(f"| M{i:02d} | {dim} | {tool} | {note} | MCP 接口 | 待AI判断 | |")
    out = os.path.join(outdir, "证据账本_机器草稿.md")
    with open(out, "w", encoding="utf-8") as fp:
        fp.write("# 证据账本（机器草稿，待 AI 逐条确认后并入正式账本）\n\n"
                 "| # | 维度 | 工具 | 摘要/关键数字 | 来源类型 | status | 备注 |\n"
                 "|---|------|------|------|------|------|------|\n"
                 + "\n".join(rows) + "\n")
    print(f"OK {len(rows)} 条 -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
