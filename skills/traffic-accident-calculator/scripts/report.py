# -*- coding: utf-8 -*-
"""
报告渲染器 —— 把结构化计算结果变成可交付的成果物
=====================================================
输出一份自包含的 HTML 报告（内联 CSS、A4 打印版式），用户在浏览器中打开后
按 Ctrl+P（Mac 为 Cmd+P）选择"另存为 PDF"，即可得到一份可下载、可打印、
可发给对方或律师的正式测算报告。

为什么用 HTML 而不是直接生成 PDF：
- 纯标准库实现，零第三方依赖，任何 Python 3.8+ 环境（含云端沙箱）都能跑；
- 浏览器打印是所有系统都自带的能力，转 PDF 无损、中文字体不乱码；
- 若运行环境恰好装了 weasyprint / wkhtmltopdf，可用 html_to_pdf() 一步出 PDF。

作者：InchStep 寸进产品实验室
"""

import os
import datetime
import hashlib
from typing import List, Dict, Any, Optional, Tuple


# ---------------------------------------------------------------------------
# 样式
# ---------------------------------------------------------------------------

_CSS = """
@page { size: A4; margin: 18mm 16mm 16mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", sans-serif;
  color: #1f2328; line-height: 1.75; font-size: 13.5px;
  margin: 0 auto; padding: 28px 32px; max-width: 820px; background: #fff;
}
.hd { border-bottom: 2px solid #1f2328; padding-bottom: 14px; margin-bottom: 20px; }
.hd h1 { font-size: 22px; margin: 0 0 6px; letter-spacing: 1px; }
.hd .sub { color: #57606a; font-size: 12.5px; }
.meta { width: 100%; border-collapse: collapse; margin-bottom: 22px; font-size: 12.5px; }
.meta td { padding: 5px 8px; border-bottom: 1px dashed #d8dee4; }
.meta td:first-child { color: #57606a; width: 110px; }
h2 {
  font-size: 15px; margin: 26px 0 10px; padding-left: 9px;
  border-left: 4px solid #1f2328;
}
table.data { width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-size: 12.5px; }
table.data th, table.data td {
  border: 1px solid #d0d7de; padding: 7px 9px; text-align: left; vertical-align: top;
}
table.data th { background: #f6f8fa; font-weight: 600; white-space: nowrap; }
table.data td.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.total { background: #f6f8fa; font-weight: 600; }
ol.pts { padding-left: 20px; margin: 8px 0 14px; }
ol.pts li { margin-bottom: 7px; }
p.text { margin: 6px 0 12px; }
.callout {
  background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 5px;
  padding: 12px 14px; margin: 10px 0 16px; font-size: 12.5px;
}
.callout .lbl { font-weight: 600; display: block; margin-bottom: 4px; }
.disc {
  margin-top: 28px; padding: 12px 14px; border: 1px solid #d0d7de;
  border-left: 4px solid #57606a; background: #fafbfc;
  font-size: 11.8px; color: #57606a; line-height: 1.7;
}
.ft {
  margin-top: 22px; padding-top: 10px; border-top: 1px solid #d8dee4;
  font-size: 11px; color: #8b949e; display: flex; justify-content: space-between;
}
.tip {
  margin: 0 0 18px; padding: 9px 12px; background: #fff8e6;
  border: 1px dashed #d4a72c; border-radius: 5px; font-size: 12px; color: #7a5c00;
}
@media print { .tip { display: none; } body { padding: 0; } }
"""


def _esc(s: Any) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _money(v: Any) -> str:
    """金额格式化：千分位 + 元。"""
    try:
        return "{:,.0f} 元".format(float(v))
    except (TypeError, ValueError):
        return _esc(v)


# ---------------------------------------------------------------------------
# 主渲染
# ---------------------------------------------------------------------------

