"""中国专利公开公告PDF结构化信息提取工具。

主入口脚本，编排完整流程：
PDF文本提取 → 章节识别 → 图片提取 → JSON生成 → Markdown生成

整体架构说明：
- PDFReader: 负责从PDF文件中提取文本内容，支持多种OCR引擎（pdfplumber/fitz/MinerU/Tesseract）
- SectionParser: 负责将提取的文本按专利文档结构拆分为各个章节（著录项目、权利要求书、说明书等）
- ImageExtractor: 负责从PDF中提取说明书附图，并按图号命名保存
- JSONGenerator: 负责将结构化的专利信息生成为JSON格式
- MarkdownGenerator: 负责将结构化的专利信息生成为Markdown格式

支持的专利类型：
- 发明专利公开（A类）
- 发明专利公告（B类）
- 实用新型公告（U类）
"""

# 标准库导入
import argparse   # 命令行参数解析库，用于解析用户输入的命令行参数
import logging    # 日志记录库，用于记录程序运行状态和调试信息
import os         # 操作系统接口库，用于文件路径操作和目录创建
import sys        # 系统相关库，用于标准输出/错误输出和程序退出
import time       # 时间库，用于生成带时间戳的日志文件名
from pathlib import Path  # 路径操作库，提供面向对象的路径处理方式

# 项目内部模块导入
from .pdf_reader import PDFReader              # PDF文本提取器，支持多种OCR引擎
from .docx_reader import DocxReader            # DOCX/DOC文本提取器
from .section_parser import SectionParser, PatentInfo  # 章节解析器和专利信息数据类
from .office_action_parser import OfficeActionParser, detect_office_action_type  # 审查文件解析器
from .image_extractor import ImageExtractor    # 附图图片提取器
from .json_generator import JSONGenerator      # JSON格式生成器
from .markdown_generator import MarkdownGenerator  # Markdown格式生成器

# 创建当前模块的日志记录器，使用 'patent_extractor' 作为日志名称
# 这样所有子模块中同名的 logger 都会归属到同一个日志层级下
logger = logging.getLogger('patent_extractor')


def _validate_drawings_count(patent_info: PatentInfo, images: list):
    """附图页数验证：比对实际提取的图片张数与著录项目记载的附图页数。

    验证流程：
    a) 从专利PDF首页提取的"附图多少页"作为基准数据（drawings_pages）
    b) 统计实际提取的图片张数（len(images)）
    c) 进行数值比对，不一致则触发错误

    这是一种质量保障机制：中国专利文档首页会记载"附图Z页"信息，
    如果实际提取的附图数量与记载不一致，说明可能存在以下问题：
    - PDF文件不完整（部分页面缺失）
    - 附图章节范围识别错误（将非附图页误判为附图页，或反之）
    - OCR识别错误导致首页信息提取不准确

    Args:
        patent_info: 解析后的专利信息对象，包含 drawings_pages（著录项目记载的附图页数）
                     和 drawings_page_range（附图在PDF中的页码范围）等字段
        images: 实际从PDF中提取的附图图片列表，每个元素代表一张附图

    Raises:
        ValueError: 当实际提取数与记载页数不一致时抛出，提示用户检查PDF完整性
    """
    # 获取实际提取的图片数量
    actual_count = len(images)
    # 获取专利首页著录项目中记载的附图页数（即"附图Z页"中的Z值）
    expected = patent_info.drawings_pages

    # 质量日志：记录提取时间、页数信息及验证结果
    logger.info(f"附图页数验证 - 著录项目记载: 附图{expected}页")
    logger.info(f"附图页数验证 - 实际提取: {actual_count}张图片")
    logger.info(
        f"附图页码范围: 第{patent_info.drawings_page_range[0]}"
        f"-{patent_info.drawings_page_range[1]}页"
    )

    if expected <= 0:
        # 未从首页提取到页数信息（可能 OCR 失败或格式异常），记录警告但不阻断
        # 这种情况下无法进行数值比对，因此跳过验证，但建议人工核对
        logger.warning(
            "附图页数验证 - 首页未找到'附图Z页'记载信息，跳过数量校验。"
            f"实际提取 {actual_count} 张图片，建议人工核对。"
        )
        return

    if actual_count != expected:
        # 实际提取数量与记载不一致，说明提取过程可能存在问题
        # 抛出 ValueError 阻断流程，强制用户检查PDF完整性或附图范围设置
        error_msg = (
            f"附图页数不一致！著录项目记载附图{expected}页，"
            f"实际提取{actual_count}张图片。"
            f"请检查 PDF 文件完整性或附图章节范围是否正确。"
        )
        logger.error(f"附图页数验证失败 - {error_msg}")
        raise ValueError(error_msg)

    # 验证通过，实际提取数与记载数一致
    logger.info(f"附图页数验证通过 - 提取数({actual_count}) == 记载数({expected})")


