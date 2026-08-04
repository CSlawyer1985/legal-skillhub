"""
配置模块 (config.py)
====================

本模块集中管理知识产权官文自动归档系统的所有配置常量，包括：
  - 目录路径：临时存放区、archives、日志、CSV、报表等
  - 子文件夹分类：专利、商标、软著
  - CSV 文件路径：归档数据表与报表数据表
  - CSV 列定义：各类型知识产权归档记录与报表的列名及顺序

注意事项：
  - BASE_DIR 为系统根路径，所有其他路径均基于此派生
  - 修改目录结构时需同步更新本模块中的路径常量
  - CSV 列定义的顺序决定了输出文件的表头顺序，增删列时需确保与
    csv_manager、legal_status、script1_process 等模块的字段映射一致
"""

import os

# ==================== 目录路径配置 ====================
# BASE_DIR: 系统根目录，所有子目录均基于此路径
BASE_DIR = os.getcwd()

# TEMP_DIR: 临时存放区，待处理的 PDF 文件放入此目录
TEMP_DIR = os.path.join(BASE_DIR, "temp-in")

# REPO_DIR: archives目录，已归档的 PDF 文件按分类存储于此
REPO_DIR = os.path.join(BASE_DIR, "archives")

# LOG_DIR: 日志目录，存放系统运行日志和 JSON 处理日志
LOG_DIR = os.path.join(BASE_DIR, "logs")

# CSV_DIR: CSV 数据目录，存放归档记录表和报表数据
CSV_DIR = os.path.join(BASE_DIR, "csv")

# REPORT_DIR: 报表目录（预留），可用于存放格式化报表输出
REPORT_DIR = os.path.join(BASE_DIR, "reports")

# FAILED_DIR: 未处理文件目录，解析失败或无法识别的 PDF 文件移入此目录
FAILED_DIR = os.path.join(BASE_DIR, "failed")

# ==================== 子文件夹分类 ====================
# archives目录下的三类知识产权子文件夹名称
# 与 _get_sub_folder() 函数中的 main_type → 子文件夹映射对应
SUB_FOLDERS = ["专利", "商标", "软著"]

# ==================== 归档数据 CSV 文件路径 ====================
# 分别对应专利、商标、软著三类知识产权的归档明细记录
PATENT_CSV = os.path.join(CSV_DIR, "patent_files_archive.csv")
TRADEMARK_CSV = os.path.join(CSV_DIR, "trademark_files_archive.csv")
SOFTWARE_CSV = os.path.join(CSV_DIR, "software_files_archive.csv")

# ==================== 报表数据 CSV 文件路径 ====================
# 分别对应专利、商标、软著三类知识产权的汇总报表
PATENT_REPORT_CSV = os.path.join(CSV_DIR, "patent_report.csv")
TRADEMARK_REPORT_CSV = os.path.join(CSV_DIR, "trademark_report.csv")
SOFTWARE_REPORT_CSV = os.path.join(CSV_DIR, "software_report.csv")

# ==================== 归档数据 CSV 列定义 ====================
# 以下列表定义了各类型归档 CSV 的列名及顺序：
#   - 子类型: 文件细分类（如"专利通知书"、"商标注册证"等）
#   - 标识号: 用于将同一知识产权的多份文件关联在一起的唯一标识
#   - 状态变更历史: 以"→"连接的法律状态变更轨迹（如"受理→实审→授权"）

PATENT_CSV_COLUMNS = [
    "申请号", "专利类型", "发明创造名称", "专利权人", "通知书名称", "发文日期",
    "申请日", "授权公告日", "公开日", "授权日", "授权公告号", "证书号",
    "发明人", "受理时申请人", "原专利权人名称", "现专利权人名称",
    "著录项目变更生效日", "年费信息", "登记簿状态", "子类型", "发文序号", "标识号",
    "原始文件名", "当前文件名", "处理时间", "文件路径"
]

TRADEMARK_CSV_COLUMNS = [
    "子类型", "标识号", "通知书名称", "发文编号", "申请号",
    "申请日期", "申请类别", "注册号", "注册日期", "注册类别",
    "复审委托代理人", "代理文号", "申请人", "注册人", "法律状态",
    "变更申请号", "变更事项",
    "文件名", "文件路径", "处理时间", "原始文件名"
]

