#!/usr/bin/env python3
"""
法律术语中英互译查询工具
支持精确匹配、子串搜索、模糊匹配，以及按领域/来源筛选。

用法：
    # 精确查询
    python lookup.py -q "不可抗力"
    python lookup.py -q "force majeure"

    # 模糊查询
    python lookup.py -q "合同违约" --fuzzy

    # 子串搜索
    python lookup.py -q "仲裁" --substring

    # 按领域筛选
    python lookup.py -q "证据" --domain 诉讼法

    # JSON 输出
    python lookup.py -q "tort" --format json

    # 限制结果数
    python lookup.py -q "party" --limit 10
"""

import csv
import argparse
import json
import os
import re
from difflib import SequenceMatcher

# ========== 配置 ==========

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_GLOSSARY = os.path.join(SKILL_DIR, 'references', 'glossary.csv')
DEFAULT_MAINLAND = os.path.join(SKILL_DIR, 'references', 'mainland_terms.csv')


def load_glossary(path):
    """加载术语库CSV"""
    entries = []
    if not os.path.exists(path):
        return entries

    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) >= 5:
                entries.append({
                    'cn': row[0].strip(),
                    'en': row[1].strip(),
                    'source': row[2].strip() if len(row) > 2 else '',
                    'domain': row[3].strip() if len(row) > 3 else '通用',
                    'type': row[4].strip() if len(row) > 4 else '',
                })
            elif len(row) >= 3:
                entries.append({
                    'cn': row[0].strip(),
                    'en': row[1].strip(),
                    'source': row[2].strip() if len(row) > 2 else '',
                    'domain': '通用',
                    'type': '',
                })
    return entries


