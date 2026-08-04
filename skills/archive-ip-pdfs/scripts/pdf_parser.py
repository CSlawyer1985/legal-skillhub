"""
PDF 解析模块 (pdf_parser.py)
=============================

本模块负责从知识产权官文 PDF 文件中提取文本信息，识别文件类型，
并解析出关键字段（如申请号、通知书名称、权利人等），最终生成
规范化的重命名文件名。

处理流程概述：
  1. 读取 PDF 首页文本（支持 pdfplumber / PyMuPDF(fitz) / PyPDF2 三种引擎）
  2. 识别主类型（专利文件 / 商标文件 / 软著文件）
  3. 识别子类型（如专利通知书、商标注册证、软著证书等）
  4. 根据子类型提取对应字段信息
  5. 按命名规则生成新文件名

PDF 读取引擎优先级：
  pdfplumber → PyMuPDF(fitz) → PyPDF2
  优先使用 pdfplumber，因其对中文 PDF 的文本提取效果最佳；
  若不可用则依次降级到 fitz 和 PyPDF2。

命名规则：
  每种子类型有独立的命名模板（见 FILENAME_FORMAT_CONFIG），
  模板中的字段从解析结果中取值，以"_"连接组成文件名。
  特殊前缀"__literal__"表示该字段为固定字面值，不从解析结果取值。

限制条件：
  - 仅支持文本型 PDF，不支持扫描件/图像 PDF（无 OCR 能力）
  - 正则匹配依赖官文的标准格式，非标准格式可能解析失败
  - 多个权利人以"&"连接

错误诊断：
  - 当 PDF 读取失败时，会记录各引擎的具体异常信息到日志
  - 错误消息区分"PDF读取失败"（引擎异常）和"图像PDF"（无文本可提取）
  - 若所有 PDF 引擎均未安装，错误消息会明确提示缺失的库
"""

import os
import re
import logging

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import fitz
except ImportError:
    fitz = None

logger = logging.getLogger(__name__)

# 商标通知书类型列表
# 用于判断商标文件属于"通知书"类别还是"证书/申请书"类别
TRADEMARK_NOTIFICATION_TYPES = [
    "商标注册申请缴费通知书",
    "商标注册申请受理通知书",
    "商标驳回通知书",
    "商标部分驳回通知书",
    "商标注册申请初步审定公告通知书",
    "商标评审申请受理通知书",
    "商标驳回复审决定书",
    "商标评审案件补正通知书",
    "商标续展注册申请受理通知书",
    "提供注册商标使用证据通知书",
    "注册商标续展申请受理通知书",
    "商标使用许可合同备案通知书",
    "商标变更申请补正通知书",
]

TRADEMARK_DISPATCH_NUMBER_RULES = {
    "商标注册申请受理通知书": {"prefix": "ZCSL", "has_serial": True},
    "商标注册申请缴费通知书": {"prefix": "JFTZ", "has_serial": True},
    "商标部分驳回通知书": {"prefix": "BFBH", "has_serial": True},
    "商标注册申请初步审定公告通知书": {"prefix": "CSGG", "has_serial": False},
    "商标驳回通知书": {"prefix": "BHTZ", "has_serial": True},
    "商标变更申请补正通知书": {"prefix": "BGBZ", "has_serial": True},
}

TRADEMARK_DISPATCH_NUMBER_BHFS_RULES = {
    "商标注册申请初步审定公告通知书": {"type_code": "CSGG", "has_serial": True},
}

# ==================== 文件名格式配置 ====================
# 定义每种子类型的文件命名模板：
#   - fields: 命名模板中包含的字段名（中文，用于展示）
#   - defaults: 实际参与命名的字段名（与 fields 对应，可省略某些字段）
#   - field_key_map: 字段名 → 解析结果字典中的键名映射
#     特殊值"__literal__XXX"表示该位置直接使用字面值"XXX"
FILENAME_FORMAT_CONFIG = {
    "专利通知书": {
        "fields": ["专利号", "发文日期", "专利通知书名称", "专利权人"],
        "defaults": ["专利号", "发文日期", "专利通知书名称", "专利权人"],
        "field_key_map": {
            "专利号": "patent_number",
            "发文日期": "dispatch_date_compact",
            "专利通知书名称": "patent_notification_name",
            "专利权人": "patent_owner",
        },
    },
    "专利证书": {
        "fields": ["专利号", "授权公告日缩写", "专利证书名称", "授权公告号", "专利权人"],
        "defaults": ["专利号", "授权公告日缩写", "专利证书名称", "授权公告号", "专利权人"],
        "field_key_map": {
            "专利号": "patent_number",
            "授权公告日缩写": "announcement_date_compact",
            "专利证书名称": "patent_certificate_name",
            "授权公告号": "announcement_number",
            "专利权人": "patent_owner",
        },
    },
    "专利登记簿副本": {
        "fields": ["专利号", "发文日期缩写", "登记簿副本", "专利权人"],
        "defaults": ["专利号", "发文日期缩写", "登记簿副本", "专利权人"],
        "field_key_map": {
            "专利号": "patent_number",
            "发文日期缩写": "cnipa_date_compact",
            "登记簿副本": "__literal__登记簿副本",
            "专利权人": "patent_owner",
        },
    },
    "商标通知书": {
        "fields": ["商标申请号", "商标通知书名称", "商标申请人"],
        "defaults": ["商标申请号", "商标通知书名称", "商标申请人"],
        "field_key_map": {
            "商标申请号": "trademark_application_number",
            "商标通知书名称": "trademark_notification_name",
            "商标申请人": "applicant",
        },
    },
    "商标注册证": {
        "fields": ["注册号", "商标注册证", "注册类别", "注册日期", "注册人"],
        "defaults": ["注册号", "商标注册证", "注册类别", "注册日期", "注册人"],
        "field_key_map": {
            "注册号": "registration_number",
            "商标注册证": "__literal__商标注册证",
            "注册类别": "registration_category",
            "注册日期": "registration_date",
            "注册人": "owner",
        },
    },
    "商标注册申请书": {
        "fields": ["代理文号", "商标注册申请书", "申请人"],
        "defaults": ["代理文号", "商标注册申请书", "申请人"],
        "field_key_map": {
            "代理文号": "agent_number",
            "商标注册申请书": "__literal__商标注册申请书",
            "申请人": "applicant",
        },
    },
    "软著受理通知书": {
        "fields": ["软件名称", "软著受理通知书", "受理日期", "申请人"],
        "defaults": ["软件名称", "软著受理通知书", "受理日期", "申请人"],
        "field_key_map": {
            "软件名称": "software_name",
            "软著受理通知书": "__literal__软著受理通知书",
            "受理日期": "acceptance_date",
            "申请人": "applicant",
        },
    },
    "软著证书": {
        "fields": ["软件名称", "软著证书", "证书日期", "著作权人"],
        "defaults": ["软件名称", "软著证书", "证书日期", "著作权人"],
        "field_key_map": {
            "软件名称": "software_name",
            "软著证书": "__literal__软著证书",
            "证书日期": "certificate_date",
            "著作权人": "owner",
        },
    },
}


def read_pdf_first_page(pdf_path):
    """读取 PDF 文件首页的文本内容。

    按优先级依次尝试三种 PDF 解析引擎，返回首页文本。
    同时返回去除空格和保留空格两个版本：
      - text_no_space: 去除所有空格和全角空格后的文本，用于关键词匹配
      - text: 保留原始空格的文本，用于正则提取（部分字段需要空格定位）

    Args:
        pdf_path (str): PDF 文件的完整路径

    Returns:
        tuple[str, str, str]: (text_no_space, text, error)
            - text_no_space: 去除空格后的文本，用于类型检测和关键词匹配
            - text: 原始文本，用于正则提取字段值
            - error: 错误信息，成功时为空字符串
    """
    text = ""
    errors = []

    # 优先使用 pdfplumber，对中文 PDF 文本提取效果最佳
    if pdfplumber:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    text = pdf.pages[0].extract_text() or ""
                    if text.strip():
                        # 去除半角空格和全角空格(\u3000)，生成无空格版本用于关键词匹配
                        text_no_space = text.replace(" ", "").replace("\u3000", "")
                        return text_no_space, text, ""
        except Exception as e:
            errors.append(f"pdfplumber: {e}")
            logger.debug(f"pdfplumber 读取失败 [{pdf_path}]: {e}")
    else:
        errors.append("pdfplumber 未安装")

    # 降级到 PyMuPDF(fitz)，提取效果次之
    if fitz:
        try:
            doc = fitz.open(pdf_path)
            if doc.page_count > 0:
                page = doc[0]
                text = page.get_text()
                doc.close()
                if text.strip():
                    text_no_space = text.replace(" ", "").replace("\u3000", "")
                    return text_no_space, text, ""
        except Exception as e:
            errors.append(f"PyMuPDF: {e}")
            logger.debug(f"PyMuPDF 读取失败 [{pdf_path}]: {e}")
    else:
        errors.append("PyMuPDF 未安装")

    # 最后降级到 PyPDF2，作为兜底方案
    if PyPDF2:
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                if reader.pages:
                    text = reader.pages[0].extract_text() or ""
                    if text.strip():
                        text_no_space = text.replace(" ", "").replace("\u3000", "")
                        return text_no_space, text, ""
        except Exception as e:
            errors.append(f"PyPDF2: {e}")
            logger.debug(f"PyPDF2 读取失败 [{pdf_path}]: {e}")
    else:
        errors.append("PyPDF2 未安装")

    # 所有引擎均失败，汇总错误信息
    error_detail = "; ".join(errors)
    return "", "", error_detail