def setup_logging(output_dir: str, verbose: bool = False) -> logging.Logger:
    """初始化日志系统，同时配置控制台输出和文件输出两个日志通道。

    日志系统设计说明：
    - 控制台通道：实时显示程序运行状态，日志级别跟随 verbose 参数
    - 文件通道：将所有日志（包括DEBUG级别）持久化保存到文件，便于事后排查问题
    - 两个通道使用不同的日志级别：控制台可控制详细程度，文件始终记录全部信息

    Args:
        output_dir: 输出目录路径，日志文件将保存在该目录下的 logs/ 子目录中
        verbose: 是否启用详细日志模式。True 时日志级别为 DEBUG（显示所有调试信息），
                 False 时日志级别为 INFO（仅显示一般信息及以上），默认为 False

    Returns:
        logging.Logger: 配置好的日志记录器实例，后续可直接使用该实例记录日志
    """
    # 根据 verbose 参数决定日志级别：DEBUG 显示最详细的信息（包括变量值、执行路径等），
    # INFO 只显示一般运行信息（步骤进度、结果摘要等）
    level = logging.DEBUG if verbose else logging.INFO

    # 获取名为 "patent_extractor" 的日志记录器
    # 该名称与模块级 logger 相同，确保所有子模块的日志都通过同一个记录器输出
    logger = logging.getLogger("patent_extractor")
    logger.setLevel(level)

    # === 配置控制台日志通道 ===
    # 将日志输出到标准输出（sys.stdout），用户可以在终端实时查看
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)  # 控制台日志级别跟随 verbose 设置
    # 日志格式：时间 日志级别 记录器名称: 日志消息
    # 例如：14:30:25 [INFO] patent_extractor: PDF文本提取完成
    console.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',  # 时间格式仅显示时分秒，不显示日期（控制台查看无需日期）
    ))
    logger.addHandler(console)

    # === 配置文件日志通道 ===
    # 日志文件保存在输出目录的 logs/ 子目录下，文件名包含时间戳以避免覆盖
    log_dir = os.path.join(output_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)  # 如果目录不存在则自动创建，已存在不报错
    # 日志文件名格式：extract_YYYYMMDD_HHMMSS.log，例如 extract_20240115_143025.log
    log_file = os.path.join(log_dir, f"extract_{time.strftime('%Y%m%d_%H%M%S')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')  # 使用UTF-8编码支持中文
    file_handler.setLevel(logging.DEBUG)  # 文件始终记录DEBUG及以上级别的所有日志
    # 文件日志格式与控制台相同，但包含完整日期时间（便于事后追溯）
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    ))
    logger.addHandler(file_handler)

    # 记录日志文件路径，方便用户找到日志文件
    logger.info(f"日志文件: {log_file}")
    return logger


