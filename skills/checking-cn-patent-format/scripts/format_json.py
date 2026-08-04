#!/usr/bin/env python3
"""
JSON文件格式化工具

将指定目录中的JSON文件重新格式化为标准缩进格式（indent=2）。
解决子Agent通过Write工具输出单行JSON的问题。

用法：
    python format_json.py --work-dir "<work_dir>" [--pattern "reviews_agent*_*.json"]
"""

import json
import sys
import io
from pathlib import Path
from glob import glob
import argparse

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (AttributeError, io.UnsupportedOperation):
    pass


def format_json_files(work_dir, pattern="reviews_agent*_*.json"):
    """格式化工作目录中所有匹配的JSON文件。"""
    work_dir = Path(work_dir)
    search_pattern = str(work_dir / pattern)
    matched_files = sorted(glob(search_pattern))

    formatted_count = 0
    skipped_count = 0
    error_count = 0

    for file_path_str in matched_files:
        file_path = Path(file_path_str)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()

            lines = raw_content.strip().split('\n')
            needs_rewrite = len(lines) <= 3
            if not needs_rewrite:
                for line in lines[:5]:
                    if len(line) > 500:
                        needs_rewrite = True
                        break

            if not needs_rewrite:
                skipped_count += 1
                continue

            data = json.loads(raw_content)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            formatted_count += 1
            print(f"  ✓ 已格式化: {file_path.name}")
        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON解析失败: {file_path.name} ({e})")
            error_count += 1
        except Exception as e:
            print(f"  ⚠ 处理失败: {file_path.name} ({e})")
            error_count += 1

    print(f"\n格式化完成：共 {len(matched_files)} 个文件，格式化 {formatted_count} 个，跳过 {skipped_count} 个，失败 {error_count} 个")
    return formatted_count, error_count


def main():
    parser = argparse.ArgumentParser(description="JSON文件格式化工具")
    parser.add_argument("--work-dir", required=True, help="工作目录路径")
    parser.add_argument("--pattern", default="reviews_agent*_*.json", help="文件匹配模式（默认：reviews_agent*_*.json）")
    args = parser.parse_args()

    format_json_files(args.work_dir, args.pattern)


if __name__ == "__main__":
    main()
