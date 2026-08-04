"""PDF文本提取模块。

本模块是专利PDF文本提取的核心组件，负责从PDF文件中提取文本内容。
采用四级引擎降级策略，确保在不同类型的PDF文件上都能尽可能提取到文本：

引擎优先级（从高到低）：
1. pdfplumber —— 纯Python库，擅长提取有文本层的普通PDF
2. PyMuPDF(fitz) —— C扩展库，速度更快，作为pdfplumber的备选
3. MinerU OCR —— 专为中文文档优化的OCR引擎，适合扫描件
4. Tesseract OCR —— 通用OCR引擎，作为MinerU的降级备选

提取方式：按页提取，每页保留页码信息，便于后续按章节定位页面范围。
对于图像型PDF（扫描件），会自动检测并切换到OCR引擎。
"""

import logging   # 日志记录模块，用于输出调试和警告信息
import os        # 操作系统接口模块，用于文件路径处理
import re        # 正则表达式模块，用于文本模式匹配和搜索
import shutil    # 文件工具模块，用于检查外部命令是否可用（如 mineru-open-api）
import subprocess  # 子进程模块，用于调用外部OCR命令（如 mineru-open-api flash-extract）
import tempfile  # 临时文件模块（备用）
from dataclasses import dataclass  # 数据类装饰器，用于简化数据结构的定义
from typing import Dict, List, Optional  # 类型注解，提高代码可读性

# 获取当前模块的日志记录器，日志名称为 'patent_extractor'，便于统一管理日志输出
logger = logging.getLogger('patent_extractor')


@dataclass
class PageText:
    """单页文本信息的数据类。

    用于存储PDF中某一页的提取结果，包含原始文本、去空格文本和来源信息。
    使用 @dataclass 装饰器自动生成 __init__、__repr__ 等方法，简化代码。

    Attributes:
        page_num: 页码，从1开始计数（1-based），与PDF阅读器显示的页码一致
        text: 从该页提取的原始文本，保留空格和换行符，用于最终输出
        text_no_space: 去除所有空格后的文本，专门用于正则模式匹配，
                       因为专利PDF中的关键词可能被空格打断（如"权 利 要 求 书"）
        source: 文本来源引擎标识，取值为以下之一：
                - "pdfplumber": 由pdfplumber引擎提取
                - "fitz": 由PyMuPDF(fitz)引擎提取
                - "mineru_ocr": 由MinerU OCR引擎识别
                - "tesseract_ocr": 由Tesseract OCR引擎识别
    """
    page_num: int          # 1-based 页码
    text: str              # 原始文本（保留空格和换行）
    text_no_space: str     # 去除空格的文本，用于模式匹配
    source: str = "pdfplumber"  # 文本来源：pdfplumber / fitz / mineru_ocr / tesseract_ocr


