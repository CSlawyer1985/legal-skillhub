#!/usr/bin/env python3
"""
使用 pywin32 将 .doc 格式文件转换为 .docx 格式

依赖: pywin32 (pip install pywin32)
运行环境: Windows + Microsoft Word

用法:
    python doc_converter.py <input_doc> [--output <output_docx>]

如果未指定 --output，则输出文件与输入文件同目录，扩展名改为 .docx。
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path


def convert_doc_to_docx(input_path: str, output_path: str = None) -> str:
    """
    使用 pywin32 (COM 自动化) 将 .doc 文件转换为 .docx 格式。

    Args:
        input_path: 输入 .doc 文件的绝对路径
        output_path: 输出 .docx 文件的绝对路径（可选，默认与输入同目录同文件名但扩展名为 .docx）

    Returns:
        转换后的 .docx 文件绝对路径

    Raises:
        ImportError: pywin32 未安装
        FileNotFoundError: 输入文件不存在
        RuntimeError: 转换失败
    """
    try:
        import win32com.client
    except ImportError:
        raise ImportError(
            "pywin32 未安装，请运行: pip install pywin32\n"
            "注意：pywin32 仅支持 Windows 平台，且需要安装 Microsoft Word"
        )

    input_path = Path(input_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    if input_path.suffix.lower() not in (".doc",):
        raise ValueError(f"输入文件必须是 .doc 格式，当前为: {input_path.suffix}")

    if output_path is None:
        output_path = input_path.with_suffix(".docx")
    else:
        output_path = Path(output_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    word = None
    doc = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0

        abs_input = str(input_path)
        abs_output = str(output_path)

        doc = word.Documents.Open(
            abs_input,
            ReadOnly=True,
            AddToRecentFiles=False,
            Visible=False,
        )

        wdFormatXMLDocument = 12
        doc.SaveAs2(
            abs_output,
            FileFormat=wdFormatXMLDocument,
        )

        print(f"转换成功: {input_path.name} -> {output_path.name}")
        return str(output_path)

    except Exception as e:
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        raise RuntimeError(f"转换 .doc -> .docx 失败: {e}")

    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass


def is_doc_file(file_path: str) -> bool:
    """判断文件是否为 .doc 格式（非 .docx）"""
    path = Path(file_path)
    return path.suffix.lower() == ".doc"


def ensure_docx(input_path: str, work_dir: str = None) -> tuple:
    """
    确保输入文件为 .docx 格式。如果是 .doc 文件，则自动转换为 .docx。

    Args:
        input_path: 输入文件路径
        work_dir: 工作目录（用于存放转换后的临时 .docx 文件）

    Returns:
        (docx_path, was_converted): .docx 文件路径和是否进行了转换的标志
    """
    input_path = Path(input_path).resolve()

    if input_path.suffix.lower() == ".docx":
        return str(input_path), False

    if input_path.suffix.lower() == ".doc":
        if work_dir:
            output_dir = Path(work_dir)
        else:
            output_dir = input_path.parent

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{input_path.stem}_converted.docx"

        docx_path = convert_doc_to_docx(str(input_path), str(output_path))
        return docx_path, True

    raise ValueError(f"不支持的文件格式: {input_path.suffix}，仅支持 .doc 和 .docx")


def main():
    parser = argparse.ArgumentParser(description="将 .doc 文件转换为 .docx 格式")
    parser.add_argument("input", help="输入 .doc 文件路径")
    parser.add_argument("--output", default=None, help="输出 .docx 文件路径（默认与输入同目录）")
    args = parser.parse_args()

    result = convert_doc_to_docx(args.input, args.output)
    print(f"输出文件: {result}")


if __name__ == "__main__":
    main()
