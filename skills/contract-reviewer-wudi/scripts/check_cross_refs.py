#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交叉引用一致性检查器
检查合同中条款编号引用是否指向存在的条款，
以及引用表述是否准确（如：第X条引用第Y条，但X条实际不存在等）。
"""

import re
import sys
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def qn(tag):
    return f'{{{W}}}{tag}'


def get_paragraph_text(p_elem):
    texts = []
    for t in p_elem.iter(qn('t')):
        if t.text:
            texts.append(t.text)
    return ''.join(texts)


# 条款编号提取模式
CLAUSE_NUM_PATTERNS = [
    # 第X条、第X款
    re.compile(r'^第([一二三四五六七八九十百千万零\d]+)条'),
    # 第X章
    re.compile(r'^第([一二三四五六七八九十百千万零\d]+)章'),
    # 1.  2.  编号
    re.compile(r'^(\d+)[\.、]\s'),
    # (一)、(二)
    re.compile(r'^[（(]([一二三四五六七八九十]+)[）、)]'),
]

# 交叉引用提取模式
XREF_PATTERNS = [
    # 第X条、第X条第Y款
    re.compile(
        r'第([一二三四五六七八九十百千万零\d]+)条'
        r'(?:第([一二三四五六七八九十\d]+)款)?'
    ),
    # 参照/参见第X条
    re.compile(r'(?:参照|参见|详见|见|依照|按照|依据|援引|引用|遵照|参照)第?([一二三四五六七八九十百\d]+)条'),
    # 附件X
    re.compile(r'附件\s*([一二三四五六七八九十\d甲乙丙]+)'),
]


def chinese_to_arabic(cn):
    """将中文数字转换为阿拉伯数字"""
    CN_MAP = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
              '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
              '百': 100, '千': 1000, '万': 10000, '零': 0}
    cn = str(cn).strip()
    if cn.isdigit():
        return int(cn)
    result = 0
    tmp = 0
    for ch in cn:
        v = CN_MAP.get(ch, 0)
        if v >= 1000:
            result += tmp * v
            tmp = 0
        elif v >= 10:
            if tmp == 0:
                tmp = 1
            result += tmp * v
            tmp = 0
        else:
            tmp += v
    result += tmp
    return result if result > 0 else 0


def extract_clause_numbers(text):
    """提取文本中的条款编号列表"""
    nums = set()
    for pat in CLAUSE_NUM_PATTERNS:
        for m in pat.finditer(text):
            raw = m.group(1) if m.lastindex else m.group(0)
            try:
                nums.add(int(chinese_to_arabic(raw)))
            except (ValueError, TypeError):
                pass
    return nums


def extract_xrefs(text):
    """提取文本中的所有交叉引用"""
    refs = []
    for pat in XREF_PATTERNS:
        for m in pat.finditer(text):
            groups = [g for g in m.groups() if g is not None]
            for g in groups:
                try:
                    num = int(chinese_to_arabic(g))
                    refs.append({'num': num, 'raw': m.group(0), 'text_snippet': text[max(0, m.start()-5):m.end()+5]})
                except (ValueError, TypeError):
                    pass
    return refs


def check_cross_refs(docx_path, output_json=None):
    """
    检查 docx 中的交叉引用一致性。
    返回 {issues: [...], statistics: {...}}
    """
    path = Path(docx_path)
    if not path.exists():
        return {'error': f'文件不存在: {path}'}

    issues = []
    clause_numbers = {}   # num -> {'text': ..., 'index': ...}
    all_xrefs = []        # (num, raw, snippet, para_index)

    try:
        with zipfile.ZipFile(path, 'r') as zf:
            xml_content = zf.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            body = tree.find(qn('body'))

            para_index = 0
            for p_elem in body.iter(qn('p')):
                text = get_paragraph_text(p_elem).strip()
                if not text:
                    para_index += 1
                    continue

                # 提取自身条款编号
                nums = extract_clause_numbers(text)
                for n in nums:
                    if n not in clause_numbers:
                        clause_numbers[n] = {'text': text[:60], 'index': para_index}

                # 提取交叉引用
                xrefs = extract_xrefs(text)
                for x in xrefs:
                    x['para_index'] = para_index
                    all_xrefs.append(x)

                para_index += 1

    except zipfile.BadZipFile:
        return {'error': '非有效 ZIP 格式'}
    except ET.ParseError as e:
        return {'error': f'XML 解析失败: {e}'}

    # 检查每个引用是否指向存在的条款
    dangling_refs = []
    for x in all_xrefs:
        if x['num'] not in clause_numbers:
            dangling_refs.append({
                'type': 'dangling_reference',
                'ref_num': x['num'],
                'ref_text': x['raw'],
                'from_paragraph_index': x['para_index'],
                'from_text_snippet': x['text_snippet'],
                'suggestion': f'合同中引用了"第{x["raw"]}"，但该条款不存在于本合同中。请核实是否为笔误或是否应引用其他条款。',
                'severity': '中风险'
            })

    # 检查编号是否连续（提示可能缺失的条款）
    if clause_numbers:
        sorted_nums = sorted(clause_numbers.keys())
        missing = []
        for i in range(len(sorted_nums) - 1):
            diff = sorted_nums[i+1] - sorted_nums[i]
            if diff > 1 and sorted_nums[i] > 0:
                missing.append({
                    'type': 'missing_clause',
                    'missing_range': f'{sorted_nums[i]+1}至{sorted_nums[i+1]-1}',
                    'after_clause': f'第{_to_chinese(sorted_nums[i])}条',
                    'before_clause': f'第{_to_chinese(sorted_nums[i+1])}条',
                    'suggestion': f'合同编号从{sorted_nums[i]}跳至{sorted_nums[i+1]}，'
                                  f'建议确认是否存在缺失条款（如：删除了某条但未重新编号，或引用了已删除条款）。',
                    'severity': '低风险'
                })

    # 检查自引用
    self_refs = []
    for num, info in clause_numbers.items():
        info_text = info['text']
        nums_in_text = extract_clause_numbers(info_text)
        for n in nums_in_text:
            if n == num:
                self_refs.append({
                    'type': 'self_reference',
                    'clause_num': num,
                    'clause_text': info_text[:80],
                    'para_index': info['index'],
                    'suggestion': f'第{_to_chinese(num)}条正文提到了自身条款编号，可能是自引用错误（如"第X条第X款"应引用其他条款）。',
                    'severity': '低风险'
                })

    # 检查附件引用
    appendix_refs = []
    for x in all_xrefs:
        if '附件' in x['raw'] or '附' in x['raw']:
            appendix_refs.append({
                'type': 'appendix_reference',
                'ref': x['raw'],
                'from_para_index': x['para_index'],
                'from_snippet': x['text_snippet'],
                'suggestion': f'合同引用了"{x["raw"]}"，请确认相应附件是否存在且编号一致。',
                'severity': '一般'
            })

    issues = dangling_refs + missing + self_refs + appendix_refs

    result = {
        'file': str(path),
        'statistics': {
            'total_clauses': len(clause_numbers),
            'total_xrefs': len(all_xrefs),
            'dangling_refs': len(dangling_refs),
            'missing_clauses': len(missing),
            'self_refs': len(self_refs),
            'appendix_issues': len(appendix_refs),
            'clean': len(issues) == 0,
        },
        'clause_numbers': {str(k): v for k, v in clause_numbers.items()},
        'issues': issues,
    }

    if output_json:
        Path(output_json).parent.mkdir(parents=True, exist_ok=True)
        Path(output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'已输出: {output_json}')

    return result


def _to_chinese(n):
    """阿拉伯数字转中文"""
    if isinstance(n, str) and n.isdigit():
        n = int(n)
    CN = '零一二三四五六七八九十'
    if n <= 10:
        return CN[n-1] if 1 <= n <= 10 else '零'
    if n < 20:
        return '十' + CN[n-11]
    if n < 100:
        return CN[n//10-1] + '十' + (CN[n%10-1] if n%10 else '')
    return str(n)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='交叉引用一致性检查器')
    parser.add_argument('docx_path', help='待检查的 .docx 文件路径')
    parser.add_argument('output_json', nargs='?', help='输出 JSON 文件路径（可选）')
    args = parser.parse_args()

    result = check_cross_refs(args.docx_path, args.output_json)

    if 'error' in result:
        print(f'[ERROR] {result["error"]}')
        sys.exit(1)

    stats = result['statistics']
    print('\n========== 交叉引用检查结果 ==========')
    print(f'  合同条款总数:    {stats["total_clauses"]}')
    print(f'  交叉引用总数:    {stats["total_xrefs"]}')
    print(f'  孤立引用（⚠️）:   {stats["dangling_refs"]}')
    print(f'  缺失条款（⚠️）:   {stats["missing_clauses"]}')
    print(f'  自引用:          {stats["self_refs"]}')
    print(f'  附件引用:        {stats["appendix_issues"]}')

    if not stats['clean']:
        print(f'\n发现 {len(result["issues"])} 个问题：')
        for i, issue in enumerate(result['issues'], 1):
            print(f'\n  【{i}】{issue["type"]} | {issue["severity"]}')
            if issue['type'] == 'dangling_reference':
                print(f'      引用了: 第{issue["ref_num"]}条')
                print(f'      在段落 {issue["from_paragraph_index"]}: "{issue["from_text_snippet"]}"')
            elif issue['type'] == 'missing_clause':
                print(f'      缺失范围: 第{issue["missing_range"]}条')
                print(f'      上一条: {issue["after_clause"]}  下一条: {issue["before_clause"]}')
            print(f'      建议: {issue["suggestion"]}')
    else:
        print('\n✅ 交叉引用检查通过，未发现明显问题。')

    print()
    if args.output_json:
        print(f'详细报告已输出至: {args.output_json}')


if __name__ == '__main__':
    main()