def detect_main_file_type(text_no_space):
    """检测 PDF 文件的主类型（专利文件/商标文件/软著文件/未知）。

    检测策略采用关键词匹配，按软著→商标→专利的优先级依次检测。
    优先检测软著是因为其关键词较为独特不易误判；商标次之；
    专利的关键词最多，放在最后。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        str: 主类型名称（"专利文件"/"商标文件"/"软著文件"/"未知"）
    """
    # 软著优先检测：关键词独特，不易误判
    # "软著登字"是软著证书的特征词；"软件名称"+"著作权人"同时出现也是软著证书的标志
    if "软著登字" in text_no_space or (
        "软件名称" in text_no_space and "著作权人" in text_no_space
    ):
        return "软著文件"
    # "软件登记受理通知书"是软著受理通知书的特征词
    if "软件登记受理通知书" in text_no_space:
        return "软著文件"
    # 商标次之检测：先匹配缩写代码+中文关键词组合，再匹配纯中文关键词
    trademark_official_keywords = [
        "JFTZ", "ZCSL", "BHTZ", "BFBH", "CSGG", "BHFS", "BGBZ",
        "商标注册申请缴费通知书",
        "商标注册申请受理通知书",
        "商标驳回通知书",
        "商标部分驳回通知书",
        "商标注册申请初步审定公告通知书",
        "商标注册证",
        "商标评审申请受理通知书",
        "驳回复审决定书",
        "商标驳回复审决定书",
        "商标评审案件补正通知书",
        "商标续展注册申请受理通知书",
        "商标续展注册证明",
        "商标变更核准证明",
        "商标转让核准证明",
        "提供商标使用证据回执",
        "提供注册商标使用证据通知书",
        "注册商标续展申请受理通知书",
        "商标使用许可合同备案通知书",
        "商标变更申请补正通知书",
    ]
    for kw in trademark_official_keywords:
        if kw in text_no_space:
            return "商标文件"
    # 商标注册证的补充判断：部分商标注册证可能不含上述关键词，但包含"注册人地址"+"注册日期"
    if "注册人地址" in text_no_space and "注册日期" in text_no_space:
        return "商标文件"
    # 专利最后检测：关键词最多，覆盖面最广
    patent_official_keywords = [
        "专利申请受理通知书",
        "授予实用新型专利权通知书",
        "授予发明专利权通知书",
        "授予外观设计专利权通知书",
        "办理登记手续通知书",
        "手续合格通知书",
        "审查意见通知书",
        "发明专利申请公布通知书",
        "发明专利申请初步审查合格通知书",
        "发明专利申请进入实质审查阶段通知书",
        "专利权终止通知书",
        "视为撤回通知书",
        "视为放弃取得专利权通知书",
        "驳回决定",
        "复审决定书",
        "复审通知书",
        "复审请求受理通知书",
        "补正通知书",
        "收费减缴审批通知书",
        "恢复权利请求审批通知书",
        "同意撤回专利申请",
        "实用新型专利证书",
        "外观设计专利证书",
        "发明专利证书",
        "登记簿副本",
    ]
    for kw in patent_official_keywords:
        if kw in text_no_space:
            return "专利文件"
    # 专利号的正则匹配作为兜底：ZL+12位数字+点+校验位
    if re.search(r"ZL\d{12}\.[\dX]", text_no_space):
        return "专利文件"
    # CN+12位数字+点+校验位，也是专利号的常见格式
    if re.search(r"CN\d{12}\.[\dX]", text_no_space):
        return "专利文件"
    # 软著的兜底检测：仅含"计算机软件著作权登记证书"或"软件名称"关键词
    software_official_keywords = [
        "计算机软件著作权登记证书",
        "软件名称",
    ]
    for kw in software_official_keywords:
        if kw in text_no_space:
            return "软著文件"
    return "未知"


def detect_patent_type(text_no_space):
    """检测专利文件的具体子类型。

    子类型包括：
      - 专利通知书: 各类审查通知书、决定书等
      - 专利登记簿副本: 专利登记簿摘录
      - 专利证书: 发明/实用新型/外观设计专利证书

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        tuple[str | None, Any]:
            - 第一个元素为子类型名称（"专利通知书"/"专利登记簿副本"/"专利证书"），
              无法识别时返回 None
            - 第二个元素为附加信息：
              - 专利通知书: 返回匹配到的通知书名称列表 (list[str])
              - 专利证书: 返回证书名称 (str)
              - 专利登记簿副本: 返回 None
    """
    # 先粗筛：文本中是否包含"通知书"或"决定"关键词
    notification_keywords = ["通知书", "决定"]
    has_notification = any(kw in text_no_space for kw in notification_keywords)

    if has_notification:
        # 精确匹配：逐一检查预定义的通知书名称是否出现在文本中
        notification_names = [
            "专利申请受理通知书",
            "办理登记手续通知书",
            "发明专利申请公布通知书",
            "发明专利申请进入实质审查阶段通知书",
            "专利权终止通知书",
            "手续合格通知书",
            "视为放弃取得专利权通知书",
            "复审决定书",
            "复审通知书",
            "复审请求受理通知书",
            "驳回决定",
            "第一次审查意见通知书",
            "第二次审查意见通知书",
            "第三次审查意见通知书",
            "第四次审查意见通知书",
            "发明专利申请初步审查合格通知书",
            "恢复权利请求审批通知书",
            "视为撤回通知书",
            "补正通知书",
            "收费减缴审批通知书",
            "授予实用新型专利权通知书",
            "授予发明专利权通知书",
            "授予外观设计专利权通知书",
        ]

        found_notifications = []
        for name in notification_names:
            if name in text_no_space:
                found_notifications.append(name)

        # 特殊处理：当"手续合格通知书"和"同意撤回专利申请"同时出现时，
        # 实际通知书名称应为"撤回专利申请手续合格通知书"，
        # 需要将"手续合格通知书"替换为更精确的名称
        if "手续合格通知书" in found_notifications and "同意撤回专利申请" in text_no_space:
            found_notifications.remove("手续合格通知书")
            if "撤回专利申请手续合格通知书" not in found_notifications:
                found_notifications.append("撤回专利申请手续合格通知书")

        if found_notifications:
            return "专利通知书", found_notifications

    # 检测登记簿副本：关键词为"登记簿副本"
    if "登记簿副本" in text_no_space:
        return "专利登记簿副本", None

    # 检测专利证书：匹配三种证书类型
    certificate_names = ["实用新型专利证书", "外观设计专利证书", "发明专利证书"]

    for cert_name in certificate_names:
        if cert_name in text_no_space:
            return "专利证书", cert_name

    return None, None


def detect_trademark_type(text_no_space):
    """检测商标文件的具体子类型。

    检测策略采用两步匹配：
      1. 先同时匹配缩写代码和中文关键词（如"JFTZ"+"缴费通知书"），
         提高识别准确度
      2. 再仅匹配中文关键词，作为降级策略

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        str | None: 商标子类型名称（如"商标注册证"、"商标驳回通知书"等），
                    无法识别时返回 None
    """
    # ===== 第一步：缩写代码 + 中文关键词双重匹配，准确度更高 =====
    if "JFTZ" in text_no_space and "商标注册申请缴费通知书" in text_no_space:
        return "商标注册申请缴费通知书"
    if "ZCSL" in text_no_space and "商标注册申请受理通知书" in text_no_space:
        return "商标注册申请受理通知书"
    if "BHTZ" in text_no_space and "商标驳回通知书" in text_no_space:
        return "商标驳回通知书"
    if "BFBH" in text_no_space and "商标部分驳回通知书" in text_no_space:
        return "商标部分驳回通知书"
    # 初步审定公告通知书有两种缩写代码：BHFS 和 CSGG
    if "BHFS" in text_no_space and "商标注册申请初步审定公告通知书" in text_no_space:
        return "商标注册申请初步审定公告通知书"
    if "CSGG" in text_no_space and "商标注册申请初步审定公告通知书" in text_no_space:
        return "商标注册申请初步审定公告通知书"

    # ===== 第二步：仅中文关键词匹配，作为降级策略 =====
    if "商标注册申请缴费通知书" in text_no_space:
        return "商标注册申请缴费通知书"
    if "商标注册申请受理通知书" in text_no_space:
        return "商标注册申请受理通知书"
    # 商标驳回通知书需排除"部分驳回"的情况
    if "商标驳回通知书" in text_no_space and "部分" not in text_no_space:
        return "商标驳回通知书"
    if "商标部分驳回通知书" in text_no_space:
        return "商标部分驳回通知书"
    if "商标注册申请初步审定公告通知书" in text_no_space:
        return "商标注册申请初步审定公告通知书"
    if "商标评审申请受理通知书" in text_no_space:
        return "商标评审申请受理通知书"
    # "商标驳回复审决定书"优先于通用的"驳回复审决定书"
    if "商标驳回复审决定书" in text_no_space:
        return "商标驳回复审决定书"
    if "驳回复审决定书" in text_no_space:
        return "商标驳回复审决定书"
    if "商标评审案件补正通知书" in text_no_space:
        return "商标评审案件补正通知书"
    if "商标续展注册申请受理通知书" in text_no_space:
        return "商标续展注册申请受理通知书"
    if "商标续展注册证明" in text_no_space:
        return "商标续展注册证明"
    if "商标变更核准证明" in text_no_space:
        return "商标变更核准证明"
    if "商标转让核准证明" in text_no_space:
        return "商标转让核准证明"
    if "提供注册商标使用证据通知书" in text_no_space:
        return "提供注册商标使用证据通知书"
    if "注册商标续展申请受理通知书" in text_no_space:
        return "注册商标续展申请受理通知书"
    if "商标使用许可合同备案通知书" in text_no_space:
        return "商标使用许可合同备案通知书"
    # 变更申请补正通知书也支持缩写代码+中文双重匹配
    if "BGBZ" in text_no_space and "商标变更申请补正通知书" in text_no_space:
        return "商标变更申请补正通知书"
    if "商标变更申请补正通知书" in text_no_space:
        return "商标变更申请补正通知书"
    # 商标注册证的检测
    if "商标注册证" in text_no_space:
        return "商标注册证"
    # 部分商标注册证可能不含"商标注册证"关键词，但含"注册人地址"+"注册日期"
    if "注册人地址" in text_no_space and "注册日期" in text_no_space:
        return "商标注册证"
    if "商标注册申请书" in text_no_space:
        return "商标注册申请书"
    return None


