#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用 OCR 工具 v3（RapidOCR ONNX Runtime 版）
===============================================
用法：
    python ocr_tool.py <图片目录> [输出文件.txt]

优化要点：
    - 引擎: RapidOCR（ONNX Runtime），轻量低CPU，无需PaddlePaddle
    - 预处理: 缩放 + CLAHE 对比度增强（不做去噪，避免CPU爆表）
    - 线程: 自动限制为CPU核心数的一半，保留系统响应能力
    - 内存: 每张图片处理完主动 gc.collect() 释放

运行环境：
    Python 3.10+
    需安装: rapidocr-onnxruntime, opencv-python, numpy
"""

import os
import sys
import time
import gc
import numpy as np
import cv2

# ── 限制线程，防止CPU爆表 ────────────────────────────────────────
CPU_CORES = os.cpu_count() or 4
THREAD_LIMIT = max(2, CPU_CORES // 2)
cv2.setNumThreads(THREAD_LIMIT)
os.environ['OMP_NUM_THREADS'] = str(THREAD_LIMIT)
os.environ['OPENBLAS_NUM_THREADS'] = str(THREAD_LIMIT)
os.environ['MKL_NUM_THREADS'] = str(THREAD_LIMIT)


def preprocess(img_path: str, max_side: int = 1500) -> np.ndarray | None:
    """轻量预处理：缩放 + CLAHE 均衡化"""
    raw = np.fromfile(img_path, dtype=np.uint8)
    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if img is None:
        return None

    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return img


def run_ocr(img_dir: str, output_file: str | None = None) -> str:
    """对目录下所有图片做OCR，返回合并文本"""
    from rapidocr_onnxruntime import RapidOCR

    if output_file is None:
        output_file = os.path.join(img_dir, 'OCR识别结果.txt')

    print(f'[配置] 线程: {THREAD_LIMIT}/{CPU_CORES} 核')
    print('[初始化] 加载 RapidOCR...')
    t0 = time.time()
    ocr = RapidOCR()
    print(f'[初始化] 完成，耗时: {time.time()-t0:.1f}秒')

    images = sorted([
        f for f in os.listdir(img_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])
    print(f'[扫描] 找到 {len(images)} 张图片')

    all_lines = []
    total_start = time.time()

    for i, img_name in enumerate(images):
        img_path = os.path.join(img_dir, img_name)
        print(f'[{i+1}/{len(images)}] {img_name}')

        img = preprocess(img_path)
        if img is None:
            print('  读取失败，跳过')
            continue

        rec_start = time.time()
        result, _ = ocr(img)
        rec_time = time.time() - rec_start

        texts = []
        if result:
            for item in result:
                if len(item) >= 2:
                    text = str(item[1]).strip()
                    conf = float(item[2]) if len(item) >= 3 else 1.0
                    if text and conf > 0.5:
                        texts.append(text)

        all_lines.append(f'\n{"="*50}')
        all_lines.append(f'图片: {img_name}  耗时: {rec_time:.1f}秒')
        all_lines.append('\n'.join(texts) if texts else '(未识别到文字)')
        print(f'  完成 {rec_time:.1f}秒 | {len(texts)} 行')

        del img
        gc.collect()

    total_time = time.time() - total_start
    avg_time = total_time / len(images) if images else 0
    summary = f'总耗时: {total_time:.1f}秒  平均: {avg_time:.1f}秒/张'
    print(f'\n[汇总] {summary}')

    content = (
        f'OCR识别结果\n'
        f'引擎: RapidOCR (ONNX Runtime)\n'
        f'识别时间: {time.strftime("%Y-%m-%d %H:%M:%S")}\n'
        f'图片数量: {len(images)}\n'
        f'{summary}\n'
        + '\n'.join(all_lines)
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[完成] 已保存: {output_file}')
    return content


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python ocr_tool.py <图片目录> [输出文件.txt]')
        sys.exit(1)
    img_dir = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    run_ocr(img_dir, out_file)
