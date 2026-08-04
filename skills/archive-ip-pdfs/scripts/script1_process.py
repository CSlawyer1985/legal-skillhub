"""
脚本1：扫描处理模块 (script1_process.py)
=========================================

本脚本是系统的核心处理流程，负责：
  1. 扫描临时存放区（TEMP_DIR）中的所有 PDF 文件
  2. 调用 pdf_parser 解析每个 PDF，提取类型和字段信息
  3. 进行幂等性校验（跳过已处理的重复文件）
  4. 将 PDF 复制到archives目录并重命名
  5. 将解析结果写入对应的 CSV 归档文件
  6. 生成 JSON 格式的处理日志
  7. 触发法律状态批量更新

处理流程详解：
  扫描 PDF → 解析类型 → 幂等性检查 → 生成文件名 → 复制到archives
  → 删除原文件 → 写入 CSV → 记录 JSON 日志 → 更新法律状态

幂等性保证：
  通过 _check_duplicate 函数检查 CSV 中是否已存在相同记录，
  判断依据因子类型而异（如专利按申请号+通知书名称+发文序号判断），
  确保重复运行不会产生重复记录。

文件命名冲突处理：
  当目标路径已存在同名文件时，自动在文件名后追加 _1、_2 等后缀，
  避免覆盖已有文件。

性能考虑：
  - 逐文件处理，单文件异常不影响后续文件
  - 法律状态更新在所有文件处理完成后统一执行，减少 CSV 读写次数
"""

import os
import re
import json
import shutil
import stat
import logging
from datetime import datetime

from . import config
from . import pdf_parser
from . import csv_manager
from .legal_status import PATENT_LEGAL_STATUS_MAP, TRADEMARK_LEGAL_STATUS_MAP, SOFTWARE_LEGAL_STATUS_MAP, determine_patent_type

logger = logging.getLogger(__name__)


def _get_sub_folder(main_type):
    """将主类型映射为archives子文件夹名称。

    Args:
        main_type (str): 主类型，取值为"专利文件"、"商标文件"、"软著文件"

    Returns:
        str | None: 子文件夹名称（"专利"/"商标"/"软著"），无法映射时返回 None
    """
    if main_type == "专利文件":
        return "专利"
    elif main_type == "商标文件":
        return "商标"
    elif main_type == "软著文件":
        return "软著"
    return None


def _get_initial_legal_status(sub_type, notification_name):
    """获取文件首次入库时的初始法律状态。

    此函数仅根据子类型和通知书名称进行简单映射，不考虑同一标识号下的
    其他记录。完整的法律状态判定由 update_all_legal_status 在所有文件
    处理完成后统一执行。

    Args:
        sub_type (str): 子类型，如"专利通知书"、"商标注册证"等
        notification_name (str): 通知书名称

    Returns:
        str: 初始法律状态，如"受理"、"实审"、"授权"等；
             无法判定时返回"未知"；专利登记簿副本返回空字符串
    """
    # 专利证书直接映射为"授权"
    if sub_type == "专利证书":
        return "授权"
    # 专利登记簿副本不设置初始法律状态，由后续批量更新处理
    if sub_type == "专利登记簿副本":
        return ""
    # 专利通知书：先查映射表，再尝试正则匹配
    if sub_type in ("专利通知书",):
        status = PATENT_LEGAL_STATUS_MAP.get(notification_name)
        if status is not None:
            return status
        # 映射表中未找到时，使用正则模式匹配（如"第X次审查意见通知书"→"实审"）
        for pattern, matched_status in [
            (r"第.+次审查意见通知书", "实审"),
        ]:
            if re.match(pattern, notification_name):
                return matched_status
        # 均未匹配则返回空字符串，等待后续批量更新
        return ""
    # 商标类文件：查商标法律状态映射表
    if sub_type in ("商标通知书", "商标注册证", "商标注册申请书", "商标变更证明", "商标续展证明", "商标转让证明"):
        status = TRADEMARK_LEGAL_STATUS_MAP.get(notification_name)
        return status if status is not None else "未知"
    # 软著类文件：查软著法律状态映射表
    if sub_type in ("软著受理通知书", "软著证书"):
        status = SOFTWARE_LEGAL_STATUS_MAP.get(notification_name)
        return status if status is not None else "未知"
    return "未知"


