#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多轮迭代管理器
管理合同审核的多轮迭代，跟踪版本历史，支持版本对比和回滚

功能:
  1. init: 初始化项目，创建 manifest.json
  2. new-round: 创建新一轮迭代
  3. status: 查看当前迭代状态
  4. compare: 对比两轮迭代的差异
  5. rollback: 回滚到指定轮次

目录结构:
  合同名称-Output/
    manifest.json           # 迭代管理清单
    round-1/
      合同-修订批注版.docx
      合同-清洁版.docx
      合同-审查报告.txt
      changes.json          # 本轮变更记录
    round-2/
      ...
    round-N/
      ...

manifest.json 格式:
{
  "project_name": "合同名称",
  "created_at": "2026-04-15T10:00:00Z",
  "current_round": 2,
  "rounds": [
    {
      "round": 1,
      "created_at": "2026-04-15T10:00:00Z",
      "files": {
        "revised": "round-1/合同-修订批注版.docx",
        "clean": "round-1/合同-清洁版.docx",
        "report": "round-1/合同-审查报告.txt",
        "changes": "round-1/changes.json"
      },
      "summary": {
        "revisions_count": 15,
        "comments_count": 8,
        "high_risk": 3,
        "medium_risk": 5,
        "low_risk": 7
      }
    },
    ...
  ]
}
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


def get_manifest_path(project_dir: Path) -> Path:
    """获取 manifest.json 路径"""
    return project_dir / 'manifest.json'


def load_manifest(project_dir: Path) -> dict:
    """加载 manifest"""
    manifest_path = get_manifest_path(project_dir)
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_manifest(project_dir: Path, manifest: dict):
    """保存 manifest"""
    manifest_path = get_manifest_path(project_dir)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def cmd_init(project_dir: Path, project_name: str = None) -> dict:
    """初始化项目"""
    manifest = load_manifest(project_dir)
    if manifest is not None:
        return {'success': False, 'error': '项目已初始化', 'manifest': manifest}

    if project_name is None:
        project_name = project_dir.name.replace('-Output', '')

    manifest = {
        'project_name': project_name,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'current_round': 0,
        'rounds': [],
    }
    save_manifest(project_dir, manifest)
    return {'success': True, 'manifest': manifest}


def cmd_new_round(project_dir: Path, files: dict = None, summary: dict = None) -> dict:
    """
    创建新一轮迭代

    files: {
        'revised': 'path/to/revised.docx',
        'clean': 'path/to/clean.docx',
        'report': 'path/to/report.txt',
        'changes': 'path/to/changes.json'
    }
    """
    manifest = load_manifest(project_dir)
    if manifest is None:
        return {'success': False, 'error': '项目未初始化，请先运行 init'}

    current = manifest['current_round']
    new_round = current + 1

    round_dir = project_dir / f'round-{new_round}'
    round_dir.mkdir(parents=True, exist_ok=True)

    round_files = {}
    if files:
        for key, src_path in files.items():
            if src_path and Path(src_path).exists():
                dest = round_dir / Path(src_path).name
                shutil.copy2(src_path, dest)
                round_files[key] = str(dest.relative_to(project_dir))

    round_info = {
        'round': new_round,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'files': round_files,
        'summary': summary or {},
    }

    manifest['rounds'].append(round_info)
    manifest['current_round'] = new_round
    save_manifest(project_dir, manifest)

    return {
        'success': True,
        'round': new_round,
        'round_dir': str(round_dir),
        'manifest': manifest,
    }


def cmd_status(project_dir: Path) -> dict:
    """查看当前状态"""
    manifest = load_manifest(project_dir)
    if manifest is None:
        return {'success': False, 'error': '项目未初始化'}

    current = manifest['current_round']
    rounds = manifest['rounds']

    return {
        'success': True,
        'project_name': manifest['project_name'],
        'current_round': current,
        'total_rounds': len(rounds),
        'rounds': [
            {
                'round': r['round'],
                'created_at': r['created_at'],
                'files': list(r.get('files', {}).keys()),
                'summary': r.get('summary', {}),
            }
            for r in rounds
        ],
    }


def cmd_compare(project_dir: Path, round_a: int, round_b: int) -> dict:
    """对比两轮迭代的差异"""
    manifest = load_manifest(project_dir)
    if manifest is None:
        return {'success': False, 'error': '项目未初始化'}

    rounds = manifest['rounds']
    round_a_info = None
    round_b_info = None

    for r in rounds:
        if r['round'] == round_a:
            round_a_info = r
        if r['round'] == round_b:
            round_b_info = r

    if round_a_info is None:
        return {'success': False, 'error': f'轮次 {round_a} 不存在'}
    if round_b_info is None:
        return {'success': False, 'error': f'轮次 {round_b} 不存在'}

    # 对比 summary
    sum_a = round_a_info.get('summary', {})
    sum_b = round_b_info.get('summary', {})

    diff = {
        'round_a': round_a,
        'round_b': round_b,
        'summary_diff': {
            key: {'from': sum_a.get(key), 'to': sum_b.get(key)}
            for key in set(sum_a.keys()) | set(sum_b.keys())
            if sum_a.get(key) != sum_b.get(key)
        },
        'files_a': round_a_info.get('files', {}),
        'files_b': round_b_info.get('files', {}),
    }

    return {'success': True, 'comparison': diff}


