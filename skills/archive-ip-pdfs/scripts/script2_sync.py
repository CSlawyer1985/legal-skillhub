"""
脚本2：文件路径同步模块 (script2_sync.py)
==========================================

本脚本负责将archives中的 PDF 文件按目录结构重新组织，
使文件存储更加有序，便于人工查阅。

核心逻辑：
  1. 读取 CSV 中的每条记录，根据标识号、专利类型、法律状态、
     当前权利人计算目标文件夹名称
  2. 将文件从当前位置移动到目标文件夹
  3. 更新 CSV 中的文件路径字段
  4. 清理移动后产生的空文件夹

目录结构示例：
  archives/
  ├── 专利/
  │   ├── 公司A/                    ← 第一级：专利权人
  │   │   ├── 授权/                 ← 第二级：法律状态
  │   │   │   ├── CN202010123456.1_授予发明专利权通知书_公司A.pdf
  │   │   │   └── CN202010123456.1_发明专利证书_CN1234567B_公司A.pdf
  │   │   └── 审/
  │   │       └── CN202020123456.2_第一次审查意见通知书_公司A.pdf
  │   └── 公司B/
  │       └── 授权/
  │           └── ...
  ├── 商标/
  │   └── 75012345-第7类-已注册-公司A/
  │       └── ...
  └── 软著/
      ├── 公司A/                     ← 第一级：当前权利人
      │   └── 2023R11S1234567-受理申请-公司A/   ← 第二级：标识号-法律状态-当前权利人
      │       └── ...
      └── 公司B/
          └── 2024SR1234567-登记下证-公司B/
              └── ...

注意：
  - 专利采用两级分类：第一级按"当前权利人"，第二级按"法律状态"
  - 商标保持单级分类：{标识号}-{商标申请类别}-{法律状态}-{当前权利人}
  - 软著采用两级分类：第一级按"当前权利人"，第二级按{标识号}-{法律状态}-{当前权利人}
  - 文件移动使用 shutil.move，若目标文件已存在则跳过
  - 源文件不存在时仅更新路径记录，不报错
  - 空文件夹清理递归处理，从最深层向上删除空目录
"""

import os
import shutil
import logging

from . import config
from . import csv_manager
from .legal_status import group_by_identifier, compute_patent_report_status, compute_trademark_report_status, compute_software_report_status

logger = logging.getLogger(__name__)


