#!/usr/bin/env python3
"""
PDF to Markdown Converter for macOS - 智能增强版
支持多场景PDF：文本型、OCR型、混合型、扫描型
"""

import sys
import os
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Dict
from dataclasses import dataclass

# 导入第三方库
try:
    import pdfplumber
    from pdf2image import convert_from_path
    import pytesseract
except ImportError as e:
    print(f"错误：缺少必要的依赖库: {e}")
    print("请运行: pip3 install pdfplumber pdf2image pytesseract Pillow")
    sys.exit(1)

# 日志文件
LOG_FILE = Path.home() / "Library" / "Logs" / "pdf2md.log"


@dataclass
class PageInfo:
    """页面信息"""
    page_num: int
    has_text_layer: bool
    text_length: int
    image_ratio: float
    ocr_quality: str  # "good" | "poor" | "none"


def log_message(message: str, level: str = "INFO"):
    """写入日志文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


def show_notification(title: str, message: str):
    """显示macOS通知"""
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], check=False)
    except Exception:
        pass




def analyze_page(pdf_path: str, page_num: int) -> PageInfo:
    """分析单页的质量和类型"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num > len(pdf.pages):
                return PageInfo(page_num, False, 0, 0.0, "none")

            page = pdf.pages[page_num - 1]

            # 提取文本层
            text = page.extract_text() or ""
            text_length = len(text.strip())
            has_text_layer = text_length > 10

            # 计算图片比例
            try:
                images = page.images
                page_area = page.width * page.height
                image_area = sum(
                    img.get('width', 0) * img.get('height', 0)
                    for img in images
                )
                image_ratio = image_area / page_area if page_area > 0 else 0
            except Exception:
                image_ratio = 0.0

            # 判断OCR质量
            if text_length > 200:
                ocr_quality = "good"
            elif text_length > 50:
                ocr_quality = "poor"
            else:
                ocr_quality = "none"

            return PageInfo(
                page_num=page_num,
                has_text_layer=has_text_layer,
                text_length=text_length,
                image_ratio=image_ratio,
                ocr_quality=ocr_quality
            )
    except Exception as e:
        log_message(f"分析第 {page_num} 页失败: {e}", "ERROR")
        return PageInfo(page_num, False, 0, 0.0, "none")


