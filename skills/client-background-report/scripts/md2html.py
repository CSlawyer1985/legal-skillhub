#!/usr/bin/env python3
"""Markdown → HTML 展示版（背调报告专用）。
用法: python3 scripts/md2html.py 报告底稿.md 附件底稿.md 输出.html
- 内容与 Word 版一致（同一 md 底稿）；
- 正文中的来源编号（A1/B2 等）转为上标脚注超链接，点击跳转至文末附件锚点；
- 附件（信息来源汇编）作为正文引用注释呈现在文末，各条目带 id 锚点；
- 图片以相对路径引用（HTML 与底稿同目录存放）。
"""
import html
import os
import re
import sys

REF_RE = re.compile(r"\b([AB]\d{1,2})\b")


def inline(text):
    t = html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = REF_RE.sub(r'<sup><a href="#src-\1" class="ref">[\1]</a></sup>', t)
    return t


def render(md, base, is_annex=False):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if not line.strip():
            continue
        if line.lstrip().startswith("|"):
            rows = []
            while True:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells):
                    rows.append(cells)
                if i >= len(lines):
                    break
                line = lines[i].rstrip()
                i += 1
                if not line.lstrip().startswith("|"):
                    break
            if rows:
                ncol = max(len(r) for r in rows)
                trs = []
                for ri, r in enumerate(rows):
                    tag = "th" if ri == 0 else "td"
                    trs.append("<tr>" + "".join(
                        f"<{tag}>{inline(r[ci]) if ci < len(r) else ''}</{tag}>"
                        for ci in range(ncol)) + "</tr>")
                out.append("<table>" + "".join(trs) + "</table>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level, text = len(m.group(1)), m.group(2)
            if is_annex:
                am = re.match(r"^([AB]\d{1,2})\.\s*(.*)$", text)
                if am:
                    out.append(f'<h3 id="src-{am.group(1)}">{inline(am.group(1))}. {inline(am.group(2))}'
                               f' <a href="#top" class="back">↩</a></h3>')
                    continue
            if level == 1:
                out.append(f"<h1>{inline(text)}</h1>")
            else:
                out.append(f"<h{level}>{inline(text)}</h{level}>")
            continue
        mi = re.match(r"^!\[(.*?)\]\((.+?)\)\s*$", line.strip())
        if mi:
            src_attr = html.escape(mi.group(2))
            out.append(f'<figure><img src="{src_attr}" alt="">'
                       f'<figcaption>{inline(mi.group(1))}</figcaption></figure>')
            continue
        if line.lstrip().startswith(("- ", "* ")):
            out.append(f"<p class='li'>• {inline(line.lstrip()[2:])}</p>")
            continue
        if line.strip().startswith("**") and line.strip().endswith("**") and len(line.strip()) > 4:
            out.append(f"<p class='subtitle'>{inline(line.strip().strip('*'))}</p>")
            continue
        out.append(f"<p>{inline(line)}</p>")
    return "\n".join(out)


CSS = """
body{max-width:880px;margin:0 auto;padding:32px 20px;font-family:"Songti SC","SimSun",serif;
color:#222;line-height:1.9;font-size:15px}
h1{text-align:center;font-family:"PingFang SC","SimHei",sans-serif;font-size:24px}
.subtitle{text-align:center;color:#555;font-size:15px}
h2{font-family:"PingFang SC","SimHei",sans-serif;font-size:19px;border-left:5px solid #2f5597;
padding-left:10px;margin-top:36px}
h3{font-size:16px;margin-top:24px}
p{text-indent:2em;margin:8px 0} p.li,p.subtitle{text-indent:0}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13.5px}
th,td{border:1px solid #999;padding:6px 8px;vertical-align:top}
th{background:#e8eef7}
sup a{color:#2f5597;text-decoration:none} sup a:hover{text-decoration:underline}
figure{text-align:center;margin:18px 0} figure img{max-width:100%;border:1px solid #ddd}
figcaption{font-size:13px;color:#666;margin-top:6px}
.annex{margin-top:48px;border-top:3px double #999;padding-top:12px}
.annex h3{scroll-margin-top:20px} .back{font-size:12px;color:#999}
header{display:flex;justify-content:flex-end;margin-bottom:8px}
header img{height:26px}
"""


def main(report_md, annex_md, dst):
    base = os.path.dirname(os.path.abspath(report_md))
    logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tctl_logo.jpeg")
    header = f'<header><img src="{os.path.relpath(logo, base)}"></header>' if os.path.exists(logo) else ""
    body = render(open(report_md, encoding="utf-8").read(), base)
    annex = render(open(annex_md, encoding="utf-8").read(), base, is_annex=True)
    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(os.path.basename(dst)[:-5])}</title><style>{CSS}</style></head>
<body id="top">{header}{body}
<div class="annex">{annex}</div>
</body></html>"""
    open(dst, "w", encoding="utf-8").write(doc)
    n = len(REF_RE.findall(open(report_md, encoding="utf-8").read()))
    print(f"OK 引用脚注 {n} 处 -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