def _sync_csv(csv_path, ip_type):
    """根据 CSV 记录将文件同步到组织化的目录结构。

    对每条记录：
      1. 获取标识号、法律状态、当前权利人，构建目标文件夹名
      2. 计算目标路径，若文件已在目标位置则跳过
      3. 若源文件存在则移动，否则仅更新路径记录

    所有移动完成后，批量更新 CSV 中的文件路径字段。

    Args:
        csv_path (str): CSV 文件路径
        ip_type (str): 知识产权类型（"专利"/"商标"/"软著"）
    """
    # CSV文件不存在则直接返回
    if not os.path.exists(csv_path):
        logger.info(f"CSV文件不存在，跳过: {csv_path}")
        return

    # 读取CSV中的所有记录
    records = csv_manager.read_csv(csv_path)
    if not records:
        logger.info(f"CSV文件无记录，跳过: {csv_path}")
        return

    # 根据知识产权类型确定archives下的子文件夹名称
    sub_folder_map = {"专利": "专利", "商标": "商标", "软著": "软著"}
    sub_folder = sub_folder_map.get(ip_type, "")
    if not sub_folder:
        return

    # path_mapping: 记录旧路径→新路径的映射，用于最后批量更新CSV
    path_mapping = {}

    # 根据知识产权类型，计算各标识号的法律状态和当前权利人
    # status_map 的结构为 {标识号: {"法律状态": ..., "当前权利人": ..., ...}}
    status_map = None
    if ip_type == "专利":
        status_map = compute_patent_report_status()
    elif ip_type == "商标":
        status_map = compute_trademark_report_status()
    elif ip_type == "软著":
        status_map = compute_software_report_status()

    # 商标需要额外收集每个标识号对应的商标类别（申请类别或注册类别）
    # 因为商标目录名中包含类别信息，但单条记录可能只有申请类别或注册类别之一
    category_map = {}
    if ip_type == "商标":
        for r in records:
            rid = r.get("标识号", "")
            if not rid:
                continue
            # 优先取申请类别，其次取注册类别
            cat = r.get("申请类别", "") or r.get("注册类别", "")
            if cat and rid not in category_map:
                category_map[rid] = cat

    # 遍历每条记录，计算目标目录并移动文件
    for record in records:
        identifier = record.get("标识号", "")
        if not identifier:
            continue

        # 从 status_map 中获取该标识号的法律状态和当前权利人
        # 优先使用 status_map（由 legal_status 模块综合计算），回退到记录自身字段
        if ip_type == "专利" and status_map:
            status_info = status_map.get(identifier, {})
            legal_status = status_info.get("法律状态", "")
            current_owner = status_info.get("当前权利人", "")
        elif ip_type == "商标" and status_map:
            status_info = status_map.get(identifier, {})
            legal_status = status_info.get("法律状态", "")
            current_owner = status_info.get("当前权利人", "")
        elif ip_type == "软著" and status_map:
            status_info = status_map.get(identifier, {})
            legal_status = status_info.get("法律状态", "")
            current_owner = status_info.get("当前权利人", "")
        else:
            legal_status = record.get("法律状态", "")
            current_owner = ""

        # ---- 根据知识产权类型构建不同的目录结构 ----

        if ip_type == "专利":
            # 专利三级目录结构：权利人 / 法律状态 / 申请号-专利类型-法律状态-当前权利人
            # 第一级：当前权利人（为空则用"未知"）
            owner_folder = current_owner or "未知"
            # 第二级：法律状态（为空则用"未知"）
            status_folder = legal_status or "未知"
            # 第三级子文件夹名：申请号-专利类型-法律状态-当前权利人
            # 优先使用申请号，回退到标识号
            patent_number = record.get("申请号", "") or identifier
            # 从 status_map 获取专利类型（发明/实用新型/外观设计）
            patent_type = ""
            if status_map and identifier in status_map:
                patent_type = status_map[identifier].get("专利类型", "")
            # 拼接第三级目录名
            patent_subfolder_name = f"{patent_number}-{patent_type}-{legal_status}-{current_owner}" if patent_number else "未知"
            # 替换文件系统不允许的非法字符为下划线
            patent_subfolder_name = patent_subfolder_name.replace("<", "_").replace(">", "_").replace(":", "_").replace('"', "_").replace("/", "_").replace("\\", "_").replace("|", "_").replace("?", "_").replace("*", "_")
            # 完整目标路径：archives/专利/权利人/法律状态/申请号-专利类型-法律状态-当前权利人/
            target_dir = os.path.join(config.REPO_DIR, sub_folder, owner_folder, status_folder, patent_subfolder_name)

        elif ip_type == "软著":
            # 软著二级目录结构：权利人 / 标识号-法律状态-当前权利人
            # 第一级：当前权利人（为空则用"未知"），并清理非法字符
            owner_folder = current_owner or "未知"
            owner_folder = owner_folder.replace("<", "_").replace(">", "_").replace(":", "_").replace('"', "_").replace("/", "_").replace("\\", "_").replace("|", "_").replace("?", "_").replace("*", "_")
            # 第二级子文件夹名：标识号-法律状态-当前权利人
            sw_subfolder_name = f"{identifier}-{legal_status}-{current_owner}"
            sw_subfolder_name = sw_subfolder_name.replace("<", "_").replace(">", "_").replace(":", "_").replace('"', "_").replace("/", "_").replace("\\", "_").replace("|", "_").replace("?", "_").replace("*", "_")
            # 完整目标路径：archives/软著/权利人/标识号-法律状态-当前权利人/
            target_dir = os.path.join(config.REPO_DIR, sub_folder, owner_folder, sw_subfolder_name)

        else:
            # 商标单级目录结构：标识号-商标类别-法律状态-当前权利人
            # 商标类别优先从 category_map 取（已预先收集），其次从记录中取
            trademark_category = category_map.get(identifier, "") or record.get("申请类别", "") or record.get("注册类别", "")
            folder_name = f"{identifier}-{trademark_category}-{legal_status}-{current_owner}"
            # 完整目标路径：archives/商标/标识号-商标类别-法律状态-当前权利人/
            target_dir = os.path.join(config.REPO_DIR, sub_folder, folder_name)

        # 确保目标目录存在（不存在则创建）
        os.makedirs(target_dir, exist_ok=True)

        # ---- 计算文件的新旧路径，执行移动 ----

        # 获取记录中的旧相对路径，无路径则跳过
        old_relative_path = record.get("文件路径", "")
        if not old_relative_path:
            continue

        # 拼接旧文件的绝对路径
        old_abs_path = os.path.join(config.REPO_DIR, old_relative_path)
        # 提取文件名，移动时保持文件名不变
        filename = os.path.basename(old_relative_path)

        # 根据知识产权类型构建新的相对路径（与目录结构对应）
        if ip_type == "专利":
            new_relative_path = os.path.join(sub_folder, owner_folder, status_folder, patent_subfolder_name, filename)
        elif ip_type == "软著":
            new_relative_path = os.path.join(sub_folder, owner_folder, sw_subfolder_name, filename)
        else:
            new_relative_path = os.path.join(sub_folder, folder_name, filename)
        # 拼接新文件的绝对路径
        new_abs_path = os.path.join(config.REPO_DIR, new_relative_path)

        # 如果目标位置已存在同名文件，说明文件已在正确位置，跳过移动
        # 但仍需记录路径映射，以防旧路径与新路径不同需要更新CSV
        if os.path.exists(new_abs_path):
            logger.info(f"  文件已在目标位置，跳过: {filename}")
            path_mapping[old_relative_path] = new_relative_path
            continue

        # 源文件不存在则跳过（可能已被移动或删除），不报错
        if not os.path.exists(old_abs_path):
            logger.warning(f"  源文件不存在，跳过: {old_abs_path}")
            continue

        # 执行文件移动，并记录路径映射
        try:
            shutil.move(old_abs_path, new_abs_path)
            logger.info(f"  移动: {old_relative_path} → {new_relative_path}")
            path_mapping[old_relative_path] = new_relative_path
        except Exception as e:
            logger.error(f"  移动失败: {old_abs_path} → {new_abs_path}, 错误: {e}")

    # 所有文件移动完成后，批量更新CSV中的文件路径字段
    if path_mapping:
        csv_manager.update_file_paths(csv_path, path_mapping)
        logger.info(f"已更新 {len(path_mapping)} 条文件路径记录")


