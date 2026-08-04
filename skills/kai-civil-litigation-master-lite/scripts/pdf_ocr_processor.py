#!/usr/bin/env python3
"""
批量 PDF OCR 处理脚本（优化版）：给扫描版 PDF 添加可搜索文本层
保持原有目录结构输出到新文件夹

核心优化：
1. 抽样检测文本层，不逐页全检
2. 仅对无文本层页面（bad_pages）执行 OCR，而非整本重跑
3. 质量模式（fast/normal/high）自动选择 zoom
4. 支持多进程并发
5. 单文件超时保护
6. 失败时自动回退复制原文件

依赖：PyMuPDF, rapidocr_onnxruntime
"""

import os
import sys
import shutil
import json
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed

import fitz


# ---------------------------------------------------------------------------
# 超时处理（Unix/Linux/macOS 可用；Windows 上会自动忽略）
# ---------------------------------------------------------------------------
try:
    import signal

    def _set_timeout(seconds: int):
        def handler(signum, frame):
            raise TimeoutError(f"单文件处理超过 {seconds} 秒")
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(seconds)

    def _clear_timeout():
        signal.alarm(0)
except (ImportError, AttributeError):
    def _set_timeout(seconds: int):
        pass

    def _clear_timeout():
        pass


# ---------------------------------------------------------------------------
# OCR 引擎
# ---------------------------------------------------------------------------
def init_ocr_engine():
    """初始化 RapidOCR 引擎"""
    try:
        from rapidocr_onnxruntime import RapidOCR
        return RapidOCR()
    except ImportError:
        print("错误：未安装 rapidocr_onnxruntime。请运行：pip install rapidocr_onnxruntime")
        sys.exit(1)


# ---------------------------------------------------------------------------
# 文本层检测：抽样 + 定向精检
# ---------------------------------------------------------------------------
def sample_pages(page_count: int, max_samples: int = 5) -> list:
    """返回抽样页码（1-based），用于快速判断文本层"""
    if page_count <= max_samples:
        return list(range(1, page_count + 1))
    # 首页、末页、中间均匀分布
    samples = [1, page_count]
    step = page_count / (max_samples - 1)
    for i in range(1, max_samples - 1):
        samples.append(max(1, min(page_count, int(round(i * step)))))
    return sorted(set(samples))


def check_text_layer(doc: fitz.Document, min_chars: int = 10, sample_mode: bool = True) -> list:
    """
    检查 PDF 文本层，返回需要 OCR 的页码列表（1-based）。
    空列表表示无需 OCR。

    策略：
    - 页数 <= 5：直接全检
    - 抽样检测：首页、末页、中间若干页
    - 若抽样页全部有文本，判定整本有文本
    - 若抽样页有缺失，对可疑区域及相邻页精检
    """
    total = len(doc)
    if total == 0:
        return []

    if not sample_mode or total <= 5:
        return [i + 1 for i in range(total) if len(doc[i].get_text().strip()) < min_chars]

    # 抽样阶段
    samples = sample_pages(total, max_samples=5)
    sample_bad = [p for p in samples if len(doc[p - 1].get_text().strip()) < min_chars]

    # 抽样页全部有文本，则认为整本无需 OCR
    if not sample_bad:
        return []

    # 粗检：每隔 3 页抽一页（避开已抽样页）
    coarse = [p for p in range(1, total + 1) if p not in samples and p % 3 == 0]
    coarse_bad = [p for p in coarse if len(doc[p - 1].get_text().strip()) < min_chars]

    # 精检：可疑页及其前后相邻页
    suspicious = set(sample_bad + coarse_bad)
    extended = set(suspicious)
    for p in suspicious:
        if p > 1:
            extended.add(p - 1)
        if p < total:
            extended.add(p + 1)

    return [p for p in sorted(extended) if len(doc[p - 1].get_text().strip()) < min_chars]


# ---------------------------------------------------------------------------
# 自适应 zoom 选择
# ---------------------------------------------------------------------------
def select_zoom(page_count: int, bad_page_count: int) -> float:
    """
    根据文档特征自动选择 OCR 渲染 zoom。
    规则：
    - 短文档（<=5 页）通常为关键单页材料，用 zoom=3 保证精度
    - 坏页比例高（>=60%）说明扫描质量差，用 zoom=3
    - 中等长度（<=30 页）用 zoom=2
    - 长文档（>30 页）用 zoom=1.5 节省时间
    """
    if page_count <= 5:
        return 3.0
    if page_count > 0 and bad_page_count / page_count >= 0.6:
        return 3.0
    if page_count <= 30:
        return 2.0
    return 1.5