def render_html(title: str,
                subtitle: str = "",
                meta: Optional[List[Tuple[str, str]]] = None,
                sections: Optional[List[Dict[str, Any]]] = None,
                disclaimer: str = "",
                footer_note: str = "") -> str:
    """
    渲染一份完整 HTML 报告。

    sections 每项为 dict，支持四种 kind：
      {"kind": "table", "title": "...", "headers": [...], "rows": [[...], ...],
       "num_cols": [2,3], "total_row_index": -1}
      {"kind": "list",  "title": "...", "items": ["...", ...]}
      {"kind": "text",  "title": "...", "body": "..."}
      {"kind": "callout", "label": "...", "body": "..."}
    """
    meta = meta or []
    sections = sections or []
    now = datetime.datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")
    serial = hashlib.md5((title + stamp).encode("utf-8")).hexdigest()[:8].upper()

    parts = ["<!DOCTYPE html>", '<html lang="zh-CN"><head><meta charset="utf-8">',
             "<title>%s</title>" % _esc(title),
             "<style>%s</style></head><body>" % _CSS]

    parts.append('<div class="tip">提示：按 Ctrl+P（Mac 为 Cmd+P）→ 目标打印机选择'
                 '「另存为 PDF」，即可把本报告保存为一份 A4 版式的 PDF 文件。此提示不会被打印。</div>')

    parts.append('<div class="hd"><h1>%s</h1>' % _esc(title))
    if subtitle:
        parts.append('<div class="sub">%s</div>' % _esc(subtitle))
    parts.append("</div>")

    all_meta = list(meta) + [("生成时间", stamp), ("报告编号", serial)]
    parts.append('<table class="meta">')
    for k, v in all_meta:
        parts.append("<tr><td>%s</td><td>%s</td></tr>" % (_esc(k), _esc(v)))
    parts.append("</table>")

    for sec in sections:
        kind = sec.get("kind", "text")
        if sec.get("title"):
            parts.append("<h2>%s</h2>" % _esc(sec["title"]))

        if kind == "table":
            num_cols = set(sec.get("num_cols", []))
            total_idx = sec.get("total_row_index", None)
            parts.append('<table class="data"><thead><tr>')
            for h in sec.get("headers", []):
                parts.append("<th>%s</th>" % _esc(h))
            parts.append("</tr></thead><tbody>")
            rows = sec.get("rows", [])
            for ri, row in enumerate(rows):
                is_total = (total_idx is not None and
                            (ri == total_idx or ri == len(rows) + total_idx))
                parts.append('<tr class="total">' if is_total else "<tr>")
                for ci, cell in enumerate(row):
                    cls = ' class="num"' if ci in num_cols else ""
                    parts.append("<td%s>%s</td>" % (cls, _esc(cell)))
                parts.append("</tr>")
            parts.append("</tbody></table>")

        elif kind == "list":
            parts.append('<ol class="pts">')
            for it in sec.get("items", []):
                parts.append("<li>%s</li>" % _esc(it))
            parts.append("</ol>")

        elif kind == "callout":
            parts.append('<div class="callout"><span class="lbl">%s</span>%s</div>'
                         % (_esc(sec.get("label", "说明")), _esc(sec.get("body", ""))))

        else:
            parts.append('<p class="text">%s</p>' % _esc(sec.get("body", "")))

    if disclaimer:
        parts.append('<div class="disc"><strong>免责声明</strong><br>%s</div>' % _esc(disclaimer))

    parts.append('<div class="ft"><span>%s</span><span>报告编号 %s</span></div>'
                 % (_esc(footer_note or "本报告由计算引擎按公式自动生成，数据以用户输入为准"), serial))
    parts.append("</body></html>")
    return "\n".join(parts)


def save_html(html: str, path: str) -> str:
    """写出 HTML 报告，返回绝对路径。"""
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.abspath(path)


def html_to_pdf(html_path: str, pdf_path: str) -> Optional[str]:
    """
    可选：环境若装了 weasyprint 或 wkhtmltopdf，直接产出 PDF。
    没有则返回 None，调用方回退到"浏览器打印另存"路径。
    """
    try:
        from weasyprint import HTML  # type: ignore
        HTML(filename=html_path).write_pdf(pdf_path)
        return os.path.abspath(pdf_path)
    except Exception:
        pass
    import shutil, subprocess
    exe = shutil.which("wkhtmltopdf")
    if exe:
        try:
            subprocess.run([exe, "-q", html_path, pdf_path], check=True, timeout=120)
            return os.path.abspath(pdf_path)
        except Exception:
            return None
    return None
