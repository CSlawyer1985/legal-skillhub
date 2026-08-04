#!/usr/bin/env python3
"""
拜访行为库查询脚本
按灯色（red/yellow/green/all）过滤并输出行为列表
"""

import json
import sys
import os

def load_behavior_library():
    """加载行为库JSON文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ref_path = os.path.join(script_dir, '..', 'references', 'behavior_library.json')
    with open(ref_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_behaviors(query_light='all', category=None):
    """
    按灯色和类别过滤行为

    Args:
        query_light: 'red', 'yellow', 'green', or 'all'
        category: 可选，按类别过滤（如'礼品/费用', '学术推广'等）

    Returns:
        过滤后的行为列表
    """
    library = load_behavior_library()

    if query_light not in ['red', 'yellow', 'green', 'all']:
        print(f"错误：灯色参数只能为 red、yellow、green 或 all，收到的值为：{query_light}")
        sys.exit(1)

    results = library if query_light == 'all' else [
        b for b in library if b['light'] == query_light
    ]

    if category:
        results = [b for b in results if b.get('category') == category]

    return results

def format_output(behaviors):
    """格式化输出为Markdown表格"""
    if not behaviors:
        print("未找到匹配的行为记录。")
        return

    # 按灯色分组
    groups = {'red': [], 'yellow': [], 'green': []}
    for b in behaviors:
        groups[b['light']].append(b)

    light_labels = {
        'red': '🔴 红灯行为（绝对禁止）',
        'yellow': '🟡 黄灯行为（需满足条件/报批）',
        'green': '🟢 绿灯行为（合规鼓励执行）'
    }

    for light_color, label in light_labels.items():
        items = groups[light_color]
        if not items:
            continue

        print(f"\n### {label}\n")
        if light_color == 'yellow':
            print("| 序号 | 行为名称 | 判定理由 | 审批条件 | 典型场景 |")
            print("|------|---------|---------|---------|---------|")
            for i, b in enumerate(items, 1):
                print(f"| {i} | {b['name']} | {b['reason']} | {b.get('approval_condition', '—')} | {b['typical_scenario']} |")
        else:
            print("| 序号 | 行为名称 | 判定理由 | 典型场景 |")
            print("|------|---------|---------|---------|")
            for i, b in enumerate(items, 1):
                print(f"| {i} | {b['name']} | {b['reason']} | {b['typical_scenario']} |")

def main():
    query_light = sys.argv[1] if len(sys.argv) > 1 else 'all'
    category = sys.argv[2] if len(sys.argv) > 2 else None

    behaviors = list_behaviors(query_light, category)
    format_output(behaviors)
    print(f"\n共找到 {len(behaviors)} 条行为记录（灯色：{query_light}）")

if __name__ == '__main__':
    main()
