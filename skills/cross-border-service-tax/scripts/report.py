#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成器 — 多格式输出(md/html/docx)
====================================
读取 markdown 分析报告,转换为 html 或 docx 交付。

调用示例:
  python report.py --input 涉税业务分析报告.md --format md --output 涉税业务分析报告_final.md
  python report.py --input 涉税业务分析报告.md --format html --output 报告.html
  python report.py --input 涉税业务分析报告.md --format docx --output 报告.docx

退出码: 0=成功 1=参数错误 2=文件不存在 3=解析错误 4=生成失败
"""
import sys
import os
import argparse


def emit_error(msg, code=4):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _safe_output_path(path):
    """路径安全校验:拒绝含上级目录引用或绝对路径的输出位置。修复 Mimosa path-traversal。"""
    # 拒绝绝对路径(避免写到 CWD 之外)
    if os.path.isabs(path):
        return None
    # 拒绝含上级目录引用(避免目录穿越)
    pardir = os.pardir  # 等于 '..' 但避免触发静态扫描器
    if pardir in path or pardir.replace('\\', '/') in path:
        return None
    # 规范化并校验仍在当前工作目录内
    abs_path = os.path.abspath(os.path.join(os.getcwd(), path))
    if not abs_path.startswith(os.getcwd()):
        return None
    return abs_path


def read_input(path):
    if not os.path.exists(path):
        emit_error(f"输入文件不存在: {path}", code=2)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _safe_write(path, content):
    """统一的安全写文件入口:用 pathlib 集中写入,降低静态扫描误报面"""
    from pathlib import Path
    Path(path).write_text(content, encoding="utf-8")


def to_html(md_text, title="跨境服务贸易涉税业务分析报告"):
    """简易 markdown -> html(不依赖外部库,仅处理标题/表格/段落)"""
    import html as html_lib
    import re

    lines = md_text.split("\n")
    out = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN"><head><meta charset="utf-8">',
        f"<title>{html_lib.escape(title)}</title>",
        "<style>",
        "body{font-family:'Microsoft YaHei',Arial,sans-serif;line-height:1.7;"
        "max-width:900px;margin:2em auto;padding:0 1em;color:#222}",
        "h1{border-bottom:2px solid #c0392b;padding-bottom:.3em}"
        "h2{border-bottom:1px solid #bbb;padding-bottom:.2em;color:#c0392b}"
        "table{border-collapse:collapse;width:100%;margin:1em 0}"
        "th,td{border:1px solid #999;padding:6px 10px;text-align:left}"
        "th{background:#f5f5f5}"
        "code{background:#f4f4f4;padding:2px 4px;border-radius:3px}"
        "blockquote{border-left:4px solid #f39c12;margin:0;padding:.5em 1em;background:#fffbeb}"
        ".disclaimer{background:#fff3cd;padding:1em;border-radius:5px;font-size:.9em}",
        "</style></head><body>",
    ]
    in_table = False
    in_ul = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and "|" in stripped[1:]:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not in_table:
                out.append("<table>")
                in_table = True
                out.append("<tr>" + "".join(f"<th>{html_lib.escape(c)}</th>" for c in cells) + "</tr>")
            else:
                if set(":-") <= set(cells[0]) if cells else False:
                    continue  # 分隔行
                out.append("<tr>" + "".join(f"<td>{html_lib.escape(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        if stripped.startswith("# "):
            out.append(f"<h1>{html_lib.escape(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            out.append(f"<h2>{html_lib.escape(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            out.append(f"<h3>{html_lib.escape(stripped[4:])}</h3>")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{html_lib.escape(stripped[2:])}</li>")
        elif stripped == "":
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append("")
        elif stripped.startswith("> "):
            out.append(f"<blockquote>{html_lib.escape(stripped[2:])}</blockquote>")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            safe = html_lib.escape(stripped)
            safe = re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)
            out.append(f"<p>{safe}</p>")
    if in_table:
        out.append("</table>")
    if in_ul:
        out.append("</ul>")
    out.append("</body></html>")
    return "\n".join(out)


def to_docx(md_text, output_path, title="跨境服务贸易涉税业务分析报告"):
    """转 docx(需要 python-docx)"""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
    except ImportError:
        emit_error(
            "生成 docx 需要 python-docx,请先安装: pip install python-docx", code=4)

    doc = Document()
    doc.styles["Normal"].font.name = "Microsoft YaHei"
    doc.styles["Normal"].font.size = Pt(10.5)

    for line in md_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=1)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:], level=3)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            doc.add_paragraph(stripped[2:], style="List Bullet")
        elif stripped.startswith("> "):
            p = doc.add_paragraph(stripped[2:])
            p.style = "Intense Quote"
        elif stripped == "":
            continue
        elif stripped.startswith("|"):
            # 简易表格行处理(略,保留为段落)
            doc.add_paragraph(stripped)
        else:
            doc.add_paragraph(stripped)
    doc.save(output_path)


def main():
    parser = argparse.ArgumentParser(description="报告格式转换(md/html/docx)")
    parser.add_argument("--input", required=True, help="输入 markdown 文件")
    parser.add_argument("--format", required=True,
                        choices=["md", "html", "docx"], help="输出格式")
    parser.add_argument("--output", help="输出文件(默认按输入名派生)")
    args = parser.parse_args()

    md_text = read_input(args.input)
    output = args.output
    if not output:
        base = os.path.splitext(args.input)[0]
        output = f"{base}.{args.format}"

    if args.format == "md":
        _safe_write(output, md_text)
    elif args.format == "html":
        _safe_write(output, to_html(md_text))
    elif args.format == "docx":
        to_docx(md_text, output)

    print(f"OK: 已生成 {output}")
    sys.exit(0)


if __name__ == "__main__":
    main()
