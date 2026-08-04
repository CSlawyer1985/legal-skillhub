"""OCR 引擎模块（降级方案）。

为图像型（扫描件）PDF 提供文本识别能力。
优先使用 tesserocr（内置 libtesseract，无需外部二进制），
备选 pytesseract（需要系统安装 tesseract 命令行工具）。
使用 chi_sim 中文语言包。

注意：此模块为降级方案。首选 OCR 引擎为 MinerU flash-extract（集成在 pdf_reader.py），
仅在 MinerU 不可用时才使用 Tesseract。MinerU 的中文识别质量远超 Tesseract。

本模块的工作流程：
1. 初始化时配置OCR语言、DPI、缓存目录等参数
2. 通过 is_available 属性检测可用的OCR后端（tesserocr 或 pytesseract）
3. 对PDF逐页渲染为高分辨率位图，然后执行OCR识别
4. 对OCR识别结果进行文本清理（去空格、修正常见错误等）

两种OCR后端的区别：
- tesserocr: 直接调用 libtesseract 共享库，性能更好，无需外部进程
- pytesseract: 通过命令行调用 tesseract，需要系统安装 tesseract 二进制
"""

# logging: 用于记录模块运行时的日志信息
# os: 用于文件路径操作和目录创建
# re: 用于正则表达式匹配，主要在OCR文本清理时使用
import logging
import os
import re
from typing import List, Optional

# PageText: 页面文本数据类，包含页码、文本内容、来源等信息
from .pdf_reader import PageText

# 使用模块专属的logger，便于在日志中区分来源
logger = logging.getLogger('patent_extractor')

# 默认 tessdata 路径：与 scripts 同级的 tessdata 目录
# tessdata 目录存放 Tesseract 的语言数据文件（如 chi_sim.traineddata）
# 目录结构：项目根/tessdata/chi_sim.traineddata
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_TESSDATA_DIR = os.path.join(_SCRIPTS_DIR, 'tessdata')


