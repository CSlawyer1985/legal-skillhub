#!/usr/bin/env python3
"""
中国大陆法律术语在线补充抓取脚本

从以下来源抓取大陆法律术语：
1. NPC 英文网站 (npc.gov.cn) - 核心法律官方英译本
2. China Law Translate (chinalawtranslate.com) - 社区翻译术语表
3. HardMTBench (GitHub) - 法律领域术语对

注意：由于网络限制，自动抓取可能失败。
内置回退使用 references/mainland_terms.csv 中的精选术语集。

用法：
    python scrape_mainland.py [--output OUTPUT.csv] [--no-fallback]

输出格式与 glossary.csv 兼容：
    中文词语,英文词语,来源,领域,类型
"""

import csv
import os
import sys
import json
import re

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILTIN_TERMS = os.path.join(SKILL_DIR, 'references', 'mainland_terms.csv')


def try_fetch_hardmtbench():
    """尝试从 GitHub 下载 HardMTBench 法律领域术语"""
    import urllib.request
    import io

    url = 'https://raw.githubusercontent.com/jasonNLP/HardMTBench/main/data/HardMTBench.jsonl'
    print(f"[*] 尝试下载 HardMTBench: {url}")

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'legal-translation-skill/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode('utf-8')

        entries = []
        for line in data.split('\n'):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                if item.get('domain') == 'Legal':
                    for term in item.get('terminology', []):
                        entries.append([
                            term.get('source', ''),
                            term.get('target', ''),
                            'HardMTBench',
                            '通用',
                            '单词',
                        ])
            except json.JSONDecodeError:
                continue

        print(f"  [+] 获取到 {len(entries)} 条法律术语")
        return entries

    except Exception as e:
        print(f"  [-] 下载失败: {e}")
        return []


def try_fetch_npc():
    """尝试从 NPC 英文网站抓取核心法律术语"""
    # NPC 网站需要特殊处理，且经常无法访问
    # 此函数留作占位符，供后续实现
    print("[*] NPC 网站抓取暂未实现（需要处理 frame 结构和 SSL 问题）")
    print("[*] 建议手动访问 http://www.npc.gov.cn/englishnpc/Law/")
    return []


def try_fetch_clt():
    """尝试从 China Law Translate 抓取术语表"""
    print("[*] China Law Translate 抓取暂未实现")
    print("[*] 建议手动访问 https://www.chinalawtranslate.com/glossary/")
    return []


def load_builtin_terms():
    """加载内置大陆法律术语精选集"""
    if not os.path.exists(BUILTIN_TERMS):
        print(f"[-] 内置术语文件不存在: {BUILTIN_TERMS}")
        return []

    entries = []
    with open(BUILTIN_TERMS, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) >= 5 and row[0].strip() and row[1].strip():
                entries.append([row[0].strip(), row[1].strip(), row[2].strip(),
                              row[3].strip(), row[4].strip()])

    print(f"[+] 加载内置术语: {len(entries)} 条")
    return entries


def merge_and_dedupe(entries_list, output_path):
    """合并多个来源的术语并去重"""
    seen = set()
    merged = []

    for entries in entries_list:
        for entry in entries:
            key = (entry[0], entry[1])  # (CN, EN)
            if key not in seen:
                seen.add(key)
                merged.append(entry)

    # 按中文排序
    merged.sort(key=lambda x: x[0])

    # 写入 CSV
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['中文词语', '英文词语', '来源', '领域', '类型'])
        writer.writerows(merged)

    return merged


def main():
    import argparse
    parser = argparse.ArgumentParser(description='中国大陆法律术语在线补充抓取')
    parser.add_argument('--output', '-o', default=None,
                        help='输出 CSV 路径 (默认: references/mainland_terms_scraped.csv)')
    parser.add_argument('--no-fallback', action='store_true',
                        help='不使用内置精选术语集作为回退')
    parser.add_argument('--online-only', action='store_true',
                        help='仅尝试在线抓取，不使用任何本地文件')

    args = parser.parse_args()

    if args.output is None:
        args.output = os.path.join(SKILL_DIR, 'references', 'mainland_terms_scraped.csv')

    all_entries = []

    # 1. 尝试在线抓取
    if not args.no_fallback or args.online_only:
        online_entries = try_fetch_hardmtbench()
        if online_entries:
            all_entries.append(online_entries)

        # NPC 和 CLT 目前未实现，跳过
        _ = try_fetch_npc()
        _ = try_fetch_clt()

    # 2. 加载内置精选集
    if not args.online_only:
        builtin = load_builtin_terms()
        if builtin:
            all_entries.append(builtin)

    # 3. 合并输出
    if not all_entries:
        print("\n[-] 未能获取任何术语，请检查网络连接或使用内置术语集")
        return 1

    merged = merge_and_dedupe(all_entries, args.output)
    print(f"\n[+] 总计: {len(merged)} 条大陆法律术语")
    print(f"[+] 输出: {args.output}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
