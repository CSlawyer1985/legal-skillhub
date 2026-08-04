#!/usr/bin/env python3
"""
专业制裁筛查 PDF 报告生成器
将 Markdown 证据报告转换为麦肯锡/Big4 级别的专业 PDF

用法:
    python generate_report.py <input_md> [--output <output_pdf>] [--entity <entity_name>] [--case-id <id>]

依赖:
    - markdown (pip install markdown)
    - Google Chrome 或 Microsoft Edge (用于 Headless PDF 渲染)
"""
import markdown
import os
import base64
import re
import subprocess
import argparse
import json
from datetime import datetime


def embed_images(md_text: str) -> tuple[str, int]:
    """将 Markdown 中的本地图片路径替换为 base64 data URI"""
    img_count = 0

    def replace_img(match):
        nonlocal img_count
        alt = match.group(1)
        img_path = match.group(2).strip()
        if img_path.startswith("data:"):
            return match.group(0)
        img_path = img_path.replace("/", os.sep)
        if os.path.exists(img_path):
            ext = os.path.splitext(img_path)[1].lower().lstrip(".")
            mime_map = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "webp": "image/webp",
            }
            mime = mime_map.get(ext, "image/png")
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            img_count += 1
            return f"![{alt}](data:{mime};base64,{b64})"
        else:
            return f"*[图片缺失: {os.path.basename(img_path)}]*"

    result = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_img, md_text)
    return result, img_count


def beautify_html(html: str) -> str:
    """后处理 HTML，增加状态徽章和图片 caption"""
    # 状态标记
    html = html.replace(
        "✅ 命中", '<span class="badge badge-hit">HIT [命中]</span>'
    )
    html = html.replace(
        "✅ **命中**", '<span class="badge badge-hit">HIT [命中]</span>'
    )
    html = html.replace(
        "❌ 未命中", '<span class="badge badge-clean">CLEAN [未命中]</span>'
    )
    html = html.replace(
        "❌ **未命中**", '<span class="badge badge-clean">CLEAN [未命中]</span>'
    )
    # 图片 caption
    html = re.sub(
        r"<p><img (.*?) alt=\"(.*?)\" (.*?)></p>",
        r'<div class="figure"><img \1 alt="\2" \3><div class="img-caption">\2</div></div>',
        html,
    )
    return html


