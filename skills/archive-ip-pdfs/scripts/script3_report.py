"""
脚本3：报表生成模块 (script3_report.py)
========================================

本脚本根据归档 CSV 数据生成汇总报表，每个知识产权标识号仅保留一条
最新记录，便于快速了解所有知识产权的当前状态。

报表类型：
  - 专利报表: 汇总每个专利申请号的最新状态
  - 商标报表: 汇总每个商标申请号的最新状态
  - 软著报表: 汇总每个软著标识号的最新状态

报表数据来源：
  从归档 CSV（patent_archive.csv 等）中读取数据，按标识号分组，
  取每组中处理时间最新的记录作为代表，提取关键字段写入报表 CSV。

报表与归档 CSV 的区别：
  - 归档 CSV: 每条记录对应一份官文文件，一个标识号可能有多条记录
  - 报表 CSV: 每条记录对应一个知识产权，仅保留最新状态的关键字段

性能考虑：
  - 报表生成采用全量覆写策略，每次运行重新生成
  - 排序操作按"处理时间+序号"降序，确保取到最新记录
"""

import os
import logging

from . import config
from . import csv_manager
from .legal_status import group_by_identifier, _safe_int, _parse_chinese_date, compute_patent_report_status, compute_trademark_report_status, compute_software_report_status

logger = logging.getLogger(__name__)


def _deduplicate_rows(rows, key_fields):
    """按指定关键字段对报表行进行去重。

    保留每组重复记录中的第一条，后续重复记录被丢弃。
    所有关键字段均为空的记录也会被过滤。

    Args:
        rows (list[dict]): 待去重的报表行列表
        key_fields (list[str]): 用于判断重复的关键字段名列表

    Returns:
        list[dict]: 去重后的报表行列表
    """
    # seen 集合记录已出现过的关键字段组合
    seen = set()
    unique = []
    for row in rows:
        # 将关键字段的值组成元组作为去重键
        key = tuple(row.get(f, "") for f in key_fields)
        # 条件1：该键未出现过；条件2：关键字段不全为空（过滤无效行）
        if key not in seen and any(k for k in key):
            seen.add(key)
            unique.append(row)
    return unique


