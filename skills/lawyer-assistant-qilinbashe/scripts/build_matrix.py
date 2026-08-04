#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""案卷精读辅助脚本：抽取文本 -> 证据清单 + 时间轴骨架 Markdown。
强哥「案卷精读·要件事实证据矩阵」技能的配套脚本。

功能：
  输入案卷 PDF / 图片 / 纯文本目录或文件，提取文本（有文字层用 fitz；无文字层自动 easyocr），
  按文件名识别「证据册 / 庭审笔录」，抽取关键法言法语（签名、捺印、房产证号、金额、日期、自认等），
  生成「证据清单 + 要件矩阵骨架 + 矛盾风险信号」Markdown 骨架到工作区，AI 再在骨架上填「要件事实—证据矩阵」。
  支持 --mask-names 对抽出的信号片段自动脱敏（隐私底线）。

用法：
  python build_matrix.py <案卷路径> [--out 输出.md] [--mask-names "真名=标签,真名=标签"]
  <案卷路径> 可为单个文件或目录。
  --mask-names 示例： "赵振福=产权人甲,赵四海=被告乙,赵春海=原告丙"
"""

import sys
import os
import re
import glob
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import easyocr
except ImportError:
    easyocr = None

_reader = None


def get_reader():
    global _reader
    if _reader is None and easyocr:
        _reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
    return _reader


def parse_mask(arg):
    """解析 --mask-names 参数。支持 '真名=标签' 或纯 '真名'（自动甲/乙/丙）。"""
    items = [x.strip() for x in arg.split(",") if x.strip()]
    table = {}
    for i, it in enumerate(items):
        if "=" in it:
            k, v = it.split("=", 1)
            table[k.strip()] = v.strip()
        else:
            label = "甲" if i == 0 else ("乙" if i == 1 else ("丙" if i == 2 else f"当事人{i + 1}"))
            table[it] = label
    return table


def apply_mask(text, mask_map):
    if not mask_map:
        return text
    for real, label in mask_map.items():
        if not real:
            continue
        text = text.replace(real, label)
    return text


# 关键信号词：用于自动标出易漏的硬事实点
SIGNAL_PATTERNS = {
    "签名/捺印": r"签名|签字|捺印|指印|手印|代签|代笔",
    "房产证/登记": r"房产证|房屋所有权证|产权人|权利人|登记|证号|NO\.?\d+",
    "金额": r"\d+\s*元|\d+\s*万|\d{4,}\s*元",
    "日期": r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    "自认": r"自认|承认|认可|我确实|我当时",
    "争议/异议": r"有异议|不认可|不予认可|真实性不予|矛盾|冲突",
    "继承/共有人": r"继承|共有人|共有|第一顺序|配偶|子女",
}


def classify(name):
    n = name.lower()
    if name.lower().endswith(".txt"):
        return "已OCR文本"
    if "笔录" in n or "庭审" in n:
        return "庭审笔录"
    if "证据" in n or "证(" in n or "证（" in n:
        return "证据册"
    return "其他材料"


def extract_text(path):
    """提取文本：.txt 直接读；.pdf 优先 fitz，无文字层自动 easyocr 兜底。"""
    if path.lower().endswith(".txt"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.read().splitlines()
            pages = [(i + 1, ln) for i, ln in enumerate(lines)]
            return pages, None
        except Exception as e:  # noqa
            return None, f"读取失败：{e}"
    if not fitz:
        return None, "fitz 未安装，请安装 PyMuPDF"
    try:
        doc = fitz.open(path)
        pages = []
        for i, page in enumerate(doc):
            txt = page.get_text()
            pages.append((i + 1, txt))
        doc.close()
        full = "\n".join(t for _, t in pages)
        if full.strip():
            return pages, None
        # 无文字层：尝试 easyocr
        if easyocr and get_reader():
            doc = fitz.open(path)
            out = []
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                import numpy as np  # noqa
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                    pix.height, pix.width, pix.n
                )[..., ::-1]
                res = get_reader().readtext(img, detail=0)
                out.append((i + 1, "\n".join(res)))
            doc.close()
            return out, None
        return None, "OCR需补（无文字层，且未装 easyocr）"
    except Exception as e:  # noqa
        return None, f"读取失败：{e}"


def scan_signals(text):
    """抽取信号词命中的片段，便于 AI 填充矩阵时不漏。"""
    hits = {}
    for label, pat in SIGNAL_PATTERNS.items():
        found = []
        for m in re.finditer(pat, text):
            s = max(0, m.start() - 30)
            e = min(len(text), m.end() + 30)
            snippet = text[s:e].replace("\n", " ")
            found.append(snippet)
            if len(found) >= 8:
                break
        if found:
            hits[label] = found
    return hits


def main():
    if len(sys.argv) < 2:
        print("用法：python build_matrix.py <案卷路径> [--out 输出.md] [--mask-names \"真名=标签,...\"]")
        sys.exit(1)
    target = sys.argv[1]
    out = None
    mask_map = {}
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    if "--mask-names" in sys.argv:
        mask_map = parse_mask(sys.argv[sys.argv.index("--mask-names") + 1])

    files = []
    if os.path.isdir(target):
        for ext in ("*.pdf", "*.png", "*.jpg", "*.jpeg", "*.txt"):
            files += glob.glob(os.path.join(target, "**", ext), recursive=True)
        # 排除 OCR/脚本产生的临时文件，保持清单干净
        files = [
            f for f in files
            if not os.path.basename(f).startswith(("_p_", "tmp_", "_sc", "_selfcheck"))
            and "_selfcheck" not in f and "_sc2" not in f
        ]
    else:
        files = [target]

    if not files:
        print("未找到案卷文件。")
        sys.exit(1)

    md = ["# 案卷精读骨架（AI 填要件矩阵用）", ""]
    md.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}　文件数：{len(files)}"
              + ("　已脱敏" if mask_map else ""))
    md.append("")
    md.append("## （甲）证据与庭审笔录清单（骨架，待补证明目的/三性/本方态度）")
    md.append("")
    md.append("| 编号 | 证据名称 | 类别 | 关键页 | 证明目的 | 三性意见 | 本方态度 |")
    md.append("|---|---|---|---|---|---|---|")

    all_signals = {}
    idx = 0
    for f in sorted(files):
        raw_name = os.path.basename(f)
        name = apply_mask(raw_name, mask_map)
        idx += 1
        cat = classify(raw_name)
        pages, note = extract_text(f)
        key_pages = ""
        if pages is None:
            md.append(f"| {idx} | {name} | {cat} | — | （{apply_mask(note, mask_map)}） | | |")
            continue
        # 取非空页前 3 页作为关键页提示
        nonempty = [p for p, t in pages if t.strip()]
        key_pages = "、".join(str(p) for p in nonempty[:3]) if nonempty else "（空/需OCR）"
        md.append(f"| {idx} | {name} | {cat} | {key_pages} | （待填） | （待填） | （待填） |")
        # 汇总信号（脱敏）
        full = apply_mask("\n".join(t for _, t in pages), mask_map)
        sig = scan_signals(full)
        for k, v in sig.items():
            all_signals.setdefault(k, []).extend([f"[{name}] {x}" for x in v])

    md.append("")
    md.append("## （乙）要件事实—证据矩阵（AI 填：纵轴=要件及待证事实，横轴=证据原文+页码+主张方+对方意见+认定状态）")
    md.append("")
    md.append("| 要件/争议事实 | 证据原文摘录 | 出处 | 主张方 | 对方意见 | 认定状态 |")
    md.append("|---|---|---|---|---|---|")
    md.append("| （待按请求权基础拆解后逐行填写） | | | | | |")
    md.append("")
    md.append("## （丙）矛盾与风险标记（自动扫描信号，待 AI 复核标注）")
    md.append("")
    for k, v in all_signals.items():
        md.append(f"### {k}")
        for x in v[:8]:
            md.append(f"- {x}")
        md.append("")

    out_text = "\n".join(md)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(out_text)
        print(f"已生成骨架：{out}" + ("（已脱敏）" if mask_map else ""))
    else:
        print(out_text)


if __name__ == "__main__":
    main()
