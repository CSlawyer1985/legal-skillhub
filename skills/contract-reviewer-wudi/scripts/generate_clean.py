#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清洁版生成器
从带修订痕迹的 docx 文件中移除所有 Track Changes 和批注，生成清洁版 docx
同时支持直接接受所有修订（保留插入内容、删除被删内容）

工作方式：
  方式一（直接处理 docx）：接受所有修订 → 移除批注 → 输出清洁版
  方式二（处理 unpacked 目录）：直接对 XML 操作，无需 LibreOffice

接受修订 = 保留 w:ins 内容 + 删除 w:del 内容
"""

import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import tempfile
import shutil

ET.register_namespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
ET.register_namespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
ET.register_namespace('w14', 'http://schemas.microsoft.com/office/word/2010/wordml')
ET.register_namespace('w15', 'http://schemas.microsoft.com/office/word/2012/wordml')
ET.register_namespace('mc', 'http://schemas.openxmlformats.org/markup-compatibility/2006')

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
W14 = 'http://schemas.microsoft.com/office/word/2010/wordml'
W15 = 'http://schemas.microsoft.com/office/word/2012/wordml'


def qn(tag):
    return f'{{{W}}}{tag}'


# ============================================================
# 核心 XML 操作
# ============================================================

def accept_changes_in_xml(xml_bytes):
    """
    接受 XML 中的所有修订：
    - w:ins 内容保留（去掉 ins 标签，保留内部内容）
    - w:del 内容删除（整个 w:del 元素去掉）
    - 移除批注标记和引用
    """
    root = ET.fromstring(xml_bytes)

    # 1. 处理 w:ins（保留内容，移除标签）
    for ins in list(root.iter(qn('ins'))):
        parent = _find_parent(root, ins)
        if parent is not None:
            idx = list(parent).index(ins)
            # 将 ins 的子元素（w:r 等）插入到 ins 原来的位置
            for i, child in enumerate(ins):
                new_child = ET.Element(child.tag, attrib=child.attrib)
                new_child.text = child.text
                new_child.tail = child.tail
                for subchild in child:
                    new_child.append(subchild)
                parent.insert(idx + i, new_child)
            # 复制 ins 的 tail 到最后一个子元素
            if len(ins) > 0:
                last = parent[idx + len(ins) - 1]
                if last.tail is None:
                    last.tail = ins.tail or ''
            elif parent[idx].tail is None:
                parent[idx].tail = ins.tail or ''
            parent.remove(ins)

    # 2. 处理 w:del（删除整个元素）
    for del_elem in list(root.iter(qn('del'))):
        parent = _find_parent(root, del_elem)
        if parent is not None:
            # 将 del 的 tail 传递给前一个元素
            prev_sibling = _get_previous_sibling(parent, del_elem)
            parent.remove(del_elem)
            if prev_sibling is not None and del_elem.tail:
                if prev_sibling.tail:
                    prev_sibling.tail += del_elem.tail
                else:
                    prev_sibling.tail = del_elem.tail

    # 3. 移除批注标记
    for tag in ['commentRangeStart', 'commentRangeEnd', 'commentReference']:
        for elem in list(root.iter(qn(tag))):
            parent = _find_parent(root, elem)
            if parent is not None:
                prev = _get_previous_sibling(parent, elem)
                parent.remove(elem)
                if prev is not None and elem.tail:
                    if prev.tail:
                        prev.tail += elem.tail
                    else:
                        prev.tail = elem.tail

    return ET.tostring(root, encoding='unicode')


def remove_comments_from_xml(xml_bytes):
    """移除批注标记（保留修订内容，仅清除批注）"""
    root = ET.fromstring(xml_bytes)

    for tag in ['commentRangeStart', 'commentRangeEnd', 'commentReference']:
        for elem in list(root.iter(qn(tag))):
            parent = _find_parent(root, elem)
            if parent is not None:
                parent.remove(elem)

    return ET.tostring(root, encoding='unicode')


def _find_parent(root, target):
    """通过遍历找到 target 的父元素"""
    for parent in root.iter():
        if target in parent:
            return parent
    return None


def _get_previous_sibling(parent, child):
    """获取前一个兄弟元素"""
    children = list(parent)
    try:
        idx = children.index(child)
        if idx > 0:
            return children[idx - 1]
    except ValueError:
        pass
    return None


# ============================================================
# 文件操作
# ============================================================

def process_docx(input_path, output_path, mode='accept_and_remove_comments'):
    """
    处理 docx 文件

    参数:
        input_path: 输入 docx 路径
        output_path: 输出 docx 路径
        mode: 
            'accept_and_remove_comments' = 接受修订 + 移除批注（最常用）
            'accept_only' = 仅接受修订，保留批注标记
            'remove_comments_only' = 保留修订，移除批注
            'remove_all' = 移除所有修订痕迹 + 批注（删除的文本真的删掉）
    """
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        extract_dir = tmpdir / 'extracted'
        extract_dir.mkdir()

        # 解压 docx
        with zipfile.ZipFile(input_path, 'r') as zf:
            zf.extractall(extract_dir)

        # 处理 document.xml
        doc_xml_path = extract_dir / 'word' / 'document.xml'
        if doc_xml_path.exists():
            with open(doc_xml_path, 'rb') as f:
                doc_xml = f.read()

            if mode == 'accept_and_remove_comments':
                doc_xml = accept_changes_in_xml(doc_xml)
                doc_xml = remove_comments_from_xml(doc_xml.encode('utf-8'))
            elif mode == 'accept_only':
                doc_xml = accept_changes_in_xml(doc_xml)
            elif mode == 'remove_comments_only':
                doc_xml = remove_comments_from_xml(doc_xml.encode('utf-8'))
            elif mode == 'remove_all':
                doc_xml = accept_changes_in_xml(doc_xml)
                doc_xml = remove_comments_from_xml(doc_xml.encode('utf-8'))

            with open(doc_xml_path, 'w', encoding='utf-8') as f:
                f.write(doc_xml)

        # 删除 comments.xml（如果 mode 包含移除批注）
        if 'remove_comments' in mode or mode == 'accept_and_remove_comments':
            comments_path = extract_dir / 'word' / 'comments.xml'
            if comments_path.exists():
                comments_path.unlink()

            # 从 [Content_Types].xml 移除 comments 类型
            ct_path = extract_dir / '[Content_Types].xml'
            if ct_path.exists():
                tree = ET.parse(ct_path)
                root = tree.getroot()
                CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
                for override in list(root.findall(f'{{{CT_NS}}}Override')):
                    if 'comments' in override.get('PartName', ''):
                        root.remove(override)
                tree.write(ct_path, encoding='utf-8', xml_declaration=True)

            # 从 document.xml.rels 移除 comments 关系
            rels_path = extract_dir / 'word' / '_rels' / 'document.xml.rels'
            if rels_path.exists():
                tree = ET.parse(rels_path)
                root = tree.getroot()
                R_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
                for rel in list(root.findall(f'{{{R_NS}}}Relationship')):
                    if 'comments' in rel.get('Target', ''):
                        root.remove(rel)
                tree.write(rels_path, encoding='utf-8', xml_declaration=True)

        # 重新打包为 docx
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in extract_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(extract_dir)
                    zf.write(file_path, arcname)

    return {'success': True, 'output': str(output_path)}


def process_unpacked_dir(input_dir, output_path, mode='accept_and_remove_comments'):
    """
    直接处理 unpacked docx 目录（无需先打包）
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc_xml_path = input_dir / 'word' / 'document.xml'
    if not doc_xml_path.exists():
        return {'success': False, 'error': f'文件不存在: {doc_xml_path}'}

    with open(doc_xml_path, 'rb') as f:
        doc_xml = f.read()

    if mode == 'accept_and_remove_comments':
        doc_xml = accept_changes_in_xml(doc_xml)
        doc_xml = remove_comments_from_xml(doc_xml.encode('utf-8'))
    elif mode == 'accept_only':
        doc_xml = accept_changes_in_xml(doc_xml)
    elif mode == 'remove_comments_only':
        doc_xml = remove_comments_from_xml(doc_xml.encode('utf-8'))
    elif mode == 'remove_all':
        doc_xml = accept_changes_in_xml(doc_xml)
        doc_xml = remove_comments_from_xml(doc_xml.encode('utf-8'))

    with open(doc_xml_path, 'w', encoding='utf-8') as f:
        f.write(doc_xml)

    # 如果输出路径不同（指定了新的 unpacked 目录），复制整个目录
    if output_path != input_dir:
        if output_path.exists():
            shutil.rmtree(output_path)
        shutil.copytree(input_dir, output_path)

    return {'success': True, 'output': str(output_path)}


# ============================================================
# 命令行入口
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='从带修订痕迹的 docx 生成清洁版'
    )
    parser.add_argument('input', help='输入 docx 文件或 unpacked 目录')
    parser.add_argument('output', help='输出文件路径')
    parser.add_argument(
        '--mode',
        choices=['accept_and_remove_comments', 'accept_only', 'remove_comments_only', 'remove_all'],
        default='accept_and_remove_comments',
        help='处理模式（默认: accept_and_remove_comments）'
    )
    parser.add_argument('--unpacked', action='store_true',
                        help='input 是 unpacked 目录而非 docx 文件')
    args = parser.parse_args()

    if args.unpacked:
        result = process_unpacked_dir(args.input, args.output, args.mode)
    else:
        result = process_docx(args.input, args.output, args.mode)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
