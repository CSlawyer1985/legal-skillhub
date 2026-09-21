# -*- coding: utf-8 -*-
"""
扫描指定文件夹内的所有文件，按类型分类并给出处理建议。

用途：
  规则8要求"读取文件夹内所有文件，不遗漏任何凭证来源"。
  本脚本自动完成步骤0——扫描文件夹，列出所有文件，分类，提示哪些需要提取截图。

用法：
  python scan_folder.py "D:/案件文件夹路径"

输出：
  1. 按类型分类的文件清单
  2. 每个文件的处理建议（直接读取/提取内嵌图片/读取数据/解压等）
  3. 提示是否有"已整理但未报销"的文档
  4. 自动对 .docx 文件调用 extract_docx_images.py 提取内嵌图片（如存在）

依赖：
  仅需 Python 标准库（os, argparse, json, zipfile）
"""
import os
import sys
import argparse
import subprocess

# 文件类型分类
TYPE_MAP = {
    # 图片（独立截图，直接读取）
    'image': {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'},
    # Word文档（可能含内嵌截图）
    'word': {'.docx', '.doc', '.wps', '.odt'},
    # PDF（可能含行程单截图）
    'pdf': {'.pdf'},
    # Excel（可能含已整理数据和插入图片）
    'excel': {'.xlsx', '.xls', '.csv', '.et'},
    # PPT（可能含截图）
    'ppt': {'.pptx', '.ppt', '.dps'},
    # 压缩包（需先解压）
    'archive': {'.zip', '.rar', '.7z', '.tar', '.gz'},
    # 文本/数据
    'data': {'.json', '.txt', '.md'},
}

TYPE_LABELS = {
    'image': '图片（独立截图）',
    'word': 'Word文档（可能含内嵌截图）',
    'pdf': 'PDF文件（可能含截图）',
    'excel': 'Excel文件（可能含数据/图片）',
    'ppt': '演示文稿（可能含截图）',
    'archive': '压缩包（需先解压）',
    'data': '数据/文本文件',
    'other': '其他文件',
}

TYPE_ACTIONS = {
    'image': '→ 直接读取，提取日期/时间/路线/金额',
    'word': '→ 运行 extract_docx_images.py 提取内嵌截图 + 读取文档文字',
    'pdf': '→ 用PDF工具提取图片（如 pdfimages / PyMuPDF）',
    'excel': '→ 读取数据表 + 检查是否有插入图片',
    'ppt': '→ 解压后检查 ppt/media/ 下的图片',
    'archive': '→ 先解压，再扫描解压出的文件',
    'data': '→ 检查是否为行程数据（如 expense_data.json）',
    'other': '→ 评估是否与差旅费相关',
}


def get_file_type(ext):
    """根据扩展名返回文件类型分类"""
    ext = ext.lower()
    for ftype, exts in TYPE_MAP.items():
        if ext in exts:
            return ftype
    return 'other'


def scan_folder(folder_path):
    """扫描文件夹，返回按类型分类的文件清单"""
    if not os.path.exists(folder_path):
        print(f"错误：文件夹不存在 - {folder_path}")
        return None

    if not os.path.isdir(folder_path):
        print(f"错误：路径不是文件夹 - {folder_path}")
        return None

    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1]
            ftype = get_file_type(ext)
            rel_path = os.path.relpath(fpath, folder_path)
            size = os.path.getsize(fpath)
            all_files.append({
                'name': fname,
                'path': fpath,
                'rel_path': rel_path,
                'ext': ext,
                'type': ftype,
                'size': size,
            })

    # 按类型分组
    by_type = {}
    for f in all_files:
        by_type.setdefault(f['type'], []).append(f)

    return all_files, by_type