def _check_duplicate(csv_path, sub_type, info):
    """检查 CSV 中是否已存在相同记录（幂等性判断）。

    不同子类型的重复判断依据：
      - 专利通知书: 申请号 + 通知书名称 + 发文序号
      - 专利证书: 申请号 + 子类型
      - 专利登记簿副本: 申请号 + 子类型 + 发文日期
      - 商标通知书: 申请号 + 通知书名称 + 发文编号
      - 商标注册证: 注册号 + 子类型
      - 商标注册申请书: 代理文号 + 子类型
      - 软著受理通知书: 受理号 + 子类型
      - 软著证书: 登记号 + 子类型

    Args:
        csv_path (str): CSV 文件路径
        sub_type (str): 子类型
        info (dict): 解析结果字典

    Returns:
        dict | None: 匹配的已有记录（dict），无匹配时返回 None
    """
    # 读取目标 CSV 中的所有已有记录
    records = csv_manager.read_csv(csv_path)
    for r in records:
        # 专利通知书：三字段联合判断（申请号+通知书名称+发文序号），确保同一通知书不会重复入库
        if sub_type == "专利通知书":
            if (r.get("申请号") == info.get("patent_number", "") and
                r.get("通知书名称") == info.get("patent_notification_name", "") and
                r.get("发文序号") == info.get("dispatch_number", "")):
                return r
        # 专利证书：同一申请号只会有一份证书，按申请号+子类型判断
        elif sub_type == "专利证书":
            if (r.get("申请号") == info.get("patent_number", "") and
                r.get("子类型") == "专利证书"):
                return r
        # 专利登记簿副本：同一申请号可能多次获取，按申请号+子类型+发文日期联合判断
        elif sub_type == "专利登记簿副本":
            cnipa_date = info.get("cnipa_date", "")
            if (r.get("申请号") == info.get("patent_number", "") and
                r.get("子类型") == "专利登记簿副本" and
                r.get("发文日期") == cnipa_date):
                return r
        # 商标通知书：三字段联合判断（申请号+通知书名称+发文编号）
        elif sub_type == "商标通知书":
            dispatch_number = info.get("trademark_dispatch_number", "")
            if (r.get("申请号") == info.get("trademark_application_number", "") and
                r.get("通知书名称") == info.get("trademark_notification_name", "") and
                r.get("发文编号") == dispatch_number):
                return r
        # 商标注册证：按注册号+子类型判断，同一注册号只会有一个注册证
        elif sub_type == "商标注册证":
            if (r.get("注册号") == info.get("registration_number", "") and
                r.get("子类型") == "商标注册证"):
                return r
        # 商标注册申请书：按代理文号+子类型判断
        elif sub_type == "商标注册申请书":
            if (r.get("代理文号") == info.get("agent_number", "") and
                r.get("子类型") == "商标注册申请书"):
                return r
        # 软著受理通知书：按受理号+子类型判断
        elif sub_type == "软著受理通知书":
            if (r.get("受理号") == info.get("acceptance_number", "") and
                r.get("子类型") == "软著受理通知书"):
                return r
        # 软著证书：按登记号+子类型判断
        elif sub_type == "软著证书":
            if (r.get("登记号") == info.get("software_registration_number", "") and
                r.get("子类型") == "软著证书"):
                return r
    return None