def similarity(a, b):
    """计算两个字符串的相似度 (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def search_exact(entries, query):
    """精确匹配：中文或英文完全相等"""
    results = []
    q_lower = query.lower().strip()

    for entry in entries:
        if entry['cn'].lower() == q_lower or entry['en'].lower() == q_lower:
            results.append((entry, 1.0))
    return results


def search_substring(entries, query):
    """子串匹配：中文或英文包含查询词"""
    results = []
    q_lower = query.lower().strip()

    for entry in entries:
        score = 0
        if q_lower in entry['cn'].lower():
            # 中文匹配：查询词占中文词语的比例
            score = len(q_lower) / max(len(entry['cn']), 1)
        if q_lower in entry['en'].lower():
            # 英文匹配：优先匹配完整单词
            en_words = entry['en'].lower().split()
            q_words = q_lower.split()
            word_match = any(qw in en_words for qw in q_words)
            en_score = len(q_lower) / max(len(entry['en']), 1)
            if word_match:
                en_score += 0.3  # 单词匹配加分
            score = max(score, en_score)
        if score > 0:
            results.append((entry, min(score, 1.0)))
    return results


def search_fuzzy(entries, query, threshold=0.4):
    """模糊匹配：计算相似度"""
    results = []
    q_lower = query.lower().strip()

    for entry in entries:
        cn_sim = similarity(entry['cn'], q_lower)
        en_sim = similarity(entry['en'], q_lower)

        # 也检查子串匹配作为快速通道
        if q_lower in entry['cn'].lower():
            cn_sim = max(cn_sim, 0.7 + 0.3 * len(q_lower) / max(len(entry['cn']), 1))
        if q_lower in entry['en'].lower():
            en_sim = max(en_sim, 0.7 + 0.3 * len(q_lower) / max(len(entry['en']), 1))

        best = max(cn_sim, en_sim)
        if best >= threshold:
            results.append((entry, best))

    return results


def filter_by_domain(results, domain):
    """按法律领域筛选"""
    return [(e, s) for e, s in results if e['domain'] == domain]


def format_text(results, query, show_source=True):
    """文本格式输出"""
    if not results:
        return f"未找到与 \"{query}\" 匹配的术语。"

    lines = []
    lines.append(f"查询: \"{query}\"")
    lines.append(f"找到 {len(results)} 条结果:")
    lines.append("-" * 60)

    for i, (entry, score) in enumerate(results, 1):
        lines.append(f"\n[{i}] {entry['cn']}")
        lines.append(f"    EN: {entry['en']}")
        if show_source and entry['source']:
            lines.append(f"    来源: {entry['source']}")
        meta = []
        if entry['domain'] and entry['domain'] != '通用':
            meta.append(entry['domain'])
        if entry['type']:
            meta.append(entry['type'])
        if meta:
            lines.append(f"    标签: {', '.join(meta)}")
        if score < 1.0:
            lines.append(f"    匹配度: {score:.0%}")

    return '\n'.join(lines)


def format_json(results, query):
    """JSON 格式输出"""
    output = {
        'query': query,
        'count': len(results),
        'results': []
    }
    for entry, score in results:
        output['results'].append({
            'cn': entry['cn'],
            'en': entry['en'],
            'source': entry['source'],
            'domain': entry['domain'],
            'type': entry['type'],
            'score': round(score, 3),
        })
    return json.dumps(output, ensure_ascii=False, indent=2)


def format_csv_output(results, query):
    """CSV 格式输出"""
    lines = ['中文词语,英文词语,来源,领域,类型,匹配度']
    for entry, score in results:
        lines.append(f'"{entry["cn"]}","{entry["en"]}","{entry["source"]}","{entry["domain"]}","{entry["type"]}",{score:.3f}')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='法律术语中英互译查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python lookup.py -q "不可抗力"
  python lookup.py -q "negligence" --fuzzy
  python lookup.py -q "仲裁" --substring --domain 诉讼法
  python lookup.py -q "tort" --format json
        """
    )
    parser.add_argument('-q', '--query', required=True, help='查询词（中文或英文）')
    parser.add_argument('--fuzzy', action='store_true', help='启用模糊匹配')
    parser.add_argument('--substring', '-s', action='store_true', help='子串搜索模式（默认）')
    parser.add_argument('--exact', '-e', action='store_true', help='仅精确匹配')
    parser.add_argument('--domain', '-d', default=None, help='按法律领域筛选')
    parser.add_argument('--source', default=None, help='按来源筛选')
    parser.add_argument('--limit', '-n', type=int, default=20, help='最大返回结果数 (默认: 20)')
    parser.add_argument('--format', '-f', default='text', choices=['text', 'json', 'csv'],
                        help='输出格式 (默认: text)')
    parser.add_argument('--glossary', '-g', default=None, help='指定术语库CSV路径')
    parser.add_argument('--no-source', action='store_true', help='不显示来源信息')

    args = parser.parse_args()

    # 加载术语库
    paths = []
    if args.glossary:
        paths.append(args.glossary)
    else:
        paths.append(DEFAULT_GLOSSARY)
        if os.path.exists(DEFAULT_MAINLAND):
            paths.append(DEFAULT_MAINLAND)

    entries = []
    for path in paths:
        loaded = load_glossary(path)
        entries.extend(loaded)
        if loaded:
            print(f"已加载 {os.path.basename(path)}: {len(loaded)} 条", file=__import__('sys').stderr)

    if not entries:
        print("错误: 未找到任何术语库文件", file=__import__('sys').stderr)
        return 1

    # 去重（保留先加载的）
    seen = set()
    unique_entries = []
    for e in entries:
        key = (e['cn'], e['en'])
        if key not in seen:
            seen.add(key)
            unique_entries.append(e)
    entries = unique_entries

    # 搜索
    query = args.query.strip()

    if args.exact:
        results = search_exact(entries, query)
    elif args.fuzzy:
        results = search_fuzzy(entries, query)
    else:
        # 先精确匹配
        results = search_exact(entries, query)
        if not results:
            # 再子串匹配
            results = search_substring(entries, query)

    # 排序（按匹配度降序）
    results.sort(key=lambda x: x[1], reverse=True)

    # 按领域筛选
    if args.domain:
        results = filter_by_domain(results, args.domain)

    # 限制数量
    results = results[:args.limit]

    # 输出
    show_source = not args.no_source
    if args.format == 'json':
        print(format_json(results, query))
    elif args.format == 'csv':
        print(format_csv_output(results, query))
    else:
        print(format_text(results, query, show_source))

    return 0


if __name__ == '__main__':
    exit(main())