def ocr_single_pdf(input_path: str, output_path: str, zoom: float = None,
                   skip_existing: bool = False, timeout: int = 600) -> dict:
    """
    对单个 PDF 进行 OCR 处理。多进程模式下，每个进程独立初始化 OCR 引擎。
    仅处理无文本层的页面（bad_pages）。
    zoom 为 None 时根据文档页数和坏页比例自动选择（自适应 zoom）。
    """

    result = {
        "input": input_path,
        "output": output_path,
        "status": "failed",
        "pages": 0,
        "bad_pages": [],
        "zoom": None,
        "message": ""
    }
    input_path = Path(input_path)
    output_path = Path(output_path)

    # 断点续传：输出已存在则跳过
    if skip_existing and output_path.exists():
        result["status"] = "skipped"
        result["message"] = "输出文件已存在，跳过"
        return result

    try:
        _set_timeout(timeout)
        doc = fitz.open(input_path)
        result["pages"] = len(doc)

        # 抽样检测坏页
        bad_pages = check_text_layer(doc, sample_mode=True)
        result["bad_pages"] = bad_pages

        # 自适应 zoom：未指定时根据文档特征自动选择
        if zoom is None:
            zoom = select_zoom(len(doc), len(bad_pages))
        result["zoom"] = zoom

        if not bad_pages:
            doc.close()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_path, output_path)
            result["status"] = "copied"
            result["message"] = "已有文本层，直接复制"
            _clear_timeout()
            return result

        # 仅对坏页执行 OCR
        bad_pages_set = set(bad_pages)
        mat = fitz.Matrix(zoom, zoom)
        ocr_engine = init_ocr_engine()

        for page_num, page in enumerate(doc):
            if (page_num + 1) not in bad_pages_set:
                continue

            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            ocr_result, _ = ocr_engine(img_data)

            if not ocr_result:
                continue

            for item in ocr_result:
                if len(item) < 2:
                    continue
                box = item[0]
                text = item[1]
                if not text or not text.strip():
                    continue

                x_coords = [p[0] / zoom for p in box]
                y_coords = [p[1] / zoom for p in box]
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                width = x_max - x_min
                height = y_max - y_min
                if width <= 0 or height <= 0:
                    continue

                font_size = max(4, height * 0.75)
                try:
                    page.insert_text(
                        (x_min, y_max - font_size * 0.1),
                        text.strip(),
                        fontsize=font_size,
                        fontname="china-ss",
                        color=(0, 0, 0),
                        render_mode=3,
                        overlay=True
                    )
                except Exception:
                    pass

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        result["status"] = "ocr"
        result["message"] = f"OCR 成功，处理 {len(bad_pages)} 页"
        _clear_timeout()
        return result

    except Exception as e:
        result["message"] = f"处理失败: {str(e)}"
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_path, output_path)
            result["message"] += "（已回退复制原文件）"
        except Exception:
            pass
        _clear_timeout()
        return result


# ---------------------------------------------------------------------------
# 目录处理
# ---------------------------------------------------------------------------
def _update_summary(summary: dict, res: dict):
    if res["status"] == "failed":
        summary["failed"] += 1
    elif res["status"] == "skipped":
        summary["skipped"] += 1
    else:
        summary["success"] += 1
        if res["status"] == "copied":
            summary["copied"] += 1
        elif res["status"] == "ocr":
            summary["ocr"] += 1


