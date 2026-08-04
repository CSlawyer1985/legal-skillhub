"""
CSV 管理模块 (csv_manager.py)
==============================

本模块提供对 CSV 文件的增删改查操作，是系统数据持久化的核心工具层。
所有 CSV 文件均使用 UTF-8-BOM (utf-8-sig) 编码，确保 Excel 打开时
中文不乱码。

主要功能：
  - init_csv: 初始化 CSV 文件（含列头校验与自动修复）
  - read_csv: 读取 CSV 全部记录
  - write_csv: 全量覆写 CSV 文件
  - append_records: 追加记录到 CSV 文件
  - update_record: 按索引更新单条记录
  - find_by_application_number: 按申请号查找记录
  - update_file_paths: 批量更新文件路径（用于文件迁移同步）
  - get_next_seq: 获取下一个自增序号

性能考虑：
  - 所有写操作均为全量覆写（read → modify → write），适用于中小规模数据
  - 若数据量达到数万条以上，建议引入数据库替代 CSV 存储
"""

import os
import csv
import shutil
import logging

logger = logging.getLogger(__name__)

# 编码探测候选列表，按优先级排列：
# utf-8-sig: 带 BOM 的 UTF-8，本系统默认写入编码，优先尝试
# utf-8: 无 BOM 的标准 UTF-8
# gbk: 简体中文 Windows 常见编码
# gb18030: GBK 的超集，兼容性更广
# latin-1: 兜底编码，任何字节都不会解码失败
_ENCODING_CANDIDATES = ["utf-8-sig", "utf-8", "gbk", "gb18030", "latin-1"]


def _detect_encoding(csv_path):
    # 依次尝试每种候选编码，读取前 4096 字节验证是否可正确解码
    for enc in _ENCODING_CANDIDATES:
        try:
            with open(csv_path, "r", encoding=enc) as f:
                f.read(4096)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 所有候选编码均失败时，回退到默认的 utf-8-sig
    return "utf-8-sig"


def _open_csv_read(csv_path):
    # 自动检测文件编码后以正确编码打开文件，供后续 CSV 读取使用
    enc = _detect_encoding(csv_path)
    return open(csv_path, "r", encoding=enc)


def init_csv(csv_path, columns):
    """初始化 CSV 文件，确保文件存在且列头与预期一致。

    若文件不存在，则创建并写入表头；若文件已存在但列头不符，
    则保留已有数据并重新写入正确的表头（缺失列填充空值）。

    Args:
        csv_path (str): CSV 文件的完整路径
        columns (list[str]): 期望的列名列表，同时决定列的顺序
    """
    # 确保目录存在，避免写入时因目录缺失而报错
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if not os.path.exists(csv_path):
        # 文件不存在：创建新文件并写入表头
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
        logger.info(f"已初始化CSV文件: {csv_path}")
    else:
        # 文件已存在：检查列头是否与预期一致
        with _open_csv_read(csv_path) as f:
            reader = csv.DictReader(f)
            existing_columns = reader.fieldnames
            if existing_columns != columns:
                # 列头不匹配：需要修复，先备份原文件
                logger.warning(f"CSV文件 {csv_path} 的列头与预期不符，将重新写入表头")
                backup_path = csv_path + ".bak"
                shutil.copy2(csv_path, backup_path)
                logger.info(f"已备份原文件至: {backup_path}")
                # 读取已有数据记录
                records = list(reader)
                # 以新列头重新写入，缺失列自动填充空值
                with open(csv_path, "w", newline="", encoding="utf-8-sig") as f2:
                    writer = csv.DictWriter(f2, fieldnames=columns)
                    writer.writeheader()
                    for record in records:
                        row = {col: record.get(col, "") for col in columns}
                        writer.writerow(row)


