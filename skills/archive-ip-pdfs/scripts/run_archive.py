"""
CLI 入口脚本 (run_archive.py)
==============================

知识产权官文自动归档系统的命令行入口，接受用户指定的输入/输出目录，
动态配置系统路径后依次执行三个核心脚本。

用法:
  python -m scripts.run_archive --input <目标文件夹> [--output <输出文件夹>]
"""

import os
import sys
import argparse
import logging
from datetime import datetime

from . import config
from .script1_process import run as script1_run
from .script2_sync import run as script2_run
from .script3_report import run as script3_run

logger = logging.getLogger(__name__)


def setup_logging():
    """初始化日志系统，配置控制台和文件双输出。

    与 main.py 中的 setup_logging 类似，但增加了防重复配置检查：
    若 root logger 已有 handler 则跳过，避免在多次调用时产生重复日志。
    控制台输出 INFO 级别，文件输出 DEBUG 级别。
    """
    # 确保日志目录存在
    os.makedirs(config.LOG_DIR, exist_ok=True)
    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(config.LOG_DIR, f"{timestamp}system.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 防重复配置：若 root logger 已有 handler，说明日志系统已初始化，直接返回
    if root_logger.handlers:
        return

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # 控制台 handler：INFO 级别输出到终端
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件 handler：DEBUG 级别输出到日志文件（包含更详细的调试信息）
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def count_pdf_files(directory):
    """递归统计指定目录下的 PDF 文件数量。

    Args:
        directory (str): 要统计的目录路径

    Returns:
        int: PDF 文件数量
    """
    count = 0
    # 递归遍历目录树，统计所有 .pdf 后缀的文件
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(".pdf"):
                count += 1
    return count


def check_dependencies():
    """检查 PDF 解析库的安装状态。

    检测 pdfplumber、PyMuPDF(fitz)、PyPDF2 三个库是否可用，
    至少需要一个库才能正常解析 PDF 文件。

    Returns:
        tuple[list[str], list[str]]: (available, missing)
            - available: 已安装的库名列表
            - missing: 未安装的库名列表
    """
    available = []
    missing = []

    # 逐一尝试导入三个 PDF 解析库，记录可用和缺失情况
    try:
        import pdfplumber
        available.append("pdfplumber")
    except ImportError:
        missing.append("pdfplumber")

    try:
        import fitz
        available.append("PyMuPDF")
    except ImportError:
        missing.append("PyMuPDF")

    try:
        import PyPDF2
        available.append("PyPDF2")
    except ImportError:
        missing.append("PyPDF2")

    return available, missing


def main():
    """CLI 入口主函数：解析命令行参数并调度三个核心脚本。

    执行流程：
      1. 解析 --input 和 --output 命令行参数
      2. 调用 config.configure 配置系统路径
      3. 初始化日志系统
      4. 检查 PDF 解析库依赖
      5. 统计输入目录中的 PDF 文件数量
      6. 按顺序执行脚本1（扫描处理）、脚本2（路径同步）、脚本3（报表生成）
      7. 输出处理完成汇总信息

    Note:
        - 任一脚本异常将中断后续脚本执行
        - 若无 PDF 解析库可用，程序将以错误码 1 退出
        - 若输入目录不存在，程序将以错误码 1 退出
    """
    # 步骤1：定义命令行参数
    parser = argparse.ArgumentParser(
        description="知识产权官文自动归档系统"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="待处理的 PDF 文件所在目录（必选）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出根目录（可选，默认在输入目录的父目录下创建 ip_archives 文件夹）",
    )
    args = parser.parse_args()

    # 步骤2：验证输入目录是否存在
    input_dir = os.path.abspath(args.input)
    if not os.path.isdir(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}", file=sys.stderr)
        sys.exit(1)

    # 将输出目录转为绝对路径，若未指定则保持 None（由 configure 函数处理默认值）
    output_dir = os.path.abspath(args.output) if args.output else None

    # 步骤3：根据用户指定的目录重新配置系统全局路径
    config.configure(input_dir, output_dir)

    # 步骤4：初始化日志系统（需在 configure 之后，确保 LOG_DIR 已更新）
    setup_logging()

    # 步骤5：检查 PDF 解析库依赖
    available, missing = check_dependencies()
    if not available:
        # 没有任何可用的 PDF 解析库，无法继续执行
        msg = (
            "错误: 没有可用的 PDF 解析库，请至少安装以下库之一:\n"
            "  pip install pdfplumber\n"
            "  pip install pymupdf\n"
            "  pip install PyPDF2\n"
            f"当前缺失: {', '.join(missing)}"
        )
        print(msg, file=sys.stderr)
        logger.error(msg)
        sys.exit(1)

    if missing:
        # 部分库缺失，发出警告但可继续运行
        logger.warning(f"PDF 解析库部分缺失: {', '.join(missing)}（可用: {', '.join(available)}）")
    else:
        logger.info(f"PDF 解析库检测通过: {', '.join(available)}")

    # 步骤6：统计输入目录中的 PDF 文件数量
    pdf_count = count_pdf_files(input_dir)

    # 打印运行参数概览
    print("=" * 60)
    print("知识产权官文自动归档系统")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {config.BASE_DIR}")
    print(f"PDF 文件数量: {pdf_count}")
    print("=" * 60)

    # 若无 PDF 文件则直接退出，无需执行后续脚本
    if pdf_count == 0:
        print("未找到 PDF 文件，无需处理。")
        return

    logger.info("知识产权官文自动归档系统 - 开始运行")

    # 步骤7：按顺序执行三个核心脚本
    success_count = 0
    fail_count = 0

    # 脚本1：扫描并处理 PDF 文件（解析→归档→写入 CSV）
    try:
        script1_run()
    except Exception as e:
        logger.error(f"脚本1执行失败: {e}")
        raise

    # 脚本2：按标识号同步文件到组织化目录结构
    try:
        script2_run()
    except Exception as e:
        logger.error(f"脚本2执行失败: {e}")
        raise

    # 脚本3：生成知识产权汇总报表
    try:
        script3_run()
    except Exception as e:
        logger.error(f"脚本3执行失败: {e}")
        raise

    logger.info("知识产权官文自动归档系统 - 全部完成")

    # 步骤8：统计处理结果并输出汇总信息
    remaining = count_pdf_files(input_dir)
    processed = pdf_count - remaining

    print()
    print("=" * 60)
    print("处理完成汇总")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {config.BASE_DIR}")
    print(f"发现 PDF: {pdf_count} 个")
    print(f"已处理:   {processed} 个")
    print(f"剩余未处理: {remaining} 个")
    print()
    print(f"归档目录: {config.REPO_DIR}")
    print(f"CSV 目录: {config.CSV_DIR}")
    print(f"日志目录: {config.LOG_DIR}")
    print(f"未处理目录: {config.FAILED_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
