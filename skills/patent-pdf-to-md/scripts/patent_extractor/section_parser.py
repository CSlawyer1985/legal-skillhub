"""章节识别与拆分模块。

基于页级别的页眉检测，识别专利类型、拆分主章节、提取著录项目字段，
并在说明书内部进一步拆分子章节。

支持两种输入模式：
1. 逐页文本（pdfplumber/fitz/Tesseract OCR）：通过页眉检测章节
2. 整篇 Markdown（MinerU OCR）：通过全文搜索章节标题
"""

import logging  # 日志模块，用于记录解析过程中的调试和警告信息
import re  # 正则表达式模块，用于文本模式匹配和提取
from dataclasses import dataclass, field  # 数据类装饰器，用于定义结构化的数据容器
from typing import Dict, List, Optional, Tuple  # 类型注解，提高代码可读性和类型安全性

from .pdf_reader import PageText  # 页面文本数据类，包含每页的文本内容、页码、来源等信息

# 获取当前模块的日志记录器，日志名称为 'patent_extractor'
logger = logging.getLogger('patent_extractor')


# 主章节页眉模式列表，用于逐页PDF文本的章节检测
# 每个元素为 (章节键名, 正则表达式) 的元组
# 正则中 \s* 用于匹配可能存在的空格（OCR识别时字符间可能有间距）
SECTION_HEADER_PATTERNS = [
    ('bibliographic', r'\(19\)国家知识产权局'),  # 著录项目页：以"(19)国家知识产权局"标识
    ('claims',        r'权\s*利\s*要\s*求\s*书'),  # 权利要求书章节
    ('description',   r'说\s*明\s*书(?!\s*附\s*图)'),   # 说明书章节（使用负向前瞻排除"说明书附图"）
    ('drawings',      r'说\s*明\s*书\s*附\s*图'),  # 说明书附图章节
]

# MinerU Markdown 中的章节标题模式（用于全文搜索）
# MinerU 输出为 Markdown 格式，章节标题可能带有 # 或 ## 前缀
# (?:^|\n) 确保匹配行首位置，避免匹配到正文中的同名文字
MINERU_SECTION_PATTERNS = [
    ('claims',        r'(?:^|\n)\s*##?\s*权\s*利\s*要\s*求\s*书'),  # 权利要求书标题
    ('description',   r'(?:^|\n)\s*##?\s*(?:说\s*明\s*书|[\u4e00-\u9fff]+(?:实用新型|发明))'),  # 说明书标题（含"XXX实用新型"/"XXX发明"等变体）
    ('drawings',      r'(?:^|\n)\s*##?\s*说\s*明\s*书\s*附\s*图'),  # 说明书附图标题
]

# 说明书子章节模式列表
# 说明书内部通常包含5个固定子章节，按顺序为：技术领域→背景技术→发明内容→附图说明→具体实施方式
# 每个元素为 (子章节键名, 正则表达式) 的元组
DESCRIPTION_SUB_PATTERNS = [
    ('technical_field',       r'技\s*术\s*领\s*域'),  # 技术领域
    ('background',            r'背\s*景\s*技\s*术'),  # 背景技术
    ('invention_content',     r'(?:实用新型内容|发明内容)'),  # 发明内容/实用新型内容（两者择一）
    ('drawings_description',  r'附\s*图\s*说\s*明'),  # 附图说明
    ('detailed_description',  r'具\s*体\s*实\s*施\s*方\s*式'),  # 具体实施方式
]

# 首页页数信息提取模式："权利要求书X页 说明书Y页 附图Z页"
# 这是中国专利首页的标准著录项目格式，用于精确计算各章节的页码范围
# 支持空格变化（全角/半角）、中文字符间距、OCR 识别误差
# 匹配后 group(1)=X(权利要求书页数), group(2)=Y(说明书页数), group(3)=Z(附图页数)
PAGE_COUNT_PATTERN = re.compile(
    r'权利要求书\s*(\d+)\s*页\s*'  # 匹配"权利要求书X页"，\s*容忍空格变化
    r'说明书\s*(\d+)\s*页\s*'      # 匹配"说明书Y页"
    r'附图\s*(\d+)\s*页',           # 匹配"附图Z页"
)

# 著录项目字段提取模式（基于 INID 代码）——仅用于单行字段
# INID代码是国际通用的专利著录项目标识符，如(21)代表申请号，(22)代表申请日
# 字典的键为中文字段名，值为正则表达式（含一个捕获组用于提取字段值）
# 注意：多行字段（如申请人、专利权人等）需要单独的提取方法处理
BIBLIOGRAPHIC_FIELD_PATTERNS = {
    '申请号': r'\(21\)\s*申请号\s*([\d\.]+)',  # (21)申请号，格式如"202210373749.5"
    '申请日': r'\(22\)\s*申请日\s*(\d{4}\.\d{2}\.\d{2})',  # (22)申请日，格式如"2022.04.22"
    '申请公布号': r'\(10\)\s*申请公布号\s*(CN\s*\d+\s*\w+)',  # (10)申请公布号（发明专利公开），格式如"CN 114909579 A"
    '申请公布日': r'\(43\)\s*申请公布日\s*(\d{4}\.\d{2}\.\d{2})',  # (43)申请公布日（发明专利公开）
    '授权公告号': r'\(10\)\s*授权公告号\s*(CN\s*\d+\s*\w+)',  # (10)授权公告号（专利授权），格式如"CN 114909579 B"
    '授权公告日': r'\(45\)\s*授权公告日\s*(\d{4}\.\d{2}\.\d{2})',  # (45)授权公告日（专利授权）
    '发明人': r'\(72\)\s*发明人\s*(.+)',  # (72)发明人，可能包含多个姓名
}

# 著录项目字段值终止标记：下一个字段开始的模式
# 用于多行字段提取时确定字段值的结束位置
# 这是一个正向前瞻断言 (?=...)，不消耗字符，仅标记字段值的边界
# 注意：同时支持换行开头和同行内出现的关键词（OCR输出中字段可能无换行分隔）
_FIELD_TERMINATOR = (
    r'(?='
    r'\n\s*[\(（]\d{1,2}[\)）]'  # 新的INID代码（如(51)、(72)），表示下一个字段开始
    r'|\n\s*地址\b'              # "地址"字段
    r'|\n\s*专利代理师\b'        # "专利代理师"字段
    r'|\n\s*代理人\b'            # "代理人"字段（旧版专利用词）
    r'|\n\s*专利权人\b'          # "专利权人"字段（附加专利权人）
    r'|\n\s*申请人\b'            # "申请人"字段（附加申请人）
    r'|\n\s*审查员\b'            # "审查员"字段
    r'|\n\s*权利要求书\b'        # "权利要求书"章节开始
    r'|\n\s*对比文件\b'          # "对比文件"字段
    r'|\n\s*申请公布号\b'        # "申请公布号"子字段
    r'|\n\s*申请公布日\b'        # "申请公布日"子字段
    r'|地址\s+\d{6}\b'           # 同行"地址 邮编"（OCR输出中地址可能紧跟前一字段值）
    r'|代理人\b'                  # 同行"代理人"（旧版专利用词）
    r'|专利代理师\b'              # 同行"专利代理师"
    r'|$)'                        # 字符串结尾，也是字段值的终止条件
)


@dataclass
class PatentInfo:
    """专利信息结构体，用于存储从专利PDF中提取的所有结构化信息。

    该数据类是整个解析流程的核心输出，包含了专利的所有关键信息：
    - 专利类型和公开/公告类型
    - 著录项目（申请号、申请人、发明人等）
    - 摘要、权利要求书、说明书内容
    - 附图页码范围和页数统计

    Attributes:
        patent_type: 专利类型，取值为"发明专利"/"实用新型"/"外观设计"/"未知"
        publication_type: 公开/公告类型，取值为"公开"（发明专利申请公布）/"公告"（专利授权公告）/"未知"
        name_field: 专利名称字段的标签名，根据专利类型不同为"发明名称"/"实用新型名称"/"外观设计名称"
        content_field: 发明内容字段的标签名，根据专利类型不同为"发明内容"/"实用新型内容"/"外观设计内容"
        patent_name: 专利名称的实际值，如"一种基于深度学习的图像识别方法"
        bibliographic: 著录项目字典，键为字段名（如"申请号"），值为字段内容
        abstract: 摘要文本内容
        claims: 权利要求书全文
        description: 说明书子章节字典，键为子章节名（如"技术领域"），值为子章节内容
        drawings_page_range: 说明书附图的页码范围，格式为(起始页, 结束页)
        claims_pages: 权利要求书页数（从首页"权利要求书X页"提取）
        description_pages: 说明书页数（从首页"说明书Y页"提取）
        drawings_pages: 附图页数（从首页"附图Z页"提取）
        _has_page_counts: 是否成功从首页提取到页数信息（内部标记，用于判断章节检测策略）
    """
    patent_type: str = ""        # 发明专利 / 实用新型 / 外观设计
    publication_type: str = ""   # 公开 / 公告
    name_field: str = ""         # 发明名称 / 实用新型名称
    content_field: str = ""      # 发明内容 / 实用新型内容
    patent_name: str = ""        # 专利名称的值
    bibliographic: Dict[str, str] = field(default_factory=dict)
    abstract: str = ""
    claims: str = ""
    description: Dict[str, str] = field(default_factory=dict)
    drawings_page_range: Tuple[int, int] = (0, 0)
    # 从首页 "权利要求书X页 说明书Y页 附图Z页" 中提取的页数
    claims_pages: int = 0        # 权利要求书页数 X
    description_pages: int = 0   # 说明书页数 Y
    drawings_pages: int = 0      # 附图页数 Z
    _has_page_counts: bool = False  # 是否成功从首页提取到页数信息


