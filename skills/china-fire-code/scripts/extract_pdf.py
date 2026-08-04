#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地 PDF 按需抽取（模式二 · 离线兜底）。

两种用法：
  1) 按需精确检索：给定 PDF + query（条款号或关键词），返回命中原文片段。
     python scripts/extract_pdf.py --pdf <文件> --query "6.2.3" [--std GB55037]
  2) 构建离线索引：把一个或一批本地 PDF 的条款目录抽取成索引文件，
     供「离线场景」快速定位（不存全文，仅存条款号+标题，版权低风险）。
     python scripts/extract_pdf.py --build-index --corpus <PDF目录> [--out ~/.firecode_offline]
     python scripts/extract_pdf.py --pdf <文件> --list            # 仅打印条款目录

依赖：pip install pymupdf   （可选 OCR：pip install paddleocr paddlepaddle）

版权纪律：本脚本只处理「用户自行下载到本地私有语料」的官方 PDF；
生成的离线索引默认写入用户主目录 ~/.firecode_offline/（仓库之外），
绝不随 skill 分发标准正文。索引仅作离线导航，引用须 ⚠️ 待官方核对，不得当 ✅。
"""

import re
import sys
import os
import argparse
import glob

try:
    import fitz  # PyMuPDF
except ImportError:
    print("╔══════════════════════════════════════════════╗")
    print("║  ⚠️  缺少 PDF 读取组件                      ║")
    print("║                                              ║")
    print("║  本功能需要安装一个免费工具（PyMuPDF），     ║")
    print("║  请在终端（命令行）中运行以下命令：          ║")
    print("║                                              ║")
    print("║    pip install pymupdf                       ║")
    print("║                                              ║")
    print("║  如果提示 'pip 不是内部命令'，请先安装       ║")
    print("║  Python（官网 python.org），或联系技术支持。   ║")
    print("╚══════════════════════════════════════════════╝")
    sys.exit(0)

# 内置兜底纠错词典（开发者已知系统性错字 → 正字）。
# 运行时还会自动叠加 references/term_memory.md 中人工确认过的映射（后者优先）。
TERM_FIX_BUILTIN = {
    "位千": "位于",
    "总 贝月": "总则",
}

CLAUSE_RE = re.compile(r'^\s*(\d+(?:\.\d+)*)\b')


def _base():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_term_memory():
    """加载 references/term_memory.md 中人工确认过的纠错映射（skill 记忆）。
    只认以「- 」开头的条目行，跳过标题/引用块/示例行。"""
    path = os.path.join(_base(), "references", "term_memory.md")
    fixes = {}
    if not os.path.exists(path):
        return fixes
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip().startswith("- "):
                continue
            m = re.search(r"`([^`]+)`\s*→\s*`([^`]+)`", line)
            if m:
                fixes[m.group(1)] = m.group(2)
    return fixes


# 合并：内置兜底 + 人工记忆（记忆优先）
TERM_MEMORY = load_term_memory()
TERM_FIX = {**TERM_FIX_BUILTIN, **TERM_MEMORY}


def extract_text_pymupdf(pdf_path):
    doc = fitz.open(pdf_path)
    chunks = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(chunks)


def ocr_text(pdf_path):
    """文字层为空时，渲染图片走可选 PaddleOCR。未安装则返回 None。"""
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        return None
    import tempfile
    doc = fitz.open(pdf_path)
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    except Exception:
        return None
    chunks = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            pix.save(tf.name)
            tmp = tf.name
        try:
            res = ocr.ocr(tmp)
            for page_res in res or []:
                for item in page_res or []:
                    chunks.append(item[1][0])
        finally:
            os.unlink(tmp)
    doc.close()
    return "\n".join(chunks)


def correct_terms(text):
    """应用纠错词典；返回 (修正后文本, 已应用映射列表[(wrong, right, src)])。
    src='memory' 表示来自已人工确认的 term_memory.md；'builtin' 表示内置兜底。"""
    applied = []
    for wrong, right in TERM_FIX.items():
        if wrong in text:
            text = text.replace(wrong, right)
            src = "memory" if wrong in TERM_MEMORY else "builtin"
            applied.append((wrong, right, src))
    return text, applied


def extract(pdf_path):
    text = extract_text_pymupdf(pdf_path)
    if len(text.strip()) < 80:  # 文字层基本为空（扫描件）
        ocr = ocr_text(pdf_path)
        if ocr:
            text = ocr
    return correct_terms(text)


def extract_clause_index(text):
    """从抽取文本解析条款目录：返回 [(条款号, 标题行+少量续行), ...]。"""
    lines = text.splitlines()
    idx, cur = [], None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        m = CLAUSE_RE.match(s)
        if m:
            if cur:
                idx.append(cur)
            cur = {"num": m.group(1), "title": s}
        elif cur is not None and len(cur["title"]) < 220:
            cur["title"] += " " + s
    if cur:
        idx.append(cur)
    return [(c["num"], c["title"]) for c in idx]


def _window(lines, i, ctx=0):
    window = [lines[i].strip()]
    j = i + 1
    while j < len(lines) and len(window) < 12:
        nxt = lines[j].strip()
        if not nxt:
            break
        if CLAUSE_RE.match(lines[j]) and j > i + 1:
            break
        window.append(nxt)
        j += 1
    if ctx:
        pre = [lines[k].strip() for k in range(max(0, i - ctx), i) if lines[k].strip()]
        window = pre + window
    return "\n".join(window)


def search(text, query):
    q = query.strip()
    lines = text.splitlines()
    qnum = q.replace(" ", "")
    is_num = bool(re.match(r'^[\d.]+$', qnum))

    if is_num:
        for i, ln in enumerate(lines):  # 精确匹配条款号
            m = CLAUSE_RE.match(ln)
            if m and m.group(1) == qnum:
                return _window(lines, i)
        for i, ln in enumerate(lines):  # 前缀匹配（如 6.2.3 → 6.2.3.2.1）
            m = CLAUSE_RE.match(ln)
            if m and m.group(1).startswith(qnum):
                return _window(lines, i)
    # keyword match：优先落在带条款号的上下文（避开目次/标题行）
    best = None
    first = None
    for i, ln in enumerate(lines):
        if q in ln:
            if first is None:
                first = i
            if CLAUSE_RE.search(_window(lines, i, ctx=2)):
                best = i
                break
    if best is not None:
        return _window(lines, best, ctx=2)
    if first is not None:
        return _window(lines, first, ctx=2)
    return None


def _index_header():
    return (
        "# 消防规范离线索引（_firecode_offline_index）\n\n"
        "> ⚠️ 本索引由 `scripts/extract_pdf.py --build-index` 从**用户本地私有 PDF** 自动生成，\n"
        "仅含「条款号 + 标题」用于离线快速定位，**不含标准正文**，版权风险低。\n"
        "> - 本文件位于用户主目录 `~/.firecode_offline/`，**不随 skill 仓库分发**。\n"
        "> - 离线引用须标 ⚠️ 待官方核对，**绝不当 ✅ 金标准**；联网后必须回 openstd 官方源复核。\n"
        "> - 标准 PDF 再分发受版权限制，请勿公开分享本索引所指向的原文。\n\n"
    )


def build_index(pdf_paths, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "_firecode_offline_index.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(_index_header())
        for p in pdf_paths:
            try:
                text, _ = extract(p)
            except Exception as e:
                f.write(f"\n## {os.path.basename(p)}\n- ⚠️ 抽取失败：{e}\n")
                continue
            idx = extract_clause_index(text)
            f.write(f"\n## {os.path.basename(p)}（{len(idx)} 条）\n")
            for num, title in idx:
                f.write(f"- `{num}` {title}\n")
    return out


def main():
    ap = argparse.ArgumentParser(
        description="消防规范 PDF 条文抽取工具（模式二）",
        epilog="示例: python extract_pdf.py --pdf GB55037.pdf --query '3.2.1'"
    )
    ap.add_argument("--pdf", help="PDF 文件路径")
    ap.add_argument("--query", help="要查找的条款号（如 6.2.3）或关键词")
    ap.add_argument("--std", default="", help="规范编号，用于标注引文")
    ap.add_argument("--list", action="store_true", help="仅列出该 PDF 的条款目录")
    ap.add_argument("--build-index", action="store_true", help="构建离线索引文件")
    ap.add_argument("--corpus", help="PDF 文件夹路径（配合 --build-index 使用）")
    ap.add_argument("--out", default=os.path.expanduser("~/.firecode_offline"),
                    help="索引保存位置（默认 ~/.firecode_offline）")
    args = ap.parse_args()

    # ---- build-index 分支 ----
    if args.build_index:
        paths = []
        if args.corpus:
            paths += sorted(glob.glob(os.path.join(args.corpus, "*.pdf")))
        if args.pdf:
            paths.append(args.pdf)
        if not paths:
            print("❌ 请告诉我 PDF 在哪里：")
            print("   --corpus <存放 PDF 的文件夹>")
            print("   或 --pdf <单个 PDF 文件名>")
            print("\n示例：python extract_pdf.py --build-index --corpus ./my_pdfs/")
            sys.exit(0)
        try:
            out = build_index(paths, args.out)
        except PermissionError:
            print(f"❌ 没有权限写入文件夹：{args.out}")
            print("   请检查该文件夹是否存在、是否被其他程序占用。")
            sys.exit(0)
        except OSError as e:
            print(f"❌ 写入失败：{e}")
            print("   请确认磁盘空间充足且有写入权限。")
            sys.exit(0)
        print(f"✅ 离线索引已生成：{out}")
        print(f"   共处理 {len(paths)} 个 PDF 文件")
        return

    # ---- 单文件查询分支 ----
    if not args.pdf:
        print("❌ 缺少参数：请用 --pdf 指定 PDF 文件")
        print("\n示例用法：")
        print("  python extract_pdf.py --pdf GB55037.pdf --query '疏散宽度'")
        print("  python extract_pdf.py --pdf GB55037.pdf --list")
        sys.exit(0)

    # 检查文件存在性（给用户友好提示）
    if not os.path.isfile(args.pdf):
        print(f"❌ 找不到文件：{args.pdf}")
        print("\n可能的原因：")
        print("  1. 文件名拼写错误——请检查是否包含中文/空格/特殊字符")
        print("  2. 路径不对——建议用绝对路径或把 PDF 放到当前目录")
        print("  3. 文件确实不存在——请先从官方渠道下载标准 PDF")
        print(f"\n当前目录下的 PDF 文件：")
        cwd_files = [f for f in glob.glob("*.pdf")]
        if cwd_files:
            for f in cwd_files[:10]:
                print(f"  📄 {f}")
        else:
            print("  （当前目录没有 .pdf 文件）")
        sys.exit(0)

    # 尝试打开 PDF
    try:
        text, applied = extract(args.pdf)
    except PermissionError:
        print(f"❌ 没有权限读取文件：{args.pdf}")
        print("   请检查文件是否被其他程序打开（如阅读器），或右键→属性→安全 查看权限。")
        sys.exit(0)
    except Exception as e:
        err_type = type(e).__name__
        if "fitz" in str(type(e)).lower() or "mupdf" in str(e).lower():
            print("❌ 无法读取这个 PDF 文件")
            print("\n可能的原因：")
            print("  • 文件损坏或不完整（下载中断？重新下载试试）")
            print("  • 文件加密或有密码保护")
            print("  • 不是有效的 PDF 文件（可能扩展名不对）")
            print(f"\n技术细节（如需反馈）：{e}")
        else:
            print(f"❌ 处理 PDF 时出错：{err_type}")
            print(f"\n详情：{e}")
            print("\n如果反复出现此问题，请把上面的信息反馈给我们。")
        sys.exit(0)

    if args.list:
        idx = extract_clause_index(text)
        if not idx:
            print(f"⚠️ 从「{os.path.basename(args.pdf)}」中没有解析出条款目录")
            print("   可能原因：这不是规范类 PDF / 是扫描图片版 / 格式特殊")
            return
        print(f"📋 条款目录 —— {os.path.basename(args.pdf)}（共 {len(idx)} 条）")
        print("-" * 50)
        for num, title in idx:
            print(f"  {num}\t{title[:80]}")
        return

    if not args.query:
        print("❌ 缺少查找内容：请用 --query 指定条款号或关键词")
        print("\n示例：")
        print("  python extract_pdf.py --pdf GB55037.pdf --query '3.2.1'")
        print("  python extract_pdf.py --pdf GB55037.pdf --query '疏散宽度'")
        sys.exit(0)

    if not text.strip():
        print("⚠️ 这个 PDF 好像是扫描版（图片），文字层为空")
        print("\n建议方案（按推荐顺序）：")
        print("  1. 安装 OCR 组件后重试：pip install paddleocr")
        print("  2. 去官网找可复制的文字版 PDF（非扫描版）")
        print("  3. 用联网检索代替（模式一）：直接问我要条文即可")
        sys.exit(0)

    passage = search(text, args.query)
    if not passage:
        print(f"🔍 在 PDF 中未找到匹配：「{args.query}」")
        print("\n你可以试试：")
        print("  • 用条款号搜索，如 '5.3' 或 '第 5.3.1 条'")
        print("  • 用更短的关键词，如 '疏散' 代替 '疏散宽度具体数值'")
        print("  • 先运行 --list 看看这个 PDF 里有哪些条款")
        sys.exit(0)

    print("=" * 52)
    print("  找到以下内容（来自本地 PDF · 请以官方版本为准）")
    print("=" * 52)
    print(passage)
    if applied:
        mem = [a for a in applied if a[2] == "memory"]
        bld = [a for a in applied if a[2] == "builtin"]
        if mem:
            print("\n💡 已自动修正已知错字：" +
                  "；".join(f"「{w}」→「{r}」" for w, r, _ in mem))
        if bld:
            print("\n⚠️ 发现疑似错字并自动替换了，**请务必人工核对一次**：")
            for w, r, _ in bld:
                print(f"   「{w}」→「{r}」")
    else:
        print("\n💡 未发现已知错字。如果你看到奇怪的字符，可以用以下命令帮我们记住正确写法：")
        print("      python scripts/term_memory.py add --wrong <错的字> --right <对的字>")

    if args.std:
        print(f"\n📎 建议引用格式：{args.std}（版本与施行日期见 规范速查表.md）")


def _safe_main():
    """顶层异常兜底——防止任何未预期的错误暴露 traceback 给用户。"""
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消（按 Ctrl+C 可随时退出）。")
    except Exception as e:
        print("\n╔══════════════════════════════════════╗")
        print("║  ⚠️  遇到了意外问题                    ║")
        print("╚══════════════════════════════════════╝")
        print(f"问题类型：{type(e).__name__}")
        print(f"详细信息：{e}")
        print("\n你可以：")
        print("  1. 检查 PDF 文件是否正常（能用阅读器打开吗？）")
        print("  2. 用 --help 查看完整使用说明")
        print("  3. 把上面的问题信息发给我们，我们会帮你解决")


if __name__ == "__main__":
    _safe_main()