def main():
    """程序主入口函数，编排专利PDF结构化信息提取的完整流程。

    执行流程共6个步骤：
    1. PDF文本提取：使用PDFReader从PDF文件中提取每页的文本内容
    2. 章节识别与拆分：使用SectionParser将文本按专利文档结构拆分为各章节
    3. 图号引用提取：从"说明书附图标记"章节中提取所有图号引用（如"图1"、"图2"）
    4. 说明书附图提取：使用ImageExtractor从PDF中提取附图图片并保存
    5. JSON生成：将结构化的专利信息输出为JSON格式文件
    6. Markdown生成：将结构化的专利信息输出为Markdown格式文件

    命令行参数说明：
    --input/-i:  必填，输入的PDF文件路径
    --output/-o: 必填，输出目录路径（所有结果文件将保存在此目录下）
    --verbose/-v: 可选，启用详细日志模式（DEBUG级别）
    --keep-ocr-cache: 可选，保留OCR过程中的临时缓存文件（默认会自动清理）
    --dpi: 可选，附图渲染的DPI值，默认200（值越大图片越清晰但文件越大）
    --ocr-engine: 可选，OCR引擎选择，默认auto（自动逐级降级）

    Returns:
        None（正常执行完毕无返回值，出错时通过 sys.exit(1) 退出）
    """
    # === 命令行参数解析 ===
    # 使用 argparse 库定义和解析命令行参数
    parser = argparse.ArgumentParser(
        description='中国专利公开公告PDF结构化信息提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,  # 保留epilog中的原始格式
        epilog="""
示例:
  python -m patent_extractor.main --input patent.pdf --output ./output/
  python -m patent_extractor.main --input patent.pdf --output ./output/ --verbose
        """,
    )
    # --input: 必填参数，指定要处理的文件路径（支持 PDF、DOCX、DOC 格式）
    parser.add_argument('--input', '-i', required=True, help='输入文件路径（支持 PDF/DOCX/DOC）')
    # --output: 必填参数，指定输出目录，提取结果将保存在该目录下
    parser.add_argument('--output', '-o', required=True, help='输出目录路径')
    # --verbose: 可选标志，启用后日志级别降为DEBUG，输出更详细的调试信息
    parser.add_argument('--verbose', '-v', action='store_true', help='输出详细日志')
    # --keep-ocr-cache: 可选标志，OCR过程中会产生临时文件，默认自动清理，此选项保留它们
    parser.add_argument('--keep-ocr-cache', action='store_true', help='保留OCR临时缓存文件')
    # --dpi: 图片渲染分辨率，DPI越高图片越清晰但文件体积越大，200是兼顾清晰度和体积的平衡值
    parser.add_argument('--dpi', type=int, default=200, help='图片渲染DPI (默认: 200)')
    # --ocr-engine: OCR引擎选择策略
    # auto: 自动降级策略，依次尝试 pdfplumber → fitz → MinerU → Tesseract
    # mineru: 强制使用MinerU引擎（高质量但需要额外安装）
    # tesseract: 强制使用Tesseract引擎（开源OCR，识别质量较低）
    parser.add_argument('--ocr-engine', choices=['auto', 'mineru', 'tesseract'],
                        default='auto', help='OCR引擎选择: auto(默认,pdfplumber→fitz→MinerU→Tesseract逐级降级)/mineru/tesseract')
    args = parser.parse_args()  # 解析命令行参数，结果存储在 args 对象中

    # 验证输入文件是否存在，如果文件路径无效则直接退出程序
    if not os.path.isfile(args.input):
        print(f"错误: 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 初始化日志系统（控制台 + 文件双通道），返回配置好的 logger 实例
    logger = setup_logging(args.output, args.verbose)
    # 打印程序启动横幅，便于在日志中标识本次运行
    logger.info("=" * 60)
    logger.info("中国专利公开公告PDF结构化信息提取工具")
    logger.info("=" * 60)
    logger.info(f"输入文件: {args.input}")
    logger.info(f"输出目录: {args.output}")

    try:
        # 检测文件类型并选择对应的文本提取器
        input_ext = Path(args.input).suffix.lower()
        is_docx_input = input_ext in ('.docx', '.doc')

        # ===== 步骤 1: 文本提取 =====
        if is_docx_input:
            # DOCX/DOC 文件处理流程
            logger.info("--- 步骤 1/5: DOCX/DOC 文本提取 ---")
            reader = DocxReader()
            pages = reader.extract_pages(args.input)
            is_image_based = False
        else:
            # PDF 文件处理流程（原有逻辑）
            logger.info("--- 步骤 1/6: PDF文本提取 ---")
            reader = PDFReader(ocr_engine=args.ocr_engine)
            pages = reader.extract_pages(args.input)
            is_image_based = reader.is_image_based

        if not pages:
            # 如果所有页面都提取失败，无法继续后续步骤，直接退出
            logger.error("文本提取完全失败，无法继续")
            sys.exit(1)

        # 记录提取结果
        logger.info(f"文本提取完成: {len(pages)} 页, "
                     f"文件类型: {'DOCX/DOC' if is_docx_input else 'PDF'}, "
                     f"图像型: {is_image_based}")

        # ===== 文档类型检测 =====
        # 先检测是否为审查文件（审查意见通知书/驳回决定/复审决定书）
        # 如果是，使用 OfficeActionParser 解析；否则使用 SectionParser
        preview_text = "\n".join(p.text for p in pages[:2]) if len(pages) >= 2 else pages[0].text
        doc_type = detect_office_action_type(preview_text[:3000])

        if doc_type:
            # 审查文件处理流程
            _process_office_action(pages, reader if not is_docx_input else None, doc_type, args, logger, is_image_based, is_docx_input)
        elif is_docx_input:
            # DOCX/DOC 专利公开/公告文件处理流程
            _process_docx_patent_publication(pages, args, logger)
        else:
            # PDF 专利公开/公告文件处理流程（原有逻辑）
            _process_patent_publication(pages, reader, args, logger)

    except Exception as e:
        # 捕获所有未处理的异常，记录完整的错误堆栈信息后退出
        # logger.exception() 会自动输出异常的完整堆栈跟踪，便于定位问题
        logger.exception(f"处理过程中发生错误: {e}")
        sys.exit(1)  # 以非零退出码退出，表示程序异常终止


def _sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符。"""
    illegal_chars = '\\/:*?"<>|'
    for char in illegal_chars:
        name = name.replace(char, '')
    return name


def _ensure_unique_base_name(base_name: str, output_dir: str) -> str:
    """确保 base_name 在输出目录中唯一，避免不同案件编号的文档合并到同一文件夹。

    当检测到目标目录中已存在同名文件时，自动追加递增后缀（_2, _3, ...），
    确保不同案件编号的文档存储在独立的子文件夹中。

    Args:
        base_name: 原始命名基础字符串
        output_dir: 输出目录路径

    Returns:
        唯一的命名基础字符串（如有冲突则带后缀）
    """
    if not os.path.isdir(output_dir):
        return base_name

    # 检查输出目录中是否已存在同名的 json/md/txt 文件
    conflicting_exts = ('.json', '.md', '.txt')
    for ext in conflicting_exts:
        if os.path.isfile(os.path.join(output_dir, f"{base_name}{ext}")):
            # 存在冲突，追加递增后缀
            suffix = 2
            while True:
                candidate = f"{base_name}_{suffix}"
                if not any(os.path.isfile(os.path.join(output_dir, f"{candidate}{e}")) for e in conflicting_exts):
                    logger.info(f"base_name 碰撞检测: '{base_name}' 已存在，使用 '{candidate}'")
                    return candidate
                suffix += 1

    return base_name


def _build_base_name_patent(patent_info: PatentInfo) -> str:
    """构建专利公开/公告文件的命名基础字符串。

    格式：{申请号}-{公开号/公告号}-{文本类型}
    示例：202210373749.5-CN114909579A-公开文本
    """
    申请号 = patent_info.bibliographic.get('申请号', '')
    公开号 = patent_info.bibliographic.get('申请公布号', '').replace(' ', '')
    公告号 = patent_info.bibliographic.get('授权公告号', '').replace(' ', '')
    publication_number = 公开号 or 公告号

    if patent_info.publication_type == '公开':
        文本类型 = '公开文本'
    elif patent_info.publication_type == '公告':
        文本类型 = '公告文本'
    else:
        文本类型 = '文本'

    parts = []
    if 申请号:
        parts.append(申请号)
    if publication_number:
        parts.append(publication_number)
    parts.append(文本类型)

    return _sanitize_filename('-'.join(parts))


def _build_base_name_office_action(oa_info) -> str:
    """构建审查文件的命名基础字符串。

    审查意见通知书：{申请号}-{审查次数}{文档类型}-{发文序号}
    驳回决定：{申请号}-{文档类型}-{发文序号}
    复审决定书：{申请号}-{文档类型}-{发文序号}-{案件编号}
    无效宣告请求审查决定书：{申请号}-{文档类型}-{决定日}-{案件编号}
    """
    # 文档类型名称映射（代码内部常量 → 规范名称）
    doc_type_names = {
        '审查意见通知书': '审查意见通知书',
        '驳回决定': '驳回决定书',
        '复审决定书': '复审决定书',
        '无效宣告请求审查决定书': '无效宣告请求审查决定书',
    }
    doc_type_name = doc_type_names.get(oa_info.doc_type, oa_info.doc_type)
    申请号 = oa_info.申请号

    if oa_info.doc_type == '审查意见通知书':
        # {申请号}-{审查次数}{文档类型}-{发文序号}
        审查次数 = oa_info.审查次数
        parts = [申请号, f'{审查次数}{doc_type_name}' if 审查次数 else doc_type_name]
        if oa_info.发文序号:
            parts.append(oa_info.发文序号)
    elif oa_info.doc_type == '驳回决定':
        # {申请号}-{文档类型}-{发文序号}
        parts = [申请号, doc_type_name]
        if oa_info.发文序号:
            parts.append(oa_info.发文序号)
    elif oa_info.doc_type == '复审决定书':
        # {申请号}-{文档类型}-{发文序号}-{案件编号}
        parts = [申请号, doc_type_name]
        if oa_info.发文序号:
            parts.append(oa_info.发文序号)
        if oa_info.案件编号:
            parts.append(oa_info.案件编号)
    elif oa_info.doc_type == '无效宣告请求审查决定书':
        # {申请号}-{文档类型}-{决定日}-{案件编号}
        # 案件编号为唯一标识，缺失时用决定号兜底，确保不同案件不会合并到同一文件夹
        parts = [申请号, doc_type_name]
        if oa_info.决定日:
            parts.append(oa_info.决定日)
        case_id = oa_info.案件编号 or oa_info.决定号
        if case_id:
            parts.append(case_id)
        else:
            # 案件编号和决定号均缺失时，使用发文序号作为最后兜底
            if oa_info.发文序号:
                parts.append(oa_info.发文序号)
    else:
        parts = [申请号, doc_type_name] if 申请号 else [doc_type_name]

    return _sanitize_filename('-'.join(parts))


def _save_raw_text(pages, output_path: str):
    """将PDF提取的原始文本保存为TXT文件。

    保留文本原有顺序和结构，包括页码分隔标记，
    便于后续人工核对和调试。

    Args:
        pages: PDF提取的页面文本列表
        output_path: TXT文件输出路径
    """
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    lines = []
    for p in pages:
        lines.append(f"===== 第 {p.page_num} 页 =====")
        lines.append(p.text)
        lines.append("")  # 页间空行
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    logger.info(f"原始文本已保存: {output_path}")


def _process_office_action(pages, reader, doc_type, args, logger, is_image_based=None, is_docx_input=False):
    """处理审查文件（审查意见通知书/驳回决定/复审决定书）。

    Args:
        pages: PDF提取的页面文本列表
        reader: PDFReader 实例（DOCX 输入时为 None）
        doc_type: 检测到的文档类型
        args: 命令行参数
        logger: 日志记录器
        is_image_based: 是否为图像型（DOCX 输入时为 False）
    """
    # 确定是否为图像型
    if is_image_based is None:
        is_image_based = reader.is_image_based if reader else False

    logger.info(f"检测到审查文件类型: {doc_type}")

    # ===== 步骤 2: 审查文件解析 =====
    logger.info("--- 步骤 2/5: 审查文件解析 ---")
    oa_parser = OfficeActionParser()
    oa_info = oa_parser.parse(pages)

    # 验证解析结果：关键字段缺失时发出警告
    if not oa_info.申请号 and not oa_info.发明创造名称:
        logger.warning("审查文件解析结果异常：申请号和发明创造名称均缺失，"
                       "可能文本提取失败或文档类型识别错误")

    # 构建命名基础字符串（含碰撞检测）
    base_name = _build_base_name_office_action(oa_info)
    base_name = _ensure_unique_base_name(base_name, args.output)
    logger.info(f"命名基础字符串: {base_name}")

    # ===== 步骤 3: 保存原始提取文本（TXT） =====
    logger.info("--- 步骤 3/5: 保存原始提取文本 ---")
    txt_path = os.path.join(args.output, f"{base_name}.txt")
    _save_raw_text(pages, txt_path)

    # ===== 步骤 4: JSON生成 =====
    logger.info("--- 步骤 4/5: JSON生成 ---")
    json_gen = JSONGenerator()
    json_data = json_gen.generate_office_action(
        info=oa_info,
        is_image_based=is_image_based,
    )
    # 修正 DOCX 来源的 text_source 标记
    if is_docx_input:
        json_data['_meta'] = {
            'is_image_based': False,
            'text_source': 'docx',
        }
    json_path = os.path.join(args.output, f"{base_name}.json")
    json_gen.save(json_data, json_path)

    # ===== 步骤 5: Markdown生成 =====
    logger.info("--- 步骤 5/5: Markdown生成 ---")
    md_gen = MarkdownGenerator()
    md_path = os.path.join(args.output, f"{base_name}.md")
    md_gen.save(json_data, md_path)

    # ===== 结果汇总 =====
    logger.info("=" * 60)
    logger.info("审查文件提取完成！输出文件：")
    logger.info(f"  TXT:       {txt_path}")
    logger.info(f"  JSON:      {json_path}")
    logger.info(f"  Markdown:  {md_path}")
    logger.info(f"  文档类型:  {doc_type}")
    logger.info(f"  申请号:    {oa_info.申请号}")
    logger.info(f"  名称:      {oa_info.发明创造名称}")
    logger.info(f"  日志:      {os.path.join(args.output, 'logs/')}")
    logger.info("=" * 60)

    # 输出基础名称供 Agent 重命名工作目录使用
    print(f"BASE_NAME:{base_name}")


def _process_docx_patent_publication(pages, args, logger):
    """处理 DOCX/DOC 格式的专利公开/公告文件。

    DOCX/DOC 文件不支持附图提取（无 PDF 页面渲染），
    其余流程（章节解析、JSON/Markdown 生成）与 PDF 一致。

    Args:
        pages: 文本提取的页面文本列表
        args: 命令行参数
        logger: 日志记录器
    """
    # ===== 步骤 2: 章节识别与拆分 =====
    logger.info("--- 步骤 2/6: 章节识别与拆分 ---")
    parser_obj = SectionParser()
    patent_info = parser_obj.parse(pages)

    # 构建命名基础字符串（含碰撞检测）
    base_name = _build_base_name_patent(patent_info)
    base_name = _ensure_unique_base_name(base_name, args.output)
    logger.info(f"命名基础字符串: {base_name}")

    # ===== 步骤 3: 保存原始提取文本（TXT） =====
    logger.info("--- 步骤 3/6: 保存原始提取文本 ---")
    txt_path = os.path.join(args.output, f"{base_name}.txt")
    _save_raw_text(pages, txt_path)

    # ===== 步骤 4: 提取附图说明中的图号引用 =====
    logger.info("--- 步骤 4/6: 图号引用提取 ---")
    figure_refs = parser_obj.extract_figure_refs()

    # ===== 步骤 5: JSON生成 =====
    logger.info("--- 步骤 5/6: JSON生成 ---")
    json_gen = JSONGenerator()
    json_data = json_gen.generate(
        patent_info=patent_info,
        images=[],  # DOCX 不支持附图提取
        is_image_based=False,
    )
    # 修正 DOCX 来源的 text_source 标记
    json_data['_meta'] = {
        'is_image_based': False,
        'text_source': 'docx',
    }
    json_path = os.path.join(args.output, f"{base_name}.json")
    json_gen.save(json_data, json_path)

    # ===== 步骤 6: Markdown生成 =====
    logger.info("--- 步骤 6/6: Markdown生成 ---")
    md_gen = MarkdownGenerator()
    md_path = os.path.join(args.output, f"{base_name}.md")
    md_gen.save(json_data, md_path)

    # ===== 结果汇总 =====
    logger.info("=" * 60)
    logger.info("提取完成！输出文件：")
    logger.info(f"  TXT:       {txt_path}")
    logger.info(f"  JSON:      {json_path}")
    logger.info(f"  Markdown:  {md_path}")
    logger.info(f"  附图:      不支持（DOCX/DOC 格式无附图提取）")
    logger.info(f"  日志:      {os.path.join(args.output, 'logs/')}")
    logger.info("=" * 60)

    # 输出基础名称供 Agent 重命名工作目录使用
    print(f"BASE_NAME:{base_name}")


def _process_patent_publication(pages, reader, args, logger):
    """处理专利公开/公告文件（原有流程）。

    Args:
        pages: PDF提取的页面文本列表
        reader: PDFReader 实例
        args: 命令行参数
        logger: 日志记录器
    """
    # ===== 步骤 2: 章节识别与拆分 =====
    logger.info("--- 步骤 2/7: 章节识别与拆分 ---")
    parser_obj = SectionParser()
    # parse() 返回 PatentInfo 对象，包含所有解析出的专利信息
    patent_info = parser_obj.parse(pages)

    # 构建命名基础字符串（含碰撞检测）
    base_name = _build_base_name_patent(patent_info)
    base_name = _ensure_unique_base_name(base_name, args.output)
    logger.info(f"命名基础字符串: {base_name}")

    # ===== 步骤 3: 保存原始提取文本（TXT） =====
    logger.info("--- 步骤 3/7: 保存原始提取文本 ---")
    txt_path = os.path.join(args.output, f"{base_name}.txt")
    _save_raw_text(pages, txt_path)

    # --- MinerU 单页模式下的附图范围修正 ---
    if patent_info._has_page_counts:
        is_mineru_sp = (pages and len(pages) == 1
                        and pages[0].source == "mineru_ocr")
        if is_mineru_sp or patent_info.drawings_page_range == (0, 0):
            total_pages = PDFReader._get_page_count(args.input)
            if total_pages > 0:
                parser_obj._apply_page_counts_to_drawings_range(total_pages)

    # ===== 步骤 4: 提取附图说明中的图号引用 =====
    logger.info("--- 步骤 4/7: 图号引用提取 ---")
    figure_refs = parser_obj.extract_figure_refs()

    # ===== 步骤 5: 说明书附图提取 =====
    logger.info("--- 步骤 5/7: 说明书附图提取 ---")
    images_dir = os.path.join(args.output, "images")
    extractor = ImageExtractor(dpi=args.dpi)

    drawings_range = patent_info.drawings_page_range
    if pages and len(pages) == 1 and pages[0].source == "mineru_ocr":
        if patent_info._has_page_counts and drawings_range[0] > 1:
            logger.info(f"使用页数信息推算的附图范围: 第{drawings_range[0]}-{drawings_range[1]}页")
        elif drawings_range[0] <= 1:
            total_pages = PDFReader._get_page_count(args.input)
            if total_pages > 1:
                logger.warning(
                    f"MinerU OCR 无法按页分割且无页数信息，"
                    f"将扫描第 1-{total_pages} 页提取附图。"
                )
                drawings_range = (1, total_pages)

    images = extractor.extract_drawing_images(
        pdf_path=args.input,
        drawings_page_range=drawings_range,
        figure_refs=figure_refs,
        output_dir=images_dir,
    )

    # ===== 附图页数验证 =====
    logger.info("--- 附图页数验证 ---")
    _validate_drawings_count(patent_info, images)

    # ===== 步骤 6: JSON生成 =====
    logger.info("--- 步骤 6/7: JSON生成 ---")
    json_gen = JSONGenerator()
    json_data = json_gen.generate(
        patent_info=patent_info,
        images=images,
        is_image_based=reader.is_image_based,
    )
    json_path = os.path.join(args.output, f"{base_name}.json")
    json_gen.save(json_data, json_path)

    # ===== 步骤 7: Markdown生成 =====
    logger.info("--- 步骤 7/7: Markdown生成 ---")
    md_gen = MarkdownGenerator()
    md_path = os.path.join(args.output, f"{base_name}.md")
    md_gen.save(json_data, md_path)

    # ===== 结果汇总 =====
    logger.info("=" * 60)
    logger.info("提取完成！输出文件：")
    logger.info(f"  TXT:       {txt_path}")
    logger.info(f"  JSON:      {json_path}")
    logger.info(f"  Markdown:  {md_path}")
    logger.info(f"  附图:      {images_dir} ({len(images)} 张)")
    if patent_info.drawings_pages <= 0:
        val_status = "跳过(无页数信息)"
    elif len(images) == patent_info.drawings_pages:
        val_status = "通过"
    else:
        val_status = "不一致"
    logger.info(f"  附图验证:  记载{patent_info.drawings_pages}页 / 实际{len(images)}张 → {val_status}")
    logger.info(f"  日志:      {os.path.join(args.output, 'logs/')}")
    logger.info("=" * 60)

    # 输出基础名称供 Agent 重命名工作目录使用
    print(f"BASE_NAME:{base_name}")


# 当脚本被直接运行（而非作为模块导入）时，执行 main() 函数
# 用法：python -m patent_extractor.main --input patent.pdf --output ./output/
if __name__ == '__main__':
    main()
