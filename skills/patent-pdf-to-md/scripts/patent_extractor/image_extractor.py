"""专利附图提取模块 —— 从专利 PDF 中提取"说明书附图"章节的页面图片。

本模块的核心职责：
    将专利 PDF 中"说明书附图"章节所覆盖的每一页，渲染为一张 PNG 图片并保存到指定目录。

核心原则：
    - 仅提取"说明书附图"章节范围内的图片，不提取摘要附图（摘要附图通常只有一张，
      且位于专利文档的开头部分，与说明书附图是不同的章节）
    - 每张提取的图片代表说明书附图章节中的**完整页面内容**（一页中可能包含一个或
      多个附图元素，例如图1、图2可能出现在同一页上）
    - 所有图片按原始页面顺序命名（figPage1.png, figPage2.png, ...），
      命名中的数字表示在说明书附图章节中的第几页，而非 PDF 的绝对页码
    - 使用 PyMuPDF (fitz) 库渲染 PDF 页面为 PNG 图片

统一提取策略：
    无论 PDF 是文本型（矢量图）还是图像型（扫描件），均采用相同的策略——
    按页面顺序逐页将整个页面渲染为一张图片。这样做的好处是：
    1. 无需区分 PDF 类型，逻辑简单统一
    2. 避免了从 PDF 中单独提取内嵌图片时可能出现的图片缺失、顺序错乱等问题
    3. 保留了页面原始布局，确保附图的完整性

使用示例：
    extractor = ImageExtractor(dpi=200)
    images = extractor.extract_drawing_images(
        pdf_path="patent.pdf",
        drawings_page_range=(5, 10),  # 说明书附图从第5页到第10页
        output_dir="images"
    )
"""

import logging   # 日志记录模块，用于输出提取过程中的信息、警告等
import os         # 操作系统接口模块，用于创建目录、拼接路径等文件操作
from typing import Dict, List, Optional, Tuple  # 类型注解模块，用于函数签名的类型提示

# 创建当前模块的日志记录器，名称为 'patent_extractor'，
# 与项目中其他模块的日志记录器保持统一的命名空间
logger = logging.getLogger('patent_extractor')


