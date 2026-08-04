#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同文件解析脚本
支持格式：PDF / DOCX / 图片 / 纯文本
用法：python3 parse_contract.py <file_path>
输出：提取的纯文本内容（stdout）
"""

import sys
import os

def extract_pdf(file_path):
    """提取 PDF 文本内容"""
    try:
        from markitdown import markitdown
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "markitdown", file_path],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception as e:
        return f"[PDF解析失败: {e}]"

def extract_docx(file_path):
    """提取 DOCX 文本内容"""
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except ImportError:
        # 尝试用 markitdown
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "markitdown", file_path],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception as e:
        return f"[DOCX解析失败: {e}]"

def extract_image(file_path):
    """OCR 识别图片中的文字"""
    try:
        # 尝试用系统和 Python 可用的 OCR 工具
        import subprocess
        # 先尝试 tesseract
        result = subprocess.run(
            ["tesseract", file_path, "stdout", "-l", "chi_sim+eng"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"[OCR识别失败，请安装 tesseract: brew install tesseract tesseract-lang]"
    except Exception as e:
        return f"[OCR识别失败: {e}，请安装 tesseract]"

def extract_txt(file_path):
    """读取纯文本文件"""
    for enc in ["utf-8", "gbk", "gb18030", "big5"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except:
            continue
    return "[文本读取失败，编码无法识别]"

def main():
    if len(sys.argv) < 2:
        print("用法：python3 parse_contract.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"[文件不存在: {file_path}]")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        content = extract_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        content = extract_docx(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        content = extract_image(file_path)
    elif ext in [".txt", ".md", ".text"]:
        content = extract_txt(file_path)
    else:
        # 尝试当作纯文本读取
        content = extract_txt(file_path)

    print(content)

if __name__ == "__main__":
    main()
