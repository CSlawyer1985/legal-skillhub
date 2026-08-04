#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采购合同文本提取脚本（固化版本 v2）
- 零外部依赖：仅使用 Python 标准库（Python 3.7+）
- 确保同一文档每次提取结果完全一致
- 支持格式：.docx, .pdf, .txt, .md
"""

import os
import sys
import re
import json
import hashlib
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


# ============================================================
# DOCX 解析（纯标准库：zipfile + xml.etree.ElementTree）
# ============================================================

# WordprocessingML 命名空间
NSMAP = {
    'w':  'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r':  'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'w14':'http://schemas.microsoft.com/office/word/2010/wordml',
}


def qn(tag: str) -> str:
    """生成带命名空间的 XML 标签（如 w:p -> {http://...}p）"""
    if ':' in tag:
        prefix, local = tag.split(':', 1)
        ns = NSMAP.get(prefix, '')
        return f'{{{ns}}}{local}'
    return tag


def extract_text_from_docx(file_path: str) -> str:
    """
    从 DOCX 文件提取文本（纯标准库实现）
    - 提取段落文本和表格内容
    - 忽略修订痕迹（Track Changes 的 ins/del/moveFrom/moveTo）
    - 按文档顺序输出
    """
    blocks = []  # [(type, text), ...] 保持文档顺序

    with zipfile.ZipFile(file_path, 'r') as zf:
        if 'word/document.xml' not in zf.namelist():
            raise ValueError("无效的 DOCX 文件：缺少 word/document.xml")

        doc_xml = zf.read('word/document.xml')
        root = ET.fromstring(doc_xml)

        body = root.find(qn('w:body'))
        if body is None:
            return ""

        for elem in body:
            # 提取标签本地名（去掉命名空间前缀）
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

            if tag == 'p':
                # 段落
                text = _extract_paragraph_text(elem)
                if text:
                    blocks.append(('para', text))

            elif tag == 'tbl':
                # 表格
                table_text = _extract_table_text(elem)
                if table_text:
                    blocks.append(('table', table_text))

            elif tag == 'sdt':
                # 结构化文档标签（如下拉列表、日期选择器等）
                for child in elem.iter():
                    child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if child_tag == 'p':
                        text = _extract_paragraph_text(child)
                        if text:
                            blocks.append(('para', text))

    # 组装输出：段落间双换行，表格用特殊标记
    result_parts = []
    for block_type, text in blocks:
        if block_type == 'table':
            result_parts.append(f'[表格内容]\n{text}')
        else:
            result_parts.append(text)

    return '\n\n'.join(result_parts)


def _extract_paragraph_text(para_elem) -> str:
    """
    提取段落文本，忽略修订痕迹
    - 跳过 w:del（删除标记，Track Changes 中的删除内容）
    - 只提取 w:r（正式运行）中未被删除的 w:t 文本
    """
    # 检查段落是否包含删除标记
    has_deletions = (
        para_elem.find(qn('w:del')) is not None or
        para_elem.find(qn('w:moveFrom')) is not None
    )

    texts = []

    for r_elem in para_elem.findall(qn('w:r')):
        # 跳过包含删除标记的运行
        if (r_elem.find(qn('w:del')) is not None or
            r_elem.find(qn('w:moveFrom')) is not None):
            continue

        # 跳过包含插入标记的运行（Track Changes 新增文本）
        if r_elem.find(qn('w:ins')) is not None:
            continue

        # 提取文本
        for t_elem in r_elem.findall(qn('w:t')):
            if t_elem.text:
                texts.append(t_elem.text)

    result = ''.join(texts).strip()

    # 如果段落完全由删除标记组成，返回空
    if has_deletions and not result:
        return ""

    return result


def _extract_table_text(table_elem) -> str:
    """提取表格内容，保留行列结构"""
    rows = []
    for row_elem in table_elem.findall(qn('w:tr')):
        cells = []
        for cell_elem in row_elem.findall(qn('w:tc')):
            cell_text_parts = []
            for p_elem in cell_elem.findall(qn('w:p')):
                para_text = _extract_paragraph_text(p_elem)
                if para_text:
                    cell_text_parts.append(para_text)
            cells.append(' '.join(cell_text_parts))
        rows.append(' | '.join(cells))

    return '\n'.join(rows)


# ============================================================
# PDF 解析（纯标准库：正则提取文本流）
# ============================================================

def extract_text_from_pdf(file_path: str) -> str:
    """
    从 PDF 文件提取文本（纯标准库实现）
    通过正则表达式提取文本流中的 BT...ET 块
    """
    with open(file_path, 'rb') as f:
        content = f.read()

    # 尝试解码为文本（PDF 通常是混合二进制）
    try:
        text = content.decode('latin-1', errors='ignore')
    except Exception:
        return ""

    # 提取文本块（BT ... ET）
    text_blocks = []
    bt_pattern = re.compile(r'BT(.*?)ET', re.DOTALL)

    for match in bt_pattern.finditer(text):
        block = match.group(1)

        # 提取 Tj 操作符（显示文本字符串）
        tj_texts = re.findall(r'\((.*?)\)\s*Tj', block)

        # 提取 TJ 操作符（文本数组）
        tj_arrays = re.findall(r'\[(.*?)\]\s*TJ', block, re.DOTALL)
        for arr in tj_arrays:
            arr_texts = re.findall(r'\((.*?)\)', arr)
            tj_texts.extend(arr_texts)

        if tj_texts:
            text_blocks.append(' '.join(tj_texts))

    result = '\n\n'.join(text_blocks)

    # 检测是否为扫描件（无文本内容）
    if not result.strip():
        return "[警告] 此PDF可能为扫描件，无可提取的文本内容。请使用OCR工具处理。"

    return result


# ============================================================
# TXT/MD 解析
# ============================================================

def extract_text_from_txt(file_path: str) -> str:
    """从 TXT/MD 文件提取文本，自动检测编码（UTF-8 → GBK 回退）"""
    # 优先尝试 UTF-8
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # 回退到 GBK（Windows 中文环境常见）
        with open(file_path, 'r', encoding='gbk', errors='replace') as f:
            content = f.read()

    # 统一换行符
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # 按段落分割后重新组合，去除空段落
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    return '\n\n'.join(paragraphs)


# ============================================================
# 文本标准化
# ============================================================

def normalize_text(text: str) -> str:
    """
    文本标准化（固化算法）
    - 去除零宽字符
    - 统一全角空格为半角
    - 标准化引号
    - 段落内压缩多余空白
    """
    # 去除零宽字符
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\ufeff]', '', text)

    # 统一全角空格为半角
    text = text.replace('\u3000', ' ')

    # 标准化引号（全角转半角）
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")

    # 去除多余空格（保留段落间分隔）
    lines = text.split('\n\n')
    normalized_lines = []
    for line in lines:
        # 段落内只保留单个空格
        line = ' '.join(line.split())
        if line:
            normalized_lines.append(line)

    return '\n\n'.join(normalized_lines)


