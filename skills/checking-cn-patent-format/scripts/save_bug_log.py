#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUG日志JSON格式化写入工具

功能：
将BUG审查结果以规范的JSON格式（indent=2, ensure_ascii=False）写入文件，
避免LLM Agent直接写入导致JSON堆在一行的问题。

用法：
    python save_bug_log.py --input <临时JSON文件> --output <目标文件路径>
    python save_bug_log.py --data '<JSON字符串>' --output <目标文件路径>
"""

import sys
import io
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (AttributeError, io.UnsupportedOperation):
    pass


def validate_bug_log(data):
    """验证BUG日志数据结构的基本完整性。"""
    if not isinstance(data, dict):
        raise ValueError("BUG日志必须是JSON对象(dict)")

    required_keys = ['meta', 'bugs']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"BUG日志缺少必需字段: {key}")

    if not isinstance(data['bugs'], list):
        raise ValueError("'bugs'字段必须是数组")

    if 'meta' in data and isinstance(data['meta'], dict):
        if 'total_bugs_found' in data['meta']:
            declared = data['meta']['total_bugs_found']
            actual = len(data['bugs'])
            if declared != actual:
                print(f"Warning: meta.total_bugs_found={declared} but actual bugs count={actual}, auto-correcting", file=sys.stderr)
                data['meta']['total_bugs_found'] = actual

    return data


def save_bug_log(data, output_path):
    """将BUG日志以规范格式写入文件。"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    data = validate_bug_log(data)

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"BUG日志已写入: {output}")
    print(f"  文件大小: {output.stat().st_size} 字节")
    print(f"  BUG数量: {len(data.get('bugs', []))}")
    return True


def main():
    parser = argparse.ArgumentParser(description='BUG日志JSON格式化写入工具')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help='输入的临时JSON文件路径')
    group.add_argument('--data', help='直接传入的JSON字符串')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--validate-only', action='store_true', help='仅验证不写入')

    args = parser.parse_args()

    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.loads(args.data)

    data = validate_bug_log(data)

    if args.validate_only:
        print("验证通过")
        return

    save_bug_log(data, args.output)


if __name__ == '__main__':
    main()