# 麦肯锡/Big4 级 CSS 样式
PROFESSIONAL_CSS = """
@page {
    size: A4;
    margin: 20mm 20mm 20mm 20mm;
    @bottom-left {
        content: "CONFIDENTIAL | LEGAL & COMPLIANCE FRAMEWORK";
        font-size: 7.5pt; color: #888;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        text-transform: uppercase; letter-spacing: 0.5pt;
    }
    @bottom-right {
        content: counter(page);
        font-size: 9pt; color: #333; font-weight: bold;
    }
}

@page :first {
    margin: 0;
    @bottom-left { content: ""; }
    @bottom-right { content: ""; }
}

body {
    font-family: 'Helvetica Neue', Arial, 'Microsoft YaHei', sans-serif;
    color: #333; line-height: 1.6; font-size: 9.5pt; margin: 0;
}

/* 封面 */
.cover-page {
    background-color: #00204a;
    min-height: 297mm;
    position: relative;
    color: white;
    page-break-after: always;
}
.cover-header { padding: 25mm 25mm 0 25mm; }
.cover-logo-line {
    border-top: 1px solid rgba(255,255,255,0.3);
    padding-top: 15mm;
    font-family: 'Palatino Linotype', 'Georgia', serif;
    font-size: 14pt; letter-spacing: 2pt; text-transform: uppercase;
}
.cover-title-area { padding: 30mm 25mm 0 25mm; }
.cover-doc-type {
    font-size: 10pt; color: #4da6ff; letter-spacing: 3pt;
    text-transform: uppercase; margin-bottom: 5mm; font-weight: bold;
}
.cover-title {
    font-family: 'Palatino Linotype', 'Georgia', serif;
    font-size: 34pt; line-height: 1.2; margin: 0 0 10mm 0; color: white; border: none;
}
.cover-subtitle { font-size: 16pt; color: #ccd6e0; font-weight: 300; margin-bottom: 20mm; }
.cover-footer {
    position: absolute; bottom: 25mm; left: 25mm; right: 25mm;
    border-top: 1px solid rgba(255,255,255,0.2);
    padding-top: 5mm; font-size: 9pt; color: #8da4b8;
    overflow: hidden;
}

/* 标题 */
h1 {
    font-family: 'Palatino Linotype', 'Georgia', serif;
    font-size: 22pt; color: #00204a;
    border-bottom: 2px solid #00204a;
    padding-bottom: 4mm; margin-top: 12mm; margin-bottom: 8mm;
    page-break-after: avoid;
}
h2 {
    font-size: 14pt; color: #003366; margin-top: 10mm; margin-bottom: 4mm;
    border-bottom: 1px solid #e0e0e0; padding-bottom: 2mm; page-break-after: avoid;
}
h3 {
    font-size: 11pt; color: #444; text-transform: uppercase;
    letter-spacing: 0.5pt; margin-top: 8mm; margin-bottom: 3mm; page-break-after: avoid;
}
h4 { font-size: 10pt; color: #003366; margin-top: 6mm; }

/* 咨询级表格 */
table {
    width: 100%; border-collapse: collapse;
    margin: 6mm 0 10mm 0; page-break-inside: avoid; font-size: 9pt;
}
th, td {
    padding: 8pt 10pt; text-align: left;
    border-top: 1px solid #e0e0e0; border-bottom: 1px solid #e0e0e0;
}
th {
    background-color: transparent; color: #00204a; font-weight: bold;
    border-top: 2px solid #00204a; border-bottom: 2px solid #00204a;
    text-transform: uppercase; letter-spacing: 0.5pt; font-size: 8.5pt;
}
tr:nth-child(even) { background-color: #f9f9f9; }
tbody tr:last-child td { border-bottom: 2px solid #00204a; }

/* 风险面板 */
.exec-summary {
    background-color: #f4f6f8; padding: 15mm; margin: 10mm 0;
    border-left: 6px solid #c00000;
}
.exec-title {
    font-family: 'Palatino Linotype', 'Georgia', serif;
    font-size: 16pt; color: #c00000; margin-bottom: 5mm;
}

/* 证据截图 */
img {
    display: block; max-width: 90%; margin: 8mm auto 2mm auto;
    border: 1px solid #d0d0d0;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05), 0 5px 15px rgba(0,0,0,0.08);
    page-break-inside: avoid;
}
.img-caption {
    font-family: 'Georgia', serif; text-align: center;
    font-size: 8.5pt; color: #666; margin-bottom: 12mm; font-style: italic;
}

/* 徽章 */
.badge { display: inline-block; padding: 2pt 5pt; font-size: 8pt; font-weight: bold; letter-spacing: 0.5pt; text-transform: uppercase; }
.badge-hit { color: #c00000; border: 1px solid #c00000; background: #fff0f0; }
.badge-clean { color: #00703c; border: 1px solid #00703c; background: #ebf5f0; }

/* 引用/警示 */
blockquote {
    background: transparent; border-left: 3px solid #00204a;
    padding: 5pt 15pt; margin: 10mm 0; color: #555; font-style: italic;
}
"""