class ImageExtractor:
    """专利附图提取器 —— 仅提取说明书附图章节范围内的完整页面图片。

    该类负责将专利 PDF 中"说明书附图"章节覆盖的每一页渲染为 PNG 图片。
    采用"整页渲染"策略，即把每一页 PDF 当作一张图片来处理，而不是尝试
    从 PDF 中单独提取内嵌的图片对象。

    为什么采用整页渲染而不是提取内嵌图片？
        - 专利 PDF 的附图可能是矢量绘制的（文本型 PDF），也可能是扫描的
          图像（图像型 PDF），两种情况下图片的存储方式不同
        - 单独提取内嵌图片容易出现：图片缺失、顺序错乱、分辨率不一致等问题
        - 整页渲染能保证每页内容的完整性和正确的页面顺序

    属性：
        dpi (int): 渲染分辨率（每英寸点数），值越大图片越清晰但文件也越大，
                   默认 200 DPI，对于大多数专利附图来说清晰度足够
    """

    def __init__(self, dpi: int = 200):
        """初始化专利附图提取器。

        Args:
            dpi (int): 渲染 PDF 页面时的分辨率（Dots Per Inch，每英寸点数）。
                       - 值越大，生成的图片越清晰，但文件体积也越大
                       - 推荐值：150-300，其中 200 为默认值，在清晰度和文件大小之间取得平衡
                       - 低于 150 可能导致附图中的细节（如细线、小字）模糊不清
                       - 高于 300 对于屏幕阅读来说通常没有必要，且会显著增加文件体积
        """
        self.dpi = dpi

    def extract_drawing_images(
        self,
        pdf_path: str,
        drawings_page_range: Tuple[int, int],
        figure_refs: Optional[List[Dict]] = None,
        output_dir: str = "images",
    ) -> List[Dict]:
        """
        提取说明书附图章节的完整页面图片。

        该方法将专利 PDF 中"说明书附图"章节覆盖的每一页渲染为一张 PNG 图片。
        每张图片对应说明书附图范围内的一页 PDF 页面，按页面顺序命名为
        figPage1.png, figPage2.png, ... 。每张图片可能包含一个或多个附图元素。

        实现思路：
            1. 校验页码范围是否有效（start 和 end 都必须大于 0）
            2. 创建输出目录（如果不存在）
            3. 使用 PyMuPDF 打开 PDF 文件
            4. 遍历说明书附图章节覆盖的每一页：
               a. 检查页码是否超出 PDF 总页数，超出则停止
               b. 将该页渲染为指定 DPI 的 PNG 图片
               c. 保存图片到输出目录
               d. 记录图片信息到结果列表
            5. 关闭 PDF 文件并返回结果列表

        Args:
            pdf_path (str): 待提取的专利 PDF 文件的绝对或相对路径。
                            必须是一个有效的、可被 PyMuPDF 打开的 PDF 文件。

            drawings_page_range (Tuple[int, int]): 说明书附图章节在 PDF 中的页码范围，
                            格式为 (start_page, end_page)，使用 1-based 编号
                            （即第1页表示 PDF 的第一页）。
                            例如 (5, 10) 表示说明书附图从 PDF 第5页到第10页。
                            如果 start 或 end <= 0，视为无效范围，方法将返回空列表。

            figure_refs (Optional[List[Dict]]): 从附图说明中提取的图号引用列表。
                            这是一个保留参数，用于保持接口兼容性，当前实现中不再使用。
                            早期版本可能根据图号引用来定位和裁剪单个附图，但现在
                            采用整页渲染策略后不再需要此参数。

            output_dir (str): 图片输出目录的路径。提取的 PNG 图片将保存到此目录下。
                            如果目录不存在，会自动创建。默认为 "images"。

        Returns:
            List[Dict]: 提取结果列表，每个元素是一个字典，包含一张图片的信息。
                        字典格式为 {'文件路径': 'images/figPageN.png'}，
                        其中文件路径是相对于当前工作目录的路径。
                        如果页码范围无效，返回空列表 []。

                        示例返回值：
                        [
                            {'文件路径': 'images/figPage1.png'},
                            {'文件路径': 'images/figPage2.png'},
                        ]
        """
        import fitz  # 延迟导入 PyMuPDF 库，避免在模块加载时就依赖该库

        # 解构页码范围元组，start 为起始页码，end 为结束页码
        start, end = drawings_page_range

        # 校验页码范围的有效性：如果起始页或结束页 <= 0，说明页码范围无效
        # （例如上游解析未能识别到说明书附图章节时，可能传入 (0, 0)）
        if start <= 0 or end <= 0:
            logger.warning("说明书附图页码范围无效，跳过图片提取")
            return []

        logger.info(f"提取说明书附图: 第{start}-{end}页, DPI={self.dpi}")

        # 创建输出目录，exist_ok=True 表示如果目录已存在则不报错
        os.makedirs(output_dir, exist_ok=True)

        # 使用 PyMuPDF 打开 PDF 文件
        doc = fitz.open(pdf_path)
        images = []  # 用于收集所有提取图片的信息

        # 统一策略：按页面顺序逐页渲染完整页面为 PNG 图片
        # enumerate 为每页分配一个从 0 开始的序号 i，用于生成图片文件名
        # range(start, end + 1) 遍历从 start 到 end 的所有页码（含两端）
        for i, page_num in enumerate(range(start, end + 1)):
            # 安全检查：如果当前页码超出了 PDF 的总页数，说明传入的范围有误，停止提取
            # doc.page_count 是 PDF 的总页数
            if page_num > doc.page_count:
                logger.warning(f"页码 {page_num} 超出 PDF 总页数 ({doc.page_count})，停止提取")
                break

            # 获取 PDF 页面对象
            # 注意：fitz 使用 0-based 索引（第1页的索引为0），而 page_num 是 1-based 的，
            # 所以需要 page_num - 1 来转换为 fitz 的索引
            page = doc[page_num - 1]

            # 生成图片文件名：figPage1, figPage2, ...
            # i + 1 是因为 i 从 0 开始，而图片编号从 1 开始更符合阅读习惯
            fig_name = f'figPage{i + 1}'

            # 将当前 PDF 页面渲染为像素图（pixmap）
            # get_pixmap() 方法会将整个页面按指定 DPI 渲染为位图
            # DPI 越高，渲染出的图片分辨率越高、越清晰
            pix = page.get_pixmap(dpi=self.dpi)

            # 拼接输出文件的完整路径
            output_path = os.path.join(output_dir, f'{fig_name}.png')

            # 将渲染后的像素图保存为 PNG 文件
            pix.save(output_path)

            # 将图片信息添加到结果列表中
            # 注意：'文件路径' 使用的是相对路径 "images/figPageN.png"，
            # 这是为了在最终生成的 Markdown 文档中作为图片引用路径
            images.append({
                '文件路径': f'images/{fig_name}.png',
            })
            logger.info(f"已保存第{i + 1}张附图页: {output_path} (PDF第{page_num}页)")

        # 关闭 PDF 文档，释放资源
        doc.close()

        # 记录提取完成的摘要信息
        # min(end, start + len(images) - 1) 用于处理实际提取页数少于预期的情况
        # （例如 PDF 总页数不足时，实际提取的页数会少于 end - start + 1）
        logger.info(f"说明书附图提取完成，共 {len(images)} 张图片（第{start}-{min(end, start + len(images) - 1)}页）")
        return images