def _cleanup_empty_folders():
    """清理archives子目录下的空文件夹。

    文件移动后，原文件夹可能变为空目录。此函数递归遍历archives的三个子目录
    （专利/商标/软著），从最深层开始向上删除空文件夹。
    """
    # 遍历三个子目录（专利/商标/软著）
    for sub in config.SUB_FOLDERS:
        sub_dir = os.path.join(config.REPO_DIR, sub)
        if not os.path.exists(sub_dir):
            continue
        # topdown=False 表示自底向上遍历，确保先处理深层目录再处理浅层
        # 这样当子目录被删除后，父目录如果也为空也能被正确删除
        for root, dirs, files in os.walk(sub_dir, topdown=False):
            for d in dirs:
                dir_path = os.path.join(root, d)
                try:
                    # 检查目录是否为空，为空则删除
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        logger.info(f"已清理空文件夹: {dir_path}")
                except Exception:
                    pass


def run():
    """脚本2的主执行函数。

    执行流程：
      1. 分别同步专利、商标、软著三类 CSV 对应的文件路径
      2. 清理移动后产生的空文件夹
    """
    logger.info("=" * 60)
    logger.info("脚本2：文件路径同步开始")
    logger.info("=" * 60)

    # 依次处理三种知识产权类型的文件同步
    _sync_csv(config.PATENT_CSV, "专利")
    _sync_csv(config.TRADEMARK_CSV, "商标")
    _sync_csv(config.SOFTWARE_CSV, "软著")

    # 文件移动完成后，清理遗留的空文件夹
    _cleanup_empty_folders()

    logger.info("脚本2：文件路径同步完成")


if __name__ == "__main__":
    from datetime import datetime as _dt
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                os.path.join(config.LOG_DIR, f"{_dt.now().strftime('%Y%m%d_%H%M%S')}system.log"), encoding="utf-8"
            ),
        ],
    )
    run()