def generate_pdf(
    input_md: str,
    output_pdf: str,
    entity_name: str = "Unknown Entity",
    case_id: str = None,
):
    """主函数：Markdown → HTML (含 base64 图片) → Chrome/Edge Headless → PDF"""
    if not case_id:
        case_id = f"SCR-{datetime.now().strftime('%Y%m%d')}-001"

    # 1. 读取 Markdown
    print(f"[1/4] 读取 Markdown: {input_md}")
    with open(input_md, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 2. 内嵌图片
    print("[2/4] 内嵌图片为 base64...")
    md_with_images, img_count = embed_images(md_content)
    print(f"      已处理 {img_count} 张图片")

    # 3. Markdown → HTML
    print("[3/4] 渲染 HTML 模板...")
    html_body = markdown.markdown(
        md_with_images, extensions=["tables", "fenced_code", "toc", "nl2br"]
    )
    html_body = beautify_html(html_body)

    now = datetime.now()
    html_full = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>{PROFESSIONAL_CSS}</style></head>
<body>
    <div class="cover-page">
        <div class="cover-header">
            <div class="cover-logo-line">Global Compliance Intelligence</div>
        </div>
        <div class="cover-title-area">
            <div class="cover-doc-type">Executive Due Diligence</div>
            <h1 class="cover-title">Global Sanctions &amp;<br/>Export Controls<br/>Fact-Finding Report</h1>
            <div class="cover-subtitle">Target Entity: {entity_name}</div>
        </div>
        <div class="cover-footer">
            <div style="float:left;">
                <strong>PREPARED DATE</strong><br/>{now.strftime('%B %d, %Y')}
            </div>
            <div style="float:left; margin-left:40mm;">
                <strong>CASE REFERENCE</strong><br/>{case_id}
            </div>
            <div style="float:right; text-align:right;">
                <strong>CLASSIFICATION</strong><br/>Strictly Confidential
            </div>
        </div>
    </div>

    <div class="exec-summary">
        <div class="exec-title">Executive Summary</div>
        <div style="font-size:10pt; line-height:1.7; color:#333;">
            <p><strong>Entity:</strong> {entity_name}</p>
            <p>This report presents the findings of an automated regulatory sweep conducted across
            major global sanctions and export control regimes. Detailed forensic evidence is provided below.</p>
        </div>
    </div>

    {html_body}

    <div style="margin-top:50pt; text-align:center; border-top:1px solid #ddd; padding-top:20pt; font-size:8pt; color:#95a5a6;">
        Case Ref: {case_id} | Generated by Autonomous Screening Engine<br/>
        &copy; {now.year} Global Intelligence Lab. Strictly Confidential.
    </div>
</body>
</html>"""

    # 保存 HTML 中间文件
    html_path = output_pdf.replace(".pdf", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_full)
    print(f"      HTML 中间文件: {html_path}")

    # 4. 渲染 PDF：Playwright 优先（更可靠），Chrome CLI 备选
    print("[4/4] 渲染 PDF...")
    html_abs = os.path.abspath(html_path).replace(os.sep, '/')
    file_url = f"file:///{html_abs}"
    pdf_ok = False

    # 方案 A：Playwright（已安装且经过验证）
    try:
        from playwright.sync_api import sync_playwright
        print("      使用 Playwright 渲染 PDF...")
        with sync_playwright() as pw:
            browser = None
            # 尝试系统 Chrome → Playwright Chromium
            for channel in ["chrome", None]:
                try:
                    kwargs = {"headless": True}
                    if channel:
                        kwargs["channel"] = channel
                    browser = pw.chromium.launch(**kwargs)
                    break
                except Exception:
                    continue
            if browser is None:
                raise RuntimeError("Playwright 无法启动浏览器")

            page = browser.new_page()
            page.goto(file_url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)  # 等待渲染完成

            # 隐藏 TOC 侧栏（打印模式）,调整主内容 margin
            page.evaluate("""() => {
                const toc = document.querySelector('.toc-sidebar');
                if (toc) toc.style.display = 'none';
                const main = document.querySelector('.main-content');
                if (main) main.style.marginLeft = '0';
            }""")
            page.wait_for_timeout(500)

            page.pdf(
                path=output_pdf,
                format="A4",
                print_background=True,
                margin={"top": "15mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
                display_header_footer=True,
                header_template='<div style="font-size:7pt;color:#aaa;width:100%;text-align:center;padding:5px;">CONFIDENTIAL | LEGAL & COMPLIANCE FRAMEWORK</div>',
                footer_template=f'<div style="font-size:8pt;width:100%;display:flex;justify-content:space-between;padding:5px 20px;color:#888;"><span>Case Ref: {case_id}</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>',
            )
            browser.close()
            pdf_ok = True
            size_mb = os.path.getsize(output_pdf) / 1024 / 1024
            print(f"[OK] PDF generated (Playwright): {output_pdf} ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"  [WARN] Playwright PDF 失败: {e}")

    # 方案 B：Chrome/Edge headless CLI 备选
    if not pdf_ok:
        print("      尝试 Chrome/Edge headless CLI 备选...")
        browser_candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser", "/usr/bin/chromium",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        browser_path = None
        for p in browser_candidates:
            if os.path.exists(p):
                browser_path = p
                break

        if browser_path:
            cmd = [
                browser_path, "--headless", "--disable-gpu", "--no-sandbox",
                f"--print-to-pdf={output_pdf}",
                "--print-to-pdf-no-header", "--no-pdf-header-footer",
                file_url,
            ]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                pdf_ok = True
                size_mb = os.path.getsize(output_pdf) / 1024 / 1024
                print(f"[OK] PDF generated (Chrome CLI): {output_pdf} ({size_mb:.1f} MB)")
            else:
                print(f"[FAIL] Chrome CLI rendering failed: {result.stderr.decode()[:200]}")

    if not pdf_ok:
        print(f"[FAIL] PDF generation failed, please open HTML in browser and print to PDF")
        print(f"   HTML 文件: {html_path}")
        return html_path

    return output_pdf


def main():
    parser = argparse.ArgumentParser(description="生成专业制裁筛查 PDF 报告")
    parser.add_argument("input_md", help="输入 Markdown 报告文件路径")
    parser.add_argument(
        "-o", "--output", default=None, help="输出 PDF 路径（默认同名 .pdf）"
    )
    parser.add_argument(
        "--entity", default="Unknown Entity", help="实体名称（用于封面）"
    )
    parser.add_argument("--case-id", default=None, help="案例编号")

    args = parser.parse_args()

    if not args.output:
        args.output = os.path.splitext(args.input_md)[0] + ".pdf"

    generate_pdf(args.input_md, args.output, args.entity, args.case_id)


if __name__ == "__main__":
    main()