# ============================================================
# 主函数
# ============================================================

def extract_contract_text(file_path: str) -> dict:
    """
    提取合同文本主函数
    返回包含文本内容和元数据的字典
    """
    path = Path(file_path)

    if not path.exists():
        return {"error": f"文件不存在: {file_path}"}

    ext = path.suffix.lower()
    extractors = {
        '.docx': extract_text_from_docx,
        '.pdf':  extract_text_from_pdf,
        '.txt':  extract_text_from_txt,
        '.md':   extract_text_from_txt,
    }

    if ext not in extractors:
        return {"error": f"不支持的文件格式: {ext}，支持: {list(extractors.keys())}"}

    raw_text = extractors[ext](file_path)
    normalized_text = normalize_text(raw_text)
    content_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

    return {
        "file_name":       path.name,
        "file_size":       path.stat().st_size,
        "file_type":       ext,
        "content_hash":    content_hash,
        "text":            normalized_text,
        "paragraph_count": len(normalized_text.split('\n\n')),
        "char_count":      len(normalized_text),
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python extract_contract.py <合同文件路径>")
        print("支持的格式: .docx, .pdf, .txt, .md")
        print("特点: 零外部依赖，仅使用Python标准库（Python 3.7+）")
        sys.exit(1)

    file_path = sys.argv[1]
    result = extract_contract_text(file_path)

    if "error" in result:
        print(f"错误: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