def _build_csv_record(result, csv_path, columns):
    """根据解析结果构建 CSV 记录字典。

    将 pdf_parser 返回的解析结果转换为符合 CSV 列定义的记录格式。
    不同主类型的字段映射逻辑不同。

    Args:
        result (dict): pdf_parser.parse_pdf 的返回结果
        csv_path (str): CSV 文件路径（用于获取下一个序号）
        columns (list[str]): CSV 列名列表

    Returns:
        dict: 符合 CSV 列定义的记录字典，键为列名
    """
    sub_type = result["sub_type"]
    info = result["info"]
    main_type = result["main_type"]
    notification_name = result.get("notification_name", "")

    # 记录处理时间，用于"处理时间"字段
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 初始化所有列为空字符串，确保每条记录的字段完整
    record = {col: "" for col in columns}
    # 填充通用字段：子类型、处理时间、原始文件名
    record["子类型"] = sub_type
    record["处理时间"] = now
    record["原始文件名"] = result["original_filename"]
    # 根据列定义选择"当前文件名"或"文件名"字段（不同CSV的列名可能不同）
    if "当前文件名" in columns:
        record["当前文件名"] = result["new_filename"] or ""
    elif "文件名" in columns:
        record["文件名"] = result["new_filename"] or ""

    # 专利文件的法律状态由后续批量更新处理，此处不设置；
    # 非专利文件在此处直接设置初始法律状态
    if main_type != "专利文件":
        initial_status = _get_initial_legal_status(sub_type, notification_name)
        record["法律状态"] = initial_status

    # ---- 专利文件字段映射 ----
    # 将 pdf_parser 解析出的 info 字段逐一映射到 CSV 列名
    if main_type == "专利文件":
        record["申请号"] = info.get("patent_number", "")
        record["通知书名称"] = info.get("patent_notification_name", notification_name)
        record["发文序号"] = info.get("dispatch_number", "")
        record["发文日期"] = result.get("dispatch_date", "")
        record["专利权人"] = info.get("patent_owner", "")
        record["授权公告号"] = info.get("announcement_number", "")
        record["授权公告日"] = info.get("announcement_date", "")
        # 根据申请号格式自动判断专利类型（发明/实用新型/外观设计）
        record["专利类型"] = determine_patent_type(info.get("patent_number", ""))
        record["发明创造名称"] = info.get("invention_name", "")
        record["发明人"] = info.get("inventors", "")
        record["申请日"] = info.get("application_date", "")
        record["受理时申请人"] = info.get("applicant_at_filing", "")
        record["证书号"] = info.get("certificate_number", "")
        record["公开日"] = info.get("publication_date", "")
        record["授权日"] = info.get("grant_date", "")
        record["原专利权人名称"] = info.get("original_patent_owner", "")
        record["现专利权人名称"] = info.get("current_patent_owner_register", "")
        record["著录项目变更生效日"] = info.get("bibliographic_change_date", "")
        record["年费信息"] = info.get("annual_fee_info", "")
        record["登记簿状态"] = info.get("register_status", "")
        # 专利文件的标识号统一使用申请号
        record["标识号"] = info.get("patent_number", "")
    # ---- 商标文件字段映射 ----
    elif main_type == "商标文件":
        record["申请号"] = info.get("trademark_application_number", "")
        record["通知书名称"] = notification_name
        record["发文编号"] = info.get("trademark_dispatch_number", "")
        record["注册号"] = info.get("registration_number", "")
        record["注册日期"] = info.get("registration_date", "")
        record["申请日期"] = info.get("application_date", "")
        record["申请类别"] = info.get("trademark_category", "")
        record["注册类别"] = info.get("registration_category", "")
        record["复审委托代理人"] = info.get("review_agent", "")
        record["代理文号"] = info.get("agent_number", "")
        record["申请人"] = info.get("applicant", "")
        record["注册人"] = info.get("owner", "")
        record["变更申请号"] = info.get("change_application_number", "")
        record["变更事项"] = info.get("change_items", "")
        # 商标文件的标识号优先使用申请号，无申请号时使用注册号
        identifier = info.get("trademark_application_number", "") or info.get("registration_number", "")
        record["标识号"] = identifier
    # ---- 软著文件字段映射 ----
    elif main_type == "软著文件":
        record["受理号"] = info.get("acceptance_number", "")
        record["登记号"] = info.get("software_registration_number", "")
        record["软件名称"] = info.get("software_name", "")
        record["证书号"] = info.get("certificate_number", "")
        record["申请人"] = info.get("applicant", "")
        record["著作权人"] = info.get("owner", "")
        record["软著代理"] = info.get("agent", "")
        record["受理日期"] = info.get("acceptance_date", "")
        record["权利取得方式"] = info.get("right_acquisition_method", "")
        record["证书日期"] = info.get("certificate_date", "")
        # 软著的标识号根据子类型不同：受理通知书用受理号，证书用登记号
        if sub_type == "软著受理通知书":
            record["标识号"] = info.get("acceptance_number", "")
        elif sub_type == "软著证书":
            record["标识号"] = info.get("software_registration_number", "")

    return record