def sample_pdf_pages(pdf_path: str) -> List[PageInfo]:
    """
    多页采样检测
    采样策略：前3页 + 中间1页 + 最后1页
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

        # 确定采样页面
        sample_pages = []

        # 前3页
        for i in range(1, min(4, total_pages + 1)):
            sample_pages.append(i)

        # 中间页
        if total_pages > 6:
            middle = total_pages // 2
            sample_pages.append(middle)

        # 最后1页
        if total_pages > 3:
            sample_pages.append(total_pages)

        # 去重并排序
        sample_pages = sorted(set(sample_pages))

        log_message(f"采样页面: {sample_pages} (共 {total_pages} 页)")

        # 分析每个采样页
        page_infos = []
        for page_num in sample_pages:
            info = analyze_page(pdf_path, page_num)
            page_infos.append(info)
            log_message(f"第 {page_num} 页: 文本长度={info.text_length}, OCR质量={info.ocr_quality}")

        return page_infos

    except Exception as e:
        log_message(f"采样失败: {e}", "ERROR")
        return []


def determine_extraction_strategy(page_infos: List[PageInfo], total_pages: int) -> str:
    """
    根据采样结果确定提取策略
    返回: "text" | "ocr_image" | "raw_image" | "mixed"
    """
    if not page_infos:
        return "raw_image"

    # 统计
    good_text_pages = sum(1 for p in page_infos if p.ocr_quality == "good")
    poor_text_pages = sum(1 for p in page_infos if p.ocr_quality == "poor")
    no_text_pages = sum(1 for p in page_infos if p.ocr_quality == "none")
    total_sampled = len(page_infos)

    log_message(f"采样统计: 高质量={good_text_pages}, 低质量={poor_text_pages}, 无文本={no_text_pages}")

    # 判断策略
    if good_text_pages >= total_sampled * 0.6:
        # 60%以上页面有高质量文本 -> 文本型PDF
        return "text"
    elif (good_text_pages + poor_text_pages) >= total_sampled * 0.5:
        # 50%以上页面有文本（无论质量）-> OCR型PDF
        return "ocr_image"
    elif no_text_pages >= total_sampled * 0.7:
        # 70%以上页面无文本 -> 纯图片型PDF
        return "raw_image"
    else:
        # 混合类型
        return "mixed"


def extract_page_with_best_method(pdf_path: str, page_num: int, page_info: PageInfo = None) -> Tuple[str, str]:
    """
    使用最佳方法提取单页文本
    返回: (提取的文本, 状态标记)
    状态: "success" | "ocr_fallback" | "failed"
    """
    if page_info is None:
        page_info = analyze_page(pdf_path, page_num)

    extracted_text = ""
    status = "failed"

    # 策略1：如果文本层质量好，直接使用
    if page_info.ocr_quality == "good":
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[page_num - 1]
                extracted_text = page.extract_text() or ""
                if len(extracted_text.strip()) > 100:
                    status = "success"
                    log_message(f"第 {page_num} 页: 使用文本层提取成功")
        except Exception as e:
            log_message(f"第 {page_num} 页文本层提取失败: {e}", "ERROR")

    # 策略2：文本层质量差或失败，尝试OCR
    if status == "failed":
        try:
            images = convert_from_path(
                pdf_path,
                first_page=page_num,
                last_page=page_num,
                dpi=200
            )

            if images:
                ocr_text = pytesseract.image_to_string(images[0], lang='chi_sim+eng')
                if len(ocr_text.strip()) > 20:
                    extracted_text = ocr_text
                    status = "ocr_fallback" if page_info.has_text_layer else "success"
                    log_message(f"第 {page_num} 页: OCR提取成功")
                else:
                    log_message(f"第 {page_num} 页: OCR未识别到文本")
        except Exception as e:
            log_message(f"第 {page_num} 页OCR失败: {e}", "ERROR")

    return extracted_text, status


def extract_all_pages_intelligent(pdf_path: str, strategy: str) -> Tuple[str, List[int], List[int]]:
    """
    智能提取所有页面
    返回: (完整文本, 成功页码列表, 失败页码列表)
    """
    try:
        pdf = pdfplumber.open(pdf_path)
        total_pages = len(pdf.pages)
    except Exception as e:
        log_message(f"无法打开PDF: {e}", "ERROR")
        return "", [], []

    log_message(f"开始提取 {total_pages} 页，策略: {strategy}")

    # 预估时间（每页OCR约2-3秒）
    estimated_time = total_pages * 3
    if estimated_time > 10:
        show_notification(
            "PDF转MD",
            f"开始处理 {total_pages} 页PDF，预计需要 {estimated_time//60}分{estimated_time%60}秒"
        )

    all_text = []
    success_pages = []
    failed_pages = []
    ocr_fallback_pages = []

    try:
        for page_num in range(1, total_pages + 1):
            # 每5页显示一次进度
            if page_num % 5 == 0 or page_num == 1:
                log_message(f"进度: {page_num}/{total_pages}")

            # 分析页面（复用已打开的 pdf 对象）
            page = pdf.pages[page_num - 1]
            text_layer = page.extract_text() or ""
            text_length = len(text_layer.strip())
            has_text_layer = text_length > 10

            if text_length > 200:
                ocr_quality = "good"
            elif text_length > 50:
                ocr_quality = "poor"
            else:
                ocr_quality = "none"

            page_info = PageInfo(page_num, has_text_layer, text_length, 0.0, ocr_quality)

            # 根据策略决定提取方式
            text, status = extract_page_with_best_method(pdf_path, page_num, page_info)

            # 记录结果
            if status == "success":
                success_pages.append(page_num)
            elif status == "ocr_fallback":
                ocr_fallback_pages.append(page_num)
                success_pages.append(page_num)
            else:
                failed_pages.append(page_num)
                text = f"[第 {page_num} 页识别失败]"

            # 添加分页标记
            all_text.append(f"\n--- 第 {page_num} 页 ---\n")
            all_text.append(text)
    finally:
        pdf.close()

    # 生成统计信息
    result_text = '\n'.join(all_text)

    # 添加处理报告
    report = f"""

--- PDF处理报告 ---
总页数: {total_pages}
成功识别: {len(success_pages)} 页
OCR降级: {len(ocr_fallback_pages)} 页
识别失败: {len(failed_pages)} 页
"""

    if failed_pages:
        report += f"失败页面: {', '.join(map(str, failed_pages))}\n"

    result_text += report

    log_message(f"提取完成: 成功 {len(success_pages)}, OCR降级 {len(ocr_fallback_pages)}, 失败 {len(failed_pages)}")

    return result_text, success_pages, failed_pages


def format_page_text(page, text: str) -> str:
    """格式化单页文本，尝试保留基本结构"""
    lines = text.split('\n')
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue

        # 简单的标题检测（基于字体大小或全大写）
        try:
            chars = page.chars
            if chars:
                # 获取当前行的平均字体大小
                line_chars = [c for c in chars if c['text'] in line[:10]]
                if line_chars:
                    avg_size = sum(c.get('size', 12) for c in line_chars) / len(line_chars)
                    # 大字体可能是标题
                    if avg_size > 14 or line.isupper():
                        if len(line) < 50:  # 短行才可能是标题
                            formatted_lines.append(f"## {line}")
                            continue
        except Exception:
            pass

        formatted_lines.append(line)

    return '\n'.join(formatted_lines) + '\n\n'


def extract_text_pdf_direct(pdf_path: str) -> str:
    """直接提取文本型PDF的所有文本"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = []
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                if text:
                    formatted = format_page_text(page, text)
                    all_text.append(f"\n--- 第 {i} 页 ---\n")
                    all_text.append(formatted)
            return '\n'.join(all_text)
    except Exception as e:
        log_message(f"直接提取失败: {e}", "ERROR")
        return ""


