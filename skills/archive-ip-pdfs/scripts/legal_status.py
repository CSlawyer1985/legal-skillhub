"""
法律状态判定模块 (legal_status.py)
==================================

本模块负责根据知识产权官文的通知书名称和已有记录，判定并更新各条记录的
法律状态、当前权利人及状态变更历史。

核心概念：
  - 法律状态：知识产权在生命周期中所处的阶段（如"受理"、"实审"、"授权"等）
  - 标识号：将同一知识产权的多份官文关联在一起的唯一标识符
  - 状态变更历史：以"→"连接的状态变更轨迹，如"受理→实审→授权"

判定策略概述：
  1. 专利：优先检查是否持有"专利证书"（授权/失效），否则按最新通知书名称映射
  2. 商标：优先检查是否持有"商标注册证"（已注册），再按通知书名称映射
  3. 软著：优先检查是否持有"软著证书"（登记下证），再按通知书名称映射

映射表说明：
  - PATENT_LEGAL_STATUS_MAP / TRADEMARK_LEGAL_STATUS_MAP / SOFTWARE_LEGAL_STATUS_MAP
    定义了通知书名称到法律状态的映射关系
  - 映射值为 None 表示该通知书不直接决定法律状态（如"手续合格通知书"仅表示
    手续合规，不改变当前状态）
  - PATENT_NOTIFICATION_REGEX_MAP 用于匹配"第N次审查意见通知书"等动态名称

性能考虑：
  - update_legal_status_in_csv 每次执行会读取并全量覆写 CSV，适用于中小规模数据
  - 排序操作按"处理时间+序号"降序，确保取到最新的有效状态
"""

import os
import re
import logging
from datetime import datetime

from . import config
from .csv_manager import read_csv, write_csv

logger = logging.getLogger(__name__)

# ==================== 专利法律状态映射表 ====================
# 键为通知书名称，值为对应的法律状态
# 值为 None 表示该通知书不直接决定法律状态（需结合其他记录综合判断）
PATENT_LEGAL_STATUS_MAP = {
    "专利申请受理通知书": "受理",
    "发明专利申请公布通知书": "受理",
    "发明专利申请初步审查合格通知书": "受理",
    "收费减缴审批通知书": None,

    "发明专利申请进入实质审查阶段通知书": "实审",
    "第一次审查意见通知书": "实审",
    "第二次审查意见通知书": "实审",
    "第三次审查意见通知书": "实审",
    "第四次审查意见通知书": "实审",
    "补正通知书": "实审",

    "驳回决定": "驳回",

    "复审决定书": "复审",
    "复审通知书": "复审",
    "复审请求受理通知书": "复审",

    "授予实用新型专利权通知书": "办登",
    "授予发明专利权通知书": "办登",
    "授予外观设计专利权通知书": "办登",
    "办理登记手续通知书": "办登",

    "专利权终止通知书": "失效",

    "视为撤回通知书": "撤回",
    "视为放弃取得专利权通知书": "撤回",

    # 手续合格通知书仅表示某项手续合规，本身不改变法律状态
    "手续合格通知书": None,
    # 撤回专利申请的手续合格通知书是特例，明确映射为"撤回"
    "撤回专利申请手续合格通知书": "撤回",
    # 恢复权利请求审批通知书仅表示恢复请求被审批，不直接改变当前状态
    "恢复权利请求审批通知书": None,
}

# 专利法律状态优先级表：数值越大优先级越高
# 用于在多条记录同时存在时，选择最高优先级的状态作为当前法律状态
# 例如：同时有"受理"和"实审"的记录时，取优先级更高的"实审"
PATENT_STATUS_PRIORITY = {
    "受理": 1,
    "实审": 2,
    "驳回": 3,
    "复审": 4,
    "办登": 5,
    "授权": 6,
    "失效": 7,
    "撤回": 8,
}

# 专利通知书名称正则匹配规则
# 用于匹配"第N次审查意见通知书"等无法穷举的动态名称
PATENT_NOTIFICATION_REGEX_MAP = [
    (r"第.+次审查意见通知书", "实审"),
]