SOFTWARE_CSV_COLUMNS = [
    "子类型", "法律状态", "标识号", "受理日期", "证书日期",
    "受理号", "登记号", "软件名称", "证书号", "申请人",
    "著作权人", "软著代理", "权利取得方式",
    "文件名", "文件路径", "处理时间", "原始文件名"
]

# ==================== 报表数据 CSV 列定义 ====================
# 报表仅保留关键字段，用于快速概览各知识产权的最新状态

PATENT_REPORT_COLUMNS = [
    "申请号", "专利类型", "发明创造名称", "专利权人", "法律状态",
    "最新专利官文名称", "最新发文日期", "申请日", "授权公告日", "公开日",
    "授权日", "授权公告号", "证书号", "发明人", "受理时申请人",
    "原专利权人名称", "现专利权人名称", "专利权人变更记录",
    "著录项目变更生效日", "年费信息", "登记簿状态"
]

TRADEMARK_REPORT_COLUMNS = [
    "标识号", "法律状态", "当前权利人",
    "申请号", "申请日期", "申请类别", "注册号", "注册日期", "注册类别",
    "复审委托代理人", "代理文号", "申请人", "注册人",
    "最新通知书名称", "变更申请号", "变更事项",
]

SOFTWARE_REPORT_COLUMNS = [
    "法律状态", "标识号", "受理日期", "证书日期",
    "受理号", "登记号", "软件名称", "证书号", "申请人",
    "著作权人", "软著代理", "权利取得方式",
    "文件名", "文件路径", "处理时间", "原始文件名"
]


def configure(input_dir, output_dir=None):
    """根据用户指定的输入/输出目录重新配置系统全局路径。

    当通过 CLI 或外部调用指定自定义目录时，需在执行脚本前调用此函数
    以覆盖默认的路径配置。该函数会修改本模块的所有全局路径变量。

    Args:
        input_dir (str): 待处理的 PDF 文件所在目录（必选），
                         将被设置为 TEMP_DIR
        output_dir (str | None): 输出根目录（可选），
                                 默认在 input_dir 的父目录下创建 ip_archives 文件夹；
                                 将被设置为 BASE_DIR，其他路径均基于此派生

    Note:
        - 调用此函数后，所有全局路径变量（BASE_DIR、TEMP_DIR、REPO_DIR 等）
          都会被重新赋值
        - FAILED_DIR 始终位于 BASE_DIR 的父目录下，与输出目录同级
        - 必须在导入其他模块的 run() 函数之前调用，否则路径不会生效
    """
    global BASE_DIR, TEMP_DIR, REPO_DIR, LOG_DIR, CSV_DIR, REPORT_DIR, FAILED_DIR
    global PATENT_CSV, TRADEMARK_CSV, SOFTWARE_CSV
    global PATENT_REPORT_CSV, TRADEMARK_REPORT_CSV, SOFTWARE_REPORT_CSV

    # 若未指定输出目录，则在输入目录的父目录下创建 ip_archives 作为默认输出根目录
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(input_dir), "ip_archives")

    # 以输出目录作为系统根路径，所有子目录均基于此派生
    BASE_DIR = output_dir
    # 输入目录即为临时存放区，脚本1从此目录扫描 PDF 文件
    TEMP_DIR = input_dir
    # 以下路径均基于 BASE_DIR 重新构建，保持与默认配置相同的目录结构
    REPO_DIR = os.path.join(BASE_DIR, "archives")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    CSV_DIR = os.path.join(BASE_DIR, "csv")
    REPORT_DIR = os.path.join(BASE_DIR, "reports")
    # FAILED_DIR 特殊处理：放在 BASE_DIR 的父目录下，与输出目录同级，避免混入归档结果
    FAILED_DIR = os.path.join(os.path.dirname(BASE_DIR), "failed")

    # 重新生成三类归档数据 CSV 的路径，基于新的 CSV_DIR
    PATENT_CSV = os.path.join(CSV_DIR, "patent_files_archive.csv")
    TRADEMARK_CSV = os.path.join(CSV_DIR, "trademark_files_archive.csv")
    SOFTWARE_CSV = os.path.join(CSV_DIR, "software_files_archive.csv")

    # 重新生成三类报表 CSV 的路径，基于新的 CSV_DIR
    PATENT_REPORT_CSV = os.path.join(CSV_DIR, "patent_report.csv")
    TRADEMARK_REPORT_CSV = os.path.join(CSV_DIR, "trademark_report.csv")
    SOFTWARE_REPORT_CSV = os.path.join(CSV_DIR, "software_report.csv")