def read_csv(csv_path):
    """读取 CSV 文件的全部记录。

    Args:
        csv_path (str): CSV 文件的完整路径

    Returns:
        list[dict]: 以字典列表形式返回所有记录，每条记录的键为列名。
                    若文件不存在则返回空列表。
    """
    if not os.path.exists(csv_path):
        return []
    with _open_csv_read(csv_path) as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_csv(csv_path, records, fieldnames=None):
    """全量覆写 CSV 文件。

    将提供的记录列表完整写入 CSV 文件（先清空再写入），
    列名由 fieldnames 参数或第一条记录的键决定。

    Args:
        csv_path (str): CSV 文件的完整路径
        records (list[dict]): 要写入的记录列表，每条记录为列名→值的字典
        fieldnames (list[str] | None): 可选的列名列表。若提供则强制使用此列名顺序；
                                       若不提供则自动从第一条记录的键推断

    Note:
        若 records 为空则直接返回，不执行任何写操作。
    """
    if not records:
        return
    # 若未指定列名，则从第一条记录的键推断列名及顺序
    if fieldnames is None:
        fieldnames = list(records[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            # 确保每行数据包含所有列，缺失列填充空值
            row = {col: record.get(col, "") for col in fieldnames}
            writer.writerow(row)


def append_records(csv_path, records, columns=None):
    """向 CSV 文件追加记录。

    若文件不存在或为空，则同时写入表头；若文件已存在，则在末尾追加。
    列名的确定优先级：columns 参数 > 已有文件的表头 > 第一条记录的键。

    Args:
        csv_path (str): CSV 文件的完整路径
        records (list[dict]): 要追加的记录列表
        columns (list[str] | None): 可选的列名列表。若提供则强制使用此列名顺序；
                                    若不提供则自动推断

    Note:
        若 records 为空则直接返回。追加时缺失的列自动填充空值。
    """
    if not records:
        return

    # 判断文件是否已存在且非空，决定是否需要写入表头
    file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0

    # 按优先级确定列名：显式传入 > 已有文件表头 > 第一条记录的键
    if columns:
        fieldnames = columns
    elif file_exists:
        with _open_csv_read(csv_path) as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or list(records[0].keys())
    else:
        fieldnames = list(records[0].keys())

    # 以追加模式打开文件，仅在新文件时写入表头
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for record in records:
            row = {col: record.get(col, "") for col in fieldnames}
            writer.writerow(row)


def update_record(csv_path, index, updates):
    """按索引更新 CSV 中的单条记录。

    读取全部记录后，对指定索引的记录执行字典更新，再全量覆写。

    Args:
        csv_path (str): CSV 文件的完整路径
        index (int): 要更新的记录索引（从 0 开始）
        updates (dict): 需要更新的字段键值对，如 {"法律状态": "授权"}
    """
    # 读取全部记录
    records = read_csv(csv_path)
    if 0 <= index < len(records):
        # 对目标记录执行字典合并更新
        records[index].update(updates)
        # 全量覆写回文件
        write_csv(csv_path, records)
    else:
        logger.error(f"CSV更新失败: 索引 {index} 超出范围（共 {len(records)} 条记录）")


def find_by_application_number(csv_path, app_number):
    """按申请号查找匹配的记录。

    Args:
        csv_path (str): CSV 文件的完整路径
        app_number (str): 要查找的申请号

    Returns:
        list[dict]: 所有"申请号"字段与 app_number 匹配的记录列表
    """
    records = read_csv(csv_path)
    # 过滤出申请号匹配的所有记录（同一申请号可能有多条归档记录）
    return [r for r in records if r.get("申请号") == app_number]


def update_file_paths(csv_path, path_mapping):
    """批量更新 CSV 中的文件路径字段。

    当文件从旧路径迁移到新路径时，根据路径映射表更新所有受影响记录的
    "文件路径"字段。仅在有变更时才执行写入。

    Args:
        csv_path (str): CSV 文件的完整路径
        path_mapping (dict[str, str]): 旧路径→新路径的映射字典

    Returns:
        bool: 是否有记录被更新（True 表示有变更并已写入）
    """
    records = read_csv(csv_path)
    updated = False
    # 遍历所有记录，检查文件路径是否在映射表中
    for record in records:
        old_path = record.get("文件路径", "")
        if old_path in path_mapping:
            record["文件路径"] = path_mapping[old_path]
            updated = True
    # 仅当有变更时才执行写入，避免无意义的 I/O 操作
    if updated:
        write_csv(csv_path, records)
    return updated


def get_next_seq(csv_path):
    """获取 CSV 文件中下一个可用的自增序号。

    遍历所有记录的"序号"字段，返回最大值 + 1。
    若文件为空或不存在则返回 1。

    Args:
        csv_path (str): CSV 文件的完整路径

    Returns:
        int: 下一个可用的序号值

    Note:
        若某条记录的"序号"无法转为整数，则跳过该记录。
    """
    records = read_csv(csv_path)
    if not records:
        return 1
    # 遍历所有记录，找出最大的序号值
    max_seq = 0
    for r in records:
        try:
            seq = int(r.get("序号", 0))
            if seq > max_seq:
                max_seq = seq
        except (ValueError, TypeError):
            # 序号字段无法转为整数时跳过该记录
            pass
    return max_seq + 1
