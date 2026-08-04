"""审查文件解析模块。

支持解析中国专利审查过程中的四类文件：
1. 审查意见通知书 —— 审查员对专利申请提出的审查意见
2. 驳回决定 —— 审查员驳回专利申请的决定
3. 复审决定书 —— 复审委员会对复审请求的审查决定
4. 无效宣告请求审查决定书 —— 复审委员会对无效宣告请求的审查决定

这四类文件的结构与专利公开/公告文件（A/B/U类）完全不同，
因此使用独立的解析器处理，不与 section_parser.py 混用。

文档类型识别策略：
- 包含"无效宣告请求审查决定书"或"无效宣告请求审查决定" → 无效宣告请求审查决定书
- 包含"复审决定书"或"复审请求审查决定" → 复审决定书
- 包含"驳回决定"且不包含"复审" → 驳回决定
- 包含"审查意见通知书" → 审查意见通知书
- 以上均无 → 返回 None，表示非审查文件，应交由 section_parser 处理
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .pdf_reader import PageText

logger = logging.getLogger('patent_extractor')


# ---- 文档类型常量 ----
DOC_TYPE_OFFICE_ACTION = '审查意见通知书'
DOC_TYPE_REJECTION = '驳回决定'
DOC_TYPE_REEXAMINATION = '复审决定书'
DOC_TYPE_INVALIDATION = '无效宣告请求审查决定书'


def detect_office_action_type(text: str) -> Optional[str]:
    """从文本中检测审查文件类型。

    检测优先级（按标题特征而非正文引用）：
    1. "复审决定书" 或 "复审请求审查决定" → 复审决定书
    2. "驳回决定"（不含"复审"） → 驳回决定
    3. "审查意见通知书" → 审查意见通知书
    4. 以上均无 → None

    注意：驳回决定和复审决定书的正文中可能引用"审查意见通知书"，
    因此检测时需要优先匹配文档标题关键词，而非正文中的引用。

    Args:
        text: OCR提取的文本（通常取前3000字符即可判断）

    Returns:
        文档类型字符串，或 None（非审查文件）
    """
    # 去除空格后匹配，因为OCR可能插入多余空格
    text_ns = text.replace(' ', '')

    # 无效宣告请求审查决定书（优先级最高，因为标题同时包含"审查"和"决定"）
    if '无效宣告请求审查决定书' in text_ns or '无效宣告请求审查决定' in text_ns:
        return DOC_TYPE_INVALIDATION

    # 复审决定书（次优先级，因为正文可能包含"驳回决定"）
    if '复审决定书' in text_ns or '复审请求审查决定' in text_ns:
        return DOC_TYPE_REEXAMINATION

    # 驳回决定（优先于审查意见通知书，因为驳回决定正文可能引用"审查意见通知书"）
    # 需要区分"驳回决定"（标题）和正文中对驳回的引用
    # 关键特征：驳回决定的标题通常出现在文档开头，格式为"## 驳回决定"或"驳回决定"
    if re.search(r'(?:^|\n)\s*#{0,3}\s*驳\s*回\s*决\s*定', text[:3000]):
        return DOC_TYPE_REJECTION
    # 也匹配"驳 回 决 定"这种带空格的OCR变体
    if '驳回决定' in text_ns and '复审' not in text_ns:
        # 额外检查：确保"驳回决定"出现在文档标题位置（前1500字符）
        # 而非仅在正文中被引用
        if '驳回决定' in text[:1500].replace(' ', ''):
            return DOC_TYPE_REJECTION

    # 审查意见通知书
    if '审查意见通知书' in text_ns:
        return DOC_TYPE_OFFICE_ACTION

    return None


@dataclass
class OfficeActionInfo:
    """审查文件信息结构体。

    存储从审查意见通知书、驳回决定、复审决定书中提取的结构化信息。

    Attributes:
        doc_type: 文档类型（审查意见通知书/驳回决定/复审决定书）
        申请号: 专利申请号
        发明创造名称: 发明/实用新型名称
        申请人: 申请人名称（审查意见通知书、驳回决定）
        复审请求人: 复审请求人名称（复审决定书）
        发文日: 文件发文日期
        发文序号: 文件发文序号
        案件编号: 案件编号（复审决定书）
        审查员: 审查员姓名（审查意见通知书、驳回决定）
        审查部门: 审查部门
        联系电话: 审查员联系电话
        合议组组长: 合议组组长（复审决定书）
        主审员: 主审员（复审决定书）
        参审员: 参审员（复审决定书）
        决定号: 决定编号（复审决定书）
        决定日: 决定日期（复审决定书）
        决定结果: 决定结果（复审决定书）
        法律依据: 法律依据（复审决定书）
        决定要点: 决定要点（复审决定书）
        审查次数: 审查意见通知书的次数（如"第一次"）
        对比文件: 对比文件列表
        结论性意见: 结论性意见（审查意见通知书）
        驳回依据: 驳回依据（驳回决定）
        针对的申请文件: 驳回决定针对的申请文件
        正文: 正文内容字典，键为章节名，值为章节内容
    """
    doc_type: str = ""
    申请号: str = ""
    发明创造名称: str = ""
    申请人: str = ""
    复审请求人: str = ""
    无效宣告请求人: str = ""
    专利权人: str = ""
    发文日: str = ""
    发文序号: str = ""
    案件编号: str = ""
    审查员: str = ""
    审查部门: str = ""
    联系电话: str = ""
    # 复审决定书特有字段
    合议组组长: str = ""
    主审员: str = ""
    参审员: str = ""
    决定号: str = ""
    决定日: str = ""
    决定结果: str = ""
    法律依据: str = ""
    决定要点: str = ""
    # 审查意见通知书特有字段
    审查次数: str = ""
    对比文件: List[Dict[str, str]] = field(default_factory=list)
    结论性意见: str = ""
    # 驳回决定特有字段
    驳回依据: str = ""
    针对的申请文件: str = ""
    # 审查意见通知书 — 首页通知事项区域原文
    通知书首页事项: str = ""
    # 驳回决定 — 首页驳回事项区域原文
    驳回决定首页事项: str = ""
    # 驳回决定 — 审查员代码
    审查员代码: str = ""
    # 复审决定书 — 首页决定简述
    复审决定首页简述: str = ""
    # 复审决定书 — 申请日
    申请日: str = ""
    # 复审决定书 — 公开日
    公开日: str = ""
    # 复审决定书 — 复审请求日
    复审请求日: str = ""
    # 复审决定书 — 国际主分类号
    国际主分类号: str = ""
    # 无效宣告请求审查决定书 — 专利号
    专利号: str = ""
    # 无效宣告请求审查决定书 — 授权公告日
    授权公告日: str = ""
    # 无效宣告请求审查决定书 — 无效宣告请求日
    无效宣告请求日: str = ""
    # 无效宣告请求审查决定书 — 国际分类号
    国际分类号: str = ""
    # 无效宣告请求审查决定书 — 首页决定简述
    无效决定首页简述: str = ""
    # 正文
    正文: Dict[str, str] = field(default_factory=dict)
    # 正文全文（清洗后）
    正文全文: str = ""


class OfficeActionParser:
    """审查文件解析器。

    负责从审查意见通知书、驳回决定、复审决定书的OCR文本中
    提取结构化信息。

    解析流程：
    1. 检测文档类型
    2. 提取首页头部信息（申请号、申请人、发文日等）
    3. 提取文档特有字段（对比文件、决定结果等）
    4. 提取正文章节内容
    5. 数据清洗与格式化
    """

    def __init__(self):
        self.pages: List[PageText] = []
        self.full_text: str = ""
        self.info = OfficeActionInfo()
        self._is_mineru_single_page: bool = False

    def parse(self, pages: List[PageText]) -> OfficeActionInfo:
        """解析审查文件，提取结构化信息。

        Args:
            pages: 按页提取的文本列表

        Returns:
            OfficeActionInfo: 解析后的审查文件信息
        """
        self.pages = pages
        self.full_text = "\n".join(p.text for p in pages)
        self.info = OfficeActionInfo()

        self._is_mineru_single_page = (
            len(pages) == 1 and pages[0].source == "mineru_ocr"
        )

        if not pages:
            logger.warning("无页面数据，无法解析审查文件")
            return self.info

        # 1. 检测文档类型
        doc_type = detect_office_action_type(self.full_text[:3000])
        if not doc_type:
            logger.warning("无法识别审查文件类型")
            return self.info
        self.info.doc_type = doc_type
        logger.info(f"审查文件类型: {doc_type}")

        # 2. 提取首页头部信息
        self._extract_header_info()

        # 3. 根据文档类型提取特有字段
        if doc_type == DOC_TYPE_OFFICE_ACTION:
            self._extract_office_action_fields()
        elif doc_type == DOC_TYPE_REJECTION:
            self._extract_rejection_fields()
        elif doc_type == DOC_TYPE_REEXAMINATION:
            self._extract_reexamination_fields()
        elif doc_type == DOC_TYPE_INVALIDATION:
            self._extract_invalidation_fields()

        # 4. 提取正文
        self._extract_body_sections()

        # 5. 数据清洗
        self._clean_data()

        logger.info(f"审查文件解析完成: 类型={doc_type}, "
                     f"申请号={self.info.申请号}, "
                     f"名称={self.info.发明创造名称}")
        return self.info

    def _extract_header_info(self):
        """提取首页头部通用信息。

        包括申请号、发明创造名称、申请人/复审请求人、发文日、发文序号等。
        这些字段在三类审查文件中都有出现。
        """
        # 搜索范围：MinerU模式取前5000字符，逐页模式取前2页
        if self._is_mineru_single_page:
            search_text = self.full_text[:5000]
        else:
            search_text = "\n".join(p.text for p in self.pages[:2])

        # 申请号
        match = re.search(r'申请号[：:]\s*([\d\.]+)', search_text)
        if not match:
            match = re.search(r'申请号或专利号[：:]\s*([\d\.]+)', search_text)
        if match:
            self.info.申请号 = match.group(1).strip()

        # 发明创造名称（支持简称"发明名称"或"实用新型名称"，以及"发明名称为xxx"格式）
        match = re.search(r'发明创造名称[：:]\s*(.+?)(?:\n|$)', search_text)
        if not match:
            match = re.search(r'发明名称[：:]\s*(.+?)(?:\n|$)', search_text)
        if not match:
            match = re.search(r'发明名称为[：:"]?\s*["\u201c]?\s*(.+?)\s*["\u201d]?(?:\n|$|的)', search_text)
        if not match:
            match = re.search(r'实用新型名称[：:]\s*(.+?)(?:\n|$)', search_text)
        if match:
            self.info.发明创造名称 = match.group(1).strip()
            # 清理 DOCX 管道分隔符残留
            self.info.发明创造名称 = re.sub(r'^[|]\s*', '', self.info.发明创造名称)
            # 如果提取到的是纯数字/申请号格式，尝试用标签前一行作为名称
            # （绝对定位 DOCX 恢复的文本可能将名称放在标签行之前）
            if re.match(r'^[\d\.]+\s*$', self.info.发明创造名称):
                label_match = re.search(
                    r'^(.+?)\n发明创造名称[：:]',
                    search_text, re.MULTILINE,
                )
                if label_match:
                    alt_name = label_match.group(1).strip()
                    if alt_name and not re.match(r'^[\d\.]+\s*$', alt_name):
                        self.info.发明创造名称 = alt_name

        # 申请人
        match = re.search(r'申请人[：:]\s*(.+?)(?:\n|$)', search_text)
        if match:
            self.info.申请人 = match.group(1).strip()

        # 复审请求人
        match = re.search(r'复审请求人[：:]\s*(.+?)(?:\n|$)', search_text)
        if match:
            self.info.复审请求人 = match.group(1).strip()

        # 无效宣告请求人（支持 DOCX 中的管道分隔符）
        match = re.search(r'无效宣告请求人[：:]\s*[|]?\s*(.+?)(?:\n|$)', search_text)
        if match:
            self.info.无效宣告请求人 = re.sub(r'[|]\s*', '', match.group(1)).strip()

        # 专利权人
        match = re.search(r'专利权人[：:]\s*[|]?\s*(.+?)(?:\n|$)', search_text)
        if match:
            self.info.专利权人 = re.sub(r'[|]\s*', '', match.group(1)).strip()

        # 发文日（支持日期与标签跨行的情况，如"发文日：\n2026年02月13日"）
        match = re.search(r'发文日[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)', search_text)
        if not match:
            match = re.search(r'发文日[：:]\s*\n?\s*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)', search_text)
        if not match:
            # 文本型PDF中，发文日和日期可能间隔多行
            match = re.search(r'发文日[：:]\s*[\s\S]{0,100}?(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)', search_text)
        if match:
            self.info.发文日 = re.sub(r'\s+', '', match.group(1))

        # 发文序号
        match = re.search(r'发文序号[：:]\s*(\d+)', search_text)
        if match:
            self.info.发文序号 = match.group(1).strip()

        # 案件编号（支持管道分隔符格式，如"案件编号： | 5W114080"）
        match = re.search(r'案件编号[：:]\s*[|]?\s*(\S+)', search_text)
        if not match:
            match = re.search(r'案件编号\s*[|]\s*(\S+)', search_text)
        if match:
            self.info.案件编号 = re.sub(r'^[|]\s*', '', match.group(1)).strip()

        # 审查员（支持带空格的格式，如"审 查 员：孔令哲"）
        match = re.search(r'审\s*查\s*员[：:]\s*([\u4e00-\u9fff]+)', search_text)
        if match:
            self.info.审查员 = match.group(1).strip()

        # 审查部门（支持带空格的格式，如"审 查 部 门：专利审查协作天津中心"）
        match = re.search(r'审\s*查\s*部\s*门[：:]\s*(.+?)(?:\n|$)', search_text)
        if match:
            self.info.审查部门 = match.group(1).strip()

        # 联系电话
        match = re.search(r'联系电话[：:]\s*([\d\-]+)', search_text)
        if match:
            self.info.联系电话 = match.group(1).strip()

        logger.info(f"头部信息: 申请号={self.info.申请号}, "
                     f"名称={self.info.发明创造名称}")

    def _extract_office_action_fields(self):
        """提取审查意见通知书特有字段。"""
        search_text = self.full_text[:8000] if self._is_mineru_single_page else self.full_text

        # 审查次数（如"第一次"、"第二次"）
        # 支持带空格的格式，如"第 一 次 审 查 意 见 通 知 书"
        match = re.search(r'(第[一二三四五六七八九十\d]+次)\s*审查意见通知书', search_text)
        if not match:
            match = re.search(r'(第\s*[一二三四五六七八九十\d]+\s*次)\s*审\s*查\s*意\s*见\s*通\s*知\s*书', search_text)
        if match:
            self.info.审查次数 = re.sub(r'\s+', '', match.group(1).strip())

        # 对比文件表格
        self._extract_comparison_documents(search_text)

        # 结论性意见
        self._extract_conclusion(search_text)

        # 提取首页通知事项区域（含编号1-9项的完整通知内容）
        self._extract_notice_items(search_text)

    def _extract_comparison_documents(self, text: str):
        """提取对比文件表格。

        对比文件表格格式：
        编号 | 文件号或名称 | 公开日期
        1   | CN214683885U | 2021-11-12
        """
        # 方式1：从HTML表格中提取（MinerU输出可能包含HTML table）
        table_rows = re.findall(
            r'<tr><td[^>]*>(\d+)</td><td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td></tr>',
            text,
        )
        if table_rows:
            for row in table_rows:
                self.info.对比文件.append({
                    '编号': row[0].strip(),
                    '文件号': row[1].strip(),
                    '公开日期': row[2].strip(),
                })
            return

        # 方式2：从纯文本中提取（格式如 "对比文件1：CN214683885U，公告日为2021年11月12日"）
        refs = re.findall(
            r'对比文件\s*(\d+)\s*[：:]\s*(CN\s*\d+\s*\w+)\s*[，,]\s*'
            r'(?:公告日|公开日)为?\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            text,
        )
        if refs:
            for ref in refs:
                self.info.对比文件.append({
                    '编号': ref[0].strip(),
                    '文件号': ref[1].strip(),
                    '公开日期': ref[2].strip(),
                })
            return

        # 方式3：从正文中的引用列表提取
        refs = re.findall(
            r'对比文件\s*(\d+)\s*[：:]\s*(CN\s*\d+\s*\w+)\s*[，,]\s*'
            r'(?:公告日|公开日)\s*(?:为\s*)?(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)',
            text,
        )
        if refs:
            for ref in refs:
                self.info.对比文件.append({
                    '编号': ref[0].strip(),
                    '文件号': re.sub(r'\s+', ' ', ref[1].strip()),
                    '公开日期': re.sub(r'\s+', '', ref[2].strip()),
                })
            return

        # 方式4：从文本型PDF正文中提取（格式如"对比文件 1（公告号：CN201702814U ，公告日：20110112）"）
        refs = re.findall(
            r'对比文件\s*(\d+)\s*[（(]\s*(?:公告号|公开号)[：:]\s*(CN\s*\d+\s*\w+)\s*[，,]\s*'
            r'(?:公告日|公开日)[：:]\s*(\d{4,8})\s*[）)]',
            text,
        )
        if refs:
            for ref in refs:
                date_str = ref[2].strip()
                # 日期格式可能是YYYYMMDD或YYYY-MM-DD，统一为YYYY年MM月DD日
                if re.match(r'^\d{8}$', date_str):
                    date_str = f"{date_str[:4]}年{date_str[4:6]}月{date_str[6:8]}日"
                self.info.对比文件.append({
                    '编号': ref[0].strip(),
                    '文件号': re.sub(r'\s+', ' ', ref[1].strip()),
                    '公开日期': date_str,
                })

    def _extract_conclusion(self, text: str):
        """提取结论性意见。

        审查意见通知书中第6项为结论性意见，包含勾选的审查结论。
        也支持文本型PDF中直接陈述的结论（如"该专利申请将被驳回"）。
        """
        # 提取"审查的结论性意见"后的勾选项
        match = re.search(
            r'审查的结论性意见[：:]?\s*\n([\s\S]+?)(?:\n\s*\d+\.|上述结论性意见)',
            text,
        )
        if match:
            conclusion_text = match.group(1).strip()
            # 提取被勾选的项目（通常以■或☑或区标记，OCR可能识别为各种字符）
            # 也提取未勾选的项目（以□标记），用于上下文
            checked_items = []
            for line in conclusion_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # 检测勾选标记：■、☑、区（OCR误识别）、√
                if re.match(r'[■☑区√]', line):
                    item = re.sub(r'^[■☑区√]\s*', '', line).strip()
                    if item:
                        checked_items.append(item)
            if checked_items:
                self.info.结论性意见 = '\n'.join(checked_items)

        # 文本型PDF：从正文中提取结论性意见
        if not self.info.结论性意见:
            # 查找"基于上述理由"或"该专利申请不能被授予专利权"等结论性表述
            match = re.search(
                r'基于上述理由[，,]\s*(.+?)(?:\n|$)',
                text,
            )
            if match:
                self.info.结论性意见 = match.group(1).strip()
            else:
                match = re.search(
                    r'(该专利申请不能被授予专利权[。，]?\s*如果申请人.+?(?:\n|$))',
                    text,
                )
                if match:
                    self.info.结论性意见 = match.group(1).strip()

    def _extract_notice_items(self, text: str):
        """提取审查意见通知书首页通知事项区域。

        审查意见通知书首页包含编号1-9的通知事项，提取此区域全文
        作为结构化信息，便于JSON/Markdown生成时展示。
        """
        # 找到"审查意见通知书"标题后的第一个编号项（如"1.应申请人"或"1.根据"）
        patterns = [
            r'(1\.\s*应申请人提出.*?审查员[：:]\s*[\u4e00-\u9fff]+.*?(?:联系电话|$)'
            r')',
            r'(1\.\s*根据专利法.*?审查员[：:]\s*[\u4e00-\u9fff]+.*?(?:联系电话|$)'
            r')',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                raw = match.group(1).strip()
                # 清理页眉页脚噪声
                raw = re.sub(r'\n\s*\d{6}\s*纸件申请.*?(?:\n|$)', '', raw)
                raw = re.sub(r'\n\s*\d{4}\.\d{2}\s*电子申请.*?(?:\n|$)', '', raw)
                raw = re.sub(r'\n\s*国家知识产权局\s*专利审查业务章.*?(?:\n|$)', '', raw)
                raw = re.sub(r'<!--\s*image\s*-->', '', raw)
                # 合并多余空行
                raw = re.sub(r'\n{3,}', '\n\n', raw)
                self.info.通知书首页事项 = raw.strip()
                logger.info(
                    f"通知书首页事项提取: {len(self.info.通知书首页事项)} 字符"
                )
                return

    def _extract_rejection_fields(self):
        """提取驳回决定特有字段。"""
        search_text = self.full_text[:8000] if self._is_mineru_single_page else self.full_text

        # 驳回依据
        match = re.search(
            r'1\.\s*根据专利法.*?决定驳回.*?驳回的依据是[；:]\s*\n([\s\S]+?)(?:\n\s*2\.|\n\s*详细的)',
            search_text,
        )
        if match:
            rejection_text = match.group(1).strip()
            # 提取被勾选的驳回依据
            checked_items = []
            for line in rejection_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if re.match(r'[■☑区√]', line):
                    item = re.sub(r'^[■☑区√]\s*', '', line).strip()
                    if item:
                        checked_items.append(item)
            if checked_items:
                self.info.驳回依据 = '\n'.join(checked_items)

        # 针对的申请文件
        match = re.search(
            r'2\.\s*本驳回决定是针对下列申请文件作出的[：:]\s*\n([\s\S]+?)(?:\n\s*3\.|\n\s*根据专利法第41条)',
            search_text,
        )
        if match:
            self.info.针对的申请文件 = match.group(1).strip()
            # 清理勾选标记
            self.info.针对的申请文件 = re.sub(r'^[■☑区√□]\s*', '', self.info.针对的申请文件, flags=re.MULTILINE)
            self.info.针对的申请文件 = self.info.针对的申请文件.strip()

        # 对比文件（驳回决定正文中也会引用对比文件）
        self._extract_comparison_documents(search_text)

        # 提取首页驳回事项区域（含编号1-3项的驳回决定首页内容）
        self._extract_rejection_front_items(search_text)

        # 审查员代码
        match = re.search(r'审查员代码[：:]\s*(\d+)', self.full_text)
        if match:
            self.info.审查员代码 = match.group(1).strip()

    def _extract_rejection_front_items(self, text: str):
        """提取驳回决定首页事项区域。

        驳回决定首页包含编号1-3的驳回决定事项，提取此区域全文。
        """
        patterns = [
            r'(1\.\s*根据专利法第38条.*?驳回的依据是[；:]\s*\n[\s\S]+?'
            r'(?:审查员[：:]|联系电话|审查部门).*?(?:$|(?=\n\s*\n)))',
            r'(1\.\s*根据专利法.*?决定驳回.*?'
            r'(?:审查员[：:]|联系电话|审查部门).*?(?:$|(?=\n\s*\n)))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                raw = match.group(1).strip()
                raw = re.sub(r'\n\s*\d{6}\s*纸件申请.*?(?:\n|$)', '', raw)
                raw = re.sub(r'\n\s*\d{4}\.\d{2}\s*电子申请.*?(?:\n|$)', '', raw)
                raw = re.sub(r'<!--\s*image\s*-->', '', raw)
                raw = re.sub(r'\n{3,}', '\n\n', raw)
                self.info.驳回决定首页事项 = raw.strip()
                logger.info(
                    f"驳回决定首页事项提取: {len(self.info.驳回决定首页事项)} 字符"
                )
                return

    def _extract_reexamination_fields(self):
        """提取复审决定书特有字段。"""
        search_text = self.full_text[:8000] if self._is_mineru_single_page else self.full_text

        # 决定号
        match = re.search(r'复审决定书\s*\n\s*[（(]\s*第\s*(\d+)\s*号\s*[）)]', search_text)
        if not match:
            match = re.search(r'复审请求审查决定\s*[（(]\s*第\s*(\d+)\s*号\s*[）)]', search_text)
        if match:
            self.info.决定号 = match.group(1).strip()

        # 决定结果（首页摘要部分）
        match = re.search(
            r'根据前置审查意见书的意见[，,]\s*(撤销|维持)\s*国家知识产权局',
            search_text,
        )
        if match:
            result1 = match.group(1).strip()
            # 检查是否驳回复审请求
            match2 = re.search(r'驳回复审请求人', search_text)
            if match2:
                self.info.决定结果 = f"{result1}驳回决定" if result1 == "撤销" else "维持驳回决定"
            else:
                self.info.决定结果 = result1

        # 检查另一种格式：□经审查，撤销...
        if not self.info.决定结果:
            match = re.search(r'[■☑区√]\s*经审查[，,]\s*(撤销|维持)', search_text)
            if match:
                self.info.决定结果 = match.group(1).strip()

        # 复审决定首页简述
        self._extract_reexamination_summary(search_text)

        # 合议组信息
        match = re.search(r'合议组组长[：:]\s*([\u4e00-\u9fff]+)', search_text)
        if match:
            self.info.合议组组长 = match.group(1).strip()

        match = re.search(r'主审员[：:]\s*([\u4e00-\u9fff]+)', search_text)
        if match:
            self.info.主审员 = match.group(1).strip()

        match = re.search(r'参审员[：:]\s*([\u4e00-\u9fff]+)', search_text)
        if match:
            self.info.参审员 = match.group(1).strip()

        # 从详情表格中提取更多信息
        self._extract_reexamination_table(search_text)

        # 对比文件
        self._extract_comparison_documents(search_text)

    def _extract_reexamination_summary(self, text: str):
        """提取复审决定书首页决定简述。

        复审决定书首页包含决定概述、决定结果勾选项以及合议组成员信息。
        提取从"经审查"开始到合议组成员信息结束的全文，
        作为结构化信息，便于 JSON/Markdown 生成时展示。
        """
        # 优先匹配"经审查，撤销/维持 ..."的总结语句，扩展到合议组信息结束
        patterns = [
            r'((?:[■☑区√]\s*)?经审查[，,]\s*(?:撤销|维持).*?(?:合议组组长[：:]|专利局复审和无效审理部))',
            r'((?:[■☑区√]\s*)?经审查[，,]\s*(?:撤销|维持).*?(?:参审员[：:].*?[\u4e00-\u9fff]+))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                raw = match.group(1).strip()
                # 清理页眉页脚噪声
                raw = re.sub(r'\n\s*\d{6}\s*纸件申请.*?(?:\n|$)', '', raw)
                raw = re.sub(r'\n\s*\d{4}\.\d{2}\s*电子申请.*?(?:\n|$)', '', raw)
                raw = re.sub(r'\n\s*国家知识产权局\s*专利审查业务章.*?(?:\n|$)', '', raw)
                raw = re.sub(r'<!--\s*image\s*-->', '', raw)
                # 合并多余空行
                raw = re.sub(r'\n{3,}', '\n\n', raw)
                self.info.复审决定首页简述 = raw.strip()
                logger.info(
                    f"复审决定首页简述提取: {len(self.info.复审决定首页简述)} 字符"
                )
                return

        # 备选方案：从前置审查受理到合议组信息的全文
        match = re.search(
            r'(根据专利法第[\d\s]+条.*?(?:合议组组长[：:]|专利局复审和无效审理部))',
            text, re.DOTALL,
        )
        if match:
            raw = match.group(1).strip()
            raw = re.sub(r'\n\s*\d{6}\s*纸件申请.*?(?:\n|$)', '', raw)
            raw = re.sub(r'\n\s*\d{4}\.\d{2}\s*电子申请.*?(?:\n|$)', '', raw)
            raw = re.sub(r'<!--\s*image\s*-->', '', raw)
            raw = re.sub(r'\n{3,}', '\n\n', raw)
            self.info.复审决定首页简述 = raw.strip()
            logger.info(
                f"复审决定首页简述(备选)提取: {len(self.info.复审决定首页简述)} 字符"
            )

    def _extract_reexamination_table(self, text: str):
        """从复审决定书的详情表格中提取信息。

        表格格式（HTML）：
        案件编号 | 第1F797010号
        决定日 | 2026年03月20日
        ...
        """
        # 从HTML表格提取
        table_rows = re.findall(
            r'<tr><td[^>]*>([^<]+)</td><td[^>]*>([^<]+)</td></tr>',
            text,
        )
        table_dict = {}
        for row in table_rows:
            key = row[0].strip()
            value = row[1].strip()
            table_dict[key] = value

        if '决定日' in table_dict and not self.info.决定日:
            self.info.决定日 = table_dict['决定日']
        if '法律依据' in table_dict:
            self.info.法律依据 = table_dict['法律依据']
        if '案件编号' in table_dict and not self.info.案件编号:
            self.info.案件编号 = table_dict['案件编号']

        # 决定要点（可能在表格的跨列行中）
        match = re.search(r'决定要点[：:]\s*(.+?)(?:\n\n|\n##|\n一、)', text, re.DOTALL)
        if match:
            self.info.决定要点 = match.group(1).strip()
            # 清理HTML标签
            self.info.决定要点 = re.sub(r'<[^>]+>', '', self.info.决定要点)
            self.info.决定要点 = re.sub(r'\s+', ' ', self.info.决定要点).strip()

        # 如果决定要点未从表格提取到，尝试从正文中提取
        if not self.info.决定要点:
            match = re.search(
                r'决定要点[：:]\s*如果.+?(?:\n\n|\n##|\n一、)',
                text, re.DOTALL,
            )
            if match:
                self.info.决定要点 = match.group(0).strip()
                self.info.决定要点 = re.sub(r'^决定要点[：:]\s*', '', self.info.决定要点)
                self.info.决定要点 = re.sub(r'<[^>]+>', '', self.info.决定要点)
                self.info.决定要点 = re.sub(r'\s+', ' ', self.info.决定要点).strip()

    def _extract_invalidation_fields(self):
        """提取无效宣告请求审查决定书特有字段。

        无效宣告请求审查决定书结构与复审决定书类似，
        但当事人为无效宣告请求人和专利权人。

        文档结构：
        - 首页：申请号/专利号、案件编号、发明创造名称、专利权人、
          无效宣告请求人、决定号、决定选项（勾选）、合议组
        - 第二页详情表格：案件编号、决定日、国际分类号、专利号、
          申请日、授权公告日、无效宣告请求日、法律依据、决定要点
        - 正文：一、案由；二、决定的理由；三、决定

        支持两种文本格式：
        - DOCX管道分隔格式：如"决定日 | 2018年05月29日"
        - PDF空格分隔格式：如"决定日 2018年05月29日"
        """
        search_text = self.full_text[:8000] if self._is_mineru_single_page else self.full_text

        # 决定号（格式如"（第35918号）"或"第35918号"，PDF可能跨行"（第 号）\n35918"）
        match = re.search(r'[（(]\s*第\s*(\d+)\s*号\s*[）)]', search_text)
        if not match:
            match = re.search(r'第\s*(\d+)\s*号\s*无效宣告', search_text)
        if not match:
            # PDF跨行格式："（第 号）\n35918"
            match = re.search(r'[（(]\s*第\s*号\s*[）)]\s*\n\s*(\d+)', search_text)
        if match:
            self.info.决定号 = match.group(1).strip()

        # 决定日（支持管道/空格分隔格式）
        match = re.search(r'决定日\s*[|:：]?\s*(\d{4}年\d{1,2}月\d{1,2}日)', search_text)
        if match:
            self.info.决定日 = match.group(1).strip()

        # 案件编号（支持管道/空格分隔格式，如"案件编号 第5W114080、5W114081号"）
        # 优先匹配"第X号"格式
        match = re.search(r'案件编号\s*[|:：]?\s*第?\s*(\S+?)号', search_text)
        if not match:
            # 尝试匹配"案件编号 | 5W114080"格式（无"第"和"号"包裹）
            match = re.search(r'案件编号\s*[|:：]\s*([A-Za-z0-9\u4e00-\u9fff]+)', search_text)
        if not match:
            # 尝试从HTML表格中提取
            match = re.search(r'案件编号\s*[|]\s*(\S+)', search_text)
        if match:
            self.info.案件编号 = match.group(1).strip()
        # 清理案件编号中的管道符残留
        self.info.案件编号 = re.sub(r'^[|]\s*', '', self.info.案件编号)
        self.info.案件编号 = re.sub(r'\s*[|]\s*$', '', self.info.案件编号)

        # 合议组信息
        match = re.search(r'合议组组长[：:]\s*[|]?\s*([\u4e00-\u9fff]+)', search_text)
        if match:
            self.info.合议组组长 = match.group(1).strip()

        match = re.search(r'主审员[：:]\s*[|]?\s*([\u4e00-\u9fff]+)', search_text)
        if match:
            self.info.主审员 = match.group(1).strip()

        match = re.search(r'参审员[：:]\s*[|]?\s*([\u4e00-\u9fff]+)', search_text)
        if match:
            self.info.参审员 = match.group(1).strip()

        # 决定要点
        match = re.search(
            r'决定要点[：:]\s*(.+?)(?:\n\n|\n一、|\n二、)',
            search_text, re.DOTALL,
        )
        if match:
            self.info.决定要点 = match.group(1).strip()
            self.info.决定要点 = re.sub(r'\s+', ' ', self.info.决定要点).strip()

        # 法律依据（支持管道/空格分隔格式）
        match = re.search(r'法律依据\s*[|:：]?\s*(.+?)(?:\n|$)', search_text)
        if match:
            self.info.法律依据 = re.sub(r'^[|]\s*', '', match.group(1)).strip()

        # 国际分类号（支持管道/空格分隔格式）
        match = re.search(r'国际分类号\s*[|:：]?\s*(.+?)(?:\n|$)', search_text)
        if match:
            self.info.国际分类号 = re.sub(r'^[|]\s*', '', match.group(1)).strip()

        # 专利号（支持管道/空格分隔格式）
        match = re.search(r'专利号\s*[|:：]?\s*([\d\.]+)', search_text)
        if match:
            self.info.专利号 = match.group(1).strip()

        # 申请日（支持管道/空格分隔格式）
        match = re.search(r'申请日\s*[|:：]?\s*(\d{4}年\d{1,2}月\d{1,2}日)', search_text)
        if match:
            self.info.申请日 = match.group(1).strip()

        # 授权公告日（支持管道/空格分隔格式）
        match = re.search(r'授权公告日\s*[|:：]?\s*(\d{4}年\d{1,2}月\d{1,2}日)', search_text)
        if match:
            self.info.授权公告日 = match.group(1).strip()

        # 无效宣告请求日（支持管道/空格分隔格式，PDF可能跨行）
        # PDF格式可能为："2017年12月25日\n无效宣告请求日\n2017年12月25日"
        match = re.search(r'无效宣告请求日\s*[|:：]?\s*(\d{4}年\d{1,2}月\d{1,2}日)', search_text)
        if not match:
            # PDF跨行格式：日期在标签下一行
            match = re.search(r'无效宣告请求日\s*[|:：]?\s*\n\s*(\d{4}年\d{1,2}月\d{1,2}日)', search_text)
        if match:
            self.info.无效宣告请求日 = match.group(1).strip()

        # 决定结果（从首页勾选项提取）
        self._extract_invalidation_result(search_text)

        # 无效决定首页简述
        self._extract_invalidation_summary(search_text)

        # 对比文件
        self._extract_comparison_documents(search_text)

    def _extract_invalidation_result(self, text: str):
        """提取无效宣告请求审查决定书的决定结果。

        首页有三个选项（勾选其中一个）：
        - 宣告专利权全部无效。
        - 宣告专利权部分无效。
        - 维持专利权有效。

        勾选标记可能是 ■、☑、√ 或 OCR 误识别的字符。
        """
        # 搜索三个选项及其勾选状态
        options = [
            (r'[■☑区√]\s*宣告专利权全部无效', '宣告专利权全部无效'),
            (r'[■☑区√]\s*宣告专利权部分无效', '宣告专利权部分无效'),
            (r'[■☑区√]\s*维持专利权有效', '维持专利权有效'),
        ]
        for pattern, result in options:
            if re.search(pattern, text):
                self.info.决定结果 = result
                return

        # 备选：从"三、决定"章节中提取决定结果
        match = re.search(
            r'三[、．.]\s*决定\s*\n([\s\S]+?)(?:\n\n|\n当事人)',
            text,
        )
        if match:
            decision_text = match.group(1).strip()
            if '维持' in decision_text and '有效' in decision_text:
                self.info.决定结果 = '维持专利权有效'
            elif '全部无效' in decision_text:
                self.info.决定结果 = '宣告专利权全部无效'
            elif '部分无效' in decision_text:
                self.info.决定结果 = '宣告专利权部分无效'

    def _extract_invalidation_summary(self, text: str):
        """提取无效宣告请求审查决定书首页决定简述。

        首页包含决定概述，格式如：
        "根据专利法第46条第1款的规定，专利复审委员会对无效宣告请求人
        就上述专利权所提出的无效宣告请求进行了审查，现决定如下：..."
        """
        patterns = [
            r'(根据专利法第46条第1款的规定.*?合议组组长[：:].*?专利复审委员会)',
            r'(根据专利法第46条第1款的规定.*?(?:参审员|专利复审委员会).*?(?:\n|$))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                raw = match.group(1).strip()
                # 清理噪声
                raw = re.sub(r'\n\s*\d{6}\s*纸件申请.*?(?:\n|$)', '', raw)
                raw = re.sub(r'\n\s*\d{4}\.\d{2}\s*电子申请.*?(?:\n|$)', '', raw)
                raw = re.sub(r'<!--\s*image\s*-->', '', raw)
                raw = re.sub(r'\n{3,}', '\n\n', raw)
                self.info.无效决定首页简述 = raw.strip()
                logger.info(
                    f"无效决定首页简述提取: {len(self.info.无效决定首页简述)} 字符"
                )
                return

    def _extract_body_sections(self):
        """提取正文章节内容。

        三类审查文件的正文结构：
        - 审查意见通知书：正文部分（审查意见详细分析）
        - 驳回决定：一、案由；二、驳回理由
        - 复审决定书：一、案由；二、决定理由（或其他章节标题）
        """
        text = self.full_text

        # 查找正文开始位置
        body_start = self._find_body_start(text)
        if body_start < 0:
            logger.warning("未找到正文开始位置")
            return

        body_text = text[body_start:]

        # 清理正文中的噪声
        body_text = self._clean_body_text(body_text)

        # 按中文数字章节标题拆分（如"一、案由"、"二、驳回理由"）
        sections = self._split_chinese_sections(body_text)

        if sections:
            self.info.正文 = sections
            logger.info(f"正文提取: {len(sections)} 个章节: {list(sections.keys())}")
        else:
            # 无法按章节拆分，将整个正文作为"正文"章节
            self.info.正文 = {'正文': body_text.strip()}
            logger.info("正文提取: 整体作为正文章节")

    def _find_body_start(self, text: str) -> int:
        """查找正文开始位置。

        正文通常以以下方式标记：
        - 审查意见通知书：以"本申请涉及"或"1.权利要求"开头
        - 驳回决定：以"本决定涉及"或"一、案由"开头
        - 复审决定书：以"一、案由"开头
        """
        # 优先查找中文数字章节标题
        patterns = [
            r'\n\s*##?\s*一[、．.]\s*案由',
            r'\n\s*一[、．.]\s*案由',
            r'\n\s*##?\s*一[、．.]',
            r'\n\s*一[、．.]',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.start() + 1  # 跳过前导换行

        # 备选：查找正文标志性开头
        body_patterns = [
            r'本申请涉及',
            r'本决定涉及',
            r'本复审请求涉及',
            r'1\.\s*权利要求\d+',
            r'根据专利法',  # 文本型PDF审查意见通知书常见开头
        ]
        for pattern in body_patterns:
            match = re.search(pattern, text)
            if match:
                return match.start()

        return -1

    def _clean_body_text(self, text: str) -> str:
        """清理正文文本中的噪声。

        包括：
        - 去除页眉（如"国家知识产权局"、"第X页"等）
        - 去除图片标记（<!-- image-->）
        - 去除HTML标签
        - 去除印章文字
        - 合并多余空行
        """
        # 去除图片标记
        text = re.sub(r'<!--\s*image\s*-->', '', text)
        # 去除HTML标签（保留内容）
        text = re.sub(r'</?table[^>]*>', '', text)
        text = re.sub(r'</?tr[^>]*>', '\n', text)
        text = re.sub(r'</?td[^>]*>', ' | ', text)
        # 去除印章文字
        text = re.sub(r'国家知识产权局\s*专利复审.*?业务章\s*\d+', '', text)
        text = re.sub(r'国家知识产权局\s*专利审查业务章\s*\d+', '', text)
        # 去除页眉
        text = re.sub(r'\n\s*国家知识产权局\s*\n', '\n', text)
        text = re.sub(r'\n\s*#{1,3}\s*国家知识产权局\s*\n', '\n', text)
        text = re.sub(r'\n\s*第\s*\d+\s*页\s*\n', '\n', text)
        # 去除页脚（审查员信息、回函地址、电子申请提示等）
        text = re.sub(r'\n\s*审\s*查\s*员[：:].*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*联系电话[：:].*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*\d{6}\s*纸件申请.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*\d{4}\.\d{2}\s*电子申请.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*审查员姓名[：:].*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\s*审查员代码[：:].*$', '', text, flags=re.MULTILINE)
        # 去除Markdown标题标记残留
        text = re.sub(r'\n\s*#{1,3}\s*$', '', text, flags=re.MULTILINE)
        # 合并多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _split_chinese_sections(self, text: str) -> Dict[str, str]:
        """按中文数字章节标题拆分正文。

        章节标题格式：
        - 一、案由
        - 二、驳回理由 / 二、决定理由
        - 三、...
        也支持带Markdown标题标记的格式：
        - ## 一、案由

        Returns:
            章节字典，键为章节标题，值为章节内容
        """
        # 匹配中文数字章节标题
        # 支持格式：一、案由 / ## 一、案由 / ### 二、决定理由
        section_pattern = re.compile(
            r'(?:^|\n)\s*#{0,3}\s*'
            r'([一二三四五六七八九十]+[、．.])'
            r'\s*(.+?)(?:\n|$)',
        )

        # 找到所有章节标题位置
        positions = []
        for match in section_pattern.finditer(text):
            title_prefix = match.group(1)  # 如"一、"
            title_name = match.group(2).strip()  # 如"案由"
            full_title = f"{title_prefix}{title_name}"
            positions.append((match.start(), full_title))

        if not positions:
            return {}

        # 按位置拆分
        result = {}
        for i, (pos, title) in enumerate(positions):
            # 当前章节的结束位置 = 下一章节的开始位置（或文本末尾）
            next_pos = positions[i + 1][0] if i + 1 < len(positions) else len(text)
            content = text[pos:next_pos].strip()
            # 去除标题行本身
            content = re.sub(r'^#{0,3}\s*[一二三四五六七八九十]+[、．.]\s*.+?(?:\n|$)', '', content, count=1)
            content = content.strip()
            # 清理内容
            content = re.sub(r'\n{3,}', '\n\n', content)
            result[title] = content

        return result

    def _clean_data(self):
        """数据清洗：修正OCR错误、统一格式。"""
        # 修正申请号格式（去除多余空格和点号）
        self.info.申请号 = re.sub(r'\s+', '', self.info.申请号)

        # 修正发明创造名称中的OCR错误
        corrections = {
            '饲科': '饲料',
            '冲止': '冲压',
            '冷印': '冷却',
        }
        for wrong, correct in corrections.items():
            if wrong in self.info.发明创造名称:
                self.info.发明创造名称 = self.info.发明创造名称.replace(wrong, correct)

        # 清洗正文中的OCR常见错误
        for key, content in self.info.正文.items():
            content = self._clean_ocr_in_body(content)
            self.info.正文[key] = content

    def _clean_ocr_in_body(self, text: str) -> str:
        """清洗正文中的OCR常见错误。

        优化段落合并逻辑：在合并跨行文本时，检测段落边界，
        避免将不同语义段落错误合并。段落边界检测规则：
        1. 空行始终作为段落分隔
        2. 以缩进开头的行视为新段落起始
        3. 以编号（如"1."、"（一）"）开头的行视为新段落起始
        4. 句号后换行且下一行以段落起始词开头的，保留分段
        """
        if not text:
            return text

        # 修正常见OCR错误
        corrections = {
            '说朋书': '说明书',
            '权刺要求': '权利要求',
            '权禾要求': '权利要求',
            '摘耍': '摘要',
            '技术领城': '技术领域',
            '具休实施': '具体实施',
            '具体买施': '具体实施',
            '背最技术': '背景技术',
            '实用新型内客': '实用新型内容',
            '发明内客': '发明内容',
            '驱回': '驳回',
            '撒销': '撤销',
            '审和香格事理部': '复审和无效审理部',
            '专利复自无效事登业务章': '专利复审无效审理业务章',
        }
        for wrong, correct in corrections.items():
            if wrong in text:
                text = text.replace(wrong, correct)

        # 段落起始标记：以这些模式开头的行通常是一个新段落的开始
        paragraph_start_re = re.compile(
            r'^(?:'
            r'\s{2,}|'  # 缩进开头的行（2个及以上空格）
            r'[（(]\s*[一二三四五六七八九十\d]+\s*[）)]|'  # 编号列表 (一) (1)
            r'\d+[.．、]|'  # 数字编号 1. 2、
            r'根据|基于|针对|关于|此外|另外|同时|因此|所以|综上|'
            r'首先|其次|再次|最后|'
            r'当|如果|假设|若|'
            r'权利要求|对比文件|实施例'
            r')'
        )

        # 清理段落内换行（合并跨行文本为连续段落）
        # 但保留段落间的空行分隔和语义段落边界
        lines = text.split('\n')
        result = []
        buffer = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                # 空行：先保存缓冲区内容，再添加空行
                if buffer:
                    result.append(''.join(buffer))
                    buffer = []
                result.append('')
            elif buffer and paragraph_start_re.match(stripped):
                # 当前行匹配段落起始标记，保存缓冲区内容并开始新段落
                result.append(''.join(buffer))
                buffer = [stripped]
            else:
                buffer.append(stripped)
        if buffer:
            result.append(''.join(buffer))

        # 重新组合，去除连续空行
        text = '\n'.join(result)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
