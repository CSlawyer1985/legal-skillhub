#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_hf_sft.py —— 从 HuggingFace 数据集抽取「社区校验问答」seed（安全路径）

数据源：sdzjoy/fire-safety-sft-dataset（Apache-2.0，38k+ 消防国标 Q&A/SFT 对）
源标准：GB 50016-2014 / 50067-2014 / 51251-2017 / 55036-2022 / 55037-2022

【安全边界 · 重要】
  - 本脚本**只抽取 Q&A 对 + 元数据索引（条文号/标准/类别）**，**绝不复制标准正文的逐字文本**。
  - 写入的条目是数据集作者按 Apache-2.0 发布的**编译成果（Q&A）**，自带许可授权；
    即便 assistant 回答中引用了少量标准片段，也属于该 Q&A 编译的一部分，随数据集整体按 Apache-2.0 再分发。
  - 每条标注 `⏳ 待官方核对`：**这不是权威金标准**，仅供 reconcile 交叉核对 / 启发式参考；
    引用任何具体数值或条文前，必须先用「模式一」在 openstd.samr.gov.cn 官方源核实。
  - 机器永不把这里的 ⏳ 自动升为 ✅；如需晋升，须人工经官方源核对后另走 golden.py confirm。

输出：references/golden/seed_hf_sft.md
  - 顶部含 Apache-2.0 署名（数据集名 / 作者 sdzjoy / License / URL）+ 修改声明 + 版权边界。
  - 每条块用 `### [HF-SFT] #n` 标记，与 golden.py 的 `### <规范> 第 <条款> 条` 条款键**不冲突**，
    也不会被 refresh_golden.py 误当成权威条款刷新。

依赖：huggingface_hub（pip install huggingface_hub）；标准库 json/os/argparse。
用量：默认抽取 300 条（--limit）；--all 抽全部（约 5.4 万条，文件较大，建议在本地/私有副本使用）。
"""

import os
import sys
import json
import argparse
import datetime
import tempfile

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    sys.exit("[错误] 缺少依赖 huggingface_hub。请运行：pip install huggingface_hub")

REPO = "sdzjoy/fire-safety-sft-dataset"
DEFAULT_FILE = "data/train.jsonl"
DATASET_URL = "https://huggingface.co/datasets/sdzjoy/fire-safety-sft-dataset"
LICENSE = "Apache-2.0"


def _base():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _default_out():
    return os.path.join(_base(), "references", "golden", "seed_hf_sft.md")


def _extract_qa(obj):
    """从一条 jsonl 抽取 (question, answer, meta_dict)。失败返回 None。"""
    msgs = obj.get("messages") or []
    if not isinstance(msgs, list):
        return None
    q = a = None
    for m in msgs:
        role = (m.get("role") or "").lower()
        content = (m.get("content") or "").strip()
        if role == "user" and not q:
            q = content
        elif role == "assistant" and not a:
            a = content
    if not q or not a:
        return None
    meta = obj.get("metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    return q, a, meta


def _fmt_block(n, q, a, meta):
    source = meta.get("source") or ""
    articles = meta.get("source_articles") or []
    if isinstance(articles, list):
        articles = ", ".join(str(x) for x in articles)
    category = meta.get("category") or ""
    topic = meta.get("topic") or ""
    return (
        f"\n### [HF-SFT] #{n}\n"
        f"- 问：{q}\n"
        f"- 答：{a}\n"
        f"- 出处标准：{source}\n"
        f"- 条文索引：{articles}\n"
        f"- 类别：{category} · 主题：{topic}\n"
        f"- 来源数据集：{REPO} ({LICENSE})\n"
        f"- 核对状态：⏳ 待官方核对\n"
    )


def _header(count, limit):
    today = datetime.date.today().isoformat()
    return (
        "# 社区校验问答 seed（HF-SFT）\n\n"
        "> **数据来源**：HuggingFace 数据集 [`sdzjoy/fire-safety-sft-dataset`](%s)（%s License）\n"
        "> **原作者/发布者**：sdzjoy ｜ **生成日期**：%s ｜ **本批条目**：%s\n"
        "> **本文件由 `scripts/import_hf_sft.py` 自动抽取生成**：仅含 Q&A 对 + 元数据索引（条文号/标准/类别），**未复制标准正文逐字文本**。\n"
        ">\n"
        "> ⚠️ **版权与边界**：GB 国家标准正文版权归住建部 / 市场监管总局（MOHURD / SAMR）。本文件再分发的是数据集作者按 %s 发布的 **Q&A 编译成果**；\n"
        "> 引用其中任何具体数值或条文前，必须先用「模式一」在官方源 `openstd.samr.gov.cn` 核实。\n"
        "> ⚠️ **信任边界**：每条均为 `⏳ 待官方核对`，**不是权威金标准**；仅供 reconcile 交叉核对 / 启发式参考，**禁止作为 ✅ 直接输出**。\n"
        "> **修改声明**：本 seed 由 china-fire-code skill 抽取聚合，非数据集原文件；如需完整数据请访问上述 HuggingFace 仓库。\n\n"
        "---\n"
        % (DATASET_URL, LICENSE, today, count, LICENSE)
    )


def main():
    ap = argparse.ArgumentParser(
        description="从 HF 数据集抽取社区校验问答 seed（仅 Q&A + 元数据，带 Apache-2.0 署名）"
    )
    ap.add_argument("--repo", default=REPO, help="HuggingFace 数据集 repo id")
    ap.add_argument("--file", default=DEFAULT_FILE, help="数据集内 jsonl 文件，默认 data/train.jsonl")
    ap.add_argument("--limit", type=int, default=300, help="抽取条数上限（0 或 --all 表示全部）")
    ap.add_argument("--all", action="store_true", help="抽取全部条目（约 5.4 万，文件较大）")
    ap.add_argument("--out", default=_default_out(), help="输出 seed 文件路径")
    ap.add_argument("--cache-dir", default=None, help="下载缓存目录（默认系统临时目录）")
    args = ap.parse_args()

    limit = 0 if args.all else max(0, args.limit)

    print(f"[下载] {args.repo} :: {args.file} ...")
    cache = args.cache_dir or tempfile.mkdtemp(prefix="hf_fire_")
    try:
        path = hf_hub_download(
            repo_id=args.repo, repo_type="dataset", filename=args.file, local_dir=cache
        )
    except Exception as e:  # noqa: BLE001
        sys.exit(f"[错误] 下载失败：{e}\n提示：检查网络；如需更高限速可设 HF_TOKEN 环境变量。")

    print(f"[读取] {path}")
    seen = set()
    blocks = []
    total = 0
    skipped_dup = 0
    bad = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            ext = _extract_qa(obj)
            if not ext:
                continue
            q, a, meta = ext
            key = q.strip()
            if key in seen:
                skipped_dup += 1
                continue
            seen.add(key)
            total += 1
            blocks.append(_fmt_block(total, q, a, meta))
            if limit and total >= limit:
                break

    out = args.out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    header = _header(total, "全部" if limit == 0 else f"前 {total} 条（上限 {limit}）")
    with open(out, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("".join(blocks))

    rel = os.path.relpath(out, _base())
    print(f"[完成] 抽取 {total} 条（跳过重复 {skipped_dup}，坏行 {bad}）")
    print(f"[写入] {rel}  （每条 ⏳ 待官方核对，Apache-2.0 署名已写入文件头）")
    if limit == 0:
        print("提示：本次为全量导入，文件较大；建议仅在本地/私有副本保留，勿大批量提交到公开仓库。")


if __name__ == "__main__":
    main()
