#!/usr/bin/env python3
"""
使用 pywin32 将 .doc 格式文件转换为 .docx 格式

依赖: pywin32 (pip install pywin32)
运行环境: Windows + Microsoft Word

用法:
    python doc_converter.py <input_doc> [--output <output_docx>]

如果未指定 --output，则输出文件与输入文件同目录，扩展名改为 .docx。
"""

# argparse 用于解析命令行参数
import argparse
# os 提供操作系统接口，如路径处理
import os
# sys 提供系统相关功能，如退出程序
import sys
# tempfile 用于创建临时文件和目录
import tempfile
# Path 是 pathlib 模块中的类，用于面向对象地处理文件路径
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
    # 尝试导入 pywin32 的 COM 客户端模块
    # 这个模块允许 Python 调用 Windows 的 COM 接口，从而控制 Microsoft Word
    try:
        import win32com.client
    except ImportError:
        # 如果导入失败，说明 pywin32 没有安装
        raise ImportError(
            "pywin32 未安装，请运行: pip install pywin32\n"
            "注意：pywin32 仅支持 Windows 平台，且需要安装 Microsoft Word"
        )

    # 将输入路径转换为 Path 对象，并解析为绝对路径
    input_path = Path(input_path).resolve()

    # 检查输入文件是否存在
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    # 检查输入文件是否是 .doc 格式
    if input_path.suffix.lower() not in (".doc",):
        raise ValueError(f"输入文件必须是 .doc 格式，当前为: {input_path.suffix}")

    # 如果没有指定输出路径，则将输出文件放在输入文件同目录，扩展名改为 .docx
    if output_path is None:
        output_path = input_path.with_suffix(".docx")
    else:
        # 如果指定了输出路径，同样解析为绝对路径
        output_path = Path(output_path).resolve()

    # 确保输出目录存在，如果不存在则创建
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 初始化 Word 应用和文档对象为 None，用于后续的清理
    word = None
    doc = None
    try:
        # 创建 Word 应用实例（COM 对象）
        # 这相当于在后台启动 Microsoft Word
        word = win32com.client.Dispatch("Word.Application")
        # 设置 Word 不可见，避免弹出窗口
        word.Visible = False
        # 关闭所有警告和提示框（如兼容性检查等）
        word.DisplayAlerts = 0

        # 获取输入和输出的绝对路径字符串
        abs_input = str(input_path)
        abs_output = str(output_path)

        # 打开输入的 .doc 文件
        # ReadOnly=True: 以只读方式打开，避免修改原文件
        # AddToRecentFiles=False: 不添加到最近文件列表
        # Visible=False: 不显示文档窗口
        doc = word.Documents.Open(
            abs_input,
            ReadOnly=True,
            AddToRecentFiles=False,
            Visible=False,
        )

        # wdFormatXMLDocument = 12 是 Word 中 .docx 格式的文件格式代码
        wdFormatXMLDocument = 12
        # 将文档另存为 .docx 格式
        doc.SaveAs2(
            abs_output,
            FileFormat=wdFormatXMLDocument,
        )

        # 转换成功，打印信息并返回输出路径
        print(f"转换成功: {input_path.name} -> {output_path.name}")
        return str(output_path)

    except Exception as e:
        # 如果发生异常，尝试删除可能已生成的不完整输出文件
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        # 抛出运行时错误，说明转换失败
        raise RuntimeError(f"转换 .doc -> .docx 失败: {e}")

    finally:
        # 无论成功与否，都要清理资源
        # 关闭文档（不保存更改）
        if doc is not None:
            try:
                doc.Close(SaveChanges=False)
            except Exception:
                pass
        # 退出 Word 应用
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass


def is_doc_file(file_path: str) -> bool:
    """判断文件是否为 .doc 格式（非 .docx）"""
    # 将路径转为 Path 对象，检查后缀名是否为小写的 .doc
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
    # 将输入路径解析为绝对路径
    input_path = Path(input_path).resolve()

    # 如果已经是 .docx 格式，直接返回路径，标记为未转换
    if input_path.suffix.lower() == ".docx":
        return str(input_path), False

    # 如果是 .doc 格式，进行转换
    if input_path.suffix.lower() == ".doc":
        # 确定输出目录：优先使用传入的工作目录，否则使用输入文件所在目录
        if work_dir:
            output_dir = Path(work_dir)
        else:
            output_dir = input_path.parent

        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        # 生成输出文件名：原文件名 + _converted.docx
        output_path = output_dir / f"{input_path.stem}_converted.docx"

        # 调用转换函数
        docx_path = convert_doc_to_docx(str(input_path), str(output_path))
        return docx_path, True

    # 不支持的文件格式，抛出错误
    raise ValueError(f"不支持的文件格式: {input_path.suffix}，仅支持 .doc 和 .docx")


def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="将 .doc 文件转换为 .docx 格式")
    # 添加输入文件参数（位置参数，必填）
    parser.add_argument("input", help="输入 .doc 文件路径")
    # 添加输出文件参数（可选，--output 指定）
    parser.add_argument("--output", default=None, help="输出 .docx 文件路径（默认与输入同目录）")
    # 解析命令行参数
    args = parser.parse_args()

    # 执行转换并打印结果
    result = convert_doc_to_docx(args.input, args.output)
    print(f"输出文件: {result}")


# 当直接运行此脚本时执行 main 函数
if __name__ == "__main__":
    main()