def cmd_rollback(project_dir: Path, target_round: int) -> dict:
    """回滚到指定轮次"""
    manifest = load_manifest(project_dir)
    if manifest is None:
        return {'success': False, 'error': '项目未初始化'}

    rounds = manifest['rounds']
    target_info = None

    for r in rounds:
        if r['round'] == target_round:
            target_info = r
            break

    if target_info is None:
        return {'success': False, 'error': f'轮次 {target_round} 不存在'}

    # 删除目标轮次之后的所有轮次
    new_rounds = [r for r in rounds if r['round'] <= target_round]
    manifest['rounds'] = new_rounds
    manifest['current_round'] = target_round

    # 删除目录
    for r in rounds:
        if r['round'] > target_round:
            round_dir = project_dir / f'round-{r["round"]}'
            if round_dir.exists():
                shutil.rmtree(round_dir)

    save_manifest(project_dir, manifest)

    return {
        'success': True,
        'rolled_back_to': target_round,
        'manifest': manifest,
    }


def cmd_export(project_dir: Path, round_num: int = None, output_dir: Path = None) -> dict:
    """
    导出指定轮次的文件到项目根目录（方便查看）
    """
    manifest = load_manifest(project_dir)
    if manifest is None:
        return {'success': False, 'error': '项目未初始化'}

    if round_num is None:
        round_num = manifest['current_round']

    target_info = None
    for r in manifest['rounds']:
        if r['round'] == round_num:
            target_info = r
            break

    if target_info is None:
        return {'success': False, 'error': f'轮次 {round_num} 不存在'}

    if output_dir is None:
        output_dir = project_dir

    exported = []
    for key, rel_path in target_info.get('files', {}).items():
        src = project_dir / rel_path
        if src.exists():
            dest = output_dir / src.name
            shutil.copy2(src, dest)
            exported.append(str(dest))

    return {
        'success': True,
        'round': round_num,
        'exported_files': exported,
    }


# ============================================================
# 命令行入口
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='合同审核多轮迭代管理器')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # init
    p_init = subparsers.add_parser('init', help='初始化项目')
    p_init.add_argument('project_dir', help='项目目录（通常是 合同名称-Output）')
    p_init.add_argument('--name', help='项目名称（默认从目录名推断）')

    # new-round
    p_new = subparsers.add_parser('new-round', help='创建新一轮迭代')
    p_new.add_argument('project_dir', help='项目目录')
    p_new.add_argument('--revised', help='修订批注版 docx 路径')
    p_new.add_argument('--clean', help='清洁版 docx 路径')
    p_new.add_argument('--report', help='审查报告 txt 路径')
    p_new.add_argument('--changes', help='changes.json 路径')

    # status
    p_status = subparsers.add_parser('status', help='查看状态')
    p_status.add_argument('project_dir', help='项目目录')

    # compare
    p_compare = subparsers.add_parser('compare', help='对比两轮迭代')
    p_compare.add_argument('project_dir', help='项目目录')
    p_compare.add_argument('round_a', type=int, help='轮次 A')
    p_compare.add_argument('round_b', type=int, help='轮次 B')

    # rollback
    p_rollback = subparsers.add_parser('rollback', help='回滚到指定轮次')
    p_rollback.add_argument('project_dir', help='项目目录')
    p_rollback.add_argument('round', type=int, help='目标轮次')

    # export
    p_export = subparsers.add_parser('export', help='导出指定轮次文件')
    p_export.add_argument('project_dir', help='项目目录')
    p_export.add_argument('--round', type=int, help='轮次（默认当前轮次）')
    p_export.add_argument('--output', help='输出目录（默认项目根目录）')

    args = parser.parse_args()

    if args.command == 'init':
        result = cmd_init(Path(args.project_dir), args.name)

    elif args.command == 'new-round':
        files = {
            'revised': args.revised,
            'clean': args.clean,
            'report': args.report,
            'changes': args.changes,
        }
        files = {k: v for k, v in files.items() if v}
        result = cmd_new_round(Path(args.project_dir), files)

    elif args.command == 'status':
        result = cmd_status(Path(args.project_dir))

    elif args.command == 'compare':
        result = cmd_compare(Path(args.project_dir), args.round_a, args.round_b)

    elif args.command == 'rollback':
        result = cmd_rollback(Path(args.project_dir), args.round)

    elif args.command == 'export':
        output_dir = Path(args.output) if args.output else None
        result = cmd_export(Path(args.project_dir), args.round, output_dir)

    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