def _generate_patent_report():
    # 读取专利归档CSV的所有记录
    records = csv_manager.read_csv(config.PATENT_CSV)
    if not records:
        logger.info("专利CSV无记录，跳过报表生成")
        return

    # 获取各标识号的综合法律状态信息（由 legal_status 模块计算）
    patent_status_map = compute_patent_report_status()

    # 按标识号（申请号）分组，每组包含同一专利的多条官文记录
    groups = group_by_identifier(records, "专利")
    report_rows = []

    for identifier, group_records in groups.items():
        # 按处理时间降序+序号降序排列，最新的记录排在最前
        sorted_records = sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0"))), reverse=True)
        # 取排序后的第一条作为"最新记录"，用于获取某些字段的默认值
        latest = sorted_records[0]

        # ---- 计算最新官文名称和最新发文日期 ----
        # 逻辑：遍历该标识号下的所有记录，找到发文日期最晚且有通知书名称的记录
        # 注意：这里按实际发文日期比较，而非处理时间，因为发文日期更准确反映官文的时间顺序
        latest_official_name = ""
        latest_dispatch_date = ""
        latest_dispatch_date_parsed = None
        for r in group_records:
            dispatch_date_str = r.get("发文日期", "")
            notification_name = r.get("通知书名称", "")
            # 只有同时有发文日期和通知书名称的记录才参与比较
            if dispatch_date_str and notification_name:
                parsed_date = _parse_chinese_date(dispatch_date_str)
                # 如果解析成功且比当前记录的日期更晚，则更新
                if parsed_date and (latest_dispatch_date_parsed is None or parsed_date > latest_dispatch_date_parsed):
                    latest_dispatch_date_parsed = parsed_date
                    latest_official_name = notification_name
                    latest_dispatch_date = dispatch_date_str
        # 回退：如果没有找到有效的发文日期+通知书名称组合，则使用最新记录中的值
        if not latest_official_name:
            latest_official_name = latest.get("通知书名称", "")
            latest_dispatch_date = latest.get("发文日期", "")

        # ---- 字段聚合：从多条记录中取非空值 ----
        # 策略：按时间从新到旧遍历，对每个字段只取第一个非空值
        # 因为不同官文可能携带不同字段信息，需要从多条记录中拼凑完整信息
        application_date = ""
        announcement_number = ""
        announcement_date = ""
        invention_name = ""
        inventors = ""
        applicant_at_filing = ""
        patent_type = latest.get("专利类型", "")
        owner_change_record = ""
        certificate_number = ""
        original_patent_owner = ""
        current_patent_owner_reg = ""
        bibliographic_change_date = ""
        annual_fee_info = ""
        patent_owner = ""
        publication_date = ""
        grant_date = ""
        register_status = ""

        for r in sorted_records:
            if r.get("申请日", "") and not application_date:
                application_date = r["申请日"]
            if r.get("授权公告号", "") and not announcement_number:
                announcement_number = r["授权公告号"]
            if r.get("授权公告日", "") and not announcement_date:
                announcement_date = r["授权公告日"]
            if r.get("发明创造名称", "") and not invention_name:
                invention_name = r["发明创造名称"]
            if r.get("发明人", "") and not inventors:
                inventors = r["发明人"]
            if r.get("受理时申请人", "") and not applicant_at_filing:
                applicant_at_filing = r["受理时申请人"]
            if r.get("专利权人变更记录", "") and not owner_change_record:
                owner_change_record = r["专利权人变更记录"]
            if r.get("证书号", "") and not certificate_number:
                certificate_number = r["证书号"]
            if r.get("原专利权人名称", "") and not original_patent_owner:
                original_patent_owner = r["原专利权人名称"]
            if r.get("现专利权人名称", "") and not current_patent_owner_reg:
                current_patent_owner_reg = r["现专利权人名称"]
            if r.get("著录项目变更生效日", "") and not bibliographic_change_date:
                bibliographic_change_date = r["著录项目变更生效日"]
            if r.get("年费信息", "") and not annual_fee_info:
                annual_fee_info = r["年费信息"]
            if r.get("公开日", "") and not publication_date:
                publication_date = r["公开日"]
            if r.get("授权日", "") and not grant_date:
                grant_date = r["授权日"]
            if r.get("登记簿状态", "") and not register_status:
                register_status = r["登记簿状态"]

        def _patent_owner_sort_key(r):
            dispatch_date = _parse_chinese_date(r.get("发文日期", ""))
            if dispatch_date:
                return (1, dispatch_date)
            return (0, r.get("处理时间", ""))

        owner_sorted = sorted(sorted_records, key=_patent_owner_sort_key, reverse=True)
        for r in owner_sorted:
            if r.get("专利权人", "") and not patent_owner:
                patent_owner = r["专利权人"]

        # 从 patent_status_map 获取综合状态信息（法律状态、专利类型、变更记录等）
        status_info = patent_status_map.get(identifier, {})

        # 构建报表行：部分字段优先使用 status_map 中的综合计算结果
        # 例如"专利类型"和"专利权人变更记录"优先取 status_map 的值，更准确
        row = {
            "申请号": latest.get("申请号", ""),
            "专利类型": status_info.get("专利类型", patent_type),
            "发明创造名称": invention_name,
            "专利权人": patent_owner,
            "法律状态": status_info.get("法律状态", ""),
            "最新专利官文名称": latest_official_name,
            "最新发文日期": latest_dispatch_date,
            "申请日": application_date,
            "授权公告日": announcement_date,
            "公开日": publication_date,
            "授权日": grant_date,
            "授权公告号": announcement_number,
            "证书号": certificate_number,
            "发明人": inventors,
            "受理时申请人": applicant_at_filing,
            "原专利权人名称": original_patent_owner,
            "现专利权人名称": current_patent_owner_reg,
            "专利权人变更记录": status_info.get("专利权人变更记录", owner_change_record),
            "著录项目变更生效日": bibliographic_change_date,
            "年费信息": annual_fee_info,
            "登记簿状态": register_status,
        }
        report_rows.append(row)

    # 按申请号去重（保留第一条），确保每个专利只出现一次
    report_rows = _deduplicate_rows(report_rows, ["申请号"])
    # 按申请号升序排序，便于查阅
    report_rows.sort(key=lambda r: r.get("申请号", ""))
    csv_manager.write_csv(config.PATENT_REPORT_CSV, report_rows, config.PATENT_REPORT_COLUMNS)
    logger.info(f"专利报表已生成: {config.PATENT_REPORT_CSV}（{len(report_rows)} 条）")


