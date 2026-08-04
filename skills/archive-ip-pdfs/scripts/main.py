"""
系统入口模块 (main.py)
=======================

本模块是知识产权官文自动归档系统的入口点，负责：
  1. 初始化日志系统（控制台 + 文件双输出）
  2. 按顺序调度三个核心脚本：
     - 脚本1 (script1_process): 扫描临时目录中的 PDF，解析并归档
     - 脚本2 (script2_sync): 按标识号同步文件到组织化目录结构
     - 脚本3 (script3_report): 生成知识产权汇总报表

运行方式：
  - 作为模块运行: python -m scripts
  - 直接运行本文件: python main.py

注意：
  - 三个脚本按顺序执行，任一脚本异常将中断后续脚本的执行
  - 日志同时输出到控制台（INFO 级别）和文件（DEBUG 级别）
"""

import os
import logging
from datetime import datetime

from . import config
from .script1_process import run as script1_run
from .script2_sync import run as script2_run
from .script3_report import run as script3_run

logger = logging.getLogger(__name__)


def setup_logging():
    """初始化日志系统，配置控制台和文件双输出。

    控制台输出 INFO 级别日志，文件输出 DEBUG 级别日志。
    日志文件以时间戳命名，存放在 LOG_DIR 目录下。
    每次调用都会重新配置 root logger，可能产生重复 handler，
    适用于单次运行的脚本场景。
    """
    # 确保日志目录存在
    os.makedirs(config.LOG_DIR, exist_ok=True)
    # 生成带时间戳的日志文件名，便于区分不同次运行
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(config.LOG_DIR, f"{timestamp}system.log")

    # 设置 root logger 的最低日志级别为 INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 统一的日志格式：时间 [级别] 模块名: 消息
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # 控制台 handler：输出 INFO 及以上级别的日志到终端
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件 handler：输出 DEBUG 及以上级别的日志到文件（比控制台更详细）
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def main():
    """系统主入口函数。

    按顺序执行三个核心脚本，任一脚本异常将向上抛出以中断执行。
    每个脚本的执行状态通过日志记录，便于排查问题。
    """
    # 第一步：初始化日志系统
    setup_logging()

    logger.info("=" * 60)
    logger.info("知识产权官文自动归档系统 - 开始运行")
    logger.info("=" * 60)

    # 第二步：依次执行三个核心脚本，任一失败则中断后续脚本
    # 脚本1：扫描临时目录中的 PDF 文件，解析内容并归档到 archives 目录
    try:
        script1_run()
    except Exception as e:
        logger.error(f"脚本1执行失败: {e}")
        raise

    # 脚本2：按标识号将文件同步到组织化的目录结构中
    try:
        script2_run()
    except Exception as e:
        logger.error(f"脚本2执行失败: {e}")
        raise

    # 脚本3：根据归档数据生成知识产权汇总报表
    try:
        script3_run()
    except Exception as e:
        logger.error(f"脚本3执行失败: {e}")
        raise

    logger.info("=" * 60)
    logger.info("知识产权官文自动归档系统 - 全部完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