def process_directory(src_dir: Path, dst_dir: Path, zoom: float = 2,
                      skip_existing: bool = False, workers: int = 1,
                      timeout: int = 600) -> dict:
    """
    递归处理目录中的所有 PDF
    """
    pdf_files = sorted(src_dir.rglob("*.pdf"))
    total = len(pdf_files)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "source": str(src_dir),
        "destination": str(dst_dir),
        "total": total,
        "success": 0,
        "failed": 0,
        "copied": 0,
        "ocr": 0,
        "skipped": 0,
        "details": []
    }

    if total == 0:
        print(f"在 {src_dir} 中未找到 PDF 文件")
        return summary

    print(f"\n共发现 {total} 个 PDF 文件，工作进程 {workers} 个，开始处理...\n")

    if workers <= 1:
        for i, pdf_path in enumerate(pdf_files, 1):
            rel_path = pdf_path.relative_to(src_dir)
            output_path = dst_dir / rel_path
            print(f"[{i}/{total}] {rel_path}")
            res = ocr_single_pdf(str(pdf_path), str(output_path), zoom, skip_existing, timeout)
            summary["details"].append(res)
            _update_summary(summary, res)
    else:
        # 多进程并发：每个进程独立初始化 OCR 引擎
        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_map = {}
            for i, pdf_path in enumerate(pdf_files, 1):
                rel_path = pdf_path.relative_to(src_dir)
                output_path = dst_dir / rel_path
                future = executor.submit(
                    ocr_single_pdf, str(pdf_path), str(output_path),
                    zoom, skip_existing, timeout
                )
                future_map[future] = (i, rel_path)

            for future in as_completed(future_map):
                i, rel_path = future_map[future]
                try:
                    res = future.result()
                except Exception as e:
                    res = {
                        "input": str(rel_path),
                        "output": "",
                        "status": "failed",
                        "pages": 0,
                        "bad_pages": [],
                        "message": f"进程异常: {str(e)}"
                    }
                print(f"[{i}/{total}] {rel_path} -> {res.get('status', 'unknown')}")
                summary["details"].append(res)
                _update_summary(summary, res)

    # 保存处理日志
    log_path = dst_dir / ".ocr_process_log.json"
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"警告：无法保存处理日志: {e}")

    return summary


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="批量 PDF OCR 处理（优化版）")
    parser.add_argument("src", help="源文件夹路径")
    parser.add_argument("dst", help="输出文件夹路径")
    parser.add_argument("--quality", choices=["fast", "normal", "high"], default=None,
                        help="OCR 质量模式（fast/normal/high），未指定时使用自适应 zoom")
    parser.add_argument("--zoom", type=float, default=None,
                        help="渲染分辨率倍数（覆盖 quality 设置），未指定时使用自适应 zoom")
    parser.add_argument("--skip-existing", action="store_true",
                        help="跳过已存在的输出文件（断点续传）")
    parser.add_argument("--workers", type=int, default=1,
                        help="并发工作进程数（默认 1，建议 CPU 核心数 - 1）")
    parser.add_argument("--timeout", type=int, default=600,
                        help="单文件处理超时秒数（默认 600）")
    args = parser.parse_args()

    zoom_map = {"fast": 1.5, "normal": 2, "high": 3}
    if args.zoom is not None:
        zoom = args.zoom
    elif args.quality is not None:
        zoom = zoom_map[args.quality]
    else:
        zoom = None  # 由单文件根据页数和坏页比例自适应选择

    src_dir = Path(args.src)
    dst_dir = Path(args.dst)

    if not src_dir.exists():
        print(f"错误：源文件夹不存在: {src_dir}")
        sys.exit(1)

    dst_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PDF OCR 批量处理（优化版）")
    print("=" * 60)
    print(f"源文件夹: {src_dir}")
    print(f"输出文件夹: {dst_dir}")
    if args.zoom is not None:
        print(f"zoom: {zoom}（手动指定）")
    elif args.quality is not None:
        print(f"质量模式: {args.quality} (zoom={zoom})")
    else:
        print("zoom: 自适应（按页数/坏页比例自动选择）")
    print(f"工作进程: {args.workers}")
    print(f"单文件超时: {args.timeout}s")
    if args.skip_existing:
        print("模式: 断点续传")
    print("=" * 60)

    summary = process_directory(src_dir, dst_dir, zoom, args.skip_existing, args.workers, args.timeout)

    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"总计: {summary['total']} 个 PDF")
    print(f"成功: {summary['success']} 个")
    print(f"  - 直接复制（已有文本层）: {summary['copied']} 个")
    print(f"  - OCR 处理: {summary['ocr']} 个")
    print(f"  - 跳过（已存在）: {summary['skipped']} 个")
    print(f"失败: {summary['failed']} 个")
    print(f"日志: {dst_dir / '.ocr_process_log.json'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