# ==================== 商标法律状态映射表 ====================
# 商标的状态流转较专利简单，映射值同样为 None 表示不直接决定法律状态
# 例如"商标变更核准证明"仅表示变更手续完成，不改变商标的注册/申请状态
TRADEMARK_LEGAL_STATUS_MAP = {
    "商标注册证": "已注册",
    "商标注册申请初步审定公告通知书": "初审公告",
    "商标注册申请缴费通知书": "受理",
    "商标注册申请受理通知书": "受理",
    "商标驳回通知书": "驳回",
    "商标部分驳回通知书": "部分驳回",
    "商标注册申请书": "申请中",
    "商标评审申请受理通知书": None,
    "商标驳回复审决定书": "复审决定",
    "商标评审案件补正通知书": None,
    "商标续展注册申请受理通知书": "续展",
    "商标续展注册证明": "续展",
    # 变更/转让/许可等手续类文书，不改变商标本身的法律状态
    "商标变更核准证明": None,
    "商标转让核准证明": None,
    "提供注册商标使用证据通知书": None,
    "注册商标续展申请受理通知书": "续展",
    "商标使用许可合同备案通知书": None,
    "商标变更申请补正通知书": None,
}

# ==================== 软著法律状态映射表 ====================
# 软著的状态最简单，只有"登记下证"和"受理申请"两种
SOFTWARE_LEGAL_STATUS_MAP = {
    "软著证书": "登记下证",
    "软著受理通知书": "受理申请",
}


def determine_patent_type(patent_number):
    """根据专利号判断专利类型（发明/实用新型/外观设计）。

    中国专利号的第5位数字标识专利类型：
      - 1: 发明专利
      - 2: 实用新型专利
      - 3: 外观设计专利

    Args:
        patent_number (str): 专利号（如"CN202010123456.1"），
                             支持带或不带"CN"前缀

    Returns:
        str: 专利类型名称（"发明"/"实用新型"/"外观设计"），
             无法判断时返回空字符串
    """
    if not patent_number:
        return ""
    # 去掉"CN"前缀，取第5位数字判断类型
    num = patent_number.replace("CN", "").strip()
    if len(num) >= 5:
        fifth_digit = num[4]
        type_map = {"1": "发明", "2": "实用新型", "3": "外观设计"}
        return type_map.get(fifth_digit, "")
    return ""


def _resolve_notification_status(notification_name):
    """根据通知书名称解析法律状态，支持复合名称（&分隔）。

    对于包含多个通知书名称的复合名称（如"驳回决定&第一次审查意见通知书"），
    按优先级选择最高优先级的法律状态。

    Args:
        notification_name (str): 通知书名称，可能包含"&"分隔的复合名称

    Returns:
        str | None: 法律状态字符串，若该通知书不参与状态判定则返回 None
    """
    # 将复合名称按"&"拆分为多个子名称
    parts = notification_name.split("&")
    best_status = None
    best_priority = 0

    for part in parts:
        part = part.strip()
        # 先在静态映射表中查找
        status = PATENT_LEGAL_STATUS_MAP.get(part)
        if status is None:
            # 静态映射表中未找到，尝试正则匹配（如"第5次审查意见通知书"）
            for pattern, matched_status in PATENT_NOTIFICATION_REGEX_MAP:
                if re.match(pattern, part):
                    status = matched_status
                    break
        # 在复合名称中，选择优先级最高的状态
        if status is not None:
            priority = PATENT_STATUS_PRIORITY.get(status, 0)
            if priority > best_priority:
                best_status = status
                best_priority = priority

    return best_status


def _get_register_status_from_records(group_records):
    """从同一标识号的记录中获取登记簿状态。

    遍历所有专利登记簿副本记录，返回第一个非空的登记簿状态值。

    Args:
        group_records (list[dict]): 同一标识号下的所有记录

    Returns:
        str: 登记簿状态（如"授权"、"失效"），无登记簿副本或状态为空时返回空字符串
    """
    for r in group_records:
        # 专利登记簿副本是国知局出具的官方登记状态凭证，其"登记簿状态"字段可信度最高
        if r.get("子类型") == "专利登记簿副本":
            register_status = r.get("登记簿状态", "")
            if register_status:
                return register_status
    return ""


