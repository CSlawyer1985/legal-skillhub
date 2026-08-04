#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销售合同文本提取脚本（固化版本）
确保同一文档每次提取结果完全一致

支持格式：.docx, .pdf, .txt
"""

import os
import sys
import re
import json
import hashlib
from pathlib import Path

# 尝试导入所需库
try:
    import docx
except ImportError:
    print("ERROR: python-docx 未安装，请运行: pip install python-docx")
    sys.exit(1)

try:
    import PyPDF2
except ImportError:
    print("WARNING: PyPDF2 未安装，PDF功能将受限。请运行: pip install PyPDF2")

def extract_text_from_docx(file_path: str) -> str:
    """
    从DOCX文件提取文本（固化算法）
    - 忽略修订痕迹(Track Changes)
    - 按段落顺序提取
    - 去除空段落
    - 统一换行符
    """
    doc = docx.Document(file_path)
    paragraphs = []
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:  # 跳过空段落
            paragraphs.append(text)
    
    # 统一使用双换行符分隔段落
    result = '\n\n'.join(paragraphs)
    return result

def extract_text_from_pdf(file_path: str) -> str:
    """从PDF文件提取文本"""
    text_parts = []
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text.strip())
    except Exception as e:
        print(f"PDF提取失败: {e}")
        return ""
    
    return '\n\n'.join([t for t in text_parts if t.strip()])

def extract_text_from_txt(file_path: str) -> str:
    """从TXT文件提取文本"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统一换行符
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # 去除首尾空白，按段落分割后重新组合
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    return '\n\n'.join(paragraphs)

def normalize_text(text: str) -> str:
    """
    文本标准化（固化算法）
    - 统一空白字符
    - 去除零宽字符
    - 标准化引号
    """
    # 去除零宽字符
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\ufeff]', '', text)
    
    # 统一全角空格为半角
    text = text.replace('\u3000', ' ')
    
    # 标准化引号（全角转半角）
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # 去除多余空格（保留段落间分隔）
    lines = text.split('\n\n')
    normalized_lines = []
    for line in lines:
        # 段落内只保留单个空格
        line = ' '.join(line.split())
        if line:
            normalized_lines.append(line)
    
    return '\n\n'.join(normalized_lines)

def extract_contract_text(file_path: str) -> dict:
    """
    提取合同文本主函数
    返回包含文本内容和元数据的字典
    """
    path = Path(file_path)
    
    if not path.exists():
        return {"error": f"文件不存在: {file_path}"}
    
    # 获取文件扩展名
    ext = path.suffix.lower()
    
    # 提取文本
    if ext == '.docx':
        raw_text = extract_text_from_docx(file_path)
    elif ext == '.pdf':
        raw_text = extract_text_from_pdf(file_path)
    elif ext in ['.txt', '.md']:
        raw_text = extract_text_from_txt(file_path)
    else:
        return {"error": f"不支持的文件格式: {ext}"}
    
    # 标准化文本
    normalized_text = normalize_text(raw_text)
    
    # 计算内容哈希（用于验证一致性）
    content_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
    
    # 提取基本信息
    file_size = path.stat().st_size
    file_name = path.name
    
    return {
        "file_name": file_name,
        "file_size": file_size,
        "file_type": ext,
        "content_hash": content_hash,
        "text": normalized_text,
        "paragraph_count": len(normalized_text.split('\n\n')),
        "char_count": len(normalized_text)
    }

def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python extract_contract.py <合同文件路径>")
        print("支持的格式: .docx, .pdf, .txt, .md")
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = extract_contract_text(file_path)
    
    if "error" in result:
        print(f"错误: {result['error']}")
        sys.exit(1)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