def print_report(folder_path, all_files, by_type):
    """打印扫描报告"""
    print("=" * 60)
    print(f"文件夹扫描报告")
    print(f"路径: {folder_path}")
    print(f"文件总数: {len(all_files)}")
    print("=" * 60)

    # 按类型顺序输出
    type_order = ['image', 'word', 'pdf', 'excel', 'ppt', 'archive', 'data', 'other']
    has_documents = False
    has_reimbursement_doc = False

    for ftype in type_order:
        files = by_type.get(ftype, [])
        if not files:
            continue

        label = TYPE_LABELS.get(ftype, ftype)
        action = TYPE_ACTIONS.get(ftype, '')
        print(f"\n【{label}】共 {len(files)} 个 {action}")
        print("-" * 50)

        for f in files:
            size_str = f"{f['size'] / 1024:.1f} KB" if f['size'] < 1024 * 1024 else f"{f['size'] / 1024 / 1024:.1f} MB"
            print(f"  {f['rel_path']}  ({size_str})")

            # 检查是否是已整理的报销文档
            name_lower = f['name'].lower()
            if any(kw in f['name'] for kw in ['报销', '差旅', '行程']) and ftype in ('word', 'excel', 'pdf'):
                has_reimbursement_doc = True
                print(f"    ⚠ 此文件可能是已整理的报销文档，内含已整理但未报销的行程截图！")
                print(f"    → 必须提取内嵌图片，与新截图合并汇总（规则8第5条）")

        if ftype in ('word', 'pdf', 'excel', 'ppt'):
            has_documents = True

    # 汇总提示
    print(f"\n{'=' * 60}")
    print("处理建议")
    print(f"{'=' * 60}")

    image_count = len(by_type.get('image', []))
    doc_count = sum(len(by_type.get(t, [])) for t in ('word', 'pdf', 'excel', 'ppt'))

    print(f"\n1. 独立截图: {image_count} 张 → 直接读取")
    if doc_count > 0:
        print(f"2. 文档文件: {doc_count} 个 → 必须提取内嵌截图（不能遗漏！）")
        has_documents = True
    if has_reimbursement_doc:
        print(f"3. ⚠ 发现已整理的报销文档 → 提取内嵌截图后与新截图合并汇总")
    if by_type.get('archive'):
        print(f"4. 压缩包: {len(by_type['archive'])} 个 → 先解压再扫描")

    if has_documents:
        print(f"\n{'=' * 60}")
        print("⚠ 重要提醒（规则8）")
        print(f"{'=' * 60}")
        print("  文件夹内包含文档文件，必须提取内嵌截图！")
        print("  不能只处理独立图片而忽略文档内的截图。")
        print("  同一文件夹 = 同一案件 = 合并报销。")
        print()

    return has_documents


def auto_extract_docx(folder_path, by_type, script_dir):
    """自动对 .docx 文件调用 extract_docx_images.py"""
    word_files = by_type.get('word', [])
    docx_files = [f for f in word_files if f['ext'].lower() == '.docx']

    if not docx_files:
        return

    extract_script = os.path.join(script_dir, 'extract_docx_images.py')
    if not os.path.exists(extract_script):
        print(f"\n（extract_docx_images.py 不在同级目录，跳过自动提取）")
        return

    print(f"\n{'=' * 60}")
    print(f"自动提取 .docx 内嵌图片（共 {len(docx_files)} 个）")
    print(f"{'=' * 60}")

    images_base = os.path.join(folder_path, 'images')
    if not os.path.exists(images_base):
        os.makedirs(images_base)

    for f in docx_files:
        # 用文件名（不含扩展名）作为子文件夹名
        case_name = os.path.splitext(f['name'])[0]
        output_dir = os.path.join(images_base, case_name, 'docx_extracted')

        print(f"\n  提取: {f['rel_path']}")
        print(f"  输出: {output_dir}")

        try:
            result = subprocess.run(
                [sys.executable, extract_script, f['path'], '--output', output_dir],
                capture_output=True, text=True, encoding='utf-8'
            )
            if result.returncode == 0:
                print(f"  ✓ 提取成功")
            else:
                print(f"  ✗ 提取失败: {result.stderr[:200]}")
        except Exception as e:
            print(f"  ✗ 执行出错: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='扫描文件夹内所有文件，按类型分类并给出处理建议（规则8自动化）'
    )
    parser.add_argument('folder', help='要扫描的文件夹路径')
    parser.add_argument(
        '--auto-extract', '-a',
        action='store_true',
        default=True,
        help='自动对 .docx 文件提取内嵌图片（默认开启）'
    )
    parser.add_argument(
        '--no-auto-extract',
        dest='auto_extract',
        action='store_false',
        help='不自动提取，只扫描报告'
    )
    args = parser.parse_args()

    result = scan_folder(args.folder)
    if result is None:
        sys.exit(1)

    all_files, by_type = result
    has_docs = print_report(args.folder, all_files, by_type)

    # 自动提取 docx 内嵌图片
    if args.auto_extract:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        auto_extract_docx(args.folder, by_type, script_dir)

    print(f"\n{'=' * 60}")
    print("扫描完成")
    print(f"{'=' * 60}")
    if has_docs:
        print("⚠ 文件夹内含文档文件，请确保已提取所有内嵌截图后再生成报销单。")
    else:
        print("文件夹内仅有图片文件，可直接读取生成报销单。")


if __name__ == '__main__':
    main()
