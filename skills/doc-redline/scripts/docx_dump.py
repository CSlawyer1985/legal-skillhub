#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTHOR: WorkBuddy (agent_created)
"""把 .docx 按“眼睛看到的样子”逐段导出为纯文本，供版本比对使用。

为什么不能直接解 XML 取所有 <w:t>：
  1) 自动编号（<w:numPr>）不在正文里，编号“三、”“1、”是渲染时才生成的。
     直接取文本会得到“工商变更前后的双方各自职责及权限：”，
     比对时会被误判成“打印稿把编号删了”。
  2) 浮动文本框（wps:txbx / VML textbox）里的文字会被取到并悄悄混入正文，
     若该文本框锚点在纸面之外（positionV 偏移 > 页高），它本来就不打印，
     必须排除，否则误判成“打印稿删掉了这个字”。
  3) 页脚/页眉是独立部件，不属于正文，要单独列出。

用法:
  python3 docx_dump.py 合同.docx                 # 正文（含渲染后编号）
  python3 docx_dump.py 合同.docx --footer        # 附：页眉页脚
  python3 docx_dump.py 合同.docx --floating      # 附：浮动对象及其纸面内/外判定
  python3 docx_dump.py 合同.docx --revisions     # 附：修订与批注
  python3 docx_dump.py 合同.docx --json out.json # 机器可读
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
V = "{urn:schemas-microsoft-com:vml}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
EMU_PER_CM = 360000

CN_NUM = "零一二三四五六七八九十"


def cn_counting(n: int) -> str:
    """chineseCounting: 1→一 10→十 11→十一 23→二十三"""
    if n <= 0:
        return str(n)
    if n <= 10:
        return "十" if n == 10 else CN_NUM[n]
    if n < 20:
        return "十" + CN_NUM[n % 10]
    if n < 100:
        t, u = divmod(n, 10)
        return CN_NUM[t] + "十" + (CN_NUM[u] if u else "")
    return str(n)


def num_fmt_value(fmt: str, n: int) -> str:
    if fmt in ("decimal", "decimalZero"):
        return str(n)
    if fmt == "chineseCounting":
        return cn_counting(n)
    if fmt == "chineseCountingThousand":
        return cn_counting(n)
    if fmt in ("lowerLetter", "upperLetter"):
        s = chr(ord("a" if fmt == "lowerLetter" else "A") + (n - 1) % 26)
        return s
    return str(n)


def fmt_level(lvl_fmt: str, lvl_text: str, n: int) -> str:
    return re.sub(r"%[1-9]", lambda m: num_fmt_value(lvl_fmt, n), lvl_text or "")


class Numbering:
    """解析 numbering.xml，把 numId+ilvl 展开成真实编号文本（按出现顺序计数）。"""

    def __init__(self, zf):
        self.num2abs = {}
        self.abs_lvl = {}
        self.counters = {}
        if "word/numbering.xml" not in zf.namelist():
            return
        root = ET.fromstring(zf.read("word/numbering.xml"))
        for num in root.findall(W + "num"):
            aid = num.find(W + "abstractNumId")
            lvl = num.find(W + "lvlOverride/" + W + "startOverride")
            self.num2abs[num.get(W + "numId")] = aid.get(W + "val") if aid is not None else None
            self.num_start_override = getattr(self, "num_start_override", {})
            if lvl is not None:
                self.num_start_override[num.get(W + "numId")] = int(lvl.get(W + "val"))
        for an in root.findall(W + "abstractNum"):
            aid = an.get(W + "abstractNumId")
            lvls = {}
            for lv in an.findall(W + "lvl"):
                ilvl = lv.get(W + "ilvl")
                f = lv.find(W + "numFmt")
                t = lv.find(W + "lvlText")
                s = lv.find(W + "start")
                lvls[ilvl] = {
                    "fmt": f.get(W + "val") if f is not None else "decimal",
                    "text": t.get(W + "val") if t is not None else "%1.",
                    "start": int(s.get(W + "val")) if s is not None else 1,
                }
            self.abs_lvl[aid] = lvls

    def label(self, num_id, ilvl):
        if num_id is None:
            return None, None
        aid = self.num2abs.get(str(num_id))
        if aid is None or aid not in self.abs_lvl:
            return None, None
        lv = self.abs_lvl[aid].get(str(ilvl), {"fmt": "decimal", "text": "%1.", "start": 1})
        key = (str(num_id), str(ilvl))
        if key not in self.counters:
            self.counters[key] = self.num_start_override.get(str(num_id), lv["start"]) if hasattr(self, "num_start_override") else lv["start"]
        n = self.counters[key]
        self.counters[key] = n + 1
        return fmt_level(lv["fmt"], lv["text"], n), aid


def para_pieces(p, numbering=None, skip_subtree_of=("txbxContent", "pict")):
    """返回 (正文文本, 自动编号前缀)。跳过浮动文本框/图片子树。"""
    prefix = ""
    num_id = ilvl = None
    ppr = p.find(W + "pPr")
    if ppr is not None and numbering is not None:
        numpr = ppr.find(W + "numPr")
        if numpr is not None:
            nid = numpr.find(W + "numId")
            il = numpr.find(W + "ilvl")
            num_id = nid.get(W + "val") if nid is not None else None
            ilvl = il.get(W + "val") if il is not None else "0"
            lab, _ = numbering.label(num_id, ilvl)
            if lab:
                prefix = lab

    def walk(node, in_textbox=False):
        out = []
        tag = node.tag.split("}")[-1]
        if tag == "txbxContent" or tag == "drawing" or tag == "pict" or tag == "AlternateContent" or tag == "object":
            return out  # 浮动/内嵌对象：正文文本一律跳过
        if tag == "t":
            out.append(node.text or "")
        elif tag == "delText":
            out.append("[[修订删除:" + (node.text or "") + "]]")
        elif tag == "tab":
            out.append("\t")
        elif tag in ("br", "cr"):
            out.append("\n")
        for ch in node:
            out.extend(walk(ch))
        return out

    return prefix, "".join(walk(p))


def floating_objects(zf, page_w_cm, page_h_cm):
    """列出所有浮动对象；positionH/V 以页为基准且偏移超出纸面 → 本来就不打印。"""
    root = ET.fromstring(zf.read("word/document.xml"))
    res = []
    for anc in root.iter(WP + "anchor"):
        name = "?"
        docpr = anc.find(WP + "docPr")
        if docpr is not None:
            name = docpr.get("name") or "?"
        ph = anc.find(WP + "positionH")
        pv = anc.find(WP + "positionV")
        x = y = None
        if ph is not None and ph.get("relativeFrom") == "page":
            off = ph.find(WP + "posOffset")
            if off is not None:
                x = int(off.text) / EMU_PER_CM
        if pv is not None and pv.get("relativeFrom") == "page":
            off = pv.find(WP + "posOffset")
            if off is not None:
                y = int(off.text) / EMU_PER_CM
        txt = "".join((t.text or "") for t in anc.iter(W + "t"))
        on_paper = None
        if x is not None and y is not None and page_w_cm and page_h_cm:
            on_paper = (0 <= x < page_w_cm) and (0 <= y < page_h_cm)
        res.append(
            {
                "name": name,
                "text": txt,
                "x_cm": None if x is None else round(x, 2),
                "y_cm": None if y is None else round(y, 2),
                "page_w_cm": page_w_cm,
                "page_h_cm": page_h_cm,
                "on_paper": on_paper,
            }
        )
    # VML 文本框（Fallback 版，mc:AlternateContent 里往往重复一份，按位置去重）
    for sh in root.iter(V + "shape"):
        style = sh.get("style") or ""
        m = re.search(r"mso-position-vertical-relative:page", style)
        if not m:
            continue
        txt = "".join((t.text or "") for t in sh.iter(W + "t"))
        top = re.search(r"margin-top:([\d.]+)pt", style)
        left = re.search(r"margin-left:([\d.]+)pt", style)
        res.append(
            {
                "name": sh.get("id") or "vml",
                "text": txt,
                "x_cm": round(float(left.group(1)) * 2.54 / 72, 2) if left else None,
                "y_cm": round(float(top.group(1)) * 2.54 / 72, 2) if top else None,
                "page_w_cm": page_w_cm,
                "page_h_cm": page_h_cm,
                "on_paper": None,
                "note": "VML Fallback 副本（与 drawing 版为同一对象）",
            }
        )
    return res


def part_text(zf, name, numbering=None):
    if name not in zf.namelist():
        return None
    root = ET.fromstring(zf.read(name))
    out = []
    for p in root.iter(W + "p"):
        _, t = para_pieces(p, numbering)
        if t.strip():
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--footer", action="store_true")
    ap.add_argument("--floating", action="store_true")
    ap.add_argument("--revisions", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()

    zf = zipfile.ZipFile(a.docx)
    numbering = Numbering(zf)
    doc = ET.fromstring(zf.read("word/document.xml"))
    body = doc.find(W + "body")

    sect = doc.find(".//" + W + "sectPr")
    pg = sect.find(W + "pgSz") if sect is not None else None
    page_w_cm = page_h_cm = None
    if pg is not None:
        page_w_cm = round(int(pg.get(W + "w")) / 566.9, 2)   # twips→cm
        page_h_cm = round(int(pg.get(W + "h")) / 566.9, 2)

    paras = []
    for el in body:
        tag = el.tag.split("}")[-1]
        if tag == "p":
            prefix, text = para_pieces(el, numbering)
            if text.strip() or prefix:
                paras.append({"num": prefix, "text": text})
        elif tag == "tbl":
            for row in el.findall(W + "tr"):
                cells = []
                for tc in row.findall(W + "tc"):
                    _, t = para_pieces(tc, None)
                    cells.append(re.sub(r"\s+", " ", t).strip())
                paras.append({"num": "", "text": "<表格行> " + " | ".join(cells)})

    result = {"file": os.path.basename(a.docx), "page_cm": [page_w_cm, page_h_cm], "paragraphs": paras}

    if a.footer:
        result["footers"] = {}
        for n in zf.namelist():
            if re.match(r"word/(footer|header)\d*\.xml$", n):
                result["footers"][n] = part_text(zf, n, numbering)
    if a.floating:
        result["floating_objects"] = floating_objects(zf, page_w_cm, page_h_cm)
    if a.revisions:
        raw = zf.read("word/document.xml").decode("utf-8")
        result["revision_marks"] = {
            "inserted_runs": len(re.findall(r"<w:ins ", raw)),
            "deleted_runs": len(re.findall(r"<w:del ", raw)),
            "comments": "word/comments.xml" in zf.namelist(),
            "track_changes_on": bool(re.search(r'<w:trackChanges[^>]*/>', raw)),
        }

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)

    print("### 文件:", result["file"], " 页面(cm):", page_w_cm, "x", page_h_cm)
    for i, p in enumerate(paras, 1):
        print(f"[{i:>3}] {p['num']}{p['text']}")
    for k, v in result.items():
        if k in ("file", "page_cm", "paragraphs"):
            continue
        print("\n###", k)
        print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