def _build_json_entry(result, record):
    """根据解析结果和 CSV 记录构建 JSON 日志条目。

    JSON 日志用于记录每次处理的详细结果，便于回溯和审计。

    Args:
        result (dict): pdf_parser.parse_pdf 的返回结果
        record (dict): 已构建的 CSV 记录字典

    Returns:
        dict: JSON 日志条目，包含类型、状态、文件名等信息
    """
    sub_type = result["sub_type"]
    info = result["info"]
    main_type = result["main_type"]

    # 主类型到日志中简短类型名的映射
    type_map = {"专利文件": "专利", "商标文件": "商标", "软著文件": "软著", "未知": "未知"}
    # 构建日志条目的基础字段
    entry = {
        "类型": type_map.get(main_type, "未知"),
        "子类型": sub_type,
        "处理状态": "成功",
        "错误信息": "",
    }

    # 根据主类型填充各自的关键标识字段，便于日志检索
    if main_type == "专利文件":
        entry["申请号"] = info.get("patent_number", "")
        entry["通知书名称"] = record.get("通知书名称", "")
        entry["发文序号"] = info.get("dispatch_number", "")
        entry["发文日期"] = result.get("dispatch_date", "")
        entry["专利权人"] = info.get("patent_owner", "")
        entry["授权公告号"] = info.get("announcement_number", "")
    elif main_type == "商标文件":
        entry["申请号"] = info.get("trademark_application_number", "")
        entry["通知书名称"] = result.get("notification_name", "")
    elif main_type == "软著文件":
        entry["受理号"] = info.get("acceptance_number", "")
        entry["登记号"] = info.get("software_registration_number", "")
        entry["软件名称"] = info.get("software_name", "")

    # 从 CSV 记录中回填法律状态和当前权利人（可能已由批量更新修改）
    entry["法律状态"] = record.get("法律状态", "")
    entry["当前权利人"] = record.get("当前权利人", "")
    entry["原始文件名"] = result["original_filename"]
    entry["重命名文件名"] = result["new_filename"] or ""

    return entry


def _copy_to_repo(pdf_path, new_filename, sub_folder):
    """将 PDF 文件复制到archives目录，处理文件名冲突。

    若目标路径已存在同名文件，自动在文件名后追加 _1、_2 等序号。
    使用 shutil.copy2 保留文件的元数据（如修改时间）。

    Args:
        pdf_path (str): 源 PDF 文件的完整路径
        new_filename (str): 目标文件名
        sub_folder (str): archives子文件夹名称（"专利"/"商标"/"软著"）

    Returns:
        tuple[str, str]: (相对路径, 实际文件名)
            - 相对路径: 相对于archives根目录的路径，用于存入 CSV
            - 实际文件名: 可能与 new_filename 不同（冲突时追加了序号）
    """
    # 构建目标目录路径，确保目录存在
    dest_dir = os.path.join(config.REPO_DIR, sub_folder)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, new_filename)

    # 文件名冲突处理：若目标路径已存在同名文件，追加 _1、_2 等序号直到不冲突
    counter = 1
    base_name = os.path.splitext(new_filename)[0]
    ext = os.path.splitext(new_filename)[1]
    while os.path.exists(dest_path):
        new_filename = f"{base_name}_{counter}{ext}"
        dest_path = os.path.join(dest_dir, new_filename)
        counter += 1

    # 使用 copy2 保留文件元数据（修改时间等），然后计算相对路径
    shutil.copy2(pdf_path, dest_path)
    relative_path = os.path.join(sub_folder, new_filename)
    return relative_path, new_filename