def write_markdown(pdf_path: Path, content: str) -> str:
    """写入Markdown文件"""
    md_path = pdf_path.with_suffix(".md")

    # 处理文件名冲突
    counter = 1
    original = md_path
    while md_path.exists():
        md_path = original.with_name(f"{pdf_path.stem}_{counter}.md")
        counter += 1

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(md_path)


def process_single_pdf(pdf_path: str) -> Tuple[bool, str, Dict]:
    """
    处理单个PDF - 智能完整版
    返回: (是否成功, 结果信息, 详细统计)
    """
    log_message(f"开始处理: {pdf_path}")
    stats = {
        "total_pages": 0,
        "success_pages": 0,
        "failed_pages": 0,
        "ocr_fallback_pages": 0,
        "strategy": "unknown"
    }

    try:
        # 检查文件
        if not os.path.exists(pdf_path):
            return False, f"文件不存在: {pdf_path}", stats

        if not pdf_path.lower().endswith(".pdf"):
            return False, f"不是PDF文件: {pdf_path}", stats

        # 获取PDF信息
        try:
            with pdfplumber.open(pdf_path) as pdf:
                stats["total_pages"] = len(pdf.pages)
        except Exception as e:
            return False, f"无法读取PDF: {e}", stats

        # 多页采样检测
        page_infos = sample_pdf_pages(pdf_path)
        if not page_infos:
            return False, "无法分析PDF结构", stats

        # 确定提取策略
        strategy = determine_extraction_strategy(page_infos, stats["total_pages"])
        stats["strategy"] = strategy
        log_message(f"检测策略: {strategy}")

        # 根据策略提取
        if strategy == "text":
            # 纯文本型：直接提取
            raw_text = extract_text_pdf_direct(pdf_path)
            if raw_text.strip():
                stats["success_pages"] = stats["total_pages"]
            else:
                # 直接提取失败，降级到智能提取
                log_message("直接提取失败，降级到智能提取")
                raw_text, success, failed = extract_all_pages_intelligent(pdf_path, "mixed")
                stats["success_pages"] = len(success)
                stats["failed_pages"] = len(failed)
        else:
            # OCR型、图片型、混合型：智能提取
            raw_text, success, failed = extract_all_pages_intelligent(pdf_path, strategy)
            stats["success_pages"] = len(success)
            stats["failed_pages"] = len(failed)

        # 检查提取结果
        if not raw_text.strip():
            return False, "无法提取任何文本", stats

        # 写入文件
        md_path = write_markdown(Path(pdf_path), raw_text)
        log_message(f"已保存: {md_path}")

        # 生成结果信息
        if stats["failed_pages"] > 0:
            result_msg = f"已保存: {md_path}\n警告: {stats['failed_pages']} 页识别失败"
            show_notification("PDF转MD完成", f"转换完成，但有 {stats['failed_pages']} 页失败")
        else:
            result_msg = f"已保存: {md_path}"
            show_notification("PDF转MD完成", f"成功转换 {stats['total_pages']} 页")

        return True, result_msg, stats

    except Exception as e:
        error_msg = f"处理失败: {str(e)}"
        log_message(error_msg, "ERROR")
        return False, error_msg, stats


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: pdf2md_converter.py <PDF文件>")
        sys.exit(1)

    pdf_files = sys.argv[1:]
    log_message(f"批量处理 {len(pdf_files)} 个文件")

    success = 0
    failed = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] {pdf_path}")

        ok, result, stats = process_single_pdf(pdf_path)

        if ok:
            success += 1
            print(f"  ✓ {result}")
            if stats["failed_pages"] > 0:
                print(f"    统计: 共{stats['total_pages']}页, 成功{stats['success_pages']}页, 失败{stats['failed_pages']}页")
        else:
            failed += 1
            print(f"  ✗ {result}")

    print(f"\n完成: 成功 {success}, 失败 {failed}")
    log_message(f"批量完成: 成功 {success}, 失败 {failed}")

    # 显示最终通知
    if failed > 0:
        show_notification("PDF转MD", f"完成: 成功 {success} 个, 失败 {failed} 个")
    else:
        show_notification("PDF转MD", f"全部成功: {success} 个文件")


if __name__ == "__main__":
    main()
