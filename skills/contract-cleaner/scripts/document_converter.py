#!/usr/bin/env python3
"""
文档转换器：将Word/PDF/Markdown转换为Markdown格式

支持格式:
- Word (.docx, .doc) → Markdown (via pandoc)
- PDF → Markdown (via OCR)
- Markdown → Markdown (直接复制)
"""

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

# 配置日志
logger = logging.getLogger('document_converter')


def load_ocr_cleanup_prompt() -> str:
    """加载OCR清理prompt"""
    prompt_path = Path(__file__).parent.parent / "references" / "api_prompt_ocr_cleanup.md"
    if prompt_path.exists():
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def basic_ocr_cleanup(text: str) -> str:
    """
    基础OCR清理（不依赖AI）
    
    修复常见问题：
    - 删除页码标记
    - 合并断行（简单的段落重组）
    - 删除多余的空行
    """
    import re
    
    # 删除页码标记（如"第 X 页"、"Page X"）
    text = re.sub(r'第\s*\d+\s*页', '', text)
    text = re.sub(r'Page\s*\d+', '', text, flags=re.IGNORECASE)
    
    # 删除页眉页脚常见标记
    text = re.sub(r'^\s*第\s*\d+\s*页\s*共\s*\d+\s*页\s*$', '', text, flags=re.MULTILINE)
    
    # 合并断行：将单行断开的文本合并（简单的启发式规则）
    # 如果一行不以标点符号结尾，且下一行不是空行，则合并
    lines = text.split('\n')
    merged_lines = []
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        if not line:
            # 空行表示段落结束
            if current_paragraph:
                merged_lines.append(''.join(current_paragraph))
                current_paragraph = []
            merged_lines.append('')  # 保留空行
        elif line.endswith(('。', '，', '；', '：', '！', '？', '.', ',', ';', ':', '!', '?')):
            # 以标点结尾，可能是段落结束
            current_paragraph.append(line)
            merged_lines.append(''.join(current_paragraph))
            current_paragraph = []
        elif line.startswith(('第', '1.', '2.', '（', '(')):
            # 条款编号开头，可能是新段落
            if current_paragraph:
                merged_lines.append(''.join(current_paragraph))
                current_paragraph = []
            current_paragraph.append(line)
        else:
            current_paragraph.append(line)
    
    # 处理最后一段
    if current_paragraph:
        merged_lines.append(''.join(current_paragraph))
    
    # 重新组合文本
    text = '\n'.join(merged_lines)
    
    # 删除多余的空行（连续多个空行合并为1个）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def _convert_doc_to_docx(input_path: str) -> Optional[str]:
    """
    使用LibreOffice将旧版.doc转换为.docx
    
    Args:
        input_path: 输入.doc文件路径
    
    Returns:
        转换后的.docx路径，失败返回None
    """
    import subprocess
    import shutil
    
    # 查找 LibreOffice/soffice
    soffice = shutil.which('soffice')
    if not soffice:
        # macOS 常见路径
        mac_paths = [
            '/Applications/LibreOffice.app/Contents/MacOS/soffice',
            '/usr/local/bin/soffice',
        ]
        for p in mac_paths:
            if os.path.isfile(p):
                soffice = p
                break
    
    if not soffice:
        logger.error("未找到LibreOffice，无法转换.doc格式。请安装: brew install --cask libreoffice")
        return None
    
    # 转换到临时目录
    temp_dir = tempfile.mkdtemp(prefix="doc_to_docx_")
    try:
        logger.info(f"使用LibreOffice转换 .doc → .docx: {input_path}")
        result = subprocess.run(
            [soffice, '--headless', '--convert-to', 'docx', '--outdir', temp_dir, input_path],
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        # 找到转换后的 .docx 文件
        stem = Path(input_path).stem
        docx_path = os.path.join(temp_dir, f"{stem}.docx")
        if os.path.isfile(docx_path):
            logger.info(f"LibreOffice转换成功: {docx_path}")
            return docx_path
        else:
            logger.error(f"LibreOffice转换后未找到输出文件: {docx_path}")
            return None
    except subprocess.TimeoutExpired:
        logger.error("LibreOffice转换超时（60秒）")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"LibreOffice转换失败: {e}")
        if e.stderr:
            logger.error(e.stderr)
        return None
    except Exception as e:
        logger.error(f"LibreOffice转换异常: {e}")
        return None