def _generate_trademark_report():
    # 读取商标归档CSV的所有记录
    records = csv_manager.read_csv(config.TRADEMARK_CSV)
    if not records:
        logger.info("商标CSV无记录，跳过报表生成")
        return

    # 获取各标识号的综合法律状态信息
    trademark_status_map = compute_trademark_report_status()

    # 按标识号分组
    groups = group_by_identifier(records, "商标")
    report_rows = []

    for identifier, group_records in groups.items():
        # 按处理时间+序号降序排列，最新的记录排在最前
        sorted_records = sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0"))), reverse=True)
        latest = sorted_records[0]

        # 商标的最新通知书名称：取排序后第一条有通知书名称的记录
        latest_notification = ""
        for r in sorted_records:
            n = r.get("通知书名称", "")
            if n:
                latest_notification = n
                break

        # 字段聚合：从多条记录中取第一个非空值
        application_date = ""
        trademark_category = ""
        registration_category = ""
        review_agent = ""
        agent_number = ""
        applicant = ""
        owner = ""
        change_application_number = ""
        change_items = ""
        for r in sorted_records:
            if r.get("申请日期", "") and not application_date:
                application_date = r["申请日期"]
            if r.get("申请类别", "") and not trademark_category:
                trademark_category = r["申请类别"]
            if r.get("注册类别", "") and not registration_category:
                registration_category = r["注册类别"]
            if r.get("复审委托代理人", "") and not review_agent:
                review_agent = r["复审委托代理人"]
            if r.get("代理文号", "") and not agent_number:
                agent_number = r["代理文号"]
            if r.get("申请人", "") and not applicant:
                applicant = r["申请人"]
            if r.get("注册人", "") and not owner:
                owner = r["注册人"]
            if r.get("变更申请号", "") and not change_application_number:
                change_application_number = r["变更申请号"]
            if r.get("变更事项", "") and not change_items:
                change_items = r["变更事项"]

        # 从 trademark_status_map 获取综合状态信息
        status_info = trademark_status_map.get(identifier, {})

        row = {
            "标识号": identifier,
            "法律状态": status_info.get("法律状态", ""),
            "当前权利人": status_info.get("当前权利人", ""),
            "申请号": latest.get("申请号", ""),
            "申请日期": application_date,
            "申请类别": trademark_category,
            "注册号": latest.get("注册号", ""),
            "注册日期": latest.get("注册日期", ""),
            "注册类别": registration_category,
            "复审委托代理人": review_agent,
            "代理文号": agent_number,
            "申请人": applicant,
            "注册人": owner,
            "最新通知书名称": latest_notification,
            "变更申请号": change_application_number,
            "变更事项": change_items,
        }
        report_rows.append(row)

    # 按标识号去重，确保每个商标只出现一次
    report_rows = _deduplicate_rows(report_rows, ["标识号"])
    # 按标识号升序排序
    report_rows.sort(key=lambda r: r.get("标识号", ""))
    csv_manager.write_csv(config.TRADEMARK_REPORT_CSV, report_rows, config.TRADEMARK_REPORT_COLUMNS)
    logger.info(f"商标报表已生成: {config.TRADEMARK_REPORT_CSV}（{len(report_rows)} 条）")


