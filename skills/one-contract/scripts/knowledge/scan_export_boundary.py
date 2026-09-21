#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出前边界巡检 —— 确认技能包中不含不得外泄的内容。

与 `validate_assets.py` 的分工：
- `validate_assets.py` 管**资产一致性**与既有的三类隐私模式（用户路径/合同族 ID/长哈希）；
- 本脚本管**导出边界**，重点是**由外部禁词表驱动**的那部分。

**为什么禁词表在包外**：本脚本会随技能包一起交付，若把不得外泄的原作品名称、
作者名直接写在脚本里，脚本自身就构成泄漏。故禁词表必须放在**包外且不进版本库**
的位置（默认 `.local_data/export-boundary-denylist.txt`，该目录已在 .gitignore 中）。

用法：
    python scripts/knowledge/scan_export_boundary.py [--root <技能包根>] [--denylist <路径>]

退出码：0 = 通过；1 = 发现命中；2 = 有检查项**未执行**（禁词表缺失等），不得视为通过。
"""
import argparse
import json
import pathlib
import re
import sys

TEXT_EXT = {".md", ".json", ".py", ".txt", ".yaml", ".yml", ".sh", ".csv", ".html", ".xml"}

# 注意：以下模式刻意用**字符串拼接**构造，避免脚本自身出现被测字面量
# （既有代码 `validate_assets.py` 对用户路径采用同样做法）。
_A = "/" + "Users" + "/"
PATHS = {
    "absolute_user_path": re.compile(re.escape(_A)),
    "contract_family_id": re.compile(r"\bcf-[0-9a-f]{20}\b"),
    "long_hash": re.compile(r"\b[0-9a-f]{64}\b"),
    "book_page_number": re.compile(r"(?:\bp\.\s*\d{1,4}\b|P\d{2,3}\s*[–—-]|第\s*\d{1,4}\s*页)"),
}


def load_denylist(path: pathlib.Path):
    """返回 (词表, 错误)。文件不存在时返回 (None, 原因) —— 调用方须据此判『未检查』。"""
    if not path.exists():
        return None, f"禁词表不存在：{path}"
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        words.append(s)
    if not words:
        return None, f"禁词表为空：{path}"
    return words, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parents[2]),
                    help="技能包根目录（默认取脚本上溯两级）")
    ap.add_argument("--denylist", default=None,
                    help="禁词表路径（默认：<包根>/../../../.local_data/export-boundary-denylist.txt）")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    if args.denylist:
        dl_path = pathlib.Path(args.denylist).resolve()
    else:
        # 向上查找含 .local_data 的目录，而不是数 parents[i]——层级数错过一次。
        dl_path = None
        for anc in [root, *root.parents]:
            cand = anc / ".local_data" / "export-boundary-denylist.txt"
            if cand.exists():
                dl_path = cand
                break
        if dl_path is None:
            dl_path = root / ".local_data" / "export-boundary-denylist.txt"  # 仅为报错显示

    words, err = load_denylist(dl_path)

    findings = []
    files_scanned = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.casefold() not in TEXT_EXT:
            continue
        if "__pycache__" in path.parts:
            continue
        # 禁词表自身不是交付物——若它恰好位于 root 内（配置失误），不得据以自命中。
        if words is not None and path.resolve() == dl_path:
            continue
        files_scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root)
        for name, pat in PATHS.items():
            m = pat.search(text)
            if m:
                findings.append({"kind": name, "file": str(rel), "match": m.group(0)[:60]})
        if words:
            for w in words:
                if w in text:
                    findings.append({"kind": "denylist_hit", "file": str(rel),
                                     "match": f"<禁词 #{words.index(w) + 1}>"})

    # ── 状态判定：**未执行 ≠ 通过** ──
    skipped = []
    if words is None:
        skipped.append({"check": "denylist_scan", "reason": err,
                        "consequence": "原作品名称/作者名等禁词**未被检查**，本次结论不覆盖该项"})

    if findings:
        status, code = "fail", 1
    elif skipped:
        status, code = "incomplete", 2
    else:
        status, code = "pass", 0

    out = {
        "status": status,
        "root": str(root),
        "denylist": str(dl_path) if words is not None else None,
        "denylist_terms": len(words) if words else 0,
        "files_scanned": files_scanned,
        "findings": findings,
        "checks_skipped": skipped,
        "note": "status=incomplete 表示有检查项未执行，**不得视为通过**；"
                "status=pass 仅在全部检查均已执行且无命中时给出。",
    }
    # 命中详情要能给出文件与片段（片段本身可能含敏感词，故不打印 match 全文到 stdout 之外）
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