def strip_auto_numbering(md_text: str) -> str:
    """
    清除 pandoc 从 Word 自动编号列表转换来的有序列表标记。

    Word 自动编号在 pandoc 转换后变成：
        1. 第一条内容
        2. 第二条内容

    这些编号是"动态"的——在最终 docx 导出或 MD 渲染时会再次被自动重排，
    导致序号紊乱。本函数将其展开为"写死"的文本形式：
        1. 第一条内容   →  1. 第一条内容  （保留编号，但去掉列表语义）

    策略：将 Markdown 有序列表项（行首 `数字.` 或 `数字)`）转换为
    普通段落行，编号作为文本的一部分保留，而非列表标记。

    Args:
        md_text: pandoc 生成的 Markdown 文本

    Returns:
        处理后的 Markdown 文本
    """
    import re

    lines = md_text.split('\n')
    result = []
    # 记录当前有序列表块的计数器，用于展开时写入实际序号
    # pandoc 输出的有序列表每个块都从1开始或按实际顺序，直接保留原序号即可
    for line in lines:
        # 匹配有序列表项：行首可有块引用前缀(> )和缩进，然后是 数字. 或 数字) 后跟空格
        m = re.match(r'^((?:>\s*)*)( {0,3})(\d+)([.)]) (.*)$', line)
        if m:
            quote_prefix, indent, num, sep, content = m.groups()
            # 将列表语义去掉：保持块引用前缀和缩进，编号写死进文本，不再是列表项
            # 使用全角/中文场景下常见的 "数字." 格式，保留原编号值
            result.append(f"{quote_prefix}{indent}{num}{sep} {content}")
        else:
            result.append(line)

    text = '\n'.join(result)

    # 二次清理：pandoc 有时对连续列表块插入 HTML 注释 <!-- --> 来重置编号，移除之
    text = re.sub(r'\n?<!--\s*-->\n?', '\n', text)

    return text


def convert_word_to_md(input_path: str, output_path: str) -> bool:
    """
    使用pandoc将Word文档转换为Markdown
    对于.doc格式，先用LibreOffice转为.docx再处理

    转换后会自动执行 strip_auto_numbering()，消除 Word 自动编号
    在后续 pandoc 导出时被重新渲染导致的序号紊乱问题。
    
    Args:
        input_path: 输入Word文件路径
        output_path: 输出MD文件路径
    
    Returns:
        是否成功
    """
    import subprocess
    
    suffix = Path(input_path).suffix.lower()
    actual_input = input_path
    doc_temp_dir = None
    
    # .doc 格式需要先用 LibreOffice 转 .docx
    if suffix == '.doc':
        logger.info("检测到旧版.doc格式，先用LibreOffice转换为.docx")
        docx_path = _convert_doc_to_docx(input_path)
        if not docx_path:
            logger.error("无法将.doc转换为.docx，处理终止")
            return False
        actual_input = docx_path
        # 记住临时目录，后续清理
        doc_temp_dir = os.path.dirname(docx_path)
    
    logger.info(f"使用pandoc转换Word文档: {actual_input}")
    
    # pandoc 参数：--wrap=none 禁止自动换行；-t markdown-smart 避免智能标点干扰
    pandoc_args = ['--wrap=none', '-t', 'markdown-smart']

    try:
        success = False
        try:
            import pypandoc
            pypandoc.convert_file(actual_input, 'markdown', outputfile=output_path,
                                  extra_args=pandoc_args)
            success = True
        except ImportError:
            logger.warning("pypandoc未安装，尝试使用命令行pandoc")
            try:
                result = subprocess.run(
                    ['pandoc'] + pandoc_args + [actual_input, '-o', output_path],
                    check=True,
                    capture_output=True,
                    text=True
                )
                success = True
            except subprocess.CalledProcessError as e:
                logger.error(f"pandoc转换失败: {e}")
                if e.stderr:
                    logger.error(e.stderr)
                return False
            except FileNotFoundError:
                logger.error("未找到pandoc命令，请安装pandoc: https://pandoc.org/installing.html")
                return False

        if success:
            # 后处理：清除自动编号列表语义，防止 docx 导出时重新编号导致紊乱
            logger.info("后处理：清除 Word 自动编号标记")
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                cleaned = strip_auto_numbering(md_content)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned)
                logger.info("自动编号清除完成")
            except Exception as e:
                logger.warning(f"自动编号清除失败（不影响主流程）: {e}")
            return True

        return False

    except Exception as e:
        logger.error(f"Word转换失败: {e}")
        return False
    finally:
        # 清理 .doc 临时转换文件
        if doc_temp_dir and os.path.isdir(doc_temp_dir):
            try:
                import shutil
                shutil.rmtree(doc_temp_dir, ignore_errors=True)
            except:
                pass


