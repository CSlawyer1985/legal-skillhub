#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引用台账核验脚本（citation_audit.py）。

功能：提取输出文件中的法条／案例／数据引用，与引用台账（citation_ledger.jsonl）
逐条比对，输出断链清单。承载大纲 7.2 第 8 条"引用台账强制登记、输出前逐条核验"。

调用方式：
  python scripts/citation_audit.py --output 03_正式文书/20260831_取保候审申请书_辩护人.md \
      --ledger citation_ledger.jsonl
  python scripts/citation_audit.py --output 03_正式文书/ --ledger citation_ledger.jsonl

识别的引用形态：
  - 法条：《法规名称》第N条（可含"之X"、第N条第M款）
  - 案例：〔……号〕 或 （20XX）……号

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0全部对上 / 1存在断链 / 2文件缺失 / 3读取失败；
  - 错误码：MISSING_PARAM / NOT_FOUND / INVALID / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_NAME = "citation_audit"

# 法条：《名称》[（版本时点括注）]第N条[之X]——容许名称与条号之间夹版本括注、数字与“第/条”间含空格
RE_LAW = re.compile(r"《([^》]+)》[^《]{0,30}?第\s*([零一二三四五六七八九十百千〇0-9]+)\s*条"
                    r"(?:之\s*([零一二三四五六七八九十〇0-9]+))?")
# 案例：〔……号〕 或 （20XX）……号
RE_CASE = re.compile(r"[〔［]([^〕］]{4,}?号)[〕］]|（(20\d{2})）([^）]{2,40}?号)")

TEXT_EXT = {".md", ".txt", ".markdown"}


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def emit(env, code):
    print(json.dumps(env, ensure_ascii=False, indent=2))
    sys.exit(code)


def collect_files(path):
    if os.path.isfile(path):
        return [path]
    out = []
    for dp, _, fns in os.walk(path):
        for fn in sorted(fns):
            if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                out.append(os.path.join(dp, fn))
    return sorted(out)


def load_ledger(path):
    """返回 (条目列表, 合并文本, 去空格文本)；条目为 JSONL 一行一事件。

    去空格文本用于比对——台账中条文常写作“第 67 条”（数字两侧含空格），
    而引用键归一化为“第67条”，两边须在同一口径下比较。
    """
    items, blob = [], []
    with open(path, "r", encoding="utf-8") as f:
        for ln_no, ln in enumerate(f, 1):
            ln = ln.strip()
            if not ln:
                continue
            blob.append(ln)
            try:
                items.append(json.loads(ln))
            except ValueError:
                items.append({"_parse_error": True, "_line": ln_no, "raw": ln})
    joined = "\n".join(blob)
    # 归一化：去空格与书名号，使“《刑事诉讼法》第 67 条”与键“刑事诉讼法第67条”可比
    norm = re.sub(r"[\s《》]+", "", joined)
    return items, joined, norm


def extract_refs(text):
    """从输出文本提取引用项，返回 [(类型, 规范化键, 原文片段)]。"""
    refs = []
    for m in RE_LAW.finditer(text):
        name, art, sub = m.group(1), m.group(2), m.group(3)
        key = "%s第%s条%s" % (name, art, ("之" + sub) if sub else "")
        refs.append(("法条", key, m.group(0)))
    for m in RE_CASE.finditer(text):
        raw = m.group(1) or (m.group(2) + m.group(3))
        key = re.sub(r"\s+", "", raw)
        refs.append(("案例", key, m.group(0)))
    # 去重保序
    seen, out = set(), []
    for r in refs:
        if r[1] in seen:
            continue
        seen.add(r[1])
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME, description="引用台账核验：输出引用与台账逐条比对，输出断链清单。")
    ap.add_argument("--output", required=True, help="输出文件或目录路径")
    ap.add_argument("--ledger", required=True, help="引用台账路径（citation_ledger.jsonl）")
    args = ap.parse_args()
    tid = make_trace_id()

    for label, p in (("--output", args.output), ("--ledger", args.ledger)):
        if not os.path.exists(p):
            emit(envelope("error", "NOT_FOUND", "%s 路径缺失：%s" % (label, p),
                          {"trace_id": tid}), 2)

    try:
        items, ledger_blob, ledger_nospace = load_ledger(args.ledger)
    except (OSError, UnicodeDecodeError) as exc:
        emit(envelope("error", "ERR_IO", "台账读取失败：%s（%s）" % (args.ledger, exc),
                      {"trace_id": tid}), 3)

    files = collect_files(args.output)
    if not files:
        emit(envelope("error", "NOT_FOUND", "无可检输出文件：%s" % args.output,
                      {"trace_id": tid}), 2)

    broken, matched, total = [], [], 0
    for fn in files:
        try:
            with open(fn, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            emit(envelope("error", "ERR_IO", "输出文件读取失败：%s（%s）" % (fn, exc),
                          {"trace_id": tid}), 3)
        for kind, key, raw in extract_refs(text):
            total += 1
            key_norm = re.sub(r"[\s《》]+", "", key)
            raw_norm = re.sub(r"[\s《》]+", "", raw)
            hit = (key in ledger_blob or raw in ledger_blob
                  or key_norm in ledger_nospace or raw_norm in ledger_nospace)
            rec = {"file": fn, "type": kind, "key": key, "raw": raw}
            if hit:
                matched.append(rec)
            else:
                rec["reason"] = "台账中无对应条目（未登记或位置不一致）"
                broken.append(rec)

    parse_err = [i for i in items if i.get("_parse_error")]
    msg = ("PASS：%d 项引用全部在台账中登记" % total if not broken
           else "FAIL：%d 项引用中 %d 项断链" % (total, len(broken)))
    emit(envelope("ok" if not broken else "error", None if not broken else "INVALID", msg,
                  {"trace_id": tid, "output_files": len(files),
                   "ledger_entries": len(items), "ref_total": total,
                   "matched": len(matched), "broken": broken,
                   "ledger_parse_errors": parse_err,
                   "note": "无台账支撑的输出视为不合格（7.2 第 8 条）"}),
         0 if not broken else 1)


if __name__ == "__main__":
    main()
