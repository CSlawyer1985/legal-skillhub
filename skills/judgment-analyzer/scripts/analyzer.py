#!/usr/bin/env python3
"""
判决书文本提取脚本
功能：
1. 批量处理 PDF/Word 判决书
2. 提取纯文本内容
3. 保存到同名 .txt 文件
"""

import sys
import os
from pathlib import Path

try:
    import pdfplumber
    from docx import Document
except ImportError:
    print("缺少依赖库，请先运行: pip install -r requirements.txt")
    sys.exit(1)


def extract_from_pdf(file_path: str) -> str:
    """从 PDF 提取文本"""
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"  警告：读取 PDF 时出错 ({file_path}): {e}")
        return ""
    return "\n".join(text_parts)


def extract_from_word(file_path: str) -> str:
    """从 Word 文档提取文本"""
    try:
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"  警告：读取 Word 时出错 ({file_path}): {e}")
        return ""


def process_file(file_path: str, output_dir: str) -> bool:
    """处理单个文件"""
    file_path = Path(file_path)
    ext = file_path.suffix.lower()

    # 提取文本
    if ext == ".pdf":
        text = extract_from_pdf(str(file_path))
    elif ext in [".docx", ".doc"]:
        text = extract_from_word(str(file_path))
    else:
        return False

    if not text or len(text.strip()) < 50:
        print(f"  警告：文本内容过少或为空 ({file_path.name})")
        if text:
            print(f"  前100字符: {text[:100]}...")

    # 保存文本文件
    output_path = os.path.join(output_dir, f"{file_path.stem}.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"  -> {file_path.stem}.txt ({len(text)} 字符)")
    return True


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  单文件: python analyzer.py <文件路径>")
        print("  文件夹: python analyzer.py <文件夹路径>")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    # 确定输出目录
    if input_path.is_file():
        output_dir = input_path.parent / "摘要"
    else:
        output_dir = input_path / "摘要"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 处理输入
    if input_path.is_file():
        print(f"处理文件: {input_path.name}")
        success = process_file(str(input_path), str(output_dir))
        if success:
            print(f"完成！文本已保存到: {output_dir}")
        else:
            print("处理失败")
    elif input_path.is_dir():
        supported_ext = {'.pdf', '.docx', '.doc'}
        files = [f for f in input_path.iterdir()
                 if f.is_file() and f.suffix.lower() in supported_ext]

        print(f"找到 {len(files)} 份文件...")
        print(f"输出目录: {output_dir}\n")

        success_count = 0
        for i, f in enumerate(files, 1):
            print(f"[{i}/{len(files)}] {f.name}")
            if process_file(str(f), str(output_dir)):
                success_count += 1

        print(f"\n完成！成功处理 {success_count}/{len(files)} 份文件")
        print(f"文本已保存到: {output_dir}")
    else:
        print(f"错误：路径不存在 {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()