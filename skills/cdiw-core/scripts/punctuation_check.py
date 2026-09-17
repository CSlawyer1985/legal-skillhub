#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标点自检脚本（punctuation_check.py）。

功能：中文文书交付前的标点合规自检。检查三项——
  ① 直引号计数：U+0022（"）与 U+0027（'）出现次数必须为 0；
  ② 引号开合配对：中文弯引号“ ”与‘ ’、括号（）与书名号《》须开合数量相等；
  ③ 案卷摘录等原始提取文本可用 --exempt 豁免，保持原貌不作修正。

调用方式：
  python scripts/punctuation_check.py --path 03_正式文书/
  python scripts/punctuation_check.py --path 文书.md
  python scripts/punctuation_check.py --path working_notes/ --exempt

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0全部通过 / 1存在违规 / 2路径缺失 / 3读取失败；
  - 错误码：MISSING_PARAM / NOT_FOUND / INVALID / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_NAME = "punctuation_check"

# 直引号（禁止出现）与成对标点（须开合相等）
STRAIGHT = {'"': "U+0022 直双引号", "'": "U+0027 直单引号"}
PAIRS = [("“", "”", "中文双引号"), ("‘", "’", "中文单引号"),
         ("（", "）", "全角括号"), ("《", "》", "书名号")]

TEXT_EXT = {".md", ".txt", ".markdown"}

# 行内代码：反引号包裹片段，其中的引号与括号属代码语法
RE_INLINE_CODE = re.compile(r"`[^`\n]*`")


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


def strip_frontmatter(text):
    """剔除 YAML frontmatter——其定界引号属语法而非散文，不参与标点自检。"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1:])
    return text


def strip_code_blocks(text):
    """剔除围栏代码块（```）与行内代码（`…`）——
    其中引号、括号属代码语法（如 JSON 数组 `["6个月-1年"]`）而非散文，不参与标点自检。"""
    out, in_fence = [], False
    for ln in text.split("\n"):
        if ln.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(RE_INLINE_CODE.sub(" ", ln))
    return "\n".join(out)


def check_text(text, fn):
    """返回 (违规项列表, 统计字典)。检查前先剔除 frontmatter 与代码块——
    二者内的引号与括号属语法而非散文（定界符、JSON/YAML 结构），不参与标点自检。"""
    text = strip_code_blocks(strip_frontmatter(text))
    issues, stats = [], {}
    for ch, desc in STRAIGHT.items():
        n = text.count(ch)
        stats[desc] = n
        if n:
            issues.append({"type": "直引号", "detail": "%s 出现 %d 次，须为 0" % (desc, n),
                           "count": n})
    for op, cl, desc in PAIRS:
        no, nc = text.count(op), text.count(cl)
        stats[desc] = {"开": no, "合": nc}
        if no != nc:
            issues.append({"type": "开合配对", "detail": "%s 开 %d 个、合 %d 个，数量不等" % (desc, no, nc),
                           "count": abs(no - nc)})
    return issues, stats


def main():
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="标点自检：直引号计数必须为 0、引号开合数量须配对。")
    ap.add_argument("--path", required=True, help="待检文件或目录路径")
    ap.add_argument("--exempt", action="store_true",
                    help="豁免模式：仅统计不判定违规（用于案卷摘录等原始提取文本）")
    args = ap.parse_args()
    tid = make_trace_id()

    if not args.path or not os.path.exists(args.path):
        emit(envelope("error", "NOT_FOUND",
                      "路径缺失：%s" % args.path, {"trace_id": tid}), 2)

    files = collect_files(args.path)
    if not files:
        emit(envelope("error", "NOT_FOUND",
                      "路径下无可检文本文件（支持 %s）：%s" % ("/".join(sorted(TEXT_EXT)), args.path),
                      {"trace_id": tid}), 2)

    results, bad = [], 0
    for fn in files:
        try:
            with open(fn, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            emit(envelope("error", "ERR_IO", "文件读取失败：%s（%s）" % (fn, exc),
                          {"trace_id": tid}), 3)
        issues, stats = check_text(text, fn)
        if issues and not args.exempt:
            bad += 1
        results.append({"file": fn, "issues": issues, "stats": stats,
                        "verdict": "PASS" if (not issues or args.exempt) else "FAIL"})

    total_issues = sum(len(r["issues"]) for r in results)
    msg = ("豁免模式：%d 个文件已统计，违规 %d 处（不判定）" % (len(files), total_issues)
           if args.exempt else
           ("PASS：%d 个文件全部通过标点自检" % len(files) if bad == 0
            else "FAIL：%d/%d 个文件存在标点违规，共 %d 处" % (bad, len(files), total_issues)))
    emit(envelope("ok" if bad == 0 else "error", None if bad == 0 else "INVALID", msg,
                  {"trace_id": tid, "exempt": args.exempt, "file_count": len(files),
                   "bad_files": bad, "issue_count": total_issues, "files": results}),
         0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