def detect_software_type(text_no_space):
    """检测软著文件的具体子类型。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        str | None: 软著子类型名称（"软著受理通知书"或"软著证书"），
                    无法识别时返回 None
    """
    # 受理通知书的特征关键词
    if "软件登记受理通知书" in text_no_space:
        return "软著受理通知书"
    # 软著证书的特征关键词：软著登字、软件名称+著作权人、证书全称
    if "软著登字" in text_no_space:
        return "软著证书"
    if "软件名称" in text_no_space and "著作权人" in text_no_space:
        return "软著证书"
    if "计算机软件著作权登记证书" in text_no_space:
        return "软著证书"
    return None


def extract_patent_number(text):
    """从文本中提取专利号。

    支持的格式：
      - ZL 后跟 12 位数字+点+校验位（如 ZL202010123456.1）
      - 直接 12 位数字+点+校验位
      - CN 后跟 12 位数字+点+校验位

    提取结果统一添加"CN"前缀。

    Args:
        text (str): 待提取的文本（去除空格后的版本）

    Returns:
        str: 专利号（含 CN 前缀），如"CN202010123456.1"；未找到返回空字符串
    """
    # 按优先级定义三种专利号格式的正则模式
    patterns = [
        r"ZL(\d{12}\.[\dX])",       # ZL前缀格式，如 ZL202010123456.1
        r"(\d{12}\.[\dX])",          # 无前缀格式，如 202010123456.1
        r"CN(\d{12}\.[\dX])",        # CN前缀格式，如 CN202010123456.1
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            patent_num = match.group(1)
            # 统一添加 CN 前缀（ZL 和纯数字格式提取出的不含 CN）
            if not patent_num.startswith("CN"):
                patent_num = "CN" + patent_num
            return patent_num
    return ""


def extract_dispatch_number(text):
    """从文本中提取发文序号（16 位数字）。

    发文序号以年份开头（如 2023123456789012），用于唯一标识一份通知书。

    Args:
        text (str): 待提取的文本（去除空格后的版本）

    Returns:
        str: 16 位发文序号；未找到返回空字符串
    """
    # 匹配所有16位连续数字，然后筛选以"20"开头的（2000年以后的发文序号）
    pattern = r"(\d{16})"
    matches = re.findall(pattern, text)
    for match in matches:
        if match.startswith("20"):
            return match
    return ""


def extract_invention_name(text):
    # 两种正则模式：匹配"发明创造名称："或"发明名称："后的内容
    # 模式1：以"发明创造名称"开头，到换行或文本末尾结束
    # 模式2：以"发明名称"开头，到申请日/公开日/授权日/换行结束
    patterns = [
        r"发明创造名称[：:](.*?)(?:\n|$)",
        r"发明名称[：:](.*?)(?:申请日|公开日|授权日|\n|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            name = match.group(1).strip()
            # 清除提取文本中的换行符、回车符和制表符
            name = name.replace("\n", "").replace("\r", "").replace("\t", "")
            if name:
                return name
    return ""


def extract_application_date(text):
    """从文本中提取申请日期。

    匹配"申请日：YYYY年MM月DD日"格式，月份和日期自动补零。

    Args:
        text (str): 待提取的文本（去除空格后的版本）

    Returns:
        str: 格式化的申请日期（如"2023年01月15日"）；未找到返回空字符串
    """
    # 正则允许"年月日"前后有空白字符，月份和日期支持1-2位数字
    pattern = r"申请日[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    match = re.search(pattern, text)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)  # 月份补零，如"3"→"03"
        day = match.group(3).zfill(2)    # 日期补零，如"5"→"05"
        return f"{year}年{month}月{day}日"
    return ""


def extract_inventors(text):
    # 两种正则模式：提取"发明人："后的内容
    # 模式1：以"专利权人"或"申请人"或换行作为结束边界（优先）
    # 模式2：仅以换行作为结束边界（降级）
    patterns = [
        r"发明人[：:](.*?)(?:专利权人|申请人|\n|$)",
        r"发明人[：:](.*?)(?:\n|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            inventors_text = match.group(1).strip()
            # 按中文/英文分隔符拆分多个发明人
            inventors = re.split(r"[、，,；;]", inventors_text)
            inventors = [inv.strip() for inv in inventors if inv.strip()]
            if inventors:
                return ",".join(inventors)
    return ""


def _compact_chinese_date(date_str):
    """将中文日期格式压缩为纯数字格式（去除"年月日"文字）。

    例如 "2023年12月15日" → "20231215"。
    主要用于文件名中嵌入日期时避免特殊字符。

    Args:
        date_str (str): 中文日期字符串

    Returns:
        str: 压缩后的日期字符串（如"20231215"）；解析失败返回空字符串
    """
    if not date_str:
        return ""
    match = re.match(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", date_str)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)  # 月份补零
        day = match.group(3).zfill(2)    # 日期补零
        return f"{year}{month}{day}"
    return ""


def extract_announcement_date(text):
    """从专利证书文本中提取授权公告日期。

    匹配"授权公告日：YYYY年MM月DD日"格式，月份和日期自动补零。
    注意正则中"授权公告日"的每个字之间允许有空格。

    Args:
        text (str): 待提取的文本（去除空格后的版本）

    Returns:
        str: 格式化的授权公告日期（如"2023年01月15日"）；未找到返回空字符串
    """
    # "授权公告日"每个字之间允许有空格，因为部分PDF提取后字间可能插入空格
    pattern = r"授\s*权\s*公\s*告\s*日[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    match = re.search(pattern, text)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}年{month}月{day}日"
    return ""


def extract_patent_owner_notification(text):
    """从专利通知书中提取专利权人。

    提取"专利权人："到"发明创造名称："之间的文本，
    多个专利权人以"&"连接。

    Args:
        text (str): PDF 首页原始文本（保留空格）

    Returns:
        str: 专利权人，如"公司A&公司B"；未找到返回空字符串
    """
    # 从"专利权人："提取到"发明创造名称："之间的文本
    pattern = r"专利权人[：:](.*?)发明创造名称[：:]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        owners_text = match.group(1).strip()
        # 按中文/英文分隔符拆分多个专利权人
        owners = re.split(r"[、，,；;]", owners_text)
        owners = [o.strip() for o in owners if o.strip()]
        return "&".join(owners)
    return ""


def extract_applicant_for_acceptance(text):
    """从专利申请受理通知书中提取申请人。

    受理通知书中使用"申请人"而非"专利权人"字段。
    提取"申请人："到"发明人："之间的文本。

    Args:
        text (str): PDF 首页原始文本（保留空格）

    Returns:
        str: 申请人，如"公司A&公司B"；未找到返回空字符串
    """
    # 受理通知书特殊处理：从"申请人"字段提取，而非"专利权人"
    # 因为受理阶段尚无专利权人概念，只有申请人
    pattern = r"申请人[：:](.*?)发明人[：:]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        applicants_text = match.group(1).strip()
        applicants = re.split(r"[、，,；;]", applicants_text)
        applicants = [a.strip() for a in applicants if a.strip()]
        return "&".join(applicants)
    return ""


def extract_patent_owner_certificate(text):
    """从专利证书中提取专利权人。

    提取"专利权人："到"地址："之间的文本。

    Args:
        text (str): PDF 首页原始文本（保留空格）

    Returns:
        str: 专利权人；未找到返回空字符串
    """
    # 专利证书中，专利权人信息位于"专利权人："和"地址："之间
    pattern = r"专利权人[：:](.*?)地址[：:]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        owners_text = match.group(1).strip()
        owners = re.split(r"[、，,；;]", owners_text)
        owners = [o.strip() for o in owners if o.strip()]
        return "&".join(owners)
    return ""


def extract_patent_owner_register(text):
    """从专利登记簿副本中提取专利权人。

    提取"专利权人："到"专利权人地址："之间的文本。

    Args:
        text (str): PDF 首页原始文本（保留空格）

    Returns:
        str: 专利权人；未找到返回空字符串
    """
    # 登记簿副本中，专利权人信息位于"专利权人："和"专利权人地址："之间
    pattern = r"专利权人[：:](.*?)专利权人地址[：:]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        owners_text = match.group(1).strip()
        owners = re.split(r"[、，,；;]", owners_text)
        owners = [o.strip() for o in owners if o.strip()]
        return "&".join(owners)
    return ""


def extract_certificate_number_register(text_no_space):
    # 从登记簿副本中提取证书号
    pattern = r"证书号[：:]\s*(\d+)"
    match = re.search(pattern, text_no_space)
    if match:
        return match.group(1)
    return ""


def extract_publication_date(text_no_space):
    # 提取公开日期，格式为"公开日：YYYY年MM月DD日"
    pattern = r"公开日[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    match = re.search(pattern, text_no_space)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}年{month}月{day}日"
    return ""


def extract_grant_date(text_no_space):
    # 提取授权日期，格式为"授权日：YYYY年MM月DD日"
    pattern = r"授权日[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    match = re.search(pattern, text_no_space)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}年{month}月{day}日"
    return ""


def extract_original_patent_owner(text_no_space):
    # 提取原专利权人名称，到"国家知识产权局"或"现专利权人名称"或文本末尾结束
    pattern = r"原专利权人名称[：:](.*?)(?:国家知识产权局|现专利权人名称|$)"
    match = re.search(pattern, text_no_space, re.DOTALL)
    if match:
        owner = match.group(1).strip()
        # 清除提取文本中的换行符等
        owner = owner.replace("\n", "").replace("\r", "").replace("\t", "")
        return owner
    return ""


def extract_current_patent_owner_register(text_no_space):
    # 提取现专利权人名称，到"著录项目变更生效日"或文本末尾结束
    pattern = r"现专利权人名称[：:](.*?)(?:著录项目变更生效日|$)"
    match = re.search(pattern, text_no_space, re.DOTALL)
    if match:
        owner = match.group(1).strip()
        owner = owner.replace("\n", "").replace("\r", "").replace("\t", "")
        return owner
    return ""


def extract_bibliographic_change_date(text_no_space):
    # 提取著录项目变更生效日期
    pattern = r"著录项目变更生效日[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    match = re.search(pattern, text_no_space)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}年{month}月{day}日"
    return ""


def extract_annual_fee_info(text_no_space):
    # 提取年费信息，到"国家知识产权局"或文本末尾结束
    pattern = r"年费信息[：:](.*?)(?:国家知识产权局|$)"
    match = re.search(pattern, text_no_space, re.DOTALL)
    if match:
        info = match.group(1).strip()
        info = info.replace("\n", "").replace("\r", "").replace("\t", "")
        return info
    return ""


def extract_cnipa_date(text_no_space):
    # 提取国家知识产权局落款日期，格式为"国家知识产权局：YYYY年MM月DD日"
    pattern = r"国家知识产权局[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    match = re.search(pattern, text_no_space)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}年{month}月{day}日"
    return ""


def extract_register_status(text_no_space):
    # 法律状态文本到显示名称的映射
    REGISTER_STATUS_TEXT_MAP = {
        "专利权有效": "授权",
        "专利权终止": "失效",
    }
    # 提取"法律状态："后的文本，到换行或末尾结束
    pattern = r"法律状态[：:\s]*(.*?)(?:\n|$)"
    match = re.search(pattern, text_no_space)
    if match:
        status_text = match.group(1).strip()
        # 在状态文本中查找匹配的映射键
        for key, value in REGISTER_STATUS_TEXT_MAP.items():
            if key in status_text:
                return value
    return ""


def extract_announcement_number(text):
    """从专利证书中提取授权公告号。

    支持的格式：
      - "授权公告号：CNXXXXXXA"
      - "授权公告号：XXXXXXA"（自动补 CN 前缀）

    Args:
        text (str): 待提取的文本（去除空格后的版本）

    Returns:
        str: 授权公告号（含 CN 前缀）；未找到返回空字符串
    """
    # 两种正则模式：含CN前缀和不含CN前缀
    patterns = [
        r"授权公告号[：:]\s*CN(\d+[A-Z])",   # 含CN前缀，如 CN123456A
        r"授权公告号[：:]\s*(\d+[A-Z])",      # 不含CN前缀，如 123456A
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            num = match.group(1)
            # 统一添加 CN 前缀
            if not num.startswith("CN"):
                num = "CN" + num
            return num
    return ""


def extract_trademark_payment_info(text_no_space):
    """从商标注册申请缴费通知书中提取信息。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含以下键：
            - trademark_application_number (str): 商标申请号
            - applicant (str): 申请人
    """
    info = {}

    # 提取商标申请号
    app_num_match = re.search(r"申请号[：:]\s*(\d+)", text_no_space)
    if app_num_match:
        info["trademark_application_number"] = app_num_match.group(1)
    else:
        info["trademark_application_number"] = ""

    # 提取申请人：从"申请人："到"缴费码"之间的文本
    applicant_match = re.search(
        r"申请人[：:](.*?)缴费码", text_no_space, re.DOTALL
    )
    if applicant_match:
        applicants_text = applicant_match.group(1).strip()
        applicants = re.split(r"[、，,；;]", applicants_text)
        applicants = [a.strip() for a in applicants if a.strip()]
        info["applicant"] = "&".join(applicants)
    else:
        info["applicant"] = ""

    # 提取商标类别
    info["trademark_category"] = extract_trademark_category(text_no_space)

    return info


def extract_trademark_acceptance_info(text_no_space, text):
    """从商标注册申请受理通知书中提取信息。

    此函数的申请人提取逻辑较复杂，采用两步降级策略：
      1. 先尝试从"商标注册申请受理通知书...根据"之间提取
      2. 若失败，再从"TMZC...ZCSL...申请日期"之间提取

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本
        text (str): PDF 首页原始文本（保留空格）

    Returns:
        dict: 包含以下键：
            - trademark_application_number (str): 商标申请号
            - applicant (str): 申请人
    """
    info = {}

    # 提取商标申请号
    app_num_match = re.search(r"申请号[：:]\s*(\d+)", text_no_space)
    if app_num_match:
        info["trademark_application_number"] = app_num_match.group(1)
    else:
        info["trademark_application_number"] = ""

    # 第一步：从"商标注册申请受理通知书"到"根据"之间提取申请人
    # 这是首选的提取方式，因为该区域通常包含申请人名称
    applicant_match = re.search(
        r"商标注册申请受理通知书\s*([^根据]+?)[：:]?\s*根据", text_no_space, re.DOTALL
    )
    if applicant_match:
        applicants_text = applicant_match.group(1).strip()
        # 清除可能残留的冒号字符
        applicants_text = applicants_text.replace("：", "").replace(":", "").strip()
        applicants = re.split(r"[、，,；;\n]", applicants_text)
        # 过滤长度≤2的短文本，避免误匹配到非申请人文本
        applicants = [a.strip() for a in applicants if a.strip() and len(a.strip()) > 2]
        info["applicant"] = "&".join(applicants) if applicants else ""
    else:
        # 第二步降级：从发文编号后的区域提取申请人
        # 格式为"TMZC+申请号+ZCSL+流水号"之后到"申请日期"之间的文本
        applicant_match2 = re.search(
            r"TMZC\d+ZCSL\d*\s*(.+?)\s*申请日期", text_no_space, re.DOTALL
        )
        if applicant_match2:
            applicants_text = applicant_match2.group(1).strip()
            applicants = re.split(r"[、，,；;\n]", applicants_text)
            applicants = [
                a.strip() for a in applicants if a.strip() and len(a.strip()) > 2
            ]
            info["applicant"] = "&".join(applicants) if applicants else ""
        else:
            info["applicant"] = ""

    # 提取申请日期和商标类别
    info["application_date"] = extract_trademark_application_date(text_no_space)
    info["trademark_category"] = extract_trademark_category(text_no_space)

    return info


def extract_trademark_rejection_info(text_no_space):
    """从商标驳回通知书中提取信息。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含以下键：
            - trademark_application_number (str): 商标申请号
            - applicant (str): 申请人
    """
    info = {}

    # 提取商标申请号
    app_num_match = re.search(r"申请号[：:]\s*(\d+)", text_no_space)
    if app_num_match:
        info["trademark_application_number"] = app_num_match.group(1)
    else:
        info["trademark_application_number"] = ""

    # 提取申请人：从"申请人："到"商标"之间的文本
    applicant_match = re.search(r"申请人[：:](.*?)商标", text_no_space, re.DOTALL)
    if applicant_match:
        applicants_text = applicant_match.group(1).strip()
        applicants = re.split(r"[、，,；;]", applicants_text)
        applicants = [a.strip() for a in applicants if a.strip()]
        info["applicant"] = "&".join(applicants)
    else:
        info["applicant"] = ""

    return info


def extract_trademark_review_decision_info(text_no_space):
    """从商标驳回复审决定书中提取信息。

    申请号的提取采用两步策略：
      1. 先匹配"申请号："格式
      2. 若失败，再匹配7-8位纯数字

    申请号的提取采用两步策略：
      1. 先匹配"申请号："格式
      2. 若失败，再匹配7-8位纯数字

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含以下键：
            - trademark_application_number (str): 商标申请号
            - applicant (str): 申请人
    """
    info = {}

    # 申请号提取：先尝试"申请号："格式，失败则降级为7-8位纯数字匹配
    app_num_match = re.search(r"申请号[：:]\s*(\d+)", text_no_space)
    if not app_num_match:
        app_num_match = re.search(r"(\d{7,8})", text_no_space)
    if app_num_match:
        info["trademark_application_number"] = app_num_match.group(1)
    else:
        info["trademark_application_number"] = ""

    # 申请人提取：先尝试到"委托代理人"结束，失败则降级为到"商标/复审/决定"结束
    applicant_match = re.search(r"申请人[：:](.*?)委托代理人", text_no_space, re.DOTALL)
    if not applicant_match:
        applicant_match = re.search(r"申请人[：:](.*?)(?:商标|复审|决定)", text_no_space, re.DOTALL)
    if applicant_match:
        applicants_text = applicant_match.group(1).strip()
        applicants = re.split(r"[、，,；;\n]", applicants_text)
        # 过滤长度≤2的短文本，避免误匹配
        applicants = [a.strip() for a in applicants if a.strip() and len(a.strip()) > 2]
        info["applicant"] = "&".join(applicants) if applicants else ""
    else:
        info["applicant"] = ""

    # 提取委托代理人信息
    info["review_agent"] = extract_trademark_review_agent(text_no_space)

    return info


def extract_trademark_change_correction_info(text_no_space):
    """从商标变更申请补正通知书中提取信息。

    提取字段：
      - trademark_application_number: 商标申请号（从"商标注册号"字段提取）
      - applicant: 申请人
      - change_application_number: 变更申请号
      - change_items: 变更事项

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含提取字段的字典
    """
    info = {}

    # 申请号提取：三步降级策略
    # 1. 先从"商标注册号"字段提取7-8位数字
    # 2. 再从"申请号"字段提取
    # 3. 最后匹配任意7-8位纯数字
    app_num_match = re.search(r"商标注册号[：:]*\s*(\d{7,8})", text_no_space)
    if not app_num_match:
        app_num_match = re.search(r"申请号[：:]\s*(\d+)", text_no_space)
    if not app_num_match:
        app_num_match = re.search(r"(\d{7,8})", text_no_space)
    if app_num_match:
        info["trademark_application_number"] = app_num_match.group(1)
    else:
        info["trademark_application_number"] = ""

    # 申请人提取：到多个可能的结束关键词之一
    applicant_match = re.search(r"申请人[：:](.*?)(?:商标|代理|地址|缴费|评审|受理|编号|日期|变更)", text_no_space, re.DOTALL)
    if applicant_match:
        applicants_text = applicant_match.group(1).strip()
        applicants = re.split(r"[、，,；;\n]", applicants_text)
        # 过滤长度≤2的短文本
        applicants = [a.strip() for a in applicants if a.strip() and len(a.strip()) > 2]
        info["applicant"] = "&".join(applicants) if applicants else ""
    else:
        info["applicant"] = ""

    # 提取变更申请号
    change_app_num_match = re.search(r"变更申请号[：:]*\s*(\d+)", text_no_space)
    if change_app_num_match:
        info["change_application_number"] = change_app_num_match.group(1)
    else:
        info["change_application_number"] = ""

    # 提取变更事项内容
    change_items_match = re.search(r"变更事项[：:]*\s*(.+?)(?:申请人|补正|国家知识产权局|\n|$)", text_no_space, re.DOTALL)
    if change_items_match:
        items = change_items_match.group(1).strip()
        items = items.replace("\n", "").replace("\r", "").replace("\t", "")
        info["change_items"] = items
    else:
        info["change_items"] = ""

    return info


def extract_trademark_generic_notification_info(text_no_space):
    """从商标通用通知书中提取信息（适用于无专用提取函数的商标通知书类型）。

    申请号的提取采用三步降级策略：
      1. 匹配"申请号："格式
      2. 匹配"商标：+7-8位数字"格式
      3. 匹配任意7-8位纯数字

    申请人提取时过滤长度≤2的短文本，避免误匹配。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含以下键：
            - trademark_application_number (str): 商标申请号
            - applicant (str): 申请人
    """
    info = {}

    # 申请号提取：三步降级策略
    # 1. 标准"申请号："格式
    app_num_match = re.search(r"申请号[：:]\s*(\d+)", text_no_space)
    if not app_num_match:
        # 2. "商标："+7-8位数字格式
        app_num_match = re.search(r"商标[：:]*\s*(\d{7,8})", text_no_space)
    if not app_num_match:
        # 3. 任意7-8位纯数字（兜底）
        app_num_match = re.search(r"(\d{7,8})", text_no_space)
    if app_num_match:
        info["trademark_application_number"] = app_num_match.group(1)
    else:
        info["trademark_application_number"] = ""

    # 申请人提取：到多个可能的结束关键词之一，过滤短文本避免误匹配
    applicant_match = re.search(r"申请人[：:](.*?)(?:商标|代理|地址|缴费|评审|受理|编号|日期)", text_no_space, re.DOTALL)
    if applicant_match:
        applicants_text = applicant_match.group(1).strip()
        applicants = re.split(r"[、，,；;\n]", applicants_text)
        applicants = [a.strip() for a in applicants if a.strip() and len(a.strip()) > 2]
        info["applicant"] = "&".join(applicants) if applicants else ""
    else:
        info["applicant"] = ""

    # 提取商标类别
    info["trademark_category"] = extract_trademark_category(text_no_space)

    return info


def extract_trademark_certificate_info(text_no_space):
    """从商标注册证中提取信息。

    注册号的提取采用两步策略：
      1. 先匹配"第 X 号"格式
      2. 若失败，再匹配 7-8 位纯数字

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含以下键：
            - registration_number (str): 注册号
            - owner (str): 注册人
            - registration_date (str): 注册日期
    """
    info = {}

    # 注册号提取：先匹配"第X号"格式，失败则降级为7-8位纯数字
    reg_num_match = re.search(r"第\s*(\d+)\s*号", text_no_space)
    if reg_num_match:
        info["registration_number"] = reg_num_match.group(1)
    else:
        reg_num_match2 = re.search(r"(\d{7,8})", text_no_space)
        if reg_num_match2:
            info["registration_number"] = reg_num_match2.group(1)
        else:
            info["registration_number"] = ""

    # 注册人提取：从"注册人："到"注册人地址"之间的文本
    owner_match = re.search(
        r"注册人[：:\s]*(.*?)注册人地址", text_no_space, re.DOTALL
    )
    if owner_match:
        owners_text = owner_match.group(1).strip()
        owners = re.split(r"[、，,；;\n]", owners_text)
        # 过滤长度≤2的短文本
        owners = [o.strip() for o in owners if o.strip() and len(o.strip()) > 2]
        info["owner"] = "&".join(owners) if owners else ""
    else:
        info["owner"] = ""

    # 注册日期提取：从"注册日期："到"有效期"之间的文本
    date_match = re.search(
        r"注册日期[：:\s]*(.*?)有效期", text_no_space, re.DOTALL
    )
    if date_match:
        date_text = date_match.group(1).strip()
        # 去除末尾可能残留的"至"字和空格
        date_text = re.sub(r"[至\s]+$", "", date_text)
        info["registration_date"] = date_text
    else:
        info["registration_date"] = ""

    # 提取国际分类（注册类别）
    info["registration_category"] = extract_trademark_registration_category(text_no_space)

    return info


def extract_trademark_application_date(text_no_space):
    # 提取商标申请日期
    pattern = r"申请日期[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    match = re.search(pattern, text_no_space)
    if match:
        year = match.group(1)
        month = match.group(2).zfill(2)
        day = match.group(3).zfill(2)
        return f"{year}年{month}月{day}日"
    return ""


def extract_trademark_category(text_no_space):
    # 提取商标类别，格式为"类别：第X类"
    pattern = r"类别[：:]\s*(第\d+类)"
    match = re.search(pattern, text_no_space)
    if match:
        return match.group(1)
    return ""


def extract_trademark_dispatch_number(text_no_space):
    """从商标通知书PDF文本中提取发文编号。

    支持两种发文编号格式：
      1. TMZC格式："TMZC+商标申请号+类型代码+流水号"
         例如：TMZC73055497ZCSL01、TMZC73055497CSGG
      2. BHFS格式（驳回后复审成功）："BHFS+复审流水号+CSGG+公告流水号"
         例如：BHFS20240000151499CSGG01

    优先匹配TMZC格式，未匹配到时再尝试BHFS格式。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        str: 提取到的发文编号；未找到返回空字符串
    """
    # TMZC格式：TMZC+7-8位申请号+类型代码(ZCSL/JFTZ/BFBH/CSGG/BHTZ)+可选流水号
    pattern_tmzc = r"(TMZC\d{7,8}(?:ZCSL|JFTZ|BFBH|CSGG|BHTZ)\d*)"
    match = re.search(pattern_tmzc, text_no_space)
    if match:
        return match.group(1)

    # TMBG格式：商标变更发文编号，TMBG+申请号+BGBZ+流水号
    pattern_tmbg = r"(TMBG\d+BGBZ\d+)"
    match = re.search(pattern_tmbg, text_no_space)
    if match:
        return match.group(1)

    # BHFS格式：驳回后复审成功的发文编号，BHFS+复审流水号+CSGG+公告流水号
    pattern_bhfs = r"(BHFS\d+CSGG\d+)"
    match = re.search(pattern_bhfs, text_no_space)
    if match:
        return match.group(1)

    return ""


def validate_trademark_dispatch_number(dispatch_number, notification_type):
    """验证商标通知书发文编号是否符合对应通知书类型的格式规则。

    支持两种发文编号格式的验证：

    TMZC格式验证规则：
      - 商标注册申请受理通知书: TMZC+申请号+ZCSL+流水号
      - 商标注册申请缴费通知书: TMZC+申请号+JFTZ+流水号
      - 商标部分驳回通知书: TMZC+申请号+BFBH+流水号
      - 商标注册申请初步审定公告通知书: TMZC+申请号+CSGG（无流水号）
      - 商标驳回通知书: TMZC+申请号+BHTZ+流水号

    BHFS格式验证规则（驳回后复审成功）：
      - 商标注册申请初步审定公告通知书: BHFS+复审流水号+CSGG+公告流水号

    Args:
        dispatch_number (str): 待验证的发文编号
        notification_type (str): 通知书类型名称

    Returns:
        bool: 验证通过返回 True，验证失败返回 False
    """
    if not dispatch_number or not notification_type:
        return False

    # ===== BHFS格式验证 =====
    if dispatch_number.startswith("BHFS"):
        rule = TRADEMARK_DISPATCH_NUMBER_BHFS_RULES.get(notification_type)
        if not rule:
            return False
        type_code = rule["type_code"]
        has_serial = rule["has_serial"]
        # 定位类型代码在发文编号中的位置
        type_code_pos = dispatch_number.find(type_code)
        if type_code_pos == -1:
            return False
        # 提取BHFS和类型代码之间的复审流水号部分，验证是否为纯数字
        review_serial_part = dispatch_number[len("BHFS"):type_code_pos]
        if not re.match(r"^\d+$", review_serial_part):
            return False
        # 提取类型代码之后的部分
        after_type_code = dispatch_number[type_code_pos + len(type_code):]
        if has_serial:
            # 需要有流水号，验证是否为纯数字
            if not re.match(r"^\d+$", after_type_code):
                return False
        else:
            # 不应有流水号，类型代码后应为空
            if after_type_code:
                return False
        return True

    # ===== TMBG格式验证（商标变更） =====
    if dispatch_number.startswith("TMBG"):
        rule = TRADEMARK_DISPATCH_NUMBER_RULES.get(notification_type)
        if not rule:
            # 无对应规则时默认通过（变更类通知书可能不在规则表中）
            return True
        type_code = rule["prefix"]
        has_serial = rule["has_serial"]
        # 定位类型代码位置
        type_code_pos = dispatch_number.find(type_code)
        if type_code_pos == -1:
            return False
        # 提取TMBG和类型代码之间的变更申请号部分，验证是否为纯数字
        change_app_number_part = dispatch_number[len("TMBG"):type_code_pos]
        if not re.match(r"^\d+$", change_app_number_part):
            return False
        # 提取类型代码之后的部分
        after_type_code = dispatch_number[type_code_pos + len(type_code):]
        if has_serial:
            if not re.match(r"^\d+$", after_type_code):
                return False
        else:
            if after_type_code:
                return False
        return True

    # ===== TMZC格式验证（默认格式） =====
    rule = TRADEMARK_DISPATCH_NUMBER_RULES.get(notification_type)
    if not rule:
        # 无对应规则时默认通过
        return True

    expected_prefix = "TMZC"
    if not dispatch_number.startswith(expected_prefix):
        return False

    type_code = rule["prefix"]
    has_serial = rule["has_serial"]

    # 定位类型代码在发文编号中的位置
    type_code_pos = dispatch_number.find(type_code)
    if type_code_pos == -1:
        return False

    # 提取TMZC和类型代码之间的申请号部分，验证是否为7-8位数字
    app_number_part = dispatch_number[len(expected_prefix):type_code_pos]
    if not re.match(r"^\d{7,8}$", app_number_part):
        return False

    # 提取类型代码之后的部分
    after_type_code = dispatch_number[type_code_pos + len(type_code):]
    if has_serial:
        # 需要有流水号，验证是否为纯数字
        if not re.match(r"^\d+$", after_type_code):
            return False
    else:
        # 不应有流水号，类型代码后应为空
        if after_type_code:
            return False

    return True


def extract_trademark_review_agent(text_no_space):
    # 委托代理人提取：两步降级策略
    # 第一步：提取到换行或末尾结束
    pattern = r"委托代理人[：:](.*?)(?:\n|$)"
    match = re.search(pattern, text_no_space)
    if match:
        agent = match.group(1).strip()
        agent = agent.replace("\n", "").replace("\r", "").replace("\t", "")
        if agent:
            return agent
    # 第二步降级：提取到"商标/复审/决定/地址/评审"等关键词结束
    pattern2 = r"委托代理人[：:](.*?)(?:商标|复审|决定|地址|评审)"
    match = re.search(pattern2, text_no_space, re.DOTALL)
    if match:
        agent = match.group(1).strip()
        agent = agent.replace("\n", "").replace("\r", "").replace("\t", "")
        return agent
    return ""


def extract_trademark_registration_category(text_no_space):
    # 从商标注册证中提取国际分类号，格式为"国际分类：X"
    pattern = r"国际分类[：:]\s*(\d+)"
    match = re.search(pattern, text_no_space)
    if match:
        return f"第{match.group(1)}类"
    return ""


def extract_software_agent(text_no_space):
    # 提取软著代理人，到多个可能的结束关键词之一
    pattern = r"代理人[：:](.*?)(?:登记类型|软件名称|著作权人|权利取得方式|权利范围|登记号|证书号|\n|$)"
    match = re.search(pattern, text_no_space, re.DOTALL)
    if match:
        agent = match.group(1).strip()
        agent = agent.replace("\n", "").replace("\r", "").replace("\t", "")
        if agent:
            return agent
    return ""


def extract_software_acceptance_date(text_no_space):
    # 提取软著受理日期：取文本中最后一个匹配的日期
    # 因为受理通知书中可能存在多个日期，最后一个通常是受理日期
    pattern = r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    matches = re.findall(pattern, text_no_space)
    if matches:
        year, month, day = matches[-1]  # 取最后一个日期
        return f"{year}年{month.zfill(2)}月{day.zfill(2)}日"
    return ""


def extract_software_right_acquisition_method(text_no_space):
    # 提取权利取得方式，到多个可能的结束关键词之一
    pattern = r"权利取得方式[：:](.*?)(?:权利范围|登记号|证书号|\n|$)"
    match = re.search(pattern, text_no_space, re.DOTALL)
    if match:
        method = match.group(1).strip()
        method = method.replace("\n", "").replace("\r", "").replace("\t", "")
        if method:
            return method
    return ""


def extract_software_certificate_date(text_no_space):
    # 提取软著证书日期：取文本中最后一个匹配的日期
    # 证书中文末尾的日期通常是发证日期
    pattern = r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
    matches = re.findall(pattern, text_no_space)
    if matches:
        year, month, day = matches[-1]  # 取最后一个日期
        return f"{year}年{month.zfill(2)}月{day.zfill(2)}日"
    return ""


def extract_trademark_application_form_info(text_no_space):
    """从商标注册申请书中提取信息。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含以下键：
            - agent_number (str): 代理文号
            - applicant (str): 申请人（中文）
    """
    info = {}

    # 提取代理文号
    agent_match = re.search(r"代理文号[：:]\s*(\S+)", text_no_space)
    if agent_match:
        info["agent_number"] = agent_match.group(1)
    else:
        info["agent_number"] = ""

    # 提取中文申请人名称：从"申请人名称（中文）："到"申请人名称（英文）"或"统一社会信用代码"之间
    applicant_match = re.search(
        r"申请人名称[（(]中文[）)][：:](.*?)(?:申请人名称[（(]英文|统一社会信用代码)",
        text_no_space,
        re.DOTALL,
    )
    if applicant_match:
        applicants_text = applicant_match.group(1).strip()
        applicants_text = applicants_text.replace("\n", "").replace("\r", "")
        applicants = re.split(r"[、，,；;]", applicants_text)
        applicants = [a.strip() for a in applicants if a.strip()]
        info["applicant"] = "&".join(applicants) if applicants else ""
    else:
        info["applicant"] = ""

    return info


def extract_software_acceptance_info(text_no_space):
    """从软著受理通知书中提取信息。

    受理号格式为"YYYYR11SXXXXXXX"（如 2023R11S1234567）。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含以下键：
            - software_name (str): 软件名称
            - applicant (str): 申请人
            - acceptance_number (str): 受理号
            - agent (str): 软著代理
            - acceptance_date (str): 受理日期
    """
    info = {}

    # 提取软件名称：从"软件名称："到"登记类型："之间的文本
    software_name_match = re.search(
        r"软件名称[：:](.*?)登记类型[：:]", text_no_space, re.DOTALL
    )
    if software_name_match:
        name = software_name_match.group(1).strip()
        name = name.replace("\n", "").replace("\r", "").replace("\t", "")
        info["software_name"] = name
    else:
        info["software_name"] = ""

    # 提取申请人：从"申请人："到"代理人："之间的文本
    applicant_match = re.search(
        r"申请人[：:](.*?)代理人[：:]", text_no_space, re.DOTALL
    )
    if applicant_match:
        applicants_text = applicant_match.group(1).strip()
        applicants_text = applicants_text.replace("\n", "").replace("\r", "")
        applicants = re.split(r"[、，,；;]", applicants_text)
        applicants = [a.strip() for a in applicants if a.strip()]
        info["applicant"] = "&".join(applicants)
    else:
        info["applicant"] = ""

    # 提取受理号：格式为YYYYR11SXXXXXXX
    acceptance_match = re.search(r"(\d{4}R11S\d{7})", text_no_space)
    if acceptance_match:
        info["acceptance_number"] = acceptance_match.group(1)
    else:
        info["acceptance_number"] = ""

    # 提取代理人和受理日期
    info["agent"] = extract_software_agent(text_no_space)
    info["acceptance_date"] = extract_software_acceptance_date(text_no_space)

    return info


def extract_software_certificate_info(text_no_space):
    """从软著证书中提取信息。

    证书号格式为"软著登字第XXXXXXX号"。
    登记号格式为"YYYYYSRXXXXXXX"（如 2023SR1234567）。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本

    Returns:
        dict: 包含以下键：
            - certificate_number (str): 证书号
            - software_name (str): 软件名称
            - owner (str): 著作权人
            - software_registration_number (str): 登记号
            - right_acquisition_method (str): 权利取得方式
            - certificate_date (str): 证书日期
    """
    info = {}

    # 提取证书号：格式为"软著登字第XXXXXXX号"
    cert_num_match = re.search(r"软著登字第(\d+)号", text_no_space)
    if cert_num_match:
        info["certificate_number"] = f"软著登字第{cert_num_match.group(1)}号"
    else:
        info["certificate_number"] = ""

    # 提取软件名称：从"软件名称："到"著作权人"或"权利取得方式"之间的文本
    software_name_match = re.search(
        r"软件名称[：:](.*?)(?:著作权人|权利取得方式)", text_no_space, re.DOTALL
    )
    if software_name_match:
        name = software_name_match.group(1).strip()
        name = name.replace("\n", "").replace("\r", "").replace("\t", "")
        info["software_name"] = name
    else:
        info["software_name"] = ""

    # 提取著作权人：从"著作权人："到"权利取得方式/权利范围/登记号"之间的文本
    owner_match = re.search(
        r"著作权人[：:](.*?)(?:权利取得方式|权利范围|登记号)", text_no_space, re.DOTALL
    )
    if owner_match:
        owners_text = owner_match.group(1).strip()
        owners_text = owners_text.replace("\n", "").replace("\r", "")
        owners = re.split(r"[、，,；;]", owners_text)
        owners = [o.strip() for o in owners if o.strip()]
        info["owner"] = "&".join(owners)
    else:
        info["owner"] = ""

    # 提取登记号：格式为YYYYSRXXXXXXX
    reg_num_match = re.search(r"(\d{4}SR\d+)", text_no_space)
    if reg_num_match:
        info["software_registration_number"] = reg_num_match.group(1)
    else:
        info["software_registration_number"] = ""

    # 提取权利取得方式和证书日期
    info["right_acquisition_method"] = extract_software_right_acquisition_method(text_no_space)
    info["certificate_date"] = extract_software_certificate_date(text_no_space)

    return info


def extract_dispatch_date(dispatch_number):
    """从发文序号中提取发文日期。

    发文序号的前 8 位为日期编码（YYYYMMDD），如 2023121500001234
    对应 2023年12月15日。

    Args:
        dispatch_number (str): 16 位发文序号

    Returns:
        str: 格式化的发文日期（如"2023年12月15日"）；
             无法解析时返回原始 8 位字符串；序号不足 8 位返回空字符串
    """
    if dispatch_number and len(dispatch_number) >= 8:
        # 取前8位作为日期编码（YYYYMMDD）
        date_str = dispatch_number[:8]
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            # 验证月份和日期的合理性
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year}年{month:02d}月{day:02d}日"
        except ValueError:
            # 解析失败时返回原始8位字符串
            return date_str
    return ""


def process_patent_notification(text_no_space, text, notification_names):
    """处理专利通知书，提取所有相关字段信息。

    特殊处理：若仅有"专利申请受理通知书"一种通知书，
    则从"申请人"字段提取专利权人（受理阶段尚无专利权人概念）。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本
        text (str): PDF 首页原始文本（保留空格）
        notification_names (list[str]): 匹配到的通知书名称列表

    Returns:
        dict: 解析结果字典，包含以下键：
            - type (str): 固定为"专利通知书"
            - patent_number (str): 专利号
            - dispatch_number (str): 发文序号
            - patent_notification_name (str): 通知书名称（多个以"&"连接）
            - patent_owner (str): 专利权人
            - invention_name (str): 发明创造名称
            - application_date (str): 申请日期
            - inventors (str): 发明人
            - applicant_at_filing (str): 受理时申请人
    """
    patent_number = extract_patent_number(text_no_space)
    dispatch_number = extract_dispatch_number(text_no_space)
    # 从发文序号前8位提取紧凑日期格式（YYYYMMDD），用于文件名
    dispatch_date_compact = dispatch_number[:8] if dispatch_number and len(dispatch_number) >= 8 else ""
    # 多个通知书名称以"&"连接
    patent_notification_name = "&".join(notification_names)

    # 特殊处理：若仅有"专利申请受理通知书"，则从"申请人"字段提取
    # 因为受理阶段尚无"专利权人"概念，只有"申请人"
    if "专利申请受理通知书" in notification_names and len(notification_names) == 1:
        patent_owner = extract_applicant_for_acceptance(text_no_space)
        applicant_at_filing = patent_owner
    else:
        patent_owner = extract_patent_owner_notification(text_no_space)
        applicant_at_filing = ""

    invention_name = extract_invention_name(text_no_space)
    application_date = extract_application_date(text_no_space)
    inventors = extract_inventors(text_no_space)

    # 对受理通知书的补充处理：确保申请人和发明人字段有值
    if "专利申请受理通知书" in notification_names and len(notification_names) == 1:
        if not applicant_at_filing:
            applicant_at_filing = extract_applicant_for_acceptance(text_no_space)
        if not inventors:
            inventors = extract_inventors(text_no_space)

    return {
        "type": "专利通知书",
        "patent_number": patent_number,
        "dispatch_number": dispatch_number,
        "dispatch_date_compact": dispatch_date_compact,
        "patent_notification_name": patent_notification_name,
        "patent_owner": patent_owner,
        "invention_name": invention_name,
        "application_date": application_date,
        "inventors": inventors,
        "applicant_at_filing": applicant_at_filing,
    }


def process_patent_certificate(text_no_space, text, cert_name):
    """处理专利证书，提取所有相关字段信息。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本
        text (str): PDF 首页原始文本（保留空格）
        cert_name (str): 证书名称（如"发明专利证书"、"实用新型专利证书"等）

    Returns:
        dict: 解析结果字典，包含以下键：
            - type (str): 固定为"专利证书"
            - patent_number (str): 专利号
            - patent_certificate_name (str): 证书名称
            - patent_owner (str): 专利权人
            - announcement_number (str): 授权公告号
            - announcement_date (str): 授权公告日期（中文格式）
            - announcement_date_compact (str): 授权公告日期（紧凑格式，如"20231215"）
            - invention_name (str): 发明创造名称
    """
    patent_number = extract_patent_number(text_no_space)
    patent_owner = extract_patent_owner_certificate(text_no_space)
    announcement_number = extract_announcement_number(text_no_space)
    announcement_date = extract_announcement_date(text_no_space)
    # 将中文日期压缩为紧凑格式，用于文件名
    announcement_date_compact = _compact_chinese_date(announcement_date)
    invention_name = extract_invention_name(text_no_space)

    return {
        "type": "专利证书",
        "patent_number": patent_number,
        "patent_certificate_name": cert_name,
        "patent_owner": patent_owner,
        "announcement_number": announcement_number,
        "announcement_date": announcement_date,
        "announcement_date_compact": announcement_date_compact,
        "invention_name": invention_name,
    }


def process_patent_register_copy(text_no_space, text):
    patent_number = extract_patent_number(text_no_space)
    patent_owner = extract_patent_owner_register(text_no_space)
    invention_name = extract_invention_name(text_no_space)
    application_date = extract_application_date(text_no_space)
    inventors = extract_inventors(text_no_space)
    certificate_number = extract_certificate_number_register(text_no_space)
    publication_date = extract_publication_date(text_no_space)
    grant_date = extract_grant_date(text_no_space)
    original_patent_owner = extract_original_patent_owner(text_no_space)
    current_patent_owner = extract_current_patent_owner_register(text_no_space)
    bibliographic_change_date = extract_bibliographic_change_date(text_no_space)
    annual_fee_info = extract_annual_fee_info(text_no_space)
    # 提取国家知识产权局落款日期及其紧凑格式
    cnipa_date = extract_cnipa_date(text_no_space)
    cnipa_date_compact = _compact_chinese_date(cnipa_date)
    register_status = extract_register_status(text_no_space)

    return {
        "type": "专利登记簿副本",
        "patent_number": patent_number,
        "patent_owner": patent_owner,
        "invention_name": invention_name,
        "application_date": application_date,
        "inventors": inventors,
        "certificate_number": certificate_number,
        "publication_date": publication_date,
        "grant_date": grant_date,
        "original_patent_owner": original_patent_owner,
        "current_patent_owner_register": current_patent_owner,
        "bibliographic_change_date": bibliographic_change_date,
        "annual_fee_info": annual_fee_info,
        "cnipa_date": cnipa_date,
        "cnipa_date_compact": cnipa_date_compact,
        "register_status": register_status,
    }


def process_trademark_file(text_no_space, text, trademark_type):
    """处理商标文件，根据子类型分发到对应的提取函数。

    分发逻辑：
      - 通知书类型（在 TRADEMARK_NOTIFICATION_TYPES 中）→ 按具体类型选择专用提取函数
      - 续展/变更/转让证明 → 使用通用通知书提取函数
      - 商标注册证 → 使用注册证专用提取函数
      - 商标注册申请书 → 使用申请书专用提取函数

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本
        text (str): PDF 首页原始文本（保留空格）
        trademark_type (str): 商标子类型名称

    Returns:
        dict | None: 解析结果字典；无法处理时返回 None
    """
    # ===== 通知书类型处理 =====
    if trademark_type in TRADEMARK_NOTIFICATION_TYPES:
        # 根据具体通知书类型选择专用提取函数
        if trademark_type == "商标注册申请缴费通知书":
            info = extract_trademark_payment_info(text_no_space)
        elif trademark_type == "商标注册申请受理通知书":
            info = extract_trademark_acceptance_info(text_no_space, text)
        elif trademark_type in ("商标驳回复审决定书",):
            info = extract_trademark_review_decision_info(text_no_space)
        elif trademark_type == "商标变更申请补正通知书":
            info = extract_trademark_change_correction_info(text_no_space)
        else:
            # 其他通知书类型使用通用提取函数
            info = extract_trademark_generic_notification_info(text_no_space)

        # 提取并验证发文编号
        dispatch_number = extract_trademark_dispatch_number(text_no_space)
        if dispatch_number:
            is_valid = validate_trademark_dispatch_number(dispatch_number, trademark_type)
            if not is_valid:
                logger.warning(f"商标发文编号格式验证失败: {dispatch_number} (类型: {trademark_type})")

        return {
            "type": "商标通知书",
            "trademark_notification_name": trademark_type,
            "trademark_application_number": info.get(
                "trademark_application_number", ""
            ),
            "applicant": info.get("applicant", ""),
            "application_date": info.get("application_date", ""),
            "trademark_category": info.get("trademark_category", ""),
            "review_agent": info.get("review_agent", ""),
            "trademark_dispatch_number": dispatch_number,
            "change_application_number": info.get("change_application_number", ""),
            "change_items": info.get("change_items", ""),
        }
    # ===== 续展/变更/转让证明处理 =====
    elif trademark_type in ("商标续展注册证明", "商标变更核准证明", "商标转让核准证明"):
        info = extract_trademark_generic_notification_info(text_no_space)
        dispatch_number = extract_trademark_dispatch_number(text_no_space)
        return {
            "type": "商标通知书",
            "trademark_notification_name": trademark_type,
            "trademark_application_number": info.get(
                "trademark_application_number", ""
            ),
            "applicant": info.get("applicant", ""),
            "application_date": info.get("application_date", ""),
            "trademark_category": info.get("trademark_category", ""),
            "review_agent": info.get("review_agent", ""),
            "trademark_dispatch_number": dispatch_number,
        }
    # ===== 商标注册证处理 =====
    elif trademark_type == "商标注册证":
        info = extract_trademark_certificate_info(text_no_space)
        return {
            "type": "商标注册证",
            "registration_number": info.get("registration_number", ""),
            "registration_date": info.get("registration_date", ""),
            "owner": info.get("owner", ""),
            "registration_category": info.get("registration_category", ""),
        }
    # ===== 商标注册申请书处理 =====
    elif trademark_type == "商标注册申请书":
        info = extract_trademark_application_form_info(text_no_space)
        return {
            "type": "商标注册申请书",
            "agent_number": info.get("agent_number", ""),
            "applicant": info.get("applicant", ""),
        }
    return None


def process_software_file(text_no_space, text, software_type):
    """处理软著文件，根据子类型分发到对应的提取函数。

    Args:
        text_no_space (str): 去除空格后的 PDF 首页文本
        text (str): PDF 首页原始文本
        software_type (str): 软著子类型名称

    Returns:
        dict | None: 解析结果字典；无法处理时返回 None
    """
    if software_type == "软著受理通知书":
        info = extract_software_acceptance_info(text_no_space)
        return {
            "type": "软著受理通知书",
            "acceptance_number": info.get("acceptance_number", ""),
            "software_name": info.get("software_name", ""),
            "applicant": info.get("applicant", ""),
            "agent": info.get("agent", ""),
            "acceptance_date": info.get("acceptance_date", ""),
        }
    elif software_type == "软著证书":
        info = extract_software_certificate_info(text_no_space)
        return {
            "type": "软著证书",
            "software_registration_number": info.get("software_registration_number", ""),
            "software_name": info.get("software_name", ""),
            "certificate_number": info.get("certificate_number", ""),
            "owner": info.get("owner", ""),
            "right_acquisition_method": info.get("right_acquisition_method", ""),
            "certificate_date": info.get("certificate_date", ""),
        }
    return None


def generate_new_filename(main_type, sub_type, info, ext):
    """根据命名模板和解析结果生成规范化文件名。

    从 FILENAME_FORMAT_CONFIG 中获取子类型对应的命名模板，
    按模板顺序拼接各字段值，以"_"连接，最后加上扩展名。

    文件名清理规则：
      - 移除换行符、制表符
      - 将非法文件名字符（<>:"/\\|?*）替换为下划线
      - 合并连续空格

    Args:
        main_type (str): 主类型（当前未使用，预留扩展）
        sub_type (str): 子类型，用于查找命名模板
        info (dict): 解析结果字典，键为字段英文名
        ext (str): 文件扩展名（如".pdf"）

    Returns:
        str | None: 生成的文件名；若子类型无模板或所有字段值均为空则返回 None
    """
    if sub_type in FILENAME_FORMAT_CONFIG:
        config = FILENAME_FORMAT_CONFIG[sub_type]
        field_key_map = config["field_key_map"]
        defaults = config["defaults"]

        parts = []
        for field_name in defaults:
            key = field_key_map.get(field_name)
            if key is None:
                continue
            # 特殊前缀"__literal__"表示该字段为固定字面值，直接使用前缀后的文本
            if key.startswith("__literal__"):
                parts.append(key[len("__literal__"):])
            else:
                # 从解析结果中取值，仅添加非空值
                value = info.get(key, "")
                if value:
                    parts.append(value)

        # 所有字段值均为空时返回 None
        if parts:
            filename = "_".join(parts) + ext
        else:
            return None
    else:
        # 子类型无对应命名模板
        return None

    # 文件名清理：移除换行符和制表符
    if filename:
        filename = filename.replace("\n", "").replace("\r", "").replace("\t", "")
        # 将非法文件名字符替换为下划线
        invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        # 合并连续空格为单个空格
        while "  " in filename:
            filename = filename.replace("  ", " ")

    return filename


def parse_pdf(pdf_path):
    """解析单个 PDF 文件的完整入口函数。

    整合了文本读取、类型检测、字段提取、文件名生成的完整流程。

    Args:
        pdf_path (str): PDF 文件的完整路径

    Returns:
        dict: 解析结果字典，包含以下键：
            - main_type (str): 主类型（"专利文件"/"商标文件"/"软著文件"/"未知"）
            - sub_type (str | None): 子类型名称
            - info (dict): 提取的字段信息
            - new_filename (str | None): 生成的新文件名
            - original_filename (str): 原始文件名
            - dispatch_date (str): 发文日期（仅专利通知书有值）
            - notification_name (str): 通知书名称（解析成功时有值）
            - error (str | None): 错误信息，成功时为 None
    """
    # 第一步：读取PDF首页文本
    text_no_space, text, read_error = read_pdf_first_page(pdf_path)

    # PDF读取失败或为图像PDF时的错误处理
    if not text_no_space:
        if read_error:
            error_msg = f"PDF读取失败: {read_error}"
        else:
            error_msg = "暂不支持图像PDF的文本识别（所有引擎均未提取到文本）"
        return {
            "main_type": "未知",
            "sub_type": None,
            "info": {},
            "new_filename": None,
            "original_filename": os.path.basename(pdf_path),
            "dispatch_date": "",
            "error": error_msg,
        }

    # 第二步：检测主类型
    main_type = detect_main_file_type(text_no_space)
    info = None
    sub_type = None
    notification_name = ""
    dispatch_date = ""

    # 第三步：根据主类型分发到对应的子类型检测和字段提取逻辑
    if main_type == "软著文件":
        sub_type = detect_software_type(text_no_space)
        if sub_type:
            info = process_software_file(text_no_space, text, sub_type)
            # 设置通知书名称
            if sub_type == "软著受理通知书":
                notification_name = "软著受理通知书"
            elif sub_type == "软著证书":
                notification_name = "软著证书"
        else:
            return {
                "main_type": main_type,
                "sub_type": None,
                "info": {},
                "new_filename": None,
                "original_filename": os.path.basename(pdf_path),
                "dispatch_date": "",
                "error": "无法识别软著文件子类型",
            }

    elif main_type == "商标文件":
        detected_type = detect_trademark_type(text_no_space)
        if detected_type:
            info = process_trademark_file(text_no_space, text, detected_type)
            sub_type = info["type"]
            notification_name = detected_type
        else:
            return {
                "main_type": main_type,
                "sub_type": None,
                "info": {},
                "new_filename": None,
                "original_filename": os.path.basename(pdf_path),
                "dispatch_date": "",
                "error": "无法识别商标文件子类型",
            }

    elif main_type == "专利文件":
        patent_sub_type, type_info = detect_patent_type(text_no_space)
        sub_type = patent_sub_type
        if sub_type:
            if sub_type == "专利通知书":
                info = process_patent_notification(text_no_space, text, type_info)
                notification_name = info.get("patent_notification_name", "")
                # 从发文序号中提取发文日期
                dispatch_date = extract_dispatch_date(info.get("dispatch_number", ""))
            elif sub_type == "专利证书":
                info = process_patent_certificate(text_no_space, text, type_info)
                notification_name = sub_type
                # 专利证书使用授权公告日期作为发文日期
                dispatch_date = info.get("announcement_date", "")
            elif sub_type == "专利登记簿副本":
                info = process_patent_register_copy(text_no_space, text)
                notification_name = sub_type
                # 登记簿副本使用国家知识产权局落款日期
                dispatch_date = info.get("cnipa_date", "")
        else:
            return {
                "main_type": main_type,
                "sub_type": None,
                "info": {},
                "new_filename": None,
                "original_filename": os.path.basename(pdf_path),
                "dispatch_date": "",
                "error": "无法识别专利文件子类型",
            }

    else:
        return {
            "main_type": "未知",
            "sub_type": None,
            "info": {},
            "new_filename": None,
            "original_filename": os.path.basename(pdf_path),
            "dispatch_date": "",
            "error": "无法识别文件类型",
        }

    # 第四步：生成新文件名
    ext = os.path.splitext(pdf_path)[1]
    new_filename = generate_new_filename(main_type, sub_type, info, ext)

    # 第五步：组装返回结果
    result = {
        "main_type": main_type,
        "sub_type": sub_type,
        "info": info if info else {},
        "new_filename": new_filename,
        "original_filename": os.path.basename(pdf_path),
        "dispatch_date": dispatch_date,
        "notification_name": notification_name,
        "error": None,
    }

    return result