def convert_pdf_to_md(input_path: str, output_path: str, dpi: int = 300) -> bool:
    """
    使用OCR将PDF转换为Markdown
    
    Args:
        input_path: 输入PDF文件路径
        output_path: 输出MD文件路径
        dpi: OCR分辨率，默认300
    
    Returns:
        是否成功
    """
    logger.info(f"开始PDF OCR转换 (DPI={dpi})")
    
    temp_dir: Optional[tempfile.TemporaryDirectory] = None
    
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image
        
        # 创建临时目录存储中间图片
        temp_dir = tempfile.TemporaryDirectory(prefix="pdf_ocr_")
        temp_path = Path(temp_dir.name)
        
        logger.info(f"临时目录: {temp_path}")
        
        # 将PDF转换为图片
        logger.info("正在将PDF转换为图片...")
        try:
            images = convert_from_path(
                input_path, 
                dpi=dpi,
                output_folder=str(temp_path),
                fmt='png',
                paths_only=True
            )
        except Exception as e:
            logger.error(f"PDF转图片失败: {e}")
            logger.error("请确保已安装poppler: brew install poppler (macOS) 或 apt-get install poppler-utils (Ubuntu)")
            return False
        
        logger.info(f"共 {len(images)} 页需要OCR识别")
        
        full_text = []
        
        for i, image_path in enumerate(images, 1):
            logger.info(f"  OCR识别第 {i}/{len(images)} 页...")
            try:
                # 使用上下文管理器确保图片资源正确释放
                with Image.open(image_path) as img:
                    # 使用中文+英文识别
                    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                    full_text.append(f"\n--- 第{i}页 ---\n")
                    full_text.append(text)
            except Exception as e:
                logger.warning(f"第{i}页OCR失败: {e}")
                full_text.append(f"\n--- 第{i}页 [OCR失败] ---\n")
                continue
            finally:
                # 删除临时图片文件
                try:
                    os.unlink(image_path)
                except:
                    pass
        
        raw_text = '\n'.join(full_text)
        logger.info("正在进行OCR后清理...")
        cleaned_text = basic_ocr_cleanup(raw_text)
        
        # 写入输出文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            logger.info(f"OCR完成并清理，输出保存至: {output_path}")
            return True
        except Exception as e:
            logger.error(f"写入输出文件失败: {e}")
            return False
            
    except ImportError as e:
        logger.error(f"缺少必要的库: {e}")
        logger.error("请安装: pip install pdf2image pytesseract pillow")
        logger.error("并确保已安装tesseract-ocr: brew install tesseract (macOS) 或 apt-get install tesseract-ocr tesseract-ocr-chi-sim (Ubuntu)")
        return False
    except Exception as e:
        logger.error(f"PDF转换失败: {e}")
        return False
    finally:
        # 确保临时目录被清理
        if temp_dir:
            try:
                temp_dir.cleanup()
            except:
                pass


def copy_md(input_path: str, output_path: str) -> bool:
    """
    直接复制Markdown文件
    
    Args:
        input_path: 输入MD文件路径
        output_path: 输出MD文件路径
    
    Returns:
        是否成功
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已复制Markdown文件")
        return True
    except UnicodeDecodeError as e:
        logger.error(f"文件编码错误: {e}")
        logger.error("请确保文件是UTF-8编码的文本文件")
        return False
    except Exception as e:
        logger.error(f"复制MD文件失败: {e}")
        return False


def validate_input_file(input_path: Path) -> tuple[bool, str]:
    """
    验证输入文件
    
    Returns:
        (是否有效, 错误信息)
    """
    if not input_path.exists():
        return False, f"文件不存在: {input_path}"
    
    if not input_path.is_file():
        return False, f"不是普通文件: {input_path}"
    
    suffix = input_path.suffix.lower()
    supported = {'.docx', '.doc', '.pdf', '.md', '.markdown', '.txt'}
    if suffix not in supported:
        return False, f"不支持的格式: {suffix}。支持: {', '.join(supported)}"
    
    # 检查文件大小（50MB限制）
    max_size = 50 * 1024 * 1024
    if input_path.stat().st_size > max_size:
        return False, f"文件过大: {input_path.stat().st_size / (1024*1024):.1f}MB (最大50MB)"
    
    return True, ""


def main():
    parser = argparse.ArgumentParser(
        description='文档转换为Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python document_converter.py -i 合同.docx -o output.md
  python document_converter.py -i 扫描件.pdf -o output.md
        """
    )
    parser.add_argument('--input', '-i', required=True, help='输入文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出MD文件路径')
    parser.add_argument('--dpi', '-d', type=int, default=300, 
                       help='PDF OCR分辨率 (默认: 300)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细日志')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # 验证输入文件
    is_valid, error_msg = validate_input_file(input_path)
    if not is_valid:
        logger.error(f"输入验证失败: {error_msg}")
        sys.exit(1)
    
    # 确保输出目录存在
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"无法创建输出目录: {e}")
        sys.exit(1)
    
    # 根据文件类型选择转换方式
    suffix = input_path.suffix.lower()
    
    logger.info(f"输入文件: {input_path}")
    logger.info(f"输出文件: {output_path}")
    
    if suffix in {'.docx', '.doc'}:
        logger.info("识别为Word文档，使用pandoc转换")
        success = convert_word_to_md(str(input_path), str(output_path))
    elif suffix == '.pdf':
        logger.info("识别为PDF文档，使用OCR转换")
        success = convert_pdf_to_md(str(input_path), str(output_path), dpi=args.dpi)
    elif suffix in {'.md', '.markdown', '.txt'}:
        logger.info("识别为文本文件，直接复制")
        success = copy_md(str(input_path), str(output_path))
    else:
        logger.error(f"不支持的文件格式: {suffix}")
        sys.exit(1)
    
    if success:
        logger.info(f"✓ 转换完成: {output_path}")
        sys.exit(0)
    else:
        logger.error("✗ 转换失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