class OCREngine:
    """Tesseract OCR 引擎封装（降级方案）。

    首选 OCR 引擎为 MinerU flash-extract，仅在 MinerU 不可用时使用 Tesseract。
    优先使用 tesserocr（直接调用 libtesseract 共享库），
    备选 pytesseract（调用 tesseract CLI）。

    使用方式：
        engine = OCREngine(lang="chi_sim", dpi=300)
        if engine.is_available:
            pages = engine.ocr_pdf_pages("patent.pdf")
    """

    def __init__(
        self,
        lang: str = "chi_sim",
        dpi: int = 300,
        cache_dir: Optional[str] = None,
        tessdata_dir: Optional[str] = None,
    ):
        """初始化OCR引擎。

        Args:
            lang: Tesseract 语言代码，默认为 "chi_sim"（简体中文）。
                  常用值包括 "chi_sim"（简体中文）、"eng"（英文）、
                  "chi_sim+eng"（中英文混合识别）
            dpi: 渲染PDF页面时的分辨率（每英寸像素数），默认300。
                 值越高识别精度越好，但处理速度越慢、内存占用越大。
                 推荐范围：200-400
            cache_dir: 页面图片缓存目录路径。若指定，则每页渲染的图片会保存到此目录，
                       便于调试和复用；若为None则不保存缓存图片
            tessdata_dir: tessdata 目录路径，存放语言数据文件。
                          若为None则使用默认路径（项目根目录下的 tessdata/）
        """
        self.lang = lang
        self.dpi = dpi
        self.cache_dir = cache_dir
        self.tessdata_dir = tessdata_dir or _DEFAULT_TESSDATA_DIR
        # OCR后端类型，初始为None，在 is_available 属性中首次检测时确定
        # 可能的值：'tesserocr' | 'pytesseract' | None（不可用）
        self._backend: Optional[str] = None

    @property
    def is_available(self) -> bool:
        """检查 OCR 后端是否可用。

        按优先级依次尝试两种OCR后端：
        1. tesserocr（优先）：直接调用 libtesseract 共享库，性能更好
        2. pytesseract（备选）：通过命令行调用 tesseract，兼容性更好

        检测逻辑：
        - 若 _backend 已确定（非None），直接返回True（避免重复检测）
        - 尝试导入 tesserocr 并初始化 API，成功则设置 _backend = 'tesserocr'
        - tesserocr 失败则尝试导入 pytesseract 并获取版本号，成功则设置 _backend = 'pytesseract'
        - 两者都失败则返回False并记录警告

        Returns:
            bool: True表示至少有一个OCR后端可用，False表示均不可用
        """
        # 若后端已确定，无需重复检测
        if self._backend is not None:
            return True
        # 优先尝试 tesserocr
        try:
            import tesserocr
            # 尝试初始化 tesserocr API，验证 tessdata 目录和语言包是否可用
            api = tesserocr.PyTessBaseAPI(
                path=self.tessdata_dir, lang=self.lang,
            )
            api.End()  # 立即释放资源，仅用于验证可用性
            self._backend = 'tesserocr'
            logger.info(f"OCR后端: tesserocr (tessdata={self.tessdata_dir})")
            return True
        except Exception as e:
            logger.debug(f"tesserocr 不可用: {e}")
        # 备选 pytesseract
        try:
            import pytesseract
            # 尝试获取 tesseract 版本号，验证 tesseract 命令行工具是否可用
            pytesseract.get_tesseract_version()
            self._backend = 'pytesseract'
            logger.info("OCR后端: pytesseract")
            return True
        except Exception as e:
            logger.debug(f"pytesseract 不可用: {e}")
        # 两种后端都不可用，记录警告并给出安装指引
        logger.warning(
            "Tesseract OCR 不可用。请安装 tesserocr 或 tesseract。"
            "\n  pip install tesserocr"
            "\n  或 brew install tesseract tesseract-lang && pip install pytesseract"
        )
        return False

    def ocr_pdf_pages(
        self, pdf_path: str, page_range: Optional[tuple] = None,
    ) -> List[PageText]:
        """
        对图像型PDF逐页执行OCR识别。

        处理流程：
        1. 打开PDF文件，确定页码范围
        2. 初始化 tesserocr API（若可用，复用同一实例提高效率）
        3. 逐页处理：
           a. 将PDF页面渲染为高分辨率位图（使用PyMuPDF/fitz）
           b. （可选）保存位图到缓存目录
           c. 将位图转换为PIL Image对象
           d. 调用OCR后端识别文本
           e. 清理OCR识别结果
        4. 释放资源，返回结果

        Args:
            pdf_path: PDF文件的绝对或相对路径
            page_range: 指定处理的页码范围，格式为 (start, end)，
                        页码从1开始计数（1-based）。例如 (1, 5) 表示处理第1到第5页。
                        若为None则处理所有页面

        Returns:
            List[PageText]: 每页OCR识别的结果列表，每个元素包含：
                - page_num: int，页码（1-based）
                - text: str，清理后的OCR识别文本
                - text_no_space: str，去除所有空格的文本（用于快速比对）
                - source: str，固定为"tesseract_ocr"
                若OCR不可用则返回空列表；若单页识别失败则该页文本为空字符串
        """
        # 先检查OCR后端是否可用
        if not self.is_available:
            logger.error("Tesseract OCR 不可用，无法识别图像型PDF文本")
            return []

        # fitz 即 PyMuPDF，用于PDF页面渲染
        import fitz

        logger.info(f"开始OCR识别: {pdf_path}, DPI={self.dpi}, lang={self.lang}")

        pages = []
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count

        # 确定实际处理的页码范围
        if page_range:
            start, end = page_range
            # 确保页码在有效范围内：不小于1，不大于总页数
            start = max(1, start)
            end = min(total_pages, end)
        else:
            # 未指定范围则处理所有页面
            start, end = 1, total_pages

        # 初始化 tesserocr API（复用同一实例提高效率）
        # tesserocr 的 API 实例可以重复使用，避免每页都重新初始化
        tess_api = None
        if self._backend == 'tesserocr':
            try:
                import tesserocr
                tess_api = tesserocr.PyTessBaseAPI(
                    path=self.tessdata_dir, lang=self.lang,
                )
            except Exception as e:
                logger.error(f"tesserocr 初始化失败: {e}")
                tess_api = None

        try:
            for page_num in range(start, end + 1):
                logger.info(f"OCR处理第 {page_num}/{total_pages} 页")
                # fitz 的页码索引从0开始，需要减1
                page = doc[page_num - 1]  # 0-based

                # 将PDF页面渲染为高分辨率位图
                # DPI越高，图片越清晰，OCR识别精度越好
                pix = page.get_pixmap(dpi=self.dpi)

                # 保存缓存（如配置了缓存目录）
                # 缓存可用于调试：查看渲染的图片质量，或复用避免重复渲染
                if self.cache_dir:
                    cache_path = os.path.join(
                        self.cache_dir, f"page_{page_num:03d}.png",
                    )
                    os.makedirs(self.cache_dir, exist_ok=True)
                    pix.save(cache_path)

                # 将 PyMuPDF 的 Pixmap 对象转换为 PIL Image 对象
                # PIL Image 是 tesserocr 和 pytesseract 都支持的输入格式
                from PIL import Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                try:
                    # 调用OCR后端识别图片中的文字
                    raw_text = self._recognize_image(img, tess_api)
                    # 清理OCR识别结果中的常见噪声
                    cleaned_text = self.clean_ocr_text(raw_text)

                    pages.append(PageText(
                        page_num=page_num,
                        text=cleaned_text,
                        # text_no_space: 去除所有空格的版本，用于快速文本比对
                        text_no_space=cleaned_text.replace(" ", ""),
                        source="tesseract_ocr",
                    ))
                except Exception as e:
                    # 单页识别失败不影响其他页面，记录错误后继续
                    logger.error(f"OCR第{page_num}页失败: {e}")
                    pages.append(PageText(
                        page_num=page_num,
                        text="",
                        text_no_space="",
                        source="tesseract_ocr",
                    ))
        finally:
            # 确保释放 tesserocr API 资源
            if tess_api is not None:
                tess_api.End()
            # 确保关闭PDF文档
            doc.close()

        logger.info(f"OCR完成，共识别 {len(pages)} 页")
        return pages

    def _recognize_image(self, img, tess_api=None) -> str:
        """使用可用后端识别单张图片文本。

        根据当前确定的OCR后端类型，调用对应的方法识别图片中的文字。
        优先使用 tesserocr（性能更好），备选使用 pytesseract。

        Args:
            img: PIL.Image 对象，待识别的图片
            tess_api: tesserocr.PyTessBaseAPI 实例（可选），
                      若提供且后端为 tesserocr，则复用该实例避免重复初始化；
                      若为None则回退到 pytesseract

        Returns:
            str: OCR识别的原始文本（未经清理），可能包含噪声和多余空格
        """
        if self._backend == 'tesserocr' and tess_api is not None:
            # 使用 tesserocr API 直接识别，性能优于 pytesseract
            tess_api.SetImage(img)
            return tess_api.GetUTF8Text()
        # 备选 pytesseract：通过命令行调用 tesseract
        import pytesseract
        return pytesseract.image_to_string(img, lang=self.lang)

    def clean_ocr_text(self, text: str) -> str:
        """清理OCR识别结果中的常见噪声。

        处理内容：
        - 去除中文字符间的多余空格（Tesseract常见问题）
        - 合并连续的空白行
        - 修正常见的形近字识别错误
        - 保留 INID 代码格式
        """
        if not text:
            return ""

        # 去除中文字符之间的多余空格
        # CJK统一汉字范围：\u4e00-\u9fff，CJK标点：\u3000-\u303f
        # 匹配：CJK字符 + 空格 + CJK字符，去掉中间空格
        text = re.sub(r'([\u4e00-\u9fff\u3000-\u303f])\s+([\u4e00-\u9fff\u3000-\u303f])', r'\1\2', text)
        # 多次执行直到没有更多匹配（处理连续多个CJK字符间都有空格的情况）
        prev = None
        while prev != text:
            prev = text
            text = re.sub(r'([\u4e00-\u9fff\u3000-\u303f])\s+([\u4e00-\u9fff\u3000-\u303f])', r'\1\2', text)

        # 合并过多的空白行（保留单个段落间距）
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 去除行首尾多余空格
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # 修正常见OCR错误（可根据实际效果扩展）
        corrections = {
            '说朋书': '说明书',
            '权刺要求书': '权利要求书',
            '权禾要求书': '权利要求书',
            '摘耍': '摘要',
            '技术领城': '技术领域',
            '具休实施方式': '具体实施方式',
            '具体买施方式': '具体实施方式',
            '背最技术': '背景技术',
            '实用新型内客': '实用新型内容',
            '发明内客': '发明内容',
        }
        for wrong, correct in corrections.items():
            if wrong in text:
                text = text.replace(wrong, correct)
                logger.debug(f"OCR修正: '{wrong}' → '{correct}'")

        return text.strip()