def _has_only_procedure_qualified(group_records):
    """判断一组专利记录中是否只有手续合格通知书决定法律状态。

    当所有非登记簿副本记录的通知书名称均映射为 None（即不直接决定法律状态），
    且其中包含手续合格通知书时，返回 True。

    Args:
        group_records (list[dict]): 同一标识号下的所有记录

    Returns:
        bool: 是否只有手续合格通知书（无其他能决定法律状态的文件）
    """
    has_procedure = False
    for r in group_records:
        # 跳过专利登记簿副本，它不参与此判断
        if r.get("子类型") == "专利登记簿副本":
            continue
        notification = r.get("通知书名称", "")
        status = _resolve_notification_status(notification)
        # 如果存在任何能直接决定法律状态的通知书，则返回 False
        if status is not None:
            return False
        # 记录是否存在手续合格通知书
        if notification == "手续合格通知书":
            has_procedure = True
    # 只有手续合格通知书，无其他能决定状态的文件
    return has_procedure


def _parse_chinese_date(date_str):
    """将中文格式的日期字符串解析为 datetime 对象。

    支持的格式："YYYY年MM月DD日"，其中年月日之间允许有空格。

    Args:
        date_str (str): 中文日期字符串，如"2023年12月15日"

    Returns:
        datetime | None: 解析成功返回 datetime 对象；解析失败或输入为空返回 None
    """
    if not date_str:
        return None
    date_str = date_str.strip()
    # 匹配"YYYY年MM月DD日"格式，允许年月日前后有空格
    match = re.match(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", date_str)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def _parse_dispatch_date_from_number(dispatch_number):
    """从发文序号中解析出发文日期。

    发文序号的前8位为日期编码（YYYYMMDD），如 2023121500001234
    对应 2023年12月15日。

    Args:
        dispatch_number (str): 16位发文序号

    Returns:
        datetime | None: 解析成功返回 datetime 对象；
                         序号不足8位或日期无效时返回 None
    """
    if not dispatch_number or len(dispatch_number) < 8:
        return None
    try:
        # 前4位为年份，5-6位为月份，7-8位为日期
        year = int(dispatch_number[:4])
        month = int(dispatch_number[4:6])
        day = int(dispatch_number[6:8])
        return datetime(year, month, day)
    except ValueError:
        return None


def determine_legal_status(main_type, sub_type, notification_name, existing_records):
    """根据知识产权类型和已有记录，判定当前法律状态。

    这是法律状态判定的入口函数，根据主类型分发到对应的判定逻辑。

    Args:
        main_type (str): 主类型，取值为"专利文件"、"商标文件"、"软著文件"
        sub_type (str): 子类型，如"专利通知书"、"商标注册证"等
        notification_name (str): 通知书名称
        existing_records (list[dict]): 同一标识号下的所有已有记录

    Returns:
        str: 判定出的法律状态，如"受理"、"实审"、"授权"等；
             无法判定时返回"未知"
    """
    # 根据主类型分发到各自的判定函数
    if main_type == "专利文件":
        return _determine_patent_legal_status(sub_type, notification_name, existing_records)
    elif main_type == "商标文件":
        return _determine_trademark_legal_status(sub_type, notification_name, existing_records)
    elif main_type == "软著文件":
        return _determine_software_legal_status(sub_type, notification_name, existing_records)
    return "未知"


def _determine_patent_legal_status(sub_type, notification_name, existing_records):
    # ===== 第一优先级：专利证书 =====
    # 专利证书是授权的最终凭证，存在证书即表示至少已授权
    has_certificate = any(r.get("子类型") == "专利证书" for r in existing_records)
    # 专利权终止通知书表示授权后专利权已失效
    has_termination = any(
        r.get("通知书名称", "") == "专利权终止通知书" for r in existing_records
    )

    # 有证书且无终止 → 当前状态为"授权"
    if has_certificate and not has_termination:
        return "授权"
    # 有证书且有终止 → 当前状态为"失效"（授权后被终止）
    if has_certificate and has_termination:
        return "失效"

    # ===== 第二优先级：通知书名称映射 =====
    # 按处理时间+序号降序排列，确保优先处理最新记录
    sorted_records = sorted(existing_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0"))), reverse=True)

    best_status = None
    best_priority = 0

    for r in sorted_records:
        # 专利登记簿副本不参与通知书名称映射，它有独立的判定逻辑（见下方）
        if r.get("子类型") == "专利登记簿副本":
            continue
        notification = r.get("通知书名称", "")
        status = _resolve_notification_status(notification)
        # 在所有能决定法律状态的通知书中，选择优先级最高的状态
        if status is not None:
            priority = PATENT_STATUS_PRIORITY.get(status, 0)
            if priority > best_priority:
                best_status = status
                best_priority = priority

    if best_status:
        return best_status

    # ===== 第三优先级：专利登记簿副本 =====
    # 登记簿副本是国知局出具的官方状态凭证，其"登记簿状态"字段可信度高
    # 但不改变已有证书的判定结果（证书优先级更高）
    register_status = _get_register_status_from_records(existing_records)
    if register_status:
        return register_status

    # ===== 第四优先级：仅有手续合格通知书 =====
    # 如果只有手续合格通知书（不直接决定状态），则默认为"受理"
    if _has_only_procedure_qualified(existing_records):
        return "受理"

    return "未知"


def _safe_int(val):
    """安全地将值转换为整数，失败时返回 0。

    用于排序时将序号字段转为可比较的整数值。

    Args:
        val: 待转换的值

    Returns:
        int: 转换后的整数值，或 0
    """
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _determine_trademark_legal_status(sub_type, notification_name, existing_records):
    """判定商标的法律状态。

    判定优先级：
      1. 若存在"商标注册证" → "已注册"
      2. 若存在"初审公告通知书" → "初审公告"
      3. 按处理时间降序遍历，取第一条有效通知书的状态映射值

    Args:
        sub_type (str): 子类型
        notification_name (str): 通知书名称
        existing_records (list[dict]): 同一标识号下的所有已有记录

    Returns:
        str: 法律状态
    """
    # 第一优先级：商标注册证是注册成功的最终凭证
    for r in existing_records:
        if r.get("子类型") == "商标注册证":
            return "已注册"

    # 第二优先级：初审公告表示商标已通过初步审查，进入公告期
    for r in existing_records:
        n = r.get("通知书名称", "")
        if n == "商标注册申请初步审定公告通知书":
            return "初审公告"

    # 第三优先级：按时间降序取最新一条有效映射状态
    sorted_records = sorted(existing_records, key=lambda r: r.get("处理时间", ""), reverse=True)
    for r in sorted_records:
        n = r.get("通知书名称", "")
        status = TRADEMARK_LEGAL_STATUS_MAP.get(n)
        if status is not None:
            return status

    return "未知"


def _determine_software_legal_status(sub_type, notification_name, existing_records):
    """判定软著的法律状态。

    判定优先级：
      1. 若存在"软著证书" → "登记下证"
      2. 按处理时间降序遍历，取第一条有效通知书的状态映射值

    Args:
        sub_type (str): 子类型
        notification_name (str): 通知书名称
        existing_records (list[dict]): 同一标识号下的所有已有记录

    Returns:
        str: 法律状态
    """
    # 第一优先级：软著证书是登记下证的最终凭证
    for r in existing_records:
        if r.get("子类型") == "软著证书":
            return "登记下证"

    # 第二优先级：按时间降序取最新一条有效映射状态
    sorted_records = sorted(existing_records, key=lambda r: r.get("处理时间", ""), reverse=True)
    for r in sorted_records:
        n = r.get("通知书名称", "")
        status = SOFTWARE_LEGAL_STATUS_MAP.get(n)
        if status is not None:
            return status

    return "未知"


def get_status_from_notification(ip_type, record, group_records):
    """根据单条记录的通知书名称获取其对应的法律状态。

    与 determine_legal_status 不同，此函数仅根据单条记录判定状态，
    不考虑同一组内的优先级逻辑。主要用于构建状态变更历史。

    Args:
        ip_type (str): 知识产权类型，取值为"专利"、"商标"、"软著"
        record (dict): 单条 CSV 记录
        group_records (list[dict]): 同一标识号下的所有记录（用于专利证书的终止判断）

    Returns:
        str | None: 法律状态字符串，若该记录不参与状态判定则返回 None
    """
    notification_name = record.get("通知书名称", "")
    sub_type = record.get("子类型", "")

    if ip_type == "专利":
        # 专利证书：需检查是否有终止通知书来决定是"授权"还是"失效"
        if sub_type == "专利证书":
            has_termination = any(
                r.get("通知书名称", "") == "专利权终止通知书" for r in group_records
            )
            return "失效" if has_termination else "授权"
        # 专利登记簿副本：不参与状态变更历史的构建，返回 None
        if sub_type == "专利登记簿副本":
            return None
        # 其他专利通知书：通过映射表解析状态
        return _resolve_notification_status(notification_name)
    elif ip_type == "商标":
        # 商标：直接查映射表
        status = TRADEMARK_LEGAL_STATUS_MAP.get(notification_name)
        return status
    elif ip_type == "软著":
        # 软著：直接查映射表
        status = SOFTWARE_LEGAL_STATUS_MAP.get(notification_name)
        return status
    return None


def get_latest_owner(sorted_records, ip_type):
    """从按时间降序排列的记录中获取最新的权利人。

    不同知识产权类型使用不同的字段名和排序策略：
      - 专利: "专利权人"，按"发文日期"降序排列取最新发文的专利权人
      - 商标: "申请人" 或 "当前权利人"
      - 软著: "申请人" 或 "著作权人" 或 "当前权利人"

    Args:
        sorted_records (list[dict]): 按处理时间降序排列的记录列表
        ip_type (str): 知识产权类型，取值为"专利"、"商标"、"软著"

    Returns:
        str: 最新的权利人名称，若均无则返回空字符串
    """
    if ip_type == "专利":
        def _patent_dispatch_sort_key(r):
            dispatch_date = _parse_chinese_date(r.get("发文日期", ""))
            if dispatch_date:
                return (1, dispatch_date)
            return (0, r.get("处理时间", ""))

        patent_sorted = sorted(sorted_records, key=_patent_dispatch_sort_key, reverse=True)
        for r in patent_sorted:
            owner = r.get("专利权人", "")
            if owner:
                return owner
        return ""

    for r in sorted_records:
        if ip_type == "商标":
            owner = r.get("申请人", "") or r.get("注册人", "") or r.get("当前权利人", "")
        elif ip_type == "软著":
            owner = r.get("申请人", "") or r.get("著作权人", "") or r.get("当前权利人", "")
        else:
            owner = ""
        if owner:
            return owner
    return ""


def group_by_identifier(records, ip_type):
    # 使用字典按标识号分组，键为标识号，值为该标识号下的所有记录列表
    groups = {}
    for r in records:
        # 为每条记录计算标识号（不同IP类型使用不同字段）
        identifier = _compute_identifier(r, ip_type, records)
        if identifier:
            if identifier not in groups:
                groups[identifier] = []
            groups[identifier].append(r)
    return groups


def _compute_identifier(record, ip_type, all_records=None):
    """为单条记录计算标识号。

    标识号用于将同一知识产权的多份官文关联在一起。
    对于软著证书，会尝试通过"软件名称"在全部记录中查找对应的受理号，
    以确保证书与受理通知书使用相同的标识号。

    Args:
        record (dict): 单条 CSV 记录
        ip_type (str): 知识产权类型
        all_records (list[dict] | None): 全部记录，用于软著证书的关联查找

    Returns:
        str: 计算出的标识号
    """
    if ip_type == "专利":
        # 专利统一使用"申请号"作为标识号
        # 同一专利的所有官文（受理通知书、审查意见、证书等）共享同一申请号
        return record.get("申请号", "")
    elif ip_type == "商标":
        # 商标优先使用"申请号"，若无则使用"注册号"
        # 注册号在商标注册成功后才有，申请号在申请阶段即有
        return record.get("申请号", "") or record.get("注册号", "")
    elif ip_type == "软著":
        sub_type = record.get("子类型", "")
        if sub_type == "软著证书":
            # 软著证书没有"受理号"字段，需要通过"软件名称"关联到受理通知书
            # 在全部记录中查找软件名称相同的受理通知书，取其受理号作为标识号
            # 这样可以确保证书和受理通知书归入同一组
            software_name = record.get("软件名称", "")
            if all_records and software_name:
                for r in all_records:
                    if r.get("子类型") == "软著受理通知书" and r.get("软件名称", "").strip() == software_name.strip():
                        return r.get("受理号", "")
            # 若无法通过软件名称关联，则使用登记号作为标识号
            return record.get("登记号", "")
        else:
            # 软著受理通知书等：优先使用"受理号"，若无则使用"登记号"
            return record.get("受理号", "") or record.get("登记号", "")
    return ""


def update_all_legal_status():
    # 仅更新商标和软著的CSV；专利的更新由 compute_patent_report_status 单独处理
    update_legal_status_in_csv(config.TRADEMARK_CSV, "商标")
    update_legal_status_in_csv(config.SOFTWARE_CSV, "软著")


def update_legal_status_in_csv(csv_path, ip_type):
    """更新指定 CSV 文件中所有记录的法律状态、当前权利人和状态变更历史。

    处理流程：
      1. 读取 CSV 全部记录
      2. 为每条记录计算标识号
      3. 按标识号分组
      4. 对每组记录判定法律状态、计算状态变更历史
      5. 对专利额外处理：判定专利类型、专利权人变更记录、当前权利人
      6. 全量覆写 CSV 文件

    Args:
        csv_path (str): CSV 文件路径
        ip_type (str): 知识产权类型（"专利"/"商标"/"软著"）

    Note:
        - 专利的法律状态判定逻辑最为复杂，需考虑专利证书、终止通知书、
          手续合格通知书等多种特殊情况
        - 状态变更历史按时间升序排列，连续相同状态会自动去重
        - 专利的当前权利人可能因"手续合格通知书"中的专利权人变更而更新
    """
    if not os.path.exists(csv_path):
        return

    # 步骤1：读取CSV全部记录
    records = read_csv(csv_path)
    if not records:
        return

    # 步骤2：为每条记录计算标识号并写入"标识号"字段
    for record in records:
        identifier = _compute_identifier(record, ip_type, records)
        record["标识号"] = identifier

    # 步骤3：按标识号分组
    groups = group_by_identifier(records, ip_type)

    # 步骤4：对每组记录进行状态判定
    for identifier, group_records in groups.items():
        # 按处理时间+序号降序排列，便于取最新记录
        sorted_records = sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0"))), reverse=True)

        # ===== 法律状态判定 =====
        if ip_type == "专利":
            # 专利状态判定优先级：
            # 1. 有专利证书且无终止 → "授权"
            # 2. 有专利证书且有终止 → "失效"
            # 3. 按通知书名称映射取最高优先级状态
            # 4. 登记簿副本中的状态
            # 5. 仅有手续合格通知书 → "受理"
            # 6. 以上均不满足 → "未知"
            has_certificate = any(r.get("子类型") == "专利证书" for r in group_records)
            has_termination = any(
                r.get("通知书名称", "") == "专利权终止通知书" for r in group_records
            )
            if has_certificate and not has_termination:
                legal_status = "授权"
            elif has_certificate and has_termination:
                legal_status = "失效"
            else:
                # 无证书时，从通知书中按优先级选择最高状态
                legal_status = None
                best_priority = 0
                for r in sorted_records:
                    # 跳过登记簿副本，它有独立的判定逻辑
                    if r.get("子类型") == "专利登记簿副本":
                        continue
                    notification = r.get("通知书名称", "")
                    status = _resolve_notification_status(notification)
                    if status is not None:
                        priority = PATENT_STATUS_PRIORITY.get(status, 0)
                        if priority > best_priority:
                            legal_status = status
                            best_priority = priority
                # 通知书映射无法确定状态时，依次尝试登记簿副本和手续合格通知书
                if legal_status is None:
                    register_status = _get_register_status_from_records(group_records)
                    if register_status:
                        legal_status = register_status
                    elif _has_only_procedure_qualified(group_records):
                        legal_status = "受理"
                    else:
                        legal_status = "未知"
        elif ip_type == "商标":
            legal_status = _determine_trademark_legal_status(
                None, None, group_records
            )
        elif ip_type == "软著":
            legal_status = _determine_software_legal_status(
                None, None, group_records
            )
        else:
            legal_status = "未知"

        # ===== 状态变更历史计算 =====
        # 按时间升序遍历所有记录，构建状态变更轨迹
        # 连续相同状态会自动去重（如"受理→受理"会合并为"受理"）
        status_history_parts = []
        for r in sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0")))):
            single_status = get_status_from_notification(ip_type, r, group_records)
            if single_status is not None:
                # 去重：仅当状态与上一个不同时才追加
                if not status_history_parts or status_history_parts[-1] != single_status:
                    status_history_parts.append(single_status)
        # 若无任何有效状态记录，则使用当前法律状态作为历史
        status_history = "→".join(status_history_parts) if status_history_parts else legal_status

        # 将判定结果写入组内每条记录
        for record in group_records:
            record["法律状态"] = legal_status
            record["状态变更历史"] = status_history

        # ===== 当前权利人计算 =====
        current_owner = get_latest_owner(sorted_records, ip_type)

        # ===== 专利特有处理：专利类型 + 专利权人变更记录 =====
        if ip_type == "专利":
            patent_number = identifier
            patent_type = determine_patent_type(patent_number)

            for record in group_records:
                record["当前权利人"] = current_owner
                record["专利类型"] = patent_type
        else:
            # 商标和软著：直接写入当前权利人
            for record in group_records:
                record["当前权利人"] = current_owner

    # 步骤5：根据IP类型选择对应的列定义，全量覆写CSV
    if ip_type == "专利":
        columns = config.PATENT_CSV_COLUMNS
    elif ip_type == "商标":
        columns = config.TRADEMARK_CSV_COLUMNS
    elif ip_type == "软著":
        columns = config.SOFTWARE_CSV_COLUMNS
    else:
        columns = None
    write_csv(csv_path, records, columns)
    logger.info(f"已更新 {csv_path} 的法律状态（共 {len(records)} 条记录）")


def compute_patent_report_status():
    # 读取专利CSV数据
    if not os.path.exists(config.PATENT_CSV):
        return {}

    records = read_csv(config.PATENT_CSV)
    if not records:
        return {}

    # 为每条记录计算标识号
    for record in records:
        identifier = _compute_identifier(record, "专利", records)
        record["标识号"] = identifier

    # 按标识号分组
    groups = group_by_identifier(records, "专利")

    result = {}

    for identifier, group_records in groups.items():
        # 按处理时间+序号降序排列
        sorted_records = sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0"))), reverse=True)

        # ===== 专利法律状态综合判定（与 update_legal_status_in_csv 逻辑一致） =====
        # 优先级：专利证书 > 通知书映射 > 登记簿副本 > 手续合格通知书 > 未知
        has_certificate = any(r.get("子类型") == "专利证书" for r in group_records)
        has_termination = any(
            r.get("通知书名称", "") == "专利权终止通知书" for r in group_records
        )
        if has_certificate and not has_termination:
            legal_status = "授权"
        elif has_certificate and has_termination:
            legal_status = "失效"
        else:
            # 无证书时，从通知书中按优先级选择最高状态
            legal_status = None
            best_priority = 0
            for r in sorted_records:
                if r.get("子类型") == "专利登记簿副本":
                    continue
                notification = r.get("通知书名称", "")
                status = _resolve_notification_status(notification)
                if status is not None:
                    priority = PATENT_STATUS_PRIORITY.get(status, 0)
                    if priority > best_priority:
                        legal_status = status
                        best_priority = priority
            # 依次尝试登记簿副本和手续合格通知书
            if legal_status is None:
                register_status = _get_register_status_from_records(group_records)
                if register_status:
                    legal_status = register_status
                elif _has_only_procedure_qualified(group_records):
                    legal_status = "受理"
                else:
                    legal_status = "未知"

        # ===== 状态变更历史计算 =====
        # 按时间升序遍历，构建状态变更轨迹，连续相同状态去重
        status_history_parts = []
        for r in sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0")))):
            single_status = get_status_from_notification("专利", r, group_records)
            if single_status is not None:
                if not status_history_parts or status_history_parts[-1] != single_status:
                    status_history_parts.append(single_status)
        status_history = "→".join(status_history_parts) if status_history_parts else legal_status

        # ===== 当前权利人计算 =====
        current_owner = get_latest_owner(sorted_records, "专利")

        # ===== 专利类型判定 =====
        patent_type = determine_patent_type(identifier)

        # ===== 专利权人变更记录计算 =====
        owner_change_records = []

        for r in sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0")))):
            notification = r.get("通知书名称", "")
            if notification == "手续合格通知书":
                owner = r.get("专利权人", "")
                if owner:
                    owner_change_records.append(owner)

        owner_change_str = "→".join(owner_change_records) if owner_change_records else ""

        # 汇总该标识号下的所有判定结果
        result[identifier] = {
            "法律状态": legal_status,
            "当前权利人": current_owner,
            "状态变更历史": status_history,
            "专利类型": patent_type,
            "专利权人变更记录": owner_change_str,
        }

    return result


def compute_trademark_report_status():
    # 读取商标CSV数据
    if not os.path.exists(config.TRADEMARK_CSV):
        return {}

    records = read_csv(config.TRADEMARK_CSV)
    if not records:
        return {}

    # 按标识号分组
    groups = group_by_identifier(records, "商标")
    result = {}

    for identifier, group_records in groups.items():
        # 按处理时间+序号降序排列
        sorted_records = sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0"))), reverse=True)

        # ===== 商标法律状态判定 =====
        # 优先级：商标注册证 > 初审公告通知书 > 最新有效通知书映射
        legal_status = _determine_trademark_legal_status(None, None, group_records)

        # ===== 状态变更历史计算 =====
        # 按时间升序遍历，构建状态变更轨迹，连续相同状态去重
        status_history_parts = []
        for r in sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0")))):
            single_status = get_status_from_notification("商标", r, group_records)
            if single_status is not None:
                if not status_history_parts or status_history_parts[-1] != single_status:
                    status_history_parts.append(single_status)
        status_history = "→".join(status_history_parts) if status_history_parts else legal_status

        # ===== 当前权利人计算 =====
        current_owner = get_latest_owner(sorted_records, "商标")

        # 汇总该标识号下的所有判定结果
        result[identifier] = {
            "法律状态": legal_status,
            "当前权利人": current_owner,
            "状态变更历史": status_history,
        }

    return result


def compute_software_report_status():
    # 读取软著CSV数据
    if not os.path.exists(config.SOFTWARE_CSV):
        return {}

    records = read_csv(config.SOFTWARE_CSV)
    if not records:
        return {}

    # 按标识号分组
    groups = group_by_identifier(records, "软著")
    result = {}

    for identifier, group_records in groups.items():
        # 按处理时间+序号降序排列
        sorted_records = sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0"))), reverse=True)

        # ===== 软著法律状态判定 =====
        # 优先级：软著证书 > 最新有效通知书映射
        legal_status = _determine_software_legal_status(None, None, group_records)

        # ===== 状态变更历史计算 =====
        # 按时间升序遍历，构建状态变更轨迹，连续相同状态去重
        status_history_parts = []
        for r in sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0")))):
            single_status = get_status_from_notification("软著", r, group_records)
            if single_status is not None:
                if not status_history_parts or status_history_parts[-1] != single_status:
                    status_history_parts.append(single_status)
        status_history = "→".join(status_history_parts) if status_history_parts else legal_status

        # ===== 当前权利人计算 =====
        current_owner = get_latest_owner(sorted_records, "软著")

        # 汇总该标识号下的所有判定结果
        result[identifier] = {
            "法律状态": legal_status,
            "当前权利人": current_owner,
            "状态变更历史": status_history,
        }

    return result