class SectionParser:
    """章节识别与拆分器。

    负责从专利PDF文本中识别章节结构，提取各章节内容。
    支持两种输入模式：
    1. 逐页文本模式（pdfplumber/fitz/Tesseract OCR）：通过页眉检测章节边界
    2. MinerU单页全文模式：通过全文搜索章节标题定位

    核心解析流程（parse方法）：
    1. 识别专利类型（发明/实用新型/外观设计）
    2. 从首页提取页数信息（最可靠的章节定位方法）
    3. 识别章节页码范围（根据输入模式选择不同策略）
    4. 提取著录项目、摘要、权利要求书、说明书等各部分内容
    """

    def __init__(self):
        """初始化章节解析器。

        Attributes:
            pages: 按页提取的文本列表，每个元素为PageText对象
            full_text: 所有页面文本拼接后的完整文本（用换行符连接）
            patent_info: 解析结果，PatentInfo数据类实例
            _is_mineru_single_page: 是否为MinerU单页全文模式
                （MinerU将整个PDF输出为单个Markdown页面，无分页信息）
        """
        self.pages: List[PageText] = []
        self.full_text: str = ""
        self.patent_info = PatentInfo()
        self._is_mineru_single_page: bool = False  # MinerU 单页全文模式标记

    def parse(self, pages: List[PageText]) -> PatentInfo:
        """
        解析专利PDF的章节结构，这是本类的核心入口方法。

        整体解析流程：
        1. 初始化内部状态，拼接全文文本
        2. 检测输入模式（逐页 vs MinerU单页全文）
        3. 识别专利类型（发明/实用新型/外观设计）和公开/公告类型
        4. 从首页提取页数信息（"权利要求书X页 说明书Y页 附图Z页"）
        5. 根据输入模式和页数信息，选择最优策略识别章节页码范围
        6. 依次提取著录项目、摘要、权利要求书、说明书、附图范围

        Args:
            pages: 按页提取的文本列表，每个PageText对象包含：
                - text: 该页的原始文本
                - text_no_space: 去除空格后的文本（用于模式匹配）
                - page_num: 页码（从1开始）
                - source: 文本来源（如"mineru_ocr"、"pdfplumber"等）

        Returns:
            PatentInfo: 解析后的专利信息结构体，包含所有提取的字段和内容
        """
        self.pages = pages
        # 将所有页面的文本用换行符拼接为完整文本，便于全文搜索
        self.full_text = "\n".join(p.text for p in pages)
        # 重置专利信息为空实例（避免多次调用parse时残留上次的数据）
        self.patent_info = PatentInfo()

        # 检测是否为 MinerU 单页全文模式
        # MinerU 会将整个PDF输出为单个Markdown页面，此时 len(pages)==1 且 source=="mineru_ocr"
        self._is_mineru_single_page = (
            len(pages) == 1 and pages[0].source == "mineru_ocr"
        )

        if not pages:
            logger.warning("无页面数据，无法解析")
            return self.patent_info

        # 1. 识别专利类型（发明/实用新型/外观设计）和公开/公告类型
        self._detect_patent_type()

        # 2. 尝试从首页提取页数信息（最可靠的方法）
        #    首页的"权利要求书X页 说明书Y页 附图Z页"是官方著录项目，精确可靠
        has_page_counts = self._parse_page_counts()

        # 3. 识别章节页码范围（根据输入模式和可用信息选择最优策略）
        if self._is_mineru_single_page:
            # MinerU 单页模式：全文无页码分割
            # - 文本章节分割仍用全文搜索
            # - 附图页码范围可基于页数信息精确推算
            sections = self._detect_sections_from_fulltext()
            if has_page_counts:
                # 用页数信息修正 drawings 页码范围
                total_pages = self._get_total_pages()
                self._apply_page_counts_to_drawings_range(total_pages)
        elif has_page_counts:
            # 文本型 PDF + 有页数信息：使用精确的页码计算
            # 这是准确率最高的方式，直接根据X/Y/Z计算各章节的起止页
            sections = self._detect_sections_from_page_counts()
        else:
            # 无页数信息：降级到页眉检测
            # 通过检测每页开头的页眉文字（如"权利要求书"、"说明书"）来判断章节边界
            sections = self._detect_section_pages()

        # 4. 提取著录项目（首页/全文）
        self._extract_bibliographic(sections)

        # 5. 提取摘要
        self._extract_abstract(sections)

        # 6. 提取权利要求书
        self._extract_claims(sections)

        # 7. 提取说明书全文 + 拆分子章节
        self._extract_description(sections)

        # 8. 记录说明书附图页码范围
        self._extract_drawings_range(sections)

        return self.patent_info

    def _detect_patent_type(self):
        """从首页文本识别专利类型和公开/公告类型。

        专利类型判断逻辑：
        - 首页出现"实用新型"关键词 → 实用新型专利
        - 首页出现"发明"关键词 → 发明专利
        - 首页出现"外观设计"关键词 → 外观设计专利
        - 以上均无 → 标记为"未知"，默认使用"发明名称"/"发明内容"

        公开/公告类型判断逻辑：
        - 出现"授权公告号"或"授权公告日" → 公告（专利已授权）
        - 出现"申请公布号"或"申请公布日" → 公开（发明专利申请公布）
        - 以上均无 → 标记为"未知"

        注意：使用 text_no_space（去除空格的文本）进行匹配，
        因为OCR识别的文本中字符间可能有不规则空格。
        """
        if not self.pages:
            return

        # 对于 MinerU 单页模式，使用全文检测
        text = self.pages[0].text_no_space
        if self._is_mineru_single_page:
            # 只检查前 500 字符（首页区域），避免正文中的关键词干扰
            text = text[:500]

        # 判断专利类型（注意判断顺序：先检查"实用新型"，再检查"发明"，
        # 因为"实用新型"中不包含"发明"，但"发明"可能在"实用新型"文本附近出现）
        if '实用新型' in text:
            self.patent_info.patent_type = '实用新型'
            self.patent_info.name_field = '实用新型名称'
            self.patent_info.content_field = '实用新型内容'
        elif '发明' in text:
            self.patent_info.patent_type = '发明专利'
            self.patent_info.name_field = '发明名称'
            self.patent_info.content_field = '发明内容'
        elif '外观设计' in text:
            self.patent_info.patent_type = '外观设计'
            self.patent_info.name_field = '外观设计名称'
            self.patent_info.content_field = '外观设计内容'
        else:
            self.patent_info.patent_type = '未知'
            self.patent_info.name_field = '发明名称'
            self.patent_info.content_field = '发明内容'

        # 判断公开/公告类型
        # "公告"表示专利已授权（授权公告号/授权公告日），"公开"表示发明专利申请公布
        if '授权公告号' in text or '授权公告日' in text:
            self.patent_info.publication_type = '公告'
        elif '申请公布号' in text or '申请公布日' in text:
            self.patent_info.publication_type = '公开'
        else:
            self.patent_info.publication_type = '未知'

        logger.info(f"专利类型: {self.patent_info.patent_type}, "
                     f"公开类型: {self.patent_info.publication_type}")

    def _parse_page_counts(self) -> bool:
        """从首页文本中提取"权利要求书X页 说明书Y页 附图Z页"信息。

        这是中国专利首页的标准著录项目格式，是确定章节页码范围最可靠的方法，
        因为页数信息直接来自专利局官方著录项目，精确到每一页，不受排版变化影响。

        提取策略：
        1. 首先使用精确模式（PAGE_COUNT_PATTERN）匹配"权利要求书X页 说明书Y页 附图Z页"
        2. 如果精确模式失败，使用宽松模式匹配（OCR可能将"页"识别为其他字符）

        Args:
            无（使用 self.pages 和 self.full_text）

        Returns:
            True 如果成功提取到 X, Y, Z 三个数值；False 如果提取失败

        提取成功后会设置：
            - self.patent_info.claims_pages = X（权利要求书页数）
            - self.patent_info.description_pages = Y（说明书页数）
            - self.patent_info.drawings_pages = Z（附图页数）
            - self.patent_info._has_page_counts = True
        """
        # 对于 MinerU 单页模式，在全文前 5000 字符内搜索（首页区域）
        # 因为 MinerU 将所有页面合并为一段文本，首页内容在开头部分
        if self._is_mineru_single_page:
            search_text = self.full_text[:5000]
        elif self.pages:
            # 逐页模式：只在首页搜索
            search_text = self.pages[0].text
        else:
            return False

        # 使用精确模式匹配"权利要求书X页 说明书Y页 附图Z页"
        match = PAGE_COUNT_PATTERN.search(search_text)
        if not match:
            # 备选：OCR 可能将"页"识别为其他字符，尝试更宽松的匹配
            # \S 匹配任意非空白字符，替代精确的"页"字
            loose_pattern = re.compile(
                r'权利要求书\s*(\d+)\s*\S\s*'
                r'说明书\s*(\d+)\s*\S\s*'
                r'附图\s*(\d+)\s*\S',
            )
            match = loose_pattern.search(search_text)

        if match:
            try:
                x = int(match.group(1))  # 权利要求书页数 X
                y = int(match.group(2))  # 说明书页数 Y
                z = int(match.group(3))  # 附图页数 Z
            except (ValueError, IndexError):
                logger.warning("页数信息解析失败: 数值转换错误")
                return False

            # 校验：权利要求书和说明书页数必须大于0（附图页数可以为0）
            if x <= 0 or y <= 0:
                logger.warning(f"页数信息异常: X={x}, Y={y}, Z={z}")
                return False

            self.patent_info.claims_pages = x
            self.patent_info.description_pages = y
            self.patent_info.drawings_pages = z
            self.patent_info._has_page_counts = True
            logger.info(
                f"从首页提取页数信息: "
                f"权利要求书={x}页, 说明书={y}页, 附图={z}页"
            )
            return True

        logger.info("首页未找到'权利要求书X页 说明书Y页 附图Z页'信息")
        return False

    def _detect_sections_from_page_counts(self) -> Dict[str, Tuple[int, int]]:
        """基于首页页数信息精确计算各章节的页码范围。

        中国专利PDF的页面布局是固定的，各章节按以下顺序排列：
            第1页: 著录项目 + 摘要
            第2 ~ 第(X+1)页: 权利要求书（共X页）
            第(X+2) ~ 第(X+Y+1)页: 说明书（共Y页）
            第(X+Y+2) ~ 第(X+Y+Z+1)页: 说明书附图（共Z页）

        其中 X、Y、Z 分别是从首页提取的权利要求书、说明书、附图页数。

        Args:
            无（使用 self.patent_info 中的 claims_pages、description_pages、drawings_pages）

        Returns:
            章节页码范围字典，格式为：
            {
                'bibliographic': (1, 1),           # 著录项目始终在第1页
                'claims': (2, X+1),                 # 权利要求书
                'description': (X+2, X+Y+1),        # 说明书
                'drawings': (X+Y+2, X+Y+Z+1),       # 说明书附图
            }
            与 _detect_section_pages() 返回格式一致，便于统一处理
        """
        x = self.patent_info.claims_pages
        y = self.patent_info.description_pages
        z = self.patent_info.drawings_pages

        # 根据固定布局公式计算各章节的页码范围
        sections = {
            'bibliographic': (1, 1),           # 著录项目：第1页
            'claims':        (2, x + 1),        # 权利要求书：第2页到第(X+1)页
            'description':   (x + 2, x + y + 1),  # 说明书：第(X+2)页到第(X+Y+1)页
            'drawings':      (x + y + 2, x + y + z + 1),  # 附图：第(X+Y+2)页到第(X+Y+Z+1)页
        }

        # 如果总页数已知，修正超出范围的页码
        # 防止计算出的附图结束页码超过PDF实际总页数
        total_pages = len(self.pages) if self.pages else 0
        if not self._is_mineru_single_page and total_pages > 0:
            sections['drawings'] = (
                sections['drawings'][0],
                min(sections['drawings'][1], total_pages),
            )

        logger.info(f"基于页数信息计算章节范围: {sections}")
        return sections

    def _detect_section_pages(self) -> Dict[str, Tuple[int, int]]:
        """
        通过页眉检测各章节的页码范围（降级方案）。

        当无法从首页提取页数信息时，使用此方法。通过检测每页开头的页眉文字
        来判断章节边界。中国专利PDF的每页开头都有页眉，如"权利要求书"、"说明书"等。

        检测策略：
        - 只检查每页开头的前 300 字符（页眉区域），防止正文中出现的章节名
          （如"根据权利要求1所述"）误触发章节切换。
        - 按页码顺序遍历，当检测到新的章节页眉时，结束当前章节，开始新章节。

        Returns:
            章节页码范围字典，格式如：
            {
                'bibliographic': (1, 1),     # 著录项目：第1页
                'claims': (2, 3),             # 权利要求书：第2-3页
                'description': (4, 11),       # 说明书：第4-11页
                'drawings': (12, 21),         # 附图：第12-21页
            }
        """
        sections = {}
        current_section = 'bibliographic'  # 默认从著录项目章节开始
        section_start = 1  # 当前章节的起始页码

        for page in self.pages:
            # 只检查页面前 300 字符（页眉区域），避免正文内容干扰
            text_ns = page.text_no_space[:300]
            matched = False

            for section_key, pattern in SECTION_HEADER_PATTERNS:
                if re.search(pattern, text_ns):
                    if section_key != current_section:
                        # 结束当前章节，开始新章节
                        end_page = page.page_num - 1
                        # 如果章节结束页 < 开始页（同一页出现两个章节），则结束页 = 开始页
                        # 这种情况极少见，但需要处理以避免页码范围异常
                        if end_page < section_start:
                            end_page = section_start
                        sections[current_section] = (section_start, end_page)
                        current_section = section_key
                        section_start = page.page_num
                        logger.debug(f"章节切换: {current_section} 从第 {page.page_num} 页开始")
                    matched = True
                    break

            # 如果当前页在"著录项目"章节，检查是否包含摘要
            # （有些PDF的摘要和著录项目在同一页）
            if current_section == 'bibliographic' and re.search(r'\(57\)\s*摘要', text_ns):
                pass  # 著录项目页包含摘要，保持在同一章节

        # 最后一个章节：遍历结束后，当前章节的结束页就是PDF的最后一页
        sections[current_section] = (section_start, len(self.pages))

        logger.info(f"章节页码范围: {sections}")
        return sections

    def _detect_sections_from_fulltext(self) -> Dict[str, Tuple[int, int]]:
        """
        从 MinerU 输出的整篇 Markdown 中检测章节（MinerU单页全文模式专用）。

        MinerU 输出为单页全文，没有分页信息，因此无法使用页眉检测。
        此方法在全文中搜索章节标题（Markdown格式的标题），返回虚拟页码范围。

        检测策略：
        1. 先使用 MINERU_SECTION_PATTERNS 搜索 Markdown 格式的章节标题（如 "## 权利要求书"）
        2. 再使用 SECTION_HEADER_PATTERNS 搜索原始页眉格式（MinerU 可能保留原始格式）
        3. 两种模式的搜索结果合并去重，按位置排序

        Args:
            无（使用 self.full_text）

        Returns:
            章节字典，页码为虚拟值（1, 1），仅用于标记章节存在性，
            不对应实际 PDF 页码。格式如：
            {
                'bibliographic': (1, 1),
                'claims': (1, 1),
                'description': (1, 1),
            }
        """
        sections = {'bibliographic': (1, 1)}  # 著录项目默认存在
        current_section = 'bibliographic'

        # 在全文中搜索 MinerU Markdown 格式的章节标题
        # 记录每个章节标题在全文中的位置，用于后续排序
        section_positions = []
        for section_key, pattern in MINERU_SECTION_PATTERNS:
            match = re.search(pattern, self.full_text)
            if match:
                section_positions.append((match.start(), section_key))
                logger.debug(f"MinerU 全文搜索: 找到 {section_key} 在位置 {match.start()}")

        # 也搜索原始页眉模式（MinerU 可能保留原始格式）
        # 这是为了兼容 MinerU 未将页眉识别为 Markdown 标题的情况
        for section_key, pattern in SECTION_HEADER_PATTERNS:
            if section_key == 'bibliographic':
                continue  # 著录项目已在首页，无需重复搜索
            match = re.search(pattern, self.full_text)
            if match:
                # 检查是否已被 MINERU_SECTION_PATTERNS 匹配（避免重复记录同一章节）
                already_found = any(
                    sk == section_key for _, sk in section_positions
                )
                if not already_found:
                    section_positions.append((match.start(), section_key))
                    logger.debug(f"MinerU 原始模式搜索: 找到 {section_key} 在位置 {match.start()}")

        # 按位置排序，确保章节顺序正确（从文本开头到结尾）
        section_positions.sort(key=lambda x: x[0])

        if not section_positions:
            logger.warning("MinerU 全文搜索: 未找到任何章节标题")
            sections['bibliographic'] = (1, 1)
            return sections

        # 构建章节字典（所有章节的页码范围都是虚拟值 (1, 1)）
        # 因为 MinerU 单页模式下没有分页信息，仅标记章节是否存在
        for i, (pos, section_key) in enumerate(section_positions):
            if section_key != current_section:
                sections[current_section] = (1, 1)  # 虚拟页码
                current_section = section_key

        sections[current_section] = (1, 1)

        logger.info(f"MinerU 全文搜索章节: {list(sections.keys())}")
        return sections

    def _extract_bibliographic(self, sections: Dict[str, Tuple[int, int]]):
        """提取著录项目字段。

        著录项目是专利首页的结构化信息，包括申请号、申请人、发明人等。
        提取流程：
        1. 获取首页文本（MinerU模式取前2000字符，逐页模式取第1页）
        2. 预处理文本（合并跨行字段值、拆分同行多字段）
        3. 使用正则模式提取单行字段（申请号、申请日等）
        4. 单独提取多行/复杂字段（申请人、地址、代理机构等）
        5. 提取专利名称

        Args:
            sections: 章节页码范围字典（本方法主要使用 'bibliographic' 键，
                      但实际上直接从首页文本提取，不依赖页码范围）
        """
        # 著录项目在首页/全文开头
        if self._is_mineru_single_page:
            raw_text = self.full_text[:2000]  # MinerU模式：前 2000 字符通常包含著录项目
        else:
            raw_text = self.pages[0].text if self.pages else ""  # 逐页模式：取第1页文本

        # 预处理：合并跨行字段值（将续行合并到前一行）
        first_page_text = self._preprocess_bibliographic_text(raw_text)

        # 提取单行字段（申请号、申请日、公布号/公告号、发明人等）
        # 这些字段值通常在一行内，使用 BIBLIOGRAPHIC_FIELD_PATTERNS 中的正则即可匹配
        for field_name, pattern in BIBLIOGRAPHIC_FIELD_PATTERNS.items():
            match = re.search(pattern, first_page_text)
            if match:
                value = match.group(1).strip()
                self.patent_info.bibliographic[field_name] = value
                logger.debug(f"著录项目: {field_name} = {value}")

        # 提取申请人/专利权人（可能跨行、可能有多个）
        # 这两个字段比较复杂，需要单独处理
        self._extract_applicant_or_patentee(first_page_text)

        # 提取地址（可能紧跟在专利权人/申请人后面）
        self._extract_address(first_page_text)

        # 提取专利代理机构 + 专利代理师/代理人
        # 代理机构和代理人可能在同一行，需要分离
        self._extract_agent_info(first_page_text)

        # 提取IPC分类号（可能包含多个分类号，如 "G01N 17/00(2006.01)"）
        self._extract_ipc(first_page_text)

        # 提取(56)对比文件（仅公告类型专利有此字段）
        self._extract_references(first_page_text)

        # 提取审查员（仅公告类型专利有此字段）
        self._extract_examiner(first_page_text)

        # 提取(65)同一申请的已公布的文献号（仅公告类型专利有此字段）
        self._extract_prior_publication(first_page_text)

        # 提取专利名称（(54)发明名称/实用新型名称/外观设计名称）
        self._extract_patent_name(first_page_text)

        logger.info(f"著录项目共提取 {len(self.patent_info.bibliographic)} 个字段")

    @staticmethod
    def _preprocess_bibliographic_text(text: str) -> str:
        """预处理著录项目文本，合并跨行字段值。

        PDF文本提取时，较长的字段值（如公司名称、地址）会被换行截断。
        此方法将续行（不以INID代码或已知字段关键词开头的行）合并到前一行。

        同时处理同一行包含多个INID代码的情况（如B类专利的双栏排版）：
        "(21)申请号 202210373749.5 (56)对比文件" → 拆分为两行

        预处理步骤：
        1. 拆分同一行中的多个INID代码（在 ")(" 之间插入换行）
        2. 逐行处理，将以INID代码或字段关键词开头的行视为新字段起始，
           其他行视为续行，合并到前一行

        Args:
            text: 原始著录项目文本

        Returns:
            预处理后的文本，跨行字段值已合并，同行多字段已拆分
        """
        # 步骤1：拆分同一行中的多个INID代码
        # 匹配 ")(" 中间插入换行，但排除IPC分类号中的括号如 "(2006.01)"
        # 正则解释：\) 匹配右括号，\s* 匹配可能的空格，\(\d{2}\) 匹配新的INID代码（两位数字括号），
        # [\u4e00-\u9fff\w] 确保括号后跟中文或字母（排除纯数字的IPC版本号）
        text = re.sub(r'\)\s*(\(\d{2}\)\s*[\u4e00-\u9fff\w])', r')\n\1', text)

        # 步骤2：逐行处理，合并续行
        lines = text.split('\n')
        result = []

        # 以INID代码或已知字段关键词开头的行视为新字段起始
        # 这些模式用于判断一行是否是新字段的开始（而非上一字段的续行）
        new_field_pattern = re.compile(
            r'^\s*[\(（]\d{1,2}[\)）]'   # INID代码如 (21), (72)
            r'|^\s*地址\b'                # 地址
            r'|^\s*专利代理师\b'          # 专利代理师
            r'|^\s*专利权人\b'            # 专利权人（无INID代码的附加专利权人）
            r'|^\s*申请人\b'              # 申请人（无INID代码的附加申请人）
            r'|^\s*审查员\b'              # 审查员
            r'|^\s*权利要求书\b'          # 权利要求书
            r'|^\s*对比文件\b'            # 对比文件
            r'|^\s*申请公布号\b'          # (65)子字段
            r'|^\s*申请公布日\b'          # (65)子字段
        )

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue  # 跳过空行
            if new_field_pattern.search(stripped) or not result:
                # 新字段起始行（或结果列表为空的第一行）：直接添加
                result.append(stripped)
            else:
                # 续行——合并到前一行（不加空格，因为中文词语跨行无空格）
                # 例如："华为技术" 和 "有限公司" 跨行，合并为 "华为技术有限公司"
                result[-1] = result[-1] + stripped

        return '\n'.join(result)

    def _extract_applicant_or_patentee(self, text: str):
        """提取申请人或专利权人（根据专利类型自适应，支持多行值和多个权利人）。

        提取逻辑：
        1. 先提取专利权人 (73) —— 授权公告类型专利使用
        2. 再提取申请人 (71) —— 申请公布类型专利使用
        3. 两者可能同时存在（授权公告专利中也有申请人信息）
        4. 支持附加专利权人/申请人（无INID代码，以关键词开头）
        5. 从字段值中分离可能混入的地址信息

        使用 _FIELD_TERMINATOR 确定字段值的结束位置，
        防止将下一个字段的内容误归入当前字段。

        Args:
            text: 预处理后的著录项目文本
        """
        # 专利权人 (73) - 预处理已合并跨行值
        # 使用 _FIELD_TERMINATOR 确定字段值结束位置
        match = re.search(r'\(73\)\s*专利权人\s*(.+?)' + _FIELD_TERMINATOR, text)
        if match:
            value = match.group(1).strip()
            # 从专利权人值中分离出地址信息（OCR输出中"地址"可能紧跟公司名，无换行分隔）
            value, separated_addr = self._separate_address_from_holder(value)
            self.patent_info.bibliographic['专利权人'] = value
            logger.debug(f"著录项目: 专利权人 = {value}")
            # 如果从专利权人中分离出了地址，且尚未提取到地址，则补充
            if separated_addr and '地址' not in self.patent_info.bibliographic:
                self.patent_info.bibliographic['地址'] = separated_addr
                logger.debug(f"著录项目: 地址（从专利权人分离） = {separated_addr}")

            # 检查附加专利权人（无INID代码，以"专利权人"关键词开头）
            # 有些专利有多个专利权人，第二个起不再标注(73)代码
            remaining = text[match.end():]
            add_match = re.search(r'专利权人\s*(.+?)' + _FIELD_TERMINATOR, remaining)
            if add_match:
                add_value = add_match.group(1).strip()
                add_value, separated_addr2 = self._separate_address_from_holder(add_value)
                # 多个专利权人用中文分号"；"连接
                self.patent_info.bibliographic['专利权人'] += '；' + add_value
                logger.debug(f"著录项目: 附加专利权人 = {add_value}")
                if separated_addr2 and '地址' not in self.patent_info.bibliographic:
                    self.patent_info.bibliographic['地址'] = separated_addr2

        # 申请人 (71) - 预处理已合并跨行值
        # 逻辑与专利权人提取相同
        match = re.search(r'\(71\)\s*申请人\s*(.+?)' + _FIELD_TERMINATOR, text)
        if match:
            value = match.group(1).strip()
            # 从申请人值中分离出地址信息
            value, separated_addr = self._separate_address_from_holder(value)
            self.patent_info.bibliographic['申请人'] = value
            logger.debug(f"著录项目: 申请人 = {value}")
            if separated_addr and '地址' not in self.patent_info.bibliographic:
                self.patent_info.bibliographic['地址'] = separated_addr

            # 检查附加申请人（无INID代码，以"申请人"关键词开头）
            remaining = text[match.end():]
            add_match = re.search(r'申请人\s*(.+?)' + _FIELD_TERMINATOR, remaining)
            if add_match:
                add_value = add_match.group(1).strip()
                add_value, separated_addr2 = self._separate_address_from_holder(add_value)
                # 多个申请人用中文分号"；"连接
                self.patent_info.bibliographic['申请人'] += '；' + add_value
                if separated_addr2 and '地址' not in self.patent_info.bibliographic:
                    self.patent_info.bibliographic['地址'] = separated_addr2

    @staticmethod
    def _separate_address_from_holder(holder_value: str) -> tuple:
        """从专利权人/申请人值中分离出地址信息。

        OCR输出中，地址可能紧跟在公司名后面（同一行），格式如：
        "源德盛塑胶电子（深圳)有限公司地址 518000 广东省深圳市龙华新区..."
        这种情况下需要将公司名和地址分离，否则地址会被误归入专利权人/申请人字段。

        分离策略：匹配"地址"关键词+6位邮编+详细地址的模式

        Args:
            holder_value: 专利权人或申请人的原始字段值

        Returns:
            (cleaned_holder, address) 元组：
            - cleaned_holder: 去除地址后的纯公司名/人名
            - address: 分离出的地址信息（含邮编），如果未找到地址则为 None
        """
        # 匹配"地址"关键词及其后的邮编+详细地址
        addr_match = re.search(r'地址\s+(\d{6}\s*.+)$', holder_value)
        if addr_match:
            address = addr_match.group(1).strip()
            cleaned = holder_value[:addr_match.start()].strip()
            return cleaned, address
        return holder_value, None

    def _extract_address(self, text: str):
        """提取地址字段。

        地址字段可能以独立行出现（有"地址"关键词前缀），
        也可能已从专利权人/申请人字段中分离出来。

        Args:
            text: 预处理后的著录项目文本
        """
        match = re.search(r'地址\s*(.+?)' + _FIELD_TERMINATOR, text)
        if match:
            value = match.group(1).strip()
            self.patent_info.bibliographic['地址'] = value
            logger.debug(f"著录项目: 地址 = {value}")

    def _extract_agent_info(self, text: str):
        """提取专利代理机构和专利代理师/代理人。

        提取逻辑：
        1. 提取专利代理机构 (74)，并从中分离可能混入的代理人/代理师信息
        2. 提取专利代理师（紧跟在代理机构之后，无INID代码）
        3. 提取代理人（旧版专利用词，格式与代理师相同）

        注意：代理人和代理师是同一角色的不同称呼，
        新版专利使用"专利代理师"，旧版专利使用"代理人"。

        Args:
            text: 预处理后的著录项目文本
        """
        # 专利代理机构 (74) - 预处理已合并跨行值
        match = re.search(r'\(74\)\s*专利代理机构\s*(.+?)' + _FIELD_TERMINATOR, text)
        if match:
            value = match.group(1).strip()
            # 从代理机构值中分离出代理人/代理师信息
            # OCR输出中"代理人"/"代理师"可能紧跟在代理机构代码后面（同一行）
            # 格式如："深圳市君盈知识产权事务所（普通合伙）44315代理人陈琳"
            value, separated_agent = self._separate_agent_from_agency(value)
            self.patent_info.bibliographic['专利代理机构'] = value
            logger.debug(f"著录项目: 专利代理机构 = {value}")
            if separated_agent:
                self.patent_info.bibliographic['代理人'] = separated_agent
                logger.debug(f"著录项目: 代理人（从代理机构分离） = {separated_agent}")

        # 专利代理师（紧跟在专利代理机构之后，无INID代码）
        # 新版专利使用"专利代理师"称呼
        match = re.search(r'专利代理师\s*(.+?)' + _FIELD_TERMINATOR, text)
        if match:
            value = match.group(1).strip()
            self.patent_info.bibliographic['专利代理师'] = value
            logger.debug(f"著录项目: 专利代理师 = {value}")

        # 代理人（旧版专利用词，紧跟在专利代理机构之后，无INID代码）
        # 旧版专利使用"代理人"称呼，与"专利代理师"是同一角色
        match = re.search(r'代理人\s*(.+?)' + _FIELD_TERMINATOR, text)
        if match:
            value = match.group(1).strip()
            # 避免与从代理机构分离出的代理人重复
            if '代理人' not in self.patent_info.bibliographic:
                self.patent_info.bibliographic['代理人'] = value
                logger.debug(f"著录项目: 代理人 = {value}")

    @staticmethod
    def _separate_agent_from_agency(agency_value: str) -> tuple:
        """从专利代理机构值中分离出代理人/代理师信息。

        OCR输出中，代理人可能紧跟在代理机构代码后面（同一行），格式如：
        "深圳市君盈知识产权事务所（普通合伙）44315代理人陈琳"
        需要将代理机构名称和代理人姓名分离。

        分离策略：匹配"代理人"或"专利代理师"关键词+中文人名的模式

        Args:
            agency_value: 专利代理机构的原始字段值

        Returns:
            (cleaned_agency, agent_name) 元组：
            - cleaned_agency: 去除代理人后的纯代理机构信息
            - agent_name: 分离出的代理人姓名，如果未找到则为 None
        """
        # 匹配"代理人"或"专利代理师"关键词及其后的人名
        # [\u4e00-\u9fff]+ 匹配一个或多个中文字符（人名通常为2-4个汉字）
        # \s*$ 确保人名在行尾，避免误匹配
        agent_match = re.search(r'(?:专利代理师|代理人)\s*([\u4e00-\u9fff]+)\s*$', agency_value)
        if agent_match:
            agent_name = agent_match.group(1).strip()
            cleaned = agency_value[:agent_match.start()].strip()
            return cleaned, agent_name
        return agency_value, None

    def _extract_ipc(self, text: str):
        """提取IPC分类号（可能包含多个分类号）。

        IPC（International Patent Classification）是国际专利分类号，
        格式如 "G01N 17/00(2006.01)"，其中：
        - G01N 是部/大类/小类
        - 17/00 是大组/小组
        - (2006.01) 是分类号版本

        一个专利可能有多个IPC分类号，用分号或空格分隔。

        Args:
            text: 预处理后的著录项目文本
        """
        match = re.search(
            r'\(51\)\s*Int\.?Cl\.?\s*([\s\S]+?)' + _FIELD_TERMINATOR, text
        )
        if match:
            value = match.group(1).strip()
            # 提取所有IPC分类号（格式如 "G01N 17/00(2006.01)"）
            # 正则解释：[A-Z]\d{2}[A-Z] 匹配部+大类+小类，\s+\d+/\d+ 匹配大组/小组，\([^)]+\) 匹配版本号
            ipc_codes = re.findall(r'[A-Z]\d{2}[A-Z]\s+\d+/\d+\([^)]+\)', value)
            if ipc_codes:
                # 多个分类号用分号连接
                self.patent_info.bibliographic['IPC分类号'] = '; '.join(ipc_codes)
            else:
                # 降级：直接使用原始值（去除多余空格）
                self.patent_info.bibliographic['IPC分类号'] = re.sub(r'\s+', ' ', value)
            logger.debug(f"著录项目: IPC分类号 = {self.patent_info.bibliographic.get('IPC分类号', '')}")

    def _extract_references(self, text: str):
        """提取(56)对比文件（仅授权公告类型专利有此字段）。

        对比文件是审查过程中引用的现有技术文献，
        格式如 "CN 215445838 U,2022.01.07"。

        Args:
            text: 预处理后的著录项目文本
        """
        # 快速判断：如果文本中没有(56)或"对比文件"关键词，直接跳过
        if '(56)' not in text and '对比文件' not in text:
            return
        # 提取所有对比文件引用（格式如 "CN 215445838 U,2022.01.07"）
        # 正则解释：CN\s*\d+ 匹配公开号，\s*\w+ 匹配类型字母(A/B/U)，\s*,\s* 匹配逗号分隔，\d{4}\.\d{2}\.\d{2} 匹配日期
        refs = re.findall(r'CN\s*\d+\s*\w+\s*,\s*\d{4}\.\d{2}\.\d{2}', text)
        if refs:
            self.patent_info.bibliographic['对比文件'] = '; '.join(refs)
            logger.debug(f"著录项目: 对比文件 = {'; '.join(refs)}")

    def _extract_examiner(self, text: str):
        """提取审查员姓名（仅授权公告类型专利有此字段）。

        审查员是负责审查该专利的审查员姓名，通常为2-4个汉字。

        Args:
            text: 预处理后的著录项目文本
        """
        match = re.search(r'审查员\s*([\u4e00-\u9fff]+)', text)
        if match:
            value = match.group(1).strip()
            self.patent_info.bibliographic['审查员'] = value
            logger.debug(f"著录项目: 审查员 = {value}")

    def _extract_prior_publication(self, text: str):
        """提取(65)同一申请的已公布的文献号（仅授权公告类型专利有此字段）。

        对于发明专利，先公开后授权。(65)字段记录的是该专利在公开阶段
        的公布号，便于追溯专利的审查历史。

        Args:
            text: 预处理后的著录项目文本
        """
        match = re.search(r'\(65\)\s*同一申请的已公布的文献号', text)
        if match:
            # 在(65)之后搜索申请公布号
            remaining = text[match.end():]
            pub_match = re.search(r'申请公布号\s*(CN\s*\d+\s*\w+)', remaining)
            if pub_match:
                value = pub_match.group(1).strip()
                self.patent_info.bibliographic['同一申请的已公布的文献号'] = value
                logger.debug(f"著录项目: 同一申请的已公布的文献号 = {value}")

    def _extract_patent_name(self, text: str):
        """提取专利名称。

        专利名称位于(54)字段，格式如"(54) 发明名称\n一种基于深度学习的图像识别方法"。
        根据专利类型不同，字段名可能是"发明名称"、"实用新型名称"或"外观设计名称"。

        提取策略（按优先级）：
        1. 半角括号模式："(54)发明名称"
        2. 全角括号模式："（54）发明名称"（MinerU输出可能使用全角）
        3. 混合括号模式：兼容半角和全角

        名称值的终止标记：(57)摘要标记、##标题标记、换行或字符串结尾

        Args:
            text: 预处理后的著录项目文本
        """
        # 名称值终止标记：遇到 (57)摘要标记、## 标题标记、换行或字符串结尾时停止
        # 这是因为专利名称通常紧跟在(57)摘要之前
        _NAME_TERMINATOR = r'(?:\s*##?\s*[\(（]57[\)）]|\s*[\(（]57[\)）]|\n|$)'

        # 策略1：半角括号模式
        pattern = r'\(54\)\s*(?:发明名称|实用新型名称|外观设计名称)\s*\n?\s*(.+?)' + _NAME_TERMINATOR
        match = re.search(pattern, text)
        if match:
            self.patent_info.patent_name = match.group(1).strip()
            self.patent_info.bibliographic[self.patent_info.name_field] = self.patent_info.patent_name
            logger.debug(f"专利名称: {self.patent_info.patent_name}")
            return

        # 策略2：全角括号模式（MinerU 输出可能使用全角括号）
        pattern = r'\（54\）\s*(?:发明名称|实用新型名称|外观设计名称)\s*\n?\s*(.+?)' + _NAME_TERMINATOR
        match = re.search(pattern, text)
        if match:
            self.patent_info.patent_name = match.group(1).strip()
            self.patent_info.bibliographic[self.patent_info.name_field] = self.patent_info.patent_name
            logger.debug(f"专利名称: {self.patent_info.patent_name}")
            return

        # 策略3：混合括号模式（兼容半角和全角括号）
        pattern = r'[\(（]54[\)）]\s*(?:发明名称|实用新型名称|外观设计名称)\s*\n?\s*(.+?)' + _NAME_TERMINATOR
        match = re.search(pattern, text)
        if match:
            self.patent_info.patent_name = match.group(1).strip()
            self.patent_info.bibliographic[self.patent_info.name_field] = self.patent_info.patent_name
            logger.debug(f"专利名称: {self.patent_info.patent_name}")

    def _extract_abstract(self, sections: Dict[str, Tuple[int, int]]):
        """提取摘要内容。

        摘要位于(57)字段，通常在首页末尾，紧跟在著录项目之后。
        提取策略（按优先级尝试）：
        1. 匹配 "(57)摘要" 标记，截取到"权利要求书"或"说明书"之前的内容
        2. 匹配 MinerU 格式的摘要标题（"## (57)摘要"），截取到下一个标题之前
        3. 从首页中提取 "(57)摘要" 之后的所有内容（截断到合理长度）

        提取后会清理摘要中的著录项目残留（如日期、公告号等）和换行符。

        Args:
            sections: 章节页码范围字典（本方法直接从首页/全文提取，不依赖页码范围）
        """
        # 优先从全文中提取（MinerU模式用全文，逐页模式用首页）
        text = self.full_text if self._is_mineru_single_page else (
            self.pages[0].text if self.pages else ""
        )

        # 策略1：匹配 (57)摘要 标记，截取到"权利要求书"或"说明书"之前
        # 这是最常见的格式，摘要位于(57)标记之后，权利要求书或说明书之前
        match = re.search(r'\(57\)\s*摘要\s*\n([\s\S]+?)(?=\n\s*权\s*利\s*要\s*求\s*书|\n\s*说\s*明\s*书)', text)
        if match:
            abstract = match.group(1).strip()
            # 清理摘要中的著录项目残留（如 "(45)授权公告日 2022.01.07"）
            # 这些残留信息是因为首页排版中摘要和著录项目混在一起
            abstract = re.sub(r'\n?\s*[\(（]\d+[\)）]\s*\S+\s*\d{4}\.\d{2}\.\d{2}.*$', '', abstract, flags=re.MULTILINE).strip()
            # 去除换行符，将摘要合并为连续文本
            abstract = abstract.replace('\n', '')
            self.patent_info.abstract = abstract
            logger.info("摘要提取成功")
            return

        # 策略2：匹配 MinerU 格式的摘要标题（## (57）摘要）
        # MinerU 输出中摘要标题可能被识别为 Markdown 标题
        # 截取到下一个 ## 标题或权利要求书编号之前
        match = re.search(r'##?\s*[\(（]57[\)）]\s*摘要\s*\n([\s\S]+?)(?=\n\s*#{1,3}\s|\n\s*权\s*利\s*要\s*求\s*书|\n\s*\d+[.．]\s*一种)', text)
        if match:
            abstract = match.group(1).strip()
            # 清理摘要中的著录项目残留
            abstract = re.sub(r'\n?\s*[\(（]\d+[\)）]\s*\S+\s*\d{4}\.\d{2}\.\d{2}.*$', '', abstract, flags=re.MULTILINE).strip()
            # 去除换行符
            abstract = abstract.replace('\n', '')
            self.patent_info.abstract = abstract
            logger.info("摘要提取成功（MinerU 格式）")
            return

        # 策略3：从首页中提取 (57) 之后的所有内容
        # 这是最宽松的匹配方式，作为最后的降级方案
        # 限制搜索范围为前3000字符，避免匹配到正文中的(57)
        match = re.search(r'\(57\)\s*摘要\s*\n([\s\S]+?)$', text[:3000])
        if match:
            text_content = match.group(1).strip()
            # 截断到合理的摘要长度（通常摘要不超过500字）
            if len(text_content) > 1000:
                text_content = text_content[:1000] + "..."
            # 去除换行符
            text_content = text_content.replace('\n', '')
            self.patent_info.abstract = text_content
            logger.info("摘要提取成功（备选方式）")
            return

        logger.warning("未找到摘要内容")

    def _clean_page_headers(self, text: str) -> str:
        """清理文本中的页眉信息。

        中国专利PDF的每页顶部都有页眉，格式如：
        - "权 利 要 求 书\\nCN 114909579 B 1/2页"
        - "说 明 书\\nCN 114909579 A 2/8 页"
        - "22\\n\\n权 利 要 求 书\\nCN 114909579 B 2/2页"（页码+页眉）

        这些页眉在提取正文内容时需要去除，否则会干扰文本阅读。

        Args:
            text: 待清理的文本

        Returns:
            去除页眉后的文本
        """
        # 清理 "章节名\nCN XXXXXXXXX [A|B|U] X/Y 页" 格式的页眉
        # 正则解释：
        # (?:^|\n)\s* 匹配行首
        # (?:权\s*利\s*要\s*求\s*书|说\s*明\s*书) 匹配章节名（容忍空格）
        # \s*\n\s* 匹配章节名和公开号之间的换行
        # CN\s+\d+\s+[AaBbUu] 匹配公开号+类型字母（A=公开, B=发明授权, U=实用新型授权）
        # \s+\d+\s*/\s*\d+\s*页 匹配页码格式"X/Y 页"
        header_pattern = (
            r'(?:^|\n)\s*'
            r'(?:权\s*利\s*要\s*求\s*书|说\s*明\s*书)'
            r'\s*\n\s*'
            r'CN\s+\d+\s+[AaBbUu]\s+\d+\s*/\s*\d+\s*页'
        )
        text = re.sub(header_pattern, '', text)
        return text

    def _clean_standalone_page_numbers(self, text: str) -> str:
        """清理文本中独立成行的页码。

        PDF文本提取时，每页的页码可能被单独提取为一行。
        页码通常单独一行，仅包含1-4位数字。
        例如：
        - "33" 单独一行
        - "1100" 单独一行

        清理策略：
        1. 删除行中仅有1-4位数字的行（中间的页码行）
        2. 处理文本开头的页码行
        3. 处理文本末尾的页码行

        Args:
            text: 待清理的文本

        Returns:
            去除独立页码行后的文本
        """
        # 删除行中仅有1-4位数字的行（页码）
        text = re.sub(r'\n[ \t]*\d{1,4}[ \t]*(?=\n)', '\n', text)
        # 处理文本开头的页码
        text = re.sub(r'^[ \t]*\d{1,4}[ \t]*\n', '', text)
        # 处理文本末尾的页码
        text = re.sub(r'\n[ \t]*\d{1,4}[ \t]*$', '', text)
        return text

    def _clean_pdf_artifacts(self, text: str) -> str:
        """清理PDF文本中的页眉和页码等排版残留。

        这是一个组合清理方法，按顺序执行：
        1. 清理页眉（章节名+公开号+页码）
        2. 清理独立成行的页码
        3. 清理多余空行（3个及以上连续空行替换为2个）

        Args:
            text: 待清理的文本

        Returns:
            清理后的文本
        """
        text = self._clean_page_headers(text)
        text = self._clean_standalone_page_numbers(text)
        # 清理连续3个及以上的空行（替换为2个换行）
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _clean_paragraph_breaks(self, text: str) -> str:
        """清理文本中的换行符，并将段落号标记为段落起始。

        说明书中的段落通常以 [XXXX]（4位阿拉伯数字的中文方括号）标记段落号，
        如 [0001]、[0002] 等。PDF文本提取时，同一段落的内容可能被换行截断。

        处理逻辑：
        1. 将 [XXXX] 识别为段落号，在段落号前插入换行以标记段落开始
        2. 去除所有其他 \\n 换行符（合并跨行文本为连续段落）

        示例：
        输入: "本发明涉及[0001]一种图像\\n识别方法，\\n包括以下步骤"
        输出: "本发明涉及\\n[0001]一种图像识别方法，包括以下步骤"

        Args:
            text: 待清理的文本

        Returns:
            清理后的文本，段落以[XXXX]分隔，段落内无换行
        """
        if not text:
            return text
        # 在段落号 [XXXX] 前插入换行（段落号前已有换行则不重复插入）
        # (?<!\n) 是负向后顾断言，确保前面不是换行符
        text = re.sub(r'(?<!\n)\n(\[\d{4}\])', r'\n\1', text)
        # 先按段落号分割，再合并每段内的换行
        # re.split 配合捕获组会保留分隔符（段落号本身）
        parts = re.split(r'(\[\d{4}\])', text)
        result = []
        current_paragraph = []
        for part in parts:
            if re.match(r'^\[\d{4}\]$', part):
                # 遇到段落号，先保存之前的段落（合并换行）
                if current_paragraph:
                    merged = ''.join(current_paragraph).replace('\n', '')
                    result.append(merged)
                current_paragraph = [part]  # 开始新段落
            else:
                current_paragraph.append(part)
        # 保存最后一个段落
        if current_paragraph:
            merged = ''.join(current_paragraph).replace('\n', '')
            result.append(merged)
        return '\n'.join(result)

    def _clean_claims_breaks(self, text: str) -> str:
        """清理权利要求书中的换行符，以权利要求编号为段落分隔。

        权利要求书中每条权利要求以数字编号开头，如"1."、"2."等。
        PDF文本提取时，同一权利要求的内容可能被换行截断。

        处理逻辑（与 _clean_paragraph_breaks 类似，但分隔标记不同）：
        1. 将数字编号（如 "1."、"2."）识别为权利要求起始，
           在编号前插入换行以标记段落开始
        2. 去除所有其他 \\n 换行符（合并跨行文本为连续段落）

        示例：
        输入: "1.一种方法，\\n其特征在于...\\n2.根据权利要求1\\n所述的方法"
        输出: "1.一种方法，其特征在于...\\n2.根据权利要求1所述的方法"

        Args:
            text: 待清理的权利要求书文本

        Returns:
            清理后的文本，每条权利要求占一段，段内无换行
        """
        if not text:
            return text
        # 在权利要求编号前插入换行（编号前已有换行则不重复插入）
        # \d+[.．] 匹配数字编号（支持半角点和全角点）
        text = re.sub(r'(?<!\n)\n(\d+[.．])', r'\n\1', text)
        # 按权利要求编号分割，再合并每段内的换行
        # 处理方式与 _clean_paragraph_breaks 相同
        parts = re.split(r'(\d+[.．])', text)
        result = []
        current_paragraph = []
        for part in parts:
            if re.match(r'^\d+[.．]$', part):
                # 遇到权利要求编号，先保存之前的段落（合并换行）
                if current_paragraph:
                    merged = ''.join(current_paragraph).replace('\n', '')
                    result.append(merged)
                current_paragraph = [part]  # 开始新权利要求
            else:
                current_paragraph.append(part)
        # 保存最后一个段落
        if current_paragraph:
            merged = ''.join(current_paragraph).replace('\n', '')
            result.append(merged)
        return '\n'.join(result)

    def _extract_claims(self, sections: Dict[str, Tuple[int, int]]):
        """提取权利要求书内容。

        根据输入模式选择不同的提取策略：
        - MinerU单页模式：从全文中搜索权利要求书的起止位置
        - 逐页模式：根据章节页码范围提取对应页面的文本

        提取后会清理页眉、页码等排版残留，并按权利要求编号合并段落。

        Args:
            sections: 章节页码范围字典，需包含 'claims' 键
        """
        if self._is_mineru_single_page:
            # MinerU单页模式：从全文中搜索权利要求书
            self._extract_claims_from_fulltext()
        elif 'claims' not in sections:
            logger.warning("未找到权利要求书章节")
        else:
            # 逐页模式：根据页码范围提取对应页面的文本
            start, end = sections['claims']
            claim_texts = []
            for page in self.pages:
                if start <= page.page_num <= end:
                    claim_texts.append(page.text)

            # 将多页文本用双换行连接
            self.patent_info.claims = "\n\n".join(claim_texts).strip()
            # 清理页眉和页码等排版残留
            self.patent_info.claims = self._clean_pdf_artifacts(self.patent_info.claims)
            # 清理段落换行：按权利要求编号合并段落
            self.patent_info.claims = self._clean_claims_breaks(self.patent_info.claims)
            logger.info(f"权利要求书提取成功，{end - start + 1} 页")

    def _extract_claims_from_fulltext(self):
        """从 MinerU 全文中提取权利要求书（MinerU单页全文模式专用）。

        在全文中搜索权利要求书的起止位置：
        - 起始位置：匹配"权利要求书"页眉或以编号开头的权利要求（如"1.一种"）
        - 结束位置：匹配"说明书"标题、"技术领域"标题等

        如果无法确定结束位置，则降级到"附图说明"之前或取到文末。

        Args:
            无（使用 self.full_text）
        """
        # 搜索权利要求书的开始位置
        claims_start = None
        claims_end = None

        # 模式1：页眉 "权利要求书"（最直接的标识）
        match = re.search(r'权\s*利\s*要\s*求\s*书\s*\n', self.full_text)
        if match:
            claims_start = match.end()  # 从页眉之后开始

        # 模式2：以编号开头的权利要求（如 "1．一种" 或 "1.一种"）
        # 当页眉未被识别时，直接从第一条权利要求开始
        if claims_start is None:
            match = re.search(r'(?:^|\n)\s*(\d+)[.．]\s*一种', self.full_text)
            if match:
                claims_start = match.start()

        if claims_start is None:
            logger.warning("全文搜索: 未找到权利要求书")
            return

        # 搜索权利要求书的结束位置（说明书开始）
        # 按优先级尝试多种模式，因为MinerU对说明书标题的识别可能不一致
        for pattern in [
            r'\n\s*##?\s*说\s*明\s*书(?!\s*附\s*图)',  # 标准说明书标题
            r'\n\s*##?\s*[\u4e00-\u9fff]+(?:实用新型|发明)',  # MinerU 可能把说明书标题识别为专利名称
            r'\n\s*##?\s*技\s*术\s*领\s*域',  # 技术领域是说明书的第一个子章节
        ]:
            match = re.search(pattern, self.full_text[claims_start:])
            if match:
                claims_end = claims_start + match.start()
                break

        if claims_end is None:
            # 降级：取到附图说明之前（说明书附图章节在说明书之后）
            match = re.search(r'\n\s*##?\s*附\s*图\s*说\s*明', self.full_text[claims_start:])
            if match:
                claims_end = claims_start + match.start()
            else:
                # 最终降级：取到全文末尾
                claims_end = len(self.full_text)

        claims_text = self.full_text[claims_start:claims_end].strip()
        # 清理页眉和页码
        claims_text = self._clean_pdf_artifacts(claims_text)
        # 清理 MinerU 输出中的 Markdown 标题标记残留
        # 如 "## 权利要求书" 或行尾的 "##"
        claims_text = re.sub(r'\n\s*#{1,3}\s*[\u4e00-\u9fff]+$', '', claims_text).strip()
        claims_text = re.sub(r'\n\s*#{1,3}\s*$', '', claims_text).strip()
        # 清理段落换行：按权利要求编号合并段落
        claims_text = self._clean_claims_breaks(claims_text)

        self.patent_info.claims = claims_text
        logger.info(f"全文搜索: 权利要求书提取成功，长度: {len(claims_text)} 字符")

    def _extract_description(self, sections: Dict[str, Tuple[int, int]]):
        """提取说明书全文并拆分子章节。

        根据输入模式选择不同的提取策略：
        - MinerU单页模式：从全文中搜索说明书的起止位置
        - 逐页模式：根据章节页码范围提取对应页面的文本

        提取后会拆分为5个子章节：技术领域、背景技术、发明内容、附图说明、具体实施方式。

        Args:
            sections: 章节页码范围字典，需包含 'description' 键
        """
        if self._is_mineru_single_page:
            # MinerU单页模式：从全文中搜索说明书
            self._extract_description_from_fulltext()
        elif 'description' not in sections:
            logger.warning("未找到说明书章节")
        else:
            # 逐页模式：根据页码范围提取对应页面的文本
            start, end = sections['description']
            desc_texts = []
            for page in self.pages:
                if start <= page.page_num <= end:
                    desc_texts.append(page.text)

            # 将多页文本用双换行连接
            description_text = "\n\n".join(desc_texts)
            # 清理页眉和页码
            description_text = self._clean_pdf_artifacts(description_text)

            # 拆分说明书子章节
            sub_sections = self._split_description_subsections(description_text)
            self.patent_info.description = sub_sections

            logger.info(f"说明书提取成功，{len(sub_sections)} 个子章节: {list(sub_sections.keys())}")

    def _extract_description_from_fulltext(self):
        """从 MinerU 全文中提取说明书（MinerU单页全文模式专用）。

        在全文中搜索说明书的起止位置：
        - 起始位置：匹配"技术领域"标题（说明书的第一个子章节）或"说明书"页眉
        - 结束位置：匹配"说明书附图"标题或图号标记

        如果无法确定结束位置，则取到文末。

        Args:
            无（使用 self.full_text）
        """
        # 搜索说明书的开始位置
        desc_start = None
        desc_end = None

        # 模式1：技术领域（说明书的第一个子章节）
        # 如果找到"技术领域"，还需要向前搜索是否有说明书标题
        match = re.search(r'(?:^|\n)\s*##?\s*技\s*术\s*领\s*域', self.full_text)
        if match:
            # 检查"技术领域"前面是否有说明书标题（MinerU可能将专利名称作为说明书标题）
            title_match = re.search(
                r'(?:^|\n)\s*##?\s*[\u4e00-\u9fff]+\n\s*##?\s*技\s*术\s*领\s*域',
                self.full_text,
            )
            if title_match:
                # 有说明书标题，从标题开始
                desc_start = title_match.start()
            else:
                # 无说明书标题，从"技术领域"开始
                desc_start = match.start()

        # 模式2：说明书页眉（当"技术领域"未被识别为标题时使用）
        if desc_start is None:
            match = re.search(r'说\s*明\s*书(?!\s*附\s*图)\s*\n', self.full_text)
            if match:
                desc_start = match.end()  # 从页眉之后开始

        if desc_start is None:
            logger.warning("全文搜索: 未找到说明书")
            return

        # 搜索说明书的结束位置（说明书附图开始）
        match = re.search(r'(?:^|\n)\s*##?\s*说\s*明\s*书\s*附\s*图', self.full_text[desc_start:])
        if match:
            desc_end = desc_start + match.start()
        else:
            # 备选：搜索 <!-- image--> 图号标记
            # MinerU 输出中附图区域通常以图号标记开始，如 "<!-- image-->\n图1"
            match = re.search(r'(?:<!--\s*image\s*-->\s*\n\s*图\s*\d+\s*$)', self.full_text[desc_start:], re.MULTILINE)
            if match:
                # 找到第一个图号标记的位置，说明书内容在此之前结束
                desc_end = desc_start + match.start()
            else:
                # 最终降级：取到全文末尾
                desc_end = len(self.full_text)

        description_text = self.full_text[desc_start:desc_end].strip()

        # 拆分说明书子章节
        sub_sections = self._split_description_subsections(description_text)
        self.patent_info.description = sub_sections

        logger.info(f"全文搜索: 说明书提取成功，{len(sub_sections)} 个子章节: {list(sub_sections.keys())}")

    def _split_description_subsections(self, text: str) -> Dict[str, str]:
        """在说明书文本中拆分出子章节。

        说明书通常包含以下子章节（按固定顺序）：
        1. 说明书标题
        2. 技术领域
        3. 背景技术
        4. 发明内容/实用新型内容
        5. 附图说明
        6. 具体实施方式

        拆分逻辑：
        1. 使用 DESCRIPTION_SUB_PATTERNS 找到所有子章节标题的位置
        2. 按位置排序，确定每个子章节的内容范围（从当前标题到下一个标题之前）
        3. 提取每个子章节的内容，清理页眉、页码和Markdown标记
        4. 提取说明书标题（第一个子章节之前的内容）

        Args:
            text: 说明书全文文本（已清理页眉和页码）

        Returns:
            子章节字典，键为子章节名，值为子章节内容：
            {
                '说明书标题': '...',
                '技术领域': '...',
                '背景技术': '...',
                '发明内容': '...',  # 或 '实用新型内容'
                '附图说明': '...',
                '具体实施方式': '...',
            }
        """
        # 初始化结果字典，所有子章节默认为空字符串
        result = {
            '说明书标题': '',
            '技术领域': '',
            '背景技术': '',
            '附图说明': '',
            '具体实施方式': '',
        }
        # 动态添加发明内容/实用新型内容字段（根据专利类型不同）
        result[self.patent_info.content_field] = ''

        # 找到所有子章节的起始位置
        # 每个元素为 (位置, 子章节键名, 匹配到的标题文本)
        sub_positions = []
        for sub_key, pattern in DESCRIPTION_SUB_PATTERNS:
            for match in re.finditer(pattern, text):
                sub_positions.append((match.start(), sub_key, match.group()))
                break  # 只取第一个匹配（避免重复匹配同一子章节）

        # 特殊处理：说明书标题（通常是第一行直到第一个子章节）
        # 按位置排序，确保子章节按文本顺序处理
        sub_positions.sort(key=lambda x: x[0])

        # 提取每个子章节的内容
        # 每个子章节的范围：从当前标题位置到下一个标题位置（或文本末尾）
        for i, (pos, sub_key, header) in enumerate(sub_positions):
            next_pos = sub_positions[i + 1][0] if i + 1 < len(sub_positions) else len(text)

            content = text[pos:next_pos].strip()
            # 去除标题行本身（只保留标题后面的内容）
            content = re.sub(r'^#{0,2}\s*' + re.escape(header) + r'\s*', '', content, count=1).strip()
            # 清理页眉和页码
            content = self._clean_pdf_artifacts(content)
            # 清理 MinerU 输出中的 Markdown 标题标记残留
            content = re.sub(r'\n\s*#{1,3}\s*$', '', content).strip()
            content = re.sub(r'\n\s*#{1,3}\s*\n', '\n', content).strip()
            # 清理孤立的 ## 标记（MinerU 输出中页分隔标记）
            content = re.sub(r'^#{1,3}\s*$', '', content, flags=re.MULTILINE).strip()
            # 清理段落换行：去除\n，以[XXXX]段落号分隔段落
            content = self._clean_paragraph_breaks(content)

            # 将英文键名映射为中文键名，存入结果字典
            if sub_key == 'technical_field':
                result['技术领域'] = content
            elif sub_key == 'background':
                result['背景技术'] = content
            elif sub_key == 'invention_content':
                result[self.patent_info.content_field] = content
            elif sub_key == 'drawings_description':
                result['附图说明'] = content
            elif sub_key == 'detailed_description':
                result['具体实施方式'] = content

        # 提取说明书标题（第一个子章节之前的内容）
        # 说明书标题通常是专利名称，位于"技术领域"之前
        if sub_positions:
            first_pos = sub_positions[0][0]
            title_text = text[:first_pos].strip()
            # 清理页眉和页码
            title_text = self._clean_pdf_artifacts(title_text)
            # 清理 Markdown 标题标记（如 "# " 或 "## "）
            title_text = re.sub(r'^#{1,3}\s*', '', title_text).strip()
            # 清理标题后的 Markdown 标记残留（如 "##"、"###"）
            title_text = re.sub(r'\n\s*#{1,3}\s*$', '', title_text).strip()
            title_text = re.sub(r'\n\s*#{1,3}\s*\n', '\n', title_text).strip()
            # 清理多余的空行
            title_text = re.sub(r'\n{2,}', '', title_text).strip()
            # 清理标题末尾残留的 # 号
            title_text = re.sub(r'\s*#+\s*$', '', title_text).strip()
            result['说明书标题'] = title_text

        return result

    def _get_total_pages(self) -> int:
        """获取 PDF 总页数。

        对于逐页模式：直接返回页面列表的长度。
        对于 MinerU 单页模式：返回 0（因为所有文本合并为 1 页，无法从此处获取真实页数），
        调用方需通过 PDFReader._get_page_count() 获取真实页码。

        Returns:
            PDF 总页数（MinerU模式返回0）
        """
        if self._is_mineru_single_page:
            return 0
        return len(self.pages)

    def _apply_page_counts_to_drawings_range(self, total_pages: int):
        """对 MinerU 单页模式，使用页数信息推算说明书附图的精确页码范围。

        在 MinerU 单页模式下，无法通过页眉检测获取附图的页码范围。
        但如果从首页提取到了页数信息（X/Y/Z），可以推算出附图占据最后Z页。

        推算公式：附图起始页 = 总页数 - 附图页数 + 1，附图结束页 = 总页数

        Args:
            total_pages: PDF 实际总页数（通过 fitz/PDFReader 获取，非MinerU输出）
        """
        if not self.patent_info._has_page_counts:
            return

        z = self.patent_info.drawings_pages
        if z > 0 and total_pages > 0:
            # 附图占据最后 Z 页
            self.patent_info.drawings_page_range = (
                total_pages - z + 1,
                total_pages,
            )
            logger.info(
                f"基于页数信息推算附图范围: "
                f"第{total_pages - z + 1}-{total_pages}页 (共{z}页)"
            )

    def _extract_drawings_range(self, sections: Dict[str, Tuple[int, int]]):
        """记录说明书附图页码范围。

        优先级：
        1. 如果已通过 _apply_page_counts_to_drawings_range 设置了精确范围
           （基于首页页数信息推算），则直接使用
        2. 否则使用 sections 字典中的页码范围（来自页眉检测或页数计算）

        Args:
            sections: 章节页码范围字典，需包含 'drawings' 键
        """
        if 'drawings' in sections:
            start, end = sections['drawings']
            # 修正：sections 中的 range 可能不准确（如页眉检测只标记开始页）
            # 如果已有 page_counts 推算的范围（更精确），优先使用
            if self.patent_info._has_page_counts and self.patent_info.drawings_page_range != (0, 0):
                # page_counts 推算的范围更精确，已通过 _apply_page_counts_to_drawings_range 设置
                # 无需覆盖，直接跳过
                pass
            else:
                self.patent_info.drawings_page_range = (start, end)
            logger.info(f"说明书附图页码范围: {self.patent_info.drawings_page_range}")
        else:
            logger.warning("未找到说明书附图章节")

    def extract_figure_refs(self) -> List[str]:
        """
        从附图说明中提取图号引用列表。

        在说明书的"附图说明"子章节中，每个图都有编号引用，如"图1"、"图2"等。
        此方法提取所有不重复的图号引用，按序号排序后返回。

        Returns:
            图号引用列表，每个元素为字典，包含：
            - '序号': 图的数字编号（int类型）
            - '引用': 图号引用文本（如"图1"、"图2"）
            例如：[{'序号': 1, '引用': '图1'}, {'序号': 2, '引用': '图2'}, ...]
            如果没有附图说明内容，返回空列表
        """
        desc_text = self.patent_info.description.get('附图说明', '')
        if not desc_text:
            return []

        # 匹配 "图1"、"图2"、"图10" 等引用
        # 图号可能出现在"附图说明"文本中的任意位置
        figure_refs = []
        seen = set()  # 用于去重（同一图号可能被多次引用）

        for match in re.finditer(r'图\s*(\d+)', desc_text):
            fig_num = match.group(1)
            if fig_num not in seen:
                seen.add(fig_num)
                figure_refs.append({
                    '序号': int(fig_num),
                    '引用': f'图{fig_num}',
                })

        # 按图号序号排序（确保图1、图2、图10的顺序正确）
        figure_refs.sort(key=lambda x: x['序号'])
        logger.info(f"从附图说明中提取到 {len(figure_refs)} 个图号引用")
        return figure_refs