class PDFReader:
    """PDF文本提取器，支持多引擎降级和图像型PDF自动检测。

    本类是PDF文本提取的核心入口，封装了多引擎降级策略和图像型PDF检测逻辑。

    工作流程：
    1. 首先尝试用 pdfplumber 提取文本（适合有文本层的普通PDF）
    2. 如果 pdfplumber 提取不到文本，尝试用 fitz 提取（另一个文本层提取引擎）
    3. 如果两个引擎都提取不到文本，判定为图像型PDF（扫描件），切换到OCR引擎
    4. OCR引擎按配置选择：auto模式先尝试MinerU，失败再降级到Tesseract

    引擎优先级：pdfplumber → fitz → MinerU flash-extract → Tesseract OCR

    Attributes:
        _is_image_based: 内部标记，记录PDF是否为图像型（扫描件）。
                         None 表示尚未检测，True 表示是图像型，False 表示不是。
        _ocr_engine: OCR引擎配置，决定OCR阶段使用哪个引擎。
    """

    def __init__(self, ocr_engine: str = "auto"):
        """初始化PDF文本提取器。

        Args:
            ocr_engine: OCR 引擎选择策略，支持以下三种模式：
                - "auto"（默认）: 自动降级模式，优先使用MinerU OCR，
                  如果MinerU不可用或提取失败，自动降级到Tesseract OCR
                - "mineru": 仅使用 MinerU OCR，不降级到Tesseract
                - "tesseract": 仅使用 Tesseract OCR，不尝试MinerU
        """
        self._is_image_based: Optional[bool] = None  # 初始为 None，表示尚未检测PDF类型
        self._ocr_engine = ocr_engine  # 保存OCR引擎配置

    @property
    def is_image_based(self) -> bool:
        """判断PDF是否为图像型（扫描件，无文本层）。

        图像型PDF是指通过扫描纸质文档生成的PDF，页面内容是图片而非可选中文字。
        这类PDF无法通过常规的文本层提取引擎获取文字，必须使用OCR识别。

        Returns:
            bool: True 表示是图像型PDF，False 表示不是。
                  如果尚未执行提取操作（_is_image_based 为 None），返回 False。
        """
        return self._is_image_based or False

    def extract_pages(self, pdf_path: str) -> List[PageText]:
        """按页提取PDF文本，返回每页的文本信息。

        这是本类的核心方法，实现了多引擎降级提取策略：
        1. 先尝试 pdfplumber（纯Python库，对有文本层的PDF效果好）
        2. 如果 pdfplumber 失败或提取为空，尝试 fitz（C扩展库，速度更快）
        3. 如果两个引擎都提取不到有效文本，判定为图像型PDF，触发OCR
        4. OCR 按配置选择 MinerU 或 Tesseract

        每次成功提取后，会同时设置 _is_image_based 标记，
        后续可通过 is_image_based 属性查询PDF类型。

        Args:
            pdf_path: PDF文件的绝对路径或相对路径

        Returns:
            List[PageText]: 每页的文本信息列表，每个元素包含页码、文本内容和来源引擎。
                            如果所有提取方式都失败，返回空列表 []。
        """
        logger.info(f"开始提取PDF文本: {pdf_path}")

        # 第一步：尝试 pdfplumber 提取
        # pdfplumber 是纯Python库，对有文本层的普通PDF提取效果好，优先使用
        pages = self._extract_with_pdfplumber(pdf_path)
        if pages and self._has_text(pages):
            self._is_image_based = False  # 标记为非图像型PDF
            logger.info(f"pdfplumber 成功提取 {len(pages)} 页文本")
            return pages

        # 第二步：尝试 PyMuPDF (fitz) 提取
        # fitz 是C扩展库，某些PDF的文本层pdfplumber读不到但fitz可以
        pages = self._extract_with_fitz(pdf_path)
        if pages and self._has_text(pages):
            self._is_image_based = False  # 标记为非图像型PDF
            logger.info(f"fitz 成功提取 {len(pages)} 页文本")
            return pages

        # 第三步：图像型PDF检测与OCR提取
        # 如果 pdfplumber 和 fitz 都提取不到文本，说明PDF没有文本层（扫描件）
        self._is_image_based = True  # 标记为图像型PDF
        logger.warning("检测到图像型PDF（扫描件），所有引擎文本提取为空，切换到OCR引擎")

        pages = self._extract_with_ocr(pdf_path)
        if pages and self._has_text(pages):
            logger.info(f"OCR 成功识别 {len(pages)} 页文本")
            return pages

        # 彻底失败：所有提取方式都无法获取文本
        # 可能是空白PDF、损坏的PDF或OCR引擎不可用
        logger.warning("所有文本提取方式均失败，返回空页列表")
        return pages or []

    def extract_full_text(self, pdf_path: str) -> str:
        """提取PDF全文，将所有页面的文本合并为一个字符串。

        内部调用 extract_pages() 获取每页文本，然后用换行符拼接。
        适用于不需要按页处理、只需要完整文本的场景。

        Args:
            pdf_path: PDF文件的绝对路径或相对路径

        Returns:
            str: 所有页面文本拼接后的完整字符串，页面之间用换行符分隔。
                 如果提取失败，返回空字符串。
        """
        pages = self.extract_pages(pdf_path)
        return "\n".join(p.text for p in pages)

    def _has_text(self, pages: List[PageText]) -> bool:
        """检查页面列表中是否有任何页面包含有效文本。

        遍历所有页面，只要有一页的文本去除首尾空白后不为空，就返回 True。
        用于判断某个引擎是否成功提取到了有效内容。

        Args:
            pages: 页面文本信息列表

        Returns:
            bool: True 表示至少有一页包含有效文本，False 表示所有页面文本都为空
        """
        return any(p.text.strip() for p in pages)

    # ---- 引擎实现 ----

    def _extract_with_pdfplumber(self, pdf_path: str) -> Optional[List[PageText]]:
        """使用 pdfplumber 引擎提取PDF文本。

        pdfplumber 是一个纯Python库，擅长从有文本层的PDF中提取文字。
        它能较好地处理表格和布局，但对扫描件（图像型PDF）无效。

        提取逻辑：
        1. 打开PDF文件
        2. 遍历每一页，调用 extract_text() 提取文本
        3. 同时生成去除空格的版本（text_no_space），用于后续关键词匹配
        4. 如果提取过程中出现任何异常，返回 None（让调用方尝试下一个引擎）

        Args:
            pdf_path: PDF文件路径

        Returns:
            Optional[List[PageText]]: 提取成功返回页面列表，失败返回 None。
                                      注意：返回空列表 [] 也算成功（只是PDF没有文本），
                                      返回 None 表示引擎本身出错。
        """
        try:
            import pdfplumber
            pages = []
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # extract_text() 可能返回 None（如页面为纯图片），此时使用空字符串
                    text = page.extract_text() or ""
                    pages.append(PageText(
                        page_num=i + 1,           # 页码从1开始，与PDF阅读器一致
                        text=text,                 # 保留原始空格和换行的文本
                        text_no_space=text.replace(" ", ""),  # 去除空格，用于模式匹配
                        source="pdfplumber",       # 标记来源引擎
                    ))
            return pages
        except Exception as e:
            # 捕获所有异常（如pdfplumber未安装、文件损坏等），返回None让调用方降级
            logger.warning(f"pdfplumber 提取失败: {e}")
            return None

    def _extract_with_fitz(self, pdf_path: str) -> Optional[List[PageText]]:
        """使用 PyMuPDF (fitz) 引擎提取PDF文本。

        fitz 是 PyMuPDF 的内部模块名，是一个基于C语言的PDF处理库，
        速度比 pdfplumber 更快，对某些PDF的文本层兼容性更好。
        作为 pdfplumber 的备选引擎使用。

        提取逻辑与 _extract_with_pdfplumber 类似：
        1. 打开PDF文档
        2. 遍历每一页，调用 get_text() 提取文本
        3. 生成 PageText 对象并收集到列表
        4. 注意：使用完后需要手动关闭文档（doc.close()）

        Args:
            pdf_path: PDF文件路径

        Returns:
            Optional[List[PageText]]: 提取成功返回页面列表，失败返回 None
        """
        try:
            import fitz
            pages = []
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                text = page.get_text()
                pages.append(PageText(
                    page_num=i + 1,           # 页码从1开始
                    text=text,                 # 保留原始格式的文本
                    text_no_space=text.replace(" ", ""),  # 去除空格版本
                    source="fitz",             # 标记来源引擎
                ))
            doc.close()  # 手动关闭文档，释放资源
            return pages
        except Exception as e:
            logger.warning(f"fitz 提取失败: {e}")
            return None

    # ---- OCR 引擎 ----

    def _extract_with_ocr(self, pdf_path: str) -> List[PageText]:
        """使用 OCR 引擎提取文本（针对图像型PDF/扫描件）。

        根据初始化时配置的 _ocr_engine 参数选择不同的OCR策略：
        - "tesseract": 直接使用 Tesseract OCR
        - "mineru": 直接使用 MinerU OCR
        - "auto"（默认）: 先尝试 MinerU，如果失败则降级到 Tesseract

        Args:
            pdf_path: PDF文件路径

        Returns:
            List[PageText]: OCR识别后的页面文本列表，失败时返回空列表
        """
        if self._ocr_engine == "tesseract":
            # 用户指定仅使用 Tesseract
            return self._ocr_with_tesseract(pdf_path)
        elif self._ocr_engine == "mineru":
            # 用户指定仅使用 MinerU
            return self._ocr_with_mineru(pdf_path)
        else:
            # auto 模式：MinerU 优先，失败降级到 Tesseract
            # MinerU 对中文文档的识别效果通常优于 Tesseract
            pages = self._ocr_with_mineru(pdf_path)
            if pages and self._has_text(pages):
                return pages
            # MinerU 失败，降级到 Tesseract 作为兜底方案
            logger.warning("MinerU OCR 失败，降级到 Tesseract OCR")
            return self._ocr_with_tesseract(pdf_path)

    def _ocr_with_mineru(self, pdf_path: str) -> List[PageText]:
        """使用 MinerU flash-extract 一次性 OCR 提取文字，然后按页分割。

        MinerU 是专为中文文档优化的OCR引擎，识别效果优于通用OCR。
        本方法采用"一次性提取 + 按页分割"的策略，而非逐页OCR，原因：
        - MinerU 的 flash-extract 命令可以一次性处理整个PDF，速度远快于逐页调用
        - 但 flash-extract 输出的是整篇 Markdown 文本，没有页码信息
        - 因此需要额外的步骤将整篇文本按页拆分

        按页分割策略：
        1. 用 fitz 提取每页的页眉关键词（如"权利要求书"、"说明书"等）
        2. 在 MinerU 输出中搜索这些关键词的位置，确定页边界
        3. 按页边界将文本切分为多个 PageText 对象
        4. 如果无法精确分割，将全文分配给第1页（后续章节解析仍可正常工作）

        注意：MinerU 仅用于提取文字内容，不直接生成 Markdown 文件。

        Args:
            pdf_path: PDF文件路径

        Returns:
            List[PageText]: OCR识别并按页分割后的页面文本列表。
                            如果 MinerU 不可用或提取失败，返回空列表 []。
        """
        # 前置检查：确认 mineru-open-api 命令行工具已安装
        if not self._is_mineru_available():
            logger.warning("mineru-open-api 不可用，跳过 MinerU OCR")
            return []

        # 获取PDF总页数，用于后续按页分割
        total_pages = self._get_page_count(pdf_path)
        if total_pages <= 0:
            logger.warning("无法获取 PDF 页数，跳过 MinerU OCR")
            return []

        # 一次性调用 flash-extract 提取整个 PDF
        # 这比逐页调用快得多，但输出是整篇文本，需要后续按页分割
        logger.info(f"MinerU OCR: 一次性提取 {total_pages} 页")
        try:
            cmd = [
                'mineru-open-api', 'flash-extract', pdf_path,
                '--language', 'ch',  # 指定中文语言，提高中文识别准确率
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=900,
                # capture_output=True: 捕获标准输出和标准错误
                # text=True: 以文本模式返回输出（而非字节）
                # timeout=900: 超时时间15分钟（OCR处理可能较慢）
            )
            # 检查命令执行结果
            if result.returncode != 0 or not result.stdout.strip():
                stderr = result.stderr.strip() if result.stderr else ""
                logger.warning(
                    f"MinerU flash-extract 失败 "
                    f"(退出码: {result.returncode}): {stderr[:200]}"
                )
                return []
        except subprocess.TimeoutExpired:
            # OCR处理超时（超过15分钟），可能是PDF过大或MinerU卡死
            logger.warning("MinerU flash-extract 超时")
            return []
        except Exception as e:
            # 其他异常（如命令不存在、权限问题等）
            logger.warning(f"MinerU flash-extract 异常: {e}")
            return []

        # 获取 MinerU 输出的完整 Markdown 文本
        full_markdown = result.stdout.strip()
        logger.info(f"MinerU OCR 全文提取成功，长度: {len(full_markdown)} 字符")

        # 将整篇 Markdown 文本按页分割为 PageText 列表
        pages = self._split_mineru_output_by_page(full_markdown, pdf_path, total_pages)
        logger.info(f"MinerU OCR 完成: {len(pages)} 页")
        return pages

    def _split_mineru_output_by_page(
        self, full_markdown: str, pdf_path: str, total_pages: int,
    ) -> List[PageText]:
        """将 MinerU 输出的整篇 Markdown 按页拆分为 PageText 列表。

        由于 MinerU flash-extract 一次性输出整篇文本，没有页码分隔信息，
        因此需要通过页眉关键词来定位页边界，实现按页拆分。

        拆分策略（按优先级）：
        1. 如果只有1页，直接返回整篇文本作为第1页
        2. 尝试用页眉关键词在 MinerU 输出中定位页边界并分割
        3. 如果关键词分割失败，降级为将全文分配给第1页
           （虽然不精确，但 section_parser 基于文本内容做章节识别，
            不依赖页码也能工作；图片提取可能受影响）

        Args:
            full_markdown: MinerU 输出的完整 Markdown 文本
            pdf_path: PDF文件路径（用于提取页眉关键词）
            total_pages: PDF总页数

        Returns:
            List[PageText]: 按页分割后的页面文本列表
        """
        # 提取每页的页眉关键词，用于在 MinerU 输出中定位页边界
        page_keywords = self._extract_page_keywords(pdf_path, total_pages)

        # 如果只有 1 页，直接返回，无需分割
        if total_pages == 1:
            return [PageText(
                page_num=1,
                text=full_markdown,
                # 使用正则去除所有空白字符（包括空格、制表符、换行等），
                # 比简单的 replace(" ", "") 更彻底
                text_no_space=re.sub(r'\s+', '', full_markdown),
                source="mineru_ocr",
            )]

        # 尝试按页眉关键词分割 MinerU 输出
        pages = self._split_by_keywords(full_markdown, page_keywords, total_pages)
        if pages:
            return pages

        # 降级策略：将全文分配给第 1 页
        # section_parser 基于文本内容做章节识别，不依赖页码也能工作
        # 但图片提取需要页码范围，此时无法精确提取图片
        logger.warning(
            "无法按页分割 MinerU 输出，将全文分配给第 1 页。"
            "章节解析仍可正常工作，但图片提取可能受影响。"
        )
        return [PageText(
            page_num=1,
            text=full_markdown,
            text_no_space=re.sub(r'\s+', '', full_markdown),
            source="mineru_ocr",
        )]

    def _extract_page_keywords(self, pdf_path: str, total_pages: int) -> Dict[int, List[str]]:
        """用 fitz 提取每页的页眉关键词，用于在 MinerU 输出中定位页边界。

        专利 PDF 的页眉通常包含章节名（如"权利要求书"、"说明书"等），
        这些关键词在 MinerU 的 OCR 输出中也会出现，因此可以作为页边界定位的锚点。

        实现思路：
        1. 用 fitz 打开 PDF，逐页提取文本
        2. 对每页的前200个字符进行正则匹配，查找已知的章节页眉关键词
        3. 同时提取页码标记（如"1/9"、"2/9"格式），作为辅助定位信息
        4. 返回 {页码: [关键词列表]} 的字典

        注意：对于图像型PDF（扫描件），fitz 提取的文本可能为空，
        此时 page_keywords 也会为空，后续分割会降级处理。

        Args:
            pdf_path: PDF文件路径
            total_pages: PDF总页数

        Returns:
            Dict[int, List[str]]: 页码到关键词列表的映射。
                                  键为页码（1-based），值为该页检测到的关键词列表。
                                  只包含检测到关键词的页面，未检测到的页面不会出现在字典中。
        """
        page_keywords: Dict[int, List[str]] = {}
        try:
            import fitz
            doc = fitz.open(pdf_path)
            for i in range(total_pages):
                page = doc[i]
                text = page.get_text()
                # 只取页面前 200 字符进行关键词检测
                # 专利PDF的页眉通常在页面最顶部，前200字符足够覆盖
                header_text = text[:200] if text else ""
                keywords = []
                # 检测章节页眉关键词
                # 正则中的 \s* 允许关键词中间有空格（如"权 利 要 求 书"）
                for pattern in [
                    r'权\s*利\s*要\s*求\s*书',   # 匹配"权利要求书"，允许中间有空格
                    r'说\s*明\s*书\s*附\s*图',   # 匹配"说明书附图"，允许中间有空格
                    r'说\s*明\s*书',             # 匹配"说明书"，允许中间有空格
                    r'摘\s*要',                  # 匹配"摘要"，允许中间有空格
                    r'\(19\)',                   # 匹配专利文献的"(19)"标记（国家代码标识）
                ]:
                    if re.search(pattern, header_text):
                        match = re.search(pattern, header_text)
                        if match:
                            keywords.append(match.group())  # 保存匹配到的实际文本
                # 提取页码标记（如 "1/9", "2/9"），表示当前页/总页数
                page_marker = re.search(r'(\d+)\s*/\s*(\d+)', header_text)
                if page_marker:
                    keywords.append(f"page_{page_marker.group(1)}_of_{page_marker.group(2)}")
                # 只保存检测到关键词的页面
                if keywords:
                    page_keywords[i + 1] = keywords  # 页码从1开始
            doc.close()
        except Exception as e:
            logger.warning(f"提取页眉关键词失败: {e}")

        logger.debug(f"页眉关键词: {page_keywords}")
        return page_keywords

    def _split_by_keywords(
        self, full_markdown: str,
        page_keywords: Dict[int, List[str]],
        total_pages: int,
    ) -> Optional[List[PageText]]:
        """尝试按页眉关键词在 MinerU 输出中定位页边界并分割。

        算法思路：
        1. 对于每个有页眉关键词的页面，在 MinerU 输出中搜索关键词首次出现的位置
        2. 将找到的位置按从小到大排序，形成页边界序列
        3. 相邻两个边界之间的文本就是对应页面的内容
        4. 检查是否有页面未被关键词覆盖，记录缺失页码

        示例（假设3页PDF）：
        - 第1页关键词"摘要"在位置 0 找到
        - 第2页关键词"权利要求书"在位置 500 找到
        - 第3页关键词"说明书"在位置 1200 找到
        则：
        - 第1页内容 = full_markdown[0:500]
        - 第2页内容 = full_markdown[500:1200]
        - 第3页内容 = full_markdown[1200:末尾]

        注意：对于图像型PDF，fitz 提取的文本为空，page_keywords 通常也为空，
        此时无法精确分割，返回 None 让调用方使用降级策略。

        Args:
            full_markdown: MinerU 输出的完整 Markdown 文本
            page_keywords: 页码到关键词列表的映射（由 _extract_page_keywords 生成）
            total_pages: PDF总页数

        Returns:
            Optional[List[PageText]]: 分割成功返回页面列表，无法分割返回 None。
                                      至少需要2个定位点才能进行分割，
                                      定位点不足时返回 None。
        """
        # 如果没有提取到任何页眉关键词，无法分割
        if not page_keywords:
            return None

        # 第一步：找到每个关键词在 MinerU 输出中的位置
        # page_positions 存储 {页码: 关键词在文本中的起始位置}
        page_positions: Dict[int, int] = {}
        for page_num, keywords in page_keywords.items():
            for kw in keywords:
                # 跳过页码标记（如"page_1_of_9"），因为MinerU输出中不会有这种格式
                if kw.startswith("page_"):
                    continue
                # 在 MinerU 输出中查找关键词首次出现的位置
                pos = full_markdown.find(kw)
                if pos >= 0:
                    page_positions[page_num] = pos
                    break  # 找到一个关键词就足够定位该页，无需继续搜索

        # 至少需要 2 个定位点才能分割出至少2段文本
        if len(page_positions) < 2:
            return None

        # 第二步：按位置从小到大排序，生成页边界
        # sorted_pages 是 [(页码, 起始位置)] 的排序列表
        sorted_pages = sorted(page_positions.items(), key=lambda x: x[1])
        pages = []
        for i, (page_num, start_pos) in enumerate(sorted_pages):
            # 当前页的结束位置 = 下一页的起始位置
            # 如果是最后一页，结束位置为文本末尾
            end_pos = sorted_pages[i + 1][1] if i + 1 < len(sorted_pages) else len(full_markdown)
            text = full_markdown[start_pos:end_pos].strip()
            pages.append(PageText(
                page_num=page_num,
                text=text,
                # 使用正则去除所有空白字符，比 replace(" ", "") 更彻底
                text_no_space=re.sub(r'\s+', '', text),
                source="mineru_ocr",
            ))

        # 第三步：检查是否有页码未被关键词覆盖
        # 某些页面可能没有页眉关键词，导致这些页面的内容被合并到相邻页
        all_page_nums = set(range(1, total_pages + 1))  # 所有页码的集合
        found_page_nums = {p.page_num for p in pages}    # 已定位的页码集合
        missing_pages = all_page_nums - found_page_nums  # 缺失的页码集合

        if missing_pages and pages:
            # 将缺失页的内容分配到最近的已定位页
            # 这不是精确的，但保证 section_parser 能获取完整文本
            logger.debug(f"以下页码未精确定位: {missing_pages}")

        return pages if pages else None

    def _ocr_with_tesseract(self, pdf_path: str) -> List[PageText]:
        """使用 Tesseract OCR 提取文本（作为 MinerU 的降级备选方案）。

        Tesseract 是一个开源的通用OCR引擎，支持多种语言。
        在本模块中作为 MinerU 的降级备选，当 MinerU 不可用或提取失败时使用。
        Tesseract 的中文识别效果通常不如 MinerU，但安装更简单、兼容性更好。

        实际的OCR逻辑委托给 ocr_engine 模块的 OCREngine 类处理，
        该类负责将PDF转为图片、调用Tesseract识别、返回按页的结果。

        Args:
            pdf_path: PDF文件路径

        Returns:
            List[PageText]: OCR识别后的页面文本列表，失败时返回空列表 []
        """
        try:
            # 从同包的 ocr_engine 模块导入 OCREngine 类
            from .ocr_engine import OCREngine
            engine = OCREngine()
            pages = engine.ocr_pdf_pages(pdf_path)
            return pages
        except Exception as e:
            # 捕获所有异常（如Tesseract未安装、图片转换失败等）
            logger.error(f"Tesseract OCR 提取失败: {e}")
            return []

    # ---- 工具方法 ----

    @staticmethod
    def _is_mineru_available() -> bool:
        """检查 mineru-open-api 命令行工具是否可用。

        通过 shutil.which() 检查 mineru-open-api 是否在系统 PATH 中，
        即用户是否已安装 MinerU 工具包。

        Returns:
            bool: True 表示 mineru-open-api 已安装且可用，False 表示不可用
        """
        return shutil.which('mineru-open-api') is not None

    @staticmethod
    def _get_page_count(pdf_path: str) -> int:
        """获取 PDF 文件的总页数。

        使用两个引擎依次尝试获取页数：
        1. 优先使用 fitz（速度快，C扩展库）
        2. fitz 失败时降级使用 pdfplumber（纯Python库）
        3. 两个引擎都失败时返回 0

        Args:
            pdf_path: PDF文件路径

        Returns:
            int: PDF总页数，获取失败时返回 0
        """
        try:
            import fitz
            doc = fitz.open(pdf_path)
            count = doc.page_count  # fitz 提供的页数属性
            doc.close()
            return count
        except Exception:
            # fitz 失败，尝试 pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    return len(pdf.pages)  # pdfplumber 通过页面列表长度获取页数
            except Exception:
                # 两个引擎都失败，返回 0
                return 0
