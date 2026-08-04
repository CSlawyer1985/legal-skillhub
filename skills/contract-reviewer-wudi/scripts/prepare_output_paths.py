#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输出路径准备工具
创建标准化的输出目录结构，支持多轮迭代
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def main():
    if len(sys.argv) < 2:
        print('用法: prepare_output_paths.py <原合同路径> [--round N]')
        sys.exit(1)

    source = Path(sys.argv[1]).resolve()
    stem = source.stem

    # 解析 --round 参数
    round_num = None
    if '--round' in sys.argv:
        idx = sys.argv.index('--round')
        if idx + 1 < len(sys.argv):
            try:
                round_num = int(sys.argv[idx + 1])
            except ValueError:
                pass

    # 基础输出目录
    output_dir = source.parent / f'{stem}-Output'
    output_dir.mkdir(parents=True, exist_ok=True)

    # 如果指定了轮次，创建子目录
    if round_num is not None:
        round_dir = output_dir / f'round-{round_num}'
        round_dir.mkdir(parents=True, exist_ok=True)
        output_dir = round_dir
        suffix = f'-R{round_num}'
    else:
        suffix = ''

    result = {
        'source': str(source),
        'source_stem': stem,
        'output_dir': str(output_dir),
        'revised_docx': str(output_dir / f'{stem}-修订批注版{suffix}.docx'),
        'clean_docx': str(output_dir / f'{stem}-清洁版{suffix}.docx'),
        'report_txt': str(output_dir / f'{stem}-审查报告{suffix}.txt'),
        'changes_json': str(output_dir / f'{stem}-changes{suffix}.json'),
        'structure_json': str(output_dir / f'{stem}-结构解析{suffix}.json'),
        'round': round_num,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