def _cleanup_empty_dirs(directory):
    """递归清理指定目录下的所有空文件夹。

    文件移动后原文件夹可能变为空目录，此函数从最深层开始向上
    逐级删除空目录，避免遗留无用的空文件夹。

    Args:
        directory (str): 要清理的根目录路径
    """
    # topdown=False 确保从最深层目录开始向上遍历，这样删除子目录后父目录才可能变为空
    for root, dirs, files in os.walk(directory, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    logger.info(f"已清理空文件夹: {dir_path}")
            except Exception:
                pass


def _force_remove_file(filepath):
    """强制删除文件，即使文件为只读属性。

    在 Windows 系统上，某些 PDF 文件可能被标记为只读，
    直接 os.remove 会失败。此函数先尝试移除只读属性再删除。

    Args:
        filepath (str): 要删除的文件路径

    Returns:
        bool: 删除成功返回 True，失败返回 False
    """
    # 先尝试移除只读属性，确保后续删除操作不会因权限问题失败
    try:
        os.chmod(filepath, stat.S_IWRITE)
    except Exception:
        pass
    try:
        os.remove(filepath)
        return True
    except Exception as e:
        logger.warning(f"  删除文件失败: {e}")
        return False


def _move_to_failed(pdf_path, failed_dir):
    """将处理失败的 PDF 文件移动到未处理目录。

    若目标路径已存在同名文件，自动在文件名后追加序号避免覆盖。
    移动前会尝试移除只读属性，确保在 Windows 上也能成功移动。

    Args:
        pdf_path (str): 源 PDF 文件路径
        failed_dir (str): 未处理文件的目标目录路径
    """
    dest_dir = failed_dir
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(pdf_path)
    dest_path = os.path.join(dest_dir, filename)
    # 处理目标路径同名文件冲突，追加序号避免覆盖
    counter = 1
    base_name = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    while os.path.exists(dest_path):
        dest_path = os.path.join(dest_dir, f"{base_name}_{counter}{ext}")
        counter += 1
    try:
        # 移除只读属性，确保 Windows 环境下可以移动文件
        try:
            os.chmod(pdf_path, stat.S_IWRITE)
        except Exception:
            pass
        shutil.move(pdf_path, dest_path)
        logger.info(f"  已移至未处理目录: {os.path.basename(dest_path)}")
    except Exception as e:
        logger.warning(f"  移至未处理目录失败: {e}")


def run():
    """脚本1的主执行函数：扫描临时目录中的 PDF 文件并归档处理。

    执行流程：
      1. 初始化目录结构和 CSV 文件
      2. 扫描 TEMP_DIR 中的所有 PDF 文件
      3. 逐文件执行：解析→幂等性检查→复制到archives→写入CSV→记录日志
      4. 所有文件处理完成后，触发法律状态批量更新
      5. 回填 JSON 日志中的法律状态和当前权利人信息
      6. 生成 JSON 格式的处理日志
      7. 清理临时目录中的空文件夹

    Note:
        - 单文件异常不会中断整体处理流程
        - 解析失败或无法识别的文件会被移至 FAILED_DIR
        - 重复文件（幂等性判断通过）会被删除原文件但不写入 CSV
    """
    # ==================== 阶段1：初始化 ====================
    logger.info("=" * 60)
    logger.info("脚本1：扫描处理开始")
    logger.info("=" * 60)

    # 确保所有必需的目录存在
    os.makedirs(config.TEMP_DIR, exist_ok=True)
    os.makedirs(config.REPO_DIR, exist_ok=True)
    os.makedirs(config.LOG_DIR, exist_ok=True)
    os.makedirs(config.CSV_DIR, exist_ok=True)
    failed_dir = config.FAILED_DIR
    os.makedirs(failed_dir, exist_ok=True)
    # 创建 archives 下的各子文件夹（专利/商标/软著）
    for sub in config.SUB_FOLDERS:
        os.makedirs(os.path.join(config.REPO_DIR, sub), exist_ok=True)

    # 初始化三个 CSV 文件（若不存在则创建含表头的空文件）
    csv_manager.init_csv(config.PATENT_CSV, config.PATENT_CSV_COLUMNS)
    csv_manager.init_csv(config.TRADEMARK_CSV, config.TRADEMARK_CSV_COLUMNS)
    csv_manager.init_csv(config.SOFTWARE_CSV, config.SOFTWARE_CSV_COLUMNS)

    # ==================== 阶段2：扫描PDF文件 ====================
    # 递归扫描临时存放区中的所有 PDF 文件
    pdf_files = []
    for root, dirs, files in os.walk(config.TEMP_DIR):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append((os.path.join(root, f), f))

    if not pdf_files:
        logger.info("临时存放区中没有PDF文件")
        return

    # 初始化处理统计计数器
    total = len(pdf_files)
    success_count = 0
    fail_count = 0
    json_files = []

    # ==================== 阶段3：逐文件处理 ====================
    for i, (pdf_path, pdf_file) in enumerate(pdf_files):
        logger.info(f"[{i+1}/{total}] 正在处理: {pdf_file}")

        try:
            # 步骤3.1：调用 pdf_parser 解析 PDF，提取类型和字段信息
            result = pdf_parser.parse_pdf(pdf_path)

            # 解析返回错误时，记录失败日志并移至未处理目录
            if result.get("error"):
                logger.warning(f"  跳过: {result['error']}")
                json_files.append({
                    "类型": "未知",
                    "子类型": result.get("sub_type", ""),
                    "原始文件名": pdf_file,
                    "重命名文件名": "",
                    "处理状态": "失败",
                    "错误信息": result["error"],
                })
                fail_count += 1
                _move_to_failed(pdf_path, failed_dir)
                continue

            # 步骤3.2：根据子类型确定对应的 CSV 文件和列定义
            sub_type = result["sub_type"]
            info = result["info"]
            main_type = result["main_type"]

            # 专利类子类型统一写入专利 CSV
            if sub_type == "专利通知书":
                csv_path = config.PATENT_CSV
                columns = config.PATENT_CSV_COLUMNS
            elif sub_type == "专利证书":
                csv_path = config.PATENT_CSV
                columns = config.PATENT_CSV_COLUMNS
            elif sub_type == "专利登记簿副本":
                csv_path = config.PATENT_CSV
                columns = config.PATENT_CSV_COLUMNS
            # 商标类子类型写入商标 CSV
            elif sub_type in ("商标通知书", "商标注册证", "商标注册申请书"):
                csv_path = config.TRADEMARK_CSV
                columns = config.TRADEMARK_CSV_COLUMNS
            # 软著类子类型写入软著 CSV
            elif sub_type in ("软著受理通知书", "软著证书"):
                csv_path = config.SOFTWARE_CSV
                columns = config.SOFTWARE_CSV_COLUMNS
            else:
                # 无法识别的子类型，记录失败并移至未处理目录
                logger.warning(f"  跳过: 无法识别子类型 {sub_type}")
                json_files.append({
                    "类型": "未知",
                    "子类型": str(sub_type),
                    "原始文件名": pdf_file,
                    "重命名文件名": "",
                    "处理状态": "失败",
                    "错误信息": f"无法识别子类型: {sub_type}",
                })
                fail_count += 1
                _move_to_failed(pdf_path, failed_dir)
                continue

            # 步骤3.3：幂等性检查——判断该文件是否已在 CSV 中存在记录
            dup_record = _check_duplicate(csv_path, sub_type, info)
            if dup_record is not None:
                logger.info(f"  跳过: 文件已处理过（幂等性判断）")
                _type_map = {"专利文件": "专利", "商标文件": "商标", "软著文件": "软著", "未知": "未知"}

                # 获取已有记录中的归档文件路径
                old_relative_path = dup_record.get("文件路径", "")
                old_abs_path = os.path.join(config.REPO_DIR, old_relative_path) if old_relative_path else ""

                if old_abs_path and os.path.exists(old_abs_path):
                    # 归档文件仍存在：只需删除当前重复的原文件即可
                    if _force_remove_file(pdf_path):
                        logger.info(f"  已删除重复原文件: {pdf_file}")
                else:
                    # 归档文件缺失：需要重新复制当前文件到归档目录，并更新 CSV 中的路径记录
                    logger.warning(f"  归档文件缺失，重新复制: {old_relative_path or '(无路径记录)'}")
                    new_filename = result.get("new_filename", "")
                    if new_filename:
                        sub_folder = _get_sub_folder(main_type)
                        # 重新复制文件到归档目录（_copy_to_repo 会自动处理文件名冲突）
                        relative_path, actual_filename = _copy_to_repo(pdf_path, new_filename, sub_folder)
                        # 更新 CSV 中已有记录的文件路径和文件名
                        records = csv_manager.read_csv(csv_path)
                        for r in records:
                            if r is dup_record:
                                r["文件路径"] = relative_path
                                filename_col = "当前文件名" if "当前文件名" in columns else "文件名"
                                r[filename_col] = actual_filename
                                break
                        csv_manager.write_csv(csv_path, records, columns)
                        logger.info(f"  已更新归档路径: {relative_path}")
                    # 删除原文件
                    if _force_remove_file(pdf_path):
                        logger.info(f"  已删除原文件: {pdf_file}")

                # 记录跳过日志（不增加 fail_count，属于正常的幂等性跳过）
                json_files.append({
                    "类型": _type_map.get(main_type, "未知"),
                    "子类型": sub_type,
                    "原始文件名": pdf_file,
                    "重命名文件名": "",
                    "处理状态": "跳过",
                    "错误信息": "文件已处理过（幂等性判断）",
                })
                continue

            # 步骤3.4：生成新文件名，若无法生成则跳过
            new_filename = result["new_filename"]
            if not new_filename:
                logger.warning(f"  跳过: 无法生成文件名")
                json_files.append({
                    "类型": "未知",
                    "子类型": sub_type,
                    "原始文件名": pdf_file,
                    "重命名文件名": "",
                    "处理状态": "失败",
                    "错误信息": "无法生成文件名",
                })
                fail_count += 1
                _move_to_failed(pdf_path, failed_dir)
                continue

            # 步骤3.5：复制 PDF 到 archives 目录（自动处理文件名冲突）
            sub_folder = _get_sub_folder(main_type)
            relative_path, actual_filename = _copy_to_repo(pdf_path, new_filename, sub_folder)

            # 步骤3.6：删除临时目录中的原文件
            if _force_remove_file(pdf_path):
                logger.info(f"  已删除原文件: {pdf_file}")

            # 更新 result 中的文件名为实际文件名（可能因冲突而追加了序号）
            result["new_filename"] = actual_filename

            # 步骤3.7：构建 CSV 记录并追加写入
            record = _build_csv_record(result, csv_path, columns)
            record["文件路径"] = relative_path
            csv_manager.append_records(csv_path, [record], columns)

            # 步骤3.8：构建 JSON 日志条目
            json_entry = _build_json_entry(result, record)
            json_files.append(json_entry)

            logger.info(f"  成功 → {relative_path}")
            success_count += 1

        except Exception as e:
            # 捕获未预期的异常，确保单文件错误不会中断整体处理流程
            logger.error(f"  错误: {e}")
            json_files.append({
                "类型": "未知",
                "子类型": "",
                "原始文件名": pdf_file,
                "重命名文件名": "",
                "处理状态": "失败",
                "错误信息": str(e),
            })
            fail_count += 1
            _move_to_failed(pdf_path, failed_dir)

    # ==================== 阶段4：CSV排序 ====================
    # 所有文件处理完成后，按标识号升序重新排列各 CSV 文件，便于查阅
    now = datetime.now()
    log_filename = now.strftime("%Y%m%d_%H%M%S") + ".json"
    log_path = os.path.join(config.LOG_DIR, log_filename)

    # 专利 CSV 按标识号（申请号）升序排序
    patent_records = csv_manager.read_csv(config.PATENT_CSV)
    if patent_records:
        patent_records.sort(key=lambda r: r.get("标识号", ""))
        csv_manager.write_csv(config.PATENT_CSV, patent_records, config.PATENT_CSV_COLUMNS)
        logger.info(f"patent_files_archive.csv 已按标识号升序排序")

    # 商标 CSV 按标识号（申请号或注册号）升序排序
    trademark_records = csv_manager.read_csv(config.TRADEMARK_CSV)
    if trademark_records:
        trademark_records.sort(key=lambda r: r.get("标识号", ""))
        csv_manager.write_csv(config.TRADEMARK_CSV, trademark_records, config.TRADEMARK_CSV_COLUMNS)
        logger.info(f"trademark_files_archive.csv 已按标识号升序排序")

    # 软著 CSV 按标识号（受理号或登记号）升序排序
    software_records = csv_manager.read_csv(config.SOFTWARE_CSV)
    if software_records:
        software_records.sort(key=lambda r: r.get("标识号", ""))
        csv_manager.write_csv(config.SOFTWARE_CSV, software_records, config.SOFTWARE_CSV_COLUMNS)
        logger.info(f"software_files_archive.csv 已按标识号升序排序")

    # ==================== 阶段5：生成JSON日志 ====================
    # 汇总本次处理结果，写入 JSON 日志文件
    log_data = {
        "process_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "total_files": total,
        "success_count": success_count,
        "fail_count": fail_count,
        # 跳过数 = 总数 - 成功数 - 失败数（包含幂等性跳过的文件）
        "skip_count": total - success_count - fail_count,
        "files": json_files,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=4)
    logger.info(f"JSON日志已写入: {log_path}")

    # ==================== 阶段6：清理 ====================
    # 清理临时目录中因文件移动而产生的空文件夹
    _cleanup_empty_dirs(config.TEMP_DIR)

    logger.info(f"脚本1处理完成: 共{total}个文件, 成功: {success_count}, 失败: {fail_count}")


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