def _generate_software_report():
    # 读取软著归档CSV的所有记录
    records = csv_manager.read_csv(config.SOFTWARE_CSV)
    if not records:
        logger.info("软著CSV无记录，跳过报表生成")
        return

    # 获取各标识号的综合法律状态信息
    software_status_map = compute_software_report_status()

    # 按标识号分组
    groups = group_by_identifier(records, "软著")
    report_rows = []

    for identifier, group_records in groups.items():
        # 按处理时间+序号降序排列，最新的记录排在最前
        sorted_records = sorted(group_records, key=lambda r: (r.get("处理时间", ""), _safe_int(r.get("序号", "0"))), reverse=True)
        latest = sorted_records[0]

        # 字段聚合：从多条记录中取第一个非空值
        acceptance_number = ""
        registration_number = ""
        software_name = ""
        certificate_number = ""
        agent = ""
        acceptance_date = ""
        right_acquisition_method = ""
        certificate_date = ""
        applicant = ""
        owner = ""

        for r in sorted_records:
            if r.get("受理号", "") and not acceptance_number:
                acceptance_number = r["受理号"]
            if r.get("登记号", "") and not registration_number:
                registration_number = r["登记号"]
            if r.get("软件名称", "") and not software_name:
                software_name = r["软件名称"]
            if r.get("证书号", "") and not certificate_number:
                certificate_number = r["证书号"]
            if r.get("软著代理", "") and not agent:
                agent = r["软著代理"]
            if r.get("受理日期", "") and not acceptance_date:
                acceptance_date = r["受理日期"]
            if r.get("权利取得方式", "") and not right_acquisition_method:
                right_acquisition_method = r["权利取得方式"]
            if r.get("证书日期", "") and not certificate_date:
                certificate_date = r["证书日期"]
            if r.get("申请人", "") and not applicant:
                applicant = r["申请人"]
            if r.get("著作权人", "") and not owner:
                owner = r["著作权人"]

        # 从 software_status_map 获取综合状态信息
        status_info = software_status_map.get(identifier, {})

        # ---- 动态列名处理 ----
        # 软著报表的列名可能因配置不同而变化，需要动态检测
        # 检查配置中的列名列表，确定实际使用的列名
        filename_col = "文件名" if "文件名" in config.SOFTWARE_REPORT_COLUMNS else "当前文件名"
        filepath_col = "文件路径" if "文件路径" in config.SOFTWARE_REPORT_COLUMNS else ""
        process_time_col = "处理时间" if "处理时间" in config.SOFTWARE_REPORT_COLUMNS else ""
        original_filename_col = "原始文件名" if "原始文件名" in config.SOFTWARE_REPORT_COLUMNS else ""

        row = {
            "法律状态": status_info.get("法律状态", ""),
            "标识号": identifier,
            "受理日期": acceptance_date,
            "证书日期": certificate_date,
            "受理号": acceptance_number,
            "登记号": registration_number,
            "软件名称": software_name,
            "证书号": certificate_number,
            "申请人": applicant,
            "著作权人": owner,
            "软著代理": agent,
            "权利取得方式": right_acquisition_method,
            # 动态列名：根据配置决定使用哪个列名
            filename_col: latest.get("文件名", "") or latest.get("当前文件名", ""),
            filepath_col: latest.get("文件路径", ""),
            process_time_col: latest.get("处理时间", ""),
            original_filename_col: latest.get("原始文件名", ""),
        }
        # 过滤掉键为空字符串的项（当配置中不含某列时，对应列名为空字符串）
        row = {k: v for k, v in row.items() if k}
        report_rows.append(row)

    # 按标识号去重，确保每个软著只出现一次
    report_rows = _deduplicate_rows(report_rows, ["标识号"])
    # 按标识号升序排序
    report_rows.sort(key=lambda r: r.get("标识号", ""))
    csv_manager.write_csv(config.SOFTWARE_REPORT_CSV, report_rows, config.SOFTWARE_REPORT_COLUMNS)
    logger.info(f"软著报表已生成: {config.SOFTWARE_REPORT_CSV}（{len(report_rows)} 条）")


def run():
    """脚本3的主执行函数。

    执行流程：
      1. 确保 CSV 目录存在
      2. 依次生成专利、商标、软著三类汇总报表
    """
    logger.info("=" * 60)
    logger.info("脚本3：报表生成开始")
    logger.info("=" * 60)

    # 确保CSV输出目录存在
    os.makedirs(config.CSV_DIR, exist_ok=True)

    # 依次生成三类报表
    _generate_patent_report()
    _generate_trademark_report()
    _generate_software_report()

    logger.info("脚本3：报表生成完成")


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
